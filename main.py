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
        axs[i].set_ylabel(y_cols[i])
    fig.suptitle(title)
    fig.tight_layout()
    fig.subplots_adjust(top=0.95)
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

    ######## Question 1 ########
    y = input("Enter (y/Y) to run Q1...")
    if y == 'y' or y == 'Y':
        daily_stats = strat_1.run_backtest()
        plot_cols(daily_stats,
                  'date', ['SPX', 'PnL'],
                  'Strategy 1: SPX and PnL',
                  strikes=[3810])


    ######## Question 2, 5 ########
    y = input("Enter (y/Y) to run Q2+5...")
    if y == 'y' or y == 'Y':
        daily_stats = strat_2.run_backtest()
        plot_cols(daily_stats,
                  'date', ['SPX', 'PnL', 'iv'],
                  'Strategy 2: SPX, PnL, and IV',
                  strikes=[3810])

    ######## Question 3, 4 ########
    y = input("Enter (y/Y) to run Q3+4...")
    if y == 'y' or y == 'Y':
        daily_stats = strat_3.run_backtest()
        plot_cols(daily_stats,
                  'date', ['SPX', 'PnL', 'delta'],
                  'Strategy 3: SPX, PnL, and Delta',
                  strikes=[3810, 3850])

    ######## Question 6 ########
    y = input("Enter (y/Y) to run Q6...")
    if y == 'y' or y == 'Y':
        stats = [strat_1.run_backtest() , strat_2.run_backtest()]
        plot_cols(stats,
                    'date', ['SPX', 'delta', 'gamma', 'theta', 'vega'],
                    'Strategy 1 and 2: SPX, IV, PnL, Greeks',
                    strikes=[3810])

        for greek in ['price', 'delta', 'gamma', 'theta', 'vega']:
            for p in [p1, p2]:
                x, y, S, K = p.plot_greek(greek, all_data=Portfolio.data)
                plt.plot(x, y, label=str(p))
            plt.axvline(x=S, color='r', linestyle='--', label='S_0')
            plt.axvline(x=K, color='g', linestyle='--', label='K')
            plt.legend()
            plt.title(f'{greek.title()} for 1 month and 2 month options')
            plt.xlabel('SPX Price')
            plt.ylabel(f'{greek.title()}')
            plt.show()

