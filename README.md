# ⚡ Binance Futures Trading Bot (Testnet)

![CI](https://github.com/KAVYA-29-ai/binance-bot/actions/workflows/ci.yml/badge.svg)

A clean, production-structured Python trading bot for the **Binance USDT-M Futures Testnet**.
Supports **Market**, **Limit**, and **Stop-Limit** orders via a **CLI**, **Interactive Menu**, and **Web UI**.

---

## ✨ Features

| Feature | Details |
|---|---|
| Order Types | MARKET, LIMIT, STOP_LIMIT |
| Sides | BUY, SELL |
| Interfaces | Interactive CLI menu + Direct CLI args + Web UI (Flask) |
| Logging | Structured file + console logging |
| Error Handling | Input validation, API errors, network failures |
| Tests | pytest unit tests with mocked API |
| CI | GitHub Actions — runs on every push to main |

---

## 📁 Project Structure

```
trading_bot/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI pipeline
├── bot/
│   ├── __init__.py
│   ├── client.py                # Binance REST API client
│   ├── orders.py                # Order placement logic
│   ├── validators.py            # Input validation
│   ├── enhanced_cli.py          # Rich interactive menu
│   └── logging_config.py       # Structured logging setup
├── tests/
│   ├── test_validators.py       # Validator unit tests
│   └── test_orders.py          # Order logic unit tests
├── templates/
│   └── index.html               # Web UI dashboard
├── static/
│   └── style.css                # Dark theme styling
├── logs/                        # Auto-created log files
├── cli.py                       # CLI entry point
├── app.py                       # Flask web UI server
├── .env.example                 # API key template
├── requirements.txt
└── README.md
```

---

## 🚀 Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/trading-bot.git
cd trading-bot
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get Binance Testnet API keys
1. Go to https://testnet.binancefuture.com
2. Sign up / log in
3. Go to **API Management** → **Generate API Key**
4. Copy your **API Key** and **Secret Key**

### 5. Configure `.env`
```bash
cp .env.example .env
```
Open `.env` and fill in:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_key_here
```

---

## 💻 CLI Usage

### Interactive Mode (recommended)
```bash
python cli.py
```
Launches a rich interactive menu:
```
┌─────────────────────────────────────┐
│  [1]  ▶  Place Market Order         │
│  [2]  ▶  Place Limit Order          │
│  [3]  ▶  Place Stop-Limit Order     │
│  [4]  ▶  Check Current Price        │
│  [5]  ▶  View Open Orders           │
│  [6]  🚪 Exit                       │
└─────────────────────────────────────┘
```

### Direct Mode (one-liner commands)

**Market Order:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

**Limit Order:**
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 50000
```

**Stop-Limit Order:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT \
  --quantity 0.01 --price 31000 --stop-price 30500
```

**Check Price:**
```bash
python cli.py --symbol BTCUSDT --price-only
```

**Open Orders:**
```bash
python cli.py --symbol BTCUSDT --open-orders
```

---

## 🌐 Web UI

```bash
python app.py
```
Open: **http://localhost:5000**

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_validators.py::TestValidateSymbol::test_valid_uppercase        PASSED
tests/test_validators.py::TestValidateSide::test_buy_uppercase            PASSED
tests/test_orders.py::TestPlaceMarketOrder::test_success_returns_order_id PASSED
...
26 passed in 0.45s
```

---

## ⚙️ CI / GitHub Actions

Every push to `main` automatically:
1. Installs all dependencies
2. Syntax-checks all Python files
3. Runs the full pytest suite

**Badge status:**
- 🟢 Green = all tests passing, code is clean
- 🔴 Red = something broke — check the Actions tab on GitHub

To enable the badge, replace `YOUR_USERNAME` in the badge URL at the top of this README.

---

## 📋 Log Files

Log files are auto-created in `logs/` as `trading_bot_YYYYMMDD.log`.

Sample entries:
```
2024-01-15 10:23:01 | INFO     | trading_bot | MARKET order | BUY BTCUSDT qty=0.01
2024-01-15 10:23:02 | INFO     | trading_bot | Order placed successfully — orderId: 3279182736
2024-01-15 10:23:02 | INFO     | trading_bot | MARKET order success | orderId=3279182736
```

---

## ❌ Error Handling

| Error | How it's handled |
|---|---|
| Missing API keys | `BinanceAuthError` — shown at startup |
| Invalid symbol/qty | `ValueError` — shown before API call |
| API rejection | `BinanceAPIError` — shows code + message |
| Network failure | `BinanceNetworkError` — 3 auto-retries |
| Unexpected errors | Full traceback logged to file |

---

## 📌 Assumptions

- Testnet only — no real funds used
- USDT-M Futures (linear, settled in USDT)
- `STOP_LIMIT` maps to Binance Futures type `"STOP"` with both `price` and `stopPrice`
- Default time-in-force: **GTC** (Good Till Cancelled)

---

## 🛠 Tech Stack

- **Python 3.x** — core language
- **python-binance** — Binance API client
- **python-dotenv** — environment variable loading
- **Flask** — web UI server
- **rich** — terminal UI (tables, colors, prompts)
- **pytest + pytest-mock** — unit testing

---

## 📬 Submission

Built for the **Python Developer (Trading Bot)** internship task.

Submitted by: `kavya`
GitHub: `KAVYA-29-ai`
