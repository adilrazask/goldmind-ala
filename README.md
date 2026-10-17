# GoldMind ALA — Autonomous Learning Agent & Quantitative Platform

An independent, autonomous AI quantitative research employee, trading strategy laboratory, and guarded execution platform.

Operates completely independently from existing GoldMind AI, Hermes, Graph Agent, Supabase, and production MT5 bridges. Contains its own relational schema (30 database tables), deterministic central risk engine, bounded tool registry, 5-tier memory architecture, multi-stage validation engine, FastAPI backend, and React/TypeScript SaaS dashboard.

---

## Architecture Overview

```
GoldMind ALA
├── frontend/                     # React + TypeScript + Vite + Tailwind CSS SaaS Dashboard
│   ├── src/pages/                # 10 Dedicated Operational Views
│   │   ├── DashboardPage.tsx     # Page 1: Main Dashboard (Status, KPIs, Kill Switch)
│   │   ├── AgentWorkspacePage.tsx# Page 2: AI Workspace (NL Hypothesis Formulation)
│   │   ├── StrategyLabPage.tsx   # Page 3: Strategy Lab (10 Allowed Families, DSL)
│   │   ├── ResearchMonitorPage.tsx# Page 4: Research Monitor & Auditable Timeline
│   │   ├── BacktestPage.tsx      # Page 5: Backtesting & Multi-Stage Validation
│   │   ├── LearningCenterPage.tsx# Page 6: Autonomous Learning Centre (5 Tiers)
│   │   ├── DemoTradingPage.tsx   # Page 7: Verified Demo Execution Desk
│   │   ├── LiveControlsPage.tsx  # Page 8: Air-Gapped Live Controls & Auth
│   │   ├── MarketDataPage.tsx    # Page 9: Market Data Feed Quality Diagnostics
│   │   └── SettingsPage.tsx      # Page 10: Settings, Ollama & System Operations
│   └── src/api.ts                # REST & WebSocket client
├── backend/app/                  # FastAPI Application
│   ├── api/endpoints.py          # REST & WebSocket API Routers
│   ├── agent/                    # Agent Controller & Bounded Tool Registry
│   ├── planner/                  # Structured Research Planner & Task Queue
│   ├── strategy_factory/         # 10 Strategy Families & Declarative DSL
│   ├── sandbox/                  # AST Static Safety & Causality Sandbox
│   ├── market_data/              # OHLCV Ingestion, Quality Audits, Regimes
│   ├── backtesting/              # Vectorized Engine (Fees, Spread, Slippage)
│   ├── validation/               # In-Sample, OOS, Walk-Forward, Regimes, Stress Tests
│   ├── risk/                     # Deterministic Central Risk Engine (18 Checks)
│   ├── execution/                # Order Lifecycle Manager & State Reconciliation
│   ├── brokers/                  # Simulated Broker & MetaTrader 5 Adapters
│   ├── learning/                 # 5-Tier Memory & Procedure Improvement Engine
│   ├── scheduler/                # Continuous Background Research Loop
│   ├── database/                 # SQLAlchemy 2.0 Database Session
│   └── models/entities.py        # 30 Versioned Relational Tables
├── tests/                        # Legacy compatibility unit tests
├── backend/tests/                # Automated backend test suite (23 pytest tests)
└── scripts/                      # Verification and automation scripts
```

---

## 10 Supported Quantitative Strategy Families

1. **Moving-Average Crossover** (`moving_average_crossover`): Fast vs slow moving average trend alignment.
2. **Momentum Continuation** (`momentum`): Relative price velocity over parameterized lookbacks.
3. **Channel Breakout** (`breakout`): Resistance penetration with volatility margin.
4. **RSI Mean Reversion** (`rsi_mean_reversion`): Exhaustion bounce from statistical oversold bands.
5. **Volatility-Filtered Strategies** (`volatility_filtered`): Momentum constrained to favorable volatility regimes.
6. **Macro Trend Following** (`trend_following`): Multi-tier trend confirmation with pullback entries.
7. **Multi-Timeframe Confirmation** (`multi_timeframe_confirmation`): HTF trend alignment validating LTF triggers.
8. **ATR Volatility Adaptation** (`atr_volatility_adaptation`): Dynamic bandwidth scaling adapting to market volatility expansion.
9. **Session-Based Strategies** (`session_based`): Peak institutional liquidity filtering (London/NY overlap).
10. **Composite Combinations** (`composite_combination`): Dual-component synthesis (e.g. Trend Filter + Oversold Dip Buying).

---

## 5-Tier Autonomous Learning Memory Architecture

1. **Instruction Memory**: Persistent operational heuristics, safety rules, and research directives provided by the owner.
2. **Demonstration Memory**: Exemplary past decisions, rationale, and anti-patterns for comparable task retrieval.
3. **Experience Memory**: Empirical observations, failure reasons, and trade review results from completed experiments.
4. **Verified Knowledge Memory**: High-confidence statistical properties that survived out-of-sample and walk-forward verification.
5. **Research-Improvement Memory**: Versioned research procedure definitions and benchmarked improvement proposals.

---

## Central Deterministic Risk Engine

- **Non-bypassable**: Operates independently of the language model; LLMs cannot alter limits or override rejections.
- **18 Pre-Trade Safety Checks**:
  1. Emergency Kill Switch state
  2. Mode permission & strategy allowlist verification
  3. Daily equity loss limit (1.0% hard stop from day baseline)
  4. Max open positions limit (3 concurrent positions)
  5. Maximum risk per trade (0.25% equity default)
  6. Deterministic position sizing based on instrument tick value, tick size, and stop-loss distance
  7. Mandatory protective Stop-Loss & Take-Profit orientation
  8. Broker minimum stop distance compliance
  9. Quote freshness (< 10 seconds age)
  10. Maximum spread gate (35 points)
  11. Allowed market trading hours
  12. Duplicate order protection via idempotency keys

---

## Quick Start Guide

### 1. Start the FastAPI Backend & Integrated SaaS Dashboard

```bash
# Activate virtual environment
source .venv/bin/activate

# Launch unified server (Serves both REST API on :8000 and the compiled React SaaS dashboard at /)
python3 main.py server --host 127.0.0.1 --port 8000
```

Open your browser at **http://127.0.0.1:8000** to access the complete SaaS UI.

### 2. Frontend Development Server (Optional)

```bash
cd frontend
npm run dev
```

Vite dev server starts on **http://localhost:5173** and proxies `/api` and `/ws` to the FastAPI backend.

### 3. Run Automated Tests

```bash
# Run complete test suite (23 backend tests + 8 legacy tests = 31 passing tests)
PYTHONPATH=. .venv/bin/pytest backend/tests/ -v
.venv/bin/python3 -m unittest discover tests

# Run end-to-end autonomous research & demo execution verification
PYTHONPATH=. .venv/bin/python3 scripts/verify_workflow.py
```

### 4. CLI Research Commands (Preserved & Enhanced)

```bash
# Run one bounded research plan
python3 main.py run --objective "Investigate M15 XAUUSD breakout persistence"

# Backtest SMA crossover on historical CSV
python3 main.py backtest --csv examples/sample_synthetic_ohlcv.csv --fast 10 --slow 30

# Generate one new allowlisted strategy candidate
python3 main.py generate --csv examples/sample_synthetic_ohlcv.csv

# Autopilot continuous research loop
python3 main.py autopilot --csv examples/sample_synthetic_ohlcv.csv --cycles 5

# View persistent instructions and demonstrations
python3 main.py instructions
python3 main.py examples
```

---

## MetaTrader 5 Integration (Windows Gateway)

1. Run on a Windows machine with desktop MetaTrader 5 terminal logged into a **verified demo account**.
2. Install dependency: `py -m pip install MetaTrader5`
3. Check status: `py main.py mt5-status --mode demo`
4. Autonomous loop: `py main.py mt5-autopilot --mode demo --symbol XAUUSD --timeframe M15 --cycles 5 --trade`

### Live Trading Protocol (Disabled by Default)

Live trading requires:
1. Environment opt-in: `ALA_ENABLE_LIVE_TRADING=YES_I_ACCEPT_RISK`
2. Daily start equity baseline: `ALA_DAILY_START_EQUITY=10000`
3. Cryptographic confirmation phrase: `"I UNDERSTAND REAL MONEY RISK"`
4. Strategy must be explicitly promoted to `LIVE_ALLOWLISTED` by the owner.
