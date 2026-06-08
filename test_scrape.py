import cloudscraper
import json

scraper = cloudscraper.create_scraper()

# Try fetching the SET website with cloudscraper
url = 'https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders'
r = scraper.get(url, timeout=20)
print(f'Status: {r.status_code}, Size: {len(r.text)}')

# Try to find the internal API endpoint
# Look for any API calls in the JavaScript
import re
api_patterns = re.findall(r'/api/[^"\']+', r.text)
print(f'Found API patterns in HTML: {len(api_patterns)}')
for p in api_patterns[:20]:
    print(f'  {p}')

# Also try the JSON endpoint
json_url = 'https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders?format=json'
r2 = scraper.get(json_url, timeout=20)
print(f'\nJSON endpoint Status: {r2.status_code}, Content-Type: {r2.headers.get("Content-Type")}')
if r2.status_code == 200 and 'json' in r2.headers.get('Content-Type', ''):
    print(json.dumps(r2.json(), indent=2)[:2000])
