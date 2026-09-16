# Verification Framework

Multi-language computational verification of six interconnected research papers.

## Languages

### Original (numerical + symbolic)
- Python (NumPy, SciPy, Matplotlib)
- Julia (LinearAlgebra, SpecialFunctions)
- Java (Apache Commons Math)
- Wolfram (Mathematica)
- TypeScript (Next.js dashboard)

### Extended — Formal proofs
- Lean 4 (Mathlib4 hybrid)
- Coq (Reals, Lra)
- Isabelle/HOL (Complex_Main)
- Agda (dependent types)

### Extended — Numerical
- Rust (ndarray)
- C++ (STL)
- Haskell (cabal)

## Build

```bash
make verify-all       # original languages
make verify-extended  # 7 new languages
```

## Docker

```bash
make docker-up
```


---

## 📜 About This Historical File

This was the **original verification framework description** — the short README that introduced the multi-language verification idea when the framework was smaller. It is preserved verbatim for provenance: the folder-level documentation reform (which gave every subdirectory its own README and expanded this one into the full [README.md](README.md)) kept this file untouched so that early references, bookmarks and citations to it remain meaningful.

**What changed since this file was current:**

| Then | Now |
|---|---|
| six Python sections + first formal ports | eleven languages: 4 proof assistants + 7 computational |
| ad-hoc per-language instructions | uniform [output contract](README.md#-the-verification-contract) + JSON verdicts |
| manual cross-checking | mechanical: [`tests/extended_cross_language_validator.py`](tests/README.md) in CI |
| no containers | one pinned Docker image per toolchain ([`docker/`](docker/README.md)) |

**Read this file** for the framework's origin story and its founding motivation (why cross-verification at all). **Read [README.md](README.md)** for everything operational: the matrix, the commands, the infrastructure, the CI wiring.

---
## 🏛 Why This File Survived the Rewrite

Two reasons, both deliberate:

1. **Provenance.** External references to this file (talks, notes, bookmarks) stay meaningful — the file they pointed at still exists, still says what it said.
2. **Honesty of the record.** The framework's growth (six sections → eleven languages, ad-hoc → contract) is part of its credibility. Keeping the original short description next to the current one makes the growth visible instead of airbrushed.

The same policy preserves the original v21 monographs next to v22 — the repository keeps its history readable. Related records: the [timeline](../README.md#-appendix-i--historical-timeline) and the [CHANGELOG](../CHANGELOG.md).

---
**One more pointer.** If you arrived here from an old link expecting commands — everything operational now lives in [`README.md`](README.md) (the full framework guide) and the root README's [command reference](../README.md#%EF%B8%8F-appendix-k--full-command-reference). This file remains the historical introduction.
