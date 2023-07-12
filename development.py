import pandas as pd

pd.set_option('display.max_columns', None)
import numpy as np
import pickle as pkl
import os
from typing import Optional, Literal, Any, List
from pydantic import validate_call, Field, validate_arguments
import re
from datetime import datetime


def load_and_preprocess(refresh=False) -> pd.DataFrame:
    pkl_fp = r"final_input.pkl"
    csv_fp = r"raw_input.csv"

    if os.path.exists(pkl_fp) and not refresh:
        df = pd.read_pickle(pkl_fp)
    else:
        df = pd.read_csv(csv_fp)

        # Remove all columns with only 1 value
        for col in df.columns:
            if len(df[col].unique()) == 1:
                df.drop(col, inplace=True, axis=1)
        # adjusted == unadjusted always, so we can drop the latter. Given we have
        if all(df['adjusted close'] == df['unadjusted']):
            df.drop(columns=['unadjusted'], inplace=True)
        # rename spaces with underscore for easier access: df.adjusted_close rather than df['adjusted close']
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('/', '_').str.lower()
        df['date'] = pd.to_datetime(df['date'])
        df['expiration'] = pd.to_datetime(df['expiration'])

        df.sort_values(['date', 'expiration', 'strike'], ascending=[True, True, True], inplace=True)
        df.to_pickle(pkl_fp)

    return df


_date_pattern = "^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$"


def parse_date(strdt, default="2021-04-30") -> datetime.date:
    if strdt is None:
        strdt = default
    if isinstance(strdt, str) and re.match(_date_pattern, strdt):
        return datetime.strptime(strdt, "%Y-%m-%d")
    raise ValueError("Invalid Date Format")


def base_round(x, base=5):
    return base * round(x / base)


class Position:
    @validate_call
    def __init__(self,
                 entry_date: str,
                 call_put: Literal['Call', 'Put'],
                 buy_sell: Literal['Buy', 'Sell'] = 'Buy',
                 entry_side: Literal['Far', 'Mid', 'Near'] = 'Far',
                 relative_strike_pct: float = Field(None, ge=-1, le=1),
                 relative_expiration_months: int = Field(None, ge=1),
                 mtm_side: Literal['Far', 'Mid', 'Near'] = 'Mid',
                 exit_date: Optional[str] = None):
        """
        This class is option position on SPX
        :param entry_date: The date we buy the option
        :param call_put: Either 'C' or 'P'
        :param entry_side: The price at which we enter 'Near' is near touch, 'Mid' is midpoint and 'Far' is far touch
        :param relative_strike_pct: negative for OTM, 0 for ATM and positive for ITM
        :param mtm_side: The price at which we mark-to-market. 'Near', 'Mid' or 'Far'
        :param exit_date: Date to exit the position (at the mtm_side). If the date is not provided or past expiration,
                            the option is held to expiration
        """
        self.entry_date = parse_date(entry_date)
        self.call_put = call_put
        self.buy_sell = buy_sell
        self.entry_side = entry_side
        self.relative_strike_pct = relative_strike_pct
        self.relative_expiration_months = relative_expiration_months
        self.mtm_side = mtm_side
        self.exit_date = parse_date(exit_date)

        self.active_position: Optional[str] = None
        self.active_position_expiry: Optional[datetime.date] = None
        self.entry_price: Optional[float] = None
        self.exit_price: Optional[float] = None

    def _enter_position(self, curr_data):
        underlying_px = curr_data['adjusted_close'].values[0]
        strike = underlying_px * (
            1 - self.relative_strike_pct if self.call_put == 'Call' else 1 + self.relative_strike_pct)
        strike = base_round(strike, base=5)
        expiration = curr_data.expiration.unique()[self.relative_expiration_months - 1]
        option = curr_data.query("strike==@strike and expiration==@expiration and call_put==@self.call_put[0]")
        assert len(option) == 1, "Multiple matching options"
        option = option.to_dict('records')[0]

        self.active_position = option['option_symbol']
        self.active_position_expiry = pd.to_datetime(option['expiration'])
        if self.entry_side == 'Mid':
            self.entry_price = (option['ask'] + option['bid']) / 2
        elif self.entry_side == 'Far':
            self.entry_price = option['ask'] if self.buy_sell == 'Buy' else option['bid']
        else:  # Near
            self.entry_price = option['bid'] if self.buy_sell == 'Buy' else option['ask']

        print(f"Entering position {self.buy_sell} {self.active_position} at px={self.entry_price}")

    def _exit_position(self, curr_data):
        option = curr_data.query("option_symbol == @self.active_position")
        if self.mtm_side == "Mid":
            self.exit_price = (option['bid'] + option['ask']) / 2
        elif self.mtm_side == 'Far':
            self.exit_price = option['bid'] if self.buy_sell == 'Buy' else option['ask']
        else:  # Near
            self.exit_price = option['ask'] if self.buy_sell == 'Buy' else option['bid']
        self.exit_price = self.exit_price.iloc[0]
        print(f"Exiting position {self.buy_sell} {self.active_position} at px={self.exit_price}")
        self.active_position = None
        self.active_position_expiry = None

    def _expire_position(self, curr_data):
        option = curr_data.query("option_symbol == @self.active_position")
        self.exit_price = ((option['adjusted_close'] - option['strike']) * (1 if self.call_put == 'Call' else -1)).iloc[
            0]
        self.exit_price = max(0, self.exit_price)
        print(f"Expiring position {self.buy_sell} {self.active_position} at px={self.exit_price}")
        self.active_position = None
        self.active_position_expiry = None

    def _get_stats(self, curr_data):
        if self.active_position is None:
            mark_px = self.exit_price
        else:
            option = curr_data.query("option_symbol == @self.active_position")
            if self.mtm_side == "Mid":
                mark_px = (option['bid'] + option['ask']) / 2
            elif self.mtm_side == 'Far':
                mark_px = option['bid'] if self.buy_sell == 'Buy' else option['ask']
            else:  # Near
                mark_px = option['ask'] if self.buy_sell == 'Buy' else option['bid']
            mark_px = mark_px.iloc[0]
        pnl = (mark_px - self.entry_price) * (1 if self.buy_sell == 'Buy' else -1)
        return {'PnL': pnl}

    def process_date(self, dt: datetime.date, curr_data: pd.DataFrame):
        if self.active_position is None:
            if dt < self.entry_date:
                return {'PnL': 0}
            elif self.exit_price is not None:
                return self._get_stats(curr_data)

            assert dt == self.entry_date, "Have not processed entry date yet!"
            self._enter_position(curr_data)
        elif dt == self.active_position_expiry:
            self._expire_position(curr_data)
        elif dt == self.exit_date:
            self._exit_position(curr_data)
        else:
            assert dt > self.entry_date and dt < self.exit_date, "Invalid date for an active position!"

        return self._get_stats(curr_data)

    def __str__(self):
        return self.active_position


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

from req_import import *
N_prime = norm.pdf
N = norm.cdf
from Options import *

def _vega_d1(S, d1, t):
    return S * N_prime(d1) * sqrt(t)

def find_iv_newton_call(S, K, r, t, market_price):
    best_guess = np.inf
    sigma_guess = 0.2
    for i in range(1000):
        bs_price = EuropeanCall.call_price(S, sigma_guess, K, t, r)
        diff = market_price - bs_price
        if abs(diff) < abs(market_price - best_guess):
            best_guess = bs_price
        if abs(diff) < 0.01:
            return sigma_guess
        d1 = (log(S / K) + (r + sigma_guess ** 2 / 2) * t) / (sigma_guess * sqrt(t))
        vega = _vega_d1(S, d1, t)
        sigma_guess += diff / vega
    return best_guess

if __name__ == '__main__':
    a = find_iv_newton_call(S=3932.59,
                   K=3810,
                   r=0,
                   t=0.00821917808219178,
                   market_price=122.05)

    print(a)
