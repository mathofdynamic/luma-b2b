from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import threading
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.utilities.common import (
    DEFAULT_PROXY,
    RateLimiter,
    canonical_url,
    clean_text,
    corporate_phones,
    domain_of,
    extract_emails,
    extract_links,
    extract_title,
    fetch_url,
    html_to_text,
    is_external_company_url,
    json_ld_objects,
    normalize_persian,
    now_iso,
    path_for,
    read_jsonl,
    stable_hash,
    walk_dicts,
    write_json,
    write_jsonl,
)


BLOCKED_SITE_DOMAINS = {
    "avval.ir", "iran-tejarat.com", "irankarkhaneh.com", "b2bmap.com", "rasmio.com",
    "neshan.org", "balad.ir", "linkedin.com", "instagram.com", "facebook.com",
    "telegram.me", "t.me", "youtube.com", "shams-abad.com", "google.com", "wikipedia.org",
}


def key_from_profile(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"/profile/([^/]+)", url)
    return f"avval:{match.group(1).lower()}" if match else None


def identity_keys(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    profile_key = key_from_profile(row.get("profile_url"))
    if profile_key:
        values.append(profile_key)
    domain = row.get("domain") or domain_of(row.get("website"))
    if domain and domain not in BLOCKED_SITE_DOMAINS:
        values.append(f"domain:{domain}")
    phones = row.get("phones_public") or []
    if phones and row.get("company_name_fa"):
        values.append(f"namephone:{normalize_persian(row['company_name_fa'], compact=True)}:{phones[0]}")
    name = normalize_persian(row.get("company_name_fa"), compact=True)
    address = normalize_persian(row.get("hq_address"), compact=True)[:60]
    if name:
        values.append(f"nameaddr:{name}:{address}")
        values.append(f"name:{name}")
    return values


def merge_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    key_to_group: dict[str, int] = {}
    for row in rows:
        keys = identity_keys(row)
        group_index = next((key_to_group[key] for key in keys if key in key_to_group), None)
        if group_index is None:
            group_index = len(groups)
            groups.append({
                "raw_rows": [], "keys": set(), "source_urls": set(), "profile_urls": set(),
                "names": [], "descriptions": [], "addresses": [], "phones": set(), "emails": set(),
                "social_profiles": set(), "website_candidates": set(), "industry_votes": Counter(),
                "sub_industries": set(), "latitudes": [], "longitudes": [], "discovery_reasons": set(),
            })
        group = groups[group_index]
        # Unioning a later group is rare but important when a domain row connects
        # two Avval profile identities. Keep the more complete connected component.
        for key in keys:
            existing = key_to_group.get(key)
            if existing is not None and existing != group_index:
                other = groups[existing]
                for field in ["raw_rows", "names", "descriptions", "addresses", "discovery_reasons"]:
                    group[field].extend(other[field])
                for field in ["source_urls", "profile_urls", "phones", "emails", "social_profiles", "website_candidates", "sub_industries"]:
                    group[field].update(other[field])
                group["industry_votes"].update(other["industry_votes"])
                group["latitudes"].extend(other["latitudes"])
                group["longitudes"].extend(other["longitudes"])
                for other_key in other["keys"]:
                    key_to_group[other_key] = group_index
                other["raw_rows"] = []
            key_to_group[key] = group_index
            group["keys"].add(key)
        group["raw_rows"].append(row)
        if row.get("source_url"):
            group["source_urls"].add(row["source_url"])
        if row.get("profile_url"):
            group["profile_urls"].add(row["profile_url"])
        if row.get("company_name_fa"):
            group["names"].append(row["company_name_fa"])
        if row.get("description"):
            group["descriptions"].append(row["description"])
        if row.get("hq_address"):
            group["addresses"].append(row["hq_address"])
        group["phones"].update(row.get("phones_public") or [])
        group["emails"].update(row.get("emails_public") or [])
        group["social_profiles"].update(row.get("social_profiles") or [])
        if row.get("website") and is_external_company_url(row.get("website"), source_domains=BLOCKED_SITE_DOMAINS):
            group["website_candidates"].add(row["website"])
        if row.get("industry"):
            group["industry_votes"][row["industry"]] += 1
        if row.get("sub_industry"):
            group["sub_industries"].add(row["sub_industry"])
        if row.get("latitude") is not None:
            group["latitudes"].append(row["latitude"])
        if row.get("longitude") is not None:
            group["longitudes"].append(row["longitude"])
        if row.get("discovery_reason"):
            group["discovery_reasons"].add(row["discovery_reason"])

    output: list[dict[str, Any]] = []
    for group in groups:
        if not group["raw_rows"] or not group["names"]:
            continue
        names = sorted(set(name for name in group["names"] if name), key=lambda value: (-len(value), value))
        descriptions = sorted(set(group["descriptions"]), key=len, reverse=True)
        addresses = sorted(set(group["addresses"]), key=len, reverse=True)
        name = names[0]
        website = sorted(group["website_candidates"], key=lambda url: (0 if urlparse(url).path in {"", "/"} else 1, len(url)))[0] if group["website_candidates"] else None
        company_id = "ir-teh-" + stable_hash(name, website or "", sorted(group["phones"])[0] if group["phones"] else "", addresses[0] if addresses else "")
        industry = group["industry_votes"].most_common(1)[0][0] if group["industry_votes"] else "other"
        first = group["raw_rows"][0]
        source_records = [
            {
                "source_url": item.get("source_url"),
                "source_title": item.get("source_title"),
                "source_type": item.get("source_type"),
                "source_quality": item.get("source_quality"),
                "discovery_reason": item.get("discovery_reason"),
                "evidence_class": item.get("evidence_class"),
                "evidence_snippet": item.get("evidence_snippet"),
                "discovered_at": item.get("discovered_at"),
            }
            for item in group["raw_rows"]
        ]
        source_evidence = [
            {
                "evidence_id": "ev-" + stable_hash(company_id, source.get("source_url"), source.get("evidence_snippet")),
                "claim": "Public source lists the company name and the quoted business/activity context.",
                "evidence_type": source.get("evidence_class") or "OBSERVED",
                "source_url": source.get("source_url"),
                "source_title": source.get("source_title"),
                "captured_at": source.get("discovered_at") or now_iso(),
                "confidence": 0.72 if source.get("source_type") == "industrial_estate_registry" else 0.78,
                "source_quality": source.get("source_quality"),
                "quote_or_snippet": clean_text(source.get("evidence_snippet") or name, 500),
            }
            for source in source_records
            if source.get("source_url")
        ]
        output.append({
            "company_id": company_id,
            "company_name_fa": name,
            "brand_name_fa": name,
            "company_name_en": next((n for n in names if re.search(r"[A-Za-z]", n)), None),
            "aliases": [n for n in names[1:] if n != name][:20],
            "national_id": None,
            "registration_no": None,
            "legal_status": "UNKNOWN",
            "website": website,
            "domain": domain_of(website),
            "website_status": "UNKNOWN",
            "industry": industry,
            "industry_fa": first.get("industry_fa") or "سایر",
            "sub_industry": sorted(group["sub_industries"])[0] if group["sub_industries"] else None,
            "business_model": ["B2B_candidate"],
            "description_observed": descriptions[0] if descriptions else None,
            "hq_address": addresses[0] if addresses else None,
            "operational_addresses": addresses[:10],
            "city": first.get("city") or "تهران",
            "province": first.get("province") or "استان تهران",
            "tehran_area": first.get("tehran_area") or (addresses[0] if addresses else None),
            "industrial_zone": first.get("industrial_zone"),
            "map_listing_urls": [],
            "latitude": group["latitudes"][0] if group["latitudes"] else None,
            "longitude": group["longitudes"][0] if group["longitudes"] else None,
            "phone_public": sorted(group["phones"]),
            "email_public": sorted(group["emails"]),
            "linkedin_company_page": next((url for url in group["social_profiles"] if "linkedin.com/company" in url), None),
            "social_profiles": sorted(group["social_profiles"]),
            "employee_estimate_min": None,
            "employee_estimate_max": None,
            "employee_confidence": 0.0,
            "founded_year": None,
            "company_age_years": None,
            "branches_count": None,
            "warehouses_count": None,
            "factories_count": None,
            "geographic_reach": None,
            "visible_customers": [],
            "visible_projects": [],
            "products_services": [],
            "certifications": [],
            "association_memberships": [],
            "active_jobs_count": None,
            "job_families": [],
            "existing_software_signals": [],
            "portal_features": [],
            "document_types_public": [],
            "source_records": source_records,
            "source_urls": sorted(group["source_urls"]),
            "discovery_reasons": sorted(group["discovery_reasons"]),
            "raw_record_count": len(group["raw_rows"]),
            "profile_urls": sorted(group["profile_urls"]),
            "website_candidates": sorted(group["website_candidates"]),
            "evidence": source_evidence,
            "enrichment_errors": [],
            "research_status": "DISCOVERED",
            "last_research_date": now_iso(),
        })
    return output


def parse_profile(response: dict[str, Any], profile_url: str) -> dict[str, Any]:
    body = response.get("body", "")
    title = extract_title(body)
    links = extract_links(body, response.get("final_url") or profile_url)
    external_sites = []
    socials = []
    for link in links:
        href = link.get("href")
        if not href:
            continue
        if any(host in href for host in ["instagram.com", "linkedin.com", "facebook.com", "t.me", "telegram.me", "youtube.com"]):
            socials.append(href)
        elif is_external_company_url(href, source_domains=BLOCKED_SITE_DOMAINS):
            if not re.search(r"\.(?:jpg|jpeg|png|gif|svg|pdf)(?:$|\?)", href, re.I):
                external_sites.append(href)
    names: list[str] = []
    addresses: list[str] = []
    for root in json_ld_objects(body):
        for item in walk_dicts(root):
            if item.get("name") and (item.get("address") or item.get("telephone")):
                names.append(clean_text(item.get("name")))
                address = item.get("address")
                if isinstance(address, dict):
                    addresses.append(clean_text(address.get("streetAddress")))
                elif address:
                    addresses.append(clean_text(address))
    text = html_to_text(body, 18000)
    emails = [email for email in extract_emails(text) if email.split("@", 1)[-1] not in {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}]
    return {
        "url": profile_url,
        "status": response.get("status"),
        "final_url": response.get("final_url"),
        "title": title,
        "names": sorted(set(names)),
        "addresses": sorted(set(address for address in addresses if address)),
        "phones": corporate_phones(text),
        "emails": sorted(set(emails)),
        "website_candidates": sorted(set(external_sites))[:10],
        "social_profiles": sorted(set(socials)),
        "text_excerpt": text,
        "content_type": response.get("content_type"),
        "elapsed_ms": response.get("elapsed_ms"),
        "error": response.get("error"),
    }


def likely_site(url: str | None) -> bool:
    domain = domain_of(url)
    if not domain or any(domain == blocked or domain.endswith("." + blocked) for blocked in BLOCKED_SITE_DOMAINS):
        return False
    return True


SIGNAL_TERMS: dict[str, list[str]] = {
    "rfq_or_quote": ["استعلام قیمت", "درخواست قیمت", "پیش فاکتور", "استعلام بها", "call for quote", "request a quote", "تماس با فروش"],
    "catalog_or_products": ["کاتالوگ", "محصولات", "محصول", "catalog", "products", ".pdf"],
    "order_or_contact_form": ["فرم سفارش", "ثبت سفارش", "فرم تماس", "تماس با ما", "contact us", "order form"],
    "branches_or_dealers": ["شعب", "نمایندگان", "نمایندگی", "دفاتر", "dealer", "branches", "نماینده فروش"],
    "factory_or_warehouse": ["کارخانه", "کارخانجات", "انبار", "شهرک صنعتی", "خط تولید", "factory", "warehouse", "production line"],
    "service_after_sales": ["خدمات پس از فروش", "گارانتی", "تعمیرات", "پشتیبانی فنی", "service", "warranty", "کالیبراسیون"],
    "projects_or_clients": ["پروژه ها", "پروژه‌ها", "مشتریان", "همکاران", "clients", "projects", "case study"],
    "certifications": ["iso", "استاندارد", "گواهینامه", "مجوز", "certificate", "gmp"],
    "tender_or_contract": ["مناقصه", "مزایده", "قرارداد", "tender", "contract", "بازرگانی"],
    "software_or_erp": ["erp", "crm", "راهکاران", "همکاران سیستم", "سپیدار", "نرم افزار", "نرم‌افزار", "excel", "اکسل"],
    "internal_tech_hiring": ["هوش مصنوعی", "یادگیری ماشین", "دانشمند داده", "برنامه نویس", "برنامه‌نویس", "توسعه دهنده", "پایتون", "backend", "frontend", "devops", "mlops"],
    "admin_or_operations_hiring": ["کارشناس فروش", "کارشناس بازرگانی", "کارشناس انبار", "کارشناس برنامه ریزی", "کارشناس برنامه‌ریزی", "حسابدار", "اپراتور", "دفتری"],
    "expansion_or_activity": ["تاسیس", "تأسیس", "افتتاح", "توسعه", "صادرات", "تولید کننده", "تولیدکننده", "سراسر کشور"],
}


def analyze_website(response: dict[str, Any], url: str) -> dict[str, Any]:
    body = response.get("body", "")
    text = html_to_text(body, 24000)
    normalized = normalize_persian(text)
    links = extract_links(body, response.get("final_url") or url)
    same_domain = domain_of(response.get("final_url") or url)
    relevant_links: list[dict[str, str]] = []
    pdf_links: list[str] = []
    for link in links:
        href = link.get("href")
        label = link.get("text", "")
        if not href:
            continue
        if re.search(r"\.pdf(?:$|\?)", href, re.I):
            pdf_links.append(href)
        if domain_of(href) == same_domain and any(term in normalize_persian(label + " " + href) for term in ["محصول", "کاتالوگ", "خدمات", "پروژه", "درباره", "تماس", "مناقصه", "catalog", "product", "service", "project", "about", "contact", "tender"]):
            relevant_links.append({"url": href, "label": clean_text(label, 180)})
    signals: dict[str, bool] = {}
    for signal, terms in SIGNAL_TERMS.items():
        signals[signal] = any(normalize_persian(term) in normalized or term.lower() in normalized for term in terms)
    evidence: list[dict[str, Any]] = []
    for signal, present in signals.items():
        if not present:
            continue
        terms = [term for term in SIGNAL_TERMS[signal] if normalize_persian(term) in normalized or term.lower() in normalized]
        evidence.append({
            "evidence_id": "ev-" + stable_hash(url, signal),
            "claim": f"Public website signal: {signal}",
            "evidence_type": "OBSERVED",
            "source_url": response.get("final_url") or url,
            "source_title": extract_title(body),
            "captured_at": now_iso(),
            "confidence": 0.86 if signal in {"catalog_or_products", "rfq_or_quote", "factory_or_warehouse"} else 0.72,
            "source_quality": "company_site",
            "quote_or_snippet": clean_text("; ".join(terms) + " | " + text[:420], 700),
            "signal": signal,
        })
    return {
        "url": url,
        "status": response.get("status"),
        "final_url": response.get("final_url"),
        "title": extract_title(body),
        "content_type": response.get("content_type"),
        "elapsed_ms": response.get("elapsed_ms"),
        "text_excerpt": text,
        "signals": signals,
        "evidence": evidence,
        "relevant_links": relevant_links[:20],
        "pdf_links": sorted(set(pdf_links))[:30],
        "phones": corporate_phones(text),
        "emails": [email for email in extract_emails(text) if email.split("@", 1)[-1] not in {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}],
        "error": response.get("error"),
    }


def run_preflight(proxy: str) -> bool:
    result = subprocess.run([sys.executable, "-m", "src.utilities.network_preflight", "--proxy", proxy], capture_output=True, text=True, check=False)
    print(result.stdout[-3000:])
    if result.returncode != 0:
        print("Enrichment stopped: direct-proxy preflight failed.", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize and enrich public Tehran company records")
    parser.add_argument("--input", default="data/raw/candidates.jsonl")
    parser.add_argument("--proxy", default=DEFAULT_PROXY)
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--max-profiles", type=int, default=1600)
    parser.add_argument("--max-sites", type=int, default=1200)
    parser.add_argument("--rate-limit-seconds", type=float, default=1.0)
    parser.add_argument("--priority-file", default=None, help="Optional scored JSONL; highest-scored records are enriched first")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()
    if not args.skip_preflight and not run_preflight(args.proxy):
        return 2
    raw = read_jsonl(args.input)
    companies = merge_rows(raw)
    if args.priority_file:
        priority_rows = read_jsonl(args.priority_file)
        priority_order = {
            item.get("company_id"): index
            for index, item in enumerate(sorted(priority_rows, key=lambda item: (-item.get("luma_opportunity_score", 0), item.get("company_name_fa", ""))))
            if item.get("company_id")
        }
        companies.sort(key=lambda item: (priority_order.get(item.get("company_id"), len(priority_order) + 1), item.get("company_name_fa", "")))
    write_jsonl(path_for("data", "normalized", "companies_discovered.jsonl"), companies)
    print(f"Normalized {len(raw)} raw rows into {len(companies)} company components")

    interval = RateLimiter(args.rate_limit_seconds)
    profile_urls: list[tuple[str, str]] = []
    for company in companies:
        for url in company.get("profile_urls", [])[:3]:
            profile_urls.append((company["company_id"], url))
    profile_urls = profile_urls[: args.max_profiles]
    profile_results: dict[tuple[str, str], dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    print(f"Fetching {len(profile_urls)} public directory profiles")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        future_map = {pool.submit(fetch_url, url, proxy=args.proxy, limiter=interval, timeout=20.0, max_bytes=2_500_000): (company_id, url) for company_id, url in profile_urls}
        for future in concurrent.futures.as_completed(future_map):
            key = future_map[future]
            response = future.result()
            profile_results[key] = {"company_id": key[0], **parse_profile(response, key[1])}
            if response.get("error"):
                errors.append({"stage": "profile", "company_id": key[0], "url": key[1], "error": response.get("error")})

    by_id = {company["company_id"]: company for company in companies}
    for (company_id, url), profile in profile_results.items():
        company = by_id.get(company_id)
        if not company:
            continue
        company.setdefault("profile_enrichment", []).append(profile)
        if profile.get("status") == 200:
            company["research_status"] = "PROFILE_ENRICHED"
        elif profile.get("error"):
            company.setdefault("enrichment_errors", []).append({"stage": "profile", "url": url, "error": profile.get("error")})
        for name in profile.get("names", []):
            if name and name != company["company_name_fa"] and name not in company["aliases"]:
                company["aliases"].append(name)
        if profile.get("addresses") and not company.get("hq_address"):
            company["hq_address"] = profile["addresses"][0]
            company["operational_addresses"] = profile["addresses"][:10]
        company["phone_public"] = sorted(set(company.get("phone_public", [])) | set(profile.get("phones", [])))
        company["email_public"] = sorted(set(company.get("email_public", [])) | set(profile.get("emails", [])))
        company["social_profiles"] = sorted(set(company.get("social_profiles", [])) | set(profile.get("social_profiles", [])))
        for site in profile.get("website_candidates", []):
            if likely_site(site):
                company.setdefault("website_candidates", []).append(site)
        company["website_candidates"] = sorted(set(company.get("website_candidates", [])))
        company["evidence"].append({
            "evidence_id": "ev-" + stable_hash(company_id, url, "directory_profile"),
            "claim": f"Directory profile lists {company['company_name_fa']} with a public Tehran business listing.",
            "evidence_type": "OBSERVED",
            "source_url": url,
            "source_title": profile.get("title"),
            "captured_at": now_iso(),
            "confidence": 0.82 if profile.get("status") == 200 else 0.45,
            "source_quality": "directory",
            "quote_or_snippet": clean_text(profile.get("text_excerpt"), 500),
        })

    site_urls: list[tuple[str, str]] = []
    seen_sites: set[str] = set()
    for company in companies:
        candidates = list(company.get("website_candidates", []))
        if company.get("website"):
            candidates.insert(0, company["website"])
        for url in candidates:
            if not likely_site(url):
                continue
            domain = domain_of(url)
            if not domain or domain in seen_sites:
                continue
            seen_sites.add(domain)
            site_urls.append((company["company_id"], url))
            break
        if args.max_sites <= 0:
            site_urls = []
        elif len(site_urls) >= args.max_sites:
            break
    print(f"Fetching {len(site_urls)} public company websites")
    site_results: dict[tuple[str, str], dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        future_map = {pool.submit(fetch_url, url, proxy=args.proxy, limiter=interval, timeout=25.0, max_bytes=3_000_000): (company_id, url) for company_id, url in site_urls}
        for future in concurrent.futures.as_completed(future_map):
            key = future_map[future]
            response = future.result()
            analyzed = analyze_website(response, key[1])
            site_results[key] = analyzed
            if response.get("error"):
                errors.append({"stage": "website", "company_id": key[0], "url": key[1], "error": response.get("error")})

    for (company_id, requested_url), site in site_results.items():
        company = by_id.get(company_id)
        if not company:
            continue
        if site.get("status"):
            company["website"] = site.get("final_url") or requested_url
            company["domain"] = domain_of(company["website"])
            company["website_status"] = str(site.get("status"))
            company["research_status"] = "WEBSITE_ENRICHED"
        elif company.get("website_status") == "UNKNOWN":
            company["website_status"] = "UNREACHABLE"
        company["website_enrichment"] = site
        company["existing_software_signals"] = sorted(set(company.get("existing_software_signals", [])) | {key for key, value in site.get("signals", {}).items() if value and key == "software_or_erp"})
        company["document_types_public"] = sorted(set(company.get("document_types_public", [])) | ({"PDF"} if site.get("pdf_links") else set()))
        company["evidence"].extend(site.get("evidence", []))
        company["phone_public"] = sorted(set(company.get("phone_public", [])) | set(site.get("phones", [])))
        company["email_public"] = sorted(set(company.get("email_public", [])) | set(site.get("emails", [])))

    for company in companies:
        company["aliases"] = sorted(set(company.get("aliases", [])))[:30]
        company["website_candidates"] = sorted(set(company.get("website_candidates", [])))[:20]
        profile_ok = any(profile.get("status") == 200 for profile in company.get("profile_enrichment", []))
        site_ok = company.get("website_status", "").isdigit() and 200 <= int(company["website_status"]) < 400
        source_types = {record.get("source_type") for record in company.get("source_records", []) if record.get("source_type")}
        evidence_count = len(company.get("evidence", []))
        listing_ok = bool(company.get("hq_address") and company.get("phone_public") and company.get("description_observed"))
        cross_source_ok = len({record.get("source_type") for record in company.get("source_records", []) if record.get("source_type")}) >= 2 and bool(company.get("hq_address"))
        if site_ok or (profile_ok and evidence_count >= 2) or listing_ok or cross_source_ok:
            company["research_status"] = "MEANINGFULLY_ENRICHED"
        company["last_research_date"] = now_iso()

    # Keep a compact, auditable source table separate from the denormalized company record.
    source_rows: list[dict[str, Any]] = []
    for company in companies:
        for source in company.get("source_records", []):
            source_rows.append({
                "source_id": "src-" + stable_hash(company["company_id"], source.get("source_url"), source.get("source_title"), source.get("evidence_snippet")),
                "company_id": company["company_id"],
                **source,
            })
        for evidence in company.get("evidence", []):
            source_rows.append({
                "source_id": evidence.get("evidence_id"),
                "company_id": company["company_id"],
                "source_type": evidence.get("source_quality"),
                "source_url": evidence.get("source_url"),
                "source_title": evidence.get("source_title"),
                "retrieved_at": evidence.get("captured_at"),
                "claim": evidence.get("claim"),
                "evidence_class": evidence.get("evidence_type"),
                "confidence": evidence.get("confidence"),
                "quote_or_snippet": evidence.get("quote_or_snippet"),
            })

    output = path_for("data", "normalized", "companies.jsonl")
    write_jsonl(output, companies)
    write_jsonl(path_for("data", "normalized", "sources.jsonl"), source_rows)
    write_jsonl(path_for("data", "raw", "profile_enrichment.jsonl"), list(profile_results.values()))
    write_jsonl(path_for("data", "raw", "website_enrichment.jsonl"), list(site_results.values()))
    summary = {
        "completed_at": now_iso(),
        "raw_rows": len(raw),
        "normalized_companies": len(companies),
        "profile_pages_requested": len(profile_urls),
        "profile_pages_ok": sum(1 for result in profile_results.values() if result.get("status") == 200),
        "website_pages_requested": len(site_urls),
        "website_pages_ok": sum(1 for result in site_results.values() if result.get("status")),
        "meaningfully_enriched": sum(1 for company in companies if company.get("research_status") == "MEANINGFULLY_ENRICHED"),
        "status_counts": dict(Counter(company.get("research_status") for company in companies)),
        "industry_counts": dict(Counter(company.get("industry") for company in companies)),
        "errors": errors,
        "proxy": args.proxy,
    }
    write_json(path_for("logs", f"enrichment-{now_iso().replace(':', '').replace('-', '')}.json"), summary)
    print(json.dumps({key: summary[key] for key in ["raw_rows", "normalized_companies", "profile_pages_requested", "profile_pages_ok", "website_pages_requested", "website_pages_ok", "meaningfully_enriched", "status_counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
