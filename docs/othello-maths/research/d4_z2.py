"""D4 x Z2 irrep projectors for the Othello 8x8 lattice.

Chess uses D4 (8 elements, 5 irreps) because Z2 colour inversion is
approximate (pawns break it, §9m).  Othello uses the full D4 x Z2
(16 elements, 10 irreps) because colour inversion is EXACT: swapping
all disc colours and flipping side-to-move gives a strategically
equivalent position.

Element indexing convention
---------------------------
Group element (g, z) with g in D4 (0..7) and z in Z2 (0 or 1).
Linear index into the 16-element group = 2*g + z.

    z = 0  : pure spatial D4 transform P_g applied to the signal.
    z = 1  : spatial transform *followed by* colour inversion s -> -s.

The character of the ten irreps factorises:

    chi_{mu,eps}(g, z) = chi_mu^{D4}(g) * eps^z

where mu in {A1, A2, B1, B2, E} and eps in {+1, -1}.  Irrep labels are
'A1+', 'A1-', ..., 'E+', 'E-'.  The '+' irreps are colour-even (Q in
section 10.3, the quadrupole moment); the '-' irreps are colour-odd
(magnetisation M).

Character projection (Serre 1977, section 2.6) — bypasses the
degenerate-subspace alignment problem that plagues direct
eigenvector decomposition.  For signal f in R^64:

    f_{mu,eps} = (d_mu / 16) * sum_{(g,z)} conj(chi_{mu,eps}(g,z))
                                            * ((g,z) . f)

where (g,z).f = (-1)^z * P_g f.  All characters are real so conj drops.
"""

from __future__ import annotations

import numpy as np

from othello_utils import N, BOARD_SIZE, rc_to_idx

# ---------------------------------------------------------------------------
# D4 spatial permutations on 64 vertices
# ---------------------------------------------------------------------------


def _make_perm(g: int) -> np.ndarray:
    """Permutation sigma such that (P_g f)[i] = f[sigma[i]]."""
    perm = np.zeros(N, dtype=int)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if g == 0:  # identity
                nr, nc = r, c
            elif g == 1:  # 90 CCW
                nr, nc = c, BOARD_SIZE - 1 - r
            elif g == 2:  # 180
                nr, nc = BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c
            elif g == 3:  # 270 CCW (= 90 CW)
                nr, nc = BOARD_SIZE - 1 - c, r
            elif g == 4:  # reflect across vertical axis
                nr, nc = r, BOARD_SIZE - 1 - c
            elif g == 5:  # reflect across horizontal axis
                nr, nc = BOARD_SIZE - 1 - r, c
            elif g == 6:  # reflect across main diagonal (r,c)->(c,r)
                nr, nc = c, r
            elif g == 7:  # reflect across anti-diagonal
                nr, nc = BOARD_SIZE - 1 - c, BOARD_SIZE - 1 - r
            else:
                raise ValueError(g)
            perm[rc_to_idx(r, c)] = rc_to_idx(nr, nc)
    return perm


D4_PERMS: list[np.ndarray] = [_make_perm(g) for g in range(8)]

# ---------------------------------------------------------------------------
# Character tables
# ---------------------------------------------------------------------------

# D4 character table, aligned to our element numbering:
#   g=0 E;  g=1 C4;  g=2 C2;  g=3 C4^-1
#   g=4 sigma_axis_v (col-flip); g=5 sigma_axis_h (row-flip)
#   g=6 sigma_diag_main (r<->c); g=7 sigma_diag_anti ((7-c, 7-r))
# Conjugacy classes (verified by direct calculation):
#   {E}, {C4, C4^-1}, {C2}, {g4, g5} axis-reflections,
#   {g6, g7} diagonal-reflections.
# Characters must be constant on each class.  Following the Dresselhaus
# convention (Dresselhaus-Dresselhaus-Jorio 2008 Table 6.3), B1 is +1
# on axis-reflections and -1 on diagonal-reflections; B2 swaps signs.
D4_CHARS: dict[str, np.ndarray] = {
    "A1": np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=float),
    "A2": np.array([1, 1, 1, 1, -1, -1, -1, -1], dtype=float),
    "B1": np.array([1, -1, 1, -1, 1, 1, -1, -1], dtype=float),
    "B2": np.array([1, -1, 1, -1, -1, -1, 1, 1], dtype=float),
    "E": np.array([2, 0, -2, 0, 0, 0, 0, 0], dtype=float),
}
D4_DIMS: dict[str, int] = {"A1": 1, "A2": 1, "B1": 1, "B2": 1, "E": 2}

Z2_CHARS: dict[str, np.ndarray] = {
    "+": np.array([1.0, 1.0]),  # z=0, z=1
    "-": np.array([1.0, -1.0]),
}

IRREP_LABELS: tuple[str, ...] = (
    "A1+", "A1-",
    "A2+", "A2-",
    "B1+", "B1-",
    "B2+", "B2-",
    "E+",  "E-",
)


def character_table_d4z2() -> dict[str, np.ndarray]:
    """Return {irrep_label -> length-16 character vector}, indexed by
    linear element index ``2*g + z``."""
    out: dict[str, np.ndarray] = {}
    for mu in ("A1", "A2", "B1", "B2", "E"):
        for eps in ("+", "-"):
            chi = np.zeros(16)
            for g in range(8):
                for z in range(2):
                    chi[2 * g + z] = (
                        D4_CHARS[mu][g] * Z2_CHARS[eps][z]
                    )
            out[f"{mu}{eps}"] = chi
    return out


# ---------------------------------------------------------------------------
# Group action on signals
# ---------------------------------------------------------------------------


def apply_element(sig: np.ndarray, g: int, z: int) -> np.ndarray:
    """Apply group element (g, z) to a 1D 64-signal or 2D (64, k) stack.

    The spatial permutation acts by ``f -> f[sigma]`` (so the value at
    site i becomes what was at site ``sigma[i]`` — equivalent to
    pushing the signal through the inverse permutation, which is the
    standard representation convention for a regular action).
    """
    arr = np.asarray(sig)
    perm = D4_PERMS[g]
    transformed = arr[perm] if arr.ndim == 1 else arr[perm, ...]
    if z == 1:
        transformed = -transformed
    return transformed


# ---------------------------------------------------------------------------
# Character projection
# ---------------------------------------------------------------------------


def project_irrep(sig: np.ndarray, irrep_label: str) -> np.ndarray:
    """Project a 64-signal onto a D4xZ2 irrep using the Serre formula.

    Returns a 64-vector (the irrep component of ``sig``).  For a
    Z2-odd signal (e.g. raw Blume-Capel magnetisation), all '+'
    projections are exactly 0; the signal lives entirely in the '-'
    subspace.  For a Z2-even signal (e.g. occupation s^2), the reverse.
    """
    if irrep_label not in IRREP_LABELS:
        raise ValueError(f"unknown irrep {irrep_label!r}")
    mu = irrep_label[:-1]
    eps = irrep_label[-1]
    d_mu = D4_DIMS[mu]
    chi_d4 = D4_CHARS[mu]
    chi_z2 = Z2_CHARS[eps]
    out = np.zeros_like(sig, dtype=float)
    for g in range(8):
        for z in range(2):
            chi = chi_d4[g] * chi_z2[z]
            out = out + chi * apply_element(sig, g, z)
    return (d_mu / 16.0) * out


def project_all(sig: np.ndarray) -> dict[str, np.ndarray]:
    """Return {irrep_label -> 64-vector} for all 10 irreps."""
    return {lbl: project_irrep(sig, lbl) for lbl in IRREP_LABELS}


def encode_concat(sig: np.ndarray) -> np.ndarray:
    """Length-640 encoder: concat of 10 D4xZ2 irrep projections, each
    a 64-vector.  Mirrors the chess D=640 layout, with Z2-eps
    taking over the role the chess pawn-antisymmetric fibre plays
    in §9a (colour symmetry is exact in Othello, approximate in chess).
    """
    projections = project_all(sig)
    return np.concatenate([projections[lbl] for lbl in IRREP_LABELS])


# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------


def sanity_character_orthogonality(tol: float = 1e-12) -> dict:
    """Check <chi_mu, chi_nu> / |G| = delta_{mu nu}."""
    chars = character_table_d4z2()
    labels = list(chars.keys())
    G = 16
    worst = 0.0
    for a in labels:
        for b in labels:
            inner = float(np.dot(chars[a], chars[b]) / G)
            expected = 1.0 if a == b else 0.0
            worst = max(worst, abs(inner - expected))
    return {"max_ortho_error": worst, "pass": worst < tol}


def sanity_group_action() -> dict:
    """Closure / associativity smoke: applying (e, 0) is identity;
    applying (g, 1) twice = applying (g^2, 0)."""
    rng = np.random.default_rng(0)
    sig = rng.standard_normal(N)
    identity_err = float(
        np.max(np.abs(apply_element(sig, 0, 0) - sig))
    )
    # (g=2 is 180 rotation, which is its own inverse)
    twice = apply_element(apply_element(sig, 2, 1), 2, 1)
    # First (2,1): rotate 180 + flip sign.  Second (2,1): rotate 180
    # again + flip sign -> returns to original.  So twice == sig.
    g2_err = float(np.max(np.abs(twice - sig)))
    return {
        "identity_err": identity_err,
        "g2_twice_err": g2_err,
        "pass": identity_err < 1e-12 and g2_err < 1e-12,
    }


def sanity_projection_idempotent(tol: float = 1e-12) -> dict:
    """Each projector P_mu is idempotent: P_mu P_mu = P_mu."""
    rng = np.random.default_rng(1)
    sig = rng.standard_normal(N)
    worst = 0.0
    for lbl in IRREP_LABELS:
        once = project_irrep(sig, lbl)
        twice = project_irrep(once, lbl)
        worst = max(worst, float(np.max(np.abs(twice - once))))
    return {"max_idempotency_err": worst, "pass": worst < tol}


def sanity_projection_completeness(tol: float = 1e-12) -> dict:
    """Sum of all 10 projections reproduces the original signal."""
    rng = np.random.default_rng(2)
    sig = rng.standard_normal(N)
    reconstructed = sum(project_irrep(sig, lbl) for lbl in IRREP_LABELS)
    err = float(np.max(np.abs(reconstructed - sig)))
    return {"reconstruction_err": err, "pass": err < tol}


def sanity_z2_parity(tol: float = 1e-12) -> dict:
    """A Z2-odd signal must project to zero on every '+' irrep;
    a Z2-even signal must project to zero on every '-' irrep."""
    rng = np.random.default_rng(3)
    odd = rng.standard_normal(N)           # generic, carries both parities
    # Antisymmetrise via Z2 projection to force odd parity:
    odd = 0.5 * (odd - apply_element(odd, 0, 1))  # odd
    even = rng.standard_normal(N)
    even = 0.5 * (even + apply_element(even, 0, 1))  # even

    worst_even_on_minus = 0.0
    for lbl in IRREP_LABELS:
        if lbl.endswith("-"):
            worst_even_on_minus = max(
                worst_even_on_minus,
                float(np.max(np.abs(project_irrep(even, lbl)))),
            )
    worst_odd_on_plus = 0.0
    for lbl in IRREP_LABELS:
        if lbl.endswith("+"):
            worst_odd_on_plus = max(
                worst_odd_on_plus,
                float(np.max(np.abs(project_irrep(odd, lbl)))),
            )
    return {
        "max_even_on_minus": worst_even_on_minus,
        "max_odd_on_plus": worst_odd_on_plus,
        "pass": (
            worst_even_on_minus < tol and worst_odd_on_plus < tol
        ),
    }


if __name__ == "__main__":
    print("=== d4_z2 sanity ===")
    r = sanity_character_orthogonality()
    print(
        f"character orthogonality: max |<chi_mu,chi_nu>/|G| - delta| = "
        f"{r['max_ortho_error']:.3e}, PASS = {r['pass']}"
    )
    r = sanity_group_action()
    print(
        f"group action: identity err = {r['identity_err']:.3e}, "
        f"(g2)^2 err = {r['g2_twice_err']:.3e}, PASS = {r['pass']}"
    )
    r = sanity_projection_idempotent()
    print(
        f"projection idempotence: max err = "
        f"{r['max_idempotency_err']:.3e}, PASS = {r['pass']}"
    )
    r = sanity_projection_completeness()
    print(
        f"projection completeness: reconstruction err = "
        f"{r['reconstruction_err']:.3e}, PASS = {r['pass']}"
    )
    r = sanity_z2_parity()
    print(
        f"Z2 parity split: even on '-' = {r['max_even_on_minus']:.3e}, "
        f"odd on '+' = {r['max_odd_on_plus']:.3e}, PASS = {r['pass']}"
    )
