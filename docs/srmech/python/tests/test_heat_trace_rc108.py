"""rc108 — ``laplacian.heat_trace`` + ``laplacian.ground_state_flux_response``:
the spectral theta / heat trace of a Laplacian (issue #1234 Item 2 / F1007).

WHY: the heat trace Θ(t) = Tr(e^{−tL}) = Σₖ e^{−t·λₖ} IS a theta function of
the Laplacian (on a cycle, the Jacobi-θ family) — the natural READ-INDEPENDENT
spectral summary. F1007 found the mock-theta split under magnetic flux: the
FULL trace is flux-invariant (Poisson → the modular/holomorphic part) while the
flux SHADOW lives only in the ground state λ_min(Φ) (0 → positive as
Φ: 0 → 0.5; periodic in integer flux). Overtone (trace) / undertone (ground
state) = the holomorphic + shadow split (the F999–F1002 asymmetric-beat family).

Covers:
  (a) DoD — heat_trace == the by-hand Σ e^{−t·λ} on BOTH dispatch paths
      (real-symmetric via jacobi_eigvals; complex-Hermitian via
      hermitian_eigendecompose), scalar-t and multi-t (ONE eigensolve, many t);
  (b) the F1007 reproduction — a flux-threaded 12-cycle: the full trace is
      flux-invariant to numerical tolerance; λ_min moves 0 → 1−cos(π/12)
      ≈ 0.0341 as Φ: 0 → 0.5; integer-flux periodicity (gauge equivalence);
  (c) the cycle attestation — heat_trace on Cₙ equals the theta sum over the
      CLOSED-FORM cyclic spectrum λ_k = 2(1 − cos(2πk/n)) (the Jacobi-θ
      family form; the exact θ₃ identity is the Poisson/continuum limit —
      honestly out of scope for a finite-n check);
  (d) Python==C value parity per op (native-only; the pure path is the
      complete alternative) + forced-pure vs native agreement;
  (e) rc105 ``charges=`` composability — a charged (dual-sense) magnetic L
      feeds heat_trace directly; an explicit uniform pattern reproduces the
      ground_state_flux_response default;
  (f) contracts (n < 1, charges-length mismatch, empty/non-finite t/fluxes,
      non-square L) + registration (tool schema; tools.total == 381).

numpy-free; no ``abs()`` (Class-K sign-branch where a magnitude is read).
"""
import ctypes

import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as L
from srmech.amsc import rational as R


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


# π via the same Class-N derivation the laplacian module uses (4·atan(1)).
_PI = 4.0 * float(R.atan(1.0))


def _cycle_edges(n):
    return [(k, (k + 1) % n) for k in range(n)]


def _path4_laplacian():
    """P4 path graph — the §75 fixture (spectrum [0, 0.586, 2, 3.414])."""
    return L.dense_laplacian(4, [(0, 1), (1, 2), (2, 3)], [1.0, 1.0, 1.0])


# The F1007 cycle: 12 nodes, unit weights, per-edge charge Φ/12 (the uniform
# default), so λ_min(Φ) = 1 − cos(2π·Φ/12) and λ_min(0.5) = 1 − cos(π/12).
_N_CYC = 12


# ─────────────────────────────────────────────────────────────────────
# (a) DoD — heat_trace == the by-hand Σ e^{−t·λ}, both paths
# ─────────────────────────────────────────────────────────────────────


def test_heat_trace_matches_by_hand_real_symmetric():
    Lm = _path4_laplacian()
    ev = L.jacobi_eigvals(Lm)
    for t in (0.25, 1.0, 3.0):
        by_hand = sum(
            float(R.exp(-(t * float(ev[i])))) for i in range(ev.shape[0])
        )
        got = L.heat_trace(Lm, t)
        assert isinstance(got, float)
        assert _mag(got - by_hand) <= 1e-9 * by_hand


def test_heat_trace_matches_by_hand_hermitian():
    Hm = L.magnetic_laplacian(4, _cycle_edges(4), [1.0] * 4, q=0.2)
    ev, _V = L.hermitian_eigendecompose(Hm)
    for t in (0.5, 2.0):
        by_hand = sum(
            float(R.exp(-(t * float(ev[i])))) for i in range(ev.shape[0])
        )
        got = L.heat_trace(Hm, t)
        assert _mag(got - by_hand) <= 1e-9 * by_hand


def test_heat_trace_multi_t_is_one_eigensolve_many_t():
    """A t-sequence returns a Vec, elementwise equal to the scalar calls."""
    Lm = _path4_laplacian()
    ts = [0.1, 0.7, 1.3, 5.0]
    vec = L.heat_trace(Lm, ts)
    assert vec.shape == (len(ts),)
    for i, t in enumerate(ts):
        assert float(vec[i]) == L.heat_trace(Lm, t)


def test_heat_trace_at_t_zero_is_n():
    """Θ(0) = Σ e⁰ = n — exact (the Q61 exp cascade gives exp(0) = 1)."""
    Lm = _path4_laplacian()
    assert L.heat_trace(Lm, 0.0) == 4.0


# ─────────────────────────────────────────────────────────────────────
# (b) the F1007 reproduction — flux-invariant trace, ground-state shadow
# ─────────────────────────────────────────────────────────────────────


def test_f1007_ground_state_shadow_moves_with_flux():
    """λ_min: 0 at Φ=0 → 1−cos(π/12) ≈ 0.0341 at Φ=0.5, monotone between."""
    lam = L.ground_state_flux_response(
        _N_CYC, _cycle_edges(_N_CYC), fluxes=[0.0, 0.25, 0.5]
    )
    assert lam.shape == (3,)
    assert _mag(float(lam[0])) < 1e-9                    # Φ=0: exact zero mode
    expected_half = 1.0 - float(R.cos(_PI / _N_CYC))     # 1 − cos(π/12)
    assert _mag(float(lam[2]) - expected_half) < 1e-6    # ≈ 0.03407
    assert float(lam[0]) < float(lam[1]) < float(lam[2])  # 0 → 0.5 monotone


def test_f1007_integer_flux_periodicity():
    """Integer flux is gauge-equivalent to none: λ_min(Φ+1) == λ_min(Φ)."""
    vals = L.ground_state_flux_response(
        _N_CYC, _cycle_edges(_N_CYC), fluxes=[0.0, 0.5, 1.0, 1.5, 2.0]
    )
    assert _mag(float(vals[2]) - float(vals[0])) < 1e-9   # Φ=1 ≡ Φ=0
    assert _mag(float(vals[3]) - float(vals[1])) < 1e-9   # Φ=1.5 ≡ Φ=0.5
    assert _mag(float(vals[4]) - float(vals[0])) < 1e-9   # Φ=2 ≡ Φ=0
    assert float(vals[1]) > 0.03                          # the shadow is real


def test_f1007_full_trace_is_flux_invariant_shadow_is_not():
    """The mock-theta split: Θ(t) invariant across Φ (to numerical
    tolerance — the Φ-dependence is the exponentially small I_n(t) Poisson
    tail), while λ_min moves 0 → ≈0.034."""
    n, t = _N_CYC, 1.0
    edges = _cycle_edges(n)
    pattern = [1.0 / n] * n
    thetas = []
    for phi in (0.0, 0.2, 0.5):
        Hm = L.magnetic_laplacian(
            n, edges, [1.0] * n, charges=[phi * p for p in pattern]
        )
        thetas.append(L.heat_trace(Hm, t))
    for th in thetas[1:]:
        assert _mag(th - thetas[0]) < 1e-9                # flux-invariant
    lam0 = L.ground_state_flux_response(n, edges, fluxes=0.0)
    lam5 = L.ground_state_flux_response(n, edges, fluxes=0.5)
    assert lam5 - lam0 > 0.03                             # the shadow moved


# ─────────────────────────────────────────────────────────────────────
# (c) the cycle attestation — the closed-form cyclic-spectrum theta
# ─────────────────────────────────────────────────────────────────────


def test_cycle_heat_trace_matches_closed_form_theta():
    """On Cₙ the heat trace equals the theta sum over the CLOSED-FORM cyclic
    spectrum λ_k = 2(1 − cos(2πk/n)) — the Jacobi-θ family form of "on a
    cycle, a Jacobi θ" (Class-I cyclic index × Class-N trig × Class-N exp).
    The exact Jacobi θ₃ identity is the Poisson / continuum limit — a
    finite-n eigensolve check attests the finite theta form, honestly."""
    n, t = _N_CYC, 0.7
    Lm = L.dense_laplacian(n, _cycle_edges(n), [1.0] * n)
    got = L.heat_trace(Lm, t)
    closed = sum(
        float(R.exp(-(t * (2.0 * (1.0 - float(R.cos((2.0 * _PI * k) / n)))))))
        for k in range(n)
    )
    assert _mag(got - closed) < 1e-9


# ─────────────────────────────────────────────────────────────────────
# (d) Python==C value parity (native-only) + forced-pure agreement
# ─────────────────────────────────────────────────────────────────────

_HAS_HT = bool(
    _native.HAS_NATIVE and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_heat_trace")
    and hasattr(_native.LIB, "srmech_heat_trace_arena_bytes")
)
_HAS_GS = bool(
    _native.HAS_NATIVE and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_ground_state_flux_response")
    and hasattr(_native.LIB, "srmech_ground_state_flux_response_arena_bytes")
)


def _call_heat_trace_c(rows, n, is_complex, t_list):
    """Drive the C peer directly via ctypes; return the Θ list."""
    lib = _native.LIB
    if is_complex:
        flat = []
        for r in rows:
            for x in r:
                z = complex(x)
                flat.append(z.real)
                flat.append(z.imag)
    else:
        flat = [float(x) for r in rows for x in r]
    L_c = (ctypes.c_double * len(flat))(*flat)
    n_t = len(t_list)
    tb = (ctypes.c_double * n_t)(*t_list)
    out = (ctypes.c_double * n_t)()
    wsb = lib.srmech_heat_trace_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0))
    wsd = int(wsb) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = lib.srmech_heat_trace(
        ctypes.c_uint32(n), ctypes.c_int(1 if is_complex else 0), L_c,
        ctypes.c_uint32(n_t), tb, out, ws, ctypes.c_size_t(wsd * 8))
    assert rc == _native.SRMECH_OK
    return [out[i] for i in range(n_t)]


@pytest.mark.skipif(
    not _HAS_HT,
    reason="native srmech_heat_trace not present (pure-Python is the "
           "complete alternative; parity is a native-only check)",
)
def test_heat_trace_python_equals_c_peer():
    ts = [0.3, 1.0]
    # real-symmetric path
    Lm = _path4_laplacian()
    py = L.heat_trace(Lm, ts)
    c = _call_heat_trace_c(Lm.tolist(), 4, False, ts)
    for i in range(len(ts)):
        assert float(py[i]) == c[i]     # the op routes to the same C peer
    # complex-Hermitian path
    Hm = L.magnetic_laplacian(4, _cycle_edges(4), [1.0] * 4, q=0.2)
    py_h = L.heat_trace(Hm, ts)
    c_h = _call_heat_trace_c(Hm.tolist(), 4, True, ts)
    for i in range(len(ts)):
        assert float(py_h[i]) == c_h[i]


@pytest.mark.skipif(
    not _HAS_HT,
    reason="native srmech_heat_trace not present",
)
def test_heat_trace_forced_pure_agrees_with_native():
    Lm = _path4_laplacian()
    nat = L.heat_trace(Lm, [0.5, 1.5])
    pure = _force_pure(lambda: L.heat_trace(Lm, [0.5, 1.5]))
    for i in range(2):
        assert _mag(float(nat[i]) - float(pure[i])) <= 1e-9 * float(nat[i])


def _call_gsfr_c(n, edges, weights, pattern, flux_list):
    """Drive the C peer directly via ctypes; return the λ_min list."""
    lib = _native.LIB
    n_edges = len(edges)
    eu = (ctypes.c_uint32 * n_edges)(*(u for u, _ in edges))
    ev = (ctypes.c_uint32 * n_edges)(*(v for _, v in edges))
    wb = (ctypes.c_double * n_edges)(*weights)
    pb = (ctypes.c_double * n_edges)(*pattern)
    n_flux = len(flux_list)
    fb = (ctypes.c_double * n_flux)(*flux_list)
    out = (ctypes.c_double * n_flux)()
    wsb = lib.srmech_ground_state_flux_response_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges))
    wsd = int(wsb) // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = lib.srmech_ground_state_flux_response(
        ctypes.c_uint32(n), ctypes.c_uint32(n_edges), eu, ev, wb, pb,
        ctypes.c_uint32(n_flux), fb, out, ws, ctypes.c_size_t(wsd * 8))
    assert rc == _native.SRMECH_OK
    return [out[i] for i in range(n_flux)]


@pytest.mark.skipif(
    not _HAS_GS,
    reason="native srmech_ground_state_flux_response not present (pure-"
           "Python is the complete alternative; parity is a native-only "
           "check)",
)
def test_gsfr_python_equals_c_peer():
    n = 6
    edges = _cycle_edges(n)
    fluxes = [0.0, 0.3, 0.5]
    py = L.ground_state_flux_response(n, edges, fluxes=fluxes)
    c = _call_gsfr_c(n, edges, [1.0] * n, [1.0 / n] * n, fluxes)
    for i in range(len(fluxes)):
        assert float(py[i]) == c[i]     # the op routes to the same C peer


@pytest.mark.skipif(
    not _HAS_GS,
    reason="native srmech_ground_state_flux_response not present",
)
def test_gsfr_forced_pure_agrees_with_native():
    n = 6
    edges = _cycle_edges(n)
    nat = L.ground_state_flux_response(n, edges, fluxes=[0.0, 0.5])
    pure = _force_pure(
        lambda: L.ground_state_flux_response(n, edges, fluxes=[0.0, 0.5])
    )
    assert _mag(float(nat[0]) - float(pure[0])) < 1e-9
    assert _mag(float(nat[1]) - float(pure[1])) < 1e-9


# ─────────────────────────────────────────────────────────────────────
# (e) rc105 charges= composability
# ─────────────────────────────────────────────────────────────────────


def test_charged_magnetic_laplacian_feeds_heat_trace():
    """The rc105 dual-sense fixture (edge (0,1) in BOTH senses, ±q charges)
    builds a charged Hermitian L that heat_trace reads directly: Θ(0) = n
    exactly, Θ positive and strictly decreasing in t (PSD spectrum with a
    positive tension)."""
    Hm = L.magnetic_laplacian(
        2, [(0, 1), (0, 1)], [1.0, 0.5], charges=[+0.125, -0.125]
    )
    assert L.heat_trace(Hm, 0.0) == 2.0
    th1 = L.heat_trace(Hm, 1.0)
    th2 = L.heat_trace(Hm, 2.0)
    assert th1 > 0.0 and th2 > 0.0
    assert th2 < th1


def test_explicit_uniform_pattern_matches_default():
    """charges=[1/n_edges]*n_edges (the rc105 pattern, passed explicitly)
    reproduces the uniform default exactly — the same scaled charges feed
    the same build + eigensolve."""
    n = 6
    edges = _cycle_edges(n)
    d = L.ground_state_flux_response(n, edges, fluxes=[0.3, 0.5])
    e = L.ground_state_flux_response(
        n, edges, fluxes=[0.3, 0.5], charges=[1.0 / n] * n
    )
    assert float(d[0]) == float(e[0])
    assert float(d[1]) == float(e[1])


def test_scalar_flux_returns_float():
    got = L.ground_state_flux_response(4, _cycle_edges(4), fluxes=0.5)
    assert isinstance(got, float)
    assert got > 0.0


# ─────────────────────────────────────────────────────────────────────
# (f) contracts + registration
# ─────────────────────────────────────────────────────────────────────


def test_contract_errors():
    with pytest.raises(ValueError):
        L.ground_state_flux_response(0, [], fluxes=1.0)          # n < 1
    with pytest.raises(ValueError):
        L.ground_state_flux_response(
            3, [(0, 1)], fluxes=0.5, charges=[0.1, 0.2])         # len mismatch
    with pytest.raises(ValueError):
        L.ground_state_flux_response(3, [(0, 1)], fluxes=[])     # empty fluxes
    with pytest.raises(ValueError):
        L.ground_state_flux_response(
            3, [(0, 1)], fluxes=float("nan"))                    # non-finite
    with pytest.raises(ValueError):
        L.heat_trace([[1.0]], [])                                # empty t
    with pytest.raises(ValueError):
        L.heat_trace([[1.0]], float("inf"))                      # non-finite t
    with pytest.raises(ValueError):
        L.heat_trace([[1.0, 0.0]], 1.0)                          # non-square


def test_empty_spectrum_gives_zero_theta():
    assert L.heat_trace([], 1.0) == 0.0


def test_registered_in_tool_schema():
    from srmech.amsc import tool_schema

    schema = tool_schema.get_tool_schema()
    for name in (
        "srmech.amsc.laplacian.heat_trace",
        "srmech.amsc.laplacian.ground_state_flux_response",
    ):
        entry = schema.lookup(name)
        assert entry is not None
        assert entry.owner == "srmech"
        assert entry.category == "laplacian"


def test_tools_total_is_367():
    from srmech import introspect

    assert introspect.describe()["tools"]["total"] == 386
