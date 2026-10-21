import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(__file__))
import jobber_recent_work as jr
from recent_work_lib import collect_attachments


class McpModeTests(unittest.TestCase):
    def test_no_oauth_in_mcp_mode(self):
        with mock.patch.dict(os.environ, {"JOBBER_MCP_RECENT_WORK_KEY": "x", "JOBBER_REFRESH_TOKEN": "r"}):
            with mock.patch.object(jr, "refresh_access_token", side_effect=AssertionError("refresh called")):
                with self.assertRaises(jr.JobberError):
                    jr.access_token()

    def test_mapping(self):
        job = {"id": "g1", "jobNumber": 3616, "title": "Booster Upgrade", "completedAt": "2026-10-21T01:27:11Z",
               "city": "Julian", "client": {"firstName": "T", "name": "T"},
               "photos": [{"url": "https://x/a.jpg?s=1", "fileName": "a.jpg", "contentType": "image/jpeg"},
                          {"url": "", "fileName": "b.jpg"}]}
        m = jr.mcp_job_to_graphql_shape(job)
        self.assertEqual(m["property"]["address"]["city"], "Julian")
        self.assertEqual(m["jobNumber"], 3616)
        self.assertEqual([a["name"] for a in collect_attachments(m)], ["a.jpg"])

    def test_fetch_paginates_via_search_jobs_only(self):
        pages = [{"jobs": [{"id": "1", "jobNumber": 1}], "pageInfo": {"hasNextPage": True, "endCursor": "c"}},
                 {"jobs": [{"id": "2", "jobNumber": 2}], "pageInfo": {"hasNextPage": False}}]
        calls = []
        def fake(name, args):
            calls.append((name, args.get("after")))
            return pages[len(calls) - 1]
        with mock.patch.dict(os.environ, {"JOBBER_MCP_RECENT_WORK_KEY": "x"}), \
             mock.patch.object(jr, "_mcp_call", side_effect=fake), mock.patch.object(jr.time, "sleep"):
            jobs = jr.fetch_jobs(days=7, pages=5, page_size=50)
        self.assertEqual([j["jobNumber"] for j in jobs], [1, 2])
        self.assertEqual(calls, [("search_jobs", None), ("search_jobs", "c")])


if __name__ == "__main__":
    unittest.main()
