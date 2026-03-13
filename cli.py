"""
cli.py
======
Entry point for the Binance Futures Trading Bot.

Two modes
---------
1. Interactive mode (default — no arguments):
       python cli.py
       python cli.py --interactive

2. Direct mode (all arguments provided):
       python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
       python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 50000
       python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT \
                     --quantity 0.01 --price 31000 --stop-price 30500
       python cli.py --symbol BTCUSDT --price-only
       python cli.py --symbol BTCUSDT --open-orders
"""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from bot.client import BinanceAPIError, BinanceAuthError, BinanceNetworkError, BinanceClient
from bot.enhanced_cli import run_interactive_menu
from bot.logging_config import setup_logger
from bot.orders import OrderManager
from bot.validators import VALID_ORDER_TYPES, VALID_SIDES

logger  = setup_logger("trading_bot")
console = Console()


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description=(
            "Binance Futures Testnet — Trading Bot\n"
            "Run with no arguments to launch the interactive menu."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Interactive  : python cli.py\n"
            "  Market BUY   : python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01\n"
            "  Limit SELL   : python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 50000\n"
            "  Stop-Limit   : python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT "
            "--quantity 0.01 --price 31000 --stop-price 30500\n"
            "  Price check  : python cli.py --symbol BTCUSDT --price-only\n"
            "  Open orders  : python cli.py --symbol BTCUSDT --open-orders\n"
        ),
    )

    # ── Flags ──────────────────────────────────────────────────────────────
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Launch the interactive menu (default when no args given).",
    )

    # ── Order params ───────────────────────────────────────────────────────
    og = parser.add_argument_group("Order Parameters")
    og.add_argument("--symbol",   "-s", type=str,         metavar="SYMBOL",
                    help="Trading pair, e.g. BTCUSDT.")
    og.add_argument("--side",           type=str.upper,   choices=list(VALID_SIDES),
                    metavar="SIDE",     help="BUY or SELL.")
    og.add_argument("--type",    "-t",  dest="order_type", type=str.upper,
                    choices=list(VALID_ORDER_TYPES), metavar="TYPE",
                    help="MARKET | LIMIT | STOP_LIMIT.")
    og.add_argument("--quantity", "-q", type=float,       metavar="QTY",
                    help="Amount of base asset, e.g. 0.01.")
    og.add_argument("--price",    "-p", type=float,       metavar="PRICE",
                    help="Limit price (required for LIMIT / STOP_LIMIT).")
    og.add_argument("--stop-price",     type=float,       metavar="STOP_PRICE",
                    dest="stop_price",
                    help="Stop trigger price (required for STOP_LIMIT).")
    og.add_argument("--time-in-force",  type=str.upper,   default="GTC",
                    choices=["GTC", "IOC", "FOK"],        metavar="TIF",
                    help="Time-in-force for LIMIT orders. Default: GTC.")

    # ── Utility flags ──────────────────────────────────────────────────────
    ug = parser.add_argument_group("Utility")
    ug.add_argument("--price-only",  action="store_true",
                    help="Print current market price for --symbol and exit.")
    ug.add_argument("--open-orders", action="store_true",
                    help="List open orders for --symbol and exit.")

    return parser


# ── Direct-mode handlers ──────────────────────────────────────────────────────


def handle_price_check(om: OrderManager, symbol: str) -> None:
    price = om.get_current_price(symbol)
    console.print(f"\n  [bold yellow]💰 {symbol}[/bold yellow]: "
                  f"[bold green]{price:,.2f} USDT[/bold green]\n")
    logger.info("Price check — %s = %s", symbol, price)


def handle_open_orders(om: OrderManager, symbol: str) -> None:
    orders = om.get_open_orders(symbol)
    if not orders:
        console.print(f"\n[yellow]📭 No open orders for {symbol}.[/yellow]\n")
    else:
        from rich.table import Table
        from rich import box
        table = Table(title=f"Open Orders — {symbol}", box=box.ROUNDED, style="cyan")
        table.add_column("Order ID"); table.add_column("Side")
        table.add_column("Type");     table.add_column("Qty")
        table.add_column("Price");    table.add_column("Status")
        for o in orders:
            sc = "green" if o.get("side") == "BUY" else "red"
            table.add_row(
                str(o.get("orderId")),
                f"[{sc}]{o.get('side')}[/{sc}]",
                str(o.get("type")), str(o.get("origQty")),
                str(o.get("price")), str(o.get("status")),
            )
        console.print(table)
    logger.info("Open orders — %s: %d found", symbol, len(orders))


def handle_direct_order(om: OrderManager, args: argparse.Namespace) -> None:
    """Route to the correct order function based on parsed args."""
    missing = [f for f, v in [("--side", args.side),
                               ("--type", args.order_type),
                               ("--quantity", args.quantity)] if not v]
    if missing:
        console.print(f"\n[bold red]❌ Missing required arguments: {', '.join(missing)}[/bold red]")
        console.print("[yellow]Run [bold]python cli.py --help[/bold] for usage.[/yellow]\n")
        sys.exit(1)

    if args.order_type == "MARKET":
        om.place_market_order(args.symbol, args.side, args.quantity)

    elif args.order_type == "LIMIT":
        if not args.price:
            console.print("\n[bold red]❌ --price is required for LIMIT orders.[/bold red]\n")
            sys.exit(1)
        om.place_limit_order(args.symbol, args.side, args.quantity,
                             args.price, args.time_in_force)

    elif args.order_type == "STOP_LIMIT":
        if not args.price or not args.stop_price:
            console.print("\n[bold red]❌ Both --price and --stop-price are required "
                          "for STOP_LIMIT orders.[/bold red]\n")
            sys.exit(1)
        om.place_stop_limit_order(args.symbol, args.side, args.quantity,
                                  args.price, args.stop_price, args.time_in_force)


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    # No args at all → interactive mode
    no_order_args = not any([args.symbol, args.side, args.order_type,
                              args.quantity, args.price_only, args.open_orders])
    if args.interactive or no_order_args:
        try:
            client = BinanceClient()
            om     = OrderManager(client)
        except BinanceAuthError as exc:
            console.print(f"\n[bold red]🔑 Auth error: {exc}[/bold red]\n")
            sys.exit(1)
        run_interactive_menu(om)
        return

    # Direct mode — symbol is required for everything below
    if not args.symbol:
        console.print("\n[bold red]❌ --symbol is required.[/bold red]\n")
        parser.print_help()
        sys.exit(1)

    logger.info("CLI direct mode — args: %s", vars(args))

    try:
        client = BinanceClient()
        om     = OrderManager(client)
    except BinanceAuthError as exc:
        console.print(f"\n[bold red]🔑 Auth error: {exc}[/bold red]\n")
        logger.critical("Auth error: %s", exc)
        sys.exit(1)

    try:
        if args.price_only:
            handle_price_check(om, args.symbol)
        elif args.open_orders:
            handle_open_orders(om, args.symbol)
        else:
            handle_direct_order(om, args)

    except ValueError as exc:
        console.print(f"\n[bold red]❌ Validation error: {exc}[/bold red]\n")
        logger.error("Validation error: %s", exc)
        sys.exit(1)
    except BinanceAPIError as exc:
        console.print(f"\n[bold red]❌ API error [{exc.code}]: {exc.message}[/bold red]\n")
        logger.error("API error: %s", exc)
        sys.exit(1)
    except BinanceNetworkError as exc:
        console.print(f"\n[bold red]🌐 Network error: {exc}[/bold red]\n")
        logger.error("Network error: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  Aborted.[/yellow]\n")
        sys.exit(0)
    except Exception as exc:
        console.print(f"\n[bold red]⚠️  Unexpected error: {exc}[/bold red]\n")
        logger.exception("Unexpected error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
