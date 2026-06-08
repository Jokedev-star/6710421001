import cloudscraper, json

scraper = cloudscraper.create_scraper()

base_url = 'https://www.set.or.th'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders',
}

# First get the main page to get cookies
scraper.get('https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders', timeout=20)

# Try various API endpoints
endpoints = [
    '/api/set/stock/PTT/major-shareholder',
    '/api/set/stock/PTT/major-shareholders',
    '/api/set/stock/PTT/shareholder',
    '/api/set/stock/PTT/shareholders',
    '/api/cms-w/v1/pages/count-share/PTT',
    '/api/cms-w/v1/pages/count-share/?symbol=PTT',
    '/api/cms-w/v1/news/set/share-counting?symbol=PTT',
    '/api/set/stock/PTT/company-profile',
]

for ep in endpoints:
    url = f'{base_url}{ep}'
    try:
        r = scraper.get(url, headers=headers, timeout=20)
        ct = r.headers.get('Content-Type', '')
        is_json = 'json' in ct
        print(f'{ep} -> {r.status_code} {ct[:30]} {len(r.text)} bytes')
        if r.status_code == 200 and is_json:
            data = r.json()
            print(json.dumps(data, indent=2)[:1500])
            break
        elif r.status_code == 200:
            print(f'  Not JSON: {r.text[:200]}')
    except Exception as e:
        print(f'{ep} -> ERROR: {e}')
