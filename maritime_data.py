"""Aggregation layer used by the Streamlit dashboard.

Wires together: providers (data) + indicators + signals.
Builds normalised watchlist rows so the dashboard never crashes on
missing columns. Each provider call's status is collected for the
Data Health panel.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import config as cfg
from indicators import compute_indicators
from providers import (
    COUNTER,
    NewsResult,
    ProviderStatus,
    fetch_bdi_proxy,
    fetch_fundamentals,
    fetch_news,
    fetch_price_history,
    paid_provider_status,
)
from signals import generate_signal


# Re-exports for backwards compatibility with the original CLI script
NEWSAPI_KEY = cfg.NEWSAPI_KEY
shipping_companies = cfg.DEFAULT_WATCHLIST


# ---------------------------------------------------------------------------
# Watchlist row schema — every key is always present
# ---------------------------------------------------------------------------
ROW_SCHEMA: Dict[str, Any] = {
    "Company": "", "Ticker": "", "Price": None, "% Change": None,
    "RSI": None, "SMA20>SMA50": None, "Trend": "unknown",
    "5d Return": None, "20d Return": None, "20d Vol": None, "3m Drawdown": None,
    "P/B": None, "EV/EBITDA": None, "Debt/Equity": None, "Current Ratio": None,
    "News Score": 0.0, "Geo Alert": False, "Relevant News": 0,
    "Action": "N/A", "Rationale": "", "Confidence": "low",
    "Signal Score": 0.0, "Tech Score": 0.0, "Fund Score": 0.0, "Risk Score": 0.0,
    "Risk Warnings": "", "Data Warnings": "",
    "_headlines": [], "_news_source": "none", "_provider_errors": [],
}


def _empty_row(company: str, ticker: str) -> Dict[str, Any]:
    row = dict(ROW_SCHEMA)
    row["Company"], row["Ticker"] = company, ticker
    return row


def build_watchlist_row(
    company: str,
    ticker: str,
    *,
    news_hours: int = cfg.DEFAULT_NEWS_HOURS,
) -> Tuple[Dict[str, Any], List[ProviderStatus]]:
    statuses: List[ProviderStatus] = []
    row = _empty_row(company, ticker)

    df, st_price = fetch_price_history(ticker)
    statuses.append(st_price)
    if not st_price.ok or df.empty:
        row["Action"] = "ERROR"
        row["Rationale"] = f"Price fetch failed ({st_price.error or 'unknown'})"
        row["_provider_errors"] = [st_price.error] if st_price.error else []
        return row, statuses

    ind = compute_indicators(df)

    funds, st_fund = fetch_fundamentals(ticker)
    statuses.append(st_fund)

    news_res, st_news = fetch_news(company, ticker, hours=news_hours)
    statuses.append(st_news)

    sig = generate_signal(
        ind=ind,
        funds=funds,
        news={
            "avg_sentiment": news_res.avg_sentiment,
            "geo_alert": news_res.geo_alert,
            "relevant_count": news_res.relevant_count,
        },
    )

    # % change vs prior close (using last 2 closes)
    pct_change = None
    closes = df["Close"].dropna()
    if len(closes) >= 2 and closes.iloc[-2]:
        pct_change = float((closes.iloc[-1] / closes.iloc[-2] - 1) * 100)

    row.update({
        "Price": ind.get("close"),
        "% Change": pct_change,
        "RSI": ind.get("rsi"),
        "SMA20>SMA50": (ind.get("sma20") is not None and ind.get("sma50") is not None
                       and ind["sma20"] > ind["sma50"]),
        "Trend": ind.get("trend"),
        "5d Return": ind.get("ret5"),
        "20d Return": ind.get("ret20"),
        "20d Vol": ind.get("vol20"),
        "3m Drawdown": ind.get("drawdown_3m"),
        "P/B": funds.get("P/B"),
        "EV/EBITDA": funds.get("EV/EBITDA"),
        "Debt/Equity": funds.get("Debt/Equity"),
        "Current Ratio": funds.get("Current_Ratio"),
        "News Score": sig.news_score,
        "Geo Alert": sig.geo_risk,
        "Relevant News": news_res.relevant_count,
        "Action": sig.label,
        "Rationale": sig.rationale,
        "Confidence": sig.confidence,
        "Signal Score": sig.signal_score,
        "Tech Score": sig.technical_score,
        "Fund Score": sig.fundamental_score,
        "Risk Score": sig.risk_score,
        "Risk Warnings": "; ".join(sig.risk_warnings),
        "Data Warnings": "; ".join(sig.data_warnings),
        "_headlines": news_res.headlines,
        "_news_source": news_res.source,
        "_provider_errors": [s.error for s in statuses if s.error],
    })
    return row, statuses


def build_watchlist(news_hours: int = cfg.DEFAULT_NEWS_HOURS,
                    *, watchlist: Dict[str, str] | None = None,
                    progress_cb=None,
                    ) -> Dict[str, Any]:
    """Run every ticker, returning rows + aggregated provider statuses."""
    COUNTER.reset()
    wl = watchlist or cfg.DEFAULT_WATCHLIST
    rows: List[Dict[str, Any]] = []
    failures: List[str] = []
    all_statuses: List[ProviderStatus] = []

    for i, (name, ticker) in enumerate(wl.items()):
        try:
            row, statuses = build_watchlist_row(name, ticker, news_hours=news_hours)
            rows.append(row)
            all_statuses.extend(statuses)
            if row["Action"] == "ERROR":
                failures.append(ticker)
        except Exception as exc:  # noqa: BLE001
            row = _empty_row(name, ticker)
            row["Action"] = "ERROR"
            row["Rationale"] = f"{type(exc).__name__}: {exc}"
            rows.append(row)
            failures.append(ticker)
        if progress_cb:
            try:
                progress_cb((i + 1) / len(wl), ticker)
            except Exception:  # noqa: BLE001
                pass

    bdi, st_bdi = fetch_bdi_proxy()
    all_statuses.append(st_bdi)

    mode = cfg.resolve_mode()
    fallback_count = sum(
        1 for s in all_statuses
        if s.error and "sample fallback" in s.error
    )
    effective_mode = mode
    if mode == "live" and fallback_count > 0:
        effective_mode = "fallback"

    return {
        "rows": rows,
        "failures": failures,
        "statuses": all_statuses,
        "bdi": bdi,
        "calls": COUNTER.snapshot(),
        "paid_providers": paid_provider_status(),
        "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "newsapi_key_present": bool(cfg.NEWSAPI_KEY),
        "app_mode": cfg.APP_MODE,
        "effective_mode": effective_mode,  # demo | live | fallback
        "fallback_count": fallback_count,
    }


# ---------------------------------------------------------------------------
# Backwards-compatible helpers for the legacy CLI script
# ---------------------------------------------------------------------------
def get_news_for_ticker(ticker: str, company_name: str, hours: int = cfg.DEFAULT_NEWS_HOURS) -> Dict[str, Any]:
    res, _ = fetch_news(company_name, ticker, hours=hours)
    return {
        "avg_sentiment": res.avg_sentiment,
        "geo_alert": res.geo_alert,
        "headlines": res.headlines,
        "source": res.source,
    }


def get_bdi_proxy() -> Dict[str, Any] | None:
    res, _ = fetch_bdi_proxy()
    if not res:
        return None
    return {
        "last": res.last,
        "pct_5d": res.pct_5d or 0.0,
        "pct_20d": res.pct_20d or 0.0,
        "series": res.series,
        "trend": res.trend,
    }
