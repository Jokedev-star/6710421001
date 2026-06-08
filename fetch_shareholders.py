import cloudscraper, json, time, os

SET50 = [
    "DELTA","ADVANC","PTT","GULF","AOT","PTTEP","SCB","CPALL","KBANK","TRUE",
    "KTB","BDMS","BBL","CPN","SCC","TTB","CPF","OR","BH","MINT",
    "TLI","CRC","IVL","GPSC","PTTGC","TOP","HMPRO","BEM","SCGP","TISCO",
    "AWC","KTC","MTC","RATCH","BJC","EGCO","WHA","TCAP","KKP","BANPU",
    "COM7","TIDLOR","OSP","CCET","TU","LH","CENTEL","SAWAD","CBG","BTS",
]

SET50_NAMES = {
    "DELTA":"Delta Electronics","ADVANC":"Advanced Info Service","PTT":"PTT",
    "GULF":"Gulf Development","AOT":"Airports of Thailand",
    "PTTEP":"PTT Exploration & Production","SCB":"SCB X",
    "CPALL":"CP All","KBANK":"Kasikornbank","TRUE":"True Corporation",
    "KTB":"Krung Thai Bank","BDMS":"Bangkok Dusit Medical Services",
    "BBL":"Bangkok Bank","CPN":"Central Pattana","SCC":"Siam Cement",
    "TTB":"TMBThanachart Bank","CPF":"Charoen Pokphand Foods","OR":"PTT Oil & Retail",
    "BH":"Bumrungrad Hospital","MINT":"Minor International",
    "TLI":"Thai Life Insurance","CRC":"Central Retail","IVL":"Indorama Ventures",
    "GPSC":"Global Power Synergy","PTTGC":"PTT Global Chemical",
    "TOP":"Thai Oil","HMPRO":"Home Product Center","BEM":"Bangkok Expressway and Metro",
    "SCGP":"SCG Packaging","TISCO":"Tisco Financial Group",
    "AWC":"Asset World Corp","KTC":"Krungthai Card","MTC":"Muangthai Capital",
    "RATCH":"Ratch Group","BJC":"Berli Jucker","EGCO":"Electricity Generating",
    "WHA":"WHA Corporation","TCAP":"Thanachart Capital","KKP":"Kiatnakin Phatra Bank",
    "BANPU":"Banpu","COM7":"Com Seven","TIDLOR":"Tidlor Holdings",
    "OSP":"Osotspa","CCET":"Cal-Comp Electronics","TU":"Thai Union Group",
    "LH":"Land and Houses","CENTEL":"Central Plaza Hotel","SAWAD":"Srisawad Corporation",
    "CBG":"Carabao Group","BTS":"BTS Group Holdings",
}

scraper = cloudscraper.create_scraper()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,th;q=0.8',
}

# First, establish a session by visiting the SET homepage
print("Establishing session...")
r = scraper.get('https://www.set.or.th/th/market/product/stock/quote/PTT/major-shareholders', headers=headers, timeout=20)
print(f"Session established: {r.status_code}")

all_data = {}
success = 0
failed = 0

for i, sym in enumerate(SET50):
    url = f'https://www.set.or.th/api/set/stock/{sym}/shareholder'
    try:
        r = scraper.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and 'json' in r.headers.get('Content-Type', ''):
            data = r.json()
            all_data[sym] = data
            holders = data.get('majorShareholders', [])
            print(f'[{i+1}/50] {sym} ({SET50_NAMES.get(sym, "")}): OK - {len(holders)} holders, bookClose={data.get("bookCloseDate","N/A")}')
            success += 1
        else:
            print(f'[{i+1}/50] {sym}: {r.status_code}')
            all_data[sym] = {"error": f"HTTP {r.status_code}", "symbol": sym}
            failed += 1
    except Exception as e:
        print(f'[{i+1}/50] {sym}: ERROR - {e}')
        all_data[sym] = {"error": str(e), "symbol": sym}
        failed += 1
    
    # Be polite - delay between requests
    if i < len(SET50) - 1:
        time.sleep(1.0)

print(f"\nDone! Success: {success}, Failed: {failed}")

# Save to JSON file
output_path = os.path.join(os.path.dirname(__file__), 'shareholder_data.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "data": all_data}, f, ensure_ascii=False, indent=2)
print(f"Data saved to {output_path}")
