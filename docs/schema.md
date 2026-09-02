# Data schema

The canonical JSONL record is the source for CSV, XLSX, reports and proposals. One record contains identity, classification, location, public contacts, scale signals, digital/internal-capability signals, evidence, workflow hypotheses, scoring and review state. Evidence and screenshots are also stored in `evidence/companies/<company_id>/`.

Required stable identifiers:

- `company_id`: deterministic `ir-teh-` + 16 hex characters derived from normalized identity/domain/phone.
- `evidence_id`: deterministic hash of company, URL, claim and capture time.
- `workflow_id`: deterministic hash of company and workflow name.

Unknown values are `null`, empty arrays or explicit `UNKNOWN`; they are not inferred from missing fields.

Commercial-audit fields include `original_priority_tier`, `original_luma_opportunity_score`, `original_industry`, `commercial_evidence_strength`, `independent_source_count`, `independent_source_families`, `company_type`, `industry_classification_confidence`, `active_status_evidence`, `company_strength_evidence_status`, `operational_complexity_evidence_status`, `workflow_evidence_classification`, `internal_tech_capability_evidence_status`, `digital_maturity_evidence_status`, `score_confidence`, `confidence_factor`, `confidence_adjusted_score`, `commercial_readiness` and `sales_readiness`.

`source_family` is the unit used for independent-source counting. `workflow_opportunities` contains at most one audit-selected primary workflow with its current-process hypothesis, supporting evidence, solution, owner, data, integrations, risks, KPIs, confidence and discovery questions.
