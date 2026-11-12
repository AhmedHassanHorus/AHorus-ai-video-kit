---
name: craft-editor
description: Integration guide and command automation for the ArtCraft suite — FilmCraft NLE, EffectCraft motion graphics, SoundCraft audio. Covers bridge execution, tick math (254016000000 ticks/sec), clip placement, graphic captions (verified recipe + gotchas), EffectCraft text anchors & typewriter effects, SFX placement/gain buses, transparent WebM alpha rendering, audio plugins, and export.
---

# ArtCraft Suite Production Skill (FilmCraft · EffectCraft · SoundCraft)

Exact automation workflows and technical rules for the **ArtCraft** creative suite on Windows AMD64.

## 1. Application Paths & Architecture

* **FilmCraft CLI:** `<install>\FilmCraft\filmcraft-cli.exe` (app: `filmcraft.exe`)
* **EffectCraft CLI:** `<install>\EffectCraft\effectcraft-cli.exe` (app: `effectcraft.exe`)
* **SoundCraft CLI:** `<install>\SoundCraft\soundcraft-cli.exe` (app: `soundcraft.exe`)

  `<install>` is the program-files directory — `C:\Program Files` by default on Windows. Confirm the real
  path with `Get-Command filmcraft-cli` before scripting; never assume it.
* **Live Bridge:** `--bridge 127.0.0.1:17890` (FilmCraft), EffectCraft used `127.0.0.1:17891`.
  * The **MCP server definitions must carry the flag too** (`opencode.jsonc` → `"--bridge","127.0.0.1:17890"` /
    `17891`), and opencode must be **restarted** after editing that file (it is not hot-reloaded).
  * Without the bridge, `filmcraft_ui_*` and `filmcraft-cli --bridge` fail with *"actively refused … os error
    10061"*. The MCP **engine commands still work headless** (the session holds the document), so edits, saves and
    exports are possible with the GUI closed — only live screenshots/clicks/scrubbing need the app running.
* **Invocation:**
  ```powershell
  & "<install>\FilmCraft\filmcraft-cli.exe" --bridge 127.0.0.1:17890 exec <command_id> "key=value" ...
  & "<install>\FilmCraft\filmcraft-cli.exe" --bridge 127.0.0.1:17890 run <batch.jsonl>
  & "<install>\EffectCraft\effectcraft-cli.exe" --bridge 127.0.0.1:17891 script <file.jsx>
  ```
* **Quoting (PS 5.1):** scalar params work as `key=value` arguments. Anything with arrays/objects must go through a
  **JSONL file** (`run`) or an **EffectCraft `.jsx` script** — `exec --params '{"a":[1,2]}'` gets mangled.
* **JSONL encoding:** must be **UTF-8 without BOM**. `Set-Content -Encoding UTF8` (PS 5.1) writes a BOM and the parser
  fails with `expected value at line 1 column 1`. Use
  `[IO.File]::WriteAllText($p,$s,(New-Object System.Text.UTF8Encoding($false)))`.
* **Client timeouts are harmless:** long renders/exports keep running in the app after the CLI call returns/times out —
  poll the output file instead of re-running.
* **Discover commands:** `<cli> commands [filter]`, `<cli> describe <id>`. Batch result lines are `{"id",...,"ok":true/false,"result":...}`.

## 2. Timing Units & The Tick Rule

* `1 Second = 254,016,000,000 Ticks`; `1 Frame @ 30fps = 8,467,200,000 Ticks`.
* `ticks = int(round(seconds * 254016000000))`; `frame_ticks = frame_no * 8467200000`.
* **Overlap prevention ("V3 is not free here"):** `seconds` **snaps to frames**, so a clip whose duration ends exactly
  where the next begins can still collide. Rule that works: align both ends to frames
  (`round(t*30)`), then **shorten every duration by 2 frames**:
  `frames = round(end*30) - round(start*30) - 2`, `time = round(start*30) * 8467200000`.

## 3. FilmCraft Graphic Captions (verified recipe)

Arabic renders correctly with no BiDi hacks (unlike the ASS/libass pipelines) — author **logical order** text.

1. **Create:** `graphics.newText`
   ```json
   {"text":"<Arabic>","position":[60,1500],"box":[960,340],"size":68,
    "font":"Tahoma","fontStyle":"Bold","seconds":<frames/30>,"track":2,"time":<frame*8467200000>}
   ```
   * `track: 2` = **Video 3** (video tracks are 0-based: 0=V1, 1=V2, 2=V3). Captions above the character go on V3.
   * `position` = the **box top-left** corner; text is **top-anchored** inside the box (no vertical-centre prop).
     `[60,1500]` + box `[960,340]` puts 1- and 2-line captions in the bottom zone (clear of scene content below ~1420).
   * Consumes **2 clip ids** per text (…, 74, 76, 78, …) — parse ids from the `run` output rather than assuming.
2. **Style:** `graphics.set {clip, layer:0, props:{fill_color:"#ffffff", stroke:true, stroke_width:6,
   shadow:true, align:"center", font:"Tahoma", font_style:"Bold", size:68}}`
3. **Keyword highlight:** `graphics.setCharStyle {clip, layer:0, start:<n>, end:<n>, style:{color:"#ffe600"}}`
   * Char indices are plain string offsets — **compute them in a script** (`text.find(word)`), never by hand.
   * Multiple `setCharStyle` calls per clip are fine (e.g. «ناعمة» + «خشنة»).
4. **Line budget:** Tahoma Bold 68 ≈ **25–28 chars/line** inside the 960 box. Keep caption text **≤ ~46 chars**
   (2 lines). Longer wraps to 3 lines with a hanging word — split such captions instead.
5. **Persist:** `exec file.save`.
6. **Edit a caption in place (verified):** `graphics.setText {clip, layer:0, text:<new text>}` rewrites the text
   and **keeps the clip's timing/motion**; then re-apply the highlights:
   `graphics.setCharStyle {clip, layer:0, start:0, end:<len>, clear:true}` followed by the new spans (indices
   into the *new* text, computed by `text.find`). `graphics.setText` shows `enabled:false` in `command_list`
   but works when given an explicit `clip`. Auto re-wrap can move the line break — **render the frame** to check.
7. **Re-export cost:** captions are burned into the export, so any caption edit forces a full
   `file.exportMedia` (~115 s for a 78.9 s film at crf 19). **Audio-only** changes can skip FilmCraft entirely:
   `ffmpeg -i final.mp4 -i new.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k out.mp4` (verify the
   video stream is untouched with `-map 0:v:0 -c copy -f md5 -` on both files).

## 4. Editing / Verification Commands (learned)

* **Delete a clip:** `edit.clear {clips:[id]}` (plain delete). `edit.rippleDelete` fails while any track is
  sync-locked (`"would break sync: V1 is sync-locked…"`).
* **Swap media keeping clip motion:** `clip.replaceFromBin {clips:[id], item:<newItemId>}` — also the way to
  replace an **audio** clip: the clip keeps its duration (trims by whole frames if the new source is shorter)
  and keeps its audio effects (volume / channel_volume / panner). Import first (`file.import {paths:[…]}`).
* **Movement / zoom:** `effects.setParam {clip, effect:"motion", param:"position", value:[x,y]}`;
  scale zoom `param:"scale", value:100→112, keyframe:true, time:<ticks>` — key times are **sequence time**
  (clip-local time silently does nothing / renders identical frames).
* **Check a frame (live app):** `exec file.exportFrame "path=out.png" format=png target=program sequence=<id> time=<ticks>`.
  The `render` subcommand is headless-only when a bridge is in use.
* **Import media:** `filmcraft-cli --bridge <p> import <files…>` (returns item ids).
* **Export:** `exec file.exportMedia "path=<out.mp4>" format=h264 crf=19 bitrateMode=crf audio=true
  hardwareEncoding=auto range=entire sequence=<id> wait=true` (~25 fps render speed → 2367 f ≈ 94 s).

## 5. EffectCraft Rendering (bridge)

* The `render` CLI fails with `--bridge`: *"render runs headless; use `exec renderQueue.add` / `renderQueue.render`"*.
  Script it in a `.jsx`:
  ```js
  renderQueue.add({comp:"Scene1",format:"h264",output:".../scene1.mp4",
                   quality:"best",resolution:"full",audio:"off",timeSpan:"comp"});
  renderQueue.render({wait:true});
  ```
* Comp durations must equal the exact frame count / 30 (e.g. 425 f → 14.1667 s, not 14.15 — off-by-one frame).
* Empirical: wave/particle **amplitude ≈ `amount`/10 px** (effect `amount` 150 → ~15 px).
* Scripts are quoting-safe (`script FILE.jsx`); prefer them over `exec`.
* **Render with `wait:false` + poll the file.** A long render outlives the client call; `renderQueue.render
  {wait:false}` returns immediately, then poll the output path until the size stops changing and ffprobe confirms
  the expected frame count. (`renderQueue.list` / `renderQueue.remove {index}` clear leftovers first — the queue
  persists between sessions.)
* **Render settings that reproduced the approved scene masters:** `format:"h264", quality:"best",
  resolution:"full", audio:"off", timeSpan:"comp"` (no explicit `bitrate`). The encoder is quality-targeted: a
  1080×1920 30 fps 14.2 s scene ≈ **5.8 MB / 3.27 Mbps** regardless of the nominal 15 Mbps in the item JSON.
  To match an existing master, compare size/bitrate with `ffprobe` instead of copying settings blindly.
* **Safe swap pattern:** render to a *new* file (`scene1_v2_fix.mp4`), verify (frames + a frame render), keep a
  backup of the old (`…_oldtyper.mp4`), then copy over the canonical name and re-import.
* **`file.save` fails with "no path: use file.saveAs {path}"** when the project was never written to disk
  (EffectCraft reports `path: null`). Rendering needs no save — just don't treat the save error as a blocker.
* Read/inspect with `get_project`, `get_comp`, `get_layer` (`flat:true` for leaf paths) and `run_script`
  (JS model: `app.project.items` — **no `items.byName`**, iterate `numItems` and match `.name`).

## 6. Transparent Motion Graphics Integration

1. Build the composition in EffectCraft.
2. Render headless with alpha (WebM VP9):
   `effectcraft-cli render --comp <CompName> --out overlay.webm --format webm --channels rgba`
3. Import into FilmCraft (`import` or `file.import`) and place above the character track.

## 7. SoundCraft (audio)

* CLI subcommands: `info`, `convert`, `run`/`script` (offline session), `commands`, `describe`,
  `app --port P METHOD JSON` (drive a **running** GUI), `mcp`, `parity`, `plugins`.
* Built-in plugins: EQ 1/7-band (HPF + shelves), Compressor/Limiter, **Expander/Gate**, De-Esser, Maximizer,
  Channel Strip, reverbs/delays/mod, saturator, pitch/time, gain/trim, DC Offset Removal, dither, instruments.
* **No AI / spectral noise reduction built in.** It hosts **VST3 + CLAP** (`engine.vst3_plugins`,
  `engine.clap_plugins`, `mix.insert`) but none are installed by default — a real denoiser needs a plugin
  download (require explicit user permission) or an external AI tool (e.g. DeepFilterNet).
* Noise-floor tools that need no download: **`expander_gate`** (threshold/ratio/range/hold/release) for the
  pauses, **`eq_7band`** HPF + high-shelf to tame rumble/hiss, `channel_strip` for gate+comp+EQ in one pass.
* Batch processing: `audiosuite.process {process:<plugin id>, params, clips|tracks, start, end}`.
* **Headless recipe:** `script FILE --bounce OUT.wav`, one `ID JSON` per line (UTF-8 no BOM):
  `file.import_audio {"path":"…"}`, then `mix.insert {track:2, slot:0, plugin:"expander_gate", params:{…}}`, …
  (`--in` takes a `.scraft` session only — import the audio in the script. `session.inspect` gives track ids.)
* **Gate gotcha:** the detector is effectively **peak-driven** — a threshold below the noise *peaks* does
  nothing (verified: threshold −38 → ≈1 dB change when noise peaks were −35). Set the threshold **above the
  noise peaks, below the quietest speech** (measured win: threshold −30, ratio 6, range 80, attack .3,
  hold 120, release 300 → pauses 7–16 dB quieter, speech untouched).
* A gate cleans **pauses only**; hiss under speech needs an AI denoiser (e.g. DeepFilterNet).
* **Recording (discovered):** SoundCraft is DAW-class and CAN capture VO — `setup.playback_engine` (input device),
  `track.new`, `mix.record_arm {tracks, value}`, `mix.input_monitor`, `transport.record` (`Cmd+Space`), plus
  `options.loop_record` and `event.retrospective_record`. Bounce/export per take (48 kHz WAV) and process in the
  same session. Simplest alternative for impatient takes: Audacity/OBS → WAV, then process here.
* **AI denoise (verified):** the standalone Rust binary
  `deep-filter-<ver>-x86_64-pc-windows-msvc.exe` (~26 MB, model bundled) from the DeepFilterNet GitHub
  release → put it anywhere on `PATH` (e.g. `<tools>\deep-filter.exe`). Usage
  `deep-filter.exe -D [--pf --pf-beta 0.05] IN.wav -o OUTDIR`
  (output is named after the input → **rename between runs**). `-D` compensates the STFT/lookahead delay so the
  result stays aligned with whisper word timings. CPU-only, ~13 s for 79 s of audio. Measured vs source:
  pauses −47.9/−47.0 dB → **−65 to −72 dB** (17–25 dB), speech ≈1.5 dB quieter (level-match afterwards).

## 8. Character Explainer Pattern (PNGTuber in an NLE)

* Prepare cards with PIL: 290×290 rounded card (r30, fill `#0b101b`, image inset 14, r22, cyan `#00f0ff` border 3 px)
  + full-frame cutaways at 1080×1920; keep the face + hands + logo in frame.
* PIP pinned top-right at `[895,185]`; full-screen cutaways at `[540,960]` with a 100→112 zoom over the window.
* Map poses to narration beats; long sentences reuse the current pose (no nervous flicker).

## 9. EffectCraft Text Layers — anchors & typewriter effects

### 9.1 The box-text anchor trap (cost hours — check this FIRST for "text is off-screen/misplaced")
The text style is **not** in the layer tree. Read it with `run_script`:
```js
var d = layer.property("ADBE Text Properties").property("ADBE Text Document").value;
// d.font, d.fontSize, d.justification, d.boxText, d.boxTextSize, d.fillColor, d.tracking
```
* `justification`: **7413 = left, 7414 = centre, 7415 = right**.
* **`boxText=true` (a "box" text) means the layer `transform/position` is the box CENTRE**, so the ink starts at
  `position.x − boxTextSize.width/2`. A 640-wide box with position.x = 300 draws from **x = −20** → the text is
  clipped by the screen edge while the property still reads a sensible "300".
* With `boxText=false` (point text, left-justified) the ink starts at `position.x` — much easier to reason about.
* Fixes: set `position.x = desired_ink_left + boxWidth/2` (e.g. 170 + 320 = 490), or switch to point text / right
  justification. Verify by **rendering a frame and measuring the ink**, never by trusting the number.
* The caret/cursor shape (a small 6×58 rect layer) is a separate layer — move it with the text (its position is
  its own centre, so caret_x = word_ink_end + ~8).

### 9.2 Typewriter / "being typed" effect (verified)
Wipe-based reveals are **not** a reliable typewriter in this build (see 9.3). Drive the **text itself**:
1. Key `text/sourceText` with **Hold** interpolation through the prefixes, frame-aligned (~0.13 s/char):
   `""` (the frame the layer's opacity reaches 100 — an empty key there prevents a stray first letter) then
   `H`, `HE`, `HEL`, `HELL`, `HELLO`.
2. Key the caret's `transform/position` (**Hold**) to each prefix's advance end + 8 px so it steps with the typing:
   measure advances with PIL `ImageFont.getlength` on the real font (measured: a 6-letter word at 56 px came out
   206.5 px from PIL vs 207 px of engine ink — within 1 px). `tracking` is in 1/1000 em (−6 ≈ −0.34 px/char).
3. Flatten any wipe's `completion` to a constant (or drop the effect) — keep the Glow.
4. Verify by rendering frames at each key time and measuring the ink span (see 9.4).

### 9.3 Linear Wipe behaviour (measured)
* `effects/#1/completion` **0 = fully visible, 100 = fully wiped**; growing completion removes from the **left**.
* The travel is **non-linear** relative to the layer's ink: with angle 90 and the keys 0→100 the word stayed fully
  visible until c≈50 % and then vanished in the last ~0.25 s; with keys 100→0 the visible ink always *ended* at the
  word's right edge and grew **leftward** (a right-to-left reveal). Conclusion: use `sourceText` keys for typing.
* `angle` values: 0 / 90 / 180 / 270 = different axes/directions; always A/B two frames rather than assuming.

### 9.4 Objective verification (never eyeball a small render)
Render frames (full size) and measure with PIL: mask bright cyan-ish pixels `(g>150)&(b>150)&(r<130)`, cluster
columns with >8 px gaps, print each cluster's x/y range. This is how an off-screen word (ink x 0…187 instead
of 170…377) and a reversed wipe were proven. Write it once as a small `analyze_ink.py` and reuse it.

## 10. FilmCraft Audio & SFX Workflow (learned)

* **Track ids are not sequential** — read them from `sequence_inspect` (e.g. A1=4, A2=5, A3=6, then A4=181, A5=182,
  A6=183 after later additions). `timeline.place {item, track, seconds, video:false, audio:true}`.
* **`timeline.place` has NO gain parameter.** Always two passes: place everything, then
  `clip.audioGain {clips:[…], mode:"set"|"adjust", db}` — `set` = absolute, `adjust` = additive; both batch fine
  and the result echoes `gainDb` per clip.
* **Sequence-length guard:** a cue whose tail runs past the sequence duration **extends the export**. Move the cue
  (here `outro_chime` went from A3 @78.3 s to A4 @76.4 s) and re-check `sequence_inspect.durationFrames`.
* **Choose SFX level for audibility, not for peak.** The mix is voice-dominated: measured mix max
  −0.1/−0.4/−0.5/−0.7/−0.8 dBFS at SFX offsets 0/−2/−3/−4.5/−6 dB — loudness is a bad target. A workable scheme
  ("smart balance"): design level **+1.5 dB for subtle cues** (design ≤ −9 dB) and **−2.5 dB for hero cues**
  (> −9 dB), applied as `adjust` on top of an earlier uniform pass.
* **Audition without exporting:** rebuild the SFX bus offline with ffmpeg (`adelay` + `volume` + `amix
  normalize=0`) from the cue plan and mix it against the extracted voice track — the model matched real exports
  within ~0.1 dB (worth a reusable `build_sfx_bus.py`).
* **No limiter / no mixdown command** in FilmCraft (`command_list filter limiter|mixdown` → `[]`);
  `effects.list {kind:"Audio"}` exposes `hard_limiter`, `amplify`, `eq_7band`, … but `effects.apply` targets
  *clips*, not a master bus.
* **Prove an audio-only change:** after re-exporting, `ffmpeg -i new.mp4 -map 0:a:0 -c copy -f md5 -` on both
  files — an identical MD5 means the audio is untouched (and vice-versa: identical video MD5 = video untouched).
