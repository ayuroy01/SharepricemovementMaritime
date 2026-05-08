# UX / Conversion Teardown — Open Maritime Quant Dashboard

> **Persona note.** This audit is written in two passes by a ruthless
> conversion-obsessed founder + first-time user. The funnel for this
> open-source project is:
>
>   1. Visitor stays past the hero (90 → 60 sec retention).
>   2. Clicks into VLCC Route Lab (the differentiated feature).
>   3. Stars / forks on GitHub.
>   4. Deploys their own copy or contributes.
>
> Every critique below is anchored to one of those four steps.

---

## PASS 1 — The Designer

You hired me to rip this apart. Here it is.

### What's working

The animated tanker silhouette with the night sky is **the best decision
in this entire product**. It's the only piece that looks like it cost
money. Keep it. Everything else is fighting it.

Tabular numerals on the metrics. Hairlined cards. Inter at 14px. The
restrained palette. All correct. You learned the right lessons from
Linear and Vercel.

### What's broken

Let's not waste time.

#### The hero is half a brand and half a Datadog widget.

Right side of the hero says `Data health: OK / Refreshed UTC: 20:45:14`.
That belongs in `/_internal/health.json`, not in the front door. **A
luxury watch doesn't tell you its battery percentage on the dial.** Move
it to the Data Health tab. The hero should sell what this product does,
not reassure ops.

#### The hero has no value prop.

> "Maritime equity monitoring · shipping & freight proxy · news and
> geopolitical risk · transparent rule-based scoring · honest backtests."

That's five product features strung together with bullets. It's not a
sentence anybody finishes reading. Compare:

- Linear: *"The new standard for modern software development."*
- Vercel: *"Develop. Preview. Ship."*
- Superhuman: *"The fastest email experience ever made."*

You need ONE line. Try: *"Maritime equity intelligence — calibrated
for the night shift."* Or: *"From spot freight rates to signal scores,
in one calm dashboard."* Pick a north star, not a feature list.

#### Seven tabs is the death of focus.

Overview / Watchlist / Drill-down / News / Backtest / VLCC Route Lab /
Data Health. **Seven.** Linear has four primary areas. Notion has three.
Your visitor's eye lands on Overview, sees a bar chart of "signal
distribution" (which means nothing to them yet), and they don't know
where to go.

Worse: **the Route Lab — your only differentiated module — is the
sixth tab from the left.** That's the equivalent of putting your demo
video below the fold.

Reorder by visitor intent:

```
Markets | Drill-down | Route Lab | Backtest | News | Health
```

`Overview + Watchlist` collapse into "Markets". `Data Health` becomes a
status dot in the hero, not a top-level tab.

#### The mode badge is invisible to the people who matter.

"DEMO" in a 11px desaturated cyan chip next to the H1. A first-time
user will not register this. Then they'll see ZIM at $29.23 with RSI
63.8 and assume it's live data. **You will eventually have someone
screenshot demo numbers and post them on a forum saying "Open Maritime
Quant says ZIM is a hold."** That's reputational damage from a typography
choice.

Fix: when in DEMO, add a thin diagonal `DEMO DATA` watermark across
chart canvases (5% opacity, brass accent). Keep the badge but change
"DEMO" to "DEMO · synthetic data". No ambiguity.

#### The sidebar is a developer's notebook.

```
News window (hours) — slider
Auto-refresh every 5 min — checkbox
NewsAPI key detected ✅
Refresh now — button
Configure via environment:
  APP_MODE = demo / live / auto
  NEWSAPI_KEY = optional
```

Nothing here is user-facing. Every line of it is dev plumbing leaking
upward.

- "News window" — fine, but call it *"News window: last 72 hours"*
  and put it on the News tab where it actually applies.
- "Auto-refresh" — fine, but it does a hard browser reload that nukes
  any in-progress Route Lab inputs. Switch it to `st.rerun()` on a timer.
- "NewsAPI key detected" — public users don't know what that is. Drop
  it. Show "Live news: on / Live news: off (demo)" instead.
- "Configure via environment: APP_MODE..." — **delete entirely**.
  Public Streamlit Cloud users can't set env vars from the sidebar
  anyway. That's documentation. Move it to README.

#### Action chips have no legend.

VALUE BUY / MOMENTUM BUY / HOLD / PROFIT TAKE / SELL / STRONG SELL /
AVOID. **Seven categories.** Where's the legend? Where's the hover
tooltip? "What do these mean?" is the first question every user asks
and you don't answer it on canvas.

Add an inline help icon next to the column header that opens a small
popover explaining the rule. Or — better — when a user clicks an Action
chip, drill into that ticker with the matching rule highlighted in the
Drill-down's Rationale.

#### The Filters expander defaults open with 24 widgets.

Action multiselect (8 options) + Geo-only checkbox + Ticker multiselect
+ Min confidence selectbox + Search field + Data warnings checkbox.
Open by default. That's 24 controls competing with the table for
attention.

Default closed. Show the active-filter chips above the table when any
are set. Linear-style: "**3 filters active** · clear all".

#### The Backtest tab is unmarketed.

"Run backtest" — a dead button that gives nothing until you push it.
**Pre-render a default backtest on page load** (ZIM, 5y, default
costs). Show the equity curve, the Sharpe, the trade count. The button
becomes "Re-run with current settings". This is the difference between
"interactive demo" and "fill-in-this-form".

#### Route Lab is your hero feature, buried.

I cannot stress this enough. **The Cape-vs-Suez calculator with
break-even AWRP is the only feature in this entire product that nobody
else has.** It's also tab #6, with five sub-tabs the user has to
discover, with 21 inputs spread across 5 columns on the first sub-tab.

Fix path:
1. Promote it to tab #3 ("Route Lab"), one position right of "Drill-down".
2. The Scenario sub-tab opens with the cost breakdown ALREADY SHOWN at
   the top. Inputs go BELOW the result, not above. Result-first design.
3. Compress 21 inputs into a single "Edit scenario" expander. Above it,
   a one-line scenario summary: *"VLCC, 300k mt cargo, IFO380 @ $694,
   $100k/d charter, no scrubber. Suez wins by $946k."*
4. The four break-even metrics get a custom 4-up card with brass
   dividers, not stock Streamlit `st.metric`. Make this the screenshot
   that ends up on Twitter.

#### Loading state is dev-flavoured.

> "Loading watchlist (price + fundamentals + news)…"

The user does not care which providers are stitched. Shorten:

> "Loading shipping market…"

#### "Refreshed UTC: 20:45:14" — wrong timezone, wrong format.

User in New York sees `20:45:14` and thinks "is that my time? UTC?
which is which?" Standard friendly form: **"updated 2 minutes ago"**.
Cache the absolute timestamp in a tooltip on hover.

#### No CTA. Anywhere.

Linear's marketing has one button. Vercel has one. Superhuman has one.
This dashboard has zero. The user lands, scrolls past 6 metric cards,
hits a 17-column table, and then... what? **What does success look
like for a visitor at minute 2?**

Add three CTAs in the right order:

1. **Hero, top-right corner.** Small `★ Star` and `⤴ Fork` GitHub badges.
   Replaces the Datadog-widget data-health box.
2. **End of Overview tab.** A single brass-accent button: *"Try the
   Route Lab →"*. This is your conversion moment.
3. **Footer.** *"Deploy your own copy"* link to README's deployment
   section.

#### Disclaimers everywhere = trust nowhere.

Count them on a single page: footer "Not investment advice", demo info
banner "📦 Demo mode — using bundled synthetic sample data", drill-down
"⚠️ Risk:", drill-down "ℹ️ Data quality:", Route Lab "⚠️ This model is
an analytical calculator. It is not routing advice...". Five different
hedges in one screen.

The cumulative signal is: *"the authors are nervous and you should be too."*

Consolidate to ONE legal-disclaimer link in the footer ("Disclaimer")
that opens a modal. In-line warnings should be SPECIFIC and ACTIONABLE
("EU ETS coverage is 0% for this voyage — EUA price input has no
effect"), not generic.

#### Plotly hover labels are dark-on-dark by default.

Check the Backtest equity curve in Chrome. If a user hovers, do they
see legible numbers? Did `apply_theme` set `hoverlabel.bgcolor` and
`hoverlabel.font.color`? If not, fix. (You did set this — verify it's
actually applied to the equity-curve figure since it has multiple
traces.)

#### Mobile is broken.

Streamlit's wide layout + 6-column metric strip + horizontal 7-tab bar
+ a hero ship absolutely-positioned at `right: 6%` = unusable on a
phone. The ship overlaps the H1 below 480px viewport.

You're never going to make this product great on mobile because the
underlying tables don't fit. **Detect narrow viewports and show a
"Best viewed on desktop" interstitial with a "Continue anyway" button
and a link to a Twitter thread that summarises the latest signals.**
Ship with grace.

#### `Drill-down` is data, not story.

User picks ZIM. Sees: action card · confidence card · signal score
card · risk score card · paragraph of rationale · risk warning ·
data warning · price chart · volume chart · drawdown chart · 7-key
indicator panel · 6-key fundamental panel · headlines table.

That's **13 surfaces** before the user gets a takeaway. Linear's PR
detail page has THREE: title, body, sidebar.

Lead with one bold sentence:

> **ZIM is in a downtrend with high leverage and no recent positive
> news. The model rates it SELL with high confidence.**

Everything else is supporting evidence. The data is fine; the
hierarchy is wrong.

#### Top-constructive / Most-cautionary lists aren't tap-targets.

You wrote bulleted markdown for them. They should be card buttons that
jump to the Drill-down for that ticker with the rationale pre-expanded.
You're 30 minutes of work away from a much better UX.

#### Captions in `--text-muted` (#93A4BD) on `--bg-deep` (#07101F).

That's a **3.7:1 contrast ratio**. Below WCAG AA for body text (needs
4.5:1). Bump muted text to `#A8B6CC` (4.8:1) for everything that's
informational, not decorative.

---

## PASS 2 — First-Time User Walking Through

(I'm pretending I'm a hedge-fund analyst who got the link from a
maritime ops friend. I have a Bloomberg terminal in another window and
limited patience.)

**:01** — Page loads. Pretty hero. Ship is bobbing. Title says "Open
Maritime Quant Dashboard". OK, what does it do?

**:04** — Reading the tagline. "Maritime equity monitoring · shipping
& freight proxy · news and geopolitical risk · transparent rule-based
scoring · honest backtests." That's a lot of "and"s. I still don't
know what *I* would use this for.

**:07** — Notice "DEMO" badge. Cool. Next to it on the right: "Data
health: OK · Refreshed UTC: 14:30:22". So... it's working. Why is the
website telling me its server is up?

**:11** — Below the hero: "📦 Demo mode — using bundled synthetic
sample data. No live providers are being called. Set NEWSAPI_KEY and
APP_MODE=live (or auto) to use real data." OK so it's a demo. But the
mode badge ALSO told me that. Why twice? Also: I don't know what an
APP_MODE is and I'm not setting one.

**:18** — Six metric tiles. BDRY $17.92, BDRY 20d -22%, BDI Trend
FALLING, Tickers 6, Failed 0, Geo alerts 1. I know what BDRY is
(thank god). What's a "Geo alert"? Is 1 a lot?

**:25** — "Signal distribution" bar chart. HOLD: 5, MOMENTUM BUY: 1.
Hmm. So 5 of 6 stocks are HOLD. Is that bad? Is HOLD the default? Did
the model fail?

**:34** — "Sub-scores by ticker" — three colored bars per ticker. I
don't know what Tech / Fund / News scores are. There's no axis hint
that they're [-1, +1].

**:42** — "Top constructive" and "Most cautionary" sections. OK these
are useful. SBLK is constructive, ZIM is cautionary. I want to click
SBLK. **Wait, I can't click them.** They're plain text. OK I'll go up
and click the Drill-down tab. (Unnatural — I'd expect them to be
links.)

**:55** — Drill-down. I have to pick a ticker from a select box.
Re-pick SBLK. See: Action MOMENTUM BUY, Confidence high, Signal +0.34,
Risk 0.10. Then a paragraph of "Rationale". Then "**Data quality:**
Missing fundamentals: P/B, EV/EBITDA". OK so it's missing data but
also the action is MOMENTUM BUY high-confidence? **How can it be high
confidence with missing fundamentals?** This makes me distrust the
score.

**1:14** — Price chart. Pretty. Three SMAs. I expected a tooltip on
hover with the close price. Hover doesn't seem to give me one. (Maybe
it does — I might have missed it because the hover label was dim.)

**1:27** — Scrolling, I see a Volume chart, then "Drawdown chart" in
an expander. I open it. Helpful but I don't know if a -8% drawdown is
typical for a tanker.

**1:35** — Indicators / Fundamentals panels. Just key-value JSON.
"Trend: downtrend" sits next to "20d Vol: 35%". I have no anchor for
whether 35% vol is high or low for shipping.

**1:48** — Headlines table. Three sample headlines with `(synthetic
sample for demo mode — not real news)`. Is the synthetic note in
EVERY headline? That's noisy.

**2:04** — I notice "🛳️ VLCC Route Lab" tab. Click it.

**2:10** — "Cape vs Suez · Editable voyage-economics calculator for a
Persian Gulf → Singapore VLCC. Defaults are an analyst scenario, not
live market data. This is not routing, insurance, legal, or investment
advice."

That's three disclaimers in two sentences. I'm going to leave.

**2:18** — But OK, I scroll. Five sub-tabs. I pick Scenario. I see 21
input fields in a grid. **There's no result anywhere on this sub-tab.**
I change "Charter rate" from 100,000 to 60,000 — nothing happens
visually. Where did my change go? Did it save?

**2:35** — I go to Cost Breakdown sub-tab. NOW I see all-in totals,
pre-insurance, break-even AWRP, break-even combined. Big numbers. But
I have to switch tabs to do my edit-then-see-result loop. I will only
do this twice before giving up.

**2:50** — Sensitivity. Heatmap. Cool. Numbers update when I change
charter rates and fuel prices. This is the best feature so far.
**This should have been the landing screen.**

**3:08** — Regulation. ETS coverage 0%. OK. The text actually
explains why — that's the first useful prose I've read.

**3:18** — Assumptions & Sources. Long table with chips. Useful that
you flag user_input vs analyst_default. But the per-row "source" text
is too small.

**3:30** — I go back to Overview to leave. I think the product is
interesting but I'm not sure WHY I'd use it next week. I won't star
the GitHub repo because I don't know there is one.

---

## Consolidated audit, sorted by severity

> Ready to feed straight to Claude Code. Each item names the file and
> a one-line spec.

### CRITICAL

#### C1. Hero has no value proposition.

- **File:** `dashboard.py` (hero block)
- **Spec:** Replace the bullet-list tagline with a single 16–18px
  sentence: *"Open-source maritime equity intelligence — built for the
  night shift."* Below it, three small metadata items in a row:
  `MIT-licensed · Open source · Demo mode included`. The current data-
  health/refresh stamp moves to the Data Health tab.

#### C2. Mode badge is too subtle for non-technical visitors.

- **File:** `dashboard.py` (hero badge), Plotly chart canvases.
- **Spec:** Expand the DEMO badge text to `DEMO · synthetic data`. Add
  a 5%-opacity diagonal `DEMO DATA` watermark `<text>` element to every
  Plotly chart canvas when `mode == "DEMO"`. Wire via `theme.apply_theme`
  taking an optional `demo_watermark=True` argument. Skip the watermark
  in LIVE mode.

#### C3. Top-tabs include the differentiated feature too far right.

- **File:** `dashboard.py` (tab definitions, line ~217).
- **Spec:** Reorder to `Markets | Drill-down | Route Lab | Backtest |
  News | Health`. Collapse the current Overview + Watchlist into a
  single "Markets" tab where the top half is the existing Overview and
  the bottom half is the table. "Data Health" remains accessible but
  becomes the rightmost tab and renders a compact status block.

#### C4. Sidebar leaks dev plumbing into the user surface.

- **File:** `dashboard.py` (sidebar block).
- **Spec:** Delete the env-var caption block. Replace
  "NewsAPI key detected/No NewsAPI key set" with `Live news: on/off`.
  Move "News window (hours)" out of the sidebar into the News tab as a
  segmented control (24h / 72h / 7d). Auto-refresh checkbox stays but
  switch the implementation from `<meta http-equiv='refresh'>` to a
  `st.rerun()` call inside `st.empty()` to preserve in-progress inputs.

#### C5. Route Lab inputs first, results buried.

- **File:** `dashboard.py` (VLCC Route Lab block).
- **Spec:** Render the four-up break-even card AT THE TOP of the
  Route Lab landing, before any sub-tabs. Wrap the 21 inputs in a
  single `st.expander("Edit scenario", expanded=False)`. Above the
  inputs, a one-line summary: *"VLCC, 300k mt cargo, IFO380 @ $694,
  $100k/d charter, no scrubber. Suez wins by $946k."* Cost breakdown,
  Sensitivity, Regulation, and Sources remain as sub-tabs but are
  reachable via in-page anchor links from the four-up card.

#### C6. Action chip semantics are unexplained.

- **File:** `dashboard.py` (Watchlist column header), `signals.py`.
- **Spec:** Add an info icon (ℹ︎) next to the "Action" column header
  that opens a popover with a 7-row table: label · trigger condition ·
  one-sentence rule. Reuse the rules from `signals._label_from_scores`.
  Also wire each Action chip in the table as a click target that opens
  the Drill-down for that ticker.

#### C7. Disclaimers competing for trust.

- **File:** `dashboard.py` (footer, drill-down, Route Lab Assumptions,
  demo banner).
- **Spec:** Consolidate every "Not advice" disclaimer into one footer
  link `Disclaimer` that opens an `st.dialog` (or `st.expander`) with
  the consolidated legal copy. Remove inline "Risk:" / "Data quality:"
  banners from Drill-down — replace with a single chip row at the top
  of the Drill-down: `⚠ 1 risk · ℹ 2 data warnings` clickable to expand.
  Keep the demo banner ONLY when `mode == "DEMO"`.

#### C8. Loading state names internal providers.

- **File:** `dashboard.py` (cached_watchlist spinner).
- **Spec:** Change `"Loading watchlist (price + fundamentals + news)…"`
  to `"Loading shipping market…"`. Provider-level breakdown moves to
  the Data Health tab only.

### HIGH

#### H1. No CTAs anywhere.

- **File:** `dashboard.py` (hero right corner, end of Overview/Markets,
  footer).
- **Spec:** Add three buttons:
  1. Hero top-right: `★ Star on GitHub` and `⤴ Fork` as outlined chips
     pointing at the repo URL. Replaces the data-health stamp.
  2. End of Markets tab: a single brass-accent primary button
     `Try the Route Lab →` that switches tabs via `st.session_state`.
  3. Footer: `Deploy your own →` linking to README#deployment.

#### H2. Backtest tab is dead until clicked.

- **File:** `dashboard.py` (Backtest tab).
- **Spec:** Pre-render a default backtest (ZIM, 5y, default costs)
  cached for 1h. Show equity curve + the four headline metrics on
  page load. The button label becomes "Re-run with current settings".

#### H3. Auto-refresh nukes in-progress inputs.

- **File:** `dashboard.py` (auto_refresh `<meta>` tag).
- **Spec:** Replace the meta-refresh with a polling pattern that calls
  `st.cache_data.clear(); st.rerun()` every 5 minutes only when the
  Markets tab is active and the user has been idle (no widget change in
  the last 30s). Detection via `time.monotonic()` stamps in
  `st.session_state`.

#### H4. Drill-down has 13 surfaces, no headline insight.

- **File:** `dashboard.py` (Drill-down tab).
- **Spec:** Lead with a single 18px sentence summarising the action:
  *"`{ticker}` is in a {trend} with {risk} risk. The model rates it
  `{action}` with {confidence} confidence."*
  Synthesised from the existing SignalResult fields. The four metric
  cards become a compact 4-up underneath, not in the spotlight.

#### H5. Top-constructive / Most-cautionary aren't clickable.

- **File:** `dashboard.py` (Overview / Markets).
- **Spec:** Render each row as an `st.button` (transparent style) that
  sets `st.session_state.drill_ticker` and calls `st.switch_page` or
  `st.session_state.active_tab = "drill"` then `st.rerun()`.

#### H6. Action chip palette is loud against the new dark surface.

- **File:** Already partially addressed in `theme.ACTION_BADGE`.
  Audit every place ACTION_COLORS solid hex is still used in `go.Bar`
  marker.color and replace with desaturated equivalents.
- **Spec:** Use `theme.ACTION_BADGE[label][2]` (the text color) for
  bar fills with 0.6 alpha instead of the saturated ACTION_COLORS hex.

#### H7. Mobile layout collapses.

- **File:** `dashboard.py` CSS block; Streamlit `set_page_config` cannot
  fix this fully.
- **Spec:** Add a `@media (max-width: 720px)` block that:
  - hides `.om-ship` (or scales to 50%);
  - reflows the metrics row to 2-column grid;
  - sets `.block-container { padding: 0.5rem; }`;
  - converts the seven-tab list into a `<select>`-style dropdown via
    `[data-baseweb="tab-list"] { overflow-x: auto; }` with a hint shadow.
  Also add a top banner under 600px viewport: *"This dashboard is
  designed for desktop. Tap to continue, or open on a larger screen."*

#### H8. Filters expander defaults open with 24 controls.

- **File:** `dashboard.py` (Watchlist Filters expander).
- **Spec:** Default `expanded=False`. Above it, render a chip row
  showing active filters (`Action: 3 · Min confidence: medium · Geo
  Alert`). The chip row includes a `Clear filters` link.

#### H9. Caption / muted text fails WCAG AA.

- **File:** `theme.py` (`TEXT_MUTED`), `dashboard.py` CSS.
- **Spec:** Bump `--text-muted` from `#93A4BD` to `#A8B6CC`. Verify
  with a contrast checker against `#07101F` (target ≥ 4.5:1). Update
  `theme.TEXT_MUTED` to match.

#### H10. Refreshed timestamp is unfriendly.

- **File:** `dashboard.py` (hero status), `maritime_data.py`
  (`refreshed_at`).
- **Spec:** Render as relative ("updated just now / 2 minutes ago")
  using a tiny helper. Absolute UTC timestamp moves to the title
  attribute on hover.

#### H11. "Configure via environment" caption is dev-leakage.

- **File:** `dashboard.py` (sidebar bottom caption).
- **Spec:** Delete. The README and `docs/PUBLISHING.md` already cover
  env-var setup.

#### H12. Sub-scores chart has no axis legend or unit hint.

- **File:** `dashboard.py` (Overview/Markets, sub-scores bar).
- **Spec:** Add `range=[-1, 1]` and a centred horizontal annotation
  "score · range −1…+1" below the chart caption. Add hover labels per
  bar with the trigger reason.

#### H13. Headlines tagged "(synthetic sample for demo mode — not real
news)" on every row.

- **File:** `sample_data/news.json`, `dashboard.py` (News tab render).
- **Spec:** Move the synthetic note out of the description field; add
  a single banner above the headlines table when `mode == "DEMO"`:
  *"Synthetic sample headlines · for product demonstration only."*

### NICE TO HAVE

#### N1. First-visit "What's this?" tour.

- **File:** new `dashboard.py` first-paint detection.
- **Spec:** On first session (`st.session_state` is empty), show a
  three-step `st.dialog`: 1) what the dashboard does, 2) Demo vs Live,
  3) where to start (Route Lab). Dismissible; never shown again in the
  session.

#### N2. Cmd-K palette.

- **File:** new component, `static/cmdk.html`.
- **Spec:** A small inline JS-free `<details>` toggled by a keyboard
  shortcut hint in the footer (`⌘K`). Out of scope for v0.5; revisit
  in v0.6.

#### N3. Route Lab scenario save/share via URL.

- **File:** `dashboard.py` (Route Lab), `route_economics.py` already
  has `RouteScenario.to_dict`.
- **Spec:** Encode current scenario as a base64 query param, restore
  on page load if present. Add a "Copy link to scenario" button.

#### N4. Export Route Lab analysis as a PNG card.

- **Spec:** Use Plotly's static export to PNG (`fig.write_image`) for
  the four-up card + cost breakdown. One-click "Share this scenario"
  download. Adds a `kaleido` dependency — out of scope unless requested.

#### N5. Drill-down rationale → benchmark context.

- **File:** `signals.py` (rationale generation).
- **Spec:** Add per-metric anchors ("20d vol 35% — typical range for
  tankers is 25–55%"). Hardcoded sector defaults are fine for v0.6.

#### N6. Empty state polish.

- **File:** `dashboard.py` (each tab).
- **Spec:** When data is empty, show a centred muted line and a
  small actionable hint, not a red `st.error`.

#### N7. Top-of-fold ship persists on scroll.

- **File:** `dashboard.py` CSS.
- **Spec:** Add a 32px ship icon to the page-top sticky bar so the
  brand mark is visible after scroll. Currently the ship disappears.

#### N8. Light-mode toggle.

- **Spec:** Skip. Maintaining two themes doubles the styling surface.
  Let users invert at the OS level.

---

## Acceptance criteria for the next pass

A new visitor should:

1. In **30 seconds**, know what the product is, who it's for, and that
   they're seeing demo data.
2. In **90 seconds**, have clicked into the Route Lab and seen the
   four-up break-even card with the differential prominently rendered.
3. In **2 minutes**, see a clear next action (`★ Star`, `⤴ Fork`,
   `Deploy your own`).
4. **Never** see the words "APP_MODE", "NEWSAPI_KEY", or "Configure
   via environment" on the canvas.
5. **Never** be unable to tell whether the numbers are real or synthetic.

---

## Notes on what's already good (don't regress)

- Animated tanker silhouette + night sky.
- Tabular numerals on metrics.
- Hairline borders, no drop shadows.
- Underline-style active tab indicator.
- Plotly theming via `apply_theme`.
- Route Lab's break-even-combined number ($1,795,886) matches the
  teammate brief — that's a credibility win, surface it harder.
- Doctor + security-check scripts. (No UI work needed; these stay
  CLI-only.)

If the next pass touches any of the above, push back on the diff.
