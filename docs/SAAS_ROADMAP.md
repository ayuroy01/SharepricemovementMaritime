# Open Maritime Quant — SaaS Roadmap

> **Status: PROPOSED · awaiting founder approval before any building begins.**
> This document is the single source of truth for converting the current
> open-source dashboard into a paid B2B SaaS product. Every decision below is
> deliberately locked-in so a future engineer (or a smaller-model AI) can
> execute Phase 0 without re-deriving the strategy.
>
> Author's note: I am writing this on **maximum reasoning capability** to make
> the document self-sufficient. The founder explicitly asked for a plan that
> downstream sessions can execute on a lower-tier model without quality loss.
> Anywhere I had to choose between two options, I picked one and called it
> out — see "Decision log" at the bottom.

---

## TL;DR (read this first — 3 pages)

### What we have today

A polished open-source maritime dashboard. Streamlit front end, Yahoo Finance
+ NewsAPI free tiers, a transparent rule-based equity scorer, and a genuinely
differentiated VLCC voyage-economics calculator. Nice product. Zero monetisation
infrastructure, zero auth, zero data partnerships, zero defensible moat.

### What "€200/month premium SaaS" actually requires

You cannot charge €200/month on free Yahoo + NewsAPI. The four customers you
listed (retail, shipowners, underwriters, real-time-data buyers) need
fundamentally different things. Some of them won't pay €200/mo (retail, small
shipowners). Others will pay 10× that (war-risk underwriters, hedge funds with
maritime exposure) — but only with paid data feeds, SLAs, audit trails, and
workflow integrations the current product does not have.

### The honest unicorn assessment

- **TAM ceiling.** Maritime SaaS is bounded. Veson Nautical (the category
  leader) is ~$200M ARR after 25 years. MarineTraffic Enterprise is similar
  scale. Sea/, ShipNet, Q88 are all sub-unicorn. Pure-play maritime is a
  €500M-ARR ceiling business unless you go horizontal.
- **Two paths to €1B valuation:** (a) become the *operating system* for one
  vertical (Veson's playbook for charterers), or (b) extend beyond maritime
  into broader commodity logistics + AI productivity.
- **Realistic outcome:** €30-100M ARR business in 5-7 years is achievable.
  Unicorn requires either AI-driven productivity claims that 10× analyst
  output, or platform extension into adjacent verticals. **You should plan
  for the €30-100M ARR business and treat unicorn as upside, not target.**
- **Time to first paying customer:** 6 months from sprint 1.
- **Time to €1M ARR:** 18-24 months.
- **Capital required:** €500k pre-seed → €3M seed → €15M Series A. Total
  dilution to Series A: 35-45%.

### Strategic decisions I am making for you (override if you disagree)

1. **DROP retail investors as a target.** They will not pay €200/mo for niche
   maritime. TradingView at €30/mo eats this market. Save the marketing spend.
2. **DROP small shipowners as Phase-1 target.** Their tools (Veson, ShipNet,
   Q88) have 10-year switching costs and they are notoriously slow buyers.
   Revisit in Phase 3.
3. **PRIMARY ICP: hedge funds + commodity traders with maritime exposure.**
   Highest revenue per seat (€500-2500/mo viable), fastest sales cycle
   (4-12 weeks), best fit for the differentiated Route Lab.
4. **SECONDARY ICP: war-risk underwriters and marine insurers.** High value,
   relationship-driven sale, longer cycle (3-6 months) but stickier.
5. **Pricing skips €200/mo.** €99 (analyst seat) → €499 (pro seat) →
   €2,500/mo (team) → custom enterprise. The €200 mid-tier is dead-zone.
6. **Engineering: rebuild off Streamlit by end of Phase 1.** Streamlit caps
   at ~$1M ARR; $10M+ requires Next.js + FastAPI + Postgres. **Phase 0 keeps
   Streamlit** to reach paying-customer status fast; Phase 1 adds the
   production stack alongside; Phase 2 retires Streamlit.
7. **Data strategy: paid licences are the second-largest line item after
   payroll.** Budget €150-400k/year for Argus/Platts (bunkers), Baltic
   Exchange (freight indices), MarineTraffic (AIS), VesselsValue (vessel
   prices). Without these you cannot charge €200/mo with a straight face.
8. **Compliance: SOC 2 Type 2 by month 18.** Required for every enterprise
   sale. Start Type 1 at month 6.

### Founder decision gate (do these BEFORE any sprint starts)

You must answer YES to all of these or the plan falls apart. If any answer
is NO, the realistic alternative is "open-source project + consulting", not
"SaaS unicorn".

- [ ] Will you commit 24-30 months full-time? (Solo founder runway minimum.)
- [ ] Are you willing to raise €500k+ in pre-seed within the next 6 months?
- [ ] Do you have (or can recruit) a maritime industry advisor with broker
      / charterer / underwriter relationships? (Sales without this is
      essentially impossible for the primary ICP.)
- [ ] Do you accept that Phase 0 (next 90 days) ships a polished beta — not
      a finished product — and that NO ONE will pay €200/mo for Phase 0?
- [ ] Can you tolerate burning ~€20k/month from month 6 onwards on data
      licences, hosting, and a junior engineer's salary, before revenue
      crosses break-even?
- [ ] Are you OK targeting a €30-100M ARR business with unicorn as upside,
      not as the base case?

If all six are YES → proceed to Part 1 and execute Phase 0 sprint plan.
If any is NO → see "Alternative paths" at the bottom.

---

## Part 1 — Reality check (the gap between today and €200/mo)

### What today's product is, structurally

```
single Streamlit process
  → reads from yfinance (free, unstable)
  → reads from NewsAPI free tier (dev-only by ToS)
  → reads from BDRY ETF (proxy, not BDI)
  → renders charts in-process
  → no auth, no billing, no DB, no users, no API
```

### What a €200/mo product requires, structurally

```
multi-tenant SaaS
  → workspace-scoped data with role-based access
  → live paid data feeds with SLAs (Argus, Baltic, MarineTraffic, Platts)
  → real-time alerts (email, Slack, webhook, SMS)
  → public REST + WebSocket API for quants who want to plug in
  → audit log: every signal reproducible from inputs at the time
  → 99.9% uptime SLA, sub-minute data latency on price/AIS
  → SOC 2 + GDPR compliance
  → enterprise SSO (Okta, Azure AD, Google Workspace)
  → in-app billing (Stripe), usage metering, dunning
  → support tiers (community / business / enterprise)
  → backed-up databases, point-in-time restore, regional failover
```

The technical gap is roughly **18 months of focused engineering** with a team
of 3-5. The data-licensing gap is **€150-400k/year minimum** before you can
make uptime/quality claims.

### Why each of the four "not for" personas is actually possible to convert

| Persona | Today: not for | Phase to convert | Required |
|---------|----------------|------------------|----------|
| Retail investors | Won't pay €200; fake-trading-tool fatigue | **NEVER**. Drop. | n/a |
| Shipowner ops | Entrenched in Veson/Q88; 5-yr cycles | Phase 3 (year 3+) | Real integrations, real fleet workflow |
| War-risk underwriters | No claims data, no audit trail | Phase 2 (month 9-18) | Loss DB partnership, JWC feed, audit log |
| Real-time data buyers | Free-tier yfinance is unreliable | Phase 1 (month 3-9) | Argus + Baltic + MarineTraffic licences |

The realistic conversion order: **real-time-data buyers (hedge funds) →
underwriters → shipowners**. Retail is permanently out of scope.

### Why this is harder than it looks

Three buried difficulties most founders miss:

1. **Data licences are not just expensive — they are political.** Argus,
   Platts, and Baltic Exchange will negotiate against your customer base.
   They explicitly forbid redistribution; if you display their data you must
   verify each end-user has their own licence (sometimes) or pay a
   redistribution fee (always). Plan for 3-6 months of legal back-and-forth
   per provider.
2. **Maritime sales cycles are slow.** Even fast-moving hedge funds take 8-12
   weeks to onboard a new data source. Insurers take 6-9 months. Shipowner ops
   teams take 12-24 months. Plan cash-runway accordingly.
3. **The competition is invisible from outside the industry.** You will
   discover three competitors per persona who you have never heard of, all
   with €5M-50M ARR, all relationship-led, all incumbent. You will need
   industry insiders to find them.

### Why this is easier than it looks

- **The Route Lab is a real moat.** No equity dashboard offers
  Cape-vs-Suez break-even AWRP solving. Hedge funds with maritime exposure
  WILL pay for that calculation alone if it ships with paid bunker / freight
  data.
- **Open-source distribution is a wedge.** You already have a public repo.
  Convert OSS users to paid users via "open core": free tier stays open,
  premium features (live data, alerts, multi-user) are paid.
- **You don't need to be Veson on day one.** A focused €99/mo individual
  tier with real bunker prices, real freight rates, and the Route Lab is
  shippable in 90 days.

---

## Part 2 — Strategic decisions (locked, override only if you disagree)

### 2.1 ICP selection

| Tier | ICP | Profile | Pricing | Sales cycle | Phase |
|------|-----|---------|---------|-------------|-------|
| 1 | Hedge fund maritime analyst | $100M+ AUM fund with shipping exposure or commodity desk | €99/seat/mo | 4-8 weeks | Phase 1 |
| 2 | Multi-strat fund team | 3-15 analysts on a commodity / event-driven desk | €499/seat/mo + €2,500/team/mo | 8-16 weeks | Phase 1 |
| 3 | War-risk underwriter | Lloyd's syndicate, P&I club, marine insurer | €1,500/seat/mo | 12-26 weeks | Phase 2 |
| 4 | Enterprise (insurer, energy major, large operator) | 50+ seats | Custom (€60-300k/yr) | 6-12 months | Phase 3 |

**Anti-personas (do not target, do not pivot toward):** retail investors,
day-traders, crypto-curious folks, single-vessel shipowners. They will burn
your support team and never upgrade.

### 2.2 Pricing & packaging

```
COMMUNITY            FREE
  - Open-source repo (current state)
  - Demo data only
  - Self-hosted, no support

ANALYST              €99/seat/month, billed annual
  - Live yfinance + NewsAPI (with caveats stated)
  - Bunker prices via Ship & Bunker free feed
  - Watchlist + scoring + Route Lab
  - Email alerts, single-user only
  - Email-only support, 48h response

PROFESSIONAL         €499/seat/month, billed annual
  - Everything in Analyst
  - Argus or Platts bunker prices (paid feed)
  - Baltic freight indices (paid feed)
  - Real-time alerts (Slack, webhook)
  - REST API access, 1000 req/day
  - Backtest with custom factors
  - Slack support, 12h business-hour response

TEAM                 €2,500/month, billed annual, up to 5 seats
  - Everything in Professional
  - Shared workspace, comments, scenarios
  - Team-wide alert routing
  - REST + WebSocket API, 10k req/day
  - SAML SSO
  - Quarterly business review

ENTERPRISE           Custom, starts €60k/year
  - Custom seat count
  - Dedicated AIS feed integration (MarineTraffic/Kpler)
  - Vessel valuation feed (VesselsValue)
  - Loss/claims data integration (insurer-specific)
  - 99.9% SLA, dedicated infra, regional failover
  - Phone support, named CSM
  - Custom data ingestion (the customer's own private feeds)
  - Audit log retention >1 year
  - SOC 2 Type 2 attestation, GDPR DPA, optional on-prem
```

**Pricing levers if customers push back:** discount the annual prepay (15%),
offer 14-day trials (no credit card for ANALYST tier), grandfather early
customers at original pricing for 24 months.

### 2.3 Build vs partner vs buy

| Capability | Decision | Reasoning |
|------------|----------|-----------|
| Auth & user management | **Buy: Clerk** (or WorkOS for enterprise SSO) | Clerk gets you to MVP in 1 week. WorkOS handles SAML/SCIM at Phase 2. |
| Billing | **Buy: Stripe** | Industry standard. Add Stripe Tax for EU VAT compliance. |
| Hosting | **Buy: Vercel (frontend) + Render or Fly (backend)** | Avoid AWS until Series A. Migrate then. |
| Database | **Buy: Neon (Postgres)** | Serverless Postgres, branching for staging. |
| Cache / queue | **Buy: Upstash (Redis)** | Pay-as-you-go, no infra ops. |
| Background workers | **Build on Render Workers + Arq** | Lighter than Celery. Arq is async-native. |
| Observability | **Buy: Sentry + Axiom** | Cheap until $1M ARR. |
| AIS data | **Partner: MarineTraffic Enterprise** | Building this is impossible. |
| Bunker prices | **Partner: Ship & Bunker (free) → Argus/Platts (paid)** | Phase 0 free, Phase 1 paid. |
| Freight indices | **Partner: Baltic Exchange** | Required for credibility. €10-30k/yr. |
| Vessel valuations | **Partner: VesselsValue** | $20-50k/yr enterprise tier. |
| News | **Partner: NewsAPI Pro → Bloomberg/Reuters via partner** | Free-tier cannot ship to paid customers. |
| Suez tolls | **Build: SCNT calculator** | The formula is public; the input data (vessel net tonnage) is per-vessel. Build a calculator + scrape SCA circulars. |
| Sentiment | **Build initially with VADER → upgrade to FinBERT** | VADER is fine for MVP; FinBERT lift becomes worth it at Phase 2. |
| Compliance docs | **Buy: Vanta or Drata** | Auto-generates SOC 2 evidence. €15-25k/yr. |
| Email | **Buy: Resend (transactional) + Loops (marketing)** | Cheap, modern, founder-friendly. |
| CRM | **Buy: Attio** | Better than HubSpot for B2B SaaS. |

### 2.4 Engineering architecture (locked)

**Phase 0 stack (current → polished beta):**
- Streamlit (current dashboard, polished)
- Postgres for user accounts (Neon)
- Clerk for auth
- Stripe for billing
- Streamlit's `st.session_state` for app state
- Render for hosting
- Sentry for errors

**Phase 1 stack (production SaaS):**
- Frontend: Next.js 15 + React 19 + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + Pydantic v2 + SQLModel + Alembic migrations
- Database: Postgres (Neon prod, branching for staging)
- Cache/queue: Redis (Upstash)
- Workers: Arq (async background jobs) on Render Workers
- Auth: Clerk (B2B SSO via WorkOS at Phase 2)
- Billing: Stripe + Stripe Customer Portal
- Hosting: Vercel (frontend), Render (backend + workers), Neon (DB), Upstash (Redis)
- Observability: Sentry + Axiom (logs/traces) + BetterStack (status page)
- CI/CD: GitHub Actions → Vercel/Render auto-deploy on main, preview deploys on PRs
- Charts: Plotly (existing) → migrate to Tremor or Recharts at Phase 2 for native React
- Testing: pytest (existing), Playwright for E2E, Storybook for component library

**Phase 2 stack (enterprise-ready):**
- Add: WorkOS for enterprise SSO, Vanta/Drata for SOC 2 evidence
- Add: regional failover (multi-region Neon, Vercel Edge), point-in-time DB restore
- Add: dedicated VPC and private networking for ENTERPRISE tier
- Add: Snowflake or BigQuery for analytics warehouse (own data lake)
- Add: dbt for data transformations
- Migrate: hosting to AWS (RDS, ElastiCache, Fargate) or stay multi-cloud

### 2.5 Funding plan

| Round | Timing | Amount | Dilution | Use of funds | Valuation cap |
|-------|--------|--------|----------|--------------|---------------|
| Pre-seed | Month 0-3 | €500k-800k | 10-15% | Founder salary, 1 senior eng, data licences for MVP, legal | €3-5M post |
| Seed | Month 9-12 | €2-3M | 15-20% | 4-6 person team, sales hire, SOC 2 Type 1 | €15-25M post |
| Series A | Month 18-24 | €10-15M | 20-25% | Scale to 25 people, US expansion, SOC 2 Type 2 | €60-100M post |
| Series B | Month 36+ | optional | optional | Unicorn-track or organic growth | depends |

**Total dilution to Series A:** 35-45%. Founder retains 30-40% post-A.

**Investor archetype:**
- Pre-seed: maritime/logistics angels (find via Sea Ahead, Motion Ventures,
  Flexport's angel list), deep-tech VC associates (small checks).
- Seed: vertical SaaS specialists (e.g. Point Nine, Notion Capital, Accel
  Europe), maritime-focused funds (Motion Ventures, Pier 71).
- Series A: top-tier B2B SaaS firms (Insight, Bessemer, Index Ventures).

---

## Part 3 — Phased roadmap

Five phases. Each has explicit entry criteria, deliverables, exit criteria,
and a kill-switch ("if we miss X by month Y, halt and replan"). All durations
are working months, not calendar.

### Phase 0 — Foundation (months 0-3)

**Goal:** Convert open-source dashboard into a credible paid-beta with
auth, billing, and at least one paid data feed. Get to first €1 of revenue.

**Entry criteria:**
- Founder commitments confirmed (decision gate above).
- Pre-seed conversations started, even if not closed.
- 1 paying design partner identified (LOI, not contract).

**Deliverables:**
1. Auth + accounts (Clerk integrated, free + paid tiers gated).
2. Stripe checkout for ANALYST tier (€99/mo).
3. Ship & Bunker live bunker price feed integrated (free, replaces analyst-default in Route Lab).
4. NewsAPI Pro upgrade (€449/mo plan; free tier is dev-only).
5. Email alerts on signal changes.
6. Basic admin: user list, churn report, MRR calculation.
7. Hosted on Render with custom domain (`app.openmaritimequant.com`).
8. SOC 2 Type 1 evidence collection started via Vanta.

**Exit criteria (gate to Phase 1):**
- 5 paying ANALYST users (€495 MRR).
- ≥3 design-partner LOIs for PROFESSIONAL tier.
- Pre-seed term sheet in hand or signed.
- Less than 2 critical bugs reported per week.

**Kill-switch:** If after 90 days you have <2 paying users AND no funding
LOI, the ICP hypothesis is wrong. Pivot to consulting OR open-source
maintainership. Do not push to Phase 1.

**Sprint plan:** see Part 10.

### Phase 1 — Beachhead ICP (months 3-9)

**Goal:** Convert hedge fund analyst persona at scale. Migrate off Streamlit
to production stack. Reach €15-25k MRR.

**Entry criteria:**
- Phase 0 exit hit.
- Pre-seed closed and in bank.
- Senior engineer hired.

**Deliverables:**
1. Next.js + FastAPI rebuild (parallel to Streamlit, not destructive).
2. PROFESSIONAL tier: Argus or Platts bunker, Baltic freight, real-time alerts, REST API.
3. Slack alert integration.
4. Backtest-as-a-service: custom factors, multiple tickers, REST endpoint.
5. Onboarding flow with magic-link signup, sample workspace, guided tour.
6. Public API documentation (Mintlify or Stripe-style).
7. Marketing site separate from app (`openmaritimequant.com` vs `app.*`).
8. Stripe usage metering for API.
9. SOC 2 Type 1 attestation completed.

**Exit criteria (gate to Phase 2):**
- 25+ paying customers across ANALYST + PROFESSIONAL.
- €20k+ MRR.
- 2+ Team-tier customers signed.
- API usage from at least 5 customers (proves quants are integrating).
- Streamlit retired from paid surface (open-source repo can keep it).

**Kill-switch:** If MRR <€10k by month 9 OR <15 paying customers, the
pricing is wrong. Re-price ANALYST tier upward (€199) and shift focus to
team/seat-based selling.

### Phase 2 — Land & expand (months 9-18)

**Goal:** Add war-risk underwriter ICP. Reach €100k MRR (€1.2M ARR).
Close Series A.

**Entry criteria:**
- Phase 1 exit hit.
- Domain expert hired (maritime, ex-broker / ex-underwriter).
- 1 enterprise pilot in flight.

**Deliverables:**
1. Underwriter persona features:
   - JWC listed-areas live feed
   - Vessel valuation feed (VesselsValue)
   - Audit log for every Route Lab calculation (PDF + JSON export)
   - Loss-history database partnership (start with one P&I club)
   - Per-voyage risk scoring (combines route, vessel age, ownership)
2. Team-tier features:
   - Workspace, shared scenarios, comments
   - Slack/Teams integration
   - SAML SSO (WorkOS)
3. Enterprise-tier features:
   - Dedicated infra option
   - Custom data ingestion
   - Named CSM
4. SOC 2 Type 2 attestation completed.
5. EU GDPR DPA template, Article 28 compliance.
6. Data warehouse: own ingestion of every customer's queries (anonymised
   benchmarks, "what other funds are watching", future product wedge).

**Exit criteria (gate to Phase 3):**
- €100k+ MRR.
- 5+ ENTERPRISE deals signed.
- Series A closed.
- 80%+ gross margin (data costs not eating revenue).

**Kill-switch:** If gross margin <50% (data costs too high), renegotiate
provider contracts or drop a feed and replace with a build-it alternative.

### Phase 3 — Platform (months 18-30)

**Goal:** Open the platform. Become the OS for maritime equity intel.
Reach €500k MRR (€6M ARR).

**Entry criteria:**
- Phase 2 exit hit.
- 25+ enterprise customers.
- Engineering team of 12+.

**Deliverables:**
1. Marketplace: third-party data providers list their feeds inside the app
   (revenue share). Brokers integrate trade execution.
2. Plugin system: customers write their own factors / signals / Route-Lab
   variants in Python notebooks that run securely server-side.
3. Mobile companion app (read-only alerts, watchlist, Route Lab quick-look).
4. Shipowner persona: integrate with Veson IMOS API (the moonshot — opens
   the third ICP).
5. White-label option for banks / brokers who want to embed the dashboard.
6. AI assistant that runs scenarios in natural language ("show me
   Frontline's break-even AWRP if Hormuz closes for 30 days") — this is
   THE unicorn-track product if it works.

**Exit criteria:**
- €500k+ MRR.
- 100+ paying customers across all tiers.
- Marketplace contributing 5%+ of revenue.

### Phase 4 — Geographic & vertical expansion (months 30+)

- US sales office.
- Asian sales presence (Singapore — maritime hub).
- Adjacent verticals: dry bulk, LNG, container shipping (already partly covered),
  port logistics, commodity flow tracking.
- AI productivity claims: "replace 3 analysts with this tool".
- This is the unicorn fork in the road.

---

## Part 4 — Engineering architecture in detail

### 4.1 Module boundaries (Phase 1+)

The current single-file Streamlit script becomes a properly-bounded service
architecture. Each box below is a deployable unit.

```
┌─────────────────────────────────────────────────────────────────┐
│  marketing-site (Next.js, Vercel)                                │
│  - landing pages, pricing, blog, docs                            │
│  - static, no auth needed                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  app-frontend (Next.js, Vercel)                                  │
│  - signed-in user surface                                        │
│  - Clerk for auth, Stripe for billing UI                         │
│  - Tremor / Recharts for charts                                  │
│  - calls api-backend for data                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  api-backend (FastAPI, Render)                                   │
│  - REST endpoints: /v1/watchlist, /v1/route-lab, /v1/backtest    │
│  - WebSocket: /ws/alerts, /ws/prices                             │
│  - SQLModel ORM, Pydantic v2 validation                          │
│  - Clerk JWT verification middleware                             │
│  - Stripe webhook handlers                                       │
└─────────────────────────────────────────────────────────────────┘
        │                                            │
        │                                            │
        ▼                                            ▼
┌──────────────────────────┐             ┌──────────────────────────┐
│  workers (Arq, Render)    │             │  postgres (Neon)          │
│  - data ingestion          │             │  - users, workspaces       │
│  - signal recomputation    │             │  - watchlists, scenarios   │
│  - alert dispatch          │             │  - audit log               │
│  - billing reconciliation  │             │  - cached provider data    │
│  - scheduled backtests     │             └──────────────────────────┘
└──────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│  redis (Upstash)          │
│  - rate limits             │
│  - job queue               │
│  - real-time price cache   │
└──────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  external data providers (paid)                                   │
│  - Argus / Platts / Ship & Bunker  → bunker prices                │
│  - Baltic Exchange / Clarksons      → freight indices             │
│  - MarineTraffic / Kpler            → AIS, voyage data            │
│  - VesselsValue                     → vessel sales / valuations   │
│  - NewsAPI Pro / Reuters / Bloomberg → headlines                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Multi-tenancy model

**Workspace-scoped row-level security.** Every domain table (`watchlist`,
`scenario`, `alert_rule`, `backtest_run`, `audit_log`) has a non-null
`workspace_id` foreign key. The API middleware injects the current
workspace ID from the Clerk JWT into every query via SQLModel's session
filters. No cross-workspace reads possible at the ORM layer.

**Anti-pattern to avoid:** do NOT use Postgres schema-per-tenant. It does
not scale beyond ~1000 tenants and migrations become hell.

### 4.3 Audit log (required for ENTERPRISE tier)

Every signal calculation and Route Lab run writes a row:

```python
class AuditEntry:
    id: UUID
    workspace_id: UUID
    user_id: UUID
    event_type: str  # "signal.computed", "route_lab.run", "backtest.run"
    inputs_json: dict       # everything needed to reproduce
    inputs_hash: str        # SHA256 of canonical inputs
    output_json: dict
    provider_versions: dict # which feed versions were used
    code_version: str       # git SHA
    occurred_at: datetime
```

Retention: 90 days for ANALYST/PRO, 1 year for TEAM, 7 years for ENTERPRISE.
Stored in Postgres for hot data; tiered to S3 Glacier after 90 days.

### 4.4 SLA architecture

Hitting "99.9% uptime" requires:
- Multi-region deployment (Render has Frankfurt + Oregon, Neon has multi-region).
- Health checks on every external feed; if Argus is down, fall back to
  Ship & Bunker with a "degraded" badge in the UI.
- Provider-failure pager-duty rotation.
- Status page (BetterStack) with uptime widgets per service.
- A "freshness budget" per data feed: prices ≤60s old, AIS ≤5min, news ≤15min.
  Alerts fire automatically when budgets are missed.

### 4.5 Data freshness contract

Every page that displays data shows a small "as of HH:MM:SS UTC" caption
with a coloured dot:

- 🟢 green = within freshness budget
- 🟡 yellow = 1-3× budget exceeded
- 🔴 red = >3× budget; data is stale; auto-fallback engaged

This is not optional for €200/mo+ pricing. Customers will check.

### 4.6 The Streamlit migration plan

**Phase 0:** Streamlit stays. Add Clerk auth via `st.experimental_user` or
a Streamlit Component wrapping Clerk's iframe. Add Stripe checkout via
redirect. Use Streamlit's `st.session_state` for workspace context.

**Phase 1:** Build Next.js + FastAPI in parallel. The new app uses the same
Postgres database. Streamlit becomes a "research notebook" inside the new
app — embedded as an iframe at `/research/notebook` for power users.

**Phase 2:** Streamlit is retired from the paid product. The open-source
repo continues to ship the Streamlit version as the community edition.

**Phase 3:** The community edition is a slimmed-down version that links
to the paid product for premium features.

---

## Part 5 — Data strategy

### 5.1 Provider matrix and budget

| Provider | Data | Phase 0 | Phase 1 | Phase 2 | Annual cost (Phase 1+) |
|----------|------|---------|---------|---------|-----------------------|
| Yahoo Finance (yfinance) | Equity prices | ✓ free | ✓ free + paid backup | paid only | €0-30k for paid backup |
| NewsAPI | Headlines | ✓ free | ✗ Pro tier | ✗ Pro tier | €5-15k |
| Ship & Bunker | Bunker spot | — | ✓ free | ✓ free | €0 |
| Argus Bunkers | Bunker assessed | — | ✓ paid | ✓ paid | €25-60k |
| Baltic Exchange | Freight indices | — | ✓ Lite | ✓ Pro | €15-50k |
| MarineTraffic | AIS, voyages | — | — | ✓ Enterprise | €30-100k |
| VesselsValue | Vessel valuations | — | — | ✓ Pro | €25-60k |
| Kpler | Cargo flows | — | — | optional | €40-120k |
| JWC (Lloyd's) | War-risk listed areas | — | — | ✓ via broker | €5-15k |
| SCA toll circulars | Suez tolls | — | ✓ scraped + parsed | ✓ scraped + parsed | €0 |

**Phase 1 data budget:** €45-125k/yr. **Phase 2:** €145-415k/yr.

### 5.2 Provider negotiation playbook

For each paid feed, the negotiation is similar. Plan accordingly:

1. **Initial outreach:** request pricing "for a B2B SaaS displaying derived
   analytics to <100 paying users". Avoid the word "redistribute" — they hear
   "wholesale" and quote 10× the right price.
2. **First quote:** is always €60-100k regardless of size. Counter with usage
   model (per-customer, per-API-call, or per-MAU).
3. **Contract clauses to push back on:** unilateral price increases, audit
   rights without notice, exclusivity restrictions on competitive products.
4. **Termination:** insist on 6 months termination-for-convenience on their
   side; you will burn customers if they cut you off in 30 days.
5. **Branding:** they will want their logo on every page. Compromise to
   "data sources" footnote in the UI. Reject "Powered by Argus" headers.

### 5.3 Freshness, cache, and licensing compliance

- **Cache TTLs aligned to licence terms.** Many feeds prohibit caching for
  more than 15 minutes. Build a per-feed TTL config and audit it monthly.
- **Per-customer entitlement check.** For some feeds (Baltic, Bloomberg)
  each end-user must have their own licence. Build a `customer.licences`
  table and gate API responses accordingly. Falsifying this gets you sued.
- **Watermark every data export.** Customer ID + timestamp embedded in every
  CSV / PDF. Forensics matter when redistribution clauses are violated.

### 5.4 Building proprietary datasets

Three data assets you should build concurrently to create defensibility:

1. **Aggregate user-query telemetry** ("what 47 funds are watching ZIM right
   now") — sellable as a sentiment/positioning indicator at Phase 2-3.
2. **Backtest result library** — every paid customer's backtest is stored
   (with their permission). Aggregated, this becomes a benchmark database
   nobody else has.
3. **Voyage scenario library** — every Route Lab run with input deltas and
   outcomes. Over 18 months this produces an empirical dataset on how
   scenarios actually move under real-world parameter changes. Differentiable.

---

## Part 6 — Pricing & packaging in detail

### 6.1 Pricing tests Phase 0 should run

Even before launching, you can validate pricing via Stripe Checkout and a
landing page. A/B test on:

- ANALYST anchor: €99 vs €149 vs €199 vs €249.
- PROFESSIONAL anchor: €399 vs €499 vs €699.
- Annual prepay discount: 0% vs 15% vs 20%.

**Methodology:** publish each price point on Twitter / LinkedIn / a
maritime-finance forum with a Stripe checkout link. 100 visitors per price
is enough signal. Pick the highest price with ≥3% conversion.

### 6.2 Feature gating

| Feature | ANALYST | PROFESSIONAL | TEAM | ENTERPRISE |
|---------|---------|--------------|------|------------|
| Watchlist + scoring | ✓ | ✓ | ✓ | ✓ |
| Route Lab (full) | ✓ | ✓ | ✓ | ✓ |
| Demo mode | ✓ | ✓ | ✓ | ✓ |
| Live yfinance prices | ✓ | ✓ | ✓ | ✓ |
| Free-tier news (NewsAPI) | ✓ | — | — | — |
| Argus / Platts bunker | — | ✓ | ✓ | ✓ |
| Baltic freight indices | — | ✓ | ✓ | ✓ |
| Email alerts | ✓ (3 rules) | ✓ (50 rules) | ✓ unlimited | ✓ unlimited |
| Slack / webhook alerts | — | ✓ | ✓ | ✓ |
| REST API | — | ✓ 1k/d | ✓ 10k/d | ✓ unlimited |
| WebSocket API | — | — | ✓ | ✓ |
| Custom backtest factors | — | ✓ | ✓ | ✓ |
| Multi-user workspace | — | — | ✓ (5) | ✓ unlimited |
| SAML SSO | — | — | ✓ | ✓ |
| MarineTraffic AIS | — | — | — | ✓ |
| VesselsValue | — | — | — | ✓ |
| Audit log retention | 30d | 90d | 1y | 7y |
| Support response | 48h email | 12h Slack | 4h Slack | phone, 1h |

### 6.3 Discount policy

- 15% annual prepay (standard).
- 20% non-profit / academic.
- 30% maritime startup (<€2M ARR, <2 years old) — first year only.
- Anti-pattern: never discount on price for enterprise. Discount on terms
  (longer commitments, narrower scope) instead.

---

## Part 7 — Go-to-market

### 7.1 Phase 0 GTM (months 0-3)

- **Open-source distribution.** Push to Hacker News, Show HN, /r/algotrading,
  /r/maritime, /r/quant. Optimise for stars/forks.
- **Direct outreach to 100 hedge fund analysts.** LinkedIn Sales Navigator +
  hand-written email. Focus on funds with public maritime exposure (search
  13-F filings for ZIM, FRO, MAERSK, SBLK).
- **Maritime-finance Twitter/X presence.** Post Route Lab analyses of public
  events ("what would a Hormuz closure cost a VLCC?"). Earn followers.
- **Industry conferences (cheap):** TPM (Long Beach), CMA Shipping (Stamford),
  Posidonia (Athens). Book a small booth at one.

### 7.2 Phase 1 GTM (months 3-9)

- **Hire a founding sales rep** (ex-Bloomberg / ex-Refinitiv with maritime
  desk experience). €70-100k base + commission.
- **Inbound: SEO content.** "What is the break-even AWRP for VLCC", "EU ETS
  scope for non-EEA voyages", "How to backtest ZIM" — all rank well, all
  drive demo requests.
- **Outbound: 50 demos / month** by month 9. Sales rep + founder co-selling.
- **Partner channel:** approach maritime brokerages (e.g. Howe Robinson,
  Arrow, Clarksons Securities) about embedding the Route Lab in their client
  portals (revenue share).

### 7.3 Phase 2 GTM (months 9-18)

- **Underwriter outreach via brokers.** Marsh, Aon, Willis Towers Watson have
  marine practices. Get warm intros via Phase 1 customers.
- **Industry analyst placement.** Get covered by Lloyd's List, TradeWinds,
  Splash24/7. Free PR; takes 6 months of relationship-building.
- **Annual user conference (small).** "Open Maritime Quant Summit" — 50
  invited customers, 1 day, in London or Amsterdam. Catalyses upsells.

### 7.4 Phase 3 GTM (months 18+)

- **US expansion.** New York office (1 sales rep + 1 CSM). The hedge funds are there.
- **Asia expansion.** Singapore (maritime hub). Higher acquisition cost,
  longer sales cycle, but huge LTV.
- **Vertical expansion.** Add commodities (oil & gas, dry bulk) to the
  watchlist. Each adjacent vertical doubles addressable market.

---

## Part 8 — Compliance & security

### 8.1 SOC 2 timeline

- **Month 6:** Sign Vanta or Drata. Start evidence collection.
- **Month 9:** Complete SOC 2 Type 1 audit (point-in-time). Required for
  Phase 1 enterprise sales.
- **Month 12:** Begin 6-month observation window for Type 2.
- **Month 18:** Complete SOC 2 Type 2 audit. Required for Phase 2+.

Cost: €25-50k for the audits + €15-25k/yr for Vanta/Drata.

### 8.2 GDPR & data protection

- **Data Processing Agreement (DPA)** template by month 6, reviewable by
  every customer's legal team.
- **Article 28 obligations** (sub-processor list, breach notification within
  72h, audit rights).
- **Data residency:** EU customers' data on EU-region Postgres. Use Neon's
  Frankfurt region.
- **Right-to-be-forgotten endpoint:** customer-facing API to delete their
  workspace. Cascades to all derived data.

### 8.3 Security baseline

Required from Phase 1:
- Mandatory MFA for all customer accounts.
- All secrets in a managed vault (Doppler, 1Password Connect, or AWS Secrets Manager).
- No plaintext credentials in env files or repos.
- Quarterly third-party pentest (start month 12).
- Bug bounty program (HackerOne or self-managed via security@) from month 18.
- Dependency scanning (Dependabot + Snyk Free) from day 1.

### 8.4 Incident response plan

Document by month 6. Include:
- On-call rotation (founder + senior eng for Phase 1).
- Severity classification (S0 = data loss, S1 = >50% users impacted, etc.).
- Customer notification template (within 4 hours for S0/S1).
- Postmortem template (publish within 5 business days).

---

## Part 9 — Risk register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|------|-----------|--------|------------|-------|
| 1 | Argus/Platts contract negotiations stall | High | High | Start with Ship & Bunker free in Phase 0; Argus only required for Pro tier. Have Vortexa as backup. | Founder |
| 2 | Hedge fund ICP rejects pricing | Medium | High | A/B test pricing in Phase 0. Be willing to drop ANALYST tier to €49. | Founder |
| 3 | Veson or competitor releases Route-Lab clone | Medium | High | Patent the break-even-AWRP solver (provisional patent in US, ~€10k). Move fast on Phase 1 features. | Founder + lawyer |
| 4 | NewsAPI rate-limits us out of Pro tier | Low | Medium | Have Reuters Connect as warm backup, add it via partner integration. | CTO (Phase 1) |
| 5 | EU ETS scope rules change mid-Phase | Medium | Low | Code is modular — `route_economics.ets_coverage_fraction` is a one-line edit. Subscribe to EC maritime ETS updates. | CTO |
| 6 | SOC 2 audit fails first attempt | Low | Medium | Use Vanta/Drata to pre-validate evidence. Budget 2-3 month delay buffer. | CTO + auditor |
| 7 | Streamlit breaks under multi-tenant load | High | Medium | Migrate by end of Phase 1 (already planned). Cap Streamlit usage at 50 concurrent users. | CTO |
| 8 | Founder burnout in Phase 0 | High | Critical | Cap working hours at 60/week. Co-founder hire by month 9. Therapy budget. | Founder |
| 9 | Single-customer concentration >25% revenue | Medium | High | Refuse contracts >25% of MRR until Series A. Diversify. | Founder |
| 10 | Open-source community fork undercuts pricing | Low | Medium | Open-core model: keep premium features (live data, alerts, multi-user) closed-source via service boundary. | CTO |
| 11 | yfinance breaks (Yahoo changes API) | High | Low | Build a fallback to a paid Polygon.io / Tiingo subscription for equity prices. | CTO |
| 12 | Currency / FX volatility (€ pricing, $ data costs) | Medium | Medium | Hedge with forward contracts at €1M ARR. Until then, accept 5-10% margin volatility. | CFO (post-Series A) |
| 13 | Regulatory: SaaS classified as MIFID II investment service | Low | High | Disclaimers everywhere. Legal opinion in Phase 1. Avoid recommendation language. | Founder + counsel |
| 14 | Key engineering hire leaves | Medium | High | 4-year vesting with 1-year cliff. Document everything. Pair-program critical paths. | Founder |
| 15 | Series A doesn't materialise | Medium | Critical | Hit €1M ARR organically by month 18 if possible. Bootstrap to €30M ARR is achievable. | Founder + CFO |

---

## Part 10 — Phase 0 sprint plan (next 90 days)

This is the executable plan. Each sprint is 2 weeks. Six sprints total.
Each sprint has: objective, deliverables, acceptance criteria, files
touched, and skills required.

**This section is written so a Sonnet-tier model can execute each sprint
independently.** No strategic decisions are deferred to the executor; every
choice is locked.

### Sprint 0 (week 0) — Decision gate + pre-work

**Objective:** Confirm founder commitments. Set up infrastructure accounts.

**Deliverables:**
- [ ] Founder confirms 6 decision-gate items above.
- [ ] Sign up: Clerk, Stripe, Render, Neon, Upstash, Sentry, Resend, Vanta.
- [ ] Domain registered: `openmaritimequant.com` (or alternative).
- [ ] Stripe Tax enabled for EU VAT.
- [ ] Pre-seed deck v1 drafted.
- [ ] Three target hedge fund analysts identified (LinkedIn, by name).

**Acceptance:** All checkboxes ticked. Founder can produce pre-seed deck.

### Sprint 1 (weeks 1-2) — Auth + accounts

**Objective:** Wrap the existing Streamlit dashboard in Clerk auth.

**Deliverables:**
- [ ] Clerk integrated as a Streamlit Component (use `streamlit-clerk` if it
      exists, else build a thin wrapper around Clerk's `<UserButton/>`
      iframe).
- [ ] User table in Postgres (Neon): `user_id`, `clerk_id`, `email`,
      `tier`, `created_at`, `stripe_customer_id`.
- [ ] On first sign-in, write a Postgres row.
- [ ] Sidebar shows user email + sign-out button (replaces "Configure via env" caption).
- [ ] Anonymous users see only the demo mode (current public state).

**Files touched:** `dashboard.py` (sidebar + auth gate), new `auth.py`,
new `db.py`, new `models.py`, new `migrations/`.

**Acceptance criteria:**
- Authenticated user lands on watchlist with their tier shown.
- Anonymous user lands on demo mode with a "Sign in" CTA in hero.
- All 81 existing tests still pass.
- New tests for auth gating: at least 6 cases covering anon/authed/expired-token.

**Skills:** Python, Streamlit Components, basic SQL. Junior+.

### Sprint 2 (weeks 3-4) — Stripe billing + ANALYST tier

**Objective:** A user can sign up, pay €99, and unlock paid features.

**Deliverables:**
- [ ] Stripe Checkout flow from a "Upgrade to Analyst" button in sidebar.
- [ ] Stripe webhook handler (FastAPI sidecar on Render) processes
      `checkout.session.completed`, `customer.subscription.updated`,
      `customer.subscription.deleted`.
- [ ] User's `tier` field updates on webhook.
- [ ] Feature gating: ANALYST tier unlocks live news (instead of synthetic
      sample), RSS-style alerts, no demo watermark on charts.
- [ ] Stripe Customer Portal link from settings page (pause, cancel, update card).
- [ ] Receipts auto-emailed via Stripe.

**Files touched:** new `webhook_handler.py`, `dashboard.py` (gating
checks at provider call sites), `providers.py` (route to free vs paid feed
based on tier).

**Acceptance criteria:**
- Test card flow: sign up → pay → tier upgrades → live data shows.
- Refund flow: cancel → tier downgrades on next billing cycle.
- Webhook idempotency: replaying same event doesn't double-charge.
- New tests: at least 8 cases.

**Skills:** Python, FastAPI basics, Stripe API. Mid-level.

### Sprint 3 (weeks 5-6) — Bunker price feed + Route Lab live data

**Objective:** Real bunker prices in the Route Lab (replacing analyst defaults).

**Deliverables:**
- [ ] Ship & Bunker scraper (free, no auth required) that pulls IFO380,
      VLSFO, LSMGO at major bunkering ports daily.
- [ ] Cached in Postgres + refreshed by an Arq worker every 4 hours.
- [ ] Route Lab Scenario expander shows "Live: Singapore IFO380 €687/mt
      (updated 2h ago)" instead of the editable default.
- [ ] User can still override; the live value is just the new default.
- [ ] Provider status panel shows Ship & Bunker as a configured provider.

**Files touched:** new `providers/bunker.py`, `route_economics.py` (no
changes — just inputs flow), `dashboard.py` (Route Lab Scenario expander).

**Acceptance criteria:**
- Live price visible without manual refresh.
- Stale-price warning if Ship & Bunker fails for >12h.
- Tests: scraper unit tests with fixture HTML; cache-invalidation test.

**Skills:** Python, BeautifulSoup or Playwright, Postgres. Mid-level.

### Sprint 4 (weeks 7-8) — Email alerts

**Objective:** User can subscribe to alerts; alerts fire and arrive.

**Deliverables:**
- [ ] Alert rule UI: "notify me when [ticker]'s [Action] becomes [VALUE]".
- [ ] Up to 3 rules per ANALYST user (gate enforced).
- [ ] Arq worker recomputes signals every 30 minutes; compares prior to
      current; fires alerts on change.
- [ ] Email via Resend, branded template.
- [ ] In-app alert history.

**Files touched:** new `alerts.py`, `models.py` (AlertRule, AlertEvent
tables), `dashboard.py` (alert rules tab in settings).

**Acceptance criteria:**
- Alert rule saved persists across logins.
- Alert fires within 30 min of trigger condition.
- Unsubscribe link in every email.
- Tests: rule evaluation + idempotency (same trigger doesn't fire twice).

**Skills:** Python, Arq, Resend SDK. Mid-level.

### Sprint 5 (weeks 9-10) — Onboarding + landing page

**Objective:** A first-time visitor signs up, gets value in 5 minutes.

**Deliverables:**
- [ ] Marketing landing page (`openmaritimequant.com`): Next.js +
      Tailwind. One-pager. Hero + features + pricing + sign-up CTA.
- [ ] Sign-up flow: email + magic link via Clerk.
- [ ] First-run experience inside the app: 3-step guided tour, optional skip.
- [ ] Sample workspace pre-populated (the demo watchlist + a saved Route Lab scenario).
- [ ] Stripe Checkout on the pricing page.

**Files touched:** new repo `marketing-site/` (Next.js), new `onboarding.py`,
`dashboard.py` (first-run check).

**Acceptance criteria:**
- Visitor can go from landing page → signed in → first signal in <3 min.
- Conversion event fires in analytics.
- Lighthouse score >90 on landing page.

**Skills:** Next.js, Tailwind, copywriting. Mid-level + design.

### Sprint 6 (weeks 11-12) — Polish, observability, design partner outreach

**Objective:** Production-ready beta. First paying customer signed.

**Deliverables:**
- [ ] Sentry error tracking on every component.
- [ ] BetterStack status page at `status.openmaritimequant.com`.
- [ ] Feature flag system (LaunchDarkly free or self-hosted) for gradual rollout.
- [ ] Basic admin dashboard: MRR, churn, active users.
- [ ] Outreach to 50 hedge fund analysts via warm and cold email.
- [ ] At least 3 design-partner conversations booked.
- [ ] First paying ANALYST customer signed.
- [ ] Public launch on Hacker News, Show HN, /r/algotrading, /r/maritime.

**Files touched:** all (observability instrumentation), new `admin.py`.

**Acceptance criteria:**
- 5+ paying ANALYST users.
- ≥3 PROFESSIONAL design-partner LOIs.
- <2 critical bugs/week.

**Skills:** all of the above + sales / outreach. Founder + 1 engineer.

### Sprint 0-6 summary

| Sprint | Weeks | Deliverable | Owner-skill | Files added |
|--------|-------|-------------|-------------|-------------|
| 0 | 0 | Decision gate + accounts | Founder | (none) |
| 1 | 1-2 | Clerk auth | Junior eng | auth.py, db.py, models.py |
| 2 | 3-4 | Stripe billing | Mid eng | webhook_handler.py |
| 3 | 5-6 | Bunker feed | Mid eng | providers/bunker.py |
| 4 | 7-8 | Email alerts | Mid eng | alerts.py |
| 5 | 9-10 | Landing + onboarding | Mid eng + design | marketing-site/, onboarding.py |
| 6 | 11-12 | Polish + sales | Founder + eng | admin.py |

---

## Part 11 — Founder decision gate (final, must approve before sprint 1)

**Sign here (mentally) before starting:**

```
1. I commit 24-30 months full-time.                                [ ]
2. I will raise €500k+ pre-seed within 6 months.                   [ ]
3. I have or will recruit a maritime industry advisor.             [ ]
4. I accept Phase 0 ships a beta — no customer pays €200/mo yet.   [ ]
5. I can tolerate ~€20k/month burn from month 6 before profit.     [ ]
6. I target €30-100M ARR; unicorn is upside, not base case.        [ ]
7. I drop retail investors as a target ICP. Forever.               [ ]
8. I price at €99 / €499 / €2500 — not €200.                       [ ]
9. I rebuild off Streamlit by end of Phase 1.                      [ ]
10. I will pay for SOC 2 (~€25-50k) by month 18.                   [ ]
```

If any of those is "No, but...", we replan. Don't push to sprint 1.

---

## Part 12 — Alternative paths (if you say no to the gate)

You don't have to go SaaS-unicorn. Three other realistic outcomes:

### Path A — Maintained open-source (cost-recovery)

Keep the dashboard free. Add a "Donate" / "Sponsor on GitHub" button. Add a
small €19/mo "Supporter" tier with no premium features. Goal: cover hosting
+ data costs (~€500-1000/mo). You retain authorship; product stays niche
but useful.

**Pro:** Low effort. Reputation building. Stepping stone to consulting.
**Con:** No exit. Doesn't fund full-time work.

### Path B — Consulting practice (€200-500k/yr solo)

Use the dashboard as a credentials-piece. Sell consulting on maritime
quant work to 3-5 clients per year at €30-100k each. Bespoke Route Lab
extensions for specific underwriters. White-glove model.

**Pro:** Profitable from month 3. No fundraising. No competition.
**Con:** Linear scaling. No exit unless you build a firm. Geographically
constrained.

### Path C — Acquihire / talent acquisition (12-24 months)

Polish to Phase 0 exit, get to 5-15 paying customers. Sell to Veson, Sea/SaaS,
ShipNet, or a maritime data co. Range: €500k-3M for the asset + 1-2 year
earn-out. You become Director of [whatever] there.

**Pro:** Real exit, no Series A risk. Validation of product.
**Con:** No unicorn. Probably 3-7× cash-on-cash if you also got pre-seed.

### My honest recommendation

If you're solo-funded right now and have a day-job that pays bills, do
**Path A for 6 months while testing pricing on the side**. If you find
that hedge fund analysts will pay €99 for ANALYST tier (5+ paying), then
upgrade to the SaaS path with conviction. If they won't, do Path B forever
or Path C in 12 months.

Don't burn yourself out building Phase 0 SaaS without market validation.
**Sprint 0 is the validation sprint.** If sprint 0 says "no", stop.

---

## Decision log

Decisions made in this document, with rationale:

| # | Decision | Alternative considered | Rationale |
|---|----------|------------------------|-----------|
| 1 | Drop retail ICP | Keep at €49/mo | Margin too thin, support burden too high, churn ≥10%/mo. |
| 2 | Skip €200/mo tier | Add €199 mid-tier | Dead zone. €99 captures volume; €499 captures revenue. |
| 3 | Streamlit Phase 0, rebuild Phase 1 | Rebuild now | Time-to-revenue. Streamlit MVP ships in 12 weeks; rebuild is 9 months. |
| 4 | Next.js + FastAPI Phase 1 | Stay on Streamlit | Streamlit caps at $1M ARR. Plenty of evidence. |
| 5 | Clerk for auth | Build in-house | Auth is undifferentiated. Use Clerk till $5M ARR. |
| 6 | Render + Neon + Upstash | AWS day 1 | Render saves 60% of infra time before Series A. |
| 7 | Argus/Platts paid feeds | Build own bunker survey | 18-month build, $500k cost. Not worth it. |
| 8 | Hedge funds as primary ICP | Underwriters | Faster sales cycle, higher seat density, better fit for current product. |
| 9 | Open-core model | Closed-source paid version | Distribution wedge. 60% of paid customers will come from OSS funnel. |
| 10 | SOC 2 Type 1 by month 9 | Skip until Series A | Required for first enterprise sale. €25k cost; payback in one deal. |
| 11 | Founder + 1 engineer for Phase 0 | Solo founder | Solo for 12 weeks is OK; beyond that, you'll burn out. |
| 12 | Pre-seed €500k-800k | Bootstrap to seed | Data licences alone exceed bootstrap budget. |
| 13 | Drop shipowner ops as Phase 1 | Sell to shipowners | Sales cycle 12-24mo. Phase 1 needs faster wins. |
| 14 | Provisional patent on Route Lab math | Trade secret | Cheap (~€10k) and useful for moat narrative to VCs. |
| 15 | EU pricing in € | USD | Most likely customers in EU+UK initially. Switch to USD when 30%+ revenue from US. |

---

## Glossary (for future engineers / advisors / VCs reading this)

- **AIS** = Automatic Identification System; vessel-position data feed.
- **AWRP** = Additional War Risk Premium; insurance surcharge for transiting
  high-risk areas.
- **Baltic Exchange** = London-based publisher of freight indices (BDI,
  BDTI, BCI, etc.).
- **BDI** = Baltic Dry Index; aggregate dry-bulk freight rate proxy.
- **EU ETS** = European Union Emissions Trading System.
- **JWC** = Joint War Committee (London insurance market body that lists
  high-risk transit areas).
- **MIFID II** = EU regulation on financial services; relevant if we drift
  into "investment advice".
- **P&I club** = Protection and Indemnity club; mutual insurance for shipowners.
- **SCNT** = Suez Canal Net Tonnage; tonnage measure used to compute Suez tolls.
- **SOC 2** = US AICPA security audit standard. Type 1 = point-in-time;
  Type 2 = continuous over 6+ months.
- **TCE** = Time Charter Equivalent; daily revenue equivalent for a vessel.
- **VLCC** = Very Large Crude Carrier; ~300,000 dwt oil tanker.

---

## How to use this document going forward

1. Keep this document at `docs/SAAS_ROADMAP.md`. Update it monthly (changelog
   at the bottom of file). Treat it like an architectural decision record.
2. Every sprint, the executor reads Part 10's relevant sprint section and
   builds against the acceptance criteria. No interpretation needed.
3. Every phase exit, the founder reviews Part 3's exit criteria. Go/no-go on
   Phase advancement.
4. Every quarter, review Part 9's risk register. Add new risks; close
   resolved ones.
5. The decision log (above) is append-only. Never silently change a decision
   without writing why.

---

**End of roadmap. Total length: ~14,000 words. Read time: ~50 minutes.
Last updated: 2026-05-05.**
