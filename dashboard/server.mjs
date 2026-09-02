import { createServer } from "node:http";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DASHBOARD_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)));
const ROOT = path.resolve(DASHBOARD_DIR, "..");
const APP_DIR = path.join(DASHBOARD_DIR, "app");
const DATA_DIR = path.join(DASHBOARD_DIR, "data");
const REVIEW_DIR = path.join(DASHBOARD_DIR, ".local");
const REVIEW_FILE = path.join(REVIEW_DIR, "review_state.json");
const PORT = Number(process.env.PORT || 5174);

const MIME = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".jsonl": "application/x-ndjson; charset=utf-8",
  ".md": "text/plain; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
  ".pdf": "application/pdf",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".ttf": "font/ttf",
};

const ALLOWED_REPO_PREFIXES = [
  "data/normalized/",
  "demos/",
  "docs/",
  "evidence/",
  "proposals/",
  "reports/",
  "research/",
  "sales/",
];

let index = null;
let details = new Map();
let reviewWriteQueue = Promise.resolve();

function jsonResponse(response, status, value) {
  const body = JSON.stringify(value);
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
  });
  response.end(body);
}

function textResponse(response, status, body, contentType = "text/plain; charset=utf-8") {
  response.writeHead(status, {
    "Content-Type": contentType,
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
  });
  response.end(body);
}

function normalizeRelative(value) {
  const decoded = decodeURIComponent(String(value || "")).replaceAll("\\", "/");
  if (!decoded || decoded.includes("\0")) throw new Error("invalid path");
  const normalized = path.posix.normalize(decoded).replace(/^\.\//, "");
  if (normalized === ".." || normalized.startsWith("../") || path.posix.isAbsolute(normalized)) throw new Error("path traversal rejected");
  return normalized;
}

function repoFile(relativePath) {
  const normalized = normalizeRelative(relativePath);
  if (!ALLOWED_REPO_PREFIXES.some((prefix) => normalized.startsWith(prefix))) throw new Error("path is outside the local evidence allowlist");
  const absolute = path.resolve(ROOT, normalized);
  if (absolute !== ROOT && !absolute.startsWith(`${ROOT}${path.sep}`)) throw new Error("path traversal rejected");
  return { normalized, absolute };
}

async function loadReviewState() {
  try {
    const parsed = JSON.parse(await fs.readFile(REVIEW_FILE, "utf8"));
    return parsed && typeof parsed === "object" && parsed.companies && typeof parsed.companies === "object"
      ? parsed
      : { version: 1, updatedAt: null, companies: {} };
  } catch {
    return { version: 1, updatedAt: null, companies: {} };
  }
}

async function persistReviewState(state) {
  await fs.mkdir(REVIEW_DIR, { recursive: true });
  const temporary = `${REVIEW_FILE}.tmp`;
  await fs.writeFile(temporary, `${JSON.stringify(state, null, 2)}\n`, "utf8");
  await fs.rename(temporary, REVIEW_FILE);
}

async function readBody(request, maxBytes = 64 * 1024) {
  const chunks = [];
  let total = 0;
  for await (const chunk of request) {
    total += chunk.length;
    if (total > maxBytes) throw new Error("request body too large");
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function loadData() {
  const indexPath = path.join(DATA_DIR, "index.json");
  const detailsPath = path.join(DATA_DIR, "company_details.jsonl");
  try {
    index = JSON.parse(await fs.readFile(indexPath, "utf8"));
    const detailText = await fs.readFile(detailsPath, "utf8");
    details = new Map();
    for (const line of detailText.split("\n")) {
      if (!line.trim()) continue;
      try {
        const detail = JSON.parse(line);
        if (detail.id) details.set(detail.id, detail);
      } catch (error) {
        console.warn(`[dashboard] skipped malformed detail line: ${error.message}`);
      }
    }
    return null;
  } catch (error) {
    index = null;
    details = new Map();
    return error;
  }
}

async function serveFile(response, absolute, fallbackType = null) {
  try {
    const stat = await fs.stat(absolute);
    if (!stat.isFile()) return textResponse(response, 404, "Not found");
    const extension = path.extname(absolute).toLowerCase();
    const type = fallbackType || MIME[extension] || "application/octet-stream";
    const body = await fs.readFile(absolute);
    response.writeHead(200, {
      "Content-Type": type,
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "Content-Length": body.byteLength,
    });
    response.end(body);
  } catch {
    textResponse(response, 404, "Not found");
  }
}

function reviewWithDetail(detail, reviewState) {
  return {
    ...detail,
    review: reviewState.companies?.[detail.id] || {
      status: "UNREVIEWED",
      favorite: false,
      note: "",
      reviewedAt: null,
      updatedAt: null,
    },
  };
}

async function handleApi(request, response, url) {
  if (!index) return jsonResponse(response, 503, { error: "Dashboard index is missing. Run npm run data:build first." });
  if (url.pathname === "/api/health") return jsonResponse(response, 200, { ok: true, localOnly: true, companies: index.counts.total, generatedAt: index.generatedAt });
  if (url.pathname === "/api/bootstrap") return jsonResponse(response, 200, index);
  if (url.pathname === "/api/review-state" && request.method === "GET") return jsonResponse(response, 200, await loadReviewState());

  const companyMatch = url.pathname.match(/^\/api\/companies\/([^/]+)$/);
  if (companyMatch && request.method === "GET") {
    const id = decodeURIComponent(companyMatch[1]);
    const detail = details.get(id);
    if (!detail) return jsonResponse(response, 404, { error: "Company not found" });
    return jsonResponse(response, 200, reviewWithDetail(detail, await loadReviewState()));
  }

  const reviewMatch = url.pathname.match(/^\/api\/review-state\/([^/]+)$/);
  if (reviewMatch && request.method === "PUT") {
    const id = decodeURIComponent(reviewMatch[1]);
    if (!details.has(id)) return jsonResponse(response, 404, { error: "Company not found" });
    let payload;
    try {
      payload = JSON.parse(await readBody(request));
    } catch (error) {
      return jsonResponse(response, 400, { error: error.message || "Invalid JSON" });
    }
    const allowedStatuses = new Set(["UNREVIEWED", "APPROVED_FOR_OUTREACH", "NEEDS_MORE_RESEARCH", "REJECTED_BY_HUMAN", "FOLLOW_UP_LATER"]);
    const status = allowedStatuses.has(payload.status) ? payload.status : "UNREVIEWED";
    const state = await loadReviewState();
    const now = new Date().toISOString();
    state.version = 1;
    state.updatedAt = now;
    state.companies[id] = {
      status,
      favorite: payload.favorite === true,
      note: typeof payload.note === "string" ? payload.note.slice(0, 5000) : "",
      reviewedAt: status === "UNREVIEWED" ? null : (state.companies[id]?.reviewedAt || now),
      updatedAt: now,
    };
    reviewWriteQueue = reviewWriteQueue.then(() => persistReviewState(state));
    try {
      await reviewWriteQueue;
      return jsonResponse(response, 200, state.companies[id]);
    } catch (error) {
      return jsonResponse(response, 500, { error: `Could not persist review state: ${error.message}` });
    }
  }

  if (url.pathname === "/api/material" && request.method === "GET") {
    try {
      const file = repoFile(url.searchParams.get("path"));
      if (!/\.(md|txt|json|jsonl)$/i.test(file.normalized)) throw new Error("unsupported material type");
      return serveFile(response, file.absolute, /\.jsonl?$/i.test(file.normalized) ? "application/json; charset=utf-8" : "text/plain; charset=utf-8");
    } catch (error) {
      return textResponse(response, 403, error.message);
    }
  }
  return jsonResponse(response, 404, { error: "API route not found" });
}

async function handleRequest(request, response) {
  const url = new URL(request.url, `http://${request.headers.host || "127.0.0.1"}`);
  if (url.pathname.startsWith("/api/")) return handleApi(request, response, url);

  if (url.pathname.startsWith("/repo/")) {
    try {
      const file = repoFile(url.pathname.slice("/repo/".length));
      return serveFile(response, file.absolute);
    } catch (error) {
      return textResponse(response, 403, error.message);
    }
  }

  const demoMatch = url.pathname.match(/^\/demo\/([^/]+)(?:\/(.*))?$/);
  if (demoMatch && index) {
    const slug = decodeURIComponent(demoMatch[1]);
    const demo = index.demos.find((item) => item.slug === slug);
    if (!demo) return textResponse(response, 404, "Demo not found");
    const rest = demoMatch[2] ? normalizeRelative(demoMatch[2]) : "app/index.html";
    const appCandidate = repoFile(`${demo.rootPath}/app/${rest}`);
    const rootCandidate = repoFile(`${demo.rootPath}/${rest}`);
    try {
      await fs.access(appCandidate.absolute);
      return serveFile(response, appCandidate.absolute);
    } catch {
      return serveFile(response, rootCandidate.absolute);
    }
  }

  if (url.pathname.startsWith("/fonts/")) {
    try {
      const fontName = normalizeRelative(url.pathname.slice("/fonts/".length));
      const allowedFont = /^IRANYekanX(?:FaNum)?-(?:Regular|Medium|DemiBold|Bold|ExtraBold|Black)\.woff2$/;
      if (!allowedFont.test(fontName)) return textResponse(response, 404, "Font not found");
      return serveFile(response, path.join(APP_DIR, "fonts", fontName));
    } catch (error) {
      return textResponse(response, 403, error.message);
    }
  }

  const appPath = url.pathname === "/" ? "index.html" : url.pathname.replace(/^\//, "");
  if (!appPath.includes("/") && ["index.html", "app.js", "views.js", "data.js", "markdown.js", "styles.css"].includes(appPath)) {
    return serveFile(response, path.join(APP_DIR, appPath));
  }
  if (appPath === "favicon.svg") return serveFile(response, path.join(APP_DIR, appPath));
  // SPA fallback keeps query-driven routes bookmarkable without exposing repo files.
  return serveFile(response, path.join(APP_DIR, "index.html"));
}

const dataError = await loadData();
if (dataError) console.warn(`[dashboard] ${dataError.message}; run npm run data:build before opening the dashboard.`);

const server = createServer((request, response) => {
  handleRequest(request, response).catch((error) => {
    console.error(`[dashboard] request error: ${error.stack || error.message}`);
    if (!response.headersSent) jsonResponse(response, 500, { error: "Local dashboard request failed" });
    else response.end();
  });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`LUMA B2B review dashboard listening at http://127.0.0.1:${PORT}/`);
  console.log("Local-only server; no external network or AI service is used.");
});

function shutdown() {
  server.close(() => process.exit(0));
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
