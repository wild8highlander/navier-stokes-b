# `docs/` — Word Editions of the Collections (RU/EN Manuscripts)

> **Navigation:** [repository root](../README.md) › **`docs`**

![Format](https://img.shields.io/badge/Format-DOCX-2B579A?style=flat-square&logo=microsoftword&logoColor=white)
![Languages](https://img.shields.io/badge/Editions-RU_%2B_EN-1284BA?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The Word-manuscript layer of the b-correction program: full,
figure-saturated editions of the collection monographs — English (`en/`)
and Russian (`ru/`) — preserved exactly as they circulated when the
articles in [`papers/`](../papers/README.md) were being prepared. Each
`.docx` contains the complete text with embedded illustrations and
editorial formatting, from which the journal-style PDF version was later
assembled.

These editions exist for a specific kind of reader: one who needs to
annotate the argument in a word processor, quote with page-level
precision from the circulated manuscript, or trace which figures
accompanied which editorial state of the text. They are **documentation
artifacts, not build inputs** — nothing in the repository compiles them.
The authoritative typeset versions are the PDF pairs in
[`papers/`](../papers/README.md); the compilable sources are the LaTeX
files in [`src/`](../src/README.md).

Every manuscript is archived twice per language: the current edition and
a `_backup_before_exact_edition.docx` snapshot taken immediately before
the exact-edition pass — so the editorial delta of the final pass is
always recoverable by a plain file diff in any Word-compatible tool.

## Contents

| Folder | Contents |
|---|---|
| [`correction-b/`](correction-b/README.md) | the correction-b & NSE regularity monograph, EN + RU editions (each with its pre-exact-edition backup) |
| [`kdv/`](kdv/README.md) | the KdV chapter monograph, EN + RU editions (each with its backup) |

The separate two-language monograph of the P1–P7 runs package — with the
open-problems appendices — lives in
[`monograph/`](../monograph/README.md) (DOCX + PDF); the typeset KdV
chapter PDFs are in [`papers/kdv/`](../papers/kdv/README.md).

## Integrity and licensing

Like everything in the repository, the manuscripts are pinned by
[`MANIFEST.json`](../MANIFEST.json) and checked by CI. They are the
exclusive property of the author under
[IPL-RP-1.0](../LICENSE.md): reading, one personal unmodified backup and
quoting with full attribution are permitted; modification, redistribution
and derivative works require separate written consent.


## The exact-edition workflow, preserved

Each manuscript folder keeps **two states per language**: the circulating
edition and the `_backup_before_exact_edition.docx` snapshot. The naming
records the workflow that produced the final texts: the manuscripts were
edited freely until the argument stabilised, then an *exact edition* pass
tightened every quantitative statement against the pinned protocols in
[`data/results/`](../data/results/README.md). The backup freezes the
pre-pass state, so the editorial delta — what changed when the numbers
became contractual — is recoverable with nothing more exotic than a diff.

## Relationship to the monograph

The two-language monograph of the runs package (PDF + DOCX) lives in
[`monograph/`](../monograph/README.md) and is a different document: it is
the program-level treatment with the open-problems appendices, whereas
`docs/` holds the *collection* manuscripts that fed the individual papers.
The roles:

| Question | Go to |
|---|---|
| what did the final argument look like? | [`papers/`](../papers/README.md) (typeset) |
| what circulated editorially? | `docs/` (this directory) |
| what does the whole program look like as a book? | [`monograph/`](../monograph/README.md) |
| what backs every number? | [`data/results/`](../data/results/README.md) + [`verification/`](../verification/README.md) |

## Practical notes

The `.docx` files open in Word, LibreOffice and Google Docs without
conversion loss; embedded figures are the same renders shipped in
[`data/plots/`](../data/plots/README.md) and
[`monograph/open-problems/figures/`](../monograph/open-problems/figures/README.md).
The files are large (the monographs carry full-page figures) — clone with
git and edit locally rather than in-browser tools that re-encode the XML
and break the manifest hash.

---

Navigation: [repository root](../README.md) · [papers (PDF)](../papers/README.md) · [monograph](../monograph/README.md) · [src (LaTeX)](../src/README.md) · [IPL-RP-1.0](../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
