# Publishing a GitHub repository and release

This repository is ready for GitHub, but **placing a source archive in ChatGPT does not itself create a GitHub repository or GitHub Release**.

## Initial publishing (one time)

The example below uses the GitHub CLI and the authenticated username `uniquedough` (change if needed). Choose `--private` instead of `--public` if the code should not be public.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s engine/tests -p 'test_v*.py' -v
python scripts/build_release.py

git init
git add .
git commit -m "Release MIDI Lab plugin v1.0.0"
git branch -M main
gh auth login
gh repo create uniquedough/midi-lab-plugin --public --source=. --remote=origin --push

git tag v1.0.0
git push origin v1.0.0
```

The included GitHub Actions release workflow runs tests, packages the plugin, and creates/updates a release when a `v*` tag is pushed. Ensure repository Actions are enabled and workflows have permission to write contents. If the workflow is disabled or blocked, create the release manually:

```bash
gh release create v1.0.0 dist/midi-lab-plugin-v1.0.0.zip --title 'MIDI Lab Plugin 1.0.0' --notes-file RELEASE_NOTES.md
```

If the repo already exists, do not rerun `gh repo create`; use `git remote add origin ...`, push `main`, then push the version tag. Avoid overwriting unrelated repositories.

## Later releases

1. Bump `plugin.json` SemVer and `CHANGELOG.md`.
2. Run both test suites and `python scripts/build_release.py`.
3. Commit and push, then create and push a matching tag such as `v1.0.1`.
4. Verify the GitHub release includes `midi-lab-plugin-v1.0.1.zip` and the expected commit.
5. Update the private ChatGPT plugin package separately; GitHub releases do **not** auto-update the installed plugin.
