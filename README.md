# AI Video Studio Kit

A free, local-first AI video production kit for coding agents: **voiceover → word timestamps →
caption timing → cuts → assembly/render**, plus 26 craft skills (motion design, typography, editing,
compositing, explainers, short-form, …) that any agent can load on demand.

No subscriptions, no cloud rendering, no vendor lock-in. Every layer has a free option and most of them run
fully offline on a normal laptop.

> **This repo is code + knowledge only.** No media, no model weights, no project files.

---

## Who this is for

You have an editing app, a GPU (or not), and you want an agent to actually *do* the work: write the script,
generate the voice, time the captions, cut the timeline, animate the graphics, export the master.

The kit is **agent-agnostic** — Claude Code, Codex, Gemini CLI, opencode, Cursor, Aider, or your own harness.
The rules live in [`AGENTS.md`](AGENTS.md); other agent files (`CLAUDE.md`, `GEMINI.md`, …) are pointers to it.

---

## Start here (in this order)

1. **Read [`AGENTS.md`](AGENTS.md).** It is the single source of truth: the no-install-without-approval rule,
   the first-run detection protocol, the toolchain, the pipelines, and the craft rules that are not negotiable.
2. **Point your agent at the repo.** Most harnesses read `AGENTS.md` automatically. If yours does not, add a
   line to its config (`"read AGENTS.md first"`) or copy `CLAUDE.md` / `GEMINI.md` if that is the filename it
   looks for.
3. **Run the detection step** (`AGENTS.md §1`) so the agent reports what is already installed instead of
   assuming. Nothing gets installed without your explicit approval — that is a hard rule, not a preference.
4. **Pick a pipeline** (`AGENTS.md §4`) and load the matching skill from `.agents/skills/`.

---

## The five scripts

Generic, path-agnostic, no personal data, no hard-coded directories.

| Script | What it does |
|---|---|
| `scripts/tts_voicetut.py` | Local GPU Egyptian-Arabic TTS — one call per full sentence + crossfade (the natural-sounding recipe) |
| `scripts/tts_edge.py` | Free online fallback TTS (Edge) with retries |
| `scripts/transcribe_words.py` | Word-level timestamps with faster-whisper (offline) |
| `scripts/align_captions.py` | Maps *your* short caption texts onto real speech timing (Needleman–Wunsch) |
| `scripts/make_cut.py` | Silence-based cut list from word timestamps |

```bash
python scripts/tts_voicetut.py --text script.txt --out build/voice --model <models>/voicetut-model
python scripts/transcribe_words.py --audio build/voice.wav --out build/words.json --language ar
python scripts/align_captions.py  --words build/words.json --captions captions.txt --out build/timing.json
python scripts/make_cut.py        --words build/words.json --out build/cuts.json
```

See [`scripts/README.md`](scripts/README.md) for the full contract of each one.

---

## Skills

`.agents/skills/` — 26 playbooks in the standard `SKILL.md` format (YAML front-matter + body). They teach
*craft*, not a specific app, so they port to whatever renderer you use.

- **production**: `arabic-tts`, `video-automation`, `craft-editor`, `effectcraft`
- **motion craft**: `animation-principles`, `motion-art-direction`, `kinetic-typography`,
  `motion-background`, `color-motion`, `logo-animation`, `shot-composition`, `beat-sync-editing`
- **formats**: `explainer-video`, `short-form-video`, `caption-animation`, `lower-thirds`,
  `countdown-video`, `wrapped-video`, `diagram-animation`, `whiteboard-animation`, `isometric-animation`
- **renderers**: `remotion-video`, `remotion-motion`, `manim-animation`, `after-effects`, `motion-design`

Third-party skills keep their original licences — see [`CREDITS.md`](CREDITS.md).

---

## Free toolchain at a glance

| Layer | Free options |
|---|---|
| Voice | VoiceTut-TTS (local, Egyptian Arabic) · Edge-TTS (online) · Piper (local, many languages) |
| Words | faster-whisper / whisper.cpp |
| Denoise | DeepFilterNet · any DAW gate+EQ (a gate cannot fix noise *under* speech) |
| Assembly | FilmCraft / DaVinci Resolve / Kdenlive / ffmpeg |
| Motion | EffectCraft / After Effects / Remotion / Manim / Rive |
| Glue | ffmpeg · ffprobe |

Details, pins and licence notes: [`docs/TOOLCHAIN.md`](docs/TOOLCHAIN.md). Install steps (each gated by your
approval): [`docs/SETUP.md`](docs/SETUP.md).

---

## Non-negotiables (short version)

- **Nothing is installed or downloaded without your explicit "yes".** Not a package, not a model, not a font.
- **Arabic is never drawn with an unshaped text API.** No PIL `draw.text()` — the letters come out
  disconnected and reversed. Use libass, a browser, an NLE, or a compositor with real shaping.
- **In ASS/libass subtitles every style needs `Encoding: -1`.** With the default, any line containing a colour
  change renders with its word blocks swapped.
- **Every visual claim is verified on a rendered frame**, not on a screenshot the agent "reads".
- **Layout is chosen per beat.** A single template repeated for ten minutes is the failure mode.

Full list with the *why*: `AGENTS.md §5`.

---

## Licence

Code: MIT. Skills: mixed, see `CREDITS.md`.
