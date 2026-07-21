"""
Portfolio construction: turns factor scores into an actual set of
target weights, using inverse-volatility (risk-based) weighting within
each sleeve, and a fixed policy split between the equity and crypto
sleeves (see config.EQUITY_SLEEVE_WEIGHT / CRYPTO_SLEEVE_WEIGHT).
"""
from __future__ import annotations
import pandas as pd
from factors import compute_annualised_volatility


def inverse_vol_weights(vol: pd.Series) -> pd.Series:
    """Weight assets inversely proportional to their volatility (risk parity-lite)."""
    inv = 1.0 / vol.replace(0, pd.NA)
    inv = inv.dropna()
    return inv / inv.sum()


def build_target_portfolio(
    equity_prices: pd.DataFrame,
    crypto_prices: pd.DataFrame,
    equity_scores: pd.DataFrame,
    top_n_equities: int,
    top_n_crypto: int,
    vol_window: int,
    equity_sleeve_weight: float,
    crypto_sleeve_weight: float,
) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: ticker, sleeve, weight
    (weights sum to 1.0 across the whole portfolio).
    """
    # --- Equity sleeve: top-N by composite factor score, inverse-vol weighted
    selected_equities = equity_scores.head(top_n_equities).index.tolist()
    equity_vol = compute_annualised_volatility(equity_prices[selected_equities], vol_window)
    equity_weights = inverse_vol_weights(equity_vol) * equity_sleeve_weight

    # --- Crypto sleeve: top-N by momentum, inverse-vol weighted
    from factors import compute_momentum
    crypto_momentum = compute_momentum(crypto_prices, 126).sort_values(ascending=False)
    selected_crypto = crypto_momentum.head(top_n_crypto).index.tolist()
    crypto_vol = compute_annualised_volatility(crypto_prices[selected_crypto], vol_window)
    crypto_weights = inverse_vol_weights(crypto_vol) * crypto_sleeve_weight

    rows = []
    for ticker, w in equity_weights.items():
        rows.append({"ticker": ticker, "sleeve": "Equity", "weight": w})
    for ticker, w in crypto_weights.items():
        rows.append({"ticker": ticker, "sleeve": "Crypto", "weight": w})

    out = pd.DataFrame(rows).sort_values(["sleeve", "weight"], ascending=[True, False])
    out = out.reset_index(drop=True)
    return out
