# -*- coding: utf-8 -*-

import asyncio

import ccxt
from ccxt_bot.trade.bot import Ccxt_bot
from ccxt_bot.core.logger import logger
from ccxt_bot.trade.stragtegy import ImpulseMACDStrategy, KD50Strategy
from ccxt_bot.core import config
import ccxt_bot
import schedule

async def main():
    logger.info(f"ccxt version: {ccxt.__version__}")
    logger.info(f"ccxt bot commit hash: {ccxt_bot.__commit_hash__}")
    # 4h KD bot
    bot = Ccxt_bot(
        api_key=config.BINANCE_API_KEY,
        secret=config.BINANCE_SECRET,
        exchange_id="binance",
        symbol="ETH/USDT",
        timeframe="4h",
        line_token=config.LINE_TOKEN,
        backtest=config.BACKTEST,
        sandbox=config.SANDBOX,
    )
    bot.register_strategy(KD50Strategy())
    bot.join_schedule(scheduler=schedule)
    
    # 1h impluse MACD bot
    bot1 = Ccxt_bot(
        api_key=config.BINANCE_API_KEY,
        secret=config.BINANCE_SECRET,
        exchange_id="binance",
        symbol="ETH/USDT",
        timeframe="1h",
        line_token=config.LINE_TOKEN,
        backtest=config.BACKTEST,
        sandbox=config.SANDBOX,
    )
    bot1.register_strategy(KD50Strategy())
    bot1.register_strategy(ImpulseMACDStrategy())
    bot1.join_schedule(scheduler=schedule)
    
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())