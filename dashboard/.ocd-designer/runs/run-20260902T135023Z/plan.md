# OCD Designer run plan — LUMA B2B Review Dashboard

Stage: `DISCOVERY` → provisional implementation and verification

## Scope

- Build only the local review dashboard under `dashboard/` plus the root `package.json`/lockfile and project documentation needed to run it.
- Treat `data/normalized/companies.jsonl` and existing repository outputs as canonical; never duplicate company records into frontend source.
- Keep the research pipeline, source evidence, public contact data, and existing Sabah demo behavior unchanged.
- Use the user brief and prior Sabah visual direction as working/provisional design inputs. Brand approval, design-direction approval, and release acceptance remain pending.
- No live company outreach, no external forms, no public deployment, no external AI/API, and no broad discovery.

## Information architecture

1. **Overview** — dataset orientation, quality signals, top industries, and direct links to filtered sets.
2. **Companies** — paginated explorer with search, facet filters, score ranges, evidence/contact filters, and compare selection.
3. **Sales Ready** — curated ۳۲-company experience with Wave 1/2/3 tabs and first-contact ranking.
4. **Evidence** — research-quality queue for source families, screenshots, decision makers, and workflow evidence.
5. **Review** — local human-review queue and persistent notes, separate from canonical research.
6. **Compare** — analytical ۲–۴ company comparison driven by explorer selections.
7. **Company detail** — identity, summary, scores, profile, workflow, evidence, visual evidence, source families, decision makers, contacts, materials, demo links, history, and review state.

## Design direction

- Desktop-first RTL shell with a compact right navigation rail, persistent global search, and a restrained navy/paper/teal/amber system.
- Dense company rows compress identity, readiness, score context, evidence quality, workflow, and decision-maker status without exposing twenty-five columns at once.
- Detail is a dossier, not a marketing profile: evidence cards visibly label observed/inference/unknown and source family counts are distinct from URL counts.
- Overview uses modest KPI tiles with context and direct links rather than vanity metrics.
- Use small bars and numbers for scores; reserve prominent accents for readiness and human review state.
- Use system fonts and local assets only; external URLs are explicit actions and are never iframe content.

## Type and spacing system

- Persian-capable system font stack: `Vazirmatn`, `IRANSans`, `Tahoma`, `Arial`, sans-serif.
- Roles: 12–13px metadata, 14px body, 16–18px section titles, 24–32px page titles, with line-height tuned for Persian wrapping.
- Working spacing tokens: 4, 8, 12, 16, 20, 24, 32px; larger gaps are reserved for page-level grouping.
- Tables use 12–13px rows with comfortable vertical padding; long values wrap or truncate only when a visible full-value affordance exists.

## Component/state plan

- Navigation: idle, active, keyboard focus, compact responsive mode.
- Search/command palette: idle, query results, no results, Escape close, keyboard selection.
- Filters: idle, active, reset, no-result state.
- Company rows/cards: hover, focus, selected for compare, favorite, unknown fields.
- Detail: loading, missing data, evidence groups, screenshot lightbox, material loading/error, external-action feedback.
- Review: unreviewed, approved, needs more research, rejected, follow-up, note saved/error.
- Compare: empty, 2–۴ selected, remove selection, limit reached.

## Responsive strategy

- Desktop: right rail plus main content; overview split panels; explorer table.
- Tablet: collapsible rail and stacked overview panels; explorer remains a dense list.
- Narrow mobile: rail becomes a compact top navigation; cards stack; filter panel becomes a disclosure; compare becomes horizontally scrollable but never page-wide overflow.

## Motion posture

- Navigation/view changes: short opacity/translate transition for the main content group.
- Command palette and screenshot lightbox: explicit open/close surface states, Escape and outside-click close, focus return.
- Review save: brief status feedback only; no blocking spinner beyond the local request.
- `prefers-reduced-motion: reduce` removes translation/stagger and preserves immediate visibility.
- Content fails open if JavaScript or an optional asset fails; the server-rendered shell still communicates local-tool context.

## Evidence matrix to capture

| ID | Route/state | Viewports | Evidence |
|---|---|---|---|
| D-OVERVIEW | `/` overview loaded | 1440×1000, 390×844 | screenshot, DOM/runtime, console/network |
| D-COMPANIES | explorer filtered/search result | 1440×1000, 1024×900, 390×844 | screenshot, DOM/runtime, keyboard/filter |
| D-READY | Wave 1 | 1440×1000 | screenshot, DOM/runtime |
| D-SABAH | Sabah detail overview | 1440×1000, 390×844 | screenshot, DOM/runtime |
| D-EVIDENCE | Sabah evidence tab/lightbox | 1440×1000 | screenshot, runtime |
| D-MATERIALS | Sabah sales materials | 1440×1000 | screenshot, runtime |
| D-COMPARE | 2–4 selected companies | 1440×1000, 390×844 | screenshot, runtime |
| D-REVIEW | local review state + note | 1440×1000 | screenshot, runtime/persistence |

## Acceptance tests

- `npm run data:build` reindexes current canonical outputs and reports counts without modifying canonical source files.
- `npm run dev` serves only localhost and exposes no external network dependency.
- ۶٬۰۸۴ records load into an indexed, paginated explorer without rendering all rows.
- Search, filters, score ranges, status/tier/wave/type/evidence/contact/workflow filters, and sorting produce accurate results.
- Sabah detail shows the verified economic buyer, evidence classifications, source families, screenshot gallery, proposal/outreach/dossier, demo links, and review state.
- Review status, favorite, and note persist across refresh through a separate local JSON state.
- Compare mode supports ۲–۴ companies and does not alter canonical records.
- Screenshots are generated headlessly at the required states; console errors, overflow, and external requests are checked.

## Approval boundary

This plan is a provisional implementation plan derived from the user brief. `approvals/design-direction.json` remains `pending`; no user confirmation is fabricated. The project is not eligible for a release verdict until the complete direction and final evidence are explicitly reviewed.
