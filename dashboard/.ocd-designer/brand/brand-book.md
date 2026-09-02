# Brand Book — LUMA B2B Review Dashboard

Status: `provisional working direction`
Version: `0.1.0`
Last updated: `2026-09-02`

> This dashboard is an internal, local-only research review tool. User-provided product and privacy constraints are `confirmed`; visual palette, information architecture details, and interaction choices are `inferred` from the brief and the previous Sabah demo direction. Brand and design approvals remain pending.

## Company and product

- Company: LUMA — `confirmed` by the repository and user brief.
- Product: a private local review dashboard for LUMA B2B company research — `confirmed` by user brief.
- Business goal: help the founder and business-development team move from the full company universe to sales-ready prospects and a defensible company dossier without opening raw repository files — `confirmed`.
- Positioning: an evidence-first intelligence operating system for human review, not a CRM or customer-facing product — `confirmed`.
- Differentiators: source-family transparency, observed/inference/unknown semantics, confidence-aware ranking, local persistence, and direct access to sales material — `confirmed`/`inferred` from the brief.
- Competitors or alternatives: `unknown`; not required for this internal tool.

## Audience and context

- Primary audience: LUMA founder and business-development team — `confirmed`.
- Secondary audience: internal researcher or salesperson reviewing a prospect with a colleague — `inferred`.
- User jobs: orient to the dataset, find a company, compare candidates, inspect evidence, read sales material, and record a human review decision — `confirmed`.
- Devices and environments: desktop/laptop first; narrow responsive layout for occasional smaller screens — `confirmed`.
- Language, locale, and direction: Persian-first `fa-IR`, RTL; mixed Persian/English names, URLs, email, scores, and file paths must remain legible — `confirmed`.
- Accessibility needs: WCAG 2.2 AA target, semantic landmarks, keyboard operation, visible focus, readable contrast, reduced-motion support, and deliberate unknown/empty states — `confirmed`/`inferred`.

## Journeys and content

- Critical journey 1: Overview → filtered company set → company detail → evidence/materials → local human review — `confirmed`.
- Critical journey 2: Sales Ready → Wave 1 → compare 2–4 prospects → select next review — `confirmed`.
- Critical journey 3: global search or command palette → open company, wave, tier, or evidence-quality set — `confirmed`.
- Primary actions: search, filter, open detail, compare, copy public contact, open source, and save local review state — `confirmed`.
- Success measures: fast orientation, no unsupported certainty, accurate canonical counts, useful Sabah end-to-end detail, persistent review state, and no outreach action — `confirmed`.
- Content hierarchy: identity and review status first; why LUMA and scores second; evidence and sources third; sales material and next action fourth — `inferred` from user jobs.
- Voice: restrained, analytical, precise, Persian-first, and explicit about certainty — `confirmed`/`inferred`.
- Claims or words to avoid: do not turn hypotheses into facts; do not imply contact was made; do not expose private information; do not present research scores as truth without confidence context — `confirmed`.

## Visual system

- Brand personality: premium, technical, calm, dense but readable, and trustworthy — `confirmed` by the design brief and prior Sabah direction.
- Visual principles: evidence before decoration; small semantic color accents; high information density with clear grouping; shallow depth; compact comparisons; one strong primary action per surface — `inferred`.
- Anti-goals: generic admin template, CRM clone, colorful vanity cards, neon AI styling, radial-score overload, public/customer-facing appearance, and hidden uncertainty — `confirmed`.
- Approved colors: no official LUMA palette was supplied, so palette is `unknown`. Working tokens inherit the previous provisional direction: deep navy ink, warm paper/cool canvas, restrained teal, amber for attention, and rose for reject — `inferred`, not officially approved.
- Typography and font files: system Persian-capable stack with Vazirmatn/IRANSans/Tahoma/Arial fallbacks; no network font dependency — `inferred` from local-only constraints.
- Iconography: small inline SVG or text-safe geometry, used as navigation cues and not as decoration — `inferred`.
- Imagery and asset rules: use repository screenshots as evidence with metadata; no synthetic or AI-generated evidence; external pages open explicitly rather than being framed — `confirmed`.
- Motion posture: purposeful discrete transitions for navigation, selection, modal, and save feedback; no looping spectacle; reduced motion removes nonessential movement — `confirmed`/`inferred`.

## Technical and release constraints

- Supported browsers and viewports: modern Chromium/Chrome for local use; desktop 1440×1000 and 1280×900; tablet 1024×900; narrow mobile 390×844 for responsive verification — `confirmed`/`inferred`.
- Performance target: startup should remain practical with ۶٬۰۸۴ records; paginate/virtualize the explorer, lazy-load detail and Markdown, and avoid rendering all records at once — `confirmed`.
- Public/private indexing policy: local-only private tool; no public deployment, no authentication provider, no external AI/API, no cloud database — `confirmed`.
- Existing design system or component constraints: reuse the prior LUMA Sabah direction where useful, but do not modify the existing research pipeline or Sabah demo routes — `confirmed`.
- In-scope routes: local dashboard overview, companies explorer, sales-ready, evidence explorer, review queue, compare mode, company detail, and local demo route links — `confirmed`.
- Explicit exclusions: broad discovery, research mutation, outreach, external form submission, CRM sync, public deployment, private data collection, and production scoring changes — `confirmed`.
- Acceptance criteria: actual current repository data is indexed; RTL and mixed scripts are readable; Sabah exposes evidence/materials/demo; search/filter/compare/review persistence work; no console errors or external dependencies; screenshots and runtime evidence are captured headlessly — `confirmed`.

## Evidence and unresolved assumptions

| Statement | Label | Source/evidence | Needs confirmation? |
|---|---|---|---|
| The canonical normalized dataset contains ۶٬۰۸۴ company records. | observed | `data/normalized/companies.jsonl` inventory on 2026-09-02 | No for this build; re-index after new research. |
| Current status distribution includes ۳۲ READY FOR OUTREACH, ۸ NEEDS DISCOVERY, and ۱۱۱ NOT READY records. | observed | canonical normalized company records | No for this build; rebuild after new research. |
| The founder prefers an evidence-first intelligence workbench over a CRM-like workflow. | confirmed | dashboard user brief | No. |
| Deep navy/teal/paper tokens represent official LUMA brand colors. | unknown | no official LUMA brand book in repository | Yes, before external productization. |
| The dashboard should use RTL with a right-side navigation rail. | inferred | Persian-first brief and previous Sabah demo direction | Yes, if the user prefers a left rail in RTL. |
| A JSON-backed local API is sufficient for review persistence. | inferred | local-only scope and small review-state payload | Yes, if multi-user or concurrent review is later needed. |
| Research evidence can be served from stored repository artifacts without live crawling. | confirmed | user request for local review and canonical source principle | No for this build. |
| G9/release acceptance is complete. | unknown | no explicit user acceptance of this exact dashboard direction or build | Yes; remains pending. |

## Confirmation

- Approval scope: `full_brand_book`
- Confirmed by: pending explicit review of this complete dashboard Brand Book.
- Date: pending.
- Confirmation evidence ID: pending.
- Decision record: `dashboard/.ocd-designer/decisions/dashboard-direction.md`.

The dashboard implementation proceeds from the detailed user brief and this provisional direction. The approval state is not fabricated; release readiness remains blocked until the user reviews the complete direction and final evidence.
