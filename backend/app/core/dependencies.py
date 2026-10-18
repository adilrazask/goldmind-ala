"""Core Shared Singletons & Runtime State for GoldMind ALA."""
from __future__ import annotations
from backend.app.core.config import settings
from backend.app.agent.controller import AgentController
from backend.app.scheduler.runner import ResearchScheduler
from backend.app.brokers.simulated import SimulatedBroker
from backend.app.brokers.mt5_adapter import MT5BrokerAdapter
from backend.app.risk.engine import CentralRiskEngine
from backend.app.execution.order_manager import OrderLifecycleManager

from backend.app.delta.adapter import delta_broker
from backend.app.database.session import init_db

# Ensure database tables exist before controllers query them
init_db()

# System Singletons
controller = AgentController()
scheduler = ResearchScheduler(controller)
risk_engine = CentralRiskEngine(
    daily_loss_limit_pct=settings.MAX_DAILY_LOSS_PCT,
    max_risk_per_trade_pct=settings.MAX_RISK_PER_TRADE_PCT,
    max_open_positions=settings.MAX_OPEN_POSITIONS,
    max_spread_points=settings.MAX_SPREAD_POINTS,
    daily_start_equity=settings.DAILY_START_EQUITY
)
simulated_broker = SimulatedBroker()
mt5_broker = MT5BrokerAdapter()
active_broker = simulated_broker
order_manager = OrderLifecycleManager(active_broker, risk_engine)

def set_active_broker(broker_name: str):
    """Dynamically switches active broker adapter (simulated, mt5, delta)."""
    global active_broker, order_manager
    name = broker_name.lower().strip()
    if name == "delta":
        active_broker = delta_broker
    elif name == "mt5":
        active_broker = mt5_broker
    else:
        active_broker = simulated_broker
    order_manager.broker = active_broker
    return active_broker

