"""Create reproducible CSV/JSONL exports from the canonical scored JSONL."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from src.utilities.common import now_iso, path_for, read_jsonl, write_jsonl


COMPANY_COLUMNS = [
    "company_id", "company_name_fa", "brand_name_fa", "company_name_en", "aliases", "national_id", "registration_no", "legal_status",
    "industry", "industry_fa", "sub_industry", "business_model", "description_observed", "hq_address", "city", "province", "tehran_area", "industrial_zone",
    "operational_addresses", "map_listing_urls", "latitude", "longitude", "phone_public", "email_public", "website", "domain", "website_status", "linkedin_company_page", "social_profiles",
    "employee_estimate_min", "employee_estimate_max", "employee_confidence", "founded_year", "company_age_years", "branches_count", "warehouses_count", "factories_count", "geographic_reach",
    "visible_customers", "visible_projects", "products_services", "certifications", "association_memberships", "active_jobs_count", "job_families", "existing_software_signals", "portal_features", "document_types_public",
    "research_status", "last_research_date", "raw_record_count", "source_urls", "discovery_reasons", "evidence_count", "screenshot_count", "hard_disqualifier",
    "company_strength_score", "operational_complexity_score", "workflow_density_score", "ai_roi_score", "data_readiness_score", "digital_maturity_score", "digital_maturity_fit_score",
    "internal_tech_capability_score", "outsourcing_fit_score", "sales_access_score", "expected_project_value_score", "implementation_score", "sales_cycle_ease_score", "regulatory_score",
    "trigger_bonus", "risk_penalty", "luma_opportunity_score", "priority_tier", "score_confidence", "qualification_reason", "strongest_observed_evidence", "decision_maker_role", "decision_maker_name_public",
    "decision_maker_source_url", "decision_maker_confidence", "strongest_workflow", "proposal_path",
]


def cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def screenshot_count(company_id: str) -> int:
    directory = path_for("evidence", "companies", company_id, "screenshots")
    if not directory.exists():
        return 0
    return sum(1 for item in directory.iterdir() if item.is_file() and item.suffix.lower() == ".png" and not item.name.startswith("._"))


def row_for(company: dict[str, Any]) -> dict[str, Any]:
    workflow = (company.get("workflow_opportunities") or [{}])[0]
    return {
        **{key: company.get(key) for key in COMPANY_COLUMNS},
        "aliases": company.get("aliases"),
        "business_model": company.get("business_model"),
        "operational_addresses": company.get("operational_addresses"),
        "map_listing_urls": company.get("map_listing_urls"),
        "social_profiles": company.get("social_profiles"),
        "visible_customers": company.get("visible_customers"),
        "visible_projects": company.get("visible_projects"),
        "products_services": company.get("products_services"),
        "certifications": company.get("certifications"),
        "association_memberships": company.get("association_memberships"),
        "job_families": company.get("job_families"),
        "existing_software_signals": company.get("existing_software_signals"),
        "portal_features": company.get("portal_features"),
        "document_types_public": company.get("document_types_public"),
        "source_urls": company.get("source_urls") or company.get("evidence_urls"),
        "discovery_reasons": company.get("discovery_reasons"),
        "evidence_count": len(company.get("evidence", [])),
        "screenshot_count": screenshot_count(company["company_id"]),
        "strongest_observed_evidence": company.get("strongest_observed_evidence"),
        "strongest_workflow": workflow.get("workflow_name"),
        "proposal_path": str(Path("proposals") / f"{company['company_id']}.md") if company.get("proposal_available") else "",
    }


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: cell(row.get(key)) for key in columns})


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the canonical LUMA B2B dataset")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    args = parser.parse_args()
    companies = read_jsonl(args.input)
    company_rows = [row_for(company) for company in companies]
    for company, row in zip(companies, company_rows):
        company["proposal_available"] = Path("proposals", f"{company['company_id']}.md").exists()
        row["proposal_path"] = str(Path("proposals") / f"{company['company_id']}.md") if company["proposal_available"] else ""
    all_rows = sorted(company_rows, key=lambda row: (-int(row.get("luma_opportunity_score") or 0), row.get("company_name_fa") or ""))
    tier_a = [row for row in all_rows if row.get("priority_tier") == "A"]
    tier_b = [row for row in all_rows if row.get("priority_tier") == "B"]
    rejected = [row for row in all_rows if row.get("priority_tier") == "Reject"]
    write_csv(path_for("data", "master_companies.csv"), all_rows, COMPANY_COLUMNS)
    write_csv(path_for("data", "tier_a.csv"), tier_a, COMPANY_COLUMNS)
    write_csv(path_for("data", "tier_b.csv"), tier_b, COMPANY_COLUMNS)
    write_csv(path_for("data", "rejected.csv"), rejected, COMPANY_COLUMNS)
    write_jsonl(path_for("data", "master_companies.jsonl"), companies)
    # These compact indexes are convenient for the workbook and downstream QA.
    workflow_rows = [workflow for company in companies for workflow in company.get("workflow_opportunities", [])]
    decision_rows = [{
        "company_id": company.get("company_id"), "company_name_fa": company.get("company_name_fa"),
        "decision_maker_role": company.get("decision_maker_role"), "decision_maker_name_public": company.get("decision_maker_name_public"),
        "source_url": company.get("decision_maker_source_url"), "confidence": company.get("decision_maker_confidence"),
    } for company in companies]
    source_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    for company in companies:
        for source in company.get("source_records", []):
            source_rows.append({"company_id": company.get("company_id"), "company_name_fa": company.get("company_name_fa"), **source})
        for evidence in company.get("evidence", []):
            evidence_rows.append({"company_id": company.get("company_id"), "company_name_fa": company.get("company_name_fa"), **evidence})
    write_jsonl(path_for("data", "normalized", "workflows.jsonl"), workflow_rows)
    write_jsonl(path_for("data", "normalized", "decision_makers.jsonl"), decision_rows)
    write_jsonl(path_for("data", "normalized", "sources_export.jsonl"), source_rows)
    write_jsonl(path_for("data", "normalized", "evidence_index.jsonl"), evidence_rows)
    write_jsonl(path_for("data", "normalized", "rejected.jsonl"), [company for company in companies if company.get("priority_tier") == "Reject"])
    print(json.dumps({"generated_at": now_iso(), "companies": len(companies), "tier_a": len(tier_a), "tier_b": len(tier_b), "rejected": len(rejected)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
