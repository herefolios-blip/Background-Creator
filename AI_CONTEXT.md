# Briefing for AI assistants

Paste this file (or its raw GitHub URL) at the start of a chat to continue development of this project.

## What this is
`index.html` is a self-contained web app (vanilla HTML, CSS, JS) that builds prompts for chat AIs. The AI returns Blender Python (bpy) that builds a photoreal virtual-production backdrop. The user pastes it into Blender, runs it, and reports errors or screenshots.

## Architecture (all inside index.html)
- JS: field definitions (`F1`..`F4`, `CK`), `prompt()` assembles the prompt, `py()` emits the Python render header from UI values, `xs()` emits the Render tweaks script, the assembler joins stage code with the header, helpers and runner.
- Embedded Python in `<script type="text/plain">` blocks: `hlp` (helpers), `run` (runner), `tt` (self-test).
- Stage contract: five functions named `stage1_materials`, `stage2_shell`, `stage3_lighting`, `stage4_dressing`, `stage5_camera`. The runner finds them by the `stageN_` prefix and wraps each in try/except.
- After the stages the runner: moves stray props inside the room, hides props in the talent zone, switches off orphan lights, seals shell gaps, checks the frame, auto-balances exposure, writes `build_log`.

## Conventions
- Edit `index.html` only, then run `python tools/extract_python.py`.
- Python in the helper block must stay valid for Blender 4.2+ and degrade gracefully (try/except) on 5.x.
- Prompt rules are numbered strings inside `prompt()`; add new rules at the end.
- Helpers must tolerate sloppy calls from the AI (wrong keywords, non-string collections).
- Never use browser storage for anything but saved projects and pasted stages, always inside try/catch.
- Typographic apostrophes in visible text.

## Known hard problems
Props vanishing (visibility checks too strict), light leaking through seams, stacked geometry from re-running scripts (solved by `RESET_SCENE`), AI inventing helper signatures (solved by the helper list in `HELPDOC`).

## When you change something
State which blocks changed, run a syntax check on the JS and each Python block, and tell the user what to regenerate (which stages) and what log line to look for.
