import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import demo_smoke_test as demo
from trading_ai.models import Blocked


class DemoProfileConsentTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / 'state').mkdir()
        (self.root / 'docs').mkdir()
        p = patch.object(demo, 'ROOT', self.root)
        p.start(); self.addCleanup(p.stop)
        p = patch.object(demo, 'load_config', return_value={})
        p.start(); self.addCleanup(p.stop)

    def test_gold_consent_cannot_authorize_us500(self):
        (self.root / 'state/demo-test-consent.json').write_text(json.dumps({'plan_sha256': 'gold'}))
        with patch.object(demo, 'MT5Broker') as broker:
            with self.assertRaises(FileNotFoundError):
                demo.main(execute=True, instrument='US500')
            broker.assert_not_called()

    def test_changed_us500_document_blocks_before_terminal_connection(self):
        (self.root / 'state/demo-us500-test-consent.json').write_text(json.dumps({'plan_sha256': 'old'}))
        (self.root / 'docs/demo-us500-test-plan.md').write_text('changed scope', encoding='utf-8')
        with patch.object(demo, 'MT5Broker') as broker:
            with self.assertRaisesRegex(Blocked, 'changed after operator approval'):
                demo.main(execute=True, instrument='US500')
            broker.assert_not_called()

    def test_unsupported_profile_cannot_connect(self):
        with patch.object(demo, 'MT5Broker') as broker:
            with self.assertRaisesRegex(Blocked, 'Unsupported'):
                demo.main(execute=True, instrument='EURUSD')
            broker.assert_not_called()

    def test_test_risk_rejects_cross_contract_request_after_base_gate(self):
        risk = demo.TestRisk({}, None, None, test_symbol='US500.pro')
        request = {'action': 1, 'type': 1, 'symbol': 'GOLD.pro', 'volume': .001}
        with patch.object(demo.RiskManager, 'prepare_open', return_value=(request, {'risk_cash': 1})):
            with self.assertRaisesRegex(Blocked, 'approved DEMO test scope'):
                risk.prepare_open({})

    def test_test_risk_retains_five_pln_cap_on_us500(self):
        risk = demo.TestRisk({}, None, None, test_symbol='US500.pro')
        request = {'action': 1, 'type': 1, 'symbol': 'US500.pro', 'volume': .001}
        with patch.object(demo.RiskManager, 'prepare_open', return_value=(request, {'risk_cash': 5.01})):
            with self.assertRaisesRegex(Blocked, 'approved DEMO test scope'):
                risk.prepare_open({})
