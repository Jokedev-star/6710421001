import cloudscraper, json, time, os, random

SET50 = [
    "DELTA","ADVANC","PTT","GULF","AOT","PTTEP","SCB","CPALL","KBANK","TRUE",
    "KTB","BDMS","BBL","CPN","SCC","TTB","CPF","OR","BH","MINT",
    "TLI","CRC","IVL","GPSC","PTTGC","TOP","HMPRO","BEM","SCGP","TISCO",
    "AWC","KTC","MTC","RATCH","BJC","EGCO","WHA","TCAP","KKP","BANPU",
    "COM7","TIDLOR","OSP","CCET","TU","LH","CENTEL","SAWAD","CBG","BTS",
]

SET50_NAMES = {
    "DELTA":"Delta Electronics (Thailand)","ADVANC":"Advanced Info Service",
    "PTT":"PTT Public Company Limited","GULF":"Gulf Energy Development",
    "AOT":"Airports of Thailand","PTTEP":"PTT Exploration and Production",
    "SCB":"SCB X Public Company Limited","CPALL":"CP All Public Company Limited",
    "KBANK":"Kasikornbank Public Company Limited","TRUE":"True Corporation",
    "KTB":"Krung Thai Bank","BDMS":"Bangkok Dusit Medical Services",
    "BBL":"Bangkok Bank","CPN":"Central Pattana","SCC":"The Siam Cement",
    "TTB":"TMBThanachart Bank","CPF":"Charoen Pokphand Foods","OR":"PTT Oil and Retail Business",
    "BH":"Bumrungrad International Hospital","MINT":"Minor International",
    "TLI":"Thai Life Insurance","CRC":"Central Retail Corporation","IVL":"Indorama Ventures",
    "GPSC":"Global Power Synergy","PTTGC":"PTT Global Chemical",
    "TOP":"Thai Oil Public Company Limited","HMPRO":"Home Product Center",
    "BEM":"Bangkok Expressway and Metro","SCGP":"SCG Packaging",
    "TISCO":"Tisco Financial Group","AWC":"Asset World Corp",
    "KTC":"Krungthai Card Public Company Limited","MTC":"Muangthai Capital",
    "RATCH":"Ratch Group","BJC":"Berli Jucker","EGCO":"Electricity Generating",
    "WHA":"WHA Corporation","TCAP":"Thanachart Capital","KKP":"Kiatnakin Phatra Bank",
    "BANPU":"Banpu","COM7":"Com Seven","TIDLOR":"Tidlor Holdings",
    "OSP":"Osotspa","CCET":"Cal-Comp Electronics (Thailand)","TU":"Thai Union Group",
    "LH":"Land and Houses","CENTEL":"Central Plaza Hotel","SAWAD":"Srisawad Corporation",
    "CBG":"Carabao Group","BTS":"BTS Group Holdings",
}

def fetch_stock_shareholders(symbol, max_retries=3):
    """Fetch shareholder data for a single stock with retry logic."""
    for attempt in range(max_retries):
        try:
            scraper = cloudscraper.create_scraper()
            headers_html = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            headers_api = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': f'https://www.set.or.th/th/market/product/stock/quote/{symbol}/major-shareholders',
            }
            r = scraper.get('https://www.set.or.th/', headers=headers_html, timeout=20)
            if r.status_code != 200:
                raise Exception(f"Homepage returned {r.status_code}")
            r2 = scraper.get(f'https://www.set.or.th/api/set/stock/{symbol}/shareholder', headers=headers_api, timeout=20)
            if r2.status_code == 200 and 'json' in r2.headers.get('Content-Type', ''):
                return r2.json()
            else:
                raise Exception(f"API returned {r2.status_code}")
        except Exception as e:
            if attempt < max_retries - 1:
                wait = random.uniform(3, 6)
                time.sleep(wait)
                continue
            return {"error": str(e), "symbol": symbol}

all_data = {}
success = 0
failed = 0

for i, sym in enumerate(SET50):
    name = SET50_NAMES.get(sym, sym)
    print(f'[{i+1}/{len(SET50)}] Fetching {sym} ({name})...')
    
    result = fetch_stock_shareholders(sym)
    all_data[sym] = result
    
    if "error" not in result:
        holders = result.get('majorShareholders', [])
        print(f'  => OK - {len(holders)} major shareholders, bookClose={result.get("bookCloseDate","N/A")}')
        success += 1
    else:
        print(f'  => FAILED - {result["error"]}')
        failed += 1
    
    print(f'  => Progress: {success} success, {failed} failed\n')
    
    if i < len(SET50) - 1:
        delay = random.uniform(2.0, 4.0)
        time.sleep(delay)

print(f'\n{"="*50}')
print(f'Final Results: {success} success, {failed} failed')
print(f'{"="*50}')

output = {
    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "source": "SET.or.th API (/api/set/stock/{symbol}/shareholder)",
    "total_stocks": len(SET50),
    "success_count": success,
    "failed_count": failed,
    "data": all_data,
}

output_path = os.path.join(os.path.dirname(__file__), 'shareholder_data.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\nData saved to {output_path}")
