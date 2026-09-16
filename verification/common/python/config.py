"""Configuration system for all verification sections."""
from dataclasses import dataclass, field
from typing import Any, Dict, List

PRESETS = {
    "quick":   {"N": 16,  "tolerance": 1e-3,  "max_iter": 1000},
    "default": {"N": 36,  "tolerance": 1e-10, "max_iter": 10000},
    "full":    {"N": 64,  "tolerance": 1e-14, "max_iter": 50000},
    "extreme": {"N": 128, "tolerance": 1e-16, "max_iter": 100000},
}

SECTION_NAMES = {
    1: "Correction b & 3D NSE Regularity",
    2: "Preprint: Analytical Proof of 3D NSE Regularity",
    3: "AB-Cloud Monograph",
    4: "KdV & b-Correction",
    5: "Klein Attractor & NS Bridge",
    6: "AB-Cloud / Riemann Zeros",
}

def get_config(section_id=1, preset="default"):
    return PRESETS.get(preset, PRESETS["default"])
