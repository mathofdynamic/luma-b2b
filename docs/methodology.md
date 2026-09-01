# Methodology

## Objective

Find established Tehran-area organizations that could plausibly buy a bounded custom AI/software/workflow project from LUMA. The pipeline is a prospecting aid, not a legal, financial or market-size database.

## Research basis

The five supplied reports were copied byte-for-byte into `research/source/` and synthesized in `research/synthesis.md`. The production model adopts their shared emphasis on industrial/distribution complexity, document-heavy workflows, moderate digital maturity, measurable operations value, Persian-first discovery and role-based outreach. Where reports disagree, the disagreement is retained and the chosen assumption is explicit in the synthesis.

## Evidence boundary

An observation is directly stated or visibly demonstrated by a public source. An inference is labelled and tied to observations. A workflow hypothesis never claims that a company manually performs a process unless public evidence demonstrates it. Missing facts are `UNKNOWN`.

## Pipeline stages

1. Read and preserve source research.
2. Discover public candidates from multiple sources.
3. Normalize Persian/Arabic characters and digits and deduplicate into stable company IDs.
4. Enrich public directory/company pages with conservative rate limits.
5. Preserve source rows, text evidence and source timestamps.
6. Capture selected rendered pages in isolated headless browser sessions.
7. Score all records and generate bounded workflow hypotheses.
8. Generate proposals only for sufficiently researched A and strong B prospects.
9. Export CSV, JSONL and XLSX and generate reports.
10. Run automated QA plus manual visual checks of representative prospect evidence.

## Research status

`DISCOVERED` means a canonical public discovery record exists. `MEANINGFULLY_ENRICHED` means this run has at least a public description, a Tehran-area address and a public corporate landline, or an equivalent public website/profile evidence path. This label does not assert active status or purchasing power.

## Network safety

All Iranian process traffic uses the verified localhost proxy in `config/sources.yaml`. The VPN remains a system-level connection for normal traffic. Preflight compares direct-proxy and normal-route egress and stops a relevant batch when the direct proxy fails.
