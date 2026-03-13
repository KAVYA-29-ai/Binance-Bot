"""
bot/enhanced_cli.py
===================
Interactive rich-powered CLI menu for the trading bot.

Launched when the user runs `python cli.py` with no arguments,
or with the --interactive / -i flag.

Menu options
------------
1. Place Market Order
2. Place Limit Order
3. Place Stop-Limit Order
4. Check Current Price
5. View Open Orders
6. Exit
"""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .validators import (
    VALID_SIDES,
    validate_order_inputs,
    validate_price,
    validate_quantity,
    validate_symbol,
)

console = Console()


# ── Banner ────────────────────────────────────────────────────────────────────


def _print_banner() -> None:
    """Print the welcome banner."""
    console.print(Panel(
        Text.assemble(
            ("⚡ Binance Futures Trading Bot\n", "bold yellow"),
            ("   USDT-M Testnet — Interactive Mode", "cyan"),
        ),
        box=box.DOUBLE,
        style="bold",
        padding=(1, 4),
    ))


# ── Input helpers (loop until valid) ─────────────────────────────────────────


def _ask_symbol() -> str:
    """Prompt for trading symbol, retry on invalid input."""
    while True:
        raw = Prompt.ask("[cyan]Symbol[/cyan] (e.g. BTCUSDT)")
        try:
            return validate_symbol(raw)
        except ValueError as exc:
            console.print(f"[bold red]❌ {exc}[/bold red]")


def _ask_side() -> str:
    """Prompt for BUY or SELL, retry on invalid input."""
    while True:
        raw = Prompt.ask(
            "[cyan]Side[/cyan]",
            choices=["BUY", "SELL", "buy", "sell"],
            show_choices=True,
        )
        return raw.upper()


def _ask_quantity() -> float:
    """Prompt for quantity, retry on invalid input."""
    while True:
        raw = Prompt.ask("[cyan]Quantity[/cyan] (e.g. 0.01)")
        try:
            return validate_quantity(raw)
        except ValueError as exc:
            console.print(f"[bold red]❌ {exc}[/bold red]")


def _ask_price(label: str = "Limit Price") -> float:
    """Prompt for a price value, retry on invalid input."""
    while True:
        raw = Prompt.ask(f"[cyan]{label}[/cyan] (USDT)")
        try:
            return validate_price(raw, field_name=label)
        except ValueError as exc:
            console.print(f"[bold red]❌ {exc}[/bold red]")


def _confirm_order(params: dict) -> bool:
    """Show an order preview table and ask for confirmation."""
    table = Table(title="📋 Order Preview", box=box.ROUNDED, style="yellow")
    table.add_column("Field", style="bold white", width=16)
    table.add_column("Value", style="yellow")
    for k, v in params.items():
        if v is not None:
            table.add_row(str(k), str(v))
    console.print(table)
    return Confirm.ask("[bold yellow]Confirm order?[/bold yellow]", default=False)


# ── Menu actions ──────────────────────────────────────────────────────────────


def _menu_market_order(om) -> None:
    """Interactively place a MARKET order."""
    console.print(Panel("[bold cyan]Place Market Order[/bold cyan]", style="cyan"))
    symbol   = _ask_symbol()
    side     = _ask_side()
    quantity = _ask_quantity()

    if _confirm_order({"Symbol": symbol, "Side": side, "Type": "MARKET", "Quantity": quantity}):
        try:
            om.place_market_order(symbol, side, quantity)
        except Exception as exc:
            console.print(f"[bold red]❌ Failed: {exc}[/bold red]")
    else:
        console.print("[yellow]⚠️  Order cancelled.[/yellow]")


def _menu_limit_order(om) -> None:
    """Interactively place a LIMIT order."""
    console.print(Panel("[bold cyan]Place Limit Order[/bold cyan]", style="cyan"))
    symbol   = _ask_symbol()
    side     = _ask_side()
    quantity = _ask_quantity()
    price    = _ask_price("Limit Price")

    if _confirm_order({"Symbol": symbol, "Side": side, "Type": "LIMIT",
                        "Quantity": quantity, "Price": price}):
        try:
            om.place_limit_order(symbol, side, quantity, price)
        except Exception as exc:
            console.print(f"[bold red]❌ Failed: {exc}[/bold red]")
    else:
        console.print("[yellow]⚠️  Order cancelled.[/yellow]")


def _menu_stop_limit_order(om) -> None:
    """Interactively place a STOP-LIMIT order."""
    console.print(Panel("[bold cyan]Place Stop-Limit Order[/bold cyan]", style="cyan"))
    symbol     = _ask_symbol()
    side       = _ask_side()
    quantity   = _ask_quantity()
    stop_price = _ask_price("Stop Trigger Price")
    price      = _ask_price("Limit Price (after trigger)")

    if _confirm_order({"Symbol": symbol, "Side": side, "Type": "STOP_LIMIT",
                        "Quantity": quantity, "Stop Price": stop_price, "Limit Price": price}):
        try:
            om.place_stop_limit_order(symbol, side, quantity, price, stop_price)
        except Exception as exc:
            console.print(f"[bold red]❌ Failed: {exc}[/bold red]")
    else:
        console.print("[yellow]⚠️  Order cancelled.[/yellow]")


def _menu_check_price(om) -> None:
    """Interactively check the current price of a symbol."""
    console.print(Panel("[bold cyan]Check Current Price[/bold cyan]", style="cyan"))
    symbol = _ask_symbol()
    try:
        price = om.get_current_price(symbol)
        console.print(Panel(
            f"[bold yellow]💰 {symbol}[/bold yellow]  →  "
            f"[bold green]{price:,.2f} USDT[/bold green]",
            style="yellow",
        ))
    except Exception as exc:
        console.print(f"[bold red]❌ Failed: {exc}[/bold red]")


def _menu_open_orders(om) -> None:
    """Interactively view open orders."""
    console.print(Panel("[bold cyan]View Open Orders[/bold cyan]", style="cyan"))
    raw = Prompt.ask("[cyan]Symbol[/cyan] (leave blank for ALL)", default="")
    symbol = raw.strip().upper() or None
    try:
        orders = om.get_open_orders(symbol)
        if not orders:
            console.print("[yellow]📭 No open orders found.[/yellow]")
            return
        table = Table(
            title=f"Open Orders — {symbol or 'ALL'}",
            box=box.ROUNDED, style="cyan"
        )
        table.add_column("Order ID",  style="white")
        table.add_column("Symbol",    style="yellow")
        table.add_column("Side",      style="bold")
        table.add_column("Type",      style="white")
        table.add_column("Qty",       style="white")
        table.add_column("Price",     style="green")
        table.add_column("Status",    style="cyan")
        for o in orders:
            side_color = "green" if o.get("side") == "BUY" else "red"
            table.add_row(
                str(o.get("orderId")),
                str(o.get("symbol")),
                f"[{side_color}]{o.get('side')}[/{side_color}]",
                str(o.get("type")),
                str(o.get("origQty")),
                str(o.get("price")),
                str(o.get("status")),
            )
        console.print(table)
    except Exception as exc:
        console.print(f"[bold red]❌ Failed: {exc}[/bold red]")


# ── Main menu loop ────────────────────────────────────────────────────────────


def run_interactive_menu(om) -> None:
    """
    Launch the full interactive CLI menu.

    Args:
        om: OrderManager instance (already initialised with a BinanceClient).
    """
    _print_banner()

    menu_items = {
        "1": ("Place Market Order",     _menu_market_order),
        "2": ("Place Limit Order",      _menu_limit_order),
        "3": ("Place Stop-Limit Order", _menu_stop_limit_order),
        "4": ("Check Current Price",    _menu_check_price),
        "5": ("View Open Orders",       _menu_open_orders),
        "6": ("Exit",                   None),
    }

    while True:
        # ── Draw menu ──────────────────────────────────────────────────────
        table = Table(box=box.SIMPLE, show_header=False, style="cyan", padding=(0, 2))
        table.add_column("Key",   style="bold yellow", width=4)
        table.add_column("Action", style="white")
        for key, (label, _) in menu_items.items():
            icon = "🚪" if key == "6" else "▶"
            table.add_row(f"[{key}]", f"{icon}  {label}")
        console.print(table)

        choice = Prompt.ask(
            "\n[bold yellow]Select option[/bold yellow]",
            choices=list(menu_items.keys()),
            show_choices=False,
        )

        if choice == "6":
            console.print(Panel(
                "[bold yellow]👋 Goodbye! Stay sharp.[/bold yellow]",
                style="yellow"
            ))
            break

        _, action_fn = menu_items[choice]
        console.rule()
        try:
            action_fn(om)
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Interrupted. Returning to menu...[/yellow]")
        console.rule()
