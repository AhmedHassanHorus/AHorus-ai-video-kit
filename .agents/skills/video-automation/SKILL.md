---
name: video-automation
description: Automated video editing workflows, offline voiceover transcription, word-level audio alignment, silence detection, cut-point generation, and timeline assembly.
---

# Video Editing Automation & Assembly Skill

This skill defines automated procedures for taking raw audio/footage and assembling a polished video timeline.

## 1. Speech Transcription & Word-Level Timing

* **Model:** Run local offline `faster-whisper-large-v3` with float16 on GPU.
* **Environment Flags:** Always run with `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `PYTHONUTF8=1`.
* **Output:** Word-level timestamps JSON (`start`, `end`, `word`).

## 2. Smart Cut Points & Jitter Prevention

1. **Pre-Speech Buffer:** When cutting to speech, start `0.05s` to `0.1s` before the first phonetic sound to prevent clipping consonants.
2. **Post-Speech Buffer:** Leave `0.15s` to `0.25s` after the final word before switching to the next pose or cut.
3. **Short Pauses (< 1.2s):** Extend the previous active character pose across the gap to prevent jittery flipping back and forth to idle.
4. **Long Pauses (>= 1.2s):** Switch to neutral or thinking idle pose.

## 3. Dynamic Zoom Punch-Ins (Jump-Cut Cam)

To keep engagement high in static character or talking-head explainers:
* Alternate zoom on every visual cut / frame change:
  `Normal (100%) -> Zoom In (115%, center-cropped) -> Normal (100%) -> Zoom In (115%)`
* Export scale factors to the NLE timeline or render center-crop via FFmpeg filter `crop=w=in_w/1.15:h=in_h/1.15:x=(in_w-out_w)/2:y=(in_h-out_h)/2`.

## 4. Multi-Track Timeline Layering

Always organize timeline tracks logically:
* **Track V1:** Base character poses / primary camera footage.
* **Track V2:** Explainer motion graphics, floating cards, icons, and diagrams.
* **Track V3:** TikTok kinetic subtitles & animated text overlays.
* **Track A1:** Clean voiceover (16-bit 48kHz WAV).
* **Track A2:** Background music (ducked -18dB under speech).
* **Track A3:** Micro-SFX (whooshes, pops, clicks on graphic triggers).
