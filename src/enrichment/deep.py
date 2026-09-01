from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from src.discovery.run import parse_ddg
from src.enrichment.enrich import analyze_website, likely_site
from src.utilities.common import DEFAULT_PROXY, RateLimiter, canonical_url, domain_of, fetch_url, normalize_persian, now_iso, path_for, read_jsonl, stable_hash, write_json, write_jsonl


def relevant_result(company: dict[str, Any], result: dict[str, Any]) -> bool:
    name = normalize_persian(company.get("company_name_fa"), compact=True)
    title = normalize_persian(result.get("company_name_fa"), compact=True)
    snippet = normalize_persian(result.get("description"), compact=True)
    tokens = [token for token in re.findall(r"[\w\u0600-\u06ff]{3,}", name) if token not in {"شرکت", "دفتر", "مرکزی", "تولید", "فروش", "تجهیزات", "تهران"}]
    if not tokens:
        return True
    return sum(1 for token in tokens if token in title or token in snippet) >= max(1, min(2, len(tokens)))


def preflight(proxy: str) -> bool:
    result = subprocess.run([sys.executable, "-m", "src.utilities.network_preflight", "--proxy", proxy], capture_output=True, text=True, check=False)
    print(result.stdout[-2400:])
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Deep-enrich highest-scoring records with targeted public search and websites")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    parser.add_argument("--proxy", default=DEFAULT_PROXY)
    parser.add_argument("--min-score", type=int, default=65)
    parser.add_argument("--max-companies", type=int, default=300)
    parser.add_argument("--max-sites", type=int, default=250)
    parser.add_argument("--max-workers", type=int, default=5)
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()
    if not args.skip_preflight and not preflight(args.proxy):
        print("Deep enrichment stopped: direct-proxy preflight failed.", file=sys.stderr)
        return 2
    companies = read_jsonl(args.input)
    targets = sorted([company for company in companies if company.get("luma_opportunity_score", 0) >= args.min_score], key=lambda company: (-company.get("luma_opportunity_score", 0), company.get("company_name_fa", "")))[: args.max_companies]
    limiter = RateLimiter(0.45)
    searches: list[dict[str, Any]] = []
    search_results: dict[str, list[dict[str, Any]]] = {}
    print(f"Targeted search for {len(targets)} companies")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        future_map = {}
        for company in targets:
            query = f'"{company.get("company_name_fa", "")}" تهران شرکت'
            url = f"https://html.duckduckgo.com/html/?{urlencode({'q': query, 'kl': 'ir-fa'})}"
            future_map[pool.submit(fetch_url, url, proxy=args.proxy, limiter=limiter, timeout=20.0, max_bytes=1_500_000)] = (company["company_id"], query, url)
        for future in concurrent.futures.as_completed(future_map):
            company_id, query, url = future_map[future]
            response = future.result()
            parsed = parse_ddg(response.get("body", ""), url, query) if response.get("body") else []
            parsed = [row for row in parsed if likely_site(row.get("website")) and relevant_result(next(company for company in targets if company["company_id"] == company_id), row)]
            search_results[company_id] = parsed
            searches.append({"company_id": company_id, "query": query, "url": url, "status": response.get("status"), "result_count": len(parsed), "elapsed_ms": response.get("elapsed_ms"), "error": response.get("error")})

    company_by_id = {company["company_id"]: company for company in companies}
    site_targets: list[tuple[str, str, dict[str, Any]]] = []
    seen_domains: set[str] = set()
    for company in targets:
        for result in search_results.get(company["company_id"], []):
            url = canonical_url(result.get("website"))
            domain = domain_of(url)
            if not url or not domain or domain in seen_domains:
                continue
            seen_domains.add(domain)
            site_targets.append((company["company_id"], url, result))
            break
        if len(site_targets) >= args.max_sites:
            break

    print(f"Fetching {len(site_targets)} targeted company pages")
    site_results: dict[str, dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        future_map = {pool.submit(fetch_url, url, proxy=args.proxy, limiter=limiter, timeout=25.0, max_bytes=2_500_000): (company_id, url, result) for company_id, url, result in site_targets}
        for future in concurrent.futures.as_completed(future_map):
            company_id, url, result = future_map[future]
            response = future.result()
            site = analyze_website(response, url)
            site["search_result_title"] = result.get("source_title")
            site_results[company_id] = site

    for company in companies:
        company_id = company["company_id"]
        for result in search_results.get(company_id, []):
            company.setdefault("source_records", []).append({
                "source_url": result.get("source_url"),
                "source_title": result.get("source_title"),
                "source_type": "targeted_search",
                "source_quality": "search_index",
                "discovery_reason": "Exact-name public search for deep enrichment",
                "evidence_class": "OBSERVED",
                "evidence_snippet": result.get("description"),
                "discovered_at": now_iso(),
            })
        site = site_results.get(company_id)
        if not site:
            continue
        company["deep_website_enrichment"] = site
        if site.get("status") and site.get("final_url"):
            company["website"] = site.get("final_url")
            company["domain"] = domain_of(site.get("final_url"))
            company["website_status"] = str(site.get("status"))
            company["website_candidates"] = sorted(set(company.get("website_candidates", [])) | {site.get("final_url")})
            company["research_status"] = "MEANINGFULLY_ENRICHED"
            company["evidence"].extend(site.get("evidence", []))
            company["phone_public"] = sorted(set(company.get("phone_public", [])) | set(site.get("phones", [])))
            company["email_public"] = sorted(set(company.get("email_public", [])) | set(site.get("emails", [])))
            company["document_types_public"] = sorted(set(company.get("document_types_public", [])) | ({"PDF"} if site.get("pdf_links") else set()))
        company["last_research_date"] = now_iso()

    write_jsonl(path_for("data", "normalized", "companies.jsonl"), companies)
    write_jsonl(path_for("data", "raw", "deep_search.jsonl"), searches)
    write_jsonl(path_for("data", "raw", "deep_websites.jsonl"), list(site_results.values()))
    summary = {
        "completed_at": now_iso(), "target_companies": len(targets), "searches_ok": sum(1 for item in searches if item.get("status") == 200),
        "site_pages_requested": len(site_targets), "site_pages_ok": sum(1 for item in site_results.values() if item.get("status")),
        "companies_with_deep_site": sum(1 for item in site_results.values() if item.get("status")), "min_score": args.min_score, "proxy": args.proxy,
    }
    write_json(path_for("logs", f"deep-enrichment-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
