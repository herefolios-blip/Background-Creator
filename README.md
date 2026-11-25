# Backdrop Prompt Builder

A single-page tool that turns a short room brief into a prompt for any chat AI (Gemini, ChatGPT, Claude, ...). The AI replies with a Blender Python script that builds a photoreal virtual-production backdrop. No server, no build step, no dependencies: open `index.html`.

## Quick start

1. Open `index.html` in a browser (or publish it with GitHub Pages, see below).
2. Fill in the room, lighting and camera fields. Pick a scene preset (office, boardroom, atrium, living room, library, loft, kitchen, hotel lobby, podcast set, bedroom, cafe or retail shop), a furniture style, and tick the furniture pieces you want. Attach your room photos in your chat AI.
3. Either copy the one-shot prompt, or use the staged build (recommended): send stages 1 to 5 in order in the same chat.
4. Paste each stage's reply into the **Assemble full script** panel and press **Build full script**.
5. In Blender (4.2 or newer), open the Scripting tab, paste the full script, press Run.
6. Read the popup or the `build_log` text datablock for what worked and what failed.
7. Use **Render tweaks** to change exposure, quality, resolution and camera without rebuilding.

## What the generated script does

- Resets the scene, builds materials, shell, lighting, dressing and camera in separate stages, each in its own error handler.
- Uses procedural materials with per-object variation, optional Poly Haven textures and HDRIs.
- Builds only the furniture you ticked, from a catalogue of ready-made pieces (sofa, armchair, chair, desk, table, sideboard, TV unit, bookcase, rug, curtains, bed, nightstand, dresser, wardrobe, counter, stool, bench, display unit) in modern, mid-century or industrial styles.
- Keeps props inside the room and inside the camera frame, avoids collisions, hides anything in the talent zone.
- Detects and seals gaps in the shell, switches off stray lights, auto-balances exposure.

See `docs/HELPERS.md` for the helper API and `AI_CONTEXT.md` if you want another AI to continue developing the project.

## Repository layout

| Path | Purpose |
|---|---|
| `index.html` | The whole app and the source of truth. Contains the prompt logic and the Blender helper code. |
| `blender/helpers.py`, `runner.py`, `self_test.py` | Extracted copies of the Python blocks, for reading, linting and diffing. |
| `tools/extract_python.py` | Regenerates `blender/*.py` from `index.html`. |
| `docs/HELPERS.md` | Reference for the helper functions the AI is told to use. |
| `tests/stub_test.py` | Runs the furniture helpers against a stubbed `bpy` and checks meshes, placement and orientation. No Blender needed. |
| `tests/dom_test.js` | Runs the app's JavaScript against a minimal fake DOM and checks presets, the furniture picker, the prompt and saved projects. Needs Node. |
| `CHANGELOG.md` | What changed in each version. |
| `AI_CONTEXT.md` | Briefing to paste into any AI chat so it can work on this repo. |

## Tests

Blender cannot run in most sandboxes, so two quick checks cover what can be tested without it:

```
python tests/stub_test.py     # prints TOTAL FAILS: 0 when the furniture helpers are sound
node tests/dom_test.js        # prints DOM TESTS PASSED
```

They do not check how anything looks in Blender. Only a real render or `build_log` confirms that.

## Publish with GitHub Pages

Repository Settings > Pages > Build and deployment > Deploy from a branch > `main` / root. The app will be at `https://<user>.github.io/<repo>/`. Saved projects use the browser's local storage, so they stay on your device.

## Troubleshooting

- **Nothing builds:** open the Text Editor in Blender and read `build_log`. Run **Copy helper self-test** from the app first.
- **Poly Haven fails:** the log lists the reason. Switch Texture source to Procedural first.
- **Props missing:** check the log for "NO ROOM" or "moved" lines.
- **A ticked piece is missing from the render:** it usually returned `None` because there was no room. Look for `NO ROOM for <name>` in the `Layout` line, then try a larger room or fewer pieces.
- Always rebuild from a plain-text script, not rich text.

## Limitations

Written against Blender 4.2+ APIs. Compositor effects and some node socket names differ in Blender 5.x; the scripts catch these and report instead of failing. Generated scripts depend on the chat AI following the prompt rules, so results vary by model.

## License

MIT
