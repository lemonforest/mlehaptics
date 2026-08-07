"""rc229 (#687) — the fuller asymmetric-halves lattice handle.

The V₄-gain (Klein-4-sector) Laplacian (EVEN channel) + ``cycle_holonomy``
(ODD channel). SIX genuine theorem checks (NOT smoke tests):

  1. χ00 sector == ``dense_laplacian`` EXACTLY (the trivial character).
  2. each ``L_χ`` == ``signed_laplacian`` on the χ-transformed weights.
  3. the COVER-SPECTRUM THEOREM — the four sector spectra's multiset union
     equals the ordinary Laplacian spectrum of the explicit V₄ cover (4n
     nodes); the Bilu–Linial 2-lift generalized to the V₄ abelian cover.
  4. switching/gauge invariance — arbitrary V₄ node re-gauging leaves all four
     sector spectra invariant.
  5. half-turn consistency — ``magnetic_laplacian(charges ∈ {0, 1/2})``
     reproduces the corresponding sector (the U(1) projection of the V₄ object).
  6. ``cycle_holonomy`` — switching-invariant; == 0 iff balanced (Zaslavsky);
     nonzero on a genuine odd cycle-gain AND distinguishing the ± chirality the
     (identical) magnetic spectra provably cannot.

Plus: native == pure parity (both ops), the read-out, edge cases, and the
registration ratchet (ToolEntry ×3 / tools.total == 418 / __all__ /
LAPLACIAN_OPS / the Rosetta rows). numpy-free (srmech + stdlib only).
"""
from __future__ import annotations

import random
from fractions import Fraction

import pytest

from srmech import _native
from srmech.math.laplacian import (
    klein4_gain_laplacian,
    klein4_relational_structure,
    cycle_holonomy,
    dense_laplacian,
    signed_laplacian,
    magnetic_laplacian,
    symmetric_eigendecompose,
    hermitian_eigendecompose,
    LAPLACIAN_OPS,
    _klein4_char_sign,
    _klein4_gain_laplacian_py,
    _cycle_holonomy_py,
    _normalize_gains_py,
    _validate_edges_weights_py,
)
import srmech.math.laplacian as _lap

_SECTORS = ("chi00", "chi01", "chi10", "chi11")

# A fixed non-trivial V₄-gain graph (5 nodes, 7 edges, mixed gains + weights).
_N = 5
_EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (1, 3)]
_WEIGHTS = [1.0, 2.0, 1.5, 1.0, 0.5, 1.0, 2.0]
_GAINS = [0, 1, 2, 3, 1, 2, 0]


def _close(a, b, tol=1e-9):
    return abs(a - b) <= tol * (1.0 + abs(b))


def _mat_eq(M, N, tol=1e-9):
    assert M.n_rows == N.n_rows and M.n_cols == N.n_cols
    return all(_close(M[i, j], N[i, j], tol)
               for i in range(M.n_rows) for j in range(M.n_cols))


def _spec(M):
    return sorted(float(x) for x in symmetric_eigendecompose(M)[0])


def _multiset_close(a, b, tol=1e-6):
    return len(a) == len(b) and all(_close(x, y, tol) for x, y in zip(sorted(a), sorted(b)))


# ── PROOF 1 ────────────────────────────────────────────────────────────
def test_proof1_chi00_equals_dense_laplacian():
    """χ00 (trivial character) == dense_laplacian exactly, for positive weights."""
    sec = klein4_gain_laplacian(_N, _EDGES, _WEIGHTS, _GAINS)
    dl = dense_laplacian(_N, _EDGES, _WEIGHTS)
    assert _mat_eq(sec["chi00"], dl), "χ00 sector must equal the ordinary Laplacian"


# ── PROOF 2 ────────────────────────────────────────────────────────────
def test_proof2_each_sector_equals_signed_laplacian_on_transformed_weights():
    """L_χ == signed_laplacian on the χ-transformed weights χ(g_e)·w_e."""
    sec = klein4_gain_laplacian(_N, _EDGES, _WEIGHTS, _GAINS)
    for k, key in enumerate(_SECTORS):
        a, b = k >> 1, k & 1
        w_sec = [_klein4_char_sign(a, b, g) * w for g, w in zip(_GAINS, _WEIGHTS)]
        sl = signed_laplacian(_N, _EDGES, w_sec)
        assert _mat_eq(sec[key], sl), f"{key} must equal signed_laplacian(χ-weights)"


# ── PROOF 3 — the COVER-SPECTRUM THEOREM ────────────────────────────────
def _v4_cover(n, edges, weights, gains):
    """The V₄ cover: node (i, s) → i*4 + s; edge (u, v, g) → (u, s)-(v, s^g)
    for every s ∈ V₄. Its ordinary Laplacian spectrum = ⋃_χ spec(L_χ)."""
    cov_e, cov_w = [], []
    for (u, v), w, g in zip(edges, weights, gains):
        for s in range(4):
            cov_e.append((u * 4 + s, v * 4 + (s ^ g)))
            cov_w.append(w)
    return dense_laplacian(4 * n, cov_e, cov_w)


def test_proof3_cover_spectrum_multiset_equals_union_of_four_sectors():
    """The real theorem: spec(V₄-cover Laplacian) == ⋃_χ spec(L_χ), as multisets."""
    sec = klein4_gain_laplacian(_N, _EDGES, _WEIGHTS, _GAINS)
    cover_spec = _spec(_v4_cover(_N, _EDGES, _WEIGHTS, _GAINS))
    union = []
    for key in _SECTORS:
        union += _spec(sec[key])
    assert len(cover_spec) == 4 * _N == len(union)
    assert _multiset_close(cover_spec, union), (
        "cover spectrum multiset must equal the union of the four sector spectra\n"
        f"cover = {[round(x, 6) for x in cover_spec]}\n"
        f"union = {[round(x, 6) for x in sorted(union)]}"
    )


# ── PROOF 4 — switching / gauge invariance ──────────────────────────────
def test_proof4_switching_invariance_of_sector_spectra():
    """Re-gauging nodes by arbitrary V₄ elements h_i (g → g ⊕ h_u ⊕ h_v) leaves
    all four sector spectra invariant (a per-character similarity transform)."""
    sec = klein4_gain_laplacian(_N, _EDGES, _WEIGHTS, _GAINS)
    rng = random.Random(20260712)
    h = [rng.randrange(4) for _ in range(_N)]
    gains2 = [g ^ h[u] ^ h[v] for (u, v), g in zip(_EDGES, _GAINS)]
    sec2 = klein4_gain_laplacian(_N, _EDGES, _WEIGHTS, gains2)
    for key in _SECTORS:
        assert _multiset_close(_spec(sec[key]), _spec(sec2[key]), 1e-7), (
            f"{key} spectrum must be invariant under V₄ node re-gauging"
        )


# ── PROOF 5 — half-turn consistency with the U(1) magnetic projection ────
def test_proof5_halfturn_magnetic_reproduces_sector():
    """A single-bit sign pattern maps to charges ∈ {0, 1/2}; the magnetic
    Laplacian at those half-turns (with the w/2 → w weight doubling) reproduces
    the corresponding V₄ sector — the U(1) projection of the V₄ object."""
    sec = klein4_gain_laplacian(_N, _EDGES, _WEIGHTS, _GAINS)
    # chi10 reads only bit0 (χ = (−1)^g0); chi01 reads only bit1.
    for key, bit in (("chi10", 0), ("chi01", 1)):
        charges = [0.5 if ((g >> bit) & 1) else 0.0 for g in _GAINS]
        w2 = [2.0 * w for w in _WEIGHTS]  # magnetic charges mode splits w/2 each way
        Lm = magnetic_laplacian(_N, _EDGES, w2, charges=charges)
        # Lm is complex-Hermitian but at half-turns the imaginary part is 0.
        assert _mat_eq(Lm, sec[key], tol=1e-9), (
            f"magnetic(charges∈{{0,1/2}}) must reproduce sector {key}"
        )


# ── PROOF 6 — cycle_holonomy: the ODD channel ───────────────────────────
def test_proof6a_balanced_iff_zero_and_distinguishes_chirality():
    """== 0 iff balanced (Zaslavsky); +c and −c give distinct holonomies
    (1/4 vs 3/4 mod 1) — the ± chirality the spectrum cannot carry."""
    tri = [(0, 1), (1, 2), (2, 0)]
    hp = cycle_holonomy(tri, [Fraction(1, 4), Fraction(0), Fraction(0)])
    hm = cycle_holonomy(tri, [Fraction(-1, 4), Fraction(0), Fraction(0)])
    assert hp["holonomies"] == [Fraction(1, 4)]
    assert hm["holonomies"] == [Fraction(3, 4)]   # −1/4 ≡ 3/4 mod 1
    assert hp["holonomies"] != hm["holonomies"], "must distinguish +c from −c"
    assert not hp["balanced"] and not hm["balanced"]
    # A coboundary charge (a pure gradient) is balanced: g(u,v) = p[v] − p[u].
    p = [Fraction(0), Fraction(1, 3), Fraction(2, 5)]
    grad = [p[v] - p[u] for (u, v) in tri]
    hb = cycle_holonomy(tri, grad)
    assert hb["balanced"] and hb["holonomies"] == [Fraction(0)], (
        "a gradient (coboundary) charge must be balanced (holonomy 0)"
    )


def test_proof6b_holonomy_switching_invariant():
    """Node re-gauging by a potential p (charge → charge + p[v] − p[u]) leaves
    every fundamental-cycle holonomy invariant (a coboundary telescopes)."""
    edges = [(0, 1), (1, 2), (2, 0), (0, 2), (1, 3), (3, 0)]
    charges = [Fraction(1, 4), Fraction(1, 3), Fraction(1, 5),
               Fraction(2, 7), Fraction(1, 2), Fraction(3, 8)]
    base = cycle_holonomy(edges, charges)
    p = [Fraction(1, 6), Fraction(-2, 9), Fraction(3, 11), Fraction(5, 13)]
    regauged = [c + p[v] - p[u] for (u, v), c in zip(edges, charges)]
    reg = cycle_holonomy(edges, regauged)
    assert base["cycle_edges"] == reg["cycle_edges"]
    assert base["holonomies"] == reg["holonomies"], (
        "cycle holonomies must be invariant under node re-gauging"
    )


def test_proof6c_holonomy_sees_what_the_spectrum_cannot():
    """The magnetic Laplacians of +c and −c are complex conjugates → IDENTICAL
    eigenvalues, so the spectrum is blind to the chirality; cycle_holonomy is not."""
    tri = [(0, 1), (1, 2), (2, 0)]
    Lp = magnetic_laplacian(3, tri, charges=[0.25, 0.0, 0.0])
    Ln = magnetic_laplacian(3, tri, charges=[-0.25, 0.0, 0.0])
    sp = sorted(float(x) for x in hermitian_eigendecompose(Lp)[0])
    sn = sorted(float(x) for x in hermitian_eigendecompose(Ln)[0])
    assert _multiset_close(sp, sn, 1e-7), "conjugate Hermitian spectra are identical"
    hp = cycle_holonomy(tri, [Fraction(1, 4), Fraction(0), Fraction(0)])
    hm = cycle_holonomy(tri, [Fraction(-1, 4), Fraction(0), Fraction(0)])
    assert hp["holonomies"] != hm["holonomies"], (
        "cycle_holonomy distinguishes the chirality the identical spectra cannot"
    )


# ── native == pure parity ───────────────────────────────────────────────
def test_klein4_native_equals_pure():
    """The C peer builds byte-identical sector Laplacians to the pure cascade."""
    from srmech.math.mat import Mat
    el, wl = _validate_edges_weights_py(_N, _EDGES, _WEIGHTS)
    gl = _normalize_gains_py(_GAINS, len(el))
    pure = _klein4_gain_laplacian_py(_N, el, wl, gl)
    api = klein4_gain_laplacian(_N, _EDGES, _WEIGHTS, _GAINS)
    for i, key in enumerate(_SECTORS):
        pm = Mat.from_rows(pure[i], is_complex=False)
        assert _mat_eq(api[key], pm, tol=0.0), f"native != pure for {key}"


@pytest.mark.skipif(not _native.has_native_cycle_holonomy(),
                    reason="cycle_holonomy C peer not loaded")
def test_cycle_holonomy_native_equals_pure():
    """The C peer's exact int64-rational holonomies match the pure Fraction path
    (same spanning-tree choice → same fundamental-cycle basis)."""
    edges = [(0, 1), (1, 2), (2, 0), (0, 2), (1, 3), (3, 0), (2, 3)]
    charges = [Fraction(1, 4), Fraction(1, 3), Fraction(1, 5), Fraction(2, 7),
               Fraction(1, 2), Fraction(3, 8), Fraction(5, 6)]
    holo_pure, ce_pure = _cycle_holonomy_py(4, edges, charges)
    res = cycle_holonomy(edges, charges)  # native when present
    assert res["holonomies"] == holo_pure
    assert res["cycle_edges"] == ce_pure


def test_cycle_holonomy_bignum_denominator_falls_to_exact_pure():
    """A charge past the int64 limit routes to the exact-Fraction path and is
    still exact (never a wrong answer)."""
    big = Fraction(1, 10 ** 9 + 7)   # denominator > the int64 rational limit
    tri = [(0, 1), (1, 2), (2, 0)]
    res = cycle_holonomy(tri, [big, Fraction(0), Fraction(0)])
    assert res["holonomies"] == [big % 1]
    assert res["holonomies"] == [big]


# ── the read-out ────────────────────────────────────────────────────────
def test_klein4_relational_structure_readout():
    """Per-sector tension/coherence + the Class-K mixed-sector asymmetry meter."""
    out = klein4_relational_structure(_EDGES, _WEIGHTS, _GAINS, n=_N)
    assert out["sectors"] == _SECTORS
    # χ00 is the ordinary PSD Laplacian on a connected graph → λ_min ≈ 0.
    assert abs(out["tension"]["chi00"]) <= 1e-8
    # Every signed Laplacian is PSD → tension (λ_min) ≥ 0 (allow eig round-off).
    for s in _SECTORS:
        assert out["tension"][s] >= -1e-8
    # The asymmetry meter is the Class-K magnitude of the χ10/χ01 tension gap.
    expect = abs(out["tension"]["chi10"] - out["tension"]["chi01"])
    assert _close(out["sector_asymmetry"], expect, 1e-12)
    assert out["sector_asymmetry"] >= 0.0


def test_klein4_relational_structure_identity_gains_all_sectors_equal():
    """gains=None (identity) → all four sectors coincide → zero asymmetry."""
    out = klein4_relational_structure(_EDGES, _WEIGHTS, gains=None, n=_N)
    t = out["tension"]
    for s in _SECTORS:
        assert _close(t[s], t["chi00"], 1e-8)
    assert out["sector_asymmetry"] <= 1e-8


# ── edge cases ──────────────────────────────────────────────────────────
def test_self_loop_is_a_one_cycle_carrying_its_charge():
    res = cycle_holonomy([(0, 0)], [Fraction(1, 3)], n=1)
    assert res["n_cycles"] == 1
    assert res["holonomies"] == [Fraction(1, 3)]
    assert not res["balanced"]


def test_parallel_edges_form_a_digon():
    """Two edges between the same pair → one tree edge + one co-tree digon whose
    holonomy is the charge difference."""
    res = cycle_holonomy([(0, 1), (0, 1)], [Fraction(1, 4), Fraction(3, 4)])
    assert res["n_cycles"] == 1
    assert res["holonomies"] == [Fraction(1, 2)]   # (3/4 − 1/4) mod 1


def test_empty_and_single_node_graphs():
    assert cycle_holonomy([], []) == {
        "n_cycles": 0, "holonomies": [], "cycle_edges": [], "balanced": True}
    out = klein4_relational_structure([], None)
    assert out["sector_asymmetry"] == 0.0


def test_gain_tuple_form_and_range_validation():
    """gains accept a 2-tuple (g0, g1); out-of-range raises."""
    # (g0, g1) = (1, 0) → int 1 ; (0, 1) → 2 ; (1, 1) → 3
    a = klein4_gain_laplacian(3, [(0, 1), (1, 2)], None, [(1, 0), (0, 1)])
    b = klein4_gain_laplacian(3, [(0, 1), (1, 2)], None, [1, 2])
    for s in _SECTORS:
        assert _mat_eq(a[s], b[s], tol=0.0)
    with pytest.raises(ValueError):
        klein4_gain_laplacian(3, [(0, 1)], None, [4])   # gain 4 out of V₄ range


# ── registration ratchet ────────────────────────────────────────────────
def test_registration_all_and_laplacian_ops():
    for name in ("klein4_gain_laplacian", "klein4_relational_structure",
                 "cycle_holonomy"):
        assert name in _lap.__all__, f"{name} missing from laplacian.__all__"
        assert name in LAPLACIAN_OPS, f"{name} missing from LAPLACIAN_OPS"


def test_registration_tool_schema_total_matches_live():
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    schema = get_tool_schema()
    assert len(schema.tools) == 560
    names = {t.name for t in schema.tools}
    for op in ("klein4_gain_laplacian", "klein4_relational_structure",
               "cycle_holonomy"):
        assert f"srmech.math.laplacian.{op}" in names, f"{op} ToolEntry missing"


def test_registration_native_helpers_present():
    # The has_native_* helpers exist and agree with HAS_NATIVE.
    assert _native.has_native_klein4_gain_laplacian() == bool(
        _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_graph_klein4_gain_laplacian"))
    assert _native.has_native_cycle_holonomy() == bool(
        _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_graph_cycle_holonomy")
        and hasattr(_native.LIB, "srmech_graph_cycle_holonomy_arena_bytes"))
