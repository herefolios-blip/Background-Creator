# Handoff: status and next steps

Repo: https://github.com/herefolios-blip/Background-Creator
Briefing for AIs: `AI_CONTEXT.md`. Helper reference: `docs/HELPERS.md`. Source of truth: `index.html`.
Last updated 25 November 2026.

## Starter prompt for a new chat
> Read https://raw.githubusercontent.com/herefolios-blip/Background-Creator/main/AI_CONTEXT.md and https://raw.githubusercontent.com/herefolios-blip/Background-Creator/main/HANDOFF.md, then fetch https://raw.githubusercontent.com/herefolios-blip/Background-Creator/main/index.html. Continue from the "Next steps" list. I test everything in Blender myself and will send screenshots and the `build_log` text.

Give the full `index.html` URL in the message. Some chat AIs can only fetch links that appear verbatim in the message, and "the same folder" is not enough.

If the AI cannot browse, paste `AI_CONTEXT.md`, this file and `index.html`.

## What the project is
A single-page tool that writes prompts for chat AIs. The AI returns a Blender (bpy) script that builds a photoreal virtual-production backdrop (room set behind on-camera talent). Workflow: fill fields, send five stage prompts in one chat, paste each reply into the assembler, run the full script in Blender, tune with the Render tweaks script.

## Done and confirmed by the user's renders
- Staged build and assembler, scene reset, procedural materials with per-object variation, wood grain aligned to boards, plants with stems, book rows, framed pictures, collision-free placement, talent clear zone, auto exposure, photographic finish option, saved projects.
- Props visible in frame (the earlier "only a rug" problem is gone).
- No black wedges at the ceiling corners in the last five renders. The cause was dark vents, so prompt rule 25 now makes vents light and flush. `seal_gaps()` found nothing to patch.
- Stray glow from sconces beside bookcases is gone in the latest render. Two causes were fixed: bookcase shelves were being counted as light fixtures, and wall fixtures were placed where bookcases stand. The `Light audit` log line has not been seen yet, so confirm it on the next build.
- Furniture helpers: `sofa()` was confirmed as "no longer reads as boxes". `table()` (round), `bookcase()` and `desk()` have appeared in renders and look right.
- Shelf-visibility guard: plants, lamps and tables no longer stand in front of bookcases.

## Written but NOT yet confirmed in Blender (verify first)
1. Desk, sideboard and TV-unit extension of the shelf guard, and the order-independent bookcase check. The last render showed a desk covering the bottom shelf of a bookcase.
2. `chair()`, `sideboard()`, `tv_unit()`, `rug()` and `curtain()` visually. None has appeared in a render yet.
3. The `midcentury` and `industrial` styles. Only `modern` has been rendered.
4. The `fabric`, `carpet` and `leather` materials in `pbr()`. The weave is fine and may only be visible close up.
5. `door()`, `window_light()` and its pane-shaped shadow pattern, plaster stains and scuffs, art mounts and glass.
6. `Light audit`, `Hid wall fixtures that sat inside furniture` and `Moved lights onto their fixtures` log lines.
7. The fallback lighting, which only runs when stage 3 fails.
For each: rebuild, then read the matching `build_log` line (see "Reading the build log" in `docs/HELPERS.md`).

## Known weaknesses
- Auto exposure ends around -3.2 EV in recent builds, so the stage 3 lights are roughly ten times too strong. The look is fine but the lights are harder to control and noisier. Fix by lowering the wattage guidance in stage 3.
- Camera and room depth: the AI sometimes puts the camera close to the back wall. Anything within `TALENT_DIST + 0.75` m of the camera counts as the talent zone, so shallow rooms lose furniture (`NO ROOM`) or whole bookcases. Rule 28 asks for the camera at least focus + 1.8 m from the back wall, but the AI does not always follow it.
- A chat AI may reserve small props before a bookcase. The guard then moves the bookcase or, failing that, builds it and logs a warning.
- `bookcase()` only fills shelves with books when `facing` is along the Y axis, because `book_row()` works in world axes.
- Panel seams render as thin black lines that look harsh in some renders.
- Walls cover most of the frame and still look like clean CG.
- Output varies by chat AI. Helpers tolerate sloppy calls but cannot fix missing intent. Failure examples seen: assigning a 3-value colour to a node socket, writing `bpy.mathutils`, building lights in stage 3 and moving the fixture in stage 4.
- Name-based detection (props, fixtures, wall fixtures, shelves) misses unusual names.
- Compositor effects and some node socket names differ on Blender 5.x. They fail soft with a message.
- No automated Blender tests. See step 5.

## Next steps (priority order)
1. **Verify the unconfirmed list above** and fix whatever the log shows. Done when a rebuilt scene shows the desk clear of the shelf, chairs, sideboards, TV units, rugs and curtains in frame, and a `Light audit` line with no unexpected removals.
2. **Extend the furniture catalogue.** Living room and office pieces are in. Still missing: beds, wardrobes, nightstands, and cafe or retail items (counters, stools, display units). Keep the same conventions: `facing`, `style`, `reserve()` inside the helper, `None` when there is no room.
3. **Lower the stage 3 light levels** so auto exposure lands near 0 EV.
4. **Declarative scene spec.** Have the AI return a JSON layout (room size, walls, windows, furniture list with positions, materials, lights) and have a fixed Python interpreter in the header build it. This removes most AI-written-code failures. Keep the current staged mode as a fallback.
5. **Blender version handling.** Log `bpy.app.version_string`, branch node and compositor code for 4.2, 4.5 and 5.x, add a version-specific self-test.
6. **Automated tests.** Add `tests/smoke.py` run with `blender -b -P`, and a GitHub Action that runs the helper self-test headless so regressions are caught without screenshots. A stubbed-`bpy` test already catches syntax errors, bad mesh indices and open meshes in the furniture helpers, and could be committed as `tests/stub_test.py`.
7. **Photo-matched mode.** A step-zero prompt that asks the AI to extract palette, materials, proportions and a layout table from the user's photos, feeding the stages.
8. **Wall realism pass.** Optional Poly Haven plaster layered under procedural stains, decal-style scuffs and dust, subtle large-scale colour drift, skirting shadow lines, softer panel reveals.
9. **Post and camera.** Vignette, film grain, halation; verify the compositor path on 5.x; depth of field presets (f/2.8, f/4).
10. **Repair loop.** Paste `build_log` into the app and auto-generate a targeted repair prompt (which stage failed, which helper, last traceback line).
11. **Deliverables.** Presets for 4K stills, looping MP4, EXR with alpha; camera-move test.
12. **App housekeeping.** Split `index.html` into modules with a build script, export and import project JSON, version number shown in the UI.

## Working rules for any AI continuing this
- Edit `index.html`, then run `python tools/extract_python.py`.
- Syntax-check the JS and every Python block before handing over. Test helper changes against a stubbed `bpy` where possible, because Blender cannot run in the chat sandbox.
- Say which stages the user must regenerate and which log line to check.
- Keep helpers tolerant of wrong keywords and non-string arguments.
- Do not claim something works in Blender unless the user's log or render confirms it.
- Prefer fixing a problem in the tool (a helper or a runner check) over asking the user to fix it in Blender. The team using this tool cannot edit scenes by hand.
- When a render shows a problem, ask for the `build_log` before guessing. The `Light audit`, `Clear zone` and `Layout` lines usually name the cause.
- Give the user a short, plain summary; they work from screenshots and logs.
