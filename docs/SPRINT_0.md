# Sprint 0 — Validation & Setup (Week 0)

> **Goal:** before writing a single line of paid-product code, validate the
> pricing hypothesis and stand up the infrastructure accounts. Cost: ~€50
> in domain + a weekend of signups. Output: a real go/no-go signal on whether
> Sprint 1 should start.

---

## 1. Decision-gate confirmation

Print this section. Sign it (mentally is fine). If any answer is "no, but…",
go back to the Roadmap Part 12 alternatives.

```
[ ]  1. I commit 24-30 months full-time to this.
[ ]  2. I will raise €500k+ pre-seed within 6 months OR self-fund €100k+.
[ ]  3. I have or can recruit a maritime industry advisor.
[ ]  4. I accept Phase 0 ships a beta — no €200/mo customers yet.
[ ]  5. I can tolerate ~€20k/month burn from month 6.
[ ]  6. I target €30-100M ARR; unicorn is upside, not base case.
[ ]  7. I drop retail investors as a target ICP.
[ ]  8. I price at €99 / €499 / €2500 — not €200.
[ ]  9. I rebuild off Streamlit by end of Phase 1.
[ ] 10. I will pay for SOC 2 (~€25-50k) by month 18.
```

If 8/10+ are checked → continue. If <8 → re-read Roadmap Part 12.

---

## 2. Infrastructure accounts (~2 hours)

Sign up for these. All free tier; no payment needed yet.

| Service | URL | Purpose | Phase |
|---------|-----|---------|-------|
| Clerk | clerk.com | Auth | Sprint 1 |
| Stripe | stripe.com | Billing | Sprint 2 |
| Stripe Tax | stripe.com/tax | EU VAT | Sprint 2 |
| Render | render.com | Hosting | Sprint 1 |
| Neon | neon.tech | Postgres | Sprint 1 |
| Upstash | upstash.com | Redis | Sprint 4 |
| Sentry | sentry.io | Errors | Sprint 6 |
| Resend | resend.com | Email | Sprint 4 |
| Vanta | vanta.com | SOC 2 | Phase 1 |
| Plausible | plausible.io | Analytics (privacy-first, no cookie banner needed) | Sprint 5 |

**Domain:** register `openmaritimequant.com` on Cloudflare or Namecheap (~€12/yr).
If taken, alternatives: `omq.io`, `maritimequant.com`, `tankerlab.app`.

---

## 3. The pricing-test landing page (~1 day)

Before writing any product code, validate that someone will pay.

### Build

A single HTML page (or one Next.js route) at `openmaritimequant.com`. No
backend. Three sections:

```
Hero:
  Open Maritime Quant
  Maritime equity intelligence — built for the night shift.
  [Get early access — €99/mo]

What it does (3 bullet points, no jargon):
  - Score 6 major shipping equities on a transparent rule set
  - Cape vs Suez voyage economics with break-even AWRP solver
  - Honest backtests with no lookahead bias

Pricing:
  ANALYST          €99/mo    [Get started]   ← Stripe Checkout link
  PROFESSIONAL     €499/mo   [Talk to us]    ← mailto: link
  TEAM             €2,500/mo [Talk to us]    ← mailto: link

Footer:
  Open source · MIT · GitHub link · X / LinkedIn
```

### What you're testing

For each price point, run a 1-week ad / post on:

- LinkedIn: post once, boost to "shipping & maritime" + "hedge funds" audience, €100 budget
- /r/algotrading: organic post (don't pitch — show the Route Lab screenshot, mention pricing in comments)
- HN: Show HN, link to GitHub repo, mention paid version in comments
- Twitter/X maritime-finance accounts: 3-5 thoughtful posts a week

### Validation thresholds

- ≥3% of landing-page visitors click the "Get started" button → pricing is right
- ≥1 person actually completes Stripe Checkout (charge them, then refund — you're testing intent, not stealing) → STRONG signal
- Zero clicks across 500 visitors → drop tier price 30% and retry

If after 4 weeks of running this you have **0 paying intent**, the ICP
hypothesis is wrong. Halt. See Roadmap Part 12.

---

## 4. Pre-seed deck v1 (outline)

12 slides. Don't make it pretty in week 0; make it true.

```
Slide 1 — Title
  Open Maritime Quant
  Maritime equity intelligence for the night shift.
  [Founder name] · [date] · [contact]

Slide 2 — Problem
  Hedge funds with shipping exposure rely on Bloomberg + back-of-envelope
  spreadsheets to size positions in ZIM, Frontline, Star Bulk.
  Veson and Clarksons own the operations side; nobody owns the equity side.
  Cape-vs-Suez decisions: paper-and-pencil math at €100k stakes.

Slide 3 — Solution
  One screen: live shipping equity scoring + voyage economics calculator.
  Open-source distribution; paid live data + alerts.
  [Screenshot of the Route Lab.]

Slide 4 — Why now
  - EU ETS extended to maritime (2024) → new compliance complexity
  - Houthi disruption (2024-now) → war-risk premiums material to P&L
  - Shipping equity volatility (ZIM, Frontline, etc.) attracted hedge fund capital
  - Bloomberg lacks maritime-specific scoring; specialised tools cost €5-50k/seat

Slide 5 — Product
  - Watchlist scoring (rule-based, transparent)
  - Cape vs Suez voyage economics with break-even AWRP solver
  - Honest backtests
  - Real-time alerts; REST API for quants
  [3 screenshots]

Slide 6 — Differentiation
  - Only equity tool with VLCC voyage economics built in
  - Open-core: free OSS funnels paid customers (60% of conversions)
  - Transparent rule-based signals (vs black-box ML competitors)

Slide 7 — Market
  TAM: €1.5-3B (maritime data + analytics, global)
  SAM: €200-400M (commodity-trading desks + maritime-aware funds + war-risk
       underwriters)
  SOM (5 yr): €30-100M

Slide 8 — Business model
  ANALYST €99/mo · PROFESSIONAL €499/mo · TEAM €2,500/mo · ENTERPRISE €60k+/yr
  Open-core funnel; SOC 2 by month 18.

Slide 9 — Traction (Sprint 0 results)
  [Fill in after running pricing-test landing page for 4 weeks]
  - X visitors / Y signups / Z paying customers
  - GitHub: A stars, B forks
  - Design partners: list of 3-5

Slide 10 — Team
  Founder: [you] — [maritime / quant / engineering credentials]
  Advisor: [name] — [maritime industry connection]
  (Hiring: senior eng + sales rep at seed)

Slide 11 — Roadmap
  Phase 0 (now): paid beta, 5-15 customers
  Phase 1 (months 3-9): production stack, €25k MRR
  Phase 2 (months 9-18): underwriter ICP, €100k MRR, Series A
  Phase 3 (18+): platform, €500k+ MRR

Slide 12 — Ask
  Raising €500-800k pre-seed
  Use of funds: founder salary 12mo + 1 senior eng + €40k data licences + €25k legal/compliance
  Valuation: €3-5M post-money
  Closing: [target date, ~3-4 months out]
```

Render it in Google Slides. Don't pay for templates yet. Iterate after 5
investor calls.

---

## 5. Three target hedge-fund analysts (template)

Find by name. Use LinkedIn Sales Navigator (free trial) or just LinkedIn search.

Filters that work:
- Title: Analyst, Senior Analyst, PM
- Industry: Hedge Fund, Asset Management, Investment Management
- Keywords (in profile): "shipping" OR "tankers" OR "maritime" OR "ZIM" OR "Frontline" OR "Maersk"
- Geography: NYC, London, Singapore, Geneva, Dubai

Fill in 3 specific names below. These are your design-partner targets.

```
Target 1
  Name:
  Title:
  Fund:
  Why them (1 sentence — public position in shipping, recent quotes, etc.):
  How you'll reach them (warm intro / cold LinkedIn DM / mutual contact):

Target 2
  Name:
  Title:
  Fund:
  Why them:
  How you'll reach them:

Target 3
  Name:
  Title:
  Fund:
  Why them:
  How you'll reach them:
```

### Cold-DM template

```
Subject: 5-min question about ZIM / shipping coverage

Hi [name],

I'm building an open-source maritime equity dashboard with a Cape-vs-Suez
voyage-economics calculator (break-even AWRP solver, EU ETS scope handling).
GitHub: [link]

You've been quoted on shipping equities — would you have 15 min to tell me
what's missing from your current Bloomberg + spreadsheet stack? No pitch,
just learning what would actually be useful.

Thanks,
[your name]
```

Send to all three. Aim for 1 reply. The reply is the start of design partnership.

---

## 6. Exit criteria for Sprint 0

You're allowed to start Sprint 1 only if:

- [ ] 8/10 decision-gate items confirmed
- [ ] All free-tier infra accounts created
- [ ] Domain registered
- [ ] Pricing-test landing page live for ≥1 week
- [ ] ≥1 of three target analysts replied (any reply, even "not interested")
- [ ] Pre-seed deck v1 in Google Slides

If by end of week 2 you don't have ≥1 analyst reply, your outreach is the
weak link. Get a warm intro (industry advisor, ex-colleague, alum network)
before continuing. **Do not start Sprint 1 without a design-partner conversation
booked.**

---

## 7. Out-of-scope for Sprint 0

Don't do these yet — they wait for later sprints:

- Building Clerk integration (Sprint 1)
- Stripe Checkout in the app (Sprint 2)
- Bunker price scraper (Sprint 3)
- Email alert system (Sprint 4)
- Marketing site beyond a single pricing page (Sprint 5)
- Hiring an engineer (post-pre-seed, ~month 3)
- SOC 2 evidence collection (month 6)
- Argus / Baltic Exchange contract negotiations (month 4)

Sprint 0 is **founder time**, not engineering time. Resist the urge to code.

---

**Sprint 0 effort:** ~25 hours over 1-2 weeks.
**Sprint 0 cost:** €12 (domain) + €100 (LinkedIn ad budget) = ~€112.
**Sprint 0 output:** validated pricing OR proven-wrong hypothesis. Both are wins.
