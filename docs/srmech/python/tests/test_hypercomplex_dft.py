"""v0.7.0rc31 — quaternion/octonion DFT composites (#863, F380).

The native transform for a Klein-4 object: its ℍ coefficient algebra resolves
BOTH Z₂ chirality axes the complex FFT collapses (the flat shadow). Klein-4 =
Q₈/{±1} ≅ Z₂×Z₂. These are composites over the qm.octonion left/right-mult
atoms — scientific tier (§22: numpy on call), but `import srmech.amsc.cascade`
stays numpy-free.
"""
import math
import sys

import pytest

from srmech.amsc.cascade import quaternion_dft, octonion_dft, hypercomplex_couple


# --- Klein-4 <-> quaternion encoding (bit0 -> i-comp sign, bit1 -> j-comp sign) ---

def _enc(s):
    """Klein-4 sector s∈{0,1,2,3} -> quaternion [0, ±1(i), ±1(j), 0]."""
    return [0.0, 1.0 - 2 * (s & 1), 1.0 - 2 * ((s >> 1) & 1), 0.0]


def _dec(q):
    """Quaternion -> Klein-4 sector (sign of i-comp = bit0, sign of j-comp = bit1)."""
    bit0 = 0 if q[1] > 0 else 1
    bit1 = 0 if q[2] > 0 else 1
    return bit0 | (bit1 << 1)


# --- the whole module is numpy-free (rc125 #564) -----------------------------

def test_cascade_import_is_numpy_free():
    """The hypercomplex_dft module is numpy-FREE (rc125 #564): the DFT
    composites carry their octonion vectors as ``list[float]`` and the
    octonion-rep operators as the numpy-free :class:`srmech.amsc.mat.Mat`, so
    the module source has ZERO numpy — no top-level import, no ``np.`` callsite,
    no lazy proxy."""
    import inspect
    import re
    from srmech.amsc.cascade import hypercomplex_dft
    src = inspect.getsource(hypercomplex_dft)
    assert "import numpy" not in src, "hypercomplex_dft imports numpy"
    assert not re.search(r"\bnp\.", src), "hypercomplex_dft has an np. callsite"


# --- QDFT round-trip recovers ALL FOUR components (both Z₂ axes) --------------

@pytest.mark.parametrize("form", ["left", "right"])
def test_quaternion_dft_round_trip(form):
    import random
    rng = random.Random(0)
    q = [[rng.uniform(-1, 1) for _ in range(4)] for _ in range(6)]
    X = quaternion_dft(q, form=form)
    qr = quaternion_dft(X, form=form, inverse=True)
    assert len(qr) == len(q)
    for r, o in zip(qr, q):
        assert len(r) == 4
        for a, b in zip(r, o):
            assert abs(a - b) < 1e-9


@pytest.mark.parametrize("mu_axis", ["i", "j", "k", "ijk"])
def test_quaternion_dft_round_trip_each_axis(mu_axis):
    q = [[0.5, -1.0, 0.25, 0.75], [1.0, 0.0, -0.5, 0.5], [-0.25, 0.5, 1.0, -1.0]]
    X = quaternion_dft(q, form="left", mu_axis=mu_axis)
    qr = quaternion_dft(X, form="left", mu_axis=mu_axis, inverse=True)
    for r, o in zip(qr, q):
        for a, b in zip(r, o):
            assert abs(a - b) < 1e-9


# --- the load-bearing DoD: Klein-4 both axes preserved vs the flat shadow -----

def test_klein4_object_both_axes_preserved():
    """QDFT round-trips a Klein-4 object and recovers BOTH Z₂ axes."""
    sectors = [0, 1, 2, 3, 1, 2, 3, 0]
    ks = [_enc(s) for s in sectors]
    X = quaternion_dft(ks, form="left")
    kr = quaternion_dft(X, form="left", inverse=True)
    assert [_dec(q) for q in kr] == sectors


def test_complex_fft_collapses_one_axis_the_flat_shadow():
    """The measurable contrast: a COMPLEX FFT must first project the quaternion
    to ℂ (q0 + q1·i), which drops the j-component = bit1. Its round-trip
    recovers bit0 but bit1 is gone — the flat shadow the QDFT does NOT cast."""
    import cmath
    sectors = [0, 1, 2, 3, 1, 2, 3, 0]
    ks = [_enc(s) for s in sectors]
    # complex projection drops the j-comp (bit1):
    cz = [complex(q[0], q[1]) for q in ks]
    n = len(cz)
    cx = [sum(cz[m] * cmath.exp(-2j * math.pi * k * m / n) for m in range(n)) for k in range(n)]
    cr = [sum(cx[k] * cmath.exp(2j * math.pi * k * m / n) for k in range(n)) / n for m in range(n)]
    # bit0 (i-comp sign) survives the complex round-trip:
    rec_bit0 = [0 if c.imag > 0 else 1 for c in cr]
    assert rec_bit0 == [s & 1 for s in sectors]
    # ...but bit1 (j-comp) was projected away — it is NOT in cr at all.
    true_bit1 = [(s >> 1) & 1 for s in sectors]
    assert any(true_bit1), "test needs at least one set bit1"
    # The complex carrier has no second imaginary axis to hold bit1: confirm the
    # QDFT recovers it where the complex FFT structurally cannot.
    kr = quaternion_dft(quaternion_dft(ks, form="left"), form="left", inverse=True)
    qdft_bit1 = [(_dec(q) >> 1) & 1 for q in kr]
    assert qdft_bit1 == true_bit1  # QDFT keeps the axis the complex FFT dropped


# --- ODFT: the bracketing convention is meaningful (non-associativity, F378) --

def test_octonion_dft_one_sided_round_trip():
    import random
    rng = random.Random(1)
    o = [[rng.uniform(-1, 1) for _ in range(8)] for _ in range(4)]
    for form in ("left", "right"):
        X = octonion_dft(o, form=form)
        orr = octonion_dft(X, form=form, inverse=True)
        for r, src in zip(orr, o):
            assert len(r) == 8
            for a, b in zip(r, src):
                assert abs(a - b) < 1e-9


def test_octonion_dft_two_sided_bracketing_is_meaningful():
    """The two-sided ODFT (W_l·x·W_r) is NOT associative: left- vs
    right-associated bracketing give DIFFERENT results (F378). This is WHY the
    bracketing convention must be an explicit declared field, not assumed."""
    import random
    rng = random.Random(2)
    o = [[rng.uniform(-1, 1) for _ in range(8)] for _ in range(4)]
    la = octonion_dft(o, form="two_sided", bracketing="left_associated",
                      mu_axis="i", two_sided_right_axis="j")
    ra = octonion_dft(o, form="two_sided", bracketing="right_associated",
                      mu_axis="i", two_sided_right_axis="j")
    diff = max(abs(a - b) for u, v in zip(la, ra) for a, b in zip(u, v))
    assert diff > 1e-6, "octonion two-sided bracketing must be non-associative"


def test_octonion_dft_two_sided_inverse_raises():
    o = [[0.0] * 8 for _ in range(3)]
    with pytest.raises(NotImplementedError):
        octonion_dft(o, form="two_sided", inverse=True)


# --- input validation --------------------------------------------------------

def test_quaternion_dft_rejects_octonion_tail():
    bad = [[0, 1, 0, 0, 0, 0, 0, 1]]  # e7 != 0 -> not a quaternion
    with pytest.raises(ValueError):
        quaternion_dft(bad)


def test_invalid_form_and_axis_raise():
    with pytest.raises(ValueError):
        quaternion_dft([[0, 1, 0, 0]], form="two_sided")  # quaternion has no two_sided
    with pytest.raises(ValueError):
        quaternion_dft([[0, 1, 0, 0]], mu_axis="z")
    with pytest.raises(ValueError):
        octonion_dft([[0] * 8], form="bogus")
    with pytest.raises(ValueError):
        octonion_dft([[0] * 8], bracketing="middle")


def test_empty_input_returns_empty():
    assert quaternion_dft([]) == []
    assert octonion_dft([]) == []


# =============================================================================
# v0.7.2rc1 (#908, F436/F437) — general/diagonal μ-axis + the bidirectional
# (σ, θ, μ) hypercomplex coupler.
# =============================================================================

# --- F436: a single named axis CARRIES but does NOT couple; diagonal COUPLES --

def test_diagonal_axis_couples_streams_named_axis_does_not():
    """F436: pack 3 streams (G,L,D) on i/j/k. With ``mu_axis='i'`` perturbing
    the i-stream (G) leaves the j,k spectral channels UNTOUCHED (carry-only — a
    complex FFT on the (1,i) plane + an independent (j,k) transform). With the
    DIAGONAL μ it folds across all axes, so the same perturbation moves j,k too."""
    import random
    rng = random.Random(20260606)
    n = 32
    G = [rng.gauss(0, 1) for _ in range(n)]
    L = [rng.gauss(0, 1) for _ in range(n)]
    D = [rng.gauss(0, 1) for _ in range(n)]
    base = [[0.0, G[t], L[t], D[t]] for t in range(n)]
    Gp = list(G); Gp[5] += 3.0
    pert = [[0.0, Gp[t], L[t], D[t]] for t in range(n)]

    def jk_change(axis):
        A = quaternion_dft(base, mu_axis=axis)
        B = quaternion_dft(pert, mu_axis=axis)
        return sum(abs(A[w][2] - B[w][2]) + abs(A[w][3] - B[w][3]) for w in range(n))

    named = jk_change("i")
    diag = jk_change("diagonal")
    assert named < 1e-9, f"named single axis must NOT couple i→(j,k); got {named:.2e}"
    assert diag > 1e-2, f"diagonal axis MUST couple i→(j,k); got {diag:.2e}"


@pytest.mark.parametrize("n_streams,expected_ratio", [(3, 3.0), (7, 7.0)])
def test_coherence_detector_anchor_energy_ratio(n_streams, expected_ratio):
    """F436: the diagonal-μ fold sends the streams into the real/anchor channel
    as a JOINT coherence detector — coherent streams add (∝ n·s), incoherent
    cancel (∝ √n). The anchor-channel energy ratio is therefore ≈ n: 3.0× for a
    quaternion (k=3), 7.0× for an octonion (k=7)."""
    import random
    rng = random.Random(7)
    m = 4000
    # theta omitted → the module default π/2: exp(μ·π/2)=μ, the pure fold.
    coh = [hypercomplex_couple([rng.gauss(0, 1)] * n_streams, axis="diagonal")[0]
           for _ in range(m)]
    inc = [hypercomplex_couple([rng.gauss(0, 1) for _ in range(n_streams)],
                               axis="diagonal")[0]
           for _ in range(m)]
    e_coh = sum(a * a for a in coh) / m
    e_inc = sum(a * a for a in inc) / m
    ratio = e_coh / e_inc
    assert abs(ratio - expected_ratio) < 0.5 * expected_ratio, (
        f"k={n_streams} coherence ratio {ratio:.2f} not ≈ {expected_ratio}")


# --- general / diagonal μ accepted by the DFTs (#908) -------------------------

@pytest.mark.parametrize("mu_axis", ["diagonal", [0.0, 0.6, 0.8, 0.0]])
def test_quaternion_dft_general_axis_round_trip(mu_axis):
    q = [[0.5, -1.0, 0.25, 0.75], [1.0, 0.0, -0.5, 0.5], [-0.25, 0.5, 1.0, -1.0]]
    X = quaternion_dft(q, form="left", mu_axis=mu_axis)
    qr = quaternion_dft(X, form="left", mu_axis=mu_axis, inverse=True)
    for r, o in zip(qr, q):
        for a, b in zip(r, o):
            assert abs(a - b) < 1e-9


def test_general_axis_is_normalised():
    """A non-unit μ is normalised to unit length, so ``[0,3,4,0]`` ≡ ``[0,.6,.8,0]``."""
    q = [[0.0, 1.0, -2.0, 0.5], [0.3, 0.0, 1.0, -1.0]]
    a = quaternion_dft(q, mu_axis=[0.0, 3.0, 4.0, 0.0])
    b = quaternion_dft(q, mu_axis=[0.0, 0.6, 0.8, 0.0])
    for ra, rb in zip(a, b):
        for x, y in zip(ra, rb):
            assert abs(x - y) < 1e-12


@pytest.mark.parametrize("mu_axis", ["diagonal", [0.0, 0, 0, 0, 0.6, 0.0, 0.8, 0.0]])
def test_octonion_dft_general_axis_round_trip(mu_axis):
    import random
    rng = random.Random(3)
    o = [[rng.uniform(-1, 1) for _ in range(8)] for _ in range(4)]
    X = octonion_dft(o, form="left", mu_axis=mu_axis)
    orr = octonion_dft(X, form="left", mu_axis=mu_axis, inverse=True)
    for r, src in zip(orr, o):
        for a, b in zip(r, src):
            assert abs(a - b) < 1e-9


# --- F437: the (σ, θ, μ) coupler binds (σ=+1) and unbinds (σ=−1) losslessly ---

@pytest.mark.parametrize("streams", [[2.0, -1.0, 3.0], [1, 2, 3, 4, 5, 6, 7]])
def test_couple_bind_unbind_round_trip(streams):
    """F437: the reverse coupling is the conjugate twiddle (σ=−1); it undoes the
    forward fold exactly because ℍ/𝕆 are division algebras
    (``x̄·(x·y)=‖x‖²·y``). Reversible up to 𝕆 → lossless for ≤7 streams."""
    bound = hypercomplex_couple(streams, axis="diagonal", theta=0.7, sigma=1)
    back = hypercomplex_couple(bound, axis="diagonal", theta=0.7, sigma=-1)
    # streams come back in the imaginary slots; the anchor returns to ~0.
    assert abs(back[0]) < 1e-9
    for got, want in zip(back[1:1 + len(streams)], streams):
        assert abs(got - want) < 1e-9


def test_couple_inverse_flag_matches_sigma_minus_one():
    """``inverse=True`` flips the effective sign — equivalent to ``sigma=-1``."""
    bound = hypercomplex_couple([2.0, -1.0, 3.0], theta=0.5, sigma=1)
    by_sigma = hypercomplex_couple(bound, theta=0.5, sigma=-1)
    by_inverse = hypercomplex_couple(bound, theta=0.5, sigma=1, inverse=True)
    for a, b in zip(by_sigma, by_inverse):
        assert abs(a - b) < 1e-12


def test_couple_diagonal_equals_equal_weight_vector():
    """``axis='diagonal'`` IS the equal-weight unit pure-imaginary axis."""
    a = hypercomplex_couple([1.0, 1.0, 1.0], axis="diagonal", theta=0.9)
    b = hypercomplex_couple([1.0, 1.0, 1.0], axis=[0.0, 1.0, 1.0, 1.0], theta=0.9)
    for x, y in zip(a, b):
        assert abs(x - y) < 1e-12


def test_couple_octonion_carrier_round_trips_full_eight():
    """A length-8 literal octonion feeds straight back in to unbind (all 8 comps)."""
    carrier = [0.5, 1.0, -2.0, 0.25, 3.0, -0.5, 0.75, -1.0]
    bound = hypercomplex_couple(carrier, axis="diagonal", theta=0.4, sigma=1)
    back = hypercomplex_couple(bound, axis="diagonal", theta=0.4, sigma=-1)
    assert len(back) == 8
    for got, want in zip(back, carrier):
        assert abs(got - want) < 1e-9


# --- error cases for the new surface -----------------------------------------

def test_couple_rejects_bad_sigma_and_form():
    with pytest.raises(ValueError):
        hypercomplex_couple([1.0, 2.0, 3.0], sigma=2)
    with pytest.raises(ValueError):
        hypercomplex_couple([1.0, 2.0, 3.0], form="two_sided")


def test_couple_rejects_too_many_streams():
    with pytest.raises(ValueError):
        hypercomplex_couple([1.0] * 9)  # > 8 components: no carrier


def test_quaternion_dft_rejects_octonion_axis():
    """A quaternion transform's μ must lie in ℍ (e4..e7 == 0)."""
    with pytest.raises(ValueError):
        quaternion_dft([[0.0, 1.0, 0.0, 0.0]], mu_axis=[0, 0, 0, 0, 1, 0, 0, 0])


def test_general_axis_must_be_pure_imaginary():
    with pytest.raises(ValueError):
        quaternion_dft([[0.0, 1.0, 0.0, 0.0]], mu_axis=[1.0, 1.0, 0.0, 0.0])  # e0!=0


def test_general_axis_rejects_zero_vector():
    with pytest.raises(ValueError):
        quaternion_dft([[0.0, 1.0, 0.0, 0.0]], mu_axis=[0.0, 0.0, 0.0, 0.0])


def test_unknown_named_axis_message_lists_diagonal():
    with pytest.raises(ValueError, match="diagonal"):
        quaternion_dft([[0.0, 1.0, 0.0, 0.0]], mu_axis="z")


# --- numpy-absent: the ops RUN (rc125 #564 flipped them numpy-free) ----------

def test_dft_runs_numpy_absent(monkeypatch):
    """rc125 (#564): ``quaternion_dft`` is numpy-FREE — it RUNS with numpy
    blocked at the meta-path (the prior scientific-tier ImportError is gone)."""
    monkeypatch.setitem(sys.modules, "numpy", None)  # `import numpy` -> ImportError
    out = quaternion_dft([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]])
    assert len(out) == 2 and len(out[0]) == 4   # N quaternions, 4 components each


def test_couple_runs_numpy_absent(monkeypatch):
    """rc125 (#564): ``hypercomplex_couple`` is numpy-FREE — it RUNS numpy-absent."""
    monkeypatch.setitem(sys.modules, "numpy", None)
    out = hypercomplex_couple([1.0, 2.0, 3.0])
    assert len(out) == 4   # a quaternion carrier (≤3 streams)
