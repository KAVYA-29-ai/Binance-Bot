"""
app.py
======
Lightweight Flask web UI for the Binance Futures Trading Bot.

Provides a browser-based interface to place orders without using the CLI.
Runs on http://localhost:5000 by default.

Routes
------
GET  /              – Main trading dashboard
POST /place_order   – Place an order (returns JSON)
GET  /price/<sym>   – Get current price for a symbol (JSON)
GET  /open_orders   – Get open orders (JSON)
GET  /health        – Health check endpoint
"""

from __future__ import annotations

import os
import sys

from flask import Flask, jsonify, render_template, request

from bot.client import BinanceAPIError, BinanceAuthError, BinanceNetworkError
from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.orders import OrderManager
from bot.validators import validate_order_inputs

logger = setup_logger("trading_bot")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret-change-in-prod")

# ── Initialise Binance client (app-wide singleton) ────────────────────────────

try:
    _client = BinanceClient()
    _order_manager = OrderManager(_client)
    logger.info("Flask app: BinanceClient initialised successfully.")
except BinanceAuthError as exc:
    logger.critical("Flask app: Auth error — %s", exc)
    _client = None
    _order_manager = None


# ── Routes ────────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    """Render the main trading dashboard."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check — returns bot and API status."""
    return jsonify(
        {
            "status": "ok",
            "api_connected": _client is not None,
            "testnet_url": "https://testnet.binancefuture.com",
        }
    )


@app.route("/price/<symbol>")
def get_price(symbol: str):
    """
    Return the current market price for a symbol.

    Args:
        symbol: Trading pair in the URL path, e.g. /price/BTCUSDT

    Returns:
        JSON: {"symbol": "BTCUSDT", "price": 43210.5}
    """
    if _order_manager is None:
        return jsonify({"error": "Bot not initialised — check API keys."}), 503

    try:
        symbol = symbol.strip().upper()
        price = _order_manager.get_current_price(symbol)
        return jsonify({"symbol": symbol, "price": price})
    except BinanceAPIError as exc:
        logger.error("Price fetch error: %s", exc)
        return jsonify({"error": exc.message}), 400
    except BinanceNetworkError as exc:
        logger.error("Network error (price): %s", exc)
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.exception("Unexpected error (price): %s", exc)
        return jsonify({"error": "Unexpected server error."}), 500


@app.route("/open_orders")
def open_orders():
    """
    Return open orders, optionally filtered by symbol.

    Query params:
        symbol (optional): e.g. /open_orders?symbol=BTCUSDT

    Returns:
        JSON: list of open order objects
    """
    if _order_manager is None:
        return jsonify({"error": "Bot not initialised — check API keys."}), 503

    symbol = request.args.get("symbol", "").strip().upper() or None
    try:
        orders = _order_manager.get_open_orders(symbol)
        return jsonify({"orders": orders, "count": len(orders)})
    except BinanceAPIError as exc:
        return jsonify({"error": exc.message}), 400
    except BinanceNetworkError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.exception("Unexpected error (open_orders): %s", exc)
        return jsonify({"error": "Unexpected server error."}), 500


@app.route("/place_order", methods=["POST"])
def place_order():
    """
    Place an order from the web UI form.

    Expected JSON body:
        {
            "symbol"    : "BTCUSDT",
            "side"      : "BUY",
            "order_type": "MARKET",
            "quantity"  : "0.01",
            "price"     : "",         // required for LIMIT / STOP_LIMIT
            "stop_price": ""          // required for STOP_LIMIT
        }

    Returns:
        JSON: order result or error message
    """
    if _order_manager is None:
        return (
            jsonify({"success": False, "error": "Bot not initialised — check API keys."}),
            503,
        )

    data = request.get_json(silent=True) or request.form.to_dict()
    logger.info("Web UI order request: %s", data)

    # ── Extract fields ────────────────────────────────────────────────────────
    symbol = data.get("symbol", "").strip()
    side = data.get("side", "").strip()
    order_type = data.get("order_type", "").strip()
    quantity = data.get("quantity", "").strip()
    price = data.get("price", "").strip() or None
    stop_price = data.get("stop_price", "").strip() or None

    # ── Validate ──────────────────────────────────────────────────────────────
    try:
        validate_order_inputs(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValueError as exc:
        logger.warning("Validation error (web): %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 400

    # ── Place order ───────────────────────────────────────────────────────────
    try:
        if order_type == "MARKET":
            result = _order_manager.place_market_order(symbol, side, quantity)

        elif order_type == "LIMIT":
            result = _order_manager.place_limit_order(symbol, side, quantity, price)

        elif order_type == "STOP_LIMIT":
            result = _order_manager.place_stop_limit_order(
                symbol, side, quantity, price or None, stop_price
            )
        else:
            return jsonify({"success": False, "error": f"Unknown order type: {order_type}"}), 400

        return jsonify({"success": True, "order": result})

    except BinanceAPIError as exc:
        logger.error("API error (web): %s", exc)
        return jsonify({"success": False, "error": f"[{exc.code}] {exc.message}"}), 400

    except BinanceNetworkError as exc:
        logger.error("Network error (web): %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 503

    except Exception as exc:
        logger.exception("Unexpected error (web): %s", exc)
        return jsonify({"success": False, "error": "Unexpected server error."}), 500


# ── Main ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting Flask web UI on http://localhost:%d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)
