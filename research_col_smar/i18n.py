"""Switchable output language for the laboratory (EN/RU).

The "language button": every human-readable string is stored in both
languages and resolved by :func:`tr`. The language is chosen by an explicit
argument, else the NSB_LAB_LANG environment variable, else English.
JSON verdict keys are deliberately NOT translated: they are a machine
contract shared with the repository verifiers.
"""
import os

LANGS = ("en", "ru")

STRINGS = {
    "banner": {
        "en": "NSB Research Lab — {title}",
        "ru": "NSB Научная лаборатория — {title}",
    },
    "params": {
        "en": "parameters: {params}",
        "ru": "параметры: {params}",
    },
    "pass": {"en": "[PASS]", "ru": "[УСПЕХ]"},
    "fail": {"en": "[FAIL]", "ru": "[СБОЙ]"},
    "progress_header": {
        "en": "    t          E(t)        Omega(t)    sup|w|     BKM int",
        "ru": "    t          E(t)        энстрофия   sup|w|     интеграл BKM",
    },
    "verdict_ok": {
        "en": "VERIFICATION: all assertions passed",
        "ru": "ВЕРИФИКАЦИЯ: все проверки пройдены",
    },
    "verdict_fail": {
        "en": "VERIFICATION: FAILURES PRESENT",
        "ru": "ВЕРИФИКАЦИЯ: ЕСТЬ СБОИ",
    },
    "blowup_no": {
        "en": "no singularity detected within the (N, T, dt) window tested",
        "ru": "сингулярность в пределах окна (N, T, dt) не обнаружена",
    },
    "blowup_yes": {
        "en": "near-singularity INDICATORS PRESENT — resolution window exhausted",
        "ru": "ЕСТЬ индикаторы околосингулярного поведения — окно разрешения исчерпано",
    },
    "check_div": {
        "en": "incompressibility: max |div u| stays at roundoff",
        "ru": "несжимаемость: max |div u| остаётся на уровне округления",
    },
    "check_energy_decay": {
        "en": "unforced decay: energy is non-increasing along the run",
        "ru": "свободное затухание: энергия не возрастает вдоль прогона",
    },
    "check_enstrophy_finite": {
        "en": "enstrophy peak exists, is finite at the tested resolution",
        "ru": "пик энстрофии существует и конечен при испытанном разрешении",
    },
    "check_temporal_order": {
        "en": "temporal convergence: dt-halving recovers the RK4 order 4",
        "ru": "временная сходимость: уменьшение dt вдвое даёт порядок RK4 (4)",
    },
    "check_resolution": {
        "en": "spatial resolution: cutoff-shell energy negligible vs peak",
        "ru": "пространственное разрешение: энергия у обрезания ничтожна против пика",
    },
    "check_symmetry": {
        "en": "exact rotation symmetry relabels the flow: diagnostics identical",
        "ru": "точная поворотная симметрия лишь переименовывает поле: диагностика совпадает",
    },
    "check_isometry": {
        "en": "pointwise b-rotation is an isometry: energy preserved to roundoff",
        "ru": "поточечный b-поворот — изометрия: энергия сохраняется до округления",
    },
    "check_incompressibility_break": {
        "en": "pointwise b-rotation BREAKS div-free (documented, reprojected)",
        "ru": "поточечный b-поворот НАРУШАЕТ соленоидальность (поле перепроецируется)",
    },
    "check_bkm_finite": {
        "en": "BKM integral stays bounded on the tested horizon",
        "ru": "интеграл BKM остаётся ограниченным на испытанном горизонте",
    },
    "check_vorticity_growth": {
        "en": "vorticity amplification tracked, self-similar fit reported",
        "ru": "рост завихренности отслежен, самоподобная аппроксимация приведена",
    },
    "scope_note": {
        "en": (
            "scope: statements produced here are window-limited numerical "
            "evidence, not proofs of global regularity"
        ),
        "ru": (
            "рамка: утверждения здесь — численные свидетельства в пределах окна, "
            "а не доказательства глобальной гладкости"
        ),
    },
}


class Lang:
    """Tiny translation accessor: Lang("ru")("pass")."""

    def __init__(self, lang: str | None = None) -> None:
        if lang is None:
            lang = os.environ.get("NSB_LAB_LANG", "en")
        self.lang = lang if lang in LANGS else "en"

    def __call__(self, key: str) -> str:
        return STRINGS[key][self.lang]

    def fmt(self, key: str, **kwargs) -> str:
        return STRINGS[key][self.lang].format(**kwargs)
