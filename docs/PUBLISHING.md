# Publishing checklist

A short list to run through before pushing this repo to a public remote
or deploying it.

## 1. Rotate any exposed secrets

If a NewsAPI key (or any other key) has appeared in chat, screenshots,
logs, prompts, or commits, **rotate it now** at the provider's dashboard.
Old keys remain valid until you do.

## 2. Run the diagnostics

```bash
python3 scripts/doctor.py            # PASS/WARN/FAIL setup audit
python3 scripts/security_check.py    # static secret scan
python3 -m pytest -q                 # offline test suite
python3 -m pip check                 # dependency consistency
```

All three should be clean. The doctor will keep WARN-ing about
"project .git not initialised" and "parent .git invalid" until you
resolve the local Git situation — that's expected on first publish.

## 3. Capture screenshots (optional)

```bash
APP_MODE=demo python3 -m streamlit run dashboard.py
```

Open <http://localhost:8501> and capture the **Overview** tab and the
**🛳️ VLCC Route Lab → Cost Breakdown** sub-tab. Save them under
`docs/screenshots/` per `docs/screenshots/README.md`. Run in **demo
mode** so the frame contains no live or proprietary data.

## 4. Resolve the parent-`.git` blocker (macOS-specific)

If `git status` from this directory complains, the issue is usually a
zero-byte `.git` *file* in `~/`. **Confirm before moving anything:**

```bash
ls -la "$HOME/.git"
file "$HOME/.git"
```

If it is a zero-byte regular file (not a directory, not a real
gitlink), back it up:

```bash
mv "$HOME/.git" "$HOME/.git.bak"
```

## 5. Initialise the project repo

```bash
cd /Users/$USER/SharepricemovementMaritime-main
git init
git add .
git commit -m "Initial open maritime dashboard"
```

The `.gitignore` already excludes `.env`, virtualenvs, caches, and
Streamlit secrets.

## 6. Push to GitHub

```bash
git remote add origin git@github.com:<your-account>/<repo-name>.git
git branch -M main
git push -u origin main
```

## 7. Configure CI

`.github/workflows/ci.yml` runs `py_compile`, `pytest`, and `pip check`
on Python 3.11 + 3.12. No secrets are required — CI runs entirely in
demo mode.

## 8. Configure deployment secrets (live mode only)

For a public live deployment, add `NEWSAPI_KEY` and (optionally)
`APP_MODE=live` via the platform's secret store:

- **Streamlit Community Cloud** → *App settings → Secrets*.
- **Hugging Face Spaces** → *Settings → Repository secrets*.
- **Docker** → `docker run --env NEWSAPI_KEY=… --env APP_MODE=live …`.

Without `NEWSAPI_KEY`, the app runs in demo mode automatically — that
is the recommended default for a public preview.

> **Reminder:** the NewsAPI free tier is for development only. Public
> live deployments need a paid plan or an alternate news provider —
> see `providers.py`. For the full commercial / data-licensing
> picture, read [COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md).

## 9. Final smoke test

After deployment, hit the public URL and check:

- The mode badge in the header reads `DEMO` (no key set) or `LIVE`.
- The **🩺 Data Health** tab shows provider statuses and "NewsAPI key
  detected: yes/no" — never the value.
- The **🛳️ VLCC Route Lab** loads the default scenario.
