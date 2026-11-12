# SETUP — per-OS install notes

> **Every command on this page requires the user's explicit approval before it runs.**
> Present the command, the size, the time, whether it is reversible, and the alternatives — then wait
> (`AGENTS.md §0`). This page is a *menu*, not an instruction to install everything.

Nothing here is mandatory. `AGENTS.md §1` tells you to **detect first**: a machine that already has
`ffmpeg`, `python` and an editing app can produce a silent-video pipeline today, with no downloads at all.

---

## 0. Detect what exists (safe, read-only)

```bash
python --version || python3 --version
git --version
ffmpeg -version | head -n 1
ffprobe -version | head -n 1
uv --version
node --version
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
```

```powershell
# Windows equivalents
Get-Command python, git, ffmpeg, ffprobe, uv, node -ErrorAction SilentlyContinue | Select-Object Name, Source
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
```

Report the result as a table (tool · present? · version · what it blocks) before proposing anything.

---

## 1. Core (needed by every pipeline)

### ffmpeg / ffprobe

| OS | Command | Size | Reversible |
|---|---|---|---|
| Windows | `winget install Gyan.FFmpeg` | ~120 MB | yes — `winget uninstall Gyan.FFmpeg` |
| macOS | `brew install ffmpeg` | ~80 MB + deps | yes — `brew uninstall ffmpeg` |
| Debian/Ubuntu | `sudo apt install ffmpeg` | ~60 MB | yes — `sudo apt remove ffmpeg` |

Verify: `ffmpeg -hide_banner -filters | grep -E "subtitles|ebur128"` (needs libass + ebur128 — the standard
builds have both). If `subtitles` is missing, Arabic caption burn-in is impossible with that build.

### Python 3.11 + a project-local venv

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      POSIX: source .venv/bin/activate
pip install -r requirements.txt -c constraints.txt
```

**Never install into the system/global Python.** If the machine is externally managed (PEP 668), the answer
is a venv, not `--break-system-packages`.

### git

Needed only if you want version control. Usually already present.

---

## 2. Voice

### A. Edge-TTS (online, no GPU) — the cheapest start

```bash
pip install edge-tts
```

Size ~1 MB, no model. Requires an internet connection at generation time. Quality on Arabic is usable but
noticeably weaker than a local dialect model (see `.agents/skills/arabic-tts §8`).

### B. VoiceTut-TTS (local GPU, Egyptian Arabic) — best quality

Needs: a CUDA-capable GPU (≥ 3 GB free VRAM), a CUDA torch build matching the driver, `transformers>=5.3.0`,
and **two model downloads (~3.1 GB total)**. Full reproduction recipe, model layout and the transformers
conflict: `.agents/skills/arabic-tts §2`.

Before installing: **copy the venv** if it is shared with other tools (`<venv>.bak`). A 5 GB copy is far
cheaper than a broken environment.

### C. Piper (local CPU, many languages, non-Arabic-friendly)

Good when there is no GPU and the language is well supported. Egyptian Arabic is not its strength.

---

## 3. Transcription

### faster-whisper (recommended)

```bash
pip install faster-whisper
```

Model: `large-v3` (~3 GB in float16). For GPU, a CUDA build of `ctranslate2` is required; on CPU use
`compute_type="int8"` and expect 3–8× realtime (fine for a 20-minute video, slow for hours of footage).

Download the model **once**, flat, and point the script at it:

```python
from huggingface_hub import snapshot_download
snapshot_download("Systran/faster-whisper-large-v3", local_dir="<models>/faster-whisper-large-v3")
```

Then run with `HF_HUB_OFFLINE=1` so nothing reaches the network again.

Alternatives: `whisper.cpp` (pure C++, no Python), `whisperx` (adds diarisation — but it pins an older
`transformers`, see `arabic-tts §2`).

---

## 4. Denoise / cleanup

| Option | Cost | Notes |
|---|---|---|
| DAW gate + EQ | free | Only cleans **between** phrases. Hiss under speech survives — a gate cannot remove what is louder than the gate. |
| DeepFilterNet (standalone binary) | ~26 MB download, CPU | Real denoiser; the release binary bundles the model. Use the delay-compensation flag so output stays aligned with your word timings. |
| Your NLE's built-in denoise | free | Check whether it has one before downloading anything. |

Always A/B the result **in the pauses** and **under speech**; report measured dB, not impressions.

---

## 5. Editing / motion (pick what you have)

| Tool | Role | Note |
|---|---|---|
| FilmCraft / DaVinci Resolve / Kdenlive / Shotcut | NLE | Prefer one with a CLI or bridge; GUI scripting is the last resort |
| EffectCraft / After Effects | compositor | AE-class expressions, keyframes, text layers |
| Remotion (React) | programmatic video | `npm install`, renders with headless Chrome |
| Manim | mathematical explainers | Python |
| ffmpeg alone | cuts, mux, burn-in, concat | no GUI needed at all |

The skill `craft-editor` covers the ArtCraft suite's bridge automation. If the user uses a different app,
the same principles apply: discover commands, never guess ids, poll the **output file** for long jobs.

---

## 6. MCP / bridge configuration

`.agents/mcp_config.json` is a **template**. Copy it into your agent's MCP config and edit the paths to the
user's install. Never commit a filled-in config with real paths.

```json
{
  "mcpServers": {
    "filmcraft":  { "command": "<install>/filmcraft-cli.exe",  "args": ["mcp"] },
    "effectcraft":{ "command": "<install>/effectcraft-cli.exe", "args": ["mcp"] }
  }
}
```

If the app exposes a live control port, the app must be started **with the flag and the auth token in its
environment**; otherwise the port never listens and clients fail with `authentication failed` or
`actively refused (os error 10061)`. Fall back to the app's own CLI when the MCP server misbehaves.

---

## 7. After installing — record it

Append to `docs/LOCAL-SETUP.md` (git-ignored):

```
2026-01-01  edge-tts 7.3.1   — fallback TTS, no GPU needed    — approved by user
2026-01-01  faster-whisper 1.2.1 + large-v3 (3.1 GB)          — word timings — approved by user
```

The next agent — or the user in six months — will need exactly this.
