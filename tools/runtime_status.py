"""Read-only operational status; never sends orders or touches authorization."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from trading_ai.broker import MT5Broker
from trading_ai.calendar import summary
from trading_ai.journal import Journal
from trading_ai.models import load_config, read_json, timestamp, utcnow


def main():
    now = utcnow()
    c = load_config(ROOT/'config.demo.json')
    j = Journal(ROOT/'state')
    b = None
    try:
        proof = j.setting('runtime_clock')
        if (proof and proof.get('account') == [c['account_login'],c['account_server']]
                and 0 <= (now-timestamp(proof['at'])).total_seconds() <= 30):
            c['broker_time_offset_seconds'] = proof['offset']
        status = {'at':now.isoformat(), 'mode':c['mode'], 'window':c['runtime'],
                  'stop':(ROOT/'state/STOP').exists(), 'disabled':(ROOT/'state/runtime/DISABLED').exists(),
                  'revoked':bool(j.setting('runtime_revoked')) or (ROOT/'state/runtime/REVOKED').exists(),
                  'quarantined':j.uncertain(), 'roles':{}}
        for role in ['baseline','engine']:
            path = ROOT/'state/runtime'/(role+'-status.json')
            value = read_json(path) if path.exists() else {'status':'NOT_STARTED'}
            if 'at' in value:
                value['heartbeat_age_seconds'] = (now-timestamp(value['at'])).total_seconds()
                value['heartbeat_fresh'] = -2 <= value['heartbeat_age_seconds'] <= 90
            status['roles'][role] = value
        b = MT5Broker(c['terminal_path'],c.get('broker_time_offset_seconds',0))
        snap = b.snapshot()
        status['broker'] = {'connected':snap['terminal']['connected'], 'account':snap['account'],
                            'positions':len(snap['positions']), 'pending':len(snap['orders']),
                            'terminal_permissions':snap['terminal']}
        status['calendar'] = summary(c,b,now)
        status['day_start_current'] = (j.setting('day_start') or {}).get('date') == now.date().isoformat()
        print(json.dumps(status,indent=2,ensure_ascii=False))
    finally:
        if b:b.close()
        j.close()


if __name__ == '__main__':main()
