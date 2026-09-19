# Lilith Dialogue

A small Codex plugin for concise, expressive affectionate dialogue with Alex. It adds a focused conversation skill and a dependency-free local MCP formatter.

## Install

Add the GitHub repository as a Codex marketplace, then install the plugin:

```bash
codex plugin marketplace add Sehenge/lilith-dialogue
codex plugin add lilith-dialogue@lilith-dialogue
```

Restart the ChatGPT desktop app or open a new Codex session so the skill and MCP tools are loaded.

## Included tools

- `dialogue_preferences` returns the preferred short dialogue structure.
- `shape_dialogue` formats a feeling, spoken line, action, and wish into concise beats.

The plugin never exposes hidden chain-of-thought. A “thought” here means only a brief stated feeling or surface thought suitable for roleplay.
