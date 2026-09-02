# Commercial quality audit

The audit is a bounded re-enrichment pass over the 151 companies that entered the repository as Tier A/B. It never expands the candidate universe. It uses targeted Persian-first public searches, the original public source records, reachable company pages and evidence packages. Search results are used to locate corroborating pages; they are not converted into new company records.

## Evidence strength

`commercial_evidence_strength` is a 0–100 measure of how strongly public evidence supports a commercially meaningful LUMA prospect. It combines supported active status, scale/complexity signals, workflow evidence, usable public pages and independent source-family coverage. The score is capped when coverage is thin: one independent family is capped at 49; an Avval-plus-company-site pair is capped at 72; two non-directory families at 82; three at 92; four or more at 100.

`independent_source_count` counts source families, not URLs. Multiple Book-e Avval pages count as `book_e_avval`; multiple pages on one company domain count as one `company_website:<domain>` family; search engines are excluded from the independent count.

## Unknown policy

Absence of a public technical-team signal is `UNKNOWN_INTERNAL_TECH`, not `KNOWN_LOW_INTERNAL_TECH`. UNKNOWN tech and digital-maturity fields receive neutral values and reduce `score_confidence`. Explicit public statements about manual/Excel/no-software operation are eligible for `KNOWN_LOW_INTERNAL_TECH`, but the audit does not infer this from a poor website.

## Workflow validation

One primary workflow is retained only when company-page signals support it. The classification is `EVIDENCE_SUPPORTED`, `STRONG_HYPOTHESIS`, `WEAK_HYPOTHESIS` or `UNSUPPORTED`. A workflow hypothesis never states that the company currently has a manual or inefficient process unless that fact is directly observed.

## Sales gates

Tier A requires the READY gate, an opportunity score of at least 80, supported active operation, at least two independent source families, commercial evidence strength of at least 70, score confidence of at least 65, a supported/strong workflow hypothesis and no known high internal technical capability. Tier B uses the documented evidence/workflow gates but does not imply outreach readiness. Proposals are generated only for `READY FOR OUTREACH` records.

See `reports/ranking_audit.md` for changes from the first run and `reports/sales_ready_prospects.md` for the actionable ranking.
