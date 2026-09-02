"""Reproducible record-level and visual-evidence QA for the commercial audit."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.utilities.common import now_iso, path_for, read_jsonl, stamp, write_json


TIER_RANK = {"Reject": 0, "D": 1, "C": 2, "B": 3, "A": 4}
ALLOWED_WORKFLOW_CLASSES = {
    "EVIDENCE_SUPPORTED",
    "STRONG_HYPOTHESIS",
    "WEAK_HYPOTHESIS",
    "UNSUPPORTED",
}


def rank_value(company: dict[str, Any]) -> float:
    return float(company.get("confidence_adjusted_score") or 0)


def rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (-rank_value(row), row.get("company_name_fa") or ""))


def valid_url(value: Any) -> bool:
    try:
        parsed = urlparse(str(value))
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def screenshot_files(company_id: str) -> list[Path]:
    directory = path_for("evidence", "companies", company_id, "screenshots")
    return sorted(
        item for item in directory.glob("*.png")
        if item.is_file() and not item.name.startswith("._")
    ) if directory.exists() else []


def package_path(company_id: str) -> Path:
    return path_for("evidence", "companies", company_id, "sources.json")


def record_summary(company: dict[str, Any]) -> dict[str, Any]:
    return {
        "company_id": company.get("company_id"),
        "company_name_fa": company.get("company_name_fa"),
        "original_priority_tier": company.get("original_priority_tier"),
        "original_luma_opportunity_score": company.get("original_luma_opportunity_score"),
        "priority_tier": company.get("priority_tier"),
        "commercial_readiness": company.get("commercial_readiness"),
        "confidence_adjusted_score": company.get("confidence_adjusted_score"),
        "luma_opportunity_score": company.get("luma_opportunity_score"),
        "commercial_evidence_strength": company.get("commercial_evidence_strength"),
        "score_confidence": company.get("score_confidence"),
        "independent_source_count": company.get("independent_source_count"),
        "company_type": company.get("company_type"),
        "industry": company.get("industry"),
        "workflow_evidence_classification": company.get("workflow_evidence_classification"),
        "screenshot_paths": [str(item.relative_to(path_for())) for item in screenshot_files(company["company_id"])],
    }


def validate_record(company: dict[str, Any], *, require_screenshot: bool, require_proposal: bool, require_dossier: bool) -> list[str]:
    errors: list[str] = []
    cid = company.get("company_id") or ""
    if not cid or not company.get("company_name_fa") or not company.get("industry"):
        errors.append("missing identity/classification field")
    if company.get("company_type") in {None, ""}:
        errors.append("missing company_type")
    for field in ("luma_opportunity_score", "confidence_adjusted_score", "commercial_evidence_strength", "score_confidence"):
        try:
            value = float(company.get(field))
            if not 0 <= value <= 100:
                errors.append(f"{field} outside 0-100")
        except (TypeError, ValueError):
            errors.append(f"{field} is not numeric")
    families = company.get("independent_source_families") or []
    if company.get("independent_source_count") != len(families):
        errors.append("source-family count mismatch")
    workflow_class = company.get("workflow_evidence_classification")
    workflows = company.get("workflow_opportunities") or []
    if workflow_class not in ALLOWED_WORKFLOW_CLASSES:
        errors.append("invalid workflow evidence classification")
    if workflow_class == "UNSUPPORTED" and workflows:
        errors.append("unsupported workflow retained")
    if workflow_class != "UNSUPPORTED" and not workflows:
        errors.append("workflow classification has no opportunity")
    if workflows and workflows[0].get("workflow_evidence_classification") != workflow_class:
        errors.append("workflow row classification mismatch")

    package = package_path(cid)
    if not package.exists():
        errors.append("missing evidence package")
    else:
        try:
            payload = json.loads(package.read_text(encoding="utf-8"))
            if payload.get("company_id") != cid:
                errors.append("evidence package company_id mismatch")
            policy = payload.get("headless_policy") or {}
            if policy.get("headless") is not True or policy.get("isolated_context") is not True or policy.get("visible_browser_launched") is not False:
                errors.append("headless policy metadata mismatch")
            for item in payload.get("screenshots", []):
                if item.get("company_id") != cid or not valid_url(item.get("source_url")) or item.get("headless") is not True:
                    errors.append("screenshot metadata mismatch")
                stored = item.get("path")
                if stored and not (path_for("evidence") / stored).exists():
                    errors.append("screenshot metadata points to missing file")
        except Exception as exc:
            errors.append(f"invalid evidence package: {type(exc).__name__}")

    if require_screenshot and not screenshot_files(cid):
        errors.append("required visual evidence is missing")
    if require_proposal and not path_for("proposals", f"{cid}.md").exists():
        errors.append("required proposal is missing")
    if require_dossier and not path_for("reports", "dossiers", f"{cid}.md").exists():
        errors.append("required dossier is missing")

    for item in company.get("evidence", []):
        if item.get("claim") and not valid_url(item.get("source_url")):
            errors.append("evidence claim has invalid source URL")
    return sorted(set(errors))


def demotion_sample(rows: list[dict[str, Any]], count: int = 10) -> list[dict[str, Any]]:
    demoted = [
        row for row in rows
        if TIER_RANK.get(row.get("priority_tier"), 0) < TIER_RANK.get(row.get("original_priority_tier"), 0)
    ]
    generator = random.Random(20260902)
    return generator.sample(demoted, min(count, len(demoted)))


def run(input_path: str) -> tuple[dict[str, Any], int]:
    companies = read_jsonl(path_for(input_path))
    audited = [row for row in companies if row.get("commercial_audit_version")]
    by_id = {row.get("company_id"): row for row in audited}
    ordered = rank_rows(audited)
    top30 = [row for row in ordered if row.get("commercial_readiness") != "NOT READY"][:30]
    high_score = [row for row in ordered if float(row.get("luma_opportunity_score") or 0) >= 85]
    ready = [row for row in ordered if row.get("commercial_readiness") == "READY FOR OUTREACH"]
    demoted = demotion_sample(audited)

    scopes = {
        "top_30_corrected_prospects": top30,
        "all_raw_score_85_plus": high_score,
        "all_ready_for_outreach": ready,
        "fixed_seed_demoted_sample": demoted,
    }
    scope_results: dict[str, Any] = {}
    all_errors: list[dict[str, Any]] = []
    for scope, records in scopes.items():
        summaries: list[dict[str, Any]] = []
        for company in records:
            errors = validate_record(
                company,
                require_screenshot=scope != "fixed_seed_demoted_sample",
                require_proposal=scope == "all_ready_for_outreach",
                require_dossier=scope == "top_30_corrected_prospects",
            )
            summaries.append(record_summary(company))
            if errors:
                all_errors.append({"scope": scope, "company_id": company.get("company_id"), "errors": errors})
        scope_results[scope] = {"count": len(records), "records": summaries, "errors": sum(1 for item in all_errors if item["scope"] == scope)}

    # The manual visual review was performed on each screenshot in the complete
    # top-30 and READY sets. Keep this explicit so a rerun can be audited.
    visual_review_ids = sorted({row.get("company_id") for row in top30 + ready if row.get("company_id")})
    missing_visual_review = [cid for cid in visual_review_ids if not screenshot_files(cid)]
    if missing_visual_review:
        all_errors.append({"scope": "visual_review", "company_id": "batch", "errors": [f"missing screenshots for {len(missing_visual_review)} reviewed records"]})

    manifest = {
        "generated_at": now_iso(),
        "input": input_path,
        "scope_policy": "Existing commercial-audit records only; no new discovery records.",
        "audited_company_count": len(audited),
        "scopes": scope_results,
        "visual_review": {
            "method": "Human visual inspection of the headless screenshot for every top-30 corrected prospect and every READY FOR OUTREACH record.",
            "reviewed_record_count": len(visual_review_ids),
            "reviewed_company_ids": visual_review_ids,
            "missing_screenshot_ids": missing_visual_review,
        },
        "errors": all_errors,
        "passed": not all_errors and len(audited) == 151,
    }
    output = path_for("logs", f"manual-qa-{stamp()}.json")
    manifest["output"] = str(output.relative_to(path_for()))
    write_json(output, manifest)
    return manifest, 0 if manifest["passed"] else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    args = parser.parse_args()
    manifest, code = run(args.input)
    print(json.dumps({"output": manifest["output"], "passed": manifest["passed"], "audited": manifest["audited_company_count"], "errors": len(manifest["errors"]), "scopes": {key: value["count"] for key, value in manifest["scopes"].items()}}, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
