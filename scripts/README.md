# scripts/

Five small, dependency-light scripts that cover the pipeline from text to cut list. They are deliberately
**generic**: no personal paths, no hard-coded project names, everything comes from arguments.

| Script | Input | Output | Needs |
|---|---|---|---|
| `tts_voicetut.py` | `script.txt` (one sentence per line) + a local model dir | `<out>.wav` (48 kHz stereo s16) + `<out>.mp3` (192 kbps) | `voicetut-tts`, numpy, ffmpeg, CUDA GPU |
| `tts_edge.py` | same script file | same outputs | `edge-tts`, numpy, ffmpeg, internet |
| `transcribe_words.py` | any audio/video file | `words.json` (segments + word timings) | `faster-whisper`, ffmpeg |
| `align_captions.py` | `words.json` + `captions.txt` | `timing.json` (per-caption start/end, optional chapters) | stdlib only |
| `make_cut.py` | `words.json` | `cuts.json` (silence-based segments) | stdlib only |

---

## tts_voicetut.py

```bash
python tts_voicetut.py --text script.txt --out build/voice --model <models>/voicetut-model \
    --voice Mohamed --speed 0.95 --pause-ms 400 --xfade-ms 60 [--lexicon lexicon.json]
```

- **One model call per full sentence** — do not pre-split sentences; each call carries its own prosody.
- Sentences are joined with a short **crossfade**, and the natural decay is kept (no tight trim).
- `--lexicon` takes `{"word": "وَرْد دِياكْرِيتِيكَال"}` — the only reliable pronunciation lever.
- Prints `DURATION_SECONDS=…` at the end so a caller can chain without re-probing.
- Writes mono 24 kHz internally, then one ffmpeg pass to 48 kHz stereo. Peak-normalised to `--peak 0.89`.

## tts_edge.py

```bash
python tts_edge.py --text script.txt --out build/voice --voice ar-EG-ShakirNeural --rate +5%
```

Same output contract as above. Retries with backoff (network hiccups are normal). Weaker Arabic: it needs
tashkeel and still truncates word endings — treat it as a fallback, not the target quality.

## transcribe_words.py

```bash
python transcribe_words.py --audio build/voice.wav --out build/words.json --language ar
python transcribe_words.py --audio video.mp4 --out words.json --device cpu --compute int8
```

JSON shape:

```json
{
  "language": "ar",
  "duration": 59.389,
  "segments": [
    { "start": 0.0, "end": 2.4, "text": "...",
      "words": [ { "word": " ...", "start": 0.0, "end": 0.31 } ] }
  ]
}
```

`--model-dir` points at a local snapshot (offline). Without it, `--model-size` lets faster-whisper resolve a
name — **which may download**. If the machine is offline and the model is missing, stop and ask the user.

## align_captions.py

```bash
python align_captions.py --words build/words.json --captions captions.txt --out build/timing.json \
    --chapters 0,4,9,14
```

Why this exists: the captions you want on screen are **not** what the transcriber heard. You write short,
readable phrasing; this aligns each caption to the real speech with Needleman–Wunsch over normalised Arabic
tokens (diacritics stripped, alef/ya/ta-marbuta unified) and interpolates any caption that finds no match.
A `?` in the printout means "interpolated, no confident match" — check those by ear.

`captions.txt` = one caption per line, in speech order. `--chapters` takes 0-based caption indices.

## make_cut.py

```bash
python make_cut.py --words build/words.json --out build/cuts.json --max-gap 0.40 --lead 0.08 --tail 0.12
```

Splits at pauses longer than `--max-gap`, drops standalone fillers (edit `FILLER_WORDS` for the language),
pads each phrase so nothing is clipped, and never lets two segments overlap. Feed it to your NLE or to a
renderer as the assembly plan.

---

## Conventions shared by all five

- `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at the top — Windows consoles are cp1252 and
  printing Arabic would otherwise raise `UnicodeEncodeError`.
- `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1` set by default, so nothing silently reaches the network.
- Output directories are created as needed; existing files are overwritten (`-y`).
- No absolute paths anywhere. If a path is machine-specific, it is an argument or an env var.
