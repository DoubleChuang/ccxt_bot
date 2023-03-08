# -*- coding: utf-8 -*-

from typing import Protocol, Optional, List
from enum import Enum, auto
from pydantic import BaseModel

class Suggestion(Enum):
    Long = auto()
    Short = auto()
    DoNothing = auto()

class StrategyResult(BaseModel):
    suggestion: Optional[Suggestion] = Suggestion.DoNothing
    msg: Optional[str] = ""
    stop_price: Optional[int] = None

class Strategy(Protocol):
    def run(self, datas) -> StrategyResult:
        ...
    
    def backtest(self, datas) -> List[StrategyResult]:
        ...