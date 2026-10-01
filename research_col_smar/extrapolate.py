"""Resolution-extrapolation protocol: the honest "extrapolate to infinity".

The laboratory cannot extrapolate over ALL initial data (the Clay question is
infinite-dimensional — see README). What it CAN do, and does here, is turn
any computed diagnostic J (BKM integral at the horizon, enstrophy peak, ...)
into a *verified-for-the-computed-solution* statement by two ladders:

    1. temporal ladder: dt, dt/2, dt/4 — for the RK4 integrator the observed
       order p must approach 4; Richardson extrapolation then estimates
       J(dt -> 0) with an explicit error bar;
    2. spatial ladder: N, 2N — for a spectral method the monitor sequence
       stabilizes once the field is resolved; the gap |J_N - J_2N| IS the
       resolution error bar (exponential convergence makes Richardson
       fitting meaningless here — we report the gap instead).

Verdict semantics (JSON keys in English by contract):
    all_passed       — the computation is internally consistent (orders
                       recovered, gaps small, incompressibility held);
    extrapolated     — the dt->0 estimate and its error bar;
    resolution_gap   — the |J_N - J_2N| spatial error bar.
"""
import math
from collections.abc import Callable

DEFAULT_LADDER = (1.0, 0.5, 0.25)


def observed_order(j_c: float, j_f: float, j_ff: float, ratio: float = 2.0
                   ) -> float:
    """Observed convergence order from a geometric refinement triplet."""
    denom = j_c - j_f
    numer = j_f - j_ff
    if abs(denom) < 1e-30 or abs(numer) < 1e-30:
        return float("nan")
    return math.log(abs(denom / numer), ratio)


def richardson(j_f: float, j_ff: float, ratio: float, order: float) -> float:
    """Richardson estimate of J(0) from the two finest levels."""
    return j_ff + (j_ff - j_f) / (ratio**order - 1.0)


def temporal_ladder(runner: Callable[[float], float],
                    ladder: tuple[float, ...] = DEFAULT_LADDER,
                    expected_order: float = 4.0,
                    order_tol: float = 0.75) -> dict:
    """Run the monitor J at dt levels and verify the RK4 order + extrapolate.

    runner(dt) must return the diagnostic value J for that time step.
    """
    values = [runner(dt) for dt in ladder]
    p = observed_order(values[0], values[1], values[2], 2.0)
    dt0 = ladder[0]
    dt1 = ladder[1]
    dt2 = ladder[2]
    extrap = richardson(values[1], values[2], 2.0, p if p == p else expected_order)
    gap_fine = abs(values[1] - values[2])
    order_ok = abs(p - expected_order) <= order_tol if p == p else False
    return {
        "values": values,
        "ladder": list(ladder),
        "dt_coarse": dt0,
        "dt_fine": dt1,
        "dt_finest": dt2,
        "observed_order": p,
        "expected_order": expected_order,
        "order_ok": bool(order_ok),
        "extrapolated": float(extrap),
        "error_bar_fine": float(gap_fine),
        "temporal_ok": bool(order_ok and gap_fine < abs(values[2]) + 1e-12),
    }


def spatial_ladder(runner: Callable[[int], float], base: int,
                   factor: int = 2) -> dict:
    """Run the monitor J at N and factor*N; report the stabilization gap."""
    j_base = runner(base)
    j_fine = runner(base * factor)
    gap = abs(j_fine - j_base)
    return {
        "n_coarse": base,
        "n_fine": base * factor,
        "value_coarse": j_base,
        "value_fine": j_fine,
        "resolution_gap": float(gap),
        "relative_gap": float(gap / max(abs(j_fine), 1e-30)),
        "resolved": bool(gap <= 0.05 * max(abs(j_fine), 1e-30)),
    }
