import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const dataDir = path.join(root, "data");
const normalizedDir = path.join(dataDir, "normalized");
const evidenceRoot = path.join(root, "evidence", "companies");

async function readJsonl(filePath) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    return text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
  } catch {
    return [];
  }
}

function cell(value) {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.some((item) => item && typeof item === "object") ? JSON.stringify(value, null, 0) : value.join(" | ");
  if (typeof value === "object") return JSON.stringify(value, null, 0);
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) return `'${value}`;
  return value;
}

function columnName(index) {
  let n = index + 1;
  let result = "";
  while (n > 0) {
    const remainder = (n - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    n = Math.floor((n - 1) / 26);
  }
  return result;
}

function rangeAddress(rowCount, colCount) {
  return `A1:${columnName(colCount - 1)}${rowCount}`;
}

async function screenshotCount(companyId) {
  try {
    const names = await fs.readdir(path.join(evidenceRoot, companyId, "screenshots"));
    return names.filter((name) => name.endsWith(".png") && !name.startsWith("._")).length;
  } catch {
    return 0;
  }
}

const companyColumns = [
  "company_id", "company_name_fa", "brand_name_fa", "company_name_en", "aliases", "industry", "industry_fa", "sub_industry", "business_model",
  "description_observed", "hq_address", "city", "province", "tehran_area", "industrial_zone", "operational_addresses", "latitude", "longitude",
  "phone_public", "email_public", "website", "domain", "website_status", "linkedin_company_page", "social_profiles", "research_status", "last_research_date",
  "raw_record_count", "source_urls", "discovery_reasons", "evidence_count", "screenshot_count", "hard_disqualifier",
  "company_strength_score", "operational_complexity_score", "workflow_density_score", "ai_roi_score", "data_readiness_score", "digital_maturity_score", "digital_maturity_fit_score",
  "internal_tech_capability_score", "outsourcing_fit_score", "sales_access_score", "expected_project_value_score", "implementation_score", "sales_cycle_ease_score", "regulatory_score",
  "trigger_bonus", "risk_penalty", "luma_opportunity_score", "priority_tier", "score_confidence", "qualification_reason", "strongest_workflow", "decision_maker_role", "decision_maker_name_public", "proposal_path",
];

const formatWidths = (headers) => headers.map((header) => {
  if (/description|reason|evidence|source|address|workflow|solution|question|snippet|url|email|phone/i.test(header)) return 34;
  if (/name|industry|status|tier|role|model|city|province|zone/i.test(header)) return 23;
  return 16;
});

function styleSheet(sheet, headers, rowCount, { tableName, widths = null, wrapBody = false, bodyRowHeight = 21 } = {}) {
  sheet.showGridLines = false;
  const header = sheet.getRangeByIndexes(0, 0, 1, headers.length);
  header.format = {
    fill: "#0B1F33",
    font: { bold: true, color: "#FFFFFF", size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
  header.format.rowHeight = 34;
  if (rowCount > 1) {
    const body = sheet.getRangeByIndexes(1, 0, rowCount - 1, headers.length);
    body.format.font = { name: "Arial", size: 10, color: "#1F2937" };
    body.format.verticalAlignment = "center";
    body.format.wrapText = wrapBody;
    body.format.borders = { insideHorizontal: { style: "thin", color: "#E5E7EB" } };
    body.format.rowHeight = bodyRowHeight;
  }
  const resolved = widths || formatWidths(headers);
  resolved.forEach((width, index) => {
    sheet.getRangeByIndexes(0, index, Math.max(1, rowCount), 1).format.columnWidth = width;
  });
  sheet.freezePanes.freezeRows(1);
  if (tableName && rowCount >= 2) {
    const table = sheet.tables.add(rangeAddress(rowCount, headers.length), true, tableName);
    table.showFilterButton = true;
  }
}

function addSheet(workbook, name, headers, rows, tableName, widths = null) {
  const sheet = workbook.worksheets.add(name);
  const matrix = [headers, ...rows.map((row) => headers.map((header) => cell(row[header])))];
  const range = sheet.getRangeByIndexes(0, 0, matrix.length, headers.length);
  range.values = matrix;
  const wrapBody = ["Workflow Opportunities", "Sources", "Evidence Index"].includes(name);
  const bodyRowHeight = name === "Workflow Opportunities" ? 54 : wrapBody ? 36 : 21;
  styleSheet(sheet, headers, matrix.length, { tableName, widths, wrapBody, bodyRowHeight });
  if (name === "Scoring Explanation" && matrix.length > 1) {
    const body = sheet.getRangeByIndexes(1, 0, matrix.length - 1, headers.length);
    body.format.wrapText = true;
    body.format.rowHeight = 42;
  }
  return sheet;
}

const companies = await readJsonl(path.join(normalizedDir, "companies.jsonl"));
const workflows = await readJsonl(path.join(normalizedDir, "workflows.jsonl"));
const decisions = await readJsonl(path.join(normalizedDir, "decision_makers.jsonl"));
const sources = await readJsonl(path.join(normalizedDir, "sources_export.jsonl"));
const evidence = await readJsonl(path.join(normalizedDir, "evidence_index.jsonl"));
const proposals = await readJsonl(path.join(normalizedDir, "proposals.jsonl"));
const proposalIds = new Set(proposals.map((item) => item.company_id));
const screenshotCounts = new Map();
for (const company of companies) screenshotCounts.set(company.company_id, await screenshotCount(company.company_id));

const companyRows = companies
  .slice()
  .sort((a, b) => (b.luma_opportunity_score || 0) - (a.luma_opportunity_score || 0))
  .map((company) => {
    const workflow = (company.workflow_opportunities || [])[0] || {};
    const row = { ...company };
    row.evidence_count = (company.evidence || []).length;
    row.screenshot_count = screenshotCounts.get(company.company_id) || 0;
    row.strongest_workflow = workflow.workflow_name || "";
    row.proposal_path = proposalIds.has(company.company_id) ? `proposals/${company.company_id}.md` : "";
    return row;
  });

const tierA = companyRows.filter((row) => row.priority_tier === "A");
const tierB = companyRows.filter((row) => row.priority_tier === "B");
const rejected = companyRows.filter((row) => row.priority_tier === "Reject");
const nameById = new Map(companyRows.map((company) => [company.company_id, company.company_name_fa || ""]));

const industryMap = new Map();
for (const company of companyRows) {
  const key = company.industry || "other";
  const item = industryMap.get(key) || { industry: key, industry_fa: company.industry_fa || "", canonical_companies: 0, enriched: 0, tier_a: 0, tier_b: 0, tier_c: 0, tier_d: 0, rejected: 0, total_score: 0, top_score: 0 };
  item.canonical_companies += 1;
  item.enriched += company.research_status === "MEANINGFULLY_ENRICHED" ? 1 : 0;
  item[({ A: "tier_a", B: "tier_b", C: "tier_c", D: "tier_d", Reject: "rejected" }[company.priority_tier]) || "rejected"] += 1;
  item.total_score += company.luma_opportunity_score || 0;
  item.top_score = Math.max(item.top_score, company.luma_opportunity_score || 0);
  industryMap.set(key, item);
}
const industries = [...industryMap.values()].map((item) => ({ ...item, median_or_mean_score: item.canonical_companies ? Math.round(item.total_score / item.canonical_companies) : 0 }));

const scoringExplanation = [
  { topic: "Score version", value: "2026.09.evidence-first-v1" },
  { topic: "Formula", value: "Raw = 12C + 12O + 10R + 16V + 10D + 12G(d) + 8A + 6E + 5P + 4F + 3S + 2L; final = clamp(raw + trigger bonus - risk penalty)" },
  { topic: "Digital maturity fit", value: "G(d) = exp(-((d-55)/24)^2); moderate/fragmented maturity is favored and both thin and highly technical organizations are lower fit." },
  { topic: "Tier thresholds", value: "A >= 80; B 70-79; C 60-69; D 45-59; Reject <45 or hard disqualifier." },
  { topic: "Evidence rule", value: "Observations are source-linked. Workflow and current-process statements are hypotheses unless directly observed." },
  { topic: "Industrial index rule", value: "Industrial-estate index membership/activity alone cannot establish purchasing power or active status; thin index-only rows are capped below B/A." },
  { topic: "Public-contact rule", value: "Corporate landlines and public corporate emails only; no private mobile numbers or non-public personal emails." },
  { topic: "Proposal gate", value: "Tier A, or strong Tier B (score >=73, website HTTP 200 or >=4 evidence objects), meaningful enrichment and no hard disqualifier." },
  { topic: "Source timestamps", value: "Research timestamps and run logs are under logs/; UNKNOWN is preserved when public evidence is missing." },
];

const workbook = Workbook.create();
addSheet(workbook, "All Companies", companyColumns, companyRows, "AllCompanies", companyColumns.map((header) => header === "company_name_fa" ? 28 : /description|reason|evidence|source_urls|discovery_reasons/.test(header) ? 36 : /url|website|email|phone/.test(header) ? 30 : 17));
addSheet(workbook, "Tier A", companyColumns, tierA, "TierA");
addSheet(workbook, "Tier B", companyColumns, tierB, "TierB");
addSheet(workbook, "Industries", ["industry", "industry_fa", "canonical_companies", "enriched", "tier_a", "tier_b", "tier_c", "tier_d", "rejected", "median_or_mean_score", "top_score"], industries, "Industries");
addSheet(workbook, "Workflow Opportunities", ["workflow_id", "company_id", "department", "workflow_name", "current_process_hypothesis", "supporting_evidence", "current_problem", "proposed_luma_solution", "primary_users", "likely_business_owner", "required_data", "required_integrations", "implementation_complexity", "implementation_risks", "measurable_KPIs", "confidence", "confidence_score", "discovery_questions"], workflows, "WorkflowOpportunities");
addSheet(workbook, "Decision Makers", ["company_id", "company_name_fa", "decision_maker_role", "decision_maker_name_public", "source_url", "confidence"], decisions.map((row) => ({ ...row, company_name_fa: nameById.get(row.company_id) || "" })), "DecisionMakers");
addSheet(workbook, "Sources", ["company_id", "company_name_fa", "source_url", "source_title", "source_type", "source_quality", "discovery_reason", "evidence_class", "evidence_snippet", "discovered_at", "captured_at", "claim", "confidence", "quote_or_snippet"], sources.map((row) => ({ ...row, company_name_fa: nameById.get(row.company_id) || "" })), "Sources");
addSheet(workbook, "Evidence Index", ["company_id", "company_name_fa", "evidence_id", "claim", "evidence_type", "source_url", "source_title", "captured_at", "confidence", "source_quality", "quote_or_snippet"], evidence.map((row) => ({ ...row, company_name_fa: nameById.get(row.company_id) || "" })), "EvidenceIndex");
addSheet(workbook, "Rejected", companyColumns, rejected, "Rejected");
addSheet(workbook, "Scoring Explanation", ["topic", "value"], scoringExplanation, "ScoringExplanation", [28, 100]);

const outputDir = path.join(root, "data");
await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outputDir, "master_companies.xlsx"));
const previewDir = path.join("/tmp", "luma-b2b-workbook-previews");
await fs.mkdir(previewDir, { recursive: true });
const previewRanges = {
  "All Companies": "A1:L20", "Tier A": "A1:L20", "Tier B": "A1:L20", "Industries": "A1:K20",
  "Workflow Opportunities": "A1:H20", "Decision Makers": "A1:F20", "Sources": "A1:J20",
  "Evidence Index": "A1:K20", "Rejected": "A1:L20", "Scoring Explanation": "A1:B20",
};
for (const [sheet, range] of Object.entries(previewRanges)) {
  const blob = await workbook.render({ sheetName: sheet, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheet.replace(/[^A-Za-z0-9]+/g, "_")}.png`), new Uint8Array(await blob.arrayBuffer()));
}
console.log(JSON.stringify({ workbook: path.join(outputDir, "master_companies.xlsx"), companies: companyRows.length, tier_a: tierA.length, tier_b: tierB.length, rejected: rejected.length, sheets: 10, previews: previewDir }, null, 2));
