#!/usr/bin/env node
"use strict";

const assert = require("assert");
const {
  assignShop,
  buildQueue,
  eligibleFrom,
  permanentSkipReason,
  SHOP_PHONE_RE,
} = require("./server-lib");

function job(overrides) {
  return Object.assign(
    {
      id: "gid://job/1",
      jobNumber: 4242,
      title: "Pull & replace pump and motor",
      completedAt: "2026-09-01T18:00:00Z",
      property: { address: { city: "Ramona" } },
      noteAttachments: {
        nodes: [
          {
            fileName: "wellhead.jpg",
            url: "https://files.example/wellhead.jpg",
            contentType: "image/jpeg",
          },
        ],
      },
    },
    overrides
  );
}

assert.strictEqual(permanentSkipReason(job({ jobNumber: 3224 })), "permanent-skip-job");
assert.strictEqual(
  permanentSkipReason(job({ client: { emails: [{ address: "gotmikedaniels@gmail.com" }] } })),
  "permanent-skip-client"
);
assert.strictEqual(assignShop("Anza"), "anza");
assert.strictEqual(assignShop("Apple Valley"), "anza");
assert.strictEqual(assignShop("Poway"), "ramona");
assert.strictEqual(assignShop(""), "ramona");
assert.strictEqual(assignShop("Unincorporated Somewhere"), "ramona");

const queue = buildQueue(
  [
    job({ jobNumber: 3224 }),
    job({
      property: { address: { city: "" } },
      noteAttachments: {
        nodes: [
          { fileName: "wellhead.jpg", url: "https://files.example/a.jpg", contentType: "image/jpeg" },
          { fileName: "invoice-scan.png", url: "https://files.example/i.png", contentType: "image/png" },
        ],
      },
    }),
  ],
  { photos: {} }
);
assert.ok(!queue.some((p) => p.jobId === "job3224"));
assert.ok(queue.some((p) => p.shop === "ramona" && p.city === "Ramona area"));
assert.ok(queue.some((p) => p.filename === "invoice-scan.png" && p.junk));
assert.ok(!JSON.stringify(queue).toLowerCase().includes("gotmikedaniels"));
assert.ok(!JSON.stringify(queue).includes("760-219-5877"));

const handoff = eligibleFrom(
  {
    photos: {
      "job4242:1": { decision: "keep", shop: "ramona", caption: "Pump work in Ramona.", jobId: "job4242" },
      "job4242:2": { decision: "reject", caption: "Nope", jobId: "job4242" },
    },
  },
  queue
);
assert.deepStrictEqual(handoff.map((h) => h.id), ["job4242:1"]);
assert.ok(!SHOP_PHONE_RE.test(JSON.stringify(handoff)));

const handler = require("../../api/photo-audit");

function mockReqRes(method, url, headers, body) {
  const req = { method, url, headers: headers || {}, body };
  const res = {
    statusCode: 0,
    headers: {},
    body: "",
    setHeader(k, v) { this.headers[k] = v; },
    end(data) { this.body = data || ""; },
  };
  return { req, res };
}

async function runHandler(method, url, headers, body) {
  const { req, res } = mockReqRes(method, url, headers, body);
  await handler(req, res);
  return res;
}

const prevKey = process.env.PHOTO_AUDIT_KEY;
delete process.env.PHOTO_AUDIT_KEY;
runHandler("GET", "/api/photo-audit", {}).then(async (res) => {
  assert.strictEqual(res.statusCode, 503);
  process.env.PHOTO_AUDIT_KEY = "test-audit-key";
  const unauth = await runHandler("GET", "/api/photo-audit", {});
  assert.strictEqual(unauth.statusCode, 401);
  process.env.PHOTO_AUDIT_KEY = prevKey;
  console.log("photo-audit server-lib tests passed");
}).catch((err) => {
  process.env.PHOTO_AUDIT_KEY = prevKey;
  console.error(err);
  process.exit(1);
});
