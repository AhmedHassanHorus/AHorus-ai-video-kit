# TOOLCHAIN — what each piece does, and what it costs

Every layer below has a **free** option. Nothing in this kit requires a subscription, a cloud account, or a
watermark.

| Layer | Free option(s) | Cost | GPU? | Offline? |
|---|---|---|---|---|
| Voice | VoiceTut-TTS, Edge-TTS, Piper | 0 | VoiceTut yes / Edge no / Piper no | VoiceTut & Piper yes |
| Transcription | faster-whisper, whisper.cpp | 0 | optional | yes, once the model is local |
| Denoise | DeepFilterNet, DAW gate+EQ | 0 | no | yes |
| Assembly | FilmCraft, Resolve, Kdenlive, Shotcut, ffmpeg | 0 | optional | yes |
| Motion | EffectCraft, After Effects, Remotion, Manim, Rive | 0 (AE: paid, not required) | optional | Remotion/Manim yes |
| Glue | ffmpeg, ffprobe | 0 | NVENC optional | yes |
| Agent | any coding agent | — | — | — |

---

## 1. Voice

**VoiceTut-TTS** — Egyptian-Arabic, fine-tuned from OmniVoice (Qwen3-0.6B backbone + a Higgs audio tokenizer)
on ~380 h of Egyptian podcast speech. Apache-2.0. Egyptian-native prosody, zero-shot cloning, ~2 GB VRAM.
Its only style control is a fixed `instruct` whitelist (gender × age × pitch × whisper) — no emotion, no
laughter. Read `.agents/skills/arabic-tts` before using it; the delivery rules (one call per sentence,
crossfade, no tight trim) are what make it sound human.

**Edge-TTS** — free Microsoft endpoint. No GPU, instant, but weaker Arabic: it needs tashkeel, truncates word
endings, and mangles some words. Good as an A/B reference and as a first-run path.

**Piper** — small local neural voices, CPU, very fast. Excellent for many languages, weak for Egyptian
Arabic.

Others worth knowing: Kokoro (fast, English-centric), XTTS v2 (cloning, multilingual), F5-TTS, Chatterbox.
Check the licence and the dialect before committing to one.

## 2. Transcription

**faster-whisper** (CTranslate2) is the practical default: `large-v3` on a 4 GB GPU with `float16`, or `int8`
on CPU. Word-level timestamps are the backbone of everything downstream — caption timing, cut points,
lip-sync checks.

`whisper.cpp` is the zero-Python option (GGML models, runs on CPU surprisingly well).

Rule: **word timestamps or nothing.** Sentence-level timestamps are not enough for karaoke-style captions or
for verifying that the TTS actually said the word you wrote.

## 3. Cleanup

A **noise gate** only acts where the signal is below threshold — i.e. between phrases. Hiss that sits *under*
speech passes straight through, and a peak-driven detector needs its threshold above the noise **peaks** to
do anything at all.

A real **denoiser** (DeepFilterNet, or a spectral-repair tool in a DAW) is the only thing that cleans under
speech. Measure before/after in dB in both conditions; "sounds better" is not a measurement.

Level the voice to **−16 LUFS integrated**, true peak ≤ **−1 dBFS** (YouTube normalises to −14; slightly
under is safer than over).

## 4. Assembly and rendering

Any NLE works. What matters for an agent:

- A **CLI or control bridge** (commands + params you can discover) beats GUI automation every time.
- Long exports are **chunked**: ~3-minute segments with explicit ranges, validated with
  `ffprobe -count_frames`, concatenated with `-c copy`, and the audio rebuilt from the source WAV.
- Quality is chosen by **CRF**, not by a fixed bitrate. Screen/static content compresses far smaller at the
  same perceptual quality. CRF 18–20 at 1080p is a good master range.
- `+faststart` for anything that will be streamed.

## 5. Motion

| Renderer | Best at | Trade-off |
|---|---|---|
| EffectCraft / After Effects | AE-class compositing, expressions, text animation | app dependency |
| Remotion | data-driven video, per-record templating, React | Node + headless Chrome |
| Manim | mathematical / technical explainers | Python, steep API |
| CSS / SVG / Canvas (browser) | lightweight loops, overlays | needs a capture step |

The skills in `.agents/skills/` describe technique in renderer-neutral terms and then give the specific
recipes (GSAP/Framer/Remotion/CSS/AE expressions). Port the idea, not the syntax.

## 6. Verification toolkit (ffmpeg one-liners)

```bash
# duration, bitrate, frame count, fps
ffprobe -v error -show_entries format=duration,bit_rate:stream=nb_frames,r_frame_rate,codec_name \
        -of default=nw=1 out.mp4

# loudness of the FINAL file (never the intermediate)
ffmpeg -hide_banner -i out.mp4 -af ebur128=peak=true -f null -

# one frame at t seconds
ffmpeg -ss 12.5 -i out.mp4 -frames:v 1 -y frame.png

# contact sheet: one minute per image
ffmpeg -i out.mp4 -vf "fps=1,scale=320:-1,tile=6x4" -frames:v 1 sheet.png

# burn subtitles (Windows path escaping matters: colons become \\:)
ffmpeg -i in.mp4 -vf "subtitles='C\\:/path/captions.ass'" -c:a copy out.mp4
```

`blackdetect` is useful but **false-positives on intentionally dark designs** — look at the frame before
calling it a bug.

## 7. Licence notes

- VoiceTut-TTS: Apache-2.0 · OmniVoice: Apache-2.0 · faster-whisper: MIT · CTranslate2: MIT
- Edge-TTS: MIT client, but the endpoint is Microsoft's service — check their terms for commercial use
- DeepFilterNet: MIT/Apache-2.0 (dual) · ffmpeg: LGPL/GPL depending on the build flags
- Remotion: company licence required above a small team size — check before shipping commercially
- The skills bundled here: MIT unless stated in `CREDITS.md`

When in doubt, **read the licence before the download**, not after the render.
