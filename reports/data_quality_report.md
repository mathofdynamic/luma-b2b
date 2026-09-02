# Data Quality Report

This report is generated before the final QA command and is supplemented by `logs/qa-*.json`.

Canonical records: 6,084; raw rows: 6,576; enriched: 900; scored: 6,084. Current commercial-audit outputs cover 151 existing A/B records, 25 Tier A, 7 Tier B, 140 screenshots and 32 proposals.

## Known issues

- A public industrial-estate index provides valuable activity discovery but not legal activity, size or purchasing power; index-only rows are marked DISCOVERED and capped below B/A.
- Some Avval listing records are meaningfully enriched under this run's operational definition (description + Tehran address + public landline) but still lack independent corroboration.
- Website, employee, founding-year, legal-ID, branch and active-status fields can remain UNKNOWN.
- The first run's exact-name search enrichment was stopped after direct-proxy timeouts; the commercial audit used a bounded set of targeted public URLs and did not fall back to the VPN.

## QA commands

Run `python3 -m src.utilities.qa --input data/normalized/companies.jsonl` after exports and evidence capture. The command checks identity uniqueness, score/tier consistency, URL presence, screenshot metadata, encoding, credentials patterns, and network/browser provenance.

## Manual commercial review

`logs/manual-qa-20260902T052252Z.json` covers all 30 top corrected prospects, all 9 records with raw score at least 85, all 32 READY FOR OUTREACH records, and a fixed-seed sample of 10 demotions. It records zero record/package/workflow/proposal/dossier errors and confirms that the reviewed screenshots are headless and company-matched. A Babco trust-seal error-page capture was replaced with its public company profile before this manifest was rerun.

## Final QA

Status: **PASSED**
Generated: 2026-09-02T05:26:31Z

| Check | Result |
|---|---:|
| Canonical companies | 6,084 |
| Meaningfully enriched | 900 |
| Scored | 6,084 |
| Tier A / B | 25 / 7 |
| Evidence packages / screenshots | 173 / 140 |
| Workbook sheets | 10 |
| Secret-pattern hits | 0 |

### Warnings

- Public-source capture errors retained in company packages: 555

### Critical issues

- None
