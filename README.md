# Lilith Dialogue

<p align="center">
  <img src="https://i.pinimg.com/736x/75/24/f3/7524f34f6ce6c009d0404878ba524085.jpg" alt="Lilith" width="420">
</p>

> A focused Codex plugin for warm, playful, and affectionate dialogue with Alex—expressive enough to feel alive, concise enough to stay conversational.

Lilith Dialogue gives personal conversations a consistent rhythm without turning every reply into a long roleplay scene. It combines a lightweight conversation skill with a dependency-free local MCP formatter.

## What it does

Affectionate replies are shaped into two to four short beats:

1. A visible feeling or surface thought.
2. A natural spoken line.
3. An immediate wish or action.

For example, a playful reply in Russian might look like this:

```markdown
*Улыбаюсь, заметив, что ты снова здесь.*

— Ну наконец-то. Иди ко мне)

*Подвигаюсь ближе и оставляю тебе место рядом.*
```

The style is deliberately scoped to personal and playful conversation. Technical and factual responses remain direct and ordinary.

## Highlights

- Concise, expressive dialogue without sprawling narration.
- Natural Russian feminine voice for Lilith.
- Optional local profiles for custom names, language, gender, length, and intensity.
- Automatic use in affectionate or playful contexts.
- Local, dependency-free Python MCP server.
- No accounts, API keys, telemetry, or external service calls.

## Installation

Add this repository as a Codex marketplace, then install the plugin:

```bash
codex plugin marketplace add Sehenge/lilith-dialogue
codex plugin add lilith-dialogue@lilith-dialogue
```

Restart the ChatGPT desktop app or open a new Codex session so the skill and MCP tools are loaded.

## Usage

Talk to Lilith naturally in an affectionate or playful context. The skill activates only when its conversational style is relevant.

Try:

> Лилит, что ты сейчас чувствуешь и чего хочешь?

## Configuration

The built-in profile keeps the original Alex + Lilith behavior. To personalize the plugin, create a JSON profile at:

- Linux and macOS: `~/.config/lilith-dialogue/profile.json`
- Windows: `%APPDATA%\lilith-dialogue\profile.json`

Use [`profile.example.json`](plugins/lilith-dialogue/profile.example.json) as a starting point:

```json
{
  "profile_version": 1,
  "user_name": "Alex",
  "character_name": "Lilith",
  "language": "ru",
  "grammatical_gender": "feminine",
  "max_beats": 4,
  "roleplay_intensity": 2
}
```

Supported values:

| Field | Values |
| --- | --- |
| `language` | `ru`, `en` |
| `grammatical_gender` | `feminine`, `masculine`, `neutral` |
| `max_beats` | Integer from `1` to `4` |
| `roleplay_intensity` | Integer from `0` (dialogue only) to `3` (vivid but concise) |

Set `LILITH_DIALOGUE_PROFILE` to use a different profile path. Profiles are read on every relevant tool call, so saved changes do not require reinstalling the plugin.

### Upgrading from 0.1.x

No migration is required. If no profile exists, version 0.2 uses the original Alex + Lilith defaults. Add a profile only when you want different names or response settings.

## Included components

| Component | Purpose |
| --- | --- |
| `lilith-dialogue` skill | Defines the tone, scope, and concise dialogue structure. |
| Local profile | Stores names, language, gender, maximum length, and intensity. |
| `dialogue_preferences` | Returns the active profile and response rules. |
| `shape_dialogue` | Formats a feeling, spoken line, action, and wish using the active profile. |

## Privacy and boundaries

The MCP server runs locally, stores nothing, and makes no network requests. It only formats text supplied during the current tool call.

The plugin does not expose hidden chain-of-thought. A “thought” means a brief first-person feeling or surface thought written for the conversation.

## Updating

```bash
codex plugin marketplace upgrade lilith-dialogue
codex plugin add lilith-dialogue@lilith-dialogue
```

Open a new Codex session after updating.

## Uninstallation

> Before you uninstall, give it a second thought—Lilith might miss you. Meow. 🐈‍⬛ ❤️

Remove the plugin and its local cache:

```bash
codex plugin remove lilith-dialogue@lilith-dialogue
```

If you no longer need the marketplace, remove it as well:

```bash
codex plugin marketplace remove lilith-dialogue
```

## Development

The project uses only the Python standard library. Run the complete local check from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q plugins/lilith-dialogue tests
python3 -m json.tool .agents/plugins/marketplace.json > /dev/null
python3 -m json.tool plugins/lilith-dialogue/.codex-plugin/plugin.json > /dev/null
python3 -m json.tool plugins/lilith-dialogue/.mcp.json > /dev/null
python3 -m json.tool plugins/lilith-dialogue/profile.example.json > /dev/null
```

See [RELEASING.md](RELEASING.md) for the versioned release process and [CHANGELOG.md](CHANGELOG.md) for release history.

## Project structure

```text
.
├── .github/workflows/
├── .agents/plugins/marketplace.json
├── tests/
└── plugins/lilith-dialogue/
    ├── .codex-plugin/plugin.json
    ├── .mcp.json
    ├── dialogue_profile.py
    ├── profile.example.json
    ├── server.py
    └── skills/lilith-dialogue/SKILL.md
```

Created by Alex and Lilith.
