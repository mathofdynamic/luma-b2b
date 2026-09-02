# LUMA B2B dashboard — UI improvement audit

Date: 2026-09-02
Mode: `improve`
Scope: existing local review dashboard under `dashboard/`
Product files changed in this audit: none

## Baseline and verification

- The current dashboard is served locally at `http://127.0.0.1:5174`.
- The existing OCD Designer state validates successfully.
- `npm run qa` passes: 6,084 indexed companies, 32 ready companies, 10 Wave 1 companies, 173 evidence packages, 140 evidence screenshots, 32 proposals/outreach/dossiers, and 1 detected demo.
- Headless Chromium checks covered overview, companies, sales-ready, evidence, review, compare, and Sabah overview/evidence/materials/history states at 1,440, 1,280, 1,024, 768, and 390px where applicable.
- Runtime interaction checks passed for Persian search, command palette open/Escape close, evidence lightbox open/Escape close, and local Markdown material loading.
- No console/page/request errors or document-level horizontal overflow were found in the sweep.
- The current 390px Sabah baseline is preserved as OCD evidence `E-0020` (`D-SABAH`) and is intentionally not an after-state.

## Findings

### UI-001 — critical responsive information failure

- Severity: `CRITICAL`
- Routes/states: company detail overview, especially Sabah at 390px; also tablet widths below 1,040px
- Components: `.detail-two-col`, decision makers, public contacts
- Expected: the two secondary dossier panels should stack before either becomes too narrow to read.
- Actual: `.detail-two-col` remains a two-column grid at 390px. Each child is approximately 142px wide, while the contact panel grows to about 2,776px because the phone list wraps one number per line. The screenshot makes both panels effectively unreadable and creates an unnecessarily long dossier.
- Source: `dashboard/app/styles.css:578`, responsive rules at `dashboard/app/styles.css:754-867`; headless geometry sweep and durable baseline `E-0020`.
- Correction: add an explicit stacking rule for `.detail-two-col` at the narrow breakpoint, then redesign dense contact values as compact grouped channels with an accessible reveal for long phone/email lists. Keep every public value available.
- Acceptance: at 390px and 768px, decision makers and contacts render as readable full-width panels; no critical text is reduced below a usable measure; the contact section has a compact default state and an explicit reveal for all values.

### UI-002 — important review text is silently truncated

- Severity: `HIGH`
- Routes/states: Companies explorer, Evidence desk, Review queue
- Components: company rows, evidence rows, review opportunity cells, source/location metadata
- Expected: workflow names, location context, and source-family context must support a review decision without opening every record.
- Actual: several high-value strings use one-line ellipsis with no title, expansion, or other full-value affordance. Examples include `تطبیق BOQ و مشخصات فنی برای پیشنهاد پروژه`, `دریافت اسناد حمل و پیگیری نقص پرونده`, long location/source-family labels, and Sabah's long evidence reasons.
- Source: `dashboard/app/styles.css:396-410`, `467-482`, `617-643`; headless clipping sweep at 1,440/1,280/1,024/768/390px.
- Correction: use two-line wrapping/clamping for decision-critical fields, expose full values through an accessible details affordance or tooltip, and reserve ellipsis for secondary metadata such as domains and file paths.
- Acceptance: key workflow and qualification context is readable or explicitly expandable at desktop, tablet, and mobile widths; the full value is available to keyboard and assistive-technology users.

### UI-003 — dossier hierarchy is dense and source-machinery-forward

- Severity: `HIGH`
- Routes/states: Sabah overview, evidence, materials, history
- Components: detail section headings, evidence cards, source-family cards, contact/decision panels, materials placeholder
- Expected: a human reviewer should see the decision-relevant summary first, with provenance available immediately but visually secondary.
- Actual: the dossier mixes Persian headings with raw English labels/codes (`Executive summary`, `Public contact`, `Textual evidence`, `EVIDENCE_SUPPORTED`, `confidence`, `family`) and presents many small cards before a clear scan path. The materials tab initially shows only a file path and a `نمایش سند` action, so the content is not visible until an additional click.
- Source: `dashboard/app/views.js:164-165`, `330-375`, `356-361`, `378-388`; baseline screenshots `E-0014`–`E-0016` and `/tmp/luma-dashboard-improve-baseline/` captures.
- Correction: establish a clear primary/secondary information contract: Persian decision label and human summary first; provenance, machine labels, paths, and raw metadata in a secondary row or disclosure. Show a short material excerpt or the most sales-relevant document by default while preserving lazy loading for the full file.
- Acceptance: the first viewport of each detail tab answers what the company is, why it matters, what is uncertain, and what to do next; raw provenance remains available without dominating the page.

### UI-004 — section heading/action layout needs an adaptive state

- Severity: `MEDIUM`
- Routes/states: detail tabs and overview panels at tablet/narrow widths
- Components: `.section-heading` and action controls
- Expected: section title, explanatory copy, and action should maintain a clear hierarchy when the available width narrows.
- Actual: `.section-heading` stays a horizontal flex row with fixed action behavior; at narrow widths headings become taller while the action has no explicit stack/priority treatment. This is not currently causing page overflow, but it increases squeeze and makes controls easy to miss.
- Source: `dashboard/app/styles.css:284-287`, responsive rules at `dashboard/app/styles.css:771-827`; geometry sweep.
- Correction: add a narrow stacked state with actions aligned to the reading direction and a consistent minimum target size.
- Acceptance: heading/action pairs are readable and consistently positioned at 390, 768, and 1,024px, with visible focus states.

### UI-005 — unknown and low-confidence information needs stronger scanning semantics

- Severity: `MEDIUM`
- Routes/states: company detail profile, evidence, score surfaces, compare
- Components: unknown values, confidence labels, score rows
- Expected: unknown should be visibly deliberate and should not be confused with an empty or failed field.
- Actual: the dashboard preserves `نامشخص`, but unknown fields are visually similar to low-priority metadata and can leave sparse grids that feel broken. Confidence is often a small trailing value rather than a clear “what this means” cue.
- Source: `dashboard/app/views.js:154-156`, `172-178`, detail renderers; baseline Sabah screenshots.
- Correction: standardize a compact unknown state with reason/context where available, and pair confidence with the claim/metric it qualifies. Keep the distinction between observed, inference, and unknown intact.
- Acceptance: a reviewer can distinguish known fact, inference, and unknown within one scan without opening raw files; empty/missing and unavailable/error states remain distinct.

### UI-006 — compare and sales-ready routes need stronger next-action framing

- Severity: `MEDIUM`
- Routes/states: Compare empty/selected, Sales Ready, Review
- Components: empty state, ready cards, review rows, compare dock
- Expected: every high-intent route should make the next review action obvious while keeping analysis secondary.
- Actual: the core interactions work, but the visual hierarchy is repetitive: the Sales Ready cards expose similar score blocks, the Review queue is very long, and the empty Compare state depends on the user already understanding that selection starts elsewhere.
- Source: `dashboard/app/views.js:264-285`, `276-280`, `282-285`; baseline screenshots `E-0013`, `E-0017`, `E-0018`.
- Correction: add a compact “why this is here / next action” line to curated cards, make Compare empty state link directly to a clearly filtered starting set, and add stronger grouping for review priority.
- Acceptance: a user can identify the next action on Sales Ready, Compare empty, and Review without scanning all rows.

### UI-007 — accessible full-value and control labeling coverage

- Severity: `MEDIUM`
- Routes/states: Companies filters and any truncated evidence/contact value
- Components: filter selects, ellipsized links, disclosure/reveal controls
- Expected: all controls and truncated content should have an accessible name and keyboard-equivalent way to recover the full value.
- Actual: the route-level control sweep found 12 filter `select` elements without a reliable accessible-name signal under the current DOM heuristic; the current UI also has no general full-value affordance for several ellipsized review fields.
- Source: `dashboard/app/views.js:236-238`, `240-251`; headless DOM control sweep.
- Correction: add explicit `id`/`for` or `aria-label` wiring for filter controls and test focus order, Escape behavior, and reveal semantics after implementation.
- Acceptance: zero unnamed interactive controls in the custom audit; keyboard users can reach and understand every filter, expansion, lightbox, and local-review action.

## Prioritized remediation plan

1. **Restore readable information architecture at every width.** Fix the detail two-column breakpoint, compact long contacts, and make section headings/action controls responsive. This resolves UI-001 and UI-004 first because they block basic reading.
2. **Protect decision-critical text.** Replace silent truncation for workflow, location, source-family, evidence-reason, and review fields with wrapping plus accessible expansion. Keep domains and file paths compact but recoverable. This resolves UI-002.
3. **Clarify the dossier scan path.** Refactor detail sections so the first read is summary → opportunity → evidence quality → contacts/decision makers → provenance. Keep research semantics and source links, but move raw machine labels and paths to secondary metadata. Make materials useful on first entry with an excerpt/default document. This resolves UI-003 and UI-005.
4. **Improve high-intent route actions.** Give Sales Ready, Compare empty, and Review a clearer “what to do next” hierarchy without adding dashboard clutter. This resolves UI-006.
5. **Harden interaction/accessibility states.** Wire explicit filter labels, verify keyboard/focus behavior, and add full-value reveals. Re-test loading, empty, disabled, error, and reduced-motion states. This resolves UI-007.
6. **Run an independent visual QA pass.** Re-capture overview, companies, Sales Ready, Sabah overview/evidence/materials, Compare, and Review at 1,440, 1,024, 768, and 390px; run `npm run qa`; compare against the preserved baseline; then record after-state evidence in OCD Designer without overwriting `E-0020` or earlier baseline artifacts.

## Approval boundary

This is an improvement audit and remediation proposal only. The existing provisional design direction remains pending user confirmation, and no product files were changed during this pass. Product-file mutation should begin only after the user explicitly approves this complete remediation direction.
