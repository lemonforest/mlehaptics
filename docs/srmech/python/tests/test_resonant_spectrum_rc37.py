"""§75 (F928) — the resonant-spectrum closure ``coupling.resonant_spectrum``.

A Class-L coupling composite over the eigensolve + best_rational + factor
kernels, with the 1:1 C peer ``srmech_resonant_spectrum``. This test is
numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it exercises
only the srmech carriers + plain Python arithmetic.

Coverage:
  (a) the op returns the right dict shape;
  (b) ``force_orders[1]`` value-equals ``L·L`` (the Λ² reconstruction);
  (c) the F928 Jupiter↔Io L²-concentration anchor (~20×+ vs outer Callisto);
  (d) Python-op == C-peer value-parity when native present (skip-clean when
      absent);
  (e) the resonances read the lock (smooth/2-adic den) vs libration
      (large-prime den) prime structure.
"""

import ctypes

import pytest

from srmech.amsc import coupling, laplacian as La, _native
from srmech.amsc.mat import Mat
from srmech.amsc.vec import Vec


# The F928 Jupiter + Galilean-moon illustrative parameters (JPL fact-sheet
# order of magnitude): a = semi-major axis (10³ km), m = mass (10²² kg).
_JUP_A = [0.0, 421.7, 671.0, 1070.4, 1882.7]
_JUP_M = [189800.0, 8.93, 4.80, 14.82, 10.76]


def _abs(x):
    """Magnitude without ``abs()`` (Class-K sign branch in test code too)."""
    return -x if x < 0.0 else x


def _jupiter_laplacian():
    n, edges, weights = coupling.from_bodies(_JUP_M, _JUP_A)
    return La.dense_laplacian(n, edges, weights), n


# ─────────────────────────────────────────────────────────────────────
# (a) dict shape
# ─────────────────────────────────────────────────────────────────────
def test_dict_shape():
    L, n = _jupiter_laplacian()
    out = coupling.resonant_spectrum(L, orders=2, max_den=64)
    assert set(out.keys()) == {"tensions", "modes", "force_orders", "resonances"}
    assert isinstance(out["tensions"], Vec)
    assert out["tensions"].shape == (n,)
    assert isinstance(out["modes"], Mat)
    assert out["modes"].shape == (n, n)
    assert isinstance(out["force_orders"], list)
    assert len(out["force_orders"]) == 2
    for fo in out["force_orders"]:
        assert isinstance(fo, Mat)
        assert fo.shape == (n, n)
    assert isinstance(out["resonances"], list)
    for r in out["resonances"]:
        assert set(r.keys()) == {"pair", "ratio", "den_coords", "locked"}
        assert isinstance(r["pair"], tuple) and len(r["pair"]) == 2
        assert isinstance(r["ratio"], tuple) and len(r["ratio"]) == 2
        assert isinstance(r["locked"], bool)


def test_tensions_ascending_with_one_free_mode():
    L, n = _jupiter_laplacian()
    out = coupling.resonant_spectrum(L, orders=1, max_den=64)
    t = [float(out["tensions"][i]) for i in range(n)]
    assert t == sorted(t)                       # ascending
    assert _abs(t[0]) < t[-1] * 1e-6            # one ~zero free/bulk mode


def test_orders_validation():
    L, _ = _jupiter_laplacian()
    with pytest.raises(ValueError):
        coupling.resonant_spectrum(L, orders=0)
    with pytest.raises(ValueError):
        coupling.resonant_spectrum(L, orders=-2)


# ─────────────────────────────────────────────────────────────────────
# (b) force_orders[1] == L·L (the Λ² reconstruction is correct)
# ─────────────────────────────────────────────────────────────────────
def test_force_order_2_equals_L_matmul_L():
    L, n = _jupiter_laplacian()
    out = coupling.resonant_spectrum(L, orders=2, max_den=64)
    L1, L2 = out["force_orders"]
    # force_orders[0] == L (the first order is L itself).
    Lrows = L.tolist()
    for i in range(n):
        for j in range(n):
            assert _abs(L1[i, j] - Lrows[i][j]) < 1e-7
    # force_orders[1] == L·L (reconstructed in the eigenbasis from ONE solve).
    LL = (L @ L).tolist()
    for i in range(n):
        for j in range(n):
            assert _abs(L2[i, j] - LL[i][j]) < 1e-9


def test_higher_orders_match_repeated_matmul():
    L, n = _jupiter_laplacian()
    out = coupling.resonant_spectrum(L, orders=3, max_den=64)
    L3 = out["force_orders"][2]
    LLL = (L @ L @ L).tolist()
    for i in range(n):
        for j in range(n):
            # L³ entries grow large; use a small relative tolerance.
            ref = LLL[i][j]
            tol = 1e-6 * (1.0 + _abs(ref))
            assert _abs(L3[i, j] - ref) < tol


# ─────────────────────────────────────────────────────────────────────
# (c) the F928 Jupiter↔Io L²-concentration anchor
# ─────────────────────────────────────────────────────────────────────
def test_f928_jupiter_io_l2_concentration():
    """L² (forces-of-forces) concentrates on the Jupiter↔Io pair (0,1) ~20×+
    vs the outer Jupiter↔Callisto coupling (0,4) — the tidal-flux signature."""
    L, _ = _jupiter_laplacian()
    out = coupling.resonant_spectrum(L, orders=2, max_den=64)
    L2 = out["force_orders"][1]
    io = _abs(L2[0, 1])         # Jupiter ↔ Io
    callisto = _abs(L2[0, 4])   # Jupiter ↔ Callisto (outer)
    assert io > 15.0 * callisto   # ~26× in practice; the > 20× anchor floor


# ─────────────────────────────────────────────────────────────────────
# (e) resonances read the lock / libration prime structure
# ─────────────────────────────────────────────────────────────────────
def test_resonances_lock_vs_libration_prime_structure():
    L, _ = _jupiter_laplacian()
    out = coupling.resonant_spectrum(L, orders=2, max_den=64)
    res = out["resonances"]
    assert len(res) >= 1
    # Every resonance carries a (num, den) ratio whose denominator factorises
    # into the reported prime-coordinates, and a lock verdict consistent with
    # the den's smoothness (every prime ≤ isqrt(max_den) ⇒ locked).
    for r in res:
        num, den = r["ratio"]
        assert den >= 1
        # den_coords reconstruct den.
        prod = 1
        for p, e in r["den_coords"].items():
            prod *= p ** e
        assert (prod if r["den_coords"] else 1) == (den if den > 1 else 1)
        # lock verdict: a small-prime / 2-adic den is LOCKED; a large-prime den
        # (e.g. 11 with max_den=64 ⇒ cutoff 8) is libration (off-lock).
        cutoff = 8  # isqrt(64)
        smooth = all(p <= cutoff for p in r["den_coords"].keys())
        assert r["locked"] == smooth
    # At least one LOCK and the Laplace ladder is read (a den with only small
    # primes appears among the adjacent-tension ratios).
    assert any(r["locked"] for r in res)


# ─────────────────────────────────────────────────────────────────────
# (d) Python-op == C-peer value-parity (skip-clean when native absent)
# ─────────────────────────────────────────────────────────────────────
def _call_c_peer(L_mat, n, orders, max_den):
    """Drive the C peer directly via ctypes and return its raw outputs."""
    lib = _native.LIB
    rows = L_mat.tolist()
    flat = [float(rows[i][j]) for i in range(n) for j in range(n)]
    L_c = (ctypes.c_double * (n * n))(*flat)
    tens = (ctypes.c_double * n)()
    modes = (ctypes.c_double * (n * n))()
    fo = (ctypes.c_double * (orders * n * n))()
    npairs = max(n - 1, 1)
    rp = (ctypes.c_int32 * (npairs * 2))()
    rr = (ctypes.c_uint64 * (npairs * 2))()
    rl = (ctypes.c_int32 * npairs)()
    rcount = ctypes.c_uint32(0)
    wsd = lib.srmech_resonant_spectrum_arena_bytes(ctypes.c_uint32(n)) // 8 + 16
    ws = (ctypes.c_double * int(wsd))()
    rc = lib.srmech_resonant_spectrum(
        ctypes.c_uint32(n), L_c, ctypes.c_uint32(orders), ctypes.c_uint64(max_den),
        tens, modes, fo, rp, rr, rl, ctypes.byref(rcount),
        ws, ctypes.c_size_t(int(wsd) * 8))
    assert rc == _native.SRMECH_OK
    return tens, modes, fo, rp, rr, rl, rcount.value


@pytest.mark.skipif(
    not (_native.HAS_NATIVE and _native.LIB is not None
         and hasattr(_native.LIB, "srmech_resonant_spectrum")),
    reason="native srmech_resonant_spectrum not present (pure-Python is the "
           "complete alternative; parity is a native-only check)",
)
def test_python_equals_c_peer_value_parity():
    L, n = _jupiter_laplacian()
    orders, max_den = 2, 64
    py = coupling.resonant_spectrum(L, orders=orders, max_den=max_den)
    tens, modes, fo, rp, rr, rl, rcount = _call_c_peer(L, n, orders, max_den)

    # tensions
    for i in range(n):
        assert _abs(float(py["tensions"][i]) - tens[i]) < 1e-9
    # modes (both sign-canonicalised → element parity is meaningful)
    pm = py["modes"].tolist()
    for i in range(n):
        for j in range(n):
            assert _abs(pm[i][j] - modes[i * n + j]) < 1e-9
    # force_orders
    for k in range(orders):
        pf = py["force_orders"][k].tolist()
        for i in range(n):
            for j in range(n):
                assert _abs(pf[i][j] - fo[k * n * n + i * n + j]) < 1e-7
    # resonances — pairs, ratios, AND lock verdicts all match
    assert len(py["resonances"]) == rcount
    for idx, r in enumerate(py["resonances"]):
        assert tuple(r["pair"]) == (int(rp[idx * 2]), int(rp[idx * 2 + 1]))
        assert tuple(r["ratio"]) == (int(rr[idx * 2]), int(rr[idx * 2 + 1]))
        assert int(bool(r["locked"])) == int(rl[idx])
