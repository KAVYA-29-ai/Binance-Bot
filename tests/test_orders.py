"""
tests/test_orders.py
====================
Unit tests for bot/orders.py using pytest-mock.

BinanceClient is mocked so no real API calls are made.

Run with:
    pytest tests/test_orders.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from bot.orders import OrderManager
from bot.client import BinanceAPIError, BinanceNetworkError


# ── Fixtures ──────────────────────────────────────────────────────────────────

FAKE_MARKET_RESPONSE = {
    "orderId":     123456789,
    "symbol":      "BTCUSDT",
    "side":        "BUY",
    "type":        "MARKET",
    "origQty":     "0.01",
    "executedQty": "0.01",
    "price":       "0",
    "avgPrice":    "43210.50",
    "stopPrice":   "0",
    "status":      "FILLED",
    "timeInForce": "GTC",
}

FAKE_LIMIT_RESPONSE = {
    "orderId":     987654321,
    "symbol":      "BTCUSDT",
    "side":        "SELL",
    "type":        "LIMIT",
    "origQty":     "0.01",
    "executedQty": "0.00",
    "price":       "50000.00",
    "avgPrice":    "0",
    "stopPrice":   "0",
    "status":      "NEW",
    "timeInForce": "GTC",
}

FAKE_STOP_RESPONSE = {
    "orderId":     111222333,
    "symbol":      "BTCUSDT",
    "side":        "SELL",
    "type":        "STOP",
    "origQty":     "0.01",
    "executedQty": "0.00",
    "price":       "39500.00",
    "avgPrice":    "0",
    "stopPrice":   "40000.00",
    "status":      "NEW",
    "timeInForce": "GTC",
}


@pytest.fixture
def mock_client():
    """Return a MagicMock that stands in for BinanceClient."""
    return MagicMock()


@pytest.fixture
def order_manager(mock_client):
    """Return an OrderManager wired to the mock client."""
    return OrderManager(mock_client)


# ── Market order tests ────────────────────────────────────────────────────────

class TestPlaceMarketOrder:
    def test_success_returns_order_id(self, order_manager, mock_client):
        mock_client.place_order.return_value = FAKE_MARKET_RESPONSE
        result = order_manager.place_market_order("BTCUSDT", "BUY", 0.01)
        assert result["orderId"] == 123456789
        assert result["status"]  == "FILLED"

    def test_calls_client_with_correct_params(self, order_manager, mock_client):
        mock_client.place_order.return_value = FAKE_MARKET_RESPONSE
        order_manager.place_market_order("BTCUSDT", "BUY", 0.01)
        call_kwargs = mock_client.place_order.call_args[1]
        assert call_kwargs["symbol"]   == "BTCUSDT"
        assert call_kwargs["side"]     == "BUY"
        assert call_kwargs["type"]     == "MARKET"
        assert call_kwargs["quantity"] == 0.01

    def test_api_error_is_raised(self, order_manager, mock_client):
        mock_client.place_order.side_effect = BinanceAPIError(-1013, "Invalid quantity")
        with pytest.raises(BinanceAPIError, match="Invalid quantity"):
            order_manager.place_market_order("BTCUSDT", "BUY", 0.01)

    def test_network_error_is_raised(self, order_manager, mock_client):
        mock_client.place_order.side_effect = BinanceNetworkError("Connection timeout")
        with pytest.raises(BinanceNetworkError):
            order_manager.place_market_order("BTCUSDT", "BUY", 0.01)

    def test_invalid_symbol_raises_before_api_call(self, order_manager, mock_client):
        with pytest.raises(ValueError):
            order_manager.place_market_order("INVALID", "BUY", 0.01)
        mock_client.place_order.assert_not_called()

    def test_invalid_quantity_raises_before_api_call(self, order_manager, mock_client):
        with pytest.raises(ValueError):
            order_manager.place_market_order("BTCUSDT", "BUY", -5)
        mock_client.place_order.assert_not_called()


# ── Limit order tests ─────────────────────────────────────────────────────────

class TestPlaceLimitOrder:
    def test_success_returns_order_id(self, order_manager, mock_client):
        mock_client.place_order.return_value = FAKE_LIMIT_RESPONSE
        result = order_manager.place_limit_order("BTCUSDT", "SELL", 0.01, 50000)
        assert result["orderId"] == 987654321
        assert result["status"]  == "NEW"

    def test_calls_client_with_correct_params(self, order_manager, mock_client):
        mock_client.place_order.return_value = FAKE_LIMIT_RESPONSE
        order_manager.place_limit_order("BTCUSDT", "SELL", 0.01, 50000)
        call_kwargs = mock_client.place_order.call_args[1]
        assert call_kwargs["type"]        == "LIMIT"
        assert call_kwargs["price"]       == 50000.0
        assert call_kwargs["timeInForce"] == "GTC"

    def test_missing_price_raises_before_api_call(self, order_manager, mock_client):
        with pytest.raises(ValueError, match="Price is required"):
            order_manager.place_limit_order("BTCUSDT", "SELL", 0.01, price=None)
        mock_client.place_order.assert_not_called()

    def test_api_error_is_raised(self, order_manager, mock_client):
        mock_client.place_order.side_effect = BinanceAPIError(-2010, "Order rejected")
        with pytest.raises(BinanceAPIError):
            order_manager.place_limit_order("BTCUSDT", "SELL", 0.01, 50000)


# ── Stop-Limit order tests ────────────────────────────────────────────────────

class TestPlaceStopLimitOrder:
    def test_success_returns_order_id(self, order_manager, mock_client):
        mock_client.place_order.return_value = FAKE_STOP_RESPONSE
        result = order_manager.place_stop_limit_order(
            "BTCUSDT", "SELL", 0.01, price=39500, stop_price=40000
        )
        assert result["orderId"] == 111222333

    def test_calls_client_with_stop_market_type(self, order_manager, mock_client):
        mock_client.place_order.return_value = FAKE_STOP_RESPONSE
        order_manager.place_stop_limit_order(
            "BTCUSDT", "SELL", 0.01, price=None, stop_price=40000
        )
        call_kwargs = mock_client.place_order.call_args[1]
        assert call_kwargs["type"]      == "STOP_MARKET"
        assert call_kwargs["stopPrice"] == 40000.0

    def test_same_price_and_stop_raises(self, order_manager, mock_client):
        with pytest.raises(ValueError, match="must be different"):
            order_manager.place_stop_limit_order(
                "BTCUSDT", "SELL", 0.01, price=40000, stop_price=40000
            )
        mock_client.place_order.assert_not_called()


# ── Utility method tests ──────────────────────────────────────────────────────

class TestGetCurrentPrice:
    def test_returns_float(self, order_manager, mock_client):
        mock_client.get_ticker_price.return_value = {"symbol": "BTCUSDT", "price": "43000.50"}
        price = order_manager.get_current_price("BTCUSDT")
        assert isinstance(price, float)
        assert price == 43000.50

    def test_network_error_propagates(self, order_manager, mock_client):
        mock_client.get_ticker_price.side_effect = BinanceNetworkError("Timeout")
        with pytest.raises(BinanceNetworkError):
            order_manager.get_current_price("BTCUSDT")


class TestGetOpenOrders:
    def test_returns_list(self, order_manager, mock_client):
        mock_client.get_open_orders.return_value = [{"orderId": 1}, {"orderId": 2}]
        orders = order_manager.get_open_orders("BTCUSDT")
        assert len(orders) == 2

    def test_empty_list_when_no_orders(self, order_manager, mock_client):
        mock_client.get_open_orders.return_value = []
        orders = order_manager.get_open_orders("BTCUSDT")
        assert orders == []
