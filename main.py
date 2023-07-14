from req_import import *
from helpers import *
from Position import *
from Portfolio import *

def plot_cols(dfs, x_col, y_cols, title, strikes):
    if not isinstance(dfs, list):
        dfs = [dfs]
    fig, axs = plt.subplots(len(y_cols), figsize=(10, 5 * len(y_cols)))
    for i in range(len(y_cols)):
        [df.plot(x=x_col, y=y_cols[i], ax=axs[i]) for df in dfs]
        if y_cols[i] == 'SPX' and len(strikes) > 0:
            for s in strikes:
                axs[i].axhline(y=s, color='r', linestyle='--')
        if i != len(y_cols) - 1:
            axs[i].set_xlabel('')
            axs[i].set_xticklabels([])
    fig.suptitle(title)
    plt.show()

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
                  buy_sell='Sell',
                  entry_side='Far',
                  relative_strike_pct=-0.01,
                  relative_expiration_months=2,
                  mtm_side='Mid',
                  exit_date=None)

    p3 = Position(entry_date='2021-02-01',
                  call_put='Call',
                  buy_sell='Buy',
                  entry_side='Far',
                  relative_strike_pct=-0.02,
                  relative_expiration_months=2,
                  mtm_side='Mid',
                  exit_date=None)

    strat_1 = Portfolio(start_date='2021-02-01',
                          end_date='2021-03-23',
                          positions=[p1],
                          shares=[1])
    strat_2 = Portfolio(start_date='2021-02-01',
                          end_date='2021-03-23',
                          positions=[p2],
                          shares=[1])
    strat_3 = Portfolio(start_date='2021-02-01',
                        end_date='2021-03-23',
                        positions=[p2, p3],
                        shares=[1, 1])

    # daily_stats = strat_1.run_backtest()
    # plot_cols(daily_stats,
    #           'date', ['SPX', 'PnL'],
    #           'Startegy 1: SPX and PnL',
    #           strikes=[3810])
    # #input("Press Enter to continue...")
    #
    # daily_stats = strat_2.run_backtest()
    # plot_cols(daily_stats,
    #           'date', ['SPX', 'PnL', 'iv'],
    #           'Startegy 2: SPX, PnL, and IV',
    #           strikes=[3810])
    #input("Press Enter to continue...")
    #
    # daily_stats = strat_3.run_backtest()
    # plot_cols(daily_stats,
    #           'date', ['SPX', 'PnL', 'delta', 'iv'],
    #           'Startegy 3: SPX, PnL, Delta and IV',
    #           strikes=[3810, 3850])

    stats = [strat_1.run_backtest() , strat_2.run_backtest()]
    plot_cols(stats,
                'date', ['SPX', 'iv', 'PnL', 'delta', 'gamma', 'theta', 'vega'],
                'Startegy 1 and 2: SPX, IV, PnL, Greeks',
                strikes=[3810])

