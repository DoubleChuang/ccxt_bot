# -*- coding: utf-8 -*-

from decouple import config


BINANCE_API_KEY = config('BINANCE_API_KEY', cast=str,  default='')
BINANCE_SECRET  = config('BINANCE_SECRET',  cast=str,  default='')
LINE_TOKEN      = config('LINE_TOKEN',      cast=str,  default='')
APP_NAME        = config('APP_NAME',        cast=str,  default='ccxt_bot')
BACKTEST        = config('BACKTEST',        cast=bool, default=False)
SANDBOX         = config('SANDBOX',         cast=bool, default=True)