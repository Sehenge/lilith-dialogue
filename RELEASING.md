# Releasing Lilith Dialogue

Releases are created from signed-off version tags after the repository passes its local checks.

## Prepare a release

1. Update the version in both:
   - `plugins/lilith-dialogue/.codex-plugin/plugin.json`
   - `plugins/lilith-dialogue/server.py`
2. Move completed entries from `Unreleased` into a dated section in `CHANGELOG.md`.
3. Run the local verification commands documented in `README.md`.
4. Commit and push the release changes to `main`.
5. Confirm that the `CI` workflow succeeds.

## Publish a release

Create and push a tag matching the manifest version exactly:

```bash
git tag -a v0.2.0 -m "Lilith Dialogue v0.2.0"
git push origin v0.2.0
```

The `Release` workflow verifies the tag against the plugin manifest, runs the test suite, and creates the GitHub Release with generated notes.

## Verify distribution

Refresh the marketplace and reinstall the plugin:

```bash
codex plugin marketplace upgrade lilith-dialogue
codex plugin add lilith-dialogue@lilith-dialogue
```

Open a new Codex session and run an affectionate dialogue smoke test.
