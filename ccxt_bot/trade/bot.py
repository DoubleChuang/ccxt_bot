# -*- coding: utf-8 -*-

from typing import List, Union
import ccxt
import asyncio
import pandas as pd
import pandas_ta as ta
import numpy as np
from schedule import Scheduler

from ccxt_bot.trade.base import Strategy, StrategyResult, Suggestion
from ccxt_bot.core import config
from ccxt_bot.core.utils import notify_line
from ccxt_bot.core.logger import logger
from ccxt_bot.trade.trader import Trader


# help functions
def calc_smma(src: pd.DataFrame, length: int):
    smma = ta.sma(src, length)

    for i in range(length, len(src)):
        smma[i] = (smma[i-1] * (length - 1) + src[i])/length
        
    return smma

def calc_zlema(src, length):
    ema1 = ta.ema(src, length)
    ema2 = ta.ema(ema1, length)
    d = ema1 - ema2

    return ema1 + d

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
        sandbox: bool = False,
    ):
        """Ccxt_bot
        這是一個執行 已註冊策略 進行自動操作 與 通知 的加密貨幣機器人 
        
        Args:
            api_key (str): 向交易所申請的api key
            secret (str): 向交易所申請的secret
            exchange_id (str): 交易所的id, ex. binance
            symbol (str): 要監測的交易對, ex. ETH/USDT
            timeframe (str): 要監測的週期的K線圖, ex. 4H
            line_token (str): 發送訊息到line的line token
            backtest (bool, optional): 回測功能. Defaults to False.
            sandbox (bool, optional): 下單功能，如果開啟 則不會真實下單 僅顯示log. Defaults to False.
        """
        exchange_class = getattr(ccxt, exchange_id)
        self._exchange: ccxt.binance = exchange_class({
            'apiKey': api_key,
            'secret': secret,
            # 'options': {
            #     'defaultType': 'margin', # 槓桿
            #     'createMarketBuyOrderRequiresPrice': False
            # }
        })
        self._symbol = symbol
        self._timeframe = timeframe
        self._line_token = line_token
        self._strategies = []
        self._backtest = backtest
        self._sandbox = sandbox
        self._trader = Trader(exchange=self._exchange, symbol=symbol, sandbox=sandbox)
        
    def register_strategy(self, strategy: Strategy) -> List[Strategy]:
        """register_strategy

        Args:
            strategy (Strategy): 註冊想要執行的策略

        Returns:
            List[Strategy]: 當前註冊的策略
        """
        self._strategies.append(strategy)
        
        return self._strategies

    def generate_indicator(self, data: pd.DataFrame):
        """indicator
        
        使用輸入的k線資料 計算需要的指標 並 回傳

        Args:
            data (pd.DataFrame): k線資料

        Returns:
            pd.DataFrame: k線資料並包含計算後的indicator
        """
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
        
        lengthMA = 34
        lengthSignal = 9
        src = data[['high', 'low', 'close']].mean(axis=1)
        data['hi'] = calc_smma(data['high'], lengthMA)
        data['lo'] = calc_smma(data['low'], lengthMA)
        data['mi'] = calc_zlema(src, lengthMA)
        
        data['md'] = np.where(data['mi'] > data['hi'], data['mi'] - data['hi'], np.where(data['mi'] < data['lo'], data['mi'] - data['lo'], 0))
        data['sb'] = ta.sma(data['md'], lengthSignal)
        data['sh'] = data['md'] - data['sb']
        data['mdc'] = np.where(src > data['mi'], np.where(src > data['hi'], 'lime', 'green'), np.where(src < data['lo'], 'red', 'orange'))
        data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=14, mamode="rma")
        
        # logger.info(f"data['atr']:{data['atr']}")
        # logger.info(f"data['close']:{data['close']}")
        
        return data

    def fetch_datas(self, limit: int=200) -> pd.DataFrame:
        """fetch_datas
        獲取股票k線資料

        Args:
            limit (int, optional): 最後輸出的資料. Defaults to 200.

        Raises:
            e: _description_

        Returns:
            pd.DataFrame: 輸出股票資料
        """
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
        df = self.generate_indicator(df).tail(limit)
        
        return df
    
    def notify_line(self, result: StrategyResult) -> None:
        """發送策略判斷的結果到Line

        Args:
            result (StrategyResult): _description_
        """
        if result.suggestion != Suggestion.DoNothing:
            
            msg = f'''
            👾 {config.APP_NAME} 👾
            
            strategy   👉 {result.name} 
            symbol     👉 {self._symbol}
            time frame 👉 {self._timeframe}
            
            {result.msg}
            '''
            notify_line(token=self._line_token, msg=msg)
        
    def do_strategies(self, skip_order: bool = False) -> None:
        """do_strategies        
        執行已註冊的策略
        """
        df = self.fetch_datas()
        # 有註冊的策略將會把資料輸入執行 並執行發送通知與建立訂單
        for stgy in self._strategies:
            if self._backtest:
                results = stgy.backtest(df)
                for result in results:
                    self.notify_line(result)
                    if not skip_order: self._trader.create_order(result, percent_of_equity=30)
            else:    
                results = stgy.run(df)
                for result in results:
                    self.notify_line(result)
                    # create order by strategy result
                    if not skip_order: self._trader.create_order(result, percent_of_equity=30)
    
                
           
    def join_schedule(self, scheduler: Scheduler) -> None:
        """ run_forever
        
        依照每經過timeframe間隔 就獲取最新資料並執行註冊的策略
        第一次進入會無條件先執行一次, 但不會交易訂單
        """
        # Execute once when just entering, but will not execute the order
        self.do_strategies(skip_order=False)
        
        amount = int(self._timeframe[0:-1])
        unit = self._timeframe[-1]
        job = self.do_strategies
        if 'y' == unit:
            scale = 365
            scheduler.every(interval=scale*amount).days.at("00:00").do(job)
        elif 'M' == unit:
            scale = 30
            scheduler.every(interval=scale*amount).days.at("00:00").do(job)
        elif 'w' == unit:
            scale = 7
            scheduler.every(interval=scale*amount).days.at("00:00").do(job)
        elif 'd' == unit:
            scale = 1
            scheduler.every(interval=scale*amount).days.at("00:00").do(job)
        elif 'h' == unit:
            for scale in range(24 // amount):
                hour = scale*amount    
                scheduler.every(interval=1).days.at(f"{hour:02}:00:01").do(job)
                scale += 1
        elif 'm' == unit:
            scale = 1
            scheduler.every(interval=scale*amount).minutes.at(":00").do(job)
        elif 's' == unit:
            scale = 1
            scheduler.every(interval=scale*amount).second.do(job)
        
        for s in scheduler.get_jobs():
            logger.info(f"{s.__repr__}")
        
        
        
    async def close(self)->None:
        if self._exchange:
            await self._exchange.close()
            self._exchange = None
            