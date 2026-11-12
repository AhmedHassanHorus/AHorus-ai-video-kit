#!/usr/bin/env python3
"""Align caption texts to whisper word timestamps.

You write the captions (short, readable, on-screen phrasing — which is usually
NOT what the transcriber heard), and this maps each caption onto the real
speech using Needleman-Wunsch over normalized Arabic tokens. Output = one JSON
with `duration`, `captions[{start,end}]`, optional `chapters`.

Usage:
    python align_captions.py --words words.json --captions captions.txt --out timing.json
    python align_captions.py ... --chapters 0,4,8,12      # caption indices that start a chapter

`captions.txt` = one caption per line. Blank lines and #comments are ignored.
The order must follow the speech; a caption that finds no match is interpolated
between its neighbours (so a slightly different wording still gets sane times).

Requires: nothing beyond the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DIAC = re.compile("[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06dc\u06df-\u06e8\u06ea-\u06ed\u0640]")


def norm(token: str) -> str:
    """Strip diacritics and unify alef/ya/ta-marbuta variants, keep Arabic letters only."""
    t = DIAC.sub("", token)
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ٱ", "ا")
    t = t.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return re.sub("[^\u0600-\u06ff]", "", t)


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a[0] == b[0] and len(a) >= 2 and len(b) >= 2:
        return 0.55
    common = len(set(a) & set(b))
    return 0.5 * common / max(len(set(a)), len(set(b)))


def align(cap_tokens: list[str], wh_tokens: list[str], gap: float = 1.0) -> dict[int, int]:
    """Return {caption_token_index: whisper_token_index} for confident matches."""
    n, m = len(cap_tokens), len(wh_tokens)
    sim = [[similarity(cap_tokens[i], wh_tokens[j]) for j in range(m)] for i in range(n)]
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best = dp[i - 1][j - 1] + (1.0 - sim[i - 1][j - 1])
            dp[i][j] = min(best, dp[i - 1][j] + gap, dp[i][j - 1] + gap)

    i, j = n, m
    pairs: dict[int, int] = {}
    while i > 0 and j > 0:
        cost = 1.0 - sim[i - 1][j - 1]
        if abs(dp[i][j] - (dp[i - 1][j - 1] + cost)) < 1e-9:
            if sim[i - 1][j - 1] >= 0.5:
                pairs[i - 1] = j - 1
            i -= 1
            j -= 1
        elif abs(dp[i][j] - (dp[i - 1][j] + gap)) < 1e-9:
            i -= 1
        else:
            j -= 1
    return pairs


def read_lines(path: str) -> list[str]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n").strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--words", required=True, help="words JSON from transcribe_words.py")
    ap.add_argument("--captions", required=True, help="caption texts, one per line")
    ap.add_argument("--out", required=True)
    ap.add_argument("--chapters", default="", help="comma-separated caption indices that start a chapter")
    ap.add_argument("--lead", type=float, default=0.06, help="seconds before the first matched word")
    ap.add_argument("--tail", type=float, default=0.10, help="seconds after the last matched word")
    args = ap.parse_args()

    data = json.load(open(args.words, encoding="utf-8"))
    duration = float(data["duration"])

    wh_tokens, wh_start, wh_end = [], [], []
    for seg in data["segments"]:
        for w in seg.get("words", []):
            tok = norm(w["word"])
            if not tok:
                continue
            wh_tokens.append(tok)
            wh_start.append(float(w["start"]))
            wh_end.append(float(w["end"]))

    captions = read_lines(args.captions)
    if not captions:
        print("error: no captions", file=sys.stderr)
        return 2

    cap_tokens, owner = [], []
    for ci, text in enumerate(captions):
        for raw in text.split(" "):
            tok = norm(raw)
            if not tok:
                continue
            cap_tokens.append(tok)
            owner.append(ci)

    pairs = align(cap_tokens, wh_tokens)

    spans: dict[int, tuple[int, int]] = {}
    for cap_i, wh_i in pairs.items():
        ci = owner[cap_i]
        lo, hi = spans.get(ci, (wh_i, wh_i))
        spans[ci] = (min(lo, wh_i), max(hi, wh_i))

    times: list[list[float] | None] = [None] * len(captions)
    for ci, (lo, hi) in spans.items():
        times[ci] = [max(0.0, wh_start[lo] - args.lead), wh_end[hi] + args.tail]

    known = [i for i, t in enumerate(times) if t]
    for ci in range(len(times)):
        if times[ci]:
            continue
        prev = max([i for i in known if i < ci], default=None)
        nxt = min([i for i in known if i > ci], default=None)
        if prev is None and nxt is not None:
            times[ci] = [0.0, times[nxt][0] - 0.10]
        elif nxt is None and prev is not None:
            times[ci] = [times[prev][1] + 0.10, duration]
        elif prev is not None and nxt is not None:
            a, b = times[prev][1], times[nxt][0]
            times[ci] = [a + 0.05, max(a + 0.30, b - 0.05)]
        else:
            times[ci] = [0.0, duration]

    for ci in range(len(times) - 1):
        if times[ci][1] > times[ci + 1][0] - 0.06:
            times[ci][1] = times[ci + 1][0] - 0.06
    times[-1][1] = min(times[-1][1], duration)

    chapters = []
    if args.chapters.strip():
        idx = [int(x) for x in args.chapters.split(",") if x.strip()]
        idx = [i for i in idx if 0 <= i < len(times)]
        if idx and idx[0] != 0:
            idx.insert(0, 0)
        for k, ci in enumerate(idx):
            start = 0.0 if k == 0 else times[ci][0]
            end = times[idx[k + 1]][0] if k + 1 < len(idx) else duration
            chapters.append({"start": round(start, 3), "end": round(end, 3)})

    out = {
        "duration": round(duration, 3),
        "captions": [{"start": round(s, 3), "end": round(e, 3)} for s, e in times],
        "chapters": chapters,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    matched = sum(1 for ci in range(len(captions)) if ci in spans)
    print(f"Wrote {args.out}")
    print(f"duration={duration:.3f}  captions={len(captions)}  matched={matched}")
    for ci, text in enumerate(captions):
        flag = " " if ci in spans else "?"
        print(f"{flag} {ci:2d} [{times[ci][0]:6.2f} -> {times[ci][1]:6.2f}] {text}")
    if chapters:
        print("chapters:", chapters)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
