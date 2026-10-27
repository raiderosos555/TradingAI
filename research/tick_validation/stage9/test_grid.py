import unittest
from grid import make_grid, stable_fx

class GridTests(unittest.TestCase):
    def setUp(self):
        self.info = dict(trade_tick_size='0.1', volume_min='0.001', volume_step='0.001', volume_max='0.02')
        self.quote = dict(bid=100, ask=100.3)
        self.config = dict(volume_step_increments=[0, 1, 9], price_tick_deltas=[-1, 1])

    def test_side_prices_and_grid(self):
        rows = make_grid(self.info, self.quote, self.config)
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0], dict(side='BUY', volume='0.001', entry='100.3', exit='100.2', delta_ticks=-1))
        self.assertEqual(rows[6], dict(side='SELL', volume='0.001', entry='100', exit='99.9', delta_ticks=-1))

    def test_volume_cap_no_invalid_calls(self):
        self.info['volume_max'] = '0.002'
        self.assertEqual({r['volume'] for r in make_grid(self.info, self.quote, self.config)}, {'0.001', '0.002'})

    def test_crossed_quote_rejected(self):
        self.quote['ask'] = 99
        with self.assertRaises(ValueError): make_grid(self.info, self.quote, self.config)

    def test_nonfinite_and_invalid_steps(self):
        for field, value in [('volume_min', 'NaN'), ('trade_tick_size', 0), ('volume_step', '-1'), ('volume_min', '.0015')]:
            info = dict(self.info, **{field: value})
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): make_grid(info, self.quote, self.config)

    def test_nonpositive_exit_rejected(self):
        self.config['price_tick_deltas'] = [-100000]
        with self.assertRaises(ValueError): make_grid(self.info, self.quote, self.config)

    def test_stability_requires_same_observation(self):
        q = dict(bid=3.89, ask=3.97, time_msc=123)
        self.assertTrue(stable_fx(q, dict(q)))
        self.assertFalse(stable_fx(q, dict(q, time_msc=124)))
        self.assertFalse(stable_fx(q, dict(q, ask=3.98)))
        self.assertFalse(stable_fx(None, q))

    def test_unstable_fx_excluded_without_fallback(self):
        from analyze import evaluate
        row = dict(side='BUY', entry='100', exit='101', volume='0.001', broker_profit=.4,
            fx_before={'USDPLN': dict(bid=3.89, ask=3.97, time_msc=123)},
            fx_after={'USDPLN': dict(bid=3.90, ask=3.98, time_msc=124)})
        capture = dict(account_currency='PLN', instruments=[dict(alias='TEST', symbol='TEST', status='OBSERVED',
            contract=dict(currency_profit='USD', trade_calc_mode=4), rows=[row])])
        result = evaluate(capture, dict(fx_candidates=['USDPLN'], round_profit_currency_hypotheses=[True]))
        c = result[0]['comparisons'][0]
        self.assertEqual((c['compared'], c['excluded'], c['matches']), (0, 1, 0))

    def test_direct_pln_has_no_fx_dependency(self):
        from analyze import evaluate
        row = dict(side='SELL', entry='4', exit='4.0001', volume='.01', broker_profit=-.1)
        capture = dict(account_currency='PLN', account_currency_digits=2,
            instruments=[dict(alias='TEST', symbol='TEST', status='OBSERVED', contract=dict(currency_profit='PLN',
                trade_calc_mode=0, trade_contract_size=100000), rows=[row])])
        result = evaluate(capture, dict(round_profit_currency_hypotheses=[False, True], currency_digits={'PLN':2}))
        self.assertEqual([c['matches'] for c in result[0]['comparisons']], [1,1])

    def test_unsupported_contract_does_not_guess_formula(self):
        from analyze import evaluate
        capture = dict(account_currency='PLN', instruments=[dict(alias='TEST', symbol='TEST', status='OBSERVED',
            contract=dict(currency_profit='USD', trade_calc_mode=2), rows=[])])
        result = evaluate(capture, {})
        self.assertEqual(result[0]['status'], 'UNSUPPORTED_CONTRACT')
        self.assertEqual(result[0]['comparisons'], [])

    def test_api_binary_representation_is_not_cash_difference(self):
        from analyze import reported_cash
        from decimal import Decimal
        self.assertEqual(reported_cash(-3.9699999999999998, 2), Decimal('-3.97'))
        self.assertEqual(reported_cash(3.5300000000000002, 2), Decimal('3.53'))

    def test_subcent_difference_is_not_silently_rounded(self):
        from analyze import reported_cash
        for value in [.105, .104, -.104]:
            with self.subTest(value=value), self.assertRaises(ValueError): reported_cash(value, 2)
