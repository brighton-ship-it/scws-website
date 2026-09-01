/**
 * Server helpers for /api/photo-audit.
 * Mirrors scripts/photo_audit_lib.py — keep lists in rules.json.
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const RULES_PATH = path.join(ROOT, "ops", "photo-audit", "rules.json");
const DECISIONS_PATH = path.join(ROOT, "ops", "photo-audit", "decisions.json");

const SHOP_PHONE_RE =
  /760[-.\s]?219[-.\s]?5877|760[-.\s]?440[-.\s]?8520|\(760\)\s*219[-.\s]?5877|\(760\)\s*440[-.\s]?8520/gi;
const STREET_RE =
  /\b\d{1,6}\s+[A-Za-z0-9.'-]+(?:\s+[A-Za-z0-9.'-]+){0,4}\s+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Way|Ct|Court|Blvd|Boulevard|Hwy|Highway|Cir|Circle|Pl|Place|Ter|Terrace|Pkwy|Parkway)\b\.?/gi;
const PRICE_RE =
  /\$\s*[\d,]+(?:\.\d{1,2})?|\b\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?\s*(?:dollars?)?\b/gi;
const EMAIL_RE = /\b[\w.+-]+@[\w-]+\.[\w.-]+\b/g;
const PHONE_RE = /\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}/g;
const URL_RE = /https?:\/\/\S+/gi;

let rulesCache = null;
let junkRe = null;

function loadRules() {
  if (rulesCache) return rulesCache;
  rulesCache = JSON.parse(fs.readFileSync(RULES_PATH, "utf8"));
  junkRe = new RegExp(
    (rulesCache.junkFilename || []).map((p) => `(?:${p})`).join("|"),
    "i"
  );
  return rulesCache;
}

function auditKey() {
  return (process.env.PHOTO_AUDIT_KEY || "").trim();
}

function providedKey(req) {
  const header =
    req.headers["x-photo-audit-key"] ||
    req.headers["authorization"] ||
    "";
  if (typeof header === "string" && header.toLowerCase().startsWith("bearer ")) {
    return header.slice(7).trim();
  }
  if (typeof header === "string" && header && !header.toLowerCase().startsWith("bearer")) {
    return header.trim();
  }
  const cookie = req.headers.cookie || "";
  const match = /(?:^|;\s*)photo_audit_key=([^;]+)/.exec(cookie);
  if (match) {
    try {
      return decodeURIComponent(match[1]);
    } catch {
      return match[1];
    }
  }
  const url = new URL(req.url, "http://localhost");
  return (url.searchParams.get("key") || "").trim();
}

function isAuthorized(req) {
  const expected = auditKey();
  if (!expected) return false;
  const got = providedKey(req);
  if (!got || got.length !== expected.length) return false;
  let out = 0;
  for (let i = 0; i < expected.length; i += 1) {
    out |= expected.charCodeAt(i) ^ got.charCodeAt(i);
  }
  return out === 0;
}

function corsHeaders(req) {
  const origin = req.headers.origin || "";
  const allowed = new Set([
    "https://scwellservice.com",
    "https://www.scwellservice.com",
    "https://scws-website.vercel.app",
  ]);
  const headers = {
    "Cache-Control": "private, no-store",
    "X-Robots-Tag": "noindex, nofollow, noarchive",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Photo-Audit-Key",
    "Access-Control-Allow-Credentials": "true",
    Vary: "Origin",
  };
  if (allowed.has(origin) || /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) {
    headers["Access-Control-Allow-Origin"] = origin;
  }
  return headers;
}

function json(res, status, body, extraHeaders) {
  const headers = { "Content-Type": "application/json; charset=utf-8", ...extraHeaders };
  res.statusCode = status;
  for (const [k, v] of Object.entries(headers)) res.setHeader(k, v);
  res.end(JSON.stringify(body));
}

function sanitizePublicText(text, fallback = "") {
  if (!text) return fallback;
  let out = String(text);
  out = out.replace(URL_RE, "");
  out = out.replace(EMAIL_RE, "");
  out = out.replace(SHOP_PHONE_RE, "");
  out = out.replace(PHONE_RE, "");
  out = out.replace(PRICE_RE, "");
  out = out.replace(STREET_RE, "");
  out = out.replace(/\s+/g, " ").replace(/\s+,/g, ",").trim().replace(/^[,;\-\s]+|[,;\-\s]+$/g, "");
  return out || fallback;
}

function publicCity(city) {
  const safe = sanitizePublicText((city || "").trim());
  if (!safe) return "";
  const first = safe.split(",")[0].trim();
  if (/\d/.test(first)) return "";
  return first;
}

function assignShop(city) {
  const rules = loadRules();
  let cityL = (city || "").trim().toLowerCase().replace(/\s+/g, " ");
  if (cityL.includes(",")) cityL = cityL.split(",")[0].trim();
  if (cityL) {
    for (const name of rules.anzaCities || []) {
      if (cityL === name || cityL.includes(name)) return "anza";
    }
    for (const name of rules.ramonaCities || []) {
      if (cityL === name || cityL.includes(name)) return "ramona";
    }
  }
  return "ramona";
}

function shopLocationLabel(city, shop) {
  const safe = publicCity(city);
  if (safe) return safe;
  return shop === "anza" ? "Anza area" : "Ramona area";
}

function isJunkFilename(name, contentType) {
  const n = (name || "").toLowerCase();
  const ct = (contentType || "").toLowerCase();
  loadRules();
  if (n.endsWith(".pdf")) return { junk: true, reason: "not-an-image" };
  const isImage = ct.startsWith("image/") || /\.(jpe?g|png|webp|gif|heic|heif)$/i.test(n);
  if (!isImage) return { junk: true, reason: "not-an-image" };
  if (junkRe && junkRe.test(name || "")) {
    return { junk: true, reason: "filename-looks-like-paperwork" };
  }
  return { junk: false, reason: null };
}

function jobNumber(job) {
  if (job.jobNumber != null && job.jobNumber !== "") return String(job.jobNumber);
  const digits = String(job.id || "").match(/\d+/g);
  return digits ? digits[digits.length - 1] : "unknown";
}

function normalizeJobId(number) {
  const raw = String(number || "").trim();
  const digits = raw.replace(/\D+/g, "") || raw;
  return digits && !raw.toLowerCase().startsWith("job") ? `job${digits}` : raw || "jobunknown";
}

function haystack(job) {
  const bits = [job.jobNumber, job.title, job.instructions, job.id];
  const client = job.client || {};
  bits.push(client.firstName, client.lastName, client.name);
  const emails = client.emails || [];
  if (Array.isArray(emails)) {
    for (const item of emails) {
      bits.push(item && typeof item === "object" ? item.address : item);
    }
  } else if (typeof emails === "string") {
    bits.push(emails);
  }
  return bits.filter(Boolean).join(" ").toLowerCase();
}

function permanentSkipReason(job) {
  const skip = loadRules().permanentSkip || {};
  const number = jobNumber(job);
  if ((skip.jobNumbers || []).map(String).includes(number)) return "permanent-skip-job";
  const hay = haystack(job);
  for (const email of skip.emails || []) {
    if (email && hay.includes(String(email).toLowerCase())) return "permanent-skip-client";
  }
  for (const frag of skip.nameFragments || []) {
    if (frag && hay.includes(String(frag).toLowerCase())) return "permanent-skip-client";
  }
  for (const inv of skip.invoiceNumbers || []) {
    if (hay.includes(`invoice ${inv}`) || hay.includes(`invoice #${inv}`)) {
      return "permanent-skip-invoice";
    }
  }
  return null;
}

function pickUrl(node) {
  for (const key of ["url", "fileUrl", "downloadUrl", "publicUrl", "uri"]) {
    if (typeof node[key] === "string" && node[key].startsWith("http")) return node[key];
  }
  if (node.file && typeof node.file === "object") return pickUrl(node.file);
  return "";
}

function pickName(node, fallback) {
  for (const key of ["fileName", "filename", "name"]) {
    if (typeof node[key] === "string" && node[key].trim()) return node[key].trim();
  }
  if (node.file && typeof node.file === "object") return pickName(node.file, fallback);
  return fallback;
}

function pickType(node) {
  for (const key of ["contentType", "fileType", "mimeType"]) {
    if (typeof node[key] === "string") return node[key];
  }
  if (node.file && typeof node.file === "object") return pickType(node.file);
  return "";
}

function collectAttachments(job) {
  const found = [];
  const seen = new Set();
  const addNodes = (nodes) => {
    if (!Array.isArray(nodes)) return;
    nodes.forEach((node, i) => {
      if (!node || typeof node !== "object") return;
      const url = pickUrl(node);
      const name = pickName(node, `attachment-${i + 1}`);
      const ctype = pickType(node);
      const { junk, reason } = isJunkFilename(name, ctype);
      if (!url) return;
      if (junk && reason === "not-an-image") return;
      const key = url.split("?")[0];
      if (seen.has(key)) return;
      seen.add(key);
      found.push({ url, name, contentType: ctype });
    });
  };
  const notes = job.noteAttachments || {};
  addNodes(notes.nodes || notes);
  const visits = (job.visits && job.visits.nodes) || [];
  for (const visit of visits) {
    if (!visit) continue;
    const vnotes = visit.noteAttachments || {};
    addNodes(vnotes.nodes || vnotes);
  }
  return found;
}

function captionForPhoto(title, city, filename, index, taken) {
  let work = sanitizePublicText(title, "");
  work = work.replace(SHOP_PHONE_RE, "").replace(/\s+/g, " ").trim();
  if (!work || work.length < 4) work = "Well service";
  const loc = publicCity(city) || String(city || "").trim() || "Southern California";
  let candidate = `${work} in ${loc}.`;
  candidate = sanitizePublicText(candidate, `Well service in ${loc}.`);
  if (!candidate.endsWith(".")) candidate += ".";
  let n = 2;
  const fileHint = sanitizePublicText(
    path.basename(filename || "", path.extname(filename || "")).replace(/[_-]+/g, " ")
  );
  while ([...taken].some((t) => t.toLowerCase() === candidate.toLowerCase())) {
    if (fileHint && n === 2 && fileHint.length >= 4) {
      candidate = `${work} (${fileHint.slice(0, 32)}) in ${loc}.`;
    } else {
      candidate = `${work} in ${loc} — field photo ${index + n - 2}.`;
    }
    candidate = sanitizePublicText(candidate, `${work} in ${loc}.`);
    if (!candidate.endsWith(".")) candidate += ".";
    n += 1;
    if (n > 8) break;
  }
  taken.add(candidate);
  return candidate;
}

function publicTitle(job) {
  const title = sanitizePublicText((job.title || "").trim(), "");
  return title && title.length >= 4 ? title : "Well service";
}

function emptyDecisions() {
  return { version: 1, updatedAt: null, photos: {} };
}

function readLocalDecisions() {
  try {
    return JSON.parse(fs.readFileSync(DECISIONS_PATH, "utf8"));
  } catch {
    return emptyDecisions();
  }
}

function decisionFor(id, decisions) {
  const value = String((decisions.photos && decisions.photos[id] && decisions.photos[id].decision) || "pending");
  return ["keep", "reject", "pending"].includes(value) ? value : "pending";
}

function buildQueue(jobs, decisions) {
  const taken = new Set();
  const items = [];
  for (const job of jobs) {
    const skip = permanentSkipReason(job);
    if (skip) continue;
    const attachments = collectAttachments(job);
    const jobId = normalizeJobId(jobNumber(job));
    const rawCity = (((job.property || {}).address || {}).city) || "";
    const city = publicCity(rawCity);
    const shop = assignShop(city || rawCity);
    const location = shopLocationLabel(city || rawCity, shop);
    const title = publicTitle(job);
    attachments.forEach((att, i) => {
      const index = i + 1;
      const id = `${jobId}:${index}`;
      const junkInfo = isJunkFilename(att.name, att.contentType);
      const existing = decisionFor(id, decisions);
      items.push({
        id,
        jobId,
        jobNumber: jobNumber(job),
        title,
        city: location,
        shop,
        completedAt: job.completedAt || job.endAt || "",
        filename: att.name,
        url: att.url,
        junk: junkInfo.junk || existing === "reject",
        junkReason: junkInfo.reason || (existing === "reject" ? "rejected" : null),
        skipped: false,
        skipReason: null,
        caption: captionForPhoto(title, location, att.name, index, taken),
        decision: existing,
      });
    });
  }
  return items;
}

function eligibleFrom(decisions, queue) {
  const byId = Object.fromEntries((queue || []).map((p) => [p.id, p]));
  const out = [];
  for (const [id, row] of Object.entries((decisions && decisions.photos) || {})) {
    if (!row || row.decision !== "keep") continue;
    const item = byId[id] || {};
    let caption = sanitizePublicText((row.caption || item.caption || "").replace(SHOP_PHONE_RE, ""));
    caption = caption.replace(SHOP_PHONE_RE, "").trim();
    if (!caption) continue;
    out.push({
      id,
      jobId: row.jobId || item.jobId || id.split(":")[0],
      shop: row.shop || item.shop || "ramona",
      city: item.city || "",
      caption,
      filename: item.filename || "",
    });
  }
  return out;
}

const JOBS_QUERY = `
query RecentWorkJobs($first: Int!, $after: String, $filter: JobFilterAttributes) {
  jobs(first: $first, after: $after, filter: $filter, sort: [{ key: COMPLETED_AT, direction: DESCENDING }]) {
    nodes {
      id
      jobNumber
      title
      jobStatus
      completedAt
      startAt
      endAt
      instructions
      client { firstName lastName emails { address } }
      property { address { city } }
      noteAttachments(first: 30) { nodes { id fileName url contentType } }
      visits(first: 10) { nodes { noteAttachments(first: 20) { nodes { id fileName url contentType } } } }
    }
    pageInfo { hasNextPage endCursor }
  }
}
`;

async function refreshJobberToken() {
  const clientId = process.env.JOBBER_CLIENT_ID || "";
  const clientSecret = process.env.JOBBER_CLIENT_SECRET || "";
  const refreshToken = process.env.JOBBER_REFRESH_TOKEN || "";
  if (process.env.JOBBER_ACCESS_TOKEN) return process.env.JOBBER_ACCESS_TOKEN;
  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error("Jobber credentials are not set");
  }
  const body = new URLSearchParams({
    client_id: clientId,
    client_secret: clientSecret,
    grant_type: "refresh_token",
    refresh_token: refreshToken,
  });
  const resp = await fetch("https://api.getjobber.com/api/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const json = await resp.json();
  if (!resp.ok || !json.access_token) {
    throw new Error("Jobber token refresh failed");
  }
  process.env.JOBBER_ACCESS_TOKEN = json.access_token;
  return json.access_token;
}

async function jobberGraphql(query, variables, token) {
  const resp = await fetch("https://api.getjobber.com/api/graphql", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "X-JOBBER-GRAPHQL-VERSION": process.env.JOBBER_GRAPHQL_VERSION || "2025-04-16",
    },
    body: JSON.stringify({ query, variables }),
  });
  const json = await resp.json();
  if (!resp.ok || json.errors) {
    throw new Error((json.errors && json.errors[0] && json.errors[0].message) || `Jobber HTTP ${resp.status}`);
  }
  return json.data;
}

async function fetchJobs({ days = 1, pages = 4, pageSize = 20 } = {}) {
  const token = await refreshJobberToken();
  const afterDate = new Date(Date.now() - days * 86400000).toISOString();
  const filter = {
    completedAt: { after: afterDate },
    jobStatus: ["ARCHIVED", "REQUIRES_INVOICING"],
  };
  const jobs = [];
  let after = null;
  let query = JOBS_QUERY;
  for (let page = 0; page < pages; page += 1) {
    let data;
    try {
      data = await jobberGraphql(query, { first: pageSize, after, filter }, token);
    } catch (err) {
      if (page === 0) {
        query = JOBS_QUERY.replace(
          "client { firstName lastName emails { address } }",
          ""
        ).replace(
          "sort: [{ key: COMPLETED_AT, direction: DESCENDING }]",
          "sort: [{ key: UPDATED_AT, direction: DESCENDING }]"
        );
        data = await jobberGraphql(query, { first: pageSize, after, filter }, token);
      } else {
        throw err;
      }
    }
    const conn = (data && data.jobs) || {};
    jobs.push(...(conn.nodes || []));
    if (!conn.pageInfo || !conn.pageInfo.hasNextPage || !conn.pageInfo.endCursor) break;
    after = conn.pageInfo.endCursor;
  }
  return jobs;
}

function githubRepo() {
  return process.env.PHOTO_AUDIT_GITHUB_REPO || "brighton-ship-it/scws-website";
}

function githubToken() {
  return (
    process.env.PHOTO_AUDIT_GITHUB_TOKEN ||
    process.env.GITHUB_TOKEN ||
    ""
  ).trim();
}

async function readDecisionsFromGitHub() {
  const token = githubToken();
  if (!token) return { json: readLocalDecisions(), sha: null, source: "local" };
  const resp = await fetch(
    `https://api.github.com/repos/${githubRepo()}/contents/ops/photo-audit/decisions.json`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "User-Agent": "scws-photo-audit",
      },
    }
  );
  if (!resp.ok) return { json: readLocalDecisions(), sha: null, source: "local" };
  const data = await resp.json();
  const text = Buffer.from(data.content, "base64").toString("utf8");
  return { json: JSON.parse(text), sha: data.sha, source: "github" };
}

async function writeDecisionsToGitHub(json, sha) {
  const token = githubToken();
  if (!token) {
    const err = new Error("PHOTO_AUDIT_GITHUB_TOKEN is not set");
    err.code = "NO_GITHUB_TOKEN";
    throw err;
  }
  const body = {
    message: "photo-audit: record keep/reject",
    content: Buffer.from(`${JSON.stringify(json, null, 2)}\n`).toString("base64"),
    sha,
    branch: process.env.PHOTO_AUDIT_DECISIONS_REF || "main",
  };
  const resp = await fetch(
    `https://api.github.com/repos/${githubRepo()}/contents/ops/photo-audit/decisions.json`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "scws-photo-audit",
      },
      body: JSON.stringify(body),
    }
  );
  if (resp.status === 409) {
    const err = new Error("conflict");
    err.code = "CONFLICT";
    throw err;
  }
  if (!resp.ok) {
    const detail = await resp.text();
    throw new Error(`GitHub write failed (${resp.status}): ${detail.slice(0, 200)}`);
  }
  return resp.json();
}

function applyDecision(data, { id, decision, caption, shop, jobId }) {
  if (!id || !["keep", "reject"].includes(decision)) {
    throw new Error("id and decision=keep|reject are required");
  }
  const photos = data.photos || {};
  const existing = photos[id] || {};
  let cleanCaption = caption
    ? sanitizePublicText(String(caption).replace(SHOP_PHONE_RE, ""))
    : existing.caption || "";
  cleanCaption = cleanCaption.replace(SHOP_PHONE_RE, "").trim();
  const now = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  photos[id] = {
    ...existing,
    decision,
    at: now,
    jobId: jobId || existing.jobId || id.split(":")[0],
    shop: shop || existing.shop || "ramona",
    caption: cleanCaption,
  };
  data.photos = photos;
  data.updatedAt = now;
  data.version = 1;
  return photos[id];
}

function keyCookie(key) {
  const secure = process.env.VERCEL ? "; Secure" : "";
  return `photo_audit_key=${encodeURIComponent(key)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800${secure}`;
}

module.exports = {
  ROOT,
  DECISIONS_PATH,
  SHOP_PHONE_RE,
  applyDecision,
  assignShop,
  auditKey,
  buildQueue,
  collectAttachments,
  corsHeaders,
  decisionFor,
  eligibleFrom,
  fetchJobs,
  githubToken,
  isAuthorized,
  json,
  keyCookie,
  permanentSkipReason,
  providedKey,
  readDecisionsFromGitHub,
  readLocalDecisions,
  refreshJobberToken,
  writeDecisionsToGitHub,
};
