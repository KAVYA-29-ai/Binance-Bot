"""
tests/test_validators.py
========================
Unit tests for bot/validators.py.

Run with:
    pytest tests/test_validators.py -v
"""

import pytest
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_order_inputs,
)


# ── validate_symbol ───────────────────────────────────────────────────────────

class TestValidateSymbol:
    def test_valid_uppercase(self):
        assert validate_symbol("BTCUSDT") == "BTCUSDT"

    def test_valid_lowercase_converted(self):
        assert validate_symbol("btcusdt") == "BTCUSDT"

    def test_valid_eth(self):
        assert validate_symbol("ETHUSDT") == "ETHUSDT"

    def test_valid_bnb_quote(self):
        assert validate_symbol("ETHBNB") == "ETHBNB"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_symbol("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_symbol("   ")

    def test_bad_quote_currency_raises(self):
        with pytest.raises(ValueError, match="quote currency"):
            validate_symbol("BTCABC")

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            validate_symbol("BTC")


# ── validate_side ─────────────────────────────────────────────────────────────

class TestValidateSide:
    def test_buy_uppercase(self):
        assert validate_side("BUY") == "BUY"

    def test_sell_uppercase(self):
        assert validate_side("SELL") == "SELL"

    def test_buy_lowercase_converted(self):
        assert validate_side("buy") == "BUY"

    def test_sell_mixed_case(self):
        assert validate_side("Sell") == "SELL"

    def test_invalid_hold_raises(self):
        with pytest.raises(ValueError, match="Invalid side"):
            validate_side("HOLD")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_side("")


# ── validate_order_type ───────────────────────────────────────────────────────

class TestValidateOrderType:
    def test_market(self):
        assert validate_order_type("MARKET") == "MARKET"

    def test_limit(self):
        assert validate_order_type("LIMIT") == "LIMIT"

    def test_stop_limit(self):
        assert validate_order_type("STOP_LIMIT") == "STOP_LIMIT"

    def test_lowercase_converted(self):
        assert validate_order_type("market") == "MARKET"

    def test_invalid_twap_raises(self):
        with pytest.raises(ValueError, match="Invalid order type"):
            validate_order_type("TWAP")

    def test_invalid_oco_raises(self):
        with pytest.raises(ValueError, match="Invalid order type"):
            validate_order_type("OCO")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_order_type("")


# ── validate_quantity ─────────────────────────────────────────────────────────

class TestValidateQuantity:
    def test_valid_float(self):
        assert validate_quantity(0.01) == 0.01

    def test_valid_string_number(self):
        assert validate_quantity("0.5") == 0.5

    def test_valid_integer(self):
        assert validate_quantity(1) == 1.0

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="greater than 0"):
            validate_quantity(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="greater than 0"):
            validate_quantity(-1)

    def test_non_numeric_string_raises(self):
        with pytest.raises(ValueError, match="not a valid number"):
            validate_quantity("abc")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_quantity(None)

    def test_below_minimum_raises(self):
        with pytest.raises(ValueError, match="minimum"):
            validate_quantity(0.00001)


# ── validate_price ────────────────────────────────────────────────────────────

class TestValidatePrice:
    def test_valid_price(self):
        assert validate_price(50000) == 50000.0

    def test_valid_string_price(self):
        assert validate_price("1234.56") == 1234.56

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="greater than 0"):
            validate_price(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="greater than 0"):
            validate_price(-100)

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="not a valid number"):
            validate_price("cheap")

    def test_custom_field_name_in_error(self):
        with pytest.raises(ValueError, match="Stop price"):
            validate_price(-1, field_name="Stop price")


# ── validate_order_inputs ─────────────────────────────────────────────────────

class TestValidateOrderInputs:
    def test_market_order_valid(self):
        result = validate_order_inputs("BTCUSDT", "BUY", "MARKET", 0.01)
        assert result["symbol"]     == "BTCUSDT"
        assert result["side"]       == "BUY"
        assert result["order_type"] == "MARKET"
        assert result["quantity"]   == 0.01
        assert "price" not in result

    def test_limit_order_valid(self):
        result = validate_order_inputs("ETHUSDT", "SELL", "LIMIT", 0.1, price=2000)
        assert result["price"] == 2000.0

    def test_limit_order_missing_price_raises(self):
        with pytest.raises(ValueError, match="Price is required"):
            validate_order_inputs("BTCUSDT", "BUY", "LIMIT", 0.01)

    def test_stop_limit_order_valid(self):
        result = validate_order_inputs(
            "BTCUSDT", "BUY", "STOP_LIMIT", 0.01,
            price=31000, stop_price=30500
        )
        assert result["price"]      == 31000.0
        assert result["stop_price"] == 30500.0

    def test_stop_limit_missing_stop_price_raises(self):
        with pytest.raises(ValueError, match="Stop price is required"):
            validate_order_inputs("BTCUSDT", "BUY", "STOP_LIMIT", 0.01, price=31000)

    def test_stop_limit_same_prices_raises(self):
        with pytest.raises(ValueError, match="must be different"):
            validate_order_inputs(
                "BTCUSDT", "BUY", "STOP_LIMIT", 0.01,
                price=30000, stop_price=30000
            )

    def test_invalid_symbol_raises(self):
        with pytest.raises(ValueError):
            validate_order_inputs("INVALID", "BUY", "MARKET", 0.01)

    def test_invalid_side_raises(self):
        with pytest.raises(ValueError):
            validate_order_inputs("BTCUSDT", "HOLD", "MARKET", 0.01)
