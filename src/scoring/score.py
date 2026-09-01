from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from typing import Any

from src.utilities.common import domain_of, normalize_persian, now_iso, path_for, read_jsonl, stable_hash, write_json, write_jsonl


WEIGHTS = {
    "company_strength_score": 12,
    "operational_complexity_score": 12,
    "workflow_density_score": 10,
    "ai_roi_score": 16,
    "data_readiness_score": 10,
    "digital_maturity_fit_score": 12,
    "outsourcing_fit_score": 8,
    "sales_access_score": 6,
    "expected_project_value_score": 5,
    "implementation_score": 4,
    "sales_cycle_ease_score": 3,
    "regulatory_score": 2,
}


INDUSTRY_BASE = {
    "industrial_distributors_importers": {"complexity": 70, "density": 75, "roi": 78, "project": 72, "sales": 72, "regulatory": 82},
    "industrial_manufacturers": {"complexity": 78, "density": 72, "roi": 80, "project": 82, "sales": 62, "regulatory": 78},
    "food_fmcg": {"complexity": 76, "density": 82, "roi": 80, "project": 75, "sales": 68, "regulatory": 70},
    "logistics_freight_customs": {"complexity": 76, "density": 82, "roi": 84, "project": 74, "sales": 68, "regulatory": 62},
    "printing_packaging_labeling": {"complexity": 70, "density": 76, "roi": 78, "project": 68, "sales": 72, "regulatory": 82},
    "medical_equipment": {"complexity": 74, "density": 76, "roi": 79, "project": 72, "sales": 60, "regulatory": 56},
    "auto_parts": {"complexity": 78, "density": 80, "roi": 82, "project": 76, "sales": 64, "regulatory": 76},
    "epc_engineering_contractors": {"complexity": 82, "density": 78, "roi": 79, "project": 84, "sales": 55, "regulatory": 64},
    "building_materials_mep": {"complexity": 72, "density": 74, "roi": 76, "project": 70, "sales": 64, "regulatory": 78},
    "industrial_maintenance_after_sales": {"complexity": 73, "density": 80, "roi": 80, "project": 72, "sales": 66, "regulatory": 78},
    "pharma": {"complexity": 82, "density": 78, "roi": 78, "project": 86, "sales": 48, "regulatory": 40},
    "other": {"complexity": 38, "density": 40, "roi": 35, "project": 32, "sales": 52, "regulatory": 74},
}


ROLE_MAP = {
    "industrial_distributors_importers": ("Commercial Director / Sales Operations Manager", "CEO / Managing Director", "IT or ERP owner"),
    "industrial_manufacturers": ("Plant Manager / Operations Director", "CEO / COO", "IT or industrial-automation manager"),
    "food_fmcg": ("Distribution or Sales Operations Director", "CEO / COO", "IT / ERP owner"),
    "logistics_freight_customs": ("Operations Director", "CEO / COO", "TMS / compliance owner"),
    "printing_packaging_labeling": ("Estimating or Production Director", "Managing Director", "Finance / IT"),
    "medical_equipment": ("Commercial / Tender Director", "CEO / Managing Director", "Regulatory / technical / IT"),
    "auto_parts": ("Commercial or Operations Director", "CEO / Managing Director", "IT / ERP owner"),
    "epc_engineering_contractors": ("Contracts / Tender / Project Controls Director", "CEO / COO", "Document control / IT security"),
    "building_materials_mep": ("Project Sales / Technical Office Director", "CEO / Commercial Director", "IT / Finance"),
    "industrial_maintenance_after_sales": ("Service Director / Maintenance Manager", "CEO / COO", "IT / field-service owner"),
    "pharma": ("QA / Supply / Operations Director", "CEO / COO", "QA validation / IT / regulatory"),
    "other": ("Operations or Commercial Manager", "CEO / Managing Director", "IT / finance"),
}


DISCOVERY_ARTIFACT_TERMS = [
    "بانک اطلاعات",
    "لیست شرکت",
    "فهرست شرکت",
    "لیست کارخانجات",
    "کارخانجات و واحدهای تولیدی",
    "دایرکتوری شرکت",
    "پایگاه صنعت",
    "صنعت مپ",
    "شهرک صنعتی شمس آباد",
    "صفحه شرکت ها",
]


INDUSTRY_LABELS_FA = {
    "industrial_distributors_importers": "توزیع‌کننده و واردکننده صنعتی",
    "industrial_manufacturers": "تولیدکننده صنعتی",
    "food_fmcg": "غذا و کالاهای تندمصرف",
    "logistics_freight_customs": "حمل‌ونقل، فورواردری و ترخیص",
    "printing_packaging_labeling": "چاپ، بسته‌بندی و لیبل",
    "medical_equipment": "تجهیزات پزشکی و آزمایشگاهی",
    "auto_parts": "قطعات خودرو",
    "epc_engineering_contractors": "EPC و پیمانکاری مهندسی",
    "building_materials_mep": "مصالح ساختمانی و تاسیسات",
    "industrial_maintenance_after_sales": "نگهداری صنعتی و خدمات پس از فروش",
    "pharma": "دارویی",
    "other": "سایر",
}


NON_CORPORATE_SITE_DOMAINS = {
    "rubika.ir", "aparat.com", "instagram.com", "facebook.com", "linkedin.com",
    "youtube.com", "telegram.me", "t.me", "x.com", "twitter.com",
}
UNRELATED_SITE_MARKERS = {"cannabis", "dispensary", "weed", "casino", "betting"}


def _contains(text: str, terms: list[str]) -> bool:
    return any(normalize_persian(term) in text for term in terms)


def sanitize_public_website(company: dict[str, Any]) -> None:
    """Do not let a social/profile landing page count as a corporate website."""
    domain = domain_of(company.get("website"))
    site = company.get("website_enrichment") or {}
    site_text = normalize_persian(site.get("text_excerpt"))[:10000]
    social_page = domain and (domain in NON_CORPORATE_SITE_DOMAINS or any(domain.endswith("." + item) for item in NON_CORPORATE_SITE_DOMAINS))
    unrelated_page = domain and any(marker in site_text for marker in UNRELATED_SITE_MARKERS)
    if social_page or unrelated_page:
        company["non_corporate_public_url"] = company.get("website")
        if social_page:
            site["qualification_excluded"] = True
        if unrelated_page:
            company["website_quality_issue"] = "UNRELATED_PUBLIC_SITE_CONTENT"
            site["qualification_excluded"] = True
        company["website"] = None
        company["domain"] = None
        company["website_status"] = "UNRELATED_PUBLIC_PAGE" if unrelated_page else "NON_CORPORATE_PUBLIC_PAGE"
        for evidence in company.get("evidence", []):
            if evidence.get("source_quality") == "company_site" and domain_of(evidence.get("source_url")) == domain:
                evidence["excluded_from_qualification"] = True


def reclassify_from_observed_evidence(company: dict[str, Any]) -> None:
    """Correct high-confidence directory/category errors without guessing from names alone."""
    original = company.get("original_industry") or company.get("industry") or "other"
    # Source-page titles are retained as rejected discovery artifacts. Their
    # category words must not be allowed to rewrite a company classification.
    if discovery_artifact_reason(company, normalize_persian(company.get("company_name_fa"))) is not None:
        return
    description = normalize_persian(company.get("description_observed"))
    sub_industry = normalize_persian(company.get("sub_industry"))
    site = company.get("website_enrichment") or {}
    site_title = normalize_persian(site.get("title"))
    # Navigation and directory pages frequently contain unrelated category
    # links. Use the description/title for corrections; keep body text as a
    # secondary signal only for explicit, distinctive phrases.
    site_text = normalize_persian(site.get("text_excerpt"))[:5000]
    focused = description_and_title = " ".join([description, site_title])
    category_text = sub_industry
    corrected = original
    reason = ""

    # A software vendor is a poor fit for custom delivery even when a directory
    # category such as accounting, warehouse or logistics was attached to it.
    software_vendor_terms = [
        "تولید کننده نرم افزار", "تولیدکننده نرم افزار", "نرم افزار حسابداری",
        "توسعه نرم افزار", "توسعه‌دهنده نرم افزار", "پلتفرم نرم افزاری",
        "نرم افزار فروشگاهی", "نرم افزار فروشگاهی و شرکتی", "حسابداری فروشگاهی و شرکتی",
        "تولیدکننده اپلیکیشن", "محصولات یکپارچه حسابداری", "سامانه مودیان",
        "software company", "accounting software",
    ]
    if _contains(focused, software_vendor_terms):
        corrected = "other"
        reason = "Explicit software-product/vendor language in the public description or website."
    elif _contains(focused, [
        "خدمات مالی", "مشاوره مالیاتی", "حسابداری حسابرسی", "حسابداری و حسابرسی",
        "financial & commercial firm", "financial accounting", "audit & control",
    ]):
        corrected = "other"
        reason = "Public website describes accounting, audit, tax or financial advisory services."
    elif _contains(focused, [
        "تجهیزات پزشکی", "تجهیزات آزمایشگاهی", "کیت های تشخیص", "medical equipment",
        "diagnostic kits",
    ]):
        corrected = "medical_equipment"
        reason = "Public product/site language identifies medical or diagnostic equipment."
    elif _contains(focused, [
        "داروسازی", "محصولات دارویی", "مواد اولیه دارویی", "pharmaceutical", "active pharmaceutical ingredient",
    ]):
        corrected = "pharma"
        reason = "Public product/site language identifies pharmaceutical products or API activity."
    elif _contains(focused, [
        "چاپ و بسته بندی", "چاپ و بسته‌بندی", "بسته بندی و چاپ", "بسته‌بندی و چاپ",
        "printing and packaging", "printing & packaging",
    ]):
        corrected = "printing_packaging_labeling"
        reason = "Public description/site explicitly identifies printing and packaging operations."
    elif _contains(focused, [
        "طراحی و ساخت ماشین آلات", "طراحی و ساخت ماشین‌آلات", "ساخت ماشین آلات",
        "ساخت ماشین‌آلات", "تولید ماشین آلات", "تولید ماشین‌آلات", "ماشین سازی", "ماشین‌سازی",
        "industrial machinery design",
    ]):
        corrected = "industrial_manufacturers"
        reason = "Public description/site explicitly identifies design or manufacture of industrial machinery."
    elif _contains(focused, [
        "صنایع غذایی", "تولید مواد غذایی", "محصولات غذایی", "پخش مویرگی",
        "food manufacturer", "food distribution",
    ]):
        corrected = "food_fmcg"
        reason = "Public description/site explicitly identifies food manufacturing or distribution."
    elif (
        original == "epc_engineering_contractors"
        and _contains(focused, ["شرکت بازرگانی", "تامین و تجهیز", "تامین، تولید و واردات", "تأمین و تجهیز"])
        and not _contains(focused, ["پیمانکار", "پیمانکاری", "خدمات مهندسی", "اجرا"])
    ):
        corrected = "industrial_distributors_importers"
        reason = "Public description identifies a trading/supply company rather than an engineering contractor."
    elif (
        _contains(focused, [
            "تامین کننده", "تامین‌کننده", "تأمین کننده", "تأمین‌کننده", "واردات و صادرات",
            "بازرگانی", "فروش عمده", "فروش ماشین آلات", "فروش ماشین‌آلات", "فروش بلبرینگ",
            "توزیع مواد اولیه", "تهیه و توزیع", "industrial supplier", "importer",
        ])
        or _contains(category_text, ["فروش ماشین آلات", "فروش ماشین‌آلات", "ابزار صنعتی"])
    ) and not _contains(focused, [
        "مواد غذایی", "صنایع غذایی", "محصولات غذایی", "food distribution", "پیمانکار",
        "پیمانکاری", "خدمات مهندسی", "تولیدکننده", "تولید کننده", "کارخانه تولید",
        "حمل و نقل", "حمل‌ونقل", "ترخیص", "فورواردر", "freight", "logistics",
        "قطعات خودرو", "لوازم یدکی", "خودرو", "شیرآلات", "مصالح ساختمانی", "فولاد", "آهن",
    ]):
        corrected = "industrial_distributors_importers"
        reason = "Public description/site emphasizes industrial supply, importing, wholesale or trading rather than manufacturing."
    elif _contains(focused, [
        "حمل و نقل بین المللی", "حمل‌ونقل بین‌المللی", "ترخیص کالا", "فورواردر",
        "freight forwarding", "customs clearance", "logistics company",
    ]):
        corrected = "logistics_freight_customs"
        reason = "Public description/site explicitly identifies freight, forwarding or customs operations."
    elif _contains(focused, [
        "قفسه فلزی", "قفسه بندی صنعتی", "قفسه‌بندی صنعتی", "سازه های فولادی انبار",
        "سازه‌های فولادی انبار",
    ]):
        corrected = "industrial_manufacturers"
        reason = "Public description/site identifies storage-rack or warehouse steel-system production."
    elif _contains(focused, [
        "نمایندگی رسمی خودرو", "تجارت خودرو", "نمایندگی محصولات خودرو", "automotive dealership",
    ]):
        corrected = "auto_parts"
        reason = "Public description/site identifies an established automotive dealership or distributor."
    elif (
        original == "auto_parts"
        and _contains(focused, ["توزیع مواد اولیه", "تهیه و توزیع مواد اولیه", "فولاد خوش تراش", "فولاد اتومات"])
    ):
        corrected = "industrial_distributors_importers"
        reason = "Public description/site identifies a steel/raw-material distributor serving industrial and automotive manufacturers."
    elif (
        original == "industrial_manufacturers"
        and (
            _contains(focused, ["نمایندگی انحصاری", "عرضه کننده و نمایندگی", "عرضه‌کننده و نمایندگی"])
            or normalize_persian(company.get("company_name_fa")) == normalize_persian("فروشگاه ماشین تراکتور")
        )
    ):
        corrected = "industrial_distributors_importers"
        reason = "Public description identifies an equipment representative/distributor, not a manufacturer."
    elif _contains(focused, [
        "قطعات خودرو", "لوازم یدکی", "automotive parts", "auto parts",
    ]):
        corrected = "auto_parts"
        reason = "Public description/site explicitly identifies automotive parts."
    elif _contains(focused, [
        "پیمانکار", "پیمانکاری", "خدمات مهندسی", "پروژه های مهندسی", "پروژه‌های مهندسی",
        "engineering contractor", "epc contractor",
    ]):
        corrected = "epc_engineering_contractors"
        reason = "Public description/site explicitly identifies EPC or engineering contracting."
    elif _contains(focused, [
        "شیرآلات صنعتی", "مصالح ساختمانی", "تجهیزات تاسیسات", "فروش آهن آلات", "فروش آهن‌آلات",
        "building materials", "steel products",
    ]):
        corrected = "building_materials_mep"
        reason = "Public description/site explicitly identifies building materials, steel or MEP products."
    elif _contains(focused, [
        "نگهداری و تعمیر", "تعمیرات صنعتی", "خدمات پس از فروش", "industrial maintenance",
        "after sales service",
    ]):
        corrected = "industrial_maintenance_after_sales"
        reason = "Public description/site explicitly identifies industrial maintenance or after-sales service."
    if corrected != original:
        company.setdefault("original_industry", original)
        company["industry"] = corrected
        company["industry_fa"] = INDUSTRY_LABELS_FA[corrected]
        company["industry_reclassification"] = {
            "from": original,
            "to": corrected,
            "reason": reason,
            "source_url": (site.get("final_url") or site.get("url") or next((item.get("source_url") for item in company.get("evidence", []) if item.get("source_url")), None)),
            "evidence_type": "OBSERVED",
        }
    else:
        company["industry"] = original
        company["industry_fa"] = INDUSTRY_LABELS_FA[original]
        company.pop("industry_reclassification", None)


WORKFLOWS = {
    "industrial_distributors_importers": {
        "workflow_name": "RFQ-to-quotation and SKU matching",
        "solution": "A Persian/English RFQ intake, catalog/SKU matcher and draft-quotation workflow with deterministic pricing rules and human approval.",
        "users": "Sales coordinators, product specialists and Commercial Director",
        "data": "Product master, specifications, price lists, stock snapshots, historical RFQs/quotes and approval rules",
        "integrations": "ERP/accounting exports or API, CRM, email/forms and approved document intake",
        "kpis": ["median quote turnaround", "RFQs handled per salesperson", "correction rate", "follow-up completion"],
        "questions": ["How many RFQs arrive each month and through which channels?", "Where do sales staff check specification, price and stock today?", "Which approval and margin rules must remain deterministic?"],
    },
    "industrial_manufacturers": {
        "workflow_name": "Production and quality reporting assistant",
        "solution": "A controlled capture and reporting layer that normalizes shift/quality documents, surfaces exceptions and retrieves SOP or maintenance evidence for human review.",
        "users": "Plant manager, planning, QA/QC and maintenance teams",
        "data": "Shift reports, production orders, QC records, downtime logs, SOPs and ERP/Excel exports",
        "integrations": "ERP/MES exports, shared folders, forms and management reporting",
        "kpis": ["report preparation hours", "exception detection latency", "rework/scrap cases", "document retrieval time"],
        "questions": ["How are shift and QC reports consolidated today?", "Which exceptions require the plant manager's attention first?", "What historical production and maintenance data can be exported?"],
    },
    "food_fmcg": {
        "workflow_name": "Order intake and inventory exception workflow",
        "solution": "A structured order/return intake and exception dashboard that consolidates sales, distributor and inventory records without replacing the distribution core.",
        "users": "Sales operations, distribution, supply chain and COO",
        "data": "Order lines, returns, inventory snapshots, customers, promotions, routes and receivables",
        "integrations": "Distribution ERP, approved email/message exports, warehouse and branch reports",
        "kpis": ["order-entry time", "stock-out exceptions", "return/expiry value", "manual reporting hours"],
        "questions": ["Which order channels still require re-keying or manual correction?", "How are substitutions, returns and credit exceptions reported?", "What data is available by SKU, warehouse and route?"],
    },
    "logistics_freight_customs": {
        "workflow_name": "Shipment document intake and exception queue",
        "solution": "Document classification/extraction with completeness checks and an operator exception queue for invoices, packing lists, bills and status updates.",
        "users": "Documentation operators, freight operations and customer service",
        "data": "Invoices, packing lists, bills of lading, shipment milestones, rate requests and customer records",
        "integrations": "Email/file intake, TMS/ERP exports and approved customer status channels",
        "kpis": ["minutes per document", "correction rate", "missing-document delay", "shipments per operator"],
        "questions": ["Which document types create the most re-keying?", "Where are shipment milestones and missing documents tracked?", "Which fields require mandatory human verification?"],
    },
    "printing_packaging_labeling": {
        "workflow_name": "Job brief, estimate and approval workflow",
        "solution": "A structured job-brief extractor and similar-job retrieval tool that supports explainable estimating and tracks artwork/specification approvals.",
        "users": "Sales, estimating, prepress and production planning",
        "data": "Customer briefs, artwork/specifications, prior jobs, material/machine rules and capacity",
        "integrations": "File intake, estimating spreadsheets, production planning and approval records",
        "kpis": ["quote turnaround", "revision cycles", "estimator throughput", "jobs delayed by missing specifications"],
        "questions": ["Which job inputs are most often missing or revised?", "Which cost rules must stay deterministic?", "How are approved artwork versions handed to production?"],
    },
    "medical_equipment": {
        "workflow_name": "Technical tender and product-dossier assistant",
        "solution": "A permissioned tender/specification matcher that retrieves cited evidence from approved catalogs and dossiers, drafts a response pack and keeps technical approval with staff.",
        "users": "Tender, commercial, technical and regulatory teams",
        "data": "Tender PDFs, product catalogs, manuals, certificates, service records and price lists",
        "integrations": "Document repository, CRM/ERP exports and controlled quotation workflow",
        "kpis": ["tender preparation hours", "requirements checked", "missing-file rate", "quote turnaround"],
        "questions": ["How many tenders/RFQs are reviewed monthly?", "Which catalog and regulatory files are authoritative?", "Where must regulatory or technical approval occur?"],
    },
    "auto_parts": {
        "workflow_name": "Parts knowledge, cross-reference and quotation",
        "solution": "A catalog and compatibility assistant that maps customer descriptions or part numbers to candidate SKUs, stock and price for salesperson confirmation.",
        "users": "Commercial, warehouse and customer-service teams",
        "data": "SKU/part master, OEM cross-references, compatibility notes, stock, price and return history",
        "integrations": "ERP/WMS exports, catalog files and CRM/order workflow",
        "kpis": ["part-search time", "wrong-part corrections/returns", "quote turnaround", "orders per salesperson"],
        "questions": ["Which descriptions or part numbers are hardest to match?", "How often do wrong-part returns occur?", "Which stock and price source is authoritative?"],
    },
    "epc_engineering_contractors": {
        "workflow_name": "Tender, BOQ and contract-obligation search",
        "solution": "A secure tender room and evidence-linked search that extracts requirements, records obligations and assembles project correspondence for human review.",
        "users": "Tender, contracts, project controls and document-control teams",
        "data": "Tender packs, BOQs, contracts, RFIs, submittals, minutes, schedules and prior bids",
        "integrations": "DMS/shared drives, project folders and reporting exports",
        "kpis": ["bid-review hours", "requirements missed", "RFI turnaround", "evidence-assembly time"],
        "questions": ["Which document sets are most difficult to search or version?", "How are deadlines and obligations tracked?", "What access-control and local-deployment rules apply?"],
    },
    "building_materials_mep": {
        "workflow_name": "BOQ/specification-to-product matching",
        "solution": "A product/specification matcher that structures BOQ lines, retrieves technical evidence and prepares a versioned submittal or quotation pack for approval.",
        "users": "Project sales, technical office and commercial management",
        "data": "BOQs, drawings/specifications, product catalogs, price lists, alternatives and prior submittals",
        "integrations": "Document repository, CRM/ERP exports and quote approval",
        "kpis": ["lines matched per hour", "submittal turnaround", "revision errors", "follow-up coverage"],
        "questions": ["Which BOQ/specification formats arrive most often?", "How are compliant alternatives selected?", "Which technical approvals are mandatory?"],
    },
    "industrial_maintenance_after_sales": {
        "workflow_name": "Service-ticket and maintenance knowledge assistant",
        "solution": "A structured ticket intake and permissioned manual/history search that helps dispatch and technicians draft service records with human sign-off.",
        "users": "Service manager, dispatchers and field technicians",
        "data": "Service tickets, asset list, manuals, work orders, parts and warranty records",
        "integrations": "CRM/field-service exports, shared manuals and inventory",
        "kpis": ["first-response time", "report preparation time", "repeat incidents", "first-time-fix support"],
        "questions": ["How are calls converted into tickets and assignments?", "Where are manuals and service history stored?", "Which recommendations must remain advisory?"],
    },
    "pharma": {
        "workflow_name": "Controlled regulatory and SOP knowledge workflow",
        "solution": "A permissioned, citation-first document search and expiry/exception workflow for QA, regulatory and supply teams; no autonomous clinical or compliance decisions.",
        "users": "QA, regulatory, supply and operations teams",
        "data": "SOPs, certificates, batch/expiry records, deviations, CAPA and approved dossiers",
        "integrations": "DMS/ERP exports and approval/audit workflow",
        "kpis": ["document retrieval time", "expired/missing-file exceptions", "review hours", "overdue actions"],
        "questions": ["Which documents are authoritative and version-controlled?", "What review/audit trail is required?", "Which decisions must remain entirely human?"],
    },
    "other": {
        "workflow_name": "Operations reporting and internal knowledge discovery",
        "solution": "A bounded reporting/search assistant that structures public operating documents and identifies one process to validate in discovery.",
        "users": "Operations and commercial management",
        "data": "Public catalogs, forms, reports and approved internal exports",
        "integrations": "Existing file stores and business-system exports",
        "kpis": ["report preparation time", "document retrieval time", "manual handoffs", "exception closure"],
        "questions": ["Which recurring process consumes the most staff time?", "What data and documents are available?", "Who owns the KPI and can approve a pilot?"],
    },
}


def text_for(company: dict[str, Any]) -> str:
    pieces = [company.get("company_name_fa"), company.get("description_observed"), company.get("sub_industry"), company.get("industry_fa"), company.get("hq_address"), company.get("domain")]
    for source in company.get("source_records", []):
        pieces.extend([source.get("source_title"), source.get("evidence_snippet"), source.get("discovery_reason")])
    site = company.get("website_enrichment") or {}
    if not site.get("qualification_excluded"):
        pieces.extend([site.get("title"), site.get("text_excerpt")])
    return normalize_persian(" ".join(str(piece) for piece in pieces if piece))


def has_any(text: str, terms: list[str]) -> bool:
    return any(normalize_persian(term) in text for term in terms)


def usable_corporate_website(company: dict[str, Any]) -> bool:
    domain = domain_of(company.get("website"))
    status = str(company.get("website_status", ""))
    return bool(domain and status.isdigit() and 200 <= int(status) < 400 and domain not in NON_CORPORATE_SITE_DOMAINS)


def discovery_artifact_reason(company: dict[str, Any], text: str) -> str | None:
    name = normalize_persian(company.get("company_name_fa"))
    # Search/official anchor text can be a source page rather than a company.
    # Keep it in the discovered universe for auditability, but prevent it from
    # becoming a prospect or receiving a proposal.
    if any(normalize_persian(term) in name for term in DISCOVERY_ARTIFACT_TERMS):
        return "DISCOVERY_ARTIFACT_TITLE"
    source_types = {record.get("source_type") for record in company.get("source_records", [])}
    if source_types and source_types <= {"search", "official_reference"} and has_any(text, DISCOVERY_ARTIFACT_TERMS):
        return "DISCOVERY_ARTIFACT_SOURCE_ONLY"
    return None


def clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def digital_scores(company: dict[str, Any], text: str) -> tuple[int, int]:
    site = company.get("website_enrichment") or {}
    website_ok = usable_corporate_website(company)
    if not website_ok and not company.get("website"):
        maturity = 25 if company.get("description_observed") else 10
    else:
        maturity = 38
    signals = {} if site.get("qualification_excluded") else (site.get("signals") or {})
    if signals.get("software_or_erp"):
        maturity += 17
    if signals.get("catalog_or_products"):
        maturity += 7
    if signals.get("order_or_contact_form") or signals.get("rfq_or_quote"):
        maturity += 4
    if signals.get("branches_or_dealers"):
        maturity += 3
    if has_any(text, ["api", "پرتال مشتری", "پنل کاربری", "سفارش آنلاین", "online order", "developer", "پلتفرم"]):
        maturity += 12
    if has_any(text, ["هوش مصنوعی", "یادگیری ماشین", "دانشمند داده", "تیم نرم افزار", "تیم نرم‌افزار", "اپلیکیشن"]):
        maturity += 15
    maturity = clamp(maturity)
    fit = clamp(100 * math.exp(-((maturity - 55) / 24) ** 2))
    return maturity, fit


def score_company(company: dict[str, Any]) -> dict[str, Any]:
    sanitize_public_website(company)
    reclassify_from_observed_evidence(company)
    text = text_for(company)
    artifact_reason = discovery_artifact_reason(company, text)
    industry = company.get("industry") or "other"
    base = INDUSTRY_BASE.get(industry, INDUSTRY_BASE["other"])
    source_records = company.get("source_records", [])
    source_types = {item.get("source_type") for item in source_records if item.get("source_type")}
    evidence_count = len([item for item in company.get("evidence", []) if not item.get("excluded_from_qualification")])
    public_phone = bool(company.get("phone_public"))
    address = bool(company.get("hq_address"))
    description = bool(company.get("description_observed"))
    website = usable_corporate_website(company)
    facility = has_any(text, ["کارخانه", "کارخانجات", "انبار", "شهرک صنعتی", "خط تولید", "warehouse", "factory", "production"])
    network = has_any(text, ["شعب", "نمایندگان", "نمایندگی", "دفاتر", "سراسر کشور", "dealer", "branches"])
    catalog = has_any(text, ["کاتالوگ", "محصولات", "محصول", "catalog", "products", "sku", ".pdf"])
    workflow = has_any(text, ["استعلام", "پیش فاکتور", "مناقصه", "قرارداد", "سفارش", "خدمات پس از فروش", "ترخیص", "بارنامه", "تولید", "گزارش", "نمایندگان", "warehouse", "tender"])
    certificates = has_any(text, ["iso", "گواهینامه", "استاندارد", "مجوز", "certificate"])
    projects = has_any(text, ["پروژه", "مشتریان", "client", "projects"])
    tech_negative = has_any(text, ["هوش مصنوعی", "یادگیری ماشین", "دانشمند داده", "برنامه نویس", "برنامه‌نویس", "پایتون", "backend", "frontend", "نرم افزار", "نرم‌افزار", "پلتفرم نرم افزاری"])
    micro = has_any(text, ["فروشگاه", "مغازه", "سوپرمارکت", "کلینیک", "مطب", "کارگاه کوچک"])
    government = has_any(text, ["وزارت", "دولتی", "شهرداری", "بانک مرکزی", "دانشگاه دولتی"])
    software_vendor_signal = industry == "other" and _contains(" ".join([
        normalize_persian(company.get("description_observed")),
        normalize_persian((company.get("website_enrichment") or {}).get("title")),
        normalize_persian((company.get("website_enrichment") or {}).get("text_excerpt"))[:3500],
    ]), [
        "تولید کننده نرم افزار", "تولیدکننده نرم افزار", "نرم افزار حسابداری",
        "توسعه نرم افزار", "نرم افزار فروشگاهی", "software company", "accounting software",
    ])
    digital_maturity, maturity_fit = digital_scores(company, text)
    internal_capability = 20
    if tech_negative:
        internal_capability += 38
    if has_any(text, ["هوش مصنوعی", "یادگیری ماشین", "دانشمند داده", "mlops", "تیم داده"]):
        internal_capability += 30
    if industry == "other" and has_any(text, ["نرم افزار", "نرم‌افزار", "اپلیکیشن", "پلتفرم"]):
        internal_capability += 25
    internal_capability = clamp(internal_capability)
    outsourcing_fit = clamp(100 - internal_capability)

    strength = 32
    strength += 12 if description else 0
    strength += 10 if address else 0
    strength += 9 if public_phone else 0
    strength += min(10, len(source_records) * 3)
    strength += min(8, max(0, company.get("raw_record_count", 0) - 1) * 3)
    strength += 8 if website else 0
    strength += 6 if facility else 0
    strength += 5 if network else 0
    strength += 4 if certificates else 0
    strength += 4 if projects else 0
    strength = clamp(strength)

    complexity = base["complexity"]
    complexity += 7 if facility else 0
    complexity += 6 if network else 0
    complexity += 5 if catalog else 0
    complexity += 4 if workflow else 0
    complexity += 4 if projects else 0
    complexity = clamp(complexity)

    density = base["density"] + (8 if workflow else 0) + (5 if catalog else 0) + (4 if facility else 0) + (3 if network else 0)
    density = clamp(density)
    roi = base["roi"] + (6 if workflow and catalog else 0) + (4 if facility else 0) + (3 if network else 0) - (10 if not description else 0)
    roi = clamp(roi)
    data_ready = 26 + (18 if description else 0) + (12 if catalog else 0) + (10 if website else 0) + (8 if evidence_count else 0) + (8 if has_any(text, ["erp", "crm", "راهکاران", "همکاران سیستم", "اکسل", "excel"]) else 0) + min(10, len(source_records) * 2)
    data_ready = clamp(data_ready)
    access = 18 + (30 if public_phone else 0) + (18 if address else 0) + (12 if website else 0) + (10 if source_records else 0) + (8 if company.get("social_profiles") else 0)
    access = clamp(access)
    project = base["project"] + (6 if facility or network else 0) + (5 if catalog else 0) + (4 if description else 0)
    project = clamp(project)
    implementation = 38 + (16 if data_ready >= 55 else 0) + (12 if description else 0) + (8 if website else 0) + (6 if not government else 0) - (10 if industry in {"pharma", "medical_equipment"} else 0)
    implementation = clamp(implementation)
    sales_ease = base["sales"] - (15 if government else 0) - (8 if industry in {"pharma", "medical_equipment", "epc_engineering_contractors"} else 0) + (6 if public_phone else 0)
    sales_ease = clamp(sales_ease)
    regulatory = base["regulatory"] - (14 if government else 0)
    regulatory = clamp(regulatory)

    capability_gap = outsourcing_fit
    components = {
        "company_strength_score": strength,
        "operational_complexity_score": complexity,
        "workflow_density_score": density,
        "ai_roi_score": roi,
        "data_readiness_score": data_ready,
        "digital_maturity_score": digital_maturity,
        "digital_maturity_fit_score": maturity_fit,
        "internal_tech_capability_score": internal_capability,
        "outsourcing_fit_score": capability_gap,
        "sales_access_score": access,
        "expected_project_value_score": project,
        "implementation_score": implementation,
        "sales_cycle_ease_score": sales_ease,
        "regulatory_score": regulatory,
    }
    formula = (
        12 * strength / 100 + 12 * complexity / 100 + 10 * density / 100 + 16 * roi / 100 + 10 * data_ready / 100
        + 12 * maturity_fit / 100 + 8 * capability_gap / 100 + 6 * access / 100 + 5 * project / 100
        + 4 * implementation / 100 + 3 * sales_ease / 100 + 2 * regulatory / 100
    )
    trigger_bonus = 0
    trigger_terms = []
    if has_any(text, ["erp", "crm", "راهکاران", "همکاران سیستم", "سپیدار"]):
        trigger_bonus += 2; trigger_terms.append("existing business system signal")
    if has_any(text, ["توسعه", "افتتاح", "گسترش", "خط تولید جدید", "new branch"]):
        trigger_bonus += 1; trigger_terms.append("expansion signal")
    if has_any(text, ["استخدام", "استخدامی", "جذب نیرو"]):
        trigger_bonus += 1; trigger_terms.append("hiring signal")
    if has_any(text, ["مناقصه", "نمایندگی جدید", "محصول جدید", "قرارداد جدید"]):
        trigger_bonus += 1; trigger_terms.append("deal/tender signal")
    trigger_bonus = min(5, trigger_bonus)
    risk_penalty = 0
    risk_reasons: list[str] = []
    if micro and not facility and not network:
        risk_penalty += 12; risk_reasons.append("possible_micro_business")
    if government:
        risk_penalty += 8; risk_reasons.append("government_or_public_exposure")
    if not description:
        risk_penalty += 8; risk_reasons.append("thin_public_description")
    if not data_ready >= 45:
        risk_penalty += 7; risk_reasons.append("limited_usable_public_data")
    if tech_negative and internal_capability >= 65:
        risk_penalty += 12; risk_reasons.append("internal_tech_signal")
    thin_public_record = (
        not public_phone
        and not website
        and company.get("research_status") != "MEANINGFULLY_ENRICHED"
        and len(source_types) <= 1
    )
    if thin_public_record:
        risk_penalty += 10
        risk_reasons.append("thin_public_record_requires_enrichment")
    risk_penalty = min(25, risk_penalty)
    final = clamp(formula + trigger_bonus - risk_penalty)
    # An industrial-estate row is useful discovery evidence, not proof of an
    # established, reachable buyer. Keep it in the database but require a
    # second source or public contact before it can score as B/A.
    if thin_public_record:
        final = min(final, 66)

    hard_reject = None
    if artifact_reason:
        hard_reject = artifact_reason
    elif government:
        hard_reject = "PUBLIC_OR_GOVERNMENT_EXPOSURE"
    elif software_vendor_signal:
        hard_reject = "SOFTWARE_VENDOR_OR_DIGITAL_NATIVE"
    elif tech_negative and internal_capability >= 85:
        hard_reject = "STRONG_INTERNAL_TECH_SIGNAL"
    elif not address and not public_phone and not website:
        hard_reject = "NO_CREDIBLE_PUBLIC_FOOTPRINT"
    elif micro and not facility and not network and strength < 55:
        hard_reject = "LIKELY_MICRO_BUSINESS"
    tier = "Reject" if hard_reject or final < 45 else "D" if final < 60 else "C" if final < 70 else "B" if final < 80 else "A"
    workflow_spec = WORKFLOWS.get(industry, WORKFLOWS["other"])
    evidence_urls = [item.get("source_url") for item in company.get("evidence", []) if item.get("source_url") and not item.get("excluded_from_qualification")]
    evidence_urls += [item.get("source_url") for item in source_records if item.get("source_url")]
    evidence_urls = list(dict.fromkeys(evidence_urls))[:12]
    observed = []
    if description:
        observed.append({"claim": "Public listing provides a business description.", "evidence_type": "OBSERVED", "source_url": evidence_urls[0] if evidence_urls else None, "confidence": 0.78})
    if address:
        observed.append({"claim": "Public listing provides a Tehran-area address.", "evidence_type": "OBSERVED", "source_url": evidence_urls[0] if evidence_urls else None, "confidence": 0.86})
    if public_phone:
        observed.append({"claim": "A public landline is listed.", "evidence_type": "OBSERVED", "source_url": evidence_urls[0] if evidence_urls else None, "confidence": 0.84})
    if facility or network or catalog or workflow:
        observed.append({"claim": "Public description/category contains operational or product-workflow signals.", "evidence_type": "OBSERVED", "source_url": evidence_urls[0] if evidence_urls else None, "confidence": 0.68})
    workflow_confidence = "High" if len(observed) >= 4 and website else "Medium" if len(observed) >= 3 else "Low"
    workflow = {
        "workflow_id": "wf-" + stable_hash(company["company_id"], workflow_spec["workflow_name"]),
        "company_id": company["company_id"],
        "department": workflow_spec["users"],
        "workflow_name": workflow_spec["workflow_name"],
        "current_process_hypothesis": "Public evidence shows a relevant product, service, facility or document context; the current internal handoff is a hypothesis requiring process validation.",
        "supporting_evidence": observed[:6],
        "current_problem": "Potential repeated lookup, intake, reporting or document handoff; not asserted as an observed internal failure.",
        "proposed_luma_solution": workflow_spec["solution"],
        "primary_users": workflow_spec["users"],
        "likely_business_owner": ROLE_MAP.get(industry, ROLE_MAP["other"])[0],
        "required_data": [workflow_spec["data"]],
        "required_integrations": [workflow_spec["integrations"]],
        "implementation_complexity": "Medium" if implementation >= 60 else "High",
        "implementation_risks": ["public sources cannot establish volume or data quality", "integration and permissions require discovery", "human approval remains required"],
        "measurable_KPIs": workflow_spec["kpis"],
        "confidence": workflow_confidence,
        "confidence_score": round(min(0.95, 0.35 + len(observed) * 0.12 + (0.1 if website else 0)), 2),
        "discovery_questions": workflow_spec["questions"],
    }
    company.update(components)
    company.update({
        "score_version": "2026.09.evidence-first-v1",
        "score_date": now_iso(),
        "capability_gap_score": capability_gap,
        "trigger_bonus": trigger_bonus,
        "trigger_signals": trigger_terms,
        "risk_penalty": risk_penalty,
        "risk_reasons": risk_reasons,
        "hard_disqualifier": hard_reject,
        "discovery_artifact": artifact_reason,
        "luma_opportunity_score": final,
        "priority_tier": tier,
        "score_confidence": round(min(0.95, 0.30 + (0.08 if description else 0) + (0.08 if address else 0) + (0.08 if public_phone else 0) + (0.12 if website else 0) + min(0.20, len(source_types) * 0.05)), 2),
        "decision_maker_role": ROLE_MAP.get(industry, ROLE_MAP["other"])[0],
        "decision_maker_name_public": None,
        "decision_maker_source_url": evidence_urls[0] if evidence_urls else None,
        "decision_maker_confidence": 0.35 if evidence_urls else 0.0,
        "workflow_opportunities": [workflow],
        "evidence_urls": evidence_urls,
        "qualification_reason": " ".join([
            "Public Tehran-area business record with",
            "a described product/service context," if description else "limited public description,",
            "an address," if address else "no verified address,",
            "a public landline." if public_phone else "no public landline.",
        ]),
        "strongest_observed_evidence": [item.get("claim") for item in observed[:4]],
        "digital_maturity_interpretation": "Moderate/fragmented fit is favored; missing public digital signals remain UNKNOWN." if maturity_fit >= 60 else "Public evidence does not establish a moderate digital operating layer; validate before outreach.",
    })
    return company


def main() -> int:
    parser = argparse.ArgumentParser(description="Score normalized LUMA B2B company records")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    args = parser.parse_args()
    companies = [score_company(company) for company in read_jsonl(args.input)]
    write_jsonl(path_for("data", "normalized", "companies.jsonl"), companies)
    write_jsonl(path_for("data", "normalized", "workflows.jsonl"), [workflow for company in companies for workflow in company.get("workflow_opportunities", [])])
    write_jsonl(path_for("data", "normalized", "decision_makers.jsonl"), [{
        "company_id": c["company_id"], "decision_maker_role": c.get("decision_maker_role"), "decision_maker_name_public": c.get("decision_maker_name_public"), "source_url": c.get("decision_maker_source_url"), "confidence": c.get("decision_maker_confidence"),
    } for c in companies])
    write_jsonl(path_for("data", "normalized", "rejected.jsonl"), [c for c in companies if c.get("priority_tier") == "Reject"])
    write_json(path_for("data", "normalized", "score_explanation.json"), {"score_version": "2026.09.evidence-first-v1", "weights": WEIGHTS, "digital_maturity_formula": "exp(-((d-55)/24)^2)", "thresholds": {"A": ">=80", "B": "70-79", "C": "60-69", "D": "45-59", "Reject": "<45 or hard disqualifier"}, "notes": ["Public evidence cannot prove internal volume, budget or decision authority.", "Missing data lowers confidence and can incur a risk penalty.", "Digital maturity is scored separately from digital-maturity fit and peaks in the fragmented middle."]})
    summary = {
        "completed_at": now_iso(),
        "companies_scored": len(companies),
        "tier_counts": dict(Counter(c.get("priority_tier") for c in companies)),
        "industry_counts": dict(Counter(c.get("industry") for c in companies)),
        "score_distribution": {"min": min((c["luma_opportunity_score"] for c in companies), default=None), "max": max((c["luma_opportunity_score"] for c in companies), default=None), "median": sorted(c["luma_opportunity_score"] for c in companies)[len(companies)//2] if companies else None},
        "score_version": "2026.09.evidence-first-v1",
    }
    write_json(path_for("logs", f"scoring-{now_iso().replace(':', '').replace('-', '')}.json"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
