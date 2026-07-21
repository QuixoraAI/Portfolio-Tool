"""
Configuration for the quantitative portfolio construction & backtesting tool.

Edit EQUITY_UNIVERSE / CRYPTO_UNIVERSE to change what the tool considers.
Edit the parameters below to change strategy behaviour.
"""

# --- Investable universe -----------------------------------------------
# Kept to liquid, well-known names so the tool is fast and fundamentals
# data is reliably available. Expand this list as you like.
EQUITY_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "JPM", "V", "JNJ",
    "PG", "KO", "XOM", "CVX", "HD", "DIS", "NFLX", "PFE", "UNH", "MA",
    "WMT", "BAC", "T", "VZ", "INTC", "CSCO", "ADBE", "CRM", "ORCL",
    "IBM", "MCD",
]

CRYPTO_UNIVERSE = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD",
]

BENCHMARKS = {
    "SPY": "S&P 500 ETF",
    "BTC-USD": "Bitcoin",
}

# --- Strategy parameters -------------------------------------------------
LOOKBACK_YEARS = 3           # how much price history to pull / backtest over
MOMENTUM_WINDOW_DAYS = 126   # ~6 months trading days, for momentum factor
VOL_WINDOW_DAYS = 60         # trailing window for volatility / risk weighting
REBALANCE_FREQ = "ME"        # 'ME' = month-end (pandas >= 2.2 alias; use 'M' on pandas < 2.2)

TOP_N_EQUITIES = 10          # how many equities the factor model selects
TOP_N_CRYPTO = 4             # how many cryptoassets the momentum model selects

EQUITY_SLEEVE_WEIGHT = 0.80  # policy split between sleeves (risk-managed default)
CRYPTO_SLEEVE_WEIGHT = 0.20  # crypto is far more volatile -> capped allocation

RISK_FREE_RATE = 0.043       # annualised, for Sharpe ratio calc (matches gilt/UST ~2026)

# Factor weights for the equity composite score (must sum to 1.0)
FACTOR_WEIGHTS = {
    "value": 1 / 3,
    "quality": 1 / 3,
    "momentum": 1 / 3,
}
