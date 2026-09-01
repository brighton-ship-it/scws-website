/**
 * Keep/reject API for the internal photo audit.
 * GET  /api/photo-audit?days=1
 * POST /api/photo-audit  { id, decision: "keep"|"reject", caption?, shop? }
 *
 * Auth: PHOTO_AUDIT_KEY via Authorization Bearer, X-Photo-Audit-Key, cookie, or ?key=
 * Decisions persist to ops/photo-audit/decisions.json via GitHub Contents API.
 */
const {
  applyDecision,
  auditKey,
  buildQueue,
  corsHeaders,
  eligibleFrom,
  fetchJobs,
  githubToken,
  isAuthorized,
  json,
  keyCookie,
  providedKey,
  readDecisionsFromGitHub,
  writeDecisionsToGitHub,
} = require("../ops/photo-audit/server-lib");

function send(res, status, body, req, extra) {
  json(res, status, body, { ...corsHeaders(req), ...extra });
}

module.exports = async function handler(req, res) {
  if (req.method === "OPTIONS") {
    send(res, 204, {}, req);
    return;
  }

  const headers = corsHeaders(req);

  if (!auditKey()) {
    send(res, 503, { error: "PHOTO_AUDIT_KEY is not set" }, req);
    return;
  }
  if (!isAuthorized(req)) {
    send(res, 401, { error: "unauthorized" }, req);
    return;
  }

  const extra = { "Set-Cookie": keyCookie(providedKey(req) || auditKey()) };

  if (req.method === "GET") {
    const url = new URL(req.url, "http://localhost");
    const days = Math.min(Math.max(parseInt(url.searchParams.get("days") || "1", 10) || 1, 1), 30);
    const eligibleOnly = url.searchParams.get("eligible") === "1";
    let decisions;
    try {
      const stored = await readDecisionsFromGitHub();
      decisions = stored.json;
    } catch {
      send(res, 500, { error: "could_not_read_decisions" }, req);
      return;
    }

    let jobs = [];
    let source = "jobber";
    try {
      jobs = await fetchJobs({ days, pages: 5, pageSize: 20 });
    } catch (err) {
      source = "unavailable";
      send(
        res,
        200,
        {
          generatedAt: new Date().toISOString(),
          days,
          source,
          warning: err instanceof Error ? err.message : "Jobber unavailable",
          photos: [],
          eligible: eligibleFrom(decisions, []),
          persist: githubToken() ? "github" : "none",
        },
        req,
        extra
      );
      return;
    }

    const photos = buildQueue(jobs, decisions);
    const payload = {
      generatedAt: new Date().toISOString(),
      days,
      source,
      count: photos.length,
      photos: eligibleOnly ? photos.filter((p) => p.decision === "keep") : photos,
      eligible: eligibleFrom(decisions, photos),
      persist: githubToken() ? "github" : "none",
    };
    json(res, 200, payload, { ...headers, ...extra });
    return;
  }

  if (req.method === "POST") {
    let body = req.body;
    if (typeof body === "string") {
      try {
        body = JSON.parse(body);
      } catch {
        send(res, 400, { error: "invalid_json" }, req);
        return;
      }
    }
    if (!body || typeof body !== "object") {
      send(res, 400, { error: "invalid_json" }, req);
      return;
    }

    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        const stored = await readDecisionsFromGitHub();
        const row = applyDecision(stored.json, body);
        if (!githubToken()) {
          send(
            res,
            503,
            {
              error: "PHOTO_AUDIT_GITHUB_TOKEN is not set",
              decision: row,
              hint: "Decision was not saved. Add a contents:write token on Vercel.",
            },
            req,
            extra
          );
          return;
        }
        await writeDecisionsToGitHub(stored.json, stored.sha);
        send(res, 200, { ok: true, decision: row, persist: "github" }, req, extra);
        return;
      } catch (err) {
        if (err && err.code === "CONFLICT" && attempt < 2) continue;
        send(
          res,
          500,
          { error: err instanceof Error ? err.message : "write_failed" },
          req,
          extra
        );
        return;
      }
    }
  }

  send(res, 405, { error: "method_not_allowed" }, req);
};
