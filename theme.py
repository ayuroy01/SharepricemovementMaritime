"""Shared visual tokens + Plotly theme for the dashboard.

Single source of truth for the dark-night-sea palette. The CSS in
`dashboard.py` mirrors these values; keep them in sync.
"""
from __future__ import annotations

from typing import Any


# --- Color tokens ----------------------------------------------------------
BG_DEEP      = "#07101F"
BG_SURFACE   = "#0E1B2E"
BG_ELEVATED  = "#142840"
HAIRLINE     = "#1F3454"
TEXT_PRIMARY = "#E6EDF7"
# Bumped from #93A4BD to meet WCAG AA (4.5:1) on #07101F deep navy.
TEXT_MUTED   = "#A8B6CC"
TEXT_FAINT   = "#6B7E99"
ACCENT       = "#6FB1FF"   # cyan-blue running-light
ACCENT_WARM  = "#C8A24A"   # brass — sparingly
STATUS_OK    = "#4FB286"
STATUS_WARN  = "#E0A458"
STATUS_BAD   = "#E26A6A"

COLORWAY = [
    "#6FB1FF", "#C8A24A", "#4FB286", "#E0A458",
    "#E26A6A", "#9F7AEA", "#7FCFE0",
]

# Diverging colorscale that reads on dark — replaces RdYlGn / RdYlGn_r.
DIVERGING = [
    [0.0, STATUS_BAD],
    [0.5, HAIRLINE],
    [1.0, STATUS_OK],
]
DIVERGING_REVERSED = [
    [0.0, STATUS_OK],
    [0.5, HAIRLINE],
    [1.0, STATUS_BAD],
]


# --- Action / mode colour tokens (desaturated for dark backgrounds) -------
# Each entry: (background, border, text)
ACTION_BADGE = {
    "VALUE BUY":     ("rgba(79,178,134,0.12)", "#2E5E48", "#B6E2C9"),
    "MOMENTUM BUY":  ("rgba(79,178,134,0.10)", "#2E5E48", "#B6E2C9"),
    "PROFIT TAKE":   ("rgba(224,164,88,0.12)", "#6E4F23", "#F2D2A0"),
    "HOLD":          ("rgba(147,164,189,0.10)", "#3A4A66", "#C7D2E2"),
    "SELL":          ("rgba(226,106,106,0.12)", "#6E2E2E", "#F2C0C0"),
    "STRONG SELL":   ("rgba(226,106,106,0.18)", "#7A2929", "#F8B6B6"),
    "AVOID":         ("rgba(226,106,106,0.22)", "#8A2424", "#FBA8A8"),
    "ERROR":         ("rgba(147,164,189,0.06)", "#2A3A52", "#93A4BD"),
}


def diverging_cmap(reverse: bool = False):
    """Matplotlib LinearSegmentedColormap for pandas Styler.background_gradient.

    Stops: STATUS_BAD ↔ HAIRLINE ↔ STATUS_OK. Set `reverse=True` so green
    appears at the LOW end (use for matrices where low values are good,
    e.g. Cape-vs-Suez differential where lower means Cape is more attractive).
    """
    try:
        from matplotlib.colors import LinearSegmentedColormap
    except ImportError:
        return None
    stops = ["#4FB286", "#1F3454", "#E26A6A"] if reverse else ["#E26A6A", "#1F3454", "#4FB286"]
    return LinearSegmentedColormap.from_list("om_diverging", stops, N=256)


def apply_theme(fig: Any, *, demo_watermark: bool = False) -> Any:
    """Apply the project's dark theme to a Plotly figure.

    Idempotent — safe to call repeatedly. Returns the same figure.

    When `demo_watermark=True`, adds a low-contrast diagonal "DEMO DATA"
    watermark across the chart canvas so users can never mistake demo
    numbers for live ones in screenshots.
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, -apple-system, sans-serif",
                  color=TEXT_PRIMARY, size=12),
        colorway=COLORWAY,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=HAIRLINE,
            borderwidth=0,
            font=dict(color=TEXT_MUTED, size=11),
            orientation="h", y=-0.18, x=0,
        ),
        margin=dict(l=8, r=8, t=16, b=8),
        hoverlabel=dict(
            bgcolor="rgba(20,40,64,0.85)", bordercolor=HAIRLINE,
            font=dict(color=TEXT_PRIMARY, family="Inter, system-ui, sans-serif"),
        ),
    )
    fig.update_xaxes(
        gridcolor=HAIRLINE, zerolinecolor=HAIRLINE, linecolor=HAIRLINE,
        tickfont=dict(color=TEXT_MUTED, size=11),
        title_font=dict(color=TEXT_MUTED, size=11),
        showspikes=False,
    )
    fig.update_yaxes(
        gridcolor=HAIRLINE, zerolinecolor=HAIRLINE, linecolor=HAIRLINE,
        tickfont=dict(color=TEXT_MUTED, size=11),
        title_font=dict(color=TEXT_MUTED, size=11),
        showspikes=False,
    )
    if demo_watermark:
        fig.add_annotation(
            text="DEMO DATA",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False,
            font=dict(family="Inter, sans-serif", size=42,
                      color=ACCENT_WARM),
            opacity=0.07, textangle=-22,
        )
    return fig
