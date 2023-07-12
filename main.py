from req_import import *
from helpers import *
from Position import *
from Portfolio import *

if __name__ == '__main__':
    p1 = Position(entry_date='2021-02-01',
                  call_put='Call',
                  buy_sell='Sell',
                  entry_side='Far',
                  relative_strike_pct=-0.01,
                  relative_expiration_months=1,
                  mtm_side='Mid',
                  exit_date=None)

    p2 = Position(entry_date='2021-02-01',
                  call_put='Call',
                  buy_sell='Buy',
                  entry_side='Far',
                  relative_strike_pct=-0.02,
                  relative_expiration_months=1,
                  mtm_side='Mid',
                  exit_date=None)

    portfolio = Portfolio(start_date='2021-02-01',
                          end_date='2021-03-23',
                          positions=[p1, p2],
                          shares=[1, 1])

    portfolio.run_backtest()