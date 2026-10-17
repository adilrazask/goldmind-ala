"""Order Lifecycle and Broker State Reconciliation Manager."""
from __future__ import annotations
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from backend.app.database.session import SessionLocal
from backend.app.models.entities import BrokerOrder, BrokerPosition, BrokerEvent, TradeReview
from backend.app.brokers.base import BaseBroker, OrderResult
from backend.app.risk.engine import CentralRiskEngine

class OrderLifecycleManager:
    def __init__(self, broker: BaseBroker, risk_engine: CentralRiskEngine):
        self.broker = broker
        self.risk_engine = risk_engine
        self.reconciliation_paused = False

    def submit_managed_order(
        self,
        strategy_id: str,
        strategy_approval_state: str,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        account_mode: str = "DEMO",
        current_spread_points: int = 25,
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if self.reconciliation_paused:
            return False, "Order execution paused due to unresolved broker reconciliation mismatch.", None

        order_id = str(uuid.uuid4())
        idem_key = idempotency_key or f"idem_{uuid.uuid4()}"
        
        db = SessionLocal()
        try:
            # Idempotency check
            existing = db.query(BrokerOrder).filter_by(idempotency_key=idem_key).first()
            if existing:
                return False, f"Duplicate order rejected by idempotency key: {idem_key}", None

            account_info = self.broker.get_account_info()
            equity = account_info.get("equity", 10000.0)
            open_positions = self.broker.get_positions(symbol)
            
            # Step 1: Central Risk Gate Evaluation
            approved, risk_reason, checks, calculated_volume = self.risk_engine.evaluate_proposal(
                strategy_id=strategy_id,
                strategy_approval_state=strategy_approval_state,
                instrument=symbol,
                side=side,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                account_mode=account_mode,
                current_equity=equity,
                current_spread_points=current_spread_points,
                open_positions_count=len(open_positions)
            )

            # Record internal order state
            order_record = BrokerOrder(
                id=order_id,
                idempotency_key=idem_key,
                strategy_id=strategy_id,
                account_mode=account_mode,
                symbol=symbol.upper(),
                side=side.upper(),
                requested_volume=calculated_volume,
                requested_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                state="VALIDATED" if approved else "REJECTED",
                rejection_reason=None if approved else risk_reason
            )
            db.add(order_record)
            db.commit()

            if not approved:
                return False, f"Risk Gate Rejected: {risk_reason}", {"order_id": order_id, "state": "REJECTED", "checks": checks}

            # Step 2: Broker Order Submission
            order_record.state = "SUBMITTED"
            db.commit()

            broker_res: OrderResult = self.broker.submit_order(
                symbol=symbol.upper(),
                side=side.upper(),
                volume=calculated_volume,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )

            # Step 3: Record Broker Result
            if broker_res.accepted and broker_res.status == "FILLED":
                order_record.state = "FILLED"
                order_record.broker_ticket = broker_res.ticket
                order_record.filled_volume = broker_res.volume
                order_record.execution_price = broker_res.execution_price
                
                # Add position record
                pos_record = BrokerPosition(
                    id=str(uuid.uuid4()),
                    ticket=broker_res.ticket or 0,
                    symbol=symbol.upper(),
                    side=side.upper(),
                    volume=broker_res.volume,
                    open_price=broker_res.execution_price,
                    current_price=broker_res.execution_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    unrealized_profit=0.0
                )
                db.add(pos_record)
            else:
                order_record.state = "REJECTED"
                order_record.rejection_reason = broker_res.message

            db.commit()
            
            return broker_res.accepted, broker_res.message, {
                "order_id": order_id,
                "ticket": broker_res.ticket,
                "symbol": symbol,
                "side": side,
                "volume": calculated_volume,
                "execution_price": broker_res.execution_price,
                "state": order_record.state
            }
        finally:
            db.close()

    def reconcile_state(self) -> Dict[str, Any]:
        """Reconciles internal DB open positions with authoritative broker state."""
        db = SessionLocal()
        try:
            broker_positions = self.broker.get_positions()
            db_positions = db.query(BrokerPosition).filter_by(is_closed=False).all()
            
            broker_tickets = {p["ticket"]: p for p in broker_positions}
            db_tickets = {p.ticket: p for p in db_positions}
            
            mismatches = []
            
            # Check for positions closed on broker
            for ticket, db_p in db_tickets.items():
                if ticket not in broker_tickets:
                    # Position was closed on broker (SL/TP hit or manual exit)
                    db_p.is_closed = True
                    db_p.closed_at = datetime.now(timezone.utc)
                    # Create post-trade review record
                    review = TradeReview(
                        id=str(uuid.uuid4()),
                        position_ticket=ticket,
                        strategy_id="MANAGED_STRATEGY",
                        realized_pnl=db_p.unrealized_profit,
                        rule_adherence=True,
                        thesis_supported=(db_p.unrealized_profit > 0),
                        observations="Position closed by broker protective order or exit logic."
                    )
                    db.add(review)

            # Check for unexpected broker positions not tracked by ALA
            for ticket, b_p in broker_tickets.items():
                if ticket not in db_tickets:
                    mismatches.append(f"Untracked external broker position found: Ticket {ticket} on {b_p['symbol']}")
            
            db.commit()
            
            if mismatches:
                self.reconciliation_paused = True
                return {"reconciled": False, "mismatches": mismatches, "paused": True}
                
            return {"reconciled": True, "broker_open_positions": len(broker_positions), "mismatches": []}
        finally:
            db.close()
