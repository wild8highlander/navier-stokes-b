# `covers/` — Print-Ready Cover PDFs

Rendered single-page vector covers for the two monograph editions,
generated from the HTML layouts `cover_ru.html` / `cover_en.html` in the
parent directory (`html2poster.js`, A4, zero margin):

| File | Used by |
|---|---|
| `cover_ru.pdf` | `MONOGRAPH_RU.pdf` (page 0, merged by `code/python/merge_pdf.py`) |
| `cover_en.pdf` | `MONOGRAPH_EN.pdf` (page 0, merged by `code/python/merge_pdf.py`) |

Regenerate: `node <pdf-skill>/scripts/html2poster.js cover_ru.html
--output covers/cover_ru.pdf --width 210mm` (and the same for `en`).
