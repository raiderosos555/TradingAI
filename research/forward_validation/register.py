"""One-time preregistration, before prospective outcome inspection."""
import hashlib,json,shutil,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
from collector import ROOT,A,save,hashfile

def main():
    root=ROOT/'state/forward_validation/cohort-20261026-v1'
    if (root/'protocol.v1.json').exists():raise SystemExit('Already registered; do not overwrite')
    root.mkdir(parents=True,exist_ok=True);frozen=root/'frozen';frozen.mkdir(exist_ok=True)
    cfg=json.loads((ROOT/'state/runtime/effective-config.json').read_text())
    if cfg['mode']!='DEMO' or cfg['live_enabled'] or cfg['live_allowlist']:raise ValueError('DEMO only')
    save(frozen/'effective-config.json',cfg)
    sources={}
    for path in sorted((ROOT/'trading_ai').glob('*.py')):
        dest=frozen/'trading_ai'/path.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(path,dest)
        sources[str(dest.relative_to(root))]=hashfile(dest)
    code={}
    for path in list(A.glob('*.py'))+[ROOT/'research/forward_context/archive.py']:
        rel=path.relative_to(ROOT);code[str(rel)]=hashfile(path)
        dest=frozen/'collector'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    registered=datetime.now(timezone.utc)
    start=(registered+timedelta(days=1)).replace(hour=8,minute=0,second=0,microsecond=0)
    end=start+timedelta(hours=8)
    protocol=dict(schema_version=1,id=root.name,registered_at=registered.isoformat(),mode='SHADOW',orders_authorized=False,
        first_window=dict(start_utc=start.isoformat(),end_utc=end.isoformat(),
            selection='NEXT UTC DAY 08:00-16:00 fixed before results; preserve failed windows; never replace because of PnL'),
        follow_on='All subsequent weekdays 08:00-16:00 UTC recorded, including blocked and zero-trade windows; no outcome-based selection',
        strategies=['local_breakout_v1','local_false_breakout_v1'],configuration_sha256=hashfile(frozen/'effective-config.json'),
        strategy_source_hashes=sources,collector_hashes=code,
        entry_selection='All seven configured instruments and both existing local strategies; unchanged parameters; no winner selection',
        statistics=dict(primary='Net account return after observed spread, commissions, fees and swap; all scheduled windows',
            secondary=['Profit Factor','expectancy in initial R','maximum drawdown','signal/entry/rejection counts','DEMO vs replay price/cost/management differences'],
            first_window_is_mechanical_validation=True,first_inference_not_before_sessions=60,
            first_inference_not_before_closed_trades=100,inference_method='Predeclared day-block bootstrap of net daily returns; confidence interval includes all days; no repeated profit-based stopping',
            caveat='Thresholds are minimums, not statistical power proof. No automatic edge claim or promotion.'),
        cadence=dict(context_seconds=5,ticks_seconds=60,contract_seconds=60,broker_deals_seconds=60,journal_seconds=30,
            closed_bars_seconds=3600,host_clock_seconds=300),
        context_sources={
            'calendar':dict(kind='calendar',path='C:/Users/EXAMPLE_USER/AppData/Roaming/MetaQuotes/Terminal/EXAMPLE_TERMINAL/MQL5/Files/TradingAI/calendar_123456789.json',max_age_seconds=900,account=[cfg['account_login'],cfg['account_server']]),
            'news':dict(kind='news',path=str(ROOT/'state/news/latest.json'),max_age_seconds=1800),
            'effective_config':dict(kind='config',path=str(ROOT/'state/runtime/effective-config.json'),max_age_seconds=None),
            'runtime':dict(kind='runtime',path=str(ROOT/'state/runtime/engine-status.json'),max_age_seconds=30)},
        safety=dict(active_engine_changes=False,quote_fix_deployed=False,can_send_orders=False,disk_reserve_gib=10,
            timeout_seconds=50,on_missing_data='Record and block acceptance; never synthesize or carry a stale quote',
            task_requires_logged_in_user_and_MT5=True),
        raw_time='Retain raw broker coordinates; corroboration is forward only, never retroactive to October 22',
        exact_engine_inputs='Not instrumented in active DEMO; poll receipts and journal are preserved, limitation explicit',
        initial_positions='Snapshot actual account; do not force-close or assume flat; current replay flat-only gate remains',
        execution_model='Existing isolated integrated_replay core; real-run acceptance requires UTC, costs, chronology, initial-state and as-of-context validation',
        historical_data_class='All previously observed history exploratory; setup-day data calibration, not confirmatory',
        external_briefing_authority='NONE; SHADOW context cannot authorize orders')
    save(root/'protocol.v1.json',protocol)
    print(root)

if __name__=='__main__':main()
