# -*- coding: utf-8 -*-

import ccxt
import schedule
import asyncio
import pandas as pd
import pandas_ta as ta

from ccxt_bot.trade.base import Strategy, StrategyResult, Suggestion
from ccxt_bot.core import config
from ccxt_bot.core.utils import notify_line
from ccxt_bot.core.logger import logger


class Ccxt_bot():
    def __init__(
        self, 
        api_key: str,
        secret: str,
        exchange_id: str, # = 'binance', 
        symbol: str,
        timeframe: str,
        line_token: str,
        backtest: bool = False,
    ):
        exchange_class = getattr(ccxt, exchange_id)
        self._exchange: ccxt.binance = exchange_class({
            'apiKey': api_key,
            'secret': secret,
        })
        self._symbol = symbol
        self._timeframe = timeframe
        self._line_token = line_token
        self._strategies = []
        self._backtest = backtest
        
    def register_strategy(self, strategy: Strategy) -> int:
        self._strategies.append(strategy)
        
        return len(self._strategies)

    def indicator(self, data: pd.DataFrame):
        data['rsi']  = data.ta.rsi(lenght=10)
        data['ema'] = ta.ema(data['close'], length=21)
        # df.ta.kdj 是 pandas_ta 庫中計算 KDJ 指標的函數。該函數會在 DataFrame 對象中添加三列新的數據列，分別是 K 值、D 值和 J 值。函數的返回值是修改後的 DataFrame 對象。

        # 以下是 df.ta.kdj 函數的參數和返回值的簡要說明：

        # 參數：

        # high：指定 High 值的列名或位置，用於計算 KDJ 指標
        # low：指定 Low 值的列名或位置，用於計算 KDJ 指標
        # close：指定 Close 值的列名或位置，用於計算 KDJ 指標
        # window：指定 KDJ 指標的窗口大小，即計算 K 值、D 值和 J 值的周期數量
        # fillna：如果存在缺失值，指定是否填充，默認為 True
        # append：指定是否將計算結果添加到原始 DataFrame 對象中，默認為 True
        # 返回值：

        # 修改後的 DataFrame 對象，其中新增三列數據：K 值、D 值和 J 值。
        data[['kdj_k', 'kdj_d', 'kdj_j']]  = ta.kdj(high=data['high'], low=data['low'], close=data['close'], window=9, fillna=True, append=False)
        # df.ta.macd 是 pandas_ta 庫中計算 MACD 指標的函數。該函數會在 DataFrame 對象中添加三列新的數據列，分別是 MACD、MACD 信號線和 MACD 柱狀圖。函數的返回值是修改後的 DataFrame 對象。

        # 以下是 df.ta.macd 函數的參數和返回值的簡要說明：

        # 參數：

        # close：指定 Close 值的列名或位置，用於計算 MACD 指標
        # fast：指定快速移動平均線的周期數
        # slow：指定慢速移動平均線的周期數
        # signal：指定 MACD 信號線的周期數
        # fillna：如果存在缺失值，指定是否填充，默認為 True
        # append：指定是否將計算結果添加到原始 DataFrame 對象中，默認為 True
        # 返回值：

        # 修改後的 DataFrame 對象，其中新增三列數據：MACD、MACD 信號線和 MACD 柱狀圖。
        data[['macd', 'macd_signal', 'macd_hist']] = ta.macd(close=data['close'], fast=12, slow=26, signal=9, fillna=True, append=False)
        
        data['kdj_j_diff'] = data['kdj_j'] - 50 - data['macd']
        data['kdj_j_diff_prev'] = data['kdj_j_diff'].shift(1)
        
        return data

    def fetch_datas(self, limit: int=200) -> pd.DataFrame:
        while True:
            try:
                kbars = self._exchange.fetch_ohlcv(
                    symbol=self._symbol,
                    timeframe=self._timeframe,
                    limit=300
                )
                break
            except ccxt.base.errors.RequestTimeout as e:
                logger.warning(f"retry {type(e).__name__}, {e.args}, {e}")
                pass
            
            except Exception as e:
                logger.error(f"{type(e).__name__}, {e.args}, {e}")
                raise e
            
        df = pd.DataFrame(kbars[:], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['dt'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('dt', inplace=True)
        df = self.indicator(df).tail(limit)
        
        return df
    
    def do_notify(self, result: StrategyResult):
        if result.suggestion != Suggestion.DoNothing:
            
            msg = f'''
            👾 {config.APP_NAME} 👾
            
            symbol 👉 {self._symbol}
            
            {result.msg}
            '''
            notify_line(token=self._line_token, msg=msg)
        
    def do_strategies(self):
        df = self.fetch_datas()
        for stgy in self._strategies:
            if self._backtest:
                results = stgy.backtest(df)
                for result in results:
                    self.do_notify(result)
            else:    
                result = stgy.run(df)
                self.do_notify(result)
           
    async def run_forever(self) -> None:
        # Execute once when just entering
        self.do_strategies()
        
        amount = int(self._timeframe[0:-1])
        unit = self._timeframe[-1]
        job = self.do_strategies
        if 'y' == unit:
            scale = 365
            schedule.every(interval=scale*amount).days.at("00:00").do(job)
        elif 'M' == unit:
            scale = 30
            schedule.every(interval=scale*amount).days.at("00:00").do(job)
        elif 'w' == unit:
            scale = 7
            schedule.every(interval=scale*amount).days.at("00:00").do(job)
        elif 'd' == unit:
            scale = 1
            schedule.every(interval=scale*amount).days.at("00:00").do(job)
        elif 'h' == unit:
            scale = 1
            schedule.every().day.at("00:00").do(job)
            schedule.every(interval=scale*amount).hours.do(job)
        elif 'm' == unit:
            scale = 1
            schedule.every(interval=scale*amount).minutes.at(":00").do(job)
        elif 's' == unit:
            scale = 1
            schedule.every(interval=scale*amount).second.do(job)
        
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)
        
    async def close(self)->None:
        if self._exchange:
            await self._exchange.close()
            self._exchange = None
            
        
    
        
        
        