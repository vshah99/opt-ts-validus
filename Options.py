from req_import import *
N_prime = norm.pdf

class Option(ABC):
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

    #
    # @abstractmethod
    # def price(
    #         self, asset_price, asset_volatility, strike_price,
    #         time_to_expiration, risk_free_rate
    # ):
    #     raise NotImplementedError

    @staticmethod
    def vega(S, K, r, t, sigma):
        d1 = (log(S / K) + (r + sigma ** 2 / 2) * t) / (sigma * sqrt(t))
        return S * N_prime(d1) * sqrt(t)

    @staticmethod
    def _vega_d1(S, d1, t):
        return S * N_prime(d1) * sqrt(t)

    def find_iv_newton(self, S, K, r, t, market_price):
        sigma_guess = 0.5
        for i in range(Option._MAX_TRY):
            if self.c_p == 'C':
                bs_price = EuropeanCall.call_price(S, sigma_guess, K, t, r)
            else:
                bs_price = EuropeanPut.put_price(S, sigma_guess, K, t, r)
            diff = market_price - bs_price
            if abs(diff) < Option._ONE_CENT:
                return sigma_guess
            d1 = (log(S / K) + (r + sigma_guess ** 2 / 2) * t) / (sigma_guess * sqrt(t))
            vega = Option._vega_d1(S, d1, t)
            sigma_guess += diff / vega
        return sigma_guess

class EuropeanCall():
    @staticmethod
    def call_price(
        asset_price, asset_volatility, strike_price,
        time_to_expiration, risk_free_rate
            ):
        b = np.exp(-risk_free_rate*time_to_expiration).astype('float')
        x1 = np.log(asset_price/(b*strike_price))
        x1 += (.5*(asset_volatility*asset_volatility)*time_to_expiration)
        x1 = x1/(asset_volatility*(time_to_expiration**.5))
        z1 = norm.cdf(x1)
        z1 = z1*asset_price
        x2 = np.log(asset_price/(b*strike_price)) - .5*(asset_volatility*asset_volatility)*time_to_expiration
        x2 = x2/(asset_volatility*(time_to_expiration**.5))
        z2 = norm.cdf(x2)
        z2 = b*strike_price*z2
        return z1 - z2

    def __init__(
        self, inputs
            ):

        self.asset_price = inputs[0]
        self.asset_volatility = inputs[1]
        self.strike_price = inputs[2]
        self.time_to_expiration = inputs[3]
        self.risk_free_rate = inputs[4]
        self.price = self.call_price(self.asset_price, self.asset_volatility, self.strike_price, self.time_to_expiration, self.risk_free_rate)

        self.gradient_func = grad(self.call_price, (0, 1, 3))
        self.delta, self.vega, self.theta = self.gradient_func(inputs[0], inputs[1], inputs[2], inputs[3], inputs[4])
        self.theta /= -365
        self.vega /= 100


class EuropeanPut():
    @staticmethod
    def put_price(
        asset_price, asset_volatility, strike_price,
        time_to_expiration, risk_free_rate
            ):
        b = np.exp(-risk_free_rate*time_to_expiration)
        x1 = np.log((b*strike_price)/asset_price) + .5*(asset_volatility*asset_volatility)*time_to_expiration
        x1 = x1/(asset_volatility*(time_to_expiration**.5))
        z1 = norm.cdf(x1)
        z1 = b*strike_price*z1
        x2 = np.log((b*strike_price)/asset_price) - .5*(asset_volatility*asset_volatility)*time_to_expiration
        x2 = x2/(asset_volatility*(time_to_expiration**.5))
        z2 = norm.cdf(x2)
        z2 = asset_price*z2
        return z1 - z2

    def __init__(
        self, inputs
            ):
        self.asset_price = inputs[0]
        self.asset_volatility = inputs[1]
        self.strike_price = inputs[2]
        self.time_to_expiration = inputs[3]
        self.risk_free_rate = inputs[4]
        self.price = self.put_price(self.asset_price, self.asset_volatility, self.strike_price, self.time_to_expiration, self.risk_free_rate)

        self.gradient_func = grad(self.put_price, (0, 1, 3)) #strike price, risk_free_rate does not change
        self.delta, self.vega, self.theta = self.gradient_func(inputs[0], inputs[1], inputs[2], inputs[3], inputs[4])
        self.theta /= -365
        self.vega /= 100


#Usage: def __init__(
#        self, c_p: Literal['C', 'P'], asset_price, option_market_price, strike_price,
#        time_to_expiration, risk_free_rate
#            ):


call = Option(c_p='C',
              asset_price=100,
              option_market_price=10,
              strike_price=105,
              time_to_expiration=365/365,
              risk_free_rate=0.00)

#option = EuropeanCall(inputs.astype('float'))
#print(option.find_iv_newton())

print(call.option.asset_volatility, call.option.delta, call.option.vega, call.option.theta, call.option.price)