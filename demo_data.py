"""Sample-data loader for DEMO / FALLBACK modes.

Reads from sample_data/ and returns the same shapes that the live
providers return, so callers can swap modes transparently.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

import config as cfg


@lru_cache(maxsize=1)
def _watchlist() -> Dict[str, str]:
    p = cfg.SAMPLE_DATA_DIR / "watchlist.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


@lru_cache(maxsize=1)
def _fundamentals() -> Dict[str, Dict[str, Any]]:
    p = cfg.SAMPLE_DATA_DIR / "fundamentals.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


@lru_cache(maxsize=1)
def _news() -> Dict[str, List[Dict[str, Any]]]:
    p = cfg.SAMPLE_DATA_DIR / "news.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _read_prices(name: str) -> pd.DataFrame:
    p = cfg.SAMPLE_DATA_DIR / "prices" / f"{name}.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, parse_dates=["Date"])
    df = df.set_index("Date")
    return df


def has_sample_data() -> bool:
    """True iff the sample fixture set is present and non-empty."""
    return bool(_watchlist()) and (cfg.SAMPLE_DATA_DIR / "prices").exists()


def load_price_history(ticker: str) -> pd.DataFrame:
    return _read_prices(ticker)


def load_fundamentals(ticker: str) -> Dict[str, Any]:
    base = {"P/B": None, "EV/EBITDA": None, "Debt/Equity": None,
            "Current_Ratio": None, "Market_Cap": None, "Shares_Out": None}
    return {**base, **_fundamentals().get(ticker, {})}


def load_news_headlines(ticker: str) -> List[Dict[str, Any]]:
    """Return synthetic headlines in NewsAPI-ish shape (title/source/url/...)."""
    items = _news().get(ticker, [])
    out: List[Dict[str, Any]] = []
    for it in items:
        out.append({
            "title": it.get("title", ""),
            "url": it.get("url", ""),
            "source": it.get("source", "Sample"),
            "publishedAt": it.get("publishedAt", ""),
            "description": it.get("description", ""),
        })
    return out


def load_bdry_series() -> pd.Series:
    df = _read_prices("BDRY")
    if df.empty or "Close" not in df.columns:
        return pd.Series(dtype=float)
    return df["Close"]


def demo_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
