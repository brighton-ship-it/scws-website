#!/usr/bin/env python3
"""Jobber GraphQL client for the Recent Work publisher.

Auth (env, never commit these):
  JOBBER_ACCESS_TOKEN
    or
  JOBBER_CLIENT_ID + JOBBER_CLIENT_SECRET + JOBBER_REFRESH_TOKEN

Optional:
  JOBBER_GRAPHQL_VERSION  (default 2025-04-16)
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

GRAPHQL_URL = "https://api.getjobber.com/api/graphql"
TOKEN_URL = "https://api.getjobber.com/api/oauth/token"
DEFAULT_VERSION = "2025-04-16"

# Public Jobber docs: jobs connection + Job.noteAttachments.
# Field names are confirmed (or adjusted) via introspection when the token works.
JOBS_QUERY = """
query RecentWorkJobs($first: Int!, $after: String, $filter: JobFilterAttributes) {
  jobs(
    first: $first
    after: $after
    filter: $filter
    sort: [{ key: COMPLETED_AT, direction: DESCENDING }]
  ) {
    nodes {
      id
      jobNumber
      title
      jobStatus
      completedAt
      startAt
      endAt
      instructions
      client {
        firstName
        lastName
        emails {
          address
        }
      }
      property {
        address {
          city
        }
      }
      noteAttachments(first: 30) {
        nodes {
          id
          fileName
          url
          contentType
        }
      }
      visits(first: 10) {
        nodes {
          noteAttachments(first: 20) {
            nodes {
              id
              fileName
              url
              contentType
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

JOBS_QUERY_NO_VISITS = JOBS_QUERY.replace(
    """
      visits(first: 10) {
        nodes {
          noteAttachments(first: 20) {
            nodes {
              id
              fileName
              url
              contentType
            }
          }
        }
      }""",
    "",
)

_CLIENT_BLOCK = """
      client {
        firstName
        lastName
        emails {
          address
        }
      }
"""
JOBS_QUERY_NO_CLIENT = JOBS_QUERY.replace(_CLIENT_BLOCK, "")
JOBS_QUERY_NO_CLIENT_NO_VISITS = JOBS_QUERY_NO_VISITS.replace(_CLIENT_BLOCK, "")
class JobberError(RuntimeError):
    pass


def graphql_version() -> str:
    return os.environ.get("JOBBER_GRAPHQL_VERSION") or DEFAULT_VERSION


def refresh_access_token() -> str:
    client_id = os.environ.get("JOBBER_CLIENT_ID") or ""
    client_secret = os.environ.get("JOBBER_CLIENT_SECRET") or ""
    refresh_token = os.environ.get("JOBBER_REFRESH_TOKEN") or ""
    if not (client_id and client_secret and refresh_token):
        raise JobberError(
            "Need JOBBER_ACCESS_TOKEN, or JOBBER_CLIENT_ID + "
            "JOBBER_CLIENT_SECRET + JOBBER_REFRESH_TOKEN"
        )
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:400]
        raise JobberError(f"Jobber token refresh failed ({exc.code}): {detail}") from exc
    token = payload.get("access_token")
    if not token:
        raise JobberError(f"Jobber token refresh returned no access_token: {payload}")
    if payload.get("refresh_token"):
        os.environ["JOBBER_REFRESH_TOKEN"] = payload["refresh_token"]
        print(
            "Jobber rotated the refresh token for this session. "
            "If later runs fail auth, update the JOBBER_REFRESH_TOKEN GitHub secret "
            "from the Jobber Developer Center / Jarvis Integration app. "
            "The new token is not written to the repo."
        )
    os.environ["JOBBER_ACCESS_TOKEN"] = token
    return token


MCP_URL_DEFAULT = "https://scws-jobs.vercel.app/api/mcp/jobber"
MCP_KEY_ENV = "JOBBER_MCP_RECENT_WORK_KEY"


def mcp_mode() -> bool:
    """True when the read-only Production MCP key is set. In this mode we never
    touch Jobber OAuth (no refresh) — the scws-jobs app owns the token store."""
    return bool((os.environ.get(MCP_KEY_ENV) or "").strip())


def access_token() -> str:
    if mcp_mode():
        raise JobberError("MCP mode: no direct Jobber OAuth from this workflow.")
    token = os.environ.get("JOBBER_ACCESS_TOKEN") or ""
    if token:
        return token
    return refresh_access_token()


def _mcp_call(name: str, arguments: dict[str, Any], attempt: int = 0) -> dict[str, Any]:
    key = (os.environ.get(MCP_KEY_ENV) or "").strip()
    url = os.environ.get("JOBBER_MCP_URL") or MCP_URL_DEFAULT
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": arguments}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST", headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "scws-recent-work-publisher/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
    except urllib.error.HTTPError as exc:
        if exc.code in {429, 500, 502, 503, 504} and attempt < 3:
            time.sleep(2 + attempt * 3)
            return _mcp_call(name, arguments, attempt + 1)
        raise JobberError(f"Jobber MCP HTTP {exc.code} on {name}") from exc
    except urllib.error.URLError as exc:
        if attempt < 3:
            time.sleep(2 + attempt * 3)
            return _mcp_call(name, arguments, attempt + 1)
        raise JobberError(f"Jobber MCP unreachable on {name}") from exc
    data_lines = [line[5:].lstrip() for line in raw.splitlines() if line.startswith("data:")]
    body = json.loads("\n".join(data_lines) if data_lines else raw)
    if body.get("error"):
        raise JobberError(f"Jobber MCP error on {name}: {(body['error'] or {}).get('message')}")
    result = body.get("result") or {}
    content = result.get("content") or []
    text = content[0].get("text") if content else ""
    if result.get("isError"):
        raise JobberError(f"Jobber MCP tool error on {name}: {str(text)[:200]}")
    try:
        return json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        raise JobberError(f"Jobber MCP returned non-JSON for {name}") from exc


def mcp_job_to_graphql_shape(job: dict[str, Any]) -> dict[str, Any]:
    """Map a search_jobs result to the GraphQL job shape the card builder expects."""
    client = job.get("client") or {}
    photos = []
    for p in job.get("photos") or []:
        if isinstance(p, dict) and (p.get("url") or "").startswith("http"):
            photos.append({"url": p["url"], "fileName": p.get("fileName") or "",
                           "contentType": p.get("contentType") or ""})
    return {
        "id": job.get("id"),
        "jobNumber": job.get("jobNumber"),
        "title": job.get("title") or "",
        "jobStatus": job.get("jobStatus"),
        "completedAt": job.get("completedAt"),
        "createdAt": job.get("createdAt"),
        "startAt": None,
        "instructions": "",
        "client": {"firstName": client.get("firstName"), "name": client.get("name")},
        "property": {"address": {"city": job.get("city")}},
        "noteAttachments": {"nodes": photos},
    }


def fetch_jobs_mcp(*, days: int, pages: int, page_size: int) -> list[dict[str, Any]]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    jobs: list[dict[str, Any]] = []
    after = None
    for _page in range(pages):
        args: dict[str, Any] = {"status": "completed", "completedAfter": since,
                                "first": max(1, min(int(page_size), 25))}
        if after:
            args["after"] = after
        data = _mcp_call("search_jobs", args)
        jobs.extend(mcp_job_to_graphql_shape(j) for j in data.get("jobs") or [])
        info = data.get("pageInfo") or {}
        after = info.get("endCursor")
        if not info.get("hasNextPage") or not after:
            break
        time.sleep(0.25)
    return jobs


def graphql(query: str, variables: dict[str, Any] | None = None, *, token: str) -> dict[str, Any]:
    payload = {"query": query, "variables": variables or {}}
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-JOBBER-GRAPHQL-VERSION": graphql_version(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        if exc.code == 401 and os.environ.get("JOBBER_REFRESH_TOKEN"):
            token = refresh_access_token()
            return graphql(query, variables, token=token)
        raise JobberError(f"Jobber GraphQL HTTP {exc.code}: {body[:400]}") from exc
    if data.get("errors"):
        messages = "; ".join(
            e.get("message", str(e)) for e in data["errors"] if isinstance(e, dict)
        )
        raise JobberError(f"Jobber GraphQL errors: {messages}")
    if not data.get("data"):
        raise JobberError(f"Jobber GraphQL returned no data: {data}")
    return data["data"]


def type_fields(token: str, type_name: str) -> set[str]:
    query = """
    query TypeFields($name: String!) {
      __type(name: $name) {
        fields { name }
        inputFields { name }
      }
    }
    """
    try:
        data = graphql(query, {"name": type_name}, token=token)
    except JobberError:
        return set()
    info = data.get("__type") or {}
    names = set()
    for bucket in ("fields", "inputFields"):
        for item in info.get(bucket) or []:
            if item.get("name"):
                names.add(item["name"])
    return names


def build_filter(days: int, token: str) -> dict[str, Any]:
    after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    fields = type_fields(token, "JobFilterAttributes")
    filt: dict[str, Any] = {}
    if "completedAt" in fields:
        filt["completedAt"] = {"after": after}
    if "jobStatus" in fields:
        filt["jobStatus"] = ["ARCHIVED", "REQUIRES_INVOICING"]
    elif "status" in fields:
        filt["status"] = ["archived", "requires_invoicing"]
    if not filt:
        # Last-resort documented shape from Jobber jobs examples.
        filt = {"jobStatus": ["ARCHIVED", "REQUIRES_INVOICING"]}
    return filt


def _with_updated_sort(query: str) -> str:
    return query.replace(
        "sort: [{ key: COMPLETED_AT, direction: DESCENDING }]",
        "sort: [{ key: UPDATED_AT, direction: DESCENDING }]",
    )


def _first_working_jobs_query(token: str, variables: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    candidates = [
        JOBS_QUERY,
        _with_updated_sort(JOBS_QUERY),
        JOBS_QUERY_NO_VISITS,
        _with_updated_sort(JOBS_QUERY_NO_VISITS),
        JOBS_QUERY_NO_CLIENT,
        _with_updated_sort(JOBS_QUERY_NO_CLIENT),
        JOBS_QUERY_NO_CLIENT_NO_VISITS,
        _with_updated_sort(JOBS_QUERY_NO_CLIENT_NO_VISITS),
    ]
    last_error: JobberError | None = None
    for query in candidates:
        try:
            return query, graphql(query, variables, token=token)
        except JobberError as exc:
            last_error = exc
            continue
    raise JobberError(
        f"{last_error}\nThe Jobber schema for this account did not accept "
        "the documented jobs + noteAttachments query. Check API "
        "version (JOBBER_GRAPHQL_VERSION) and app scopes."
    )


def fetch_jobs(*, days: int, pages: int, page_size: int) -> list[dict[str, Any]]:
    if mcp_mode():
        return fetch_jobs_mcp(days=days, pages=pages, page_size=page_size)
    token = access_token()
    filt = build_filter(days, token)
    jobs: list[dict[str, Any]] = []
    after = None
    query: str | None = None
    for _page in range(pages):
        variables = {"first": page_size, "after": after, "filter": filt}
        if query is None:
            query, data = _first_working_jobs_query(token, variables)
        else:
            data = graphql(query, variables, token=token)
        conn = data.get("jobs") or {}
        nodes = conn.get("nodes") or []
        jobs.extend(nodes)
        page_info = conn.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")
        if not after:
            break
        time.sleep(0.25)
    return jobs


def download_bytes(url: str, *, token: str | None = None) -> bytes:
    headers = {"User-Agent": "scws-recent-work-publisher/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403} and token is None and not mcp_mode():
            return download_bytes(url, token=access_token())
        raise JobberError(f"Failed to download attachment ({exc.code}): {url[:80]}") from exc
