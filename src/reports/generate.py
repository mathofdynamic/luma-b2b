"""Generate the human-readable research, prospect and evidence reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.utilities.common import domain_of, now_iso, path_for, read_jsonl, write_json


LABELS = {
    "industrial_distributors_importers": "Industrial distributors / importers / wholesalers",
    "industrial_manufacturers": "Mid-market industrial manufacturers",
    "food_fmcg": "Food / FMCG manufacturers and distributors",
    "logistics_freight_customs": "Freight forwarding / logistics / customs",
    "printing_packaging_labeling": "Printing / packaging / labeling",
    "medical_equipment": "Medical-equipment distributors / importers",
    "auto_parts": "Auto-parts manufacturers / established distributors",
    "epc_engineering_contractors": "EPC / engineering / industrial contractors",
    "building_materials_mep": "Building-material / MEP suppliers",
    "industrial_maintenance_after_sales": "Industrial maintenance / after-sales",
    "pharma": "Pharmaceutical",
    "other": "Other / unresolved",
}


def latest_log(prefix: str) -> dict[str, Any]:
    files = sorted([item for item in path_for("logs").glob(f"{prefix}-*.json") if not item.name.startswith("._")], key=lambda item: item.stat().st_mtime)
    if not files:
        return {}
    try:
        return json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception:
        return {}


def md_link(url: str | None, label: str | None = None) -> str:
    if not url:
        return "UNKNOWN"
    return f"[{label or url}]({url})"


def screenshot_paths(company_id: str) -> list[str]:
    directory = path_for("evidence", "companies", company_id, "screenshots")
    if not directory.exists():
        return []
    return sorted(str(item.relative_to(path_for())) for item in directory.glob("*.png") if not item.name.startswith("._"))


def corporate_website(company: dict[str, Any]) -> str | None:
    if company.get("website_quality_issue"):
        return None
    website = company.get("website")
    if website and str(company.get("website_status", "")).isdigit() and 200 <= int(company.get("website_status")) < 400:
        return website
    for candidate in company.get("website_candidates") or []:
        domain = domain_of(candidate)
        if domain and not any(domain == blocked or domain.endswith("." + blocked) for blocked in ["rubika.ir", "aparat.com", "instagram.com", "facebook.com", "linkedin.com", "youtube.com", "telegram.me", "t.me", "x.com", "twitter.com"]):
            return candidate
    return None


def capture_error_summary() -> dict[str, Any]:
    """Summarize retained source errors from the per-company evidence packages."""
    packages_with_errors = 0
    errors = 0
    headless_blocked = 0
    domains: Counter[str] = Counter()
    for package_file in path_for("evidence", "companies").glob("*/sources.json"):
        if package_file.name.startswith("._"):
            continue
        try:
            payload = json.loads(package_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        package_errors = payload.get("errors") or []
        if package_errors:
            packages_with_errors += 1
        errors += len(package_errors)
        headless_blocked += sum(1 for item in package_errors if item.get("classification") == "HEADLESS_BLOCKED")
        for item in package_errors:
            domain = domain_of(item.get("source_url"))
            if domain:
                domains[domain] += 1
    return {
        "packages_with_errors": packages_with_errors,
        "errors": errors,
        "headless_blocked": headless_blocked,
        "common_domains": domains.most_common(12),
    }


def source_urls(company: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(
        [item.get("source_url") for item in company.get("source_records", []) if item.get("source_url")]
        + [item.get("source_url") for item in company.get("evidence", []) if item.get("source_url") and not item.get("excluded_from_qualification")]
    ))[:12]


def best_evidence(company: dict[str, Any], limit: int = 3) -> list[str]:
    values: list[str] = []
    for evidence in company.get("evidence", []):
        if evidence.get("excluded_from_qualification"):
            continue
        snippet = evidence.get("quote_or_snippet")
        if snippet:
            values.append(snippet)
    for source in company.get("source_records", []):
        if source.get("evidence_snippet"):
            values.append(source["evidence_snippet"])
    return list(dict.fromkeys(values))[:limit]


def eligible_top(company: dict[str, Any]) -> bool:
    return company.get("priority_tier") in {"A", "B"} and not company.get("hard_disqualifier")


def company_line(company: dict[str, Any], rank: int) -> str:
    workflow = (company.get("workflow_opportunities") or [{}])[0]
    shots = screenshot_paths(company["company_id"])
    sources = source_urls(company)
    location = company.get("hq_address") or company.get("industrial_zone") or "UNKNOWN"
    website = corporate_website(company)
    proposal = Path("proposals", f"{company['company_id']}.md")
    evidence = best_evidence(company)
    lines = [
        f"{rank}. **{company.get('company_name_fa')}** — {LABELS.get(company.get('industry'), company.get('industry'))}; {location}; score **{company.get('luma_opportunity_score')}** ({company.get('priority_tier')}).",
        f"   Website: {md_link(website)}; digital maturity: {company.get('digital_maturity_score')} / fit {company.get('digital_maturity_fit_score')}; internal tech capability: {company.get('internal_tech_capability_score')} / outsourcing fit {company.get('outsourcing_fit_score')}.",
        f"   Qualification: {company.get('qualification_reason')}",
        f"   Strongest observed evidence: {' | '.join(evidence) if evidence else 'UNKNOWN — no preserved quote beyond the source record.'}",
        f"   Strongest workflow hypothesis: **{workflow.get('workflow_name', 'UNKNOWN')}** — {workflow.get('current_process_hypothesis', 'UNKNOWN')}",
        f"   Likely decision-maker role: {company.get('decision_maker_role') or 'UNKNOWN'}; proposal: {md_link(str(proposal), str(proposal)) if proposal.exists() else 'Not generated by the proposal gate.'}",
        f"   Sources: {'; '.join(md_link(url, 'source') for url in sources) if sources else 'UNKNOWN'}",
        f"   Screenshots: {'; '.join(f'`{shot}`' for shot in shots) if shots else 'UNKNOWN'}",
    ]
    return "\n".join(lines)


def write_reports(companies: list[dict[str, Any]]) -> dict[str, int]:
    scored = [company for company in companies if company.get("luma_opportunity_score") is not None]
    top = sorted([company for company in scored if eligible_top(company)], key=lambda item: (-item.get("luma_opportunity_score", 0), item.get("company_name_fa", "")))[:100]
    tiers = Counter(company.get("priority_tier") for company in scored)
    industries = Counter(company.get("industry") for company in scored)
    enriched = sum(1 for company in companies if company.get("research_status") == "MEANINGFULLY_ENRICHED")
    screenshots = sum(len(screenshot_paths(company["company_id"])) for company in companies)
    proposals = len(read_jsonl(path_for("data", "normalized", "proposals.jsonl")))
    raw = len(read_jsonl(path_for("data", "raw", "candidates.jsonl")))
    vic = latest_log("vic-discovery")
    discovery = latest_log("discovery")
    enrichment = latest_log("enrichment")
    capture = latest_log("evidence-capture")
    capture_errors = capture_error_summary()
    deep = latest_log("deep-enrichment")
    qualified_segment_counts = Counter(
        company.get("industry")
        for company in scored
        if company.get("priority_tier") in {"A", "B"} and company.get("industry") != "other"
    )
    best_qualified_segment = qualified_segment_counts.most_common(1)[0] if qualified_segment_counts else ("other", 0)
    best_qualified_segment_text = f"{LABELS.get(best_qualified_segment[0], best_qualified_segment[0])} ({best_qualified_segment[1]} Tier A/B records)"

    executive = [
        "# LUMA B2B Tehran — Executive Summary", "", f"Generated: {now_iso()}", "",
        f"The first production run contains **{raw:,} raw candidate rows**, **{len(companies):,} canonical company records**, **{enriched:,} meaningfully enriched records**, and **{len(scored):,} scored records**.",
        "", f"Tier counts: A **{tiers.get('A', 0):,}**, B **{tiers.get('B', 0):,}**, C **{tiers.get('C', 0):,}**, D **{tiers.get('D', 0):,}**, Reject **{tiers.get('Reject', 0):,}**.",
        "", f"The run covers {sum(1 for key in industries if key != 'other')} priority-relevant industry codes plus an unresolved/other bucket. The strongest public-evidence pattern is a Tehran-area operating context with a usable description, public landline, reachable management channel and an observable document/catalog/operations surface.",
        "", "## Strategic read", "",
        f"- The strongest current segment by qualified volume is **{best_qualified_segment_text}**; this is derived from actual public listing and website evidence, not location alone.",
        "- Moderate digital maturity is treated as a fit window. A missing or extremely thin public digital footprint lowers confidence; a strong internal software/AI signal lowers outsourcing fit.",
        "- Workflow opportunities are hypotheses. No internal manual process, ROI percentage, budget or decision authority is claimed without direct evidence.",
        "", "## First-run limitations", "",
        "- Search-engine exact-name deep enrichment was stopped after direct-proxy timeouts; the blocked source is recorded rather than rerouted through the VPN.",
        "- National/legal IDs, employee counts, founding years and active status remain UNKNOWN unless a public source established them; the index is not treated as a legal registry.",
        f"- Headless visual evidence: **{screenshots:,}** screenshots; company packages retain {capture_errors['errors']} ordinary source/capture errors across {capture_errors['packages_with_errors']} packages and {capture_errors['headless_blocked']} HEADLESS_BLOCKED pages.",
    ]
    path_for("reports", "executive_summary.md").write_text("\n".join(executive) + "\n", encoding="utf-8")

    discovery_report = [
        "# Discovery Report", "", f"Generated: {now_iso()}", "",
        "## Scope and method", "",
        "Persian-first public discovery was run for Tehran city/Tehran Province across the priority industries and the research-defined clusters. The run used Book-e Avval category pages, public official/association references, Persian search results where responsive, and the public VIC industrial-estate company/activity index.",
        "", f"Raw candidate rows: **{raw:,}**; canonical after deterministic normalization/deduplication: **{len(companies):,}**.", "",
        "## Source run results", "",
        f"- Book-e Avval / broad directory: {discovery.get('source_counts', {}).get('directory', 'recorded in discovery log')} rows in the broad run.",
        f"- VIC industrial-estate index: {vic.get('candidate_count', 'UNKNOWN')} rows across {len(vic.get('runs', []))} configured zone requests; final successful zones are retained in `data/raw/industrial_estate_sources.json`.",
        f"- Search and official/association rows are retained in the raw candidate file and source table; targeted exact-name search was later stopped after direct-proxy timeout behavior.",
        "", "## Deduplication", "", "Identity is connected by Avval profile key, external domain, public landline plus normalized name, normalized name/address and finally normalized name. Names are normalized for Arabic/Persian character variants, Persian/Arabic digits and zero-width characters. A canonical record preserves all source rows in `source_records`.",
        "", "## Qualification boundary", "", "A zone index establishes discovery and an activity label only. It does not establish a strong business, active status, purchasing power or workflow pain. Thin index-only records are retained for future enrichment but capped below B/A by the scoring model.",
        "", "## Blocked / incomplete", "", "- DuckDuckGo targeted exact-name enrichment: direct-proxy requests timed out; that batch was stopped.\n- Avval concurrent profile pass: earlier high-concurrency requests produced HTTP 429s; a later serial prioritized pass returned 220/220 HTTP 200.\n- Some public sites returned unreachable/unknown status and remain explicitly marked.",
    ]
    path_for("reports", "discovery_report.md").write_text("\n".join(discovery_report) + "\n", encoding="utf-8")

    segment_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for company in scored:
        segment_rows[company.get("industry") or "other"].append(company)
    qualified_by_segment = {
        key: sum(1 for item in values if item.get("priority_tier") in {"A", "B"})
        for key, values in segment_rows.items()
        if key != "other"
    }
    best_segment_key = max(qualified_by_segment, key=qualified_by_segment.get) if qualified_by_segment else None
    best_segment_text = (
        f"{LABELS.get(best_segment_key, best_segment_key)} ({qualified_by_segment[best_segment_key]} Tier A/B records)"
        if best_segment_key else "UNKNOWN"
    )
    segment = ["# Segment Performance", "", "Counts include the full canonical scored universe. Tier A/B counts are not a claim that every record is fully researched; the enrichment and evidence columns show that distinction.", "", "| Segment | Canonical | Enriched | A | B | Median score | Top score |", "|---|---:|---:|---:|---:|---:|---:|"]
    for key, values in sorted(segment_rows.items(), key=lambda pair: (-max(item.get('luma_opportunity_score', 0) for item in pair[1]), pair[0])):
        scores = sorted(item.get("luma_opportunity_score", 0) for item in values)
        segment.append(f"| {LABELS.get(key, key)} | {len(values)} | {sum(1 for item in values if item.get('research_status') == 'MEANINGFULLY_ENRICHED')} | {sum(1 for item in values if item.get('priority_tier') == 'A')} | {sum(1 for item in values if item.get('priority_tier') == 'B')} | {scores[len(scores)//2]} | {max(scores)} |")
    segment += ["", f"Best-performing segment by current Tier A/B volume: **{best_segment_text}**.", "", "Interpretation: the ranking is a qualification signal under the documented model, not a market-size estimate. Industrial-estate-only records are intentionally held below B/A until corroborated."]
    path_for("reports", "segment_performance.md").write_text("\n".join(segment) + "\n", encoding="utf-8")

    source_counts = Counter(item.get("source_type") for company in companies for item in company.get("source_records", []))
    coverage = ["# Source Coverage", "", f"Generated: {now_iso()}", "", "| Source type | Preserved source rows | Notes |", "|---|---:|---|"]
    for source, count in source_counts.most_common():
        notes = {"directory": "Book-e Avval public category/listing evidence", "industrial_estate_registry": "VIC public industrial-estate company/activity index", "search": "Persian search discovery; not authoritative", "official_reference": "Public official/association reference links"}.get(source, "Public discovery source")
        coverage.append(f"| {source} | {count} | {notes} |")
    coverage += ["", "## Source limitations", "", "No one directory is treated as authoritative. Legal/company-registry and market-data fields remain UNKNOWN unless public evidence is present. LinkedIn, map portals, Rasmio/Codal and job platforms were not used through private/authenticated access; targeted search was recorded as blocked when the direct route timed out.", "", "## Evidence capture failures", "", f"The evidence packages retain {capture_errors['errors']} ordinary source/capture errors across {capture_errors['packages_with_errors']} packages; these are not silently converted into observations. HEADLESS_BLOCKED classifications: **{capture_errors['headless_blocked']}**.", "", "Representative failure domains: " + (", ".join(f"`{domain}` ({count})" for domain, count in capture_errors["common_domains"]) if capture_errors["common_domains"] else "None recorded."), "", "## Network provenance", "", "Iranian research traffic used `http://127.0.0.1:1087` with the VPN left connected. Preflight logs under `logs/network_preflight-*.json` record the comparison and direct egress."]
    path_for("reports", "source_coverage.md").write_text("\n".join(coverage) + "\n", encoding="utf-8")

    top_report = ["# Top 100 Prospects", "", "Ranked by the transparent evidence-first opportunity score. Hard-disqualified records are excluded; fields marked UNKNOWN remain unknown.", ""]
    for index, company in enumerate(top, 1):
        top_report.append(company_line(company, index))
        top_report.append("")
    path_for("reports", "top_100_prospects.md").write_text("\n".join(top_report), encoding="utf-8")

    gallery = ["# Evidence Gallery", "", "Visual evidence was captured with isolated headless Playwright sessions through the direct proxy. Screenshots are public-page evidence, not synthetic images.", ""]
    gallery_dir = path_for("reports", "top_100_evidence")
    gallery_dir.mkdir(parents=True, exist_ok=True)
    for index, company in enumerate(top, 1):
        shots = screenshot_paths(company["company_id"])
        sources = source_urls(company)
        snippets = best_evidence(company, 2)
        gallery.extend([f"## {index}. {company.get('company_name_fa')} — score {company.get('luma_opportunity_score')}", "", f"Qualification: {company.get('qualification_reason')}", "", f"Evidence notes: {' | '.join(snippets) if snippets else 'UNKNOWN'}", "", "Screenshots:"])
        gallery.extend([f"- `{shot}`" for shot in shots] or ["- UNKNOWN — no screenshot captured."])
        gallery.extend(["", "Sources:"])
        gallery.extend([f"- {md_link(url)}" for url in sources] or ["- UNKNOWN"])
        gallery.append("")
        mini = [f"# {index}. {company.get('company_name_fa')}", "", f"Score: {company.get('luma_opportunity_score')} ({company.get('priority_tier')})", f"Qualification: {company.get('qualification_reason')}", "", "## Evidence notes", ""]
        mini.extend([f"- {snippet}" for snippet in snippets] or ["- UNKNOWN"])
        mini.extend(["", "## Screenshots", ""])
        mini.extend([f"- `{shot}`" for shot in shots] or ["- UNKNOWN"])
        mini.extend(["", "## Sources", ""])
        mini.extend([f"- {md_link(url)}" for url in sources] or ["- UNKNOWN"])
        mini.append("")
        (gallery_dir / f"{index:03d}-{company['company_id']}.md").write_text("\n".join(mini), encoding="utf-8")
    path_for("reports", "evidence_gallery.md").write_text("\n".join(gallery), encoding="utf-8")

    quality = [
        "# Data Quality Report", "", "This report is generated before the final QA command and is supplemented by `logs/qa-*.json`.", "", f"Canonical records: {len(companies):,}; raw rows: {raw:,}; enriched: {enriched:,}; scored: {len(scored):,}; screenshots: {screenshots:,}; proposals: {proposals:,}.", "", "## Known issues", "", "- A public industrial-estate index provides valuable activity discovery but not legal activity, size or purchasing power; index-only rows are marked DISCOVERED and capped below B/A.", "- Some Avval listing records are meaningfully enriched under this run's operational definition (description + Tehran address + public landline) but still lack independent corroboration.", "- Website, employee, founding-year, legal-ID, branch and active-status fields can remain UNKNOWN.", "- Exact-name search enrichment timed out through the direct proxy and was stopped; no VPN fallback was used.", "", "## QA commands", "", "Run `python3 -m src.utilities.qa --input data/normalized/companies.jsonl` after exports and evidence capture. The command checks identity uniqueness, score/tier consistency, URL presence, screenshot metadata, encoding, credentials patterns, and network/browser provenance."]
    path_for("reports", "data_quality_report.md").write_text("\n".join(quality) + "\n", encoding="utf-8")

    return {"raw": raw, "companies": len(companies), "enriched": enriched, "scored": len(scored), "top100": len(top), "screenshots": screenshots, "proposals": proposals}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate LUMA B2B markdown reports")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    args = parser.parse_args()
    summary = write_reports(read_jsonl(args.input))
    write_json(path_for("logs", f"reports-{now_iso().replace(':', '').replace('-', '')}.json"), {"completed_at": now_iso(), **summary})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
