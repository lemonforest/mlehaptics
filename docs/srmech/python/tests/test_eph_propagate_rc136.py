"""rc136 — EPH: ``laplacian.propagate`` + ``laplacian.eph_harvest`` — the
complex-time Wick-rotation propagator ``harvest = e^{-zL}·u0`` (siona gh#1274).

WHY: EPH = ``harvest = Propagate·excite`` generalises the op⊗operand pattern to
a full retrieval / inference cascade — a propagator ``P = e^{-zL}`` (operator)
applied to an excitation ``u0`` (operand) → the harvest ``H``. The thermal
``e^{-tL}`` and the coherent ``e^{-itL}`` are NOT two ops: they are the ONE
complex-time propagator ``e^{-zL}`` with ``z`` COMPLEX, the ``i`` being the
Wick-rotation phase. ``arg(z)`` is the coherence dial (real → thermal,
imaginary → coherent, between → partial). RBS-SNN = EPH-with-a-synaptic-
propagator; no privileged instance.

Covers:
  (a) DoD — propagate == an INDEPENDENT e^{-zL}·u0 reference (a numpy-free
      scaling-and-squaring Taylor matrix-exp with stdlib cmath.exp, independent
      of the eigensolver + the Class-N seam-folded scalar), on thermal /
      coherent / partial z, real + complex-Hermitian L;
  (b) the WICK DIAL — z real → thermal (real, decaying); z imaginary →
      coherent (unitary, ‖harvest‖ ≈ ‖u0‖ conserved); arg(z) between → partial,
      the coherence (norm-retention) MONOTONIC across the dial (the siona
      0.34 → 0.44 → 0.92 shape);
  (c) THE 2π SEAM-FOLD (the crux) — propagate CORRECT at large t·λ (≈ 44) vs
      the independent reference (≈ 1.0), while the RAW cos_series_truncate(44,
      1, N) blows up to ~2.3e17 (the with-fold-vs-without-fold contrast);
  (d) the Born-rule harvest + the EPH read (excite → propagate → rank the
      reaction center by |harvest_i|²);
  (e) read-only (L and u0 unmutated);
  (f) Python == C value parity (native vs forced-pure) — the harvest is
      basis-invariant, so it agrees to the eigensolve tolerance;
  (g) contracts (non-square L, u0-length mismatch, n = 0) + registration
      (tool schema; tools.total == 403; both ToolEntries present).

numpy-free; no ``abs()`` (Class-K sign-branch / squares where a magnitude is
read).
"""
import cmath
import math

from srmech.amsc import _native
from srmech.amsc import laplacian as L
from srmech.amsc.rational import cos_series_truncate


# ── helpers (no numpy, no abs()) ────────────────────────────────────────


def _mag2(z):
    """Born |z|² = re² + im² (Class-K squares, never abs())."""
    c = complex(z)
    return c.real * c.real + c.imag * c.imag


def _norm(vec):
    """‖vec‖ over a complex sequence (Class-K squares + Class-N sqrt)."""
    return math.sqrt(sum(_mag2(x) for x in vec))


def _force_pure(fn):
    """Run fn with the native dispatch masked (the complete pure path)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


# ── an INDEPENDENT e^{-zL}·u0 reference: scaling-and-squaring Taylor of the
#    matrix exponential (stdlib cmath.exp only; NO eigensolver, NO Class-N
#    series — genuinely independent of the op under test). ────────────────


def _cmatmul(A, B):
    n = len(A)
    out = [[0j] * n for _ in range(n)]
    for i in range(n):
        for k in range(n):
            aik = A[i][k]
            if aik == 0:
                continue
            for j in range(n):
                out[i][j] += aik * B[k][j]
    return out


def _cmatvec(A, v):
    n = len(A)
    return [sum(A[i][j] * v[j] for j in range(n)) for i in range(n)]


def _expm(M, terms=28, squarings=8):
    """e^M for a small complex matrix via (Σ_{k≤terms} (M/2^s)^k / k!)^(2^s)."""
    n = len(M)
    s = squarings
    scale = float(1 << s)
    Ms = [[M[i][j] / scale for j in range(n)] for i in range(n)]
    # P = Σ (Ms)^k / k!
    P = [[1.0 + 0j if i == j else 0j for j in range(n)] for i in range(n)]
    term = [[1.0 + 0j if i == j else 0j for j in range(n)] for i in range(n)]
    for k in range(1, terms + 1):
        term = _cmatmul(term, Ms)
        term = [[term[i][j] / k for j in range(n)] for i in range(n)]
        P = [[P[i][j] + term[i][j] for j in range(n)] for i in range(n)]
    for _ in range(s):
        P = _cmatmul(P, P)
    return P


def _ref(Lm, u0, z):
    """Independent reference harvest = e^{-zL}·u0."""
    n = len(Lm)
    M = [[-(z) * complex(Lm[i][j]) for j in range(n)] for i in range(n)]
    E = _expm(M)
    return _cmatvec(E, [complex(x) for x in u0])


def _P4():
    """P4 path-graph Laplacian (spectrum [0, 0.586, 2, 3.414])."""
    return L.dense_laplacian(4, [(0, 1), (1, 2), (2, 3)], [1.0, 1.0, 1.0])


def _rand_lap(n, seed):
    """A random real-symmetric graph Laplacian L = D − A (no numpy)."""
    st = seed
    def rnd():
        nonlocal st
        st = (st * 1103515245 + 12345) & 0x7FFFFFFF
        return st / float(0x7FFFFFFF)
    A = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            w = rnd()
            A[i][j] = w
            A[j][i] = w
    out = [[0.0] * n for _ in range(n)]
    for i in range(n):
        deg = sum(A[i])
        for j in range(n):
            out[i][j] = (deg if i == j else 0.0) - A[i][j]
    return out


# ── (a) DoD: propagate == the independent reference ─────────────────────


def test_propagate_matches_independent_reference():
    Lm = _P4()
    u0 = [1.0, 0.0, 0.0, 0.0]
    for z in (0.7 + 0j, 0.5j, 1.3 * cmath.exp(1j * 0.6), 1.0 + 0.5j):
        hv = L.propagate(Lm, u0, z)
        got = [complex(hv[i]) for i in range(4)]
        ref = _ref(Lm, u0, z)
        err = max(_mag2(got[i] - ref[i]) for i in range(4)) ** 0.5
        assert err < 1e-9, f"z={z}: propagate vs reference err={err:.3e}"


def test_propagate_hand_2x2():
    # L = [[2,-1],[-1,2]] eigenvalues 1, 3; analytic reference.
    Lm = [[2.0, -1.0], [-1.0, 2.0]]
    u0 = [1.0, 0.0]
    r = 1.0 / math.sqrt(2.0)
    V = [[r, r], [r, -r]]
    lam = [1.0, 3.0]
    for z in (0.4 + 0j, 0.9j, 0.6 * cmath.exp(1j * 0.9)):
        c = [sum(V[i][k] * u0[i] for i in range(2)) * cmath.exp(-z * lam[k])
             for k in range(2)]
        ref = [sum(V[i][k] * c[k] for k in range(2)) for i in range(2)]
        hv = L.propagate(Lm, u0, z)
        got = [complex(hv[i]) for i in range(2)]
        err = max(_mag2(got[i] - ref[i]) for i in range(2)) ** 0.5
        assert err < 1e-10, f"z={z}: err={err:.3e}"


def test_complex_hermitian_input():
    # Hermitian [[2, i], [-i, 2]] — eigenvalues 1, 3; coherent conserves norm.
    H = [[2.0 + 0j, 1j], [-1j, 2.0 + 0j]]
    u0 = [1.0 + 0j, 0.0 + 0j]
    hv = L.propagate(H, u0, 0.5j)
    got = [complex(hv[i]) for i in range(2)]
    ref = _ref(H, u0, 0.5j)
    err = max(_mag2(got[i] - ref[i]) for i in range(2)) ** 0.5
    assert err < 1e-9
    assert abs(_norm(got) - 1.0) < 1e-9   # coherent → unitary


# ── (b) the WICK dial: thermal / coherent / partial, monotonic ──────────


def test_wick_dial_thermal_is_real_and_decaying():
    Lm = _P4()
    u0 = [1.0, 0.5, -0.5, 1.0]
    hv = L.propagate(Lm, u0, 0.8 + 0j)      # z real → thermal
    got = [complex(hv[i]) for i in range(4)]
    for x in got:
        assert abs(x.imag) < 1e-9, "thermal harvest must be REAL"
    assert _norm(got) < _norm(u0)           # positive spectrum damps


def test_wick_dial_coherent_conserves_norm():
    Lm = _P4()
    u0 = [1.0, 0.5, -0.5, 1.0]
    for t in (0.3, 1.0, 3.5):
        hv = L.propagate(Lm, u0, complex(0.0, t))   # z imaginary → coherent
        got = [complex(hv[i]) for i in range(4)]
        assert abs(_norm(got) - _norm(u0)) < 1e-9, f"t={t}: norm not conserved"


def test_wick_dial_partial_is_monotonic():
    """The coherence (norm-retention) rises monotonically thermal → coherent —
    the siona 0.34 → 0.44 → 0.92 shape (only the unified z-form names the
    partial middle)."""
    Lm = _P4()
    u0 = [1.0, 0.5, -0.5, 1.0]
    n0 = _norm(u0)
    t = 1.5
    prev = -1.0
    ratios = []
    for dial in (0.0, 0.25, 0.5, 0.75, 1.0):
        phi = dial * (math.pi / 2.0)
        z = t * complex(math.cos(phi), math.sin(phi))
        hv = L.propagate(Lm, u0, z)
        ratio = _norm([complex(hv[i]) for i in range(4)]) / n0
        ratios.append(ratio)
        assert ratio >= prev - 1e-12, f"non-monotonic at dial={dial}: {ratios}"
        prev = ratio
    assert ratios[0] < ratios[-1]                 # genuinely rising
    assert abs(ratios[-1] - 1.0) < 1e-9           # coherent limit conserves


# ── (c) THE 2π SEAM-FOLD (the crux) ─────────────────────────────────────


def test_seam_fold_correct_at_large_t_lambda():
    """propagate is EXACT at large t·λ (≈ 44) vs the independent reference —
    the mandatory Machin-2π seam-fold at work."""
    Lm = [[2.0, -1.0], [-1.0, 2.0]]           # eigenvalues 1, 3
    u0 = [1.0, 0.0]
    t = 44.0 / 3.0                            # coherent: t·λ_max = 44
    z = complex(0.0, t)
    hv = L.propagate(Lm, u0, z)
    got = [complex(hv[i]) for i in range(2)]
    ref = _ref(Lm, u0, z)
    err = max(_mag2(got[i] - ref[i]) for i in range(2)) ** 0.5
    assert err < 1e-9, f"seam-fold FAILED at t·λ=44: err={err:.3e}"
    assert abs(_norm(got) - 1.0) < 1e-9      # still unitary (not 2.3e17)


def test_seam_fold_vs_no_fold_contrast():
    """The with-fold-vs-without contrast: the RAW Class-N cos series BLOWS UP
    past its convergence radius (the reason the seam-fold is mandatory)."""
    raw = cos_series_truncate(44, 1, 18)     # NO fold — diverged partial sum
    raw_val = raw[0] / raw[1]
    assert abs(raw_val) > 1e6, "raw cos_series should blow up (>1e6)"
    # the folded propagate gets ~cos(44) ≈ 0.9998 right (see the large-t test):
    Lm = [[1.0, 0.0], [0.0, 0.0]]            # eigenvalues 1, 0
    hv = L.propagate(Lm, [1.0, 0.0], complex(0.0, 44.0))  # mode-0 phase = 44 rad
    got0 = complex(hv[0])
    assert abs(got0.real - math.cos(44.0)) < 1e-9   # folded → true cos(44)
    assert abs(got0.imag + math.sin(44.0)) < 1e-9   # e^{-i·44} = cos − i·sin


# ── (d) the Born-rule harvest + the EPH read ────────────────────────────


def test_eph_harvest_born_rule_and_rank():
    Lm = _P4()
    u0 = [1.0, 0.0, 0.0, 0.0]
    r = L.eph_harvest(Lm, u0, 0.6 + 0j)
    assert set(r) == {"ranked_nodes", "energies", "reaction_center",
                      "total_energy", "harvest_re", "harvest_im"}
    energies = r["energies"]
    # Born rule: energy_i == |harvest_i|² of the raw components
    for i in range(4):
        recomputed = r["harvest_re"][i] ** 2 + r["harvest_im"][i] ** 2
        assert abs(energies[i] - recomputed) < 1e-12
    # ranked descending by energy
    ranked = r["ranked_nodes"]
    assert ranked == sorted(range(4), key=lambda i: energies[i], reverse=True)
    assert r["reaction_center"] == ranked[0]
    assert abs(r["total_energy"] - sum(energies)) < 1e-12
    # JSON-native (ints / floats only)
    assert all(isinstance(i, int) for i in ranked)
    assert all(isinstance(e, float) for e in energies)


def test_eph_harvest_reaction_center_is_seeded_node_under_weak_coupling():
    """Excite node 0; a short thermal propagation keeps the reaction center at
    the seeded node (energy = relevance)."""
    Lm = _P4()
    r = L.eph_harvest(Lm, [1.0, 0.0, 0.0, 0.0], 0.2 + 0j)
    assert r["reaction_center"] == 0


# ── (e) read-only ───────────────────────────────────────────────────────


def test_inputs_unmutated():
    Lm = _P4()
    u0 = [1.0, 0.5, -0.5, 1.0]
    Lsnap = [row[:] for row in Lm]
    usnap = u0[:]
    L.propagate(Lm, u0, 0.7 + 0.3j)
    L.eph_harvest(Lm, u0, 0.7 + 0.3j)
    assert Lm == Lsnap, "L mutated"
    assert u0 == usnap, "u0 mutated"


# ── (f) Python == C value parity (native vs forced-pure) ────────────────


def test_python_equals_c_parity():
    tol = 1e-8
    for n in (2, 3, 5, 8):
        Lm = _rand_lap(n, 1234 + n)
        u0 = [((i * 7 + 3) % 11) - 5.0 for i in range(n)]   # deterministic
        for z in (0.7 + 0j, 0.9j, 1.1 * cmath.exp(1j * 0.7), 2.0j):
            native = L.propagate(Lm, u0, z)
            pure = _force_pure(lambda: L.propagate(Lm, u0, z))
            got = [complex(native[i]) for i in range(n)]
            pur = [complex(pure[i]) for i in range(n)]
            err = max(_mag2(got[i] - pur[i]) for i in range(n)) ** 0.5
            assert err < tol, f"n={n} z={z}: native vs pure err={err:.3e}"


# ── (g) contracts + registration ────────────────────────────────────────


def test_contracts():
    import pytest
    with pytest.raises(ValueError):
        L.propagate([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], [1.0, 2.0], 1.0)  # non-square
    with pytest.raises(ValueError):
        L.propagate([[1.0, 0.0], [0.0, 1.0]], [1.0], 1.0)               # u0 mismatch
    hv0 = L.propagate([], [], 1.0)                                       # n = 0
    assert hv0.shape == (0,)
    assert hv0.is_complex


def test_registration_and_count():
    import srmech
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.propagate" in names
    assert "srmech.amsc.laplacian.eph_harvest" in names
    assert len(get_tool_schema().tools) == 403
    assert srmech.describe()["tools"]["total"] == 403
    assert "propagate" in L.LAPLACIAN_OPS
    assert "eph_harvest" in L.LAPLACIAN_OPS
