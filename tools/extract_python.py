"""Regenerate blender/*.py from the Python blocks embedded in index.html.

index.html is the source of truth. Run after editing it:
    python tools/extract_python.py
"""
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent
html = (root / "index.html").read_text(encoding="utf-8")
out = root / "blender"
out.mkdir(exist_ok=True)
for block_id, filename in (("hlp", "helpers.py"), ("run", "runner.py"), ("tt", "self_test.py")):
    m = re.search(r'<script type="text/plain" id="%s">\n?(.*?)</script>' % block_id, html, re.S)
    if not m:
        raise SystemExit("block %s not found in index.html" % block_id)
    (out / filename).write_text(m.group(1).strip() + "\n", encoding="utf-8")
    print("wrote blender/" + filename)
