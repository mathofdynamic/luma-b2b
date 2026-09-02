# Brand Book

Status: `working direction derived from user brief`
Version: `0.1.0`
Last updated: `2026-09-02`

> Material direction is marked `confirmed`, `inferred`, or `unknown`. The user brief is the source of confirmed constraints; the provisional palette and component details remain open for later review.

## Company and product

- Company: LUMA — `confirmed` by user brief.
- Product: a private, local, deterministic Sabah sales-demo prototype for RFQ structuring and product matching — `confirmed` by user brief.
- Business goal: make a controlled custom-software opportunity understandable in a 2–4 minute sales meeting — `confirmed`.
- Positioning: serious internal B2B operations tooling; business outcome first, with human approval — `confirmed`.
- Client context: Sabah product facts are public reference material; internal Sabah workflows are not claimed — `confirmed`.
- Competitors or alternatives: `unknown`; not in scope for this demo.

## Audience and context

- Primary audience: LUMA sales and commercial staff presenting to Sabah — `confirmed` by task scope.
- Secondary audience: a future commercial/operations process owner at Sabah — `inferred`.
- User jobs: choose a sample RFQ, show extraction, inspect candidates, surface ambiguity, edit a response, and approve manually — `confirmed`.
- Devices and environments: desktop-first private meeting, responsive fallback — `confirmed`.
- Language, locale, and direction: Persian, `fa-IR`, RTL; preserve English technical product names — `confirmed`.
- Accessibility needs: visible focus states, semantic controls, readable contrast, reduced-motion support — `inferred` from the project acceptance bar.

## Journeys and content

- Critical journey: RFQ text → structured extraction → product candidates → clarification → draft response → human approval — `confirmed`.
- Primary action: `تحلیل درخواست`; presentation control: `بعدی` — `confirmed`.
- Success measures: the flow is understandable, uncertainty is visible, no automatic send is implied, and the demo works offline — `confirmed`.
- Content hierarchy: customer request first, structured facts second, product evidence third, proposed action last — `confirmed`.
- Voice: restrained, professional, precise, and hypothesis-aware — `confirmed`.
- Claims to avoid: actual Sabah internal problems, actual prices, fabricated savings, unverified workflow knowledge, generic AI claims — `confirmed`.

## Visual system

- Brand personality: minimal, premium, technical, calm, and information-dense — `confirmed`.
- Visual principles: strong typography, generous spacing, precise tables, shallow depth, restrained status colors, and obvious approval gates — `confirmed`.
- Provisional palette: deep navy `#102C40`, off-white `#FBFCFA`, cool canvas `#EEF2EF`, teal `#2A847D`, warm amber `#AD6E28`, rose only for return/review — `inferred` from the brief; not an official LUMA palette.
- Typography: local/system Persian-capable stack (`IRANSans`, `Vazirmatn`, `Tahoma`, `Arial`) with no network font dependency — `inferred`.
- Iconography: CSS geometry and text-safe symbols only; no external asset dependency — `confirmed` for reliability, implementation detail `inferred`.
- Imagery: no synthetic evidence; no unnecessary redistribution of Sabah imagery; product data is text-first — `confirmed`.
- Motion posture: short, purposeful transitions; no neon, orbs, particles, bouncing, or terminal theatre — `confirmed`.

## Technical and release constraints

- Browser/runtime: modern Chromium/Chrome via invisible headless test plus a local static server — `confirmed`.
- Performance target: no external API or remote asset required for the base path — `confirmed`.
- Privacy: private repository; no public deployment; no private profiles, cookies, credentials, or confidential Sabah data — `confirmed`.
- Architecture: separate static UI, demo data, deterministic matcher, and workflow state so a production API can replace the matcher later — `confirmed`.
- In-scope route: `demos/sabahi/app/index.html` — `confirmed`.
- Explicit exclusions: real outreach, real submission, production integration, real pricing, production AI, and public deployment — `confirmed`.
- Acceptance criteria: all three RFQs work; ambiguity is not hallucinated; presentation controls work; RTL/responsive layout is coherent; screenshots are captured headlessly; no console errors; no external AI dependency — `confirmed`.

## Evidence and unresolved assumptions

| Statement | Label | Source/evidence | Needs confirmation? |
|---|---|---|---|
| Sabah publicly presents industrial supply, production, product categories, and Pexide technical pages. | confirmed | `demos/sabahi/research.md` and linked public Sabah URLs | No for demo scope; validate product details before production use. |
| The internal Sabah RFQ journey is known. | unknown | No public source establishes it. | Yes, in a discovery meeting. |
| The selected RFQ fields are useful to a technical buyer. | inferred | Public Pexide fields plus demo design judgment. | Yes. |
| Deep navy/teal palette represents official LUMA brand colors. | unknown | No official LUMA brand book was supplied. | Yes, before external collateral. |
| The deterministic matcher is suitable for production. | unknown | It is a meeting-safe prototype only. | Yes, after real samples and validation. |

## Confirmation

- Approval scope: `full_brand_book`
- Confirmed by: pending explicit review of this working direction.
- Date: pending.
- Confirmation evidence ID: pending.
- Decision record: `.ocd-designer/decisions/README.md`.

The implementation proceeds from the user’s detailed brief while keeping unreviewed brand details provisional. The SHA-256 is stored outside this document in `brand/approval.json`; inserting the hash here would change the document being hashed.
