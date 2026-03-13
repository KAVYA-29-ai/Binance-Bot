"""
bot/orders.py
=============
High-level order placement using python-binance client.
Uses `rich` for beautiful terminal output.

Supported order types
---------------------
MARKET     -- executes immediately at current market price
LIMIT      -- executes at a specified price or better
STOP_LIMIT -- triggers a limit order when the stop price is hit
"""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import BinanceAPIError, BinanceClient, BinanceNetworkError
from .logging_config import setup_logger
from .validators import validate_order_inputs

logger  = setup_logger("trading_bot")
console = Console()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _format_response(response: dict) -> dict:
    """
    Extract the most useful fields from a Binance order response.

    Args:
        response: Raw JSON dict returned by BinanceClient.place_order().

    Returns:
        dict: Simplified summary with key order fields.
    """
    return {
        "orderId":     response.get("orderId"),
        "symbol":      response.get("symbol"),
        "side":        response.get("side"),
        "type":        response.get("type"),
        "origQty":     response.get("origQty"),
        "executedQty": response.get("executedQty"),
        "price":       response.get("price"),
        "avgPrice":    response.get("avgPrice"),
        "stopPrice":   response.get("stopPrice"),
        "status":      response.get("status"),
        "timeInForce": response.get("timeInForce"),
    }


def _print_request_table(params: dict) -> None:
    """Print a rich table showing the order request summary."""
    table = Table(title="📋 Order Request Summary", box=box.ROUNDED, style="cyan")
    table.add_column("Field", style="bold white", width=16)
    table.add_column("Value", style="yellow")
    for k, v in params.items():
        if v is not None:
            table.add_row(k.capitalize(), str(v))
    console.print(table)


def _print_response_table(result: dict) -> None:
    """Print a rich table showing the successful order response."""
    side_color   = "green" if result.get("side") == "BUY" else "red"
    status       = result.get("status", "")
    status_color = "green" if status == "FILLED" else "yellow"

    table = Table(title="✅ Order Response", box=box.ROUNDED, style="green")
    table.add_column("Field",       style="bold white", width=16)
    table.add_column("Value",       style="white")

    table.add_row("Order ID",     str(result.get("orderId")))
    table.add_row("Symbol",       str(result.get("symbol")))
    table.add_row("Side",         f"[{side_color}]{result.get('side')}[/{side_color}]")
    table.add_row("Type",         str(result.get("type")))
    table.add_row("Quantity",     str(result.get("origQty")))
    table.add_row("Executed Qty", str(result.get("executedQty")))
    table.add_row("Avg Price",    str(result.get("avgPrice") or "N/A"))
    table.add_row("Status",       f"[{status_color}]{status}[/{status_color}]")
    console.print(table)
    console.print(Panel("[bold green]✅ Order placed successfully![/bold green]", style="green"))


def _print_error_table(error_msg: str) -> None:
    """Print a rich error panel when an order fails."""
    console.print(Panel(
        f"[bold red]❌ Order Failed[/bold red]\n\n{error_msg}\n\n"
        "[yellow]Check logs/ folder for full details.[/yellow]",
        style="red",
        title="Error"
    ))


# ── OrderManager ──────────────────────────────────────────────────────────────


class OrderManager:
    """
    High-level interface for placing and querying futures orders.

    Example
    -------
    >>> from bot import BinanceClient, OrderManager
    >>> client = BinanceClient()
    >>> om = OrderManager(client)
    >>> result = om.place_market_order("BTCUSDT", "BUY", 0.01)
    """

    def __init__(self, client: BinanceClient) -> None:
        self.client = client
        logger.info("OrderManager initialised.")

    # ── Market Order ──────────────────────────────────────────────────────────

    def place_market_order(
        self, symbol: str, side: str, quantity: float | str
    ) -> dict:
        """
        Place a MARKET order — executes immediately at current price.

        Args:
            symbol  : Trading pair, e.g. "BTCUSDT".
            side    : "BUY" or "SELL".
            quantity: Amount of base asset to trade.

        Returns:
            dict: Simplified order response summary.

        Raises:
            ValueError         : On invalid inputs.
            BinanceAPIError    : On API rejection.
            BinanceNetworkError: On connectivity failures.
        """
        validated = validate_order_inputs(
            symbol=symbol, side=side,
            order_type="MARKET", quantity=quantity,
        )
        params = {
            "symbol":   validated["symbol"],
            "side":     validated["side"],
            "type":     "MARKET",
            "quantity": validated["quantity"],
        }
        logger.info("MARKET order | %s %s qty=%s",
                    validated["side"], validated["symbol"], validated["quantity"])
        _print_request_table(params)
        try:
            raw    = self.client.place_order(**params)
            result = _format_response(raw)
            logger.info("MARKET order success | orderId=%s", result["orderId"])
            _print_response_table(result)
            return result
        except (BinanceAPIError, BinanceNetworkError) as exc:
            logger.error("MARKET order failed: %s", exc)
            _print_error_table(str(exc))
            raise

    # ── Limit Order ───────────────────────────────────────────────────────────

    def place_limit_order(
        self, symbol: str, side: str, quantity: float | str,
        price: float | str, time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a LIMIT order — executes at the specified price or better.

        Args:
            symbol       : Trading pair.
            side         : "BUY" or "SELL".
            quantity     : Amount of base asset to trade.
            price        : Limit price.
            time_in_force: "GTC" (default), "IOC", or "FOK".

        Returns:
            dict: Simplified order response summary.

        Raises:
            ValueError         : On invalid inputs.
            BinanceAPIError    : On API rejection.
            BinanceNetworkError: On connectivity failures.
        """
        validated = validate_order_inputs(
            symbol=symbol, side=side,
            order_type="LIMIT", quantity=quantity, price=price,
        )
        params = {
            "symbol":      validated["symbol"],
            "side":        validated["side"],
            "type":        "LIMIT",
            "quantity":    validated["quantity"],
            "price":       validated["price"],
            "timeInForce": time_in_force,
        }
        logger.info("LIMIT order | %s %s qty=%s price=%s",
                    validated["side"], validated["symbol"],
                    validated["quantity"], validated["price"])
        _print_request_table(params)
        try:
            raw    = self.client.place_order(**params)
            result = _format_response(raw)
            logger.info("LIMIT order success | orderId=%s", result["orderId"])
            _print_response_table(result)
            return result
        except (BinanceAPIError, BinanceNetworkError) as exc:
            logger.error("LIMIT order failed: %s", exc)
            _print_error_table(str(exc))
            raise

    # ── Stop-Limit Order ──────────────────────────────────────────────────────

    def place_stop_limit_order(
        self, symbol: str, side: str, quantity: float | str,
        price: float | str, stop_price: float | str,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a STOP_LIMIT order — triggers a limit order at stop_price.

        A stop-limit order triggers a LIMIT order when the market reaches
        stop_price, then executes at price or better.

        Args:
            symbol       : Trading pair.
            side         : "BUY" or "SELL".
            quantity     : Amount of base asset to trade.
            price        : Limit price after trigger.
            stop_price   : Price that triggers the limit order.
            time_in_force: "GTC" (default), "IOC", or "FOK".

        Returns:
            dict: Simplified order response summary.

        Raises:
            ValueError         : On invalid inputs.
            BinanceAPIError    : On API rejection.
            BinanceNetworkError: On connectivity failures.
        """
        validated = validate_order_inputs(
            symbol=symbol, side=side, order_type="STOP_LIMIT",
            quantity=quantity, price=price, stop_price=stop_price,
        )
        params = {
            "symbol":      validated["symbol"],
            "side":        validated["side"],
            "type":        "STOP_MARKET",  # Testnet supports STOP_MARKET not STOP
            "quantity":    validated["quantity"],
            "stopPrice":   validated["stop_price"],
        }
        logger.info("STOP_LIMIT order | %s %s qty=%s stop=%s",
                    validated["side"], validated["symbol"], validated["quantity"],
                    validated["stop_price"])
        _print_request_table(params)
        try:
            raw    = self.client.place_order(**params)
            result = _format_response(raw)
            logger.info("STOP_LIMIT order success | orderId=%s", result["orderId"])
            _print_response_table(result)
            return result
        except (BinanceAPIError, BinanceNetworkError) as exc:
            logger.error("STOP_LIMIT order failed: %s", exc)
            _print_error_table(str(exc))
            raise

    # ── Utility ───────────────────────────────────────────────────────────────

    def get_current_price(self, symbol: str) -> float:
        """Return the latest market price for a symbol."""
        data = self.client.get_ticker_price(symbol)
        return float(data["price"])

    def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        """Return open orders, optionally filtered by symbol."""
        return self.client.get_open_orders(symbol)
