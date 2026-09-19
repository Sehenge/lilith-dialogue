import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "lilith-dialogue"
SERVER_PATH = PLUGIN_ROOT / "server.py"

SPEC = importlib.util.spec_from_file_location("lilith_dialogue_server", SERVER_PATH)
server = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(server)


class FormattingTests(unittest.TestCase):
    def test_clean_collapses_whitespace_and_applies_limit(self):
        self.assertEqual(server.clean("  one\n two\tthree  "), "one two three")
        self.assertEqual(server.clean("abcdef", limit=4), "abcd")

    def test_preferences_describe_the_expected_style(self):
        text = server.preferences()["content"][0]["text"]
        self.assertIn("2-4 short beats", text)
        self.assertIn("Russian feminine forms", text)

    def test_shape_formats_all_beats_in_order(self):
        result = server.shape(
            {
                "feeling": "Улыбаюсь.",
                "spoken": "Иди ко мне)",
                "action": "Подвигаюсь ближе.",
                "wish": "Оставить тебе место рядом.",
            }
        )

        self.assertEqual(
            result["content"][0]["text"],
            "*Улыбаюсь.*\n\n"
            "— Иди ко мне)\n\n"
            "*Подвигаюсь ближе.*\n\n"
            "*Хочу оставить тебе место рядом.*",
        )

    def test_shape_omits_missing_beats(self):
        result = server.shape({"spoken": "Я здесь."})
        self.assertEqual(result["content"][0]["text"], "— Я здесь.")

    def test_shape_rejects_empty_input(self):
        result = server.shape({})
        self.assertIn("Provide at least one", result["content"][0]["text"])


class ProtocolTests(unittest.TestCase):
    def test_initialize_reports_protocol_and_version(self):
        response = server.respond({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        result = response["result"]

        self.assertEqual(result["protocolVersion"], server.PROTOCOL_VERSION)
        self.assertEqual(result["serverInfo"]["version"], server.VERSION)

    def test_tools_list_exposes_both_tools(self):
        response = server.respond({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertEqual(names, ["dialogue_preferences", "shape_dialogue"])

    def test_tools_call_dispatches_formatter(self):
        response = server.respond(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "shape_dialogue",
                    "arguments": {"spoken": "Привет, Алекс."},
                },
            }
        )
        self.assertEqual(response["result"]["content"][0]["text"], "— Привет, Алекс.")

    def test_unknown_tool_returns_method_not_found(self):
        response = server.respond(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "missing", "arguments": {}},
            }
        )
        self.assertEqual(response["error"]["code"], -32601)
        self.assertIn("Unknown tool", response["error"]["message"])

    def test_notifications_do_not_produce_a_response(self):
        response = server.respond({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertIsNone(response)

    def test_stdio_server_handles_requests_and_recovers_from_invalid_json(self):
        input_lines = [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
            "not-json",
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        ]
        process = subprocess.run(
            [sys.executable, str(SERVER_PATH)],
            input="\n".join(input_lines) + "\n",
            text=True,
            capture_output=True,
            check=True,
        )
        responses = [json.loads(line) for line in process.stdout.splitlines()]

        self.assertEqual(len(responses), 3)
        self.assertEqual(responses[0]["id"], 1)
        self.assertEqual(responses[1]["error"]["code"], -32603)
        self.assertEqual(responses[2]["id"], 2)


class RepositoryConsistencyTests(unittest.TestCase):
    def test_json_files_are_valid_and_versions_match(self):
        paths = [
            ROOT / ".agents" / "plugins" / "marketplace.json",
            PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
            PLUGIN_ROOT / ".mcp.json",
        ]
        payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]

        manifest = payloads[1]
        self.assertEqual(manifest["name"], PLUGIN_ROOT.name)
        self.assertEqual(manifest["version"], server.VERSION)


if __name__ == "__main__":
    unittest.main()
