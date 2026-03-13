"""
Binance Futures Trading Bot — Core Package
==========================================
Exposes the main client and order functions for use by CLI and Web UI.
"""

from .client import BinanceClient
from .orders import OrderManager

__all__ = ["BinanceClient", "OrderManager"]
