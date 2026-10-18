"""Configuration and Environment Settings for Delta Exchange Integration."""
from __future__ import annotations
import os
import re
from typing import Dict, Any, Optional
from enum import Enum

class DeltaEnvironment(str, Enum):
    INDIA_PRODUCTION = "INDIA_PRODUCTION"
    INDIA_TESTNET = "INDIA_TESTNET"
    GLOBAL_PRODUCTION = "GLOBAL_PRODUCTION"
    GLOBAL_TESTNET = "GLOBAL_TESTNET"

# Official documented base URLs for Delta Exchange
DEFAULT_URLS = {
    DeltaEnvironment.INDIA_PRODUCTION: {
        "rest": "https://api.india.delta.exchange",
        "ws_public": "wss://socket.india.delta.exchange",
        "ws_private": "wss://socket.india.delta.exchange",
        "docs": "https://docs.delta.exchange/"
    },
    DeltaEnvironment.INDIA_TESTNET: {
        "rest": "https://cdn-ind.testnet.deltaex.org",
        "ws_public": "wss://socket-ind.testnet.deltaex.org",
        "ws_private": "wss://socket-ind.testnet.deltaex.org",
        "docs": "https://docs.delta.exchange/"
    },
    DeltaEnvironment.GLOBAL_PRODUCTION: {
        "rest": "https://api.delta.exchange",
        "ws_public": "wss://socket.delta.exchange",
        "ws_private": "wss://socket.delta.exchange",
        "docs": "https://docs.delta.exchange/"
    },
    DeltaEnvironment.GLOBAL_TESTNET: {
        "rest": "https://testnet-api.delta.exchange",
        "ws_public": "wss://socket.delta.exchange",
        "ws_private": "wss://socket.delta.exchange",
        "docs": "https://docs.delta.exchange/"
    }
}

class DeltaSettings:
    """Manages Delta Exchange credentials, endpoints, and operating policies."""
    def __init__(self):
        self.reload()

    def reload(self):
        # 1. Environment & Target Market
        env_raw = os.getenv("DELTA_ENVIRONMENT", "INDIA_TESTNET").strip().upper()
        try:
            self.environment = DeltaEnvironment(env_raw)
        except ValueError:
            self.environment = DeltaEnvironment.INDIA_TESTNET

        defaults = DEFAULT_URLS[self.environment]
        self.rest_base_url = os.getenv("DELTA_API_BASE_URL", defaults["rest"]).rstrip("/")
        self.ws_public_url = os.getenv("DELTA_PUBLIC_WEBSOCKET_URL", defaults["ws_public"])
        self.ws_private_url = os.getenv("DELTA_PRIVATE_WEBSOCKET_URL", defaults["ws_private"])

        # 2. Authentication Credentials
        self.api_key = os.getenv("DELTA_API_KEY", "").strip()
        self.api_secret = os.getenv("DELTA_API_SECRET", "").strip()

        # 3. Operating Execution Mode: "PAPER" (default) or "LIVE"
        self.trading_mode = os.getenv("DELTA_TRADING_MODE", "PAPER").strip().upper()
        if self.trading_mode not in ("PAPER", "LIVE"):
            self.trading_mode = "PAPER"

        # 4. Strict Safety Guard: Live Trading requires deliberate double opt-in
        live_opt_in = os.getenv("DELTA_ENABLE_LIVE_TRADING", "NO").strip().upper()
        self.is_live_enabled = (self.trading_mode == "LIVE" and live_opt_in == "YES_I_ACCEPT_EXCHANGE_RISK")

        # 5. Rate Limits and Timeouts
        self.request_timeout_seconds = float(os.getenv("DELTA_REQUEST_TIMEOUT", "10.0"))
        self.stale_data_threshold_seconds = float(os.getenv("DELTA_STALE_DATA_THRESHOLD", "15.0"))
        self.reconnect_delay_seconds = float(os.getenv("DELTA_RECONNECT_DELAY", "3.0"))
        self.max_reconnect_attempts = int(os.getenv("DELTA_MAX_RECONNECT", "5"))

    def validate_configuration(self) -> Dict[str, Any]:
        """Validates configuration parameters and returns health audit."""
        issues = []
        is_india = "INDIA" in self.environment.value
        has_india_domain = "india" in self.rest_base_url or "ind" in self.rest_base_url

        if is_india and not has_india_domain:
            issues.append(
                f"Configuration Mismatch: Environment is {self.environment.value} but REST URL {self.rest_base_url} does not point to an India endpoint."
            )

        if self.trading_mode == "LIVE":
            if not self.api_key or not self.api_secret:
                issues.append("Live trading mode selected, but DELTA_API_KEY or DELTA_API_SECRET is missing.")
            if not self.is_live_enabled:
                issues.append("DELTA_TRADING_MODE is LIVE, but DELTA_ENABLE_LIVE_TRADING != 'YES_I_ACCEPT_EXCHANGE_RISK'.")

        has_keys = bool(self.api_key and self.api_secret)
        return {
            "valid": len(issues) == 0,
            "environment": self.environment.value,
            "rest_base_url": self.rest_base_url,
            "ws_public_url": self.ws_public_url,
            "trading_mode": self.trading_mode,
            "is_live_authorized": self.is_live_enabled,
            "has_credentials": has_keys,
            "masked_api_key": self.get_masked_api_key(),
            "issues": issues
        }

    def get_masked_api_key(self) -> str:
        """Returns masked API key for UI and logs (never displays full key)."""
        if not self.api_key:
            return "NOT_CONFIGURED"
        if len(self.api_key) <= 8:
            return "********"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"

delta_settings = DeltaSettings()
