---
name: remotion-motion
description: Programmatic React video creation and motion graphics using Remotion. Use when creating animated UI cards, spring physics animations, data charts, kinetic layouts, and exporting transparent WebM/MP4 videos for overlays.
---

# Remotion Motion Graphics & Video Skill

This skill teaches agents how to build, animate, and render programmatic video and motion graphics using **Remotion** (React + TypeScript).

## 1. Core Architecture

Remotion treats video as React components where animation is driven by the current frame index:
* **Current Frame:** `const frame = useCurrentFrame();`
* **Video Metadata:** `const { fps, durationInFrames, width, height } = useVideoConfig();`
* **Interpolation:** `interpolate(frame, [startFrame, endFrame], [startValue, endValue], { extrapolateRight: 'clamp' })`

## 2. Spring Physics (The Secret to Natural Motion)

Always prefer `spring()` over linear interpolation for UI cards, badges, and pop-in animations:

```tsx
import { spring, useCurrentFrame, useVideoConfig } from 'remotion';

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

// Smooth bouncy entrance (damping: 12 is bouncy, 16 is subtle)
const scale = spring({
  frame,
  fps,
  config: {
    damping: 12,
    mass: 0.5,
    stiffness: 100,
  },
});

// Use directly in style: transform: `scale(${scale})`
```

## 3. Short-Form Vertical Layouts (9:16 TikTok / Reels / Shorts)

* **Dimensions:** `width={1080}` and `height={1920}`
* **FPS:** Standard `30` or `60`
* **Safe Margins:**
  * Keep key text and cards between `Y: 300px` (avoid top UI) and `Y: 1550px` (avoid bottom caption/action UI).
  * Center X: `540px`. Maximum card width: `920px` (80px horizontal padding).

## 4. Transparent Alpha Video Rendering (Overlays)

To create motion graphics designed to be placed above a video track in an NLE (like FilmCraft):
1. Keep the root background transparent (`style={{ backgroundColor: 'transparent' }}`).
2. Render using WebM VP9 or ProRes 4444 with alpha:
   ```bash
   npx remotion render src/index.ts <CompositionName> out/overlay.webm --codec=vp9 --transparent
   ```

## 5. Audio Synchronization

* Calculate frames from speech timestamps:
  `frameNumber = Math.round(seconds * fps)`
* Trigger entry springs when `frame >= entryFrame`.
