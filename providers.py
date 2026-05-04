"""Data provider layer.

Each provider call returns a `ProviderStatus` alongside its payload so
the dashboard can render a Data Health panel without guessing.

Failures are sanitised — exception types are surfaced, full tracebacks
and any header/secret material are not.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
import requests
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import config as cfg
import demo_data


_analyzer = SentimentIntensityAnalyzer()


# ---------------------------------------------------------------------------
# Status object
# ---------------------------------------------------------------------------
@dataclass
class ProviderStatus:
    provider: str
    ok: bool
    records: int = 0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


def _sanitise_error(exc: BaseException) -> str:
    """Strip anything that could leak secrets (URLs with query params, headers)."""
    msg = f"{type(exc).__name__}"
    detail = str(exc)
    if detail:
        # Drop everything after the first '?', '&apiKey', or 'Authorization'
        for marker in ("apiKey", "api_key", "Authorization", "Bearer "):
            if marker in detail:
                detail = detail.split(marker)[0] + "[redacted]"
                break
        # Trim very long messages
        if len(detail) > 200:
            detail = detail[:200] + "..."
        msg = f"{msg}: {detail}"
    return msg


# ---------------------------------------------------------------------------
# Simple retry helper
# ---------------------------------------------------------------------------
def _retry(fn: Callable, attempts: int, base_delay: float = 0.5):
    last_exc: Optional[BaseException] = None
    for i in range(attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if i < attempts:
                time.sleep(base_delay * (2 ** i))
    if last_exc:
        raise last_exc


# ---------------------------------------------------------------------------
# Call counter (best-effort, in-memory only — reset per dashboard refresh)
# ---------------------------------------------------------------------------
class CallCounter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: Dict[str, int] = {}

    def bump(self, name: str, n: int = 1) -> None:
        with self._lock:
            self._counts[name] = self._counts.get(name, 0) + n

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._counts)

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()


COUNTER = CallCounter()


# ---------------------------------------------------------------------------
# Yahoo: prices
# ---------------------------------------------------------------------------
def _demo_price(ticker: str) -> Tuple[pd.DataFrame, ProviderStatus]:
    df = demo_data.load_price_history(ticker)
    if df.empty:
        return df, ProviderStatus("sample:price", ok=False, error="no sample data for ticker")
    return df, ProviderStatus("sample:price", ok=True, records=len(df))


def fetch_price_history(ticker: str, period: str = "6mo") -> Tuple[pd.DataFrame, ProviderStatus]:
    if cfg.resolve_mode() == "demo":
        return _demo_price(ticker)
    name = "yfinance:price"
    try:
        df = _retry(lambda: yf.Ticker(ticker).history(period=period), cfg.YF_MAX_RETRIES)
        COUNTER.bump(name)
        if df is None or df.empty:
            # Fallback to sample data so the dashboard stays alive.
            sdf, _ = _demo_price(ticker)
            if not sdf.empty:
                return sdf, ProviderStatus(name, ok=False,
                                           error="empty response (using sample fallback)",
                                           records=len(sdf))
            return pd.DataFrame(), ProviderStatus(name, ok=False, error="empty response")
        return df, ProviderStatus(name, ok=True, records=len(df))
    except Exception as exc:  # noqa: BLE001
        sdf, _ = _demo_price(ticker)
        if not sdf.empty:
            return sdf, ProviderStatus(name, ok=False,
                                       error=f"{_sanitise_error(exc)} (using sample fallback)",
                                       records=len(sdf))
        return pd.DataFrame(), ProviderStatus(name, ok=False, error=_sanitise_error(exc))


# ---------------------------------------------------------------------------
# Yahoo: fundamentals
# ---------------------------------------------------------------------------
def _demo_funds(ticker: str) -> Tuple[Dict[str, Any], ProviderStatus]:
    f = demo_data.load_fundamentals(ticker)
    present = sum(1 for v in f.values() if v is not None)
    return f, ProviderStatus("sample:fundamentals", ok=present > 0, records=present)


def fetch_fundamentals(ticker: str) -> Tuple[Dict[str, Any], ProviderStatus]:
    if cfg.resolve_mode() == "demo":
        return _demo_funds(ticker)
    name = "yfinance:fundamentals"
    try:
        info = _retry(lambda: yf.Ticker(ticker).info, cfg.YF_MAX_RETRIES) or {}
        COUNTER.bump(name)
        funds = {
            "P/B": info.get("priceToBook"),
            "EV/EBITDA": info.get("enterpriseToEbitda"),
            "Debt/Equity": info.get("debtToEquity"),
            "Current_Ratio": info.get("currentRatio"),
            "Market_Cap": info.get("marketCap"),
            "Shares_Out": info.get("sharesOutstanding"),
        }
        present = sum(1 for v in funds.values() if v is not None)
        return funds, ProviderStatus(name, ok=present > 0, records=present,
                                     error=None if present else "all fundamentals missing")
    except Exception as exc:  # noqa: BLE001
        # Fall back to sample data if available so the dashboard keeps rendering.
        sf, _ = _demo_funds(ticker)
        if any(v is not None for v in sf.values()):
            return sf, ProviderStatus(name, ok=False,
                                      error=f"{_sanitise_error(exc)} (using sample fallback)",
                                      records=sum(1 for v in sf.values() if v is not None))
        return {
            "P/B": None, "EV/EBITDA": None, "Debt/Equity": None,
            "Current_Ratio": None, "Market_Cap": None, "Shares_Out": None,
        }, ProviderStatus(name, ok=False, error=_sanitise_error(exc))


# ---------------------------------------------------------------------------
# News: NewsAPI primary, yfinance fallback
# ---------------------------------------------------------------------------
def _build_query(company_name: str, ticker: str) -> str:
    """Construct a focused NewsAPI query string.

    - Quoted company name (exact phrase)
    - Ticker only when not in the ambiguous list
    - Always ANDed with maritime context to avoid unrelated noise
    """
    parts: List[str] = [f'"{company_name}"']
    if ticker not in cfg.AMBIGUOUS_TICKERS:
        parts.append(ticker)
    name_clause = "(" + " OR ".join(parts) + ")"
    context_clause = "(" + " OR ".join(cfg.MARITIME_CONTEXT_TERMS[:6]) + ")"
    return f"{name_clause} AND {context_clause}"


def _newsapi_call(query: str, hours: int) -> List[Dict[str, Any]]:
    if not cfg.NEWSAPI_KEY:
        return []
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
    params = {
        "q": query,
        "from": since,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": cfg.NEWSAPI_PAGE_SIZE,
        "apiKey": cfg.NEWSAPI_KEY,
    }

    def _do() -> List[Dict[str, Any]]:
        r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=cfg.NEWSAPI_TIMEOUT)
        if r.status_code != 200:
            raise RuntimeError(f"newsapi http {r.status_code}")
        return r.json().get("articles", []) or []

    return _retry(_do, cfg.NEWSAPI_MAX_RETRIES)


def _yfinance_news(ticker: str, hours: int) -> List[Dict[str, Any]]:
    try:
        items = yf.Ticker(ticker).news or []
    except Exception:  # noqa: BLE001
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out: List[Dict[str, Any]] = []
    for item in items:
        # yfinance schema varies by version; flatten what we can.
        title = item.get("title") or (item.get("content") or {}).get("title", "")
        url = item.get("link") or item.get("url") or (item.get("content") or {}).get("clickThroughUrl", {}).get("url", "")
        ts = item.get("providerPublishTime")
        when = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
        if when and when < cutoff:
            continue
        out.append({
            "title": title,
            "url": url,
            "source": item.get("publisher", "yfinance"),
            "publishedAt": when.isoformat() if when else "",
        })
    return out


def _normalise_newsapi(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for a in articles:
        out.append({
            "title": a.get("title") or "",
            "url": a.get("url") or "",
            "source": (a.get("source") or {}).get("name") or "",
            "publishedAt": a.get("publishedAt") or "",
            "description": a.get("description") or "",
        })
    return out


def _relevance(text: str) -> float:
    """0..1 relevance score based on maritime/geo keyword density."""
    if not text:
        return 0.0
    t = text.lower()
    hits = 0
    for kw in cfg.MARITIME_CONTEXT_TERMS:
        if kw in t:
            hits += 1
    for kw in cfg.GEO_KEYWORDS:
        if kw in t:
            hits += 1
    return min(1.0, hits / 4.0)


def _score_one(item: Dict[str, Any]) -> Dict[str, Any]:
    title = item.get("title") or ""
    desc = item.get("description") or ""
    text = f"{title}. {desc}"
    sent = _analyzer.polarity_scores(title)["compound"] if title else 0.0
    geo_hits = [k for k in cfg.GEO_KEYWORDS if k in text.lower()]
    return {
        **item,
        "sentiment": round(sent, 3),
        "geo_keywords": ", ".join(geo_hits),
        "relevance": round(_relevance(text), 3),
    }


def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_url, seen_title, out = set(), set(), []
    for it in items:
        u = (it.get("url") or "").strip()
        t = (it.get("title") or "").strip().lower()
        if u and u in seen_url:
            continue
        if t and t in seen_title:
            continue
        if u:
            seen_url.add(u)
        if t:
            seen_title.add(t)
        out.append(it)
    return out


@dataclass
class NewsResult:
    headlines: List[Dict[str, Any]]
    avg_sentiment: float
    geo_alert: bool
    relevant_count: int
    source: str           # "newsapi" | "yfinance" | "none"
    fallback_used: bool


def _demo_news(ticker: str) -> Tuple[NewsResult, ProviderStatus]:
    raw = demo_data.load_news_headlines(ticker)
    scored = _dedupe([_score_one(h) for h in raw if h.get("title")])
    relevant = [h for h in scored if h.get("relevance", 0.0) >= cfg.MIN_RELEVANCE]
    sentiments = [h["sentiment"] for h in relevant]
    avg = sum(sentiments) / len(sentiments) if sentiments else 0.0
    geo = any(h.get("geo_keywords") for h in relevant)
    res = NewsResult(headlines=scored, avg_sentiment=avg, geo_alert=geo,
                     relevant_count=len(relevant), source="sample", fallback_used=False)
    return res, ProviderStatus("sample:news", ok=len(scored) > 0, records=len(scored))


def fetch_news(company_name: str, ticker: str, hours: int = cfg.DEFAULT_NEWS_HOURS,
               ) -> Tuple[NewsResult, ProviderStatus]:
    if cfg.resolve_mode() == "demo":
        return _demo_news(ticker)
    name = "news"
    headlines: List[Dict[str, Any]] = []
    source = "none"
    fallback_used = False
    error: Optional[str] = None
    used_provider = "no provider"

    if cfg.NEWSAPI_KEY:
        used_provider = "newsapi"
        try:
            raw = _newsapi_call(_build_query(company_name, ticker), hours)
            COUNTER.bump("newsapi")
            headlines = _normalise_newsapi(raw)
            if headlines:
                source = "newsapi"
        except Exception as exc:  # noqa: BLE001
            error = _sanitise_error(exc)

    if not headlines:
        used_provider = "yfinance" if source == "none" else used_provider
        try:
            yf_items = _yfinance_news(ticker, hours)
            COUNTER.bump("yfinance:news")
            if yf_items:
                if source == "newsapi":
                    fallback_used = False  # NewsAPI succeeded but returned 0
                else:
                    fallback_used = True
                    source = "yfinance"
                headlines.extend(yf_items)
        except Exception as exc:  # noqa: BLE001
            error = error or _sanitise_error(exc)

    headlines = _dedupe([_score_one(h) for h in headlines if h.get("title")])

    relevant = [h for h in headlines if h.get("relevance", 0.0) >= cfg.MIN_RELEVANCE]
    sentiments = [h["sentiment"] for h in relevant]
    avg = sum(sentiments) / len(sentiments) if sentiments else 0.0
    geo = any(h.get("geo_keywords") for h in relevant)

    # Final fallback: if both providers returned nothing, use sample data
    # so the user sees *something*. Mark explicitly.
    if not headlines:
        sample_res, _ = _demo_news(ticker)
        if sample_res.headlines:
            sample_res.fallback_used = True
            sample_res.source = "sample"
            return sample_res, ProviderStatus(
                f"news:{used_provider} (sample fallback)",
                ok=False, records=len(sample_res.headlines),
                error=error or "no relevant headlines",
            )

    result = NewsResult(
        headlines=headlines,
        avg_sentiment=avg,
        geo_alert=geo,
        relevant_count=len(relevant),
        source=source,
        fallback_used=fallback_used,
    )
    status = ProviderStatus(
        provider=f"{name}:{used_provider}",
        ok=len(headlines) > 0,
        records=len(headlines),
        error=error,
    )
    return result, status


# ---------------------------------------------------------------------------
# BDRY (BDI proxy)
# ---------------------------------------------------------------------------
@dataclass
class BdiResult:
    last: Optional[float]
    pct_5d: Optional[float]
    pct_20d: Optional[float]
    series: pd.Series
    trend: str

    def to_metrics(self) -> Dict[str, Any]:
        return {
            "last": self.last,
            "pct_5d": self.pct_5d,
            "pct_20d": self.pct_20d,
            "trend": self.trend,
        }


def _demo_bdi() -> Tuple[Optional[BdiResult], ProviderStatus]:
    series = demo_data.load_bdry_series()
    if series.empty:
        return None, ProviderStatus("sample:BDRY", ok=False, error="no sample data")
    last = float(series.iloc[-1])
    pct_5 = float((series.iloc[-1] / series.iloc[-6] - 1) * 100) if len(series) > 5 else None
    pct_20 = float((series.iloc[-1] / series.iloc[-21] - 1) * 100) if len(series) > 20 else None
    trend = "rising" if (pct_20 or 0) > 0 else "falling"
    return BdiResult(last=last, pct_5d=pct_5, pct_20d=pct_20, series=series, trend=trend), \
           ProviderStatus("sample:BDRY", ok=True, records=len(series))


def fetch_bdi_proxy() -> Tuple[Optional[BdiResult], ProviderStatus]:
    if cfg.resolve_mode() == "demo":
        return _demo_bdi()
    name = "yfinance:BDRY"
    try:
        df = _retry(lambda: yf.Ticker("BDRY").history(period="3mo"), cfg.YF_MAX_RETRIES)
        COUNTER.bump(name)
        if df is None or df.empty:
            return None, ProviderStatus(name, ok=False, error="empty BDRY response")
        close = df["Close"].dropna()
        if close.empty:
            return None, ProviderStatus(name, ok=False, error="empty BDRY series")
        last = float(close.iloc[-1])
        pct_5 = float((close.iloc[-1] / close.iloc[-min(6, len(close))] - 1) * 100) if len(close) > 5 else None
        pct_20 = float((close.iloc[-1] / close.iloc[-min(21, len(close))] - 1) * 100) if len(close) > 20 else None
        trend = "rising" if (pct_20 or 0) > 0 else "falling"
        return BdiResult(last=last, pct_5d=pct_5, pct_20d=pct_20, series=close, trend=trend), \
               ProviderStatus(name, ok=True, records=len(close))
    except Exception as exc:  # noqa: BLE001
        sres, _ = _demo_bdi()
        if sres is not None:
            return sres, ProviderStatus(name, ok=False,
                                        error=f"{_sanitise_error(exc)} (using sample fallback)")
        return None, ProviderStatus(name, ok=False, error=_sanitise_error(exc))


# ---------------------------------------------------------------------------
# Paid maritime data — placeholder layer (returns "not configured")
# ---------------------------------------------------------------------------
def paid_provider_status() -> List[Dict[str, Any]]:
    """Return availability snapshot for paid maritime providers."""
    out = []
    for name, env_var, purpose in cfg.PAID_PROVIDERS:
        out.append({
            "provider": name,
            "purpose": purpose,
            "configured": cfg.has_key(env_var),
            "status": "configured (not yet implemented)" if cfg.has_key(env_var) else "not configured",
        })
    return out
