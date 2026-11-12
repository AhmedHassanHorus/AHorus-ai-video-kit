---
name: motion-design
description: Rules and best practices for modern short-form motion design, TikTok/Reels kinetic typography, Pop-in animation dynamics, keyword color highlighting, and frame verification loops.
---

# Short-Form Motion Design & Kinetic Typography Skill

This skill guides the agent in designing high-retention motion graphics optimized for TikTok, Instagram Reels, and YouTube Shorts.

## 1. The 3-Second Hook Architecture

* **0–3s:** Bold visual change every 1.0 to 1.5 seconds.
* **Movement Rule:** Every time a new concept or sentence starts, trigger a subtle punch-in zoom (100% -> 115%) or introduce a kinetic visual badge.
* **No Dead Frames:** Natural pauses > 1.2s switch to an idle/thinking pose; pauses < 1.2s extend smoothly without nervous jitter.

## 2. Kinetic Typography Rules (TikTok Subtitle Style)

1. **Size & Weight:**
   * Font: Bold sans-serif (e.g., `Tahoma Bold`, `Montserrat ExtraBold`, `Inter Black`).
   * Size: `70px` to `80px` for 1080x1920 canvas.
2. **Chunking & Lines:**
   * Maximum 5–7 words per chunk (~2 to 2.5 seconds).
   * Balance into two centered lines (`\n`) of approximately equal visual width.
   * Never let text wrap awkwardly into single-word lines.
3. **Script direction (Arabic via libass/ASS):**
    * Author captions in **logical order** with style `Encoding: -1`, wrap by measured width in logical
      order, keep highlighted runs atomic in the wrap — **never pre-reverse Arabic words** (doing so
      scrambles multi-colour lines). Full mechanics: `AGENTS.md` §7 gotcha 1.
4. **Keyword Highlighting:**
    * Select the single most impactful word in the chunk (e.g., action verb, main subject, or emotional punchline).
   * Apply high-contrast highlight color:
     * Primary Text: Clean White (`#FFFFFF`)
     * Highlight Keyword: High-voltage Yellow (`#FFFF00` or `#FFE500`) or Cyan (`#00FFFF`)
   * Add high-contrast text stroke or dark card background to ensure readability over any background.

## 3. Pop-In Animation Dynamics (The Bouncy Overshoot)

When animating an icon, card, or text banner into view:
* **Frame 0:** Scale `0%`, Opacity `0%`
* **Frame 4:** Scale `115%`, Opacity `100%` (overshoot peak)
* **Frame 7:** Scale `98%` (slight bounce-back)
* **Frame 9:** Scale `100%` (settled state)
* Total entry duration: ~0.3 seconds (9 frames at 30fps).

## 4. Visual Frame Verification Loop

Never assume visual layout correctness without rendering a check frame:
1. Render a single headless frame at the middle timestamp of the element.
2. Verify:
   * Is the text inside safe vertical boundaries (not clipping under video UI)?
   * Are colors readable against the background character/scene?
   * Did any text box overflow?
