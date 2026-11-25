#!/usr/bin/env python3
"""Self-contained stdio MCP host for the original MIDI Lab v3-v4.2 engine.

No external MCP SDK needed. Dependencies: Python>=3.10 and mido.
Each JSON-RPC message occupies one line; stdout reserved for MCP protocol.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"
OUTPUT = Path(os.environ.get("MIDILAB_OUTPUT_DIR", str(Path.home() / "Music" / "MIDI Lab Outputs"))).expanduser().resolve()
PRESETS = ["bossa_afterglow", "broadcast_ident", "fracture_void", "midnight_motorik", "rigid_machine", "tape_bliss"]
EMOTIONS = ["yearning", "regret", "numbness", "recognition", "acceptance", "triumph", "unease", "tenderness"]

COOK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "description": "Short output title; sanitized into a .mid filename"},
        "engine": {"type": "string", "enum": ["v3", "v4", "v4.1"], "default": "v4.1"},
        "bpm": {"type": "number", "minimum": 40, "maximum": 220},
        "minutes": {"type": "number", "minimum": 0.75, "maximum": 9},
        "key": {"type": "string", "description": "Tonic: C, C#, D, Eb, E, F, F#, G, Ab, A, Bb, B"},
        "mode": {"type": "string", "enum": ["major", "minor", "dorian", "mixolydian"]},
        "profile": {"type": "string"},
        "harmony": {"type": "string"},
        "rhythm": {"type": "string"},
        "bass": {"type": "string"},
        "melody": {"type": "string"},
        "arrangement": {"type": "string"},
        "arc": {"type": "string", "description": "Comma-separated emotional stages, such as yearning,regret,recognition,triumph"},
        "repetition": {"type": "string", "enum": ["immutable", "microevolution", "phase"]},
        "instrument_detail": {"type": "string", "enum": ["machine", "natural", "expressive"]},
        "style": {"type": "string", "enum": ["minimal", "bliss", "fracture", "hybrid"]},
        "drum_mode": {"type": "string", "enum": ["keep", "replace", "off"]},
        "drum_complexity": {"type": "number", "minimum": 0, "maximum": 1},
        "intensity": {"type": "number", "minimum": 0, "maximum": 1},
        "seed": {"type": "integer", "minimum": 0, "maximum": 2147483647},
        "production_style": {"type": "string", "enum": PRESETS, "description": "Generate separate .effects42.json sound-design advice"},
        "drums": {"type": "string", "description": "Legacy v3 rhythm choice; only for engine=v3"},
        "performance": {"type": "string", "enum": ["none", "natural", "tight", "loose", "neworder"], "description": "Legacy v3 performance choice"},
    },
    "required": ["title", "bpm", "minutes", "key"]
}

TOOLS = [
    {"name": "cook_midi", "description": "Compose original multitrack Type-1 MIDI with MIDI Lab v3/v4/v4.1 and optional v4.2 Logic effects advice. Writes files locally.", "inputSchema": COOK_SCHEMA},
    {"name": "list_profiles", "description": "List all source style profiles and supported MIDI Lab engines/effect presets.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "analyze_midi", "description": "Audit an existing local MIDI and write an analysis JSON file.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False}},
    {"name": "advise_effects", "description": "Recommend track-by-track Logic Pro sound-design chains for an existing local MIDI; does not alter notes.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "preset": {"type": "string", "enum": PRESETS}}, "required": ["path"], "additionalProperties": False}},
    {"name": "patch_textures", "description": "Add removable fracture/bliss textures or replace drums on an existing local MIDI.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "title": {"type": "string"}, "key": {"type": "string"}, "mode": {"type": "string", "enum": ["major", "minor", "dorian", "mixolydian"]}, "style": {"type": "string", "enum": ["minimal", "bliss", "fracture", "hybrid"]}, "drum_mode": {"type": "string", "enum": ["keep", "replace", "off"]}, "intensity": {"type": "number", "minimum": 0, "maximum": 1}, "drum_complexity": {"type": "number", "minimum": 0, "maximum": 1}, "seed": {"type": "integer", "minimum": 0}}, "required": ["path", "title"], "additionalProperties": False}},
]

class ToolError(Exception):
    pass


def output_path(title: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:75]
    if not slug:
        raise ToolError("Provide a title with letters or digits")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    candidate = OUTPUT / (slug + ".mid")
    i = 2
    while candidate.exists():
        candidate = OUTPUT / (slug + f"_{i}.mid")
        i += 1
    return candidate


def input_path(raw: str) -> Path:
    p = Path(raw).expanduser().resolve()
    if not p.is_file() or p.suffix.lower() not in (".mid", ".midi"):
        raise ToolError("An existing local .mid or .midi path is required")
    return p


def run(script: str, args: list[str]) -> dict:
    cmd = [sys.executable, str(ENGINE / script), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ENGINE, timeout=120)
    if proc.returncode:
        raise ToolError((proc.stderr or proc.stdout or "Engine failed")[-3000:])
    return {"command": script + " " + " ".join(args), "summary": proc.stdout.strip()[-1500:]}


def run_audit(p: Path) -> dict:
    from mido import MidiFile
    mid = MidiFile(str(p))
    prohibited = []
    notes = 0
    for track in mid.tracks:
        for msg in track:
            if msg.type == "program_change" or (msg.type == "control_change" and msg.control in (0, 32)):
                prohibited.append(msg.type)
            if msg.type == "note_on" and msg.velocity > 0:
                notes += 1
    if prohibited:
        raise ToolError("Export contains forbidden program/bank events: " + repr(prohibited))
    return {"midi_type": mid.type, "ppq": mid.ticks_per_beat, "tracks": len(mid.tracks), "notes": notes, "forbidden_events": 0, "size_bytes": p.stat().st_size}


def parse_options(o: dict, allowed: list[str]) -> list[str]:
    result = []
    for name in allowed:
        if name in o and o[name] is not None:
            result.extend(["--" + name.replace("_", "-"), str(o[name])])
    return result


def make_effects(p: Path, preset: str) -> str:
    if preset not in PRESETS:
        raise ToolError("Unknown production style")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    dest = OUTPUT / (p.stem + ".effects42.json")
    i = 2
    while dest.exists():
        dest = OUTPUT / (p.stem + f"_{i}.effects42.json")
        i += 1
    run("effects42.py", [str(p), "--preset", preset, "--output", str(dest)])
    return str(dest)


def handle(name: str, o: dict) -> dict:
    if name == "list_profiles":
        data = json.loads((ENGINE / "style_profiles.json").read_text())
        return {"profiles": sorted(data["profiles"].keys()), "engines": ["v3", "v4", "v4.1"], "effects": PRESETS, "emotional_stages": EMOTIONS}
    if name == "cook_midi":
        engine = o.get("engine", "v4.1")
        if engine not in ("v3", "v4", "v4.1"):
            raise ToolError("Unknown engine")
        if not 40 <= float(o["bpm"]) <= 220 or not .75 <= float(o["minutes"]) <= 9:
            raise ToolError("BPM and minutes are out of range")
        if o.get("mode", "minor") not in ("minor", "major", "dorian", "mixolydian"):
            raise ToolError("Invalid mode")
        if o.get("arc") and any(s.strip() not in EMOTIONS for s in o["arc"].split(",")):
            raise ToolError("Unsupported emotional stage; see list_profiles")
        dest = output_path(o["title"])
        basic = ["profile", "harmony", "rhythm", "bass", "melody", "arrangement", "bpm", "minutes", "key", "mode", "seed"]
        opts = parse_options(o, basic)
        if engine == "v3":
            extra = parse_options(o, ["drums", "performance"])
            resp = run("midilab3.py", ["cook", *opts, *extra, "--output", str(dest)])
        elif engine == "v4":
            extra = parse_options(o, ["arc", "repetition", "instrument_detail"])
            resp = run("midilab4.py", ["cook", *opts, *extra, "--output", str(dest)])
        else:
            extra = parse_options(o, ["arc", "repetition", "instrument_detail", "style", "intensity", "drum_complexity", "drum_mode"])
            resp = run("midilab41.py", ["cook", *opts, *extra, "--output", str(dest)])
        info = run_audit(dest)
        result = {"midi_file": str(dest), "engine": engine, "audit": info, "engine_output": resp["summary"]}
        if o.get("production_style"):
            result["effects_file"] = make_effects(dest, o["production_style"])
        result["sidecar_files"] = sorted(str(p) for p in dest.parent.glob(dest.stem + ".*.json"))
        return result
    if name == "analyze_midi":
        p = input_path(o["path"])
        report = OUTPUT / (p.stem + ".analysis.json")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        resp = run("midilab3.py", ["analyze", "--input", str(p), "--output", str(report)])
        return {"midi_file": str(p), "report": str(report), "audit": run_audit(p), "summary": resp["summary"]}
    if name == "advise_effects":
        p = input_path(o["path"])
        return {"midi_file": str(p), "effects_file": make_effects(p, o.get("preset", "tape_bliss"))}
    if name == "patch_textures":
        source = input_path(o["path"])
        dest = output_path(o["title"])
        if source == dest:
            raise ToolError("Output must differ from input for non-destructive patching")
        args = ["patch", "--input", str(source), "--output", str(dest)]
        args += parse_options(o, ["key", "mode", "style", "drum_mode", "intensity", "drum_complexity", "seed"])
        resp = run("midilab41.py", args)
        return {"midi_file": str(dest), "source_file": str(source), "audit": run_audit(dest), "summary": resp["summary"]}
    raise ToolError("Unknown tool " + name)


def dispatch(msg: dict) -> dict | None:
    method = msg.get("method")
    if method is None or "id" not in msg:
        return None
    msg_id = msg["id"]
    base = {"jsonrpc": "2.0", "id": msg_id}
    try:
        if method == "initialize":
            result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "midi-lab", "version": "1.0.0"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = msg.get("params", {})
            try:
                payload = handle(params.get("name", ""), params.get("arguments") or {})
                result = {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}], "isError": False}
            except (ToolError, ValueError, KeyError, subprocess.TimeoutExpired) as ex:
                result = {"content": [{"type": "text", "text": str(ex)}], "isError": True}
        else:
            return {**base, "error": {"code": -32601, "message": "Method not found"}}
        return {**base, "result": result}
    except Exception as ex:
        print("MIDI Lab MCP internal error: " + repr(ex), file=sys.stderr)
        return {**base, "error": {"code": -32603, "message": "Internal error"}}


def main():
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            output = dispatch(msg)
            if output is not None:
                sys.stdout.write(json.dumps(output, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("Ignoring malformed MCP input", file=sys.stderr)

if __name__ == "__main__":
    main()
