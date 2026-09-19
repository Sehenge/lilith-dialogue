import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "lilith-dialogue"
SERVER_PATH = PLUGIN_ROOT / "server.py"
sys.path.insert(0, str(PLUGIN_ROOT))

import dialogue_profile

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
        self.assertIn("at most 4 short beats", text)
        self.assertIn("Russian using feminine grammatical forms", text)

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

    def test_shape_uses_english_wish_prefix(self):
        profile = dialogue_profile.DEFAULT_PROFILE | {"language": "en"}
        result = server.shape({"wish": "Stay close."}, profile=profile)
        self.assertEqual(result["content"][0]["text"], "*I want to stay close.*")

    def test_shape_respects_configured_max_beats(self):
        profile = dialogue_profile.DEFAULT_PROFILE | {"max_beats": 2}
        result = server.shape(
            {
                "feeling": "Улыбаюсь.",
                "spoken": "Я здесь.",
                "action": "Подвигаюсь ближе.",
            },
            profile=profile,
        )
        self.assertEqual(
            result["content"][0]["text"],
            "*Улыбаюсь.*\n\n— Я здесь.",
        )


class ProfileTests(unittest.TestCase):
    def test_missing_profile_preserves_alex_and_lilith_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            profile, resolved_path, warning = dialogue_profile.load_profile(path)

        self.assertEqual(profile, dialogue_profile.DEFAULT_PROFILE)
        self.assertEqual(resolved_path, path)
        self.assertIsNone(warning)

    def test_custom_profile_is_loaded_and_reflected_in_preferences(self):
        custom = {
            "profile_version": 1,
            "user_name": "Sam",
            "character_name": "Mira",
            "language": "en",
            "grammatical_gender": "neutral",
            "max_beats": 2,
            "roleplay_intensity": 1,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps(custom), encoding="utf-8")
            profile, _, warning = dialogue_profile.load_profile(path)

        text = server.preferences(profile=profile)["content"][0]["text"]
        self.assertIsNone(warning)
        self.assertIn("Character: Mira", text)
        self.assertIn("User: Sam", text)
        self.assertIn("Reply in English", text)
        self.assertIn("neutral grammatical forms", text)
        self.assertIn("at most 2 short beats", text)
        self.assertIn("restrained roleplay", text)

    def test_invalid_profile_falls_back_with_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text('{"language": "klingon"}', encoding="utf-8")
            profile, _, warning = dialogue_profile.load_profile(path)

        self.assertEqual(profile, dialogue_profile.DEFAULT_PROFILE)
        self.assertIn("Using defaults", warning)

    def test_boolean_profile_version_is_rejected(self):
        invalid = dialogue_profile.DEFAULT_PROFILE | {"profile_version": True}
        with self.assertRaises(dialogue_profile.ProfileError):
            dialogue_profile.validate_profile(invalid)

    def test_environment_override_selects_profile_path(self):
        path = dialogue_profile.default_profile_path(
            env={dialogue_profile.PROFILE_ENV_VAR: "/tmp/custom-profile.json"},
            home="/unused",
        )
        self.assertEqual(path, Path("/tmp/custom-profile.json"))


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

    def test_stdio_server_uses_profile_from_environment(self):
        custom = dialogue_profile.DEFAULT_PROFILE | {
            "user_name": "Sam",
            "character_name": "Mira",
            "language": "en",
            "grammatical_gender": "neutral",
            "max_beats": 2,
            "roleplay_intensity": 1,
        }
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "dialogue_preferences", "arguments": {}}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "shape_dialogue",
                    "arguments": {
                        "feeling": "I smile.",
                        "spoken": "Come closer.",
                        "wish": "Stay here.",
                    },
                },
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps(custom), encoding="utf-8")
            environment = os.environ | {dialogue_profile.PROFILE_ENV_VAR: str(path)}
            process = subprocess.run(
                [sys.executable, str(SERVER_PATH)],
                input="\n".join(json.dumps(request) for request in requests) + "\n",
                text=True,
                capture_output=True,
                check=True,
                env=environment,
            )

        responses = [json.loads(line) for line in process.stdout.splitlines()]
        preferences_text = responses[0]["result"]["content"][0]["text"]
        shaped_text = responses[1]["result"]["content"][0]["text"]
        self.assertIn("Character: Mira", preferences_text)
        self.assertEqual(shaped_text, "*I smile.*\n\n— Come closer.")


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

        profile_example = json.loads(
            (PLUGIN_ROOT / "profile.example.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            dialogue_profile.validate_profile(profile_example),
            dialogue_profile.DEFAULT_PROFILE,
        )


if __name__ == "__main__":
    unittest.main()
