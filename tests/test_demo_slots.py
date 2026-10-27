import copy
import json
import tempfile
import unittest
from pathlib import Path
from trading_ai.models import Blocked, load_config


class DemoSlotConfigurationTests(unittest.TestCase):
    def check(self, mode, slots, valid):
        c = json.loads((Path(__file__).resolve().parents[1]/'examples/config.demo.example.json').read_text())
        c.pop('runtime', None)
        c['mode'] = mode
        c['risk']['max_positions'] = slots
        original_risk = copy.deepcopy(c['risk'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'config.json'
            path.write_text(json.dumps(c))
            if valid:
                self.assertEqual(load_config(path)['risk'], original_risk)
            else:
                with self.assertRaises(Blocked):
                    load_config(path)

    def test_demo_accepts_seven_without_changing_risk(self):
        self.check('DEMO', 7, True)

    def test_non_demo_cap_preserved(self):
        for mode in ('LIVE', 'DRY_RUN'):
            self.check(mode, 2, True)
            self.check(mode, 3, False)

    def test_invalid_demo_limits_rejected(self):
        for slots in (0, -1, 8, 2.5, True, '7'):
            self.check('DEMO', slots, False)
