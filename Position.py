import pandas as pd

from req_import import *
from helpers import *

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

    def reset(self):
        self.active_position = None
        self.active_position_expiry = None
        self.entry_price = None
        self.exit_price = None

    def _enter_position(self, curr_data):
        underlying_px = curr_data['adjusted_close'].values[0]
        strike = underlying_px * (
            1 - self.relative_strike_pct if self.call_put == 'Call' else 1 + self.relative_strike_pct)
        strike = base_round(strike, base=5) #TODO: make this work for any K increment
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
        if self.entry_side == "Mid":
            self.exit_price = (option['bid'] + option['ask']) / 2
        elif self.entry_side == 'Far':
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

    def _get_pnl(self, curr_data):
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
        return pnl

    def _days_to_expiry(self, curr_date):
        if self.active_position_expiry is None:
            return 0
        else:
            return (self.active_position_expiry - curr_date).days

    def _get_option_stats(self, curr_data):
        pnl = self._get_pnl(curr_data)
        if self.active_position is None:
            return {'value': 0, 'PnL': pnl, 'iv': 0,'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}

        option = curr_data.query("option_symbol == @self.active_position").to_dict('records')[0]
        price = (option['bid'] + option['ask']) / 2
        S = option['adjusted_close']
        K = option['strike']
        t = self._days_to_expiry(option['date']) / 365
        r = 0.00

        intrinsic = max(S - K, 0) if self.call_put == 'Call' else max(K - S, 0)
        if price < intrinsic:
            print(f"Below intrinsic: {self.active_position} {self.call_put} {S} {K} {t} {r} {price}")
            print("Setting price to ask")
            price = option['ask']

        implied_vol = iv(price, S, K, t, r, 'c' if self.call_put == 'Call' else 'p')
        implied_delta = delta('c' if self.call_put == 'Call' else 'p', S, K, t, r, implied_vol)
        implied_gamma = gamma('c' if self.call_put == 'Call' else 'p', S, K, t, r, implied_vol)
        implied_theta = theta('c' if self.call_put == 'Call' else 'p', S, K, t, r, implied_vol)
        implied_vega = vega('c' if self.call_put == 'Call' else 'p', S, K, t, r, implied_vol)
        return {'value': price, 'PnL': pnl, 'iv': implied_vol, 'delta': implied_delta, 'gamma': implied_gamma,
                'theta': implied_theta, 'vega': implied_vega}

    def process_date(self, dt: datetime.date, curr_data: pd.DataFrame):
        if self.active_position is None:
            if dt < self.entry_date:
                return {'value': 0, 'PnL': 0, 'iv': 0,'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
            elif self.exit_price is not None:
                return {'value': 0, 'PnL': self._get_pnl(curr_data), 'iv': 0,'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}

            assert dt == self.entry_date, "Have not processed entry date yet!"
            self._enter_position(curr_data)
        elif dt == self.active_position_expiry:
            self._expire_position(curr_data)
        elif dt == self.exit_date:
            self._exit_position(curr_data)
        else:
            assert dt > self.entry_date and dt < self.exit_date, "Invalid date for an active position!"

        stats = self._get_option_stats(curr_data)
        return stats

    def __str__(self):
        return self.active_position