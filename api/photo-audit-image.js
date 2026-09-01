/**
 * Authenticated image proxy so the audit page never needs a second photo store.
 * GET /api/photo-audit-image?id=job4242:1&days=1
 */
const {
  auditKey,
  buildQueue,
  corsHeaders,
  fetchJobs,
  isAuthorized,
  json,
  readDecisionsFromGitHub,
  refreshJobberToken,
} = require("../ops/photo-audit/server-lib");

const IMAGE_CACHE = new Map();

module.exports = async function handler(req, res) {
  const headers = corsHeaders(req);
  if (req.method === "OPTIONS") {
    json(res, 204, {}, headers);
    return;
  }
  if (req.method !== "GET") {
    json(res, 405, { error: "method_not_allowed" }, headers);
    return;
  }
  if (!auditKey() || !isAuthorized(req)) {
    json(res, 401, { error: "unauthorized" }, headers);
    return;
  }

  const url = new URL(req.url, "http://localhost");
  const id = url.searchParams.get("id") || "";
  const days = Math.min(Math.max(parseInt(url.searchParams.get("days") || "7", 10) || 7, 1), 30);
  if (!id) {
    json(res, 400, { error: "id_required" }, headers);
    return;
  }

  let jobs;
  try {
    jobs = await fetchJobs({ days, pages: 5, pageSize: 20 });
  } catch {
    json(res, 502, { error: "jobber_unavailable" }, headers);
    return;
  }
  const stored = await readDecisionsFromGitHub();
  const photos = buildQueue(jobs, stored.json);
  const photo = photos.find((p) => p.id === id);
  if (!photo || !photo.url || photo.skipped) {
    json(res, 404, { error: "not_found" }, headers);
    return;
  }

  const cacheKey = photo.url.split("?")[0];
  let buf = IMAGE_CACHE.get(cacheKey);
  if (!buf) {
    let token = null;
    try {
      token = await refreshJobberToken();
    } catch {
      token = null;
    }
    const headersIn = { "User-Agent": "scws-photo-audit/1.0" };
    let resp = await fetch(photo.url, { headers: headersIn });
    if ((resp.status === 401 || resp.status === 403) && token) {
      resp = await fetch(photo.url, {
        headers: { ...headersIn, Authorization: `Bearer ${token}` },
      });
    }
    if (!resp.ok) {
      json(res, 502, { error: "image_fetch_failed" }, headers);
      return;
    }
    buf = Buffer.from(await resp.arrayBuffer());
    if (buf.length > 800) IMAGE_CACHE.set(cacheKey, buf);
    if (IMAGE_CACHE.size > 40) {
      const first = IMAGE_CACHE.keys().next().value;
      IMAGE_CACHE.delete(first);
    }
  }

  res.statusCode = 200;
  for (const [k, v] of Object.entries(headers)) res.setHeader(k, v);
  res.setHeader("Content-Type", "image/jpeg");
  res.setHeader("Cache-Control", "private, max-age=300");
  res.end(buf);
};
