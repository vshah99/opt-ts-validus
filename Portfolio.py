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
        self.shares_list = shares

    def run_backtest(self):
        for d in self._valid_date_list:
            d = pd.to_datetime(d)
            if self.start_date > d or self.end_date < d:
                continue

            data_slice = self.data.query("date == @d")
            print(d)
            daily_stats = {'PnL': 0}
            for p, s in zip(self.position_list, self.shares_list):
                val = p.process_date(d, data_slice)
                if p.active_position is not None:
                    print(f"Security {p}:\n",
                          f"\tNumber of Shares: {s}\n",
                          f"\tCumulative PnL per Share: {val['PnL']}")
                daily_stats['PnL'] += s * (val['PnL'])
            print(f"Cumulative Total PnL: {daily_stats['PnL']}\n")
