"""
bot/validators.py
=================
Input-validation helpers for all order parameters.

Every function raises ValueError with a human-readable message on failure,
so callers (CLI and Web UI) can surface the error without extra logic.

Supported order typesx
---------------------
MARKET     – quantity only, no price needed
LIMIT      – quantity + price
STOP_LIMIT – quantity + price (limit) + stop_price
"""

from __future__ import annotations

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}

# Binance Futures minimum notional / qty guardrails (conservative defaults)
MIN_QUANTITY = 0.001
MAX_QUANTITY = 1_000_000.0
MIN_PRICE = 0.01
MAX_PRICE = 10_000_000.0


# ── Public validators ─────────────────────────────────────────────────────────


def validate_symbol(symbol: str) -> str:
    """
    Normalise and validate a trading-pair symbol.

    Rules:
      - Must be a non-empty string.
      - Converted to uppercase.
      - Must end with a recognised quote currency (USDT, BUSD, BTC, ETH, BNB).

    Args:
        symbol: Raw symbol string, e.g. "btcusdt" or "BTCUSDT".

    Returns:
        str: Upper-cased, validated symbol.

    Raises:
        ValueError: If the symbol is empty or uses an unsupported quote currency.
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty.")

    symbol = symbol.strip().upper()

    valid_quotes = ("USDT", "BUSD", "BTC", "ETH", "BNB")
    if not any(symbol.endswith(q) for q in valid_quotes):
        raise ValueError(
            f"Symbol '{symbol}' does not end with a supported quote currency "
            f"({', '.join(valid_quotes)}). Example: BTCUSDT"
        )

    if len(symbol) < 5:
        raise ValueError(
            f"Symbol '{symbol}' is too short. Expected format: BTCUSDT"
        )

    return symbol


def validate_side(side: str) -> str:
    """
    Validate the order side.

    Args:
        side: "BUY" or "SELL" (case-insensitive).

    Returns:
        str: Upper-cased side string.

    Raises:
        ValueError: If the side is not BUY or SELL.
    """
    if not side or not side.strip():
        raise ValueError("Side cannot be empty.")

    side = side.strip().upper()

    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}"
        )

    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate the order type.

    Args:
        order_type: "MARKET", "LIMIT", or "STOP_LIMIT" (case-insensitive).

    Returns:
        str: Upper-cased order type.

    Raises:
        ValueError: If the order type is not recognised.
    """
    if not order_type or not order_type.strip():
        raise ValueError("Order type cannot be empty.")

    order_type = order_type.strip().upper()

    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(VALID_ORDER_TYPES)}"
        )

    return order_type


def validate_quantity(quantity: float | str) -> float:
    """
    Validate the order quantity.

    Args:
        quantity: Numeric quantity (float or numeric string).

    Returns:
        float: Validated quantity.

    Raises:
        ValueError: If quantity is not a positive number within allowed range.
    """
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(
            f"Quantity '{quantity}' is not a valid number."
        )

    if qty <= 0:
        raise ValueError("Quantity must be greater than 0.")

    if qty < MIN_QUANTITY:
        raise ValueError(
            f"Quantity {qty} is below the minimum allowed ({MIN_QUANTITY})."
        )

    if qty > MAX_QUANTITY:
        raise ValueError(
            f"Quantity {qty} exceeds the maximum allowed ({MAX_QUANTITY:,})."
        )

    return qty


def validate_price(price: float | str, field_name: str = "Price") -> float:
    """
    Validate a price value (used for both limit price and stop price).

    Args:
        price     : Numeric price (float or numeric string).
        field_name: Label used in error messages (default "Price").

    Returns:
        float: Validated price.

    Raises:
        ValueError: If price is not a positive number within allowed range.
    """
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name} '{price}' is not a valid number."
        )

    if p <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")

    if p < MIN_PRICE:
        raise ValueError(
            f"{field_name} {p} is below the minimum allowed ({MIN_PRICE})."
        )

    if p > MAX_PRICE:
        raise ValueError(
            f"{field_name} {p} exceeds the maximum allowed ({MAX_PRICE:,})."
        )

    return p


def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float | str,
    price: float | str | None = None,
    stop_price: float | str | None = None,
) -> dict:
    """
    Run all validations for a single order and return a clean params dict.

    Args:
        symbol     : Trading pair, e.g. "BTCUSDT".
        side       : "BUY" or "SELL".
        order_type : "MARKET", "LIMIT", or "STOP_LIMIT".
        quantity   : Order quantity.
        price      : Limit price — required for LIMIT and STOP_LIMIT orders.
        stop_price : Stop trigger price — required for STOP_LIMIT orders.

    Returns:
        dict: Validated and normalised parameters ready for the API client.

    Raises:
        ValueError: Descriptive message for the first validation failure found.
    """
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }

    ot = validated["order_type"]

    # Price is mandatory for LIMIT only
    if ot == "LIMIT":
        if price is None or str(price).strip() == "":
            raise ValueError("Price is required for LIMIT orders.")
        validated["price"] = validate_price(price, field_name="Price")

    # Stop price is mandatory for STOP_LIMIT (uses STOP_MARKET — only needs stopPrice)
    if ot == "STOP_LIMIT":
        if stop_price is None or str(stop_price).strip() == "":
            raise ValueError("Stop price is required for STOP_LIMIT orders.")
        validated["stop_price"] = validate_price(
            stop_price, field_name="Stop price"
        )
        # If limit price also provided, validate it is different from stop price
        if price is not None and str(price).strip() != "":
            validated["price"] = validate_price(price, field_name="Price")
            if validated["stop_price"] == validated["price"]:
                raise ValueError(
                    "Stop price and limit price must be different for STOP_LIMIT orders."
                )

    return validated
