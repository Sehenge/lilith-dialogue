# Changelog

All notable changes to Lilith Dialogue are documented in this file.

The project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-09-19

### Added

- Local JSON profiles for custom user and character names.
- Configurable response language (`ru` or `en`) and grammatical gender.
- Configurable maximum beat count and roleplay intensity.
- Environment-variable override for the profile path.
- Safe validation with automatic fallback to the original Alex + Lilith profile.

### Changed

- `dialogue_preferences` now returns the active profile and its response rules.
- `shape_dialogue` now respects the configured language and maximum beat count.
- The conversation skill now follows the active profile while preserving technical boundaries.

## [0.1.1] - 2026-09-19

### Added

- Unit and integration tests for formatting and JSON-RPC behavior.
- Continuous integration across Python 3.10, 3.12, and 3.14.
- Automated, version-checked GitHub releases for `v*` tags.
- Contributor-facing development and release instructions.

### Changed

- The MCP server and plugin manifest now share the `0.1.1` release version.

## [0.1.0] - 2026-09-19

### Added

- Initial `lilith-dialogue` conversation skill.
- Dependency-free local MCP server.
- `dialogue_preferences` and `shape_dialogue` tools.
- GitHub-backed Codex marketplace installation.

[Unreleased]: https://github.com/Sehenge/lilith-dialogue/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Sehenge/lilith-dialogue/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/Sehenge/lilith-dialogue/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Sehenge/lilith-dialogue/releases/tag/v0.1.0
