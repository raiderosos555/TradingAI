"""Owner-approved <=5,000,000 byte COT/Fed package, fixed years 2010-2025.
Fed country HTML is a fixed source page; only 2010-2025 rows enter analysis.
No MT5, no orders, no accounts, no automatic retry/pagination.
"""
import json
from pathlib import Path
from urllib.parse import urlencode
from fetch import fetch
OUT=Path(__file__).resolve().parent/'private'/'package-v1'
CAP=5_000_000

def main():
    if OUT.exists():raise RuntimeError('Refuse overwrite')
    jobs=[]
    common='report_date_as_yyyy_mm_dd,cftc_contract_market_code,open_interest_all,futonly_or_combined'
    for name,ds,codes,fields,limit in [
      ('tff','gpe5-46if',['099741','096742','13874A','209742'],'lev_money_positions_long,lev_money_positions_short',1_600_000),
      ('disagg','72hh-3qpy',['088691','067651'],'m_money_positions_long_all,m_money_positions_short_all',850_000)]:
        params={'$select':common+','+fields,'$where':"cftc_contract_market_code in ("+','.join("'"+x+"'" for x in codes)+") AND report_date_as_yyyy_mm_dd >= '2010-01-01T00:00:00' AND report_date_as_yyyy_mm_dd < '2026-01-01T00:00:00'",'$order':'cftc_contract_market_code,report_date_as_yyyy_mm_dd','$limit':'4000'}
        jobs.append((name,'https://publicreporting.cftc.gov/resource/'+ds+'.json?'+urlencode(params),limit))
    jobs += [('fed_'+name+'_complete','https://www.federalreserve.gov/releases/h10/hist/dat00_'+code+'.htm',1_250_000) for name,code in [('eur','eu'),('gbp','uk')]]
    results=[];used=0
    for name,url,limit in jobs:
        r=fetch(name,url,OUT,min(limit,CAP-used));used+=r.get('bytes',0);results.append(r)
        (OUT/'manifest.json').write_text(json.dumps({'approved_cap':CAP,'used':used,'sources':results},indent=2),encoding='utf-8')
        if r['returncode']!=0:raise RuntimeError('Stop on failed download: '+name)
    assert used<=CAP
    (OUT/'manifest.json').write_text(json.dumps({'approved_cap':CAP,'used':used,'sources':results},indent=2),encoding='utf-8')

if __name__=='__main__':main()
