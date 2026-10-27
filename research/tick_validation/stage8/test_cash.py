import unittest
from cash import diagnostic_profit,historical_net

class CashTests(unittest.TestCase):
    def calc(self,side='BUY',entry=100,exit=100.1,**kwargs):
        return diagnostic_profit(side,entry,exit,.001,50,3.89,3.97,**kwargs)
    def test_rounding_in_profit_currency_changes_small_lot_result(self):
        self.assertEqual(self.calc(round_profit_currency=True)['profit_account'],'0.04')
        self.assertEqual(self.calc(round_profit_currency=False)['profit_account'],'0.02')
    def test_negative_profit_uses_ask_and_half_away_from_zero(self):
        r=self.calc(exit=99.9,round_profit_currency=True)
        self.assertEqual(r['gross_profit_currency_converted'],'-0.01')
        self.assertEqual(r['profit_account'],'-0.04');self.assertEqual(r['conversion_side'],'ASK')
    def test_sell_sign_correct(self):
        self.assertEqual(self.calc(side='SELL',exit=99.9,round_profit_currency=True)['profit_account'],'0.04')
    def test_smaller_than_half_cent_can_round_to_zero(self):
        self.assertEqual(self.calc(exit=100.09,round_profit_currency=True)['profit_account'],'0.00')
    def test_missing_cost_inputs_not_defaulted_to_zero(self):
        policy=dict(historical_verified=True,evidence_id='SYNTHETIC',valid_from_raw_ms=0,valid_until_raw_ms=100)
        with self.assertRaises(ValueError):historical_net(policy,1,commission=None,swap=0,fee=0)
    def test_current_diagnostic_policy_not_accepted_as_historical(self):
        with self.assertRaisesRegex(ValueError,'not verified'):historical_net({'historical_verified':False},1,commission=0,swap=0,fee=0)
    def test_validity_range_not_extrapolated(self):
        policy=dict(historical_verified=True,evidence_id='SYNTHETIC',valid_from_raw_ms=0,valid_until_raw_ms=100)
        with self.assertRaisesRegex(ValueError,'outside'):historical_net(policy,100,commission=0,swap=0,fee=0)
    def test_crossed_fx_rejected(self):
        with self.assertRaises(ValueError):diagnostic_profit('BUY',100,101,.1,50,4,3,True)
    def test_partial_closes_round_independently_not_after_summing(self):
        from decimal import Decimal
        partial=Decimal(diagnostic_profit('BUY',100,99.1,.001,50,3.89,3.97,True)['profit_account'])
        full=Decimal(diagnostic_profit('BUY',100,99.1,.002,50,3.89,3.97,True)['profit_account'])
        self.assertEqual(partial*2,Decimal('-.40'));self.assertEqual(full,Decimal('-.36'))

if __name__=='__main__':unittest.main()
