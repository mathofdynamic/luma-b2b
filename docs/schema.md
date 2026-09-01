# Data schema

The canonical JSONL record is the source for CSV, XLSX, reports and proposals. One record contains identity, classification, location, public contacts, scale signals, digital/internal-capability signals, evidence, workflow hypotheses, scoring and review state. Evidence and screenshots are also stored in `evidence/companies/<company_id>/`.

Required stable identifiers:

- `company_id`: deterministic `ir-teh-` + 16 hex characters derived from normalized identity/domain/phone.
- `evidence_id`: deterministic hash of company, URL, claim and capture time.
- `workflow_id`: deterministic hash of company and workflow name.

Unknown values are `null`, empty arrays or explicit `UNKNOWN`; they are not inferred from missing fields.
