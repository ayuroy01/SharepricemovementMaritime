# marketing-site

Single static HTML page for the Sprint 0 pricing-test landing page.

## Preview locally

```bash
cd marketing-site
python3 -m http.server 8080
# open http://localhost:8080
```

## Deploy (free, takes 2 minutes)

### Option A — Cloudflare Pages (recommended)

1. Push this folder to GitHub (it's already in the main repo).
2. Cloudflare Pages → Connect to GitHub → pick this repo.
3. Build command: leave empty.
4. Build output directory: `marketing-site`
5. Done. Cloudflare assigns `xxx.pages.dev`. Add `openmaritimequant.com`
   as a custom domain when registered.

### Option B — Netlify drag-and-drop

1. Open netlify.com/drop.
2. Drag the `marketing-site/` folder into the page.
3. Done. Add custom domain in Netlify settings.

### Option C — Vercel

1. `npm i -g vercel`
2. `cd marketing-site && vercel`
3. Follow prompts. Add custom domain in Vercel dashboard.

## Before going live — replace these

Search the file for `REPLACE_WITH_REAL_LINK` (2 occurrences) and paste your
real Stripe Checkout URLs.

To create them:

1. Stripe Dashboard → Products → New product
2. Name: "Analyst", price €99/month, recurring.
3. Click into the price → "Create payment link" → copy URL.
4. Paste into both `REPLACE_WITH_REAL_LINK` slots.

For the €499 and €2,500 tiers, the buttons use `mailto:hello@openmaritimequant.com`.
Set up that mailbox at your domain registrar (Cloudflare Email Routing is
free) so replies land somewhere you actually read.

## Plausible analytics (privacy-first, no cookie banner)

The script tag is commented out. Once you've signed up at plausible.io and
added `openmaritimequant.com`, uncomment line 13 in `index.html`. No GDPR
banner needed — Plausible doesn't use cookies.

## What this page is for

This is the **Sprint 0 validation tool**. The job of this page is to answer
one question:

> Will hedge fund analysts pay €99/mo for maritime equity intelligence?

Run it for 4 weeks. Measure:

- Conversion rate from visit → "Get started" click. Target: ≥3%.
- Conversion rate from click → completed Stripe checkout. Target: ≥1 user.
- Reply rate on the cold-DM outreach (see `docs/SPRINT_0.md`). Target: ≥1 of 3.

If all three are missed, the ICP hypothesis is wrong. **Do not start
Sprint 1.** See `docs/SAAS_ROADMAP.md` Part 12 for alternative paths.
