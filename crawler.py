import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin
import time
import logging
from datetime import datetime, timedelta
import asyncio
import aiohttp

from bs4 import XMLParsedAsHTMLWarning
import warnings

from config import config
from url_schemas import url_schemas

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Load configuration
headers = config["headers"]
output_file = config["output_file"]
concurrency_limit = config["concurrency_limit"]

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Set up concurrency
semaphore = asyncio.Semaphore(concurrency_limit)

processed_urls = set()

class Crawler:
    def __init__(self, session):
        self.session = session

    async def process_schema(self, url, source, all_data):
        global processed_urls
        print(f'Crawling page: {url}')

        soup = await self.crawl_page(url)

        if not soup:
            return False

        links = soup.find_all('a')
        has_links = False

        if links:
            for link in links:
                link_url = link.get('href')

                if link_url is None or link_url in processed_urls:
                    continue

                has_links = True
                processed_urls.add(link_url)

                link_soup = await self.crawl_page(link_url, base_url=url)
                if link_soup and self.is_article(link_soup):
                    metadata = self.extract_metadata(link_soup, source)
                    if metadata:
                        all_data.append(metadata)

        return has_links
    
    async def crawl_page(self, url, base_url=None):
        try:
            if not url:
                raise ValueError("URL is empty or None")

            if base_url:
                url = urljoin(base_url, url)

            async with semaphore:
                async with self.session.get(url, headers=headers, timeout=10) as response:
                    response.raise_for_status()
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    return soup

        except (aiohttp.ClientError, ValueError) as e:
            logger.error(f"Error crawling URL {url}: {e}")
            return None
        except asyncio.exceptions.TimeoutError as te:
            logger.error(f"Timeout error while crawling URL {url}: {te}")
            return None
    
    def is_article(self, soup):
        if not soup:
            return False

        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            property_attr = meta.get('property')
            if property_attr == 'og:type':
                return meta.get('content') == 'article'
        return False

    def extract_metadata(self, soup, source):
        if not soup:
            return None

        meta_tags = soup.find_all('meta')
        is_article = False
        url = ''
        title = ''
        description = ''
        thumbnail = ''
        date = ''

        for meta in meta_tags:
            property_attr = meta.get('property')
            name_attr = meta.get('name')
            itemprop_attr = meta.get('itemprop')

            if property_attr == 'og:type':
                is_article = meta.get('content') == 'article'

            if property_attr == 'og:locale':
                locale = meta.get('content')

            if (
                name_attr in ['modified-date', 'publish-date', 'article:published_time', 'article:modified_time'] or 
                itemprop_attr == 'datePublished' or
                property_attr in ['article:published_time', 'article:modified_time']
            ):
                date = meta.get('content')[:10]

            if name_attr == 'description' or property_attr == 'og:description':
                description = meta.get('content')

            if property_attr == 'og:image':
                thumbnail = meta.get('content')

            if name_attr == 'keywords':
                keywords = meta.get('content')

        if is_article:
            title = soup.title.string if soup.title else ''
            url_element = soup.find('link', rel='canonical')
            
            if url_element:
                url = url_element['href']
            else:
                return None

            return {
                'url': url,
                'source': source,
                'title': title,
                'description': description,
                'thumbnail': thumbnail,
                'date': date
            }
        else:
            return None
    
class PageCrawler():
    def __init__(self, session, schema, page, all_data):
        self.session = session
        self.schema = schema
        self.page = page
        self.all_data = all_data

    async def process(self):
        url = self.schema['url']
        page_url = url.format(page=self.page)
        return Crawler(self.session).process_schema(page_url, self.schema['source'], self.all_data)

class DateCrawler():
    def __init__(self, session, schema, current_date, all_data):
        self.session = session
        self.schema = schema
        self.current_date = current_date
        self.all_data = all_data

    async def process(self):
        has_links = False

        if 'column' in self.schema['url']:
            columns = self.schema['columns']
            
            for column in columns:
                has_links = await self.process_pages(column=column)
                
        else:
            has_links = await self.process_pages(column=None)

        return has_links

    async def process_pages(self, column:None):
        date_str = self.current_date.strftime('%Y-%m-%d')
        year, month, day = date_str.split('-')

        has_links = True
        page = 1

        while has_links:
            if column:
                url = self.schema['url'].format(column=column, date=date_str, year=year, month=month, day=day, page=page)
            else:
                url = self.schema['url'].format(date=date_str, year=year, month=month, day=day, page=page)
            
            has_links = await Crawler(self.session).process_schema(url, self.schema['source'], self.all_data)

            if has_links:
                page += 1
            else:
                break
        
        return has_links

async def save_data(data, file_name=output_file):
    if not data:
        return

    with open(file_name, 'a') as file:
        for item in data:
            file.write(json.dumps(item, ensure_ascii=False) + '\n')

async def save_data_periodically(all_data, save_period=config["save_period"]):
    while True:
        await asyncio.sleep(save_period)
        await save_data(all_data)
        all_data.clear()

async def main():
    global processed_urls
    global output_file

    all_data = []

    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            for line in file:
                data_item = json.loads(line.strip())
                processed_urls.add(data_item['url'])
    
    more_pages = True
    page = 1
    current_date = datetime.now().date()

    async with aiohttp.ClientSession() as session:
        save_data_task = asyncio.create_task(save_data_periodically(all_data))

        while more_pages:
            more_pages = True

            tasks = []
            for schema in url_schemas:
                if(schema['type'] == 'PAGE'):
                    task = PageCrawler(session, schema, page, all_data).process()
                elif(schema['type'] == 'DATE'):
                    task = DateCrawler(session, schema, current_date, all_data).process()
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            # more_pages = any(results)
            
            page += 1
            current_date -= timedelta(days=1)
        
        save_data_task.cancel()
        await save_data(all_data)

if __name__ == '__main__':
    asyncio.run(main())