# LUMA Tehran B2B research synthesis

Research basis: the five source reports preserved verbatim in `research/source/`. The reports were read in full before pipeline construction. This synthesis is a strategic interpretation, not a replacement for the originals.

## Where the reports agree

All five reports converge on the same commercial thesis: LUMA should sell custom operational software and AI-assisted workflows to established Tehran-area B2B companies, not generic AI subscriptions. The strongest prospects combine meaningful scale, repeated operational work, usable digital material, visible process friction, limited internal AI/software capability, measurable ROI and reachable management.

The consistent target profile is a private or privately controlled mid-market company with roughly 50–500 employees (larger companies can qualify when the relevant unit is still under-digitized), a factory, warehouse, project portfolio, branch network or document-heavy commercial operation, and a mixed stack of local ERP/accounting software, Excel, PDFs, email, phone and messaging. Very small shops, inactive entities, early unstable startups, state/public organizations with diffuse procurement, digitally native software companies and organizations with strong internal engineering/AI teams are consistently poor first-wave targets.

The reports agree that Persian-first discovery and evidence preservation are essential; no single directory is authoritative. They repeatedly recommend Tehran Chamber, ISIPO/industrial-estate sources, sector associations, exhibitions, company websites, maps, legal/company databases, job boards, LinkedIn and public social/news sources as a source stack. Official registries and company/association sources should outrank directories and social signals.

The most repeated workflow families are RFQ/quotation, product or SKU matching, order intake, document extraction, tender/BOQ/contract processing, inventory and procurement exceptions, production/QC/maintenance reporting, shipment documents, internal knowledge search, customer-service assistance and management reporting. The preferred delivery pattern is a bounded pilot with human approval, local/on-premise or controlled deployment, read-only integration first, and a measurable before/after KPI.

The reports also agree on the digital-maturity paradox: almost no digital process is too immature to support reliable automation, while digital-native companies with modern engineering/data teams are often able to build internally. The sweet spot is an organization with a usable digital core but fragmented, manual or poorly integrated edge workflows.

## Where the reports disagree

### Segment ordering

The market-level rankings differ because they use different weights and evidence frames:

- The 2026–2027 report puts distributors/importers first, followed by manufacturing, auto parts, food/FMCG, medical equipment, EPC, logistics, pharma and packaging.
- The shorter market study puts customs/freight first, then FMCG distribution, manufacturing, pharma/medical, packaging, private healthcare and auto parts.
- The high-potential report puts industrial equipment/material distributors first, followed by food/FMCG manufacturing/distribution, manufacturing, packaging, EPC, medical equipment, building/MEP, pharma, logistics and auto parts.
- The earliest report ranks import/export/wholesale first, then auto parts, construction materials, pharma, food, healthcare, packaging and freight.

These are not company-level findings. They are directional market hypotheses. The apparent conflict is resolved operationally by using eight priority batches, measuring source coverage and evidence quality, and letting company-level evidence—not the market rank alone—determine score and effort.

### Numeric scores and thresholds

Market scores range from the mid-70s to the mid-90s across reports. Formulae also differ: one report uses seven weighted factors, another uses 0–5 factors summing to 100, and another uses a 12-factor normalized model with a Gaussian digital-maturity fit. Thresholds vary from 75 for a priority prospect to 85 for Tier A. These numbers are estimates and must not be treated as observed company facts.

Production adoption: use the most auditable 12-component model from the latest evidence-first report, with normalized 0–100 component fields, a non-linear `G(d) = exp(-((d-55)/24)^2)` maturity fit, trigger bonuses, risk penalties and hard disqualifiers. For operational labels, retain the user-requested tiers: A ≥80, B 70–79, C 60–69, D 45–59, Reject <45. Tier A/B proposals additionally require minimum evidence and manual-review flags. This preserves the user's stricter qualification gate while retaining the research's useful score components.

### Company-size ranges

Most reports center on 50–500 employees; specific ICPs vary from 20–150 trading houses to 100–800 FMCG operators and 80–1,000 EPC/manufacturing firms. Production therefore stores ranges and confidence rather than pretending to know an exact headcount. A company can qualify through strong operational evidence even when public employee count is unknown, but unknowns lower score confidence and proposal eligibility.

### Healthcare and regulated work

Some reports rank private hospitals, laboratories, pharma and medical equipment highly because of budget and document volume; others emphasize regulatory friction and sales-cycle difficulty. Production adopts the common safe boundary: prioritize administrative, knowledge, document, service and tender support; do not propose autonomous diagnosis, treatment, credit, legal conclusions or irreversible decisions. Regulatory burden is a scored component and a proposal risk note.

### ROI claims

Some source examples mention possible percentage reductions. The reports also repeatedly warn that such values are estimates. Production never copies an unsupported percentage into a company record or proposal. It stores KPI hypotheses and missing baseline inputs; quantified ROI is only a discovery-stage validation item.

## Adopted production assumptions

1. **Scope:** Tehran city and Tehran Province, including Tehran-headquartered companies with operations elsewhere. A location hint alone never qualifies an account.
2. **Discovery breadth:** use multiple public source types and keep every discovery URL/snippet. Directory records are leads, not validation.
3. **Qualification:** candidate records remain in the master dataset even when rejected; rejection reason and evidence are preserved.
4. **Evidence classes:** `OBSERVED`, `STRONG_INFERENCE`, `WEAK_INFERENCE`, `UNKNOWN`. Every material observation has URL, title, timestamp, confidence and short quote/snippet.
5. **Digital maturity:** rate observed maturity separately from `digital_maturity_fit_score`; both extremes are penalized and the moderate/fragmented middle is favored.
6. **Internal capability:** software/AI/data hiring and a software-product business materially lower outsourcing fit. Absence of a public signal is not proof that a team does not exist.
7. **Proposal gate:** only sufficiently researched Tier A and strong Tier B records with at least two independent factual observations, a scale signal, a workflow/data signal, role-first contact path and no hard disqualifier receive proposals.
8. **Network:** Iranian research traffic is isolated through the verified direct HTTP proxy `http://127.0.0.1:1087`; the VPN remains untouched. Preflight failure stops the relevant batch.
9. **Browser:** all browser work is headless, isolated and proxied. Browser failures are recorded as `HEADLESS_BLOCKED` rather than repaired with a visible browser.
10. **Scale:** the discovery runner seeks 1,000+ raw candidates and uses measured counts to report whether enrichment/scoring targets are genuinely achieved. It never manufactures rows to hit a target.

## Recommended workflow logic

For each strong company, the pipeline follows: observable company operation → repeated human handoff → likely cost/delay/error → public data asset → narrow LUMA workflow → human approval → KPI to validate. The primary proposal names one workflow only. Typical required data includes catalogs, prices, inventory, RFQs, ERP/Excel exports, PDFs, service history, project documents or job/role signals. Integration and security unknowns remain explicit.

## Unresolved assumptions to validate

- Public directory presence correlates with active purchasing power.
- Public website/catalog quality is a useful but imperfect digital-maturity signal.
- Local ERP/accounting data exists and can be exported without a replacement project.
- Operational volume is high enough for a measurable pilot.
- A reachable economic buyer exists behind the public company record.
- The company has permission to use the documents needed for a pilot.
- Local hosting, data residency and integration constraints can be met for the use case.
- Sector ranking will remain stable after company-level win/loss and delivery data are collected.

The production dataset marks each of these as `UNKNOWN` until public evidence or future human discovery validates it.
