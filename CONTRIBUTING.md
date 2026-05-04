# Contributing

Thanks for considering a contribution! This is a small, focused research
project — a few principles keep it that way.

## Ground rules

- **Honest data.** Never fabricate live market or news values. Sample
  data lives in `sample_data/` and is clearly labelled.
- **No secrets in commits.** API keys load from `.env` only. The
  `.gitignore` covers it; please double-check before pushing.
- **Don't add heavy dependencies** unless they replace something
  load-bearing. The repo deliberately stays close to a small,
  well-known stack (Streamlit, Plotly, pandas, yfinance, requests).
- **Don't market it as AI/ML** unless you actually train and validate
  a model. The signal engine is rule-based on purpose.
- **Test what you can offline.** New tests should not require live
  yfinance or NewsAPI. Mock those calls.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # leave NEWSAPI_KEY blank for demo mode
make test                        # run pytest
make run                         # streamlit on :8501
```

## Pull request checklist

Before opening a PR:

- [ ] `make test` is green
- [ ] `python3 -m py_compile` is clean for any file you touched
- [ ] No secrets, no hardcoded keys
- [ ] No live API calls in tests
- [ ] README / docstrings updated if behaviour changed
- [ ] If you added a config knob, it lives in `config.py`

## What's in scope

- Bug fixes, especially around provider failures and edge cases.
- Better demo data (still synthetic — no copyrighted text).
- New technical indicators or signal-engine refinements (with tests).
- Real paid-provider integrations (Baltic Exchange, Clarksons, etc.) —
  start by extending `providers.py` and `paid_provider_status()`.
- UX polish on the Streamlit dashboard.

## What's out of scope (for now)

- Anything claiming predictive power without rigorous backtests.
- Adding live data sources that require user logins or break TOS.
- Heavyweight ML frameworks (keep `requirements.txt` lean).

## Questions or proposals

Open an issue first for anything non-trivial — it's faster than a PR
that misses the goal.
