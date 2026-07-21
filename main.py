"""
Factor calculations. Pure functions operating on price / fundamentals
DataFrames - no data-fetching here, so this module is easy to unit test.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def compute_momentum(prices: pd.DataFrame, window: int) -> pd.Series:
    """Trailing total return over `window` trading days, as of the last date."""
    if len(prices) <= window:
        raise ValueError(f"Need more than {window} rows of price history for momentum.")
    return prices.iloc[-1] / prices.iloc[-window] - 1.0


def compute_annualised_volatility(prices: pd.DataFrame, window: int) -> pd.Series:
    """Annualised volatility of daily returns over the trailing `window` days."""
    returns = prices.pct_change().dropna(how="all")
    trailing = returns.tail(window)
    return trailing.std() * np.sqrt(252)


def zscore(series: pd.Series) -> pd.Series:
    """Standard z-score, NaN-safe. Returns 0 for a degenerate (zero-variance) series."""
    s = series.astype(float)
    std = s.std()
    if std == 0 or np.isnan(std):
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / std


def equity_composite_score(
    momentum: pd.Series,
    fundamentals: pd.DataFrame,
    weights: dict[str, float],
) -> pd.DataFrame:
    """
    Combine value (inverse P/E), quality (ROE) and momentum into a single
    composite z-score per equity. Missing fundamentals are treated as
    factor-neutral (z-score 0) rather than excluding the stock, since
    small/limited datasets often have gaps.
    """
    df = pd.DataFrame(index=momentum.index)
    df["momentum"] = momentum

    fundamentals = fundamentals.reindex(df.index)
    # Value: lower P/E is better -> invert sign before z-scoring
    pe = fundamentals["trailing_pe"].astype(float)
    pe = pe.where(pe > 0)  # negative/zero P/E is not meaningful here
    df["value_raw"] = -pe
    df["quality_raw"] = fundamentals["return_on_equity"].astype(float)

    df["value_z"] = zscore(df["value_raw"].fillna(df["value_raw"].mean()))
    df["quality_z"] = zscore(df["quality_raw"].fillna(df["quality_raw"].mean()))
    df["momentum_z"] = zscore(df["momentum"])

    df["composite_score"] = (
        weights["value"] * df["value_z"]
        + weights["quality"] * df["quality_z"]
        + weights["momentum"] * df["momentum_z"]
    )
    return df.sort_values("composite_score", ascending=False)
