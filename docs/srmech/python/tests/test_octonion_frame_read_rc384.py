"""rc384 (`#T957` / `#T959`) — the 𝕆 frame-committed coherence read.

Two shipped ops + the differential gate that IS the `#T959` attestation:

  * ``srmech.cascade.octonion_frame_read(x, *, frame=4)`` — the exact-ℚ ELEMENT
    frame-read: 𝕆 = ℍ ⊕ ℍℓ on the committed seam ℓ=e₄, returning the
    quaternionic-Hopf base (frame-free UNDER the S³ fiber = the coherent note) +
    the equivariant writhe.
  * ``srmech.math.laplacian.octonion_laplacian(n, edges, *, gains=None)`` — the
    8n×8n real-symmetric octonion gain Laplacian, the Class-L peer of
    ``quaternion_laplacian`` that MEASURES the ceiling.

Genuine theorem checks (NOT smoke tests):

  1. the ℍ base subalgebra is FULLY coherent (0/64) and ALL 168 of 𝕆's
     non-closures CROSS the doubling seam (0 non-seam) — via ``associator``.
  2. FRAME-FREE UNDER THE FIBER (non-tautological): base UNCHANGED under a UNIT
     quaternion right-multiply of both halves, CHANGED under a non-fiber move;
     the writhe is EQUIVARIANT; the exact four-sphere identity.
  3. the frame gate (``frame != 4`` and non-octonion inputs raise).
  4. octonion_laplacian: shape (8n×8n) + EXACT real-symmetry + identity-gain
     KNOWN ANSWER (``½·(dense L) ⊗ I₈``).
  5. THE CEILING — a node-wise unit-octonion gauge on a CYCLE MOVES the 𝕆
     spectrum (NOT gauge-invariant), while the shipped ``quaternion_laplacian``
     is Sp(1)-invariant to ~1e-15 on the same experiment.
  6. registration ratchet (ToolEntry / __all__ / LAPLACIAN_OPS / Rosetta / the
     describe() total 535).

numpy-free (srmech + stdlib only).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import srmech
from srmech.cascade import octonion_frame_read, associator, cd_basis
from srmech.cascade.cayley_dickson import cd_mult, cd_conjugate, cd_norm_sq
from srmech.math.q import Q
from srmech.math.laplacian import (
    octonion_laplacian,
    quaternion_laplacian,
    dense_laplacian,
    mat_hermitian_eigendecompose,
    LAPLACIAN_OPS,
)
from srmech.physics.qm.octonion import (
    octonion_norm, octonion_conjugate, octonion_left_mult,
)
from srmech.physics.qm.quaternion import (
    quaternion_norm, quaternion_conjugate, quaternion_left_mult,
)

_HBASE = (0, 1, 2, 3)


def _e(i):
    return cd_basis(8, i)


# ── 1. ℍ base coherence + 𝕆 seam-confinement (the EXACT-ℚ census) ────────
def test_H_base_subalgebra_is_fully_coherent():
    nz = sum(1 for i in _HBASE for j in _HBASE for k in _HBASE
             if any(v != 0 for v in associator(_e(i), _e(j), _e(k))))
    assert nz == 0, f"ℍ base must be coherent (0/64); got {nz}"


def test_all_octonion_nonclosures_cross_the_seam():
    nz = seam = nonseam = 0
    half = lambda i: 0 if i < 4 else 1
    for i in range(8):
        for j in range(8):
            for k in range(8):
                if any(v != 0 for v in associator(_e(i), _e(j), _e(k))):
                    nz += 1
                    if half(i) + half(j) + half(k) > 0:
                        seam += 1
                    else:
                        nonseam += 1
    assert nz == 168, f"expected 168 nonzero associators; got {nz}"
    assert seam == 168 and nonseam == 0, (
        f"every non-closure must cross the seam; got seam={seam} "
        f"non_seam={nonseam}")


# ── 2. frame-free UNDER the fiber, non-tautological ──────────────────────
_X = [1, 2, -3, 1, 2, -1, 1, 4]
_LAM = (Q(1, 2), Q(1, 2), Q(1, 2), Q(1, 2))   # |λ|² = 1 (Hurwitz unit)


def test_fiber_leaves_base_invariant_and_moves_writhe():
    assert cd_norm_sq(_LAM) == Q(1, 1)
    r = octonion_frame_read(_X)
    q0f, q1f = cd_mult(r["q0"], _LAM), cd_mult(r["q1"], _LAM)
    rf = octonion_frame_read(list(q0f) + list(q1f))
    # base is the COHERENT NOTE — unchanged under the S³ fiber
    assert rf["base_H"] == r["base_H"]
    assert rf["base_R"] == r["base_R"]
    assert rf["norm_sq"] == r["norm_sq"]
    # writhe carries the fiber DOF — it MOVES (equivariant)
    assert rf["writhe"] != r["writhe"]


def test_nonfiber_move_changes_the_base_nontautology():
    r = octonion_frame_read(_X)
    # right-multiply ONLY q0 (not both halves) — breaks the diagonal fiber
    q0n = cd_mult(r["q0"], _LAM)
    rn = octonion_frame_read(list(q0n) + list(r["q1"]))
    # projective base ratio must CHANGE (the instrument can return otherwise)
    changed = not all(
        rn["base_H"][i] * r["base_R"] == r["base_H"][i] * rn["base_R"]
        for i in range(4))
    assert changed


def test_base_lies_on_the_exact_four_sphere():
    r = octonion_frame_read(_X)
    assert cd_norm_sq(r["base_H"]) + r["base_R"] * r["base_R"] == \
        r["norm_sq"] * r["norm_sq"]


def test_frame_read_shape_and_known_values():
    r = octonion_frame_read(_X)
    assert r["frame"] == 4 and r["dim"] == 8
    assert r["base_H"] == (Q(2, 1), Q(36, 1), Q(4, 1), Q(-2, 1))
    assert r["base_R"] == Q(-7, 1)
    assert r["norm_sq"] == Q(37, 1)
    assert r["writhe"] == (Q(2, 1), Q(-1, 1), Q(1, 1), Q(4, 1))


def test_degenerate_fiber_is_the_point_at_infinity():
    r = octonion_frame_read([3, 1, 0, 2, 0, 0, 0, 0])
    assert r["writhe"] is None
    assert r["canonical_affine"] is None
    assert r["base_R"] == r["norm_sq"]        # base_R = +|q0|²


# ── 3. the frame gate ────────────────────────────────────────────────────
def test_frame_read_rejects_non_octonion():
    with pytest.raises(ValueError):
        octonion_frame_read([1, 2, 3, 4])


def test_frame_read_rejects_non_seam_frame():
    """A frame whose ℓ lies INSIDE its own ℍ base is still refused.

    ⚠️ This test asserted ``frame=5`` raised until v0.9.0rc421 (`#T1122`), and
    that expectation encoded the very claim rc421 falsified. rc420's validator
    argued ``e₅/e₆/e₇`` "are not independent seam generators, so no other single
    basis unit splits 𝕆 = ℍ ⊕ ℍℓ cleanly" — but measured against ``cd_mult``
    the standard ℍ base admits FOUR valid splitting units ``{e₄,e₅,e₆,e₇}``, and
    ``frame=5`` is a well-posed frame giving a genuinely different read. The
    surviving rejection is the half of the old argument that WAS true:
    ``e₁/e₂/e₃`` lie inside the base. See
    ``tests/test_octonion_frame_28_rc421.py`` for the full 28-frame gate.
    """
    with pytest.raises(ValueError):
        octonion_frame_read(_X, frame=2)        # inside the ℍ base — refused
    # ...and the value this test used to pin as invalid is now a real frame
    assert octonion_frame_read(_X, frame=5)["frame"] == 5


# ── 4. octonion_laplacian shape / symmetry / known answer ────────────────
_TRI = [(0, 1), (1, 2), (2, 0)]


def test_octonion_laplacian_shape_and_symmetry():
    M = octonion_laplacian(3, _TRI)
    assert M.shape == (24, 24)
    rows = M.tolist()
    # real-symmetric BY CONSTRUCTION (L(conj g) == L(g)ᵀ), exact
    asym = max((rows[i][j] - rows[j][i]) * (rows[i][j] - rows[j][i])
               for i in range(24) for j in range(24))
    assert asym == 0.0


def test_octonion_laplacian_identity_gain_known_answer():
    # gains=None == ½·(dense graph Laplacian) ⊗ I₈
    M = octonion_laplacian(3, _TRI).tolist()
    L = dense_laplacian(n=3, edges=_TRI).tolist()
    for a in range(3):
        for b in range(3):
            for c in range(8):
                assert M[8 * a + c][8 * b + c] == 0.5 * float(L[a][b])


def test_octonion_laplacian_gain_validation():
    with pytest.raises(ValueError):
        octonion_laplacian(2, [(0, 1)], gains=[[1, 0, 0, 0]])   # 4-vec, not 8
    with pytest.raises(ValueError):
        octonion_laplacian(2, [(0, 1)], gains=[[0] * 8])        # zero norm


# ── 5. THE CEILING — 𝕆 gauge-dependence vs ℍ Sp(1)-invariance ────────────
def _spectrum(mat):
    ev, _ = mat_hermitian_eigendecompose(mat)
    return sorted(complex(ev[i, 0]).real for i in range(ev.n_rows))


def _spec_dev(s1, s2):
    ss = sum((a - b) * (a - b) for a, b in zip(s1, s2))
    return ss ** 0.5


def _unit8(v):
    n = octonion_norm(v)
    return [c / n for c in v]


def _o(a, b):
    lo = octonion_left_mult(a).tolist()
    return [sum(lo[k][j] * b[j] for j in range(8)) for k in range(8)]


def _unit4(v):
    n = quaternion_norm(v)
    return [c / n for c in v]


def _q(a, b):
    lq = quaternion_left_mult(a).tolist()
    return [sum(lq[k][j] * b[j] for j in range(4)) for k in range(4)]


_G8 = [_unit8([1, 2, -1, 3, 0, -2, 1, 1]), _unit8([2, 0, 1, -1, 1, 1, 0, -1]),
       _unit8([-1, 1, 2, 1, 0, 1, -1, 1])]
_S8 = [_unit8([1, 1, 0, 1, 0, 1, 1, 0]), _unit8([0, 1, 1, 0, 1, 0, 1, 1]),
       _unit8([1, 0, 1, 1, 0, 1, 0, 1])]
_G4 = [_unit4([1, 2, -1, 3]), _unit4([2, 0, 1, -1]), _unit4([-1, 1, 2, 1])]
_S4 = [_unit4([1, 1, 0, 1]), _unit4([0, 1, 1, 0]), _unit4([1, 0, 1, 1])]


def test_octonion_spectrum_is_NOT_gauge_invariant_on_a_cycle():
    """THE CEILING: at 𝕆 the node-wise unit-octonion gauge MOVES the spectrum
    on a cycle (non-associativity ⇒ L is not a homomorphism)."""
    gg = [_o(_o(_S8[u], g), octonion_conjugate(_S8[v]))
          for (u, v), g in zip(_TRI, _G8)]
    dev = _spec_dev(_spectrum(octonion_laplacian(3, _TRI, gains=_G8)),
                    _spectrum(octonion_laplacian(3, _TRI, gains=gg)))
    assert dev > 1e-3, (
        f"𝕆 spectrum must MOVE under the gauge on a cycle; got {dev:.2e}")


def test_quaternion_spectrum_IS_gauge_invariant_the_control():
    """The ℍ control: the shipped quaternion_laplacian is Sp(1)-invariant to
    ~1e-15 on the SAME experiment (the rung where L IS a homomorphism)."""
    gg = [_q(_q(_S4[u], g), quaternion_conjugate(_S4[v]))
          for (u, v), g in zip(_TRI, _G4)]
    dev = _spec_dev(_spectrum(quaternion_laplacian(3, _TRI, gains=_G4))[::4],
                    _spectrum(quaternion_laplacian(3, _TRI, gains=gg))[::4])
    assert dev < 1e-9, f"ℍ spectrum must be gauge-invariant; got {dev:.2e}"


# ── 6. registration ratchet ──────────────────────────────────────────────
def test_both_ops_in_laplacian_and_cascade_surfaces():
    assert "octonion_laplacian" in LAPLACIAN_OPS
    assert hasattr(srmech.cascade, "octonion_frame_read")
    assert hasattr(srmech.math.laplacian, "octonion_laplacian")


def test_both_ops_registered_and_describe_total_is_535():
    from srmech.introspect.tool_schema import get_tool_schema
    names = {e.name for e in get_tool_schema().tools}
    assert "srmech.cascade.octonion_frame_read" in names
    assert "srmech.math.laplacian.octonion_laplacian" in names
    assert srmech.describe()["tools"]["total"] == 656


def test_rosetta_rows_present_composition_of_c():
    path = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip()]
    by = {r["exposed_as"]: r for r in rows}
    for name in ("srmech.cascade.octonion_frame_read",
                 "srmech.math.laplacian.octonion_laplacian"):
        assert by[name]["bucket"] == "composition_of_c"
