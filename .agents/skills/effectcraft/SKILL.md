---
name: effectcraft
description: EffectCraft compositor playbook (After Effects 2026-class) and the AE → EffectCraft mapping. Use whenever working in EffectCraft via the MCP engine (execute_command / command_batch / batch / run_script) or the live bridge — comps & layers, text, shapes, cameras/3D, expressions & rigging, keyframes & interpolation, effects, masks, text animators/presets, and rendering/export. Also use it to translate the imported iart-ai motion skills (after-effects, kinetic-typography, explainer-video, short-form-video, …) from AE/Remotion/GSAP into EffectCraft commands.
---

# EffectCraft

EffectCraft is this project's **motion-graphics compositor** — an After Effects-class app. We composite the
motion scenes here and assemble them in **FilmCraft** (NLE); audio cleanup lives in **SoundCraft**. For the
FilmCraft/SoundCraft side and the full pipeline, use the **`craft-editor`** skill.

## What this build is (verified 2026-10, v0.10.0)
- **Target:** Adobe **After Effects 2026 (26.5)**. Parity ≈ **91 % feature breadth** (alpha stage).
- **Effects:** **307 registered** (280 GPU) — *every* AE effect is present. `list_effects` (MCP) / `effect.list`.
- **Expressions:** full AE expression API (see §3). **Scripting:** AE-style `.jsx`/JS object model.
- **Export:** h264, hevc, av1, prores, uncompressed, webm, png/jpeg/tiff/exr sequences, gif, wav, aiff.
- **Also:** Lottie import/export, OCIO/ACES color management, Premiere/FCPXML/OTIO/EDL/AAF interchange,
  3D models (.gltf/.glb/.obj/.stl/.fbx) + cameras/lights, Classic & Advanced 3D.

## 1. How to drive it (MCP `effectcraft` server)
- **One command:** `execute_command {id, params}` (aka `command_run`). Discover ids with `command_list {filter}`;
  read exact params with `describe_command {command}`. `command_list {enabled_only:true}` shows `why` when a
  command can't run (usually "no composition is open").
- **Several, ordered:** `command_batch {steps}` (stops on error). **Atomic** (one undo, `$N` result refs):
  `batch {steps}`. Dedicated helpers: `set_property`, `add_keyframe`, `add_effect`, `get_property`, `get_layer`.
- **AE-style JS:** `run_script {code}` — `app.project`, `items.addComp`, `comp.layers.addText/addSolid`,
  `layer.property("ADBE Transform Group")`, `Effects.addProperty("ADBE Gaussian Blur 2")`, `setValueAtTime`,
  expressions, markers, `renderQueue`. Wrap with `app.beginUndoGroup/endUndoGroup`.
- **Check your work:** `render_frame` / `render_preview` (PNG; `max_side`, `path`, `time`, `transparent`).
  Read state: `get_state`, `get_project`, `get_comp`, `get_layer {flat:true}`, `doc_inspect`.
- **Live GUI (optional):** start the app `effectcraft.exe --control 17891`, then `screenshot` + `ui_*` tools.
  Without the bridge the engine still edits the document headless, but the MCP server needs the app running.
- **Undo:** `undo`/`redo`/`history`. Every edit is one undo step; `batch` groups them.

## 2. THE GOLDEN RULE — AE craft transfers, only AE-only tooling doesn't
We import the `iart-ai` motion skills (`after-effects`, `kinetic-typography`, `animation-principles`,
`beat-sync-editing`, `shot-composition`, `color-motion`, `logo-animation`, `motion-background`,
`explainer-video`, `whiteboard-animation`, `isometric-animation`, `diagram-animation`, `wrapped-video`,
`short-form-video`, `caption-animation`, `countdown-video`, `lower-thirds`, `remotion-video`). Read them, but
**translate to EffectCraft** with the map below:

| The skill says… | In EffectCraft do… |
|---|---|
| AE **expressions** / rigging (slider, null, pick-whip) | **Works as-is** — same language, same `ADBE …` names, same dimension checks. `prop.setExpression` / `set_property {expression}` / `prop.pickWhip`. |
| AE **keyframes** (hold / bezier / easy ease / overshoot) | `prop.addKey`, `keys.interpolation {interpolation: linear\|bezier\|continuousBezier\|autoBezier\|hold}`, `keys.setEase`, `keys.velocity`. |
| AE **text animators / per-char reveal** | `layer.addTextAnimator`, `layer.addTextSelector {kind: range\|wiggly\|expression}`, or a preset `layer.applyTextPreset {typewriter\|fadeUpCharacters\|bounceInWords\|trackingIn\|scramble\|blurIn\|jitter\|dropInLines}`. |
| AE **effect** by name | `effect.apply {effect: "Gaussian Blur", layers:[…]}` (AE name or `ec.*` id). |
| **GSAP / CSS / Framer Motion / Remotion** code | Rewrite as **EffectCraft keyframes or expressions** — there is no web runtime here. The *timing/easing numbers* (stagger ms, cubic-bezier) still guide the keyframe spacing. |
| AE **export via AME / MOGRT** | EffectCraft renders **in-app** — `renderQueue.add {format:"h264"}` (no Media Encoder). Lottie: `file.exportLottie`. |
| AE **RAM preview / Disk Cache / MFR** prefs | N/A. `render.backend {backend: gpu\|cpu}`; preview with `render_frame`. |
| AE **ExtendScript `.jsx`** | `run_script` (same object model) or `file.runScript {path}` / `{steps:[{command,params}]}`. |

## 3. Expressions (verified working — full AE API)
Language menu (`expr.languageMenu`) confirms these categories are present: Global (`comp`, `footage`,
`thisComp`, `thisLayer`, `time`, `value`, `posterizeTime`), Vector Math, Random (`seedRandom`, `random`,
`gaussRandom`, `noise`), Interpolation (`linear`, `ease`, `easeIn`, `easeOut`), Color (`rgbToHsl`, `hslToRgb`,
`hexToRgb`), Comp/Layer/Footage, **Property** (`value`, `valueAtTime`, `velocity`, `speed`, `wiggle`,
`temporalWiggle`, `smooth`, `loopIn`, `loopOut`, `loopInDuration`, `loopOutDuration`, `key`, `nearestKey`,
`numKeys`), **Path Property** (`points`, `createPath`), **Text** (`text.sourceText.style`, `getStyleAt`,
`textIndex`, `textTotal`, `selectorValue`), Key/Marker Key, Time Conversion (`timeToFrames`, `framesToTime`,
`timeToTimecode`…), Space Transforms (`toComp`/`fromComp`/`toWorld`), `sourceRectAtTime`, `sampleImage`.

Verified examples (all returned correct, time-varying values):
```js
wiggle(2, 30)                                              // position → jitters (t0 [941,540] … t2 [935,551])
thisComp.layer("Lead").transform.position.valueAtTime(time - 0.2 * index)   // staggered echo
time * 90                                                  // rotation → 90 @t1, 225 @t2.5
loopOut("cycle")                                           // opacity 0→50 keys: t0.5→25, t1.25→12.5, t2.75→37.5
seedRandom(index, true); 50 + random() * 50                // per-layer constant (same value at every t)
s = thisComp.layer("Lead").effect("Slider Control")("Slider"); [s, s, s]   // rig a 1-D slider onto 3-D scale
```
- **Dimension checking is AE-accurate:** a 1-D slider on `transform/scale` returns
  `expression result must be of dimension 3, not 1` — wrap as `[s, s, s]` (or `[s, s]` for 2-D).
- ⚠️ **`value` must be a NUMBER, not a string.** `prop.addKey {value:"0"}` → `bad value`; `{value:0}` works.
  Same for `set_property {value}` / `add_keyframe {keys:[{time,value}]}`.
- Errors surface in `expr.errors {comp?, time?}` (the error bar); `layer.revealExpressionErrors`.
- `prop.convertExpressionToKeyframes` bakes an expression; `layer.expressions {enabled}` toggles all.

## 4. Command cookbook (AE action → EffectCraft id)
**Project / comp:** `file.newProject`, `file.open`, `file.save` / `file.saveAs {path}` (⚠️ `file.save` errors
when the project has no path — use `saveAs`), `file.import {paths}`, `comp.new {name,width,height,frameRate,
duration,background,renderer?}`, `comp.settings`, `comp.open`, `comp.workArea`, `comp.addMarker`,
`comp.renderer {renderer: advanced3d|classic3d}`, `project.delete {items}`, `file.projectSettings` (bit depth,
OCIO/ACES, time display).

**Layers:** `layer.newText {text,name,position,box,font,style,size,fill,justify,direction,…}`,
`layer.newSolid {name,color,width,height}`, `layer.newNull`, `layer.newShape {kind: rect|rounded|ellipse|star|
polygon|none, size, fill, stroke, strokeWidth, position}`, `layer.newAdjustment`, `layer.addItem {item,…}`,
`layer.settings`, `layer.rename`, `layer.setBlendMode`, `layer.setParent {parent,compensate}`,
`layer.setTrackMatte {matte, kind}`, `layer.precompose`, `layer.arrange`, `layer.align` / `layer.distribute`,
`layer.nudge`, `layer.sequence {overlap,duration,transition}` (stagger + dissolve — kinetic stagger),
`layer.create {op: editableText|shapesFromText|masksFromText|shapesFromVector}`.

**Transform / timing:** `layer.setTransform {prop: anchor|position|scale|orientation|rotation|opacity, value}`,
`layer.transform {op: center|fit|fitWidth|flipH|flipV}`, `layer.centerAnchor`,
`layer.timing`, `layer.slip`, `layer.timeStretch`, `layer.timeReverse`, `layer.enableTimeRemap`,
`layer.freezeFrame`, `layer.autoOrient`, `keys.toggleTransform {prop}` (Alt+Shift+A/P/S/R/T).

**Masks / shapes:** `layer.addMask {shape, rect, mode}`, `layer.setMask`, `layer.mask.shape`,
`layer.mask.mode/invert/feather`, `shape.newPath {vertices,inTangents,outTangents,closed}`,
`shape.newShape`, `layer.addShapeItem {kind: rect|ellipse|star|polygon|path|fill|stroke|trim|repeater|round|
offset|pucker|twist|zigzag|wiggle|merge}`, `shape.fillStroke`, `shape.dashes.add`, `shape.stroke.taper`,
`shape.stroke.wave`, `path.groupShapes`/`ungroupShapes`, `edit.pasteSvg {svg}`.

**Effects:** `effect.apply {effect, layers}`, `effect.list {filter} → [{params:[{id,name,type,default,min,max}]}]`
(**read this to get a param's `id`**), `effect.remove`, `effect.toggle`, `effect.reorder`, `effect.duplicate`,
`effect.copy`/`effect.paste`, `effect.reset`, `effect.editDropdown`. Params are set with
`set_property {layer, path:"effects/#n/<paramId>", value}`; `add_effect {layer, effect, values}` applies+sets
in one step and returns the `effects/#n` path.

**Text (kinetic typography):** `layer.setText {layer, text, font, style, size, fill, tracking, leading, justify,
direction: ltr|rtl, composer, box, …}` (keeps the clip's timing), `text.edit`/`text.insert`/`text.setSelection`,
`layer.addTextAnimator {properties:[position,scale,rotation,opacity,fillColor,blur,tracking,characterValue,…]}`,
`layer.addTextSelector {kind: range|wiggly|expression}`, `layer.enablePerChar3D`,
`layer.applyTextPreset {typewriter|fadeUpCharacters|bounceInWords|trackingIn|scramble|blurIn|jitter|dropInLines}`,
`text.animatorProperties`, `text.presets`, `text.fonts {query}` / MCP `list_fonts`.

**Layer styles (no precomp needed):** `layer.style.add {style: dropShadow|innerShadow|outerGlow|innerGlow|
bevelEmboss|satin|colorOverlay|gradientOverlay|stroke}`, `layer.style.list`, `layer.style.remove/toggle`.

**3D / cameras / lights:** `layer.newCamera {type, preset, focalLength, dof, position, poi}`,
`layer.newLight {kind: Parallel|Spot|Point|Ambient|Environment, …}`, `layer.newModel {path|item}`,
`layer.new3dPrimitive {kind: cube|sphere|plane|torus|cone|cylinder}`, `layer.environment`,
`layer.cameraSettings`, `layer.lightSettings` (switching to a 3D layer sets the comp to Advanced 3D).

**Misc / data:** `layer.addMarker`, `keys.audioToKeyframes {comp}` (audio → keyframes),
`layer.alignVideoToData`, `layer.autoTrace`, `layer.sceneEditDetection`, `layer.newContentAwareFill`.

## 5. Keyframes & interpolation
- Add: `prop.addKey {layer, path, time, value}` or `set_property {…, time, value}`; `prop.toggleKey` at CTI;
  `keys.toggleTransform {prop}`. Time base: `timeBase: layer` (default) or `comp`.
- Interpolate: `keys.interpolation {interpolation: linear|bezier|continuousBezier|autoBezier|hold, in?, out?,
  spatial?, roving?}` (AE: F9 = Easy Ease). Finer: `keys.setEase {side, speed, influence}`,
  `keys.velocity {inSpeed, inInfluence, outSpeed, outInfluence, continuous}`.
- Move/edit: `keys.set {time, newTime, value}`, `keys.move {delta}`, `keys.nudge {frames}`,
  `keys.transform {timeScale,timeOffset,valueScale,valueOffset}`, `keys.timeReverse`, `keys.select`,
  `keys.delete`, `keys.copy`/`keys.paste`, `keys.pasteReversedKeyframes`.
- **Overshoot / pop-in** (from `motion-design`): 3 keys — scale 0 % → 115 % → 100 %, the middle key with
  `keys.interpolation {interpolation: bezier}` and a fast `keys.setEase` on the way in (~9 frames total).

## 6. Rendering & export
```jsonc
// add a job, then render in the background and poll the output file
{"id":"renderQueue.add","params":{"comp":"S1_Intro_v2","format":"h264","output":"…/scene1.mp4",
  "quality":"best","resolution":"full","timeSpan":"comp","audio":"off"}}
{"id":"renderQueue.render","params":{"wait":false}}
```
- `renderQueue.add` params: `format: h264|hevc|av1|prores|uncompressed|webm|png|jpeg|tiff|exr|gif|wav|aiff`,
  `output`, `quality`, `resolution: full|half|third|quarter|scale`, `timeSpan: workArea|comp|custom`,
  `start/end/duration`, `channels: rgb|rgba|alpha`, `bitrate`, `proresProfile`, `audio: auto|on|off`,
  `sampleRate`, `audioChannels`, `colorDepth`, `frameBlending`, `motionBlur`. Also `renderQueue.remove`,
  `renderQueue.list`, `renderQueue.stop`, `renderQueue.setOutputModule`, `renderQueue.templates`.
- **ProRes / alpha** for editor handoff & transparency; **h264** for delivery. H.264 cannot store alpha.
- **Frames/stills:** `comp.saveFrameAs {path:"…png", time}`, `comp.saveFrameAsPsd`, `comp.saveFrameAsExr`,
  `comp.copyFrame`. **Lottie:** `file.exportLottie {comp, path, includeExpressions, textAsShapes}`.
  **To the NLE:** `file.exportTimeline {path:"…xml", format: xml|fcpxml|otio|edl|aaf|omf}`.
- ⚠️ **Long renders:** the CLI/MCP call times out while the app keeps working → `renderQueue.render
  {wait:false}` and **poll the output file**. Queue renders go **comp-time**; a layer whose tail passes the
  comp end lengthens the output — keep it inside.
- Encoder is **quality-targeted** (a 1080×1920 30 fps 14.2 s h264 "best" ≈ 5.8 MB), not the nominal bitrate.

## 7. Gotchas (learned here — do not regress)
1. **Box-text anchor = the box CENTRE.** For `boxText=true` text, ink starts at
   `position.x − boxTextSize.width/2`. Read the doc via `run_script`
   (`layer.property("ADBE Text Properties").property("ADBE Text Document").value` →
   `.font/.fontSize/.justification/.boxText/.boxTextSize/.fillColor/.tracking`); it is **not** in the layer tree.
   `justification`: 7413 left / 7414 centre / 7415 right. (Cost hours on the `OPENAI` intro — see AGENTS §10c.)
2. **`value` is a number, not a string** (see §3). `"0"` → `bad value`.
3. **No ASS / libass here.** The old Arabic-subtitle tricks (AGENTS §7: `Encoding:-1`, pre-wrap by pixel width,
   ASS colour order) are for the retired ffmpeg pipeline — **not** EffectCraft. Text layers shape Arabic
   natively (HarfBuzz/FriBidi) with `direction: rtl`; just set the text and font — shaping and letter order
   are correct (verified in comp 484).
4. **⚠️ Trailing punctuation on Arabic text lands on the WRONG side.** EffectCraft lays the line out on an
   **LTR base**: the Arabic run itself renders correctly RTL (ة leftmost … م rightmost), but trailing
   neutrals (`!`, `؟`, `…`) are appended at the visual **right**, so an RTL reader sees them *before* the
   word (`مطرقعة!` displayed as `!` … then read `!مطرقعة`). **Fix (verified):** author the punctuation
   **logically first** — `!مطرقعة` renders as `[!][مطرقعة]` which reads `مطرقعة!` right-to-left. Same
   bug-family as libass per-run BiDi (AGENTS §7.1). Check rendered frames, not source text.
5. **Keyframing via the MCP tools:** `effectcraft_set_property` with `time`+`value` errors `bad value` even
   with numeric arrays — instead use `effectcraft_add_keyframe` with
   `keys:[{time,value},…]` (numbers only); keys at the same time **replace** existing ones in place, so it
   doubles as an editor. `execute_command prop.set` works for static values.
6. **`file.save` needs a path** → `file.saveAs {path}` for an unsaved project (the MCP project often has
   `path: null`). Rendering needs no save.
7. **Typewriter = keyframe the text, not a wipe.** Key `text/sourceText` on **Hold** through the prefixes
   (`""`, `O`, `OP`, … ) frame-aligned (~0.133 s/char ≈ 0.8 s total), and key the caret to each prefix's
   advance end + 8 px. Linear Wipe is not a reliable type-on. Or just use `layer.applyTextPreset {typewriter}`.
8. **Effects are referenced by AE name or `ec.*` id**; get a parameter's `id` from `effect.list {filter}`.
9. **`enabled:false` in `command_list`** means the action needs state (open a comp / select a layer first);
   `why` tells you what's missing.

## 8. See also
- **`craft-editor`** — FilmCraft NLE assembly, tick math, graphic captions, SFX placement/gain buses, SoundCraft
  audio (§9 EffectCraft text anchors, §10 FilmCraft SFX). Use it for the NLE/audio half.
- **`after-effects`** — the deep AE expression cookbook & rigging patterns (port as-is, §2).
- **`kinetic-typography`**, **`motion-design`**, **`animation-principles`** — timing/easing/reveal craft.
- **`explainer-video`**, **`whiteboard-animation`**, **`isometric-animation`**, **`diagram-animation`** — the
  explainer genre we ship.
