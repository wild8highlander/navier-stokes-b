"""Shared runner plumbing: presets, verdict assembly, printing, JSON line."""
from __future__ import annotations

import json
import sys
import time as _time

from research_lab.i18n import Lang

PRESETS: dict[str, dict] = {
    "smoke": {"n": 16, "t_horizon": 1.0, "nu": 0.1, "dt": 0.01},
    "default": {"n": 32, "t_horizon": 2.0, "nu": 0.02, "dt": 0.005},
    "deep": {"n": 64, "t_horizon": 4.0, "nu": 0.01, "dt": 0.0025},
}


class Verdict:
    """Collects named assertions and renders the repo-standard contract."""

    def __init__(self, experiment: str, lang: Lang, params: dict) -> None:
        self.experiment = experiment
        self.lang = lang
        self.params = dict(params)
        self.checks: list[tuple[str, bool, str]] = []
        self.values: dict = {}
        self.extra: dict = {}
        self._t0 = _time.time()

    def check(self, key: str, ok: bool, detail: str = "") -> bool:
        self.checks.append((key, bool(ok), detail))
        return bool(ok)

    def finish(self) -> int:
        all_ok = all(ok for _, ok, _ in self.checks)
        wall = round(_time.time() - self._t0, 2)
        for key, ok, detail in self.checks:
            status = self.lang("pass") if ok else self.lang("fail")
            line = f"{status} {self.lang(key)}"
            if detail:
                line += f"  ({detail})"
            print(line)
        print(self.lang.fmt("scope_note"))
        verdict = {
            "verifier": "research_lab",
            "experiment": self.experiment,
            "language": "python",
            "values": self.values,
            "all_passed": all_ok,
            "wall_seconds": wall,
        }
        verdict.update(self.extra)
        print("JSON: " + json.dumps(verdict, ensure_ascii=False))
        print(self.lang("verdict_ok") if all_ok else self.lang("verdict_fail"))
        return 0 if all_ok else 1


def banner(lang: Lang, title_key_params: str, params: dict) -> None:
    print("=== " + lang.fmt("banner", title=title_key_params) + " ===")
    print(lang.fmt("params", params=", ".join(
        f"{k}={v}" for k, v in params.items())))


def progress_header(lang: Lang) -> None:
    print(lang("progress_header"))


def eprint(*args) -> None:
    print(*args, file=sys.stderr)
