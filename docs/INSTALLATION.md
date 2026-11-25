# Installation and compatibility

## Prerequisites

- Python 3.10 or higher
- A local MCP-compatible ChatGPT/Codex desktop host capable of starting stdio servers
- `mido` Python dependency (`pip install -r requirements.txt`)
- Logic Pro or any other MIDI-compatible DAW for assigning instruments and applying effects

## ChatGPT plugin package

The root `plugin.json` is the Agent Plugins 1.0 manifest. The `mcp.json` advertises a local stdio server. You can install the `.zip` as a private ChatGPT plugin using Plugin Creator. *Installation creates the plugin record, not a cloud-hosted Python process.* Local tools are available only in environments that support and start the local executor. The skill can still answer recipe and production questions in other ChatGPT environments.

If the plugin is visible but `cook_midi` is absent, **do not assume the tools have started**. Use a desktop client that supports local stdio plugins or run the Python CLI directly. A restart/reconnect may be necessary after enabling local tools.

## Python installation

```bash
python --version
python -m pip install -r requirements.txt
```

Use `python3` if your environment requires it. If `python` is not on PATH, edit `mcp.json` to a working local Python command or interpreter path. Do not package your personal machine path as a universal default.

## Output

Default: `~/Music/MIDI Lab Outputs`.

Override:

```bash
# Unix shell
export MIDILAB_OUTPUT_DIR="$HOME/Music/My MIDI Projects"
# Windows PowerShell
$env:MIDILAB_OUTPUT_DIR="$HOME\Music\MIDI Lab Outputs"
```

Each `cook_midi` call returns real local paths for MIDI and its sidecar manifests/audits. Your chat client may or may not expose those local paths as downloadable chat attachments. If not, open the folder yourself and drag the `.mid` into Logic.

## Test the stdio server directly

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s engine/tests -p 'test_v*.py' -v
```

### Troubleshooting

- **Tools absent in web/mobile:** stdio local tools are not cloud-hosted. Use a supported local host or the CLI.
- **`No module named mido`:** install requirements into the same Python interpreter that starts the server.
- **Unknown profile:** query `list_profiles` or `python engine/midilab3.py profiles`.
- **BPM/duration mismatch:** the original composer may round section lengths to complete bars/loops. Inspect generated `.audit.json` and import at the embedded MIDI tempo.
- **No sound in Logic:** MIDI does not carry a software instrument patch. Assign a synth/keyboard/drum kit to each imported track.
