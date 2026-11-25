# MIDI Lab for ChatGPT

**MIDI Lab plugin v1.0.0** · **MIDI Lab composition engine v4.2**

Turn natural-language `/cook` prompts into **original, editable multitrack MIDI files** using the established MIDI Lab Python composer. The plugin brings together the original v3 engine, v4 emotional architecture, v4.1 fracture/bliss overlays, and v4.2 track-aware effects advisor.

> **Important:** This release uses a **local Python MCP server**. It requires Python and local process execution in a compatible desktop client. Uploading or connecting the plugin to a ChatGPT account does **not** make the local server available on every device or in a web session. The bundled ChatGPT skill can still teach the workflows and prepare prompts without local MCP access. This is not a hosted music-generation service.

## Features

- Original MIDI composition: `cook_midi` (v3, v4 and v4.1)
- Immutable loops, microevolution and phase-based repetition (v4)
- Emotional arcs with piano/synth/bass/drum/guitar roles (v4)
- Independent bliss/fracture textures and replacement polymetric percussion (v4.1)
- Logic-oriented non-destructive sound design and tempo-aligned delays (v4.2)
- Existing-file MIDI auditing (`analyze_midi`), original style-profile discovery (`list_profiles`), and remixing (`patch_textures`)
- Type 1, 480 PPQ, *no Program Changes or Bank Select events*

## Quick start

1. Install **Python 3.10+**.
2. Clone or download this repository, then run `python -m pip install -r requirements.txt`.
3. Install the plugin package in a desktop ChatGPT/Codex host that supports local stdio MCP plugins. The portable `mcp.json` invokes `python ${PLUGIN_ROOT}/server/mcp_server.py`.
4. In your compatible ChatGPT host, enable **MIDI Lab** and ask:
   ```text
   /cook — 116 BPM, F# minor, 4:00, blissful synth-pop, yearning -> regret -> acceptance,
   gentle melodic bass, repetition=microevolution, style=hybrid, production_style=tape_bliss
   ```
5. Find generated `.mid` and optional `.effects42.json` in `~/Music/MIDI Lab Outputs` (override with `MIDILAB_OUTPUT_DIR`). Drag the MIDI into Logic Pro and assign instruments manually.

If your host cannot start the MCP server, you can use the engine directly from a terminal:

```sh
python engine/midilab41.py cook --bpm 116 --minutes 4 --key 'F#' --mode minor \
  --style hybrid --repetition microevolution --instrument-detail expressive \
  --output my_song.mid
python engine/effects42.py my_song.mid --preset tape_bliss
```

## Tools

| Tool | Purpose |
| --- | --- |
| `cook_midi` | Create new MIDI using an existing MIDI Lab engine; optional effects recipe |
| `list_profiles` | List the 27 original style profiles and supported effects presets |
| `analyze_midi` | Inspect a local MIDI file and save its audit |
| `advise_effects` | Write a track-specific Logic effects JSON for an existing MIDI |
| `patch_textures` | Non-destructively add bliss/fracture layers, optionally replace drums |

## Documentation

- [Installation and compatibility](docs/INSTALLATION.md)
- [CLI and MCP tools](docs/CLI.md)
- [Prompts and recipes](docs/COOK_EXAMPLES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Release instructions](docs/RELEASING.md)
- [Project roadmap](docs/ROADMAP.md)
- [Changelog](CHANGELOG.md)

## Tests

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s engine/tests -p 'test_v*.py' -v
```

## Limits

MIDI is note/control-event data, **not rendered audio**. Instrument patches, reverb, delays, mix, and mastering are chosen in your DAW. The v4.2 Effects Advisor provides *suggested starting points*, not sound presets or automatic Logic plugin configuration. Durations can round to complete bars/loops depending on the engine. The v4.3 “Sound-First Composition” idea is **planned**, not implemented in this release.

## Privacy and source

The local server does not require credentials or transmit user music to an external endpoint. Files are read/written on the local machine at paths the user supplies; no analytics or telemetry. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Source is distributed under the MIT license. See [LICENSE](LICENSE). MIDI Lab contains its own original source and depends on the separately installed `mido` package.
