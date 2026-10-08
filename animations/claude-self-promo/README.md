# Claude, untangled — a 25-second self-promo experiment

An unofficial creative experiment, made by Claude. The film is 1920×1080, 30 fps, 25.0 s, with H.264 video and AAC audio.

**Story:** a messy request arrives as five sticky notes ("One request. Five opinions."). A small ember-like character untangles them into a plan, writes a short chart snippet, and runs three checks inside the film. The first run fails on a real bug (the bars forget to subtract the gaps), the character fixes it, the checks pass, and the "make it pop" task finally pops the chart. The lockup says: "Bring the mess. I'll check the work."

Everything is original:
- **Picture:** drawn in code on one `<canvas>`. No image or video assets.
- **Sound:** synthesized in `make_audio.py` (sine/noise/pad synthesis). No samples.
- **Type:** Inter (SIL Open Font License), installed in the render environment.
- **The checks are real:** the snippet on screen is the snippet that runs. `verify_checks.cjs` executes it and confirms the first version fails one check and the fix passes all three.

## Files

| File | What it is |
| --- | --- |
| `film.html` | The whole picture. `renderAt(t)` draws the frame at time `t` (seconds). |
| `cues.js` | The shared timeline and the two code versions. Picture and sound both read it. |
| `make_audio.py` | Generates the soundtrack and sound effects from `cues.js`. |
| `render.cjs` | Drives headless Chromium frame by frame, pipes PNGs into ffmpeg, muxes the audio. |
| `verify_checks.cjs` | Runs the on-screen code and the checks outside the browser. |
| `claude-self-promo.mp4` | The rendered film. |

## Rebuild

```sh
cd animations/claude-self-promo
node verify_checks.cjs                              # expect: first run fails 1 check, fix passes all 3
python3 make_audio.py cues.js soundtrack.wav        # sound, aligned to cues.js
NODE_PATH=/path/to/node_modules node render.cjs --audio soundtrack.wav --out claude-self-promo.mp4
node render.cjs --stills 1.0,12.6,17.7 --dir previews   # optional: spot-check single frames
```

`render.cjs` needs `playwright` (Chromium) and `ffmpeg` on the path. It falls back to `/opt/node22/lib/node_modules/playwright` if the module is not resolvable from here.

To change timing, edit `cues.js` and rebuild both the audio and the picture, so the sound stays on the same frames.
