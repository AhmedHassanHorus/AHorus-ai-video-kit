# CLAUDE.md

**This file is a pointer. Do not duplicate content here.**

All rules, knowledge and pipelines live in one place:

> ### → [`AGENTS.md`](AGENTS.md) — read it before doing anything.

That file is the single source of truth. Specialised playbooks live in `.agents/skills/`.

The three rules you must never miss (full detail in `AGENTS.md`):

1. **Never install, download, clone or upgrade anything without the user's explicit approval** — including
   "tiny" packages, models, fonts and binaries. Ask with the exact command, then wait.
2. **Verify on rendered frames / probe output**, never by reading a screenshot or trusting an editor canvas.
3. **Arabic text must be rendered with real shaping** (libass / browser / NLE / compositor). Never PIL
   `draw.text()`. In ASS, every style needs `Encoding: -1`.
