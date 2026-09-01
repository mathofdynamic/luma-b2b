# Data Quality Report

This report is generated before the final QA command and is supplemented by `logs/qa-*.json`.

Canonical records: 6,084; raw rows: 6,576; enriched: 900; scored: 6,084; screenshots: 134; proposals: 59.

## Known issues

- A public industrial-estate index provides valuable activity discovery but not legal activity, size or purchasing power; index-only rows are marked DISCOVERED and capped below B/A.
- Some Avval listing records are meaningfully enriched under this run's operational definition (description + Tehran address + public landline) but still lack independent corroboration.
- Website, employee, founding-year, legal-ID, branch and active-status fields can remain UNKNOWN.
- Exact-name search enrichment timed out through the direct proxy and was stopped; no VPN fallback was used.

## QA commands

Run `python3 -m src.utilities.qa --input data/normalized/companies.jsonl` after exports and evidence capture. The command checks identity uniqueness, score/tier consistency, URL presence, screenshot metadata, encoding, credentials patterns, and network/browser provenance.

## Final QA

Status: **PASSED**
Generated: 2026-09-01T09:38:12Z

| Check | Result |
|---|---:|
| Canonical companies | 6,084 |
| Meaningfully enriched | 900 |
| Scored | 6,084 |
| Tier A / B | 32 / 119 |
| Evidence packages / screenshots | 135 / 134 |
| Workbook sheets | 10 |
| Secret-pattern hits | 0 |

### Warnings

- Public-source capture errors retained in company packages: 66

### Critical issues

- None
