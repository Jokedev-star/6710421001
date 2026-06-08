import cloudscraper, re, json

scraper = cloudscraper.create_scraper()

# Get the page to find JavaScript chunks
r = scraper.get('https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders', timeout=20)

# Find all script src
scripts = re.findall(r'<script[^>]+src="([^"]+)"', r.text)
js_files = [s for s in scripts if s.endswith('.js')]
print(f'Found {len(js_files)} JS files')
for js in js_files[:10]:
    print(f'  {js}')
    try:
        if js.startswith('/'):
            js_url = f'https://www.set.or.th{js}'
        elif js.startswith('http'):
            js_url = js
        else:
            continue
        js_r = scraper.get(js_url, timeout=10)
        # Look for API endpoints in JS
        apis = re.findall(r'["\'](/api/[^"\']+)["\']', js_r.text)
        if apis:
            print(f'    APIs found: {apis[:5]}')
            for api in apis[:5]:
                print(f'      -> {api}')
    except Exception as e:
        print(f'    Error: {e}')
