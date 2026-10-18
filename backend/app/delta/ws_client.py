"""Delta Exchange Real-time WebSocket Client (Public Feeds & Private Channels)."""
from __future__ import annotations
import json
import time
import asyncio
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone

from backend.app.delta.config import delta_settings
from backend.app.delta.auth import DeltaAuth

class DeltaWebSocketClient:
    """Manages resilient WebSocket connections, subscriptions, authentication, and stale-data detection."""

    def __init__(self, settings=None):
        self.settings = settings or delta_settings
        self.is_running = False
        self.is_connected = False
        self.is_authenticated = False
        self.last_message_time = 0.0
        
        # Subscriptions
        self.subscribed_channels: List[Dict[str, Any]] = []
        self.subscribed_symbols: List[str] = ["BTCUSD", "ETHUSD", "BTC_USDT"]
        
        # In-memory Real-time Caches
        self.tickers: Dict[str, Dict[str, Any]] = {}
        self.order_books: Dict[str, Dict[str, Any]] = {}
        self.positions: Dict[str, Any] = {}
        self.orders: Dict[str, Any] = {}
        
        # Callbacks
        self.on_ticker_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.on_order_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.on_position_callbacks: List[Callable[[Dict[str, Any]], None]] = []

        # Threading
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def get_status(self) -> Dict[str, Any]:
        """Returns connection health, freshness, and channel subscription stats."""
        now = time.time()
        age_seconds = round(now - self.last_message_time, 2) if self.last_message_time > 0 else 999.0
        is_stale = age_seconds > self.settings.stale_data_threshold_seconds

        return {
            "is_connected": self.is_connected,
            "is_authenticated": self.is_authenticated,
            "data_freshness_status": "FRESH" if (self.is_connected and not is_stale) else "STALE",
            "last_message_age_seconds": age_seconds,
            "endpoint": self.settings.ws_public_url,
            "subscribed_symbols": self.subscribed_symbols,
            "cached_tickers_count": len(self.tickers),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def update_ticker_cache(self, symbol: str, data: Dict[str, Any]):
        """Updates real-time ticker cache and invokes registered callbacks."""
        self.last_message_time = time.time()
        self.tickers[symbol.upper()] = {
            "symbol": symbol.upper(),
            "close": float(data.get("close") or data.get("mark_price") or 0.0),
            "mark_price": float(data.get("mark_price") or data.get("close") or 0.0),
            "spot_price": float(data.get("spot_price") or data.get("close") or 0.0),
            "bid": float(data.get("quotes", {}).get("best_bid") or data.get("bid") or 0.0) if isinstance(data.get("quotes"), dict) else float(data.get("bid") or 0.0),
            "ask": float(data.get("quotes", {}).get("best_ask") or data.get("ask") or 0.0) if isinstance(data.get("quotes"), dict) else float(data.get("ask") or 0.0),
            "volume_24h": float(data.get("volume") or 0.0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "DELTA_WEBSOCKET"
        }
        for cb in self.on_ticker_callbacks:
            try:
                cb(self.tickers[symbol.upper()])
            except Exception:
                pass

    def start(self):
        """Starts the WebSocket worker thread."""
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the WebSocket client and closes connection."""
        self.is_running = False
        self.is_connected = False
        self.is_authenticated = False

    def _run_loop(self):
        """Worker thread loop hosting the async WebSocket client."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_and_listen())

    async def _connect_and_listen(self):
        """Manages WebSocket connection lifecycle, heartbeats, and message handling."""
        import websockets
        
        while self.is_running:
            try:
                ws_url = self.settings.ws_public_url
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
                    self.is_connected = True
                    self.last_message_time = time.time()
                    
                    # 1. Authenticate if API credentials exist
                    if self.settings.api_key and self.settings.api_secret:
                        try:
                            auth_msg = DeltaAuth.build_ws_auth_message(
                                api_key=self.settings.api_key,
                                api_secret=self.settings.api_secret
                            )
                            await ws.send(json.dumps(auth_msg))
                        except Exception:
                            pass

                    # 2. Subscribe to market tickers
                    sub_payload = {
                        "type": "subscribe",
                        "payload": {
                            "channels": [
                                {"name": "v2/ticker", "symbols": self.subscribed_symbols}
                            ]
                        }
                    }
                    await ws.send(json.dumps(sub_payload))

                    # 3. Listen for incoming messages
                    while self.is_running:
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=25.0)
                            msg = json.loads(raw)
                            self._handle_message(msg)
                        except asyncio.TimeoutError:
                            # Send heartbeat ping if idle
                            await ws.ping()
            except Exception:
                self.is_connected = False
                self.is_authenticated = False
                if self.is_running:
                    await asyncio.sleep(self.settings.reconnect_delay_seconds)

    def _handle_message(self, msg: Dict[str, Any]):
        """Dispatches incoming message packets to appropriate handlers."""
        self.last_message_time = time.time()
        msg_type = msg.get("type")
        
        if msg_type == "key-auth":
            if msg.get("success"):
                self.is_authenticated = True
        elif msg_type in ("v2/ticker", "ticker", "all_ticker"):
            symbol = msg.get("symbol")
            if symbol:
                self.update_ticker_cache(symbol, msg)
        elif "symbol" in msg and ("close" in msg or "mark_price" in msg):
            self.update_ticker_cache(msg["symbol"], msg)

delta_ws = DeltaWebSocketClient()
