"""The universal b-correction constants, shared with repository sections 1-7.

b = 1/(4*pi + 2*sqrt(3)), theta_b = arcsin(b), and the reference rotation
matrix R(theta_b, axis) built exactly as in verification/section2_preprint.
Everything here is pure stdlib so the module also runs inside the multi-
language verifier contract.
"""
import math

B = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
THETA_B = math.asin(B)
# same axis as section 2 of the repository (unit norm, deterministic)
AXIS = (0.3, -0.5, math.sqrt(1.0 - 0.3**2 - 0.5**2))


def rodrigues(theta: float, axis: tuple[float, float, float]) -> list[list[float]]:
    """Rotation matrix about a unit axis (Rodrigues formula)."""
    ex, ey, ez = axis
    cross_mat = [[0.0, -ez, ey], [ez, 0.0, -ex], [-ey, ex, 0.0]]
    outer = [[ex * ex, ex * ey, ex * ez],
             [ey * ex, ey * ey, ey * ez],
             [ez * ex, ez * ey, ez * ez]]
    c, s = math.cos(theta), math.sin(theta)
    return [[(1.0 if i == j else 0.0) * c + (1.0 - c) * outer[i][j]
             - s * cross_mat[i][j]
             for j in range(3)] for i in range(3)]


def b_rotation_matrix() -> list[list[float]]:
    """The reference b-rotation R(theta_b, AXIS) used across the repository."""
    return rodrigues(THETA_B, AXIS)


def quarter_rotation_matrix() -> list[list[float]]:
    """Grid-matching rotation (pi/2 about z): maps the torus grid onto itself.

    Used to test the EXACT symmetry of the equations: u'(x) = R u(R^-1 x)
    with R a symmetry of the periodic lattice is a relabeling, so every
    diagnostic must be identical. theta_b does NOT map the grid onto itself,
    which is precisely why the full-symmetry test uses a quarter turn while
    the isometry test uses the b-rotation itself.
    """
    return rodrigues(math.pi / 2.0, (0.0, 0.0, 1.0))
