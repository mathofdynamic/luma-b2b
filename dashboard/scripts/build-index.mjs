import { createReadStream } from "node:fs";
import { promises as fs } from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { fileURLToPath } from "node:url";

const DASHBOARD_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ROOT = path.resolve(DASHBOARD_DIR, "..");
const DATA_DIR = path.join(DASHBOARD_DIR, "data");
const EVIDENCE_DIR = path.join(ROOT, "evidence", "companies");

const SOURCE_FILES = {
  companies: path.join(ROOT, "data", "normalized", "companies.jsonl"),
  evidence: path.join(ROOT, "data", "normalized", "evidence_index.jsonl"),
  sources: path.join(ROOT, "data", "normalized", "sources.jsonl"),
  workflows: path.join(ROOT, "data", "normalized", "workflows.jsonl"),
  decisionMakers: path.join(ROOT, "data", "normalized", "decision_makers.jsonl"),
  evidenceCapture: path.join(ROOT, "data", "normalized", "evidence_capture.jsonl"),
};

const READINESS = {
  "READY FOR OUTREACH": "READY",
  "NEEDS DISCOVERY": "DISCOVERY",
  "NOT READY": "NOT_READY",
};

const READINESS_LABELS = {
  "READY FOR OUTREACH": "آماده ارتباط",
  "NEEDS DISCOVERY": "نیازمند کشف",
  "NOT READY": "فعلاً آماده نیست",
  UNKNOWN: "نامشخص",
};

const TIER_ORDER = { A: 1, B: 2, C: 3, D: 4, Reject: 5, UNKNOWN: 6 };

const asArray = (value) => {
  if (Array.isArray(value)) return value.filter((item) => item !== null && item !== undefined && item !== "");
  if (value === null || value === undefined || value === "") return [];
  return [value];
};

const asText = (value) => (value === null || value === undefined ? "" : String(value).trim());

const nullableText = (value) => asText(value) || null;

const numberOrNull = (value) => {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const unique = (values, limit = Infinity) => {
  const output = [];
  const seen = new Set();
  for (const value of values) {
    const text = asText(value);
    if (!text || seen.has(text)) continue;
    seen.add(text);
    output.push(text);
    if (output.length >= limit) break;
  }
  return output;
};

const shorten = (value, limit = 520) => {
  const text = asText(value).replace(/\s+/g, " ");
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
};

const normalizeSearch = (value) => asText(value)
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

const localUrl = (relativePath) => `/repo/${relativePath.split("/").map(encodeURIComponent).join("/")}`;

const categoryLabel = (row) => nullableText(row.industry_fa) || nullableText(row.industry) || "نامشخص";

const statusKey = (row) => nullableText(row.sales_readiness) || "UNKNOWN";

const tierKey = (row) => nullableText(row.priority_tier) || "UNKNOWN";

const waveKey = (row) => nullableText(row.contact_wave) || "NONE";

const workflowClass = (workflow) => nullableText(
  workflow?.workflow_evidence_classification || workflow?.activation_evidence_classification || workflow?.evidence_classification || workflow?.classification,
) || "UNKNOWN";

const compactEvidence = (item) => ({
  id: nullableText(item.evidence_id),
  type: nullableText(item.evidence_type) || "UNKNOWN",
  claim: shorten(item.claim, 420),
  quote: shorten(item.quote_or_snippet || item.evidence_snippet, 620),
  sourceFamily: nullableText(item.source_family) || "unknown",
  sourceQuality: nullableText(item.source_quality) || "unknown",
  sourceTitle: nullableText(item.source_title) || "بدون عنوان منبع",
  sourceUrl: nullableText(item.source_url),
  confidence: numberOrNull(item.confidence),
  capturedAt: nullableText(item.captured_at || item.retrieved_at),
  signal: nullableText(item.signal),
});

const compactWorkflow = (workflow) => {
  if (!workflow || typeof workflow !== "object") return null;
  return {
    id: nullableText(workflow.workflow_id),
    name: nullableText(workflow.workflow_name),
    nameFa: nullableText(workflow.workflow_name_fa),
    family: nullableText(workflow.workflow_family),
    classification: workflowClass(workflow),
    confidence: nullableText(workflow.confidence),
    confidenceScore: numberOrNull(workflow.confidence_score),
    currentProblem: nullableText(workflow.current_problem),
    currentProblemFa: nullableText(workflow.current_problem_fa),
    hypothesis: nullableText(workflow.current_process_hypothesis_fa || workflow.current_process_hypothesis),
    solution: nullableText(workflow.proposed_luma_solution_fa || workflow.proposed_luma_solution),
    primaryUsers: nullableText(workflow.primary_users_fa || workflow.primary_users),
    businessOwner: nullableText(workflow.likely_business_owner),
    requiredData: unique(asArray(workflow.required_data_fa || workflow.required_data), 12),
    integrations: unique(asArray(workflow.required_integrations_fa || workflow.required_integrations), 12),
    complexity: nullableText(workflow.implementation_complexity),
    risks: unique(asArray(workflow.implementation_risks_fa || workflow.implementation_risks), 8),
    kpis: unique(asArray(workflow.measurable_KPIs_fa || workflow.measurable_KPIs), 8),
    questions: unique(asArray(workflow.discovery_questions), 8),
    sourceUrls: unique(asArray(workflow.source_urls || workflow.sourceUrls), 16),
    supportingEvidence: unique(asArray(workflow.supporting_evidence).map((item) => item?.claim || item), 8),
  };
};

const emptyMapArray = () => new Map();

async function readJsonl(filePath, onRecord) {
  const input = createReadStream(filePath, { encoding: "utf8" });
  const lines = readline.createInterface({ input, crlfDelay: Infinity });
  let count = 0;
  for await (const line of lines) {
    if (!line.trim()) continue;
    try {
      const record = JSON.parse(line);
      await onRecord(record);
      count += 1;
    } catch (error) {
      console.warn(`[data:build] skipped malformed JSONL line in ${filePath}: ${error.message}`);
    }
  }
  return count;
}

async function exists(relativePath) {
  try {
    await fs.access(path.join(ROOT, relativePath));
    return true;
  } catch {
    return false;
  }
}

async function listFiles(relativeDirectory) {
  const absolute = path.join(ROOT, relativeDirectory);
  const output = [];
  async function walk(current, relative) {
    let entries;
    try {
      entries = await fs.readdir(current, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      if (entry.name.startsWith("._") || entry.name === ".DS_Store") continue;
      const currentPath = path.join(current, entry.name);
      const relativePath = path.join(relative, entry.name).split(path.sep).join("/");
      if (entry.isDirectory()) await walk(currentPath, relativePath);
      else if (entry.isFile()) output.push(relativePath);
    }
  }
  await walk(absolute, relativeDirectory);
  return output.sort();
}

async function scanEvidenceAssets(ids) {
  const byCompany = new Map();
  let packageCount = 0;
  let screenshotCount = 0;
  for (const id of ids) {
    const relativeDirectory = `evidence/companies/${id}`;
    const files = await listFiles(relativeDirectory);
    if (!files.length) continue;
    packageCount += 1;
    const screenshots = files.filter((file) => /\.(png|jpe?g|webp)$/i.test(file)).map((file) => ({
      path: file,
      url: localUrl(file),
      sourceUrl: null,
      sourceTitle: "ذخیره تصویری شواهد",
      capturedAt: null,
      reason: "تصویر ذخیره‌شده برای بررسی داخلی؛ جزئیات capture در metadata عمومی موجود نیست.",
    }));
    screenshotCount += screenshots.length;
    byCompany.set(id, {
      files: files.map((file) => ({ path: file, url: localUrl(file), kind: path.extname(file).toLowerCase() === ".md" ? "markdown" : "text" })),
      screenshots,
      notesPath: files.includes(`${relativeDirectory}/notes.md`) ? `${relativeDirectory}/notes.md` : null,
      sourcesPath: files.includes(`${relativeDirectory}/sources.json`) ? `${relativeDirectory}/sources.json` : null,
      pages: files.filter((file) => file.includes("/pages/")).map((file) => ({ path: file, url: localUrl(file) })),
    });
  }
  return { byCompany, packageCount, screenshotCount };
}

async function scanDemos(companySummaries) {
  const demoRoot = path.join(ROOT, "demos");
  let entries = [];
  try {
    entries = await fs.readdir(demoRoot, { withFileTypes: true });
  } catch {
    return { demos: [], assignments: new Map() };
  }
  const demos = [];
  const assignments = new Map();
  const summaryValues = [...companySummaries.values()];
  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith(".")) continue;
    const slug = entry.name;
    const appIndex = `demos/${slug}/app/index.html`;
    if (!(await exists(appIndex))) continue;
    const files = await listFiles(`demos/${slug}`);
    let manifest = null;
    try {
      manifest = JSON.parse(await fs.readFile(path.join(ROOT, `demos/${slug}/manifest.json`), "utf8"));
    } catch {
      // A manifest is optional; the current Sabah demo is matched by its public domain.
    }
    const demo = {
      slug,
      label: slug === "sabahi" ? "دموی صباحی" : slug,
      rootPath: `demos/${slug}`,
      route: `/demo/${encodeURIComponent(slug)}/`,
      files: files.map((file) => ({ path: file, url: localUrl(file) })),
      screenshots: files.filter((file) => /\/screenshots\/[^/]+\.(png|jpe?g|webp)$/i.test(file)).map((file) => ({ path: file, url: localUrl(file) })),
      readmePath: files.includes(`demos/${slug}/README.md`) ? `demos/${slug}/README.md` : null,
      scriptPath: files.includes(`demos/${slug}/DEMO_SCRIPT_FA.md`) ? `demos/${slug}/DEMO_SCRIPT_FA.md` : null,
      questionsPath: files.includes(`demos/${slug}/DISCOVERY_QUESTIONS_FA.md`) ? `demos/${slug}/DISCOVERY_QUESTIONS_FA.md` : null,
      manifestCompanyId: nullableText(manifest?.company_id),
    };
    demos.push(demo);
    let companyId = demo.manifestCompanyId;
    if (!companyId) {
      const normalizedSlug = normalizeSearch(slug).replace(/[^a-z0-9]+/g, "");
      const match = summaryValues.find((company) => {
        const domain = normalizeSearch(company.contacts?.domain || company.domain || "").split(".")[0].replace(/[^a-z0-9]+/g, "");
        const english = normalizeSearch(company.nameEn || "").replace(/[^a-z0-9]+/g, "");
        const aliases = company.aliases.map((alias) => normalizeSearch(alias).replace(/[^a-z0-9]+/g, ""));
        return [domain, english, ...aliases].some((token) => token && (token === normalizedSlug || token.includes(normalizedSlug) || normalizedSlug.includes(token)));
      });
      companyId = match?.id || null;
    }
    if (companyId) assignments.set(companyId, demo);
  }
  return { demos, assignments };
}

function compactSourceGroups(groupMap, fallbackFamilies = []) {
  const websiteFamily = fallbackFamilies.find((family) => family.startsWith("company_website:"));
  const canonicalFamily = (family) => {
    if (family === "company_site" && websiteFamily) return websiteFamily;
    if (family === "directory" && fallbackFamilies.includes("book_e_avval")) return "book_e_avval";
    return family;
  };
  const merged = new Map();
  for (const group of groupMap.values()) {
    const family = canonicalFamily(group.family);
    const existing = merged.get(family) || { family, sourceType: group.sourceType, quality: group.quality, count: 0, urls: [], titles: [], claims: [] };
    existing.count += group.count;
    existing.urls = unique([...existing.urls, ...group.urls], 18);
    existing.titles = unique([...existing.titles, ...group.titles], 8);
    existing.claims = unique([...existing.claims, ...group.claims], 6);
    if (!existing.sourceType) existing.sourceType = group.sourceType;
    if (!existing.quality || existing.quality === "unknown") existing.quality = group.quality;
    merged.set(family, existing);
  }
  const groups = [...merged.values()];
  const known = new Set(groups.map((group) => group.family));
  for (const family of fallbackFamilies) {
    if (known.has(family)) continue;
    groups.push({ family, sourceType: null, quality: "canonical declaration; URL not indexed", count: 0, urls: [], titles: [], claims: [] });
  }
  return groups.sort((left, right) => right.count - left.count || left.family.localeCompare(right.family));
}

function makeDecisionMakers(row) {
  const decisions = [
    {
      key: "operational",
      label: "مالک عملیاتی",
      role: nullableText(row.primary_contact_role),
      name: nullableText(row.primary_contact_name),
      sourceUrl: nullableText(row.primary_contact_source_url),
      confidence: numberOrNull(row.primary_contact_confidence),
    },
    {
      key: "economic",
      label: "خریدار اقتصادی",
      role: nullableText(row.economic_buyer_role),
      name: nullableText(row.economic_buyer_name),
      sourceUrl: nullableText(row.economic_buyer_source_url),
      confidence: numberOrNull(row.economic_buyer_confidence),
    },
    {
      key: "technical",
      label: "دروازه‌بان فنی",
      role: nullableText(row.technical_gatekeeper_role),
      name: nullableText(row.technical_gatekeeper_name),
      sourceUrl: nullableText(row.technical_gatekeeper_source_url),
      confidence: numberOrNull(row.technical_gatekeeper_confidence),
    },
  ];
  return decisions.map((item) => ({
    ...item,
    status: item.name ? "VERIFIED_NAME" : item.role ? "ROLE_ONLY" : "UNKNOWN",
  }));
}

function materialPaths(id) {
  const candidates = {
    internal: `sales/internal/${id}.md`,
    proposalClient: `sales/client/${id}.md`,
    proposal: `proposals/${id}.md`,
    outreach: `sales/outreach/${id}.md`,
    dossier: `reports/dossiers/${id}.md`,
    visual: `sales/visual/${id}/README.md`,
  };
  return Object.fromEntries(Object.entries(candidates).map(([key, relativePath]) => [key, { path: relativePath, url: localUrl(relativePath), available: false }]));
}

async function resolveMaterials(materials) {
  const resolved = {};
  for (const [key, value] of Object.entries(materials)) {
    resolved[key] = { ...value, available: await exists(value.path) };
  }
  return resolved;
}

function makeSummary(row, workflow, sourceFamilies, assetInfo, materials, demo) {
  const id = asText(row.company_id);
  const phones = unique(asArray(row.phone_public));
  const emails = unique(asArray(row.email_public));
  const aliases = unique(asArray(row.aliases));
  const decisionMakers = makeDecisionMakers(row);
  const status = statusKey(row);
  const tier = tierKey(row);
  const evidence = asArray(row.evidence);
  const sourceFamilyList = unique(asArray(row.independent_source_families));
  const evidenceClassCounts = {};
  for (const item of evidence) {
    const type = nullableText(item?.evidence_type) || "UNKNOWN";
    evidenceClassCounts[type] = (evidenceClassCounts[type] || 0) + 1;
  }
  const detailWorkflow = workflow || compactWorkflow(asArray(row.workflow_opportunities)[0]) || null;
  const website = nullableText(row.website);
  const domain = nullableText(row.domain) || (() => {
    try { return new URL(website).hostname.replace(/^www\./, ""); } catch { return null; }
  })();
  const quality = {
    evidenceStrength: numberOrNull(row.commercial_evidence_strength),
    scoreConfidence: numberOrNull(row.score_confidence),
    independentSourceCount: numberOrNull(row.independent_source_count) ?? sourceFamilyList.length,
    independentSourceFamilies: sourceFamilyList,
    evidenceCount: evidence.length,
    evidenceClassCounts,
    screenshots: assetInfo?.screenshots?.length || 0,
    hasThreePlusSources: (numberOrNull(row.independent_source_count) ?? sourceFamilyList.length) >= 3,
    directoryOnly: sourceFamilyList.length === 1 && sourceFamilyList[0].toLowerCase().includes("book_e_avval"),
    workflowClass: workflowClass(detailWorkflow),
    unknownFieldCount: [website, row.description_observed, row.company_type, row.company_strength_score, row.operational_complexity_score, row.digital_maturity_score, row.internal_tech_capability_score, row.decision_maker_name_public || row.economic_buyer_name, phones.length || null, emails.length || null].filter((value) => value === null || value === undefined || value === "" || value === "UNKNOWN").length,
  };
  const scores = {
    opportunity: numberOrNull(row.luma_opportunity_score),
    adjusted: numberOrNull(row.confidence_adjusted_score),
    firstContact: numberOrNull(row.first_contact_score),
    evidenceStrength: quality.evidenceStrength,
    scoreConfidence: quality.scoreConfidence,
    companyStrength: numberOrNull(row.company_strength_score),
    operationalComplexity: numberOrNull(row.operational_complexity_score),
    workflowDensity: numberOrNull(row.workflow_density_score),
    dataReadiness: numberOrNull(row.data_readiness_score),
    digitalMaturity: numberOrNull(row.digital_maturity_score),
    digitalMaturityFit: numberOrNull(row.digital_maturity_fit_score),
    internalTech: numberOrNull(row.internal_tech_capability_score),
    outsourcingFit: numberOrNull(row.outsourcing_fit_score),
    aiRoi: numberOrNull(row.ai_roi_score),
    implementation: numberOrNull(row.implementation_score),
    salesAccess: numberOrNull(row.sales_access_score),
    salesCycle: numberOrNull(row.sales_cycle_ease_score),
    regulatory: numberOrNull(row.regulatory_score),
  };
  const contacts = {
    phones,
    emails,
    website,
    domain,
    linkedin: nullableText(row.linkedin_company_page),
    whatsapp: unique(asArray(row.activation_whatsapp))[0] || null,
    preferredChannel: nullableText(row.preferred_channel),
  };
  const nameFa = nullableText(row.company_name_fa) || "شرکت بدون نام";
  const searchText = normalizeSearch([
    nameFa,
    row.brand_name_fa,
    row.company_name_en,
    ...aliases,
    row.description_observed,
    row.industry,
    row.industry_fa,
    row.sub_industry,
    row.company_type,
    website,
    domain,
    detailWorkflow?.name,
    detailWorkflow?.nameFa,
    detailWorkflow?.solution,
    ...decisionMakers.flatMap((item) => [item.name, item.role]),
  ].filter(Boolean).join(" "));
  return {
    id,
    nameFa,
    brandFa: nullableText(row.brand_name_fa),
    nameEn: nullableText(row.company_name_en),
    aliases,
    industry: nullableText(row.industry) || "other",
    industryLabel: categoryLabel(row),
    subIndustry: nullableText(row.sub_industry),
    companyType: nullableText(row.company_type) || "unknown",
    businessModel: unique(asArray(row.business_model)),
    status,
    statusLabel: READINESS_LABELS[status] || READINESS_LABELS.UNKNOWN,
    tier,
    wave: waveKey(row),
    waveRank: numberOrNull(row.wave_rank),
    dossierRank: numberOrNull(row.dossier_rank),
    researchStatus: nullableText(row.research_status) || "UNKNOWN",
    activeStatus: nullableText(row.active_status_evidence) || "UNKNOWN",
    location: {
      city: nullableText(row.city),
      province: nullableText(row.province),
      area: nullableText(row.tehran_area),
      industrialZone: nullableText(row.industrial_zone),
      hq: nullableText(row.hq_address),
    },
    websiteStatus: nullableText(row.website_status) || "UNKNOWN",
    scores,
    quality,
    workflow: detailWorkflow,
    contacts,
    decisions: decisionMakers,
    materials,
    assets: assetInfo || { files: [], screenshots: [], notesPath: null, sourcesPath: null, pages: [] },
    demo: demo || null,
    searchText,
  };
}

function makeDetailBase(row) {
  return {
    description: nullableText(row.description_observed),
    productsServices: unique(asArray(row.products_services), 30),
    customerTypes: unique(asArray(row.business_model), 12),
    visibleCustomers: unique(asArray(row.visible_customers), 16),
    visibleProjects: unique(asArray(row.visible_projects), 16),
    certifications: unique(asArray(row.certifications), 16),
    associations: unique(asArray(row.association_memberships), 16),
    socialProfiles: unique(asArray(row.social_profiles), 16),
    operationalAddresses: unique(asArray(row.operational_addresses), 16),
    scale: {
      foundedYear: numberOrNull(row.founded_year),
      companyAgeYears: numberOrNull(row.company_age_years),
      employeeMin: numberOrNull(row.employee_estimate_min),
      employeeMax: numberOrNull(row.employee_estimate_max),
      branches: numberOrNull(row.branches_count),
      factories: numberOrNull(row.factories_count),
      warehouses: numberOrNull(row.warehouses_count),
      geographicReach: nullableText(row.geographic_reach),
    },
    classification: {
      confidence: numberOrNull(row.industry_classification_confidence),
      reason: nullableText(row.classification_correction_reason),
      originalIndustry: nullableText(row.original_industry),
      reclassification: nullableText(row.industry_reclassification),
    },
    quality: {
      qualificationReason: nullableText(row.qualification_reason),
      evidenceReason: nullableText(row.commercial_evidence_strength_reason),
      strongestObserved: unique(asArray(row.strongest_observed_evidence), 10),
      riskReasons: unique(asArray(row.risk_reasons), 10),
      hardDisqualifier: nullableText(row.hard_disqualifier),
      websiteIssue: nullableText(row.website_quality_issue),
      triggerSignals: unique(asArray(row.trigger_signals), 12),
    },
    technology: {
      internalCapabilityStatus: nullableText(row.internal_tech_capability_evidence_status) || "UNKNOWN_INTERNAL_TECH",
      internalCapabilityInterpretation: nullableText(row.internal_tech_capability_interpretation),
      softwareSignals: unique(asArray(row.existing_software_signals), 16),
      jobFamilies: unique(asArray(row.job_families), 16),
      portalFeatures: unique(asArray(row.portal_features), 16),
      digitalStatus: nullableText(row.digital_maturity_evidence_status) || "UNKNOWN_DIGITAL_MATURITY",
      digitalInterpretation: nullableText(row.digital_maturity_interpretation),
    },
    history: {
      originalTier: nullableText(row.original_priority_tier),
      originalIndustry: nullableText(row.original_industry),
      originalOpportunity: numberOrNull(row.original_luma_opportunity_score),
      originalConfidence: numberOrNull(row.original_score_confidence),
      originalWorkflowDensity: numberOrNull(row.original_workflow_density_score),
      originalDigitalMaturity: numberOrNull(row.original_digital_maturity_score),
      scoreDate: nullableText(row.score_date),
      scoreVersion: nullableText(row.score_version),
      auditVersion: nullableText(row.commercial_audit_version),
      lastResearchDate: nullableText(row.last_research_date),
      lastActivationDate: nullableText(row.activation_research_date),
    },
    publicSurface: {
      entryPoints: unique(asArray(row.public_sales_surface?.entry_points), 12),
      intakeChannels: unique(asArray(row.public_sales_surface?.intake_channels), 12),
      observableSteps: unique(asArray(row.public_sales_surface?.observable_steps_fa || row.public_sales_surface?.observable_steps), 12),
    },
  };
}

async function main() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  const rowsById = new Map();
  const sourceFamilyMap = emptyMapArray();
  const evidenceMap = emptyMapArray();
  const workflowMap = emptyMapArray();
  const decisionMap = emptyMapArray();
  const captureMap = emptyMapArray();
  let canonicalRows = 0;

  canonicalRows = await readJsonl(SOURCE_FILES.companies, async (row) => {
    if (!row.company_id) return;
    const id = asText(row.company_id);
    rowsById.set(id, {
      row,
      detailBase: makeDetailBase(row),
    });
  });

  await readJsonl(SOURCE_FILES.evidence, async (item) => {
    const id = asText(item.company_id);
    if (!id || !rowsById.has(id)) return;
    if (!evidenceMap.has(id)) evidenceMap.set(id, []);
    evidenceMap.get(id).push(compactEvidence(item));
  });

  await readJsonl(SOURCE_FILES.sources, async (item) => {
    const id = asText(item.company_id);
    if (!id || !rowsById.has(id)) return;
    const family = nullableText(item.source_family) || nullableText(item.source_type) || "unknown";
    if (!sourceFamilyMap.has(id)) sourceFamilyMap.set(id, new Map());
    const byFamily = sourceFamilyMap.get(id);
    if (!byFamily.has(family)) byFamily.set(family, { family, sourceType: nullableText(item.source_type), quality: nullableText(item.source_quality) || "unknown", count: 0, urls: [], titles: [], claims: [] });
    const group = byFamily.get(family);
    group.count += 1;
    group.urls = unique([...group.urls, item.source_url], 18);
    group.titles = unique([...group.titles, item.source_title], 8);
    group.claims = unique([...group.claims, item.claim || item.evidence_snippet], 6).map((claim) => shorten(claim, 260));
  });

  await readJsonl(SOURCE_FILES.workflows, async (item) => {
    const id = asText(item.company_id);
    if (!id || !rowsById.has(id)) return;
    if (!workflowMap.has(id)) workflowMap.set(id, []);
    const compact = compactWorkflow(item);
    if (compact) workflowMap.get(id).push(compact);
  });

  await readJsonl(SOURCE_FILES.decisionMakers, async (item) => {
    const id = asText(item.company_id);
    if (!id || !rowsById.has(id)) return;
    decisionMap.set(id, {
      role: nullableText(item.decision_maker_role),
      name: nullableText(item.decision_maker_name_public),
      sourceUrl: nullableText(item.source_url),
      confidence: numberOrNull(item.confidence),
    });
  });

  await readJsonl(SOURCE_FILES.evidenceCapture, async (item) => {
    const id = asText(item.company_id);
    if (!id || !rowsById.has(id)) return;
    captureMap.set(id, {
      screenshots: numberOrNull(item.screenshots) || 0,
      headless: item.headless === true,
      errors: unique(asArray(item.errors), 12),
    });
  });

  const assets = await scanEvidenceAssets(rowsById.keys());
  const summaries = new Map();
  for (const [id, record] of rowsById) {
    const row = record.row;
    const sources = compactSourceGroups(sourceFamilyMap.get(id) || new Map(), asArray(row.independent_source_families));
    const workflows = workflowMap.get(id) || [];
    const workflow = compactWorkflow(row.activation_primary_opportunity) || workflows[0] || compactWorkflow(asArray(row.workflow_opportunities)[0]);
    const materials = await resolveMaterials(materialPaths(id));
    const summary = makeSummary(row, workflow, sources, assets.byCompany.get(id), materials, null);
    summary.capture = captureMap.get(id) || null;
    summary.decisionMaker = decisionMap.get(id) || null;
    summaries.set(id, summary);
  }

  const demos = await scanDemos(summaries);
  for (const [id, demo] of demos.assignments) {
    const summary = summaries.get(id);
    if (summary) summary.demo = demo;
  }

  const companyList = [...summaries.values()].map((summary) => ({
    ...summary,
    // Keep the explorer record compact; full evidence, profile and materials are lazy-loaded from company_details.jsonl.
    assets: { screenshots: summary.assets.screenshots.length, files: summary.assets.files.length },
  })).sort((left, right) => (TIER_ORDER[left.tier] || 9) - (TIER_ORDER[right.tier] || 9) || (right.scores.adjusted ?? -1) - (left.scores.adjusted ?? -1) || left.nameFa.localeCompare(right.nameFa, "fa"));

  const details = [];
  for (const [id, record] of rowsById) {
    const summary = summaries.get(id);
    const row = record.row;
    const evidence = (evidenceMap.get(id) || []).sort((left, right) => (right.confidence ?? -1) - (left.confidence ?? -1));
    const sourceFamilies = compactSourceGroups(sourceFamilyMap.get(id) || new Map(), asArray(row.independent_source_families));
    const workflows = workflowMap.get(id) || [];
    const primaryWorkflow = summary.workflow || workflows[0] || null;
    details.push({
      ...summary,
      profile: record.detailBase,
      evidence,
      sourceFamilies,
      workflows: primaryWorkflow ? [primaryWorkflow, ...workflows.filter((workflow) => workflow.id !== primaryWorkflow.id)] : workflows,
      decisionMakers: makeDecisionMakers(row),
      capture: captureMap.get(id) || null,
      originalData: {
        activationStatus: nullableText(row.activation_status),
        activationVersion: nullableText(row.activation_version),
        activationEvidenceSourceCount: numberOrNull(row.activation_evidence_source_count),
        activationExternalSourceFamilies: unique(asArray(row.activation_external_source_families), 12),
        activationErrors: unique(asArray(row.activation_errors), 12),
        dossierRank: numberOrNull(row.dossier_rank),
      },
    });
  }

  const count = (predicate) => companyList.reduce((total, item) => total + (predicate(item) ? 1 : 0), 0);
  const counts = {
    total: companyList.length,
    enriched: count((item) => item.researchStatus === "MEANINGFULLY_ENRICHED"),
    tierA: count((item) => item.tier === "A"),
    tierB: count((item) => item.tier === "B"),
    ready: count((item) => item.status === "READY FOR OUTREACH"),
    needsDiscovery: count((item) => item.status === "NEEDS DISCOVERY"),
    notReady: count((item) => item.status === "NOT READY"),
    wave1: count((item) => item.wave === "WAVE 1"),
    wave2: count((item) => item.wave === "WAVE 2"),
    wave3: count((item) => item.wave === "WAVE 3"),
    proposals: count((item) => item.materials.proposal.available || item.materials.proposalClient.available),
    outreachFiles: count((item) => item.materials.outreach.available),
    dossiers: count((item) => item.materials.dossier.available),
    verifiedDecisionMakers: count((item) => item.decisions.some((decision) => decision.status === "VERIFIED_NAME")),
    threePlusSources: count((item) => item.quality.hasThreePlusSources),
    directoryOnly: count((item) => item.quality.directoryOnly),
    workflowSupported: count((item) => item.quality.workflowClass === "EVIDENCE_SUPPORTED"),
    workflowHypothesis: count((item) => ["STRONG_HYPOTHESIS", "WEAK_HYPOTHESIS"].includes(item.quality.workflowClass)),
    screenshotPackages: assets.packageCount,
    evidenceScreenshots: assets.screenshotCount,
    demos: demos.demos.length,
    demoScreenshots: demos.demos.reduce((total, demo) => total + demo.screenshots.length, 0),
  };

  const facet = (key, labelKey = key) => {
    const map = new Map();
    for (const item of companyList) {
      const value = key === "quality.workflowClass" ? item.quality.workflowClass : (item[key] || "UNKNOWN");
      const label = item[labelKey] || value;
      if (!map.has(value)) map.set(value, { value, label, count: 0 });
      map.get(value).count += 1;
    }
    return [...map.values()].sort((left, right) => right.count - left.count || String(left.label).localeCompare(String(right.label), "fa"));
  };

  const index = {
    schemaVersion: "0.1.0",
    generatedAt: new Date().toISOString(),
    sourceOfTruth: "data/normalized/companies.jsonl",
    sourceFiles: Object.fromEntries(Object.entries(SOURCE_FILES).map(([key, value]) => [key, path.relative(ROOT, value).split(path.sep).join("/")])),
    canonicalRows,
    counts,
    facets: {
      industries: facet("industry", "industryLabel"),
      companyTypes: facet("companyType"),
      statuses: facet("status"),
      tiers: facet("tier"),
      waves: facet("wave"),
      workflowClasses: facet("quality.workflowClass"),
    },
    demos: demos.demos,
    companies: companyList,
  };

  await fs.writeFile(path.join(DATA_DIR, "index.json"), `${JSON.stringify(index)}\n`, "utf8");
  const detailLines = details.map((detail) => JSON.stringify(detail)).join("\n");
  await fs.writeFile(path.join(DATA_DIR, "company_details.jsonl"), `${detailLines}\n`, "utf8");
  await fs.writeFile(path.join(DATA_DIR, "build-meta.json"), `${JSON.stringify({ generatedAt: index.generatedAt, counts, sourceFiles: index.sourceFiles }, null, 2)}\n`, "utf8");

  console.log(JSON.stringify({
    generatedAt: index.generatedAt,
    sourceOfTruth: index.sourceOfTruth,
    companiesIndexed: counts.total,
    readyCompanies: counts.ready,
    wave1: counts.wave1,
    evidencePackages: counts.screenshotPackages,
    evidenceScreenshots: counts.evidenceScreenshots,
    proposals: counts.proposals,
    outreachFiles: counts.outreachFiles,
    demos: counts.demos,
    output: ["dashboard/data/index.json", "dashboard/data/company_details.jsonl", "dashboard/data/build-meta.json"],
  }, null, 2));
}

main().catch((error) => {
  console.error(`[data:build] fatal: ${error.stack || error.message}`);
  process.exitCode = 1;
});
