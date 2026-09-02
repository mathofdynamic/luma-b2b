import { escapeHtml, renderMarkdown } from "./markdown.js";

const faNumber = new Intl.NumberFormat("fa-IR");

const STATUS_LABELS = {
  "READY FOR OUTREACH": "آماده ارتباط",
  "NEEDS DISCOVERY": "نیازمند کشف",
  "NOT READY": "فعلاً آماده نیست",
  UNKNOWN: "نامشخص",
};

const STATUS_CLASS = {
  "READY FOR OUTREACH": "status-ready",
  "NEEDS DISCOVERY": "status-discovery",
  "NOT READY": "status-not-ready",
  UNKNOWN: "status-unknown",
};

const TIER_LABELS = { A: "Tier A", B: "Tier B", C: "Tier C", D: "Tier D", Reject: "Reject", UNKNOWN: "بدون tier" };
const WAVE_LABELS = { "WAVE 1": "Wave 1", "WAVE 2": "Wave 2", "WAVE 3": "Wave 3", NONE: "بدون wave" };
const TYPE_LABELS = {
  manufacturer: "تولیدکننده",
  distributor: "توزیع‌کننده",
  importer: "واردکننده",
  freight_forwarder: "فورواردر",
  customs_broker: "کارگزار گمرکی",
  warehouse_operator: "اپراتور انبار",
  service_company: "شرکت خدماتی",
  EPC_contractor: "پیمانکار EPC",
  retailer: "خرده‌فروش",
  mixed: "ترکیبی",
  branch: "شعبه / واحد",
  unknown: "نامشخص",
};
const WORKFLOW_LABELS = {
  EVIDENCE_SUPPORTED: "پشتیبانی‌شده با شواهد",
  STRONG_HYPOTHESIS: "فرضیه قوی",
  WEAK_HYPOTHESIS: "فرضیه ضعیف",
  UNSUPPORTED: "پشتیبانی‌نشده",
  UNKNOWN: "نامشخص",
};
const EVIDENCE_LABELS = {
  OBSERVED: "مشاهده‌شده",
  STRONG_INFERENCE: "استنباط قوی",
  WEAK_INFERENCE: "استنباط ضعیف",
  UNKNOWN: "نامشخص",
};
const REVIEW_LABELS = {
  UNREVIEWED: "بررسی‌نشده",
  APPROVED_FOR_OUTREACH: "تأیید برای ارتباط",
  NEEDS_MORE_RESEARCH: "نیازمند پژوهش بیشتر",
  REJECTED_BY_HUMAN: "ردشده توسط انسان",
  FOLLOW_UP_LATER: "پیگیری بعدی",
};
const REVIEW_CLASS = {
  UNREVIEWED: "review-unreviewed",
  APPROVED_FOR_OUTREACH: "review-approved",
  NEEDS_MORE_RESEARCH: "review-research",
  REJECTED_BY_HUMAN: "review-rejected",
  FOLLOW_UP_LATER: "review-later",
};
const SOURCE_LABELS = {
  book_e_avval: "کتاب اول",
  "company_website:sabahi.com": "وب‌سایت رسمی",
  company_site: "وب‌سایت شرکت",
  linkedin_public: "LinkedIn عمومی",
  job_portal: "پرتال استخدام",
  search_engine: "موتور جست‌وجو",
  other_public: "منبع عمومی دیگر",
  directory: "دایرکتوری",
  unknown: "نامشخص",
};
const PROFILE_STATUS_LABELS = {
  SUPPORTED: "تأییدشده از منابع عمومی",
  PARTIAL: "تأییدشده به‌صورت جزئی",
  UNSUPPORTED: "پشتیبانی‌نشده",
  UNKNOWN: "نامشخص",
};
const DIGITAL_STATUS_LABELS = {
  KNOWN_MODERATE_DIGITAL_MATURITY: "بلوغ دیجیتال متوسط / پراکنده",
  KNOWN_HIGH_DIGITAL_MATURITY: "بلوغ دیجیتال بالا",
  KNOWN_LOW_DIGITAL_MATURITY: "بلوغ دیجیتال پایین",
  UNKNOWN_DIGITAL_MATURITY: "بلوغ دیجیتال نامشخص",
};
const TECH_STATUS_LABELS = {
  KNOWN_LOW_INTERNAL_TECH: "توان فنی داخلی پایین / مشاهده‌شده",
  KNOWN_MODERATE_INTERNAL_TECH: "توان فنی داخلی متوسط / مشاهده‌شده",
  KNOWN_HIGH_INTERNAL_TECH: "توان فنی داخلی بالا / مشاهده‌شده",
  UNKNOWN_INTERNAL_TECH: "توان فنی داخلی نامشخص",
};

const viewMeta = {
  overview: { label: "نمای کلی", eyebrow: "اتاق تصمیم‌گیری" },
  companies: { label: "همه شرکت‌ها", eyebrow: "کاوشگر" },
  ready: { label: "آماده‌های فروش", eyebrow: "Sales Ready" },
  evidence: { label: "میز شواهد", eyebrow: "Research Quality" },
  review: { label: "صف بررسی", eyebrow: "Human Review" },
  compare: { label: "مقایسه", eyebrow: "Decision Support" },
  detail: { label: "پرونده شرکت", eyebrow: "Company Dossier" },
};

const text = (value, fallback = "نامشخص") => {
  if (value === null || value === undefined || value === "" || value === "UNKNOWN") return `<span class="unknown-value" title="${escapeHtml(fallback)}" aria-label="${escapeHtml(fallback)}">${escapeHtml(fallback)}</span>`;
  return escapeHtml(String(value));
};

const plain = (value, fallback = "نامشخص") => {
  if (value === null || value === undefined || value === "" || value === "UNKNOWN") return fallback;
  return String(value);
};

const valueAttrs = (value, fallback = "نامشخص") => {
  const label = plain(value, fallback);
  return `title="${escapeHtml(label)}" aria-label="${escapeHtml(label)}"`;
};

const int = (value) => value === null || value === undefined || Number.isNaN(Number(value)) ? "—" : faNumber.format(Number(value));

const score = (value) => value === null || value === undefined || Number.isNaN(Number(value)) ? "—" : String(Math.round(Number(value)));

const confidence = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "نامشخص";
  const number = Number(value);
  return `${Math.round(number <= 1 ? number * 100 : number)}٪`;
};

const profileStatus = (value, labels) => {
  if (value === null || value === undefined || value === "" || value === "UNKNOWN") return "نامشخص";
  return labels[value] || String(value).replaceAll("_", " ");
};

const dateLabel = (value) => {
  if (!value) return "تاریخ نامشخص";
  try {
    return new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium" }).format(new Date(value));
  } catch {
    return String(value).slice(0, 10);
  }
};

const safeUrl = (url) => /^https?:\/\//i.test(String(url || "")) ? String(url) : null;

const externalLink = (url, label, className = "text-link") => {
  const href = safeUrl(url);
  return href ? `<a class="${className}" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(label || href)}">${escapeHtml(label)}</a>` : `<span class="unknown-value">${escapeHtml(label || "نامشخص")}</span>`;
};

const localLink = (url, label, className = "text-link") => url ? `<a class="${className}" href="${escapeHtml(url)}" title="${escapeHtml(label)}">${escapeHtml(label)}</a>` : `<span class="unknown-value">ناموجود</span>`;

function contactCollection(values, type) {
  const items = Array.isArray(values) ? values.filter(Boolean).map(String) : [];
  if (!items.length) return null;
  const itemMarkup = (item) => type === "email" ? `<a href="mailto:${escapeHtml(item)}">${escapeHtml(item)}</a>` : `<span>${escapeHtml(item)}</span>`;
  if (items.length === 1) return `<span class="contact-value ltr" dir="ltr">${itemMarkup(items[0])}</span>`;
  const countLabel = type === "phone" ? `${int(items.length)} شماره عمومی` : `${int(items.length)} ایمیل عمومی`;
  return `<details class="contact-list-details"><summary><span class="contact-preview ltr" dir="ltr" title="${escapeHtml(items[0])}">${escapeHtml(items[0])}</span><span class="contact-count">${escapeHtml(countLabel)}</span></summary><div class="contact-list-more" dir="ltr">${items.map(itemMarkup).join("")}</div></details>`;
}

const statusBadge = (value) => `<span class="badge ${STATUS_CLASS[value] || STATUS_CLASS.UNKNOWN}"><span class="badge-dot"></span>${escapeHtml(STATUS_LABELS[value] || value || "نامشخص")}</span>`;

const tierBadge = (value) => `<span class="tier-badge tier-${String(value || "unknown").toLowerCase()}">${escapeHtml(TIER_LABELS[value] || value || "بدون tier")}</span>`;

const waveBadge = (value) => value && value !== "NONE" ? `<span class="wave-badge">${escapeHtml(WAVE_LABELS[value] || value)}</span>` : `<span class="muted-badge">بدون wave</span>`;

const workflowBadge = (value) => `<span class="workflow-badge workflow-${String(value || "UNKNOWN").toLowerCase()}">${escapeHtml(WORKFLOW_LABELS[value] || value || "نامشخص")}</span>`;

const reviewBadge = (value) => `<span class="review-badge ${REVIEW_CLASS[value] || REVIEW_CLASS.UNREVIEWED}">${escapeHtml(REVIEW_LABELS[value] || REVIEW_LABELS.UNREVIEWED)}</span>`;

const icon = (name) => {
  const glyphs = { overview: "⌂", companies: "▦", ready: "↗", evidence: "◈", review: "✓", compare: "⇄", search: "⌕", arrow: "←", external: "↗", copy: "⧉", back: "→", star: "☆", starred: "★", filter: "≡", close: "×", note: "✎", file: "▤", image: "▧", demo: "▶", lock: "⌁" };
  return `<span class="icon icon-${name}" aria-hidden="true">${glyphs[name] || "·"}</span>`;
};

function scoreBar(label, value, tone = "navy", detail = "") {
  const numeric = value === null || value === undefined ? null : Math.max(0, Math.min(100, Number(value)));
  return `<div class="score-row"><div class="score-row-head"><span>${escapeHtml(label)}</span><strong>${numeric === null ? "—" : score(numeric)}</strong></div><div class="score-track"><span class="score-fill fill-${tone}" style="width:${numeric === null ? 0 : numeric}%"></span></div>${detail ? `<small>${escapeHtml(detail)}</small>` : ""}</div>`;
}

function metricCard(label, value, detail, tone = "navy", link = null) {
  const body = `<div class="metric-card-top"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div><span class="metric-detail">${escapeHtml(detail)}</span><span class="metric-line metric-line-${tone}"></span>`;
  return link ? `<a class="metric-card" href="${escapeHtml(link)}">${body}${icon("arrow")}</a>` : `<div class="metric-card">${body}</div>`;
}

function sectionHeading(eyebrow, title, description = "", action = "") {
  return `<div class="section-heading"><div><span class="eyebrow">${escapeHtml(eyebrow)}</span><h2>${escapeHtml(title)}</h2>${description ? `<p>${escapeHtml(description)}</p>` : ""}</div>${action}</div>`;
}

function emptyState(title, description, action = "") {
  return `<div class="empty-state"><span class="empty-mark">∅</span><h3>${escapeHtml(title)}</h3><p>${escapeHtml(description)}</p>${action}</div>`;
}

function reviewFor(reviews, id) {
  return reviews?.companies?.[id] || { status: "UNREVIEWED", favorite: false, note: "", reviewedAt: null, updatedAt: null };
}

function compactLocation(company) {
  return [company.location?.city, company.location?.area || company.location?.industrialZone].filter(Boolean).join(" · ") || "مکان نامشخص";
}

function companyTitle(company) {
  const nameFa = plain(company.nameFa, "بدون نام");
  return `<strong class="company-name" ${valueAttrs(nameFa)}>${escapeHtml(nameFa)}</strong>${company.nameEn ? `<span class="company-name-en" dir="ltr" title="${escapeHtml(company.nameEn)}">${escapeHtml(company.nameEn)}</span>` : ""}`;
}

function companyRow(company, reviews, selectedCompare = []) {
  const review = reviewFor(reviews, company.id);
  const isSelected = selectedCompare.includes(company.id);
  const website = company.contacts?.website;
  const location = compactLocation(company);
  const workflowName = plain(company.workflow?.nameFa || company.workflow?.name, "فرصت نامشخص");
  const decisionLabel = plain(company.decisions?.find((item) => item.status === "VERIFIED_NAME")?.name || company.decisions?.find((item) => item.role)?.role, "تصمیم‌گیرنده نامشخص");
  return `<article class="company-row ${isSelected ? "is-selected" : ""}" data-company-row="${escapeHtml(company.id)}">
    <div class="company-identity"><button class="company-open" data-company-open="${escapeHtml(company.id)}" aria-label="باز کردن پرونده ${escapeHtml(company.nameFa)}">${companyTitle(company)}</button><div class="company-meta"><span ${valueAttrs(company.industryLabel)}>${text(company.industryLabel)}</span><span ${valueAttrs(TYPE_LABELS[company.companyType] || company.companyType || "نامشخص")}>${escapeHtml(TYPE_LABELS[company.companyType] || company.companyType || "نامشخص")}</span><span ${valueAttrs(location)}>${escapeHtml(location)}</span></div>${website ? `<span class="domain" dir="ltr" title="${escapeHtml(company.domain || website)}">${escapeHtml(company.domain || website)}</span>` : ""}</div>
    <div class="company-status-cell">${tierBadge(company.tier)}${statusBadge(company.status)}${waveBadge(company.wave)}</div>
    <div class="company-score-cell"><div><span>فرصت</span><strong>${score(company.scores?.opportunity)}</strong></div><div><span>تنظیم‌شده</span><strong class="score-accent">${score(company.scores?.adjusted)}</strong></div></div>
    <div class="company-evidence-cell"><div class="evidence-number"><strong>${score(company.quality?.evidenceStrength)}</strong><span>قدرت تجاری</span></div><div class="evidence-meta"><span>${int(company.quality?.independentSourceCount)} منبع مستقل</span><span>${int(company.quality?.screenshots)} تصویر</span></div></div>
    <div class="company-opportunity-cell">${company.workflow ? `<strong class="cell-wrap" ${valueAttrs(workflowName)}>${escapeHtml(workflowName)}</strong>${workflowBadge(company.quality?.workflowClass)}<span class="cell-wrap secondary-value" ${valueAttrs(decisionLabel)}>${escapeHtml(decisionLabel)}</span>` : `<strong class="cell-wrap unknown-value" ${valueAttrs(workflowName)}>${escapeHtml(workflowName)}</strong>${workflowBadge("UNKNOWN")}`}</div>
    <div class="company-actions"><button class="icon-button ${review.favorite ? "is-favorite" : ""}" data-favorite="${escapeHtml(company.id)}" aria-label="${review.favorite ? "حذف از علاقه‌مندی" : "افزودن به علاقه‌مندی"}" title="${review.favorite ? "حذف علاقه‌مندی" : "افزودن به علاقه‌مندی"}">${icon(review.favorite ? "starred" : "star")}</button><button class="compare-toggle ${isSelected ? "is-active" : ""}" data-compare-toggle="${escapeHtml(company.id)}" aria-pressed="${isSelected}">${isSelected ? "انتخاب شد" : "مقایسه"}</button></div>
  </article>`;
}

function readyCard(company, reviews, rank) {
  const review = reviewFor(reviews, company.id);
  const workflowName = plain(company.workflow?.nameFa || company.workflow?.name, "فرصت نامشخص");
  return `<article class="ready-card"><div class="ready-card-top"><span class="rank">${int(rank)}</span><div class="ready-card-title"><button class="company-open" data-company-open="${escapeHtml(company.id)}">${companyTitle(company)}</button><span>${text(company.industryLabel)} · ${escapeHtml(TYPE_LABELS[company.companyType] || company.companyType || "نامشخص")}</span></div><button class="icon-button ${review.favorite ? "is-favorite" : ""}" data-favorite="${escapeHtml(company.id)}" aria-label="علاقه‌مندی">${icon(review.favorite ? "starred" : "star")}</button></div><div class="ready-card-middle"><div class="ready-score"><strong>${score(company.scores?.firstContact ?? company.scores?.adjusted)}</strong><span>اولویت تماس</span></div><div class="ready-score"><strong>${score(company.quality?.evidenceStrength)}</strong><span>قدرت شواهد</span></div><div class="ready-detail"><span>${waveBadge(company.wave)}</span><span>${int(company.quality?.independentSourceCount)} منبع مستقل</span><span>${company.quality?.screenshots ? `${int(company.quality.screenshots)} تصویر` : "بدون تصویر"}</span></div></div><div class="ready-card-footer"><div>${company.workflow ? `<strong class="cell-wrap" ${valueAttrs(workflowName)}>${escapeHtml(workflowName)}</strong>${workflowBadge(company.quality.workflowClass)}` : `<span class="cell-wrap unknown-value" ${valueAttrs(workflowName)}>${escapeHtml(workflowName)}</span>`}</div><span class="contact-signal">${company.contacts?.emails?.length ? "ایمیل عمومی" : company.contacts?.phones?.length ? "تلفن عمومی" : "کانال نامشخص"}</span><button class="text-button ready-open-action" data-company-open="${escapeHtml(company.id)}">بررسی پرونده ${icon("arrow")}</button></div></article>`;
}

function renderSidebar(view, index, reviews) {
  const reviewCount = Object.values(reviews?.companies || {}).filter((item) => item.status && item.status !== "UNREVIEWED").length;
  const nav = [
    ["overview", "نمای کلی", "داده و کیفیت"],
    ["companies", "همه شرکت‌ها", `${int(index.counts.total)} رکورد`],
    ["ready", "آماده‌های فروش", `${int(index.counts.ready)} شرکت`],
    ["evidence", "میز شواهد", `${int(index.counts.screenshotPackages)} بسته`],
    ["review", "صف بررسی", reviewCount ? `${int(reviewCount)} تصمیم` : "هنوز خالی"],
    ["compare", "مقایسه", "۲ تا ۴ شرکت"],
  ];
  return `<aside class="sidebar" aria-label="ناوبری اصلی"><div class="sidebar-brand"><span class="brand-mark"><i></i><i></i><i></i></span><div><strong>LUMA</strong><span>Research OS</span></div></div><div class="local-lock"><span>${icon("lock")}</span><div><strong>محلی و خصوصی</strong><span>بدون sync بیرونی</span></div></div><nav class="main-nav" aria-label="بخش‌های داشبورد">${nav.map(([key, label, detail]) => `<button class="nav-item ${view === key ? "is-active" : ""}" data-view="${key}" aria-current="${view === key ? "page" : "false"}">${icon(key)}<span class="nav-copy"><strong>${label}</strong><small>${detail}</small></span>${view === key ? `<span class="nav-active-mark"></span>` : ""}</button>`).join("")}</nav><div class="sidebar-bottom"><div class="side-rule"></div><span>منبع اصلی</span><code dir="ltr">data/normalized/companies.jsonl</code><span class="side-version">Index ${escapeHtml(String(index.schemaVersion || "0.1"))} · ${escapeHtml(dateLabel(index.generatedAt))}</span></div></aside>`;
}

function renderHeader(view, index, state) {
  const meta = viewMeta[view] || viewMeta.overview;
  return `<header class="topbar"><div class="topbar-context"><span class="eyebrow">${escapeHtml(meta.eyebrow)}</span><h1>${escapeHtml(meta.label)}</h1></div><div class="topbar-tools"><label class="global-search"><span class="sr-only">جست‌وجوی سراسری</span>${icon("search")}<input id="global-search" type="search" autocomplete="off" placeholder="جست‌وجوی شرکت، صنعت، دامنه یا فرصت…" value="${escapeHtml(state.query || "")}"><kbd>⌘ K</kbd></label><button class="command-trigger" data-palette-open="true" aria-label="باز کردن جست‌وجوی سریع">${icon("search")}<span>فرمان سریع</span><kbd>⌘ K</kbd></button><span class="local-indicator"><span class="status-dot"></span>داده محلی</span></div></header>`;
}

function renderOverview(index, reviews) {
  const stats = index.counts;
  const ready = index.companies.filter((company) => company.status === "READY FOR OUTREACH").sort((a, b) => (a.waveRank || 99) - (b.waveRank || 99)).slice(0, 5);
  const industries = (index.facets.industries || []).slice(0, 8);
  const qualityRows = [
    ["۳+ منبع مستقل", stats.threePlusSources, `از ${int(stats.total)} شرکت`, "view=companies&evidence=three"],
    ["قدرت workflow با شواهد", stats.workflowSupported, "EVIDENCE_SUPPORTED", "view=evidence&evidenceFilter=supported"],
    ["نام تصمیم‌گیرنده عمومی", stats.verifiedDecisionMakers, "تأییدشده در داده فعلی", "view=evidence&evidenceFilter=decision"],
    ["فقط شواهد دایرکتوری", stats.directoryOnly, "نیازمند احتیاط بیشتر", "view=evidence&evidenceFilter=directory"],
  ];
  const reviewTouched = Object.keys(reviews?.companies || {}).length;
  const reviewCounts = Object.values(reviews?.companies || {}).reduce((acc, item) => { acc[item.status] = (acc[item.status] || 0) + 1; return acc; }, {});
  return `<div class="page overview-page"><div class="page-intro"><div><span class="eyebrow">فضای بررسی داخلی · ${escapeHtml(dateLabel(index.generatedAt))}</span><h2>از نقشه بازار تا تصمیم انسانی.</h2><p>یک نمای قابل جست‌وجو از شرکت‌ها، شواهد، فرصت‌ها و مواد فروش؛ با فاصله‌گذاری روشن بین آنچه دیده‌ایم و آنچه باید بررسی شود.</p></div><div class="intro-actions"><button class="button button-dark" data-view="ready">${icon("ready")}شروع از آماده‌های فروش</button><button class="button button-light" data-view="companies">${icon("companies")}کاوشگر شرکت‌ها</button></div></div><div class="metric-grid">${metricCard("کل شرکت‌ها", int(stats.total), "رکورد canonical", "navy", "?view=companies")}${metricCard("معناداراً غنی‌شده", int(stats.enriched), "سطح enrichment", "teal", "?view=companies&enriched=true")}${metricCard("Tier A / B", `${int(stats.tierA)} / ${int(stats.tierB)}`, "اولویت پژوهش", "amber", "?view=companies&tier=A")}${metricCard("آماده ارتباط", int(stats.ready), "۳۲ پرونده فعلی", "teal", "?view=ready")}${metricCard("Wave 1", int(stats.wave1), "صف تماس اول", "navy", "?view=ready&wave=WAVE%201")}${metricCard("بسته شواهد", int(stats.screenshotPackages), "پکیج‌های شرکت", "amber", "?view=evidence")}</div><div class="overview-grid"><section class="surface focus-surface">${sectionHeading("Focus now", "پنج پرونده برای شروع", "Wave 1 از داده واقعی؛ نه یک لیست hardcoded.", `<button class="text-button" data-view="ready">مشاهده همه ${icon("arrow")}</button>`)}<div class="focus-list">${ready.map((company) => `<button class="focus-row" data-company-open="${escapeHtml(company.id)}"><span class="focus-rank">${int(company.waveRank)}</span><span class="focus-copy"><strong>${text(company.nameFa)}</strong><span>${text(company.workflow?.nameFa || company.industryLabel)} · ${waveBadge(company.wave)}</span></span><span class="focus-score"><strong>${score(company.scores.firstContact)}</strong><small>تماس</small></span>${icon("arrow")}</button>`).join("")}</div></section><section class="surface quality-surface">${sectionHeading("Research quality", "کیفیت را کنار فرصت ببین", "منبع بیشتر همیشه به‌معنای منبع مستقل بیشتر نیست.", `<button class="text-button" data-view="evidence">میز شواهد ${icon("arrow")}</button>`)}<div class="quality-list">${qualityRows.map(([label, value, detail, href]) => `<a class="quality-row" href="?${href}"><span class="quality-icon">${icon(label.includes("workflow") ? "file" : label.includes("تصمیم") ? "star" : label.includes("دایرکتوری") ? "note" : "evidence")}</span><span><strong>${escapeHtml(label)}</strong><small>${escapeHtml(detail)}</small></span><b>${int(value)}</b>${icon("arrow")}</a>`).join("")}</div></section></div><div class="overview-grid lower-grid"><section class="surface industry-surface">${sectionHeading("Market shape", "صنایع پرتکرار", "تعداد کشف‌شده، نه الزاماً تعداد آماده فروش.", `<button class="text-button" data-view="companies">جزئیات ${icon("arrow")}</button>`)}<div class="industry-list">${industries.map((item) => `<button class="industry-row" data-industry="${escapeHtml(item.value)}"><span class="industry-name">${escapeHtml(item.label)}</span><span class="industry-track"><i style="width:${Math.max(3, Math.round(item.count / Math.max(1, industries[0]?.count || 1) * 100))}%"></i></span><strong>${int(item.count)}</strong></button>`).join("")}</div></section><section class="surface review-surface">${sectionHeading("Human layer", "وضعیت بررسی انسانی", "این لایه جدا از داده پژوهشی در فایل local ذخیره می‌شود.", `<button class="text-button" data-view="review">صف بررسی ${icon("arrow")}</button>`)}<div class="review-overview"><div class="review-ring" style="--review-progress:${reviewTouched ? Math.max(4, Math.round(Math.min(100, reviewTouched / Math.max(1, stats.total) * 100))) : 0}%"><strong>${int(reviewTouched)}</strong><span>پرونده دارای تعامل</span></div><div class="review-stat-list">${Object.entries(REVIEW_LABELS).slice(1).map(([key, label]) => `<div><span class="review-chip ${REVIEW_CLASS[key]}"></span><span>${escapeHtml(label)}</span><strong>${int(reviewCounts[key] || 0)}</strong></div>`).join("")}</div></div><div class="local-note">${icon("lock")} یادداشت‌ها و تصمیم‌های انسانی داخل canonical research نوشته نمی‌شوند.</div></section></div></div>`;
}

function renderFilterSelect(id, label, value, options) {
  return `<label class="filter-field" for="filter-${escapeHtml(id)}"><span id="filter-${escapeHtml(id)}-label">${escapeHtml(label)}</span><select id="filter-${escapeHtml(id)}" data-filter="${escapeHtml(id)}" aria-label="${escapeHtml(label)}" aria-labelledby="filter-${escapeHtml(id)}-label"><option value="ALL">همه</option>${options.map(([key, textValue]) => `<option value="${escapeHtml(key)}" ${value === key ? "selected" : ""}>${escapeHtml(textValue)}</option>`).join("")}</select></label>`;
}

function renderCompanies(index, reviews, state, filtered, pagination) {
  const facets = index.facets;
  const filters = state.filters;
  const activeFilterCount = Object.values(filters).filter((value) => value && value !== "ALL" && value !== false && value !== "").length;
  const industryOptions = (facets.industries || []).map((item) => [item.value, item.label]);
  const typeOptions = (facets.companyTypes || []).map((item) => [item.value, TYPE_LABELS[item.value] || item.label]);
  const statusOptions = [["READY FOR OUTREACH", "آماده ارتباط"], ["NEEDS DISCOVERY", "نیازمند کشف"], ["NOT READY", "فعلاً آماده نیست"], ["UNKNOWN", "نامشخص / کشف اولیه"]];
  const tierOptions = [["A", "Tier A"], ["B", "Tier B"], ["C", "Tier C"], ["D", "Tier D"], ["Reject", "Reject"]];
  const waveOptions = [["WAVE 1", "Wave 1"], ["WAVE 2", "Wave 2"], ["WAVE 3", "Wave 3"], ["NONE", "بدون wave"]];
  const workflowOptions = Object.entries(WORKFLOW_LABELS).map(([key, value]) => [key, value]);
  const sortOptions = [["adjusted", "confidence-adjusted score"], ["firstContact", "first-contact score"], ["evidence", "commercial evidence"], ["opportunity", "opportunity score"], ["name", "نام شرکت"], ["research", "آخرین پژوهش"]];
  return `<div class="page companies-page"><div class="page-intro compact-intro"><div><span class="eyebrow">${int(index.counts.total)} رکورد canonical</span><h2>همه شرکت‌ها</h2><p>یک نمای فشرده برای عبور از بازار بزرگ به پرونده قابل بررسی. برای جزئیات، روی نام شرکت کلیک کنید.</p></div><div class="intro-actions"><button class="button button-teal" data-view="ready">${icon("ready")}۳۲ آماده فروش</button><button class="button button-light" data-compare-go="true">${icon("compare")}مقایسه ${state.selectedCompare.length ? `(${int(state.selectedCompare.length)})` : ""}</button></div></div><div class="explorer-toolbar"><label class="explorer-search">${icon("search")}<span class="sr-only">جست‌وجو در شرکت‌ها</span><input id="company-search" type="search" placeholder="نام، توضیح، صنعت، دامنه، فرصت یا تصمیم‌گیرنده…" value="${escapeHtml(state.query || "")}"></label><div class="toolbar-actions"><span class="result-count">${int(pagination.total)} نتیجه</span><label class="sort-select" for="sort-filter"><span id="sort-filter-label">مرتب‌سازی</span><select id="sort-filter" data-filter="sort" aria-label="مرتب‌سازی شرکت‌ها" aria-labelledby="sort-filter-label">${sortOptions.map(([key, label]) => `<option value="${key}" ${state.sort === key ? "selected" : ""}>${escapeHtml(label)}</option>`).join("")}</select></label></div></div><details class="filter-drawer" ${activeFilterCount ? "open" : ""}><summary>${icon("filter")}فیلترهای دقیق <span class="filter-count">${activeFilterCount ? int(activeFilterCount) : "بدون فیلتر"}</span></summary><div class="filters-body"><div class="filter-grid">${renderFilterSelect("status", "وضعیت پژوهشی", filters.status, statusOptions)}${renderFilterSelect("tier", "Tier", filters.tier, tierOptions)}${renderFilterSelect("wave", "Wave", filters.wave, waveOptions)}${renderFilterSelect("industry", "صنعت", filters.industry, industryOptions)}${renderFilterSelect("companyType", "نوع شرکت", filters.companyType, typeOptions)}${renderFilterSelect("workflow", "وضعیت workflow", filters.workflow, workflowOptions)}</div><div class="range-grid"><label class="filter-field"><span>فرصت ≥</span><input aria-label="فرصت بیشتر یا مساوی" data-filter="opportunityMin" type="number" min="0" max="100" value="${escapeHtml(filters.opportunityMin || "")}" placeholder="—"></label><label class="filter-field"><span>تنظیم‌شده ≥</span><input aria-label="امتیاز تنظیم‌شده بیشتر یا مساوی" data-filter="adjustedMin" type="number" min="0" max="100" value="${escapeHtml(filters.adjustedMin || "")}" placeholder="—"></label><label class="filter-field"><span>قدرت شواهد ≥</span><input aria-label="قدرت شواهد بیشتر یا مساوی" data-filter="evidenceMin" type="number" min="0" max="100" value="${escapeHtml(filters.evidenceMin || "")}" placeholder="—"></label><label class="filter-field"><span>اعتماد امتیاز ≥</span><input aria-label="اعتماد امتیاز بیشتر یا مساوی" data-filter="confidenceMin" type="number" min="0" max="100" value="${escapeHtml(filters.confidenceMin || "")}" placeholder="—"></label><label class="filter-field"><span>اولویت تماس ≥</span><input aria-label="اولویت تماس بیشتر یا مساوی" data-filter="firstContactMin" type="number" min="0" max="100" value="${escapeHtml(filters.firstContactMin || "")}" placeholder="—"></label></div><div class="check-grid"><label class="check-field"><input type="checkbox" aria-label="۳+ منبع مستقل" data-filter="threePlus" ${filters.threePlus ? "checked" : ""}><span>۳+ منبع مستقل</span></label><label class="check-field"><input type="checkbox" aria-label="تصویر شواهد دارد" data-filter="hasScreenshots" ${filters.hasScreenshots ? "checked" : ""}><span>تصویر شواهد دارد</span></label><label class="check-field"><input type="checkbox" aria-label="نام تصمیم‌گیرنده دارد" data-filter="hasDecision" ${filters.hasDecision ? "checked" : ""}><span>نام تصمیم‌گیرنده دارد</span></label><label class="check-field"><input type="checkbox" aria-label="فقط دایرکتوری" data-filter="directoryOnly" ${filters.directoryOnly ? "checked" : ""}><span>فقط دایرکتوری</span></label><label class="check-field"><input type="checkbox" aria-label="کانال تماس عمومی" data-filter="hasContact" ${filters.hasContact ? "checked" : ""}><span>کانال تماس عمومی</span></label></div><button class="text-button reset-filters" data-filter-reset="true" aria-label="پاک‌کردن همه فیلترها">پاک‌کردن همه فیلترها</button></div></details><div class="table-shell"><div class="company-table-head"><span>شرکت / زمینه</span><span>وضعیت</span><span>امتیازها</span><span>شواهد</span><span>فرصت اصلی</span><span>عملیات</span></div><div class="company-table-body">${filtered.length ? filtered.map((company) => companyRow(company, reviews, state.selectedCompare)).join("") : emptyState("نتیجه‌ای پیدا نشد", "ترکیب جست‌وجو و فیلترها با هیچ رکوردی منطبق نیست.", `<button class="button button-light" data-filter-reset="true">پاک‌کردن فیلترها</button>`)}</div></div>${renderPagination(pagination)}</div>`;
}

function renderPagination(pagination) {
  if (pagination.pages <= 1) return `<div class="pagination"><span>${int(pagination.total)} رکورد در این نما</span></div>`;
  const buttons = [];
  for (let page = 1; page <= pagination.pages; page += 1) {
    if (page === 1 || page === pagination.pages || Math.abs(page - pagination.page) <= 1) buttons.push(`<button class="page-button ${page === pagination.page ? "is-active" : ""}" data-page="${page}" aria-label="صفحه ${page}" ${page === pagination.page ? "aria-current=page" : ""}>${int(page)}</button>`);
    else if (buttons[buttons.length - 1] !== "…") buttons.push("…");
  }
  return `<nav class="pagination" aria-label="صفحه‌بندی"><span>${int((pagination.page - 1) * pagination.pageSize + 1)}–${int(Math.min(pagination.total, pagination.page * pagination.pageSize))} از ${int(pagination.total)}</span><div class="pagination-buttons"><button class="page-button" data-page="${pagination.page - 1}" ${pagination.page === 1 ? "disabled" : ""}>قبلی</button>${buttons.map((button) => button === "…" ? `<span class="page-gap">…</span>` : button).join("")}<button class="page-button" data-page="${pagination.page + 1}" ${pagination.page === pagination.pages ? "disabled" : ""}>بعدی</button></div></nav>`;
}

function renderReady(index, reviews, state) {
  const wave = state.wave || "WAVE 1";
  const companies = index.companies.filter((company) => company.status === "READY FOR OUTREACH" && company.wave === wave).sort((a, b) => (a.waveRank || 99) - (b.waveRank || 99));
  const waveCounts = ["WAVE 1", "WAVE 2", "WAVE 3"].map((value) => [value, index.companies.filter((company) => company.status === "READY FOR OUTREACH" && company.wave === value).length]);
  return `<div class="page ready-page"><div class="page-intro compact-intro"><div><span class="eyebrow">${int(index.counts.ready)} پرونده qualified</span><h2>آماده‌های فروش</h2><p>نمای curated از شرکت‌هایی که برای بررسی انسانی و تصمیم تماس آماده‌ترند؛ ranking فقط به score خلاصه نمی‌شود.</p></div><div class="intro-callout"><span>Focus wave</span><strong>${escapeHtml(WAVE_LABELS[wave] || wave)}</strong><small>${int(companies.length)} شرکت در این موج</small></div></div><div class="wave-tabs" role="tablist" aria-label="موج تماس">${waveCounts.map(([value, count]) => `<button class="wave-tab ${wave === value ? "is-active" : ""}" data-wave="${value}" role="tab" aria-selected="${wave === value}"><span>${escapeHtml(WAVE_LABELS[value])}</span><strong>${int(count)}</strong></button>`).join("")}</div><div class="ready-toolbar"><div><span class="eyebrow">Contact readiness</span><h3>${escapeHtml(WAVE_LABELS[wave])} · اولویت انسانی</h3></div><div class="ready-legend"><span><i class="legend-dot teal"></i>workflow با شواهد/فرضیه</span><span><i class="legend-dot amber"></i>کانال عمومی</span><button class="button button-light" data-compare-go="true">${icon("compare")}مقایسه انتخاب‌ها</button></div></div><div class="ready-list">${companies.length ? companies.map((company) => readyCard(company, reviews, company.waveRank)).join("") : emptyState("این wave خالی است", "در داده فعلی برای این موج پرونده‌ای وجود ندارد.", `<button class="button button-light" data-view="companies">رفتن به کاوشگر</button>`)}</div></div>`;
}

function renderEvidence(index, reviews, state, rows) {
  const tabs = [["all", "همه"], ["three", "۳+ منبع"], ["screenshots", "تصویر دارد"], ["decision", "نام تصمیم‌گیرنده"], ["directory", "فقط دایرکتوری"], ["supported", "workflow پشتیبانی‌شده"], ["unknown", "UNKNOWN زیاد"]];
  return `<div class="page evidence-page"><div class="page-intro compact-intro"><div><span class="eyebrow">Evidence desk</span><h2>میز شواهد</h2><p>اینجا کیفیت پژوهش را ممیزی می‌کنیم: familyهای مستقل، تصویر، تصمیم‌گیرنده و فاصله‌ی بین fact و hypothesis.</p></div><div class="evidence-summary"><strong>${int(index.counts.evidenceScreenshots)}</strong><span>تصویر شواهد</span><small>${int(index.counts.threePlusSources)} شرکت با ۳+ منبع</small></div></div><div class="evidence-metrics"><div><strong>${int(index.counts.threePlusSources)}</strong><span>۳+ منبع مستقل</span></div><div><strong>${int(index.counts.workflowSupported)}</strong><span>workflow پشتیبانی‌شده</span></div><div><strong>${int(index.counts.verifiedDecisionMakers)}</strong><span>نام عمومی تأییدشده</span></div><div><strong>${int(index.counts.directoryOnly)}</strong><span>فقط دایرکتوری</span></div></div><div class="segmented-tabs" role="tablist" aria-label="فیلتر کیفیت">${tabs.map(([key, label]) => `<button class="segment-tab ${state.evidenceFilter === key ? "is-active" : ""}" data-evidence-filter="${key}" role="tab" aria-selected="${state.evidenceFilter === key}">${escapeHtml(label)}</button>`).join("")}</div><div class="evidence-table-shell"><div class="evidence-table-head"><span>شرکت</span><span>منبع مستقل</span><span>تصویر / evidence</span><span>workflow</span><span>تصمیم‌گیرنده</span><span>بررسی</span></div><div class="evidence-list">${rows.length ? rows.map((company) => { const review = reviewFor(reviews, company.id); const decision = company.decisions?.find((item) => item.status === "VERIFIED_NAME"); const location = compactLocation(company); const sourceFamilies = company.quality.independentSourceFamilies.slice(0, 2).map((item) => SOURCE_LABELS[item] || item).join(" · ") || "منبع مستقل نامشخص"; const decisionName = decision ? plain(decision.name) : "نام تأییدشده ندارد"; const decisionRole = plain(decision?.role || company.decisions?.find((item) => item.role)?.role, "نقش تصمیم‌گیرنده نامشخص"); return `<article class="evidence-row"><div class="evidence-company"><button class="company-open" data-company-open="${escapeHtml(company.id)}">${companyTitle(company)}</button><span class="cell-wrap secondary-value" ${valueAttrs(`${plain(company.industryLabel)} · ${location}`)}>${text(company.industryLabel)} · ${escapeHtml(location)}</span></div><div class="source-count"><strong>${int(company.quality.independentSourceCount)}</strong><span class="cell-wrap secondary-value" ${valueAttrs(sourceFamilies)}>${escapeHtml(sourceFamilies)}</span></div><div class="evidence-count"><strong>${int(company.quality.screenshots)}</strong><span>${int(company.quality.evidenceCount)} شاهد متنی</span></div><div>${workflowBadge(company.quality.workflowClass)}<span class="quality-small" ${valueAttrs(confidence(company.workflow?.confidenceScore))}>${confidence(company.workflow?.confidenceScore)}</span></div><div class="decision-cell">${decision ? `<strong class="cell-wrap" ${valueAttrs(decisionName)}>${escapeHtml(decisionName)}</strong><span class="cell-wrap secondary-value" ${valueAttrs(decisionRole)}>${escapeHtml(decisionRole)}</span>` : `<span class="unknown-value">نام تأییدشده ندارد</span><small class="cell-wrap secondary-value" ${valueAttrs(decisionRole)}>${escapeHtml(decisionRole)}</small>`}</div><div>${reviewBadge(review.status)}</div></article>`; }).join("") : emptyState("در این فیلتر رکوردی نیست", "فیلتر دیگری را امتحان کنید یا به نمای همه بازگردید.", `<button class="button button-light" data-evidence-filter="all">نمایش همه</button>`)}</div></div></div>`;
}

function renderReview(index, reviews, state, rows) {
  const statuses = Object.entries(REVIEW_LABELS);
  const counts = statuses.reduce((acc, [key]) => { acc[key] = Object.values(reviews?.companies || {}).filter((item) => item.status === key).length; return acc; }, {});
  return `<div class="page review-page"><div class="page-intro compact-intro"><div><span class="eyebrow">Human layer · local JSON</span><h2>صف بررسی انسانی</h2><p>تصمیم شما از research جدا ذخیره می‌شود. می‌توانید یک پرونده را approve، برای پژوهش بیشتر نگه دارید یا بعداً پیگیری کنید.</p></div><div class="review-storage"><span>${icon("lock")} ذخیره‌سازی محلی</span><strong>dashboard/.local/review_state.json</strong><small>هیچ پیام یا ارتباطی ارسال نمی‌شود.</small></div></div><div class="review-tabs" role="tablist" aria-label="فیلتر بررسی">${statuses.map(([key, label]) => `<button class="review-tab ${state.reviewFilter === key ? "is-active" : ""}" data-review-filter="${key}" role="tab" aria-selected="${state.reviewFilter === key}">${escapeHtml(label)}<b>${int(counts[key] || 0)}</b></button>`).join("")}</div><div class="review-list">${rows.length ? rows.map((company) => { const review = reviewFor(reviews, company.id); const workflowName = plain(company.workflow?.nameFa || company.workflow?.name, "فرصت نامشخص"); const context = `${plain(company.industryLabel)} · اولویت ${score(company.scores.firstContact)}`; const note = review.note ? review.note : "بدون یادداشت"; return `<article class="review-row"><div class="review-company"><button class="company-open" data-company-open="${escapeHtml(company.id)}">${companyTitle(company)}</button><span>${statusBadge(company.status)} ${tierBadge(company.tier)} ${waveBadge(company.wave)}</span></div><div class="review-opportunity"><strong class="cell-wrap" ${valueAttrs(workflowName)}>${escapeHtml(workflowName)}</strong><span class="cell-wrap secondary-value" ${valueAttrs(context)}>${escapeHtml(context)}</span></div><div class="review-current">${reviewBadge(review.status)}${review.note ? `<span class="note-preview cell-wrap" ${valueAttrs(note)}>${escapeHtml(review.note)}</span>` : `<span class="unknown-value">بدون یادداشت</span>`}</div><div class="review-row-actions"><button class="button button-light" data-company-open="${escapeHtml(company.id)}">باز کردن</button><button class="icon-button ${review.favorite ? "is-favorite" : ""}" data-favorite="${escapeHtml(company.id)}" aria-label="علاقه‌مندی">${icon(review.favorite ? "starred" : "star")}</button></div></article>`; }).join("") : emptyState("صف خالی است", "برای ایجاد صف، از پرونده شرکت یک وضعیت انسانی ثبت کنید.", `<button class="button button-light" data-view="ready">مشاهده آماده‌های فروش</button>`)}</div></div>`;
}

function renderCompare(index, reviews, selectedIds) {
  const companies = selectedIds.map((id) => index.companies.find((company) => company.id === id)).filter(Boolean);
  if (companies.length < 2) return `<div class="page compare-page"><div class="page-intro compact-intro"><div><span class="eyebrow">Decision support</span><h2>مقایسه تحلیلی</h2><p>از کاوشگر شرکت‌ها با دکمه «مقایسه» دو تا چهار شرکت انتخاب کنید. این صفحه برای تصمیم تماس است، نه رتبه‌بندی مطلق.</p></div><div class="compare-count"><strong>${int(companies.length)}</strong><span>انتخاب فعلی</span></div></div><div class="compare-empty surface">${icon("compare")}${emptyState("برای شروع، دو شرکت انتخاب کنید", "از کاوشگر شرکت‌ها انتخاب کنید؛ انتخاب‌ها در همین نشست باقی می‌مانند.", `<button class="button button-dark" data-view="companies">انتخاب از کاوشگر ${icon("arrow")}</button>`)}</div></div>`;
  const metricRows = [["Opportunity score", "scores.opportunity", "فرصت LUMA"], ["Confidence-adjusted", "scores.adjusted", "امتیاز تنظیم‌شده با اعتماد"], ["Evidence strength", "quality.evidenceStrength", "قدرت شواهد تجاری"], ["Score confidence", "quality.scoreConfidence", "اعتماد به امتیاز"], ["First-contact score", "scores.firstContact", "اولویت تماس"], ["Implementation", "scores.implementation", "سهولت اجرا"]];
  const getPath = (company, path) => path.split(".").reduce((value, key) => value?.[key], company);
  return `<div class="page compare-page"><div class="page-intro compact-intro"><div><span class="eyebrow">Decision support · ${int(companies.length)} شرکت</span><h2>مقایسه تحلیلی</h2><p>امتیاز، شواهد و قابلیت تماس کنار هم؛ unknownها عمداً به‌عنوان خلأ اطلاعات می‌مانند.</p></div><div class="intro-actions"><button class="button button-light" data-clear-compare="true">پاک‌کردن انتخاب‌ها</button><button class="button button-dark" data-view="ready">برگشت به آماده‌ها ${icon("arrow")}</button></div></div><div class="compare-grid"><section class="surface compare-score-surface"><div class="compare-company-head"><div class="compare-label">معیار</div>${companies.map((company) => `<div class="compare-company"><button class="company-open" data-company-open="${escapeHtml(company.id)}">${companyTitle(company)}</button><span>${text(company.industryLabel)}</span><button class="remove-compare" data-compare-remove="${escapeHtml(company.id)}" aria-label="حذف ${escapeHtml(company.nameFa)}">×</button></div>`).join("")}</div>${metricRows.map(([key, path, label]) => `<div class="compare-metric-row"><span class="compare-metric-label">${escapeHtml(label)}</span>${companies.map((company) => { const value = getPath(company, path); const numeric = value === null || value === undefined ? null : Number(value) <= 1 ? Number(value) * 100 : Number(value); return `<div class="compare-metric-value"><strong>${numeric === null ? "—" : score(numeric)}</strong><span class="compare-mini-track"><i style="width:${numeric === null ? 0 : Math.max(0, Math.min(100, numeric))}%"></i></span></div>`; }).join("")}</div>`).join("")}</section><section class="surface compare-insight-surface">${sectionHeading("What changes the decision", "تفاوت‌های تعیین‌کننده", "یک نگاه کیفی برای تصمیم جلسه بعد.")}${companies.map((company) => `<div class="compare-insight"><div class="compare-insight-head"><span>${text(company.nameFa)}</span>${waveBadge(company.wave)}</div><div class="compare-insight-lines"><div><span>فرصت اصلی</span><strong>${text(company.workflow?.nameFa || company.workflow?.name)}</strong></div><div><span>منبع مستقل</span><strong>${int(company.quality.independentSourceCount)} · ${company.quality.hasThreePlusSources ? "۳+" : "کمتر از ۳"}</strong></div><div><span>تماس</span><strong>${company.contacts?.emails?.length ? "ایمیل" : company.contacts?.phones?.length ? "تلفن" : "نامشخص"} · ${company.decisions?.some((item) => item.status === "VERIFIED_NAME") ? "نام تأییدشده" : "نقش / نامشخص"}</strong></div></div><button class="text-button" data-company-open="${escapeHtml(company.id)}">باز کردن پرونده ${icon("arrow")}</button></div>`).join("")}</section></div></div>`;
}

function detailScoreStrip(detail) {
  const scores = detail.scores || {};
  return `<div class="detail-score-strip"><div><span>فرصت</span><strong>${score(scores.opportunity)}</strong></div><div class="accent"><span>تنظیم‌شده</span><strong>${score(scores.adjusted)}</strong></div><div><span>تماس اول</span><strong>${score(scores.firstContact)}</strong></div><div><span>شواهد تجاری</span><strong>${score(detail.quality.evidenceStrength)}</strong></div><div><span>اعتماد امتیاز</span><strong>${confidence(detail.quality.scoreConfidence)}</strong></div></div>`;
}

function renderDetailHeader(detail, review) {
  const website = detail.contacts?.website;
  const locationLine = detail.location?.hq || compactLocation(detail);
  return `<div class="detail-header"><div class="detail-breadcrumb"><button class="back-button" data-back="true">${icon("back")}بازگشت</button><span>/</span><span>${escapeHtml(viewMeta[detail.status === "READY FOR OUTREACH" ? "ready" : "companies"].label)}</span></div><div class="detail-title-row"><div><div class="detail-kicker">${text(detail.industryLabel)} · ${escapeHtml(TYPE_LABELS[detail.companyType] || detail.companyType || "نامشخص")}</div><h2>${companyTitle(detail)}</h2><p>${text(locationLine)}</p></div><div class="detail-title-actions"><button class="icon-button large ${review.favorite ? "is-favorite" : ""}" data-favorite="${escapeHtml(detail.id)}" aria-label="${review.favorite ? "حذف از علاقه‌مندی" : "افزودن به علاقه‌مندی"}">${icon(review.favorite ? "starred" : "star")}</button>${website ? externalLink(website, "باز کردن وب‌سایت", "button button-light") : `<span class="button button-disabled">وب‌سایت نامشخص</span>`}<button class="button button-dark" data-review-scroll="true">${icon("review")}ثبت review</button></div></div><div class="detail-badges">${tierBadge(detail.tier)}${statusBadge(detail.status)}${waveBadge(detail.wave)}${reviewBadge(review.status)}<span class="detail-status-note">آخرین پژوهش: ${escapeHtml(dateLabel(detail.profile?.history?.lastResearchDate || detail.profile?.history?.lastActivationDate))}</span></div>${detailScoreStrip(detail)}</div>`;
}

function renderSummaryCard(detail) {
  const description = detail.profile?.description || detail.profile?.quality?.qualificationReason;
  const why = detail.profile?.quality?.strongestObserved?.slice(0, 2).join(" · ");
  const uncertainty = detail.profile?.quality?.riskReasons?.[0] || detail.profile?.technology?.internalCapabilityInterpretation || "اطلاعات عمومی برای همه ابعاد کافی نیست.";
  return `<div class="summary-grid"><section class="surface summary-main">${sectionHeading("خلاصه تصمیم", "پرونده در یک نگاه", "هویت، دلیل توجه و قدم بعدی.")}<div class="summary-copy"><div><span>این شرکت چه می‌کند؟</span><p>${text(description, "شرح عمومی کافی در داده فعلی وجود ندارد.")}</p></div><div><span>چرا LUMA اهمیت می‌دهد؟</span><p>${text(why, "دلیل تجاری هنوز نیازمند بررسی است.")}</p></div><div class="uncertainty-block"><span>بزرگ‌ترین خلأ اطلاعات</span><p>${text(uncertainty)}</p></div></div></section><section class="surface next-action-card">${sectionHeading("قدم بعدی", "تصمیم پیشنهادی", "این پیشنهاد حاصل داده پژوهشی است؛ جایگزین قضاوت انسانی نیست.")}<div class="next-action"><span class="next-action-mark">${detail.status === "READY FOR OUTREACH" ? "→" : "?"}</span><div><strong>${detail.status === "READY FOR OUTREACH" ? "بازبینی انسانی برای ارتباط" : detail.status === "NEEDS DISCOVERY" ? "پژوهش تکمیلی پیش از ارتباط" : "فعلاً در صف بررسی عمومی"}</strong><p>${text(detail.workflow?.hypothesis || detail.profile?.quality?.riskReasons?.[0], "گام بعدی از منابع عمومی قابل تعیین نیست.")}</p></div></div><div class="next-action-footer">${workflowBadge(detail.quality.workflowClass)}<span>${int(detail.quality.independentSourceCount)} منبع مستقل ثبت‌شده</span></div></section></div>`;
}

function profileValue(label, value, options = {}) {
  const display = options.array ? (Array.isArray(value) && value.length ? `<div class="inline-list">${value.slice(0, options.limit || 6).map((item) => `<span>${text(item)}</span>`).join("")}</div>` : text(null)) : text(value, options.fallback || "نامشخص");
  return `<div class="profile-field"><span>${escapeHtml(label)}</span><strong>${display}</strong></div>`;
}

function renderProfile(detail) {
  const scale = detail.profile?.scale || {};
  const tech = detail.profile?.technology || {};
  return `<section class="surface profile-surface">${sectionHeading("Company profile", "اطلاعات پایه و مقیاس", "unknown یک وضعیت معتبر است، نه فضای خالی.")}<div class="profile-grid">${profileValue("نوع شرکت", TYPE_LABELS[detail.companyType] || detail.companyType)}${profileValue("مدل کسب‌وکار", detail.businessModel, { array: true })}${profileValue("توضیح عمومی", detail.profile?.description)}${profileValue("محصولات / خدمات", detail.profile?.productsServices, { array: true, limit: 8 })}${profileValue("سال تأسیس", scale.foundedYear)}${profileValue("تعداد کارکنان", scale.employeeMin || scale.employeeMax ? `${scale.employeeMin ? int(scale.employeeMin) : "؟"} – ${scale.employeeMax ? int(scale.employeeMax) : "؟"}` : null)}${profileValue("شعبه", scale.branches)}${profileValue("کارخانه", scale.factories)}${profileValue("انبار", scale.warehouses)}${profileValue("گستره جغرافیایی", scale.geographicReach)}${profileValue("گواهی / عضویت", [...(detail.profile?.certifications || []), ...(detail.profile?.associations || [])], { array: true })}${profileValue("وضعیت فعالیت عمومی", profileStatus(detail.activeStatus, PROFILE_STATUS_LABELS))}${profileValue("وضعیت دیجیتال", profileStatus(tech.digitalStatus, DIGITAL_STATUS_LABELS))}${profileValue("توان فنی داخلی", profileStatus(tech.internalCapabilityStatus, TECH_STATUS_LABELS))}</div>${detail.profile?.operationalAddresses?.length ? `<div class="address-strip"><span>آدرس‌های عملیاتی ثبت‌شده</span>${detail.profile.operationalAddresses.slice(0, 5).map((item) => `<span>${text(item)}</span>`).join("")}</div>` : ""}</section>`;
}

function renderWorkflow(detail) {
  const workflow = detail.workflow;
  if (!workflow) return `<section class="surface workflow-surface">${emptyState("فرصت workflow ثبت نشده", "در داده فعلی پیشنهاد مشخصی برای این شرکت وجود ندارد.")}</section>`;
  const list = (items, fallback = "نامشخص") => items?.length ? `<ul>${items.map((item) => `<li>${text(item)}</li>`).join("")}</ul>` : `<span class="unknown-value">${escapeHtml(fallback)}</span>`;
  return `<section class="surface workflow-surface">${sectionHeading("فرصت LUMA", "فرصت عملیاتی اصلی", "این بخش باید قبل از تماس توسط انسان مرور شود.", workflow.classification ? workflowBadge(workflow.classification) : "")}<div class="workflow-head"><div><h3>${text(workflow.nameFa || workflow.name)}</h3><p>${text(workflow.solution, "راهکار مشخص در داده فعلی نیست.")}</p></div><div class="workflow-confidence"><strong>${confidence(workflow.confidenceScore)}</strong><span>اعتماد به فرضیه</span></div></div><div class="workflow-columns"><div><span>فرضیه فرایند فعلی</span><p>${text(workflow.hypothesis)}</p></div><div><span>مالک / کاربران</span><p>${text(workflow.businessOwner)} · ${text(workflow.primaryUsers)}</p></div><div><span>پیامد قابل اندازه‌گیری</span>${list(workflow.kpis)}</div><div><span>داده لازم</span>${list(workflow.requiredData)}</div><div><span>اتصال‌های لازم</span>${list(workflow.integrations)}</div><div><span>ریسک‌ها</span>${list(workflow.risks)}</div></div>${workflow.questions?.length ? `<div class="discovery-box"><span>سؤال‌های کشف</span>${list(workflow.questions)}</div>` : ""}</section>`;
}

function renderDecisions(detail) {
  return `<section class="surface decision-surface">${sectionHeading("مخاطبان کلیدی", "نقش‌های تصمیم‌گیری", "نقش، نام و میزان اعتماد را جدا ببینید.")}<div class="decision-grid">${(detail.decisions || []).map((decision) => `<article class="decision-card"><div class="decision-card-top"><span class="decision-label">${escapeHtml(decision.label)}</span><span class="decision-status ${decision.status === "VERIFIED_NAME" ? "is-verified" : ""}">${decision.status === "VERIFIED_NAME" ? "نام تأییدشده" : decision.status === "ROLE_ONLY" ? "فقط نقش" : "نامشخص"}</span></div><h3>${text(decision.name)}</h3><p>${text(decision.role)}</p><div class="decision-footer"><span>${decision.confidence === null ? "اعتماد نامشخص" : `اعتماد ${confidence(decision.confidence)}`}</span>${decision.sourceUrl ? externalLink(decision.sourceUrl, "منبع", "text-link") : `<span class="unknown-value">منبع نامشخص</span>`}</div></article>`).join("")}</div></section>`;
}

function renderContacts(detail) {
  const contact = detail.contacts || {};
  const rows = [
    ["وب‌سایت", contact.website ? externalLink(contact.website, contact.domain || contact.website, "contact-value ltr") : null, "website"],
    ["تلفن عمومی", contactCollection(contact.phones, "phone"), "phone"],
    ["ایمیل شرکتی", contactCollection(contact.emails, "email"), "email"],
    ["LinkedIn شرکت", contact.linkedin ? externalLink(contact.linkedin, "صفحه عمومی", "contact-value") : null, "linkedin"],
    ["WhatsApp شرکتی", contact.whatsapp ? externalLink(contact.whatsapp, "کانال عمومی", "contact-value") : null, "whatsapp"],
  ];
  return `<section class="surface contacts-surface">${sectionHeading("تماس عمومی", "کانال‌های عمومی", "این‌ها برای بازبینی انسانی‌اند؛ هیچ ارسال خودکاری وجود ندارد.")}<div class="contact-grid">${rows.map(([label, value, key]) => `<div class="contact-row"><span>${escapeHtml(label)}</span>${value || `<span class="unknown-value">عمومی ثبت نشده</span>`}${value && ["phone", "email"].includes(key) ? `<button class="copy-button" data-copy-contact="${escapeHtml(detail.id)}" data-copy-value="${escapeHtml((key === "phone" ? contact.phones : contact.emails).join("\n"))}" aria-label="کپی ${escapeHtml(label)}">${icon("copy")}</button>` : ""}</div>`).join("")}</div></section>`;
}

function evidenceTypeClass(type) {
  return String(type || "UNKNOWN").toLowerCase().replaceAll("_", "-");
}

function renderEvidenceCard(item) {
  const source = item.sourceUrl ? externalLink(item.sourceUrl, item.sourceTitle || "باز کردن منبع", "evidence-source-link") : `<span class="unknown-value">URL نامشخص</span>`;
  const evidenceType = item.type || "UNKNOWN";
  const evidenceLabel = EVIDENCE_LABELS[evidenceType] || evidenceType;
  const claim = plain(item.claim, "ادعای ثبت‌شده بدون متن");
  return `<article class="evidence-card"><div class="evidence-card-head"><span class="evidence-class evidence-${evidenceTypeClass(evidenceType)}" title="${escapeHtml(evidenceType)}">${escapeHtml(evidenceLabel)}</span><span class="evidence-confidence" title="اعتماد به این شاهد">${confidence(item.confidence)}</span></div><h3 ${valueAttrs(claim)}>${escapeHtml(claim)}</h3>${item.quote ? `<blockquote>${text(item.quote)}</blockquote>` : ""}<div class="evidence-card-footer"><div><strong>${escapeHtml(SOURCE_LABELS[item.sourceFamily] || item.sourceFamily || "نامشخص")}</strong><span>${source}</span></div><time>${escapeHtml(dateLabel(item.capturedAt))}</time></div></article>`;
}

function renderGallery(detail, lightbox) {
  const screenshots = Array.isArray(detail.assets?.screenshots) ? detail.assets.screenshots : [];
  return `<section class="surface visual-surface">${sectionHeading("Visual evidence", "تصویرهای ثبت‌شده", "تصویر، مدرک داخلی است؛ جایگزین source یا claim نیست.", `${int(screenshots.length)} تصویر`)}${screenshots.length ? `<div class="screenshot-grid">${screenshots.map((item, index) => `<button class="screenshot-tile" data-lightbox="${index}" aria-label="باز کردن تصویر ${index + 1}"><img src="${escapeHtml(item.url)}" alt="شاهد تصویری ${index + 1} برای ${escapeHtml(detail.nameFa)}" loading="lazy"><span><strong>${int(index + 1)}</strong><small class="cell-wrap" ${valueAttrs(item.reason || "شاهد تصویری ذخیره‌شده")}>${escapeHtml(item.reason || "شاهد تصویری ذخیره‌شده")}</small></span></button>`).join("")}</div>` : emptyState("تصویر شواهد ندارد", "برای این شرکت screenshot داخلی در evidence package ثبت نشده است.")}</section>`;
}

function renderEvidenceDetail(detail) {
  const evidence = detail.evidence || [];
  const sourceFamilies = detail.sourceFamilies || [];
  const topEvidence = evidence.slice(0, 18);
  const storedFiles = Array.isArray(detail.assets?.files) ? detail.assets.files : [];
  return `<div class="detail-tab-page evidence-detail-page"><div class="evidence-detail-summary"><div><span class="eyebrow">دفترچه شواهد</span><h3>${int(evidence.length)} شاهد ثبت‌شده</h3><p>برای هر ادعا، نوع شاهد، منبع و میزان اعتماد را کنار هم ببینید.</p></div><div class="detail-quality-block"><strong>${int(detail.quality.independentSourceCount)}</strong><span>منبع مستقل اعلام‌شده</span><small>${detail.quality.independentSourceFamilies.map((family) => escapeHtml(SOURCE_LABELS[family] || family)).join(" · ") || "نامشخص"}</small></div></div>${renderGallery(detail)}<section class="surface evidence-cards-surface">${sectionHeading("شواهد متنی", "ادعاها و مشاهدات", "مشاهده‌شده، استنباط و نامشخص با رنگ و متن جدا شده‌اند.", `${int(evidence.length)} رکورد`)}<div class="evidence-card-grid">${topEvidence.length ? topEvidence.map(renderEvidenceCard).join("") : emptyState("متن شواهد موجود نیست", "منبع یا ادعای ساختاریافته‌ای برای این شرکت ثبت نشده است.")}</div>${evidence.length > topEvidence.length ? `<div class="more-note">${int(evidence.length - topEvidence.length)} مورد دیگر در شاخص ذخیره است؛ برای جلوگیری از ازدحام، این نما ۱۸ مورد اول را نشان می‌دهد.</div>` : ""}</section><section class="surface source-families-surface">${sectionHeading("منابع مستقل", "خانواده‌های منبع", "چند صفحه از یک family را با چند منبع مستقل اشتباه نکنید.", `<strong class="source-total">${int(sourceFamilies.length)} خانواده</strong>`)}<div class="source-family-grid">${sourceFamilies.map((source) => `<article class="source-family-card"><div class="source-family-top"><span>${escapeHtml(SOURCE_LABELS[source.family] || source.family)}</span><strong>${int(source.count)}</strong></div><small>${escapeHtml(source.sourceType || "نوع منبع نامشخص")} · ${escapeHtml(source.quality || "کیفیت نامشخص")}</small>${source.titles?.length ? `<p class="cell-wrap" ${valueAttrs(source.titles[0])}>${escapeHtml(source.titles[0])}</p>` : ""}<div class="source-url-list">${(Array.isArray(source.urls) ? source.urls : []).slice(0, 4).map((url) => externalLink(url, (() => { try { return new URL(url).hostname; } catch { return "منبع"; } })(), "source-url")).join("")}</div></article>`).join("") || emptyState("خانواده مستقلی ثبت نشده", "در داده فعلی خانواده منبع قابل نمایش نیست.")}</div></section><section class="surface stored-files-surface">${sectionHeading("فایل‌های ذخیره‌شده", "فایل‌های محلی شواهد", "نسخه ذخیره‌شده برای بررسی داخلی؛ URL منبع جداست.")}<div class="stored-file-list">${storedFiles.slice(0, 24).map((file) => `${localLink(file.url, file.path, "stored-file")}`).join("") || `<span class="unknown-value">فایل محلی ندارد</span>`}</div></section></div>`;
}

function materialButton(key, label, material, active) {
  return `<button class="material-tab ${active === key ? "is-active" : ""}" data-material-tab="${escapeHtml(key)}" ${material?.available ? "" : "disabled"}>${icon(key === "dossier" ? "file" : key === "outreach" ? "arrow" : "note")}<span>${escapeHtml(label)}</span>${material?.available ? "" : `<small>ناموجود</small>`}</button>`;
}

function renderMaterialBody(state, detail, key) {
  const material = detail.materials?.[key];
  if (!material?.available) return emptyState("این سند موجود نیست", "برای این شرکت فایل متناظر در repository پیدا نشد.");
  const cached = state.materialCache?.[`${detail.id}:${key}`];
  if (cached === "loading") return `<div class="material-loading"><span class="loading-line"></span><span class="loading-line short"></span><span class="loading-line"></span><p>در حال خواندن فایل محلی…</p></div>`;
  if (cached?.error) return emptyState("خواندن سند ممکن نشد", cached.error, `<button class="button button-light" data-load-material="${escapeHtml(key)}">تلاش دوباره</button>`);
  if (!cached) return `<div class="material-placeholder"><span>${icon("file")}</span><h3>${escapeHtml(material.path)}</h3><p>این Markdown از repository داخل داشبورد render می‌شود.</p><button class="button button-dark" data-load-material="${escapeHtml(key)}">نمایش سند ${icon("arrow")}</button></div>`;
  return `<div class="material-render"><div class="material-meta"><span>${escapeHtml(material.path)}</span><button class="text-button" data-copy-material="${escapeHtml(key)}">کپی متن ${icon("copy")}</button></div><article class="markdown-body">${renderMarkdown(cached)}</article></div>`;
}

function renderMaterialsDetail(detail, state) {
  const materials = detail.materials || {};
  const tabs = [["internal", "خلاصه داخلی"], ["proposalClient", "پیشنهاد مشتری"], ["outreach", "پیش‌نویس ارتباط"], ["dossier", "پرونده"], ["proposal", "پیشنهاد پژوهشی"]];
  const active = state.materialTab || "internal";
  return `<div class="detail-tab-page materials-detail-page"><div class="materials-intro"><div><span class="eyebrow">مواد فروش</span><h3>اسناد این پرونده داخل داشبورد</h3><p>هر فایل از مسیر واقعی repository خوانده می‌شود؛ نسخه canonical بازنویسی نمی‌شود.</p></div><div class="material-count"><strong>${int(tabs.filter(([key]) => materials[key]?.available).length)}</strong><span>سند موجود</span></div></div><div class="materials-layout"><nav class="material-tabs" aria-label="اسناد فروش">${tabs.map(([key, label]) => materialButton(key, label, materials[key], active)).join("")}</nav><section class="surface material-surface">${renderMaterialBody(state, detail, active)}</section></div>${detail.demo ? `<section class="surface demo-link-surface">${sectionHeading("دموی محلی", "دموی محلی این شرکت", "ساختار demo به‌صورت خودکار از پوشه demos شناسایی شده است.", `<span class="badge status-ready"><span class="badge-dot"></span>موجود</span>`)}<div class="demo-link-grid"><a class="demo-link-card" href="${escapeHtml(detail.demo.route)}" target="_blank" rel="noopener noreferrer">${icon("demo")}<strong>باز کردن دمو</strong><span>route محلی، در تب جدا</span></a>${detail.demo.readmePath ? `<button class="demo-link-card" data-material-path="${escapeHtml(detail.demo.readmePath)}">${icon("file")}<strong>راهنمای دمو</strong><span>نمایش سند محلی</span></button>` : ""}${detail.demo.scriptPath ? `<button class="demo-link-card" data-material-path="${escapeHtml(detail.demo.scriptPath)}">${icon("note")}<strong>سناریوی ارائه</strong><span>راهنمای ارائه</span></button>` : ""}${detail.demo.questionsPath ? `<button class="demo-link-card" data-material-path="${escapeHtml(detail.demo.questionsPath)}">${icon("search")}<strong>سؤال‌های کشف</strong><span>سؤال‌های جلسه کشف</span></button>` : ""}</div></section>` : ""}</div>`;
}

function renderHistory(detail) {
  const history = detail.profile?.history || {};
  const classification = detail.profile?.classification || {};
  return `<div class="detail-tab-page history-detail-page"><div class="history-banner"><span class="eyebrow">ردپای پژوهش</span><h3>تغییرات رتبه و طبقه‌بندی در طول پژوهش</h3><p>این بخش برای فهمیدن چرایی تصمیم‌هاست، نه برای تغییر داده canonical.</p></div><div class="history-grid"><section class="surface history-card">${sectionHeading("مقایسه پیشین و فعلی", "مقایسه امتیازها", "مقادیر اصلی و فعلی را کنار هم بخوانید.")}<div class="history-score-grid"><div><span>Tier قبلی</span><strong>${text(history.originalTier)}</strong><small>اکنون ${escapeHtml(TIER_LABELS[detail.tier] || detail.tier)}</small></div><div><span>فرصت قبلی</span><strong>${score(history.originalOpportunity)}</strong><small>اکنون ${score(detail.scores.opportunity)}</small></div><div><span>اعتماد قبلی</span><strong>${confidence(history.originalConfidence)}</strong><small>اکنون ${confidence(detail.scores.scoreConfidence)}</small></div><div><span>تراکم workflow قبلی</span><strong>${score(history.originalWorkflowDensity)}</strong><small>اکنون ${score(detail.scores.workflowDensity)}</small></div></div></section><section class="surface history-card">${sectionHeading("طبقه‌بندی", "چرا این طبقه‌بندی؟", "اصلاح نوع شرکت و میزان اعتماد را شفاف نگه می‌داریم.")}<div class="history-facts"><div><span>صنعت قبلی</span><strong>${text(history.originalIndustry)}</strong></div><div><span>اعتماد به طبقه‌بندی</span><strong>${score(classification.confidence)}</strong></div><div><span>دلیل</span><p>${text(classification.reason)}</p></div><div><span>طبقه‌بندی دوباره</span><p>${text(classification.reclassification)}</p></div></div></section></div><section class="surface timeline-surface">${sectionHeading("زمان‌بندی پژوهش", "تاریخچه زمانی", "منابع و خروجی‌های این پرونده چه زمانی به‌روزرسانی شده‌اند.")}<div class="timeline"><div><span>آخرین پژوهش</span><strong>${escapeHtml(dateLabel(history.lastResearchDate))}</strong></div><div><span>آخرین فعال‌سازی</span><strong>${escapeHtml(dateLabel(history.lastActivationDate))}</strong></div><div><span>نسخه امتیازدهی</span><strong dir="ltr">${text(history.scoreVersion)}</strong></div><div><span>نسخه audit</span><strong dir="ltr">${text(history.auditVersion)}</strong></div></div></section></div>`;
}

function renderReviewPanel(detail, review) {
  return `<section class="surface human-review-surface" id="review-panel">${sectionHeading("بررسی انسانی", "تصمیم شخصی شما", "این فیلدها در local review state ذخیره می‌شوند و به پژوهش canonical نمی‌چسبند.", reviewBadge(review.status))}<div class="review-form"><label for="review-status"><span>وضعیت بررسی</span><select id="review-status"><option value="UNREVIEWED" ${review.status === "UNREVIEWED" ? "selected" : ""}>بررسی‌نشده</option><option value="APPROVED_FOR_OUTREACH" ${review.status === "APPROVED_FOR_OUTREACH" ? "selected" : ""}>تأیید برای ارتباط</option><option value="NEEDS_MORE_RESEARCH" ${review.status === "NEEDS_MORE_RESEARCH" ? "selected" : ""}>نیازمند پژوهش بیشتر</option><option value="REJECTED_BY_HUMAN" ${review.status === "REJECTED_BY_HUMAN" ? "selected" : ""}>ردشده توسط انسان</option><option value="FOLLOW_UP_LATER" ${review.status === "FOLLOW_UP_LATER" ? "selected" : ""}>پیگیری بعدی</option></select></label><label class="note-field" for="review-note"><span>یادداشت داخلی</span><textarea id="review-note" maxlength="5000" placeholder="چرا این شرکت را نگه می‌دارید یا چه چیزی باید بررسی شود؟">${escapeHtml(review.note || "")}</textarea></label><div class="review-form-footer"><span>${review.updatedAt ? `آخرین تغییر: ${escapeHtml(dateLabel(review.updatedAt))}` : "هنوز ذخیره نشده"}</span><button class="button button-dark" data-save-review="${escapeHtml(detail.id)}">ذخیره تصمیم محلی ${icon("arrow")}</button></div></div></section>`;
}

function renderDetailOverview(detail, reviews) {
  const review = reviewFor(reviews, detail.id);
  return `<div class="detail-tab-page detail-overview-page">${renderSummaryCard(detail)}${renderProfile(detail)}${renderWorkflow(detail)}<div class="detail-two-col">${renderDecisions(detail)}${renderContacts(detail)}</div>${renderReviewPanel(detail, review)}</div>`;
}

function renderLightbox(detail, index) {
  const item = detail?.assets?.screenshots?.[index];
  if (!item) return "";
  return `<div class="lightbox-backdrop" data-lightbox-close="true"><div class="lightbox-dialog" role="dialog" aria-modal="true" aria-label="تصویر شواهد" tabindex="-1"><button class="lightbox-close" data-lightbox-close="true" aria-label="بستن">×</button><img src="${escapeHtml(item.url)}" alt="شاهد تصویری ${escapeHtml(detail.nameFa)}"><div class="lightbox-caption"><strong>${escapeHtml(detail.nameFa)}</strong><span>${escapeHtml(item.reason || "شاهد تصویری ذخیره‌شده")}</span><small>${item.sourceUrl ? escapeHtml(item.sourceUrl) : "جزئیات source در metadata تصویر موجود نیست."}</small></div></div></div>`;
}

function renderDetail(detail, state, reviews) {
  const review = reviewFor(reviews, detail.id);
  const tabs = [["overview", "نمای کلی"], ["evidence", "شواهد"], ["materials", "مواد فروش"], ["history", "تاریخچه پژوهش"]];
  return `<div class="page detail-page">${renderDetailHeader(detail, review)}<div class="detail-tabs" role="tablist" aria-label="بخش‌های پرونده">${tabs.map(([key, label]) => `<button class="detail-tab ${state.detailTab === key ? "is-active" : ""}" data-detail-tab="${key}" role="tab" aria-selected="${state.detailTab === key}">${escapeHtml(label)}</button>`).join("")}</div>${state.detailTab === "overview" ? renderDetailOverview(detail, reviews) : state.detailTab === "evidence" ? renderEvidenceDetail(detail) : state.detailTab === "materials" ? renderMaterialsDetail(detail, state) : renderHistory(detail)}${state.lightboxIndex !== null && state.lightboxIndex !== undefined ? renderLightbox(detail, state.lightboxIndex) : ""}</div>`;
}

function paletteResults(index, query) {
  const normalized = String(query || "").trim().toLocaleLowerCase("fa-IR");
  const commands = [
    { type: "action", label: "نمای کلی", detail: "مشاهده وضعیت کل dataset", action: "overview" },
    { type: "action", label: "Wave 1", detail: "۱۰ پرونده برای تماس اول", action: "ready" },
    { type: "action", label: "میز شواهد", detail: "کیفیت source و screenshot", action: "evidence" },
    { type: "action", label: "شرکت‌های بدون تصمیم‌گیرنده", detail: "فیلتر نام‌های unknown", action: "missingDecision" },
  ];
  if (!normalized) return commands;
  return [...commands.filter((item) => `${item.label} ${item.detail}`.toLocaleLowerCase("fa-IR").includes(normalized)), ...index.companies.filter((company) => company.searchText.includes(normalized)).slice(0, 8).map((company) => ({ type: "company", label: company.nameFa, detail: `${company.industryLabel} · ${STATUS_LABELS[company.status] || "نامشخص"}`, id: company.id }))];
}

function renderPalette(index, state) {
  if (!state.paletteOpen) return "";
  const results = paletteResults(index, state.paletteQuery);
  return `<div class="palette-backdrop" data-palette-close="true"><section class="command-palette" role="dialog" aria-modal="true" aria-label="فرمان سریع"><div class="palette-head"><span>${icon("search")}</span><input id="palette-search" type="search" placeholder="جست‌وجو یا فرمان…" value="${escapeHtml(state.paletteQuery || "")}" autofocus><kbd>ESC</kbd></div><div class="palette-results">${results.length ? results.map((result) => `<button class="palette-result" data-palette-action="${escapeHtml(result.action || "company")}" ${result.id ? `data-company-open="${escapeHtml(result.id)}"` : ""}>${result.type === "company" ? `<span class="palette-avatar">${escapeHtml(result.label.slice(0, 1))}</span>` : `<span class="palette-command">⌘</span>`}<span><strong>${escapeHtml(result.label)}</strong><small>${escapeHtml(result.detail)}</small></span>${icon("arrow")}</button>`).join("") : emptyState("نتیجه‌ای نیست", "نام یا فرمان دیگری را امتحان کنید.")}</div><div class="palette-footer"><span>جست‌وجوی سریع محلی</span><span><kbd>↑↓</kbd> حرکت <kbd>↵</kbd> انتخاب</span></div></section></div>`;
}

function renderFileViewer(state) {
  const viewer = state.fileViewer;
  if (!viewer) return "";
  const body = viewer.loading
    ? `<div class="material-loading"><span class="loading-line"></span><span class="loading-line short"></span><p>در حال خواندن سند محلی…</p></div>`
    : viewer.error
      ? emptyState("خواندن سند ممکن نشد", viewer.error)
      : `<article class="markdown-body">${renderMarkdown(viewer.text)}</article>`;
  return `<div class="file-viewer-backdrop" data-file-viewer-close="true"><section class="file-viewer-dialog" role="dialog" aria-modal="true" aria-label="سند محلی"><header><div><span class="eyebrow">Repository material</span><h2>${escapeHtml(viewer.path || "سند محلی")}</h2></div><div class="file-viewer-actions"><button class="text-button" data-copy-file-viewer="true">کپی متن ${icon("copy")}</button><button class="icon-button large" data-file-viewer-close="true" aria-label="بستن">×</button></div></header><div class="file-viewer-body">${body}</div></section></div>`;
}

export function renderDashboard({ index, reviews, state, companies, pagination, detail }) {
  const view = detail ? "detail" : state.view;
  const content = detail ? renderDetail(detail, state, reviews) : view === "overview" ? renderOverview(index, reviews) : view === "companies" ? renderCompanies(index, reviews, state, companies, pagination) : view === "ready" ? renderReady(index, reviews, state) : view === "evidence" ? renderEvidence(index, reviews, state, companies) : view === "review" ? renderReview(index, reviews, state, companies) : view === "compare" ? renderCompare(index, reviews, state.selectedCompare) : renderOverview(index, reviews);
  return `<div class="dashboard-shell"><div class="shell-frame">${renderSidebar(view, index, reviews)}<div class="main-column">${renderHeader(view, index, state)}<main id="main-content" tabindex="-1">${content}</main><footer class="app-footer"><span>${icon("lock")} LUMA B2B Research OS · فقط برای review داخلی</span><span>Source of truth: <code dir="ltr">data/normalized/companies.jsonl</code></span></footer></div></div>${state.selectedCompare.length ? `<div class="compare-dock"><span><strong>${int(state.selectedCompare.length)}</strong> شرکت برای مقایسه</span><div>${state.selectedCompare.slice(0, 4).map((id) => { const company = index.companies.find((item) => item.id === id); return company ? `<button data-company-open="${escapeHtml(id)}">${escapeHtml(company.nameFa)}</button>` : ""; }).join("")}</div><button class="button button-dark" data-compare-go="true">مقایسه ${icon("arrow")}</button></div>` : ""}${renderPalette(index, state)}${renderFileViewer(state)}${state.toast ? `<div class="toast" role="status" aria-live="polite">${escapeHtml(state.toast)}</div>` : ""}</div>`;
}

export { REVIEW_LABELS, STATUS_LABELS, TYPE_LABELS, WORKFLOW_LABELS };
