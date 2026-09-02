"""Generate one evidence-first proposal for each sufficiently researched prospect."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from src.utilities.common import now_iso, path_for, read_jsonl, stable_hash, write_json, write_jsonl


OUTREACH = {
    "industrial_distributors_importers": "با توجه به تنوع محصولات و فرایندهای استعلام و فروش، یک گفت‌وگوی کوتاه درباره ساختاردهی RFQ، کاتالوگ و پیش‌فاکتور می‌تواند نقطه شروع مناسبی باشد.",
    "industrial_manufacturers": "با توجه به زمینه تولید و اطلاعات عملیاتی قابل مشاهده، پیشنهاد می‌کنیم ابتدا فرایند گزارش تولید، کیفیت یا توقفات را بررسی کنیم و یک لایه کم‌ریسک برای جمع‌بندی و کشف استثناها طراحی کنیم.",
    "food_fmcg": "با توجه به زمینه تولید/پخش و تکرارپذیری سفارش و موجودی، ارزش دارد یک فرایند واقعی سفارش، مرجوعی یا گزارش پخش را بررسی کنیم و فقط همان گلوگاه را به‌صورت آزمایشی بهبود دهیم.",
    "logistics_freight_customs": "با توجه به زمینه حمل، ترخیص یا انبارداری، یک گفت‌وگو درباره ورود اسناد، کنترل نقص مدارک و پیگیری استثناها می‌تواند به یک پروژه قابل‌اندازه‌گیری تبدیل شود.",
    "printing_packaging_labeling": "با توجه به زمینه چاپ و بسته‌بندی، پیشنهاد می‌کنیم مسیر دریافت بریف، برآورد، اصلاحات و تأیید فایل را بررسی کنیم تا یک دستیار ساختاریافته برای همان فرایند طراحی شود.",
    "medical_equipment": "با توجه به کاتالوگ‌ها، مستندات فنی یا زمینه مناقصه تجهیزات، یک بررسی محدود از جست‌وجوی مستندات و آماده‌سازی پاسخ فنی می‌تواند بدون خودکارسازی تصمیم‌های تخصصی آغاز شود.",
    "auto_parts": "با توجه به تنوع قطعات و نیاز احتمالی به جست‌وجو و تطبیق، ارزش دارد فرایند تطبیق شماره/شرح قطعه با موجودی و قیمت را با تیم فروش یا عملیات اعتبارسنجی کنیم.",
    "epc_engineering_contractors": "با توجه به زمینه پروژه و اسناد مهندسی، گفت‌وگو درباره جست‌وجوی مناقصه، BOQ، قرارداد و تعهدات می‌تواند یک نقطه شروع مشخص و قابل‌کنترل باشد.",
    "building_materials_mep": "با توجه به زمینه مصالح یا تأسیسات، پیشنهاد می‌کنیم مسیر تطبیق BOQ و مشخصات فنی با محصولات و آماده‌سازی سابمیتال را بررسی کنیم.",
    "industrial_maintenance_after_sales": "با توجه به زمینه خدمات و نگهداری، یک بررسی از ورود تیکت، دسترسی به سوابق و آماده‌سازی گزارش سرویس می‌تواند فرصت عملیاتی مناسبی را مشخص کند.",
    "pharma": "با توجه به حساسیت مستندات دارویی، پیشنهاد ما یک جست‌وجوی مجوزدار و استنادمحور در SOPها و پرونده‌هاست؛ هر تصمیم کیفی یا نظارتی باید نزد تیم مسئول باقی بماند.",
}


def md_link(label: str, url: str | None) -> str:
    return f"[{label}]({url})" if url else "UNKNOWN"


def observed_facts(company: dict[str, Any]) -> list[str]:
    facts: list[str] = []
    if company.get("description_observed"):
        facts.append(f"OBSERVED — منبع عمومی، این زمینه/شرح را برای رکورد شرکت درج کرده است: «{company['description_observed']}».")
    if company.get("hq_address"):
        facts.append(f"OBSERVED — آدرس عمومی ثبت‌شده: {company['hq_address']}.")
    if company.get("phone_public"):
        facts.append(f"OBSERVED — شماره(های) ثابت عمومی: {', '.join(company['phone_public'])}.")
    if company.get("website"):
        facts.append(f"OBSERVED — وب‌سایت/صفحه عمومی قابل ارجاع: {md_link(company['website'], company['website'])}.")
    for evidence in [item for item in company.get("evidence", []) if not item.get("excluded_from_qualification")][:4]:
        snippet = evidence.get("quote_or_snippet")
        url = evidence.get("source_url")
        if snippet and url:
            facts.append(f"OBSERVED — {snippet} ({md_link('منبع', url)}).")
    return facts[:8]


def eligible(company: dict[str, Any]) -> bool:
    if company.get("priority_tier") not in {"A", "B"} or company.get("hard_disqualifier") or company.get("industry") == "other":
        return False
    if company.get("sales_readiness") != "READY FOR OUTREACH":
        return False
    if company.get("workflow_evidence_classification") not in {"EVIDENCE_SUPPORTED", "STRONG_HYPOTHESIS"}:
        return False
    if not (company.get("workflow_opportunities") or []):
        return False
    return (company.get("commercial_evidence_strength") or 0) >= 70 and (company.get("score_confidence") or 0) >= 65


def proposal(company: dict[str, Any]) -> dict[str, Any]:
    workflow = (company.get("workflow_opportunities") or [{}])[0]
    evidence_urls = list(dict.fromkeys(
        [item.get("source_url") for item in company.get("evidence", []) if item.get("source_url") and not item.get("excluded_from_qualification")]
        + (company.get("source_urls") or [])
    ))
    website_ok = str(company.get("website_status", "")).isdigit() and int(company.get("website_status")) == 200
    confidence = "High" if (company.get("commercial_evidence_strength") or 0) >= 80 and (company.get("score_confidence") or 0) >= 80 and company.get("workflow_evidence_classification") == "EVIDENCE_SUPPORTED" else "Medium"
    facts = observed_facts(company)
    questions = workflow.get("discovery_questions") or [
        "فرایند فعلی از ورود درخواست تا خروجی نهایی چگونه انجام می‌شود؟",
        "حجم ماهانه و نقاط کنترل انسانی این فرایند چیست؟",
        "داده‌ها و سامانه‌های مرجع در اختیار کدام تیم هستند؟",
    ]
    questions = questions[:6]
    body = [
        f"# {company.get('company_name_fa')}",
        "",
        "## What we found",
        "",
        *([f"- {fact}" for fact in facts] or ["- UNKNOWN — public evidence is not yet sufficient for a detailed factual summary."]),
        "",
        "## Likely operational opportunity",
        "",
        f"{company.get('workflow_evidence_classification', 'STRONG_HYPOTHESIS')} — بر پایه سطح عمومی عملیات و شواهد لینک‌شده، فرایند قابل بررسی: **{workflow.get('workflow_name', 'Operational reporting and internal knowledge discovery')}**. این شواهد وجود یک فرایند داخلی ناکارآمد را ثابت نمی‌کند و باید در گفت‌وگوی کشف اعتبارسنجی شود.",
        "",
        "## Proposed LUMA solution",
        "",
        workflow.get("proposed_luma_solution") or "A bounded, evidence-linked workflow assistant with human approval.",
        "",
        "## How it would work",
        "",
        "1. دریافت داده یا سند از مسیرهای مورد تأیید شرکت.",
        "2. ساختاردهی، جست‌وجو یا تطبیق قابل‌ردیابی توسط سیستم.",
        "3. نمایش موارد عادی و استثناها به کاربر مسئول.",
        "4. تأیید انسانی و ثبت خروجی/معیار قبل از هر اقدام عملیاتی.",
        "",
        "## Expected business impact",
        "",
        "ROI percentage is not claimed from public data. Measure: " + "; ".join(workflow.get("measurable_KPIs") or ["turnaround time", "manual handoffs", "correction rate"]),
        "",
        "## What needs validation",
        "",
        *[f"- {question}" for question in questions],
        "",
        "## Likely person to contact",
        "",
        f"Role first: **{company.get('decision_maker_role') or workflow.get('likely_business_owner') or 'Operations or Commercial Manager'}**.",
        f"Public name: {company.get('decision_maker_name_public') or 'UNKNOWN — no publicly verified person name collected.'}",
        "",
        "## Outreach angle",
        "",
        OUTREACH.get(company.get("industry"), "پیشنهاد می‌کنیم یک فرایند تکرارشونده عملیاتی را با تیم مسئول بررسی کنیم و یک راهکار محدود و قابل‌اندازه‌گیری طراحی کنیم.") + "",
        "",
        "## Confidence",
        "",
        f"{confidence} — raw opportunity score {company.get('luma_opportunity_score')}, confidence-adjusted score {company.get('confidence_adjusted_score')}, commercial evidence strength {company.get('commercial_evidence_strength')}/100, score confidence {company.get('score_confidence')}/100 and {company.get('independent_source_count')} independent source families. Public sources establish a researchable context, not budget, internal volume or buying authority.",
        "",
        "## What we do not know",
        "",
        "Budget, monthly workflow volume, system ownership, buying authority, current manual handoffs and implementation constraints remain UNKNOWN until discovery.",
        "",
        "## Source links",
        "",
        *[f"- {md_link(url, url)}" for url in evidence_urls[:12]],
    ]
    return {
        "proposal_id": "proposal-" + stable_hash(company["company_id"], company.get("score_date")),
        "company_id": company["company_id"],
        "company_name_fa": company.get("company_name_fa"),
        "tier": company.get("priority_tier"),
        "score": company.get("luma_opportunity_score"),
        "confidence": confidence,
        "workflow_name": workflow.get("workflow_name"),
        "path": str(Path("proposals") / f"{company['company_id']}.md"),
        "source_urls": evidence_urls[:12],
        "generated_at": now_iso(),
        "markdown": "\n".join(body) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate evidence-first LUMA proposals")
    parser.add_argument("--input", default="data/normalized/companies.jsonl")
    args = parser.parse_args()
    companies = read_jsonl(args.input)
    selected = sorted([company for company in companies if eligible(company)], key=lambda item: (-item.get("luma_opportunity_score", 0), item.get("company_name_fa", "")))
    outputs: list[dict[str, Any]] = []
    proposal_dir = path_for("proposals")
    proposal_dir.mkdir(parents=True, exist_ok=True)
    selected_ids = {company["company_id"] for company in selected}
    for existing in proposal_dir.glob("*.md"):
        if not existing.name.startswith("._") and existing.stem not in selected_ids:
            existing.unlink()
    for company in selected:
        item = proposal(company)
        (proposal_dir / f"{company['company_id']}.md").write_text(item["markdown"], encoding="utf-8")
        outputs.append({key: value for key, value in item.items() if key != "markdown"})
    write_jsonl(path_for("data", "normalized", "proposals.jsonl"), outputs)
    write_json(path_for("logs", f"proposals-{now_iso().replace(':', '').replace('-', '')}.json"), {"completed_at": now_iso(), "proposals_generated": len(outputs), "eligible_tiers": ["A", "B"], "gate": "READY FOR OUTREACH + EVIDENCE_SUPPORTED/STRONG_HYPOTHESIS workflow + commercial evidence >=70 + score confidence >=65"})
    print(json.dumps({"proposals_generated": len(outputs), "tier_counts": {tier: sum(1 for item in outputs if item["tier"] == tier) for tier in ["A", "B"]}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
