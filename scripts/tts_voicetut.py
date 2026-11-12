#!/usr/bin/env python3
"""Voiceover generation with VoiceTut-TTS (Egyptian Arabic, local GPU).

One model call per FULL sentence, then a short crossfade between sentences,
then a single ffmpeg pass to 48 kHz stereo. This is the delivery recipe that
sounds natural; do not pre-split sentences or butt-splice the audio.

Usage:
    python tts_voicetut.py --text script.txt --out out/voice --model /path/to/voicetut-model

`script.txt` = one sentence per line (blank lines and lines starting with # are ignored).
Optional `--lexicon lexicon.json` = {"word": "وَرْد دِياكْرِيتِيكَال"} pronunciation overrides.

Requires: voicetut-tts, numpy, ffmpeg on PATH. The model directory must contain
model.safetensors + tokenizer + audio_tokenizer/ (see docs/TOOLCHAIN.md).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import wave

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("PYTHONUTF8", "1")

try:  # Windows consoles are cp1252; printing Arabic would raise otherwise
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np


def silence(ms: int, rate: int) -> np.ndarray:
    return np.zeros(int(rate * ms / 1000), dtype=np.int16)


def trim(audio: np.ndarray, rate: int, pad_ms: int = 60, thr: int = 250) -> np.ndarray:
    """Cut leading/trailing silence but keep the natural decay (pad_ms)."""
    idx = np.where(np.abs(audio) > thr)[0]
    if len(idx) == 0:
        return audio
    pad = int(rate * pad_ms / 1000)
    return audio[max(0, int(idx[0]) - pad): min(len(audio), int(idx[-1]) + pad + 1)]


def xfade(a: np.ndarray, b: np.ndarray, ms: int, rate: int) -> np.ndarray:
    n = min(int(rate * ms / 1000), len(a), len(b))
    if n <= 0:
        return np.concatenate([a, b]).astype(np.int16)
    fa = np.linspace(1.0, 0.0, n, dtype=np.float32)
    fb = np.linspace(0.0, 1.0, n, dtype=np.float32)
    head = a[len(a) - n:].astype(np.float32) * fa + b[:n].astype(np.float32) * fb
    return np.concatenate([a[: len(a) - n], head.astype(np.int16), b[n:]]).astype(np.int16)


def to_int16(wav) -> np.ndarray:
    return np.clip(np.asarray(wav, dtype=np.float32) * 32767.0, -32768, 32767).astype(np.int16)


def read_script(path: str) -> list[str]:
    lines = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", required=True, help="text file, one sentence per line")
    ap.add_argument("--out", required=True, help="output basename, e.g. out/voice -> voice.wav + voice.mp3")
    ap.add_argument("--model", required=True, help="VoiceTut-TTS model directory (local, offline)")
    ap.add_argument("--voice", default="Mohamed", help="built-in speaker name (default: Mohamed)")
    ap.add_argument("--speed", type=float, default=0.95)
    ap.add_argument("--num-step", type=int, default=32)
    ap.add_argument("--guidance", type=float, default=2.5)
    ap.add_argument("--pause-ms", type=int, default=400, help="pause between sentences (320-420 sounds natural)")
    ap.add_argument("--xfade-ms", type=int, default=60, help="crossfade between sentences")
    ap.add_argument("--lexicon", help="JSON file: {word: diacritized_spelling}")
    ap.add_argument("--peak", type=float, default=0.89, help="peak normalisation target (0-1)")
    args = ap.parse_args()

    from voicetut_tts import GenerationParams, VoiceTutTTS

    sentences = read_script(args.text)
    if not sentences:
        print("error: empty script", file=sys.stderr)
        return 2

    lexicon = {}
    if args.lexicon:
        with open(args.lexicon, encoding="utf-8") as fh:
            lexicon = json.load(fh)

    print(f"Loading VoiceTut-TTS ({args.voice}) from {args.model} ...", flush=True)
    tts = VoiceTutTTS.from_pretrained(args.model, device="cuda", dtype="float16")
    if lexicon:
        tts.add_lexicon(lexicon)
    params = GenerationParams(num_step=args.num_step, guidance_scale=args.guidance, speed=args.speed)
    rate = int(tts.sampling_rate)  # 24 kHz for VoiceTut

    pieces: list[np.ndarray] = []
    for i, sentence in enumerate(sentences):
        wav = trim(to_int16(tts.synthesize(sentence, speaker=args.voice, params=params)), rate)
        pieces.append(wav)
        if i != len(sentences) - 1:
            pieces.append(silence(args.pause_ms, rate))
        print(f"  [{i:02d}] {sentence[:60]}", flush=True)

    audio = pieces[0]
    for piece in pieces[1:]:
        audio = xfade(audio, piece, args.xfade_ms, rate)

    peak = float(np.abs(audio).max())
    if peak > 0:
        audio = np.clip(audio.astype(np.float32) * (args.peak * 32767.0 / peak), -32768, 32767).astype(np.int16)

    out_base = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_base) or ".", exist_ok=True)
    tmp_wav = out_base + ".src.wav"
    out_wav, out_mp3 = out_base + ".wav", out_base + ".mp3"

    with wave.open(tmp_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(audio.tobytes())

    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp_wav,
                    "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", out_wav], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_wav,
                    "-c:a", "libmp3lame", "-b:a", "192k", out_mp3], check=True)
    os.remove(tmp_wav)

    print(f"Saved: {out_wav}")
    print(f"Saved: {out_mp3}")
    print(f"DURATION_SECONDS={len(audio) / rate:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
