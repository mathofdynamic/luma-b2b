import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();

async function readJsonl(filePath) {
  const text = await fs.readFile(filePath, "utf8");
  return text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function value(input) {
  if (input === null || input === undefined) return "";
  if (Array.isArray(input)) return input.map((item) => typeof item === "object" ? JSON.stringify(item) : String(item)).join("\n");
  if (typeof input === "object") return JSON.stringify(input);
  return input;
}

function columnName(index) {
  let number = index + 1;
  let result = "";
  while (number > 0) {
    const remainder = (number - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    number = Math.floor((number - 1) / 26);
  }
  return result;
}

function rangeAddress(rowCount, columnCount) {
  return `A1:${columnName(columnCount - 1)}${rowCount}`;
}

function styleTable(sheet, headers, rowCount, widths) {
  sheet.showGridLines = false;
  const header = sheet.getRangeByIndexes(0, 0, 1, headers.length);
  header.format = {
    fill: "#0B1F33",
    font: { name: "Arial", bold: true, color: "#FFFFFF", size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
  header.format.rowHeight = 34;
  if (rowCount > 1) {
    const body = sheet.getRangeByIndexes(1, 0, rowCount - 1, headers.length);
    body.format = {
      font: { name: "Arial", size: 10, color: "#1F2937" },
      verticalAlignment: "center",
      wrapText: true,
      borders: { insideHorizontal: { style: "thin", color: "#E5E7EB" } },
    };
    body.format.rowHeight = 44;
  }
  widths.forEach((width, index) => {
    sheet.getRangeByIndexes(0, index, Math.max(1, rowCount), 1).format.columnWidth = width;
  });
  sheet.freezePanes.freezeRows(1);
  if (rowCount > 1) {
    const table = sheet.tables.add(rangeAddress(rowCount, headers.length), true, "OutreachPipeline");
    table.showFilterButton = true;
  }
}

const columns = [
  "company_id", "company_name", "wave", "first_contact_score", "industry", "website",
  "primary_contact_role", "primary_contact_name", "economic_buyer_role", "economic_buyer_name",
  "phone", "email", "linkedin", "whatsapp", "preferred_channel", "primary_opportunity",
  "pilot_name", "proposal_path", "outreach_path", "dossier_path", "status", "last_contact_date",
  "next_action", "next_action_date", "notes",
];

const widths = [22, 30, 12, 16, 28, 34, 30, 24, 24, 24, 24, 30, 34, 28, 18, 40, 42, 32, 32, 32, 18, 20, 42, 20, 50];
const companies = (await readJsonl(path.join(root, "data", "normalized", "companies.jsonl")))
  .filter((company) => company.commercial_readiness === "READY FOR OUTREACH")
  .sort((a, b) => (a.wave_rank ?? 999) - (b.wave_rank ?? 999));

const rows = companies.map((company) => {
  const contact = company.activation_contacts || {};
  const workflow = company.activation_primary_opportunity || {};
  const pilot = company.activation_pilot || {};
  return {
    company_id: company.company_id,
    company_name: company.company_name_fa,
    wave: company.contact_wave,
    first_contact_score: company.first_contact_score,
    industry: company.industry_fa || company.industry,
    website: company.website,
    primary_contact_role: contact.primary_contact_role,
    primary_contact_name: contact.primary_contact_name,
    economic_buyer_role: contact.economic_buyer_role,
    economic_buyer_name: contact.economic_buyer_name,
    phone: (contact.public_corporate_phones || []).join(", "),
    email: (contact.public_corporate_emails || []).join(", "),
    linkedin: contact.public_linkedin_company,
    whatsapp: contact.public_whatsapp,
    preferred_channel: company.preferred_channel,
    primary_opportunity: workflow.workflow_name_fa || workflow.workflow_name,
    pilot_name: pilot.pilot_name,
    proposal_path: `sales/client/${company.company_id}.md`,
    outreach_path: `sales/outreach/${company.company_id}.md`,
    dossier_path: `reports/dossiers/${company.company_id}.md`,
    status: "NOT_CONTACTED",
    last_contact_date: "",
    next_action: "Human review and approval before any first contact",
    next_action_date: "",
    notes: "No outreach sent. Validate process owner, volume, data owner and pilot sample.",
  };
});

if (rows.length !== 32) throw new Error(`Expected 32 READY rows, found ${rows.length}`);

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Outreach Pipeline");
const matrix = [columns, ...rows.map((row) => columns.map((column) => value(row[column])))];
sheet.getRangeByIndexes(0, 0, matrix.length, columns.length).values = matrix;
styleTable(sheet, columns, matrix.length, widths);

const instructions = workbook.worksheets.add("Instructions");
const instructionRows = [
  ["Field", "Meaning"],
  ["Scope", "Exactly the 32 current READY FOR OUTREACH companies; no additional discovery is represented here."],
  ["Status", "Every row starts as NOT_CONTACTED. This workbook does not claim any call, email, WhatsApp or LinkedIn action."],
  ["Wave 1", "First 10 recommended companies for human-approved preparation and contact sequencing."],
  ["Wave 2", "Next 10 companies after Wave 1 learning and review."],
  ["Wave 3", "Remaining 12 companies; retain as prepared opportunities, not contacted records."],
  ["Public channels", "Use only public corporate channels retained in the record. Names are blank unless publicly verified."],
];
instructions.getRangeByIndexes(0, 0, instructionRows.length, 2).values = instructionRows;
instructions.showGridLines = false;
instructions.getRangeByIndexes(0, 0, 1, 2).format = { fill: "#0B1F33", font: { name: "Arial", bold: true, color: "#FFFFFF", size: 10 }, wrapText: true };
instructions.getRangeByIndexes(0, 0, 1, 2).format.rowHeight = 30;
instructions.getRangeByIndexes(1, 0, instructionRows.length - 1, 2).format = { font: { name: "Arial", size: 10, color: "#1F2937" }, wrapText: true, verticalAlignment: "center", borders: { insideHorizontal: { style: "thin", color: "#E5E7EB" } } };
instructions.getRangeByIndexes(1, 0, instructionRows.length - 1, 2).format.rowHeight = 36;
instructions.getRangeByIndexes(0, 0, instructionRows.length, 1).format.columnWidth = 20;
instructions.getRangeByIndexes(0, 1, instructionRows.length, 1).format.columnWidth = 110;
instructions.freezePanes.freezeRows(1);

const outputDir = path.join(root, "data");
await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outputDir, "outreach_pipeline.xlsx"));

const previewDir = "/tmp/luma-b2b-outreach-previews";
await fs.mkdir(previewDir, { recursive: true });
for (const [sheetName, range, fileName] of [
  ["Outreach Pipeline", "A1:J15", "outreach_pipeline.png"],
  ["Instructions", "A1:B8", "instructions.png"],
]) {
  const blob = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, fileName), new Uint8Array(await blob.arrayBuffer()));
}

console.log(JSON.stringify({ workbook: path.join(outputDir, "outreach_pipeline.xlsx"), rows: rows.length, sheets: 2, preview_dir: previewDir }, null, 2));
