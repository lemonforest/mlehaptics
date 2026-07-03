"""rc105 — `magnetic_laplacian(..., charges=[...])` per-edge charge: the
CHIRAL Laplacian for dual-sense knowledge graphs (issue #1234 Item 3 /
F1006 / F1007).

WHY (the honesty-driven encoding fix): F1006's is-a / is-not-a knowledge
audit showed the real ``signed_laplacian`` ANNIHILATES a dual-sense edge —
"X is-a Y" (+1) and "X is-not-a Y" (−1) sum to 0, so a genuine dual sense
(Brown *is* a pigment color / *is not* a spectral color) reads as
"balanced" and vanishes. F1007: move the two senses onto the phase circle —
is-a = e^{+i·2π·q} and is-not-a = e^{−i·2π·q} are conjugate partners that
SURVIVE: symmetric content in the real cosine, the is-a/is-not-a IMBALANCE
in the imaginary sine residue (chiral flux, not cancellation).

Covers:
  (a) the DoD audit fixture — signed annihilation (off-diagonal == 0.0)
      vs magnetic-charges survival (non-zero complex off-diagonal);
  (b) the imaginary residue −(a−b)/2·sin(2πq) carrying the imbalance;
  (c) Hermiticity EXACT by construction (incl. self-loops + reciprocal
      directions) + PSD spectrum via the Hermitian eigensolver;
  (d) integer-flux periodicity (approximate — a full turn per edge);
  (e) the q ⊕ charges mutual-exclusion / length-validation / TypeError
      contracts + byte-for-byte scalar back-compat;
  (f) pure == native EXACT parity (==, no tolerance) in BOTH modes —
      the C peer runs the same Q61 trig cascade.

numpy-free; no ``abs()`` (Class-K sign-branch where a magnitude is read).
"""
import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as L


# ── helpers (no numpy, no abs()) ────────────────────────────────────────


def _mag(x):
    """Class-K sign-branch magnitude (never abs())."""
    return x if x >= 0 else -x


def _force_pure(fn):
    """Run fn with the native dispatch masked (the complete pure path)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def _mat_exactly_equal(a, b):
    """Entry-by-entry EXACT (==) comparison of two Mat carriers."""
    if a.shape != b.shape:
        return False
    nr, nc = a.shape
    return all(a[i, j] == b[i, j] for i in range(nr) for j in range(nc))


# The dual-sense fixture (the F1006 audit shape): node 0 = "brown",
# node 1 = "pigment-color"; edge (0, 1) carries BOTH senses —
# is-a (weight a, charge +q) and is-not-a (weight b, charge −q).
# q = 0.125 turns (an eighth turn: cos = sin = √2/2, so BOTH the real
# and imaginary channels are live — q = 0.25 would zero the cosine).
_Q = 0.125


def _dual_sense_edges(a, b):
    edges = [(0, 1), (0, 1)]
    weights = [a, b]
    charges = [+_Q, -_Q]
    return edges, weights, charges


# ── (a) the DoD audit fixture: annihilation vs survival ────────────────


def test_signed_laplacian_annihilates_dual_sense():
    """The real signed Laplacian: +1 (is-a) and −1 (is-not-a) sum to 0 —
    the dual-sense relationship VANISHES from the off-diagonal."""
    Ls = L.signed_laplacian(2, [(0, 1), (0, 1)], weights=[+1.0, -1.0])
    assert Ls[0, 1] == 0.0          # annihilated: reads as "no relationship"
    assert Ls[1, 0] == 0.0
    # control: a single sense alone is visible
    Ls1 = L.signed_laplacian(2, [(0, 1)], weights=[+1.0])
    assert Ls1[0, 1] != 0.0


def test_magnetic_charges_preserve_dual_sense():
    """The chiral Laplacian: the same dual-sense pair SURVIVES as the
    conjugate-partner sum −(a+b)/2·cos(2πq) (balanced ⇒ real, non-zero)."""
    edges, weights, charges = _dual_sense_edges(1.0, 1.0)
    Lm = L.magnetic_laplacian(2, edges, weights, charges=charges)
    off = Lm[0, 1]
    assert off != 0                 # SURVIVES (contrast the signed 0.0)
    # balanced senses (a == b): the imaginary residue is zero...
    assert off.imag == 0.0
    # ...and the real part is the conjugate-partner cosine sum
    # −(a+b)/2·cos(2π·0.125) = −cos(π/4) ≈ −0.7071.
    expected_re = -float(L._rcos(2.0 * L._PI * _Q))
    assert _mag(off.real - expected_re) < 1e-15
    assert off.real < 0.0


# ── (b) the imaginary residue carries the is-a/is-not-a imbalance ──────


def test_imaginary_residue_carries_imbalance():
    """Asymmetric senses (a ≠ b): Im(L[0,1]) = −(a−b)/2·sin(2πq) ≠ 0 —
    the imbalance registers as chiral flux, not cancellation."""
    a, b = 2.0, 1.0
    edges, weights, charges = _dual_sense_edges(a, b)
    Lm = L.magnetic_laplacian(2, edges, weights, charges=charges)
    off = Lm[0, 1]
    s = float(L._rsin(2.0 * L._PI * _Q))
    expected_im = -((a - b) / 2.0) * s
    assert off.imag != 0.0
    assert _mag(off.imag - expected_im) < 1e-15
    # the sign of the residue tracks the sign of the imbalance (a − b)
    Lm_flip = L.magnetic_laplacian(
        2, edges, [b, a], charges=charges
    )
    assert Lm_flip[0, 1].imag > 0.0 > off.imag
    # the real channel still carries the symmetric content
    expected_re = -((a + b) / 2.0) * float(L._rcos(2.0 * L._PI * _Q))
    assert _mag(off.real - expected_re) < 1e-15


# ── (c) Hermiticity + PSD spectrum ─────────────────────────────────────


def _mixed_graph():
    """A mixed is-a/is-not-a graph: dual-sense pair on (0,1), a lone
    is-a on (1,2), a lone is-not-a on (2,0), a reciprocal-direction
    edge (2,1) and a self-loop (3,3)."""
    n = 4
    edges = [(0, 1), (0, 1), (1, 2), (2, 0), (2, 1), (3, 3)]
    weights = [2.0, 1.0, 1.5, 1.0, 0.5, 1.0]
    charges = [+_Q, -_Q, +_Q, -_Q, +0.0625, +_Q]
    return n, edges, weights, charges


def test_charges_hermitian_exact():
    """L[i,j] == conj(L[j,i]) EXACTLY (by construction: the two writes per
    edge are exact conjugates), and the diagonal is real."""
    n, edges, weights, charges = _mixed_graph()
    Lm = L.magnetic_laplacian(n, edges, weights, charges=charges)
    for i in range(n):
        for j in range(n):
            assert Lm[i, j] == Lm[j, i].conjugate()
    for i in range(n):
        assert Lm[i, i].imag == 0.0
        assert Lm[i, i].real >= 0.0     # magnitude degree


def test_charges_psd_spectrum():
    """Each edge contributes a PSD 2×2 block ⇒ the chiral Laplacian is PSD;
    the Hermitian eigensolver returns real, non-negative eigenvalues."""
    n, edges, weights, charges = _mixed_graph()
    Lm = L.magnetic_laplacian(n, edges, weights, charges=charges)
    ev, _ = L.hermitian_eigendecompose(Lm)
    assert all(not isinstance(e, complex) for e in ev)
    assert min(ev) >= -1e-9


def test_direction_charge_equivalence():
    """(u, v, c) ≡ (v, u, −c): flipping BOTH the edge direction and the
    charge sign leaves the matrix unchanged (exact)."""
    La = L.magnetic_laplacian(3, [(0, 1), (1, 2)], [1.0, 2.0],
                              charges=[+_Q, -0.0625])
    Lb = L.magnetic_laplacian(3, [(1, 0), (2, 1)], [1.0, 2.0],
                              charges=[-_Q, +0.0625])
    assert _mat_exactly_equal(La, Lb)


# ── (d) integer-flux periodicity ───────────────────────────────────────


def test_integer_flux_periodicity():
    """Charges are in TURNS: c and c + 1 (a full extra turn per edge) give
    the same matrix (up to the float 2π·(c+1) round-off — approximate)."""
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [1.0, 2.0, 0.5]
    La = L.magnetic_laplacian(3, edges, weights, charges=[_Q, -_Q, 0.0625])
    Lb = L.magnetic_laplacian(3, edges, weights,
                              charges=[_Q + 1.0, -_Q + 1.0, 1.0625])
    for i in range(3):
        for j in range(3):
            d = La[i, j] - Lb[i, j]
            assert _mag(d.real) < 1e-9 and _mag(d.imag) < 1e-9


# ── (e) the q ⊕ charges contract + scalar back-compat ──────────────────


def test_q_and_charges_mutually_exclusive():
    with pytest.raises(ValueError):
        L.magnetic_laplacian(2, [(0, 1)], q=0.25, charges=[0.25])
    with pytest.raises(ValueError):
        L.magnetic_laplacian(2, [(0, 1)], q=0.0, charges=[0.25])


def test_charges_length_must_match_edges():
    with pytest.raises(ValueError):
        L.magnetic_laplacian(2, [(0, 1)], charges=[0.25, 0.25])
    with pytest.raises(ValueError):
        L.magnetic_laplacian(3, [(0, 1), (1, 2)], charges=[0.25])


def test_charges_edge_validation_still_applies():
    with pytest.raises(ValueError):
        L.magnetic_laplacian(2, [(0, 5)], charges=[0.25])


def test_empty_graph_charges():
    Lm = L.magnetic_laplacian(3, [], charges=[])
    for i in range(3):
        for j in range(3):
            assert Lm[i, j] == 0.0


def test_scalar_backcompat_unset_q_is_quarter_turn():
    """q unset == q=0.25 explicitly (the rc28 default), exact."""
    edges = [(0, 1), (1, 2), (2, 0)]
    La = L.magnetic_laplacian(3, edges)
    Lb = L.magnetic_laplacian(3, edges, q=0.25)
    assert _mat_exactly_equal(La, Lb)


def test_scalar_backcompat_type_errors_preserved():
    """Junk q still raises the SAME TypeError as rc104 (the sentinel does
    not relax the q contract)."""
    with pytest.raises(TypeError):
        L.magnetic_laplacian(2, [(0, 1)], q=None)
    with pytest.raises(TypeError):
        L.magnetic_laplacian(2, [(0, 1)], q="0.25")
    with pytest.raises(TypeError):
        L.magnetic_laplacian(2, [(0, 1)], q=1j)


# ── (f) pure == native EXACT parity (both modes) ───────────────────────


def test_scalar_mode_pure_native_parity_exact():
    """The C peer runs the SAME Q61 trig cascade as the pure path — the
    scalar-q construction is bit-identical (==, no tolerance)."""
    edges = [(0, 1), (1, 2), (2, 0), (0, 2), (1, 1)]
    weights = [1.0, 2.0, 0.5, 3.0, 1.0]
    La = L.magnetic_laplacian(4, edges, weights, q=0.3)
    Lb = _force_pure(lambda: L.magnetic_laplacian(4, edges, weights, q=0.3))
    assert _mat_exactly_equal(La, Lb)


def test_charges_mode_pure_native_parity_exact():
    """Per-edge charges: native == pure EXACTLY on the mixed fixture."""
    n, edges, weights, charges = _mixed_graph()
    La = L.magnetic_laplacian(n, edges, weights, charges=charges)
    Lb = _force_pure(
        lambda: L.magnetic_laplacian(n, edges, weights, charges=charges)
    )
    assert _mat_exactly_equal(La, Lb)


def test_charges_mode_matches_pure_helper_exact():
    """The public op equals the pure construction helper entry-for-entry
    (native or not — the dispatch may not change a single bit)."""
    n, edges, weights, charges = _mixed_graph()
    el, wl = L._validate_edges_weights_py(n, edges, weights)
    rows = L._magnetic_laplacian_charges_py(n, el, wl, list(charges))
    Lm = L.magnetic_laplacian(n, edges, weights, charges=charges)
    for i in range(n):
        for j in range(n):
            assert Lm[i, j] == rows[i][j]


def test_scalar_mode_matches_rc28_construction_exact():
    """charges=None is byte-for-byte the rc28 scalar construction (the
    pure scalar path was split out verbatim as _magnetic_laplacian_scalar_py)."""
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [1.0, 2.0, 0.5]
    el, wl = L._validate_edges_weights_py(3, edges, weights)
    rows = L._magnetic_laplacian_scalar_py(3, el, wl, 0.25)
    Lm = L.magnetic_laplacian(3, edges, weights, q=0.25)
    for i in range(3):
        for j in range(3):
            assert Lm[i, j] == rows[i][j]
