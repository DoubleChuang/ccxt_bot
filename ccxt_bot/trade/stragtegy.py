# -*- coding: utf-8 -*-

from typing import List

from ccxt_bot.core.logger import logger
from ccxt_bot.trade.base import StrategyResult, Suggestion


class KD50Strategy():
    """ KD50Strategy
    
    當KD 上穿50 則 發送 做多
    當KD 下穿50 則 發送 做空
    以上皆非 則 發送 不做事
    
    """
    def __init__(self):
        self._long_date = None
        self._short_date = None
    
    def run(self, datas) -> List[StrategyResult]:
        logger.info(f"Run {self.__class__.__name__} ...")
        
        curr_idx = -2
        prev_kd = datas['kdj_k'][curr_idx-1]
        curr_kd = datas['kdj_k'][curr_idx]
        
        results = [] 
        # StrategyResult(
        #     suggestion=Suggestion.DoNothing,
        # )
        
        prev_date = datas.index[curr_idx-1]
        curr_date = datas.index[curr_idx]
        
        logger.info(f"check KD from {prev_date} to {curr_date}")
        
        
        # KD轉多
        if prev_kd < 50 and curr_kd >= 50:
            
            stop_price = datas['low'][curr_idx]
            date = datas.index[curr_idx]
            
            msg = f"做多, 停損 {stop_price} at {date}"
            
            if self._long_date and self._long_date >= date:
                return results
                
            self._long_date = date
            
            r = StrategyResult(
                suggestion=Suggestion.Long,
                msg = msg,
                stop_price=stop_price,
            )
            results.append(r)
        
        # KD轉空
        elif prev_kd > 50 and curr_kd <= 50:
            stop_price = datas['high'][curr_idx]
            date = datas.index[curr_idx]
            
            msg = f"做空, 停損 {stop_price} at {date}"
            
            if self._short_date and self._short_date >= date:
                return results
        
            self._short_date = date

            r = StrategyResult(
                suggestion=Suggestion.Short,
                msg = msg,
                stop_price=stop_price,
            )
            results.append(r)
        
        return results

    def backtest(self, datas) -> List[StrategyResult]:
        logger.info(f"Run {self.__class__.__name__} backtest ...")
        results = []
        
        for i in range(1, len(datas)):
            
            curr_idx = i
            prev_kd = datas['kdj_k'][curr_idx-1]
            curr_kd = datas['kdj_k'][curr_idx]
            
            result = StrategyResult(
                suggestion=Suggestion.DoNothing,
            )
            
            if prev_kd < 50 and curr_kd >= 50:
                stop_price = datas['low'][curr_idx]
                date = datas.index[curr_idx]
                # msg = f"KD轉多 {prev_kd} -> {curr_kd} at {date}"
                msg = f"做多 {datas['open'][curr_idx]}, 停損 {stop_price} at {date}"
                
                if self._long_date and self._long_date >= date:
                    results.append(result)
                    continue
                    
                self._long_date = date
                
                results.append(
                    StrategyResult(
                        suggestion=Suggestion.Long,
                        msg = msg,
                        stop_price=stop_price,
                    )
                )
                
            elif prev_kd > 50 and curr_kd <= 50:
                stop_price = datas['high'][curr_idx]
                date = datas.index[curr_idx]
                # msg = f"KD轉空 {prev_kd} -> {curr_kd} at {datas.index[-1]}"
                msg = f"做空 {datas['open'][curr_idx]}, 停損 {stop_price} at {date}"
                
                if self._short_date and self._short_date >= date:
                    results.append(result)
                    continue
            
                self._short_date = date

                results.append(
                    StrategyResult(
                        suggestion=Suggestion.Short,
                        msg = msg,
                        stop_price=stop_price,
                    )
                )
            
            results.append(result)
        
        return results


class ImpulseMACDStrategy():
    def __init__(self):
        self._position_size = 0 # 持倉數量
        self._long_stop_price = 0.0
        self._short_stop_price = 0.0
        self._long_stop_price = None
        self._short_stop_price = None
    
    def run(self, datas) -> List[StrategyResult]:
        logger.info(f"Run {self.__class__.__name__} ...")
        
        results = []
        # StrategyResult(
        #     suggestion=Suggestion.DoNothing,
        # )
        
        curr_idx = -2
        close = datas['close'][curr_idx]
        atr = datas['atr'][-1]
        open = datas['open'][-1]
        date = datas.index[curr_idx]
        
        long_cond = datas['mdc'][curr_idx-3] == 'red' and datas['mdc'][curr_idx-2] == 'red' and \
                    datas['mdc'][curr_idx-1] == 'grean' and datas['mdc'][curr_idx] == 'green'
                    
        short_cond = datas['mdc'][curr_idx-3] == 'lime' and datas['mdc'][curr_idx-2] == 'lime' and \
                    datas['mdc'][curr_idx-1] == 'orange' and datas['mdc'][curr_idx] == 'orange'
        
        long_exit_cond = short_cond and self._position_size > 0
        short_exit_cond = long_cond and self._position_size < 0
        
        long_stop_cond = self._position_size > 0 and self._long_stop_price is not None and close <= self._long_stop_price
        short_stop_cond = self._position_size < 0 and self._short_stop_price is not None and close >= self._short_stop_price
        
        if long_exit_cond or long_stop_cond:
            msg = f"{'多單止損' if long_stop_cond else '多單停利'} {close}, at {date}"
            
            self._long_stop_price = None
            r = StrategyResult(
                suggestion=Suggestion.Long_SL if long_stop_cond else Suggestion.Long_TP,
                msg = msg,
            )
            results.append(r)
            
        if short_exit_cond or short_stop_cond:
            msg = f"{'空單止損' if short_stop_cond else '空單停利'} {close}, at {date}"
            
            self._short_stop_price = None
            r = StrategyResult(
                suggestion=Suggestion.Short_SL if short_stop_cond else Suggestion.Short_TP,
                msg = msg,
            )
            results.append(r)
    
        if short_cond:
            self._short_stop_price = open + 1.5 * atr
            msg = f"做空 {close}, 停損 {self._short_stop_price} at {date}"
            
            r = StrategyResult(
                suggestion=Suggestion.Short,
                msg = msg,
                stop_price=self._short_stop_price,
            )
            results.append(r)
        
        if long_cond:
            self._long_stop_price = open - 1.5 * atr
            msg = f"做多 {close}, 停損 {self._long_stop_price} at {date}"
            
            r = StrategyResult(
                suggestion=Suggestion.Long,
                msg = msg,
                stop_price=self._long_stop_price,
            )
            results.append(r)
        

        return results

    def backtest(self, datas) -> List[StrategyResult]:
        logger.info(f"Run {self.__class__.__name__} backtest ...")
        results = []
        
        # for i in range(1, len(datas)):
            
        #     result = StrategyResult(
        #         suggestion=Suggestion.DoNothing,
        #     )
            
        #     results.append(result)
        
        return results