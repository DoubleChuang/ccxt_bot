# -*- coding: utf-8 -*-

import asyncio

import ccxt
from ccxt_bot.trade.bot import Ccxt_bot
from ccxt_bot.core.logger import logger
from ccxt_bot.trade.stragtegy import MjStategy
from ccxt_bot.core import config
import ccxt_bot


async def main():
    logger.info(f"ccxt version: {ccxt.__version__}")
    logger.info(f"ccxt bot commit hash: {ccxt_bot.__commit_hash__}")
    
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
    
    bot.register_strategy(MjStategy())
    
    await bot.run_forever()

if __name__ == '__main__':
    asyncio.run(main())