"""Manual live smoke test. Hits real Yahoo + (optional) NewsAPI.

Run:
    python3 scripts/smoke_test.py

Prints provider status + one ZIM watchlist row. Never prints API keys.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from maritime_data import build_watchlist  # noqa: E402


def main() -> int:
    print(f"NewsAPI key detected: {bool(config.NEWSAPI_KEY)}")
    result = build_watchlist(watchlist={"ZIM Integrated Shipping": "ZIM"})
    rows = result["rows"]
    print(f"Refreshed at: {result['refreshed_at']}")
    print(f"Failed tickers: {result['failures']}")
    for s in result["statuses"]:
        print(f"  - {s.provider}: ok={s.ok}, records={s.records}, error={s.error or '-'}")
    if rows:
        r = rows[0]
        print("\nZIM:")
        for k in ("Ticker", "Price", "RSI", "Trend", "Action", "Confidence",
                  "Signal Score", "Risk Score", "Rationale"):
            print(f"  {k}: {r.get(k)}")
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
