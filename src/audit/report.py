"""Write sales-ready, ranking-audit and human dossier artifacts for the 151-record audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.utilities.common import domain_of, now_iso, path_for, read_jsonl, write_json


def audited(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [company for company in companies if company.get("commercial_audit_version")]


def rank_value(company: dict[str, Any]) -> float:
    value = company.get("confidence_adjusted_score")
    return float(value if value is not None else company.get("luma_opportunity_score") or 0)


def rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda item: (-rank_value(item), item.get("company_name_fa") or ""))


def md_link(url: str | None, label: str | None = None) -> str:
    return f"[{label or url}]({url})" if url else "UNKNOWN"


def source_urls(company: dict[str, Any], limit: int = 12) -> list[str]:
    values: list[str] = []
    for item in list(company.get("source_records") or []) + list(company.get("evidence") or []):
        url = item.get("source_url")
        if url and url not in values:
            values.append(url)
    return values[:limit]


def latest_audit_run() -> dict[str, Any]:
    files = sorted(
        [item for item in path_for("logs").glob("commercial-audit-*.json") if not item.name.startswith(("._", "commercial-audit-report-"))],
        key=lambda item: item.stat().st_mtime,
    )
    if not files:
        return {}
    try:
        return json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception:
        return {}


def evidence_items(company: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    items = [item for item in company.get("evidence", []) if not item.get("excluded_from_qualification")]
    audit_items = [item for item in items if item.get("audit_round")]
    ordered = audit_items + [item for item in items if item not in audit_items]
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for item in ordered:
        key = (item.get("source_url"), item.get("claim"))
        if key in seen:
            continue
        seen.add(key)
        selected.append(item)
    return selected[:limit]


def screenshot_paths(company_id: str) -> list[str]:
    directory = path_for("evidence", "companies", company_id, "screenshots")
    if not directory.exists():
        return []
    return sorted(str(item.relative_to(path_for())) for item in directory.glob("*.png") if item.is_file() and not item.name.startswith("._"))


def workflow(company: dict[str, Any]) -> dict[str, Any]:
    return (company.get("workflow_opportunities") or [{}])[0] or {}


def workflow_label(company: dict[str, Any]) -> str:
    item = workflow(company)
    return item.get("workflow_name") or "UNKNOWN — no evidence-backed workflow retained"


def contact_lines(company: dict[str, Any]) -> list[str]:
    lines = [f"- Website: {md_link(company.get('website'))}"]
    phones = company.get("phone_public") or []
    lines.append(f"- Public corporate phone: {', '.join(str(phone) for phone in phones) if phones else 'UNKNOWN'}")
    emails = company.get("email_public") or []
    lines.append(f"- Public corporate email: {', '.join(str(email) for email in emails) if emails else 'UNKNOWN'}")
    if company.get("linkedin_company_page"):
        lines.append(f"- LinkedIn company page: {md_link(company.get('linkedin_company_page'))}")
    return lines


def strongest_evidence_lines(company: dict[str, Any], limit: int = 3) -> list[str]:
    lines: list[str] = []
    for item in evidence_items(company, limit):
        claim = item.get("claim") or "Observed public evidence"
        snippet = item.get("quote_or_snippet") or item.get("evidence_snippet") or ""
        source = md_link(item.get("source_url"), item.get("source_title") or "source")
        lines.append(f"- OBSERVED — {claim} {('Snippet: ' + snippet[:420] + ' ') if snippet else ''}({source})")
    return lines or ["- UNKNOWN — no preserved evidence quote was sufficient for a stronger claim."]


def sales_line(company: dict[str, Any], rank: int) -> list[str]:
    item = workflow(company)
    package = Path("evidence", "companies", company["company_id"], "sources.json")
    proposal = Path("proposals", f"{company['company_id']}.md")
    lines = [
        f"### {rank}. {company.get('company_name_fa')}",
        "",
        f"- Corrected industry / company type: `{company.get('industry')}` / `{company.get('company_type')}` (classification confidence {company.get('industry_classification_confidence')}/100)",
        f"- Original score/tier: {company.get('original_luma_opportunity_score')} / {company.get('original_priority_tier')}",
        f"- New score/tier: {company.get('luma_opportunity_score')} / {company.get('priority_tier')}",
        f"- Confidence-adjusted score: {company.get('confidence_adjusted_score')} (factor {company.get('confidence_factor')})",
        f"- Commercial evidence strength: {company.get('commercial_evidence_strength')}/100; score confidence: {company.get('score_confidence')}/100",
        f"- Independent source families: {company.get('independent_source_count')} — {', '.join(company.get('independent_source_families') or [])}",
        f"- Website: {md_link(company.get('website'))}",
        f"- Public phone: {', '.join(str(phone) for phone in company.get('phone_public') or []) or 'UNKNOWN'}",
        f"- Public corporate email: {', '.join(str(email) for email in company.get('email_public') or []) or 'UNKNOWN'}",
        f"- Strongest evidence: {' | '.join((item.get('claim') or '') for item in evidence_items(company, 3)) or 'UNKNOWN'}",
        f"- Why LUMA should care: {company.get('audit_summary')}",
        f"- ONE strongest workflow: **{item.get('workflow_name') or 'UNKNOWN'}**",
        f"- Workflow evidence classification: `{company.get('workflow_evidence_classification')}`",
        f"- Likely business owner: {item.get('likely_business_owner') or company.get('decision_maker_role') or 'UNKNOWN'}",
        f"- Publicly verified decision-maker name: {company.get('decision_maker_name_public') or 'UNKNOWN'}",
        f"- Evidence package: `{package}`",
        f"- Audit page text: {', '.join(f'`evidence/{path}`' for path in company.get('audit_page_paths') or []) or 'UNKNOWN'}",
        f"- Screenshots: {', '.join('`' + path + '`' for path in screenshot_paths(company['company_id'])) or 'UNKNOWN'}",
        f"- Proposal: `{proposal}`" if proposal.exists() else "- Proposal: not generated because the proposal gate did not select this record",
        "",
    ]
    return lines


def write_sales_ready(rows: list[dict[str, Any]]) -> None:
    groups = {
        "READY FOR OUTREACH": rank_rows([row for row in rows if row.get("sales_readiness") == "READY FOR OUTREACH"]),
        "NEEDS DISCOVERY": rank_rows([row for row in rows if row.get("sales_readiness") == "NEEDS DISCOVERY"]),
        "NOT READY": rank_rows([row for row in rows if row.get("sales_readiness") == "NOT READY"]),
    }
    lines = [
        "# Sales-ready prospects — commercial audit",
        "",
        f"Generated: {now_iso()}",
        "",
        f"This report audits only the {len(rows)} companies that entered the run as existing Tier A/B records. It does not add candidates. A public workflow surface supports a sales hypothesis; it does not prove an internal failure, budget, volume or buying authority.",
        "",
        f"Counts: READY FOR OUTREACH **{len(groups['READY FOR OUTREACH'])}**; NEEDS DISCOVERY **{len(groups['NEEDS DISCOVERY'])}**; NOT READY **{len(groups['NOT READY'])}**.",
        "",
        "## READY FOR OUTREACH",
        "",
        "These records clear the commercial gate: active operation supported, meaningful scale or complexity, at least two independent source families, a supported/strong workflow hypothesis, no known high internal AI/software capability, commercial evidence strength ≥70, score confidence ≥65 and revised opportunity score ≥70.",
        "",
    ]
    for index, company in enumerate(groups["READY FOR OUTREACH"], 1):
        lines.extend(sales_line(company, index))
    lines += ["## NEEDS DISCOVERY", "", "These records remain plausible but fail at least one READY gate or remain below the revised opportunity threshold.", ""]
    for index, company in enumerate(groups["NEEDS DISCOVERY"], 1):
        lines.extend(sales_line(company, index))
    lines += ["## NOT READY", "", "These records should not receive a personalized sales proposal from this run. Reasons are preserved in the canonical record.", "", "| Company | Original tier | New tier | Adjusted score | Evidence | Main reason |", "|---|---:|---:|---:|---:|---|"]
    for company in groups["NOT READY"]:
        lines.append(f"| {company.get('company_name_fa')} | {company.get('original_priority_tier')} | {company.get('priority_tier')} | {company.get('confidence_adjusted_score')} | {company.get('commercial_evidence_strength')} | {', '.join(company.get('risk_reasons') or []) or company.get('hard_disqualifier') or company.get('classification_correction_reason') or 'workflow/evidence gate'} |")
    path_for("reports", "sales_ready_prospects.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def dossier(company: dict[str, Any]) -> str:
    item = workflow(company)
    facts = strongest_evidence_lines(company, 6)
    questions = (item.get("discovery_questions") or [])[:8]
    while len(questions) < 5:
        questions.append("حجم ماهانه، منبع داده و نقطه تأیید انسانی این فرایند چیست؟")
    screenshots = screenshot_paths(company["company_id"])
    recommendation = "GO" if company.get("sales_readiness") == "READY FOR OUTREACH" else "DISCOVERY FIRST" if company.get("sales_readiness") == "NEEDS DISCOVERY" else "NO-GO"
    decision_status = company.get("decision_maker_evidence_status") or "UNKNOWN_DECISION_MAKER"
    return "\n".join([
        f"# {company.get('company_name_fa')}",
        "",
        "## Snapshot",
        "",
        f"- Corrected classification: `{company.get('industry')}` / `{company.get('company_type')}`.",
        f"- Public description: {company.get('description_observed') or 'UNKNOWN'}",
        f"- Location: {company.get('hq_address') or company.get('city') or 'UNKNOWN'}",
        f"- Revised score: {company.get('luma_opportunity_score')}; confidence-adjusted: {company.get('confidence_adjusted_score')}; tier: {company.get('priority_tier')}",
        f"- Commercial evidence strength: {company.get('commercial_evidence_strength')}/100; score confidence: {company.get('score_confidence')}/100; independent source families: {company.get('independent_source_count')}",
        "",
        "## Why it is commercially interesting",
        "",
        *facts,
        f"- The public operating surface suggests meaningful activity around {company.get('company_type') or 'an unresolved company type'}; scale and buying power remain bounded by the evidence above.",
        "",
        "## Evidence",
        "",
        *facts,
        "",
        "## Likely operational bottleneck",
        "",
        f"STRONG_INFERENCE — {item.get('current_process_hypothesis') or 'No workflow hypothesis is retained.'}",
        "The public record does not establish that the company currently handles this process manually or inefficiently.",
        "",
        "## Recommended LUMA solution",
        "",
        item.get("proposed_luma_solution") or "UNKNOWN — no sufficiently supported solution retained.",
        "",
        "## Why this solution could matter financially",
        "",
        "No ROI percentage is invented. Validate the KPI categories: " + "; ".join(item.get("measurable_KPIs") or ["turnaround time", "manual handoffs", "correction rate"]) + ".",
        "",
        "## What we do NOT know",
        "",
        "- Monthly volume, current handoffs, budget, decision authority, system ownership, data quality and implementation constraints are UNKNOWN.",
        f"- Internal technical capability: `{company.get('internal_tech_capability_evidence_status')}` — {company.get('internal_tech_capability_interpretation')}",
        f"- Digital maturity: `{company.get('digital_maturity_evidence_status')}` — {company.get('digital_maturity_interpretation')}",
        "",
        "## Questions to ask",
        "",
        *[f"{index}. {question}" for index, question in enumerate(questions[:8], 1)],
        "",
        "## Decision maker",
        "",
        f"- Role: {company.get('decision_maker_role') or item.get('likely_business_owner') or 'UNKNOWN'} (role status: `{decision_status}`).",
        f"- Publicly verified name: {company.get('decision_maker_name_public') or 'UNKNOWN'}.",
        f"- Source: {md_link(company.get('decision_maker_source_url'), 'public source')}; confidence: {company.get('decision_maker_confidence') or 0}.",
        "",
        "## Contact channels",
        "",
        *contact_lines(company),
        "",
        "## Screenshots",
        "",
        *([f"- `{path}`" for path in screenshots] or ["- UNKNOWN — no visual evidence is currently stored for this company."]),
        "",
        "## Sales recommendation",
        "",
        f"**{recommendation}** — {company.get('sales_readiness')}; the recommendation follows the evidence gate and does not imply verified budget or authority.",
        "",
        "## Source links",
        "",
        *([f"- {md_link(url)}" for url in source_urls(company)] or ["- UNKNOWN"]),
        "",
    ])


def write_dossiers(rows: list[dict[str, Any]]) -> int:
    candidates = rank_rows([row for row in rows if row.get("sales_readiness") != "NOT READY"])[:30]
    directory = path_for("reports", "dossiers")
    directory.mkdir(parents=True, exist_ok=True)
    for old in directory.glob("*.md"):
        if not old.name.startswith("._"):
            old.unlink()
    for company in candidates:
        (directory / f"{company['company_id']}.md").write_text(dossier(company), encoding="utf-8")
    return len(candidates)


def old_score_distribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "old_internal_tech_20": sum(1 for row in rows if row.get("original_internal_tech_capability_score") == 20),
        "old_outsourcing_80": sum(1 for row in rows if row.get("original_outsourcing_fit_score") == 80),
        "old_score_confidence_fractional": sum(1 for row in rows if isinstance(row.get("original_score_confidence"), float) and row.get("original_score_confidence") < 1),
        "one_independent_family": sum(1 for row in rows if row.get("independent_source_count") == 1),
    }


def write_ranking_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tier_order = {"Reject": 0, "D": 1, "C": 2, "B": 3, "A": 4}
    old_counts = Counter(row.get("original_priority_tier") for row in rows)
    new_counts = Counter(row.get("priority_tier") for row in rows)
    promoted = [row for row in rows if tier_order.get(row.get("priority_tier"), 0) > tier_order.get(row.get("original_priority_tier"), 0)]
    demoted = [row for row in rows if tier_order.get(row.get("priority_tier"), 0) < tier_order.get(row.get("original_priority_tier"), 0)]
    classification_changes = [row for row in rows if row.get("original_industry") != row.get("industry")]
    risk_counts = Counter(reason for row in rows for reason in (row.get("risk_reasons") or []))
    old_workflows = Counter((row.get("original_workflow_opportunities") or [{}])[0].get("workflow_name") for row in rows if (row.get("original_workflow_opportunities") or []))
    source_bias = Counter(
        "Book-e Avval only" if row.get("independent_source_families") == ["book_e_avval"] else "Book-e Avval plus corroboration" if "book_e_avval" in (row.get("independent_source_families") or []) else "Other source families"
        for row in rows
    )
    old = old_score_distribution(rows)
    run = latest_audit_run()
    task_count = (run.get("initial_tasks") or 0) + (run.get("followup_tasks") or 0)
    page_ok = run.get("pages_ok") or 0
    page_failed = run.get("pages_failed") or run.get("failed_sources") or 0
    lines = [
        "# Ranking audit — existing Tier A/B cohort",
        "",
        f"Generated: {now_iso()}",
        "",
        "Scope: the 151 records that entered this run as Tier A/B. No new discovery records were added.",
        "",
        "## Tier changes",
        "",
        f"- Old Tier A: **{old_counts.get('A', 0)}** → new Tier A: **{new_counts.get('A', 0)}**",
        f"- Old Tier B: **{old_counts.get('B', 0)}** → new Tier B: **{new_counts.get('B', 0)}**",
        f"- New C/D/Reject: **{new_counts.get('C', 0)} / {new_counts.get('D', 0)} / {new_counts.get('Reject', 0)}**",
        f"- Promoted within the tier scale: **{len(promoted)}**; demoted: **{len(demoted)}**; rejected: **{new_counts.get('Reject', 0)}**.",
        "",
        "### Promoted",
        "",
        *([f"- {row.get('company_name_fa')}: {row.get('original_priority_tier')} → {row.get('priority_tier')}" for row in rank_rows(promoted)] or ["- None"]),
        "",
        "### Demoted",
        "",
        *([f"- {row.get('company_name_fa')}: {row.get('original_priority_tier')} → {row.get('priority_tier')} — {', '.join(row.get('risk_reasons') or []) or row.get('hard_disqualifier') or row.get('classification_correction_reason') or 'confidence/workflow gate'}" for row in rank_rows(demoted)] or ["- None"]),
        "",
        "## Classification corrections",
        "",
        f"Industry changed on **{len(classification_changes)}** records. This count represents a changed classification field, not a claim that every old label was legally incorrect.",
        "",
        *([f"- {row.get('company_name_fa')}: `{row.get('original_industry')}` → `{row.get('industry')}`; company type `{row.get('company_type')}` — {row.get('classification_correction_reason')}" for row in rank_rows(classification_changes)] or ["- None"]),
        "",
        "## Score-default problems found",
        "",
        f"- The prior run awarded internal-tech score 20 on **{old['old_internal_tech_20']}/{len(rows)}** records and outsourcing-fit score 80 on **{old['old_outsourcing_80']}/{len(rows)}**. That treated missing tech evidence like known low internal capability.",
        "- The revised model stores `KNOWN_LOW_INTERNAL_TECH` separately from `UNKNOWN_INTERNAL_TECH`; UNKNOWN maps to neutral 50/50 values and lowers confidence rather than awarding a capability-gap bonus.",
        f"- The prior score-confidence field used fractional values below 1 on **{old['old_score_confidence_fractional']}/{len(rows)}** records even though the requested field is 0–100. The audit rewrites it to an integer 0–100 scale.",
        "- Prior digital-maturity and component values were often tied because they were derived from defaults. The audit uses observed signal density where available and keeps unknown dimensions neutral.",
        "",
        "## Workflow-template problems found",
        "",
        f"- Prior workflow templates were distributed from industry/category context without requiring a company-specific operating signal. The new run retains a workflow only when public company-page signals support it; otherwise the value is `UNSUPPORTED`.",
        f"- Existing workflow-name distribution in the audited cohort: {dict(old_workflows)}.",
        "- Warehouse rental, branch, retail and software-product records are not allowed to inherit freight, manufacturing or generic RFQ workflows from category labels.",
        "",
        "## Evidence weaknesses",
        "",
        f"- **{old['one_independent_family']}/{len(rows)}** audited records still have only one independent source family; these cannot pass the READY gate.",
        f"- Source-family mix: {dict(source_bias)}. Book-e Avval appears in {sum(1 for row in rows if 'book_e_avval' in (row.get('independent_source_families') or []))}/{len(rows)} records; it was a major discovery input and was not treated as authoritative.",
        f"- Targeted audit fetches: {task_count} public URL tasks; {page_ok} HTTP-success pages and {page_failed} retained failures/timeouts. Every company had at least one usable page under the audit matching rule, but many usable pages are still self-published or directory evidence.",
        "- Public evidence generally cannot establish budget, current workflow volume, decision authority or the absence of an undisclosed internal engineering team; those fields remain UNKNOWN.",
        "",
        "## Audit interpretation",
        "",
        "The original ranking was materially biased toward directory/category signals and fixed defaults. The corrected ranking is intentionally smaller: only records with corroborated activity and a supported workflow hypothesis are sales-ready. The strongest remaining uncertainty is not a missing score—it is the lack of public proof of internal process volume and buying authority.",
        "",
    ]
    path_for("reports", "ranking_audit.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "old_tier_a": old_counts.get("A", 0), "new_tier_a": new_counts.get("A", 0),
        "old_tier_b": old_counts.get("B", 0), "new_tier_b": new_counts.get("B", 0),
        "promoted": len(promoted), "demoted": len(demoted), "rejected": new_counts.get("Reject", 0),
        "classification_errors_fixed": len(classification_changes), "source_bias": dict(source_bias),
    }


def append_audit_summary(companies: list[dict[str, Any]], audit_rows: list[dict[str, Any]], dossier_count: int, ranking: dict[str, Any]) -> None:
    ready = sum(1 for row in audit_rows if row.get("sales_readiness") == "READY FOR OUTREACH")
    needs = sum(1 for row in audit_rows if row.get("sales_readiness") == "NEEDS DISCOVERY")
    not_ready = sum(1 for row in audit_rows if row.get("sales_readiness") == "NOT READY")
    block = [
        "## Commercial quality audit",
        "",
        f"Generated: {now_iso()}",
        "",
        f"The follow-up audit covered **{len(audit_rows)}** existing Tier A/B records only. Revised tiers are A **{ranking['new_tier_a']}**, B **{ranking['new_tier_b']}**, with **{ready} READY FOR OUTREACH**, **{needs} NEEDS DISCOVERY** and **{not_ready} NOT READY**.",
        "",
        "Use `reports/sales_ready_prospects.md` and `reports/ranking_audit.md` for the commercial decision. The legacy first-run top-100 ranking must not be treated as sales-ready without this audit status.",
        "",
        f"Top human-quality dossier set: **{dossier_count}** under `reports/dossiers/`.",
        "",
    ]
    path = path_for("reports", "executive_summary.md")
    existing = path.read_text(encoding="utf-8") if path.exists() else "# LUMA B2B — Executive Summary\n"
    existing = existing.split("\n## Commercial quality audit", 1)[0].rstrip()
    path.write_text(existing + "\n\n" + "\n".join(block), encoding="utf-8")

    top100 = path_for("reports", "top_100_prospects.md")
    if top100.exists():
        existing = top100.read_text(encoding="utf-8")
        notice = "## Commercial audit notice\n\nThis legacy top-100 artifact predates the 151-record commercial audit. For current sales prioritization, use `reports/sales_ready_prospects.md`, which applies the corrected classification, workflow, evidence-strength and confidence-adjusted gates.\n\n"
        existing = existing.split("## Commercial audit notice", 1)[0]
        top100.write_text(existing.rstrip() + "\n\n" + notice, encoding="utf-8")

    gallery = path_for("reports", "evidence_gallery.md")
    existing = gallery.read_text(encoding="utf-8") if gallery.exists() else "# Evidence Gallery\n"
    existing = existing.split("\n## Commercial audit gallery", 1)[0].rstrip()
    gallery_lines = ["## Commercial audit gallery", "", "These entries are ranked by confidence-adjusted score within the audited cohort.", ""]
    for index, company in enumerate(rank_rows([row for row in audit_rows if row.get("sales_readiness") != "NOT READY"])[:30], 1):
        gallery_lines.extend([f"### {index}. {company.get('company_name_fa')} — adjusted score {company.get('confidence_adjusted_score')}", "", f"- Qualification: {company.get('qualification_reason')}", f"- Evidence notes: {' | '.join((item.get('claim') or '') for item in evidence_items(company, 3)) or 'UNKNOWN'}", f"- Screenshots: {', '.join('`' + path + '`' for path in screenshot_paths(company['company_id'])) or 'UNKNOWN'}", f"- Sources: {', '.join(md_link(url, 'source') for url in source_urls(company)) or 'UNKNOWN'}", ""])
    gallery.write_text(existing + "\n\n" + "\n".join(gallery_lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate commercial audit ranking, sales-ready report and dossiers")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    args = parser.parse_args()
    companies = read_jsonl(args.input)
    rows = audited(companies)
    ranking = write_ranking_audit(rows)
    write_sales_ready(rows)
    dossier_count = write_dossiers(rows)
    append_audit_summary(companies, rows, dossier_count, ranking)
    summary = {"generated_at": now_iso(), "audited": len(rows), "ready_for_outreach": sum(1 for row in rows if row.get("sales_readiness") == "READY FOR OUTREACH"), "needs_discovery": sum(1 for row in rows if row.get("sales_readiness") == "NEEDS DISCOVERY"), "not_ready": sum(1 for row in rows if row.get("sales_readiness") == "NOT READY"), "dossiers": dossier_count, **ranking}
    write_json(path_for("logs", f"commercial-audit-report-{now_iso().replace(':', '').replace('-', '')}.json"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
