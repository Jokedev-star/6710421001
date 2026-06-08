import requests, re, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,th;q=0.8',
}

r = requests.get('https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders', headers=headers, timeout=10)
print(f'Status: {r.status_code}, Content-Type: {r.headers.get("Content-Type")}, Size: {len(r.text)}')

# Look for JSON data in script tags
for match in re.findall(r'<script[^>]*>window\.__NUXT__\s*=\s*({.*?})</script>', r.text, re.DOTALL):
    print('Found Nuxt data!')
    data = json.loads(match)
    print(json.dumps(data, indent=2)[:2000])
    break
else:
    print('No Nuxt data found')
    # Try looking for any JSON-like data
    for match in re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', r.text, re.DOTALL):
        print(f'Found JSON script tag: {match[:200]}')
        break
    else:
        print('No JSON script tags found')
    
    # Check if major shareholder table exists in some form
    if 'รายชื่อผู้ถือหุ้น' in r.text or 'major' in r.text.lower() or 'shareholder' in r.text.lower():
        print('Found shareholder-related keywords in HTML')

    print('\nFirst 1500 chars:')
    print(r.text[:1500])
