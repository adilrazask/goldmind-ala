"""Structured Command Interpreter & Intent Allowlist Validator."""
from __future__ import annotations
import re
from typing import Dict, Any, Optional, Tuple, List
from backend.app.voice.schema import VoiceCommand, VoiceCommandIntent, PermissionLevel
from backend.app.voice.config import voice_settings

class CommandInterpreter:
    def __init__(self):
        # Allowlist of intent pattern matchers (Ordered by strict precedence)
        self.intent_patterns = [
            # 1. Protected Actions (Level 3 - Strictly Blocked via Voice)
            (
                r"\b(change|modify|increase|decrease|update|set|alter|override|boost)\b.*\b(risk|limit|limits|drawdown|loss)\b",
                VoiceCommandIntent.CHANGE_RISK_LIMITS,
                PermissionLevel.LEVEL_3_PROTECTED_ACTION
            ),
            (
                r"\b(enable|activate|turn\s*on|start|switch\s*to)\b.*\b(live|real\s*money|real\s*trading)\b",
                VoiceCommandIntent.ENABLE_LIVE_TRADING,
                PermissionLevel.LEVEL_3_PROTECTED_ACTION
            ),
            (
                r"\b(buy|sell|place\s*order|execute\s*order|enter\s*position|open\s*trade)\b",
                VoiceCommandIntent.PLACE_LIVE_ORDER,
                PermissionLevel.LEVEL_3_PROTECTED_ACTION
            ),
            (
                r"\b(change|update|set)\b.*\b(broker|credentials?|api\s*key|password)\b",
                VoiceCommandIntent.MODIFY_BROKER_CREDENTIALS,
                PermissionLevel.LEVEL_3_PROTECTED_ACTION
            ),

            # 2. System Controls (Level 1: system pause/stop commands per Section 8)
            (
                r"\b(pause|pause\s*research|pause\s*new\s*research|pause\s*jobs?|hold\s*research)\b",
                VoiceCommandIntent.PAUSE_RESEARCH,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(resume|resume\s*research|continue\s*research|restart\s*research)\b",
                VoiceCommandIntent.RESUME_RESEARCH,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(stop\s*current\s*task|stop\s*task|cancel\s*task|stop\s*experiment|stop\s*current\s*research)\b",
                VoiceCommandIntent.STOP_CURRENT_TASK,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(agent\s*status|system\s*status|show\s*status|check\s*status|status)\b",
                VoiceCommandIntent.SHOW_AGENT_STATUS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(data\s*connection|feed\s*health|market\s*feed|connection\s*status)\b",
                VoiceCommandIntent.CHECK_DATA_CONNECTION,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(read\s*(latest)?\s*report|read\s*report|tell\s*me\s*findings)\b",
                VoiceCommandIntent.READ_LATEST_REPORT,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(activity\s*log|today'?s\s*activity|show\s*log|audit\s*log|history)\b",
                VoiceCommandIntent.SHOW_ACTIVITY_LOG,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),

            # Exchange & Account Operations (Level 1 & Level 2)
            (
                r"\b(open\s*positions?|my\s*positions?|current\s*positions?|positions?)\b",
                VoiceCommandIntent.SHOW_OPEN_POSITIONS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(available\s*margin|margin|free\s*margin|account\s*balance|wallet\s*balance|balances?)\b",
                VoiceCommandIntent.SHOW_AVAILABLE_MARGIN,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(pending\s*orders?|open\s*orders?|active\s*orders?)\b",
                VoiceCommandIntent.SHOW_PENDING_ORDERS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(start\s*paper\s*trading|paper\s*trading\s*mode|enable\s*paper\s*trading|switch\s*to\s*paper)\b",
                VoiceCommandIntent.START_PAPER_TRADING,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(realized\s*(and|&)\s*unrealized\s*p&?l|p&?l|profit\s*(and|&)\s*loss|today'?s\s*p&?l|how\s*much\s*profit)\b",
                VoiceCommandIntent.SHOW_PROFIT_LOSS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(pause\s*(new\s*)?trading\s*signals?|pause\s*signals?)\b",
                VoiceCommandIntent.PAUSE_TRADING_SIGNALS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(cancel\s*(this\s*)?(pending\s*)?order|delete\s*order)\b",
                VoiceCommandIntent.CANCEL_PENDING_ORDER,
                PermissionLevel.LEVEL_2_CONTROLLED_RESEARCH
            ),

            # 3. Market Research Comparison & Reports
            (
                r"\b(compare|comparison)\b",
                VoiceCommandIntent.COMPARE_MARKETS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(market\s*structure|structure\s*of\s*market|price\s*structure)\b",
                VoiceCommandIntent.GET_MARKET_STRUCTURE,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(price\s*data|latest\s*(available)?\s*price|current\s*price|quotes?)\b",
                VoiceCommandIntent.CHECK_PRICE_DATA,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(trend\s*and\s*volatility|volatility|trend|explain\s*trend)\b",
                VoiceCommandIntent.EXPLAIN_TREND_VOLATILITY,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(support\s*(and|&)\s*resistance|support|resistance|zones?|levels?)\b",
                VoiceCommandIntent.IDENTIFY_SUPPORT_RESISTANCE,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(ema|rsi|indicators?|moving\s*average|vwap|atr)\b",
                VoiceCommandIntent.CHECK_INDICATORS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(market\s*risks?|volatility\s*risks?|current\s*risks?|risk\s*conditions?)\b",
                VoiceCommandIntent.EXPLAIN_MARKET_RISKS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(market\s*report|generate\s*market\s*report|market\s*research\s*report)\b",
                VoiceCommandIntent.GENERATE_MARKET_REPORT,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(analyse|analyze|research|evaluate|examine|inspect|check\s*out)\b",
                VoiceCommandIntent.ANALYSE_MARKET,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),

            # 4. Strategy Research & Backtesting
            (
                r"\b(transaction\s*costs?|fees?|slippage|spread\s*costs?)\b",
                VoiceCommandIntent.CHECK_TRANSACTION_COSTS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(max\s*drawdown|maximum\s*drawdown|drawdown|draw\s*down)\b",
                VoiceCommandIntent.SHOW_MAX_DRAWDOWN,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(benchmark|compare\s*with\s*benchmark|buy\s*and\s*hold)\b",
                VoiceCommandIntent.COMPARE_BENCHMARK,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(poor\s*performance|performed\s*poorly|why\s*fail|loss\s*reason)\b",
                VoiceCommandIntent.EXPLAIN_POOR_PERFORMANCE,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(strategy\s*report|strategy\s*evaluation|prepare\s*evaluation)\b",
                VoiceCommandIntent.PREPARE_STRATEGY_REPORT,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(review\s*strategy|latest\s*strategy|strategy\s*results?)\b",
                VoiceCommandIntent.REVIEW_STRATEGY_RESULTS,
                PermissionLevel.LEVEL_1_LOW_RISK
            ),
            (
                r"\b(backtest|run\s*backtest|test\s*strategy|back-test)\b",
                VoiceCommandIntent.BACKTEST_STRATEGY,
                PermissionLevel.LEVEL_2_CONTROLLED_RESEARCH
            )
        ]


    def extract_symbols(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts primary and optional secondary symbol from command text."""
        symbols_found = []
        
        # Check XAUUSD
        if re.search(r"\b(xauusd|gold|xau)\b", text, re.IGNORECASE):
            symbols_found.append("XAUUSD")
        # Check BTCUSD
        if re.search(r"\b(btcusd|bitcoin|btc)\b", text, re.IGNORECASE):
            symbols_found.append("BTCUSD")
        # Check ETHUSD
        if re.search(r"\b(ethusd|ethereum|eth)\b", text, re.IGNORECASE):
            symbols_found.append("ETHUSD")
        # Check EURUSD
        if re.search(r"\b(eurusd|euro|eur)\b", text, re.IGNORECASE):
            symbols_found.append("EURUSD")

        primary = symbols_found[0] if symbols_found else None
        secondary = symbols_found[1] if len(symbols_found) > 1 else None
        return primary, secondary

    def extract_timeframe(self, text: str) -> Optional[str]:
        """Extracts and normalizes timeframe string (M1, M5, M15, M30, H1, H4, D1)."""
        lower = text.lower()
        for pattern, tf in voice_settings.supported_timeframes.items():
            if re.search(r"\b" + re.escape(pattern) + r"\b", lower):
                return tf
        return None

    def interpret(self, raw_text: str, session_context: Optional[Dict[str, Any]] = None) -> VoiceCommand:
        """Parses speech text into a structured, validated, and permission-classified VoiceCommand."""
        clean_text = raw_text.strip()
        
        # 1. Extract symbols & timeframe
        symbol, sec_symbol = self.extract_symbols(clean_text)
        timeframe = self.extract_timeframe(clean_text)

        # Apply conversational context if symbol/timeframe missing
        if session_context:
            if not symbol and session_context.get("last_symbol"):
                symbol = session_context.get("last_symbol")
            if not timeframe and session_context.get("last_timeframe"):
                timeframe = session_context.get("last_timeframe")

        # Default timeframe to M15 if symbol was specified but timeframe omitted
        if symbol and not timeframe:
            timeframe = voice_settings.default_timeframe

        # 2. Match intent against allowlisted patterns
        matched_intent = VoiceCommandIntent.UNKNOWN_COMMAND
        permission_level = PermissionLevel.LEVEL_1_LOW_RISK

        for pattern, intent, perm in self.intent_patterns:
            if re.search(pattern, clean_text, re.IGNORECASE):
                matched_intent = intent
                permission_level = perm
                break

        # Check for conversational follow-ups like "now check BTCUSD" or "compare both"
        if matched_intent == VoiceCommandIntent.UNKNOWN_COMMAND and session_context:
            if re.search(r"\b(compare|compare\s*both)\b", clean_text, re.IGNORECASE):
                matched_intent = VoiceCommandIntent.COMPARE_MARKETS
                permission_level = PermissionLevel.LEVEL_1_LOW_RISK
            elif symbol:
                matched_intent = VoiceCommandIntent.ANALYSE_MARKET
                permission_level = PermissionLevel.LEVEL_1_LOW_RISK

        # 3. Check for Protected Operations (Level 3)
        is_blocked = False
        blocked_reason = None

        if permission_level == PermissionLevel.LEVEL_3_PROTECTED_ACTION:
            is_blocked = True
            if matched_intent == VoiceCommandIntent.CHANGE_RISK_LIMITS:
                blocked_reason = (
                    "Risk limit modifications are strictly prohibited via voice commands. "
                    "All risk parameters are protected by the Central Deterministic Risk Engine."
                )
            elif matched_intent == VoiceCommandIntent.ENABLE_LIVE_TRADING:
                blocked_reason = (
                    "Live trading cannot be enabled via voice. "
                    "It requires explicit web dashboard authorization with environment confirmation phrase."
                )
            elif matched_intent == VoiceCommandIntent.PLACE_LIVE_ORDER:
                blocked_reason = (
                    "Live orders cannot be placed or modified via voice alone. "
                    "Voice-only live trading is disabled to protect capital integrity."
                )
            else:
                blocked_reason = "Protected action: this operation requires authenticated web session controls."

        # 4. Construct validated VoiceCommand
        return VoiceCommand(
            intent=matched_intent,
            raw_text=clean_text,
            symbol=symbol,
            secondary_symbol=sec_symbol,
            timeframe=timeframe,
            permission_level=permission_level,
            requires_confirmation=(permission_level == PermissionLevel.LEVEL_2_CONTROLLED_RESEARCH),
            confirmation_prompt=(
                f"Confirm starting research operation: {matched_intent.value} on {symbol}?"
                if permission_level == PermissionLevel.LEVEL_2_CONTROLLED_RESEARCH else None
            ),
            is_blocked=is_blocked,
            blocked_reason=blocked_reason,
            session_id=session_context.get("session_id") if session_context else None
        )

command_interpreter = CommandInterpreter()
