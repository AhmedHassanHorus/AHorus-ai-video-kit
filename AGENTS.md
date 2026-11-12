# AI Video Studio Kit — Agent Handbook

**Read this whole file before you touch anything.** It is the single source of truth for how to work in
this repository. `CLAUDE.md`, `GEMINI.md` and similar files are only pointers to this document — do not
duplicate content into them.

This kit is tool- and vendor-agnostic: any coding agent (Claude Code, Codex, Gemini CLI, opencode,
Cursor, Aider, …) can follow it. Skills live in `.agents/skills/` in the standard `SKILL.md` format.

---

## 0. The rule that overrides every other rule

> ### 🚫 NEVER INSTALL, DOWNLOAD, CLONE, OR UPGRADE ANYTHING WITHOUT THE USER'S EXPLICIT APPROVAL.
>
> Not a package, not a model, not a font, not a binary, not a repo, not a "tiny" utility. **Ask first, every
> time, with the exact command you intend to run.** Silence is not approval. "It's free" is not approval.
> "It's just 50 MB" is not approval. A previous approval for one package does not cover the next one.

Why this is absolute:

- The user may be on a metered connection, a locked-down corporate machine, or a machine with almost no
  free disk. A 4 GB CUDA wheel set can cost them an hour and a full drive.
- Installs can **break a working environment** (a `transformers` upgrade silently breaks another tool that
  was fine yesterday — this has really happened; see §3.4).
- Downloading models from the internet may be **against the user's policy**, or the model may have a licence
  they do not accept.
- You cannot un-break a broken environment as easily as you can avoid breaking it.

### What needs approval

| Action | Approval? |
|---|---|
| `pip install`, `uv pip install`, `npm install`, `winget/choco/brew/apt install`, `cargo install` | **Yes — always** |
| Downloading a model, checkpoint, tokenizer, dataset, font, sample media, binary release | **Yes — always** |
| `git clone` of another repo, or adding a dependency to a manifest | **Yes — always** |
| `pip install --upgrade` / changing a pinned version in an existing environment | **Yes — always** |
| Installing a browser, driver, codec pack, or starting a server on a public port | **Yes — always** |
| Running tools that **already exist** on the machine (`ffmpeg`, `python`, `git`, the NLE CLI) | No |
| Reading files, writing files inside the project, running the project's own scripts | No |
| Creating a local virtualenv **with packages already present in the wheel cache** | Still ask — it may pull from the network |

### How to ask (use this shape, do not improvise)

```
I need <tool> to <reason>.
Command: <exact command, with versions pinned>
Size / time: <approx download + install time>
Reversible? <yes: how / no>
Alternatives: <e.g. run on CPU, use a smaller model, skip this step>
May I run it? (y/n)
```

Then **wait**. If the user says no, find a path that uses what is already installed, or stop and say what
is blocked.

### Hard no's even with approval

- Never install into the **system/global** Python. Use a project-local virtualenv (`.venv/`) or the venv
  the user already uses for this work.
- Never `sudo`, never edit `PATH` system-wide, never disable antivirus/firewall, never `--break-system-packages`.
- Never put credentials, tokens or cookies into a command line that will be logged, and never commit them.
- Never download from an unofficial mirror; prefer the project's official release page or PyPI/HuggingFace.

---

## 1. First run in a new environment (onboarding protocol)

A fresh machine usually has **none** of the optional tools. Do not assume; **detect first**, then report,
then ask. Follow the five steps in order.

### Step 1 — Detect (read-only, safe, no approval needed)

```bash
# core
python --version || python3 --version
git --version
ffmpeg -version | head -n 1
ffprobe -version | head -n 1

# optional / heavy
uv --version
node --version
nvidia-smi --query-gpu=name,memory.total --format=csv    # GPU present? how much VRAM?
pip list 2>/dev/null | grep -iE "faster-whisper|edge-tts|torch|numpy"
```

On Windows (PowerShell) the equivalents are `Get-Command ffmpeg`, `nvidia-smi`, `python --version`, etc.
Also check whether the machine is **offline** (`ping`/`curl` a known host) — it changes what is possible.

### Step 2 — Report what you found

Give the user one compact table: tool, present/missing, version, and what it blocks. Never start work by
"assuming ffmpeg exists" — half of the pipeline dies silently if it does not.

### Step 3 — Ask before installing anything

Use the §0 template. Offer a **minimum viable path** first (e.g. "you already have ffmpeg + python, so we
can do a silent-video pipeline today; the voiceover needs a model download of ~3 GB — do you want it?").

### Step 4 — Install only what was approved, only in a project-local environment

```bash
python -m venv .venv                 # or: uv venv
# Windows: .venv\Scripts\activate      POSIX: source .venv/bin/activate
pip install -r requirements.txt      # pin everything; no floating versions
```

- Prefer a **constraints file** for shared environments so an install can never move a working package:
  `pip install -c constraints.txt <pkg>`.
- Prefer `--no-deps` + explicit dependency list when a package pulls a huge training stack you do not need.
- After installing, **verify**: import it, print the version, run a 5-second smoke test.

### Step 5 — Record it

Append what you installed (name, version, reason, date) to `docs/LOCAL-SETUP.md` (create it, it is
git-ignored). The next agent — or the user in three months — will thank you.

### If something is missing and the user declines the install

Say exactly what is blocked and offer alternatives: CPU instead of GPU, a smaller model, an online service
the user already pays for, or a manual step the user can do themselves. **Never silently substitute** a
different tool or model for the approved one.

---

## 2. What is in this repo

```
.
├── AGENTS.md                  ← you are here (single source of truth)
├── CLAUDE.md / GEMINI.md      ← pointers only
├── README.md                  ← human-facing intro + quick start
├── docs/
│   ├── SETUP.md               ← per-OS install notes (each one gated by user approval)
│   └── TOOLCHAIN.md           ← the free toolchain, what each piece does, licence notes
├── scripts/
│   ├── tts_voicetut.py        ← local GPU TTS, one call per sentence + crossfade
│   ├── tts_edge.py            ← free online fallback TTS
│   ├── transcribe_words.py    ← word-level timestamps (faster-whisper)
│   ├── align_captions.py      ← map your caption texts onto real speech timing
│   └── make_cut.py            ← silence-based cut list
├── .agents/
│   ├── mcp_config.json        ← MCP server template (edit paths to your install)
│   └── skills/                ← craft playbooks (SKILL.md format, 25+ of them)
├── constraints.txt            ← shared pins (torch/numpy/…) — see §3.4
└── requirements.txt           ← the Python side of the pipeline
```

**Never commit media.** Rendered videos, frames, voiceovers, project files and model weights stay out of
git (see `.gitignore`). This repo is code + knowledge, not assets.

---

## 3. The toolchain (all free, all local where possible)

| Layer | Tool | Role | Notes |
|---|---|---|---|
| Voice | **VoiceTut-TTS** (Egyptian Arabic) or **Edge-TTS** | text → speech | see `.agents/skills/arabic-tts` |
| Words | **faster-whisper** (large-v3) | speech → word timestamps | the backbone of all caption timing |
| Clean-up | **DeepFilterNet** / any denoiser | remove hiss under speech | a gate cannot fix noise under speech |
| Assembly | any NLE with a CLI/MCP bridge, or **ffmpeg** | timeline / render | see `.agents/skills/craft-editor` |
| Motion | any AE-class compositor (EffectCraft) or Remotion/Manim | graphics | see `.agents/skills/effectcraft` |
| Glue | **ffmpeg / ffprobe** | every mux, resample, probe, frame grab | assume it is installed; verify anyway |

Golden rule: **the same content must be verifiable without watching the whole video.** Probe it: duration,
frame count, loudness, and a few extracted frames.

### 3.1 Model layout (offline-friendly)

If a model must be local, keep it in **one flat directory** (not the default HF cache, which stores the
blob twice on Windows):

```python
from huggingface_hub import snapshot_download
snapshot_download("<repo>", local_dir="<models>/<name>", ignore_patterns=["*.bin", "optimizer*"])
```

Then point the script at it explicitly (`--model <path>`), and run with `HF_HUB_OFFLINE=1`,
`TRANSFORMERS_OFFLINE=1` so nothing silently reaches the network.

### 3.2 VRAM discipline

Small laptop GPUs (4 GB class) fit **one** model at a time. Never run transcription and TTS concurrently;
load, generate, unload. If VRAM is short, prefer CPU for the cheap step rather than OOM-ing the expensive one.

### 3.3 Determinism

Some TTS/LLM backends sample without a seed. Two runs of the same text **will** differ. Therefore:

- Never judge a pipeline from one clip.
- Always verify the **full** take (transcribe it end-to-end), then regenerate if a word is wrong.
- Do not "fix" a word by adding pronunciation rules until it has failed twice in full runs.

### 3.4 Pinned environments

A single shared venv can host both transcription and TTS, but their dependency ranges can conflict
(classic case: one package wants `transformers>=5`, another pins `<5`). Keep a `constraints.txt` with the
versions that work, and install with `-c constraints.txt`. If an install wants to move a pinned package,
**stop and ask** — that is exactly the change that breaks a working machine.

---

## 4. Pipelines

### 4.1 Voice → words → captions → render

```bash
# 1. voiceover (one sentence per line in script.txt)
python scripts/tts_voicetut.py --text script.txt --out build/voice --model <models>/voicetut

# 2. word timestamps
python scripts/transcribe_words.py --audio build/voice.wav --out build/words.json --language ar

# 3. align your short on-screen captions to the real speech
python scripts/align_captions.py --words build/words.json --captions captions.txt --out build/timing.json

# 4. optional: silence-based cut list for an NLE
python scripts/make_cut.py --words build/words.json --out build/cuts.json

# 5. verify the take before building anything on top of it
python scripts/transcribe_words.py --audio build/voice.wav --out build/verify.json --language ar
```

Step 5 exists because **TTS lies**: it produces fluent audio that can still mispronounce a word. Read the
transcript, compare it with the script, and regenerate the full take when a word is off.

### 4.2 Driving an NLE / compositor through a CLI bridge

If the user's editing app exposes a control port (an "MCP"/bridge mode), prefer it over scripting the GUI:

- Start the app **with the port flag and the auth token in its environment** — a token mismatch shows up as
  `authentication failed` and the listener may never appear.
- Prefer the app's own CLI client: `app-cli run --commands file.jsonl --bridge 127.0.0.1:<port>`.
- Discover commands before using them (`app-cli commands`, `describe <id>`); never guess an id or a param.
- Every call is undoable and can be batched into one undo step.
- Long operations (exports) return a job id: poll the **output file** (size stable), not just job state.
- If the app is closed, ask before launching it — starting an app changes the user's screen.

### 4.3 Exporting long sequences

A 20-minute sequence exported in one pass can crash the app (or take an hour). The reliable recipe:

1. Export in **chunks** of ~3 minutes using an explicit time range.
2. Validate each chunk (`ffprobe -count_frames` equals expected frames).
3. Concatenate with `ffmpeg -f concat -safe 0 -i list.txt -c copy` — no re-encode.
4. Rebuild the **audio** separately from the source wav rather than concatenating AAC chunks (avoids
   encoder-priming gaps at the joins).
5. Mux: `-c:v copy -c:a aac -b:a 320k -movflags +faststart`.

Choose quality by **CRF**, not by a fixed bitrate: static/screen content compresses far smaller at the
same visual quality. CRF 18–20 at 1080p is a good master range; verify with a spot frame, not by eyeballing
the file size.

---

## 5. Craft rules that are not negotiable

These cost hours to learn. Break them and the result is subtly wrong in a way that is hard to see.

### 5.1 Arabic / RTL text

- **Never** draw Arabic with a library that lacks HarfBuzz shaping (e.g. PIL `draw.text()` on Windows): the
  letters come out disconnected and reversed. Use a renderer with shaping (libass, a browser, an NLE, or a
  compositor with proper text layout).
- In **ASS/libass** subtitles: set `Encoding: -1` on every style. With the default `Encoding: 1`, libass
  reorders each same-style run separately, so any line with a colour change renders with swapped blocks.
  Also keep `Spacing: 0` — positive letter spacing breaks Arabic ordering in some builds.
- Author text in **logical order**; never pre-reverse words. Wrap lines yourself by measured pixel width
  (`WrapStyle: 2`), breaking only between logical units.
- ASS colours are `&HAABBGGRR` (**BGR**, not RGB). A wrong channel order silently swaps yellow and cyan.
- A colour reset (`{\c}`) must be followed by a space, otherwise the reset is swallowed and the rest of the
  line stays highlighted.
- In compositors that lay out a mixed Arabic/Latin line with an LTR paragraph base, the **word order flips**
  (the glyphs are fine). Wrap the string in `RLE … PDF` (`\u202B … \u202C`) to force an RTL base.
- Trailing punctuation (`!`, `؟`) lands on the visual right; author it logically first.
- **Never judge Arabic from a thumbnail.** Crop the text line and upscale it, or better: verify against the
  rendered frame with a word-level template match.

### 5.2 On-screen text and layout

- Any sentence must sit on **something** — a plate/bar/card, or a genuinely clean area of the frame. Bare
  glyphs over detailed artwork are unreadable, and that is the most common complaint from viewers.
- Choose the layout **per beat**: full-bleed, lower third, bottom strip, side column, corner chip, centred
  title card. A single template repeated for ten minutes is the failure mode; variety is the point.
- Keep a consistent type hierarchy even when the position changes, keep ~60 px safe margins, and never put
  text over the presenter's face.
- Fewer, denser beats beat one caption per sentence. If a beat has nothing to say visually, cut it.

### 5.3 Audio

- Deliver 48 kHz stereo, 16-bit. Peak-normalise the voiceover (~0.89) before muxing.
- Target **−16 LUFS integrated** (YouTube normalises to −14; being slightly under is safer than over).
  Check true peak ≤ −1 dBFS.
- A noise gate only helps **between** phrases. Hiss under speech needs a real denoiser.
- Always verify loudness on the **final** file (`ffmpeg -af ebur128`), never on the intermediate.

### 5.4 Verification loop

Every visual claim must be checked on a **rendered frame**, not in the editor's canvas and not in a
screenshot you "read". Cheap and reliable:

```bash
ffmpeg -ss <t> -i out.mp4 -frames:v 1 frame.png
ffprobe -v error -show_entries format=duration,bit_rate:stream=nb_frames,r_frame_rate -of default=nw=1 out.mp4
ffmpeg -hide_banner -i out.mp4 -af ebur128=peak=true -f null -
```

Contact sheets (`ffmpeg -vf "fps=1,scale=320:-1,tile=6x4"`) let you review a whole minute in one image.
`blackdetect` is useful but **false-positives on intentionally dark designs** — look at the frame before
calling it a bug.

---

## 6. Skills

`.agents/skills/` holds craft playbooks in `SKILL.md` format (YAML front-matter with `name` +
`description`, then the body). Load one when the task matches its description:

- **production**: `arabic-tts`, `video-automation`, `craft-editor`, `effectcraft`
- **motion craft**: `animation-principles`, `motion-art-direction`, `kinetic-typography`,
  `motion-background`, `color-motion`, `logo-animation`, `shot-composition`, `beat-sync-editing`
- **formats**: `explainer-video`, `short-form-video`, `caption-animation`, `lower-thirds`,
  `countdown-video`, `wrapped-video`, `diagram-animation`, `whiteboard-animation`, `isometric-animation`
- **renderers**: `remotion-video`, `remotion-motion`, `manim-animation`, `after-effects`, `motion-design`

Third-party skills are MIT-licensed; see `CREDITS.md`. When you learn something new, update the relevant
`SKILL.md` (or `AGENTS.md` if it is a rule, not a technique) — a lesson that lives only in a chat is a
lesson lost.

---

## 7. Hygiene

- **Never commit**: media (`*.mp4`, `*.mov`, `*.wav`, `*.png` frames), project files (`*.fcproj`,
  `*.ecproj`, `*.prproj`), model weights, tokens, `docs/LOCAL-SETUP.md`, `.venv/`.
- **No absolute paths in scripts.** Take them as arguments, or resolve them relative to the repo. If a
  script needs a machine-specific path, read it from an env var with a documented default.
- **No personal data in this repo** — no names, no machine paths, no account ids, no tokens. Check
  `git diff` before every commit.
- Keep commits small and describe the *why*.

---

## 8. Working with the user

- **Do not fabricate content on screen.** If the video says "model X is 50 MB", the frame must show model X,
  not a different project's page. False claims get caught.
- **Never kill a long-running job** (render, export, download) without asking.
- **Do not start expensive work** (a full render, a full transcription) without saying roughly how long it
  will take.
- Report what changed in one short list: files touched, what was verified, what is still open.
- If you are unsure about a decision that affects the user's own edit (timing, cuts, wording), **ask** — or
  read their intent from the project and report your reading, without "fixing" it.
