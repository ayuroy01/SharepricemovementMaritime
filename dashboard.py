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
import theme
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
    initial_sidebar_state="collapsed",
)

# --- Dark night-sea palette + dashboard styling ----------------------------
# Visual tokens mirror those in theme.py. Keep them in sync.
# IMPORTANT: every line in this CSS string MUST start at column 0. If lines
# are indented, Streamlit's CommonMark parser treats them as a code block and
# the CSS leaks as literal text on the page. The font is loaded via @import
# inside <style> so we don't rely on <link> tags being preserved.
_CSS = """\
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --bg-deep:      #02060E;
  --bg-night:     #050B18;
  --bg-surface:   rgba(14, 27, 46, 0.45);
  --bg-elevated:  rgba(20, 40, 64, 0.62);
  --hairline:     rgba(255, 255, 255, 0.09);
  --hairline-strong: rgba(255, 255, 255, 0.16);
  --inset-hi:     rgba(255, 255, 255, 0.08);
  --text-primary: #E6EDF7;
  --text-muted:   #A8B6CC;
  --text-faint:   #6B7E99;
  --accent:       #6FB1FF;
  --accent-soft:  rgba(111, 177, 255, 0.18);
  --accent-warm:  #C8A24A;
  --status-ok:    #4FB286;
  --status-warn:  #E0A458;
  --status-bad:   #E26A6A;
}

/* ---------- Base typography & app shell ---------- */
html, body, [class*="css"] {
  font-family: "Inter", system-ui, -apple-system, sans-serif;
  background: var(--bg-deep) !important;
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* The app is a transparent layer floating on the night-sky background. */
.stApp { background: transparent !important; }
.stApp > header { background: transparent !important; backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); }
[data-testid="stHeader"] { background: transparent !important; }

.block-container {
  padding-top: 4rem !important;
  padding-bottom: 6rem !important;
  padding-left: 2.5rem !important;
  padding-right: 2.5rem !important;
  max-width: 1440px !important;
}

/* Section breathing room — Streamlit elements get more vertical air */
.element-container, .stMarkdown, .stPlotlyChart, .stDataFrame { margin-bottom: 1rem; }

h1, h2, h3, h4 { font-family: inherit; color: var(--text-primary); letter-spacing: -0.015em; }
h1 { font-weight: 700; letter-spacing: -0.025em; }
h2 { font-weight: 600; font-size: 1.6rem; margin-top: 1.6rem; margin-bottom: 0.8rem; }
h3 { font-weight: 600; font-size: 1.25rem; margin-top: 1.2rem; margin-bottom: 0.6rem; }
p, li, span, label, div { color: var(--text-primary); }
.stCaption, [data-testid="stCaptionContainer"] {
  color: var(--text-muted) !important; font-size: 13px; line-height: 1.65;
}

/* ---------- Glass cards (Apple-style) ---------- */
[data-testid="stMetric"] {
  position: relative;
  background: var(--bg-surface) !important;
  backdrop-filter: blur(22px) saturate(160%);
  -webkit-backdrop-filter: blur(22px) saturate(160%);
  border: 1px solid var(--hairline);
  border-radius: 18px;
  padding: 26px 24px;
  box-shadow: inset 0 1px 0 var(--inset-hi), 0 8px 32px 0 rgba(0, 0, 0, 0.32);
  transition: transform 0.35s cubic-bezier(.2,.8,.2,1),
              box-shadow 0.35s ease,
              border-color 0.35s ease;
  overflow: hidden;
}
[data-testid="stMetric"]::before {
  content: "";
  position: absolute; inset: 0;
  background: radial-gradient(140% 80% at 50% -20%, rgba(111,177,255,0.10), transparent 60%);
  pointer-events: none;
}
[data-testid="stMetric"]:hover {
  transform: translateY(-4px);
  box-shadow:
    inset 0 1px 0 var(--inset-hi),
    0 14px 44px 0 rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(111,177,255,0.18);
  border-color: rgba(111,177,255,0.32);
}
[data-testid="stMetricValue"] {
  font-size: 32px; font-weight: 600;
  font-feature-settings: "tnum"; font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  margin-top: 10px;
}
[data-testid="stMetricLabel"] {
  color: var(--text-muted); font-size: 12px;
  text-transform: uppercase; letter-spacing: 0.12em;
  font-weight: 500;
}
[data-testid="stMetricDelta"] {
  font-feature-settings: "tnum"; font-variant-numeric: tabular-nums;
  font-size: 14px;
}

/* ---------- Tables ---------- */
[data-testid="stDataFrame"] {
  background: var(--bg-surface);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  overflow: hidden;
  box-shadow:
    inset 0 1px 0 var(--inset-hi),
    0 8px 32px 0 rgba(0, 0, 0, 0.28);
}
[data-testid="stDataFrame"] * {
  font-feature-settings: "tnum"; font-variant-numeric: tabular-nums;
  font-size: 14px;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
  border-bottom: 1px solid var(--hairline);
  gap: 8px;
  background: rgba(10, 18, 32, 0.35);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 6px 6px 0 6px;
  border-radius: 14px 14px 0 0;
  border: 1px solid var(--hairline);
  border-bottom: none;
}
.stTabs [data-baseweb="tab"] {
  background: transparent;
  border: 0;
  border-radius: 10px 10px 0 0;
  padding: 12px 20px;
  color: var(--text-muted);
  font-size: 15px; font-weight: 500;
  transition: color 0.3s ease, background 0.3s ease;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.03);
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: var(--text-primary);
  border-bottom: 2px solid var(--accent);
  background: rgba(111,177,255,0.06);
}

/* ---------- Expander ---------- */
[data-testid="stExpander"] {
  background: var(--bg-surface);
  backdrop-filter: blur(16px) saturate(140%);
  -webkit-backdrop-filter: blur(16px) saturate(140%);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  box-shadow: inset 0 1px 0 var(--inset-hi);
}

/* ---------- Sidebar (frosted glass column) ---------- */
[data-testid="stSidebar"] {
  background: rgba(8, 16, 30, 0.55) !important;
  backdrop-filter: blur(28px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
  border-right: 1px solid var(--hairline);
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  font-size: 13px; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--text-muted);
  margin-bottom: 1rem;
}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--hairline);
  border-radius: 10px;
  padding: 9px 22px;
  font-weight: 500; font-size: 14px;
  transition: all 0.25s cubic-bezier(.2,.8,.2,1);
  box-shadow: inset 0 1px 0 var(--inset-hi);
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(111,177,255,0.12);
  transform: translateY(-2px);
  box-shadow:
    inset 0 1px 0 var(--inset-hi),
    0 6px 18px rgba(111,177,255,0.18);
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent), #8AC1FF);
  color: var(--bg-deep);
  border: none;
  font-weight: 600;
  box-shadow: 0 6px 16px rgba(111,177,255,0.32);
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #8AC1FF, #AEDBFF);
  box-shadow: 0 8px 20px rgba(111,177,255,0.5);
}

/* ---------- Inputs ---------- */
.stTextInput > div > div > input,
.stNumberInput input,
.stSelectbox > div > div,
.stMultiSelect > div > div {
  background: rgba(0, 0, 0, 0.25);
  border-color: var(--hairline);
  color: var(--text-primary);
  border-radius: 10px;
  padding: 10px 14px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.stTextInput > div > div > input:focus,
.stNumberInput input:focus,
.stSelectbox > div > div:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(111,177,255,0.22);
}

/* ============================================================
   Full-page Night Sky Background (fixed, behind every element)
   ============================================================ */
.om-bg {
  position: fixed;
  inset: 0;
  z-index: -10;
  pointer-events: none;
  overflow: hidden;
  background:
    radial-gradient(ellipse 90% 60% at 50% 110%, rgba(13, 31, 60, 0.65), transparent 70%),
    radial-gradient(ellipse 60% 40% at 82% 18%, rgba(111,177,255,0.06), transparent 60%),
    linear-gradient(180deg, #010204 0%, #03070F 38%, #050C1A 65%, #061224 85%, #04101F 100%);
}

/* Soft aurora glow overlay across the top */
.om-bg::before {
  content: "";
  position: absolute;
  top: -10%; left: -10%; right: -10%; height: 70%;
  background:
    radial-gradient(ellipse 50% 40% at 30% 20%, rgba(98, 70, 200, 0.07), transparent 65%),
    radial-gradient(ellipse 45% 35% at 75% 40%, rgba(111, 177, 255, 0.05), transparent 65%);
  filter: blur(40px);
  opacity: 0.85;
  animation: om-aurora 24s ease-in-out infinite alternate;
}
@keyframes om-aurora {
  0%   { transform: translate3d(0, 0, 0) scale(1); opacity: 0.7; }
  50%  { transform: translate3d(20px, -10px, 0) scale(1.05); opacity: 0.95; }
  100% { transform: translate3d(-10px, 14px, 0) scale(1.02); opacity: 0.75; }
}

/* Subtle vignette to anchor the corners */
.om-bg::after {
  content: "";
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 110% 80% at 50% 50%, transparent 55%, rgba(0,0,0,0.55) 100%);
  pointer-events: none;
}

.om-stars-layer { position: absolute; inset: 0; }

/* Each star is an absolutely positioned dot. Its size, position, opacity,
   animation duration & delay come from inline style props built in Python. */
.om-star {
  position: absolute;
  border-radius: 50%;
  background: #FFFFFF;
  box-shadow: 0 0 4px rgba(255,255,255,0.45);
  animation-name: om-twinkle;
  animation-iteration-count: infinite;
  animation-timing-function: ease-in-out;
  will-change: opacity, transform;
}
@keyframes om-twinkle {
  0%, 100% { opacity: 0.18; transform: scale(0.85); }
  50%      { opacity: 1;    transform: scale(1.25); }
}

/* Shooting star streaks — rare, dramatic */
.om-shooting {
  position: absolute;
  width: 140px; height: 1.2px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.85) 75%, rgba(255,255,255,0));
  border-radius: 999px;
  filter: drop-shadow(0 0 6px rgba(180, 210, 255, 0.7));
  opacity: 0;
  transform-origin: left center;
}
.om-shooting.s1 { top: 12%; left: -10%; transform: rotate(15deg); animation: om-shoot 9s ease-in 2s infinite; }
.om-shooting.s2 { top: 28%; left: -10%; transform: rotate(22deg); animation: om-shoot 13s ease-in 6s infinite; }
.om-shooting.s3 { top: 8%;  left: -10%; transform: rotate(8deg);  animation: om-shoot 17s ease-in 11s infinite; }
@keyframes om-shoot {
  0%   { opacity: 0; transform: translate(0, 0) rotate(15deg); }
  4%   { opacity: 1; }
  18%  { opacity: 0.9; }
  30%  { opacity: 0; transform: translate(110vw, 30vh) rotate(15deg); }
  100% { opacity: 0; transform: translate(110vw, 30vh) rotate(15deg); }
}

/* Moon — soft lit disc with halo */
.om-moon {
  position: absolute;
  right: 9%; top: 8%;
  width: 78px; height: 78px;
  border-radius: 50%;
  background: radial-gradient(circle at 34% 32%,
    #FFFFFF 0%, #ECEFF6 35%, #B6BCC8 70%, rgba(160,166,180,0.0) 78%);
  box-shadow:
    0 0 60px rgba(255,255,255,0.18),
    0 0 120px rgba(150,180,230,0.10),
    inset -8px -10px 22px rgba(60,70,90,0.45);
  filter: blur(0.4px);
  opacity: 0.9;
  animation: om-moon-glow 8s ease-in-out infinite alternate;
}
@keyframes om-moon-glow {
  0%   { box-shadow: 0 0 60px rgba(255,255,255,0.16), 0 0 120px rgba(150,180,230,0.08), inset -8px -10px 22px rgba(60,70,90,0.45); }
  100% { box-shadow: 0 0 90px rgba(255,255,255,0.22), 0 0 160px rgba(150,180,230,0.14), inset -8px -10px 22px rgba(60,70,90,0.45); }
}

/* Distant cloud band */
.om-cloud {
  position: absolute;
  bottom: 36%;
  width: 60%;
  height: 50px;
  background: radial-gradient(ellipse 50% 100% at 50% 50%, rgba(80, 100, 140, 0.18), transparent 70%);
  filter: blur(18px);
  opacity: 0.7;
  animation: om-cloud-drift 80s linear infinite;
}
.om-cloud.c1 { left: -30%; bottom: 38%; }
.om-cloud.c2 { left: -50%; bottom: 33%; height: 40px; opacity: 0.5; animation-duration: 110s; animation-delay: -25s; }
@keyframes om-cloud-drift {
  0%   { transform: translateX(0); }
  100% { transform: translateX(180vw); }
}

/* Horizon glow */
.om-horizon {
  position: absolute; left: 0; right: 0; bottom: 28%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(111,177,255,0.5), transparent);
  box-shadow: 0 0 30px rgba(111,177,255,0.35);
  opacity: 0.7;
}

/* Ocean / water layer */
.om-ocean {
  position: absolute;
  left: 0; right: 0; bottom: 0;
  height: 30%;
  background:
    repeating-linear-gradient(0deg, rgba(111,177,255,0.045) 0 1px, transparent 1px 9px),
    linear-gradient(180deg, rgba(7,16,31,0.4) 0%, rgba(2,4,8,0.95) 100%);
  overflow: hidden;
}
/* Moonlight reflection on water — animated */
.om-moonpath {
  position: absolute;
  right: 8%; bottom: 0; width: 90px; height: 30%;
  background: linear-gradient(180deg,
    rgba(255,255,255,0.16) 0%,
    rgba(255,255,255,0.10) 30%,
    rgba(255,255,255,0.04) 70%,
    transparent 100%);
  filter: blur(6px);
  mix-blend-mode: screen;
  animation: om-moonpath-shimmer 6s ease-in-out infinite;
  opacity: 0.7;
}
@keyframes om-moonpath-shimmer {
  0%, 100% { opacity: 0.55; transform: scaleX(1); }
  50%      { opacity: 0.85; transform: scaleX(1.05); }
}
.om-wave-shimmer {
  position: absolute;
  left: -30%; right: -30%; bottom: 6%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
  filter: blur(1.2px);
  opacity: 0.4;
  animation: om-shimmer-pulse 7s ease-in-out infinite;
}
.om-wave-shimmer.w2 { bottom: 14%; opacity: 0.25; animation-duration: 9s; animation-delay: -2s; }
.om-wave-shimmer.w3 { bottom: 20%; opacity: 0.18; animation-duration: 11s; animation-delay: -4.5s; }
@keyframes om-shimmer-pulse {
  0%, 100% { transform: translateX(-10%); opacity: 0.3; }
  50%      { transform: translateX(10%);  opacity: 0.7; }
}

/* ---------- Ships ---------- */
.om-ship-track {
  position: absolute;
  left: 0; right: 0;
  pointer-events: none;
}
.om-ship-track.t1 { bottom: 10%; }   /* foreground big tanker — right side, slow drift */
.om-ship-track.t2 { bottom: 20%; }   /* mid distance, moves left → right */
.om-ship-track.t3 { bottom: 25%; }   /* far horizon, moves right → left */

.om-ship-wrap {
  position: absolute;
  display: inline-block;
}
.om-ship-wrap.foreground {
  right: 8%; bottom: 0;
  width: min(38vw, 460px);
  min-width: 280px;
  animation: om-ship-bob 9s ease-in-out infinite;
}
.om-ship-wrap.midground {
  bottom: 0;
  width: 200px;
  animation:
    om-ship-sail-right 75s linear infinite,
    om-ship-bob 7s ease-in-out infinite;
}
.om-ship-wrap.farground {
  bottom: 0;
  width: 110px;
  opacity: 0.55;
  filter: blur(0.4px);
  animation:
    om-ship-sail-left 120s linear infinite,
    om-ship-bob 11s ease-in-out infinite;
}
@keyframes om-ship-bob {
  0%, 100% { transform: translateY(0) rotate(-0.4deg); }
  50%      { transform: translateY(-5px) rotate(0.4deg); }
}
@keyframes om-ship-sail-right {
  0%   { left: -20%; }
  100% { left: 120%; }
}
@keyframes om-ship-sail-left {
  0%   { left: 110%; }
  100% { left: -20%; }
}

.om-ship-svg { display: block; width: 100%; height: auto; }

/* Reflection underneath the ship */
.om-ship-reflection {
  position: absolute;
  left: 2%; right: 2%;
  bottom: -42%;
  height: 70%;
  transform: scaleY(-0.55);
  transform-origin: top center;
  opacity: 0.22;
  filter: blur(2.2px);
  mask-image: linear-gradient(180deg, rgba(0,0,0,0.95), transparent 80%);
  -webkit-mask-image: linear-gradient(180deg, rgba(0,0,0,0.95), transparent 80%);
}
/* Wake — soft light trail behind hull */
.om-wake {
  position: absolute;
  left: -18%;
  right: 18%;
  bottom: -2px;
  height: 26px;
  opacity: 0.55;
  background:
    linear-gradient(100deg, transparent, rgba(111,177,255,0.32), transparent 58%),
    linear-gradient(96deg, transparent 8%, rgba(255,255,255,0.18), transparent 44%);
  transform: skewX(-22deg);
  filter: blur(1px);
  animation: om-wake-pulse 9s ease-in-out infinite;
}
@keyframes om-wake-pulse {
  0%, 100% { opacity: 0.4; filter: blur(0.6px); }
  50%      { opacity: 0.7; filter: blur(1.6px); }
}

/* Running-light pulse on ship navigation lights */
.om-runlight {
  animation: om-runlight-pulse 2.4s ease-in-out infinite;
  transform-origin: center;
}
.om-runlight.r2 { animation-duration: 3.1s; animation-delay: -0.8s; }
.om-runlight.r3 { animation-duration: 2.8s; animation-delay: -1.6s; }
.om-runlight.r4 { animation-duration: 3.6s; animation-delay: -2.2s; }
@keyframes om-runlight-pulse {
  0%, 100% { opacity: 0.55; }
  50%      { opacity: 1; }
}
/* Steady deck windows: subtle warm flicker */
.om-window {
  animation: om-window-flicker 5.8s ease-in-out infinite;
}
.om-window.w2 { animation-delay: -1.2s; }
.om-window.w3 { animation-delay: -2.6s; }
@keyframes om-window-flicker {
  0%, 100% { opacity: 0.85; }
  47%      { opacity: 0.95; }
  50%      { opacity: 0.7; }
  53%      { opacity: 0.95; }
}

/* ============================================================
   Hero / dashboard surfaces
   ============================================================ */
.om-hero-card {
  position: relative;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 24px;
  padding: 44px 52px;
  background: linear-gradient(135deg, rgba(20, 32, 54, 0.55) 0%, rgba(10, 20, 35, 0.4) 100%);
  backdrop-filter: blur(28px) saturate(170%);
  -webkit-backdrop-filter: blur(28px) saturate(170%);
  border: 1px solid var(--hairline);
  border-radius: 28px;
  margin-bottom: 48px;
  box-shadow:
    inset 0 1px 0 var(--inset-hi),
    0 16px 56px 0 rgba(0, 0, 0, 0.5);
  overflow: hidden;
}
.om-hero-card::before {
  content: "";
  position: absolute; inset: 0;
  background: radial-gradient(120% 80% at 8% -10%, rgba(111,177,255,0.14), transparent 55%);
  pointer-events: none;
}
.om-hero-card::after {
  content: "";
  position: absolute; right: -120px; bottom: -120px;
  width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(200,162,74,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.om-hero-title {
  font-size: 46px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 0;
  line-height: 1.1;
  background: linear-gradient(180deg, #FFFFFF 0%, #B6C2D6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.om-hero-tag {
  color: var(--text-muted);
  font-size: 16px;
  margin-top: 14px;
  max-width: 620px;
  line-height: 1.65;
  font-weight: 300;
}
.om-hero-warm-rule {
  width: 64px; height: 3px;
  background: linear-gradient(90deg, var(--accent-warm), transparent);
  margin: 22px 0;
  border-radius: 2px;
}
.om-hero-status {
  text-align: right;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
  display: flex; flex-direction: column; align-items: flex-end; gap: 10px;
}

/* GitHub chips in hero */
.om-gh-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 16px;
  border-radius: 10px;
  font-size: 13px; font-weight: 500; letter-spacing: 0.02em;
  color: var(--text-primary);
  text-decoration: none;
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--hairline);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.25s ease;
}
.om-gh-chip:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(111,177,255,0.12);
  transform: translateY(-2px);
}

/* Mode badges */
.mode-badge {
  display: inline-block; padding: 4px 12px; border-radius: 8px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.1em;
  vertical-align: middle; margin-left: 14px;
  border: 1px solid; font-family: "Inter", sans-serif;
  text-transform: uppercase;
}
.mode-DEMO     { background: rgba(111,177,255,0.16); border-color: rgba(111,177,255,0.42); color: #BFD8FF; }
.mode-LIVE     { background: rgba(79,178,134,0.16);  border-color: rgba(79,178,134,0.42);  color: #B6E2C9; }
.mode-FALLBACK { background: rgba(224,164,88,0.16);  border-color: rgba(224,164,88,0.42);  color: #F2D2A0; }

/* Filter chip row (used on Markets/Watchlist) */
.om-filter-chips {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin: 12px 0 16px 0;
}
.om-filter-chip {
  display: inline-flex; align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px; letter-spacing: 0.02em;
  color: var(--text-muted);
  background: rgba(111,177,255,0.08);
  border: 1px solid rgba(111,177,255,0.22);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* Route Lab summary chip */
.om-summary-chip {
display: inline-block;
padding: 12px 18px;
margin: 6px 0 14px 0;
border-radius: 12px;
background: linear-gradient(135deg, rgba(111,177,255,0.10), rgba(200,162,74,0.06));
border: 1px solid rgba(111,177,255,0.22);
color: var(--text-primary);
font-size: 14px;
line-height: 1.55;
backdrop-filter: blur(12px) saturate(150%);
-webkit-backdrop-filter: blur(12px) saturate(150%);
box-shadow: inset 0 1px 0 var(--inset-hi);
}
.om-summary-chip b { color: var(--accent); font-weight: 600; }

/* Headline insight (drill-down summary line) */
.om-headline-insight {
  display: inline-block;
  padding: 10px 16px;
  margin: 8px 0 20px 0;
  border-radius: 12px;
  background: rgba(111,177,255,0.06);
  border: 1px solid rgba(111,177,255,0.18);
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.55;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
.om-headline-insight b { color: var(--accent); }

/* Footer */
.footer {
  color: var(--text-muted); font-size: 13px;
  margin-top: 4rem; padding-top: 28px;
  border-top: 1px solid var(--hairline);
  text-align: center;
}

/* Streamlit alerts on glass */
[data-testid="stAlert"] {
  background: var(--bg-surface) !important;
  backdrop-filter: blur(14px) saturate(150%);
  -webkit-backdrop-filter: blur(14px) saturate(150%);
  border: 1px solid var(--hairline) !important;
  color: var(--text-primary) !important;
  border-radius: 14px;
  box-shadow: inset 0 1px 0 var(--inset-hi);
}

/* Reduce-motion respect */
@media (prefers-reduced-motion: reduce) {
  .om-ship-wrap, .om-ship-wrap *, .om-wake, .om-shooting,
  .om-cloud, .om-star, .om-runlight, .om-window,
  .om-bg::before, .om-moon, .om-moonpath, .om-wave-shimmer {
    animation: none !important;
  }
}

/* Mobile guard */
@media (max-width: 820px) {
  .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 2rem !important; }
  .om-hero-card { flex-direction: column; padding: 28px; align-items: flex-start; }
  .om-hero-status { align-items: flex-start; text-align: left; margin-top: 8px; }
  .om-hero-title { font-size: 30px; }
  .om-hero-tag { font-size: 14px; }
  [data-testid="stMetricValue"] { font-size: 26px; }
  .om-ship-wrap.foreground { width: 70vw; }
  .om-ship-wrap.midground { width: 130px; }
  .om-ship-wrap.farground { width: 80px; }
}
</style>
"""
# Defensive flatten: strip leading whitespace from every line in _CSS so that
# Streamlit's markdown parser cannot, under any version or quirk, mistake an
# indented CSS continuation for a fenced code block. CSS is whitespace-
# insensitive inside rules, so this has no visual effect.
_CSS = "\n".join(line.lstrip() for line in _CSS.split("\n"))
st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Full-page night-sky background
# ---------------------------------------------------------------------------
# The background is built once and rendered before any Streamlit content. It
# stays fixed in place behind the dashboard via z-index: -10 (so card content
# floats over it). Stars and ships are emitted as plain HTML — keep every line
# of the rendered string flush-left so Streamlit's markdown parser doesn't
# treat indented HTML as a fenced code block.
def _build_night_sky_html() -> str:
    """Return the HTML for the full-page night sky.

    Stars are deterministic (seeded) so the layout is stable across reruns.
    Ships are absolutely-positioned SVGs that drift across the ocean band.
    """
    import random
    rng = random.Random(7)

    # Static star field — many small stars across the sky band (top 70% of viewport)
    static_stars: List[str] = []
    for _ in range(140):
        cx = rng.uniform(0, 100)
        cy = rng.uniform(0, 70)
        size = rng.choice([1, 1, 1, 1.5, 1.5, 2])
        op = rng.uniform(0.25, 0.85)
        static_stars.append(
            f'<div class="om-star" style="left:{cx:.2f}%; top:{cy:.2f}%;'
            f' width:{size}px; height:{size}px; opacity:{op:.2f};'
            f' animation: none;"></div>'
        )

    # Twinkling stars — fewer, bigger, with varied animation timing
    twinkling_stars: List[str] = []
    for _ in range(45):
        cx = rng.uniform(0, 100)
        cy = rng.uniform(0, 65)
        size = rng.choice([1.8, 2, 2, 2.4, 2.6, 3])
        dur = rng.uniform(2.4, 6.5)
        delay = rng.uniform(-6, 0)
        op = rng.uniform(0.55, 1.0)
        twinkling_stars.append(
            f'<div class="om-star" style="left:{cx:.2f}%; top:{cy:.2f}%;'
            f' width:{size}px; height:{size}px; opacity:{op:.2f};'
            f' animation-duration:{dur:.2f}s; animation-delay:{delay:.2f}s;'
            f' box-shadow:0 0 {size*3:.0f}px rgba(255,255,255,0.85);"></div>'
        )

    stars_html = "".join(static_stars + twinkling_stars)

    # Ship SVG factory — emits a stylised cargo ship silhouette with running lights.
    def _ship_svg(scale: float = 1.0, lights_warm: bool = True) -> str:
        # Compact viewBox for layout, simple silhouette + glowing lights.
        warm = "#FFE299" if lights_warm else "#BFD8FF"
        return f'''<svg class="om-ship-svg" viewBox="0 0 720 122" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
<defs>
<linearGradient id="hullFill_{int(scale*100)}" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="#1C2B3F" stop-opacity="0.9"/>
<stop offset="100%" stop-color="#06101F" stop-opacity="0.98"/>
</linearGradient>
<linearGradient id="hullEdge_{int(scale*100)}" x1="0" x2="1">
<stop offset="0%" stop-color="#7489A6" stop-opacity="0.45"/>
<stop offset="50%" stop-color="#D6E0EC" stop-opacity="0.7"/>
<stop offset="100%" stop-color="#7489A6" stop-opacity="0.42"/>
</linearGradient>
<filter id="lightGlow_{int(scale*100)}" x="-200%" y="-200%" width="500%" height="500%">
<feGaussianBlur stdDeviation="2.8" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
</defs>
<path d="M 18,72 L 36,58 L 86,52 L 600,52 L 660,52 L 690,58 L 704,68 L 698,86 L 34,86 Z"
fill="url(#hullFill_{int(scale*100)})" stroke="url(#hullEdge_{int(scale*100)})" stroke-width="1.6" stroke-linejoin="round"/>
<path d="M 24,73 L 696,73" stroke="#A8B6CC" opacity="0.28"/>
<path d="M 86,52 L 86,42 L 156,42 L 156,52" fill="#0D1A2D" stroke="#A8B6CC" opacity="0.78"/>
<rect x="95"  y="44" width="6" height="4" fill="{warm}" filter="url(#lightGlow_{int(scale*100)})" class="om-window"/>
<rect x="106" y="44" width="6" height="4" fill="{warm}" filter="url(#lightGlow_{int(scale*100)})" class="om-window w2"/>
<rect x="117" y="44" width="6" height="4" fill="{warm}" filter="url(#lightGlow_{int(scale*100)})" class="om-window w3"/>
<rect x="128" y="44" width="6" height="4" fill="{warm}" filter="url(#lightGlow_{int(scale*100)})" class="om-window"/>
<rect x="139" y="44" width="6" height="4" fill="{warm}" filter="url(#lightGlow_{int(scale*100)})" class="om-window w2"/>
<path d="M 326,52 L 326,46 L 416,46 L 416,52" fill="#0D1A2D" stroke="#A8B6CC" opacity="0.7"/>
<path d="M 540,52 L 540,30 L 600,30 L 600,52" fill="#0D1A2D" stroke="#A8B6CC" opacity="0.78"/>
<rect x="546" y="34" width="48" height="4" fill="#6FB1FF" opacity="0.4"/>
<rect x="546" y="42" width="48" height="3" fill="#6FB1FF" opacity="0.22"/>
<path d="M 612,30 L 612,18 L 632,18 L 632,30" fill="#0D1A2D" stroke="#A8B6CC" opacity="0.74"/>
<g stroke="#A8B6CC" stroke-width="1.2" opacity="0.66" stroke-linecap="round">
<line x1="120" y1="42" x2="120" y2="20"/>
<line x1="115" y1="24" x2="125" y2="24"/>
<line x1="525" y1="30" x2="525" y2="8"/>
<line x1="520" y1="14" x2="530" y2="14"/>
</g>
<circle cx="120" cy="18" r="3" fill="#FF5252" filter="url(#lightGlow_{int(scale*100)})" class="om-runlight"/>
<circle cx="525" cy="6"  r="3" fill="#FFFFFF" filter="url(#lightGlow_{int(scale*100)})" class="om-runlight r2"/>
<circle cx="622" cy="16" r="2.5" fill="#4FB286" filter="url(#lightGlow_{int(scale*100)})" class="om-runlight r3"/>
<circle cx="34"  cy="82" r="1.8" fill="#FFFFFF" filter="url(#lightGlow_{int(scale*100)})" class="om-runlight r4"/>
<circle cx="698" cy="82" r="1.8" fill="#FFFFFF" filter="url(#lightGlow_{int(scale*100)})" class="om-runlight r2"/>
<circle cx="240" cy="48" r="1.6" fill="{warm}" filter="url(#lightGlow_{int(scale*100)})" class="om-runlight r3"/>
<circle cx="380" cy="48" r="1.6" fill="{warm}" filter="url(#lightGlow_{int(scale*100)})" class="om-runlight r4"/>
<circle cx="470" cy="48" r="1.6" fill="{warm}" filter="url(#lightGlow_{int(scale*100)})" class="om-runlight"/>
<path d="M 60,92 C 148,104 286,107 392,96 C 506,84 612,90 696,98"
fill="none" stroke="#6FB1FF" stroke-width="1" opacity="0.22"/>
</svg>'''

    def _reflection_svg(scale: float = 1.0) -> str:
        return f'''<svg class="om-ship-svg" viewBox="0 0 720 122" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
<path d="M 18,72 L 36,58 L 86,52 L 600,52 L 660,52 L 690,58 L 704,68 L 698,86 L 34,86 Z" fill="#6FB1FF"/>
<path d="M 540,52 L 540,30 L 600,30 L 600,52" fill="#A8B6CC"/>
<path d="M 86,52 L 86,42 L 156,42 L 156,52" fill="#A8B6CC"/>
</svg>'''

    fg_ship = (
        '<div class="om-ship-track t1">'
        '<div class="om-ship-wrap foreground">'
        '<div class="om-wake"></div>'
        + _ship_svg(1.0, True)
        + '<div class="om-ship-reflection">' + _reflection_svg(1.0) + '</div>'
        + '</div></div>'
    )
    mid_ship = (
        '<div class="om-ship-track t2">'
        '<div class="om-ship-wrap midground">'
        '<div class="om-wake"></div>'
        + _ship_svg(0.5, True)
        + '</div></div>'
    )
    far_ship = (
        '<div class="om-ship-track t3">'
        '<div class="om-ship-wrap farground">'
        + _ship_svg(0.3, False)
        + '</div></div>'
    )

    return (
        '<div class="om-bg" aria-hidden="true">'
        '<div class="om-stars-layer">' + stars_html + '</div>'
        '<div class="om-shooting s1"></div>'
        '<div class="om-shooting s2"></div>'
        '<div class="om-shooting s3"></div>'
        '<div class="om-moon"></div>'
        '<div class="om-cloud c1"></div>'
        '<div class="om-cloud c2"></div>'
        '<div class="om-horizon"></div>'
        '<div class="om-ocean">'
        '<div class="om-moonpath"></div>'
        '<div class="om-wave-shimmer w3"></div>'
        '<div class="om-wave-shimmer w2"></div>'
        '<div class="om-wave-shimmer"></div>'
        + far_ship + mid_ship + fg_ship +
        '</div>'
        '</div>'
    )


st.markdown(_build_night_sky_html(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Project metadata (used in hero CTAs and footer)
# ---------------------------------------------------------------------------
GITHUB_URL = "https://github.com/ayuroy01/SharepricemovementMaritime"


# ---------------------------------------------------------------------------
# Sidebar controls — user-facing only. Dev workflow lives in README.
# ---------------------------------------------------------------------------
# Initialise watchlist from defaults on first session load.
if "user_watchlist" not in st.session_state:
    st.session_state["user_watchlist"] = dict(cfg.DEFAULT_WATCHLIST)

with st.sidebar:
    st.markdown("### Open Maritime Quant")
    st.caption("Maritime equity intelligence · open source · not investment advice")
    st.markdown("---")

    st.markdown("**Display**")
    auto_refresh = st.checkbox("Auto-refresh every 5 minutes", value=False,
                               help="Reload market data every 5 min while this tab is open.")

    st.markdown("**News**")
    news_hours = st.select_slider(
        "Window",
        options=[24, 48, 72, 96, 120, 144, 168],
        value=cfg.DEFAULT_NEWS_HOURS,
        format_func=lambda h: f"last {h}h" if h < 168 else "last 7 days",
    )

    st.markdown("**Watchlist**")
    _wl = st.session_state["user_watchlist"]
    with st.expander(f"{len(_wl)} ticker(s)", expanded=False):
        # List existing tickers with a remove button each
        for ticker in list(_wl.keys()):
            r1, r2 = st.columns([3, 1])
            r1.markdown(
                f"<span style='font-feature-settings:\"tnum\"'>"
                f"<b>{ticker}</b><br>"
                f"<span style='color:var(--text-muted); font-size:11px'>{_wl[ticker]}</span>"
                f"</span>",
                unsafe_allow_html=True,
            )
            if r2.button("×", key=f"rm_{ticker}",
                         help=f"Remove {ticker}",
                         disabled=len(_wl) <= 1):
                _wl.pop(ticker, None)
                st.cache_data.clear()
                st.rerun()

        st.markdown("---")
        st.caption("Add a ticker (Yahoo Finance symbol)")
        nt1, nt2 = st.columns([2, 3])
        new_ticker = nt1.text_input("Symbol", placeholder="e.g. CMRE",
                                    key="new_ticker_input",
                                    label_visibility="collapsed")
        new_company = nt2.text_input("Company", placeholder="Costamare Inc.",
                                     key="new_company_input",
                                     label_visibility="collapsed")
        ba, br = st.columns([1, 1])
        if ba.button("Add", use_container_width=True, type="primary",
                     disabled=not new_ticker.strip()):
            symbol = new_ticker.strip().upper()
            company = new_company.strip() or symbol
            if symbol in _wl:
                st.warning(f"{symbol} is already on the watchlist.")
            else:
                _wl[company] = symbol
                st.cache_data.clear()
                # Clear the inputs by deleting their session_state keys
                for k in ("new_ticker_input", "new_company_input"):
                    st.session_state.pop(k, None)
                st.rerun()
        if br.button("Reset to defaults", use_container_width=True):
            st.session_state["user_watchlist"] = dict(cfg.DEFAULT_WATCHLIST)
            st.cache_data.clear()
            st.rerun()
        if not cfg.NEWSAPI_KEY and any(t not in cfg.DEFAULT_WATCHLIST.values()
                                       for t in _wl.values()):
            st.caption(
                "ℹ️ Custom tickers won't have demo data — switch to live mode "
                "or add the symbol to `sample_data/prices/` to see fixtures."
            )

    st.markdown("---")
    if cfg.NEWSAPI_KEY:
        st.markdown("Live news: <span style='color:var(--status-ok)'>**on**</span>",
                    unsafe_allow_html=True)
    else:
        st.markdown("Live news: <span style='color:var(--text-muted)'>**off (demo)**</span>",
                    unsafe_allow_html=True)
        st.caption("Public users see synthetic headlines. To enable live news, "
                   "see the deployment guide in the README.")

# Use st.rerun-based polling instead of meta-refresh: meta-refresh wipes
# in-progress widget state (especially Route Lab inputs).
if auto_refresh:
    import time as _time
    _last = st.session_state.get("_last_auto_refresh", _time.time())
    if _time.time() - _last >= 300:
        st.cache_data.clear()
        st.session_state["_last_auto_refresh"] = _time.time()
        st.rerun()
    else:
        st.session_state.setdefault("_last_auto_refresh", _time.time())


# ---------------------------------------------------------------------------
# Cached data layer
# ---------------------------------------------------------------------------
@st.cache_data(ttl=cfg.WATCHLIST_CACHE_TTL, show_spinner=False)
def cached_watchlist(hours: int, watchlist_items: tuple) -> Dict[str, Any]:
    """`watchlist_items` is a tuple of (company, ticker) pairs — used as the
    cache key. We rebuild the dict inside so callers don't need to hash it."""
    return build_watchlist(news_hours=hours, watchlist=dict(watchlist_items))


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


with st.spinner("Loading shipping market…"):
    data = cached_watchlist(
        news_hours,
        tuple(sorted(st.session_state["user_watchlist"].items())),
    )

rows: List[Dict[str, Any]] = data["rows"]
df = pd.DataFrame(rows) if rows else pd.DataFrame()
bdi = data.get("bdi")
failures: List[str] = data.get("failures", [])
refreshed_at: str = data.get("refreshed_at", "")
mode: str = data.get("effective_mode", "demo").upper()
_IS_DEMO = mode == "DEMO"  # used to mark Plotly canvases with a watermark


# ---------------------------------------------------------------------------
# Hero / header — full-bleed night-sky band with VLCC silhouette
# ---------------------------------------------------------------------------
def _relative_time(iso_ts: str) -> str:
    """Human-friendly time delta for the hero. Falls back to absolute UTC."""
    if not iso_ts:
        return "—"
    try:
        from datetime import datetime, timezone
        ts = datetime.fromisoformat(iso_ts)
        now = datetime.now(timezone.utc)
        delta = (now - ts).total_seconds()
        if delta < 60:
            return "just now"
        if delta < 3600:
            mins = int(delta // 60)
            return f"{mins}m ago"
        if delta < 86400:
            hrs = int(delta // 3600)
            return f"{hrs}h ago"
        return ts.strftime("%Y-%m-%d")
    except Exception:  # noqa: BLE001
        return iso_ts[-8:] if iso_ts else "—"


_relative = _relative_time(refreshed_at)
# Mode label includes a hint when DEMO so users can't mistake demo numbers for live.
_mode_label = "DEMO · synthetic data" if mode == "DEMO" else mode

# Inline night-sky SVG: 30 stars at fixed seeded coordinates + VLCC silhouette.
# Total payload ~5KB, no JS, no external assets, decorative (aria-hidden).
_GH_ICON = (
    '<svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">'
    '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
    '0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 '
    '1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 '
    '0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 '
    '1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 '
    '3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 '
    '16 8c0-4.42-3.58-8-8-8z"/></svg>'
)
# The hero is a single glass card. Background visuals come from the global
# .om-bg layer above. Keep markup flush-left so Streamlit's markdown parser
# doesn't treat indented lines as code blocks.
_HERO = (
    '<div class="om-hero-card">'
    '<div style="flex:1 1 540px; min-width:280px;">'
    f'<h1 class="om-hero-title">Open Maritime Quant Dashboard'
    f' <span class="mode-badge mode-{mode}">{_mode_label}</span></h1>'
    '<div class="om-hero-warm-rule"></div>'
    '<div class="om-hero-tag">'
    'Open-source maritime equity intelligence — watchlist scoring, '
    'Cape-vs-Suez voyage economics, and honest backtests in one calm dashboard.'
    '</div>'
    '</div>'
    '<div class="om-hero-status">'
    '<div style="display:flex; gap:10px;">'
    f'<a class="om-gh-chip" href="{GITHUB_URL}" target="_blank" rel="noopener">{_GH_ICON} Star</a>'
    f'<a class="om-gh-chip" href="{GITHUB_URL}/fork" target="_blank" rel="noopener">⤴ Fork</a>'
    '</div>'
    f'<div style="font-size:12px; color:var(--text-faint);">updated {_relative}</div>'
    '</div>'
    '</div>'
)
st.markdown(_HERO, unsafe_allow_html=True)

# Single, tightly-scoped status banner — only when state requires user attention.
# Replaces the previous duplicate DEMO banner (the badge + watermark already say it).
if mode == "FALLBACK":
    st.warning(
        f"Live data unavailable for {data.get('fallback_count', 0)} call(s). "
        "Showing sample data where providers failed — see Data Health for details.",
        icon="⚠️",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# Desaturated action palette tuned for the dark surface (matches theme.ACTION_BADGE).
# Values used for plotly stacked bars / charts where solid fills are appropriate.
ACTION_COLORS = {
    "VALUE BUY":     "#4FB286",
    "MOMENTUM BUY":  "#3F9A72",
    "PROFIT TAKE":   "#C8A24A",
    "SELL":          "#C46666",
    "STRONG SELL":   "#A24747",
    "AVOID":         "#8B3030",
    "HOLD":          "#5C6E89",
    "ERROR":         "#3A4A66",
}


def color_action(val: str) -> str:
    """Inline style for the Action cell: hairlined chip, not solid fill."""
    bg, border, fg = theme.ACTION_BADGE.get(str(val),
        ("rgba(147,164,189,0.06)", "#3A4A66", "#93A4BD"))
    return (f"background-color: {bg}; color: {fg}; "
            f"border: 1px solid {border}; border-radius: 4px; "
            f"padding: 1px 6px;")


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
# Tab order is funnel-aligned: Markets first (the room you walk into),
# then per-ticker Drill-down, then the differentiated Route Lab, then
# the supporting tabs. Health is last because most visitors never need it.
tab_markets, tab_drill, tab_route, tab_back, tab_news, tab_health = st.tabs(
    ["📊 Markets", "🔍 Drill-down", "🛳️ Route Lab",
     "🧪 Backtest", "📰 News", "🩺 Data Health"]
)
# Internally we still keep two surfaces under "Markets" — the existing
# Overview content above the watchlist table — but they render in one tab.
tab_overview = tab_markets
tab_watch = tab_markets


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
            theme.apply_theme(fig, demo_watermark=_IS_DEMO)
            fig.update_layout(height=280, xaxis_title="", yaxis_title="", showlegend=False)
            st.plotly_chart(fig, width="stretch")
        with c2:
            st.subheader("Sub-scores by ticker")
            chart_df = df[["Ticker", "Tech Score", "Fund Score", "News Score"]].set_index("Ticker")
            st.bar_chart(chart_df, height=260,
                         color=[theme.ACCENT, theme.ACCENT_WARM, "#7FCFE0"])
            st.caption(
                "Score range −1…+1 · Tech: trend + RSI + drawdown · "
                "Fund: P/B, EV/EBITDA, D/E, current ratio · "
                "News: relevance-weighted VADER sentiment."
            )

        def _render_pick_row(r, key_prefix: str) -> None:
            """One clickable row: button + supporting markdown."""
            cols = st.columns([3, 5, 2])
            cols[0].markdown(
                f"**{r['Ticker']}** · {r['Company']}", unsafe_allow_html=True,
            )
            cols[1].markdown(
                f"<span style='{color_action(r['Action'])} font-size:0.78em;"
                f"font-weight:600; letter-spacing:0.04em;'>{r['Action']}</span> · "
                f"<span style='color:var(--text-muted)'>score "
                f"<b style='color:var(--text-primary); font-feature-settings:\"tnum\"'>"
                f"{r['Signal Score']:+.2f}</b></span>",
                unsafe_allow_html=True,
            )
            if cols[2].button("Drill in →", key=f"{key_prefix}_{r['Ticker']}",
                              help=f"Pre-select {r['Ticker']} on the Drill-down tab"):
                st.session_state["drill_ticker"] = r["Ticker"]
                # Streamlit can't programmatically switch tabs; nudge the user.
                try:
                    st.toast(f"{r['Ticker']} pre-selected · open Drill-down ↑", icon="🔍")
                except Exception:  # noqa: BLE001
                    pass

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Top constructive")
            top = df.sort_values("Signal Score", ascending=False).head(3)
            for _, r in top.iterrows():
                _render_pick_row(r, "topc")
        with c4:
            st.subheader("Most cautionary")
            bot = df.sort_values("Signal Score", ascending=True).head(3)
            for _, r in bot.iterrows():
                _render_pick_row(r, "topb")

        if bdi and len(bdi.series) > 0:
            st.subheader("BDRY (BDI proxy)")
            bd_fig = go.Figure(go.Scatter(
                x=bdi.series.index, y=bdi.series.values,
                fill="tozeroy", line=dict(color=theme.ACCENT, width=1.5),
                fillcolor="rgba(111,177,255,0.10)",
            ))
            theme.apply_theme(bd_fig, demo_watermark=_IS_DEMO)
            bd_fig.update_layout(height=240, yaxis_title="BDRY close")
            st.plotly_chart(bd_fig, width="stretch")


# ---- Watchlist (rendered inside Markets, below Overview) -------------------
with tab_watch:
    st.markdown("---")
    st.subheader("Watchlist")
    if df.empty:
        st.error("No data returned from upstream providers.")
    else:
        with st.expander("Filters", expanded=False):
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
        # Active-filter chip row (only when filters are non-default).
        _chip_bits = []
        if len(sel_actions) != len(actions):
            _chip_bits.append(f"<span class='om-filter-chip'>Action · {len(sel_actions)}</span>")
        if min_conf != "low":
            _chip_bits.append(f"<span class='om-filter-chip'>Confidence ≥ {min_conf}</span>")
        if geo_only:
            _chip_bits.append("<span class='om-filter-chip'>Geo Alert</span>")
        if ticker_filter:
            _chip_bits.append(f"<span class='om-filter-chip'>Ticker · {len(ticker_filter)}</span>")
        if search.strip():
            _chip_bits.append(f"<span class='om-filter-chip'>Search · \"{search.strip()}\"</span>")
        if data_warn_only:
            _chip_bits.append("<span class='om-filter-chip'>Data warnings</span>")
        if _chip_bits:
            st.markdown(
                "<div class='om-filter-chips'>" + " ".join(_chip_bits) + "</div>",
                unsafe_allow_html=True,
            )

        st.dataframe(styled, width="stretch", hide_index=True)
        cap_l, cap_r = st.columns([3, 1])
        cap_l.caption(f"Showing {len(view)} of {len(df)} rows.")
        with cap_r:
            with st.popover("ℹ️ What do Actions mean?", use_container_width=True):
                st.markdown(
                    "**`VALUE BUY`** — RSI < 35 (oversold) and fundamentals supportive.<br>"
                    "**`MOMENTUM BUY`** — uptrend confirmed, RSI < 65, fundamentals OK.<br>"
                    "**`HOLD`** — mixed signals; no decisive trigger.<br>"
                    "**`PROFIT TAKE`** — RSI > 70 (overbought) and fundamentals weak.<br>"
                    "**`SELL`** — downtrend with weak fundamentals.<br>"
                    "**`STRONG SELL`** — falling RSI + solvency risk (D/E > 150).<br>"
                    "**`AVOID`** — geopolitical risk in weak/uncertain momentum.<br>"
                    "**`ERROR`** — provider failure for this ticker; see Data Health.",
                    unsafe_allow_html=True,
                )

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
        ticker_options = df["Ticker"].tolist()
        # Honour pre-selection from clickable top cards on Markets
        _preset = st.session_state.get("drill_ticker")
        _idx = ticker_options.index(_preset) if _preset in ticker_options else 0
        ticker_choice = st.selectbox(
            "Pick a ticker", options=ticker_options, index=_idx,
            format_func=lambda t: f"{t} — {df.loc[df['Ticker']==t, 'Company'].iloc[0]}",
            key="drill_ticker_choice",
        )
        row = df.loc[df["Ticker"] == ticker_choice].iloc[0].to_dict()
        st.markdown(f"### {row['Company']} ({row['Ticker']})")

        # ---- Headline insight (one sentence) ----------------------------------
        _act = row['Action']
        _trend = (row.get('Trend') or 'unknown').replace('_', ' ')
        _conf = row['Confidence']
        _risk_score = float(row.get('Risk Score') or 0.0)
        _risk_word = "elevated" if _risk_score >= 0.5 else ("moderate" if _risk_score >= 0.2 else "low")
        _summary = (
            f"<span class='om-headline-insight'>"
            f"<b>{row['Ticker']}</b> is in a <b>{_trend}</b> with <b>{_risk_word}</b> risk. "
            f"The model rates it <em>{_act}</em> with <b>{_conf}</b> confidence."
            f"</span>"
        )
        st.markdown(_summary, unsafe_allow_html=True)

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Action", _act)
        a2.metric("Confidence", _conf)
        a3.metric("Signal", f"{row['Signal Score']:+.2f}")
        a4.metric("Risk", f"{_risk_score:.2f}")

        # Compact, expandable warnings — replaces two stacked st.warning/st.info
        _risk_w = row.get("Risk Warnings") or ""
        _data_w = row.get("Data Warnings") or ""
        if _risk_w or _data_w:
            with st.expander(
                f"⚠ {len([w for w in _risk_w.split(';') if w.strip()])} risk · "
                f"ℹ {len([w for w in _data_w.split(';') if w.strip()])} data note(s)",
                expanded=False,
            ):
                if _risk_w:
                    st.markdown(f"**Risk:** {_risk_w}")
                if _data_w:
                    st.markdown(f"**Data quality:** {_data_w}")
                st.caption(row["Rationale"])
        else:
            st.caption(row["Rationale"])

        hist = cached_price_history(ticker_choice)
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close",
                                     line=dict(width=2, color=theme.ACCENT)))
            for col, dash, color in [
                ("SMA_20",  "dot",      "#7FCFE0"),
                ("SMA_50",  "dash",     theme.ACCENT_WARM),
                ("SMA_200", "longdash", theme.TEXT_FAINT),
            ]:
                if col in hist.columns and hist[col].notna().any():
                    fig.add_trace(go.Scatter(x=hist.index, y=hist[col], name=col,
                                             line=dict(dash=dash, color=color, width=1.4)))
            theme.apply_theme(fig, demo_watermark=_IS_DEMO)
            fig.update_layout(height=380)
            st.plotly_chart(fig, width="stretch")

            if "Volume" in hist.columns:
                vfig = go.Figure(go.Bar(x=hist.index, y=hist["Volume"], name="Volume",
                                        marker=dict(color=theme.TEXT_FAINT, opacity=0.7)))
                theme.apply_theme(vfig, demo_watermark=_IS_DEMO)
                vfig.update_layout(height=160, showlegend=False, yaxis_title="Volume")
                st.plotly_chart(vfig, width="stretch")

            running_max = hist["Close"].cummax()
            dd = (hist["Close"] / running_max - 1.0)
            with st.expander("Drawdown chart"):
                ddfig = go.Figure(go.Scatter(
                    x=dd.index, y=dd * 100, fill="tozeroy",
                    line=dict(color=theme.STATUS_BAD, width=1.2),
                    fillcolor="rgba(226,106,106,0.12)",
                    name="Drawdown %",
                ))
                theme.apply_theme(ddfig, demo_watermark=_IS_DEMO)
                ddfig.update_layout(height=220, yaxis_title="%")
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
    if _IS_DEMO:
        st.info(
            "📰 **Synthetic sample headlines** for product demonstration only. "
            "No real news content is shown in demo mode.",
            icon="ℹ️",
        )
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
        "Ticker",
        options=list(st.session_state["user_watchlist"].values()),
        index=list(st.session_state["user_watchlist"].values()).index("ZIM")
              if "ZIM" in st.session_state["user_watchlist"].values() else 0,
        key="backtest_ticker",
    )
    period = bc2.selectbox("Period", ["1y", "2y", "5y", "10y", "max"], index=2, key="backtest_period")
    commission = bc3.number_input(
        "Commission (bps/side)", 0.0, 100.0, cfg.BT_COMMISSION_BPS, 1.0, key="backtest_commission",
    )
    slippage = bc4.number_input(
        "Slippage (bps/side)", 0.0, 100.0, cfg.BT_SLIPPAGE_BPS, 1.0, key="backtest_slippage",
    )
    # Pre-render with current settings on every load — no dead button.
    # Cached so it's effectively instant after first run.
    @st.cache_data(ttl=3600, show_spinner=False)
    def _cached_backtest(_ticker, _period, _commission, _slippage):
        hist_df, _st = fetch_price_history(_ticker, period=_period)
        result = run_backtest(hist_df, _ticker,
                              commission_bps=_commission, slippage_bps=_slippage)
        return hist_df, result

    rerun_btn = st.button("Re-run with current settings", type="primary", key="backtest_run")
    if rerun_btn:
        _cached_backtest.clear()  # user explicitly asked for a fresh run
    with st.spinner(f"Backtesting {bt_ticker}…"):
        hist, res = _cached_backtest(bt_ticker, period, commission, slippage)
    # Always render the result — there's never a dead state on this tab now.
    if res is not None:
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
                                         line=dict(color=theme.STATUS_OK, width=2)))
                fig.add_trace(go.Scatter(x=eq_df.index, y=eq_df["buy_hold"], name="buy & hold",
                                         line=dict(color=theme.TEXT_MUTED, width=1, dash="dash")))
                theme.apply_theme(fig, demo_watermark=_IS_DEMO)
                fig.update_layout(height=300, yaxis_title="Equity ($)")
                st.plotly_chart(fig, width="stretch")

                eq_max = eq_df["strategy"].cummax()
                bt_dd = (eq_df["strategy"] / eq_max - 1) * 100
                ddfig = go.Figure(go.Scatter(
                    x=bt_dd.index, y=bt_dd, fill="tozeroy",
                    line=dict(color=theme.STATUS_BAD, width=1.2),
                    fillcolor="rgba(226,106,106,0.12)", name="Drawdown %",
                ))
                theme.apply_theme(ddfig, demo_watermark=_IS_DEMO)
                ddfig.update_layout(height=180, yaxis_title="%")
                st.plotly_chart(ddfig, width="stretch")

            if res.trades:
                st.subheader("Trades")
                st.dataframe(pd.DataFrame([t.__dict__ for t in res.trades]),
                             hide_index=True, width="stretch")
            if res.notes:
                st.caption(" · ".join(res.notes))
            st.warning("Past performance does not guarantee future results. "
                       "This is a technical-only research backtest.")

    # ---- Portfolio backtest: same strategy across the watchlist -----------
    st.markdown("---")
    st.subheader("Portfolio backtest")
    st.caption(
        "Run the same strategy across every ticker in your watchlist with "
        "equal capital. Each ticker is backtested independently; the portfolio "
        "curve is the equal-weighted average. No rebalancing; no correlation "
        "modelling. Use it to spot which tickers carry the strategy."
    )

    if st.button("Run portfolio backtest", key="portfolio_backtest_run"):
        portfolio_results: List[Dict[str, Any]] = []
        equity_traces = {}
        wl = st.session_state["user_watchlist"]
        progress = st.progress(0.0, text="Backtesting watchlist…")
        for i, (name, t) in enumerate(wl.items()):
            try:
                hist_p, _ = fetch_price_history(t, period=period)
                r = run_backtest(hist_p, t,
                                 commission_bps=commission, slippage_bps=slippage)
                if r.bars > 0:
                    portfolio_results.append({
                        "Ticker": t, "Company": name,
                        "Total return": r.total_return,
                        "Buy & hold": r.benchmark_return,
                        "vs B&H": r.total_return - r.benchmark_return,
                        "Max drawdown": r.max_drawdown,
                        "Sharpe": r.sharpe,
                        "Trades": r.n_trades,
                        "Win rate": r.win_rate,
                    })
                    if r.equity_curve and r.equity_dates:
                        eq = pd.Series(r.equity_curve,
                                       index=pd.to_datetime(r.equity_dates))
                        # Normalise so all tickers start at 1.0
                        equity_traces[t] = eq / eq.iloc[0]
            except Exception as exc:  # noqa: BLE001
                portfolio_results.append({
                    "Ticker": t, "Company": name, "Total return": None,
                    "Buy & hold": None, "vs B&H": None,
                    "Max drawdown": None, "Sharpe": None,
                    "Trades": 0, "Win rate": None,
                    "_error": str(exc),
                })
            progress.progress((i + 1) / len(wl), text=f"Backtested {t}")
        progress.empty()

        if not portfolio_results:
            st.error("Portfolio backtest produced no results.")
        else:
            # Per-ticker summary table
            pdf = pd.DataFrame(portfolio_results).drop(
                columns=[c for c in ["_error"] if c in pd.DataFrame(portfolio_results).columns],
                errors="ignore",
            )
            shown = pdf.style.format({
                "Total return": lambda v: f"{v*100:+.2f}%" if pd.notna(v) else "—",
                "Buy & hold":  lambda v: f"{v*100:+.2f}%" if pd.notna(v) else "—",
                "vs B&H":      lambda v: f"{v*100:+.2f}%" if pd.notna(v) else "—",
                "Max drawdown": lambda v: f"{v*100:+.2f}%" if pd.notna(v) else "—",
                "Sharpe":      lambda v: f"{v:.2f}" if pd.notna(v) else "—",
                "Win rate":    lambda v: f"{v*100:.1f}%" if pd.notna(v) else "—",
            }, na_rep="—")
            st.dataframe(shown, hide_index=True, width="stretch")

            # Equal-weight portfolio curve + per-ticker traces
            if equity_traces:
                merged = pd.concat(equity_traces.values(), axis=1, join="outer")
                merged.columns = list(equity_traces.keys())
                merged = merged.fillna(method="ffill").fillna(1.0)
                portfolio = merged.mean(axis=1)

                pf_fig = go.Figure()
                # Per-ticker traces (faded)
                for col in merged.columns:
                    pf_fig.add_trace(go.Scatter(
                        x=merged.index, y=merged[col], name=col,
                        line=dict(width=1, color=theme.TEXT_FAINT),
                        opacity=0.5, hoverinfo="skip" if len(merged.columns) > 8 else None,
                    ))
                # Portfolio (bold accent)
                pf_fig.add_trace(go.Scatter(
                    x=portfolio.index, y=portfolio, name="Equal-weight portfolio",
                    line=dict(width=2.5, color=theme.ACCENT),
                ))
                theme.apply_theme(pf_fig, demo_watermark=_IS_DEMO)
                pf_fig.update_layout(height=320,
                                     yaxis_title="Indexed equity (1.0 = start)")
                st.plotly_chart(pf_fig, width="stretch")

                # Headline portfolio metrics
                pm1, pm2, pm3 = st.columns(3)
                pf_total = float(portfolio.iloc[-1] - 1.0)
                pf_max_dd = float((portfolio / portfolio.cummax() - 1.0).min())
                pm1.metric("Portfolio total", f"{pf_total*100:+.2f}%")
                pm2.metric("Portfolio max drawdown", f"{pf_max_dd*100:+.2f}%")
                pm3.metric("Tickers contributing", len(equity_traces))

            errs = [r for r in portfolio_results if r.get("_error") or r.get("Total return") is None]
            if errs:
                with st.expander(f"⚠ {len(errs)} ticker(s) skipped"):
                    for e in errs:
                        st.caption(f"{e['Ticker']}: {e.get('_error', 'no data')}")


# ---- VLCC Route Lab --------------------------------------------------------
with tab_route:
    import base64
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

    # ---------------------------------------------------------------------
    # Scenario sharing helpers (URL params + JSON download/upload).
    # Mapping translates a route_economics scenario dict to/from the widget
    # session_state keys used by the inputs expander below.
    # ---------------------------------------------------------------------
    _SCENARIO_KEY_MAP = [
        # (section,    field,                                widget_key)
        ("vessel",     "hull_value_usd",                     "route_hull_value"),
        ("vessel",     "cargo_tonnes",                       "route_cargo_tonnes"),
        ("vessel",     "cargo_value_per_tonne_usd",          "route_cargo_value_per_tonne"),
        ("vessel",     "fuel_consumption_mt_day",            "route_fuel_burn"),
        ("vessel",     "scrubber_equipped",                  "route_scrubber"),
        ("fuel",       "grade",                              "route_fuel_grade"),
        ("fuel",       "price_per_mt_usd",                   "route_fuel_price"),
        ("fuel",       "vlsfo_price_per_mt_usd",             "route_vlsfo_ref"),
        ("fuel",       "co2_factor",                         "route_co2_factor"),
        ("charter",    "rate_per_day_usd",                   "route_charter_rate"),
        ("charter",    "financing_rate_annual",              "route_financing_rate"),
        ("route",      "suez_days",                          "route_suez_days"),
        ("route",      "cape_days",                          "route_cape_days"),
        ("route",      "suez_toll_usd",                      "route_suez_toll"),
        ("route",      "cape_port_fees_usd",                 "route_cape_fees"),
        ("route",      "cape_congestion_delay_days",         "route_cape_delay"),
        ("insurance",  "hm_awrp_pct_suez",                   "route_hm_suez"),
        ("insurance",  "hm_awrp_pct_cape",                   "route_hm_cape"),
        ("insurance",  "cargo_awrp_pct_suez",                "route_cargo_suez"),
        ("insurance",  "cargo_awrp_pct_cape",                "route_cargo_cape"),
        ("regulation", "origin_in_eea",                      "route_origin_eea"),
        ("regulation", "dest_in_eea",                        "route_dest_eea"),
        ("regulation", "has_intermediate_eea_port_call",     "route_mid_eea"),
        ("regulation", "eua_price_usd",                      "route_eua_price"),
    ]

    def _scenario_dict_to_state(d: dict) -> int:
        """Push values from a scenario dict into widget session_state keys.
        Returns the count of fields populated. Skips unknown sections silently."""
        n = 0
        for section, field, key in _SCENARIO_KEY_MAP:
            try:
                v = d.get(section, {}).get(field)
            except AttributeError:
                continue
            if v is None:
                continue
            st.session_state[key] = v
            n += 1
        return n

    def _encode_scenario(scen: RouteScenario) -> str:
        """Serialise → base64url for use in ?scenario=... query params."""
        d = scen.to_dict()
        # Drop the immutable metadata; only the inputs need to round-trip.
        slim = {sec: d[sec] for sec in
                ("vessel", "fuel", "charter", "insurance", "route", "regulation")
                if sec in d}
        raw_b = json.dumps(slim, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw_b).decode("ascii").rstrip("=")

    def _decode_scenario(token: str) -> dict | None:
        """Inverse of _encode_scenario. Returns None on any error."""
        try:
            pad = "=" * (-len(token) % 4)
            raw_b = base64.urlsafe_b64decode((token + pad).encode("ascii"))
            return json.loads(raw_b)
        except Exception:  # noqa: BLE001
            return None

    # Hydrate inputs from URL on first load only — never overwrite user edits
    # made later in the session.
    if not st.session_state.get("_route_url_loaded"):
        _qp = st.query_params
        if "scenario" in _qp:
            decoded = _decode_scenario(_qp["scenario"])
            if decoded:
                _scenario_dict_to_state(decoded)
        st.session_state["_route_url_loaded"] = True

    st.markdown("## 🛳️ VLCC Route Lab — Cape vs Suez")
    st.caption(
        f"Voyage-economics calculator · {base.name} · last reviewed {base.last_reviewed}"
    )

    # --- 1. INPUTS (collapsed by default) — values flow into `scen` below
    with st.expander("Edit scenario assumptions", expanded=False):
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

    # --- 2. SCENARIO SUMMARY CHIP + 4-UP BREAK-EVEN CARD ----------------
    cmp = compare_routes(scen)
    _scrubber_str = "scrubber" if scen.vessel.scrubber_equipped else "no scrubber"
    _summary = (
        f"<div class='om-summary-chip'>"
        f"VLCC · <b>{int(scen.vessel.cargo_tonnes):,} mt</b> cargo · "
        f"<b>{scen.fuel.grade} @ ${scen.fuel.price_per_mt_usd:.0f}/mt</b> · "
        f"<b>${scen.charter.rate_per_day_usd:,.0f}/d</b> charter · "
        f"{_scrubber_str} · "
        f"<b>{cmp.cheaper_route}</b> wins by "
        f"<b>${abs(cmp.differential_cape_minus_suez):,.0f}</b> all-in"
        f"</div>"
    )
    st.markdown(_summary, unsafe_allow_html=True)
    st.markdown("")

    # Headline 4-up card — the screenshot moment for the whole product.
    st.markdown(
        "<div style='font-size:11px; text-transform:uppercase; letter-spacing:0.08em; "
        "color:var(--text-muted); margin-bottom:6px;'>Break-even snapshot</div>",
        unsafe_allow_html=True,
    )
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("All-in Cape − Suez",
              f"${cmp.differential_cape_minus_suez:,.0f}",
              delta_color=("inverse" if cmp.differential_cape_minus_suez > 0 else "normal"),
              help="Headline differential at current assumptions, "
                   "including insurance entered on both routes.")
    h2.metric("Pre-insurance Cape − Suez",
              f"${cmp.pre_insurance_differential_cape_minus_suez:,.0f}",
              help="Same comparison with H&M and cargo war-risk excluded on both sides. "
                   "Often the framing used in analyst briefs.")
    if cmp.breakeven_combined_suez_insurance_usd is not None:
        v = cmp.breakeven_combined_suez_insurance_usd
        h3.metric("Break-even combined Suez insurance",
                  f"${v:,.0f}",
                  delta_color=("normal" if v > 0 else "inverse"),
                  help="Total Suez-side war-risk USD that would tie Cape (given Cape's "
                       "current insurance). Negative ⇒ Cape already cheaper before insurance.")
    else:
        h3.metric("Break-even combined Suez insurance", "—")
    if cmp.breakeven_awrp_for_cape_pct is not None:
        h4.metric("Break-even Suez H&M AWRP",
                  f"{cmp.breakeven_awrp_for_cape_pct*100:.3f}% of hull",
                  help="H&M war-risk on Suez (given all other current assumptions) "
                       "at which the all-in totals tie.")
    else:
        h4.metric("Break-even Suez H&M AWRP", "—")
    st.markdown(
        "<div style='font-size:11px; color:var(--text-muted); margin-top:6px;'>"
        "Different reports may quote different break-even numbers depending on whether "
        "insurance is netted into the subtotal — compare like with like."
        "</div>",
        unsafe_allow_html=True,
    )

    # --- 2b. SHARE / EXPORT / IMPORT this scenario --------------------------
    with st.expander("🔗 Share this scenario", expanded=False):
        share_token = _encode_scenario(scen)
        share_url = f"?scenario={share_token}"
        st.caption(
            "Append this to your dashboard URL — anyone who opens it sees the same "
            "inputs. The encoded payload contains only the scenario fields (no "
            "personal data, no API keys)."
        )
        st.code(share_url, language=None)

        sc1, sc2 = st.columns([1, 1])
        with sc1:
            json_bytes = json.dumps(scen.to_dict(), indent=2).encode("utf-8")
            st.download_button(
                "⬇️ Download JSON",
                data=json_bytes,
                file_name=f"route_scenario_{int(scen.vessel.cargo_tonnes/1000)}kmt.json",
                mime="application/json",
                use_container_width=True,
                key="route_share_download",
            )
        with sc2:
            uploaded = st.file_uploader(
                "⬆️ Load JSON file",
                type=["json"],
                key="route_share_upload",
                label_visibility="collapsed",
            )
            if uploaded is not None and not st.session_state.get(
                f"_uploaded_processed_{uploaded.file_id}"
            ):
                try:
                    parsed = json.loads(uploaded.read().decode("utf-8"))
                    n = _scenario_dict_to_state(parsed)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not load scenario: {exc}")
                else:
                    st.session_state[f"_uploaded_processed_{uploaded.file_id}"] = True
                    st.success(f"Loaded {n} scenario fields. Reloading…")
                    st.rerun()

        # ----- Markdown export — for memos / Slack / GitHub issues ---------
        st.markdown("**📋 Copy as Markdown**")
        st.caption("Drop into a Slack message, a memo, or a GitHub issue.")
        _md_lines = [
            f"### VLCC Route Lab · {scen.name}",
            "",
            f"_Last reviewed {scen.last_reviewed} · "
            f"{int(scen.vessel.cargo_tonnes):,} mt cargo · "
            f"{scen.fuel.grade} @ ${scen.fuel.price_per_mt_usd:,.0f}/mt · "
            f"${scen.charter.rate_per_day_usd:,.0f}/d charter._",
            "",
            "**Headline differential**",
            "",
            f"| Metric | Value |",
            f"| --- | ---: |",
            f"| All-in Cape − Suez | ${cmp.differential_cape_minus_suez:,.0f} |",
            f"| Pre-insurance Cape − Suez | ${cmp.pre_insurance_differential_cape_minus_suez:,.0f} |",
            f"| Break-even combined Suez insurance | "
            f"${cmp.breakeven_combined_suez_insurance_usd:,.0f} |",
        ]
        if cmp.breakeven_awrp_for_cape_pct is not None:
            _md_lines.append(
                f"| Break-even Suez H&M AWRP | "
                f"{cmp.breakeven_awrp_for_cape_pct*100:.3f}% of hull |"
            )
        _md_lines.extend([
            "",
            f"**Model-implied lower-cost route:** `{cmp.cheaper_route}` "
            f"(all-in) · `{cmp.cheaper_route_ex_insurance}` (pre-insurance).",
            "",
            "**Cost components (USD)**",
            "",
            f"| Component | Suez | Cape |",
            f"| --- | ---: | ---: |",
        ])
        for c in cmp.suez.components:
            _md_lines.append(
                f"| {c.replace('_', ' ').title()} | "
                f"${cmp.suez.components[c]:,.0f} | "
                f"${cmp.cape.components[c]:,.0f} |"
            )
        _md_lines.extend([
            f"| **Total** | **${cmp.suez.total_cost:,.0f}** | "
            f"**${cmp.cape.total_cost:,.0f}** |",
            "",
            f"_ETS coverage: {ets_coverage_fraction(scen.regulation)*100:.0f}% · "
            f"Generated by Open Maritime Quant — not investment, routing, "
            f"or insurance advice._",
        ])
        st.code("\n".join(_md_lines), language="markdown")

    st.markdown("---")

    # --- 3. SUB-TABS (results only — Cost Breakdown is the default surface)
    sub_cost, sub_sens, sub_reg, sub_src = st.tabs(
        ["💰 Cost Breakdown", "🎯 Sensitivity", "🌍 Regulation", "📚 Assumptions & Sources"]
    )

    # --- Cost Breakdown ----------------------------------------------------
    with sub_cost:
        # cmp already computed above for the headline card; reuse it.

        # Per-route totals (the headline 4-up + scenario summary chip already
        # show the differentials; this surface is the line-item evidence).
        st.markdown("**Totals (USD)**")
        m1, m2 = st.columns(2)
        m1.metric("Suez total", f"${cmp.suez.total_cost:,.0f}")
        m2.metric("Cape total", f"${cmp.cape.total_cost:,.0f}")

        rows = [cmp.suez.as_row(), cmp.cape.as_row()]
        bdf = pd.DataFrame(rows).set_index("route").T
        st.dataframe(
            bdf.style.format("{:,.0f}").apply(
                lambda s: ["background-color: rgba(79,178,134,0.10); color: #B6E2C9; "
                           "border-top: 1px solid #2E5E48; font-weight: 600;"
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
        theme.apply_theme(comp_fig, demo_watermark=_IS_DEMO)
        comp_fig.update_layout(barmode="stack", height=320, yaxis_title="Cost (USD)")
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
        _cmap_diff = theme.diverging_cmap(reverse=True)  # low (Cape cheaper) → green
        _styled_diff = diff_df.style.format("{:,.0f}")
        if _cmap_diff is not None:
            _styled_diff = _styled_diff.background_gradient(cmap=_cmap_diff, axis=None)
        st.dataframe(_styled_diff, width="stretch")

        awrp_df = pd.DataFrame(
            [[(v if v is not None else float("nan")) * 100 for v in row] for row in sens.breakeven_awrp_matrix],
            index=diff_df.index, columns=diff_df.columns,
        )
        st.markdown("**Break-even Suez H&M AWRP (% of hull)**")
        _cmap_awrp = theme.diverging_cmap(reverse=False)  # high tolerance → green
        _styled_awrp = awrp_df.style.format("{:.3f}%", na_rep="—")
        if _cmap_awrp is not None:
            _styled_awrp = _styled_awrp.background_gradient(cmap=_cmap_awrp, axis=None)
        st.dataframe(_styled_awrp, width="stretch")

        # Two line charts
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("**Break-even AWRP vs charter rate** (at current fuel price)")
            xs = sens.charter_rates
            ys = []
            for cr in xs:
                s = scenario_with_overrides(scen, charter_rate=cr)
                ys.append((compare_routes(s).breakeven_awrp_for_cape_pct or 0) * 100)
            fig = go.Figure(go.Scatter(
                x=xs, y=ys, mode="lines+markers",
                line=dict(color=theme.ACCENT, width=1.6),
                marker=dict(color=theme.ACCENT, size=7),
            ))
            theme.apply_theme(fig, demo_watermark=_IS_DEMO)
            fig.update_layout(height=260,
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
            fig = go.Figure(go.Scatter(
                x=xs, y=ys, mode="lines+markers",
                line=dict(color=theme.ACCENT_WARM, width=1.6),
                marker=dict(color=theme.ACCENT_WARM, size=7),
            ))
            theme.apply_theme(fig, demo_watermark=_IS_DEMO)
            fig.update_layout(height=260,
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
        # Color-code the kind column with desaturated chip styling (matches mode badges).
        kind_chip = {
            "user_input":          ("rgba(111,177,255,0.10)", "#2A4870", "#BFD8FF"),
            "analyst_default":     ("rgba(224,164,88,0.10)",  "#6E4F23", "#F2D2A0"),
            "regulatory_constant": ("rgba(79,178,134,0.10)",  "#2E5E48", "#B6E2C9"),
            "vessel_default":      ("rgba(147,164,189,0.08)", "#3A4A66", "#C7D2E2"),
        }
        def _kind_style(v):
            bg, bd, fg = kind_chip.get(v, ("rgba(147,164,189,0.06)", "#3A4A66", "#93A4BD"))
            return (f"background-color: {bg}; color: {fg}; "
                    f"border: 1px solid {bd}; border-radius: 4px;")
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
# Footer + consolidated disclaimer dialog
# ---------------------------------------------------------------------------
st.markdown(
    f"<div class='footer'>"
    f"Open-source · <a href='{GITHUB_URL}' target='_blank' "
    f"style='color:var(--text-muted); text-decoration:none; border-bottom:1px dotted var(--text-muted);'>MIT</a> · "
    f"<a href='{GITHUB_URL}#deployment' target='_blank' "
    f"style='color:var(--text-muted); text-decoration:none; border-bottom:1px dotted var(--text-muted);'>Deploy your own →</a> · "
    f"<a href='#disclaimer' style='color:var(--text-muted); text-decoration:none; "
    f"border-bottom:1px dotted var(--text-muted);' "
    f"onclick='document.getElementById(\"om-disclaimer-toggle\").click(); return false;'>Disclaimer</a>"
    f"</div>",
    unsafe_allow_html=True,
)
with st.expander("Disclaimer", expanded=False):
    st.markdown("""
**This dashboard is research and educational software. It is:**

- **Not investment advice.** Equity signals are unvalidated heuristics.
- **Not routing advice.** The Route Lab does not consider weather, traffic separation,
  port slots, charterer instructions, or current threat reports.
- **Not insurance advice.** AWRP percentages are user-editable placeholders.
- **Not legal advice.** EU ETS scope rules are implemented per public EC/EMSA
  documents but should be verified with counsel.
- **Not warranty-backed.** Free-tier data may be delayed, missing, or wrong.

In demo mode the dashboard runs on synthetic sample data. In live mode it uses
yfinance and NewsAPI free tiers (the latter is dev-only by license). BDRY is a
public proxy for the Baltic Dry Index, not the index itself. TCE rates,
vessel valuations, and AIS positions require paid licensed providers and are
shown as "not configured" in this build.

See [SECURITY.md]({}/blob/main/SECURITY.md) and
[docs/COMMERCIAL_READINESS.md]({}/blob/main/docs/COMMERCIAL_READINESS.md) for
the full data-licensing and deployment guidance.
""".format(GITHUB_URL, GITHUB_URL))
