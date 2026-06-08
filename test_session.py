import cloudscraper, time

scraper = cloudscraper.create_scraper()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Visit the major shareholders page first to get session cookies
print("1. Visiting shareholders page...")
r = scraper.get('https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders', headers=headers, timeout=20)
print(f"   Status: {r.status_code}, Cookies: {len(scraper.cookies)}")
for c in scraper.cookies:
    print(f"   Cookie: {c.name} = {c.value[:30] if c.value else 'None'}...")

time.sleep(2)

# Now try the API with JSON accept
print("\n2. Calling API...")
headers2 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders',
}
r2 = scraper.get('https://www.set.or.th/api/set/stock/PTT/shareholder', headers=headers2, timeout=20)
print(f"   Status: {r2.status_code}, Content-Type: {r2.headers.get('Content-Type')}")
if r2.status_code == 200:
    print(f"   Data: {r2.text[:300]}")
else:
    print(f"   Response: {r2.text[:200]}")

# Try without the session page visit
print("\n3. Fresh scraper - visit homepage first...")
scraper2 = cloudscraper.create_scraper()
r3 = scraper2.get('https://www.set.or.th/', headers=headers, timeout=20)
print(f"   Homepage Status: {r3.status_code}")
time.sleep(2)

print("\n4. Then call API...")
r4 = scraper2.get('https://www.set.or.th/api/set/stock/PTT/shareholder', headers=headers2, timeout=20)
print(f"   Status: {r4.status_code}, Content-Type: {r4.headers.get('Content-Type')}")
if r4.status_code == 200:
    print(f"   Data: {r4.text[:300]}")
else:
    print(f"   Response: {r4.text[:200]}")

print("\n5. Try with fresh IP approach...")
import requests as std_requests
s = std_requests.Session()
s.headers.update(headers)
r5 = s.get('https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders', timeout=20)
print(f"   Page Status: {r5.status_code}")
time.sleep(2)
r6 = s.get('https://www.set.or.th/api/set/stock/PTT/shareholder', headers=headers2, timeout=20)
print(f"   API Status: {r6.status_code}")
if r6.status_code == 200:
    print(f"   Data: {r6.text[:300]}")
else:
    print(f"   Response: {r6.text[:200]}")
