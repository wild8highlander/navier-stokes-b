"""merge_pdf.py — insert cover as page 0 of the body PDF and brand it."""

from __future__ import annotations

import os
import sys

from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MONO = os.path.join(ROOT, "monograph")
COVERS = os.path.join(ROOT, "covers")

A4_W, A4_H = 595.28, 841.89


def normalize(page):
    box = page.mediabox
    w, h = float(box.width), float(box.height)
    if abs(w - A4_W) > 0.3 or abs(h - A4_H) > 0.3:
        page.scale_to(A4_W, A4_H)
    return page


def main() -> int:
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    body = os.path.join(MONO, f"MONOGRAPH_{lang.upper()}_body.pdf")
    cover = os.path.join(COVERS, f"cover_{lang}.pdf")
    out = os.path.join(MONO, f"MONOGRAPH_{lang.upper()}.pdf")

    writer = PdfWriter()
    writer.add_page(normalize(PdfReader(cover).pages[0]))
    for page in PdfReader(body).pages:
        writer.add_page(normalize(page))
    writer.add_metadata({
        "/Title": "The Smagorinsky and Kolmogorov Constants (RU edition)"
        if lang == "ru"
        else "The Smagorinsky and Kolmogorov Constants (EN edition)",
        "/Author": "wild8highlander",
        "/Creator": "navier-stokes-b research program",
        "/Subject": "Unified spectral theory, closures and numerical experiment",
    })
    with open(out, "wb") as fh:
        writer.write(fh)
    print(f"[merge] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
