"""
Data access layer. Wraps yfinance so the rest of the codebase never
imports yfinance directly - this also makes it easy to swap in a
different data provider later, or to substitute synthetic data for
testing (see test_synthetic.py).
"""
from __future__ import annotations
import pandas as pd


def fetch_price_history(tickers: list[str], years: int) -> pd.DataFrame:
    """
    Fetch daily adjusted close prices for a list of tickers.

    Returns a DataFrame indexed by date, one column per ticker.
    Tickers that fail to download are dropped with a warning rather
    than crashing the whole run.
    """
    import yfinance as yf

    period = f"{years}y"
    raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)

    if raw.empty:
        raise RuntimeError("No price data returned - check tickers / internet connection.")

    # yfinance returns a MultiIndex column DataFrame when given multiple tickers
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        # single ticker case
        prices = raw[["Close"]]
        prices.columns = tickers

    missing = [t for t in tickers if t not in prices.columns or prices[t].isna().all()]
    if missing:
        print(f"[data] Warning: dropping tickers with no data: {missing}")
        prices = prices.drop(columns=[c for c in missing if c in prices.columns])

    return prices.dropna(how="all")


def fetch_fundamentals(tickers: list[str]) -> pd.DataFrame:
    """
    Fetch a small set of fundamental metrics used for the value/quality
    factors. Equities only - crypto has no P/E or ROE.

    Returns a DataFrame indexed by ticker with columns:
    trailing_pe, return_on_equity
    """
    import yfinance as yf

    rows = []
    for t in tickers:
        try:
            info = yf.Ticker(t).info
            rows.append({
                "ticker": t,
                "trailing_pe": info.get("trailingPE"),
                "return_on_equity": info.get("returnOnEquity"),
            })
        except Exception as e:
            print(f"[data] Warning: could not fetch fundamentals for {t}: {e}")
            rows.append({"ticker": t, "trailing_pe": None, "return_on_equity": None})

    return pd.DataFrame(rows).set_index("ticker")
