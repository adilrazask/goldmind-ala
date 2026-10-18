"""Delta Exchange HMAC-SHA256 Authentication Module."""
from __future__ import annotations
import hmac
import hashlib
import time
from typing import Dict, Any, Tuple, Optional

class DeltaAuth:
    """Handles official Delta Exchange cryptographic signature generation and header building."""
    
    @staticmethod
    def generate_signature(api_secret: str, method: str, path: str, timestamp: str, body: str = "") -> str:
        """Calculates HMAC-SHA256 signature for Delta Exchange API v2.
        
        Formula:
        payload = METHOD + TIMESTAMP + PATH + BODY
        signature = hex(HMAC_SHA256(api_secret, payload))
        """
        if not api_secret:
            raise ValueError("Delta Exchange API Secret is required to generate signature.")
            
        clean_method = method.strip().upper()
        clean_path = path.strip()
        clean_body = body.strip() if body else ""
        
        message = f"{clean_method}{timestamp}{clean_path}{clean_body}"
        return hmac.new(
            api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def get_auth_headers(api_key: str, api_secret: str, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Builds authenticated request headers for Delta Exchange REST API."""
        if not api_key or not api_secret:
            raise ValueError("Both Delta Exchange API Key and API Secret are required for private endpoints.")
            
        timestamp = str(int(time.time()))
        signature = DeltaAuth.generate_signature(
            api_secret=api_secret,
            method=method,
            path=path,
            timestamp=timestamp,
            body=body
        )
        
        return {
            "api-key": api_key,
            "signature": signature,
            "timestamp": timestamp,
            "Content-Type": "application/json",
            "User-Agent": "GoldMind-ALA-Engine/1.0"
        }

    @staticmethod
    def build_ws_auth_message(api_key: str, api_secret: str) -> Dict[str, Any]:
        """Builds official 'key-auth' WebSocket payload for authenticating private channels.
        
        Per Delta Exchange documentation:
        method = 'GET'
        path = '/live'
        signature = HMAC_SHA256(secret, 'GET' + timestamp + '/live')
        """
        if not api_key or not api_secret:
            raise ValueError("Both API Key and API Secret are required for WebSocket authentication.")
            
        timestamp = str(int(time.time()))
        signature = DeltaAuth.generate_signature(
            api_secret=api_secret,
            method="GET",
            path="/live",
            timestamp=timestamp,
            body=""
        )
        
        return {
            "type": "key-auth",
            "payload": {
                "api-key": api_key,
                "signature": signature,
                "timestamp": timestamp
            }
        }
