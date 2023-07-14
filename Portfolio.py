from req_import import *
from helpers import *
from Position import *

class Portfolio:
    _min_date = parse_date('2021-02-01')
    _max_date = parse_date('2021-04-30')
    data = load_and_preprocess(refresh=True)
    _valid_date_list = data['date'].unique()

    @staticmethod
    def validate_positions(value: Any) -> Any:
        if len(value) > 0:
            return None
        raise ValueError("Position List must not be empty")

    def reset_positions(self):
        for p in self.position_list:
            p.reset()

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def __init__(self,
                 start_date: str,
                 end_date: str,
                 positions: List[Position],
                 shares: Optional[List[int]] = None):
        """

        :param positions: A list of positions
        """
        self.start_date = parse_date(start_date)
        self.end_date = parse_date(end_date)
        assert self._min_date <= self.start_date < self.end_date <= self._max_date, \
            "Start/End dates must be within range and sd<ed"
        self.validate_positions(positions)
        self.position_list = positions
        if shares is None:
            shares = [1] * len(positions)
        assert len(shares) == len(positions)
        assert all([s > 0 for s in shares]), "Shares must be positive. For short, use position init"
        self.shares_list = shares

    def run_backtest(self):
        all_days = []
        for d in self._valid_date_list:
            d = pd.to_datetime(d)
            if self.start_date > d or self.end_date < d:
                continue

            data_slice = self.data.query("date == @d")
            print(d)
            print("SPX Price: ", data_slice['adjusted_close'].values[0])
            daily_stats = {'date': d, 'SPX': data_slice['adjusted_close'].values[0], 'PnL': 0, 'iv': 0, 'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
            for p, s in zip(self.position_list, self.shares_list):
                if p.active_position is not None: print(f"Security {p}:")
                stats = p.process_date(d, data_slice)
                b_s_multiplier = 1 if p.buy_sell == 'Buy' else -1
                if p.active_position is not None:
                    print(f"\tNumber of Shares: {s} {'long' if p.buy_sell=='Buy' else 'short'}\n",
                          f"\tCumulative PnL per Share: {stats['PnL']}",
                          f"\tIV per Share: {stats['iv']}",
                          f"\tDelta per Share: {stats['delta'] * b_s_multiplier}",
                          f"\tGamma per Share: {stats['gamma'] * b_s_multiplier}",
                          f"\tVega per Share: {stats['vega'] * b_s_multiplier}",
                          f"\tTheta per Share: {stats['theta'] * b_s_multiplier}",)
                daily_stats['PnL'] += s * (stats['PnL'])
                daily_stats['iv'] += s * (stats['iv'] ** 2)
                daily_stats['delta'] += s * (stats['delta']) * b_s_multiplier
                daily_stats['gamma'] += s * (stats['gamma']) * b_s_multiplier
                daily_stats['theta'] += s * (stats['theta']) * b_s_multiplier
                daily_stats['vega'] += s * (stats['vega']) * b_s_multiplier
            daily_stats['iv'] = np.sqrt(daily_stats['iv'])

            print(f"Cumulative Total PnL: {daily_stats['PnL']}")
            print(f"Total IV: {daily_stats['iv']}")
            print(f"Total Delta: {daily_stats['delta']}")
            print(f"Total Gamma: {daily_stats['gamma']}")
            print(f"Total Theta: {daily_stats['theta']}")
            print(f"Total Vega: {daily_stats['vega']}")
            print("\n")
            all_days.append(daily_stats)
        all_days = pd.DataFrame(all_days)
        self.reset_positions()
        return all_days