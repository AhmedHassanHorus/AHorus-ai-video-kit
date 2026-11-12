#!/usr/bin/env python3
"""Turn word timestamps into cut points (silence-based rough cut).

Splits the speech wherever the pause between two words exceeds --max-gap, drops
standalone filler words, and pads each phrase so nothing is clipped. Feed the
result to your NLE (or to a renderer) as the assembly plan.

Usage:
    python make_cut.py --words words.json --out cuts.json
    python make_cut.py --words words.json --out cuts.json --max-gap 0.45 --lead 0.10 --tail 0.15

Output: {"segments": [{start, end, text}], "total_segments", "total_duration"}
Requires: standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FILLER_WORDS = {
    # English
    "um", "uh", "erm", "ah", "like", "youknow",
    # Egyptian Arabic fillers (add/remove per dialect)
    "يعني", "اه", "اها", "امم", "بص", "طبعا",
}


def clean_word(word: str) -> str:
    return re.sub(r"[^\w]", "", word.lower()).strip()


def build_cuts(data: dict, max_gap: float, lead: float, tail: float) -> dict:
    words = []
    if data.get("word_segments"):
        words = data["word_segments"]
    else:
        for seg in data.get("segments", []):
            words.extend(seg.get("words", []))

    valid = [w for w in words if "start" in w and "end" in w]
    if not valid:
        raise SystemExit("no word timings found in the transcript")

    phrases: list[list[dict]] = []
    current: list[dict] = []
    for w in valid:
        is_filler = clean_word(w.get("word", "")) in FILLER_WORDS
        if not current:
            if not is_filler:
                current.append(w)
            continue
        gap = w["start"] - current[-1]["end"]
        if gap > max_gap:
            phrases.append(current)
            current = []
            if not is_filler:
                current.append(w)
        else:
            current.append(w)
    if current:
        phrases.append(current)

    segments = []
    for phrase in phrases:
        if not phrase:
            continue
        segments.append({
            "start": round(max(0.0, phrase[0]["start"] - lead), 3),
            "end": round(phrase[-1]["end"] + tail, 3),
            "text": " ".join(w.get("word", "").strip() for w in phrase).strip(),
        })

    # never let two segments overlap
    for i in range(len(segments) - 1):
        if segments[i]["end"] > segments[i + 1]["start"]:
            mid = round((segments[i]["end"] + segments[i + 1]["start"]) / 2.0, 3)
            segments[i]["end"] = mid
            segments[i + 1]["start"] = mid

    return {
        "segments": segments,
        "total_segments": len(segments),
        "total_duration": round(sum(s["end"] - s["start"] for s in segments), 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--words", required=True, help="words JSON from transcribe_words.py")
    ap.add_argument("--out", required=True, help="output cuts JSON")
    ap.add_argument("--max-gap", type=float, default=0.40, help="pause (s) that starts a new segment")
    ap.add_argument("--lead", type=float, default=0.08, help="padding before the first word")
    ap.add_argument("--tail", type=float, default=0.12, help="padding after the last word")
    args = ap.parse_args()

    data = json.load(open(args.words, encoding="utf-8"))
    cuts = build_cuts(data, args.max_gap, args.lead, args.tail)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(cuts, fh, ensure_ascii=False, indent=2)

    print(f"Generated {cuts['total_segments']} segments "
          f"({cuts['total_duration']}s total). Saved to {args.out}")
    for seg in cuts["segments"][:10]:
        print(f"  [{seg['start']:7.2f} -> {seg['end']:7.2f}] {seg['text'][:70]}")
    if len(cuts["segments"]) > 10:
        print(f"  ... {len(cuts['segments']) - 10} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
