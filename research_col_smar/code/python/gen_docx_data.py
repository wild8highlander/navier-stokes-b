"""gen_docx_data.py — dump monograph content to JSON for the docx-js build."""

from __future__ import annotations

import json
import os
import sys

from PIL import Image as PILImage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, "monograph", "assets")
FIGDIR = os.path.join(ROOT, "figures")

LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
if LANG == "ru":
    sys.path.insert(0, HERE)
    from mg_content_ru_full import CONTENT_RU as CONTENT, META
else:
    sys.path.insert(0, HERE)
    from mg_content_en_full import CONTENT_EN as CONTENT, META


def dims(path):
    pil = PILImage.open(path)
    return {"w": pil.width, "h": pil.height}


blocks = []
for block in CONTENT:
    kind = block[0]
    if kind in ("h1", "h2", "p", "ref"):
        blocks.append({"t": kind, "text": block[1]})
    elif kind == "formula":
        path = os.path.join(ASSETS, f"formula_{block[1]}.png")
        d = dims(path)
        blocks.append({"t": "formula", "path": path, "eqno": block[2],
                       "w": d["w"], "h": d["h"]})
    elif kind == "fig":
        path = os.path.join(FIGDIR, LANG, block[1])
        d = dims(path)
        blocks.append({"t": "fig", "path": path, "caption": block[2],
                       "w": d["w"], "h": d["h"]})
    elif kind == "table":
        blocks.append({"t": "table", "headers": block[1], "rows": block[2],
                       "caption": block[3]})

payload = {"meta": META, "lang": LANG, "blocks": blocks}
out = os.path.join(HERE, f"mg_content_{LANG}.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False)
print(f"[docx-data] {out}: {len(blocks)} blocks")
