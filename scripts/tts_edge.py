#!/usr/bin/env python3
"""Voiceover generation with Microsoft Edge-TTS (free, no GPU, online).

Fallback engine. It is fast and free but noticeably weaker than a local
Egyptian-dialect model: it needs tashkeel (diacritics) to pronounce Arabic
properly and still truncates word endings and mangles some words. Use it when
you have no GPU or as an A/B reference.

Usage:
    python tts_edge.py --text script.txt --out out/voice --voice ar-EG-ShakirNeural --rate +5%

`script.txt` = one sentence per line (blank lines / # comments ignored).
Each line is synthesized in ONE call, then the lines are joined with a pause.

Requires: edge-tts, numpy, ffmpeg on PATH, and an internet connection.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
import tempfile
import wave

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np

SR = 48000
CHANNELS = 2


def silence(ms: int) -> np.ndarray:
    return np.zeros((int(SR * ms / 1000), CHANNELS), dtype=np.int16)


def trim(audio: np.ndarray, pad_ms: int = 50, thr: int = 180) -> np.ndarray:
    mono = np.abs(audio).max(axis=1)
    idx = np.where(mono > thr)[0]
    if len(idx) == 0:
        return audio
    pad = int(SR * pad_ms / 1000)
    return audio[max(0, int(idx[0]) - pad): min(len(audio), int(idx[-1]) + pad + 1)]


async def synth(edge_tts, text: str, voice: str, rate: str, tmpdir: str, tag: str, attempts: int = 5) -> np.ndarray:
    mp3 = os.path.join(tmpdir, f"v_{tag}.mp3")
    last = None
    for attempt in range(attempts):
        try:
            await edge_tts.Communicate(text, voice, rate=rate).save(mp3)
            if os.path.getsize(mp3) > 1000:
                break
            last = "empty file"
        except Exception as exc:  # network hiccups are common
            last = exc
        await asyncio.sleep(1.5 * (attempt + 1))
    else:
        raise RuntimeError(f"TTS failed ({last}) for: {text}")

    raw = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", mp3,
         "-f", "s16le", "-acodec", "pcm_s16le", "-ar", str(SR), "-ac", str(CHANNELS), "-"],
        capture_output=True, check=True,
    ).stdout
    return trim(np.frombuffer(raw, dtype=np.int16).reshape(-1, CHANNELS))


def read_script(path: str) -> list[str]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


async def run(args) -> int:
    import edge_tts

    sentences = read_script(args.text)
    if not sentences:
        print("error: empty script", file=sys.stderr)
        return 2

    print(f"Generating voiceover ({args.voice}, rate={args.rate}) ...", flush=True)
    with tempfile.TemporaryDirectory(prefix="edge_tts_") as tmpdir:
        pieces: list[np.ndarray] = []
        for i, sentence in enumerate(sentences):
            pieces.append(await synth(edge_tts, sentence, args.voice, args.rate, tmpdir, f"{i:03d}"))
            if i != len(sentences) - 1:
                pieces.append(silence(args.pause_ms))
            print(f"  [{i:02d}] {sentence[:60]}", flush=True)
    audio = np.concatenate(pieces)

    peak = float(np.abs(audio).max())
    if peak > 0:
        audio = np.clip(audio.astype(np.float32) * (args.peak * 32767.0 / peak), -32768, 32767).astype(np.int16)

    out_base = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_base) or ".", exist_ok=True)
    out_wav, out_mp3 = out_base + ".wav", out_base + ".mp3"
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(audio.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_wav,
                    "-c:a", "libmp3lame", "-b:a", "192k", out_mp3], check=True)

    print(f"Saved: {out_wav}")
    print(f"Saved: {out_mp3}")
    print(f"DURATION_SECONDS={len(audio) / SR:.3f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", required=True)
    ap.add_argument("--out", required=True, help="output basename, e.g. out/voice")
    ap.add_argument("--voice", default="ar-EG-ShakirNeural")
    ap.add_argument("--rate", default="+5%")
    ap.add_argument("--pause-ms", type=int, default=400)
    ap.add_argument("--peak", type=float, default=0.89)
    return asyncio.run(run(ap.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
