"""Central configuration for the maritime dashboard.

All tunable knobs live here so they can be changed in one place and
covered by tests. Secrets are loaded from .env via a minimal in-process
loader (no python-dotenv dependency required).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


# ---------------------------------------------------------------------------
# .env loader (minimal — keeps dependency surface small)
# ---------------------------------------------------------------------------
def load_dotenv(path: Path | None = None) -> None:
    """Populate os.environ from a .env file. Existing env vars win."""
    env_path = path or (Path(__file__).parent / ".env")
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)
    except OSError:
        # Unreadable .env should not crash the app.
        return


load_dotenv()


# ---------------------------------------------------------------------------
# Application mode (demo / live / auto)
# ---------------------------------------------------------------------------
# - "demo"  : always use bundled sample data (no network, no quota)
# - "live"  : require live providers; surface failures honestly
# - "auto"  : live if a NewsAPI key is configured AND yfinance is reachable,
#             otherwise demo. Resolved at runtime by `resolve_mode()`.
APP_MODE: str = os.environ.get("APP_MODE", "auto").strip().lower() or "auto"

# Where to find bundled sample fixtures.
SAMPLE_DATA_DIR: Path = Path(__file__).parent / "sample_data"


# ---------------------------------------------------------------------------
# Secrets (boolean presence checks only — never expose values)
# ---------------------------------------------------------------------------
NEWSAPI_KEY: str = os.environ.get("NEWSAPI_KEY", "").strip()

# Placeholders for future paid maritime providers. Presence-only, never logged.
BALTIC_EXCHANGE_KEY: str = os.environ.get("BALTIC_EXCHANGE_KEY", "").strip()
CLARKSONS_KEY: str = os.environ.get("CLARKSONS_KEY", "").strip()
VESSELSVALUE_KEY: str = os.environ.get("VESSELSVALUE_KEY", "").strip()
KPLER_KEY: str = os.environ.get("KPLER_KEY", "").strip()
MARINETRAFFIC_KEY: str = os.environ.get("MARINETRAFFIC_KEY", "").strip()


def has_key(name: str) -> bool:
    """Presence check by env-var name. Never returns the value."""
    return bool(os.environ.get(name, "").strip())


def resolve_mode() -> str:
    """Resolve APP_MODE to a concrete value of demo|live.

    'auto' demotes to 'demo' if no NewsAPI key is set, otherwise 'live'.
    The resolution is intentionally cheap (no network calls) — providers
    will fall back to demo data per-call if a live request fails.
    """
    # Read from module globals so tests can `monkeypatch.setattr(config, ...)`
    # and have it take effect. Production code never mutates these.
    mode = globals().get("APP_MODE", "auto")
    if mode in {"demo", "live"}:
        return mode
    return "live" if globals().get("NEWSAPI_KEY") else "demo"


PAID_PROVIDERS = [
    ("Baltic Exchange", "BALTIC_EXCHANGE_KEY", "Freight indices (BDI, BDTI, BCI)"),
    ("Clarksons", "CLARKSONS_KEY", "TCE rates, fleet data"),
    ("VesselsValue", "VESSELSVALUE_KEY", "Fleet/vessel valuation, FVG inputs"),
    ("Kpler", "KPLER_KEY", "Cargo flow / commodity tracking"),
    ("MarineTraffic", "MARINETRAFFIC_KEY", "AIS vessel positions"),
    # Route Lab placeholders
    ("Bunker prices", "BUNKER_FEED_KEY", "HSFO/IFO380/VLSFO/LSMGO spot prices (Ship & Bunker, Argus, Platts)"),
    ("Suez tolls", "SUEZ_TOLL_FEED_KEY", "SCNT-based toll calculator / SCA circulars"),
    ("War-risk premiums", "WAR_RISK_FEED_KEY", "JWC listed-areas, broker quotes for AWRP"),
    ("Port congestion", "PORT_CONGESTION_FEED_KEY", "Cape/anchorage waiting times"),
    ("Route distances", "ROUTE_DISTANCE_KEY", "Sea-distance / voyage routing API"),
]


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------
DEFAULT_WATCHLIST: Dict[str, str] = {
    "A.P. Moller - Maersk": "MAERSK-B.CO",
    "Hapag-Lloyd": "HLAG.DE",
    "ZIM Integrated Shipping": "ZIM",
    "Frontline Ltd.": "FRO",
    "Star Bulk Carriers": "SBLK",
    "Wallenius Wilhelmsen": "WAWI.OL",
}

# Tickers ambiguous enough that we should NOT use the bare ticker as a
# news-search term (false positives swamp the signal).
AMBIGUOUS_TICKERS = {"FRO", "ZIM", "SBLK"}


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------
DEFAULT_NEWS_HOURS: int = 72
MIN_NEWS_HOURS: int = 12
MAX_NEWS_HOURS: int = 168
NEWSAPI_PAGE_SIZE: int = 25
NEWSAPI_TIMEOUT: int = 8
NEWSAPI_MAX_RETRIES: int = 2

GEO_KEYWORDS = [
    "houthi", "red sea", "suez", "canal", "tariff", "trade war",
    "sanction", "black sea", "drought", "piracy", "embargo", "hormuz",
    "panama canal", "strait", "blockade", "war", "missile", "drone strike",
]

MARITIME_CONTEXT_TERMS = [
    "shipping", "freight", "vessel", "tanker", "container", "bulk carrier",
    "maritime", "port", "cargo", "fleet", "charter",
]

# Relevance scoring (0..1). Headlines below MIN_RELEVANCE are excluded
# from sentiment aggregation.
MIN_RELEVANCE: float = 0.25


# ---------------------------------------------------------------------------
# Indicators / signal thresholds
# ---------------------------------------------------------------------------
RSI_PERIOD: int = 14
SMA_SHORT: int = 20
SMA_MED: int = 50
SMA_LONG: int = 200
VOL_WINDOW: int = 20
DRAWDOWN_LOOKBACK_DAYS: int = 63  # ~3 months

RSI_OVERSOLD: float = 35.0
RSI_OVERBOUGHT: float = 70.0
RSI_NEUTRAL_HIGH: float = 65.0
RSI_NEUTRAL_LOW: float = 50.0

DEBT_EQUITY_HIGH: float = 150.0
DEBT_EQUITY_LOW: float = 50.0
PB_CHEAP: float = 1.0
PB_EXPENSIVE: float = 2.5
EV_EBITDA_CHEAP: float = 5.0
CURRENT_RATIO_WEAK: float = 1.0


# ---------------------------------------------------------------------------
# HTTP / cache
# ---------------------------------------------------------------------------
HTTP_TIMEOUT: int = 8
YF_MAX_RETRIES: int = 2
WATCHLIST_CACHE_TTL: int = 300   # 5 min
PRICE_CACHE_TTL: int = 300
BDI_CACHE_TTL: int = 900         # 15 min


# ---------------------------------------------------------------------------
# Backtest defaults
# ---------------------------------------------------------------------------
BT_INITIAL_CASH: float = 100_000.0
BT_COMMISSION_BPS: float = 10.0   # 0.10% per side
BT_SLIPPAGE_BPS: float = 5.0      # 0.05% per side
BT_RISK_FREE_RATE: float = 0.04   # for Sharpe
TRADING_DAYS_PER_YEAR: int = 252
