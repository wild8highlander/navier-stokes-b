"""NSB Research Lab — falsification-oriented numerical laboratory for the 3D
Navier-Stokes regularity question.

This package extends the repository's algebraic verifiers (sections 1-7) with
a dynamical layer: a dealiased pseudospectral Navier-Stokes solver on the 3D
torus, singularity diagnostics (Beale-Kato-Majda monitors, enstrophy,
palinstrophy, spectral tails), and a resolution-extrapolation protocol.

Design contract mirrors the repository verifiers:
    banner -> per-assertion [PASS]/[FAIL] -> JSON verdict line -> exit code.

Language: all human-readable output is switchable (EN/RU) via --lang or the
NSB_LAB_LANG environment variable; JSON keys stay in English (machine
contract). Documentation: README.md (EN) / README.ru.md (RU).
"""

__version__ = "0.1.0"
