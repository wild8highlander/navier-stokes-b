# `Common/` — the Lean foundation module

> **Navigation:** [repository root](../../../README.md) › [verification](../../../verification/README.md) › [lean4](../../README.md) › [ResearchPapersVerification](../README.md) › **`Common`**

![Module](https://img.shields.io/badge/Foundation.lean-informational?style=flat-square) ![Role](https://img.shields.io/badge/shared-2EA043?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

`Foundation.lean` is imported by every section module: it declares the
constant `bCorrection` with its pinned precision, the positivity and
range lemmas every section reuses, and the shared notation. Keeping these
facts in one module is what makes the cross-section consistency
mechanical — a section cannot silently re-define the constant.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
