"""Public RSS context, independent of broker execution. Headlines are data, never instructions."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timezone
from email.utils import parsedate_to_datetime
import html
import re
import sqlite3
import os
import ssl
import subprocess
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .journal import atomic_write, process_lock
from .models import Blocked, canonical, digest, read_json, timestamp, utcnow

SOURCES = {
 'fed': {'url':'https://www.federalreserve.gov/feeds/press_monetary.xml', 'hosts':['www.federalreserve.gov','federalreserve.gov'],
         'instruments':['GOLD','US500','US100','EURUSD','GBPUSD','OIL'], 'topic':'monetary_policy'},
 'ecb': {'url':'https://www.ecb.europa.eu/rss/press.html','hosts':['www.ecb.europa.eu','www.ecb.europa.eu'],
         'instruments':['EURUSD','EURPLN'], 'topic':'euro_area'},
 'eia': {'url':'https://www.eia.gov/rss/todayinenergy.xml','hosts':['www.eia.gov','eia.gov'],
         'instruments':['OIL'], 'topic':'energy'},
 'bbc_world': {'url':'https://feeds.bbci.co.uk/news/world/rss.xml','hosts':['feeds.bbci.co.uk','www.bbc.com','www.bbc.co.uk'],
         'instruments':['GOLD','US500','US100','OIL','EURUSD','GBPUSD','EURPLN'], 'topic':'world_news'}
}
EVENT_WORDS = re.compile(r'\b(war|attack|sanctions?|tariffs?|ceasefire|oil|inflation|interest rates?|fomc)\b',re.I)

def download(spec):
    request=Request(spec['url'],headers={'User-Agent':'TradingAI-LocalResearch/1.0 RSS reader'})
    try:
        with urlopen(request,timeout=12) as response:
            if urlsplit(response.url).hostname not in spec['hosts']:raise ValueError('Unexpected redirect')
            return response.read(2_000_001)
    except URLError as exc:
        if os.name!='nt' or not isinstance(exc.reason,ssl.SSLCertVerificationError):raise
        # Windows' native TLS chain builder can retrieve missing intermediates.
        # Certificate and hostname validation remain enabled; never use SkipCertificateCheck.
        script = '''$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new();
        $r=Invoke-WebRequest -Uri $env:TRADINGAI_FEED_URL -UseBasicParsing -TimeoutSec 15;
        if ($r.BaseResponse.ResponseUri.Host -notin ($env:TRADINGAI_FEED_HOSTS -split ',')) {throw 'Unexpected redirect'};
        if ($r.RawContentLength -gt 2000000) {throw 'Oversized feed'};
        [Console]::Write($r.Content)'''
        env={**os.environ,'TRADINGAI_FEED_URL':spec['url'],'TRADINGAI_FEED_HOSTS':','.join(spec['hosts'])}
        result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],
            env=env,capture_output=True,timeout=25,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        return result.stdout

def clean(value):
    return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',value or ''))).strip()[:500]

def parse_feed(raw, source, now):
    if len(raw)>2_000_000 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Unsafe or oversized XML')
    root=ET.fromstring(raw)
    nodes=root.findall('.//item')
    if not nodes:raise ValueError('No RSS items; unsupported or empty response')
    result=[]; rejected=0
    for node in nodes[:300]:
        try:
            title=clean(node.findtext('title'))
            url=(node.findtext('link') or '').strip()
            parsed=urlsplit(url)
            if parsed.scheme!='https' or parsed.hostname not in SOURCES[source]['hosts'] or not title:
                raise ValueError('Invalid publisher link')
            pub=parsedate_to_datetime(node.findtext('pubDate'))
            if pub.tzinfo is None:raise ValueError('Missing timezone')
            pub=pub.astimezone(timezone.utc)
            if (pub-now).total_seconds()>120:raise ValueError('Future publication timestamp')
            item={'source':source,'title':title,'url':url,'published_at':pub.isoformat(),
                  'topic':SOURCES[source]['topic'], 'instruments':SOURCES[source]['instruments'],
                  'event_keyword':bool(EVENT_WORDS.search(title)), 'direction':'UNDETERMINED'}
            item['id']=digest([source,url,title,item['published_at']])
            result.append(item)
        except (ValueError,TypeError,AttributeError,OverflowError):rejected+=1
    if not result:raise ValueError('No valid dated publisher items')
    return result,rejected

def fetch(source,now):
    spec=SOURCES[source]
    try:
        raw=download(spec)
        items,rejected=parse_feed(raw,source,now)
        return source,items,{'status':'OK','rejected_items':rejected,'fetched_at':now.isoformat(),
                            'latest_publication':max(x['published_at'] for x in items),'url':spec['url']}
    except Exception as exc:
        return source,[],{'status':'UNAVAILABLE','reason':str(exc),'fetched_at':now.isoformat(),'url':spec['url']}

def eligible(item,as_of,max_age_hours=72):
    pub,seen=timestamp(item['published_at']),timestamp(item['first_seen_at'])
    return pub<=as_of and seen<=as_of and 0 <= (as_of-pub).total_seconds() <= max_age_hours*3600

def collect(root):
    root.mkdir(parents=True,exist_ok=True)
    with process_lock(root):
        now=utcnow(); db=sqlite3.connect(root/'news.sqlite3')
        try:
            db.execute('CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            health={}
            with ThreadPoolExecutor(max_workers=4) as pool:
                batches=list(pool.map(lambda s:fetch(s,now),SOURCES))
            with db:
                for source,items,status in batches:
                    health[source]=status
                    for item in items:
                        item['first_seen_at']=utcnow().isoformat()
                        db.execute('INSERT OR IGNORE INTO items VALUES(?,?)',(item['id'],canonical(item)))
            import json
            all_items=[json.loads(row[0]) for row in db.execute('SELECT payload FROM items')]
            cutoff=utcnow()
            recent=sorted([x for x in all_items if eligible(x,cutoff)],key=lambda x:timestamp(x['published_at']),reverse=True)
            for source,status in health.items():
                status['recent_items']=sum(x['source']==source for x in recent)
                if status['status']=='OK' and not status['recent_items']:status['status']='NO_RECENT_ITEMS'
            snapshot={'schema_version':'1.0','as_of':cutoff.isoformat(),'mode':'SHADOW_CONTEXT',
                'status':'PARTIAL' if any(x['status']=='UNAVAILABLE' for x in health.values()) else 'COLLECTED',
                'sources':health,'items':recent[:100], 'orders_authorized':False,
                'coverage_gaps':['No direct NBP/BoE feed yet','No full corporate earnings feed','RSS is delayed and incomplete; no historical news backfill'],
                'interpretation':'Topic and affected instrument mapping are heuristics. Headlines do not establish direction, surprise or trading permission.'}
            atomic_write(root/'latest.json',canonical(snapshot))
            atomic_write(root/'snapshots'/(cutoff.strftime('%Y%m%dT%H%M%S')+'.json'),canonical(snapshot))
            atomic_write(root/'latest.md',markdown(snapshot))
            return snapshot
        finally:db.close()

def summary(root,now):
    try:
        data=read_json(root/'latest.json')
        if not 0 <= (now-timestamp(data['as_of'])).total_seconds() <= 1800:
            return {'status':'STALE','mode':'SHADOW_CONTEXT','items':[],'sources':{},'orders_authorized':False}
        data['items']=[x for x in data['items'] if eligible(x,now)]
        return data
    except (Blocked,OSError,ValueError,KeyError,TypeError):
        return {'status':'UNAVAILABLE','mode':'SHADOW_CONTEXT','items':[],'sources':{},'orders_authorized':False}

def record_signal_context(journal,scan,now):
    data=summary(journal.root/'news',now)
    for candidate in scan:
        env=candidate.get('signal')
        if not env:continue
        key='news_evidence:'+digest(env)
        if journal.setting(key) is not None:continue
        alias=env['signal']['instrument']
        evidence={'signal_id':env['signal']['id'],'observed_at':now.isoformat(),
            'snapshot_at':data.get('as_of'),'status':data['status'],'mode':'SHADOW_CONTEXT',
            'sources':data.get('sources',{}),
            'items':[x for x in data['items'] if alias in x['instruments']],
            'affects_execution':False}
        journal.set_setting(key,evidence)
        journal.event('signal_news_context',evidence)

def markdown(data):
    lines=['## Kontekst wiadomości','',f"Status: {data['status']}; tryb obserwacyjny. News nie jest zgodą ani samodzielnym sygnałem BUY/SELL.",'',
           'Źródła: '+', '.join(k+': '+v['status'] for k,v in data.get('sources',{}).items()),'']
    for item in data.get('items',[])[:20]:
        title=item['title'].replace('[','(').replace(']',')').replace('<','&lt;').replace('>','&gt;')
        lines.append(f"- {item['published_at']} · {item['source']} · {', '.join(item['instruments'])}: [{title}]({item['url'].replace(')','%29')})")
    lines+=['','Brak wiadomości lub awaria źródła nie oznacza braku ryzyka. Brakuje bezpośrednich feedów NBP/BoE oraz pełnych danych o wynikach spółek. RSS nie jest serwisem natychmiastowych depesz.']
    return '\n'.join(lines)
