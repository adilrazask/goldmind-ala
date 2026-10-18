"""Delta Exchange Official REST API Client (Public & Private Endpoints)."""
from __future__ import annotations
import json
import time
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from backend.app.delta.config import delta_settings
from backend.app.delta.auth import DeltaAuth
from backend.app.market_data.manager import DataQualityAudit

class DeltaRestClient:
    """Official Delta Exchange REST API v2 Adapter."""

    def __init__(self, settings=None):
        self.settings = settings or delta_settings
        self.session = requests.Session()

    def _get_base_url(self) -> str:
        return self.settings.rest_base_url

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        auth_required: bool = False
    ) -> Dict[str, Any]:
        """Executes HTTP request with optional HMAC-SHA256 authentication."""
        url = f"{self._get_base_url()}{path}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "GoldMind-ALA-Engine/1.0"
        }
        body_str = ""

        if data:
            body_str = json.dumps(data)
            headers["Content-Type"] = "application/json"

        # Calculate authentication headers if required
        if auth_required:
            if not self.settings.api_key or not self.settings.api_secret:
                raise ValueError("Delta Exchange API credentials required for private endpoints.")
            auth_headers = DeltaAuth.get_auth_headers(
                api_key=self.settings.api_key,
                api_secret=self.settings.api_secret,
                method=method,
                path=path,
                body=body_str
            )
            headers.update(auth_headers)

        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=params,
                data=body_str if data else None,
                headers=headers,
                timeout=self.settings.request_timeout_seconds
            )
            
            # Rate limiting or server error handling
            if resp.status_code == 429:
                return {
                    "success": False,
                    "error": "RATE_LIMITED",
                    "status_code": 429,
                    "message": "Delta Exchange rate limit reached. Backing off."
                }
            
            if resp.status_code >= 400:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message") or err_json.get("message") or resp.text
                except Exception:
                    err_msg = resp.text
                return {
                    "success": False,
                    "error": "HTTP_ERROR",
                    "status_code": resp.status_code,
                    "message": err_msg
                }

            res_json = resp.json()
            return {"success": True, "data": res_json}
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": "NETWORK_EXCEPTION",
                "message": f"Connection to {url} failed: {str(e)}"
            }

    # ----------------------------------------------------
    # 1. Connectivity & Product Discovery
    # ----------------------------------------------------
    def check_connectivity(self) -> Dict[str, Any]:
        """Pings Delta Exchange REST API and computes round-trip latency."""
        start = time.time()
        res = self._request("GET", "/v2/products")
        latency_ms = round((time.time() - start) * 1000, 2)
        
        is_ok = res.get("success", False)
        products_count = len(res.get("data", {}).get("result", [])) if is_ok else 0

        return {
            "online": is_ok,
            "latency_ms": latency_ms,
            "environment": self.settings.environment.value,
            "endpoint": self._get_base_url(),
            "products_discovered": products_count,
            "error": res.get("message") if not is_ok else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_products(self) -> List[Dict[str, Any]]:
        """Retrieves and standardizes full tradeable product catalogue from Delta Exchange."""
        res = self._request("GET", "/v2/products")
        if not res.get("success"):
            return []

        raw_products = res.get("data", {}).get("result", [])
        standardized = []
        for p in raw_products:
            standardized.append({
                "id": p.get("id"),
                "symbol": p.get("symbol"),
                "contract_type": p.get("contract_type"),
                "underlying_asset": p.get("underlying_asset", {}).get("symbol") if isinstance(p.get("underlying_asset"), dict) else p.get("underlying_asset"),
                "quoting_asset": p.get("quoting_asset", {}).get("symbol") if isinstance(p.get("quoting_asset"), dict) else p.get("quoting_asset"),
                "settling_asset": p.get("settling_asset", {}).get("symbol") if isinstance(p.get("settling_asset"), dict) else p.get("settling_asset"),
                "tick_size": float(p.get("tick_size") or 0.1),
                "contract_value": float(p.get("contract_value") or 1.0),
                "min_order_size": float(p.get("min_order_size") or 1.0),
                "trading_status": p.get("trading_status", "operational"),
                "description": p.get("description", p.get("symbol"))
            })
        return standardized

    def get_tickers(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves real-time tickers, mark prices, and 24h volumes."""
        params = {"contract_types": "perpetual_futures,futures,spot"} if not symbol else None
        res = self._request("GET", "/v2/tickers", params=params)
        if not res.get("success"):
            return []

        raw_tickers = res.get("data", {}).get("result", [])
        tickers = []
        for t in raw_tickers:
            sym = t.get("symbol")
            if symbol and sym != symbol:
                continue
            tickers.append({
                "symbol": sym,
                "product_id": t.get("product_id"),
                "close": float(t.get("close") or 0.0),
                "mark_price": float(t.get("mark_price") or t.get("close") or 0.0),
                "spot_price": float(t.get("spot_price") or t.get("mark_price") or 0.0),
                "bid": float(t.get("quotes", {}).get("best_bid") or 0.0) if isinstance(t.get("quotes"), dict) else 0.0,
                "ask": float(t.get("quotes", {}).get("best_ask") or 0.0) if isinstance(t.get("quotes"), dict) else 0.0,
                "high_24h": float(t.get("high") or 0.0),
                "low_24h": float(t.get("low") or 0.0),
                "volume_24h": float(t.get("volume") or 0.0),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        return tickers

    # ----------------------------------------------------
    # 2. Historical Market Data
    # ----------------------------------------------------
    def get_candles(
        self,
        symbol: str,
        resolution: str = "15m",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 300
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Retrieves historical OHLCV candlesticks from Delta Exchange with data quality audit."""
        now_ts = int(time.time())
        if not end_time:
            end_time = now_ts
        if not start_time:
            # Default to appropriate lookback based on resolution
            res_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}.get(resolution, 15)
            start_time = end_time - (res_minutes * 60 * limit)

        params = {
            "symbol": symbol,
            "resolution": resolution,
            "start": start_time,
            "end": end_time
        }
        res = self._request("GET", "/v2/history/candles", params=params)
        if not res.get("success"):
            return [], {"is_valid": False, "error": res.get("message")}

        raw_candles = res.get("data", {}).get("result", [])
        candles = []
        for c in raw_candles:
            # Delta returns [time, open, high, low, close, volume] or dict
            if isinstance(c, list) and len(c) >= 5:
                ts = datetime.fromtimestamp(c[0], tz=timezone.utc).isoformat()
                candles.append({
                    "timestamp": ts,
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5]) if len(c) > 5 else 0.0,
                    "source": "DELTA_EXCHANGE"
                })
            elif isinstance(c, dict):
                epoch = c.get("time") or c.get("timestamp") or 0
                ts = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat() if isinstance(epoch, (int, float)) else str(epoch)
                candles.append({
                    "timestamp": ts,
                    "open": float(c.get("open", 0)),
                    "high": float(c.get("high", 0)),
                    "low": float(c.get("low", 0)),
                    "close": float(c.get("close", 0)),
                    "volume": float(c.get("volume", 0)),
                    "source": "DELTA_EXCHANGE"
                })

        # Sort ascending by timestamp
        candles.sort(key=lambda x: x["timestamp"])
        audit = DataQualityAudit.audit_candles(candles, expected_timeframe_minutes={"15m": 15, "1h": 60, "1d": 1440}.get(resolution, 15))
        return candles, audit

    # ----------------------------------------------------
    # 3. Account Balances, Positions & Orders (Private)
    # ----------------------------------------------------
    def get_wallet_balances(self) -> List[Dict[str, Any]]:
        """Retrieves actual wallet balances from Delta Exchange."""
        res = self._request("GET", "/v2/wallet/balances", auth_required=True)
        if not res.get("success"):
            return []
        return res.get("data", {}).get("result", [])

    def get_positions(self) -> List[Dict[str, Any]]:
        """Retrieves authoritative open positions from Delta Exchange."""
        res = self._request("GET", "/v2/positions", auth_required=True)
        if not res.get("success"):
            return []
        return res.get("data", {}).get("result", [])

    def get_open_orders(self, product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves active orders from Delta Exchange."""
        params = {"product_id": product_id} if product_id else None
        res = self._request("GET", "/v2/orders", params=params, auth_required=True)
        if not res.get("success"):
            return []
        return res.get("data", {}).get("result", [])

    def place_order(
        self,
        product_id: int,
        size: float,
        side: str, # "buy" or "sell"
        order_type: str = "limit_order", # "market_order", "limit_order"
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """Submits an order to Delta Exchange."""
        payload = {
            "product_id": product_id,
            "size": int(size) if float(size).is_integer() else size,
            "side": side.lower(),
            "order_type": order_type,
            "reduce_only": reduce_only
        }
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        if stop_price is not None:
            payload["stop_price"] = str(stop_price)
        if client_order_id:
            payload["client_order_id"] = client_order_id

        return self._request("POST", "/v2/orders", data=payload, auth_required=True)

    def cancel_order(self, order_id: Optional[int] = None, product_id: Optional[int] = None) -> Dict[str, Any]:
        """Cancels an existing order by order_id or product_id."""
        payload = {}
        if order_id:
            payload["id"] = order_id
        if product_id:
            payload["product_id"] = product_id
        return self._request("DELETE", "/v2/orders", data=payload, auth_required=True)

delta_client = DeltaRestClient()
