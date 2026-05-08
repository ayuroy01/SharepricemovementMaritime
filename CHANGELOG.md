# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] — 2026-05-04

### Added
- **Visual redesign — dark night-sea theme.** Full dark palette
  (`#07101F` deep navy ground, `#0E1B2E` surfaces, hairlined cards,
  cyan-blue accent, brass for the active-tab indicator), Inter
  webfont, tabular numerals on every metric and dataframe.
- **Animated hero band** with a VLCC tanker silhouette (inline SVG,
  technical-drawing style — not cartoonish), 30 fixed-position stars
  with five animated twinklers, horizon hairline, and a slow specular
  sheen across the water. Pure SVG + CSS keyframes; no JS, ~5 KB
  inline. Wrapped in `prefers-reduced-motion` so it freezes
  gracefully.
- `theme.py` — single source of truth for color tokens, `apply_theme()`
  for Plotly figures, and a custom diverging colormap that replaces
  RdYlGn / RdYlGn_r in the Route Lab heatmaps so they read on dark.
- Re-tuned **mode badges** (DEMO / LIVE / FALLBACK) to desaturated
  hairlined chips instead of solid pills.
- Re-tuned **Action chips** in tables and overview lists to match the
  badge palette (replaces the previous saturated greens/reds).

### Changed
- `.streamlit/config.toml` `[theme]` switched to `base = "dark"` with
  the new palette so first-paint matches the redesign.
- All Plotly figures now route through `theme.apply_theme()` for
  consistent paper/plot colors, gridlines, hover labels, and legends.
- Drill-down price chart, BDRY chart, drawdown charts, equity curve,
  and Route Lab stacked bar use the new colorway.
- Pandas Styler `background_gradient` calls in the Route Lab use
  `theme.diverging_cmap()` (red ↔ hairline ↔ green) instead of
  matplotlib RdYlGn / RdYlGn_r.

### Notes
- No new runtime dependencies. The optional `matplotlib` import is
  guarded; the diverging colormap silently falls back if matplotlib
  isn't installed (it's already in `requirements.txt`).
- All 81 tests still pass; provider/security/doctor checks unchanged.

## [0.4.0] — 2026-05-02

### Added
- **Local launcher** (`launcher.py`) — Tkinter GUI with terminal
  fallback. Detects mode (DEMO/LIVE/AUTO) and NewsAPI key presence
  without ever displaying the value. Run / Stop / Doctor / Security /
  Tests / Smoke / Open README / Open localhost buttons. Auto-selects
  next free port if 8501 is busy.
- **`scripts/doctor.py`** — PASS/WARN/FAIL setup check covering
  Python, files, imports, .env, .gitignore, project + parent .git,
  sample data, and port availability. Outputs concrete next steps.
- **`scripts/security_check.py`** — static audit for likely leaked
  secrets across tracked files. Returns non-zero on any finding;
  reports redacted matches only (`[redacted, length=N]`).
- **`tests/test_security_check.py`** — verifies the redactor never
  emits raw values and placeholders are correctly allowlisted.
- **Route Lab terminology fixes**: new
  `RouteCostResult.total_cost_ex_insurance`,
  `pre_insurance_differential_cape_minus_suez`,
  `breakeven_combined_suez_insurance_usd`, plus dashboard metrics with
  help captions distinguishing all-in totals from pre-insurance and
  combined-USD break-even framings. Tests for each new function.
- `docs/screenshots/` directory with capture instructions; README
  updated to use it (no broken image links).
- `.streamlit/config.toml` — light theme tuning, usage stats off.
- `pyproject.toml` — pytest + ruff config (no mandatory dependency).
- Makefile targets: `launch`, `run-demo`, `run-live`, `run-auto`,
  `doctor`, `security-check`, `screenshot`.

### Changed
- README: launcher quick-start, screenshot workflow, Git-troubleshooting
  section with the safe parent-`.git` recovery steps, expanded
  Route Lab section explaining why different break-even numbers exist.
- SECURITY.md: explicit key-rotation procedure, deployment-secrets
  guidance, and how to use `security_check.py`.

## [0.3.0] — 2026-05-02

### Added
- **VLCC Route Lab** — deterministic voyage-economics calculator with
  five sub-tabs (Scenario, Cost Breakdown, Sensitivity, Regulation,
  Assumptions & Sources). Compares Cape of Good Hope vs Suez Canal for
  a Persian Gulf → Singapore VLCC voyage.
- `route_economics.py` module: dataclasses (`VesselProfile`,
  `FuelAssumptions`, `CharterAssumptions`, `InsuranceAssumptions`,
  `RouteAssumptions`, `RegulationAssumptions`, `RouteScenario`,
  `RouteCostResult`, `ComparisonResult`, `SensitivityResult`),
  `compute_route_cost`, `compare_routes`, `breakeven_hm_awrp_pct_for_suez`,
  `sensitivity_matrix`, `scrubber_analysis`, `ets_coverage_fraction`,
  `assumption_rows`.
- `sample_data/route_scenarios/may_2026_vlcc_pg_singapore.json` —
  editable default scenario with explicit `sources` array.
- `tests/test_route_economics.py` — 20+ deterministic offline tests
  covering cost components, ETS scope rules, break-even AWRP,
  sensitivity matrix, scrubber economics, and edge cases.
- New paid-provider placeholders in `config.PAID_PROVIDERS`:
  bunker prices, Suez tolls, war-risk premiums, port congestion,
  route distances.
- README sections for VLCC Route Lab + Roadmap with EU ETS source
  citations.

### Notes
- No live data feeds for bunker / toll / war-risk / congestion / EUA
  prices — all are user-editable scenario inputs labelled accordingly.

## [0.2.0] — 2026-05-01

### Added
- **Demo / Live / Fallback modes** with `APP_MODE` env var and runtime
  resolver. Demo mode runs with no API keys using bundled synthetic data
  in `sample_data/`.
- `demo_data.py` loader and `sample_data/generate.py` deterministic
  fixture generator.
- Public-ready dashboard: hero header with mode badge, signal
  distribution chart, top constructive / most cautionary panels,
  CSV export, news-tab filters (sentiment / geo / search), Plotly
  drawdown charts on Drill-down and Backtest tabs.
- OSS metadata: `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, GitHub issue/PR templates.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`.
- `Makefile` with `install`, `test`, `smoke`, `run`, `lint` targets.
- GitHub Actions CI workflow (compile, pytest, pip check).

### Changed
- `providers.py` falls back to sample data on live failure and labels
  the call as a sample-fallback in the Data Health panel.
- `maritime_data.build_watchlist` returns `app_mode`, `effective_mode`,
  and `fallback_count`.

## [0.1.0] — 2026-04-30

### Added
- Initial modular pipeline: `config.py`, `providers.py`, `indicators.py`,
  `signals.py`, `backtest.py`, `maritime_data.py`, tabbed Streamlit
  dashboard, pytest suite, README.
