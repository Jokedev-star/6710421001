import json
with open('shareholder_data.json', encoding='utf-8') as f:
    data = json.load(f)
print('Total stocks:', data['total_stocks'])
print('Fetched at:', data['fetched_at'])
ptt = data['data']['PTT']
print('\nPTT bookCloseDate:', ptt['bookCloseDate'])
print('Total shareholders (SET count):', ptt['totalShareholder'])
print('\nTop 10 PTT shareholders:')
for h in ptt['majorShareholders'][:10]:
    print(f'  #{h["sequence"]}: {h["name"]} - {h["numberOfShare"]:,} shares ({h["percentOfShare"]}%) NVDR={h["isThaiNVDR"]}')
cpn = data['data']['CPN']
print(f'\nCPN major holders count:', len(cpn['majorShareholders']))
