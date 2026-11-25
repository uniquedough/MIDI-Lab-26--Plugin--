# MIDI Lab Plugin v1.0.0

First installable ChatGPT plugin distribution of MIDI Lab **composition engine v4.2**. Includes the original v3/v4/v4.1 composers, 27 taste profiles, the v4.2 Effects Advisor, a Python local MCP tool server, and a skill for `/cook` requests. MIDI outputs remain separate named Type-1 / 480 PPQ tracks with no program/bank change events.

**Installation:** Python 3.10+, `pip install -r requirements.txt`, install the plugin ZIP in a compatible ChatGPT/Codex local-MCP host. The bundled stdio server is **not** cloud-hosted and the plugin cannot execute local Python in a normal web/mobile chat without compatible tooling.

**Validation:** see the GitHub Actions CI workflow and local test instructions in README.

**Not included:** Audio rendering, automatic Logic effect insertion, and the proposed v4.3 sound-first composition engine.
