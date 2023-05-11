# -*- coding: utf-8 -*-

import pytest
import pytest_mock
import ccxt
from ccxt_bot.core import config

from ccxt_bot.trade.trader import Trader

@pytest.fixture
def balance_data() -> tuple:
    return ('ETH', 'USDT'), \
            (
                {'free': 0.0, 'used': 0.0, 'total': 0.0, 'debt': 0.05},
                {'free': 500, 'used': 0.0, 'total': 500, 'debt': 0.0}
            )



@pytest.mark.parametrize("expected", [
    (0.450),
])
def test_calc_amount(balance_data: tuple,
                    mocker: pytest_mock.MockFixture,
                    expected
                    ):
    
    exchange_class = getattr(ccxt, 'binance')
    exchange:ccxt.binance = exchange_class({
        'apiKey': config.BINANCE_API_KEY,
        'secret': config.BINANCE_SECRET,
    })
    
    trader = Trader(
        exchange=exchange,
        symbol="ETH/USDT",
    )
    mocker.patch.object(Trader, "fetch_balance", return_value=balance_data)
    mocker.patch.object(ccxt.binance, "fetch_ticker", return_value={'close':1000.0})
    
    assert trader.calc_amount() == expected
