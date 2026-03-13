"""
bot/client.py
=============
Binance Futures Testnet client — built on top of the python-binance library.

Responsibilities
----------------
- Load API credentials from environment variables (.env).
- Connect to Binance USDT-M Futures Testnet.
- Wrap python-binance calls with clean error handling and logging.

Environment variables required (set in .env)
--------------------------------------------
BINANCE_API_KEY    – your testnet API key
BINANCE_API_SECRET – your testnet secret key
"""

from __future__ import annotations

import os
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from .logging_config import setup_logger

# ── Setup ─────────────────────────────────────────────────────────────────────

load_dotenv()

logger = setup_logger("trading_bot")

TESTNET_FUTURES_URL = "https://testnet.binancefuture.com"


# ── Custom exceptions ─────────────────────────────────────────────────────────


class BinanceAPIError(Exception):
    """Raised when Binance returns an API-level error."""
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceNetworkError(Exception):
    """Raised on network-level failures."""


class BinanceAuthError(Exception):
    """Raised when API credentials are missing or invalid."""


# ── Client ────────────────────────────────────────────────────────────────────


class BinanceClient:
    """
    Authenticated Binance Futures Testnet client using python-binance.

    Example
    -------
    >>> client = BinanceClient()
    >>> price = client.get_ticker_price("BTCUSDT")
    """

    def __init__(self) -> None:
        self.api_key    = os.getenv("BINANCE_API_KEY", "").strip()
        self.api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
        self._validate_credentials()

        # Point python-binance to the Futures Testnet
        self._client = Client(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=False,   # we set the URL manually below
        )
        # Override futures base URL to testnet
        self._client.FUTURES_URL = TESTNET_FUTURES_URL + "/fapi"

        logger.info("BinanceClient ready — testnet: %s", TESTNET_FUTURES_URL)

    # ── Credential check ──────────────────────────────────────────────────────

    def _validate_credentials(self) -> None:
        if not self.api_key:
            raise BinanceAuthError(
                "BINANCE_API_KEY is not set. Add it to your .env file."
            )
        if not self.api_secret:
            raise BinanceAuthError(
                "BINANCE_API_SECRET is not set. Add it to your .env file."
            )

    # ── Internal wrapper ──────────────────────────────────────────────────────

    def _call(self, fn, *args, **kwargs) -> Any:
        """
        Wrap any python-binance call with unified error handling.

        Args:
            fn: The python-binance method to call.
            *args / **kwargs: Forwarded to fn.

        Returns:
            API response (dict or list).

        Raises:
            BinanceAPIError    : API-level rejection.
            BinanceNetworkError: Connectivity failure.
        """
        try:
            result = fn(*args, **kwargs)
            logger.debug("API call success: %s | response: %s", fn.__name__, result)
            return result
        except BinanceAPIException as exc:
            logger.error("Binance API error %s: %s", exc.code, exc.message)
            raise BinanceAPIError(exc.code, exc.message) from exc
        except BinanceRequestException as exc:
            logger.error("Binance request/network error: %s", exc)
            raise BinanceNetworkError(str(exc)) from exc
        except Exception as exc:
            logger.error("Unexpected client error: %s", exc)
            raise BinanceNetworkError(f"Unexpected error: {exc}") from exc

    # ── Public API methods ────────────────────────────────────────────────────

    def get_ticker_price(self, symbol: str) -> dict:
        """Return the latest futures price for a symbol."""
        logger.debug("Fetching futures ticker price for %s", symbol)
        return self._call(
            self._client.futures_symbol_ticker, symbol=symbol
        )

    def get_account_info(self) -> dict:
        """Return futures account balances and positions."""
        logger.info("Fetching futures account info")
        return self._call(self._client.futures_account)

    def get_exchange_info(self) -> dict:
        """Return futures exchange metadata (symbols, filters)."""
        logger.info("Fetching futures exchange info")
        return self._call(self._client.futures_exchange_info)

    def place_order(self, **kwargs) -> dict:
        """
        Place a futures order.

        Keyword Args:
            symbol      : e.g. "BTCUSDT"
            side        : "BUY" or "SELL"
            type        : "MARKET", "LIMIT", "STOP" etc.
            quantity    : float
            price       : float (LIMIT orders)
            stopPrice   : float (STOP orders)
            timeInForce : "GTC", "IOC", "FOK"

        Returns:
            dict: Order confirmation from Binance.
        """
        logger.info(
            "Placing futures order — symbol=%s side=%s type=%s qty=%s",
            kwargs.get("symbol"),
            kwargs.get("side"),
            kwargs.get("type"),
            kwargs.get("quantity"),
        )
        response = self._call(self._client.futures_create_order, **kwargs)
        logger.info("Order accepted — orderId: %s", response.get("orderId"))
        return response

    def get_open_orders(self, symbol: str | None = None) -> list:
        """Return open futures orders, optionally filtered by symbol."""
        params = {"symbol": symbol} if symbol else {}
        logger.info("Fetching open futures orders — symbol: %s", symbol or "ALL")
        return self._call(self._client.futures_get_open_orders, **params)

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query a specific futures order by ID."""
        logger.info("Fetching order %d for %s", order_id, symbol)
        return self._call(
            self._client.futures_get_order, symbol=symbol, orderId=order_id
        )

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open futures order."""
        logger.info("Cancelling order %d for %s", order_id, symbol)
        return self._call(
            self._client.futures_cancel_order, symbol=symbol, orderId=order_id
        )
