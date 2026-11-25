# Architecture and data flow

```
ChatGPT/Codex conversation
  ├─ skill: MIDI Lab composition instructions
  └─ MCP tools/list, tools/call (local stdio JSON-RPC)
         ↓
     server/mcp_server.py (Python stdlib, command validation)
         ↓
     engine/midilab3.py   original v3 composer and analyzer
     engine/midilab4.py   v4 emotional arcs / stable loops
     engine/midilab41.py  v4.1 bliss/fracture layering
     engine/effects42.py  v4.2 track-aware effects recommendation
         ↓
  ~/Music/MIDI Lab Outputs/*.mid + *.json
         ↓ (manual import)
     Logic Pro / other MIDI DAW
```

The MCP server uses Python's standard library for the protocol and subprocess invocation, with `mido` installed for MIDI parsing. Commands use argument lists, not shells. Outputs are restricted to a configurable output folder and sanitized titles; existing local MIDI inputs are explicitly user-supplied absolute paths. The server is **not** remotely hosted and has no authentication or network calls.

Supported protocol methods: `initialize`, `ping`, `tools/list`, `tools/call`. This lightweight local tool server deliberately omits other optional MCP resources/prompts/streaming features. Desktop host support is contingent on compatible stdio MCP execution and trust settings.

A plugin archive is not the same as a running tool server. The ChatGPT plugin account record and local server process are distinct. There is no claimed web/mobile ability to execute the bundled Python binary.

Test the engine via `python -m unittest discover -s engine/tests -p 'test_v*.py'`. Test the plugin protocol and orchestration via `python -m unittest discover -s tests -p 'test_*.py'`.

## File privacy

No telemetry, external API calls, or audio uploads. Compositions and effect recipes stay local unless you choose to share/upload them. There is no background job service.
