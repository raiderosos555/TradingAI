"""Explicit diagnostic cash arithmetic. Historical use requires separate evidence."""
from decimal import Decimal,ROUND_HALF_UP

def dec(value):
    if value is None or isinstance(value,bool):raise ValueError('Explicit finite number required')
    number=Decimal(str(value))
    if not number.is_finite():raise ValueError('Explicit finite number required')
    return number
def rounded(value,digits):
    if type(digits) is not int or not 0<=digits<=8:raise ValueError('Invalid currency precision')
    return value.quantize(Decimal(1).scaleb(-digits),rounding=ROUND_HALF_UP)

def diagnostic_profit(side,entry,exit,volume,contract_size,bid,ask,round_profit_currency,
                      profit_digits=2,account_digits=2,fx_digits=4):
    if side not in {'BUY','SELL'} or type(round_profit_currency) is not bool:raise ValueError('Explicit side/rounding policy required')
    entry,exit,volume,size,bid,ask=map(dec,(entry,exit,volume,contract_size,bid,ask))
    if min(entry,exit,volume,size,bid,ask)<=0 or bid>ask:raise ValueError('Invalid price, size or FX quote')
    bid,ask=rounded(bid,fx_digits),rounded(ask,fx_digits)
    gross=(exit-entry)*volume*size*(1 if side=='BUY' else -1)
    conversion_amount=rounded(gross,profit_digits) if round_profit_currency else gross
    fx=bid if gross>=0 else ask
    return dict(gross_profit_currency_unrounded=str(gross),gross_profit_currency_converted=str(conversion_amount),
                conversion_side='BID' if gross>=0 else 'ASK',fx=str(fx),profit_account=str(rounded(conversion_amount*fx,account_digits)))

def historical_net(policy,raw_ms,*,commission,swap,fee,**inputs):
    # Deliberately fail closed with the actual evidence currently available.
    if policy.get('historical_verified') is not True or not policy.get('evidence_id'):
        raise ValueError('Historical contract/conversion/rounding policy not verified')
    if not policy['valid_from_raw_ms']<=raw_ms<policy['valid_until_raw_ms']:
        raise ValueError('Historical policy outside evidenced interval')
    costs=[dec(x) for x in [commission,swap,fee]]  # signed cash entries, never implicit zero
    result=diagnostic_profit(**inputs)
    result['net_account']=str(dec(result['profit_account'])+sum(costs))
    return result
