# LUMA B2B dashboard — UI improvement verification

Date: 2026-09-02
Mode: `improve`
Scope: approved remediation plan for the existing local review dashboard

## Implementation result

The approved remediation plan was implemented after explicit user approval recorded in `approval-record-20260902.md` and evidence `E-0021`.

- Detail secondary panels now stack at tablet and narrow widths.
- Long phone and email collections use a compact summary with an explicit native disclosure; all public values remain available.
- Workflow, location, source-family, decision-maker, evidence, and screenshot-reason fields wrap to a readable two-line measure and retain full values through accessible labels/titles.
- Detail section headings and action controls stack cleanly on narrow screens.
- Dossier labels now prioritize Persian decision language while preserving source provenance and machine values as secondary metadata.
- Materials opened directly by URL or by tab switch now load the selected local Markdown automatically.
- Sales-ready cards expose a clear پروندهٔ بررسی action.
- Compare empty state explains where selection starts.
- Filter controls and review fields have explicit accessible names/labels.
- Evidence cards use zero-minimum grid tracks so long content cannot create document overflow.

## Verification

- `npm run qa`: passed.
- `node --check dashboard/app/views.js`: passed.
- `node --check dashboard/app/app.js`: passed.
- `git diff --check`: passed.
- Headless Chromium matrix: 40 route/viewport checks across overview, companies, ready, evidence, review, compare, and Sabah overview/evidence/materials/history at 1440, 1024, 768, and 390px.
- Matrix result: all routes rendered one main content region, all expected rows/cards/materials appeared, document overflow was `0` for every check, and no page errors, console errors, or failed requests were observed.
- Interaction checks: Persian company search, command palette open/Escape close, evidence lightbox open/Escape close, contact disclosure expansion with 12 phone values, compare selection/removal, direct materials auto-load, and explicit control-name audit all passed.
- Typography check: `IRANYekanX` and `IRANYekanXFaNum` loaded and were applied to body, headings, and numeric score values.
- Browser mode: headless Chromium only; no visible browser window was launched.

## Durable visual artifacts

- Final desktop captures remain in `dashboard/screenshots/01-overview.png` through `dashboard/screenshots/08-review-state.png`.
- Additional narrow-width Sabah captures were inspected from the headless run at 390px; the preserved pre-fix baseline `E-0020` was not overwritten.

## Boundary

This verifies the requested implementation and local visual behavior. The OCD Designer Brand Book approval and release acceptance remain pending; no release verdict or public deployment is claimed.
