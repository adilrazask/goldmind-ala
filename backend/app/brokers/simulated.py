"""Simulated Broker Adapter: Deterministic execution simulator for testing and non-Windows environments."""
from __future__ import annotations
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .base import BaseBroker, OrderResult

class SimulatedBroker(BaseBroker):
    def __init__(self, initial_balance: float = 10000.0, mode: str = "DEMO"):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.mode = mode # DEMO
        self.is_connected = True
        self.positions: Dict[int, Dict[str, Any]] = {}
        import time
        self.ticket_counter = int(time.time() * 1000) % 90000000 + 10000000

    def connect(self) -> bool:
        self.is_connected = True
        return True

    def get_account_info(self) -> Dict[str, Any]:
        # Recalculate equity from unrealized profits
        unrealized = sum(p["unrealized_profit"] for p in self.positions.values())
        self.equity = self.balance + unrealized
        used_margin = sum(p["volume"] * p["open_price"] * 0.01 for p in self.positions.values())
        return {
            "broker": "Simulated Demo Gateway",
            "account_number": "SIM-DEMO-88210",
            "mode": self.mode,
            "currency": "USD",
            "balance": round(self.balance, 2),
            "equity": round(self.equity, 2),
            "margin": round(used_margin, 2),
            "free_margin": round(self.equity - used_margin, 2),
            "is_connected": self.is_connected,
            "trade_allowed": True
        }

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        pos_list = list(self.positions.values())
        if symbol:
            pos_list = [p for p in pos_list if p["symbol"] == symbol.upper()]
        return pos_list

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
        if not self.is_connected:
            return OrderResult(False, None, symbol, side, volume, 0.0, stop_loss, take_profit, "REJECTED", "Broker disconnected")
            
        self.ticket_counter += 1
        ticket = self.ticket_counter
        
        pos = {
            "ticket": ticket,
            "symbol": symbol.upper(),
            "side": side.upper(),
            "volume": volume,
            "open_price": entry_price,
            "current_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "unrealized_profit": 0.0,
            "magic": magic,
            "open_time": datetime.now(timezone.utc).isoformat()
        }
        self.positions[ticket] = pos
        return OrderResult(
            accepted=True,
            ticket=ticket,
            symbol=symbol.upper(),
            side=side.upper(),
            volume=volume,
            execution_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status="FILLED",
            message="Simulated demo order filled successfully"
        )

    def update_tick_price(self, symbol: str, current_price: float):
        """Simulate tick updates for open positions."""
        for p in self.positions.values():
            if p["symbol"] == symbol.upper():
                p["current_price"] = current_price
                if p["side"] == "BUY":
                    p["unrealized_profit"] = round((current_price - p["open_price"]) * p["volume"] * 100.0, 2)
                else:
                    p["unrealized_profit"] = round((p["open_price"] - current_price) * p["volume"] * 100.0, 2)

    def close_position(self, ticket: int, magic: int = 610181) -> bool:
        if ticket in self.positions:
            pos = self.positions.pop(ticket)
            self.balance += pos["unrealized_profit"]
            self.equity = self.balance
            return True
        return False

    def disconnect(self):
        self.is_connected = False
