import { renderDashboard } from "./views.js";

const root = document.querySelector("#app");

const DEFAULT_FILTERS = {
  status: "ALL",
  tier: "ALL",
  wave: "ALL",
  industry: "ALL",
  companyType: "ALL",
  workflow: "ALL",
  opportunityMin: "",
  adjustedMin: "",
  evidenceMin: "",
  confidenceMin: "",
  firstContactMin: "",
  enriched: false,
  threePlus: false,
  hasScreenshots: false,
  hasDecision: false,
  directoryOnly: false,
  hasContact: false,
};

const state = {
  view: "overview",
  query: "",
  filters: { ...DEFAULT_FILTERS },
  sort: "adjusted",
  page: 1,
  pageSize: 24,
  wave: "WAVE 1",
  evidenceFilter: "all",
  reviewFilter: "UNREVIEWED",
  selectedCompare: [],
  detailTab: "overview",
  detail: null,
  returnView: "companies",
  materialTab: "internal",
  materialCache: {},
  fileViewer: null,
  lightboxIndex: null,
  paletteOpen: false,
  paletteQuery: "",
  toast: "",
};

let index = null;
let reviews = { version: 1, updatedAt: null, companies: {} };
let toastTimer = null;
let renderQueued = false;

const VALID_VIEWS = new Set(["overview", "companies", "ready", "evidence", "review", "compare"]);
const VALID_DETAIL_TABS = new Set(["overview", "evidence", "materials", "history"]);
const VALID_REVIEW_FILTERS = new Set(["UNREVIEWED", "APPROVED_FOR_OUTREACH", "NEEDS_MORE_RESEARCH", "REJECTED_BY_HUMAN", "FOLLOW_UP_LATER"]);

function normalizeSearch(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .replace(/[يى]/g, "ی")
    .replace(/[ك]/g, "ک")
    .replace(/[ۀة]/g, "ه")
    .replace(/[ؤإأ]/g, "ا")
    .replace(/[\u200c\u200d]/g, " ")
    .replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
    .toLocaleLowerCase("fa-IR")
    .replace(/\s+/g, " ")
    .trim();
}

function reviewFor(id) {
  return reviews.companies?.[id] || {
    status: "UNREVIEWED",
    favorite: false,
    note: "",
    reviewedAt: null,
    updatedAt: null,
  };
}

function companyById(id) {
  return index?.companies.find((company) => company.id === id) || null;
}

function numeric(value) {
  if (value === null || value === undefined || value === "" || value === "UNKNOWN") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function atLeast(value, minimum) {
  const parsedValue = numeric(value);
  const parsedMinimum = numeric(minimum);
  return parsedMinimum === null || (parsedValue !== null && parsedValue >= parsedMinimum);
}

function hasVerifiedDecision(company) {
  return Boolean(company.decisions?.some((decision) => decision.status === "VERIFIED_NAME" && decision.name));
}

function hasPublicContact(company) {
  return Boolean(company.contacts?.phones?.length || company.contacts?.emails?.length || company.contacts?.linkedin);
}

function sortRows(rows) {
  const valueFor = (company) => {
    if (state.sort === "firstContact") return numeric(company.scores?.firstContact);
    if (state.sort === "evidence") return numeric(company.quality?.evidenceStrength);
    if (state.sort === "opportunity") return numeric(company.scores?.opportunity);
    if (state.sort === "research") return numeric(company.dossierRank) === null ? null : -numeric(company.dossierRank);
    return numeric(company.scores?.adjusted);
  };
  return [...rows].sort((left, right) => {
    if (state.sort === "name") return String(left.nameFa || "").localeCompare(String(right.nameFa || ""), "fa");
    const leftValue = valueFor(left);
    const rightValue = valueFor(right);
    if (leftValue === null && rightValue !== null) return 1;
    if (rightValue === null && leftValue !== null) return -1;
    if (leftValue !== rightValue) return (rightValue ?? -Infinity) - (leftValue ?? -Infinity);
    return String(left.nameFa || "").localeCompare(String(right.nameFa || ""), "fa");
  });
}

function explorerRows() {
  const filters = state.filters;
  const query = normalizeSearch(state.query);
  const rows = index.companies.filter((company) => {
    if (query && !String(company.searchText || "").includes(query)) return false;
    if (filters.status !== "ALL" && company.status !== filters.status) return false;
    if (filters.tier !== "ALL" && company.tier !== filters.tier) return false;
    if (filters.wave !== "ALL" && company.wave !== filters.wave) return false;
    if (filters.industry !== "ALL" && company.industry !== filters.industry) return false;
    if (filters.companyType !== "ALL" && company.companyType !== filters.companyType) return false;
    if (filters.workflow !== "ALL" && company.quality?.workflowClass !== filters.workflow) return false;
    if (filters.enriched && company.researchStatus !== "MEANINGFULLY_ENRICHED") return false;
    if (!atLeast(company.scores?.opportunity, filters.opportunityMin)) return false;
    if (!atLeast(company.scores?.adjusted, filters.adjustedMin)) return false;
    if (!atLeast(company.quality?.evidenceStrength, filters.evidenceMin)) return false;
    if (!atLeast(company.quality?.scoreConfidence, filters.confidenceMin)) return false;
    if (!atLeast(company.scores?.firstContact, filters.firstContactMin)) return false;
    if (filters.threePlus && !company.quality?.hasThreePlusSources) return false;
    if (filters.hasScreenshots && !(company.quality?.screenshots > 0)) return false;
    if (filters.hasDecision && !hasVerifiedDecision(company)) return false;
    if (filters.directoryOnly && !company.quality?.directoryOnly) return false;
    if (filters.hasContact && !hasPublicContact(company)) return false;
    return true;
  });
  return sortRows(rows);
}

function paginated(rows) {
  const pages = Math.max(1, Math.ceil(rows.length / state.pageSize));
  state.page = Math.min(Math.max(1, state.page), pages);
  const start = (state.page - 1) * state.pageSize;
  return {
    rows: rows.slice(start, start + state.pageSize),
    pagination: { page: state.page, pages, pageSize: state.pageSize, total: rows.length },
  };
}

function evidenceRows() {
  const filter = state.evidenceFilter;
  let rows = index.companies;
  if (filter === "three") rows = rows.filter((company) => company.quality?.hasThreePlusSources);
  if (filter === "screenshots") rows = rows.filter((company) => company.quality?.screenshots > 0);
  if (filter === "decision") rows = rows.filter(hasVerifiedDecision);
  if (filter === "directory") rows = rows.filter((company) => company.quality?.directoryOnly);
  if (filter === "supported") rows = rows.filter((company) => company.quality?.workflowClass === "EVIDENCE_SUPPORTED");
  if (filter === "unknown") rows = rows.filter((company) => (company.quality?.unknownFieldCount || 0) >= 4 || company.quality?.workflowClass === "UNKNOWN");
  return [...rows].sort((left, right) => {
    const leftScore = numeric(left.quality?.evidenceStrength) ?? -1;
    const rightScore = numeric(right.quality?.evidenceStrength) ?? -1;
    return rightScore - leftScore || String(left.nameFa).localeCompare(String(right.nameFa), "fa");
  }).slice(0, 160);
}

function reviewRows() {
  const candidates = index.companies.filter((company) => {
    const review = reviewFor(company.id);
    if (state.reviewFilter === "UNREVIEWED") {
      return review.status === "UNREVIEWED" && ["READY FOR OUTREACH", "NEEDS DISCOVERY"].includes(company.status);
    }
    return review.status === state.reviewFilter;
  });
  return [...candidates].sort((left, right) => {
    const leftValue = numeric(left.scores?.firstContact) ?? numeric(left.scores?.adjusted) ?? -1;
    const rightValue = numeric(right.scores?.firstContact) ?? numeric(right.scores?.adjusted) ?? -1;
    return rightValue - leftValue || String(left.nameFa).localeCompare(String(right.nameFa), "fa");
  }).slice(0, 120);
}

function syncUrl(replace = false) {
  const params = new URLSearchParams();
  if (state.detail && state.view === "detail") {
    params.set("company", state.detail.id);
    if (state.detailTab !== "overview") params.set("tab", state.detailTab);
  } else {
    params.set("view", state.view);
    if (state.view === "ready" && state.wave !== "WAVE 1") params.set("wave", state.wave);
    if (state.view === "companies") {
      if (state.query) params.set("q", state.query);
      for (const key of ["status", "tier", "wave", "industry", "companyType", "workflow"]) {
        if (state.filters[key] && state.filters[key] !== "ALL") params.set(key, state.filters[key]);
      }
      if (state.filters.enriched) params.set("enriched", "true");
      if (state.filters.threePlus) params.set("evidence", "three");
    }
    if (state.view === "evidence" && state.evidenceFilter !== "all") params.set("evidenceFilter", state.evidenceFilter);
  }
  const next = `${location.pathname}?${params.toString()}`;
  const method = replace ? "replaceState" : "pushState";
  history[method]({}, "", next);
}

function parseUrl() {
  const params = new URLSearchParams(location.search);
  const companyId = params.get("company");
  state.query = params.get("q") || "";
  state.view = companyId ? "detail" : (VALID_VIEWS.has(params.get("view")) ? params.get("view") : "overview");
  state.wave = ["WAVE 1", "WAVE 2", "WAVE 3"].includes(params.get("wave")) ? params.get("wave") : "WAVE 1";
  state.detailTab = VALID_DETAIL_TABS.has(params.get("tab")) ? params.get("tab") : "overview";
  state.evidenceFilter = params.get("evidenceFilter") || "all";
  state.filters = { ...DEFAULT_FILTERS };
  for (const key of ["status", "tier", "wave", "industry", "companyType", "workflow"]) {
    if (params.has(key)) state.filters[key] = params.get(key);
  }
  state.filters.enriched = params.get("enriched") === "true";
  state.filters.threePlus = params.get("evidence") === "three";
  return companyId;
}

function restoreFocus(previousId) {
  requestAnimationFrame(() => {
    if (state.paletteOpen) {
      document.querySelector("#palette-search")?.focus();
      return;
    }
    const element = previousId ? document.getElementById(previousId) : null;
    if (element) {
      element.focus();
      if (typeof element.setSelectionRange === "function") {
        const end = element.value.length;
        element.setSelectionRange(end, end);
      }
    }
  });
}

function render(options = {}) {
  if (!index) return;
  const activeId = document.activeElement?.id || null;
  let companies = [];
  let pagination = { page: 1, pages: 1, pageSize: state.pageSize, total: 0 };
  if (state.view === "companies") {
    const result = paginated(explorerRows());
    companies = result.rows;
    pagination = result.pagination;
  } else if (state.view === "evidence") {
    companies = evidenceRows();
  } else if (state.view === "review") {
    companies = reviewRows();
  }
  root.innerHTML = renderDashboard({ index, reviews, state, companies, pagination, detail: state.detail });
  if (options.focus !== false) {
    requestAnimationFrame(() => document.querySelector("#main-content")?.focus({ preventScroll: true }));
  }
  if (options.restoreFocus !== false && activeId && !options.focus) restoreFocus(activeId);
}

function setToast(message) {
  state.toast = message;
  render({ focus: false });
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    state.toast = "";
    render({ focus: false });
  }, 3600);
}

function navigate(view, options = {}) {
  if (!VALID_VIEWS.has(view)) return;
  state.view = view;
  state.detail = null;
  state.page = 1;
  state.paletteOpen = false;
  if (options.wave) state.wave = options.wave;
  if (options.evidenceFilter) state.evidenceFilter = options.evidenceFilter;
  if (options.push !== false) syncUrl();
  render();
}

async function openCompany(id, options = {}) {
  const summary = companyById(id);
  if (!summary) {
    setToast("پرونده شرکت در شاخص محلی پیدا نشد.");
    return;
  }
  if (state.view !== "detail") state.returnView = state.view;
  state.view = "detail";
  state.detail = summary;
  state.detailTab = options.tab || "overview";
  state.materialCache = {};
  state.fileViewer = null;
  state.lightboxIndex = null;
  state.paletteOpen = false;
  if (options.push !== false) syncUrl();
  render();
  try {
    const response = await fetch(`/api/companies/${encodeURIComponent(id)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const detail = await response.json();
    state.detail = detail;
    if (detail.review) reviews.companies[id] = detail.review;
    render();
  } catch (error) {
    setToast(`جزئیات کامل بارگذاری نشد؛ نمای خلاصه باقی ماند (${error.message}).`);
  }
}

function closeDetail() {
  state.detail = null;
  state.view = VALID_VIEWS.has(state.returnView) ? state.returnView : "companies";
  state.paletteOpen = false;
  syncUrl();
  render();
}

async function saveReview(id) {
  const status = document.querySelector("#review-status")?.value || "UNREVIEWED";
  const note = document.querySelector("#review-note")?.value || "";
  const current = reviewFor(id);
  try {
    const response = await fetch(`/api/review-state/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, note, favorite: current.favorite === true }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    reviews.companies[id] = await response.json();
    reviews.updatedAt = reviews.companies[id].updatedAt;
    setToast("تصمیم انسانی در ذخیره‌سازی محلی ثبت شد.");
  } catch (error) {
    setToast(`ذخیره تصمیم انجام نشد: ${error.message}`);
  }
}

async function toggleFavorite(id) {
  const current = reviewFor(id);
  try {
    const response = await fetch(`/api/review-state/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: current.status, note: current.note || "", favorite: !current.favorite }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    reviews.companies[id] = await response.json();
    reviews.updatedAt = reviews.companies[id].updatedAt;
    render({ focus: false });
  } catch (error) {
    setToast(`تغییر علاقه‌مندی انجام نشد: ${error.message}`);
  }
}

async function copyText(value, success = "کپی شد.") {
  if (!value) {
    setToast("اطلاعاتی برای کپی وجود ندارد.");
    return;
  }
  try {
    await navigator.clipboard.writeText(value);
    setToast(success);
  } catch {
    setToast("کپی خودکار در این مرورگر در دسترس نیست.");
  }
}

async function loadMaterial(key) {
  const detail = state.detail;
  const material = detail?.materials?.[key];
  if (!material?.available) return;
  const cacheKey = `${detail.id}:${key}`;
  state.materialCache[cacheKey] = "loading";
  render({ focus: false });
  try {
    const response = await fetch(`/api/material?path=${encodeURIComponent(material.path)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.materialCache[cacheKey] = await response.text();
  } catch (error) {
    state.materialCache[cacheKey] = { error: error.message };
  }
  render({ focus: false });
}

async function openFileViewer(relativePath) {
  state.fileViewer = { path: relativePath, loading: true, text: "" };
  render({ focus: false });
  try {
    const response = await fetch(`/api/material?path=${encodeURIComponent(relativePath)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.fileViewer = { path: relativePath, loading: false, text: await response.text() };
  } catch (error) {
    state.fileViewer = { path: relativePath, loading: false, error: error.message, text: "" };
  }
  render({ focus: false });
}

function toggleCompare(id) {
  if (state.selectedCompare.includes(id)) {
    state.selectedCompare = state.selectedCompare.filter((item) => item !== id);
  } else if (state.selectedCompare.length >= 4) {
    setToast("مقایسه برای خوانایی به حداکثر چهار شرکت محدود است.");
    return;
  } else {
    state.selectedCompare = [...state.selectedCompare, id];
  }
  render({ focus: false });
}

function handlePaletteAction(action) {
  state.paletteOpen = false;
  state.paletteQuery = "";
  if (action === "overview") return navigate("overview");
  if (action === "ready") return navigate("ready", { wave: "WAVE 1" });
  if (action === "evidence") return navigate("evidence", { evidenceFilter: "all" });
  if (action === "missingDecision") return navigate("evidence", { evidenceFilter: "decision" });
}

function handleClick(event) {
  const companyTarget = event.target.closest("[data-company-open]");
  if (companyTarget) {
    event.preventDefault();
    openCompany(companyTarget.dataset.companyOpen);
    return;
  }

  const fileClose = event.target.closest("[data-file-viewer-close]");
  if (fileClose && event.target === fileClose) {
    state.fileViewer = null;
    render({ focus: false });
    return;
  }
  const paletteClose = event.target.closest("[data-palette-close]");
  if (paletteClose && event.target === paletteClose) {
    state.paletteOpen = false;
    state.paletteQuery = "";
    render({ focus: false });
    return;
  }
  const lightboxClose = event.target.closest("[data-lightbox-close]");
  if (lightboxClose && event.target === lightboxClose) {
    state.lightboxIndex = null;
    render({ focus: false });
    return;
  }

  const target = event.target.closest("button, a, [data-filter]");
  if (!target) return;
  if (target.dataset.view) {
    event.preventDefault();
    navigate(target.dataset.view);
    return;
  }
  if (target.dataset.back) {
    event.preventDefault();
    closeDetail();
    return;
  }
  if (target.dataset.paletteOpen) {
    state.paletteOpen = true;
    state.paletteQuery = "";
    render({ focus: false });
    return;
  }
  if (target.dataset.paletteAction && !target.dataset.companyOpen) {
    event.preventDefault();
    handlePaletteAction(target.dataset.paletteAction);
    return;
  }
  if (target.dataset.wave) {
    state.wave = target.dataset.wave;
    render({ focus: false });
    syncUrl(true);
    return;
  }
  if (target.dataset.evidenceFilter) {
    state.evidenceFilter = target.dataset.evidenceFilter;
    render({ focus: false });
    syncUrl(true);
    return;
  }
  if (target.dataset.reviewFilter) {
    state.reviewFilter = target.dataset.reviewFilter;
    render({ focus: false });
    return;
  }
  if (target.dataset.filterReset) {
    state.filters = { ...DEFAULT_FILTERS };
    state.query = "";
    state.page = 1;
    render({ focus: false });
    syncUrl(true);
    return;
  }
  if (target.dataset.industry) {
    state.view = "companies";
    state.detail = null;
    state.page = 1;
    state.query = "";
    state.filters = { ...DEFAULT_FILTERS, industry: target.dataset.industry };
    syncUrl();
    render();
    return;
  }
  if (target.dataset.page) {
    const nextPage = Number(target.dataset.page);
    if (Number.isFinite(nextPage)) state.page = nextPage;
    render();
    return;
  }
  if (target.dataset.compareToggle) {
    toggleCompare(target.dataset.compareToggle);
    return;
  }
  if (target.dataset.compareRemove) {
    state.selectedCompare = state.selectedCompare.filter((id) => id !== target.dataset.compareRemove);
    render({ focus: false });
    return;
  }
  if (target.dataset.compareGo) {
    if (state.selectedCompare.length < 2) {
      setToast("برای مقایسه، حداقل دو شرکت انتخاب کنید.");
      return;
    }
    navigate("compare");
    return;
  }
  if (target.dataset.clearCompare) {
    state.selectedCompare = [];
    render({ focus: false });
    return;
  }
  if (target.dataset.copyContact) {
    copyText(target.dataset.copyValue || "", "اطلاعات تماس کپی شد.");
    return;
  }
  if (target.dataset.favorite) {
    toggleFavorite(target.dataset.favorite);
    return;
  }
  if (target.dataset.detailTab) {
    state.detailTab = target.dataset.detailTab;
    state.materialTab = "internal";
    if (state.detail) syncUrl(true);
    render({ focus: false });
    return;
  }
  if (target.dataset.materialTab) {
    state.materialTab = target.dataset.materialTab;
    render({ focus: false });
    return;
  }
  if (target.dataset.loadMaterial) {
    loadMaterial(target.dataset.loadMaterial);
    return;
  }
  if (target.dataset.copyMaterial && state.detail) {
    const material = state.detail.materials?.[target.dataset.copyMaterial];
    const cached = state.materialCache?.[`${state.detail.id}:${target.dataset.copyMaterial}`];
    copyText(typeof cached === "string" ? cached : "", "متن سند کپی شد.");
    return;
  }
  if (target.dataset.materialPath) {
    openFileViewer(target.dataset.materialPath);
    return;
  }
  if (target.dataset.copyFileViewer && state.fileViewer) {
    copyText(state.fileViewer.text, "متن سند کپی شد.");
    return;
  }
  if (target.dataset.lightbox !== undefined) {
    state.lightboxIndex = Number(target.dataset.lightbox);
    render({ focus: false });
    return;
  }
  if (target.dataset.reviewScroll) {
    document.querySelector("#review-panel")?.scrollIntoView({ behavior: "smooth", block: "center" });
    document.querySelector("#review-status")?.focus();
    return;
  }
  if (target.dataset.saveReview) {
    saveReview(target.dataset.saveReview);
  }
}

function handleInput(event) {
  const target = event.target;
  if (target.id === "global-search" || target.id === "company-search") {
    state.query = target.value;
    state.page = 1;
    if (target.id === "global-search" && target.value.trim() && state.view !== "companies") {
      state.view = "companies";
      state.detail = null;
      syncUrl(true);
    }
    render({ focus: false });
    return;
  }
  if (target.id === "palette-search") {
    state.paletteQuery = target.value;
    render({ focus: false });
  }
}

function handleChange(event) {
  const target = event.target;
  const key = target.dataset.filter;
  if (!key) return;
  state.filters[key] = target.type === "checkbox" ? target.checked : target.value;
  state.page = 1;
  render({ focus: false });
  syncUrl(true);
}

function handleKeydown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    state.paletteOpen = true;
    state.paletteQuery = "";
    render({ focus: false });
    return;
  }
  if (event.key === "Escape") {
    if (state.paletteOpen || state.fileViewer || state.lightboxIndex !== null) {
      state.paletteOpen = false;
      state.paletteQuery = "";
      state.fileViewer = null;
      state.lightboxIndex = null;
      render({ focus: false });
      return;
    }
  }
  if (event.key === "Enter" && event.target.id === "palette-search") {
    event.preventDefault();
    document.querySelector(".palette-result")?.click();
  }
}

async function init() {
  const pendingCompany = parseUrl();
  try {
    const [bootstrapResponse, reviewResponse] = await Promise.all([fetch("/api/bootstrap"), fetch("/api/review-state")]);
    if (!bootstrapResponse.ok) throw new Error(`bootstrap HTTP ${bootstrapResponse.status}`);
    index = await bootstrapResponse.json();
    if (reviewResponse.ok) reviews = await reviewResponse.json();
    root.addEventListener("click", handleClick);
    root.addEventListener("input", handleInput);
    root.addEventListener("change", handleChange);
    document.addEventListener("keydown", handleKeydown);
    render();
    if (pendingCompany) await openCompany(pendingCompany, { push: false, tab: state.detailTab });
  } catch (error) {
    root.innerHTML = `<div class="fatal-state" dir="rtl"><strong>شاخص داشبورد بارگذاری نشد.</strong><span>${String(error.message || error)}</span><code dir="ltr">npm run data:build</code></div>`;
  }
}

window.addEventListener("popstate", async () => {
  const pendingCompany = parseUrl();
  state.detail = null;
  if (pendingCompany && index) await openCompany(pendingCompany, { push: false, tab: state.detailTab });
  else render();
});

init();
