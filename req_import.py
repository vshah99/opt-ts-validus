import pandas as pd

pd.set_option('display.max_columns', None)
import numpy as np
import pickle as pkl
import os
from typing import Optional, Literal, Any, List
from pydantic import validate_call, Field, validate_arguments
import re
from datetime import datetime

# import jax.numpy as np
# from jax.numpy import log, sqrt, exp, pi
# from jax.scipy.stats import norm
# from jax import grad

from abc import ABC, abstractmethod

from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.implied_volatility import implied_volatility as iv
from py_vollib.black_scholes.greeks.analytical import delta, vega, theta, gamma

from py_lets_be_rational.exceptions import BelowIntrinsicException