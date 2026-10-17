"""Broker interface defining uniform execution contract."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class OrderResult:
    accepted: bool
    ticket: Optional[int]
    symbol: str
    side: str
    volume: float
    execution_price: float
    stop_loss: float
    take_profit: float
    status: str # FILLED, REJECTED, SUBMITTED
    message: str

class BaseBroker(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass
        
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def submit_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        magic: int = 610181
    ) -> OrderResult:
        pass
        
    @abstractmethod
    def close_position(self, ticket: int, magic: int = 610181) -> bool:
        pass
        
    @abstractmethod
    def disconnect(self):
        pass
