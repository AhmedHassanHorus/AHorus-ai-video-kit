---
name: arabic-tts
description: Production playbook for Egyptian-Arabic voiceover generation with VoiceTut-TTS (local GPU) and Edge-TTS (free online fallback). Covers the offline flat model layout, install with uv (no pip in the venv), pronunciation lexicon overrides, natural-delivery rules (one call per full sentence + crossfade), what the model cannot do (emotion/laughter/tone), whisper round-trip verification, and disk hygiene.
---

# Arabic TTS Production Skill (Egyptian dialect)

Two engines, one output contract: **48 kHz stereo 16-bit WAV + 192 kbps MP3, peak-normalised to 0.89**.
**VoiceTut-TTS** (local GPU, Egyptian-native) is primary; **Edge-TTS** (free, online) is the fallback.

> **Rule zero:** never install or download anything without the user's explicit approval. The commands
> below are the *reproduction recipe* — they are not permission to run them. Read `AGENTS.md §0` first.

Placeholders used in this file:

| Placeholder | Meaning |
|---|---|
| `<venv>` | the project's Python environment (`<venv>/Scripts/python.exe` on Windows, `<venv>/bin/python` elsewhere) |
| `<models>` | the local model directory, e.g. `~/.cache/video-models` |
| `<uv>` | path to the `uv` binary (only if the user agreed to use uv) |

---

## 1. Environment

The scripts in `scripts/` need: `numpy`, `ffmpeg` on `PATH`, and one TTS backend.

Recommended shape — **one shared venv** for transcription *and* TTS, because both want a CUDA torch:

| Thing | Recommended |
|---|---|
| Python | 3.11 (3.10–3.12 fine) |
| torch / torchaudio | a matching CUDA build for the user's driver (example pin: `2.6.0+cu124`) |
| transformers | **≥ 5.3.0** for VoiceTut/OmniVoice (it imports `HiggsAudioV2TokenizerModel`) |
| Package manager | `uv` if available — a uv venv has **no `pip` inside**, install with `uv pip install --python <venv>/Scripts/python.exe …` |
| VRAM | 4 GB class is enough for TTS *or* whisper, never both at once |

Always run generation with these environment variables, or the tools may silently reach the network:

```python
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows console is cp1252
```

Without the last line, printing Arabic raises `UnicodeEncodeError` and the run dies at the first log line.

---

## 2. VoiceTut-TTS — flat, offline model layout

Keep everything in **one directory** (`<models>/voicetut-model`, ~3.1 GB). Do **not** use the default
HuggingFace cache on Windows: it stores the blob *and* a snapshot copy, doubling disk use.

```
model.safetensors            ~2.3 GB   ← the weights; the only thing inference needs
tokenizer.json               ~11 MB
config.json / chat_template.jinja / scheduler.bin
reference_speakers/          ~20 MB    ← the built-in voices (wavs + references.json)
audio_tokenizer/             ~0.75 GB  ← eustlb/higgs-audio-v2-tokenizer (REQUIRED, see below)
```

- `optimizer.bin` (~4.7 GB) is **training-only** — skip it. It only lets you resume training; it has zero
  effect on inference. Downloading it is the classic wasted-gigabyte mistake.
- `audio_tokenizer/` is **not** part of the VoiceTut repo. `omnivoice` looks for
  `<model_dir>/audio_tokenizer` and, if missing, tries to download it at runtime. Putting it inside the
  model dir keeps the whole thing offline and self-contained.

### Install (reproduction recipe — ask first)

```bash
# 1) the thin wrapper (pulls only soundfile/cffi/pycparser)
uv pip install --python <venv>/Scripts/python.exe --no-cache -c constraints.txt voicetut-tts

# 2) the OmniVoice code WITHOUT deps first, so you choose them yourself
uv pip install --python <venv>/Scripts/python.exe --no-cache --no-deps \
    "git+https://github.com/k2-fsa/OmniVoice.git"

# 3) only the deps that are actually on the inference path
#    (skip gradio / webdataset / tensorboardX — training + web UI only)
uv pip install --python <venv>/Scripts/python.exe --no-cache -c constraints.txt \
    "transformers>=5.3.0" accelerate pydub librosa
```

```python
# 4) the weights (skip the training blob)
from huggingface_hub import snapshot_download
snapshot_download("mohammedaly22/VoiceTut-TTS",
                  local_dir="<models>/voicetut-model",
                  ignore_patterns=["optimizer.bin"])

# 5) the required audio tokenizer, INSIDE the model dir
snapshot_download("eustlb/higgs-audio-v2-tokenizer",
                  local_dir="<models>/voicetut-model/audio_tokenizer")
```

`constraints.txt` pins the shared packages so an install can never move them (torch, torchaudio, numpy,
einops). Install with `-c constraints.txt` every time.

### ⚠️ The transformers conflict (read before upgrading anything)

- VoiceTut/OmniVoice needs `transformers>=5.3.0`.
- `whisperx` declares `transformers==4.57.x` → installing VoiceTut **upgrades transformers and breaks
  whisperx**.
- This is harmless if you transcribe with **`faster-whisper` only** (`scripts/transcribe_words.py`):
  faster-whisper depends on `tokenizers`, not `transformers`. Verified working with transformers 5.x.
- Before touching a working environment, **copy the venv** (`<venv>.bak`) so recovery is a folder copy and
  not a re-install. A 5 GB copy is much cheaper than a broken machine.

---

## 3. Usage

```python
from voicetut_tts import VoiceTutTTS, GenerationParams

tts = VoiceTutTTS.from_pretrained("<models>/voicetut-model", device="cuda", dtype="float16")
tts.add_lexicon(LEXICON)                       # pronunciation overrides (see §5)

params = GenerationParams(num_step=32, guidance_scale=2.5, speed=0.95)
wav = tts.synthesize("...", speaker="<Name>", params=params)   # np.float32 @ 24 kHz
tts.sampling_rate  # 24000
```

- Voice selection: `speaker="<Name>"` for a built-in voice, `ref_audio=… (+ref_text=…)` for zero-shot
  cloning, `instruct="…"` for voice design. **Pick exactly one** — the engine raises if you combine them.
- Long text helpers: `tts.stream(text, …)` yields `(sr, chunk)` per sentence;
  `tts.synthesize_long(text, out, gap_ms=120, …)` streams and concatenates.

### Measured reference (4 GB laptop GPU, float16)

| Metric | Value |
|---|---|
| Model load | ~30 s |
| RTF | **≈ 1.2×** (60 s of speech ≈ 100 s wall-clock) |
| Peak VRAM | ~2.0 GB |
| Output | 24 kHz mono |

**Never run Whisper and TTS at the same time** — they will fight for VRAM and one of them OOMs.

Production script: **`scripts/tts_voicetut.py`** (writes `<out>.wav` 48 kHz stereo + `<out>.mp3`).

---

## 4. Delivery rules — how to not sound robotic

Hard-won; **do not regress these**:

1. **One generation call per FULL sentence.** Never pre-split a sentence into fragments and glue them:
   each call carries its own prosody, so the joins sound chopped and the meaning falls apart.
2. **Join with a crossfade** (`XFADE_MS = 60`), never a hard butt-splice.
3. **Do not trim tight** — `trim(thr=250, pad_ms=60)`. Cutting the natural decay is what makes speech feel
   "disconnected".
4. **Sentence pause 320–420 ms.** Internal sub-chunk pauses are unnecessary: captions are timed from
   whisper word timestamps, not from audio boundaries.
5. Output is 24 kHz mono → let **ffmpeg** do the single resample to 48 kHz stereo, then peak-normalise.
6. Do not compress or limit the TTS output before verification; judge the raw take.

---

## 5. Pronunciation control — `LEXICON`

The **only** reliable lever is respelling a word with **diacritics** (harakat), applied during
normalization via `tts.add_lexicon({...})`:

```python
LEXICON = {
    "كموجة": "كَمَوْجَة",     # was heard as "كمود"
    "كجسيم": "كَجُسَيْم",     # was heard as "ككسيم"
    "واحدة": "وَاحْدَة",
    "صغيرة": "صَغِيرَة",      # was heard as "غيره"
    "بتلف": "بِتْلِفّ",       # was heard as "بتلفت"
}
```

**Not bugs — correct Egyptian dialect:** `ذ → ز` («الذرة» → "الزر") and `ث → س` («ثابتة» → "سابتة"،
«أكثف» → "أكسف"). MSA-trained engines say these the MSA way; an Egyptian model says them the Egyptian way.
Also `جسيم` may be heard with a hard Egyptian `g`.

Preference that generalises: keep the script **plain** and fix only the words that actually fail — a fully
diacritised script was tried and rejected (it reads stilted and makes editing miserable).

---

## 6. What this model CANNOT do

**No emotion, tone, laughter, or crying.** There is no such channel.

The only style entry point is `instruct` (voice-design mode) and it is a **fixed whitelist** of speaker
attributes — one value per category, all optional:

| Category | Allowed values |
|---|---|
| Gender | `male`, `female` |
| Age | `child`, `teenager`, `young adult`, `middle-aged`, `elderly` |
| Pitch | `very low pitch`, `low pitch`, `moderate pitch`, `high pitch`, `very high pitch` |
| Style | `whisper` (the only one) |
| Accent | american, british, australian, canadian, indian, chinese, korean, portuguese, russian, japanese (English only) |
| Dialect | Chinese only |

- `instruct` is **mutually exclusive with `speaker`** (and with `ref_audio`).
- There is no Egyptian/Arabic accent option and no `[laugh]`-style non-verbal tags anywhere in the codebase.

### How to get expressiveness instead

1. **Zero-shot cloning from a reference clip with the energy you want** — delivery/prosody transfers, not
   just timbre. This is the strongest lever.
2. **Text cues:** written laughter (`هههههه`), interjections (`آآآه`), elongation (`طويييييل`), strong
   punctuation (`!!!` `؟؟؟`), short punchy sentences.
3. **`speed` / `duration`** knobs — pacing only (`duration` pins the exact output length).
4. **Post-FX in ffmpeg** — pitch / EQ / compression. Full, reliable control, no model cooperation needed.

---

## 7. Verification — always do a whisper round-trip

Never trust the text you sent; transcribe the produced audio and read what was actually said:

```bash
python scripts/transcribe_words.py --audio out/voice.wav --out out/verify.json --language ar
```

Whisper's hearing is also occasionally wrong — treat a single odd word as **suspicious, not conclusive**.
A listening judgement by the user outranks any transcript. Known Egyptian-dialect hallucinations:
«النقط دي» → "المؤدي", «الانحدار» → "الإنحضار". A leading English phrase may be dropped by Whisper even
when the TTS said it — listen to the audio before "fixing" anything.

### ⚠️ Takes are STOCHASTIC — never trust a single take or an isolated clip

`GenerationParams.class_temperature` is `0.0` (greedy), but `position_temperature=5.0` samples the unmask
positions with an **unseeded** `torch.rand_like`. No seed is exposed in the public API, so every full run
pronounces slightly differently. Observed: «مستقيم» came out «مستسقي» in one full take and perfect in the
next, while isolated A/B clips of the same word sounded fine. Rules:

- **Always verify the FULL voiceover** (transcribe it end to end). Never judge the pipeline by isolated
  clips — a clip that sounds good alone can scramble inside the full run.
- On a mispronounced word, **regenerate the full take first**. Only if it fails the same way twice, add a
  `LEXICON` entry. Never add lexicon entries from a single take.

---

## 8. Non-VoiceTut fallback — Edge-TTS

`scripts/tts_edge.py` — default `ar-EG-ShakirNeural`, `rate="+5%"`.

- Zero GPU, free, but requires **tashkeel + per-chunk scripting** to be usable.
- `ar-EG-SalmaNeural` has been rejected server-side ("No audio was received") — do not rely on it.
- Documented defects: `كموجة` → "كمود"; truncates word endings; garbles some sentences; can append junk at
  the end. Always A/B against the local model before shipping.
- Needs an internet connection and network retries (the script retries with backoff).

---

## 9. Disk hygiene

Download caches silently grow to many GB of redundant wheels and duplicated blobs.

```bash
uv cache clean                      # often several GB of unpacked CUDA wheels
python -m pip cache purge
```

When pulling HF repos prefer `snapshot_download(..., local_dir=...)` (a single flat copy) over the default
cache, and always pass `ignore_patterns=[...]` for training-only blobs.
