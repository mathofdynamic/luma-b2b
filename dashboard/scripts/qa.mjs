import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DASHBOARD_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ROOT = path.resolve(DASHBOARD_DIR, "..");
const failures = [];

function check(condition, message) {
  if (!condition) failures.push(message);
}

async function exists(relativePath) {
  try {
    await fs.access(path.join(ROOT, relativePath));
    return true;
  } catch {
    return false;
  }
}

async function main() {
  const required = [
    "dashboard/app/index.html",
    "dashboard/app/app.js",
    "dashboard/app/views.js",
    "dashboard/app/markdown.js",
    "dashboard/app/styles.css",
    "dashboard/server.mjs",
    "dashboard/data/index.json",
    "dashboard/data/company_details.jsonl",
    "dashboard/README.md",
  ];
  const fontFiles = [
    "IRANYekanX-Regular.woff2",
    "IRANYekanX-Medium.woff2",
    "IRANYekanX-DemiBold.woff2",
    "IRANYekanX-Bold.woff2",
    "IRANYekanX-ExtraBold.woff2",
    "IRANYekanX-Black.woff2",
    "IRANYekanXFaNum-Regular.woff2",
    "IRANYekanXFaNum-Medium.woff2",
    "IRANYekanXFaNum-DemiBold.woff2",
    "IRANYekanXFaNum-Bold.woff2",
    "IRANYekanXFaNum-ExtraBold.woff2",
    "IRANYekanXFaNum-Black.woff2",
  ].map((file) => `dashboard/app/fonts/${file}`);
  for (const file of required) check(await exists(file), `missing required file: ${file}`);
  for (const file of fontFiles) check(await exists(file), `missing local font file: ${file}`);

  let index = null;
  try {
    index = JSON.parse(await fs.readFile(path.join(DASHBOARD_DIR, "data/index.json"), "utf8"));
  } catch (error) {
    failures.push(`index is not valid JSON: ${error.message}`);
  }

  if (index) {
    check(index.sourceOfTruth === "data/normalized/companies.jsonl", "index source of truth is not canonical normalized JSONL");
    check(index.counts?.total >= 6000, `unexpected company count: ${index.counts?.total}`);
    check(index.counts?.ready === 32, `expected 32 ready companies, got ${index.counts?.ready}`);
    check(index.counts?.wave1 === 10, `expected 10 wave-one companies, got ${index.counts?.wave1}`);
    check(index.counts?.proposals === 32, `expected 32 proposal files, got ${index.counts?.proposals}`);
    check(index.counts?.outreachFiles === 32, `expected 32 outreach files, got ${index.counts?.outreachFiles}`);
    check(index.counts?.demos === 1, `expected one detected demo, got ${index.counts?.demos}`);
    check(index.companies?.length === index.counts?.total, "company index length does not match total");
    check(new Set(index.companies.map((company) => company.id)).size === index.companies.length, "duplicate company IDs in index");
    const sabahi = index.companies.find((company) => company.id === "ir-teh-2587928f98e4f816");
    check(Boolean(sabahi), "Sabah company is not indexed");
    check(sabahi?.nameFa === "شرکت صباحی", "Sabah canonical name is not present");
    check(sabahi?.decisions?.some((decision) => decision.name === "ناصر صباحی" && decision.key === "economic"), "Sabah economic buyer is not wired");
    check(sabahi?.demo?.slug === "sabahi", "Sabah demo is not attached to its company record");
    check(sabahi?.materials?.proposalClient?.available === true, "Sabah client proposal is not indexed");
    check(sabahi?.materials?.outreach?.available === true, "Sabah outreach draft is not indexed");
    check((index.facets?.workflowClasses || []).some((item) => item.value === "STRONG_HYPOTHESIS"), "workflow classification facet did not preserve strong hypotheses");
  }

  const appSource = await fs.readFile(path.join(DASHBOARD_DIR, "app/app.js"), "utf8");
  const viewSource = await fs.readFile(path.join(DASHBOARD_DIR, "app/views.js"), "utf8");
  const styleSource = await fs.readFile(path.join(DASHBOARD_DIR, "app/styles.css"), "utf8");
  const serverSource = await fs.readFile(path.join(DASHBOARD_DIR, "server.mjs"), "utf8");
  check(!/https?:\/\/(?!127\.0\.0\.1)/i.test(appSource), "frontend app contains an external network dependency");
  check(!/https?:\/\/(?!127\.0\.0\.1)/i.test(viewSource), "view layer contains an external network dependency");
  check(!/url\((['"]?)https?:\/\//i.test(styleSource), "styles contain an external font or asset dependency");
  check(styleSource.includes('font-family: var(--font-ui)'), "IRANYekanX UI font is not wired into the stylesheet");
  check(styleSource.includes('font-family: var(--font-numeric)'), "IRANYekanXFaNum numeric font is not wired into the stylesheet");
  check(styleSource.includes("@media (prefers-reduced-motion: reduce)"), "reduced-motion CSS is missing");
  check(appSource.includes("/api/review-state/"), "review persistence action is missing");
  check(serverSource.includes("127.0.0.1"), "server is not visibly loopback-only");
  check(serverSource.includes('".woff2": "font/woff2"'), "local WOFF2 font MIME type is missing");
  check(serverSource.includes('url.pathname.startsWith("/fonts/")'), "local font route is missing");
  check(serverSource.includes("path traversal rejected"), "local file path traversal guard is missing");
  check(!/open -a|osascript\s+activate/i.test(`${appSource}\n${serverSource}`), "visible macOS browser launch command found");

  const detailsText = await fs.readFile(path.join(DASHBOARD_DIR, "data/company_details.jsonl"), "utf8");
  const detailLines = detailsText.split("\n").filter(Boolean);
  check(detailLines.length === index?.counts?.total, `detail JSONL count mismatch: ${detailLines.length}`);
  for (const [lineNumber, line] of detailLines.slice(0, 20).entries()) {
    try {
      const item = JSON.parse(line);
      check(Boolean(item.id && item.nameFa && item.scores && item.quality), `detail line ${lineNumber + 1} missing required shape`);
    } catch (error) {
      failures.push(`detail line ${lineNumber + 1} is invalid JSON: ${error.message}`);
    }
  }

  const result = {
    passed: failures.length === 0,
    failures,
    counts: index?.counts || null,
    checked: {
      requiredFiles: required.length,
      detailRows: detailLines.length,
      localOnlyServer: serverSource.includes("127.0.0.1"),
      externalFrontendDependency: /https?:\/\/(?!127\.0\.0\.1)/i.test(appSource),
    },
  };
  console.log(JSON.stringify(result, null, 2));
  if (failures.length) process.exitCode = 1;
}

main().catch((error) => {
  console.error(`[dashboard:qa] fatal: ${error.stack || error.message}`);
  process.exitCode = 1;
});
