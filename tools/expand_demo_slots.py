"""Apply the operator-authorized 2 -> 7 DEMO slot change; no broker calls.

Preserves risk budgets, contract lot caps, clocks, and frozen research inputs.
The runtime reloads the configuration and its matching authorization. A race
across the file/SQLite boundary fails closed until the next runtime iteration.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trading_ai.journal import Journal, atomic_write
from trading_ai.models import canonical, load_config, utcnow
from trading_ai.runtime import configuration_hash


def main():
    path = ROOT / 'config.demo.json'
    before = load_config(path)
    assert before['mode'] == 'DEMO' and not before['live_enabled'] and not before['live_allowlist']
    assert before['risk']['max_positions'] == 2
    assert [before['risk'][k] for k in ('max_trade_pct', 'max_total_pct', 'max_daily_loss_pct')] == [.1, .2, .5]
    assert len(before['symbols']) == 7
    after = copy.deepcopy(before)
    after['risk']['max_positions'] = 7
    audit = ROOT / 'state/config-migrations/demo-slots-20261026-validated'
    audit.mkdir(parents=True, exist_ok=False)
    atomic_write(audit/'config-candidate.json', json.dumps(after, indent=2))
    assert load_config(audit/'config-candidate.json') == after
    assert (ROOT/'state/runtime/DISABLED').exists(), 'Apply during controlled runtime restart'
    j = Journal(ROOT / 'state')
    try:
        key = 'runtime_authorization:' + before['runtime']['authorization_id']
        auth = j.setting(key)
        assert auth and auth['config_hash'] == configuration_hash(before)
        assert not j.setting('runtime_revoked') and not (ROOT/'state/runtime/REVOKED').exists()
        updated = copy.deepcopy(auth)
        updated.update(config_hash=configuration_hash(after), revised_at=utcnow().isoformat(),
            revision_reason='Operator permits additional DEMO positions when valid entries exist; risk budgets unchanged',
            previous_config_hash=auth['config_hash'],
            revision_operator_source='na demo jezeli jest taka potrzeba to nie musimy miec tylko maksymalnie 2 pozycji jesli sa widoczne wejscia to niech otwiera pozycje')
        for name, data in [('config-before', before), ('config-after', after), ('authorization-before', auth), ('authorization-after', updated)]:
            atomic_write(audit / (name+'.json'), json.dumps(data, indent=2, ensure_ascii=False))
        # No policy or gate is disabled during reload. Stale config/auth pairs
        # cannot authorize an order; existing broker SL/TP remain in place.
        with j.db:
            j.db.execute('UPDATE settings SET value=? WHERE key=?', (canonical(updated), key))
            atomic_write(path, json.dumps(after, indent=2))
        atomic_write(ROOT/'state/runtime-authorization.json', canonical(updated))
        result = dict(at=utcnow().isoformat(), change={'risk.max_positions': [2,7]},
            previous_hash=configuration_hash(before), config_hash=configuration_hash(after),
            risk_budgets_unchanged=True, frozen_research_unchanged=True,
            quote_fix_deployed=False, orders_sent_by_migration=0)
        j.event('operator_config_migration', result)
        atomic_write(audit/'result.json', canonical(result))
        assert configuration_hash(load_config(path)) == j.setting(key)['config_hash']
        print(json.dumps(result, indent=2))
    finally:
        j.close()


if __name__ == '__main__':
    main()
