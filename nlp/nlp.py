import re
import json
import spacy
import huspacy
import jsonlines
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import concurrent.futures

class ArticlePreprocessor:
    def __init__(self, nlp_model):
        self.nlp = nlp_model

    def remove_newspaper_name(self, title, newspaper_name):
        patterns = [
            rf"{newspaper_name}:\s*",
            rf"\s*-\s*{newspaper_name}",
            rf"\s*\|\s*{newspaper_name}",
        ]
        
        for pattern in patterns:
            title = re.sub(pattern, "", title)
        
        return title.strip()

    def preprocess_text(self, text):
        doc = self.nlp(text)
        tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
        return " ".join(tokens)
    
    def compute_tfidf(self, documents):
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)
        return tfidf_matrix, vectorizer.get_feature_names_out()

class SentimentAnalyzer:
    def __init__(self, model_name):
        self.sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)

    def analyze_sentiment(self, text):
        result = self.sentiment_pipeline(text)
        return result[0]["label"], result[0]["score"]
    
def process_article(article, preprocessor, sentiment_analyzer):
    title = article["title"]
    newspaper_name = article["source"]

    # Remove newspaper name from the title
    clean_title = preprocessor.remove_newspaper_name(title, newspaper_name)

    # Preprocess title
    processed_title = preprocessor.preprocess_text(clean_title)

    # Analyze sentiment
    #sentiment, score = sentiment_analyzer.analyze_sentiment(clean_title)

    return {
        "original_title": title,
        "clean_title": clean_title,
        "processed_title": processed_title,
    }

def main():
    # Load Hungarian NLP model
    nlp = huspacy.load()

    # Create a preprocessor instance
    preprocessor = ArticlePreprocessor(nlp)

    # Load the sentiment analysis model (Replace "model_name" with a Hungarian sentiment analysis model)
    sentiment_analyzer = SentimentAnalyzer("NYTK/sentiment-ohb3-hubert-hungarian")   

    processed_titles = []

    # Process the articles
    input_file = "./input.ndjson"
    output_file = "./output.json"

    with jsonlines.open(input_file) as reader, open(output_file, "w") as writer:
        # Process the articles in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_article, article, preprocessor, sentiment_analyzer) for article in reader]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Create a list of preprocessed titles from the results
        processed_titles = [result["processed_title"] for result in results]

        # Compute TF-IDF scores for preprocessed titles
        title_tfidf_matrix, title_features = preprocessor.compute_tfidf(processed_titles)

        # Write output data to JSON file
        json.dump(results, writer)

if __name__ == "__main__":
    main()