# `monograph/` — The Two-Language Monograph Editions

| File | Language | Format | Role |
|---|---|---|---|
| `MONOGRAPH_RU.pdf` / `MONOGRAPH_RU.docx` | Russian | PDF / DOCX | citable + editorial editions |
| `MONOGRAPH_EN.pdf` / `MONOGRAPH_EN.docx` | English | PDF / DOCX | citable + editorial editions |
| `assets/` | — | PNG | display formulas rendered at 300 dpi (shared by both languages) |

Both PDFs carry the dark academic cover (Template 03; the print-ready
HTML layouts are `cover_ru.html` / `cover_en.html` at the program root),
a clickable table of contents, page-numbered bodies and identical
chapter structure. The DOCX editions are kept in sync with the PDFs and
carry the same formulas and figures as embedded images.

Regenerate: `python3 code/python/gen_pdf.py ru|en`,
`python3 code/python/gen_docx_data.py ru|en` + `bun code/python/gen_docx.js ru|en`.
