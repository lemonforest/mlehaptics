"""BATCH B8b (rc146) — C-composition parity for the 9 so(8) / octonion / triality
``qm`` ops (``qm_exact_assembly`` part 2).

The 9 ops all move ``python_only_debt`` → ``composition_of_c`` (ceiling 62 → 53)
with **NO new C symbol** (ABI stays 3). They split into two honest sub-classes,
both standalone-C-reproducible:

* **6 BYTE-EXACT** — ``so8_adjoint_basis`` / ``g2_subalgebra`` route their
  EXACT-INTEGER ``{-1,0,+1}`` derivation matmuls through the ``c_dispatched``
  ``laplacian.mat_matmul`` (``srmech_dense_matmul_complex``); ``triality_swap`` /
  ``triality_automorphism`` / ``triality_companions`` /
  ``lean_isa_seventh_primitive`` compose ``mat_matmul`` + ``mat_norm`` over the
  exact-DYADIC-ℚ companion maps (whose exact-ℚ solve is standalone-reproducible
  via the ``c_dispatched`` ``srmech_qmat_rref`` — VERIFIED byte-identical to the
  fast pure sparse-Fraction solve). Integer / small-dyadic sums are exact in
  float64 regardless of accumulation order ⇒ native path is **byte-identical** to
  forced-pure.
* **3 FLOAT-COMPOSITION** — ``so7_subalgebra`` / ``an_embedding`` /
  ``quaternion_subalgebra_stabilizer`` compose the C-backed ``mat_svd``
  (``srmech_svd_f64``) ∘ ``mat_hermitian_eigendecompose`` ∘ ``mat_matmul`` ∘
  ``kron`` — the SAME established ``composition_of_c`` pattern as the rc140
  esprit / map_ml / mimo_svd float-SVD ops. The SVD/eigen basis is
  non-unique, so native vs forced-pure agree on every **invariant** (dimension,
  antisymmetry, span, ``J² = −I``, Killing rank, the basis-independent Killing
  SPECTRUM within the accepted ~1e-9 carrier shift) and on every EXACT field
  (the g2-content-addressed attestation, the decomposition tuple), NOT
  element-wise (which the free SVD basis forbids).

Plus the load-bearing structural certificate: the triality automorphism ``τ`` is
genuinely **order 3** (``τ³ = I`` exact, ``τ ≠ I``, ``τ² ≠ I``) — a real
permutation of ``8v / 8s / 8c``.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""
from __future__ import annotations

import contextlib

import pytest

from srmech.amsc import _native
from srmech.amsc.laplacian import mat_matmul, mat_norm, mat_svd
from srmech.amsc.mat import Mat
from srmech.qm import so8, triality


requires_native = pytest.mark.skipif(
    not (_native.HAS_NATIVE and _native.LIB is not None
         and hasattr(_native.LIB, "srmech_dense_matmul_complex")),
    reason="rc146 B8b native parity needs srmech_dense_matmul_complex; on a "
    "no-C host the pure-Python cascade is the complete, identical alternative.",
)

_TOL = 1e-9


def _clear_caches() -> None:
    """Drop every so8 / triality memoised build so the next call re-derives in
    the currently-selected (native or forced-pure) dispatch mode."""
    for mod in (so8, triality):
        for name in dir(mod):
            obj = getattr(mod, name)
            if hasattr(obj, "cache_clear"):
                try:
                    obj.cache_clear()
                except Exception:  # noqa: BLE001
                    pass


@contextlib.contextmanager
def force_pure():
    """Disable native dispatch AND clear the caches so every carrier op
    (mat_matmul / mat_svd / mat_hermitian_eigendecompose / mat_norm and the
    srmech_qmat_rref-mirrored companion solve) takes its pure-Python fallback —
    the forced-pure reference the native path is compared against."""
    saved = _native.HAS_NATIVE
    _clear_caches()
    _native.HAS_NATIVE = False
    try:
        yield
    finally:
        _native.HAS_NATIVE = saved
        _clear_caches()


# ── deterministic serialisation for the byte-exact comparison ──────────────────
def _ser(x, out):
    if isinstance(x, Mat):
        out.append(x.tobytes())
    elif isinstance(x, (list, tuple)):
        out.append(b"[%d]" % len(x))
        for e in x:
            _ser(e, out)
    elif isinstance(x, dict):
        for k in sorted(x.keys(), key=repr):
            out.append(repr(k).encode())
            _ser(x[k], out)
    elif isinstance(x, float):
        import struct
        out.append(struct.pack("<d", x))
    elif isinstance(x, complex):
        import struct
        out.append(struct.pack("<dd", x.real, x.imag))
    else:
        out.append(repr(x).encode())
    return out


def _blob(value) -> bytes:
    return b"|".join(_ser(value, []))


def _native_then_pure(thunk):
    """(native_value, pure_value) for a zero-arg op, caches cleared between."""
    _clear_caches()
    _native.HAS_NATIVE = True
    native = thunk()
    with force_pure():
        pure = thunk()
    _clear_caches()
    return native, pure


# ── the 6 BYTE-EXACT ops ───────────────────────────────────────────────────────
def _companions_thunk():
    # A fixed L-type so(8) generator (index 14 = first coset direction).
    g_v = so8.so8_adjoint_basis()[14]
    return triality.triality_companions(g_v)


_BYTE_EXACT = {
    "so8_adjoint_basis": so8.so8_adjoint_basis,
    "g2_subalgebra": so8.g2_subalgebra,
    "triality_swap": triality.triality_swap,
    "triality_automorphism": triality.triality_automorphism,
    "triality_companions": _companions_thunk,
    "lean_isa_seventh_primitive": triality.lean_isa_seventh_primitive,
}


@requires_native
@pytest.mark.parametrize("name", sorted(_BYTE_EXACT))
def test_byte_exact_native_equals_forced_pure(name):
    """Each of the 6 exact ops: native (C matmul / norm + C-mirrored exact-ℚ
    companion solve) is BYTE-IDENTICAL to the forced-pure fallback (EXACT —
    integer / dyadic-ℚ entries, NOT a float tolerance)."""
    native, pure = _native_then_pure(_BYTE_EXACT[name])
    assert _blob(native) == _blob(pure), f"{name}: native != forced-pure bytes"


# ── the 3 FLOAT-COMPOSITION ops — invariants + exact sub-fields ────────────────
def _antisymmetric(m: Mat) -> bool:
    rows = m.tolist()
    n = len(rows)
    return mat_norm(Mat.from_rows(
        [[rows[i][j] + rows[j][i] for j in range(n)] for i in range(n)])) < _TOL


def _span_rank_float(columns) -> int:
    """Float-tolerant rank of a column stack via the cascade mat_svd (the same
    small-σ-floor-generous count the so8 acceptance suite uses)."""
    rows = [[columns[c][r] for c in range(len(columns))]
            for r in range(len(columns[0]))]
    _, S, _ = mat_svd(Mat.from_rows(rows))
    smax = S[0] if S else 0.0
    return sum(1 for s in S if s > 1e-6 * smax)


@requires_native
def test_so7_float_composition_parity():
    """so7_subalgebra composes the C-backed mat_svd; native & forced-pure each
    yield a valid 21-dim so(7) basis spanning the IDENTICAL fixed space (the SVD
    basis is free, so span — not element bytes — is the invariant)."""
    native, pure = _native_then_pure(so8.so7_subalgebra)
    assert len(native) == 21 and len(pure) == 21
    assert all(_antisymmetric(m) for m in native)
    nat_coords = [so8._epq_coords(m) for m in native]
    pure_coords = [so8._epq_coords(m) for m in pure]
    # Each basis is rank 21, and the STACKED span does not grow ⇒ same space.
    assert _span_rank_float(nat_coords) == 21
    assert _span_rank_float(pure_coords) == 21
    assert _span_rank_float(nat_coords + pure_coords) == 21


@requires_native
def test_an_embedding_float_composition_parity():
    """an_embedding composes mat_svd ∘ mat_hermitian_eigendecompose ∘ kron;
    the EXACT fields (g2-content-addressed attestation, decomposition, unit) are
    byte-identical native==pure, and every dimension / J²=−I invariant holds in
    both dispatch modes (the SVD/eigen basis itself is free)."""
    native, pure = _native_then_pure(lambda: so8.an_embedding(1))
    # EXACT sub-fields: the attestation hashes the INTEGER g2 generators, and the
    # decomposition / imaginary_unit are exact ⇒ byte-identical across modes.
    for key in ("attestation", "decomposition", "imaginary_unit",
                "framework_an_reading"):
        assert _blob(native[key]) == _blob(pure[key]), f"an_embedding[{key}] drift"
    assert native["decomposition"]["adjoint_14"] == (8, 3, 3)
    assert native["decomposition"]["vector_7"] == (1, 3, 3)
    for emb in (native, pure):
        assert len(emb["su3"]) == 8 and len(emb["complement"]) == 6
        assert len(emb["triplet"]) == 3 and len(emb["antitriplet"]) == 3
        j = emb["complex_structure_J"]
        jj = mat_matmul(j, j)
        i6 = Mat.from_rows([[1.0 if a == b else 0.0 for b in range(6)]
                            for a in range(6)])
        # J² = −I  ⇒  ‖J² + I‖ ≈ 0.
        assert mat_norm(Mat.from_rows(
            [[jj[a, b] + i6[a, b] for b in range(6)] for a in range(6)])) < _TOL


@requires_native
def test_quaternion_stabiliser_float_composition_parity():
    """quaternion_subalgebra_stabilizer composes mat_svd ∘
    mat_hermitian_eigendecompose; the EXACT fields byte-identical, the
    basis-independent Killing SPECTRUM agrees within the accepted carrier shift,
    and the semisimplicity certificate (Killing rank 6) holds in both modes."""
    native, pure = _native_then_pure(lambda: so8.quaternion_subalgebra_stabilizer(1))
    for key in ("attestation", "decomposition", "quaternion_fano_line",
                "quaternion_imaginary_units", "killing_rank"):
        assert _blob(native[key]) == _blob(pure[key]), f"quaternion[{key}] drift"
    assert native["killing_rank"] == 6
    assert native["decomposition"]["so4_6"] == (3, 3)
    for st in (native, pure):
        assert len(st["so4"]) == 6
        assert len(st["su2_plus"]) == 3 and len(st["su2_minus"]) == 3
    # The Killing SPECTRUM is basis-independent → native ≈ pure within tolerance.
    for a, b in zip(native["killing_spectrum"], pure["killing_spectrum"]):
        assert abs(a - b) < _TOL
    # Two distinct eigenvalues, multiplicity 3 each (the su(2) ⊕ su(2) fingerprint).
    spec = sorted(round(v, 6) for v in native["killing_spectrum"])
    assert len(set(spec)) == 2


# ── the load-bearing structural certificate: τ is genuinely order 3 ────────────
@requires_native
def test_triality_tau_is_order_three_permutation():
    """``τ³ = I`` EXACT, ``τ ≠ I``, ``τ² ≠ I`` — the genuine order-3 outer
    automorphism (a real permutation of 8v/8s/8c), not an involution."""
    tau = triality.triality_automorphism()
    assert tau.shape == (28, 28)
    identity = Mat.from_rows([[1.0 if i == j else 0.0 for j in range(28)]
                              for i in range(28)])

    def dev(m):
        r = m.tolist()
        idn = identity.tolist()
        return mat_norm(Mat.from_rows(
            [[r[i][j] - idn[i][j] for j in range(28)] for i in range(28)]))

    tau2 = mat_matmul(tau, tau)
    tau3 = mat_matmul(tau2, tau)
    assert dev(tau3) < _TOL            # τ³ = I (order divides 3)
    assert dev(tau) > 1.0              # τ ≠ I
    assert dev(tau2) > 1.0             # τ² ≠ I  ⇒ order is EXACTLY 3
    # The certificate op agrees.
    cert = triality.lean_isa_seventh_primitive()["certificate"]
    assert cert["triality_order"] == 3
    assert cert["triality_order_residual"] < _TOL
    assert cert["lagrange_obstruction"] is True


# ── independent structural oracles (guard a value wrong in BOTH paths) ─────────
@requires_native
def test_structural_oracles():
    """Dimensions the construction must satisfy, independent of the SVD basis."""
    assert len(so8.so8_adjoint_basis()) == 28   # 14 g2 + 7 L + 7 R
    assert len(so8.g2_subalgebra()) == 14        # dim g2 = Der(O)
    # g2 rank is EXACTLY 14 over ℚ (the exact-integer derivation coords).
    g2_coords = [so8._epq_coords(m) for m in so8.g2_subalgebra()]
    assert so8._rank_exact(g2_coords) == 14


def test_numpy_is_absent():
    """The whole B8b path runs with numpy uninstalled (carrier-native)."""
    import sys
    assert "numpy" not in sys.modules
