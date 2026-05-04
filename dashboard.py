"""Open Maritime Quant Dashboard — Streamlit UI.

Run:  python3 -m streamlit run dashboard.py

Modes:
  - DEMO     : bundled synthetic sample data (no API keys, no network).
  - LIVE     : yfinance + NewsAPI when configured.
  - FALLBACK : LIVE attempted but at least one provider returned sample data.

Configure via env vars (see .env.example):
  APP_MODE=demo|live|auto   NEWSAPI_KEY=...
"""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config as cfg
from backtest import run_backtest
from maritime_data import build_watchlist
from providers import fetch_price_history


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Maritime Quant Dashboard",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Light CSS polish — kept minimal so Streamlit themes still work.
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.4rem; padding-bottom: 1rem; }
      div[data-testid="stMetricValue"] { font-size: 1.4rem; }
      .mode-badge {
        display:inline-block; padding:2px 10px; border-radius:10px;
        font-size:0.78rem; font-weight:600; letter-spacing:0.04em;
        vertical-align:middle; margin-left:8px;
      }
      .mode-DEMO    { background:#0277bd; color:#fff; }
      .mode-LIVE    { background:#1b5e20; color:#fff; }
      .mode-FALLBACK{ background:#ef6c00; color:#fff; }
      .footer { color:#888; font-size:0.78rem; margin-top:1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Open Maritime Quant")
    st.caption("Research dashboard · open source · not investment advice")
    st.markdown("---")

    news_hours = st.slider(
        "News window (hours)",
        cfg.MIN_NEWS_HOURS, cfg.MAX_NEWS_HOURS, cfg.DEFAULT_NEWS_HOURS, 12,
    )
    auto_refresh = st.checkbox("Auto-refresh every 5 min", value=False)
    st.markdown("---")
    if cfg.NEWSAPI_KEY:
        st.success("NewsAPI key detected")
    else:
        st.info("No NewsAPI key. Demo mode bundled — public users still see headlines.")
    if st.button("Refresh now", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption(
        "Configure via environment:\n"
        "- `APP_MODE` = demo / live / auto\n"
        "- `NEWSAPI_KEY` = optional"
    )

if auto_refresh:
    st.markdown("<meta http-equiv='refresh' content='300'>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached data layer
# ---------------------------------------------------------------------------
@st.cache_data(ttl=cfg.WATCHLIST_CACHE_TTL, show_spinner=False)
def cached_watchlist(hours: int) -> Dict[str, Any]:
    return build_watchlist(news_hours=hours)


@st.cache_data(ttl=cfg.PRICE_CACHE_TTL, show_spinner=False)
def cached_price_history(ticker: str, period: str = "6mo") -> pd.DataFrame:
    df, _ = fetch_price_history(ticker, period=period)
    if df.empty:
        return df
    df = df.copy()
    df["SMA_20"] = df["Close"].rolling(cfg.SMA_SHORT).mean()
    df["SMA_50"] = df["Close"].rolling(cfg.SMA_MED).mean()
    df["SMA_200"] = df["Close"].rolling(cfg.SMA_LONG).mean()
    return df


with st.spinner("Loading watchlist (price + fundamentals + news)…"):
    data = cached_watchlist(news_hours)

rows: List[Dict[str, Any]] = data["rows"]
df = pd.DataFrame(rows) if rows else pd.DataFrame()
bdi = data.get("bdi")
failures: List[str] = data.get("failures", [])
refreshed_at: str = data.get("refreshed_at", "")
mode: str = data.get("effective_mode", "demo").upper()


# ---------------------------------------------------------------------------
# Hero / header
# ---------------------------------------------------------------------------
hero_l, hero_r = st.columns([3, 2])
with hero_l:
    st.markdown(
        f"## 🚢 Open Maritime Quant Dashboard "
        f"<span class='mode-badge mode-{mode}'>{mode}</span>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Maritime equity monitoring · shipping/freight proxy · news & geopolitical risk · "
        "transparent rule-based scoring · honest backtests."
    )
with hero_r:
    health_ok = len(failures) == 0
    st.markdown(
        f"<div style='text-align:right; padding-top:0.5rem;'>"
        f"<b>Data health:</b> "
        f"<span style='color:{'#1b5e20' if health_ok else '#b71c1c'}'>"
        f"{'OK' if health_ok else f'{len(failures)} failed'}</span><br>"
        f"<span style='color:#666;'>Refreshed (UTC): {refreshed_at[-8:] if refreshed_at else '—'}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

if mode == "DEMO":
    st.info(
        "📦 **Demo mode** — using bundled synthetic sample data. "
        "No live providers are being called. "
        "Set `NEWSAPI_KEY` and `APP_MODE=live` (or `auto`) to use real data.",
        icon="ℹ️",
    )
elif mode == "FALLBACK":
    st.warning(
        "⚠️ **Fallback mode** — at least one live provider failed and was substituted "
        "with sample data. See the **Data Health** tab for details.",
        icon="⚠️",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ACTION_COLORS = {
    "VALUE BUY": "#1b5e20", "MOMENTUM BUY": "#2e7d32",
    "PROFIT TAKE": "#ef6c00",
    "SELL": "#c62828", "STRONG SELL": "#b71c1c", "AVOID": "#880e4f",
    "HOLD": "#455a64", "ERROR": "#000000",
}


def color_action(val: str) -> str:
    bg = ACTION_COLORS.get(str(val), "")
    return f"background-color: {bg}; color: white" if bg else ""


def fmt_pct(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    try:
        return f"{x*100:+.2f}%"
    except Exception:  # noqa: BLE001
        return "—"


def fmt_num(x, ndigits=2):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    try:
        return f"{x:.{ndigits}f}"
    except Exception:  # noqa: BLE001
        return "—"


def metrics_row() -> None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    if bdi:
        c1.metric("BDRY (BDI proxy)", f"${bdi.last:.2f}" if bdi.last is not None else "—",
                  f"{bdi.pct_5d:+.2f}% 5d" if bdi.pct_5d is not None else "")
        c2.metric("BDRY 20d", f"{bdi.pct_20d:+.2f}%" if bdi.pct_20d is not None else "—")
        c3.metric("BDI Trend", bdi.trend.upper())
    else:
        c1.metric("BDRY (BDI proxy)", "n/a"); c2.metric("BDRY 20d", "—"); c3.metric("BDI Trend", "—")
    c4.metric("Tickers", len(rows))
    c5.metric("Failed", len(failures), delta_color="inverse")
    geo_alerts = int(df["Geo Alert"].sum()) if not df.empty and "Geo Alert" in df.columns else 0
    c6.metric("Geo alerts", geo_alerts)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_overview, tab_watch, tab_drill, tab_news, tab_back, tab_route, tab_health = st.tabs(
    ["📊 Overview", "📋 Watchlist", "🔍 Drill-down", "📰 News",
     "🧪 Backtest", "🛳️ VLCC Route Lab", "🩺 Data Health"]
)


# ---- Overview --------------------------------------------------------------
with tab_overview:
    metrics_row()
    st.markdown("")
    if df.empty:
        st.error("No data returned from upstream providers.")
    else:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Signal distribution")
            counts = df.groupby("Action").size().reset_index(name="count").sort_values("count", ascending=False)
            colors = [ACTION_COLORS.get(a, "#888") for a in counts["Action"]]
            fig = go.Figure(go.Bar(
                x=counts["count"], y=counts["Action"], orientation="h",
                marker=dict(color=colors), text=counts["count"], textposition="outside",
            ))
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="", yaxis_title="", showlegend=False)
            st.plotly_chart(fig, width="stretch")
        with c2:
            st.subheader("Sub-scores by ticker")
            chart_df = df[["Ticker", "Tech Score", "Fund Score", "News Score"]].set_index("Ticker")
            st.bar_chart(chart_df, height=280)

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Top constructive")
            top = df.sort_values("Signal Score", ascending=False).head(3)
            for _, r in top.iterrows():
                st.markdown(
                    f"**{r['Ticker']}** · {r['Company']} · "
                    f"<span style='background:{ACTION_COLORS.get(r['Action'], '#888')};color:white;"
                    f"padding:1px 6px;border-radius:4px;font-size:0.8em;'>{r['Action']}</span> · "
                    f"score `{r['Signal Score']:+.2f}` · {r['Rationale']}",
                    unsafe_allow_html=True,
                )
        with c4:
            st.subheader("Most cautionary")
            bot = df.sort_values("Signal Score", ascending=True).head(3)
            for _, r in bot.iterrows():
                st.markdown(
                    f"**{r['Ticker']}** · {r['Company']} · "
                    f"<span style='background:{ACTION_COLORS.get(r['Action'], '#888')};color:white;"
                    f"padding:1px 6px;border-radius:4px;font-size:0.8em;'>{r['Action']}</span> · "
                    f"score `{r['Signal Score']:+.2f}` · {r['Rationale']}",
                    unsafe_allow_html=True,
                )

        if bdi and len(bdi.series) > 0:
            st.subheader("BDRY (BDI proxy)")
            bd_fig = go.Figure(go.Scatter(x=bdi.series.index, y=bdi.series.values,
                                          fill="tozeroy", line=dict(color="#0277bd")))
            bd_fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10),
                                 yaxis_title="BDRY close")
            st.plotly_chart(bd_fig, width="stretch")


# ---- Watchlist -------------------------------------------------------------
with tab_watch:
    metrics_row()
    st.markdown("")
    if df.empty:
        st.error("No data returned from upstream providers.")
    else:
        with st.expander("Filters", expanded=True):
            f1, f2, f3, f4 = st.columns(4)
            actions = sorted(df["Action"].unique().tolist())
            sel_actions = f1.multiselect("Action", actions, default=actions, key="watch_action_filter")
            geo_only = f2.checkbox("Geo Alert only", value=False, key="watch_geo_only")
            ticker_filter = f3.multiselect(
                "Ticker", sorted(df["Ticker"].unique().tolist()), key="watch_ticker_filter",
            )
            min_conf = f4.selectbox(
                "Min confidence", ["low", "medium", "high"], index=0, key="watch_min_conf",
            )
            f5, f6 = st.columns([3, 1])
            search = f5.text_input("Search ticker / company", "", key="watch_search")
            data_warn_only = f6.checkbox("Data warnings only", value=False, key="watch_data_warn_only")

        conf_rank = {"low": 0, "medium": 1, "high": 2}
        view = df[df["Action"].isin(sel_actions)]
        view = view[view["Confidence"].map(conf_rank).fillna(0) >= conf_rank[min_conf]]
        if geo_only:
            view = view[view["Geo Alert"] == True]  # noqa: E712
        if ticker_filter:
            view = view[view["Ticker"].isin(ticker_filter)]
        if search.strip():
            s = search.strip().lower()
            view = view[
                view["Ticker"].str.lower().str.contains(s, na=False)
                | view["Company"].str.lower().str.contains(s, na=False)
            ]
        if data_warn_only:
            view = view[view["Data Warnings"].astype(str).str.len() > 0]

        display_cols = [
            "Ticker", "Company", "Price", "% Change", "RSI", "Trend", "SMA20>SMA50",
            "P/B", "EV/EBITDA", "Debt/Equity", "Current Ratio",
            "News Score", "Geo Alert", "Action", "Confidence",
            "Signal Score", "Risk Score", "Rationale",
        ]
        cols = [c for c in display_cols if c in view.columns]
        styled = view[cols].style.map(color_action, subset=["Action"]).format(
            {
                "Price": "{:.2f}", "% Change": "{:+.2f}",
                "RSI": "{:.1f}", "P/B": "{:.2f}", "EV/EBITDA": "{:.2f}",
                "Debt/Equity": "{:.0f}", "Current Ratio": "{:.2f}",
                "News Score": "{:+.2f}", "Signal Score": "{:+.2f}", "Risk Score": "{:.2f}",
            }, na_rep="—",
        )
        st.dataframe(styled, width="stretch", hide_index=True)
        st.caption(f"Showing {len(view)} of {len(df)} rows.")

        export_cols = [
            "Ticker", "Company", "Price", "% Change", "RSI", "Trend",
            "P/B", "EV/EBITDA", "Debt/Equity", "Current Ratio",
            "News Score", "Geo Alert", "Action", "Confidence",
            "Signal Score", "Tech Score", "Fund Score", "Risk Score",
            "Rationale", "Risk Warnings", "Data Warnings",
        ]
        csv = view[[c for c in export_cols if c in view.columns]].to_csv(index=False)
        st.download_button("⬇️ Export filtered table (CSV)", csv,
                           file_name="maritime_watchlist.csv", mime="text/csv")


# ---- Drill-down ------------------------------------------------------------
with tab_drill:
    metrics_row()
    st.markdown("")
    if df.empty:
        st.error("No data to drill into.")
    else:
        ticker_choice = st.selectbox(
            "Pick a ticker", options=df["Ticker"].tolist(),
            format_func=lambda t: f"{t} — {df.loc[df['Ticker']==t, 'Company'].iloc[0]}",
            key="drill_ticker_choice",
        )
        row = df.loc[df["Ticker"] == ticker_choice].iloc[0].to_dict()
        st.markdown(f"### {row['Company']} ({row['Ticker']})")

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Action", row["Action"])
        a2.metric("Confidence", row["Confidence"])
        a3.metric("Signal", f"{row['Signal Score']:+.2f}")
        a4.metric("Risk", f"{row['Risk Score']:.2f}")
        st.write(row["Rationale"])

        if row.get("Risk Warnings"):
            st.warning("**Risk:** " + row["Risk Warnings"])
        if row.get("Data Warnings"):
            st.info("**Data quality:** " + row["Data Warnings"])

        hist = cached_price_history(ticker_choice)
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close",
                                     line=dict(width=2, color="#0d47a1")))
            for col, dash, color in [
                ("SMA_20", "dot", "#42a5f5"),
                ("SMA_50", "dash", "#7e57c2"),
                ("SMA_200", "longdash", "#9e9e9e"),
            ]:
                if col in hist.columns and hist[col].notna().any():
                    fig.add_trace(go.Scatter(x=hist.index, y=hist[col], name=col,
                                             line=dict(dash=dash, color=color)))
            fig.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10),
                              legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig, width="stretch")

            if "Volume" in hist.columns:
                vfig = go.Figure(go.Bar(x=hist.index, y=hist["Volume"], name="Volume",
                                        marker=dict(color="#90a4ae")))
                vfig.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10),
                                   showlegend=False, yaxis_title="Volume")
                st.plotly_chart(vfig, width="stretch")

            running_max = hist["Close"].cummax()
            dd = (hist["Close"] / running_max - 1.0)
            with st.expander("Drawdown chart"):
                ddfig = go.Figure(go.Scatter(x=dd.index, y=dd * 100, fill="tozeroy",
                                             line=dict(color="#c62828"), name="Drawdown %"))
                ddfig.update_layout(height=220, margin=dict(l=10, r=10, t=20, b=10),
                                    yaxis_title="%")
                st.plotly_chart(ddfig, width="stretch")

        cA, cB = st.columns(2)
        with cA:
            st.markdown("**Technical**")
            st.write({
                "RSI (14)": fmt_num(row["RSI"], 1),
                "Trend": row.get("Trend"),
                "SMA20 > SMA50": row.get("SMA20>SMA50"),
                "5d Return": fmt_pct(row.get("5d Return")),
                "20d Return": fmt_pct(row.get("20d Return")),
                "20d Vol": fmt_pct(row.get("20d Vol")),
                "3m Drawdown": fmt_pct(row.get("3m Drawdown")),
            })
        with cB:
            st.markdown("**Fundamental**")
            st.write({
                "P/B": fmt_num(row["P/B"]),
                "EV/EBITDA": fmt_num(row["EV/EBITDA"]),
                "Debt/Equity": fmt_num(row["Debt/Equity"], 0),
                "Current Ratio": fmt_num(row["Current Ratio"]),
                "News source": row.get("_news_source"),
                "Relevant headlines": row.get("Relevant News"),
            })

        hl = row.get("_headlines") or []
        if hl:
            st.markdown("**Recent headlines**")
            hl_df = pd.DataFrame(hl)
            keep = [c for c in ["title", "source", "publishedAt", "sentiment",
                                "geo_keywords", "relevance", "url"] if c in hl_df.columns]
            st.dataframe(
                hl_df[keep].head(8),
                width="stretch", hide_index=True,
                column_config={"url": st.column_config.LinkColumn("url")} if "url" in keep else None,
            )


# ---- News ------------------------------------------------------------------
with tab_news:
    metrics_row()
    st.markdown("")
    if df.empty:
        st.error("No news data.")
    else:
        all_rows: List[Dict[str, Any]] = []
        for _, r in df.iterrows():
            for h in r.get("_headlines") or []:
                all_rows.append({
                    "Ticker": r["Ticker"], "Company": r["Company"],
                    "title": h.get("title", ""),
                    "source": h.get("source", ""),
                    "publishedAt": h.get("publishedAt", ""),
                    "sentiment": h.get("sentiment"),
                    "relevance": h.get("relevance"),
                    "geo_keywords": h.get("geo_keywords", ""),
                    "url": h.get("url", ""),
                })
        if not all_rows:
            st.info("No headlines retrieved. In live mode, set `NEWSAPI_KEY` for richer news.")
        else:
            news_df = pd.DataFrame(all_rows)
            n1, n2, n3, n4 = st.columns([1.2, 1.2, 1.2, 1.5])
            t_filter = n1.multiselect(
                "Ticker", sorted(news_df["Ticker"].unique().tolist()), key="news_ticker_filter",
            )
            sentiment_filter = n2.selectbox(
                "Sentiment", ["all", "positive", "neutral", "negative"], index=0,
                key="news_sentiment_filter",
            )
            geo_only = n3.checkbox("Geo keywords only", key="news_geo_only")
            search = n4.text_input("Search title", key="news_search")

            view = news_df.copy()
            if t_filter:
                view = view[view["Ticker"].isin(t_filter)]
            if sentiment_filter == "positive":
                view = view[view["sentiment"] > 0.1]
            elif sentiment_filter == "negative":
                view = view[view["sentiment"] < -0.1]
            elif sentiment_filter == "neutral":
                view = view[view["sentiment"].between(-0.1, 0.1)]
            if geo_only:
                view = view[view["geo_keywords"].astype(str).str.len() > 0]
            if search.strip():
                view = view[view["title"].str.contains(search.strip(), case=False, na=False)]

            view = view.drop_duplicates(subset=["title", "url"]).sort_values("publishedAt", ascending=False)
            st.dataframe(
                view, width="stretch", hide_index=True,
                column_config={"url": st.column_config.LinkColumn("url")},
            )
            st.caption(f"{len(view)} of {len(news_df)} headlines after filters.")
            sources_used = sorted(set(r.get("_news_source", "") for _, r in df.iterrows()))
            st.caption(f"News sources active this refresh: {', '.join(s for s in sources_used if s)}")


# ---- Backtest --------------------------------------------------------------
with tab_back:
    st.subheader("Technical-only backtest")
    st.caption(
        "Strategy: enter when SMA20>SMA50 and 40<RSI<65; exit when SMA20<SMA50 or RSI>75. "
        "Orders fill at next bar's open (no lookahead). Configurable costs and slippage. "
        "Fundamentals/news are excluded — see README for why."
    )
    bc1, bc2, bc3, bc4 = st.columns([1.2, 1, 1, 1])
    bt_ticker = bc1.selectbox(
        "Ticker", options=list(cfg.DEFAULT_WATCHLIST.values()),
        index=list(cfg.DEFAULT_WATCHLIST.values()).index("ZIM")
              if "ZIM" in cfg.DEFAULT_WATCHLIST.values() else 0,
        key="backtest_ticker",
    )
    period = bc2.selectbox("Period", ["1y", "2y", "5y", "10y", "max"], index=2, key="backtest_period")
    commission = bc3.number_input(
        "Commission (bps/side)", 0.0, 100.0, cfg.BT_COMMISSION_BPS, 1.0, key="backtest_commission",
    )
    slippage = bc4.number_input(
        "Slippage (bps/side)", 0.0, 100.0, cfg.BT_SLIPPAGE_BPS, 1.0, key="backtest_slippage",
    )
    run = st.button("Run backtest", type="primary", key="backtest_run")
    if run:
        with st.spinner(f"Backtesting {bt_ticker}…"):
            hist, _ = fetch_price_history(bt_ticker, period=period)
            res = run_backtest(hist, bt_ticker, commission_bps=commission, slippage_bps=slippage)
        if res.bars == 0:
            st.error("No data for backtest. " + " ".join(res.notes))
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total return", f"{res.total_return*100:+.2f}%")
            m2.metric("Buy & hold", f"{res.benchmark_return*100:+.2f}%")
            m3.metric("Max drawdown", f"{res.max_drawdown*100:+.2f}%")
            m4.metric("Sharpe", f"{res.sharpe:.2f}" if res.sharpe is not None else "—")
            n1, n2, n3, n4 = st.columns(4)
            n1.metric("CAGR", f"{res.cagr*100:+.2f}%" if res.cagr is not None else "—")
            n2.metric("Trades", res.n_trades)
            n3.metric("Win rate", f"{res.win_rate*100:.1f}%" if res.win_rate is not None else "—")
            n4.metric("Avg holding (bars)", f"{res.avg_holding_bars:.1f}" if res.avg_holding_bars is not None else "—")

            if res.equity_curve:
                eq_df = pd.DataFrame({"strategy": res.equity_curve},
                                     index=pd.to_datetime(res.equity_dates))
                bench = (hist["Close"] / hist["Close"].iloc[0] * cfg.BT_INITIAL_CASH).reindex(eq_df.index)
                eq_df["buy_hold"] = bench
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=eq_df.index, y=eq_df["strategy"], name="strategy",
                                         line=dict(color="#1b5e20", width=2)))
                fig.add_trace(go.Scatter(x=eq_df.index, y=eq_df["buy_hold"], name="buy & hold",
                                         line=dict(color="#888", width=1, dash="dash")))
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                                  yaxis_title="Equity ($)",
                                  legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig, width="stretch")

                eq_max = eq_df["strategy"].cummax()
                bt_dd = (eq_df["strategy"] / eq_max - 1) * 100
                ddfig = go.Figure(go.Scatter(x=bt_dd.index, y=bt_dd, fill="tozeroy",
                                             line=dict(color="#c62828"), name="Drawdown %"))
                ddfig.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10),
                                    yaxis_title="%")
                st.plotly_chart(ddfig, width="stretch")

            if res.trades:
                st.subheader("Trades")
                st.dataframe(pd.DataFrame([t.__dict__ for t in res.trades]),
                             hide_index=True, width="stretch")
            if res.notes:
                st.caption(" · ".join(res.notes))
            st.warning("Past performance does not guarantee future results. "
                       "This is a technical-only research backtest.")


# ---- VLCC Route Lab --------------------------------------------------------
with tab_route:
    import json
    from pathlib import Path
    from route_economics import (
        RouteScenario, scenario_from_dict, compare_routes, sensitivity_matrix,
        scrubber_analysis, ets_coverage_fraction, assumption_rows,
        scenario_with_overrides,
    )

    SCENARIO_PATH = Path("sample_data/route_scenarios/may_2026_vlcc_pg_singapore.json")

    @st.cache_data(ttl=3600, show_spinner=False)
    def _load_default_scenario() -> dict:
        if not SCENARIO_PATH.exists():
            return {}
        return json.loads(SCENARIO_PATH.read_text())

    raw = _load_default_scenario()
    base = scenario_from_dict(raw) if raw else RouteScenario()

    st.markdown("## 🛳️ VLCC Route Lab — Cape vs Suez")
    st.caption(
        "Editable voyage-economics calculator for a Persian Gulf → Singapore VLCC. "
        "Defaults are an analyst scenario, **not** live market data. "
        "This is **not routing, insurance, legal, or investment advice**."
    )
    if base.label:
        st.info(f"Scenario: **{base.name}** · {base.label} · last reviewed {base.last_reviewed}")

    sub_scenario, sub_cost, sub_sens, sub_reg, sub_src = st.tabs(
        ["⚙️ Scenario", "💰 Cost Breakdown", "🎯 Sensitivity",
         "🌍 Regulation", "📚 Assumptions & Sources"]
    )

    # --- Scenario inputs ---------------------------------------------------
    with sub_scenario:
        sec1, sec2, sec3 = st.columns(3)
        with sec1:
            st.markdown("**Vessel**")
            hull = st.number_input("Hull value (USD)", 0.0, 1e9,
                                   float(base.vessel.hull_value_usd), step=1_000_000.0,
                                   format="%.0f", key="route_hull_value")
            cargo_t = st.number_input("Cargo (tonnes)", 0.0, 1e6,
                                      float(base.vessel.cargo_tonnes), step=10_000.0,
                                      format="%.0f", key="route_cargo_tonnes")
            cargo_v = st.number_input("Cargo value per tonne (USD)", 0.0, 5_000.0,
                                      float(base.vessel.cargo_value_per_tonne_usd),
                                      step=10.0, format="%.2f", key="route_cargo_value_per_tonne")
            burn = st.number_input("Fuel consumption (mt/day)", 0.0, 200.0,
                                   float(base.vessel.fuel_consumption_mt_day),
                                   step=1.0, format="%.1f", key="route_fuel_burn")
            scrubber = st.checkbox(
                "Scrubber-equipped", value=base.vessel.scrubber_equipped, key="route_scrubber",
            )
        with sec2:
            st.markdown("**Fuel & Charter**")
            grade = st.selectbox("Fuel grade", ["IFO380", "HSFO", "VLSFO", "LSMGO"],
                                 index=["IFO380", "HSFO", "VLSFO", "LSMGO"].index(base.fuel.grade)
                                       if base.fuel.grade in ["IFO380", "HSFO", "VLSFO", "LSMGO"] else 0,
                                 key="route_fuel_grade")
            fuel_price = st.number_input("Fuel price (USD/mt)", 0.0, 3000.0,
                                         float(base.fuel.price_per_mt_usd),
                                         step=5.0, format="%.2f", key="route_fuel_price")
            vlsfo_ref = st.number_input("VLSFO reference (USD/mt)", 0.0, 3000.0,
                                        float(base.fuel.vlsfo_price_per_mt_usd),
                                        step=5.0, format="%.2f", key="route_vlsfo_ref")
            co2_factor = st.number_input("CO2 factor (t CO2 / t fuel)", 1.0, 4.0,
                                         float(base.fuel.co2_factor),
                                         step=0.001, format="%.3f", key="route_co2_factor")
            charter = st.number_input("Charter rate (USD/day)", 0.0, 1_000_000.0,
                                      float(base.charter.rate_per_day_usd),
                                      step=1_000.0, format="%.0f", key="route_charter_rate")
            financing = st.number_input("Cargo financing rate (annual)", 0.0, 0.5,
                                        float(base.charter.financing_rate_annual),
                                        step=0.005, format="%.3f", key="route_financing_rate")
        with sec3:
            st.markdown("**Route**")
            suez_d = st.number_input("Suez voyage days", 0.0, 90.0,
                                     float(base.route.suez_days), step=0.1, format="%.2f",
                                     key="route_suez_days")
            cape_d = st.number_input("Cape voyage days", 0.0, 120.0,
                                     float(base.route.cape_days), step=0.1, format="%.2f",
                                     key="route_cape_days")
            suez_toll = st.number_input("Suez toll (USD)", 0.0, 5_000_000.0,
                                        float(base.route.suez_toll_usd),
                                        step=5_000.0, format="%.0f", key="route_suez_toll")
            cape_fees = st.number_input("Cape port/bunker fees (USD)", 0.0, 1_000_000.0,
                                        float(base.route.cape_port_fees_usd),
                                        step=1_000.0, format="%.0f", key="route_cape_fees")
            cape_delay = st.number_input("Cape congestion delay (days)", 0.0, 60.0,
                                         float(base.route.cape_congestion_delay_days),
                                         step=0.5, format="%.1f", key="route_cape_delay")

        sec4, sec5 = st.columns(2)
        with sec4:
            st.markdown("**Insurance / War-Risk**")
            hm_suez = st.number_input("H&M AWRP — Suez (% of hull)", 0.0, 0.10,
                                      float(base.insurance.hm_awrp_pct_suez),
                                      step=0.0005, format="%.4f", key="route_hm_suez")
            hm_cape = st.number_input("H&M AWRP — Cape (% of hull)", 0.0, 0.10,
                                      float(base.insurance.hm_awrp_pct_cape),
                                      step=0.0005, format="%.4f", key="route_hm_cape")
            cargo_suez = st.number_input("Cargo war-risk — Suez (% of cargo)", 0.0, 0.10,
                                         float(base.insurance.cargo_awrp_pct_suez),
                                         step=0.0005, format="%.4f", key="route_cargo_suez")
            cargo_cape = st.number_input("Cargo war-risk — Cape (% of cargo)", 0.0, 0.10,
                                         float(base.insurance.cargo_awrp_pct_cape),
                                         step=0.0005, format="%.4f", key="route_cargo_cape")
        with sec5:
            st.markdown("**Regulation (EU ETS scope)**")
            origin_eea = st.checkbox("Origin port in EEA",
                                     value=base.regulation.origin_in_eea, key="route_origin_eea")
            dest_eea = st.checkbox("Destination port in EEA",
                                   value=base.regulation.dest_in_eea, key="route_dest_eea")
            mid_eea = st.checkbox("Intermediate EEA port call",
                                  value=base.regulation.has_intermediate_eea_port_call,
                                  key="route_mid_eea")
            eua_price = st.number_input("EUA price (USD/t CO2)", 0.0, 500.0,
                                        float(base.regulation.eua_price_usd),
                                        step=1.0, format="%.2f", key="route_eua_price")

        # Build the editable scenario from inputs.
        from route_economics import (
            VesselProfile, FuelAssumptions, CharterAssumptions,
            InsuranceAssumptions, RouteAssumptions, RegulationAssumptions,
        )
        scen = RouteScenario(
            name=base.name, label=base.label, last_reviewed=base.last_reviewed,
            vessel=VesselProfile(hull_value_usd=hull, cargo_tonnes=cargo_t,
                                 cargo_value_per_tonne_usd=cargo_v,
                                 fuel_consumption_mt_day=burn,
                                 scrubber_equipped=scrubber),
            fuel=FuelAssumptions(grade=grade, price_per_mt_usd=fuel_price,
                                 vlsfo_price_per_mt_usd=vlsfo_ref,
                                 co2_factor=co2_factor),
            charter=CharterAssumptions(rate_per_day_usd=charter,
                                       financing_rate_annual=financing),
            insurance=InsuranceAssumptions(hm_awrp_pct_suez=hm_suez,
                                           hm_awrp_pct_cape=hm_cape,
                                           cargo_awrp_pct_suez=cargo_suez,
                                           cargo_awrp_pct_cape=cargo_cape),
            route=RouteAssumptions(suez_days=suez_d, cape_days=cape_d,
                                   suez_toll_usd=suez_toll,
                                   cape_port_fees_usd=cape_fees,
                                   cape_congestion_delay_days=cape_delay),
            regulation=RegulationAssumptions(origin_in_eea=origin_eea,
                                             dest_in_eea=dest_eea,
                                             has_intermediate_eea_port_call=mid_eea,
                                             eua_price_usd=eua_price),
            notes=list(base.notes),
        )
        st.session_state["_route_scenario"] = scen

    # Reuse the scenario built above for every sub-tab.
    scen: RouteScenario = st.session_state.get("_route_scenario", base)

    # --- Cost Breakdown ----------------------------------------------------
    with sub_cost:
        cmp = compare_routes(scen)

        st.markdown("**All-in totals** (current assumptions, including insurance)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Suez total", f"${cmp.suez.total_cost:,.0f}",
                  help="All cost components for the Suez routing.")
        m2.metric("Cape total", f"${cmp.cape.total_cost:,.0f}",
                  help="All cost components for the Cape of Good Hope routing.")
        m3.metric("All-in Cape − Suez", f"${cmp.differential_cape_minus_suez:,.0f}",
                  delta_color=("inverse" if cmp.differential_cape_minus_suez > 0 else "normal"),
                  help="Positive ⇒ Cape costs more. Negative ⇒ Cape costs less. "
                       "Includes whatever H&M and cargo war-risk you entered.")

        st.markdown(
            "**Pre-insurance comparison** "
            "(excludes H&M war-risk and cargo war-risk on both sides)"
        )
        p1, p2, p3 = st.columns(3)
        p1.metric("Suez ex-insurance",
                  f"${cmp.suez.total_cost_ex_insurance:,.0f}")
        p2.metric("Cape ex-insurance",
                  f"${cmp.cape.total_cost_ex_insurance:,.0f}")
        p3.metric("Pre-insurance Cape − Suez",
                  f"${cmp.pre_insurance_differential_cape_minus_suez:,.0f}",
                  delta_color=("inverse" if cmp.pre_insurance_differential_cape_minus_suez > 0 else "normal"),
                  help="How much extra Suez risk-cost can be tolerated before Cape wins on price.")

        st.markdown("**Break-even thresholds**")
        b1, b2 = st.columns(2)
        if cmp.breakeven_awrp_for_cape_pct is not None:
            b1.metric("Break-even Suez H&M AWRP",
                      f"{cmp.breakeven_awrp_for_cape_pct*100:.3f}% of hull",
                      help="H&M AWRP on Suez (given all other assumptions, "
                           "including current cargo war-risk on both routes) at "
                           "which the all-in totals tie.")
        else:
            b1.metric("Break-even Suez H&M AWRP", "—")
        if cmp.breakeven_combined_suez_insurance_usd is not None:
            v = cmp.breakeven_combined_suez_insurance_usd
            b2.metric("Break-even combined Suez insurance/risk",
                      f"${v:,.0f}",
                      delta_color=("normal" if v > 0 else "inverse"),
                      help="Total Suez-side war-risk/insurance USD that would tie "
                           "Cape (given Cape's current insurance assumption). "
                           "Closer to the framing used in some analyst briefs. "
                           "Negative ⇒ Cape is already cheaper before insurance.")
        else:
            b2.metric("Break-even combined Suez insurance/risk", "—")

        st.markdown(
            f"**Model-implied lower-cost route (all-in):** "
            f"`{cmp.cheaper_route}` · differential `${cmp.differential_cape_minus_suez:,.0f}`. "
            f"**Pre-insurance:** `{cmp.cheaper_route_ex_insurance}` · "
            f"`${cmp.pre_insurance_differential_cape_minus_suez:,.0f}`."
        )
        st.caption(
            "⚠️ Different reports may quote different break-even numbers depending "
            "on whether insurance is netted into the subtotal. Compare like with like."
        )

        rows = [cmp.suez.as_row(), cmp.cape.as_row()]
        bdf = pd.DataFrame(rows).set_index("route").T
        st.dataframe(
            bdf.style.format("{:,.0f}").apply(
                lambda s: ["background-color: #1b5e20; color: white"
                           if s.name == "total" else "" for _ in s], axis=1
            ),
            width="stretch",
        )

        # Stacked bar comparison
        components = [c for c in cmp.suez.components.keys()]
        comp_fig = go.Figure()
        for c in components:
            comp_fig.add_trace(go.Bar(
                name=c, x=["Suez", "Cape"],
                y=[cmp.suez.components[c], cmp.cape.components[c]],
            ))
        comp_fig.update_layout(barmode="stack", height=320,
                               margin=dict(l=10, r=10, t=10, b=10),
                               yaxis_title="Cost (USD)",
                               legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(comp_fig, width="stretch")

        for w in cmp.warnings:
            st.warning(w)

        with st.expander("Scrubber analysis (optional)"):
            sa = scrubber_analysis(scen)
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Daily saving", f"${sa.daily_saving_usd:,.0f}")
            sc2.metric("Suez voyage saving", f"${sa.suez_voyage_saving_usd:,.0f}")
            sc3.metric("Cape voyage saving", f"${sa.cape_voyage_saving_usd:,.0f}")
            st.caption(sa.note)
            st.caption(f"Scrubber-applied: **{scen.vessel.scrubber_equipped}**. "
                       f"Toggle on the Scenario sub-tab to model HSFO vs VLSFO economics.")

    # --- Sensitivity -------------------------------------------------------
    with sub_sens:
        st.caption("Cape − Suez differential and break-even Suez AWRP across "
                   "charter rate and fuel price grids. Lower differential ⇒ Cape more attractive.")
        cr_default = "60000, 90000, 100000, 120000"
        fp_default = "535, 694, 900"
        cca, ccb = st.columns(2)
        cr_in = cca.text_input(
            "Charter rates (USD/day, comma-separated)", cr_default, key="route_sens_charter_rates",
        )
        fp_in = ccb.text_input(
            "Fuel prices (USD/mt, comma-separated)", fp_default, key="route_sens_fuel_prices",
        )
        try:
            charter_rates = [float(x.strip()) for x in cr_in.split(",") if x.strip()]
            fuel_prices = [float(x.strip()) for x in fp_in.split(",") if x.strip()]
        except ValueError:
            st.error("Could not parse rate/price grids — falling back to defaults.")
            charter_rates = [60_000, 90_000, 100_000, 120_000]
            fuel_prices = [535.0, 694.0, 900.0]

        sens = sensitivity_matrix(scen, charter_rates=charter_rates, fuel_prices=fuel_prices)
        diff_df = pd.DataFrame(sens.differential_matrix,
                               index=[f"${cr:,.0f}/d" for cr in sens.charter_rates],
                               columns=[f"${fp:,.0f}/mt" for fp in sens.fuel_prices])
        st.markdown("**Cape − Suez total cost differential (USD)**")
        st.dataframe(
            diff_df.style.format("{:,.0f}").background_gradient(
                cmap="RdYlGn_r", axis=None
            ),
            width="stretch",
        )

        awrp_df = pd.DataFrame(
            [[(v if v is not None else float("nan")) * 100 for v in row] for row in sens.breakeven_awrp_matrix],
            index=diff_df.index, columns=diff_df.columns,
        )
        st.markdown("**Break-even Suez H&M AWRP (% of hull)**")
        st.dataframe(
            awrp_df.style.format("{:.3f}%", na_rep="—").background_gradient(
                cmap="RdYlGn", axis=None
            ),
            width="stretch",
        )

        # Two line charts
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("**Break-even AWRP vs charter rate** (at current fuel price)")
            xs = sens.charter_rates
            ys = []
            for cr in xs:
                s = scenario_with_overrides(scen, charter_rate=cr)
                ys.append((compare_routes(s).breakeven_awrp_for_cape_pct or 0) * 100)
            fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers",
                                       line=dict(color="#0277bd")))
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="Charter rate (USD/day)",
                              yaxis_title="Break-even AWRP (%)")
            st.plotly_chart(fig, width="stretch")
        with sc2:
            st.markdown("**Break-even AWRP vs fuel price** (at current charter rate)")
            xs = sens.fuel_prices
            ys = []
            for fp in xs:
                s = scenario_with_overrides(scen, fuel_price=fp)
                ys.append((compare_routes(s).breakeven_awrp_for_cape_pct or 0) * 100)
            fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers",
                                       line=dict(color="#ef6c00")))
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="Fuel price (USD/mt)",
                              yaxis_title="Break-even AWRP (%)")
            st.plotly_chart(fig, width="stretch")

    # --- Regulation --------------------------------------------------------
    with sub_reg:
        coverage = ets_coverage_fraction(scen.regulation)
        suez_r = compare_routes(scen).suez
        cape_r = compare_routes(scen).cape
        r1, r2, r3 = st.columns(3)
        r1.metric("ETS coverage", f"{coverage*100:.0f}%")
        r2.metric("Suez physical CO2 (t)", f"{suez_r.physical_emissions_t:,.0f}")
        r3.metric("Cape physical CO2 (t)", f"{cape_r.physical_emissions_t:,.0f}")

        st.markdown(
            "**Why a direct PG → Singapore voyage has zero EU ETS payable carbon cost:** "
            "both endpoints are non-EEA, and there is no intermediate EEA port call. "
            "Per EU maritime ETS scope rules, the regulated emissions fraction is **0%**, "
            "so the EUA price input does not affect payable carbon cost. "
            "Physical emissions are still computed for transparency."
        )

        st.markdown("**Emissions decomposition**")
        ems = pd.DataFrame([
            {"route": "Suez",
             "physical_emissions_t": round(suez_r.physical_emissions_t),
             "regulated_emissions_t": round(suez_r.regulated_emissions_t),
             "payable_carbon_usd": round(suez_r.payable_carbon_cost)},
            {"route": "Cape",
             "physical_emissions_t": round(cape_r.physical_emissions_t),
             "regulated_emissions_t": round(cape_r.regulated_emissions_t),
             "payable_carbon_usd": round(cape_r.payable_carbon_cost)},
        ])
        st.dataframe(ems, hide_index=True, width="stretch")

        if coverage > 0:
            st.warning("ETS coverage is non-zero for this voyage configuration. "
                       "Verify port-call assumptions and confirm the EUA price input "
                       "reflects the relevant EU ETS auction reference.")

        st.caption(
            "Sources: European Commission — 'FAQ — Maritime transport in the EU ETS'; "
            "EMSA Maritime ETS resources; Directive (EU) 2023/959. "
            "From 1 Jan 2026, 100% of regulated emissions are surrendered (no phase-in)."
        )

    # --- Assumptions & Sources --------------------------------------------
    with sub_src:
        rows = assumption_rows(scen)
        sdf = pd.DataFrame(rows)
        if "value" in sdf.columns:
            sdf["value"] = sdf["value"].apply(lambda v: "" if v is None else str(v))
        # Color-code the kind column so user-input vs analyst-default is obvious
        kind_color = {
            "user_input": "#0277bd",
            "analyst_default": "#ef6c00",
            "regulatory_constant": "#1b5e20",
            "vessel_default": "#455a64",
        }
        def _kind_style(v):
            return f"background-color: {kind_color.get(v, '#888')}; color: white"
        st.dataframe(
            sdf.style.map(_kind_style, subset=["kind"]),
            width="stretch", hide_index=True,
        )
        st.caption(
            f"Scenario last reviewed: **{scen.last_reviewed}**. "
            "User inputs (blue) are user-editable in the Scenario tab. "
            "Analyst defaults (orange) come from the editable scenario file and "
            "should be verified before use. Regulatory constants (green) reference "
            "official sources. Vessel defaults (grey) are engineering placeholders."
        )
        st.warning(
            "**This model is an analytical calculator.** It is not routing advice, "
            "legal advice, insurance advice, or investment advice. Bunker prices, "
            "tolls, war-risk premiums, port congestion, and EUA prices are not yet "
            "wired to live data sources — see the Data Health tab for placeholder status."
        )


# ---- Data Health -----------------------------------------------------------
with tab_health:
    st.subheader("Data Health")

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("App mode", mode)
    h2.metric("NewsAPI key", "yes" if data["newsapi_key_present"] else "no")
    h3.metric("Failed tickers", len(failures), delta_color="inverse")
    h4.metric("Last refresh (UTC)", refreshed_at[-8:] if refreshed_at else "—")

    if data.get("fallback_count", 0) > 0:
        st.warning(f"{data['fallback_count']} provider call(s) used the sample fallback this refresh.")
    if failures:
        st.error(f"Failed tickers: {', '.join(failures)}")
    elif mode == "DEMO":
        st.info("Running in demo mode with bundled sample data.")
    else:
        st.success("All tickers loaded successfully.")

    st.markdown("**Provider statuses**")
    statuses = data.get("statuses", [])
    if statuses:
        sdf = pd.DataFrame([
            {"provider": s.provider, "ok": s.ok, "records": s.records,
             "error": s.error or "", "timestamp": s.timestamp}
            for s in statuses
        ])
        st.dataframe(sdf, hide_index=True, width="stretch")
    else:
        st.info("No provider calls made yet.")

    st.markdown("**API call counts (this refresh)**")
    calls = data.get("calls", {})
    if calls:
        st.dataframe(pd.DataFrame([{"endpoint": k, "calls": v} for k, v in calls.items()]),
                     hide_index=True, width="stretch")
    else:
        st.info("No live calls counted (cache hit or demo mode).")

    st.markdown("**Cache TTLs (seconds)**")
    st.write({
        "watchlist": cfg.WATCHLIST_CACHE_TTL,
        "price_history": cfg.PRICE_CACHE_TTL,
        "BDRY": cfg.BDI_CACHE_TTL,
    })

    st.markdown("**Paid maritime providers**")
    paid = data.get("paid_providers", [])
    st.dataframe(pd.DataFrame(paid), hide_index=True, width="stretch")
    st.caption(
        "TCE rates, FVG, vessel valuations, AIS positions and the actual Baltic Dry Index "
        "require paid feeds. The dashboard reports these honestly and never fabricates values."
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    "<div class='footer'>"
    "Open-source research dashboard · MIT license · "
    "yfinance + NewsAPI + BDRY (BDI proxy) · "
    "Free-tier data may be delayed or incomplete · "
    "<b>Not investment advice.</b>"
    "</div>",
    unsafe_allow_html=True,
)
