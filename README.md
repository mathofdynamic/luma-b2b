# LUMA B2B

Evidence-backed Tehran B2B prospect discovery, qualification, workflow-opportunity analysis and proposal generation for LUMA custom AI/software projects.

## Initial discovery-run results

- 6,576 raw candidate rows
- 6,084 canonical companies after normalization and deduplication
- 900 records meaningfully enriched under the documented public-evidence definition
- 6,084 records scored
- 32 Tier A and 119 Tier B records under the evidence-first scoring model
- 134 metadata-complete real headless screenshots captured across 135 evidence packages
- 100/100 ranked top-prospect records have a visual evidence package and screenshot

## Current commercial-audit results

- The audit re-enriched **151 existing Tier A/B records only**; no discovery rows were added.
- Revised tiers: **25 Tier A**, **7 Tier B**, **6 Tier C**, **5 Tier D**, **108 Reject** within that audited cohort.
- Sales readiness: **32 READY FOR OUTREACH**, **8 NEEDS DISCOVERY**, **111 NOT READY**.
- **32 evidence-backed proposals** were retained/regenerated; generic first-run proposals outside the READY gate were removed.
- The refreshed audit evidence set contains **140 headless screenshots across 173 evidence packages**; six missing A/B visuals were captured through the direct proxy.
- Human-quality dossiers are under `reports/dossiers/`; the actionable ranking is `reports/sales_ready_prospects.md`.
- The original top-100 artifact is preserved with an audit notice. Do not use it as a sales list without the commercial audit status.

These are research signals, not claims of revenue, legal standing, buying authority or internal workflow pain. Unknown values stay `UNKNOWN`.

## Scope

The primary scope is Tehran city and Tehran Province, including Tehran-headquartered organizations with facilities elsewhere. Priority segments are industrial distributors/importers, industrial manufacturers, food/FMCG, logistics/freight/customs, printing/packaging/labeling, medical equipment, auto parts, EPC/engineering, building materials/MEP, industrial maintenance/after-sales and pharmaceutical companies.

## Method

The pipeline reads the five source reports copied exactly into `research/source/`, records strategic agreement/disagreement in `research/synthesis.md`, discovers Persian-first public records, normalizes names/characters/digits, connects duplicate identities, enriches public company pages, preserves source-backed evidence, detects bounded workflow hypotheses, scores every company and exports review artifacts. The bounded commercial audit re-checks existing A/B records with independent-source counts, evidence strength, explicit UNKNOWN states, company-type correction, workflow validation and confidence-adjusted ranking.

The first production run uses Book-e Avval category pages, public official/association references, Persian search results where responsive, and the public VIC industrial-estate index for Shamsabad, Abbasabad, Parand, Nasirabad, Qods and Qarchak. No one directory is authoritative. Industrial-estate index membership alone never qualifies a company as A/B.

## Scoring

Every score component is stored separately in `data/master_companies.jsonl` and the workbook. Digital maturity is non-linear: moderate/fragmented maturity is favored, while a missing operating layer and strong internal engineering capability reduce outsourcing fit. UNKNOWN is neutral and confidence-reducing, not evidence of low internal capability. `confidence_adjusted_score = luma_opportunity_score × (0.40 + 0.60 × score_confidence / 100)`. See `docs/scoring.md`, `docs/commercial_audit.md` and `research/synthesis.md`.

## Evidence and screenshots

Each company package is under `evidence/companies/<company_id>/` with `sources.json`, `notes.md`, `pages/` and `screenshots/`. Textual evidence distinguishes `OBSERVED`, `STRONG_INFERENCE`, `WEAK_INFERENCE` and `UNKNOWN`. Screenshots are captured only from public pages with isolated headless Playwright sessions; no regular browser profile, cookies or private portal is used.

## Network and browser requirement

Keep the VPN connected. Iranian research traffic must use the already-verified direct proxy:

```text
http://127.0.0.1:1087
```

The headless browser configuration is `config/playwright.headless.json`. A future browser job should use the Playwright wrapper with that config, for example:

```bash
python3 -m src.utilities.network_preflight --proxy http://127.0.0.1:1087
~/.codex/skills/playwright/scripts/playwright_cli.sh -s=luma-b2b-<job-id> open https://example.ir --config config/playwright.headless.json
```

Do not use `open -a`, `open -na`, GUI automation, a regular Chrome profile, VPN commands or system proxy changes. If preflight fails, stop the relevant batch and retain the failure in `logs/`.

## Re-run commands

```bash
python3 -m src.utilities.network_preflight --proxy http://127.0.0.1:1087
python3 -m src.discovery.run --config config/sources.yaml
python3 -m src.discovery.vic --config config/sources.yaml
python3 -m src.discovery.merge
python3 -m src.enrichment.enrich --input data/raw/candidates.jsonl --priority-file data/normalized/companies.jsonl --max-workers 1 --max-profiles 220 --max-sites 80 --rate-limit-seconds 1.0
python3 -m src.scoring.score --input data/normalized/companies.jsonl
python3 -m src.evidence.capture --input data/normalized/companies.jsonl --min-score 70 --limit 100 --proxy http://127.0.0.1:1087
python3 -m src.proposals.generate --input data/normalized/companies.jsonl
python3 -m src.exports.generate --input data/normalized/companies.jsonl
node src/exports/build_workbook.mjs
python3 -m src.reports.generate --input data/normalized/companies.jsonl
python3 -m src.utilities.qa --input data/normalized/companies.jsonl

# Bounded commercial audit of the existing A/B cohort
python3 -m src.audit.commercial --input data/normalized/companies.jsonl --proxy http://127.0.0.1:1087
python3 -m src.proposals.generate --input data/normalized/companies.jsonl
python3 -m src.exports.generate --input data/normalized/companies.jsonl
node src/exports/build_workbook.mjs
python3 -m src.audit.report --input data/normalized/companies.jsonl
python3 -m src.utilities.qa --input data/normalized/companies.jsonl
```

For a full discovery refresh, `src.discovery.run` now includes the configured VIC connector. The separate `src.discovery.vic` plus `src.discovery.merge` commands are useful for refreshing only industrial-estate sources without repeating every source.

## Outputs

- Main dataset: `data/master_companies.csv`, `data/master_companies.jsonl`
- Excel workbook: `data/master_companies.xlsx`
- Tier exports: `data/tier_a.csv`, `data/tier_b.csv`, `data/rejected.csv`
- Proposals: `proposals/<company_id>.md`
- Reports: `reports/`
- Commercial audit report: `reports/ranking_audit.md`
- Sales-ready report: `reports/sales_ready_prospects.md`
- Human dossiers: `reports/dossiers/`
- Evidence: `evidence/companies/`
- Run logs: `logs/`

## Limitations

Public research cannot establish exact company strength, active status, employee count, budget, decision authority, current data volume or internal manual process. Personal phone numbers and non-public personal emails are excluded. Search-engine blocks, site failures and unknown fields are recorded rather than silently substituted with VPN traffic or invented facts.
