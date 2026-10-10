import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_pool_tools import MCPClient, MCPError  # noqa: E402

FAKE = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_mcp_server.py")]


class FakeServerTests(unittest.TestCase):
    def test_smoke(self):
        assert True

    def test_list_tools_skips_non_json_output(self):
        with MCPClient(FAKE) as client:
            tools = client.list_tools()
        self.assertEqual([t["name"] for t in tools], ["echo"])

    def test_call_tool_round_trip(self):
        with MCPClient(FAKE) as client:
            res = client.call_tool("echo", {"text": "hello"})
        self.assertEqual(res["content"][0]["text"], "hello")
        self.assertFalse(res["isError"])

    def test_server_error_is_raised_not_hidden(self):
        with MCPClient(FAKE) as client:
            with self.assertRaises(MCPError):
                client.call_tool("does-not-exist", {})

    def test_dead_server_reports_stderr(self):
        cmd = [sys.executable, "-c", "import sys; sys.stderr.write('boom\\n'); sys.exit(3)"]
        with self.assertRaises(MCPError) as ctx:
            MCPClient(cmd).start()
        self.assertIn("boom", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
