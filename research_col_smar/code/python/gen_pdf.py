"""gen_pdf.py — build MONOGRAPH_{RU,EN}.pdf (body) via ReportLab.

Usage: python3 gen_pdf.py ru|en

Follows the pdf-skill report brief: TocDocTemplate + multiBuild, TOC with
clickable bookmarks, CondPageBreak before H1, safe_keep_together, tables
with Paragraph cells and proportional widths, formulas and figures as
block-level images with preserved aspect ratio, FreeSerif text with
install_font_fallback, symmetric margins.
"""

from __future__ import annotations

import hashlib
import importlib
import os
import sys

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")
FIGDIR = os.path.join(ROOT, "figures")
ASSETS = os.path.join(ROOT, "monograph", "assets")
OUTDIR = os.path.join(ROOT, "monograph")
os.makedirs(OUTDIR, exist_ok=True)

PDF_SKILL = "/home/z/my-project/skills/pdf"
sys.path.insert(0, os.path.join(PDF_SKILL, "scripts"))
from pdf import install_font_fallback  # noqa: E402

FONT_DIR = "/usr/share/fonts"
pdfmetrics.registerFont(TTFont("FreeSerif", f"{FONT_DIR}/truetype/freefont/FreeSerif.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-Bold", f"{FONT_DIR}/truetype/freefont/FreeSerifBold.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-Italic", f"{FONT_DIR}/truetype/freefont/FreeSerifItalic.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-BoldItalic", f"{FONT_DIR}/truetype/freefont/FreeSerifBoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("NotoSerifSC", f"{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSerifSC-Bold", f"{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf"))
registerFontFamily("FreeSerif", normal="FreeSerif", bold="FreeSerif-Bold",
                   italic="FreeSerif-Italic", boldItalic="FreeSerif-BoldItalic")
registerFontFamily("NotoSerifSC", normal="NotoSerifSC", bold="NotoSerifSC-Bold")
install_font_fallback()

# cascade palette (seed 42)
PAGE_BG = colors.HexColor("#f5f5f4")
HEADER_FILL = colors.HexColor("#4e4732")
TABLE_STRIPE = colors.HexColor("#ededeb")
BORDER = colors.HexColor("#c5bfac")
ACCENT = colors.HexColor("#92761f")
TEXT_PRIMARY = colors.HexColor("#151513")
TEXT_MUTED = colors.HexColor("#7e7c74")

MARGIN = 0.95 * inch
PAGE_W, PAGE_H = A4
AVAIL = PAGE_W - 2 * MARGIN

LANG = sys.argv[1] if len(sys.argv) > 1 else "en"

if LANG == "ru":
    sys.path.insert(0, HERE)
    from mg_content_ru_full import CONTENT_RU as CONTENT, META
else:
    sys.path.insert(0, HERE)
    from mg_content_en_full import CONTENT_EN as CONTENT, META

OUT = os.path.join(OUTDIR, f"MONOGRAPH_{LANG.upper()}_body.pdf")

ST = {
    "h1": ParagraphStyle("H1", fontName="FreeSerif", fontSize=17, leading=23,
                         textColor=HEADER_FILL, spaceBefore=18, spaceAfter=10),
    "h2": ParagraphStyle("H2", fontName="FreeSerif", fontSize=13, leading=18,
                         textColor=TEXT_PRIMARY, spaceBefore=12, spaceAfter=6),
    "body": ParagraphStyle("Body", fontName="FreeSerif", fontSize=10.5,
                           leading=16.5, alignment=TA_JUSTIFY,
                           textColor=TEXT_PRIMARY, spaceAfter=8,
                           firstLineIndent=0),
    "ref": ParagraphStyle("Ref", fontName="FreeSerif", fontSize=9.5,
                          leading=13.5, alignment=TA_LEFT,
                          textColor=TEXT_PRIMARY, spaceAfter=4,
                          leftIndent=24, firstLineIndent=-24),
    "caption": ParagraphStyle("Cap", fontName="FreeSerif-Italic", fontSize=9,
                              leading=12.5, alignment=TA_CENTER,
                              textColor=TEXT_MUTED, spaceBefore=4,
                              spaceAfter=14),
    "toc_t": ParagraphStyle("TOCTitle", fontName="FreeSerif", fontSize=17,
                            leading=23, textColor=HEADER_FILL, spaceAfter=14),
}

TOC_L0 = ParagraphStyle("TOC0", fontName="FreeSerif", fontSize=11,
                        leading=16, leftIndent=6, textColor=TEXT_PRIMARY)
TOC_L1 = ParagraphStyle("TOC1", fontName="FreeSerif", fontSize=9.5,
                        leading=14, leftIndent=24, textColor=TEXT_MUTED)


class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, "bookmark_name"):
            level = getattr(flowable, "bookmark_level", 0)
            text = getattr(flowable, "bookmark_text", "")
            key = getattr(flowable, "bookmark_key", "")
            self.notify("TOCEntry", (level, text, self.page, key))


def add_heading(text, style, level=0):
    key = "h_" + hashlib.md5(text.encode()).hexdigest()[:8]
    par = Paragraph(f'<a name="{key}"/><b>{text}</b>', style)
    par.bookmark_name = key
    par.bookmark_level = level
    par.bookmark_text = text
    par.bookmark_key = key
    return par


def fit_image(path, max_w, max_h):
    pil = PILImage.open(path)
    ow, oh = pil.size
    ratio = min(max_w / ow if ow > max_w else 1.0,
                max_h / oh if oh > max_h else 1.0)
    return Image(path, width=ow * ratio, height=oh * ratio)


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("FreeSerif-Italic", 8)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(MARGIN, PAGE_H - 0.55 * inch, META["title"])
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.7)
    canvas.line(MARGIN, PAGE_H - 0.62 * inch, PAGE_W - MARGIN,
                PAGE_H - 0.62 * inch)
    canvas.setStrokeColor(BORDER)
    canvas.line(MARGIN, 0.62 * inch, PAGE_W - MARGIN, 0.62 * inch)
    canvas.setFont("FreeSerif", 9)
    canvas.drawCentredString(PAGE_W / 2, 0.42 * inch, str(doc.page))
    canvas.setFont("FreeSerif-Italic", 8)
    canvas.drawString(MARGIN, 0.44 * inch, META["footer_left"])
    canvas.drawRightString(PAGE_W - MARGIN, 0.44 * inch, META["footer_right"])
    canvas.restoreState()


def build_story():
    story = []
    toc = TableOfContents()
    toc.levelStyles = [TOC_L0, TOC_L1]
    story.append(Paragraph(f"<b>{'Оглавление' if LANG == 'ru' else 'Table of Contents'}</b>", ST["toc_t"]))
    story.append(toc)
    story.append(PageBreak())

    avail_h = PAGE_H - 2 * MARGIN
    threshold = avail_h * 0.25
    fig_no = 0
    tbl_no = 0
    eq_no_counter = 0

    for block in CONTENT:
        kind = block[0]
        if kind == "h1":
            story.append(CondPageBreak(threshold))
            story.append(add_heading(block[1], ST["h1"], level=0))
        elif kind == "h2":
            story.append(CondPageBreak(avail_h * 0.12))
            story.append(add_heading(block[1], ST["h2"], level=1))
        elif kind == "p":
            story.append(Paragraph(block[1], ST["body"]))
        elif kind == "ref":
            story.append(Paragraph(block[1], ST["ref"]))
        elif kind == "formula":
            key, eqno = block[1], block[2]
            path = os.path.join(ASSETS, f"formula_{key}.png")
            pil = PILImage.open(path)
            w_pt = min(AVAIL * 0.86, pil.width * 72.0 / 300.0)
            h_pt = pil.height * (w_pt / pil.width)
            img = Image(path, width=w_pt, height=h_pt)
            eq_par = Paragraph(eqno, ParagraphStyle(
                "eq", fontName="FreeSerif", fontSize=10,
                textColor=TEXT_MUTED))
            row = [[img, eq_par]]
            t = Table(row, colWidths=[AVAIL * 0.82, AVAIL * 0.14],
                      hAlign="CENTER")
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(Spacer(1, 4))
            story.append(t)
            story.append(Spacer(1, 6))
        elif kind == "fig":
            fig_no += 1
            path = os.path.join(FIGDIR, LANG, block[1])
            img = fit_image(path, AVAIL * 0.94, PAGE_H * 0.34)
            cap = Paragraph(block[2], ST["caption"])
            story.append(Spacer(1, 10))
            story.append(KeepTogether([img, cap]))
        elif kind == "table":
            tbl_no += 1
            headers, rows, cap = block[1], block[2], block[3]
            cell_h = ParagraphStyle(
                "ch", fontName="FreeSerif", fontSize=8.6, leading=11.5,
                alignment=TA_LEFT, textColor=colors.white)
            cell_b = ParagraphStyle(
                "cb", fontName="FreeSerif", fontSize=8.8, leading=12,
                alignment=TA_LEFT, textColor=TEXT_PRIMARY)
            data = [[Paragraph(f"<b>{h}</b>", cell_h) for h in headers]]
            for r in rows:
                data.append([Paragraph(str(x), cell_b) for x in r])
            ncol = len(headers)
            ratios = [1.0 / ncol] * ncol
            widths = [r * AVAIL * 0.98 for r in ratios]
            t = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1)
            style = [
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
            for i in range(1, len(data)):
                if i % 2 == 0:
                    style.append(("BACKGROUND", (0, i), (-1, i), TABLE_STRIPE))
            t.setStyle(TableStyle(style))
            cap_par = Paragraph(cap, ST["caption"])
            story.append(Spacer(1, 10))
            if len(rows) <= 10:
                story.append(KeepTogether([t, cap_par]))
            else:
                story.append(t)
                story.append(cap_par)
            story.append(Spacer(1, 6))
    return story


def main() -> int:
    doc = TocDocTemplate(
        OUT, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.95 * inch, bottomMargin=0.85 * inch,
        title=META["title"], author="wild8highlander",
        creator="navier-stokes-b research program",
        subject=META["subtitle"],
    )
    story = build_story()
    doc.multiBuild(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"[pdf] wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
