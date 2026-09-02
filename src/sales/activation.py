"""Deepen and package the existing READY FOR OUTREACH companies.

This module is deliberately bounded to the 32 records already marked READY by
the commercial audit.  It performs targeted public research through the
verified direct proxy, stores compact source/evidence records, then generates
human sales briefs, Persian client one-pagers, outreach drafts, visual indexes,
and a first-contact ranking.  It never submits a form or sends a message.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlencode, urlparse

from src.audit.commercial import (
    derive_page_signals,
    fetch_cached,
    independent_families,
    source_family as audit_source_family,
)
from src.discovery.run import parse_ddg
from src.utilities.common import (
    DEFAULT_PROXY,
    RateLimiter,
    canonical_url,
    clean_text,
    corporate_phones,
    domain_of,
    extract_emails,
    extract_links,
    filter_public_emails,
    html_to_text,
    now_iso,
    path_for,
    read_jsonl,
    stable_hash,
    write_json,
    write_jsonl,
)


ACTIVATION_VERSION = "2026.09.sales-activation-v1"
EXPECTED_READY = 32

FREE_EMAIL_DOMAINS = {
    "gmail.com", "gmail.co", "gmai.com", "yahoo.com", "yahoo.co.uk", "hotmail.com",
    "outlook.com", "live.com", "mail.com", "proton.me", "protonmail.com",
}
GENERIC_EMAIL_PREFIXES = {
    "info", "sales", "support", "contact", "office", "admin", "hello", "enquiries",
    "inquiry", "import", "export", "service", "services", "marketing", "hr", "jobs",
    "reception", "pm", "dm", "commercial", "salesoffice", "customerservice",
}
SEARCH_DOMAINS = {"html.duckduckgo.com", "duckduckgo.com", "www.bing.com", "bing.com", "google.com", "search.yahoo.com"}
AVVAL_DOMAINS = {"avval.ir"}
COMPANY_SOCIAL_DOMAINS = {"instagram.com", "facebook.com", "youtube.com", "telegram.me", "t.me", "x.com", "twitter.com"}

FAMILY_PRIORITY = {
    "official_registry": 1,
    "association_or_exhibition": 2,
    "job_portal": 3,
    "linkedin_public": 4,
    "public_news": 5,
    "industry_directory": 6,
    "map_listing": 7,
    "company_website": 8,
    "other_public": 9,
}

COUNTED_EXTERNAL_FAMILIES = {
    "official_registry", "association_or_exhibition", "job_portal", "linkedin_public",
    "public_news", "industry_directory", "map_listing", "industrial_estate_registry",
}

WORKFLOW_PROFILES: dict[str, dict[str, Any]] = {
    "rfq_quotation": {
        "name": "RFQ intake, product matching and draft quotation",
        "fa_name": "دریافت استعلام، تطبیق محصول و پیش‌نویس پیشنهاد قیمت",
        "business_owner": "Commercial Director / Sales Operations Manager",
        "primary_users": "Sales operations, product specialists and commercial management",
        "users_fa": "فروش، بازرگانی و کارشناسان فنی محصول",
        "solution": "A controlled intake workspace that structures incoming requests, matches them against the approved product/specification master, and prepares an explainable draft response for human approval.",
        "solution_fa": "یک میزکار کنترل‌شده برای ساختاردهی درخواست‌های ورودی، تطبیق آن‌ها با مرجع تأییدشده محصولات و مشخصات، و آماده‌سازی پیش‌نویس پاسخ برای تأیید انسانی.",
        "data": "RFQs, product/SKU master, specifications, price lists, stock snapshots, historical quotes and approval rules",
        "data_fa": "استعلام‌ها، مرجع محصول و SKU، مشخصات فنی، فهرست قیمت، تصویر موجودی، پیشنهادهای قبلی و قواعد تأیید",
        "integrations": "Approved email/form intake and exports or APIs from ERP, CRM or accounting systems if available",
        "integrations_fa": "ورودی ایمیل/فرم و در صورت وجود خروجی یا API سامانه‌های ERP، CRM یا حسابداری",
        "kpis": ["quote turnaround time", "RFQs handled per salesperson", "correction rate", "follow-up completion"],
        "kpis_fa": ["زمان پاسخ به استعلام", "تعداد استعلام قابل پردازش برای هر کارشناس", "نرخ اصلاح پیشنهاد", "تکمیل پیگیری"],
        "questions": [
            "در ماه چند درخواست قیمت وارد می‌شود و از چه کانال‌هایی؟",
            "امروز برای تطبیق مشخصات، قیمت و موجودی به کدام فایل یا سامانه رجوع می‌شود؟",
            "کدام قواعد قیمت‌گذاری و حاشیه سود باید کاملاً قطعی و انسانی باقی بماند؟",
            "برای شروع، پاسخ فنی، پیشنهاد محصول یا پیش‌فاکتور کدام خروجی ارزشمندتر است؟",
            "یک نمونه استعلام واقعی برای اندازه‌گیری زمان و میزان اصلاحات کدام است؟",
        ],
        "pilot_fa": "پایلوت پاسخ‌گویی ساختاریافته به استعلام‌ها",
        "demo_fa": "یک استعلام نمونه با چند مشخصه وارد می‌شود؛ سیستم محصولات/گزینه‌های منطبق را با منبع نشان می‌دهد، پیش‌نویس پاسخ می‌سازد و کارشناس آن را تأیید یا اصلاح می‌کند.",
    },
    "shipment_document_automation": {
        "name": "Shipment-document intake and exception tracking",
        "fa_name": "دریافت اسناد حمل و پیگیری نقص پرونده",
        "business_owner": "Operations Director / Customs Manager",
        "primary_users": "Operations, customs/compliance and customer-service teams",
        "users_fa": "عملیات، ترخیص/کنترل اسناد و خدمات مشتری",
        "solution": "A document intake layer that extracts shipment fields, checks a configurable completeness list, and routes exceptions to the responsible operator for approval.",
        "solution_fa": "یک لایه دریافت اسناد که اطلاعات پرونده حمل را ساختاریافته می‌کند، چک‌لیست کامل‌بودن را بررسی می‌کند و موارد ناقص را برای تأیید به مسئول مربوط ارجاع می‌دهد.",
        "data": "Bills of lading, invoices, packing lists, customs documents, milestones and customer instructions",
        "data_fa": "بارنامه، فاکتور، پکینگ‌لیست، اسناد گمرکی، نقاط پیشرفت و دستورهای مشتری",
        "integrations": "Shared folders, email intake, approved TMS/ERP exports and management reporting",
        "integrations_fa": "پوشه‌های مشترک، ورودی ایمیل، خروجی مجاز TMS/ERP و گزارش مدیریت",
        "kpis": ["document completeness", "exception closure time", "manual re-keying", "shipment-status response time"],
        "kpis_fa": ["کامل‌بودن پرونده", "زمان بستن نقص", "ورود دوباره اطلاعات", "زمان پاسخ‌گویی وضعیت محموله"],
        "questions": [
            "کدام اسناد حمل و ترخیص بیشترین حجم ورود و کنترل را دارند؟",
            "نقص هر پرونده چگونه به مسئول آن ارجاع و تا بسته‌شدن پیگیری می‌شود؟",
            "کدام داده‌ها بین ایمیل، اکسل و سامانه‌های مختلف دوباره وارد می‌شوند؟",
            "چه نقاطی نیازمند تأیید کارشناس گمرک یا مدیر عملیات هستند؟",
            "برای شروع، کدام نوع محموله یا مسیر کم‌ریسک‌تر است؟",
        ],
        "pilot_fa": "پایلوت کنترل کامل‌بودن پرونده‌های حمل",
        "demo_fa": "دو سند نمونه بارگذاری می‌شود؛ فیلدهای اصلی استخراج، موارد جاافتاده مشخص، و یک چک‌لیست قابل پیگیری برای کارشناس عملیات ساخته می‌شود.",
    },
    "boq_specification_matching": {
        "name": "BOQ/specification matching and technical submittal support",
        "fa_name": "تطبیق BOQ و مشخصات فنی برای پیشنهاد پروژه",
        "business_owner": "Technical Office / Project Sales Director",
        "primary_users": "Technical office, project sales, procurement and commercial management",
        "users_fa": "دفتر فنی، فروش پروژه، تأمین و مدیریت بازرگانی",
        "solution": "A document-grounded workspace that structures BOQ lines, retrieves approved technical evidence, and prepares a versioned submittal or quotation pack for review.",
        "solution_fa": "یک میزکار مبتنی بر اسناد که ردیف‌های BOQ را ساختاریافته می‌کند، مستندات فنی تأییدشده را بازیابی می‌کند و بسته نسخه‌بندی‌شده سابمیتال یا پیشنهاد قیمت را برای بازبینی آماده می‌کند.",
        "data": "BOQs, specifications, drawings, product catalogs, alternatives, certificates and prior submittals",
        "data_fa": "BOQ، مشخصات و نقشه‌ها، کاتالوگ محصول، گزینه‌های جایگزین، گواهی‌ها و سابمیتال‌های قبلی",
        "integrations": "Document repository, approved CRM/ERP exports, quotation workflow and approval records",
        "integrations_fa": "مخزن اسناد، خروجی مجاز CRM/ERP، گردش پیشنهاد قیمت و سوابق تأیید",
        "kpis": ["lines matched per hour", "submittal turnaround", "revision errors", "follow-up coverage"],
        "kpis_fa": ["تعداد ردیف تطبیق‌یافته در ساعت", "زمان آماده‌سازی سابمیتال", "خطاهای اصلاحی", "پوشش پیگیری پروژه"],
        "questions": [
            "BOQ و مشخصات فنی معمولاً با چه قالبی وارد می‌شوند؟",
            "تطبیق گزینه‌های مجاز و جایگزین توسط چه نقشی تأیید می‌شود؟",
            "کاتالوگ، دیتاشیت و گواهی فنی مرجع در کجا نگهداری می‌شود؟",
            "کدام بخش از سابمیتال باید نسخه‌بندی و قابل ردیابی باشد؟",
            "یک پروژه نمونه برای مقایسه زمان و خطا کدام است؟",
        ],
        "pilot_fa": "پایلوت تطبیق ردیف‌های BOQ با مستندات فنی",
        "demo_fa": "یک BOQ کوچک وارد می‌شود؛ ردیف‌ها استخراج، محصولات یا گزینه‌های کاندید با لینک مستندات نمایش، و بسته پیشنهادی برای بازبینی انسانی آماده می‌شود.",
    },
    "order_inventory_exceptions": {
        "name": "Order intake and inventory-exception reporting",
        "fa_name": "دریافت سفارش و گزارش استثناهای موجودی",
        "business_owner": "Distribution or Sales Operations Director",
        "primary_users": "Sales operations, distribution, supply chain and branch management",
        "users_fa": "عملیات فروش، پخش، زنجیره تأمین و مدیریت شعب/مراکز",
        "solution": "A structured intake and exception view that consolidates approved order, return and inventory records without replacing the distribution core.",
        "solution_fa": "یک لایه ساختاریافته برای دریافت و نمایش استثنا که سفارش، مرجوعی و موجودی تأییدشده را بدون جایگزین‌کردن هسته توزیع یکپارچه می‌کند.",
        "data": "Order lines, returns, inventory snapshots, customers, promotions, routes and receivables",
        "data_fa": "اقلام سفارش، مرجوعی، تصویر موجودی، مشتری، تخفیف، مسیر و مطالبات",
        "integrations": "Distribution ERP, branch/warehouse reports and approved email or message exports",
        "integrations_fa": "ERP پخش، گزارش شعب/انبار و خروجی مجاز ایمیل یا پیام‌رسان",
        "kpis": ["order-entry time", "stock-out exceptions", "return/expiry value", "manual reporting hours"],
        "kpis_fa": ["زمان ورود سفارش", "استثناهای کسری موجودی", "ارزش مرجوعی/انقضا", "ساعات گزارش‌سازی دستی"],
        "questions": [
            "سفارش‌ها از چه کانال‌هایی وارد می‌شوند و کجا دوباره‌کاری می‌شوند؟",
            "مرجع قطعی موجودی و قیمت برای تیم فروش کدام است؟",
            "کسری، مرجوعی یا تاریخ انقضا چگونه گزارش و پیگیری می‌شود؟",
            "گزارش روزانه یا هفتگی مدیریت چه فیلدهایی دارد؟",
            "آیا انبار، شعب یا نمایندگان خروجی استاندارد قابل اتصال دارند؟",
        ],
        "pilot_fa": "پایلوت داشبورد استثناهای سفارش و موجودی",
        "demo_fa": "یک فایل سفارش و تصویر موجودی نمونه وارد می‌شود؛ موارد کسری/تعارض جدا، خلاصه مدیریتی تولید، و نقاط تأیید انسانی مشخص می‌شوند.",
    },
    "production_quality_reporting": {
        "name": "Production, quality and downtime reporting",
        "fa_name": "گزارش تولید، کیفیت و توقفات",
        "business_owner": "Plant Manager / Operations Director",
        "primary_users": "Plant management, production planning, QA/QC and maintenance teams",
        "users_fa": "مدیریت کارخانه، برنامه‌ریزی تولید، QA/QC و نگهداری",
        "solution": "A controlled reporting layer that normalizes shift, quality and downtime records, surfaces exceptions and links approved SOP or maintenance evidence for review.",
        "solution_fa": "یک لایه گزارش‌دهی کنترل‌شده که گزارش شیفت، کیفیت و توقف را استاندارد می‌کند، استثناها را نشان می‌دهد و مستندات تأییدشده SOP یا نگهداری را برای بازبینی پیوند می‌دهد.",
        "data": "Shift reports, production orders, QC records, downtime logs, SOPs and approved ERP exports",
        "data_fa": "گزارش شیفت، سفارش تولید، سوابق QC، لاگ توقف، SOP و خروجی مجاز ERP",
        "integrations": "Existing files, ERP/MES exports and management reporting; no core-system replacement in the pilot",
        "integrations_fa": "فایل‌های موجود، خروجی ERP/MES و گزارش مدیریت؛ در پایلوت هسته سامانه جایگزین نمی‌شود",
        "kpis": ["report completion time", "exception response time", "downtime categorization", "quality-record completeness"],
        "kpis_fa": ["زمان تکمیل گزارش", "زمان پاسخ به استثنا", "دقت دسته‌بندی توقف", "کامل‌بودن سوابق کیفیت"],
        "questions": [
            "گزارش‌های شیفت، کیفیت و توقف امروز در چه قالبی ثبت می‌شوند؟",
            "کدام استثنا باید همان روز به مدیر تولید یا QA برسد؟",
            "مرجع نسخه معتبر SOP و دستورالعمل نگهداری کجاست؟",
            "چه خروجی‌ای برای جلسه روزانه یا هفتگی مدیریت لازم است؟",
            "یک خط یا محصول کم‌ریسک برای شروع پایلوت کدام است؟",
        ],
        "pilot_fa": "پایلوت استانداردسازی گزارش‌های شیفت و کیفیت",
        "demo_fa": "سه گزارش نمونه شیفت/کیفیت کنار هم قرار می‌گیرد؛ داده‌های کلیدی استخراج، توقف‌های نیازمند توجه مشخص و گزارش خلاصه برای تأیید مدیر آماده می‌شود.",
    },
    "service_ticket_maintenance": {
        "name": "Service-ticket intake and maintenance knowledge",
        "fa_name": "ثبت درخواست سرویس و بازیابی دانش نگهداری",
        "business_owner": "Service Director / Maintenance Manager",
        "primary_users": "Service director, field technicians, maintenance and customer-support teams",
        "users_fa": "مدیریت خدمات، تکنسین‌های میدانی، نگهداری و پشتیبانی مشتری",
        "solution": "A controlled service workspace that structures requests, retrieves approved maintenance knowledge and prepares a human-reviewed service report.",
        "solution_fa": "یک میزکار کنترل‌شده خدمات که درخواست‌ها را ساختاریافته می‌کند، دانش نگهداری تأییدشده را بازیابی می‌کند و گزارش سرویس را برای بازبینی انسانی آماده می‌کند.",
        "data": "Service requests, equipment/serial records, manuals, prior interventions, parts and service reports",
        "data_fa": "درخواست خدمت، سوابق تجهیز/سریال، دفترچه‌ها، سوابق تعمیر، قطعات و گزارش‌های سرویس",
        "integrations": "CRM/ERP exports, service forms, shared documents and approved email or message intake",
        "integrations_fa": "خروجی CRM/ERP، فرم خدمات، اسناد مشترک و ورودی مجاز ایمیل یا پیام‌رسان",
        "kpis": ["first-response time", "repeat visits", "report completion time", "parts lookup time"],
        "kpis_fa": ["زمان پاسخ اول", "تعداد مراجعه تکراری", "زمان تکمیل گزارش", "زمان یافتن قطعه/راهنما"],
        "questions": [
            "درخواست خدمت چگونه ثبت، اولویت‌بندی و به تکنسین ارجاع می‌شود؟",
            "سوابق تجهیز، شماره سریال و تعمیرات قبلی در چه منبعی است؟",
            "تکنسین برای یافتن راهنمای معتبر یا قطعه مناسب چه مسیری دارد؟",
            "کدام گزارش‌های سرویس نیازمند تأیید مدیر یا مشتری هستند؟",
            "مهم‌ترین شاخص سرویس برای مدیریت چیست؟",
        ],
        "pilot_fa": "پایلوت ثبت و اولویت‌بندی درخواست‌های سرویس",
        "demo_fa": "یک درخواست سرویس و شماره تجهیز وارد می‌شود؛ سوابق و راهنمای مرتبط از مخزن تأییدشده پیشنهاد، موارد ناقص مشخص و گزارش اولیه برای تأیید ساخته می‌شود.",
    },
    "job_brief_estimate": {
        "name": "Job-brief extraction and estimating support",
        "fa_name": "استخراج بریف سفارش و پشتیبانی برآورد",
        "business_owner": "Estimating or Production Director",
        "primary_users": "Sales, estimating, prepress and production planning",
        "users_fa": "فروش، برآورد، پیش‌ازچاپ و برنامه‌ریزی تولید",
        "solution": "A structured job-brief extractor and similar-job retrieval tool that supports explainable estimating and tracks artwork/specification approvals.",
        "solution_fa": "یک ابزار استخراج بریف و بازیابی سفارش‌های مشابه که برآورد قابل توضیح را پشتیبانی می‌کند و تأیید فایل و مشخصات را قابل پیگیری می‌سازد.",
        "data": "Customer briefs, artwork/specifications, prior jobs, material/machine rules and capacity",
        "data_fa": "بریف مشتری، فایل و مشخصات، سفارش‌های قبلی، قواعد مواد/ماشین و ظرفیت",
        "integrations": "File intake, estimating spreadsheets, production planning and approval records",
        "integrations_fa": "دریافت فایل، فایل‌های برآورد، برنامه‌ریزی تولید و سوابق تأیید",
        "kpis": ["estimate turnaround", "revision cycles", "estimator throughput", "jobs delayed by missing specifications"],
        "kpis_fa": ["زمان برآورد", "تعداد دور اصلاح", "خروجی کارشناس برآورد", "سفارش‌های متوقف به‌دلیل نقص مشخصات"],
        "questions": [
            "چه ورودی‌هایی در بریف مشتری بیشتر ناقص یا اصلاح‌شونده هستند؟",
            "قواعد هزینه و ظرفیت چگونه تعیین می‌شوند و کدام بخش قطعی است؟",
            "نسخه نهایی فایل و مشخصات چگونه به تولید تحویل می‌شود؟",
            "چه تعداد استعلام یا سفارش سفارشی در ماه بررسی می‌شود؟",
            "یک نمونه واقعی برای مقایسه زمان برآورد و اصلاحات چیست؟",
        ],
        "pilot_fa": "پایلوت تبدیل بریف سفارش به برگه برآورد",
        "demo_fa": "یک بریف واقعیِ پاک‌شده از اطلاعات محرمانه وارد می‌شود؛ ابعاد، جنس، چاپ و نقاط ناقص استخراج، یک سفارش مشابه نشان داده و برگه آماده بررسی تولید می‌شود.",
    },
    "parts_catalog_matching": {
        "name": "Parts/catalog matching for sales confirmation",
        "fa_name": "تطبیق کاتالوگ و قطعه برای تأیید فروش",
        "business_owner": "Commercial or Operations Director",
        "primary_users": "Commercial, warehouse and customer-service teams",
        "users_fa": "بازرگانی، انبار و خدمات مشتری",
        "solution": "A catalog and compatibility assistant that maps customer descriptions or part numbers to candidate SKUs, stock and price for salesperson confirmation.",
        "solution_fa": "یک دستیار کاتالوگ و سازگاری که شرح یا شماره قطعه مشتری را به SKUهای کاندید، موجودی و قیمت برای تأیید کارشناس نگاشت می‌کند.",
        "data": "SKU/part master, OEM cross-references, compatibility notes, stock, price and return history",
        "data_fa": "مرجع SKU/قطعه، cross-reference سازنده، یادداشت سازگاری، موجودی، قیمت و سوابق مرجوعی",
        "integrations": "ERP/WMS exports, catalog files and CRM/order workflow",
        "integrations_fa": "خروجی ERP/WMS، فایل‌های کاتالوگ و گردش CRM/سفارش",
        "kpis": ["part-search time", "wrong-part corrections/returns", "quote turnaround", "orders per salesperson"],
        "kpis_fa": ["زمان جست‌وجوی قطعه", "اصلاح/مرجوعی قطعه اشتباه", "زمان پاسخ قیمت", "سفارش هر کارشناس"],
        "questions": [
            "پیدا کردن کدام شماره یا شرح قطعه برای فروش دشوارتر است؟",
            "مرجع قطعی موجودی و قیمت کدام سامانه یا فایل است؟",
            "خطای تطبیق قطعه چگونه شناسایی و اصلاح می‌شود؟",
            "آیا کاتالوگ و cross-reference رسمی قابل دسترسی است؟",
            "تأیید نهایی پیشنهاد قطعه با چه نقشی است؟",
        ],
        "pilot_fa": "پایلوت جست‌وجو و تطبیق قطعات پرتکرار",
        "demo_fa": "شرح یا شماره قطعه نمونه وارد می‌شود؛ چند SKU کاندید با مشخصات و منبع نمایش داده می‌شود و کارشناس گزینه نهایی را تأیید می‌کند.",
    },
}

ROLE_BUNDLES: dict[str, dict[str, str]] = {
    "rfq_quotation": {"primary": "Commercial / Sales Operations Director", "economic": "Managing Director / CEO", "technical": "Product or Technical Sales Manager"},
    "shipment_document_automation": {"primary": "Operations Director / Customs Manager", "economic": "Managing Director / CEO", "technical": "Compliance or Operations Systems Lead"},
    "boq_specification_matching": {"primary": "Technical Office / Project Sales Director", "economic": "Managing Director / CEO", "technical": "Project Controls or Engineering Manager"},
    "order_inventory_exceptions": {"primary": "Distribution / Sales Operations Director", "economic": "Managing Director / CEO", "technical": "ERP or Distribution Systems Owner"},
    "production_quality_reporting": {"primary": "Plant Manager / Operations Director", "economic": "Managing Director / CEO", "technical": "QA/QC or Production Systems Lead"},
    "service_ticket_maintenance": {"primary": "Service Director / Maintenance Manager", "economic": "Managing Director / CEO", "technical": "Engineering or Service Systems Lead"},
    "job_brief_estimate": {"primary": "Estimating / Production Director", "economic": "Managing Director / CEO", "technical": "Prepress or Production Planning Manager"},
    "parts_catalog_matching": {"primary": "Commercial / Operations Director", "economic": "Managing Director / CEO", "technical": "Parts or Warehouse Systems Owner"},
}

OWNER_FA = {
    "rfq_quotation": "مدیر بازرگانی یا مدیر عملیات فروش",
    "shipment_document_automation": "مدیر عملیات یا مدیر اسناد و ترخیص",
    "boq_specification_matching": "مدیر دفتر فنی یا مدیر فروش پروژه",
    "order_inventory_exceptions": "مدیر عملیات پخش یا مدیر زنجیره تأمین",
    "production_quality_reporting": "مدیر کارخانه یا مدیر عملیات",
    "service_ticket_maintenance": "مدیر خدمات یا مدیر نگهداری و تعمیرات",
    "job_brief_estimate": "مدیر برآورد یا مدیر تولید",
    "parts_catalog_matching": "مدیر بازرگانی یا مدیر عملیات",
}

CLIENT_STAGES_FA = {
    "rfq_quotation": ["دریافت استعلام از یک کانال منتخب", "استخراج مشخصات و اقلام درخواست", "تطبیق با مرجع تأییدشده محصولات و قواعد قیمت", "تهیه پیش‌نویس پاسخ برای بررسی کارشناس", "تأیید انسانی و ثبت نتیجه پیگیری"],
    "shipment_document_automation": ["دریافت اسناد یک پرونده منتخب", "استخراج فیلدهای اصلی و شماره پرونده", "بررسی چک‌لیست اسناد لازم", "ارجاع موارد ناقص به مسئول مربوط", "تأیید کارشناس و ثبت وضعیت پرونده"],
    "boq_specification_matching": ["دریافت یک BOQ یا درخواست فنی نمونه", "استخراج ردیف‌ها و الزامات کلیدی", "بازیابی گزینه‌ها و مستندات فنی تأییدشده", "ساخت بسته پیشنهادی نسخه‌دار", "بازبینی و تأیید توسط دفتر فنی یا فروش پروژه"],
    "order_inventory_exceptions": ["دریافت خروجی نمونه سفارش و موجودی", "یکپارچه‌کردن اقلام و مشتریان", "نمایش کسری، تعارض یا مرجوعی به‌عنوان استثنا", "ارسال مورد به مسئول مربوط برای بررسی", "ثبت تصمیم و تولید خلاصه مدیریتی"],
    "production_quality_reporting": ["دریافت چند گزارش نمونه شیفت یا کیفیت", "استخراج شاخص‌ها و دسته‌بندی توقف‌ها", "نمایش موارد خارج از قاعده و سوابق مرتبط", "بازبینی توسط تولید یا QA/QC", "تأیید و انتشار گزارش مدیریتی"],
    "service_ticket_maintenance": ["ثبت یک درخواست سرویس نمونه", "ساختاردهی تجهیز، اولویت و شرح مشکل", "بازیابی راهنمای تأییدشده و سوابق مرتبط", "ارجاع و تکمیل گزارش اولیه", "تأیید کارشناس و ثبت نتیجه خدمت"],
    "job_brief_estimate": ["دریافت بریف یا مشخصات سفارش نمونه", "استخراج ابعاد، جنس و الزامات", "نمایش موارد ناقص و سفارش‌های مشابه", "ساخت برگه برآورد قابل بازبینی", "تأیید نهایی برای تحویل به تولید"],
    "parts_catalog_matching": ["دریافت شرح یا شماره قطعه نمونه", "استخراج مشخصات و محدودیت سازگاری", "نمایش SKUهای کاندید با منبع", "بررسی موجودی و قیمت از مرجع مجاز", "تأیید کارشناس و ثبت پاسخ مشتری"],
}

WORKFLOW_QUERY_TERMS = {
    "rfq_quotation": "کاتالوگ استعلام قیمت فروش محصولات",
    "shipment_document_automation": "بارنامه اسناد حمل ترخیص",
    "boq_specification_matching": "مناقصه پروژه BOQ مشخصات فنی",
    "order_inventory_exceptions": "سفارش پخش موجودی انبار نمایندگی",
    "production_quality_reporting": "کارخانه تولید کنترل کیفیت استخدام",
    "service_ticket_maintenance": "تعمیرات نگهداری خدمات پروژه استخدام",
    "job_brief_estimate": "سفارش چاپ کارتن بسته بندی کارخانه",
    "parts_catalog_matching": "کاتالوگ قطعات شماره فنی نمایندگی",
}

ROLE_TERMS = [
    "مدیرعامل", "مدیر عامل", "مدیر اجرایی", "رئیس هیئت مدیره", "رییس هیئت مدیره", "عضو هیئت مدیره",
    "مدیر فروش", "مدیر بازرگانی", "مدیر عملیات", "مدیر تولید", "مدیر کارخانه", "مدیر پروژه",
    "مدیر خدمات", "مدیر فنی", "مدیر کنترل پروژه", "مدیرعامل", "ceo", "managing director",
    "commercial director", "sales director", "operations director", "plant manager", "service director",
]
NAME_STOPWORDS = {
    "شرکت", "گروه", "مجموعه", "مدیریت", "مدیر", "عامل", "هیئت", "رئیسه", "رئیس", "رییس", "عضو",
    "تولیدی", "صنعتی", "بازرگانی", "مهندسی", "تجارت", "بین", "الملل", "تهران", "ایران", "است", "شد",
    "the", "company", "director", "manager", "chief", "executive", "and", "of", "for", "limited",
}
PERSON_STOPWORDS = {
    "استان", "اصفهان", "تهران", "ایران", "شعب", "شعبه", "واحد", "عملیات", "سایر", "سمت",
    "نوشته", "پیام", "برای", "را", "می", "باشد", "چشم", "انداز", "برندها", "نام", "عنوان",
    "ما", "آشنا", "شوید", "یک", "ماه", "منقضی", "شده", "تومان", "کارفرمای", "مسئولیت", "پذیر",
    "هدایت", "کننده", "ناظر", "مشاور", "سال", "تأسیس", "تاسیس", "چشم", "انداز", "شعب", "بر", "به", "از", "در",
    "name", "your", "job", "position", "company", "department", "other", "unit", "branch",
}


def _tokens(value: str | None) -> list[str]:
    return [token for token in re.findall(r"[\w\u0600-\u06ff]{2,}", (value or "").lower()) if token not in NAME_STOPWORDS]


def _name_tokens(company: dict[str, Any]) -> list[str]:
    return _tokens(str(company.get("company_name_fa") or ""))


def _company_domain_set(company: dict[str, Any]) -> set[str]:
    domains: set[str] = set()
    # Only the canonical website is trusted as an official domain here.  The
    # first discovery pass stored social-share, trust-seal and directory URLs
    # in website_candidates; treating those as company domains caused the
    # activation pass to fetch unrelated pages and polluted source counts.
    for value in [company.get("website")]:
        if domain_of(value):
            domains.add(domain_of(value) or "")
    if not domains:
        for item in company.get("source_records") or []:
            family = str(item.get("source_family") or "")
            if family.startswith("company_website:"):
                domains.add(family.split(":", 1)[1])
    return {value for value in domains if value}


def activation_family(url: str | None) -> str | None:
    domain = domain_of(url)
    if not domain:
        return None
    if domain in SEARCH_DOMAINS or domain.endswith(".duckduckgo.com"):
        return "search_engine"
    if domain in AVVAL_DOMAINS or domain.endswith(".avval.ir"):
        return "book_e_avval"
    if domain in {"rrk.ir", "ilenc.ssaa.ir", "sabteagahi.ir", "codal.ir"} or domain.endswith((".rrk.ir", ".ssaa.ir")):
        return "official_registry"
    if domain == "vic.ir" or domain.endswith(".vic.ir"):
        return "industrial_estate_registry"
    if domain in {"tccim.ir", "iccima.ir", "iranfair.com", "isipo.ir", "tehran.isipo.ir"} or domain.endswith((".tccim.ir", ".iccima.ir", ".iranfair.com", ".isipo.ir")):
        return "association_or_exhibition"
    if domain in {"jobinja.ir", "jobvision.ir", "irantalent.com", "e-estekhdam.com", "jobinja.com"} or domain.endswith((".jobinja.ir", ".jobvision.ir", ".irantalent.com")):
        return "job_portal"
    if domain == "linkedin.com" or domain.endswith(".linkedin.com"):
        return "linkedin_public"
    if domain in {"neshan.org", "balad.ir"} or domain.endswith((".neshan.org", ".balad.ir")):
        return "map_listing"
    if domain in {"inexhub.ir", "iranindustry.com", "parscenter.com", "sanatmap.com", "irantamin.com", "rasmio.com", "companyregister.ir"} or domain.endswith((".inexhub.ir", ".rasmio.com")):
        return "industry_directory"
    if domain in {
        "irna.ir", "isna.ir", "ilna.ir", "mehrnews.com", "tasnimnews.com", "farsnews.ir", "yjc.ir",
        "khabaronline.ir", "dana.ir", "tejaratnews.com", "donya-e-eqtesad.com", "shana.ir",
    }:
        return "public_news"
    if domain in COMPANY_SOCIAL_DOMAINS or any(domain.endswith("." + item) for item in COMPANY_SOCIAL_DOMAINS):
        return "social_public"
    return "other_public"


def _is_company_domain(url: str | None, domains: set[str]) -> bool:
    domain = domain_of(url)
    return bool(domain and any(domain == item or domain.endswith("." + item) for item in domains))


def _valid_external_result(url: str | None, company: dict[str, Any]) -> bool:
    family = activation_family(url)
    if not url or not family or family in {"search_engine", "book_e_avval", "social_public", "other_public"}:
        return False
    if family == "linkedin_public" and "/company/" not in (url or "").lower():
        return False
    if _is_company_domain(url, _company_domain_set(company)):
        return False
    return True


def _resolve_yahoo_target(value: str | None) -> str | None:
    """Resolve Yahoo's public result wrapper without following a click."""
    if not value:
        return None
    href = html_lib.unescape(value)
    match = re.search(r"/RU=([^/]+)(?:/RK=|$)", href, re.I)
    target = unquote(match.group(1)) if match else href
    for _ in range(2):
        decoded = unquote(target)
        if decoded == target:
            break
        target = decoded
    return canonical_url(target)


def _parse_yahoo(body: str, source_url: str, query: str) -> list[dict[str, Any]]:
    """Parse Yahoo's server-rendered public results page.

    DuckDuckGo began returning a human challenge to the direct proxy during
    this run.  Yahoo's HTML results are used only as a locator; every selected
    result is fetched separately and identity-checked before becoming evidence.
    """
    blocks = re.findall(
        r'<div[^>]+class="[^"]*\balgo-sr\b[^"]*"[^>]*>.*?(?=<div[^>]+class="[^"]*\balgo-sr\b[^"]*"|</ol>)',
        body or "",
        re.I | re.S,
    )
    rows: list[dict[str, Any]] = []
    for block in blocks:
        links = extract_links(block, source_url)
        if not links:
            continue
        target = _resolve_yahoo_target(links[0].get("href"))
        if not target:
            continue
        title = clean_text(links[0].get("text"), 300)
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", block, re.I | re.S)
        snippet = clean_text(re.sub(r"<[^>]+>", " ", html_lib.unescape(paragraphs[0]))) if paragraphs else ""
        rows.append({
            "raw_candidate_id": stable_hash(source_url, target, title),
            "website": target,
            "source_title": title,
            "description": snippet,
            "source_url": source_url,
            "query": query,
        })
    return rows


def _parse_search_results(body: str, source_url: str, query: str) -> list[dict[str, Any]]:
    if domain_of(source_url) == "search.yahoo.com":
        return _parse_yahoo(body, source_url, query)
    return parse_ddg(body, source_url, query)


def activation_search_url(query: str) -> str:
    return "https://search.yahoo.com/search?" + urlencode({"p": query, "vl": "lang_fa"})


def _workflow_key(company: dict[str, Any]) -> str:
    workflow = (company.get("workflow_opportunities") or [{}])[0] or {}
    return str(workflow.get("workflow_family") or "rfq_quotation")


def query_variants(company: dict[str, Any]) -> list[str]:
    name = clean_text(company.get("company_name_fa"), 160)
    key = _workflow_key(company)
    domain = sorted(_company_domain_set(company))[0] if _company_domain_set(company) else ""
    queries = [
        f'"{name}" مدیرعامل مدیر فروش مدیر عملیات',
        f'"{name}" استخدام فرصت شغلی',
        f'"{name}" نمایشگاه انجمن عضو',
        f'"{name}" {WORKFLOW_QUERY_TERMS.get(key, "فرایند عملیاتی")}',
    ]
    if domain:
        queries.append(f'"{name}" "{domain}" شرکت')
    return list(dict.fromkeys(queries))


def _search_result_relevance(company: dict[str, Any], result: dict[str, Any]) -> int:
    text = " ".join(str(result.get(item) or "") for item in ["source_title", "description", "website"])
    normalized = text.lower()
    tokens = _name_tokens(company)
    exact = sum(1 for token in tokens if token in normalized)
    if len(tokens) <= 1:
        return 3 if exact else 0
    return exact


def _page_matches_company(company: dict[str, Any], page: dict[str, Any], *, allow_official: bool = False) -> bool:
    if not page.get("status") or not page.get("text"):
        return False
    text = f"{page.get('title', '')} {page.get('text', '')}".lower()
    if re.search(r"domain\s+(?:has\s+)?expired|suspendedpage|صفحه مورد نظر یافت نشد|فعالیت.{0,30}(?:تعطیل|متوقف)", text, re.I):
        return False
    if allow_official and _is_company_domain(page.get("url"), _company_domain_set(company)):
        return True
    tokens = _name_tokens(company)
    tokens += _tokens(str(company.get("brand_name_fa") or ""))
    tokens += _tokens(str(company.get("company_name_en") or ""))
    tokens = list(dict.fromkeys(tokens))
    if not tokens:
        return False
    return sum(1 for token in tokens if token in text) >= (1 if len(tokens) <= 2 else 2)


def _extract_page(url: str, response: dict[str, Any], *, kind: str, query: str | None = None) -> dict[str, Any]:
    body = response.get("body") or ""
    is_html = "text/html" in str(response.get("content_type") or "").lower() or "<html" in body[:1000].lower()
    text = html_to_text(body, 18000) if is_html else clean_text(body, 18000)
    title = clean_text(re.search(r"<title[^>]*>(.*?)</title>", body or "", re.I | re.S).group(1), 300) if re.search(r"<title[^>]*>(.*?)</title>", body or "", re.I | re.S) else ""
    links = extract_links(body, response.get("final_url") or url) if is_html else []
    detail = {
        "url": response.get("final_url") or url,
        "requested_url": url,
        "title": title,
        "status": response.get("status"),
        "content_type": response.get("content_type"),
        "captured_at": now_iso(),
        "kind": kind,
        "query": query,
        "source_family": activation_family(response.get("final_url") or url),
        "text": text,
        "text_excerpt": clean_text(text, 5000),
        "links": [{"text": clean_text(item.get("text"), 180), "href": item.get("href")} for item in links if item.get("href")],
        "emails": filter_public_emails(extract_emails(body + " " + text)),
        "phones": corporate_phones(text),
        "whatsapp_urls": [item.get("href") for item in links if domain_of(item.get("href")) in {"wa.me", "api.whatsapp.com"}],
        "error": response.get("error"),
    }
    detail["signals"] = derive_page_signals({"title": title, "text_excerpt": detail["text_excerpt"]})
    return detail


def _usable_status(value: Any) -> bool:
    try:
        return 200 <= int(value) < 400
    except (TypeError, ValueError):
        return False


def _search_blocked(page: dict[str, Any]) -> bool:
    text = f"{page.get('title') or ''} {page.get('text') or ''}".lower()
    return any(term in text for term in ["unfortunately, bots", "human challenge", "anomaly-modal", "captcha"])


def _official_urls(company: dict[str, Any], limit: int = 5) -> list[str]:
    values: list[str] = []
    official_domains = _company_domain_set(company)
    records = list(company.get("source_records") or [])
    records.sort(key=lambda item: (0 if "contact" in str(item.get("source_title") or "").lower() or "تماس" in str(item.get("source_title") or "") else 1, str(item.get("source_url") or "")))
    for item in records:
        if not str(item.get("source_family") or "").startswith("company_website:"):
            continue
        url = canonical_url(item.get("source_url"))
        if url and _is_company_domain(url, official_domains) and url not in values:
            values.append(url)
    for candidate in [company.get("website")]:
        url = canonical_url(candidate)
        if url and _is_company_domain(url, _company_domain_set(company)) and url not in values:
            values.insert(0, url)
    return values[:limit]


def _external_candidates(company: dict[str, Any], search_pages: list[dict[str, Any]], max_external: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_family: set[str] = set()
    seen_url: set[str] = set()
    all_results: list[dict[str, Any]] = []
    for page in search_pages:
        body = page.get("_body") or ""
        if not body:
            continue
        query = page.get("query") or ""
        for result in _parse_search_results(body, page.get("requested_url") or page.get("url") or "", query):
            result["query"] = query
            result["relevance"] = _search_result_relevance(company, result)
            result["activation_family"] = activation_family(result.get("website"))
            if result["relevance"] > 0 and _valid_external_result(result.get("website"), company):
                all_results.append(result)
    all_results.sort(key=lambda item: (FAMILY_PRIORITY.get(item.get("activation_family"), 99), -int(item.get("relevance") or 0), str(item.get("website") or "")))
    for result in all_results:
        url = canonical_url(result.get("website"))
        family = result.get("activation_family")
        if not url or not family or url in seen_url:
            continue
        # One page per independent family is preferable to five pages from one
        # employment site.  A second page is allowed only after all available
        # families have had a chance.
        if family in seen_family and len(seen_family) < max_external:
            continue
        selected.append({"url": url, "family": family, "title": result.get("source_title"), "snippet": result.get("description"), "query": result.get("query"), "relevance": result.get("relevance")})
        seen_url.add(url)
        seen_family.add(family)
        if len(selected) >= max_external:
            break
    if len(selected) < max_external:
        for result in all_results:
            url = canonical_url(result.get("website"))
            if not url or url in seen_url:
                continue
            selected.append({"url": url, "family": result.get("activation_family"), "title": result.get("source_title"), "snippet": result.get("description"), "query": result.get("query"), "relevance": result.get("relevance")})
            seen_url.add(url)
            if len(selected) >= max_external:
                break
    return selected


def _public_email_candidates(company: dict[str, Any], pages: Iterable[dict[str, Any]]) -> list[str]:
    official_domains = _company_domain_set(company)
    values: list[str] = []
    for email in list(company.get("email_public") or []) + [email for page in pages for email in page.get("emails") or []]:
        value = str(email).lower().strip()
        local, sep, domain = value.partition("@")
        if not sep or not local or not domain or domain in FREE_EMAIL_DOMAINS:
            continue
        if domain == "google.com" or domain.startswith("gmai"):
            continue
        if domain not in official_domains and local not in GENERIC_EMAIL_PREFIXES:
            continue
        if local not in GENERIC_EMAIL_PREFIXES:
            continue
        values.append(value)
    return sorted(set(values))


def _public_linkedin(company: dict[str, Any], pages: Iterable[dict[str, Any]], search_pages: Iterable[dict[str, Any]]) -> str | None:
    values = [company.get("linkedin_company_page")]
    values.extend(item.get("url") for item in pages for item in [item] if item.get("source_family") == "linkedin_public")
    for page in search_pages:
        body = page.get("_body") or ""
        for result in _parse_search_results(body, page.get("requested_url") or "", page.get("query") or "") if body else []:
            url = canonical_url(result.get("website"))
            if url and domain_of(url) == "linkedin.com" and "/company/" in url:
                values.append(url)
    for value in values:
        url = canonical_url(value)
        if url and domain_of(url) == "linkedin.com" and "/company/" in url:
            return url
    return None


def _snippet(text: str, terms: Iterable[str], limit: int = 650) -> str:
    text = clean_text(text, 18000)
    lowered = text.lower()
    for term in terms:
        pos = lowered.find(str(term).lower())
        if pos >= 0:
            return clean_text(text[max(0, pos - 120): pos + limit], limit)
    return clean_text(text, limit)


def _surface_claims(company: dict[str, Any], pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key = _workflow_key(company)
    terms_by_key = {
        "rfq_quotation": ["استعلام", "قیمت", "محصولات", "کاتالوگ", "تماس"],
        "shipment_document_automation": ["بارنامه", "اسناد", "ترخیص", "حمل", "خدمات"],
        "boq_specification_matching": ["مشخصات فنی", "پروژه", "مناقصه", "محصولات", "خدمات"],
        "order_inventory_exceptions": ["سفارش", "پخش", "موجودی", "محصولات", "تماس"],
        "production_quality_reporting": ["تولید", "کارخانه", "کیفیت", "محصولات", "استاندارد"],
        "service_ticket_maintenance": ["تعمیرات", "نگهداری", "خدمات", "پشتیبانی", "تماس"],
        "job_brief_estimate": ["کارتن", "جعبه", "بسته بندی", "سفارش", "تماس"],
        "parts_catalog_matching": ["قطعات", "کاتالوگ", "شماره", "محصولات", "تماس"],
    }
    claims: list[dict[str, Any]] = []
    for page in pages:
        if page.get("kind") != "official_page" or not page.get("status"):
            continue
        signals = page.get("signals") or {}
        relevant = [
            label for label, present in [
                ("product/catalog information", signals.get("catalog_or_products")),
                ("a contact or order entry point", signals.get("order_or_contact_form") or signals.get("rfq_or_quote")),
                ("service or maintenance information", signals.get("service_after_sales")),
                ("projects or client information", signals.get("projects_or_clients")),
                ("factory/production information", signals.get("factory_or_warehouse")),
                ("tender/contract language", signals.get("tender_or_contract")),
            ] if present
        ]
        if not relevant:
            continue
        claim = f"The public page titled '{page.get('title') or 'company page'}' exposes " + ", ".join(relevant[:2]) + "."
        claims.append({
            "claim": claim,
            "source_url": page.get("url"),
            "source_title": page.get("title") or "Official company page",
            "quote_or_snippet": _snippet(page.get("text") or "", terms_by_key.get(key, [])),
            "evidence_type": "OBSERVED",
            "confidence": 0.8,
            "source_family": page.get("source_family"),
        })
    # Keep the public surface compact and avoid treating multiple pages in one
    # domain as independent evidence.
    seen: set[tuple[str | None, str | None]] = set()
    output: list[dict[str, Any]] = []
    for claim in claims:
        token = (claim.get("source_url"), claim.get("claim"))
        if token not in seen:
            seen.add(token)
            output.append(claim)
    return output[:5]


def _external_claim(company: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    family = page.get("source_family") or "other_public"
    name = company.get("company_name_fa")
    if family == "job_portal":
        claim = f"A public employment or employer page associates {name} with hiring/activity information."
        terms = ["استخدام", "فرصت شغلی", "کارشناس", "job"]
        confidence = 0.72
    elif family == "association_or_exhibition":
        claim = f"A public association or exhibition page associates {name} with an industry participation or membership context."
        terms = ["نمایشگاه", "عضو", "شرکت", "غرفه", "انجمن"]
        confidence = 0.78
    elif family == "official_registry":
        claim = f"A public registry/company-record page associates {name} with a formal company identity or registration reference."
        terms = ["شناسه ملی", "شرکت", "ثبت", "مدیرعامل"]
        confidence = 0.82
    elif family == "linkedin_public":
        claim = f"A public LinkedIn page associates {name} with an organizational or professional identity."
        terms = ["company", "شرکت", "employee", "کارمند"]
        confidence = 0.62
    elif family == "industry_directory":
        claim = f"A public industry profile describes {name} in a stated business or product context."
        terms = ["تولید", "فروش", "محصول", "خدمات", "شرکت"]
        confidence = 0.68
    elif family == "map_listing":
        claim = f"A public map listing provides a secondary identity/location reference for {name}."
        terms = ["تهران", "آدرس", "شرکت", "مکان"]
        confidence = 0.58
    elif family == "public_news":
        claim = f"A public news page mentions {name} in a commercial, project or industry context."
        terms = ["شرکت", "پروژه", "صنعت", "تولید", "مدیر"]
        confidence = 0.7
    else:
        claim = f"A public web page provides an additional external reference for {name}."
        terms = ["شرکت", "محصول", "خدمات"]
        confidence = 0.5
    return {
        "claim": claim,
        "source_url": page.get("url"),
        "source_title": page.get("title") or family,
        "quote_or_snippet": _snippet(page.get("text") or page.get("snippet") or "", terms),
        "evidence_type": "OBSERVED",
        "confidence": confidence,
        "source_family": family,
    }


def _clean_person_name(value: str) -> str | None:
    value = re.sub(r"\s+", " ", value.replace("،", " ").replace(",", " ").strip(" :-–—|،."))
    value = re.sub(r"^(?:مهندس|دکتر|جناب|سرکار خانم|آقای|خانم)\s+", "", value)
    value = re.sub(r"\s+(?:است|می باشد|و|در|شرکت|گروه).*$", "", value)
    parts = value.split()
    if len(parts) < 2 or len(parts) > 4:
        return None
    if any(part.lower() in NAME_STOPWORDS or part.lower() in PERSON_STOPWORDS for part in parts):
        return None
    if any(not re.fullmatch(r"[A-Za-z\u0600-\u06ff]{2,}", part) for part in parts):
        return None
    return " ".join(parts)


def _name_candidates_from_text(text: str, url: str, title: str, family: str | None, *, direct: bool) -> list[dict[str, Any]]:
    text = clean_text(text, 20000)
    candidates: list[dict[str, Any]] = []
    role_groups = [
        ("economic_buyer", ["مدیرعامل", "مدیر عامل", "مدیر اجرایی", "رئیس هیئت مدیره", "رییس هیئت مدیره", "ریاست گروه", "بنیانگذار", "بنیان‌گذار", "ceo", "managing director"]),
        ("primary_contact", ["مدیر فروش", "مدیر بازرگانی", "مدیر عملیات", "مدیر تولید", "مدیر کارخانه", "مدیر پروژه", "مدیر خدمات", "مدیر کنترل پروژه", "commercial director", "sales director", "operations director", "plant manager", "service director"]),
        ("technical_gatekeeper", ["مدیر فناوری اطلاعات", "مدیر IT", "مدیر سیستم", "مسئول فناوری", "technical manager", "it manager"]),
    ]
    # A named founder/owner is sometimes introduced as «آقای ...» rather than
    # by placing the name immediately after a role label.  Require a nearby
    # ownership phrase so ordinary prose is not promoted to a person record.
    for match in re.finditer(r"(?:آقای|خانم|مهندس|دکتر)\s+([A-Za-z\u0600-\u06ff]{2,}(?:\s+[A-Za-z\u0600-\u06ff]{2,}){1,2}?)\s+(?=(?:را\s+)?(?:بر عهده|عهده|بنیانگذار|بنیان‌گذار))", text, re.I):
        name = _clean_person_name(match.group(1))
        if name:
            candidates.append({"field": "economic_buyer", "role": "public founder/owner", "name": name, "source_url": url, "source_title": title, "source_family": family, "direct": direct, "confidence": 0.88 if direct else 0.35, "evidence": clean_text(text[max(0, match.start() - 90): match.end() + 90], 360)})
    for field, roles in role_groups:
        for role in roles:
            role_pattern = rf"{re.escape(role)}(?![A-Za-z\u0600-\u06ff])"
            pattern = rf"{role_pattern}\s*(?:[:：\-–—،]\s*|\s+)(?:مهندس|دکتر)?\s*([A-Za-z\u0600-\u06ff]{{2,}}(?:\s+[A-Za-z\u0600-\u06ff]{{2,}}){{1,3}})"
            for match in re.finditer(pattern, text, re.I):
                name = _clean_person_name(match.group(1))
                if name:
                    candidates.append({"field": field, "role": role, "name": name, "source_url": url, "source_title": title, "source_family": family, "direct": direct, "confidence": 0.85 if direct else 0.35, "evidence": clean_text(text[max(0, match.start() - 90): match.end() + 90], 360)})
            reverse = rf"([A-Za-z\u0600-\u06ff]{{2,}}(?:\s+[A-Za-z\u0600-\u06ff]{{2,}}){{1,3}})\s+{role_pattern}"
            for match in re.finditer(reverse, text, re.I):
                name = _clean_person_name(match.group(1))
                if name:
                    candidates.append({"field": field, "role": role, "name": name, "source_url": url, "source_title": title, "source_family": family, "direct": direct, "confidence": 0.85 if direct else 0.35, "evidence": clean_text(text[max(0, match.start() - 90): match.end() + 90], 360)})
    seen: set[tuple[str, str, str]] = set()
    return [item for item in candidates if not ((item["field"], item["name"], item["source_url"]) in seen or seen.add((item["field"], item["name"], item["source_url"])))][:20]


def _extract_contacts(company: dict[str, Any], official_pages: list[dict[str, Any]], external_pages: list[dict[str, Any]], search_pages: list[dict[str, Any]]) -> dict[str, Any]:
    direct_candidates: list[dict[str, Any]] = []
    search_candidates: list[dict[str, Any]] = []
    for page in official_pages + external_pages:
        if not _page_matches_company(company, page, allow_official=page in official_pages):
            continue
        if page in official_pages:
            identity_page = f"{page.get('url') or ''} {page.get('title') or ''}".lower()
            if not re.search(r"team|management|board|مدیر|تیم|اعضا|پرسنل|rrk|ssaa|بنیانگذار|بنیان‌گذار|ریاست گروه", identity_page, re.I):
                continue
        elif page.get("source_family") not in {"linkedin_public", "official_registry"}:
            # Job boards, directories, maps and news can corroborate activity,
            # but their snippets routinely place arbitrary words after a role
            # label.  They are not treated as verified management sources.
            continue
        direct_candidates.extend(_name_candidates_from_text(page.get("text") or "", page.get("url") or "", page.get("title") or "", page.get("source_family"), direct=True))
    for page in search_pages:
        body = page.get("_body") or ""
        if not body:
            continue
        for result in _parse_search_results(body, page.get("requested_url") or "", page.get("query") or ""):
            if _search_result_relevance(company, result) <= 0:
                continue
            search_candidates.extend(_name_candidates_from_text(" ".join([result.get("source_title") or "", result.get("description") or ""]), result.get("website") or "", result.get("source_title") or "", activation_family(result.get("website")), direct=False))
    key = _workflow_key(company)
    bundle = ROLE_BUNDLES.get(key, ROLE_BUNDLES["rfq_quotation"])
    primary = next((item for item in direct_candidates if item.get("field") == "primary_contact"), None)
    economic = next((item for item in direct_candidates if item.get("field") == "economic_buyer"), None)
    technical = next((item for item in direct_candidates if item.get("field") == "technical_gatekeeper"), None)
    official_pages_all = official_pages + [page for page in external_pages if page.get("source_family") == "linkedin_public"]
    emails = _public_email_candidates(company, official_pages_all)
    phones = sorted(set(company.get("phone_public") or []) | {phone for page in official_pages for phone in page.get("phones") or [] if str(phone).startswith("021")})
    whatsapp = next((url for page in official_pages for url in page.get("whatsapp_urls") or [] if url), None)
    linkedin = _public_linkedin(company, external_pages, search_pages)
    return {
        "primary_contact_role": bundle["primary"],
        "primary_contact_name": primary.get("name") if primary else None,
        "primary_contact_source_url": primary.get("source_url") if primary else None,
        "primary_contact_confidence": primary.get("confidence", 0.0) if primary else 0.0,
        "economic_buyer_role": bundle["economic"],
        "economic_buyer_name": economic.get("name") if economic else None,
        "economic_buyer_source_url": economic.get("source_url") if economic else None,
        "economic_buyer_confidence": economic.get("confidence", 0.0) if economic else 0.0,
        "technical_gatekeeper_role": bundle["technical"],
        "technical_gatekeeper_name": technical.get("name") if technical else None,
        "technical_gatekeeper_source_url": technical.get("source_url") if technical else None,
        "technical_gatekeeper_confidence": technical.get("confidence", 0.0) if technical else 0.0,
        "decision_maker_search_candidates": search_candidates[:12],
        "decision_maker_direct_candidates": direct_candidates[:20],
        "public_corporate_emails": emails,
        "public_corporate_phones": phones,
        "public_linkedin_company": linkedin,
        "public_whatsapp": whatsapp,
    }


def _journey(company: dict[str, Any], official_pages: list[dict[str, Any]], claims: list[dict[str, Any]], contacts: dict[str, Any]) -> dict[str, Any]:
    key = _workflow_key(company)
    has_catalog = any((page.get("signals") or {}).get("catalog_or_products") for page in official_pages)
    has_form = any((page.get("signals") or {}).get("order_or_contact_form") or (page.get("signals") or {}).get("rfq_or_quote") for page in official_pages)
    has_service = any((page.get("signals") or {}).get("service_after_sales") for page in official_pages)
    has_projects = any((page.get("signals") or {}).get("projects_or_clients") for page in official_pages)
    entry = []
    if has_catalog:
        entry.append("public product/service information or catalog")
    if has_projects:
        entry.append("public project/client information")
    if has_service:
        entry.append("public service/maintenance information")
    if not entry:
        entry.append("the company's public identity and service description")
    intake = []
    if has_form:
        intake.append("website contact or inquiry surface")
    if contacts.get("public_corporate_emails"):
        intake.append("published corporate email")
    if contacts.get("public_corporate_phones"):
        intake.append("published corporate phone")
    if contacts.get("public_whatsapp"):
        intake.append("explicitly published WhatsApp business link")
    if not intake:
        intake.append("public contact route; exact intake method needs validation")
    workflow_step = {
        "rfq_quotation": "sales team prepares a response or quotation",
        "shipment_document_automation": "operations team reviews the shipment/customs case",
        "boq_specification_matching": "technical/commercial team reviews a project request",
        "order_inventory_exceptions": "distribution team confirms order and availability",
        "production_quality_reporting": "plant/quality team reviews operational records",
        "service_ticket_maintenance": "service team reviews and assigns the request",
        "job_brief_estimate": "estimating/production team reviews the job brief",
        "parts_catalog_matching": "commercial/warehouse team confirms the part",
    }.get(key, "the responsible business team reviews the request")
    return {
        "observable_steps": [
            f"Customer reaches {company.get('company_name_fa')} through {', '.join(entry)}.",
            f"Customer uses {', '.join(intake)} to ask for information or service.",
            workflow_step + "; the public record does not expose the internal handoffs or approval rules.",
            "A discovery meeting should validate volume, data sources, ownership and the smallest safe pilot.",
        ],
        "observable_steps_fa": [
            f"مشتری از طریق {('، '.join(entry))} به {company.get('company_name_fa')} می‌رسد.",
            f"مشتری از {('، '.join(intake))} برای دریافت اطلاعات یا خدمت استفاده می‌کند.",
            f"{workflow_step}؛ مراحل داخلی و قواعد تأیید از منابع عمومی قابل مشاهده نیست.",
            "در جلسه کشف، حجم، منابع داده، مالک فرایند و کوچک‌ترین پایلوت امن اعتبارسنجی شود.",
        ],
        "entry_points": entry,
        "intake_channels": intake,
        "evidence": claims[:4],
    }


def _pilot(company: dict[str, Any], workflow: dict[str, Any], contacts: dict[str, Any]) -> dict[str, Any]:
    profile = WORKFLOW_PROFILES[_workflow_key(company)]
    return {
        "pilot_name": f"{profile['pilot_fa']} — {company.get('company_name_fa')}",
        "pilot_scope": f"یک مسیر محدود و قابل کنترل برای {profile['fa_name']} با یک قالب ورودی و یک گروه کاربر؛ هسته ERP یا تصمیم نهایی جایگزین نمی‌شود.",
        "primary_users": profile["users_fa"],
        "input_data_needed": profile["data_fa"],
        "existing_systems_to_connect_if_known": "UNKNOWN — begin with approved exports, shared files or email samples; confirm system ownership in discovery.",
        "what_luma_builds": profile["solution_fa"],
        "human_approval_points": "تأیید محصول/مقدار/قیمت، تأیید نقص یا استثنا، و انتشار خروجی نهایی نزد کارشناس یا مدیر مربوط باقی می‌ماند.",
        "pilot_duration_estimate": "حدود ۳ تا ۶ هفته کاری پس از تأیید دسترسی، نمونه داده و دامنه پایلوت؛ مدت دقیق در جلسه کشف تعیین می‌شود.",
        "success_metrics": profile["kpis_fa"],
        "expansion_path": "پس از سنجش پایلوت، افزودن قالب‌ها/واحدهای بیشتر، اتصال کنترل‌شده به سامانه موجود و داشبورد مدیریتی.",
        "risks": [
            "حجم واقعی و کیفیت داده عمومی نیست و باید با نمونه واقعی سنجیده شود.",
            "مجوز دسترسی، نسخه مرجع داده و مالک تأیید باید مشخص شود.",
            "خروجی پیشنهادی بدون تأیید انسانی منتشر نشود.",
        ],
    }


def _demo(company: dict[str, Any], workflow: dict[str, Any], official_pages: list[dict[str, Any]]) -> dict[str, Any]:
    profile = WORKFLOW_PROFILES[_workflow_key(company)]
    relevant_page = next((page for page in official_pages if page.get("status") and page.get("title")), None)
    return {
        "demo_concept": profile["demo_fa"],
        "demo_inputs": "یک نمونه ساختگی یا پاک‌سازی‌شده از داده واقعی مشتری، بدون اطلاعات محرمانه.",
        "demo_steps": [
            "انتخاب یک نمونه عمومی/پاک‌سازی‌شده",
            "استخراج و ساختاربندی داده",
            "نمایش پیشنهاد یا استثنا همراه با منبع",
            "تأیید یا اصلاح توسط کاربر کسب‌وکار",
            "نمایش KPI قابل اندازه‌گیری و مسیر گسترش",
        ],
        "public_surface_reference": relevant_page.get("url") if relevant_page else None,
    }


def _workflow(company: dict[str, Any], official_pages: list[dict[str, Any]], claims: list[dict[str, Any]]) -> dict[str, Any]:
    key = _workflow_key(company)
    profile = WORKFLOW_PROFILES.get(key, WORKFLOW_PROFILES["rfq_quotation"])
    claim_count = len(claims)
    has_direct_intake = any((page.get("signals") or {}).get("order_or_contact_form") or (page.get("signals") or {}).get("rfq_or_quote") for page in official_pages)
    classification = "EVIDENCE_SUPPORTED" if claim_count >= 2 and has_direct_intake else "STRONG_HYPOTHESIS" if claim_count >= 1 else "WEAK_HYPOTHESIS"
    evidence = claims[:5]
    return {
        "workflow_id": "wf-" + stable_hash(company["company_id"], key, ACTIVATION_VERSION),
        "company_id": company["company_id"],
        "department": profile["business_owner"],
        "workflow_name": profile["name"],
        "workflow_name_fa": profile["fa_name"],
        "workflow_family": key,
        "workflow_evidence_classification": classification,
        "activation_evidence_classification": classification,
        "current_process_hypothesis": f"Based on the public {profile['fa_name']} surface, the first process to validate is the handoff from incoming information to a reviewed business output. Public sources do not establish the internal process or a current inefficiency.",
        "current_process_hypothesis_fa": f"با توجه به سطح عمومی {profile['fa_name']}، نخستین فرایند قابل بررسی، تبدیل ورودی به خروجی کسب‌وکاریِ قابل بازبینی است؛ منابع عمومی فرایند داخلی یا وجود ناکارآمدی فعلی را اثبات نمی‌کنند.",
        "supporting_evidence": evidence,
        "current_problem": "A repeated lookup, document or approval handoff is plausible; validate the actual volume, owner and baseline before proposing automation.",
        "current_problem_fa": "تکرار جست‌وجو، ساخت سند یا تأیید محتمل است؛ حجم واقعی، مالک و خط مبنا پیش از پیشنهاد خودکارسازی اعتبارسنجی شود.",
        "proposed_luma_solution": profile["solution"],
        "proposed_luma_solution_fa": profile["solution_fa"],
        "primary_users": profile["primary_users"],
        "primary_users_fa": profile["users_fa"],
        "likely_business_owner": profile["business_owner"],
        "required_data": [profile["data"]],
        "required_data_fa": [profile["data_fa"]],
        "required_integrations": [profile["integrations"]],
        "required_integrations_fa": [profile["integrations_fa"]],
        "implementation_complexity": "Medium" if key in {"rfq_quotation", "job_brief_estimate", "parts_catalog_matching", "order_inventory_exceptions"} else "High",
        "implementation_risks": ["data quality and permissions require discovery", "human approval remains required", "pilot should use a bounded workflow and approved samples"],
        "implementation_risks_fa": ["کیفیت داده و مجوزها باید در کشف بررسی شود", "تأیید انسانی حفظ می‌شود", "پایلوت با گردش محدود و نمونه‌های تأییدشده شروع شود"],
        "measurable_KPIs": profile["kpis"],
        "measurable_KPIs_fa": profile["kpis_fa"],
        "confidence": "High" if classification == "EVIDENCE_SUPPORTED" else "Medium" if classification == "STRONG_HYPOTHESIS" else "Low",
        "confidence_score": 0.85 if classification == "EVIDENCE_SUPPORTED" else 0.7 if classification == "STRONG_HYPOTHESIS" else 0.45,
        "discovery_questions": profile["questions"],
        "source_urls": [item.get("source_url") for item in evidence if item.get("source_url")],
    }


def _save_activation_page(company_id: str, page: dict[str, Any]) -> str | None:
    if not page.get("status") or not page.get("text") or not page.get("url"):
        return None
    directory = path_for("evidence", "companies", company_id, "pages")
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"sales-{stable_hash(page.get('url'), ACTIVATION_VERSION)}.txt"
    output = directory / filename
    header = [
        "Sales activation public-page capture",
        f"Company ID: {company_id}",
        f"URL: {page.get('url')}",
        f"Title: {page.get('title') or 'UNKNOWN'}",
        f"Source family: {page.get('source_family') or 'UNKNOWN'}",
        f"Captured at: {page.get('captured_at') or now_iso()}",
        "",
    ]
    output.write_text("\n".join(header) + clean_text(page.get("text"), 8000) + "\n", encoding="utf-8")
    return str(Path("companies") / company_id / "pages" / filename)


def _merge_evidence_package(company: dict[str, Any], pages: list[dict[str, Any]], claims: list[dict[str, Any]], errors: list[dict[str, Any]], contact: dict[str, Any], journey: dict[str, Any], workflow: dict[str, Any]) -> list[str]:
    package_path = path_for("evidence", "companies", company["company_id"], "sources.json")
    try:
        payload = json.loads(package_path.read_text(encoding="utf-8")) if package_path.exists() else {}
    except Exception:
        payload = {}
    old_sources = payload.get("sources") or []
    old_keys = {(item.get("source_url"), item.get("source_family")) for item in old_sources}
    added_sources: list[dict[str, Any]] = []
    page_paths: list[str] = []
    for page in pages:
        path = _save_activation_page(company["company_id"], page)
        if path:
            page_paths.append(path)
        if not page.get("status") or not page.get("url"):
            continue
        record = {
            "source_id": "src-" + stable_hash(company["company_id"], page.get("url"), ACTIVATION_VERSION),
            "company_id": company["company_id"],
            "source_url": page.get("url"),
            "source_title": page.get("title") or page.get("source_family") or page.get("kind"),
            "source_type": "sales_activation_public_page",
            "source_quality": "public_page",
            "source_family": page.get("source_family") or audit_source_family(page.get("url"), source_type="sales_activation"),
            "discovery_reason": "Targeted sales activation enrichment of an existing READY FOR OUTREACH company",
            "evidence_class": "OBSERVED",
            "evidence_snippet": clean_text(page.get("text"), 700),
            "captured_at": page.get("captured_at") or now_iso(),
            "sales_activation_round": ACTIVATION_VERSION,
        }
        if (record["source_url"], record["source_family"]) not in old_keys:
            added_sources.append(record)
    all_sources = old_sources + added_sources
    existing_errors = payload.get("errors") or []
    error_keys: set[tuple[Any, ...]] = set()
    merged_errors: list[dict[str, Any]] = []
    for item in existing_errors + errors:
        key = tuple(item.get(name) for name in ["stage", "url", "source_url", "classification", "error"])
        if key not in error_keys:
            error_keys.add(key)
            merged_errors.append(item)
    payload.update({
        "company_id": company["company_id"],
        "generated_at": now_iso(),
        "sources": all_sources,
        "errors": merged_errors,
        "sales_activation": {
            "version": ACTIVATION_VERSION,
            "captured_page_paths": page_paths,
            "public_journey": journey,
            "workflow": workflow,
            "contacts": contact,
            "source_families_added": sorted({page.get("source_family") for page in pages if page.get("source_family") and page.get("source_family") not in {"company_website:" + domain for domain in _company_domain_set(company)}}),
            "no_outreach_sent": True,
        },
        "headless_policy": {"headless": True, "proxy": DEFAULT_PROXY, "isolated_context": True, "visible_browser_launched": False},
    })
    write_json(package_path, payload)
    notes_path = package_path.parent / "notes.md"
    notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else f"# {company.get('company_name_fa')}\n"
    notes = notes.split("\n## Sales activation", 1)[0].rstrip()
    notes += "\n\n## Sales activation\n\n"
    notes += f"Activation version: {ACTIVATION_VERSION}\n\n"
    notes += "Captured pages:\n" + "\n".join(f"- `{path}`" for path in page_paths) + "\n\n"
    notes += f"Source families added/confirmed: {', '.join(sorted({page.get('source_family') for page in pages if page.get('source_family')})) or 'UNKNOWN'}\n"
    notes += f"Primary workflow classification: {workflow.get('activation_evidence_classification')}\n"
    notes += "No outreach was sent; no contact form, RFQ, email, WhatsApp or phone call was submitted.\n"
    notes_path.write_text(notes, encoding="utf-8")
    return page_paths


def _merge_activation_source_records(company: dict[str, Any], pages: list[dict[str, Any]]) -> None:
    """Add only verified external page references to the canonical record."""
    records = list(company.get("source_records") or [])
    keys = {(item.get("source_url"), item.get("source_family")) for item in records}
    for page in pages:
        family = page.get("source_family")
        url = page.get("url")
        if family not in COUNTED_EXTERNAL_FAMILIES or not url or not page.get("text"):
            continue
        key = (url, family)
        if key in keys:
            continue
        records.append({
            "source_id": "src-" + stable_hash(company["company_id"], url, ACTIVATION_VERSION),
            "company_id": company["company_id"],
            "source_url": url,
            "source_title": page.get("title") or family,
            "source_type": "sales_activation_public_page",
            "source_quality": "public_page",
            "source_family": family,
            "discovery_reason": "Targeted independent source found during first-contact preparation",
            "captured_at": page.get("captured_at") or now_iso(),
        })
        keys.add(key)
    company["source_records"] = records


def _evidence_additions(company: dict[str, Any], claims: list[dict[str, Any]], external_pages: list[dict[str, Any]]) -> None:
    old = company.get("evidence") or []
    keys = {(item.get("source_url"), item.get("claim")) for item in old}
    additions: list[dict[str, Any]] = []
    for item in claims + [_external_claim(company, page) for page in external_pages if page.get("status") and page.get("text")]:
        key = (item.get("source_url"), item.get("claim"))
        if key in keys:
            continue
        keys.add(key)
        additions.append({
            "evidence_id": "ev-" + stable_hash(company["company_id"], item.get("source_url"), item.get("claim"), ACTIVATION_VERSION),
            "company_id": company["company_id"],
            "claim": item.get("claim"),
            "evidence_type": item.get("evidence_type") or "OBSERVED",
            "source_url": item.get("source_url"),
            "source_title": item.get("source_title"),
            "captured_at": now_iso(),
            "confidence": item.get("confidence", 0.6),
            "source_quality": "public_page",
            "quote_or_snippet": clean_text(item.get("quote_or_snippet"), 800),
            "source_family": item.get("source_family") or activation_family(item.get("source_url")),
            "sales_activation_round": ACTIVATION_VERSION,
        })
    company["evidence"] = old + additions


def _activation_source_families(company: dict[str, Any]) -> list[str]:
    values: set[str] = set()
    official_domains = _company_domain_set(company)
    for value in independent_families(company):
        if not value or value in {"search_engine", "other_public"}:
            continue
        if value in COUNTED_EXTERNAL_FAMILIES or value == "book_e_avval":
            values.add(value)
        elif value.startswith("company_website:") and value.split(":", 1)[1] in official_domains:
            values.add(value)
    values.update(value for value in company.get("activation_external_source_families") or [] if value in COUNTED_EXTERNAL_FAMILIES)
    return sorted(values)


def _company_description(company: dict[str, Any]) -> str:
    value = company.get("description_observed") or company.get("description") or ""
    return clean_text(value, 420)


def _activation_score(company: dict[str, Any], workflow: dict[str, Any], contacts: dict[str, Any], official_pages: list[dict[str, Any]], external_pages: list[dict[str, Any]]) -> tuple[int, dict[str, int], list[str]]:
    families = _activation_source_families(company)
    evidence_quality = min(100, 52 + max(0, len(families) - 2) * 12 + (10 if any(page.get("source_family") == "official_registry" for page in external_pages) else 0) + (8 if len(official_pages) >= 2 else 0))
    classification = workflow.get("activation_evidence_classification")
    workflow_clarity = 88 if classification == "EVIDENCE_SUPPORTED" else 74 if classification == "STRONG_HYPOTHESIS" else 52
    pilot_simplicity = 84 if workflow.get("implementation_complexity") == "Medium" else 68
    roi = 82 if len(workflow.get("measurable_KPIs") or []) >= 3 else 66
    named = bool(contacts.get("primary_contact_name") or contacts.get("economic_buyer_name"))
    decision_reach = 92 if contacts.get("primary_contact_name") and contacts.get("economic_buyer_name") else 78 if contacts.get("primary_contact_name") or contacts.get("economic_buyer_name") else 62
    contact_availability = 30 + (25 if contacts.get("public_corporate_phones") else 0) + (25 if contacts.get("public_corporate_emails") else 0) + (12 if contacts.get("public_linkedin_company") else 0) + (8 if contacts.get("public_whatsapp") else 0)
    contact_availability = min(100, contact_availability)
    tech_status = company.get("internal_tech_capability_evidence_status")
    external_fit = 78 if tech_status == "KNOWN_LOW_INTERNAL_TECH" else 60 if tech_status == "UNKNOWN_INTERNAL_TECH" else 52 if tech_status == "KNOWN_MODERATE_INTERNAL_TECH" else 30
    key = _workflow_key(company)
    sales_cycle = 78 if key in {"rfq_quotation", "job_brief_estimate", "parts_catalog_matching", "service_ticket_maintenance"} else 68 if key in {"order_inventory_exceptions", "shipment_document_automation"} else 60
    demo = 86 if official_pages and workflow_clarity >= 74 else 64
    delivery = 82 if pilot_simplicity >= 80 else 70
    components = {
        "evidence_quality": evidence_quality, "workflow_clarity": workflow_clarity, "pilot_simplicity": pilot_simplicity,
        "measurable_roi": roi, "decision_maker_reachability": decision_reach, "corporate_contact_availability": contact_availability,
        "external_software_purchase_fit": external_fit, "sales_cycle_reasonableness": sales_cycle, "demo_concept_strength": demo,
        "luma_delivery_confidence": delivery,
    }
    weights = {"evidence_quality": 15, "workflow_clarity": 15, "pilot_simplicity": 10, "measurable_roi": 10, "decision_maker_reachability": 10, "corporate_contact_availability": 10, "external_software_purchase_fit": 10, "sales_cycle_reasonableness": 5, "demo_concept_strength": 10, "luma_delivery_confidence": 5}
    score = round(sum(components[key] * weights[key] / 100 for key in weights))
    reasons: list[str] = []
    if not named:
        score -= 6
        reasons.append("decision-maker name not publicly verified")
    if not contacts.get("public_corporate_emails") and not contacts.get("public_corporate_phones"):
        score -= 8
        reasons.append("weak public contact coverage")
    if classification == "WEAK_HYPOTHESIS":
        score -= 8
        reasons.append("workflow still broad")
    if workflow.get("implementation_complexity") == "High":
        score -= 4
        reasons.append("pilot requires heavier document/system validation")
    if key in {"medical_equipment", "pharma"}:
        score -= 4
        reasons.append("regulated context requires additional validation")
    if tech_status in {"KNOWN_HIGH_INTERNAL_TECH", "KNOWN_MODERATE_INTERNAL_TECH"}:
        score -= 5
        reasons.append("internal systems capability needs validation")
    return max(0, min(100, score)), components, reasons


def _rank_and_wave(company: dict[str, Any], workflow: dict[str, Any], contacts: dict[str, Any], official_pages: list[dict[str, Any]], external_pages: list[dict[str, Any]]) -> None:
    score, components, reasons = _activation_score(company, workflow, contacts, official_pages, external_pages)
    company["first_contact_score"] = score
    company["first_contact_score_components"] = components
    company["first_contact_score_reasons"] = reasons
    company["first_contact_formula"] = "weighted component average (weights documented in docs/sales_activation.md), less explicit uncertainty penalties"


def _source_urls(company: dict[str, Any], limit: int = 14) -> list[str]:
    values: list[str] = []
    for item in list(company.get("source_records") or []) + list(company.get("evidence") or []):
        url = item.get("source_url")
        if url and url not in values:
            values.append(url)
    return values[:limit]


def _screenshot_paths(company_id: str) -> list[str]:
    directory = path_for("evidence", "companies", company_id, "screenshots")
    if not directory.exists():
        return []
    return sorted(str(path.relative_to(path_for())) for path in directory.glob("*.png") if path.is_file() and not path.name.startswith("._"))


def _md_link(url: str | None, label: str | None = None) -> str:
    return f"[{label or url}]({url})" if url else "اطلاعات عمومی تأییدشده‌ای یافت نشد"


def internal_brief(company: dict[str, Any]) -> str:
    workflow = (company.get("activation_primary_opportunity") or (company.get("workflow_opportunities") or [{}])[0] or {})
    pilot = company.get("activation_pilot") or {}
    demo = company.get("activation_demo") or {}
    contact = company.get("activation_contacts") or {}
    journey = company.get("public_sales_surface") or {}
    facts = company.get("activation_evidence") or []
    lines = [
        f"# Internal sales brief — {company.get('company_name_fa')}", "",
        f"Prepared: {now_iso()}",
        "Scope: existing READY FOR OUTREACH record only. No outreach has been sent.", "",
        "## Company snapshot", "",
        f"- Industry / type: `{company.get('industry')}` / `{company.get('company_type')}`",
        f"- Public description: {company.get('description_observed') or 'UNKNOWN'}",
        f"- Location: {company.get('hq_address') or company.get('city') or 'UNKNOWN'}",
        f"- Commercial score / adjusted score: {company.get('luma_opportunity_score')} / {company.get('confidence_adjusted_score')}",
        f"- First-contact score / wave: {company.get('first_contact_score')} / {company.get('contact_wave')}",
        f"- Source families: {company.get('independent_source_count')} — {', '.join(company.get('independent_source_families') or [])}",
        "",
        "## Evidence", "",
    ]
    lines += [f"- {item.get('claim')} — {_md_link(item.get('source_url'), item.get('source_title') or 'source')}" for item in facts[:8]] or ["- No additional activation evidence was preserved."]
    lines += ["", "## Decision makers", "", f"- Primary business owner: {contact.get('primary_contact_role') or 'UNKNOWN'}; public name: {contact.get('primary_contact_name') or 'UNKNOWN'}; confidence: {contact.get('primary_contact_confidence') or 0}.", f"- Economic buyer: {contact.get('economic_buyer_role') or 'UNKNOWN'}; public name: {contact.get('economic_buyer_name') or 'UNKNOWN'}; confidence: {contact.get('economic_buyer_confidence') or 0}.", f"- Technical gatekeeper: {contact.get('technical_gatekeeper_role') or 'UNKNOWN'}; public name: {contact.get('technical_gatekeeper_name') or 'UNKNOWN'}.", ""]
    lines += ["## Public customer journey", "", *[f"{index}. {step}" for index, step in enumerate(journey.get('observable_steps') or [], 1)], "", "## One primary opportunity", "", f"- Workflow: **{workflow.get('workflow_name')}** / {workflow.get('workflow_name_fa')}", f"- Evidence classification: `{workflow.get('activation_evidence_classification')}`", f"- Hypothesis: {workflow.get('current_process_hypothesis')}", f"- Business owner: {workflow.get('likely_business_owner')}", f"- Evidence: {'; '.join(item.get('claim') or '' for item in workflow.get('supporting_evidence') or [])}", ""]
    lines += ["## Recommended first pilot", "", f"- Name: {pilot.get('pilot_name')}", f"- Scope: {pilot.get('pilot_scope')}", f"- Users: {pilot.get('primary_users')}", f"- Data: {pilot.get('input_data_needed')}", f"- Systems: {pilot.get('existing_systems_to_connect_if_known')}", f"- LUMA builds: {pilot.get('what_luma_builds')}", f"- Approval points: {pilot.get('human_approval_points')}", f"- Duration estimate: {pilot.get('pilot_duration_estimate')}", f"- Success metrics: {', '.join(pilot.get('success_metrics') or [])}", f"- Expansion: {pilot.get('expansion_path')}", ""]
    lines += ["## Demo concept", "", demo.get('demo_concept') or "UNKNOWN", "", "## Uncertainty / objections", "", *[f"- {item}" for item in (pilot.get('risks') or [])], "- Budget, volume, authority, system ownership and current baseline are not publicly established.", "- Do not say the company currently performs a manual or inefficient process; ask discovery questions first.", ""]
    lines += ["## Discovery questions", "", *[f"{index}. {question}" for index, question in enumerate(workflow.get('discovery_questions') or [], 1)], "", "## Sales angle", "", f"Lead with the public {workflow.get('workflow_name_fa')} surface and the bounded pilot. Ask for the person who owns the process, not IT first unless the company directs the conversation there.", "", "## Contact channels", "", f"- Website: {_md_link(company.get('website') or next((item.get('source_url') for item in company.get('source_records') or [] if str(item.get('source_family') or '').startswith('company_website:')), None))}", f"- Phone: {', '.join(contact.get('public_corporate_phones') or []) or 'UNKNOWN'}", f"- Corporate email: {', '.join(contact.get('public_corporate_emails') or []) or 'UNKNOWN'}", f"- LinkedIn company: {_md_link(contact.get('public_linkedin_company'))}", f"- WhatsApp: {_md_link(contact.get('public_whatsapp')) if contact.get('public_whatsapp') else 'No explicitly published business WhatsApp found; do not infer one.'}", "", "## Ranking rationale", "", f"- First-contact score: {company.get('first_contact_score')}/100", f"- Components: {json.dumps(company.get('first_contact_score_components') or {}, ensure_ascii=False, sort_keys=True)}", f"- Penalties/uncertainties: {', '.join(company.get('first_contact_score_reasons') or []) or 'None'}", "", "## Evidence paths", "", f"- Package: `evidence/companies/{company.get('company_id')}/sources.json`", f"- Screenshots: {', '.join('`' + value + '`' for value in _screenshot_paths(company['company_id'])) or 'UNKNOWN'}", f"- Client one-pager: `sales/client/{company.get('company_id')}.md`", f"- Outreach draft: `sales/outreach/{company.get('company_id')}.md`", ""]
    return "\n".join(lines)


def client_one_pager(company: dict[str, Any]) -> str:
    workflow = company.get("activation_primary_opportunity") or {}
    pilot = company.get("activation_pilot") or {}
    journey = company.get("public_sales_surface") or {}
    profile = WORKFLOW_PROFILES.get(_workflow_key(company), WORKFLOW_PROFILES["rfq_quotation"])
    key = _workflow_key(company)
    name = company.get("company_name_fa")
    opportunity_intro = {
        "rfq_quotation": f"با توجه به تنوع محصولات و مسیر عمومی دریافت اطلاعات و استعلام در {name}، یکی از فرایندهایی که ارزش بررسی دارد، تبدیل درخواست‌های ورودی به پاسخ تجاریِ ساختاریافته است.",
        "shipment_document_automation": f"با توجه به گستردگی خدمات حمل و ترخیص {name}، یکی از فرایندهایی که ارزش بررسی دارد، ساختاردهی اسناد پرونده و پیگیری موارد ناقص است.",
        "boq_specification_matching": f"با توجه به فعالیت مهندسی، تأمین یا پروژه‌ای {name}، یکی از فرایندهایی که ارزش بررسی دارد، تبدیل BOQ و مشخصات فنی به بسته پیشنهادی قابل بازبینی است.",
        "order_inventory_exceptions": f"با توجه به سطح محصولات و فعالیت توزیعی {name}، یکی از فرایندهایی که ارزش بررسی دارد، یکپارچه‌کردن ورودی سفارش و دیدن استثناهای موجودی است.",
        "production_quality_reporting": f"با توجه به فعالیت تولیدی و محصولی {name}، یکی از فرایندهایی که ارزش بررسی دارد، استانداردسازی گزارش‌های تولید، کیفیت و توقفات است.",
        "service_ticket_maintenance": f"با توجه به خدمات تخصصی و نگهداری {name}، یکی از فرایندهایی که ارزش بررسی دارد، ثبت ساختاریافته درخواست و دسترسی سریع به دانش تأییدشده است.",
        "job_brief_estimate": f"با توجه به سفارش‌های سفارشی و خدمات بسته‌بندی {name}، یکی از فرایندهایی که ارزش بررسی دارد، تبدیل بریف مشتری به برگه برآورد و تحویل تولید است.",
        "parts_catalog_matching": f"با توجه به تنوع قطعات و اطلاعات فنی {name}، یکی از فرایندهایی که ارزش بررسی دارد، جست‌وجو و تطبیق سریع قطعه برای تأیید فروش است.",
    }.get(_workflow_key(company), f"با توجه به فعالیت‌های {name}، یکی از فرایندهایی که ارزش بررسی دارد، ساختاردهی یک گردش عملیاتی پرتکرار است.")
    lines = [
        f"# پیشنهاد اولیه برای {name}", "",
        "## فرصت", "", opportunity_intro,
        "این پیشنهاد، یک نقطه شروع محدود برای گفت‌وگوست و پس از شناخت مسیر فعلی شما دقیق‌تر می‌شود.", "",
        "## راهکار پیشنهادی", "", profile["solution_fa"], "",
        "## نحوه کار", "",
        *[f"{index}. {step}" for index, step in enumerate(CLIENT_STAGES_FA.get(key, CLIENT_STAGES_FA["rfq_quotation"]), 1)],
        "", "## نتیجه‌ای که باید اندازه‌گیری شود", "",
        *[f"- {metric}" for metric in profile["kpis_fa"]],
        "", "## پیشنهاد شروع", "", pilot.get("pilot_scope") or "یک مسیر محدود با نمونه داده و کاربر مشخص انتخاب می‌شود.", f"دامنه پیشنهادی: {pilot.get('pilot_name') or profile['pilot_fa']}", "", "## مرحله بعد", "", "یک جلسه کوتاه برای دیدن یک نمونه واقعی، شناخت حجم و منابع داده، مشخص‌کردن مالک فرایند و انتخاب دامنه پایلوت.", "", "LUMA",
    ]
    return "\n".join(lines) + "\n"


def outreach_package(company: dict[str, Any]) -> str:
    workflow = company.get("activation_primary_opportunity") or {}
    key = _workflow_key(company)
    profile = WORKFLOW_PROFILES.get(key, WORKFLOW_PROFILES["rfq_quotation"])
    contact = company.get("activation_contacts") or {}
    name = company.get("company_name_fa")
    owner = OWNER_FA.get(key, "مدیر مربوط به این فرایند")
    opening = {
        "rfq_quotation": f"سلام وقت بخیر. من از لاما تماس می‌گیرم. ما روی ساخت ابزارهای اختصاصی برای کوتاه‌تر و قابل‌ردیابی‌تر شدن فرایندهای فروش کار می‌کنیم. با توجه به تنوع محصولات و ماهیت فروش تخصصی مجموعه {name}، یکی از فرایندهایی که ارزش بررسی دارد، تبدیل درخواست‌های ورودی به پاسخ تجاری ساختاریافته است. برای همین نوع فرایند یک نمایش کوچک آماده کرده‌ایم و می‌توانیم در یک گفت‌وگوی ۱۵ تا ۲۰ دقیقه‌ای نشانش دهیم؛ این نمونه از داده عمومی و داده ساختگی استفاده می‌کند و ادعایی درباره فرایند داخلی شما ندارد. اگر شما مالک این فرایند هستید، خوشحال می‌شویم گفت‌وگو را با شناخت مسیر فعلی و یک نمونه واقعی ادامه دهیم.",
        "shipment_document_automation": f"سلام وقت بخیر. من از لاما تماس می‌گیرم. با توجه به خدمات حمل و ترخیص {name}، یکی از نقاطی که می‌شود بدون تغییر هسته کار بررسی کرد، ساختاردهی اسناد پرونده و پیگیری نقص‌هاست. اگر شما مسئول عملیات یا اسناد هستید، پیشنهاد ما یک گفت‌وگوی کوتاه برای شناخت مسیر فعلی و انتخاب یک نمونه محدود است.",
        "boq_specification_matching": f"سلام وقت بخیر. من از لاما تماس می‌گیرم. با توجه به فعالیت پروژه‌ای و فنی {name}، می‌خواهیم یک نمونه کوچک از تبدیل BOQ و مشخصات فنی به بسته قابل بازبینی را بررسی کنیم. اگر شما مالک دفتر فنی یا فروش پروژه هستید، یک جلسه کوتاه برای شناخت مسیر فعلی مناسب است.",
        "order_inventory_exceptions": f"سلام وقت بخیر. من از لاما تماس می‌گیرم. در مجموعه‌هایی با ورودی سفارش و موجودی متعدد، یک نقطه قابل بررسی، جداکردن استثناهای سفارش و موجودی از گزارش‌های روزمره است. با توجه به فعالیت {name}، اگر شما مسئول عملیات فروش یا پخش هستید، خوشحال می‌شویم یک نمونه واقعی را در گفت‌وگویی کوتاه ببینیم.",
        "production_quality_reporting": f"سلام وقت بخیر. من از لاما تماس می‌گیرم. با توجه به فعالیت تولیدی {name}، یکی از نقاط قابل بررسی می‌تواند استانداردسازی گزارش‌های شیفت، کیفیت و توقفات در یک مسیر محدود باشد. اگر شما مالک عملیات یا کارخانه هستید، پیشنهاد می‌کنیم ابتدا فقط نمونه گزارش‌ها و شاخص‌های فعلی را بشناسیم.",
        "service_ticket_maintenance": f"سلام وقت بخیر. من از لاما تماس می‌گیرم. با توجه به خدمات نگهداری و تعمیرات {name}، ساختاردهی درخواست‌های سرویس و بازیابی راهنمای تأییدشده می‌تواند یک نقطه قابل بررسی باشد. اگر شما مسئول خدمات هستید، مایل هستیم در یک جلسه کوتاه مسیر فعلی را بفهمیم.",
        "job_brief_estimate": f"سلام وقت بخیر. من از لاما تماس می‌گیرم. با توجه به سفارش‌های سفارشی و بسته‌بندی {name}، تبدیل بریف مشتری به برگه برآورد و تحویل تولید می‌تواند یک پایلوت محدود و قابل سنجش باشد. اگر شما مسئول برآورد یا تولید هستید، خوشحال می‌شویم یک نمونه پاک‌سازی‌شده را بررسی کنیم.",
        "parts_catalog_matching": f"سلام وقت بخیر. من از لاما تماس می‌گیرم. با توجه به تنوع قطعات و اطلاعات فنی {name}، یک دستیار جست‌وجو و تطبیق قطعه می‌تواند نقطه شروع گفت‌وگو باشد. اگر شما مسئول فروش یا عملیات هستید، پیشنهاد می‌کنیم با چند نمونه واقعی و بدون دسترسی حساس شروع کنیم.",
    }.get(_workflow_key(company), f"سلام وقت بخیر. من از لاما تماس می‌گیرم. با توجه به فعالیت {name}، یک فرایند عملیاتی پرتکرار را می‌توان در قالب یک پایلوت محدود بررسی کرد. اگر شما مالک این فرایند هستید، خوشحال می‌شویم در گفت‌وگویی کوتاه مسیر فعلی را بشناسیم.")
    email_subject = f"پیشنهاد بررسی یک پایلوت عملیاتی برای {name}"
    if key == "rfq_quotation":
        email_body = f"سلام وقت بخیر،\n\nما در LUMA ابزارهای اختصاصی برای ساختاردهی فرایندهای عملیاتی و فروش می‌سازیم. با توجه به تنوع محصولات و ماهیت فروش تخصصی مجموعه {name}، یکی از فرایندهایی که ارزش بررسی دارد، تبدیل درخواست‌های ورودی به پاسخ تجاری ساختاریافته است. برای همین موضوع یک نمایش کوچک و مشخص آماده کرده‌ایم که می‌توانیم در یک جلسه ۱۵ تا ۲۰ دقیقه‌ای ارائه کنیم. این نمونه با داده عمومی و نمونه‌های کاملاً ساختگی ساخته شده و ادعایی درباره فرایند داخلی {name} ندارد.\n\nاگر شما {owner} هستید یا همکار مناسب را معرفی می‌کنید، خوشحال می‌شویم یک گفت‌وگوی کوتاه برای شناخت مسیر فعلی و انتخاب دامنه پایلوت داشته باشیم.\n\nبا احترام\nLUMA"
        linkedin = f"سلام، ما در LUMA برای ساختاردهی فرایندهای عملیاتی و فروش ابزار اختصاصی می‌سازیم. با توجه به تنوع محصولات و ماهیت فروش تخصصی مجموعه {name}، یک نمایش کوتاه برای تبدیل درخواست‌های ورودی به پاسخ ساختاریافته آماده کرده‌ایم. اگر مالک این فرایند را معرفی کنید، خوشحال می‌شویم در یک گفت‌وگوی کوتاه نمونه را نشان دهیم."
        followup = f"سلام وقت بخیر، پیرو پیام قبلی درباره نمایش کوتاه ساختاردهی درخواست‌های ورودی در {name}، اگر این موضوع نزد شما یا همکار دیگری است، ممنون می‌شوم مسیر درست گفت‌وگو را معرفی کنید. در غیر این صورت مزاحم نمی‌شویم."
    else:
        email_body = f"سلام وقت بخیر،\n\nبا توجه به {profile['fa_name']} در {name}، یک نقطه قابل بررسی، اجرای محدود همین فرایند با داده و کاربر مشخص است. لاما در این مرحله پیشنهاد پروژه بزرگ یا جایگزینی سامانه‌های اصلی را ندارد؛ هدف، بررسی یک نمونه واقعی و سنجش شاخص‌هایی مانند {('، '.join(profile['kpis_fa'][:3]))} در یک دامنه محدود است.\n\nاگر شما {owner} هستید یا همکار مناسب را معرفی می‌کنید، مایل هستیم یک جلسه کوتاه برای شناخت مسیر فعلی و انتخاب دامنه پایلوت داشته باشیم.\n\nبا احترام\nLUMA"
        linkedin = f"سلام، با توجه به فعالیت {name} در حوزه {company.get('industry_fa') or company.get('industry')}، یک نقطه قابل بررسی برای ما {profile['fa_name']} است. اگر مالک این فرایند را معرفی کنید، خوشحال می‌شویم با یک نمونه کوچک و قابل سنجش گفت‌وگو را شروع کنیم."
        followup = f"سلام وقت بخیر، پیرو پیام قبلی درباره بررسی محدود {profile['fa_name']} در {name}، اگر این موضوع نزد شما یا همکار دیگری است، ممنون می‌شوم مسیر درست گفت‌وگو را معرفی کنید. در غیر این صورت مزاحم نمی‌شویم."
    whatsapp = "کانال واتساپ شرکتی به‌صورت عمومی تأیید نشده است؛ پیام واتساپ ارسال نشود."
    return "\n".join([
        f"# Outreach draft — {name}", "", "این فایل آماده‌سازی داخلی است. هیچ پیام یا تماسی ارسال نشده است.", "", f"## هدف ارتباط", f"- نقش پیشنهادی: {owner}", f"- کانال ترجیحی: {company.get('preferred_channel')}", "", "## PHONE OPENING", "", opening, "", "## EMAIL", "", f"Subject: {email_subject}", "", email_body, "", "## LINKEDIN", "", linkedin, "", "## WHATSAPP", "", whatsapp, "", "## FOLLOW-UP", "", followup, "", "## Public channels", "", f"- Phone: {', '.join(contact.get('public_corporate_phones') or []) or 'UNKNOWN'}", f"- Email: {', '.join(contact.get('public_corporate_emails') or []) or 'UNKNOWN'}", f"- LinkedIn: {_md_link(contact.get('public_linkedin_company'))}", f"- Contact form: use only after approval and a human-led plan; do not submit automatically.", ""])


def visual_readme(company: dict[str, Any]) -> str:
    screenshots = _screenshot_paths(company["company_id"])
    workflow = company.get("activation_primary_opportunity") or {}
    official = (company.get("public_sales_surface") or {}).get("evidence") or []
    strongest = screenshots[0] if screenshots else "No existing screenshot found"
    return "\n".join([
        f"# Visual sales asset index — {company.get('company_name_fa')}", "", "These are internal references only. Existing public-page screenshots are reused; no synthetic evidence or client collateral image was generated.", "", "## Strongest existing screenshot", "", f"- `{strongest}`", "- Demonstrates: the public company/product/service surface captured in the existing evidence package.", "- Use externally: do not send the screenshot without a human review of copyright, context and currentness.", "", "## Screenshot that should not be shown externally", "", "- Any screenshot containing directory UI, search-provider chrome, error pages, private contact information or third-party promotional content.", "", "## Public product/service visual", "", f"- Use the public page references in `evidence/companies/{company.get('company_id')}/sources.json` to understand the business. Do not redistribute website imagery into the client one-pager by default.", *[f"- {_md_link(item.get('source_url'), item.get('source_title') or 'public page')}" for item in official[:3]], "", "## Recommended demo UI concept", "", workflow.get("workflow_name_fa") or "یک گردش کار محدود با ورودی، پیشنهاد قابل توضیح و تأیید انسانی.", "", "## Review note", "", "Wave 1 assets require human review before any external presentation. No outreach has been sent.", ""])


def sales_dossier(company: dict[str, Any], rank: int) -> str:
    workflow = company.get("activation_primary_opportunity") or {}
    pilot = company.get("activation_pilot") or {}
    demo = company.get("activation_demo") or {}
    contact = company.get("activation_contacts") or {}
    evidence = company.get("activation_evidence") or []
    screenshots = _screenshot_paths(company["company_id"])
    recommendation = "GO" if company.get("contact_wave") == "WAVE 1" and workflow.get("activation_evidence_classification") in {"EVIDENCE_SUPPORTED", "STRONG_HYPOTHESIS"} else "DISCOVERY FIRST"
    name_source = contact.get("economic_buyer_source_url") if contact.get("economic_buyer_name") else contact.get("primary_contact_source_url")
    lines = [
        f"# {company.get('company_name_fa')}", "",
        f"Dossier rank: {rank} | First-contact score: {company.get('first_contact_score')}/100 | Wave: {company.get('contact_wave')}",
        "This is an internal sales preparation document. No outreach has been sent.", "",
        "## Snapshot", "",
        f"- What the company publicly presents: {company.get('description_observed') or company.get('description') or 'No concise public description was preserved.'}",
        f"- Corrected classification: `{company.get('industry')}` / `{company.get('company_type')}`; B2B signal: `{company.get('b2b_b2c') or company.get('business_model') or 'not established'}`",
        f"- Location: {company.get('hq_address') or company.get('city') or 'not established'}",
        f"- Public website: {_md_link(company.get('website'))}",
        f"- Commercial evidence strength: {company.get('commercial_evidence_strength', 'not recalculated in this activation pass')}",
        f"- Independent source families counted: {company.get('independent_source_count')} — {', '.join(company.get('independent_source_families') or [])}", "",
        "## Why it is commercially interesting", "",
        f"The public record supports a conversation around **{workflow.get('workflow_name_fa')}**. The attraction is the possibility of a bounded process improvement around {workflow.get('primary_users_fa') or workflow.get('primary_users')}, while leaving the company's core systems and final decisions under human control.",
        "This is a sales hypothesis, not a claim that the company currently has a known inefficiency.", "",
        "## Evidence", "",
    ]
    lines += [f"- {item.get('claim')} — {_md_link(item.get('source_url'), item.get('source_title') or 'source')}" for item in evidence[:8]] or ["- No additional activation evidence was preserved."]
    lines += ["", "## Likely operational bottleneck", "", f"**Inference to validate:** incoming information may need repeated lookup, structuring or approval before the business team can produce the final output described by **{workflow.get('workflow_name_fa')}**. Public pages establish the customer-facing surface, not the internal handoff, volume or baseline.", "", "## Recommended LUMA solution", "", f"**{workflow.get('workflow_name_fa')}** — {workflow.get('proposed_luma_solution_fa')}", "", "## Why this solution could matter financially", "", "Measure the baseline and pilot change in terms of:"]
    lines += [f"- {metric}" for metric in workflow.get("measurable_KPIs_fa") or workflow.get("measurable_KPIs") or ["cycle time", "rework/correction volume", "throughput", "exception closure"]]
    lines += ["", "## What we do not know", "", "- Monthly volume, current handoffs, approval rules and baseline time are not public.", "- The authoritative data owner and integration surface are not public.", "- Budget authority, buying process and timing are not public.", "- Internal software/data capability is not sufficiently established publicly; missing evidence is not treated as evidence of absence.", "", "## Questions to ask", ""]
    questions = list(workflow.get("discovery_questions") or [])
    questions += ["چه کسی مالک این فرایند و تأیید خروجی نهایی است؟", "یک نمونه واقعی و پاک‌سازی‌شده برای مقایسه خط مبنا و پایلوت کدام است؟", "اگر پایلوت موفق باشد، گسترش آن به کدام واحد یا قالب بیشترین ارزش را دارد؟"]
    lines += [f"{index}. {question}" for index, question in enumerate(questions[:8], 1)]
    lines += ["", "## Decision maker", "", f"- Primary business owner: {contact.get('primary_contact_role') or workflow.get('likely_business_owner') or 'Role to validate'}; public name: {contact.get('primary_contact_name') or 'Not publicly verified'}.", f"- Economic buyer: {contact.get('economic_buyer_role') or 'Managing Director / CEO'}; public name: {contact.get('economic_buyer_name') or 'Not publicly verified'}.", f"- Technical gatekeeper: {contact.get('technical_gatekeeper_role') or 'Only identify after process owner is engaged'}; public name: {contact.get('technical_gatekeeper_name') or 'Not publicly verified'}."]
    if name_source:
        lines.append(f"- Verified-name source: {_md_link(name_source, contact.get('economic_buyer_name') or contact.get('primary_contact_name'))}")
    lines += ["", "## Contact channels", f"- Website: {_md_link(company.get('website'))}", f"- Public phone: {', '.join(contact.get('public_corporate_phones') or []) or 'Not preserved'}", f"- Corporate email: {', '.join(contact.get('public_corporate_emails') or []) or 'Not preserved'}", f"- Company LinkedIn: {_md_link(contact.get('public_linkedin_company'))}", f"- Public WhatsApp: {_md_link(contact.get('public_whatsapp')) if contact.get('public_whatsapp') else 'Not explicitly published'}", "", "## Pilot and demo", "", f"- Pilot: {pilot.get('pilot_name')}", f"- Scope: {pilot.get('pilot_scope')}", f"- Users: {pilot.get('primary_users')}", f"- Data: {pilot.get('input_data_needed')}", f"- Human approval: {pilot.get('human_approval_points')}", f"- Duration: {pilot.get('pilot_duration_estimate')}", f"- Demo: {demo.get('demo_concept')}", "", "## Screenshots", ""]
    lines += [f"- `{path}`" for path in screenshots] or ["- No existing screenshot was found for this company."]
    lines += ["", "## Sales recommendation", "", f"**{recommendation}** — use the internal brief and outreach draft only after human review. Proposal: `sales/client/{company.get('company_id')}.md`; outreach draft: `sales/outreach/{company.get('company_id')}.md`.", ""]
    return "\n".join(lines)


def write_dossiers(companies: list[dict[str, Any]], limit: int = 30) -> list[dict[str, Any]]:
    ranked = sorted(companies, key=lambda row: (-int(row.get("first_contact_score") or 0), -float(row.get("confidence_adjusted_score") or 0), str(row.get("company_name_fa") or "")))
    directory = path_for("reports", "dossiers")
    directory.mkdir(parents=True, exist_ok=True)
    selected = ranked[:limit]
    manifest = ["# Sales dossier index", "", f"Current activation dossier set: top {len(selected)} of the 32 READY FOR OUTREACH companies, ranked by first-contact score.", "", "| Rank | Company | Score | Wave | Dossier |", "|---:|---|---:|---|---|"]
    for rank, company in enumerate(selected, 1):
        company["dossier_rank"] = rank
        cid = company["company_id"]
        (directory / f"{cid}.md").write_text(sales_dossier(company, rank), encoding="utf-8")
        manifest.append(f"| {rank} | {company.get('company_name_fa')} | {company.get('first_contact_score')} | {company.get('contact_wave')} | `{cid}.md` |")
    manifest += ["", "Files not listed above are retained for historical audit context and are not part of this activation top-30 set.", ""]
    (directory / "README.md").write_text("\n".join(manifest), encoding="utf-8")
    return selected


def write_sales_artifacts(companies: list[dict[str, Any]]) -> None:
    rows = [company for company in companies if company.get("commercial_readiness") == "READY FOR OUTREACH"]
    ranked = sorted(rows, key=lambda row: (-int(row.get("first_contact_score") or 0), -float(row.get("confidence_adjusted_score") or 0), str(row.get("company_name_fa") or "")))
    for index, company in enumerate(ranked, 1):
        company["contact_wave"] = "WAVE 1" if index <= 10 else "WAVE 2" if index <= 20 else "WAVE 3"
        company["wave_rank"] = index
    # Update the ranking only after wave assignment so generated documents agree
    # with the tracker.
    for company in rows:
        cid = company["company_id"]
        (path_for("sales", "internal")).mkdir(parents=True, exist_ok=True)
        (path_for("sales", "client")).mkdir(parents=True, exist_ok=True)
        (path_for("sales", "outreach")).mkdir(parents=True, exist_ok=True)
        (path_for("sales", "visual", cid)).mkdir(parents=True, exist_ok=True)
        (path_for("sales", "internal", f"{cid}.md")).write_text(internal_brief(company), encoding="utf-8")
        (path_for("sales", "client", f"{cid}.md")).write_text(client_one_pager(company), encoding="utf-8")
        (path_for("sales", "outreach", f"{cid}.md")).write_text(outreach_package(company), encoding="utf-8")
        (path_for("sales", "visual", cid, "README.md")).write_text(visual_readme(company), encoding="utf-8")


def _tracker_row(company: dict[str, Any]) -> dict[str, Any]:
    contact = company.get("activation_contacts") or {}
    workflow = company.get("activation_primary_opportunity") or {}
    cid = company["company_id"]
    website = company.get("website") or next((item.get("source_url") for item in company.get("source_records") or [] if str(item.get("source_family") or "").startswith("company_website:")), "")
    return {
        "company_id": cid,
        "company_name": company.get("company_name_fa"),
        "wave": company.get("contact_wave"),
        "first_contact_score": company.get("first_contact_score"),
        "industry": company.get("industry"),
        "website": website,
        "primary_contact_role": contact.get("primary_contact_role"),
        "primary_contact_name": contact.get("primary_contact_name"),
        "economic_buyer_role": contact.get("economic_buyer_role"),
        "economic_buyer_name": contact.get("economic_buyer_name"),
        "phone": ", ".join(contact.get("public_corporate_phones") or []),
        "email": ", ".join(contact.get("public_corporate_emails") or []),
        "linkedin": contact.get("public_linkedin_company"),
        "whatsapp": contact.get("public_whatsapp"),
        "preferred_channel": company.get("preferred_channel"),
        "primary_opportunity": workflow.get("workflow_name_fa") or workflow.get("workflow_name"),
        "pilot_name": (company.get("activation_pilot") or {}).get("pilot_name"),
        "proposal_path": f"sales/client/{cid}.md",
        "outreach_path": f"sales/outreach/{cid}.md",
        "dossier_path": f"reports/dossiers/{cid}.md",
        "status": "NOT_CONTACTED",
        "last_contact_date": "",
        "next_action": "Human review of internal brief and approval of first outreach",
        "next_action_date": "",
        "notes": "No outreach sent. Validate role, volume, data owner and pilot sample before contact.",
    }


def write_tracker_csv(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    import csv

    columns = ["company_id", "company_name", "wave", "first_contact_score", "industry", "website", "primary_contact_role", "primary_contact_name", "economic_buyer_role", "economic_buyer_name", "phone", "email", "linkedin", "whatsapp", "preferred_channel", "primary_opportunity", "pilot_name", "proposal_path", "outreach_path", "dossier_path", "status", "last_contact_date", "next_action", "next_action_date", "notes"]
    rows = sorted([_tracker_row(company) for company in companies if company.get("commercial_readiness") == "READY FOR OUTREACH"], key=lambda row: (row.get("wave") or "", -int(row.get("first_contact_score") or 0), row.get("company_name") or ""))
    output = path_for("data", "outreach_pipeline.csv")
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def _preflight(proxy: str) -> bool:
    result = subprocess.run([sys.executable, "-m", "src.utilities.network_preflight", "--proxy", proxy, "--target", "https://didmeet.ir/", "--ip-endpoint", "https://api.ipify.org"], capture_output=True, text=True, check=False)
    print(result.stdout[-3500:])
    return result.returncode == 0


def collect_and_augment(companies: list[dict[str, Any]], *, proxy: str, rate_limit: float, timeout: float, max_official: int, max_external: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    targets = [company for company in companies if company.get("commercial_readiness") == "READY FOR OUTREACH"]
    if len(targets) != EXPECTED_READY:
        raise RuntimeError(f"Expected exactly {EXPECTED_READY} current READY records; found {len(targets)}. No activation run performed.")
    limiter = RateLimiter(rate_limit)
    research_rows: list[dict[str, Any]] = []
    counts = Counter()
    updated: dict[str, dict[str, Any]] = {}
    for number, original in enumerate(targets, 1):
        company = dict(original)
        cid = company["company_id"]
        print(f"[{number}/{len(targets)}] {company.get('company_name_fa')}", flush=True)
        official_pages: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for url in _official_urls(company, max_official):
            response = fetch_cached(url, proxy=proxy, limiter=limiter, timeout=timeout, max_bytes=2_500_000)
            page = _extract_page(url, response, kind="official_page")
            if _usable_status(page.get("status")) and _page_matches_company(company, page, allow_official=True):
                official_pages.append(page)
            else:
                errors.append({"stage": "official_page", "url": url, "error": page.get("error") or "No HTTP status", "classification": "SOURCE_ERROR"})
        search_pages: list[dict[str, Any]] = []
        for query in query_variants(company):
            url = activation_search_url(query)
            response = fetch_cached(url, proxy=proxy, limiter=limiter, timeout=timeout, max_bytes=1_500_000)
            page = _extract_page(url, response, kind="search_query", query=query)
            page["_body"] = response.get("body") or ""
            if _usable_status(page.get("status")) and not _search_blocked(page):
                search_pages.append(page)
            else:
                errors.append({"stage": "search_query", "url": url, "error": page.get("error") or "Search provider returned a challenge or no usable result page", "classification": "SEARCH_ENGINE_BLOCKED" if _search_blocked(page) else "SOURCE_ERROR"})
        external_specs = _external_candidates(company, search_pages, max_external)
        external_pages: list[dict[str, Any]] = []
        for spec in external_specs:
            response = fetch_cached(spec["url"], proxy=proxy, limiter=limiter, timeout=timeout, max_bytes=2_500_000)
            page = _extract_page(spec["url"], response, kind="external_page", query=spec.get("query"))
            page["source_family"] = spec.get("family") or page.get("source_family")
            page["search_title"] = spec.get("title")
            page["search_snippet"] = spec.get("snippet")
            if _usable_status(page.get("status")) and _page_matches_company(company, page):
                external_pages.append(page)
            elif _usable_status(page.get("status")):
                errors.append({"stage": "external_page", "url": spec["url"], "error": "Company identity was not sufficiently confirmed on the fetched page", "classification": "IDENTITY_UNCONFIRMED"})
            else:
                errors.append({"stage": "external_page", "url": spec["url"], "error": page.get("error") or "No HTTP status", "classification": "SOURCE_ERROR"})
        claims = _surface_claims(company, official_pages)
        _evidence_additions(company, claims, external_pages)
        contacts = _extract_contacts(company, official_pages, external_pages, search_pages)
        workflow = _workflow(company, official_pages, claims)
        pilot = _pilot(company, workflow, contacts)
        demo = _demo(company, workflow, official_pages)
        journey = _journey(company, official_pages, claims, contacts)
        _merge_evidence_package(company, official_pages + external_pages, claims, errors, contacts, journey, workflow)
        company["activation_contacts"] = contacts
        company["primary_contact_role"] = contacts["primary_contact_role"]
        company["primary_contact_name"] = contacts["primary_contact_name"]
        company["primary_contact_source_url"] = contacts["primary_contact_source_url"]
        company["economic_buyer_role"] = contacts["economic_buyer_role"]
        company["economic_buyer_name"] = contacts["economic_buyer_name"]
        company["economic_buyer_source_url"] = contacts["economic_buyer_source_url"]
        company["technical_gatekeeper_role"] = contacts["technical_gatekeeper_role"]
        company["technical_gatekeeper_name"] = contacts["technical_gatekeeper_name"]
        company["activation_primary_opportunity"] = workflow
        company["workflow_opportunities"] = [workflow]
        company["workflow_evidence_classification"] = workflow["activation_evidence_classification"]
        company["strongest_workflow"] = workflow["workflow_name"]
        company["activation_pilot"] = pilot
        company["activation_demo"] = demo
        company["public_sales_surface"] = journey
        company["activation_evidence"] = claims + [_external_claim(company, page) for page in external_pages]
        company["activation_page_paths"] = sorted({str(Path("evidence") / path) for path in _list_activation_page_paths(cid)})
        company["activation_external_source_families"] = sorted({page.get("source_family") for page in external_pages if page.get("source_family")})
        _merge_activation_source_records(company, external_pages)
        company["independent_source_families"] = _activation_source_families(company)
        company["independent_source_count"] = len(company["independent_source_families"])
        company["activation_research_date"] = now_iso()
        company["activation_version"] = ACTIVATION_VERSION
        company["activation_public_email"] = ", ".join(contacts.get("public_corporate_emails") or [])
        company["activation_public_phone"] = ", ".join(contacts.get("public_corporate_phones") or [])
        company["activation_linkedin_company"] = contacts.get("public_linkedin_company")
        company["activation_whatsapp"] = contacts.get("public_whatsapp")
        company["preferred_channel"] = "EMAIL" if contacts.get("public_corporate_emails") else "PHONE" if contacts.get("public_corporate_phones") else "LINKEDIN" if contacts.get("public_linkedin_company") else "WEB_FORM"
        company["activation_errors"] = errors
        company["activation_status"] = "PUBLIC_SURFACE_RESEARCHED" if official_pages or external_pages else "CONTACT_ONLY"
        company["activation_evidence_source_count"] = len(claims) + sum(1 for page in external_pages if page.get("status"))
        _rank_and_wave(company, workflow, contacts, official_pages, external_pages)
        updated[cid] = company
        counts.update({"official_pages_ok": len(official_pages), "external_pages_ok": len(external_pages), "search_pages_ok": len(search_pages), "errors": len(errors), "decision_names": int(bool(contacts.get("primary_contact_name") or contacts.get("economic_buyer_name"))), "three_plus_families": int(company["independent_source_count"] >= 3)})
        search_compact = [{key: value for key, value in page.items() if key != "_body"} for page in search_pages]
        for page in search_compact:
            page.pop("text", None)
            page.pop("links", None)
        research_rows.append({"company_id": cid, "company_name_fa": company.get("company_name_fa"), "captured_at": now_iso(), "official_pages": [{key: value for key, value in page.items() if key not in {"text", "links"}} for page in official_pages], "external_pages": [{key: value for key, value in page.items() if key not in {"text", "links"}} for page in external_pages], "search_pages": search_compact, "errors": errors, "source_families": company.get("independent_source_families"), "decision_maker_direct_candidates": contacts.get("decision_maker_direct_candidates"), "decision_maker_search_candidates": contacts.get("decision_maker_search_candidates")})
    output = [updated.get(company.get("company_id"), company) for company in companies]
    write_jsonl(path_for("data", "normalized", "companies.jsonl"), output)
    write_jsonl(path_for("data", "raw", "sales_activation_research.jsonl"), research_rows)
    return output, {"target_companies": len(targets), **counts, "source_family_distribution": dict(Counter(family for company in targets for family in updated[company["company_id"]].get("activation_external_source_families") or [])), "decision_maker_names_verified": sum(bool(updated[company["company_id"]].get("primary_contact_name") or updated[company["company_id"]].get("economic_buyer_name")) for company in targets), "companies_with_three_plus_source_families": sum(updated[company["company_id"]].get("independent_source_count", 0) >= 3 for company in targets)}


def _list_activation_page_paths(company_id: str) -> list[str]:
    directory = path_for("evidence", "companies", company_id, "pages")
    if not directory.exists():
        return []
    return [str(item.relative_to(path_for("evidence"))) for item in directory.glob("sales-*.txt") if item.is_file() and not item.name.startswith("._")]


def build_reports(companies: list[dict[str, Any]]) -> dict[str, Any]:
    targets = [company for company in companies if company.get("commercial_readiness") == "READY FOR OUTREACH"]
    write_sales_artifacts(targets)
    write_dossiers(targets, limit=30)
    # Wave and rank fields are part of the canonical activation output, not
    # only transient tracker values.
    write_jsonl(path_for("data", "normalized", "companies.jsonl"), companies)
    rows = write_tracker_csv(targets)
    waves = Counter(row["wave"] for row in rows)
    first_contact = sorted(targets, key=lambda row: (-int(row.get("first_contact_score") or 0), -float(row.get("confidence_adjusted_score") or 0), row.get("company_name_fa") or ""))
    plan_lines = [
        "# First-contact plan", "", f"Generated: {now_iso()}", "", f"Scope: exactly {len(targets)} current READY FOR OUTREACH companies. No new discovery was performed and no outreach was sent.", "", "## Ranking method", "", "The first-contact score is separate from the opportunity score. It combines evidence quality (15%), workflow clarity (15%), pilot simplicity (10%), measurable ROI (10%), decision-maker reachability (10%), public corporate contact coverage (10%), external-purchase fit (10%), sales-cycle reasonableness (5%), demo strength (10%) and LUMA delivery confidence (5%). Explicit penalties apply for an unverified decision-maker name, weak public channels, a weak workflow hypothesis, heavy integration/pilot burden, regulated context, or internal systems capability that requires validation.", "", f"Waves: WAVE 1 **{waves.get('WAVE 1', 0)}**, WAVE 2 **{waves.get('WAVE 2', 0)}**, WAVE 3 **{waves.get('WAVE 3', 0)}**.", "", "## WAVE 1 — first 10 companies", "", "These are ranked first because they combine a visible public operating surface, a bounded first pilot, a clear business owner role and usable corporate contact coverage. The ranking is a preparation recommendation, not permission to contact without human approval.", ""]
    for index, company in enumerate(first_contact[:10], 1):
        contact = company.get("activation_contacts") or {}
        workflow = company.get("activation_primary_opportunity") or {}
        pilot = company.get("activation_pilot") or {}
        plan_lines += [f"### {index}. {company.get('company_name_fa')} — {company.get('first_contact_score')}/100", "", f"- Industry: `{company.get('industry')}` / `{company.get('company_type')}`", f"- Website: {_md_link(company.get('website') or next((item.get('source_url') for item in company.get('source_records') or [] if str(item.get('source_family') or '').startswith('company_website:')), None))}", f"- Primary decision-maker role: {contact.get('primary_contact_role') or 'UNKNOWN'}", f"- Verified primary-contact name: {contact.get('primary_contact_name') or 'UNKNOWN'}"]
        if contact.get("economic_buyer_name"):
            plan_lines += [f"- Economic buyer: {contact.get('economic_buyer_role') or 'Managing Director / CEO'} — {contact.get('economic_buyer_name')}", f"- Economic-buyer source: {_md_link(contact.get('economic_buyer_source_url'))}"]
        plan_lines += [f"- Best contact channel: {company.get('preferred_channel')}", f"- Public contact: phone {', '.join(contact.get('public_corporate_phones') or []) or 'UNKNOWN'}; email {', '.join(contact.get('public_corporate_emails') or []) or 'UNKNOWN'}; LinkedIn {_md_link(contact.get('public_linkedin_company'))}", f"- Primary workflow: {workflow.get('workflow_name_fa')} — `{workflow.get('activation_evidence_classification')}`", f"- Pilot: {pilot.get('pilot_name')}", f"- Demo: {(company.get('activation_demo') or {}).get('demo_concept')}", f"- Why contact now: {company.get('first_contact_score_reasons') or 'Clear surface and bounded pilot with usable contact route.'}", f"- Key uncertainty: volume, current handoffs, data owner, budget and authority require discovery.", f"- Client proposal: `sales/client/{company.get('company_id')}.md`", f"- Outreach draft: `sales/outreach/{company.get('company_id')}.md`", f"- Evidence: `evidence/companies/{company.get('company_id')}/sources.json`", ""]
    plan_lines += ["## WAVE 2", "", "The next 10 ranked records remain viable but should follow the first wave after learning from pilot conversations.", "", "| Rank | Company | Score | Workflow | Main reason to wait |", "|---:|---|---:|---|---|"]
    for index, company in enumerate(first_contact[10:20], 11):
        plan_lines.append(f"| {index} | {company.get('company_name_fa')} | {company.get('first_contact_score')} | {(company.get('activation_primary_opportunity') or {}).get('workflow_name_fa')} | {', '.join(company.get('first_contact_score_reasons') or ['sequencing'])} |")
    plan_lines += ["", "## WAVE 3", "", "The remaining 12 current READY records are not rejected; sequence them after more evidence, a stronger contact route, or additional learning from the first waves.", "", "| Rank | Company | Score | Workflow | Main reason to wait |", "|---:|---|---:|---|---|"]
    for index, company in enumerate(first_contact[20:], 21):
        plan_lines.append(f"| {index} | {company.get('company_name_fa')} | {company.get('first_contact_score')} | {(company.get('activation_primary_opportunity') or {}).get('workflow_name_fa')} | {', '.join(company.get('first_contact_score_reasons') or ['sequencing'])} |")
    plan_lines += ["", "## Contact safeguards", "", "- Status in the tracker is NOT_CONTACTED for every record.", "- Use only the public corporate phone/email/company LinkedIn captured in the record.", "- Do not infer WhatsApp from a phone number; only an explicitly published business link is retained.", "- Do not claim that a company currently has a manual problem. Use the discovery questions and validate the public-surface hypothesis.", "- No calls, emails, WhatsApp messages, LinkedIn messages, forms, RFQs or account actions were performed by this run.", ""]
    path_for("reports", "first_contact_plan.md").write_text("\n".join(plan_lines), encoding="utf-8")
    real_md = lambda directory: sum(1 for item in path_for(*directory).glob("*.md") if item.is_file() and not item.name.startswith("._"))
    summary = {"ready_companies_processed": len(targets), "waves": dict(waves), "wave1": [company.get("company_name_fa") for company in first_contact[:10]], "first_contact_scores": {company["company_id"]: company.get("first_contact_score") for company in first_contact}, "client_proposals": real_md(("sales", "client")), "outreach_packages": real_md(("sales", "outreach")), "internal_briefs": real_md(("sales", "internal")), "visual_indexes": sum(1 for company in targets if (path_for("sales", "visual", company["company_id"], "README.md")).exists()), "dossiers_generated": min(30, len(targets))}
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Deepen and package only the existing LUMA READY FOR OUTREACH records")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    parser.add_argument("--proxy", default=DEFAULT_PROXY)
    parser.add_argument("--rate-limit-seconds", type=float, default=0.4)
    parser.add_argument("--timeout", type=float, default=18.0)
    parser.add_argument("--max-official-pages", type=int, default=5)
    parser.add_argument("--max-external-pages", type=int, default=5)
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()
    if not args.skip_preflight and not _preflight(args.proxy):
        print("Sales activation stopped: direct-proxy preflight failed; no company records changed.", file=sys.stderr)
        return 2
    companies = read_jsonl(args.input)
    updated, collection_summary = collect_and_augment(companies, proxy=args.proxy, rate_limit=args.rate_limit_seconds, timeout=args.timeout, max_official=args.max_official_pages, max_external=args.max_external_pages)
    report_summary = build_reports(updated)
    summary = {"completed_at": now_iso(), "activation_version": ACTIVATION_VERSION, "proxy": args.proxy, "no_outreach_sent": True, **collection_summary, **report_summary}
    log_name = f"sales-activation-{now_iso().replace(':', '').replace('-', '')}.json"
    write_json(path_for("logs", log_name), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
