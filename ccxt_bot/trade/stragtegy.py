# -*- coding: utf-8 -*-

from typing import List

from ccxt_bot.core.logger import logger
from ccxt_bot.trade.base import StrategyResult, Suggestion


class MjStategy():
    """ MjStategy
    
    當KD 上穿50 則 發送 做多
    當KD 下穿50 則 發送 做空
    以上皆非 則 發送 不做事
    
    """
    def __init__(self):
        self._long_date = None
        self._short_date = None
    
    def run(self, datas) -> StrategyResult:
        logger.info(f"Run MjStategy ...")
        
        curr_idx = -2
        prev_kd = datas['kdj_k'][curr_idx-1]
        curr_kd = datas['kdj_k'][curr_idx]
        
        result = StrategyResult(
            suggestion=Suggestion.DoNothing,
        )
        
        prev_date = datas.index[curr_idx-1]
        curr_date = datas.index[curr_idx]
        
        logger.info(f"check KD from {prev_date} to {curr_date}")
        
        
        # KD轉多
        if prev_kd < 50 and curr_kd >= 50:
            
            stop_price = datas['low'][curr_idx]
            date = datas.index[curr_idx]
            
            msg = f"做多, 停損 {stop_price} at {date}"
            
            if self._long_date and self._long_date >= date:
                return result
                
            self._long_date = date
            
            return StrategyResult(
                suggestion=Suggestion.Long,
                msg = msg,
                stop_price=stop_price,
            )
        
        # KD轉空
        elif prev_kd > 50 and curr_kd <= 50:
            stop_price = datas['high'][curr_idx]
            date = datas.index[curr_idx]
            
            msg = f"做空, 停損 {stop_price} at {date}"
            
            if self._short_date and self._short_date >= date:
                return result
        
            self._short_date = date

            return StrategyResult(
                suggestion=Suggestion.Short,
                msg = msg,
                stop_price=stop_price,
            )
        
        return result

    def backtest(self, datas) -> List[StrategyResult]:
        logger.info(f"Run MjStategy backtest ...")
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
