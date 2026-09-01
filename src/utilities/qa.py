"""Final, reproducible quality checks for the LUMA B2B production outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

from .common import DEFAULT_PROXY, normalize_persian, now_iso, path_for, read_jsonl, write_json


EXPECTED_SHEETS = {
    "All Companies", "Tier A", "Tier B", "Industries", "Workflow Opportunities",
    "Decision Makers", "Sources", "Evidence Index", "Rejected", "Scoring Explanation",
}
TEXT_SUFFIXES = {".md", ".py", ".mjs", ".json", ".jsonl", ".csv", ".yaml", ".yml", ".txt", ".toml"}
FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "proton.me", "protonmail.com"}
SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
]


def latest_json(prefix: str) -> tuple[Path | None, dict[str, Any]]:
    files = sorted(
        [item for item in path_for("logs").glob(f"{prefix}-*.json") if not item.name.startswith("._")],
        key=lambda item: item.stat().st_mtime,
    )
    if not files:
        return None, {}
    try:
        return files[-1], json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception:
        return files[-1], {}


def add_issue(result: dict[str, Any], message: str, *, critical: bool = False) -> None:
    result["issues" if critical else "warnings"].append(message)


def valid_url(url: Any) -> bool:
    try:
        parsed = urlparse(str(url))
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def actual_screenshots(company_id: str) -> list[Path]:
    directory = path_for("evidence", "companies", company_id, "screenshots")
    if not directory.exists():
        return []
    return sorted(item for item in directory.glob("*.png") if item.is_file() and not item.name.startswith("._"))


def check_companies(companies: list[dict[str, Any]], result: dict[str, Any]) -> None:
    ids = [company.get("company_id") for company in companies]
    duplicate_ids = [key for key, count in Counter(ids).items() if key and count > 1]
    result["counts"]["duplicate_company_ids"] = len(duplicate_ids)
    if duplicate_ids:
        add_issue(result, f"Duplicate company_id values: {duplicate_ids[:10]}", critical=True)

    identity_groups: dict[str, list[str]] = {}
    for company in companies:
        name = normalize_persian(company.get("company_name_fa"), compact=True)
        address = normalize_persian(company.get("hq_address"), compact=True)
        if name and address:
            identity_groups.setdefault(f"{name}:{address}", []).append(company.get("company_id", ""))
    duplicate_identity_groups = [values for values in identity_groups.values() if len(values) > 1]
    result["counts"]["duplicate_name_address_groups"] = len(duplicate_identity_groups)
    if duplicate_identity_groups:
        add_issue(result, f"Potential duplicate name/address groups remain: {len(duplicate_identity_groups)}")

    expected = 0
    tier_errors = 0
    missing_required = 0
    evidence_url_errors = 0
    private_contact_errors = 0
    for company in companies:
        score = company.get("luma_opportunity_score")
        hard = company.get("hard_disqualifier")
        if score is not None:
            expected = "Reject" if hard or score < 45 else "D" if score < 60 else "C" if score < 70 else "B" if score < 80 else "A"
            if company.get("priority_tier") != expected:
                tier_errors += 1
        if not company.get("company_id") or not company.get("company_name_fa") or not company.get("industry"):
            missing_required += 1
        for evidence in company.get("evidence", []):
            if evidence.get("claim") and not valid_url(evidence.get("source_url")):
                evidence_url_errors += 1
        for source in company.get("source_records", []):
            if source.get("source_url") and not valid_url(source.get("source_url")):
                evidence_url_errors += 1
        for phone in company.get("phone_public") or []:
            if str(phone).startswith("09"):
                private_contact_errors += 1
        for email in company.get("email_public") or []:
            if str(email).lower().rsplit("@", 1)[-1] in FREE_EMAIL_DOMAINS:
                private_contact_errors += 1

    result["counts"].update({
        "companies": len(companies),
        "tier_consistency_errors": tier_errors,
        "missing_required_identity_fields": missing_required,
        "evidence_url_errors": evidence_url_errors,
        "private_contact_field_errors": private_contact_errors,
        "meaningfully_enriched": sum(1 for c in companies if c.get("research_status") == "MEANINGFULLY_ENRICHED"),
        "scored": sum(1 for c in companies if c.get("luma_opportunity_score") is not None),
        "tier_a": sum(1 for c in companies if c.get("priority_tier") == "A"),
        "tier_b": sum(1 for c in companies if c.get("priority_tier") == "B"),
        "rejected": sum(1 for c in companies if c.get("priority_tier") == "Reject"),
    })
    if tier_errors:
        add_issue(result, f"Score/tier consistency errors: {tier_errors}", critical=True)
    if missing_required:
        add_issue(result, f"Records missing required identity fields: {missing_required}", critical=True)
    if evidence_url_errors:
        add_issue(result, f"Evidence/source rows with invalid or missing URLs: {evidence_url_errors}", critical=True)
    if private_contact_errors:
        add_issue(result, f"Potential private contact values in public-contact fields: {private_contact_errors}", critical=True)


def check_evidence(companies: list[dict[str, Any]], result: dict[str, Any]) -> None:
    package_count = 0
    metadata_count = 0
    metadata_errors = 0
    screenshot_total = 0
    error_entries = 0
    headless_blocked = 0
    for package in path_for("evidence", "companies").glob("*/sources.json"):
        if package.name.startswith("._"):
            continue
        try:
            payload = json.loads(package.read_text(encoding="utf-8"))
        except Exception:
            metadata_errors += 1
            continue
        package_count += 1
        error_entries += len(payload.get("errors", []))
        headless_blocked += sum(1 for error in payload.get("errors", []) if error.get("classification") == "HEADLESS_BLOCKED")
        company_id = package.parent.name
        if payload.get("company_id") != company_id:
            metadata_errors += 1
        policy = payload.get("headless_policy") or {}
        if policy.get("headless") is not True or policy.get("isolated_context") is not True or policy.get("visible_browser_launched") is not False:
            metadata_errors += 1
        for item in payload.get("screenshots", []):
            metadata_count += 1
            screenshot_total += 1
            if item.get("company_id") != company_id or not valid_url(item.get("source_url")) or not item.get("captured_at") or item.get("headless") is not True:
                metadata_errors += 1
            stored = item.get("path")
            if stored and not (path_for("evidence") / stored).exists():
                metadata_errors += 1

    top = sorted(
        [company for company in companies if company.get("priority_tier") in {"A", "B"} and not company.get("hard_disqualifier")],
        key=lambda item: (-item.get("luma_opportunity_score", 0), item.get("company_name_fa", "")),
    )[:100]
    top_missing_packages = [company.get("company_id") for company in top if not (path_for("evidence", "companies", company.get("company_id", ""), "sources.json")).exists()]
    top_without_visual = [company.get("company_id") for company in top if not actual_screenshots(company.get("company_id", ""))]
    result["counts"].update({
        "evidence_packages": package_count,
        "screenshot_metadata": metadata_count,
        "screenshots_on_disk": sum(len(actual_screenshots(company.get("company_id", ""))) for company in companies),
        "top_100_packages_missing": len(top_missing_packages),
        "top_100_without_visual": len(top_without_visual),
        "capture_error_entries": error_entries,
        "headless_blocked_source_entries": headless_blocked,
    })
    if metadata_errors:
        add_issue(result, f"Evidence metadata errors: {metadata_errors}", critical=True)
    if top_missing_packages:
        add_issue(result, f"Top-100 evidence packages missing: {top_missing_packages[:10]}", critical=True)
    if top_without_visual:
        add_issue(result, f"Top-100 records without a screenshot: {top_without_visual[:10]}")
    if error_entries:
        add_issue(result, f"Public-source capture errors retained in company packages: {error_entries}")
    if headless_blocked:
        add_issue(result, f"Sources explicitly classified HEADLESS_BLOCKED: {headless_blocked}")


def check_exports(companies: list[dict[str, Any]], result: dict[str, Any]) -> None:
    expected_files = [
        "data/master_companies.csv", "data/master_companies.jsonl", "data/master_companies.xlsx",
        "data/tier_a.csv", "data/tier_b.csv", "data/rejected.csv",
    ]
    missing = [item for item in expected_files if not path_for(item).exists()]
    if missing:
        add_issue(result, f"Missing required exports: {missing}", critical=True)
    for name, expected_count in [("master_companies.csv", len(companies)), ("tier_a.csv", sum(1 for c in companies if c.get("priority_tier") == "A")), ("tier_b.csv", sum(1 for c in companies if c.get("priority_tier") == "B")), ("rejected.csv", sum(1 for c in companies if c.get("priority_tier") == "Reject"))]:
        file_path = path_for("data", name)
        if not file_path.exists():
            continue
        try:
            with file_path.open(encoding="utf-8-sig", newline="") as handle:
                count = sum(1 for _ in csv.DictReader(handle))
            result["counts"][f"{name}_rows"] = count
            if count != expected_count:
                add_issue(result, f"{name} row count {count} != expected {expected_count}", critical=True)
        except Exception as exc:
            add_issue(result, f"Could not read {name}: {exc}", critical=True)

    workbook = path_for("data", "master_companies.xlsx")
    if workbook.exists():
        try:
            with zipfile.ZipFile(workbook) as archive:
                workbook_xml = ElementTree.fromstring(archive.read("xl/workbook.xml"))
                namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                sheets = {sheet.attrib.get("name") for sheet in workbook_xml.findall("main:sheets/main:sheet", namespace)}
                result["counts"]["workbook_sheets"] = len(sheets)
                if sheets != EXPECTED_SHEETS:
                    add_issue(result, f"Workbook sheet set mismatch: {sorted(sheets)}", critical=True)
        except Exception as exc:
            add_issue(result, f"Workbook integrity check failed: {exc}", critical=True)


def check_proposals(companies: list[dict[str, Any]], result: dict[str, Any]) -> None:
    proposal_rows = read_jsonl(path_for("data", "normalized", "proposals.jsonl"))
    by_id = {company.get("company_id"): company for company in companies}
    invalid = []
    missing_files = []
    for row in proposal_rows:
        company = by_id.get(row.get("company_id"))
        if not company or company.get("priority_tier") not in {"A", "B"} or company.get("hard_disqualifier") or company.get("industry") == "other":
            invalid.append(row.get("company_id"))
        if not path_for("proposals", f"{row.get('company_id')}.md").exists():
            missing_files.append(row.get("company_id"))
    result["counts"]["proposals"] = len(proposal_rows)
    if invalid:
        add_issue(result, f"Proposal rows outside the proposal gate: {invalid[:10]}", critical=True)
    if missing_files:
        add_issue(result, f"Proposal markdown files missing: {missing_files[:10]}", critical=True)


def check_network_and_browser(result: dict[str, Any]) -> None:
    preflight_path, preflight = latest_json("network_preflight")
    result["network_log"] = str(preflight_path.relative_to(path_for())) if preflight_path else None
    if not preflight.get("vpn_connected"):
        add_issue(result, "Latest network preflight does not confirm VPN connected.", critical=True)
    if preflight.get("physical_interface") != "en1":
        add_issue(result, f"Physical interface is not en1: {preflight.get('physical_interface')}", critical=True)
    if preflight.get("proxy") != DEFAULT_PROXY:
        add_issue(result, f"Preflight proxy differs from configured direct proxy: {preflight.get('proxy')}", critical=True)
    direct_ip = (preflight.get("direct_ip") or {}).get("body", "").strip()
    normal_ip = (preflight.get("normal_ip") or {}).get("body", "").strip()
    if direct_ip != "5.238.239.167":
        add_issue(result, f"Direct egress differs from verified value: {direct_ip or 'UNKNOWN'}", critical=True)
    if not direct_ip or direct_ip == normal_ip:
        add_issue(result, "Normal and direct egress values are not observably distinct.", critical=True)
    if (preflight.get("direct_target") or {}).get("http_status") != 200:
        add_issue(result, "Latest direct didmeet preflight is not HTTP 200.", critical=True)

    config_path = path_for("config", "playwright.headless.json")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        launch = config.get("browser", {}).get("launchOptions", {})
        if launch.get("headless") is not True or (launch.get("proxy") or {}).get("server") != DEFAULT_PROXY:
            add_issue(result, "Playwright config is not headless with the verified direct proxy.", critical=True)
    except Exception as exc:
        add_issue(result, f"Could not read headless browser config: {exc}", critical=True)

    capture_path, capture = latest_json("evidence-capture")
    result["capture_log"] = str(capture_path.relative_to(path_for())) if capture_path else None
    if capture.get("visible_browser_launched") is not False:
        add_issue(result, "Latest evidence-capture log does not prove visible_browser_launched=false.", critical=True)
    if capture.get("headless_blocked", 0):
        result["headless_blocked"] = capture.get("headless_blocked")


def check_encoding_and_secrets(result: dict[str, Any]) -> None:
    encoding_errors = []
    secret_hits = []
    for directory in ["README.md", "research", "src", "config", "data", "docs", "reports", "proposals"]:
        base = path_for(directory)
        paths = [base] if base.is_file() else base.rglob("*") if base.exists() else []
        for item in paths:
            if not item.is_file() or item.name.startswith("._") or item.suffix.lower() not in TEXT_SUFFIXES or "inspect" in item.name or ".playwright-cli" in str(item):
                continue
            try:
                text = item.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                encoding_errors.append(str(item.relative_to(path_for())))
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    secret_hits.append(str(item.relative_to(path_for())))
                    break
    result["counts"]["text_encoding_errors"] = len(encoding_errors)
    result["counts"]["secret_pattern_hits"] = len(secret_hits)
    if encoding_errors:
        add_issue(result, f"UTF-8 decoding errors: {encoding_errors[:10]}", critical=True)
    if secret_hits:
        add_issue(result, f"Possible credential patterns found: {secret_hits[:10]}", critical=True)


def write_quality_report(result: dict[str, Any]) -> None:
    report_path = path_for("reports", "data_quality_report.md")
    existing = report_path.read_text(encoding="utf-8") if report_path.exists() else "# Data Quality Report\n"
    existing = existing.split("\n## Final QA", 1)[0].rstrip()
    status = "PASSED" if result["passed"] else "FAILED"
    lines = [
        existing, "", "## Final QA", "", f"Status: **{status}**", f"Generated: {result['generated_at']}", "",
        "| Check | Result |", "|---|---:|",
        f"| Canonical companies | {result['counts'].get('companies', 0):,} |",
        f"| Meaningfully enriched | {result['counts'].get('meaningfully_enriched', 0):,} |",
        f"| Scored | {result['counts'].get('scored', 0):,} |",
        f"| Tier A / B | {result['counts'].get('tier_a', 0):,} / {result['counts'].get('tier_b', 0):,} |",
        f"| Evidence packages / screenshots | {result['counts'].get('evidence_packages', 0):,} / {result['counts'].get('screenshots_on_disk', 0):,} |",
        f"| Workbook sheets | {result['counts'].get('workbook_sheets', 0):,} |",
        f"| Secret-pattern hits | {result['counts'].get('secret_pattern_hits', 0):,} |",
        "", "### Warnings", "", *([f"- {item}" for item in result["warnings"]] or ["- None"]),
        "", "### Critical issues", "", *([f"- {item}" for item in result["issues"]] or ["- None"]), "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final LUMA B2B dataset/evidence/network QA")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    args = parser.parse_args()
    result: dict[str, Any] = {
        "generated_at": now_iso(), "passed": True, "issues": [], "warnings": [], "counts": {},
    }
    companies = read_jsonl(args.input)
    check_companies(companies, result)
    check_evidence(companies, result)
    check_exports(companies, result)
    check_proposals(companies, result)
    check_network_and_browser(result)
    check_encoding_and_secrets(result)
    result["passed"] = not result["issues"]
    result["quality_gate"] = "PASS" if result["passed"] else "FAIL"
    log_path = path_for("logs", f"qa-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    write_json(log_path, result)
    write_quality_report(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
