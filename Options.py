from req_import import *
N_prime = norm.pdf
N = norm.cdf

class OptionFromPrice():
    _MAX_TRY = 1000
    _ONE_CENT = 0.01

    @validate_call
    def __init__(
        self, c_p: Literal['C', 'P'], asset_price, option_market_price, strike_price,
        time_to_expiration, risk_free_rate
            ):
        self.c_p = c_p
        self.asset_volatility = self.find_iv_newton(S=asset_price,
                                                    K=strike_price,
                                                    r=risk_free_rate,
                                                    t=time_to_expiration,
                                                    market_price=option_market_price)
        inputs = np.array([asset_price, self.asset_volatility, strike_price, time_to_expiration, risk_free_rate])
        self.option = EuropeanCall(inputs) if c_p == 'C' else EuropeanPut(inputs)

    @staticmethod
    def vega(S, K, r, t, sigma):
        d1 = (log(S / K) + (r + sigma ** 2 / 2) * t) / (sigma * sqrt(t))
        return S * N_prime(d1) * sqrt(t)

    @staticmethod
    def _vega_d1(S, d1, t):
        return S * N_prime(d1) * sqrt(t)

    def find_iv_newton(self, S, K, r, t, market_price):
        best_guess = np.inf
        sigma_guess = 0.2
        for i in range(OptionFromPrice._MAX_TRY):
            if self.c_p == 'C':
                bs_price = EuropeanCall.call_price(S, sigma_guess, K, t, r)
            else:
                bs_price = EuropeanPut.put_price(S, sigma_guess, K, t, r)
            diff = market_price - bs_price
            if abs(diff) < abs(market_price - best_guess):
                best_guess = bs_price
            if abs(diff) < OptionFromPrice._ONE_CENT:
                return sigma_guess
            d1 = (log(S / K) + (r + sigma_guess ** 2 / 2) * t) / (sigma_guess * sqrt(t))
            vega = OptionFromPrice._vega_d1(S, d1, t)
            sigma_guess += diff / vega
        return bs_price

class EuropeanCall():
    @staticmethod
    def call_price(S, sigma, K, t, r=0):
        b = exp(-r * t)#.astype('float')
        d1 = log(S / (b * K)) + (((sigma ** 2) * t) / 2)
        d1 = d1 / (sigma * sqrt(t))
        d2 = np.log(S / (b * K)) - ((sigma ** 2) * t) / 2
        d2 = d2 / (sigma * (t ** .5))
        z1 = N(d1) * S
        z2 = ((b * K) * N(d2))
        return z1 - z2


    def __init__(
        self, inputs
            ):

        self.asset_price = inputs[0]
        self.asset_volatility = inputs[1]
        self.strike_price = inputs[2]
        self.time_to_expiration = inputs[3]
        self.risk_free_rate = inputs[4]
        self.price = self.call_price(self.asset_price, self.asset_volatility, self.strike_price,
                                     self.time_to_expiration, self.risk_free_rate)

        self.gradient_func = grad(self.call_price, (0, 1, 3))
        self.delta, self.vega, self.theta = self.gradient_func(inputs[0], inputs[1], inputs[2], inputs[3], inputs[4])
        self.theta /= -365
        self.vega /= 100

    @property
    def _greeks(self):
        return self.delta, self.vega, self.theta


class EuropeanPut():
    @staticmethod
    def put_price(S, sigma, K, t, r=0):
        b = exp(-r * t)#.astype('float')
        d1 = (log((b * K) / S)) + (((sigma ** 2) * t) / 2)
        d1 = d1 / (sigma * sqrt(t))
        d2 = (log((b * K) / S)) - (((sigma ** 2) * t) / 2)
        d2 = d2 / (sigma * (t ** .5))
        z1 = ((b * K) * N(d1))
        z2 = S * N(d2)
        return z1 - z2

    def __init__(
        self, inputs
            ):
        self.asset_price = inputs[0]
        self.asset_volatility = inputs[1]
        self.strike_price = inputs[2]
        self.time_to_expiration = inputs[3]
        self.risk_free_rate = inputs[4]
        self.price = self.put_price(self.asset_price, self.asset_volatility, self.strike_price, self.time_to_expiration,
                                    self.risk_free_rate)

        self.gradient_func = grad(self.put_price, (0, 1, 3)) #strike price, risk_free_rate does not change
        self.delta, self.vega, self.theta = self.gradient_func(inputs[0], inputs[1], inputs[2], inputs[3], inputs[4])
        self.theta /= -365
        self.vega /= 100


#Usage: def __init__(
#        self, c_p: Literal['C', 'P'], asset_price, option_market_price, strike_price,
#        time_to_expiration, risk_free_rate
#            ):

if __name__=='__main__':
    call = OptionFromPrice(c_p='C',
                  asset_price=3932.59,
                  option_market_price=10,
                  strike_price=105,
                  time_to_expiration=365/365,
                  risk_free_rate=0.00)

    #option = EuropeanCall(inputs.astype('float'))
    #print(option.find_iv_newton())

    print(call.option.asset_volatility, call.option.delta, call.option.vega, call.option.theta, call.option.price)