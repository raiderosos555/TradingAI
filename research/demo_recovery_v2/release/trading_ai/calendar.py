"""Read-only macro calendar. Missing/stale/incomplete data never means a clear market."""
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from .models import Blocked, fields, identifier, number, read_json

DEFAULTS = {"enabled":False, "max_age_seconds":900, "before_minutes":30, "after_minutes":15,
            "min_importance":3, "path":None, "instrument_currencies":{
                "GOLD":["USD"], "US500":["USD"], "US100":["USD"], "OIL":["USD"],
                "EURUSD":["EUR","USD"], "GBPUSD":["GBP","USD"], "EURPLN":["EUR","PLN"]}}


def calendar_config(config):
    c = {**DEFAULTS, **config.get("calendar",{})}
    fields(c, DEFAULTS.keys())
    if type(c["enabled"]) is not bool or c["path"] is not None and (not isinstance(c["path"],str) or not Path(c["path"]).is_absolute()):
        raise Blocked("Calendar enabled must be boolean and optional path must be absolute")
    for k,lo,hi in (("max_age_seconds",30,3600),("before_minutes",0,240),("after_minutes",0,240),("min_importance",1,3)):
        if type(c[k]) is not int or not lo <= c[k] <= hi:
            raise Blocked("Invalid calendar configuration: "+k)
    if not isinstance(c["instrument_currencies"],dict):
        raise Blocked("Calendar needs instrument/currency mapping")
    for alias, currencies in c["instrument_currencies"].items():
        identifier(alias)
        if not isinstance(currencies,list) or not currencies or any(not isinstance(x,str) or len(x)!=3 or not x.isalpha() or not x.isupper() for x in currencies):
            raise Blocked("Calendar currencies must be nonempty uppercase ISO codes")
    return c


def load_calendar(config, broker, now):
    c=calendar_config(config)
    path=Path(c["path"]) if c["path"] else Path(broker.paths()["data_path"])/"MQL5"/"Files"/"TradingAI"/f'calendar_{config["account_login"]}.json'
    d=read_json(path)
    if d.get("schema_version")!="1.0" or d.get("read_only") is not True or d.get("status")!="OK":
        raise Blocked("Calendar unavailable or provider returned incomplete data")
    if [d.get("account_login"),d.get("account_server")] != [config["account_login"],config["account_server"]]:
        raise Blocked("Calendar account/server mismatch")
    if d.get("server_minus_gmt_seconds") != config.get("broker_time_offset_seconds",0):
        raise Blocked("Calendar server time offset disagrees with broker adapter")
    for key in ("retrieved_at_utc","coverage_from_utc","coverage_until_utc"):
        number(d.get(key),"calendar."+key)
    if not -2 <= now.timestamp()-d["retrieved_at_utc"] <= c["max_age_seconds"]:
        raise Blocked("Calendar stale or dated in the future")
    if d["coverage_from_utc"] >= d["coverage_until_utc"]:
        raise Blocked("Calendar coverage interval invalid")
    if not isinstance(d.get("currencies"),list) or any(not isinstance(x,str) for x in d["currencies"]):
        raise Blocked("Calendar currency coverage missing")
    if not isinstance(d.get("events"),list) or not d["events"] or len(d["events"])>10000:
        raise Blocked("Calendar event list invalid")
    seen=set()
    for event in d["events"]:
        fields(event,("id","name","currency","importance","precision","start_utc","end_utc"),
               ("event_id","source_url","unit","multiplier","actual","forecast","previous"))
        identifier(event["id"])
        if event["id"] in seen: raise Blocked("Duplicate calendar event ID")
        seen.add(event["id"])
        if not isinstance(event["name"],str) or not event["name"] or len(event["name"])>1000:
            raise Blocked("Calendar event name invalid")
        if event["currency"] not in d["currencies"] or type(event["importance"]) is not int or not 0<=event["importance"]<=3:
            raise Blocked("Calendar event classification invalid")
        if event["precision"] not in {"exact","day"}:
            raise Blocked("Unknown calendar time precision")
        for key in ("start_utc","end_utc"): number(event[key],"event."+key)
        duration=event["end_utc"]-event["start_utc"]
        if (event["precision"]=="exact" and duration!=0) or (event["precision"]=="day" and duration!=86400):
            raise Blocked("Calendar event time range disagrees with precision")
        # Out-of-range scheduled events indicate a malformed or incorrect snapshot.
        if event["end_utc"] < d["coverage_from_utc"]-86400 or event["start_utc"] > d["coverage_until_utc"]+86400:
            raise Blocked("Calendar event outside declared coverage")
    return d


def assessment(config, broker, alias, now, until=None, data=None):
    c=calendar_config(config)
    if not c["enabled"]:
        return {"status":"DISABLED","instrument":alias,"events":[]}
    try:
        currencies=c["instrument_currencies"].get(alias)
        if not currencies: raise Blocked("No calendar currency mapping for instrument")
        d=data if data is not None else load_calendar(config,broker,now)
        if not set(currencies).issubset(d["currencies"]): raise Blocked("Calendar does not cover instrument currencies")
        start=now.timestamp(); end=until.timestamp() if until else start
        if end<start: raise Blocked("Calendar horizon ends before now")
        # Need both past events whose after-window persists, and future before-windows.
        if d["coverage_from_utc"] > start-c["after_minutes"]*60 or d["coverage_until_utc"] < end+c["before_minutes"]*60:
            raise Blocked("Calendar does not cover the complete exposure horizon")
        events=[e for e in d["events"] if e["currency"] in currencies and e["importance"]>=c["min_importance"]
                and e["start_utc"]-c["before_minutes"]*60 <= end and e["end_utc"]+c["after_minutes"]*60 >= start]
        return {"status":"BLOCKED" if events else "CLEAR", "instrument":alias,"events":events,
                "reason":"High-impact event window intersects exposure" if events else "No matching high-impact event in configured window",
                "source":d.get("source"),"retrieved_at_utc":d["retrieved_at_utc"]}
    except (Blocked,OSError,KeyError,TypeError,ValueError,AttributeError) as exc:
        return {"status":"UNAVAILABLE","instrument":alias,"events":[],"reason":str(exc)}


def require_clear(config,broker,alias,now,until=None):
    state=assessment(config,broker,alias,now,until)
    if state["status"] not in {"DISABLED","CLEAR"}:
        names=", ".join(e["name"] for e in state["events"])
        raise Blocked("Economic calendar: "+state["reason"]+("; "+names if names else ""))
    return state


def summary(config,broker,now):
    c=calendar_config(config)
    if not c["enabled"]: return {"status":"DISABLED","events":[],"instruments":[]}
    try:
        d=load_calendar(config,broker,now)
        # Report the next 24h and recent publications still inside the post-event window.
        events=[]
        for e in d["events"]:
            if e["end_utc"]+c["after_minutes"]*60 >= now.timestamp() and e["start_utc"] <= now.timestamp()+86400:
                events.append({**e,"time_warsaw":datetime.fromtimestamp(e["start_utc"],timezone.utc).astimezone(ZoneInfo("Europe/Warsaw")).isoformat()})
        return {"status":"READY","source":d.get("source"),"retrieved_at_utc":d["retrieved_at_utc"],
                "events":sorted(events,key=lambda e:e["start_utc"]),
                "instruments":[assessment(config,broker,alias,now,data=d) for alias in config["symbols"]],
                "before_minutes":c["before_minutes"],"after_minutes":c["after_minutes"],"min_importance":c["min_importance"]}
    except (Blocked,OSError,KeyError,TypeError,ValueError,AttributeError) as exc:
        return {"status":"UNAVAILABLE","reason":str(exc),"events":[],"instruments":[]}
