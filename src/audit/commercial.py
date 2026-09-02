"""Audit existing Tier A/B records without expanding the discovery universe.

This module deliberately keeps discovery and commercial audit separate. It reads
the canonical dataset, selects only the records that were already A/B, fetches
targeted public pages through the verified direct proxy, and writes the revised
record in-place with an audit trail.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from src.discovery.run import parse_ddg
from src.enrichment.enrich import analyze_website, parse_profile
from src.utilities.common import (
    DEFAULT_PROXY,
    RateLimiter,
    canonical_url,
    clean_text,
    corporate_phones,
    domain_of,
    extract_emails,
    filter_public_emails,
    extract_links,
    fetch_url,
    html_to_text,
    normalize_persian,
    now_iso,
    path_for,
    read_jsonl,
    stable_hash,
    write_json,
    write_jsonl,
)


AUDIT_VERSION = "2026.09.commercial-audit-v1"
SEARCH_DOMAINS = {"html.duckduckgo.com", "duckduckgo.com", "www.bing.com", "bing.com", "google.com"}
NON_CORPORATE_DOMAINS = {
    "avval.ir", "vic.ir", "google.com", "googleusercontent.com", "bing.com", "duckduckgo.com",
    "linkedin.com", "instagram.com", "facebook.com", "youtube.com", "telegram.me", "t.me",
    "x.com", "twitter.com", "rubika.ir", "aparat.com", "balad.ir", "neshan.org",
    "api.whatsapp.com", "wa.me", "enamad.ir", "trustseal.enamad.ir",
}
DIRECTORY_DOMAINS = {
    "parscenter.com", "sanatmap.com", "iranindustry.com", "irantamin.com",
    "basalam.com", "emalls.ir", "torob.com", "digikala.com",
}
FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "proton.me", "protonmail.com"}

SIGNAL_LABELS = {
    "rfq_or_quote": "public quotation or RFQ language",
    "catalog_or_products": "public product/catalog surface",
    "order_or_contact_form": "public order or contact intake",
    "branches_or_dealers": "branches, representatives or dealer network",
    "factory_or_warehouse": "factory, warehouse or production facility",
    "service_after_sales": "after-sales, repair or service operation",
    "projects_or_clients": "public projects, clients or partners",
    "certifications": "certification, license or standards evidence",
    "tender_or_contract": "tender, contract or procurement language",
    "software_or_erp": "named ERP/CRM/software signal",
    "internal_tech_hiring": "internal software/data/AI hiring signal",
    "admin_or_operations_hiring": "operational hiring signal",
    "expansion_or_activity": "expansion, export, founding or current activity signal",
}

WORKFLOW_SPECS = {
    "rfq_quotation": {
        "workflow_name": "RFQ intake, product matching and draft quotation",
        "solution": "A Persian/English RFQ intake and catalog/SKU matcher that prepares an explainable draft quotation for human approval.",
        "users": "Sales operations, product specialists and commercial management",
        "data": "Product master, specifications, price lists, stock snapshots, historical RFQs and approval rules",
        "integrations": "ERP/accounting exports or API, CRM, email/forms and approved document intake",
        "kpis": ["quote turnaround time", "RFQs handled per salesperson", "correction rate", "follow-up completion"],
        "questions": [
            "در ماه چند درخواست قیمت وارد می‌شود و از چه کانال‌هایی؟",
            "امروز فروشنده برای تطبیق مشخصات، قیمت و موجودی به چه منابعی رجوع می‌کند؟",
            "کدام قواعد قیمت‌گذاری و حاشیه سود باید کاملاً قطعی و انسانی باقی بماند؟",
            "خروجی مطلوب پیش‌فاکتور است یا فقط پیشنهاد محصول و پاسخ فنی؟",
            "داده مرجع محصول و قیمت در کدام سامانه یا فایل نگهداری می‌شود؟",
        ],
    },
    "shipment_document_automation": {
        "workflow_name": "Shipment-document intake and exception tracking",
        "solution": "A document intake layer that extracts shipment and customs fields, checks missing items and routes exceptions to the responsible operator for approval.",
        "users": "Operations, customs/compliance and customer-service teams",
        "data": "Bills of lading, invoices, packing lists, customs documents, shipment milestones and customer instructions",
        "integrations": "Shared folders, email intake, approved TMS/ERP exports and management reporting",
        "kpis": ["document completeness", "exception closure time", "manual re-keying", "shipment-status response time"],
        "questions": [
            "کدام اسناد حمل و ترخیص بیشترین حجم ورود و کنترل را دارند؟",
            "چطور نقص مدارک یا تأخیر هر پرونده به مسئول آن ارجاع می‌شود؟",
            "کدام داده‌ها در ایمیل، اکسل یا سامانه‌های مختلف تکراراً وارد می‌شوند؟",
            "چه نقاطی نیازمند تأیید کارشناس گمرک یا مدیر عملیات هستند؟",
            "برای شروع پایلوت، کدام مسیر یا نوع محموله کم‌ریسک‌تر است؟",
        ],
    },
    "service_ticket_maintenance": {
        "workflow_name": "Service-ticket intake and maintenance knowledge",
        "solution": "A controlled service workspace that structures incoming requests, retrieves approved maintenance knowledge and prepares a human-reviewed service report.",
        "users": "Service director, field technicians, maintenance and customer-support teams",
        "data": "Service requests, equipment/serial records, manuals, prior interventions, parts and service reports",
        "integrations": "CRM/ERP exports, service forms, shared documents and approved messaging or email intake",
        "kpis": ["first-response time", "repeat visits", "report completion time", "parts lookup time"],
        "questions": [
            "درخواست خدمت چگونه ثبت، اولویت‌بندی و به تکنسین ارجاع می‌شود؟",
            "سوابق تجهیز، شماره سریال و تعمیرات قبلی در چه منبعی است؟",
            "تکنسین برای یافتن راهنمای معتبر یا قطعه مناسب چه مسیری دارد؟",
            "کدام گزارش‌های سرویس باید امضای انسانی یا تأیید مشتری داشته باشند؟",
            "مهم‌ترین شاخص سرویس برای مدیریت چیست؟",
        ],
    },
    "boq_specification_matching": {
        "workflow_name": "BOQ/specification matching and technical submittal support",
        "solution": "A document-grounded matcher that structures BOQ lines, retrieves technical evidence and prepares a versioned submittal or quotation pack for approval.",
        "users": "Technical office, project sales, procurement and commercial management",
        "data": "BOQs, drawings/specifications, product catalogs, price lists, alternatives and prior submittals",
        "integrations": "Document repository, CRM/ERP exports, quotation workflow and approval records",
        "kpis": ["lines matched per hour", "submittal turnaround", "revision errors", "follow-up coverage"],
        "questions": [
            "BOQ و مشخصات فنی معمولاً با چه قالبی وارد می‌شوند؟",
            "تطبیق گزینه‌های مجاز و جایگزین توسط چه نقشی تأیید می‌شود؟",
            "کاتالوگ و گواهی فنی مرجع در کجا نگهداری می‌شود؟",
            "کدام بخش از سابمیتال باید نسخه‌بندی و قابل ردیابی باشد؟",
            "یک پروژه نمونه برای اندازه‌گیری زمان و خطا کدام است؟",
        ],
    },
    "order_inventory_exceptions": {
        "workflow_name": "Order intake and inventory-exception reporting",
        "solution": "A structured order/return intake and exception dashboard that consolidates approved sales, inventory and route records without replacing the distribution core.",
        "users": "Sales operations, distribution, supply chain and branch management",
        "data": "Order lines, returns, inventory snapshots, customers, promotions, routes and receivables",
        "integrations": "Distribution ERP, warehouse/branch reports and approved email or message exports",
        "kpis": ["order-entry time", "stock-out exceptions", "return/expiry value", "manual reporting hours"],
        "questions": [
            "سفارش‌ها از چه کانال‌هایی وارد می‌شوند و کجا دوباره‌کاری می‌شوند؟",
            "موجودی و قیمت مرجع برای تیم فروش کدام است؟",
            "استثناهای کسری، مرجوعی یا تاریخ انقضا چطور گزارش می‌شوند؟",
            "گزارش روزانه یا هفتگی مدیریت چه فیلدهایی دارد؟",
            "آیا انبار، شعب یا نمایندگان خروجی استاندارد قابل اتصال دارند؟",
        ],
    },
    "production_quality_reporting": {
        "workflow_name": "Production, quality and downtime reporting",
        "solution": "A controlled reporting layer that normalizes shift, quality and downtime documents, surfaces exceptions and retrieves approved SOP or maintenance evidence for human review.",
        "users": "Plant management, production planning, QA/QC and maintenance teams",
        "data": "Shift reports, production orders, QC records, downtime logs, SOPs and ERP/Excel exports",
        "integrations": "ERP/MES exports, shared folders, forms and management reporting",
        "kpis": ["report preparation hours", "exception detection latency", "rework/scrap cases", "document retrieval time"],
        "questions": [
            "گزارش شیفت، تولید و توقفات امروز در چه قالب‌هایی ثبت می‌شود؟",
            "کدام شاخص کیفیت یا تولید نیازمند جمع‌بندی تکراری است؟",
            "SOP و سوابق تعمیرات معتبر در کجا نسخه‌بندی می‌شوند؟",
            "چه خروجی‌هایی باید قبل از انتشار توسط مدیر یا QA تأیید شوند؟",
            "برای پایلوت، کدام خط یا محصول داده منظم‌تری دارد؟",
        ],
    },
    "tender_document_assistant": {
        "workflow_name": "Tender and technical-document response assistant",
        "solution": "A permissioned document assistant that retrieves approved technical, commercial and compliance evidence and assembles a traceable draft response for human review.",
        "users": "Tender, contracts, technical and commercial teams",
        "data": "Tender files, technical catalogs, certificates, previous submissions, contracts and approved answers",
        "integrations": "Document management, shared folders, CRM/ERP exports and review workflow",
        "kpis": ["response preparation time", "missing-document exceptions", "answer reuse", "review cycles"],
        "questions": [
            "مناقصه یا استعلام معمولاً در چه قالبی وارد می‌شود؟",
            "اسناد فنی و گواهی‌های مورد تأیید در کجا نگهداری می‌شوند؟",
            "کدام پاسخ‌ها یا مدارک قابلیت استفاده مجدد دارند؟",
            "چه کسی پاسخ نهایی و هر ادعای فنی را تأیید می‌کند؟",
            "محدودیت دسترسی و نگهداری اسناد حساس چیست؟",
        ],
    },
    "job_brief_estimate": {
        "workflow_name": "Job-brief extraction and estimating support",
        "solution": "A structured job-brief extractor and similar-job retrieval tool that supports explainable estimating and tracks artwork/specification approvals.",
        "users": "Sales, estimating, prepress and production planning",
        "data": "Customer briefs, artwork/specifications, prior jobs, material/machine rules and capacity",
        "integrations": "File intake, estimating spreadsheets, production planning and approval records",
        "kpis": ["estimate turnaround", "revision cycles", "estimator throughput", "jobs delayed by missing specifications"],
        "questions": [
            "چه ورودی‌هایی در بریف مشتری بیشتر ناقص یا اصلاح‌شونده هستند؟",
            "قواعد هزینه و ظرفیت چگونه تعیین می‌شوند و کدام بخش قطعی است؟",
            "نسخه نهایی فایل و مشخصات چگونه به تولید تحویل می‌شود؟",
            "چه تعداد استعلام یا سفارش سفارشی در ماه بررسی می‌شود؟",
            "یک نمونه واقعی برای مقایسه زمان برآورد و اصلاحات چیست؟",
        ],
    },
    "parts_catalog_matching": {
        "workflow_name": "Parts/catalog matching for sales confirmation",
        "solution": "A catalog and compatibility assistant that maps customer descriptions or part numbers to candidate SKUs, stock and price for salesperson confirmation.",
        "users": "Commercial, warehouse and customer-service teams",
        "data": "SKU/part master, OEM cross-references, compatibility notes, stock, price and return history",
        "integrations": "ERP/WMS exports, catalog files and CRM/order workflow",
        "kpis": ["part-search time", "wrong-part corrections/returns", "quote turnaround", "orders per salesperson"],
        "questions": [
            "پیدا کردن کدام شماره یا شرح قطعه برای فروش دشوارتر است؟",
            "مرجع قطعی موجودی و قیمت کدام سامانه یا فایل است؟",
            "خطای تطبیق قطعه چطور شناسایی و اصلاح می‌شود؟",
            "آیا کاتالوگ و cross-reference رسمی قابل دسترسی است؟",
            "تأیید نهایی پیشنهاد قطعه با چه نقشی است؟",
        ],
    },
}

OWNER_BY_WORKFLOW = {
    "rfq_quotation": "Commercial Director / Sales Operations Manager",
    "shipment_document_automation": "Operations Director / Customs Manager",
    "service_ticket_maintenance": "Service Director / Maintenance Manager",
    "boq_specification_matching": "Technical Office / Project Sales Director",
    "order_inventory_exceptions": "Distribution or Sales Operations Director",
    "production_quality_reporting": "Plant Manager / Operations Director",
    "tender_document_assistant": "Tender / Contracts Director",
    "job_brief_estimate": "Estimating or Production Director",
    "parts_catalog_matching": "Commercial or Operations Director",
}


def _text(*values: Any) -> str:
    return normalize_persian(" ".join(str(value) for value in values if value))


def _has(text: str, terms: list[str]) -> bool:
    return any(normalize_persian(term) in text for term in terms)


def _meaningful_name_tokens(name: str) -> list[str]:
    stop = {"شرکت", "گروه", "موسسه", "موسسه", "دفتر", "مرکزی", "شعبه", "کارخانه", "فروشگاه", "تهران", "نمایندگی"}
    return [token for token in re.findall(r"[\w\u0600-\u06ff]{3,}", normalize_persian(name)) if token not in stop]


def source_family(url: str | None, *, source_type: str | None = None) -> str | None:
    domain = domain_of(url)
    if not domain:
        return None
    if domain in {"avval.ir", "www.avval.ir"} or domain.endswith(".avval.ir"):
        return "book_e_avval"
    if domain == "vic.ir" or domain.endswith(".vic.ir"):
        return "industrial_estate_registry"
    if domain in SEARCH_DOMAINS or domain.endswith(".duckduckgo.com"):
        return "search_engine"
    if domain in {"linkedin.com", "www.linkedin.com"} or domain.endswith(".linkedin.com"):
        return "linkedin_public"
    if domain in {"jobinja.ir", "irantalent.com", "jobvision.ir", "jobinja.com"} or domain.endswith((".jobinja.ir", ".irantalent.com", ".jobvision.ir")):
        return "job_portal"
    if domain in {"balad.ir", "neshan.org"} or domain.endswith((".balad.ir", ".neshan.org")):
        return "map_listing"
    if domain in {"codal.ir", "rrk.ir", "ilenc.ssaa.ir", "sabteagahi.ir"} or domain.endswith((".codal.ir", ".rrk.ir")):
        return "official_registry"
    if domain in {"tccim.ir", "service.tccim.ir", "iccima.ir", "tehran.isipo.ir", "isipo.ir", "iranfair.com"} or domain.endswith((".tccim.ir", ".iccima.ir", ".isipo.ir", ".iranfair.com")):
        return "association_or_exhibition"
    if domain in {"instagram.com", "facebook.com", "youtube.com", "telegram.me", "t.me", "rubika.ir", "aparat.com", "x.com", "twitter.com"} or domain.endswith((".instagram.com", ".facebook.com", ".youtube.com")):
        return "social_public"
    if domain in DIRECTORY_DOMAINS or any(domain.endswith("." + item) for item in DIRECTORY_DOMAINS):
        return f"directory:{domain}"
    if source_type in {"directory", "targeted_search_result"}:
        return f"directory:{domain}"
    return f"company_website:{domain}"


def valid_public_url(url: str | None) -> bool:
    domain = domain_of(url)
    return bool(url and domain and domain not in NON_CORPORATE_DOMAINS and not any(domain.endswith("." + item) for item in NON_CORPORATE_DOMAINS))


def cache_path(url: str) -> Path:
    return path_for("data", "raw", "http-cache", "commercial-audit", f"{stable_hash(url, length=24)}.json")


def fetch_cached(url: str, *, proxy: str, limiter: RateLimiter, timeout: float, max_bytes: int) -> dict[str, Any]:
    path = cache_path(url)
    if path.exists():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
            cached["cached"] = True
            return cached
        except Exception:
            pass
    response = fetch_url(url, proxy=proxy, limiter=limiter, timeout=timeout, max_bytes=max_bytes)
    response["cached"] = False
    write_json(path, response)
    return response


def preflight(proxy: str) -> bool:
    result = subprocess.run([sys.executable, "-m", "src.utilities.network_preflight", "--proxy", proxy], capture_output=True, text=True, check=False)
    print(result.stdout[-3000:])
    return result.returncode == 0


def search_url(query: str) -> str:
    return "https://html.duckduckgo.com/html/?" + urlencode({"q": query, "kl": "ir-fa"})


def query_variants(company: dict[str, Any]) -> list[str]:
    name = clean_text(company.get("company_name_fa"), 180)
    values = [
        f'"{name}" تهران شرکت',
        f'"{name}" (کارخانه OR انبار OR نمایندگی OR پروژه OR صادرات)',
        f'"{name}" (استخدام OR مدیرعامل OR مدیر فروش OR مدیر عملیات)',
    ] if name else []
    english = company.get("company_name_en") or ""
    if not english:
        english = " ".join(re.findall(r"[A-Za-z][A-Za-z0-9&. -]{2,}", " ".join(str(x or "") for x in [company.get("brand_name_fa"), company.get("website"), company.get("description_observed")]))).strip()
    if english and re.search(r"[A-Za-z]{3,}", english):
        values.append(f'"{clean_text(english, 120)}" Tehran Iran company')
    return list(dict.fromkeys(values))[:4]


def relevant_search_result(company: dict[str, Any], result: dict[str, Any]) -> bool:
    name = " ".join(_meaningful_name_tokens(company.get("company_name_fa", "")))
    title = _text(result.get("company_name_fa"), result.get("source_title"), result.get("description"))
    tokens = _meaningful_name_tokens(name)
    if not tokens:
        return False
    return sum(1 for token in tokens if token in title) >= max(1, min(2, len(tokens)))


def compact_page(response: dict[str, Any], requested_url: str, kind: str, query: str | None = None) -> dict[str, Any]:
    body = response.get("body") or ""
    html = "text/html" in str(response.get("content_type", "")).lower() or "<html" in body[:1000].lower()
    analyzed = analyze_website(response, requested_url) if html and body else {
        "url": requested_url, "status": response.get("status"), "final_url": response.get("final_url"),
        "title": "", "content_type": response.get("content_type"), "elapsed_ms": response.get("elapsed_ms"),
        "text_excerpt": "", "signals": {}, "evidence": [], "relevant_links": [], "pdf_links": [],
        "phones": [], "emails": [], "error": response.get("error"),
    }
    text_excerpt = clean_text(analyzed.get("text_excerpt"), 5000)
    analyzed["signals"] = derive_page_signals(analyzed)
    return {
        "requested_url": requested_url,
        "final_url": analyzed.get("final_url") or response.get("final_url"),
        "status": analyzed.get("status") or response.get("status"),
        "title": clean_text(analyzed.get("title"), 300),
        "content_type": analyzed.get("content_type") or response.get("content_type"),
        "elapsed_ms": analyzed.get("elapsed_ms") or response.get("elapsed_ms"),
        "text_excerpt": text_excerpt,
        "signals": analyzed.get("signals") or {},
        "relevant_links": analyzed.get("relevant_links") or [],
        "pdf_links": analyzed.get("pdf_links") or [],
        "phones": analyzed.get("phones") or [],
        "emails": [email for email in (analyzed.get("emails") or []) if email.rsplit("@", 1)[-1].lower() not in FREE_EMAIL_DOMAINS],
        "error": analyzed.get("error") or response.get("error"),
        "kind": kind,
        "query": query,
        "source_family": source_family(analyzed.get("final_url") or response.get("final_url") or requested_url, source_type=kind),
        "captured_at": now_iso(),
}


def derive_page_signals(page: dict[str, Any]) -> dict[str, bool]:
    """Recompute signals with narrower terms than the broad site analyzer.

    The generic analyzer is useful for navigation discovery, but a commercial
    audit must not treat a footer/category link as proof of a factory, tender or
    software team.
    """
    title = _text(page.get("title"))
    body = _text(page.get("text_excerpt"))
    focused = _text(title, body)
    exact = {
        "rfq_or_quote": _has(focused, ["استعلام قیمت", "درخواست قیمت", "پیش فاکتور", "استعلام بها", "درخواست پیش فاکتور", "request a quote", "quote request"]),
        "catalog_or_products": _has(focused, ["کاتالوگ", "محصولات", "محصول", "catalog", "products"]),
        "order_or_contact_form": _has(focused, ["ثبت سفارش", "سفارش آنلاین", "فرم سفارش", "online order", "order form"]),
        "branches_or_dealers": _has(focused, ["شعبه", "شعب", "نمایندگان", "نمایندگی", "دفاتر", "dealer", "branches"]),
        "factory_or_warehouse": _has(focused, ["کارخانه", "خط تولید", "تاسیسات تولید", "انبار مرکزی", "انبار اختصاصی", "production facility", "manufacturing plant", "warehouse facility"]),
        "service_after_sales": _has(focused, ["خدمات پس از فروش", "تعمیرات", "پشتیبانی فنی", "گارانتی", "service", "warranty"]),
        "projects_or_clients": _has(focused, ["پروژه ها", "پروژه‌ها", "مشتریان ما", "نمونه کار", "case study", "our clients", "our projects"]),
        "certifications": _has(focused, ["گواهینامه", "استاندارد", "مجوز", "certificate", "iso", "gmp"]),
        "tender_or_contract": _has(focused, ["مناقصه", "مزایده", "قرارداد", "tender", "contract"]),
        "software_or_erp": _has(focused, ["erp", "crm", "راهکاران", "همکاران سیستم", "سپیدار", "نرم افزار", "نرم‌افزار"]),
        "internal_tech_hiring": _has(focused, ["هوش مصنوعی", "یادگیری ماشین", "دانشمند داده", "برنامه نویس", "برنامه‌نویس", "توسعه دهنده", "پایتون", "backend", "frontend", "devops", "mlops"]),
        "admin_or_operations_hiring": _has(focused, ["کارشناس فروش", "کارشناس بازرگانی", "کارشناس انبار", "کارشناس برنامه ریزی", "کارشناس برنامه‌ریزی", "حسابدار", "اپراتور"]),
        "expansion_or_activity": _has(focused, ["تاسیس", "تأسیس", "سال سابقه", "سال فعالیت", "افتتاح", "توسعه", "صادرات", "سراسر کشور", "founded", "export"]),
    }
    return exact


SIGNAL_TERMS = {
    "rfq_or_quote": ["استعلام قیمت", "درخواست قیمت", "پیش فاکتور", "استعلام بها", "درخواست پیش فاکتور", "request a quote", "quote request"],
    "catalog_or_products": ["کاتالوگ", "محصولات", "محصول", "catalog", "products"],
    "order_or_contact_form": ["ثبت سفارش", "سفارش آنلاین", "فرم سفارش", "online order", "order form"],
    "branches_or_dealers": ["شعبه", "شعب", "نمایندگان", "نمایندگی", "دفاتر", "dealer", "branches"],
    "factory_or_warehouse": ["کارخانه", "خط تولید", "تاسیسات تولید", "انبار مرکزی", "انبار اختصاصی", "production facility", "manufacturing plant", "warehouse facility"],
    "service_after_sales": ["خدمات پس از فروش", "تعمیرات", "پشتیبانی فنی", "گارانتی", "service", "warranty"],
    "projects_or_clients": ["پروژه ها", "پروژه‌ها", "مشتریان ما", "نمونه کار", "case study", "our clients", "our projects"],
    "certifications": ["گواهینامه", "استاندارد", "مجوز", "certificate", "iso", "gmp"],
    "tender_or_contract": ["مناقصه", "مزایده", "قرارداد", "tender", "contract"],
}


def signal_snippet(page: dict[str, Any], signal: str) -> str:
    text = clean_text(page.get("text_excerpt"), 5000)
    lowered = text.lower()
    for term in SIGNAL_TERMS.get(signal, []):
        index = lowered.find(term.lower())
        if index >= 0:
            return text[max(0, index - 150): index + 420]
    return text[:650]


def page_matches_company(company: dict[str, Any], page: dict[str, Any]) -> bool:
    if not page.get("status") or not page.get("text_excerpt"):
        return False
    body = _text(page.get("title"), page.get("text_excerpt"))
    if _has(body, ["suspendedpage", "domain has expired", "this site can’t be reached", "صفحه مورد نظر یافت نشد", "سایت در دسترس نیست"]):
        return False
    name_tokens = _meaningful_name_tokens(company.get("company_name_fa", ""))
    if len(name_tokens) <= 1:
        return True
    return sum(1 for token in name_tokens if token in body) >= 1


def source_record(company_id: str, page: dict[str, Any], *, source_url: str | None = None, snippet: str | None = None) -> dict[str, Any]:
    url = source_url or page.get("final_url") or page.get("requested_url")
    return {
        "source_id": "src-" + stable_hash(company_id, url, page.get("title"), "commercial_audit"),
        "company_id": company_id,
        "source_url": url,
        "source_title": page.get("title") or page.get("kind"),
        "source_type": "commercial_audit",
        "source_quality": "public_page" if page.get("kind") in {"company_homepage", "company_page", "directory_profile"} else "search_index",
        "source_family": page.get("source_family") or source_family(url, source_type=page.get("kind")),
        "discovery_reason": "Targeted commercial audit of an existing Tier A/B company",
        "evidence_class": "OBSERVED",
        "evidence_snippet": clean_text(snippet or page.get("text_excerpt"), 700),
        "captured_at": page.get("captured_at") or now_iso(),
        "audit_round": AUDIT_VERSION,
    }


def evidence_item(company_id: str, claim: str, url: str, title: str, snippet: str, confidence: float, *, signal: str | None = None, evidence_type: str = "OBSERVED", family: str | None = None) -> dict[str, Any]:
    return {
        "evidence_id": "ev-" + stable_hash(company_id, url, claim, AUDIT_VERSION),
        "company_id": company_id,
        "claim": claim,
        "evidence_type": evidence_type,
        "source_url": url,
        "source_title": title,
        "captured_at": now_iso(),
        "confidence": round(max(0.0, min(1.0, confidence)), 2),
        "source_quality": "public_page",
        "quote_or_snippet": clean_text(snippet, 800),
        "source_family": family or source_family(url),
        "audit_round": AUDIT_VERSION,
        **({"signal": signal} if signal else {}),
    }


def save_page_text(company_id: str, page: dict[str, Any]) -> str | None:
    if not page.get("text_excerpt") or not page.get("status"):
        return None
    directory = path_for("evidence", "companies", company_id, "pages")
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"audit-{stable_hash(page.get('final_url') or page.get('requested_url'), AUDIT_VERSION)}.txt"
    path = directory / filename
    header = [
        "Commercial audit public-page capture", f"Company ID: {company_id}", f"URL: {page.get('final_url') or page.get('requested_url')}",
        f"Title: {page.get('title') or 'UNKNOWN'}", f"Source family: {page.get('source_family') or 'UNKNOWN'}", f"Captured at: {page.get('captured_at') or now_iso()}", "",
    ]
    path.write_text("\n".join(header) + page.get("text_excerpt", "")[:5000] + "\n", encoding="utf-8")
    return str(Path("companies") / company_id / "pages" / filename)


def existing_families(company: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for item in list(company.get("source_records") or []) + list(company.get("evidence") or []):
        url = item.get("source_url")
        family = item.get("source_family") or source_family(url, source_type=item.get("source_type"))
        if family:
            values.add(family)
    return values


def independent_families(company: dict[str, Any]) -> set[str]:
    return {family for family in existing_families(company) if family != "search_engine"}


def signal_union(company: dict[str, Any], pages: list[dict[str, Any]]) -> dict[str, bool]:
    signals = {key: False for key in SIGNAL_LABELS}
    for page in pages:
        if not str(page.get("source_family") or "").startswith("company_website:"):
            continue
        for key, value in (page.get("signals") or {}).items():
            signals[key] = signals.get(key, False) or bool(value)
    return signals


def all_audit_text(company: dict[str, Any], pages: list[dict[str, Any]]) -> str:
    parts = [company.get("company_name_fa"), company.get("brand_name_fa"), company.get("description_observed")]
    # Directory category labels are discovery evidence, not a company
    # description. Only retain directory snippets here when the canonical
    # record itself has no better public description.
    if company.get("description_observed"):
        parts.extend(item.get("quote_or_snippet") for item in company.get("evidence", []) if item.get("source_quality") in {"company_site", "public_page"} and not item.get("excluded_from_qualification"))
    else:
        parts.extend(item.get("evidence_snippet") for item in company.get("source_records", []) if item.get("source_family") not in {"book_e_avval", "industrial_estate_registry"})
    site = company.get("website_enrichment") or {}
    if site.get("text_excerpt") and not site.get("qualification_excluded"):
        parts.extend([site.get("title"), site.get("text_excerpt")])
    for page in pages:
        if str(page.get("source_family") or "").startswith("company_website:"):
            parts.extend([page.get("title"), page.get("text_excerpt")])
    return _text(*parts)


def classify_company(company: dict[str, Any], text: str, signals: dict[str, bool], pages: list[dict[str, Any]]) -> tuple[str, str, int, str]:
    name = _text(company.get("company_name_fa"), company.get("brand_name_fa"))
    focused = _text(name, company.get("description_observed"), *(page.get("title") for page in pages if str(page.get("source_family") or "").startswith("company_website:")), company.get("website"))
    original = company.get("industry") or "other"
    production_markers = ["تولید کننده", "تولیدکننده", "تولید محصولات", "تولید انواع", "تولید و عرضه", "تولید و تامین", "تولید و تأمین", "تولید مواد", "خط تولید", "کارخانه", "manufacturing plant", "manufacturer"]
    supply_markers = ["بازرگانی", "واردات", "صادرات", "تامین کننده", "تامین‌کننده", "تأمین کننده", "تأمین‌کننده", "عرضه", "بازاریابی و فروش", "فروش عمده", "پخش", "توزیع", "نمایندگی", "عاملیت", "wholesaler", "distributor"]
    food_markers = ["مواد غذایی", "محصولات غذایی", "صنایع غذایی", "مواد خوراکی", "محصولات خوراکی", "کالاهای غذایی", "آبمیوه", "کلوچه", "شکلات", "نوشیدنی", "مالت", "غذای آماده", "food", "fmcg"]
    industrial_supply_markers = ["قفسه فلزی", "ماشین آلات صنعتی", "ماشین‌آلات صنعتی", "اتوماسیون صنعتی", "دیزل ژنراتور", "ژنراتور", "فولاد", "آهن آلات", "فروش آهن", "بلبرینگ", "کابل", "قطعات صنعتی", "محصولات صنعتی", "تجهیزات صنعتی"]
    if _has(focused, ["شعبه", "دفتر مرکزی", "دفتر فروش", "دفتر تهران", "branch", "tehran office"]):
        return "other", "branch", 95, "Name explicitly identifies a branch or head-office listing rather than a standalone company."
    if _has(focused, ["اجاره انبار", "انبار اجاره", "اجاره سوله", "انبارچیان", "self storage", "warehouse rental"]) or (_has(focused, ["اجاره انبار کانتینری", "اجاره سوله", "انبار برای وسایل منزل", "storage rental"]) and not _has(focused, ["حمل و نقل بین المللی", "فورواردر", "ترخیص کالا", "اسناد حمل"])):
        return "other", "warehouse_operator", 92, "Public description emphasizes storage/rental; freight-forwarding or customs operations are not established."
    if _has(focused, ["تولید کننده نرم افزار", "تولیدکننده نرم افزار", "نرم افزار حسابداری", "توسعه نرم افزار", "پلتفرم نرم افزاری", "پلتفرم نرم‌افزاری", "اپلیکیشن تخصصی", "اپلیکیشن ساروپارت", "نرم افزار", "نرم‌افزار", "software company", "accounting software"]) and not _has(focused, industrial_supply_markers + ["تجهیزات پزشکی", "تولید مواد", "کارخانه"]):
        return "other", "service_company", 94, "Public pages identify a software/product business, outside LUMA's preferred buyer profile."
    if _has(focused, ["آپشن", "تیونینگ", "آپشن خودرو", "کرمان موتور", "car tuning"]) and not _has(focused, ["فروش عمده", "تامین کننده", "تامین‌کننده", "توزیع", "پخش", "قطعات یدکی", "نمایندگی"]):
        return "other", "service_company", 88, "Public context is consumer vehicle fitting/tuning rather than an established B2B parts or industrial operation."
    if _has(focused, ["فروشگاه", "سوپرمارکت", "خرده فروشی", "خرده‌فروشی", "retail store"]) and not _has(focused, supply_markers + ["صنعت", "قطعات", "محصولات صنعتی", "کارخانه", "تولید"]):
        return "other", "retailer", 90, "Public context is a retail business without evidence of meaningful B2B distribution or industrial operations."
    if _has(focused, ["بازرگانی", "trading company"]) and _has(focused, production_markers) and not _has(focused, ["کارخانه شرکت", "کارخانه ما", "خط تولید ما", "تولیدکننده مستقیم", "own factory"]) and not _has(focused, ["ترخیص", "گمرک", "فورواردر", "فوروارد", "ترابر", "حمل و نقل", "حمل‌ونقل", "customs", "freight"]):
        return "industrial_distributors_importers", "mixed", 78, "Public pages combine trading/supply language with production claims, but do not independently establish ownership of a manufacturing facility."
    if _has(focused, ["پیمانکار", "پیمانکاری", "epc", "خدمات مهندسی", "شرکت مهندسی", "مهندسی و خدمات", "پروژه مهندسی", "پروژه‌های مهندسی", "طراحی و ساخت", "طراحی، ساخت", "نصب و راه اندازی", "راه اندازی و بهره برداری"]):
        return "epc_engineering_contractors", "EPC_contractor", 90, "Public pages explicitly identify engineering, EPC, project delivery or contracting activity."
    if _has(focused, food_markers):
        if _has(focused, production_markers):
            return "food_fmcg", "manufacturer", 88, "Public pages identify food/FMCG production or a food manufacturing facility."
        if _has(focused, supply_markers + ["بنکداری", "عمده"]):
            return "food_fmcg", "importer" if _has(focused, ["واردات", "صادرات"]) else "distributor", 86, "Public pages identify food/FMCG wholesale, distribution or supply activity."
        return "food_fmcg", "unknown", 70, "Public pages identify a food/FMCG business, but public material does not establish whether it manufactures or distributes."
    if _has(focused, ["نگهداری و تعمیر", "تعمیرات صنعتی", "خدمات پس از فروش", "پشتیبانی فنی", "تنش زدایی", "industrial maintenance", "after sales"]):
        return "industrial_maintenance_after_sales", "service_company", 86, "Public pages identify industrial maintenance, repair or after-sales operations."
    if _has(focused, ["ترخیص کالا", "کارگزار گمرکی", "customs broker"]):
        return "logistics_freight_customs", "customs_broker", 90, "Public pages explicitly identify customs-clearance activity."
    if _has(focused, ["فورواردر", "فوروارد", "ترابر", "حمل و نقل", "حمل‌ونقل", "freight forwarding", "shipping line", "freight"]):
        return "logistics_freight_customs", "freight_forwarder", 90, "Public pages explicitly identify freight transport, forwarding or shipping activity."
    if _has(focused, ["چاپ و بسته بندی", "چاپ و بسته‌بندی", "بسته بندی و چاپ", "کارتن", "جعبه", "لیبل", "printing", "packaging"]):
        return "printing_packaging_labeling", "manufacturer" if _has(focused, production_markers) or signals.get("factory_or_warehouse") else "service_company", 86, "Public product/service pages identify printing, packaging or labeling activity."
    if _has(focused, ["تجهیزات پزشکی", "تجهیزات آزمایشگاهی", "کیت تشخیص", "کیت های تشخیص", "کیتهای تشخیص", "تشخیص طبی", "پزشکی", "medical equipment", "diagnostic kits"]):
        return "medical_equipment", "importer" if _has(focused, ["واردات", "نمایندگی", "نماینده انحصاری", "تامین", "تأمین"]) else "distributor", 90, "Public pages identify medical, laboratory or diagnostic-equipment activity."
    if _has(focused, ["داروسازی", "مواد اولیه دارویی", "محصولات دارویی", "دارویی", "دارو", "pharmaceutical", "active pharmaceutical ingredient"]):
        return "pharma", "manufacturer" if _has(focused, production_markers) else "importer" if _has(focused, ["واردات", "صادرات"]) else "distributor", 88, "Public pages identify pharmaceutical or pharmaceutical-input activity."
    if _has(focused, ["شیرآلات صنعتی", "مصالح ساختمانی", "تاسیسات", "تأسیسات", "فروش آهن", "فولاد", "آهن آلات", "building materials", "steel products"]):
        return "building_materials_mep", "manufacturer" if _has(focused, production_markers) else "distributor", 84, "Public pages identify building-material, steel or MEP products."
    if _has(focused, ["مینی لودر", "لودر", "بیل مکانیکی", "بابکت", "دیزل ژنراتور", "ژنراتور", "اتوماسیون صنعتی", "ماشین آلات صنعتی", "ماشین‌آلات صنعتی"]) and not _has(focused, production_markers):
        return "industrial_distributors_importers", "distributor", 84, "Public pages identify industrial equipment or machinery supply without establishing manufacturing ownership."
    if _has(focused, ["قطعات خودرو", "لوازم یدکی خودرو", "قطعات یدکی خودرو", "خودرو", "automotive parts", "auto parts"]):
        return "auto_parts", "manufacturer" if _has(focused, ["خط تولید", "تولید قطعات", "کارخانه"]) else "distributor", 84, "Public pages identify automotive-parts activity."
    if _has(focused, industrial_supply_markers) and not _has(focused, production_markers):
        return "industrial_distributors_importers", "importer" if _has(focused, ["واردات", "صادرات"]) else "distributor", 82, "Public pages identify industrial products or supply activity without establishing manufacturing ownership."
    if _has(focused, supply_markers) and not _has(focused, production_markers):
        return "industrial_distributors_importers", "importer" if _has(focused, ["واردات", "صادرات"]) else "distributor", 82, "Public pages identify commercial supply, import or distribution activity."
    if _has(focused, production_markers):
        return "industrial_manufacturers", "manufacturer", 82, "Public pages contain explicit production, factory or industrial-manufacturing language."
    return original, "unknown", 45, "Public evidence does not establish a more specific company type than the original category."


def evidence_statuses(company: dict[str, Any], text: str, signals: dict[str, bool], pages: list[dict[str, Any]], company_type: str) -> dict[str, str]:
    page_ok = [p for p in pages if p.get("status") and page_matches_company(company, p) and str(p.get("source_family") or "").startswith("company_website:")]
    has_corporate = any(p.get("kind") in {"company_homepage", "company_page", "search_company_page"} for p in page_ok)
    active_markers = _has(text, ["تماس با ما", "تماس", "سفارش", "محصولات", "خدمات", "مشتریان", "فعالیت", "افتتاح", "تاسیس", "تأسیس", "export", "contact us", "products"])
    # Do not treat ordinary business-hours language such as "closed on
    # holidays" as evidence that the company itself is inactive. Require an
    # explicit closure, dissolution, suspension or expired-domain statement.
    negative_markers = bool(re.search(
        r"(?:suspendedpage|domain\s+(?:has\s+)?expired|(?:منحل|تعطیل|متوقف)\s+(?:شد|شده|است|گردید)|فعالیت.{0,30}(?:متوقف|تعطیل)|تعلیق\s+(?:فعالیت|شده|است)|فعالیت\s+به\s+حالت\s+تعلیق|بسته\s+شد(?:ه)?(?:\s|[.!،]|$))",
        text,
        re.IGNORECASE,
    ))
    scale_signals = sum(bool(item) for item in [
        signals.get("factory_or_warehouse"), signals.get("branches_or_dealers"), signals.get("projects_or_clients"),
        signals.get("certifications"), _has(text, ["سال سابقه", "سال فعالیت", "نماینده انحصاری", "سراسر کشور", "کشورهای مختلف", "دفتر در", "warehouse network"]),
    ])
    complexity_signals = sum(bool(item) for item in [
        signals.get("rfq_or_quote"), signals.get("catalog_or_products"), signals.get("order_or_contact_form"), signals.get("factory_or_warehouse"),
        signals.get("branches_or_dealers"), signals.get("service_after_sales"), signals.get("projects_or_clients"), signals.get("tender_or_contract"),
    ])
    workflow_signal_count = sum(bool(signals.get(key)) for key in ["rfq_or_quote", "catalog_or_products", "order_or_contact_form", "factory_or_warehouse", "service_after_sales", "tender_or_contract", "projects_or_clients"])
    if negative_markers:
        active = "NEGATIVE"
    elif has_corporate and active_markers:
        active = "SUPPORTED"
    elif any(p.get("kind") == "directory_profile" and p.get("status") for p in pages) and company.get("phone_public") and company.get("hq_address"):
        active = "PARTIAL"
    else:
        active = "UNKNOWN"
    if scale_signals >= 3:
        strength = "KNOWN_STRONG"
    elif scale_signals >= 1:
        strength = "KNOWN_MODERATE"
    else:
        strength = "UNKNOWN"
    if complexity_signals >= 3 or company_type in {"freight_forwarder", "customs_broker", "EPC_contractor", "manufacturer"} and scale_signals >= 1:
        complexity = "KNOWN_HIGH"
    elif complexity_signals >= 1:
        complexity = "KNOWN_MODERATE"
    else:
        complexity = "UNKNOWN"
    if workflow_signal_count >= 2:
        workflow = "DIRECT_SIGNALS"
    elif workflow_signal_count == 1:
        workflow = "SINGLE_SIGNAL"
    else:
        workflow = "UNKNOWN"
    software_high = _has(text, ["هوش مصنوعی", "یادگیری ماشین", "دانشمند داده", "تیم نرم افزار", "تیم نرم‌افزار", "برنامه نویس", "برنامه‌نویس", "backend", "frontend", "devops", "mlops", "پلتفرم نرم افزاری", "پلتفرم نرم‌افزاری", "اپلیکیشن", "اپلیکیشن تخصصی", "software company"])
    software_moderate = signals.get("software_or_erp") or _has(text, ["crm", "erp", "راهکاران", "همکاران سیستم", "سپیدار", "پرتال مشتری", "پنل کاربری", "api"])
    if software_high:
        tech = "KNOWN_HIGH_INTERNAL_TECH"
    elif software_moderate:
        tech = "KNOWN_MODERATE_INTERNAL_TECH"
    elif _has(text, ["فرآیند دستی", "فرآیندهای دستی", "به صورت دستی", "فایل اکسل", "excel-based", "manual process", "بدون نرم افزار", "بدون نرم‌افزار", "فاقد نرم افزار", "فاقد نرم‌افزار"]):
        tech = "KNOWN_LOW_INTERNAL_TECH"
    else:
        tech = "UNKNOWN_INTERNAL_TECH"
    digital_high = _has(text, ["api", "پرتال مشتری", "پنل کاربری", "developer portal", "سامانه آنلاین", "اپلیکیشن", "online ordering"]) or (signals.get("software_or_erp") and signals.get("order_or_contact_form"))
    digital_moderate = signals.get("catalog_or_products") or signals.get("order_or_contact_form") or signals.get("rfq_or_quote") or bool(company.get("website")) and has_corporate
    digital_low = has_corporate and not digital_moderate and not digital_high
    if digital_high:
        digital = "KNOWN_HIGH_DIGITAL_MATURITY"
    elif digital_moderate:
        digital = "KNOWN_MODERATE_DIGITAL_MATURITY"
    elif digital_low:
        digital = "KNOWN_LOW_DIGITAL_MATURITY"
    else:
        digital = "UNKNOWN_DIGITAL_MATURITY"
    decision = "PUBLIC_NAME_VERIFIED" if company.get("decision_maker_name_public") and company.get("decision_maker_source_url") else "ROLE_HYPOTHESIS" if company.get("decision_maker_role") else "UNKNOWN_DECISION_MAKER"
    return {
        "active_status_evidence": active,
        "company_strength_evidence_status": strength,
        "operational_complexity_evidence_status": complexity,
        "workflow_evidence_status": workflow,
        "internal_tech_capability_evidence_status": tech,
        "digital_maturity_evidence_status": digital,
        "decision_maker_evidence_status": decision,
    }


def score_from_status(status: str, mapping: dict[str, int], default: int = 50) -> int:
    return int(mapping.get(status, default))


def choose_workflow(company: dict[str, Any], text: str, signals: dict[str, bool], company_type: str, statuses: dict[str, str], evidence: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    industry = company.get("industry")
    key: str | None = None
    if company_type in {"freight_forwarder", "customs_broker"} and (signals.get("tender_or_contract") or _has(text, ["بارنامه", "اسناد حمل", "پروفرما", "گمرک", "shipment", "bill of lading"])):
        key = "shipment_document_automation"
    elif company_type == "warehouse_operator":
        key = None
    elif industry in {"epc_engineering_contractors", "building_materials_mep"} and (signals.get("tender_or_contract") or signals.get("projects_or_clients") or _has(text, ["boq", "اقلام", "سابمیتال", "مشخصات فنی", "طراحی و ساخت", "طراحی، ساخت"])):
        key = "boq_specification_matching"
    elif industry == "printing_packaging_labeling" and (signals.get("projects_or_clients") or signals.get("factory_or_warehouse") or signals.get("catalog_or_products")):
        key = "job_brief_estimate"
    elif industry in {"industrial_maintenance_after_sales", "auto_parts"} and signals.get("service_after_sales"):
        key = "service_ticket_maintenance"
    elif industry in {"epc_engineering_contractors", "medical_equipment"} and signals.get("tender_or_contract"):
        key = "tender_document_assistant"
    elif signals.get("rfq_or_quote") or (signals.get("catalog_or_products") and industry in {"industrial_distributors_importers", "building_materials_mep", "medical_equipment", "auto_parts"}):
        key = "rfq_quotation"
    elif industry in {"food_fmcg", "industrial_distributors_importers"} and (signals.get("order_or_contact_form") or signals.get("branches_or_dealers") or signals.get("factory_or_warehouse")):
        key = "order_inventory_exceptions"
    elif industry in {"industrial_manufacturers", "pharma"} and (signals.get("factory_or_warehouse") or signals.get("certifications")):
        key = "production_quality_reporting"
    elif industry == "auto_parts" and signals.get("catalog_or_products"):
        key = "parts_catalog_matching"
    if not key:
        return None, "UNSUPPORTED"
    spec = WORKFLOW_SPECS[key]
    direct = statuses.get("workflow_evidence_status") == "DIRECT_SIGNALS"
    supporting = [item for item in evidence if item.get("signal") in {"rfq_or_quote", "catalog_or_products", "order_or_contact_form", "factory_or_warehouse", "service_after_sales", "projects_or_clients", "tender_or_contract", "certifications"}]
    classification = "EVIDENCE_SUPPORTED" if direct and len(supporting) >= 2 else "STRONG_HYPOTHESIS" if direct or len(supporting) >= 1 else "WEAK_HYPOTHESIS"
    confidence = 0.85 if classification == "EVIDENCE_SUPPORTED" else 0.7 if classification == "STRONG_HYPOTHESIS" else 0.45
    urls = list(dict.fromkeys(item.get("source_url") for item in supporting if item.get("source_url")))[:6]
    workflow = {
        "workflow_id": "wf-" + stable_hash(company["company_id"], key, AUDIT_VERSION),
        "company_id": company["company_id"],
        "workflow_name": spec["workflow_name"],
        "workflow_family": key,
        "workflow_evidence_classification": classification,
        "current_process_hypothesis": f"{classification} — Public evidence shows {', '.join(SIGNAL_LABELS[item.get('signal')] for item in supporting[:3] if item.get('signal') in SIGNAL_LABELS) or 'a relevant commercial context'}; the internal handoff and volume require discovery.",
        "supporting_evidence": [{"claim": item.get("claim"), "source_url": item.get("source_url"), "source_title": item.get("source_title"), "quote_or_snippet": item.get("quote_or_snippet"), "evidence_type": item.get("evidence_type"), "confidence": item.get("confidence")} for item in supporting[:6]],
        "current_problem": "A repeated lookup, intake, reporting or document handoff is plausible from the public operating surface; an internal failure is not claimed.",
        "proposed_luma_solution": spec["solution"],
        "primary_users": spec["users"],
        "likely_business_owner": OWNER_BY_WORKFLOW[key],
        "required_data": [spec["data"]],
        "required_integrations": [spec["integrations"]],
        "implementation_complexity": "High" if key in {"shipment_document_automation", "production_quality_reporting", "tender_document_assistant"} else "Medium",
        "implementation_risks": ["public sources cannot establish volume or data quality", "integration and permissions require discovery", "human approval remains required"],
        "measurable_KPIs": spec["kpis"],
        "confidence": "High" if confidence >= 0.8 else "Medium" if confidence >= 0.6 else "Low",
        "confidence_score": confidence,
        "discovery_questions": spec["questions"],
        "source_urls": urls,
    }
    return workflow, classification


def audit_company(company: dict[str, Any], pages: list[dict[str, Any]]) -> dict[str, Any]:
    company = dict(company)
    company.setdefault("original_priority_tier", company.get("priority_tier"))
    company.setdefault("original_luma_opportunity_score", company.get("luma_opportunity_score"))
    company.setdefault("original_score_confidence", company.get("score_confidence"))
    company.setdefault("original_industry", company.get("industry") or "other")
    company.setdefault("original_workflow_opportunities", company.get("workflow_opportunities") or [])
    for component_key in [
        "company_strength_score", "operational_complexity_score", "workflow_density_score", "ai_roi_score", "data_readiness_score",
        "digital_maturity_score", "digital_maturity_fit_score", "internal_tech_capability_score", "outsourcing_fit_score",
    ]:
        company.setdefault(f"original_{component_key}", company.get(component_key))
    # Older first-run source rows did not consistently store a family. Fill it
    # from the URL/type so the audit count and exported provenance are stable.
    for source in company.get("source_records") or []:
        if not source.get("source_family"):
            source["source_family"] = source_family(source.get("source_url"), source_type=source.get("source_type"))
    for item in company.get("evidence") or []:
        if not item.get("source_family"):
            item["source_family"] = source_family(item.get("source_url"), source_type=item.get("source_quality"))
    usable_pages = [page for page in pages if page_matches_company(company, page)]
    text = all_audit_text(company, usable_pages)
    signals = signal_union(company, usable_pages)
    corrected_industry, company_type, class_conf, class_reason = classify_company(company, text, signals, usable_pages)
    statuses = evidence_statuses(company, text, signals, usable_pages, company_type)
    new_evidence: list[dict[str, Any]] = []
    new_sources: list[dict[str, Any]] = []
    page_paths: list[str] = []
    for page in usable_pages:
        url = page.get("final_url") or page.get("requested_url")
        if not url:
            continue
        new_sources.append(source_record(company["company_id"], page))
        stored = save_page_text(company["company_id"], page)
        if stored:
            page_paths.append(stored)
        if not str(page.get("source_family") or "").startswith("company_website:"):
            continue
        for signal, present in (page.get("signals") or {}).items():
            if present and signal in SIGNAL_LABELS:
                snippet = signal_snippet(page, signal) or SIGNAL_LABELS[signal]
                new_evidence.append(evidence_item(company["company_id"], f"Public page shows {SIGNAL_LABELS[signal]}.", url, page.get("title") or "Public page", snippet, 0.82 if signal in {"rfq_or_quote", "catalog_or_products", "factory_or_warehouse", "projects_or_clients"} else 0.72, signal=signal, family=page.get("source_family")))
        if page.get("kind") == "search_company_page" and page.get("text_excerpt"):
            new_evidence.append(evidence_item(company["company_id"], "A targeted public search result associates this company name with the linked page.", url, page.get("title") or "Search result", page.get("text_excerpt"), 0.58, evidence_type="OBSERVED", family=page.get("source_family")))
    # Deduplicate audit evidence while retaining the original evidence untouched.
    old_keys = {(item.get("source_url"), item.get("claim")) for item in company.get("evidence", [])}
    company["evidence"] = list(company.get("evidence", [])) + [item for item in new_evidence if (item.get("source_url"), item.get("claim")) not in old_keys]
    old_source_keys = {(item.get("source_url"), item.get("source_family") or source_family(item.get("source_url"), source_type=item.get("source_type"))) for item in company.get("source_records", [])}
    company["source_records"] = list(company.get("source_records", [])) + [item for item in new_sources if (item.get("source_url"), item.get("source_family")) not in old_source_keys]
    company["email_public"] = filter_public_emails(company.get("email_public") or [])
    for page in usable_pages:
        company["phone_public"] = sorted(set(company.get("phone_public") or []) | set(page.get("phones") or []))
        company["email_public"] = filter_public_emails(list(company.get("email_public") or []) + list(page.get("emails") or []))
    company["audit_page_paths"] = sorted(set(company.get("audit_page_paths") or []) | set(page_paths))
    company["audit_signals"] = signals
    company["audit_source_families"] = sorted(existing_families(company))
    company["independent_source_families"] = sorted(independent_families(company))
    company["independent_source_count"] = len(company["independent_source_families"])
    company["audit_pages_checked"] = len(pages)
    company["audit_pages_usable"] = len(usable_pages)
    company["industry"] = corrected_industry
    company["industry_classification_confidence"] = class_conf
    company["classification_correction_reason"] = class_reason
    company["company_type"] = company_type
    company.update(statuses)
    # A page's direct evidence, not the directory category, drives the workflow.
    workflow, workflow_class = choose_workflow(company, text, signals, company_type, statuses, new_evidence)
    company["workflow_evidence_classification"] = workflow_class
    company["workflow_opportunities"] = [workflow] if workflow else []
    signal_counts = {
        key: sum(1 for page in usable_pages if str(page.get("source_family") or "").startswith("company_website:") and (page.get("signals") or {}).get(key))
        for key in SIGNAL_LABELS
    }
    company["audit_signal_counts"] = signal_counts
    scale_count = sum(1 for key in ["factory_or_warehouse", "branches_or_dealers", "projects_or_clients", "certifications", "expansion_or_activity"] if signals.get(key))
    complexity_count = sum(1 for key in ["rfq_or_quote", "catalog_or_products", "order_or_contact_form", "factory_or_warehouse", "branches_or_dealers", "service_after_sales", "projects_or_clients", "tender_or_contract"] if signals.get(key))
    workflow_signal_count = sum(1 for key in ["rfq_or_quote", "catalog_or_products", "order_or_contact_form", "factory_or_warehouse", "service_after_sales", "tender_or_contract", "projects_or_clients"] if signals.get(key))
    data_signal_count = sum(1 for key in ["catalog_or_products", "rfq_or_quote", "order_or_contact_form", "factory_or_warehouse", "tender_or_contract"] if signals.get(key))
    strength = {
        "KNOWN_STRONG": min(96, 76 + scale_count * 5),
        "KNOWN_MODERATE": min(76, 56 + scale_count * 7),
    }.get(statuses["company_strength_evidence_status"], 50)
    complexity = {
        "KNOWN_HIGH": min(96, 70 + complexity_count * 4),
        "KNOWN_MODERATE": min(78, 54 + complexity_count * 7),
    }.get(statuses["operational_complexity_evidence_status"], 50)
    workflow_density = 72 + min(24, workflow_signal_count * 6) if statuses["workflow_evidence_status"] == "DIRECT_SIGNALS" else 62 if statuses["workflow_evidence_status"] == "SINGLE_SIGNAL" else 45
    maturity = {
        "KNOWN_LOW_DIGITAL_MATURITY": 32,
        "KNOWN_MODERATE_DIGITAL_MATURITY": min(76, 50 + min(26, (signal_counts.get("catalog_or_products", 0) + signal_counts.get("order_or_contact_form", 0) + signal_counts.get("rfq_or_quote", 0)) * 6)),
        "KNOWN_HIGH_DIGITAL_MATURITY": 84,
    }.get(statuses["digital_maturity_evidence_status"], 50)
    maturity_fit = {
        "KNOWN_LOW_DIGITAL_MATURITY": 44,
        "KNOWN_MODERATE_DIGITAL_MATURITY": min(96, 82 + min(14, workflow_signal_count * 3)),
        "KNOWN_HIGH_DIGITAL_MATURITY": 30,
    }.get(statuses["digital_maturity_evidence_status"], 50)
    tech = score_from_status(statuses["internal_tech_capability_evidence_status"], {"KNOWN_LOW_INTERNAL_TECH": 25, "KNOWN_MODERATE_INTERNAL_TECH": 58, "KNOWN_HIGH_INTERNAL_TECH": 88}, 50)
    outsourcing = score_from_status(statuses["internal_tech_capability_evidence_status"], {"KNOWN_LOW_INTERNAL_TECH": 82, "KNOWN_MODERATE_INTERNAL_TECH": 55, "KNOWN_HIGH_INTERNAL_TECH": 18}, 50)
    direct_workflow = workflow_class in {"EVIDENCE_SUPPORTED", "STRONG_HYPOTHESIS"}
    ai_roi = min(94, 72 + min(22, workflow_signal_count * 5)) if workflow_class == "EVIDENCE_SUPPORTED" else 65 if workflow_class == "STRONG_HYPOTHESIS" else 50 if workflow_class == "WEAK_HYPOTHESIS" else 36
    data_readiness = min(94, 50 + data_signal_count * 8) if usable_pages else 45
    sales_access = 40
    if company.get("phone_public"):
        sales_access += 18
    if usable_pages:
        sales_access += 12
    if company.get("website") or any(str(page.get("source_family") or "").startswith("company_website:") for page in usable_pages):
        sales_access += 8
    if company.get("decision_maker_role"):
        sales_access += 5
    project_value = 82 if statuses["company_strength_evidence_status"] == "KNOWN_STRONG" else 66 if statuses["company_strength_evidence_status"] == "KNOWN_MODERATE" else 50
    implementation = 76 if data_readiness >= 70 and direct_workflow else 64 if direct_workflow else 54 if usable_pages else 45
    sales_ease = 72 if sales_access >= 75 else 55
    regulatory = 62 if corrected_industry in {"medical_equipment", "pharma"} else 74
    if corrected_industry in {"logistics_freight_customs", "industrial_distributors_importers", "printing_packaging_labeling", "auto_parts"}:
        regulatory += 8
    components = {
        "company_strength_score": strength, "operational_complexity_score": complexity, "workflow_density_score": workflow_density,
        "ai_roi_score": ai_roi, "data_readiness_score": data_readiness, "digital_maturity_score": maturity,
        "digital_maturity_fit_score": maturity_fit, "internal_tech_capability_score": tech, "outsourcing_fit_score": outsourcing,
        "sales_access_score": sales_access, "expected_project_value_score": project_value, "implementation_score": implementation,
        "sales_cycle_ease_score": sales_ease, "regulatory_score": min(100, regulatory),
    }
    weights = {"company_strength_score": 12, "operational_complexity_score": 12, "workflow_density_score": 10, "ai_roi_score": 16, "data_readiness_score": 10, "digital_maturity_fit_score": 12, "outsourcing_fit_score": 8, "sales_access_score": 6, "expected_project_value_score": 5, "implementation_score": 4, "sales_cycle_ease_score": 3, "regulatory_score": 2}
    raw_score = sum(weights[key] * components[key] / 100 for key in weights)
    trigger_bonus = 2 if signals.get("expansion_or_activity") else 0
    if signals.get("software_or_erp"):
        trigger_bonus += 1
    trigger_bonus = min(3, trigger_bonus)
    risk_reasons: list[str] = []
    risk = 0
    if company_type == "branch":
        risk += 30; risk_reasons.append("branch_listing_not_standalone")
    if company_type == "warehouse_operator":
        risk += 22; risk_reasons.append("warehouse_rental_not_freight_forwarding")
    if company_type == "retailer":
        risk += 18; risk_reasons.append("retail_context_without_established_B2B_scale")
    if statuses["active_status_evidence"] == "UNKNOWN":
        risk += 12; risk_reasons.append("active_status_unknown")
    elif statuses["active_status_evidence"] == "PARTIAL":
        risk += 6; risk_reasons.append("active_status_only_partially_supported")
    if statuses["company_strength_evidence_status"] == "UNKNOWN":
        risk += 12; risk_reasons.append("scale_unknown")
    if statuses["operational_complexity_evidence_status"] == "UNKNOWN":
        risk += 10; risk_reasons.append("operational_complexity_unknown")
    if workflow_class == "WEAK_HYPOTHESIS":
        risk += 10; risk_reasons.append("workflow_weak_hypothesis")
    elif workflow_class == "UNSUPPORTED":
        risk += 18; risk_reasons.append("workflow_unsupported")
    if statuses["internal_tech_capability_evidence_status"] == "KNOWN_HIGH_INTERNAL_TECH":
        risk += 18; risk_reasons.append("strong_internal_tech_signal")
    risk = min(45, risk)
    new_score = max(0, min(100, round(raw_score + trigger_bonus - risk)))
    coverage_statuses = [statuses["active_status_evidence"], statuses["company_strength_evidence_status"], statuses["operational_complexity_evidence_status"], statuses["workflow_evidence_status"], statuses["digital_maturity_evidence_status"], statuses["internal_tech_capability_evidence_status"]]
    covered = sum(1 for value in coverage_statuses if value not in {"UNKNOWN", "UNKNOWN_INTERNAL_TECH", "UNKNOWN_DIGITAL_MATURITY"})
    unknown_dimensions = len(coverage_statuses) - covered
    score_confidence = min(100, 20 + 12 * min(company["independent_source_count"], 5) + 6 * min(covered, 7) - 10 * unknown_dimensions + (5 if usable_pages else 0) + (4 if any(page.get("kind") == "directory_profile" and page.get("status") for page in pages) else 0))
    score_confidence = max(20, score_confidence)
    score_confidence = int(score_confidence)
    confidence_factor = round(0.40 + 0.60 * score_confidence / 100, 3)
    adjusted_score = round(new_score * confidence_factor, 1)
    evidence_strength = 20 + min(20, 10 * min(company["independent_source_count"], 2))
    evidence_strength += {"SUPPORTED": 18, "PARTIAL": 8, "NEGATIVE": 0, "UNKNOWN": 0}.get(statuses["active_status_evidence"], 0)
    evidence_strength += {"KNOWN_STRONG": 18, "KNOWN_MODERATE": 10, "UNKNOWN": 0}.get(statuses["company_strength_evidence_status"], 0)
    evidence_strength += {"KNOWN_HIGH": 16, "KNOWN_MODERATE": 10, "UNKNOWN": 0}.get(statuses["operational_complexity_evidence_status"], 0)
    evidence_strength += {"EVIDENCE_SUPPORTED": 18, "STRONG_HYPOTHESIS": 12, "WEAK_HYPOTHESIS": 5, "UNSUPPORTED": 0}.get(workflow_class, 0)
    evidence_strength += 8 if usable_pages else 0
    evidence_strength -= 18 if company_type in {"branch", "warehouse_operator", "retailer"} else 0
    # Two families (usually Avval plus a self-published company site) are
    # useful corroboration but do not justify maximum commercial certainty.
    independent = company.get("independent_source_families") or []
    if len(independent) == 0:
        family_cap = 25
    elif len(independent) == 1:
        family_cap = 49
    elif len(independent) == 2 and "book_e_avval" in independent and any(item.startswith("company_website:") for item in independent):
        family_cap = 72
    elif len(independent) == 2:
        family_cap = 82
    elif len(independent) == 3:
        family_cap = 92
    else:
        family_cap = 100
    commercial_strength = max(0, min(family_cap, evidence_strength))
    hard = None
    if company_type == "branch":
        hard = "BRANCH_LISTING_NOT_STANDALONE"
    elif statuses["active_status_evidence"] == "NEGATIVE":
        hard = "NEGATIVE_ACTIVE_STATUS_SIGNAL"
    elif statuses["internal_tech_capability_evidence_status"] == "KNOWN_HIGH_INTERNAL_TECH" and company_type == "service_company":
        hard = "STRONG_INTERNAL_TECH_SIGNAL"
    elif not company.get("hq_address") and not company.get("phone_public") and not usable_pages:
        hard = "NO_CREDIBLE_PUBLIC_FOOTPRINT"
    meaningful = statuses["company_strength_evidence_status"] != "UNKNOWN" or statuses["operational_complexity_evidence_status"] != "UNKNOWN"
    ready_gate = (
        not hard and statuses["active_status_evidence"] == "SUPPORTED" and meaningful
        and company["independent_source_count"] >= 2 and workflow_class in {"EVIDENCE_SUPPORTED", "STRONG_HYPOTHESIS"}
        and statuses["internal_tech_capability_evidence_status"] != "KNOWN_HIGH_INTERNAL_TECH" and commercial_strength >= 70 and score_confidence >= 65 and new_score >= 70
    )
    a_gate = ready_gate and new_score >= 80
    b_gate = not hard and new_score >= 70 and commercial_strength >= 50 and score_confidence >= 50 and workflow_class != "UNSUPPORTED" and statuses["active_status_evidence"] != "NEGATIVE"
    tier = "A" if a_gate else "B" if b_gate else "C" if new_score >= 60 else "D" if new_score >= 45 else "Reject"
    if hard:
        tier = "Reject"
    if not hard and tier in {"A", "B"} and statuses["active_status_evidence"] == "UNKNOWN":
        tier = "C"
    if not hard and tier == "A" and commercial_strength < 70:
        tier = "B"
    if not hard and tier == "B" and (commercial_strength < 50 or score_confidence < 50):
        tier = "C"
    if tier == "A" and statuses["active_status_evidence"] != "SUPPORTED":
        tier = "B" if b_gate else "C"
    if ready_gate:
        readiness = "READY FOR OUTREACH"
    elif not hard and workflow_class != "UNSUPPORTED" and (adjusted_score >= 52 or commercial_strength >= 50):
        readiness = "NEEDS DISCOVERY"
    else:
        readiness = "NOT READY"
    if company_type in {"branch", "warehouse_operator", "retailer"} or hard or workflow_class == "UNSUPPORTED":
        readiness = "NOT READY" if not (tier == "B" and workflow_class != "UNSUPPORTED" and company_type not in {"branch", "warehouse_operator", "retailer"}) else readiness
    evidence_urls = list(dict.fromkeys(item.get("source_url") for item in company.get("evidence", []) if item.get("source_url") and not item.get("excluded_from_qualification")))[:20]
    company.update(components)
    company.update({
        "commercial_audit_version": AUDIT_VERSION,
        "commercial_evidence_strength": commercial_strength,
        "commercial_evidence_strength_reason": "Independent public source families plus corroborated activity, scale/complexity and workflow signals; UNKNOWN dimensions were not awarded positive points.",
        "score_confidence": score_confidence,
        "confidence_factor": confidence_factor,
        "confidence_adjusted_score": adjusted_score,
        "luma_opportunity_score": new_score,
        "priority_tier": tier,
        "commercial_readiness": readiness,
        "sales_readiness": readiness,
        "score_version": AUDIT_VERSION,
        "score_date": now_iso(),
        "trigger_bonus": trigger_bonus,
        "risk_penalty": risk,
        "risk_reasons": risk_reasons,
        "hard_disqualifier": hard,
        "workflow_evidence_classification": workflow_class,
        "evidence_urls": evidence_urls,
        "last_research_date": now_iso(),
        "audit_summary": f"{class_reason} Active status: {statuses['active_status_evidence']}; scale: {statuses['company_strength_evidence_status']}; complexity: {statuses['operational_complexity_evidence_status']}; workflow: {workflow_class}.",
        "qualification_reason": f"Commercial audit: {readiness}; {company_type}; {commercial_strength}/100 evidence strength; {company['independent_source_count']} independent source families; {score_confidence}/100 score confidence.",
        "strongest_observed_evidence": [item.get("claim") for item in new_evidence[:6]] or company.get("strongest_observed_evidence") or [],
        "decision_maker_source_url": next((item.get("source_url") for item in new_evidence if item.get("source_url")), company.get("decision_maker_source_url")),
        "decision_maker_confidence": 0.85 if statuses["decision_maker_evidence_status"] == "PUBLIC_NAME_VERIFIED" else 0.35 if company.get("decision_maker_role") else 0.0,
        "digital_maturity_interpretation": {
            "UNKNOWN_DIGITAL_MATURITY": "UNKNOWN — no positive digital-maturity score was awarded from absence of public evidence.",
            "KNOWN_LOW_DIGITAL_MATURITY": "Known low public digital surface; this is a risk signal, not an automatic outsourcing-fit bonus.",
            "KNOWN_MODERATE_DIGITAL_MATURITY": "Known moderate/fragmented public digital surface; validate internal handoffs and system ownership.",
            "KNOWN_HIGH_DIGITAL_MATURITY": "Known high digital surface; outsourcing fit is reduced and internal ownership must be validated.",
        }.get(statuses["digital_maturity_evidence_status"], "UNKNOWN"),
        "internal_tech_capability_interpretation": {
            "UNKNOWN_INTERNAL_TECH": "UNKNOWN — lack of public evidence is not treated as known low internal capability.",
            "KNOWN_LOW_INTERNAL_TECH": "Known low internal technical capability from explicit public evidence.",
            "KNOWN_MODERATE_INTERNAL_TECH": "Known moderate business-systems capability; custom delivery ownership remains to be validated.",
            "KNOWN_HIGH_INTERNAL_TECH": "Known high internal software/data capability; LUMA outsourcing fit is reduced.",
        }.get(statuses["internal_tech_capability_evidence_status"], "UNKNOWN"),
    })
    if workflow:
        company["strongest_workflow"] = workflow.get("workflow_name")
    else:
        company["strongest_workflow"] = None
    # Keep the final family list after all new records have been appended.
    company["audit_source_families"] = sorted(existing_families(company))
    company["independent_source_families"] = sorted(independent_families(company))
    company["independent_source_count"] = len(company["independent_source_families"])
    return company


def apply_evidence_package(company: dict[str, Any], pages: list[dict[str, Any]], errors: list[dict[str, Any]]) -> None:
    package = path_for("evidence", "companies", company["company_id"], "sources.json")
    existing: dict[str, Any] = {}
    if package.exists():
        try:
            existing = json.loads(package.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    old_sources = existing.get("sources") or []
    old_keys = {(item.get("source_url"), item.get("source_family")) for item in old_sources}
    added_sources = [source_record(company["company_id"], page) for page in pages if page.get("status")]
    all_sources = old_sources + [item for item in added_sources if (item.get("source_url"), item.get("source_family")) not in old_keys]
    old_errors = existing.get("errors") or []
    merged_errors: list[dict[str, Any]] = []
    seen_errors: set[tuple[Any, ...]] = set()
    for item in old_errors + errors:
        error_key = tuple(item.get(key) for key in ("stage", "url", "source_url", "classification", "error"))
        if error_key in seen_errors:
            continue
        seen_errors.add(error_key)
        merged_errors.append(item)
    package_payload = {
        "company_id": company["company_id"],
        "generated_at": now_iso(),
        "sources": all_sources,
        "screenshots": existing.get("screenshots") or [],
        "errors": merged_errors,
        "commercial_audit": {
            "version": AUDIT_VERSION,
            "pages_checked": len(pages),
            "pages_usable": sum(1 for page in pages if page_matches_company(company, page)),
            "source_families": company.get("audit_source_families") or [],
            "independent_source_count": company.get("independent_source_count"),
            "sales_readiness": company.get("sales_readiness"),
        },
        "headless_policy": {"headless": True, "proxy": DEFAULT_PROXY, "isolated_context": True, "visible_browser_launched": False},
    }
    write_json(package, package_payload)
    notes_path = package.parent / "notes.md"
    existing_notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else f"# {company.get('company_name_fa')}\n"
    existing_notes = existing_notes.split("\n## Commercial audit", 1)[0].rstrip()
    notes = [existing_notes, "", "## Commercial audit", "", f"Audit version: {AUDIT_VERSION}", f"Corrected industry/type: {company.get('industry')} / {company.get('company_type')}", f"Commercial evidence strength: {company.get('commercial_evidence_strength')}/100", f"Score confidence: {company.get('score_confidence')}/100", f"Readiness: {company.get('sales_readiness')}", f"Pages checked/usable: {len(pages)}/{sum(1 for page in pages if page_matches_company(company, page))}", "", "Page captures:"]
    notes.extend(f"- `{path}`" for path in company.get("audit_page_paths") or [])
    if errors:
        notes.extend(["", "Audit fetch notes:"])
        notes.extend(f"- {item.get('classification', 'SOURCE_ERROR')}: {item.get('url') or item.get('source_url')}: {item.get('error', '')}" for item in errors)
    notes_path.write_text("\n".join(notes) + "\n", encoding="utf-8")


def fetch_tasks(tasks: list[dict[str, Any]], *, proxy: str, max_workers: int, rate_limit: float, timeout: float) -> list[dict[str, Any]]:
    limiter = RateLimiter(rate_limit)
    results: list[dict[str, Any]] = []
    def one(task: dict[str, Any]) -> dict[str, Any]:
        response = fetch_cached(task["url"], proxy=proxy, limiter=limiter, timeout=timeout, max_bytes=2_500_000)
        page = compact_page(response, task["url"], task["kind"], task.get("query"))
        page["company_id"] = task["company_id"]
        page["task_id"] = task.get("task_id")
        return page
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(one, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                task = tasks[len(results)] if len(results) < len(tasks) else {}
                results.append({"company_id": task.get("company_id"), "requested_url": task.get("url"), "kind": task.get("kind"), "status": None, "error": f"{type(exc).__name__}: {exc}", "source_family": source_family(task.get("url"))})
    return results


def choose_initial_tasks(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for company in companies:
        cid = company["company_id"]
        profile = next((url for url in company.get("profile_urls") or [] if url), None)
        if profile:
            tasks.append({"task_id": stable_hash(cid, profile, "profile"), "company_id": cid, "url": profile, "kind": "directory_profile"})
        website_candidates = [company.get("website")] + list(company.get("website_candidates") or [])
        website = next((canonical_url(url) for url in website_candidates if valid_public_url(url)), None)
        if website:
            key = (cid, website, "company_homepage")
            if key not in seen:
                seen.add(key)
                tasks.append({"task_id": stable_hash(cid, website, "homepage"), "company_id": cid, "url": website, "kind": "company_homepage"})
        for query in query_variants(company):
            url = search_url(query)
            tasks.append({"task_id": stable_hash(cid, url), "company_id": cid, "url": url, "kind": "search_query", "query": query})
    return tasks


def build_followup_tasks(companies: list[dict[str, Any]], initial_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in initial_pages:
        by_id[page.get("company_id")].append(page)
    tasks: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for company in companies:
        cid = company["company_id"]
        for page in by_id.get(cid, []):
            if page.get("kind") == "search_query" and page.get("status") == 200 and page.get("text_excerpt"):
                query = page.get("query")
                parsed = parse_ddg(page.get("_body", ""), page.get("requested_url", ""), query or "") if page.get("_body") else []
                for result in parsed[:5]:
                    if not relevant_search_result(company, result):
                        continue
                    target = canonical_url(result.get("website"))
                    if not target or not valid_public_url(target):
                        continue
                    key = (cid, target)
                    if key in seen:
                        continue
                    seen.add(key)
                    tasks.append({"task_id": stable_hash(cid, target, "search_result"), "company_id": cid, "url": target, "kind": "search_company_page", "query": query})
            if page.get("kind") in {"company_homepage", "company_page", "search_company_page"} and page.get("status") == 200:
                for link in page.get("relevant_links") or []:
                    target = canonical_url(link.get("url"), page.get("final_url") or page.get("requested_url"))
                    if not target or domain_of(target) != domain_of(page.get("final_url") or page.get("requested_url")):
                        continue
                    key = (cid, target)
                    if key in seen or target == (page.get("final_url") or page.get("requested_url")):
                        continue
                    seen.add(key)
                    tasks.append({"task_id": stable_hash(cid, target, "company_page"), "company_id": cid, "url": target, "kind": "company_page"})
                    if sum(1 for item in tasks if item["company_id"] == cid and item["kind"] == "company_page") >= 3:
                        break
    return tasks


def restore_search_bodies(pages: list[dict[str, Any]]) -> None:
    for page in pages:
        if page.get("kind") != "search_query":
            continue
        path = cache_path(page.get("requested_url", ""))
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            page["_body"] = payload.get("body", "")
        except Exception:
            page["_body"] = ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Commercially re-enrich only existing Tier A/B LUMA prospects")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    parser.add_argument("--proxy", default=DEFAULT_PROXY)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--rate-limit-seconds", type=float, default=0.45)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()
    if not args.skip_preflight and not preflight(args.proxy):
        print("Commercial audit stopped: direct-proxy preflight failed.", file=sys.stderr)
        return 2
    all_companies = read_jsonl(args.input)
    targets = [
        company for company in all_companies
        if (company.get("original_priority_tier") or company.get("priority_tier")) in {"A", "B"}
    ]
    if len(targets) != 151:
        print(f"Target count is {len(targets)}; this audit expects the existing 151 A/B records.", file=sys.stderr)
    tasks = choose_initial_tasks(targets)
    print(f"Commercial audit targets: {len(targets)} existing A/B records; initial public tasks: {len(tasks)}")
    initial = fetch_tasks(tasks, proxy=args.proxy, max_workers=args.max_workers, rate_limit=args.rate_limit_seconds, timeout=args.timeout)
    restore_search_bodies(initial)
    followups = build_followup_tasks(targets, initial)
    print(f"Targeted follow-up public pages: {len(followups)}")
    second = fetch_tasks(followups, proxy=args.proxy, max_workers=args.max_workers, rate_limit=args.rate_limit_seconds, timeout=args.timeout)
    pages_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in initial + second:
        page.pop("_body", None)
        pages_by_id[page.get("company_id")].append(page)
    updated: dict[str, dict[str, Any]] = {}
    audit_sources: list[dict[str, Any]] = []
    errors_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for company in targets:
        cid = company["company_id"]
        pages = pages_by_id.get(cid, [])
        for page in pages:
            audit_sources.append({key: value for key, value in page.items() if key != "_body"})
            if not page.get("status"):
                errors_by_id[cid].append({"stage": page.get("kind"), "url": page.get("requested_url"), "error": page.get("error") or "No HTTP status", "classification": "SOURCE_TIMEOUT" if "timed out" in str(page.get("error", "")).lower() else "SOURCE_ERROR"})
        audited = audit_company(company, pages)
        apply_evidence_package(audited, pages, errors_by_id.get(cid, []))
        updated[cid] = audited
    output = [updated.get(company.get("company_id"), company) for company in all_companies]
    write_jsonl(path_for("data", "normalized", "companies.jsonl"), output)
    write_jsonl(path_for("data", "raw", "commercial_audit_sources.jsonl"), audit_sources)
    summary = {
        "completed_at": now_iso(), "audit_version": AUDIT_VERSION, "target_companies": len(targets), "initial_tasks": len(tasks), "followup_tasks": len(followups),
        "pages_ok": sum(1 for page in initial + second if page.get("status")), "pages_failed": sum(1 for page in initial + second if not page.get("status")),
        "companies_with_usable_pages": sum(1 for company in targets if any(page_matches_company(company, page) for page in pages_by_id.get(company["company_id"], []))),
        "independent_source_count_distribution": dict(Counter(updated[cid].get("independent_source_count") for cid in updated)),
        "readiness_counts": dict(Counter(updated[cid].get("sales_readiness") for cid in updated)),
        "tier_counts": dict(Counter(updated[cid].get("priority_tier") for cid in updated)),
        "classification_counts": dict(Counter(updated[cid].get("company_type") for cid in updated)),
        "workflow_classification_counts": dict(Counter(updated[cid].get("workflow_evidence_classification") for cid in updated)),
        "proxy": args.proxy, "visible_browser_launched": False, "headless_browser_tasks": 0,
        "failed_sources": sum(len(value) for value in errors_by_id.values()),
    }
    write_json(path_for("logs", f"commercial-audit-{now_iso().replace(':', '').replace('-', '')}.json"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
