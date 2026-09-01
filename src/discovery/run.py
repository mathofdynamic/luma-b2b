from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import threading
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urlparse

from src.utilities.common import (
    DEFAULT_PROXY,
    RateLimiter,
    canonical_url,
    clean_text,
    corporate_phones,
    domain_of,
    extract_links,
    extract_title,
    fetch_url,
    html_to_text,
    is_external_company_url,
    json_ld_objects,
    now_iso,
    parse_simple_yaml,
    path_for,
    resolve_url_from_ddg,
    stable_hash,
    write_json,
    write_jsonl,
)


INDUSTRY_RULES: list[tuple[str, str, list[str]]] = [
    ("medical_equipment", "تجهیزات پزشکی و آزمایشگاهی", ["تجهیزات پزشکی", "آزمایشگاهی", "دندانپزشکی", "پزشکی"]),
    ("pharma", "دارویی", ["دارو", "دارویی", "داروسازی"]),
    ("food_fmcg", "غذا و کالاهای تندمصرف", ["غذایی", "مواد غذایی", "فروشگاه زنجیره", "فروش عمده", "پخش کالا", "نوشیدنی"]),
    ("printing_packaging_labeling", "چاپ، بسته‌بندی و لیبل", ["بسته بندی", "بسته‌بندی", "کارتن", "جعبه", "چاپ", "لیبل", "یونولیت"]),
    ("logistics_freight_customs", "حمل‌ونقل، فورواردری و ترخیص", ["ترخیص", "حمل و نقل", "فورواردر", "انبارداری", "باربری", "لجستیک"]),
    ("auto_parts", "قطعات خودرو", ["خودرو", "لوازم یدکی", "قطعات یدکی", "قطعات خودرو"]),
    ("epc_engineering_contractors", "EPC و پیمانکاری مهندسی", ["پیمانکار", "پیمانکاری", "مهندسی", "نفت و گاز", "پتروشیمی", "EPC"]),
    ("building_materials_mep", "مصالح ساختمانی و تاسیسات", ["مصالح", "ساختمان", "تاسیسات", "شیرآلات", "اتصالات", "فولاد", "آهن"]),
    ("industrial_maintenance_after_sales", "نگهداری صنعتی و خدمات پس از فروش", ["نگهداری", "تعمیر کارخانجات", "خدمات پس از فروش", "تعمیرات صنعتی", "تعمیر ماشین آلات"]),
    ("industrial_manufacturers", "تولیدکننده صنعتی", ["تولید", "کارخانه", "ماشین آلات", "ماشین‌آلات", "صنعتی", "آلیاژ"]),
    ("industrial_distributors_importers", "توزیع‌کننده و واردکننده صنعتی", ["واردات", "صادرات", "بازرگانی", "فروش ماشین آلات", "ابزار صنعتی"]),
]


def classify_industry(*values: str) -> tuple[str, str]:
    text = " ".join(value or "" for value in values).lower()
    for code, label, terms in INDUSTRY_RULES:
        if any(term.lower() in text for term in terms):
            return code, label
    return "other", "سایر"


def _address_fields(address: Any) -> tuple[str, str, str]:
    if isinstance(address, dict):
        street = clean_text(address.get("streetAddress"))
        locality = clean_text(address.get("addressLocality"))
        region = clean_text(address.get("addressRegion"))
        return street, locality, region
    text = clean_text(address)
    return text, "", ""


def _profile_item(obj: dict[str, Any], parent_url: str | None, source_url: str, category: str, page_title: str) -> dict[str, Any] | None:
    name = clean_text(obj.get("name"))
    address = obj.get("address")
    telephone = obj.get("telephone")
    if not name or not (address or telephone or obj.get("url")):
        return None
    street, locality, region = _address_fields(address)
    profile_url = canonical_url(obj.get("url") or parent_url, source_url)
    same_as = obj.get("sameAs")
    if isinstance(same_as, str):
        same_as = [same_as]
    if not isinstance(same_as, list):
        same_as = []
    phones = corporate_phones(" ".join(str(item) for item in (telephone if isinstance(telephone, list) else [telephone]) if item))
    industry, industry_fa = classify_industry(category, name, obj.get("description", ""))
    geo = obj.get("geo") if isinstance(obj.get("geo"), dict) else {}
    return {
        "raw_candidate_id": stable_hash(source_url, profile_url, name),
        "company_name_fa": name,
        "brand_name_fa": name,
        "company_name_en": name if re.search(r"[A-Za-z]", name) else None,
        "aliases": [],
        "website": None,
        "domain": None,
        "industry": industry,
        "industry_fa": industry_fa,
        "sub_industry": clean_text(category),
        "description": clean_text(obj.get("description"), 1200),
        "hq_address": street,
        "city": locality,
        "province": region,
        "tehran_area": street,
        "industrial_zone": next((term for term in ["شمس آباد", "عباس آباد", "چهاردانگه", "نصیرآباد", "پرند", "شهر قدس", "شاپور", "فجر", "صفادشت", "اسلامشهر", "ری", "حسن آباد"] if term in street), None),
        "phones_public": phones,
        "emails_public": [],
        "linkedin_company_url": None,
        "social_profiles": [canonical_url(item) for item in same_as if canonical_url(item)],
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
        "source_url": source_url,
        "source_title": page_title,
        "source_type": "directory",
        "source_quality": "directory",
        "source_published_at": None,
        "discovery_reason": f"Book-e Avval category: {category}",
        "evidence_class": "OBSERVED",
        "evidence_snippet": clean_text(obj.get("description") or name, 500),
        "profile_url": profile_url,
        "discovered_at": now_iso(),
    }


def parse_avval(body: str, source_url: str, category: str) -> list[dict[str, Any]]:
    title = extract_title(body)
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in json_ld_objects(body):
        for obj in _walk_item_businesses(root):
            item = _profile_item(obj["item"], obj.get("parent_url"), source_url, category, title)
            if not item:
                continue
            key = item.get("profile_url") or stable_hash(item.get("company_name_fa"), item.get("hq_address"))
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
    # Avval's first category page exposes JSON-LD, while subsequent /search
    # pages may expose the same public cards only as HTML attributes.
    for card in re.findall(r'<div\s+class="card\s+job-entity\b.*?(?=<div\s+class="card\s+job-entity\b|</main>)', body or "", re.I | re.S):
        title_match = re.search(r'data-map-marker-title="([^"]+)"', card, re.I)
        profile_match = re.search(r'data-map-marker-link="([^"]+)"', card, re.I)
        if not title_match or not profile_match:
            continue
        name = clean_text(title_match.group(1))
        profile_url = canonical_url(profile_match.group(1), source_url)
        if not name or not profile_url or profile_url in seen:
            continue
        phone_match = re.search(r'data-map-marker-phone=(?:"([^"]+)"|([^\s>]+))', card, re.I)
        location_match = re.search(r'data-map-marker-location="\[?([0-9.]+)\s*,\s*([0-9.]+)\]?"', card, re.I)
        address_match = re.search(r'data-print-adv="address"[^>]*>(.*?)</p>', card, re.I | re.S)
        description_match = re.search(r'<p[^>]+class="[^"]*(?:description|desc)[^"]*"[^>]*>(.*?)</p>', card, re.I | re.S)
        description = html_to_text(description_match.group(1), 1200) if description_match else ""
        street = html_to_text(address_match.group(1), 800) if address_match else ""
        industry, industry_fa = classify_industry(category, name, description)
        item = {
            "raw_candidate_id": stable_hash(source_url, profile_url, name),
            "company_name_fa": name,
            "brand_name_fa": name,
            "company_name_en": name if re.search(r"[A-Za-z]", name) else None,
            "aliases": [], "website": None, "domain": None,
            "industry": industry, "industry_fa": industry_fa, "sub_industry": clean_text(category),
            "description": description, "hq_address": street,
            "city": "تهران", "province": "استان تهران", "tehran_area": street,
            "industrial_zone": next((term for term in ["شمس آباد", "عباس آباد", "چهاردانگه", "نصیرآباد", "پرند", "صفادشت", "اسلامشهر", "ری", "حسن آباد"] if term in street), None),
            "phones_public": corporate_phones(phone_match.group(1) or phone_match.group(2)) if phone_match else corporate_phones(street),
            "emails_public": [], "linkedin_company_url": None, "social_profiles": [],
            "latitude": float(location_match.group(1)) if location_match else None,
            "longitude": float(location_match.group(2)) if location_match else None,
            "source_url": source_url, "source_title": extract_title(body), "source_type": "directory",
            "source_quality": "directory", "source_published_at": None,
            "discovery_reason": f"Book-e Avval category: {category}", "evidence_class": "OBSERVED",
            "evidence_snippet": clean_text(description or name, 500), "profile_url": profile_url, "discovered_at": now_iso(),
        }
        seen.add(profile_url)
        output.append(item)
    return output


def _walk_item_businesses(value: Any, parent_url: str | None = None):
    if isinstance(value, dict):
        if isinstance(value.get("item"), dict) and value["item"].get("name"):
            yield {"item": value["item"], "parent_url": value.get("url") or parent_url}
        elif value.get("name") and (value.get("address") or value.get("telephone")):
            yield {"item": value, "parent_url": parent_url}
        for key, child in value.items():
            if key not in {"item"}:
                yield from _walk_item_businesses(child, value.get("url") or parent_url)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_item_businesses(child, parent_url)


def next_page_url(body: str) -> str | None:
    match = re.search(r"<link[^>]+rel=[\"']next[\"'][^>]+href=[\"']([^\"']+)", body or "", re.I)
    if not match:
        match = re.search(r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]+rel=[\"']next[\"']", body or "", re.I)
    return canonical_url(match.group(1)) if match else None


def page_number_url(url: str, page: int) -> str:
    if "page=" in url:
        return re.sub(r"page=\d+", f"page={page}", url)
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}page={page}"


def fetch_avval_category(category: str, max_pages: int, proxy: str, limiter: RateLimiter) -> dict[str, Any]:
    city = quote("تهران", safe="")
    slug = quote(category, safe="")
    first_url = f"https://avval.ir/directory/{slug}/{city}"
    response = fetch_url(first_url, proxy=proxy, limiter=limiter)
    rows = parse_avval(response.get("body", ""), first_url, category) if response.get("body") else []
    errors = [] if response.get("status") else [{"url": first_url, "error": response.get("error")}]
    next_url = next_page_url(response.get("body", "")) if response.get("body") else None
    for page in range(2, max_pages + 1):
        if not next_url:
            break
        url = page_number_url(next_url, page)
        result = fetch_url(url, proxy=proxy, limiter=limiter)
        page_rows = parse_avval(result.get("body", ""), url, category) if result.get("body") else []
        if not page_rows:
            break
        rows.extend(page_rows)
        if result.get("status") is None:
            errors.append({"url": url, "error": result.get("error")})
            break
    return {"category": category, "rows": rows, "errors": errors, "pages": min(max_pages, page if 'page' in locals() else 1)}


def parse_ddg(body: str, source_url: str, query: str) -> list[dict[str, Any]]:
    links = extract_links(body, source_url)
    titles = [item for item in links if "result__a" in item.get("class", "")]
    snippets = [item for item in links if "result__snippet" in item.get("class", "")]
    rows: list[dict[str, Any]] = []
    for index, title_link in enumerate(titles):
        target = resolve_url_from_ddg(title_link.get("href"))
        if not target or not is_external_company_url(target, source_domains={"duckduckgo.com"}):
            continue
        title = clean_text(title_link.get("text"), 300)
        snippet = clean_text(snippets[index].get("text"), 800) if index < len(snippets) else ""
        industry, industry_fa = classify_industry(query, title, snippet)
        parsed = urlparse(target)
        rows.append({
            "raw_candidate_id": stable_hash(source_url, target, title),
            "company_name_fa": title,
            "brand_name_fa": title,
            "company_name_en": title if re.search(r"[A-Za-z]", title) else None,
            "aliases": [],
            "website": target,
            "domain": domain_of(target),
            "industry": industry,
            "industry_fa": industry_fa,
            "sub_industry": query,
            "description": snippet,
            "hq_address": "",
            "city": "تهران",
            "province": "استان تهران",
            "tehran_area": "",
            "industrial_zone": next((term for term in ["شمس آباد", "عباس آباد", "چهاردانگه", "نصیرآباد", "پرند", "صفادشت", "اسلامشهر", "ری", "حسن آباد"] if term in title + snippet), None),
            "phones_public": corporate_phones(snippet),
            "emails_public": [],
            "linkedin_company_url": target if "linkedin.com/company" in target else None,
            "social_profiles": [target] if any(host in parsed.netloc for host in ["instagram.", "linkedin.", "t.me", "telegram."]) else [],
            "latitude": None,
            "longitude": None,
            "source_url": source_url,
            "source_title": title,
            "source_type": "search",
            "source_quality": "search_index",
            "source_published_at": None,
            "discovery_reason": f"DuckDuckGo Persian query: {query}",
            "evidence_class": "OBSERVED",
            "evidence_snippet": snippet,
            "profile_url": None,
            "discovered_at": now_iso(),
        })
    return rows


def parse_official_page(body: str, source_url: str) -> list[dict[str, Any]]:
    title = extract_title(body)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for link in extract_links(body, source_url):
        target = link.get("href")
        text = clean_text(link.get("text"), 250)
        if not text or len(text) < 3 or not target or not is_external_company_url(target, source_domains={"tccim.ir", "iccima.ir", "isipo.ir", "tehran.isipo.ir", "iranfair.com"}):
            continue
        if len(text) > 160 or text.lower() in {"home", "contact", "about", "صفحه اصلی", "تماس با ما"}:
            continue
        if not any(token in (link.get("class", "") + " " + target).lower() for token in ["member", "company", "exhibit", "profile", "supplier", "vendor", "شرکت"]):
            continue
        key = target
        if key in seen:
            continue
        seen.add(key)
        industry, industry_fa = classify_industry(text, source_url)
        rows.append({
            "raw_candidate_id": stable_hash(source_url, target, text),
            "company_name_fa": text,
            "brand_name_fa": text,
            "company_name_en": text if re.search(r"[A-Za-z]", text) else None,
            "aliases": [],
            "website": target,
            "domain": domain_of(target),
            "industry": industry,
            "industry_fa": industry_fa,
            "sub_industry": title,
            "description": "",
            "hq_address": "",
            "city": "تهران",
            "province": "استان تهران",
            "tehran_area": "",
            "industrial_zone": None,
            "phones_public": [],
            "emails_public": [],
            "linkedin_company_url": target if "linkedin.com/company" in target else None,
            "social_profiles": [],
            "latitude": None,
            "longitude": None,
            "source_url": source_url,
            "source_title": title,
            "source_type": "official_reference",
            "source_quality": "official",
            "source_published_at": None,
            "discovery_reason": "Public link from official/association source",
            "evidence_class": "OBSERVED",
            "evidence_snippet": text,
            "profile_url": None,
            "discovered_at": now_iso(),
        })
    return rows


def run_preflight(proxy: str) -> bool:
    result = subprocess.run([sys.executable, "-m", "src.utilities.network_preflight", "--proxy", proxy], capture_output=True, text=True, check=False)
    print(result.stdout[-5000:])
    if result.returncode != 0:
        print("Discovery stopped: direct-proxy preflight failed.", file=sys.stderr)
        if result.stderr:
            print(result.stderr[-2000:], file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover Tehran-area B2B candidates from public sources")
    parser.add_argument("--config", default="config/sources.yaml")
    parser.add_argument("--proxy", default=None)
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--max-workers", type=int, default=None)
    args = parser.parse_args()
    config = parse_simple_yaml(args.config)
    proxy = args.proxy or config.get("direct_proxy") or DEFAULT_PROXY
    if not args.skip_preflight and not run_preflight(proxy):
        return 2
    interval = float(config.get("rate_limit_seconds") or 0.35)
    workers = int(args.max_workers or config.get("max_workers") or 6)
    pages = int((config.get("discovery") or [{}])[0].get("pages") or 12)
    categories = config.get("avval_categories") or []
    queries = config.get("queries") or []
    limiter = RateLimiter(interval)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    source_runs: list[dict[str, Any]] = []
    lock = threading.Lock()

    print(f"Starting Avval discovery: categories={len(categories)} pages={pages} workers={workers}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch_avval_category, category, pages, proxy, limiter) for category in categories]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            with lock:
                rows.extend(result["rows"])
                errors.extend(result["errors"])
                source_runs.append({"source": "book_e_avval", "category": result["category"], "rows": len(result["rows"]), "pages": result["pages"]})
            print(f"Avval {result['category']}: {len(result['rows'])} rows")

    ddg_urls = []
    pages_cfg = next((item for item in (config.get("discovery") or []) if item.get("name") == "duckduckgo_html"), {})
    ddg_pages = int(pages_cfg.get("pages") or 3)
    for query in queries:
        for page in range(ddg_pages):
            params = {"q": query, "s": page * 30, "kl": "ir-fa"}
            ddg_urls.append((query, f"https://html.duckduckgo.com/html/?{urlencode(params)}"))
    print(f"Starting DuckDuckGo discovery: pages={len(ddg_urls)}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(fetch_url, url, proxy=proxy, limiter=limiter): (query, url) for query, url in ddg_urls}
        for future in concurrent.futures.as_completed(future_map):
            query, url = future_map[future]
            result = future.result()
            parsed = parse_ddg(result.get("body", ""), url, query) if result.get("body") else []
            rows.extend(parsed)
            source_runs.append({"source": "duckduckgo_html", "query": query, "url": url, "rows": len(parsed), "status": result.get("status"), "elapsed_ms": result.get("elapsed_ms")})
            if result.get("status") is None:
                errors.append({"url": url, "error": result.get("error")})

    official_cfg = next((item for item in (config.get("discovery") or []) if item.get("name") == "official_and_associations"), {})
    official_urls = official_cfg.get("urls") or []
    print(f"Starting official/association discovery: pages={len(official_urls)}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, 4)) as pool:
        future_map = {pool.submit(fetch_url, url, proxy=proxy, limiter=limiter): url for url in official_urls}
        for future in concurrent.futures.as_completed(future_map):
            url = future_map[future]
            result = future.result()
            parsed = parse_official_page(result.get("body", ""), url) if result.get("body") else []
            rows.extend(parsed)
            source_runs.append({"source": "official_and_associations", "url": url, "rows": len(parsed), "status": result.get("status"), "elapsed_ms": result.get("elapsed_ms")})
            if result.get("status") is None:
                errors.append({"url": url, "error": result.get("error")})

    output = path_for("data", "raw", "candidates.jsonl")
    write_jsonl(output, rows)
    write_jsonl(path_for("data", "raw", "discovery_sources.jsonl"), source_runs)
    report = {
        "completed_at": now_iso(),
        "raw_candidate_count": len(rows),
        "source_unique_candidate_count": len({row.get("raw_candidate_id") for row in rows}),
        "source_counts": dict(Counter(row.get("source_type") for row in rows)),
        "industry_counts": dict(Counter(row.get("industry") for row in rows)),
        "avval_categories": len(categories),
        "avval_pages_limit": pages,
        "search_queries": len(queries),
        "errors": errors,
        "source_runs": source_runs,
        "proxy": proxy,
    }
    write_json(path_for("logs", f"discovery-{now_iso().replace(':', '').replace('-', '')}.json"), report)
    print(json.dumps({k: report[k] for k in ["raw_candidate_count", "source_unique_candidate_count", "source_counts", "industry_counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
