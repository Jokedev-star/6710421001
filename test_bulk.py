import cloudscraper, json, time

SET50 = [
    "DELTA","ADVANC","PTT","GULF","AOT","PTTEP","SCB","CPALL","KBANK","TRUE",
    "KTB","BDMS","BBL","CPN","SCC","TTB","CPF","OR","BH","MINT",
    "TLI","CRC","IVL","GPSC","PTTGC","TOP","HMPRO","BEM","SCGP","TISCO",
    "AWC","KTC","MTC","RATCH","BJC","EGCO","WHA","TCAP","KKP","BANPU",
    "COM7","TIDLOR","OSP","CCET","TU","LH","CENTEL","SAWAD","CBG","BTS",
]

scraper = cloudscraper.create_scraper()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.set.or.th/th/market/product/stock/quote/',
}

results = {}
for i, sym in enumerate(SET50[:5]):  # Test first 5
    url = f'https://www.set.or.th/api/set/stock/{sym}/shareholder'
    try:
        r = scraper.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and 'json' in r.headers.get('Content-Type', ''):
            data = r.json()
            results[sym] = data
            print(f'[{i+1}/5] {sym}: OK - {len(data.get("majorShareholders", []))} shareholders, bookClose={data.get("bookCloseDate")}')
        else:
            print(f'[{i+1}/5] {sym}: {r.status_code} - {r.text[:100]}')
    except Exception as e:
        print(f'[{i+1}/5] {sym}: ERROR - {e}')
    time.sleep(0.5)

print('\n=== SAMPLE DATA (PTT) ===')
print(json.dumps(results.get('PTT', {}), indent=2, ensure_ascii=False)[:2000])
