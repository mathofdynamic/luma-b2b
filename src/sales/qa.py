"""Quality gates for the bounded LUMA sales-activation package.

The validator is intentionally narrow: it checks the current READY set and
the artifacts built for it. It does not discover, enrich, contact, or mutate
company records. ``--record-wave1-review`` records the human inspection that
was performed on the existing Wave 1 screenshots; it never opens a browser.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from src.utilities.common import DEFAULT_PROXY, now_iso, path_for, read_jsonl, write_json


EXPECTED_READY = 32
EXPECTED_WAVES = {"WAVE 1": 10, "WAVE 2": 10, "WAVE 3": 12}
ALLOWED_WORKFLOW_CLASSES = {
    "EVIDENCE_SUPPORTED",
    "STRONG_HYPOTHESIS",
    "WEAK_HYPOTHESIS",
    "UNSUPPORTED",
}
COUNTED_EXTERNAL_FAMILIES = {
    "official_registry",
    "association_or_exhibition",
    "job_portal",
    "linkedin_public",
    "public_news",
    "industry_directory",
    "map_listing",
    "industrial_estate_registry",
}
CLIENT_BANNED_TERMS = (
    "OBSERVED",
    "STRONG_INFERENCE",
    "score confidence",
    "Tier A",
    "commercial evidence strength",
    "UNKNOWN",
    "OSINT",
    "qualification score",
)
CLIENT_HEADINGS = (
    "## فرصت",
    "## راهکار پیشنهادی",
    "## نحوه کار",
    "## نتیجه‌ای که باید اندازه‌گیری شود",
    "## پیشنهاد شروع",
    "## مرحله بعد",
)
OUTREACH_HEADINGS = ("PHONE OPENING", "EMAIL", "LINKEDIN", "WHATSAPP", "FOLLOW-UP")
TRACKER_COLUMNS = (
    "company_id",
    "company_name",
    "wave",
    "first_contact_score",
    "industry",
    "website",
    "primary_contact_role",
    "primary_contact_name",
    "economic_buyer_role",
    "economic_buyer_name",
    "phone",
    "email",
    "linkedin",
    "whatsapp",
    "preferred_channel",
    "primary_opportunity",
    "pilot_name",
    "proposal_path",
    "outreach_path",
    "dossier_path",
    "status",
    "last_contact_date",
    "next_action",
    "next_action_date",
    "notes",
)


def real_files(directory: Path, pattern: str) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(item for item in directory.glob(pattern) if item.is_file() and not item.name.startswith("._"))


def add(errors: list[dict[str, Any]], scope: str, message: str, company_id: str | None = None) -> None:
    errors.append({"scope": scope, "company_id": company_id, "message": message})


def load_targets(input_path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    companies = read_jsonl(path_for(input_path))
    ready = [row for row in companies if row.get("commercial_readiness") == "READY FOR OUTREACH"]
    return companies, ready, [row for row in companies if row.get("commercial_audit_version")]


def validate_records(ready: list[dict[str, Any]], errors: list[dict[str, Any]]) -> None:
    ids = [row.get("company_id") for row in ready]
    if len(ready) != EXPECTED_READY:
        add(errors, "scope", f"Expected exactly {EXPECTED_READY} READY records; found {len(ready)}")
    if len(set(ids)) != len(ids):
        add(errors, "scope", "READY company IDs are not unique")

    waves = Counter(row.get("contact_wave") for row in ready)
    if dict(waves) != EXPECTED_WAVES:
        add(errors, "ranking", f"Wave counts are {dict(waves)}, expected {EXPECTED_WAVES}")
    ranks = sorted(row.get("wave_rank") for row in ready)
    if ranks != list(range(1, EXPECTED_READY + 1)):
        add(errors, "ranking", "wave_rank is not a unique sequence from 1 through 32")

    for row in ready:
        cid = str(row.get("company_id") or "")
        for field in ("activation_version", "activation_research_date", "company_name_fa", "industry", "company_type"):
            if not row.get(field):
                add(errors, "record", f"missing {field}", cid)
        try:
            score = float(row.get("first_contact_score"))
            if not 0 <= score <= 100:
                add(errors, "ranking", "first_contact_score outside 0-100", cid)
        except (TypeError, ValueError):
            add(errors, "ranking", "first_contact_score is not numeric", cid)

        families = row.get("independent_source_families") or []
        if row.get("independent_source_count") != len(families) or len(set(families)) != len(families):
            add(errors, "evidence", "independent source-family count/list mismatch", cid)
        for family in families:
            if family in {"search_engine", "other_public"}:
                add(errors, "evidence", f"uncounted family leaked into independent list: {family}", cid)
            elif family != "book_e_avval" and not family.startswith("company_website:") and family not in COUNTED_EXTERNAL_FAMILIES:
                add(errors, "evidence", f"unrecognized independent family: {family}", cid)

        workflow = row.get("activation_primary_opportunity") or {}
        workflows = row.get("workflow_opportunities") or []
        classification = row.get("workflow_evidence_classification")
        if len(workflows) != 1 or not workflow:
            add(errors, "workflow", "record does not contain exactly one primary workflow", cid)
        if classification not in ALLOWED_WORKFLOW_CLASSES:
            add(errors, "workflow", f"invalid workflow classification: {classification}", cid)
        if classification == "UNSUPPORTED":
            add(errors, "workflow", "unsupported workflow retained for READY record", cid)
        if workflows and workflows[0].get("workflow_evidence_classification") != classification:
            add(errors, "workflow", "workflow classification mismatch", cid)
        for field in ("workflow_name", "workflow_name_fa", "current_process_hypothesis", "discovery_questions"):
            if not workflow.get(field):
                add(errors, "workflow", f"missing primary workflow field: {field}", cid)

        pilot = row.get("activation_pilot") or {}
        for field in ("pilot_name", "pilot_scope", "primary_users", "input_data_needed", "what_luma_builds", "human_approval_points", "pilot_duration_estimate", "success_metrics", "expansion_path", "risks"):
            if not pilot.get(field):
                add(errors, "pilot", f"missing pilot field: {field}", cid)
        demo = row.get("activation_demo") or {}
        for field in ("demo_concept", "demo_inputs", "demo_steps"):
            if not demo.get(field):
                add(errors, "demo", f"missing demo field: {field}", cid)
        journey = row.get("public_sales_surface") or {}
        if not journey.get("observable_steps") or not journey.get("entry_points"):
            add(errors, "sales_surface", "public customer journey is missing observable steps or entry points", cid)

        contacts = row.get("activation_contacts") or {}
        for field in ("primary_contact_role", "economic_buyer_role", "technical_gatekeeper_role"):
            if not contacts.get(field):
                add(errors, "contacts", f"missing contact role: {field}", cid)
        for field in ("primary_contact_name", "economic_buyer_name", "technical_gatekeeper_name"):
            name = contacts.get(field)
            if name and not contacts.get(f"{field.rsplit('_', 1)[0]}_source_url"):
                add(errors, "contacts", f"named contact has no source URL: {field}", cid)
        for phone in contacts.get("public_corporate_phones") or []:
            if re.match(r"^09", str(phone)):
                add(errors, "contacts", "mobile-looking number in public corporate phone field", cid)
        for email in contacts.get("public_corporate_emails") or []:
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email)):
                add(errors, "contacts", "invalid public corporate email", cid)


def validate_evidence(ready: list[dict[str, Any]], errors: list[dict[str, Any]]) -> None:
    for row in ready:
        cid = str(row.get("company_id"))
        package_path = path_for("evidence", "companies", cid, "sources.json")
        if not package_path.exists():
            add(errors, "evidence", "missing evidence package", cid)
            continue
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except Exception as exc:
            add(errors, "evidence", f"invalid sources.json: {type(exc).__name__}", cid)
            continue
        if package.get("company_id") != cid:
            add(errors, "evidence", "evidence package company_id mismatch", cid)
        policy = package.get("headless_policy") or {}
        if policy.get("headless") is not True or policy.get("isolated_context") is not True or policy.get("visible_browser_launched") is not False:
            add(errors, "evidence", "headless/isolated/visible-browser policy metadata mismatch", cid)
        for screenshot in package.get("screenshots") or []:
            if screenshot.get("company_id") != cid or screenshot.get("headless") is not True or not screenshot.get("source_url"):
                add(errors, "evidence", "screenshot metadata mismatch", cid)
            stored = screenshot.get("path")
            if stored and not (path_for("evidence") / stored).exists():
                add(errors, "evidence", f"missing screenshot file: {stored}", cid)
        if not real_files(path_for("evidence", "companies", cid, "screenshots"), "*.png"):
            add(errors, "evidence", "no existing screenshot for sales package", cid)


def validate_sales_documents(ready: list[dict[str, Any]], errors: list[dict[str, Any]]) -> None:
    expected = {str(row.get("company_id")) for row in ready}
    for directory, label in (("sales/internal", "internal"), ("sales/client", "client"), ("sales/outreach", "outreach")):
        files = real_files(path_for(*directory.split("/")), "*.md")
        actual = {item.stem for item in files}
        if actual != expected:
            add(errors, "documents", f"{label} package IDs do not match READY set: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    visual_dir = path_for("sales", "visual")
    visual_ids = {item.name for item in visual_dir.iterdir() if item.is_dir() and not item.name.startswith("._")} if visual_dir.exists() else set()
    if visual_ids != expected:
        add(errors, "documents", f"visual index IDs do not match READY set: missing={sorted(expected - visual_ids)}, extra={sorted(visual_ids - expected)}")

    for row in ready:
        cid = str(row.get("company_id"))
        client_path = path_for("sales", "client", f"{cid}.md")
        outreach_path = path_for("sales", "outreach", f"{cid}.md")
        client = client_path.read_text(encoding="utf-8") if client_path.exists() else ""
        outreach = outreach_path.read_text(encoding="utf-8") if outreach_path.exists() else ""
        for term in CLIENT_BANNED_TERMS:
            if term.lower() in client.lower():
                add(errors, "client_document", f"internal research label leaked into client one-pager: {term}", cid)
        for heading in CLIENT_HEADINGS:
            if heading not in client:
                add(errors, "client_document", f"missing client heading: {heading}", cid)
        for heading in OUTREACH_HEADINGS:
            if heading not in outreach:
                add(errors, "outreach", f"missing outreach section: {heading}", cid)
        if "ارسال نشده" not in outreach and "No outreach" not in outreach:
            add(errors, "outreach", "outreach draft does not explicitly state it was not sent", cid)


def validate_tracker(ready: list[dict[str, Any]], errors: list[dict[str, Any]]) -> None:
    csv_path = path_for("data", "outreach_pipeline.csv")
    if not csv_path.exists():
        add(errors, "tracker", "missing outreach_pipeline.csv")
        return
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if tuple(reader.fieldnames or ()) != TRACKER_COLUMNS:
            add(errors, "tracker", "tracker CSV columns do not match required schema")
    expected = {str(row.get("company_id")) for row in ready}
    actual = {row.get("company_id") for row in rows}
    if len(rows) != EXPECTED_READY or actual != expected:
        add(errors, "tracker", f"tracker rows do not match READY set: rows={len(rows)} missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    for row in rows:
        cid = row.get("company_id")
        if row.get("status") != "NOT_CONTACTED":
            add(errors, "tracker", "row is not NOT_CONTACTED", cid)
        if row.get("last_contact_date") or row.get("next_action_date"):
            add(errors, "tracker", "contact/date field is populated before human approval", cid)
    xlsx_path = path_for("data", "outreach_pipeline.xlsx")
    if not xlsx_path.exists():
        add(errors, "tracker", "missing outreach_pipeline.xlsx")
    else:
        try:
            with zipfile.ZipFile(xlsx_path) as archive:
                bad = archive.testzip()
                names = set(archive.namelist())
                workbook = archive.read("xl/workbook.xml").decode("utf-8", "ignore")
                if bad:
                    add(errors, "tracker", f"xlsx ZIP integrity failed at {bad}")
                if "Outreach Pipeline" not in workbook or "Instructions" not in workbook:
                    add(errors, "tracker", "xlsx is missing required sheets")
                if "xl/worksheets/sheet1.xml" not in names:
                    add(errors, "tracker", "xlsx is missing the pipeline worksheet")
        except (OSError, zipfile.BadZipFile, KeyError) as exc:
            add(errors, "tracker", f"invalid xlsx: {type(exc).__name__}")


def validate_dossiers(ready: list[dict[str, Any]], errors: list[dict[str, Any]]) -> None:
    expected_top = [str(row.get("company_id")) for row in sorted(ready, key=lambda row: int(row.get("wave_rank") or 999))[:30]]
    readme = path_for("reports", "dossiers", "README.md")
    if not readme.exists():
        add(errors, "dossiers", "missing dossier README")
        return
    text = readme.read_text(encoding="utf-8")
    listed = re.findall(r"`(ir-teh-[a-z0-9]+)\.md`", text)
    if listed != expected_top:
        add(errors, "dossiers", "dossier README does not list the current top 30 in rank order")
    for cid in expected_top:
        if not path_for("reports", "dossiers", f"{cid}.md").exists():
            add(errors, "dossiers", "missing top-30 dossier", cid)


def record_wave1_review(ready: list[dict[str, Any]]) -> Path:
    observations = {
        "ir-teh-2587928f98e4f816": "Official Sabahi homepage: group identity, product/brand catalog, subsidiaries, customer/experience claims and public phone are visible.",
        "ir-teh-4b1dd8c047fc2163": "Official Spota homepage: industrial product categories, product cards, customer/service sections and a prominent commercial contact surface are visible.",
        "ir-teh-adb049f466e03f58": "Official Kangaroo homepage: industrial/petrochemical imagery, business introduction, multiple material/service categories and public contact links are visible.",
        "ir-teh-b12fca8dcac7066d": "Public Ketab profile for Sarang: company title, import/export food-raw-material description, Tehran map/contact panel and website link are visible; directory UI is internal-only.",
        "ir-teh-5a0d9c69e8a63c56": "Official Farazin Sanat homepage: ABB/Schneider/Siemens brand surface, industrial product cards, catalog-style browsing and articles are visible.",
        "ir-teh-d284bae5deddc82f": "Official Milad homepage: industrial trading identity, product grid, import/engineering/production/repair service stages and project-oriented content are visible.",
        "ir-teh-5911ae5691d19335": "Official Lux Box homepage: substantial product catalog, category navigation, prices/order buttons and corporate contact/footer are visible; consumer/gift positioning needs care.",
        "ir-teh-37da8ab7a735aff9": "Official Sepidar Carton homepage: carton/packaging identity, detailed production copy, service/contact form and corporate contact details are visible.",
        "ir-teh-a1e0c5ed00f31de5": "Official Iran Bobcat homepage: Bobcat product/sales surface, consultation and purchase CTAs, warranty/after-sales content and public contact links are visible; some content blocks are blank in the capture.",
        "ir-teh-5d9c46c5fec405da": "Official Tak Voltage homepage: industrial electrical brand/product catalog, product cards, brand logos, articles and contact/navigation surface are visible.",
    }
    wave1 = sorted((row for row in ready if row.get("contact_wave") == "WAVE 1"), key=lambda row: int(row.get("wave_rank") or 999))
    records = []
    for row in wave1:
        cid = str(row.get("company_id"))
        screenshots = [str(item.relative_to(path_for())) for item in real_files(path_for("evidence", "companies", cid, "screenshots"), "*.png")]
        records.append({"company_id": cid, "company_name_fa": row.get("company_name_fa"), "wave_rank": row.get("wave_rank"), "screenshots": screenshots, "observation": observations.get(cid, "Existing screenshot inspected for identity, source match and useful business surface.")})
    output = path_for("logs", "sales_activation_manual_review.json")
    write_json(output, {"generated_at": now_iso(), "method": "Human inspection through the local image viewer of existing screenshots captured by isolated headless research; no browser launched.", "scope": "All 10 current Wave 1 companies", "reviewed_count": len(records), "reviewed_company_ids": [item["company_id"] for item in records], "records": records})
    return output


def validate_manual_review(ready: list[dict[str, Any]], errors: list[dict[str, Any]]) -> None:
    path = path_for("logs", "sales_activation_manual_review.json")
    if not path.exists():
        add(errors, "manual_review", "missing Wave 1 manual review log")
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        add(errors, "manual_review", f"invalid manual review log: {type(exc).__name__}")
        return
    expected = [str(row.get("company_id")) for row in sorted(ready, key=lambda row: int(row.get("wave_rank") or 999)) if row.get("contact_wave") == "WAVE 1"]
    if payload.get("reviewed_company_ids") != expected or payload.get("reviewed_count") != len(expected):
        add(errors, "manual_review", "manual review log does not cover exactly the current Wave 1")
    if "no browser launched" not in str(payload.get("method") or "").lower():
        add(errors, "manual_review", "manual review log does not document invisible browser behavior")


def run(input_path: str, *, record_review: bool = False) -> tuple[dict[str, Any], int]:
    companies, ready, audited = load_targets(input_path)
    errors: list[dict[str, Any]] = []
    if len(companies) < EXPECTED_READY or len(audited) != 151:
        add(errors, "scope", f"unexpected source scope: total={len(companies)}, audited={len(audited)}")
    if record_review:
        record_wave1_review(ready)
    validate_records(ready, errors)
    validate_evidence(ready, errors)
    validate_sales_documents(ready, errors)
    validate_tracker(ready, errors)
    validate_dossiers(ready, errors)
    validate_manual_review(ready, errors)
    network_logs = sorted(real_files(path_for("logs"), "sales-activation-*.json"), key=lambda item: item.stat().st_mtime)
    if network_logs:
        try:
            latest = json.loads(network_logs[-1].read_text(encoding="utf-8"))
            if latest.get("proxy") != DEFAULT_PROXY or latest.get("no_outreach_sent") is not True:
                add(errors, "network", "latest activation log does not prove the required proxy/no-outreach state")
        except Exception as exc:
            add(errors, "network", f"invalid latest activation log: {type(exc).__name__}")
    else:
        add(errors, "network", "no activation log found")

    summary = {
        "generated_at": now_iso(),
        "input": input_path,
        "scope": "Exactly the existing READY FOR OUTREACH set; no discovery or contact action.",
        "companies_total": len(companies),
        "audited_total": len(audited),
        "ready_total": len(ready),
        "waves": dict(Counter(row.get("contact_wave") for row in ready)),
        "manual_review_log": str(path_for("logs", "sales_activation_manual_review.json").relative_to(path_for())),
        "errors": errors,
        "passed": not errors,
    }
    output = path_for("logs", f"sales-activation-qa-{now_iso().replace(':', '').replace('-', '')}.json")
    write_json(output, summary)
    summary["output"] = str(output.relative_to(path_for()))
    return summary, 0 if not errors else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the bounded LUMA sales activation package")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    parser.add_argument("--record-wave1-review", action="store_true")
    args = parser.parse_args()
    summary, code = run(args.input, record_review=args.record_wave1_review)
    print(json.dumps({"passed": summary["passed"], "output": summary["output"], "ready": summary["ready_total"], "errors": len(summary["errors"])}, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
