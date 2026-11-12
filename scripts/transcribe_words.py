#!/usr/bin/env python3
"""Word-level transcription with faster-whisper (local, offline).

Produces the JSON that every later step depends on: sentence timing, caption
alignment and silence-based cutting all read word timestamps from here.

Usage:
    python transcribe_words.py --audio voice.wav --out words.json
    python transcribe_words.py --audio video.mp4 --out words.json --language ar --device cpu

Model: pass --model-dir for a local CTranslate2/whisper snapshot, or --model-size
to let faster-whisper resolve a name. If the machine is offline and the model is
not present, STOP and ask the user before downloading anything.

Requires: faster-whisper (+ a CUDA build of ctranslate2 for GPU), ffmpeg on PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("PYTHONUTF8", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio", required=True, help="audio or video file (ffmpeg-readable)")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--model-dir", help="local model directory (recommended for offline use)")
    ap.add_argument("--model-size", default="large-v3", help="used only when --model-dir is absent")
    ap.add_argument("--language", default="ar", help="ISO code, or 'auto' to detect")
    ap.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    ap.add_argument("--compute", default="float16", help="float16 (GPU) / int8 (CPU)")
    ap.add_argument("--min-silence-ms", type=int, default=400)
    ap.add_argument("--beam-size", type=int, default=5)
    args = ap.parse_args()

    from faster_whisper import WhisperModel

    model_ref = args.model_dir or args.model_size
    if args.device == "cpu" and args.compute == "float16":
        args.compute = "int8"

    print(f"Loading faster-whisper '{model_ref}' on {args.device}/{args.compute} ...", flush=True)
    model = WhisperModel(model_ref, device=args.device, compute_type=args.compute)

    segments, info = model.transcribe(
        args.audio,
        language=None if args.language == "auto" else args.language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=args.min_silence_ms),
        beam_size=args.beam_size,
    )

    data = {"language": info.language, "duration": round(float(info.duration), 3), "segments": []}
    for seg in segments:  # generator: transcription happens while iterating
        data["segments"].append({
            "start": round(float(seg.start), 3),
            "end": round(float(seg.end), 3),
            "text": seg.text.strip(),
            "words": [
                {"word": w.word, "start": round(float(w.start), 3), "end": round(float(w.end), 3)}
                for w in (seg.words or [])
            ],
        })
        print(f"  [{seg.start:7.2f} -> {seg.end:7.2f}] {seg.text.strip()[:70]}", flush=True)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    words = sum(len(s["words"]) for s in data["segments"])
    print(f"\nWrote {args.out}")
    print(f"language={data['language']}  duration={data['duration']:.3f}s  "
          f"segments={len(data['segments'])}  words={words}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
