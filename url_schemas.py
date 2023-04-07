url_schemas = [
    {
        'url': 'https://www.borsonline.hu/kereses?page={page}',
        'type': 'PAGE',
        'source': 'BorsOnline'
    },
    {
        'url': 'https://www.magyarhirlap.hu/kereses?tol={date}&ig={date}&page={page}',
        'type': 'DATE',
        'source': 'Magyar Hírlap'
    },
    {
        'url': 'https://magyarnemzet.hu/kereses?from_date={date}&to_date={date}&page={page}',
        'type': 'DATE',
        'source': 'Magyar Nemzet'
    },
    {
        'url': 'https://www.origo.hu/hir-archivum/{year}/{year}{month}{day}.html',
        'type': 'DATE',
        'source': 'Origo'
    },
    {
        'url': 'https://pestisracok.hu/page/{page}/?s',
        'type': 'PAGE',
        'source': 'PestiSrácok'
    },
    {
        'url': 'https://www.szoljon.hu/kereses?fromDate={date}&toDate={date}&page={page}',
        'type': 'DATE',
        'source': 'Szoljon.hu'
    },
    {
        'url': 'https://24.hu/{column}/{year}/{month}/{day}/page/{page}',
        'type': 'DATE',
        'source': '24.hu',
        'columns': ['belfold', 'kulfold', 'gazdasag', 'kultura', 'tech', 'elet-stilus', 'szorakozas', 'kozelet', 'tudomany', 'sport', 'otthon']
    },
    {
        'url': 'https://www.blikk.hu/archivum/online?date={date}&page={page}',
        'type': 'DATE',
        'source': 'Blikk'
    },
    {
        'url': 'https://www.portfolio.hu/kereses?q=&a=&df={date}&dt={date}&c=&page={page}',
        'type': 'DATE',
        'source': 'Portfolio'
    },
    {
        'url': 'https://telex.hu/archivum?oldal={page}',
        'type': 'PAGE',
        'source': 'Telex'
    },
]

""" url_schemas = [
    {
        'url': 'https://www.origo.hu/hir-archivum/{year}/{year}{month}{day}.html',
        'type': 'DATE',
        'source': 'Origo'
    },
] """