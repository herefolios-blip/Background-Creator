# Handoff: status and next steps

Repo: https://github.com/herefolios-blip/Background-Creator
Briefing for AIs: `AI_CONTEXT.md`. Helper reference: `docs/HELPERS.md`. Source of truth: `index.html`.

## Starter prompt for a new chat
> Read https://raw.githubusercontent.com/herefolios-blip/Background-Creator/main/AI_CONTEXT.md and https://raw.githubusercontent.com/herefolios-blip/Background-Creator/main/HANDOFF.md, then fetch index.html from the same folder. Continue from the "Next steps" list. I test everything in Blender myself and will send screenshots and the `build_log` text.

If the AI cannot browse, paste `AI_CONTEXT.md`, this file and `index.html`.

## What the project is
A single-page tool that writes prompts for chat AIs. The AI returns a Blender (bpy) script that builds a photoreal virtual-production backdrop (room set behind on-camera talent). Workflow: fill fields, send five stage prompts in one chat, paste each reply into the assembler, run the full script in Blender, tune with the Render tweaks script.

## Done and confirmed by the user's renders
Staged build and assembler; scene reset; procedural materials with per-object variation; wood grain aligned to boards; plants with stems; book rows; framed pictures; collision-free placement; talent clear zone; auto exposure; photographic finish option; saved projects.

## Written but NOT yet confirmed in Blender (verify first)
1. Props visible again after the relaxed floor-item frame check (last render showed only a rug).
2. Orphan-light removal (stray glow on a panel seam).
3. `seal_gaps()` for black wedges at the ceiling corners.
4. `door()`, `window_light()` and its pane-shaped shadow pattern, plaster stains and scuffs, smooth shading, art mounts and glass.
5. Stray-prop containment (`room_bounds`, `contain_props`).
For each: rebuild, then read the matching `build_log` line (`Layout`, `Clear zone`, `Switched off lights`, `Sealed gaps`, `Frame check`, `Moved stray props`).

## Known weaknesses
- Furniture is the least realistic part: AI-written sofas, chairs and tables are boxy.
- Walls cover most of the frame and still look like clean CG.
- Output varies by chat AI; helpers tolerate sloppy calls but cannot fix missing intent.
- Name-based detection (props, fixtures, windows) misses unusual names.
- Compositor effects and some node socket names differ on Blender 5.x; they fail soft with a message.
- No automated tests: Blender cannot run in the chat sandbox.

## Next steps (priority order)
1. **Verify the unconfirmed list above** and fix whatever the log shows. Done when a rebuilt scene shows props in frame, no stray glow, no black wedges.
2. **Furniture helper library.** Add `sofa()`, `armchair()`, `table()`, `rug()`, `curtain()` helpers (separate base, seat, back, arms, legs, cushions with sag, bevels up to 3 cm, fabric weave via `pbr`), registered through `reserve()`, and tell the AI to use them instead of boxes. Done when a sofa render no longer reads as boxes.
3. **Declarative scene spec.** Have the AI return a JSON layout (room size, walls, windows, furniture list with positions, materials, lights) and have a fixed Python interpreter in the header build it. This removes most AI-written-code failures. Keep the current staged mode as a fallback.
4. **Blender version handling.** Log `bpy.app.version_string`, branch node and compositor code for 4.2, 4.5 and 5.x, add a version-specific self-test.
5. **Automated tests.** Add `tests/smoke.py` run with `blender -b -P`, and a GitHub Action that runs the helper self-test headless so regressions are caught without screenshots.
6. **Photo-matched mode.** A step-zero prompt that asks the AI to extract palette, materials, proportions and a layout table from the user's photos, feeding the stages.
7. **Wall realism pass.** Optional Poly Haven plaster layered under procedural stains, decal-style scuffs and dust, subtle large-scale colour drift, skirting shadow lines.
8. **Post and camera.** Vignette, film grain, halation; verify the compositor path on 5.x; depth of field presets (f/2.8, f/4).
9. **Repair loop.** Paste `build_log` into the app and auto-generate a targeted repair prompt (which stage failed, which helper, last traceback line).
10. **Deliverables.** Presets for 4K stills, looping MP4, EXR with alpha; camera-move test.
11. **App housekeeping.** Split `index.html` into modules with a build script, export and import project JSON, version number shown in the UI.

## Working rules for any AI continuing this
- Edit `index.html`, then run `python tools/extract_python.py`.
- Syntax-check the JS and every Python block before handing over.
- Say which stages the user must regenerate and which log line to check.
- Keep helpers tolerant of wrong keywords and non-string arguments.
- Do not claim something works in Blender unless the user's log or render confirms it.
- Give the user a short, plain summary; they work from screenshots and logs.
