# -*- coding: utf-8 -*-

from typing import Protocol, Optional, List
from enum import Enum, auto
from pydantic import BaseModel

class Suggestion(Enum):
    Long = auto() # long
    Long_SL = auto() # long stop loss
    Long_TP = auto() # long take profit
    
    Short = auto() # short
    Short_SL = auto() # short stop loss
    Short_TP = auto() # short take profit
    
    DoNothing = auto() # do nothing

class StrategyResult(BaseModel):
    name: str
    suggestion: Optional[Suggestion] = Suggestion.DoNothing
    msg: Optional[str] = ""
    stop_price: Optional[float] = None
    tp_price: Optional[float] = None

class Strategy(Protocol):
    def run(self, datas) -> StrategyResult:
        ...
    
    def backtest(self, datas) -> List[StrategyResult]:
        ...