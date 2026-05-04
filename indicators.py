"""Technical indicators. Pure functions, no I/O.

Inputs are pandas DataFrames with at minimum a 'Close' column.
Outputs are dicts of scalars (the latest value of each indicator) so
they're trivial to serialise and test.
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

import config as cfg


def _safe_float(x: Any) -> float | None:
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if np.isnan(f) or np.isinf(f):
        return None
    return f


def rsi(close: pd.Series, period: int = cfg.RSI_PERIOD) -> pd.Series:
    """Wilder-style RSI via EWMA."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(com=period - 1, min_periods=period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=period - 1, min_periods=period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute the full indicator panel from a price history DataFrame.

    Returns scalars for the latest bar plus a 'has_long' flag indicating
    whether SMA200 had enough data.
    """
    out: Dict[str, Any] = {
        "close": None, "sma20": None, "sma50": None, "sma200": None,
        "rsi": None, "vol20": None, "ret5": None, "ret20": None,
        "drawdown_3m": None, "trend": "unknown", "volume_trend": None,
        "has_long": False, "bars": 0,
    }
    if df is None or df.empty or "Close" not in df.columns:
        return out

    close = df["Close"].dropna()
    out["bars"] = int(len(close))
    if close.empty:
        return out

    out["close"] = _safe_float(close.iloc[-1])

    sma20 = close.rolling(cfg.SMA_SHORT).mean()
    sma50 = close.rolling(cfg.SMA_MED).mean()
    sma200 = close.rolling(cfg.SMA_LONG).mean()
    out["sma20"] = _safe_float(sma20.iloc[-1]) if len(close) >= cfg.SMA_SHORT else None
    out["sma50"] = _safe_float(sma50.iloc[-1]) if len(close) >= cfg.SMA_MED else None
    if len(close) >= cfg.SMA_LONG:
        out["sma200"] = _safe_float(sma200.iloc[-1])
        out["has_long"] = out["sma200"] is not None

    rsi_series = rsi(close)
    if not rsi_series.empty:
        out["rsi"] = _safe_float(rsi_series.iloc[-1])

    rets = close.pct_change()
    if len(rets.dropna()) >= cfg.VOL_WINDOW:
        out["vol20"] = _safe_float(rets.rolling(cfg.VOL_WINDOW).std().iloc[-1] * np.sqrt(cfg.VOL_WINDOW))
    if len(close) > 5:
        out["ret5"] = _safe_float(close.iloc[-1] / close.iloc[-6] - 1)
    if len(close) > 20:
        out["ret20"] = _safe_float(close.iloc[-1] / close.iloc[-21] - 1)

    look = min(cfg.DRAWDOWN_LOOKBACK_DAYS, len(close))
    if look > 1:
        peak = close.iloc[-look:].max()
        out["drawdown_3m"] = _safe_float(close.iloc[-1] / peak - 1)

    out["trend"] = _classify_trend(out)

    if "Volume" in df.columns:
        vol = df["Volume"].dropna()
        if len(vol) >= 40:
            recent = vol.iloc[-20:].mean()
            prior = vol.iloc[-40:-20].mean()
            if prior and prior > 0:
                out["volume_trend"] = _safe_float(recent / prior - 1)

    return out


def _classify_trend(ind: Dict[str, Any]) -> str:
    s20, s50, s200 = ind.get("sma20"), ind.get("sma50"), ind.get("sma200")
    if s20 is None or s50 is None:
        return "unknown"
    if s200 is not None:
        if s20 > s50 > s200:
            return "strong_uptrend"
        if s20 < s50 < s200:
            return "strong_downtrend"
    if s20 > s50:
        return "uptrend"
    if s20 < s50:
        return "downtrend"
    return "sideways"
