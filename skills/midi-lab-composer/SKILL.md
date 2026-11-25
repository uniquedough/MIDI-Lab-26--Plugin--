---
name: midi-lab-composer
description: Compose original music with MIDI Lab v3/v4/v4.1, explain /cook prompts, create Logic-ready multitrack MIDI, use emotional and repetition modes, add removable textures, audit MIDI, and recommend v4.2 sound-design effects. Use for user requests about MIDI Lab songs, /cook prompts, and MIDI Lab production.
---

# MIDI Lab composer

Use the bundled **existing** source code under `engine/`; do not invent different composition capabilities. The composer ships with v3, v4.0, v4.1, and the v4.2 effects advisor. The **4.3 Sound-First Composition engine is a future roadmap**, not part of this release.

## Workflow

1. Parse `/cook` natural language into BPM, tonic, mode, duration, profile roles, emotional arc, repetition and texture style. Preserve the user's intent, particularly immutable loops and maximum density.
2. Use `list_profiles` when an actual profile identifier is uncertain; do not fabricate profile availability. The supported entry points are `midilab3.py`, `midilab4.py`, `midilab41.py`, and `effects42.py`.
3. If local MCP `cook_midi` is available, call it and use the returned path. For v3 songs select engine `v3`, for long emotional loops `v4`, for bliss/fracture/hybrid textures `v4.1`. Use optional `production_style` to create a separate Effects Advisor JSON.
4. If MCP tools are not available, do **not** claim to have run the local engine. If Python execution and the package are available in the task, invoke the engine directly following `docs/CLI.md`. Otherwise provide an accurate prompt and installation guidance.
5. For existing files, `analyze_midi`, `advise_effects`, and `patch_textures` are non-destructive. `patch_textures` writes a new MIDI. Original MIDI should always remain intact.
6. Verify file existence and the saved audit before linking any generated output. If the host cannot expose local files as ChatGPT downloads, provide the real local output path and steps to open it in Logic Pro instead of fabricating a download link.

## Invariants

- Type 1 multitrack MIDI, 480 PPQ, named instrument tracks. Never include MIDI Program Change, Bank Select CC0/CC32. The server checks forbidden events. Perform deeper technical checks through the engine's audit files.
- Sound-design chains are **recommendations**, not inserted audio effects, automation, or Logic preset files. A dotted-eighth delay is 45000/BPM milliseconds.
- Keep instrument and effects roles removable. Treat exact loop and drum locks as testable constraints.
- Preserve original authorship: draw on general production traits of musical influences, never reproduce a protected melody or arrangement note-for-note.
- Be specific about what the software generated vs what the person must assign inside Logic.

## References

- `docs/CLI.md` for available commands and modes.
- `docs/COOK_EXAMPLES.md` for demonstration prompts.
- `engine/README_V4_2.md`, `engine/README_V4_1.md`, `engine/README_V4.md`, `engine/README.md` for source-specific guidance.
