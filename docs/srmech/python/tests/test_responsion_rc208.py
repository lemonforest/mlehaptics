"""rc208 — RESPONSION: ``laplacian.responsion`` — the response-function
family of a generator L acting on an excitation u0 (F1186: the
op⊗operand⊗responsion k=3 completion — the stored relationship itself;
srmech = Stored-RELATIONSHIP Mechanism).

WHY: the op⊗operand DUALITY (A-N operator verbs ⊗ carrier operand nouns)
completes at k=3 with the responsion — the answering-correspondence
between successive op-on-operand applications. The family generalizes
EPH's ``e^{−zL}`` to the general response function; its two canonical
continuous-form members are LAPLACE-TRANSFORM DUALS:
``kind="propagator"`` = ``e^{−zL}·u0`` (delegates verbatim to the shipped
``propagate``) and ``kind="resolvent"`` = ``(zI − L)^{−1}·u0`` (the
Green's function — NEW, a real complex linear solve via the 2n×2n block
embedding over the shipped Gauss–Jordan kernel).

Covers:
  (a) the PROPAGATOR DIFFERENTIAL — responsion(kind="propagator") is
      EXACTLY equal to propagate at the same dispatch tier (native AND
      forced-pure; it is a verbatim delegation);
  (b) the RESOLVENT RESIDUAL — ``‖(zI−L)·x − u0‖ ≤ 1e-9`` for real L /
      real z, real L / complex z, complex-Hermitian L / complex z (the
      INDEPENDENT check: the defining equation, not the solver);
  (c) the LAPLACE-DUAL EIGEN-CHECK — via an independent
      eigendecomposition, per mode: ``c_res,k·(z−λ_k) == c_0,k`` (the
      resolvent eigen-response 1/(z−λ)) vs ``c_prop,k == e^{−zλ_k}·c_0,k``
      (the propagator eigen-response) — the dual pair on one eigenbasis;
  (d) the QUADRATURE LAPLACE-TRANSFORM IDENTITY —
      ``(zI−L)^{−1}·u0 = ∫₀^∞ e^{−zt}·e^{tL}·u0 dt`` for Re z > max λ(L),
      integrated by Simpson over the SHIPPED propagator at negative time
      (``e^{tL}·u0 = propagate(L, u0, −t)``) — the genuine transform link
      between the two members, verified numerically;
  (e) the RESOLVENT POLE — z exactly in spec(L) raises ZeroDivisionError
      honestly (native AND forced-pure; the pole IS the physics);
  (f) Python == C parity — native vs forced-pure resolvent within 1e-9;
  (g) the C peer DIRECTLY (bare-C host contract) — srmech_responsion
      kind=0 byte-identical to srmech_eph_propagate; kind=1 equal to the
      public op;
  (h) read-only inputs; contracts (unknown kind, non-square L, u0
      mismatch, n = 0); return carrier (complex Vec); registration
      (ToolEntry; tools.total == 418; LAPLACIAN_OPS).

numpy-free. cmath is the test-side INDEPENDENT reference (never the op's
own machinery).
"""
import cmath
import ctypes

from srmech import _native
from srmech.math import laplacian as L


# ── helpers (no numpy) ──────────────────────────────────────────────────


def _force_pure(fn):
    """Run fn with the native dispatch masked (the complete pure path)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def _mag(z) -> float:
    """|z| via Class-K squares + sqrt (test-side magnitude)."""
    c = complex(z)
    return (c.real * c.real + c.imag * c.imag) ** 0.5


def _matvec(A, x, n):
    """Complex A·x (test-side independent reference — hand accumulation)."""
    out = []
    for i in range(n):
        acc = 0j
        for j in range(n):
            acc += complex(A[i][j]) * complex(x[j])
        out.append(acc)
    return out


def _residual(Lm, x, u0, z, n) -> float:
    """‖(zI − L)·x − u0‖ — the resolvent's DEFINING equation, checked
    independently of any solve machinery."""
    z = complex(z)
    A = [[(z if i == j else 0j) - complex(Lm[i][j]) for j in range(n)]
         for i in range(n)]
    ax = _matvec(A, x, n)
    s = 0.0
    for i in range(n):
        d = ax[i] - complex(u0[i])
        s += d.real * d.real + d.imag * d.imag
    return s ** 0.5


def _L2():
    """[[2,-1],[-1,2]] — eigenvalues exactly 1 and 3."""
    return [[2.0, -1.0], [-1.0, 2.0]]


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


# ── (a) the propagator member IS propagate (verbatim delegation) ────────


def test_propagator_kind_exactly_equals_propagate_native_tier():
    for n, seed in ((2, 11), (4, 22), (7, 33)):
        Lm = _rand_lap(n, seed)
        u0 = [((i * 7 + 3) % 11) - 5.0 for i in range(n)]
        for z in (0.7 + 0j, 3.9j, 1.1 * cmath.exp(1j * 0.7)):
            a = L.propagate(Lm, u0, z)
            b = L.responsion(Lm, u0, z, kind="propagator")
            for i in range(n):
                assert complex(a[i]) == complex(b[i]), (
                    f"n={n} z={z} node {i}: responsion propagator "
                    f"{complex(b[i])!r} != propagate {complex(a[i])!r} "
                    f"(delegation must be verbatim)")


def test_propagator_kind_is_default_and_pure_tier_identical():
    Lm = _rand_lap(5, 99)
    u0 = [1.0, -0.5, 0.25, 0.0, 2.0]
    z = 2.5j

    def both():
        return L.propagate(Lm, u0, z), L.responsion(Lm, u0, z)

    a, b = _force_pure(both)
    for i in range(5):
        assert complex(a[i]) == complex(b[i])


# ── (b) the resolvent residual: the defining equation, independently ────


def test_resolvent_residual_real_L_real_z():
    for n, seed in ((2, 5), (4, 17), (8, 29)):
        Lm = _rand_lap(n, seed)
        u0 = [((i * 5 + 2) % 7) - 3.0 for i in range(n)]
        # Any non-spectral z solves (the residual check needs no Re z > λ_max
        # — that condition is only for the transform INTEGRAL, test (d)).
        for z in (5.0 + 0j, -2.5 + 0j, 0.31 + 0j):
            x_vec = L.responsion(Lm, u0, z, kind="resolvent")
            x = [complex(x_vec[i]) for i in range(n)]
            r = _residual(Lm, x, u0, z, n)
            assert r <= 1e-9, f"n={n} z={z}: residual {r:.3e} > 1e-9"


def test_resolvent_residual_real_L_complex_z():
    for n, seed in ((3, 7), (6, 41)):
        Lm = _rand_lap(n, seed)
        u0 = [1.0] * n
        for z in (2.0 + 3.0j, -1.0 + 0.5j, 4.7j):
            x_vec = L.responsion(Lm, u0, z, kind="resolvent")
            x = [complex(x_vec[i]) for i in range(n)]
            r = _residual(Lm, x, u0, z, n)
            assert r <= 1e-9, f"n={n} z={z}: residual {r:.3e} > 1e-9"


def test_resolvent_residual_hermitian_L_complex_z():
    H = [[2.0 + 0j, 1j], [-1j, 2.0 + 0j]]      # eigenvalues 1, 3
    u0 = [1.0 + 0.5j, -0.25 + 0j]
    for z in (5.0 + 0j, 2.0 + 2.0j, -3.0 + 1.0j):
        x_vec = L.responsion(H, u0, z, kind="resolvent")
        x = [complex(x_vec[i]) for i in range(2)]
        r = _residual(H, x, u0, z, 2)
        assert r <= 1e-9, f"z={z}: residual {r:.3e} > 1e-9"
    # complex excitation genuinely rides: the response is complex
    x_vec = L.responsion(H, u0, 2.0 + 2.0j, kind="resolvent")
    assert x_vec.is_complex


# ── (c) the Laplace-dual eigen-check: 1/(z−λ) vs e^{−zλ} per mode ───────


def test_laplace_dual_eigen_responses_per_mode():
    """One independent eigenbasis; per mode k the dual pair:
    resolvent  c_res,k = c_0,k / (z − λ_k)   (checked as c_res,k·(z−λ_k))
    propagator c_prop,k = e^{−z·λ_k}·c_0,k   (cmath.exp the independent ref)
    — the SAME relationship object read in the two Laplace-dual domains."""
    Lm = _L2()                                  # λ = 1, 3 exactly
    n = 2
    u0 = [1.0, 0.25]
    z = 2.0 + 1.5j
    eigvals, V = L.symmetric_eigendecompose(Lm)  # independent eigensolve
    Vl = V.tolist()
    lam = [float(eigvals[k]) for k in range(n)]
    c0 = [sum(Vl[i][k] * u0[i] for i in range(n)) for k in range(n)]

    x_res = L.responsion(Lm, u0, z, kind="resolvent")
    x_prop = L.responsion(Lm, u0, z, kind="propagator")
    c_res = [sum(Vl[i][k] * complex(x_res[i]) for i in range(n))
             for k in range(n)]
    c_prop = [sum(Vl[i][k] * complex(x_prop[i]) for i in range(n))
              for k in range(n)]
    for k in range(n):
        # resolvent eigen-response: c_res,k·(z − λ_k) == c_0,k
        d1 = c_res[k] * (z - lam[k]) - c0[k]
        assert _mag(d1) <= 1e-9, (
            f"mode {k} (λ={lam[k]}): resolvent eigen-response violates "
            f"1/(z−λ): err {_mag(d1):.3e}")
        # propagator eigen-response: c_prop,k == e^{−z·λ_k}·c_0,k
        d2 = c_prop[k] - cmath.exp(-z * lam[k]) * c0[k]
        assert _mag(d2) <= 1e-9, (
            f"mode {k} (λ={lam[k]}): propagator eigen-response violates "
            f"e^(−zλ): err {_mag(d2):.3e}")


# ── (d) the quadrature Laplace-transform identity (the genuine link) ────


def test_laplace_transform_quadrature_identity():
    """(zI − L)^{−1}·u0 = ∫₀^∞ e^{−zt}·e^{tL}·u0 dt for Re z > max λ(L),
    with e^{tL}·u0 = propagate(L, u0, −t) — Simpson quadrature over the
    SHIPPED propagator, truncated at T where the integrand ~ e^{−(z−λ)T}
    is far below the check tolerance. The slowest decay here is
    e^{−(5−3)t} = e^{−2t} → T = 16 leaves ~1e-14."""
    Lm = _L2()                                  # λ_max = 3
    n = 2
    u0 = [1.0, 0.25]
    z = 5.0                                     # Re z = 5 > 3
    T = 16.0
    steps = 640                                 # Simpson: even count
    h = T / steps
    acc = [0j] * n
    for j in range(steps + 1):
        t = j * h
        w = 1.0 if j in (0, steps) else (4.0 if j % 2 == 1 else 2.0)
        e_tL_u0 = L.propagate(Lm, u0, -t)       # e^{+tL}·u0
        f = cmath.exp(-z * t)
        for i in range(n):
            acc[i] += w * f * complex(e_tL_u0[i])
    integral = [a * (h / 3.0) for a in acc]
    x_res = L.responsion(Lm, u0, z, kind="resolvent")
    for i in range(n):
        d = _mag(integral[i] - complex(x_res[i]))
        assert d <= 1e-6, (
            f"node {i}: quadrature Laplace transform {integral[i]!r} != "
            f"resolvent {complex(x_res[i])!r} (err {d:.3e})")


# ── (e) the resolvent pole: z ∈ spec(L) is honest, never a number ───────


def test_resolvent_pole_raises_native_tier():
    import pytest
    # λ = 3 exactly for _L2(); (3I − L) = [[1,1],[1,1]] is exactly singular.
    with pytest.raises(ZeroDivisionError):
        L.responsion(_L2(), [1.0, 0.0], 3.0, kind="resolvent")


def test_resolvent_pole_raises_pure_tier():
    import pytest
    with pytest.raises(ZeroDivisionError):
        _force_pure(
            lambda: L.responsion(_L2(), [1.0, 0.0], 3.0, kind="resolvent"))


# ── (f) Python == C parity ──────────────────────────────────────────────


def test_resolvent_native_equals_pure():
    for n, seed in ((2, 3), (5, 13), (9, 77)):
        Lm = _rand_lap(n, seed)
        u0 = [((i * 3 + 1) % 5) - 2.0 for i in range(n)]
        for z in (4.0 + 0j, 1.0 + 2.0j, -0.7 + 0.9j):
            nat = L.responsion(Lm, u0, z, kind="resolvent")
            pur = _force_pure(
                lambda: L.responsion(Lm, u0, z, kind="resolvent"))
            err = max(_mag(complex(nat[i]) - complex(pur[i]))
                      for i in range(n))
            assert err <= 1e-9, f"n={n} z={z}: native vs pure err {err:.3e}"


# ── (g) the C peer directly (the bare-C host contract) ──────────────────


def _native_responsion_ready():
    return (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_responsion")
            and hasattr(_native.LIB, "srmech_responsion_arena_bytes"))


def test_c_peer_kind0_byte_identical_to_eph_propagate():
    """srmech_responsion kind=0 IS srmech_eph_propagate (pass-through
    delegation) — byte-identical outputs from the same lib."""
    import pytest
    if not _native_responsion_ready():
        pytest.skip("native srmech_responsion not available")
    Lm = _L2()
    n = 2
    u0 = [1.0, 0.25]
    zr, zi = 0.4, 1.7
    flat = [float(x) for r in Lm for x in r]
    L_c = (ctypes.c_double * len(flat))(*flat)
    u_c = (ctypes.c_double * (2 * n))(*[v for x in u0 for v in (x, 0.0)])
    out_a = (ctypes.c_double * (2 * n))()
    out_b = (ctypes.c_double * (2 * n))()
    ws_bytes = int(_native.LIB.srmech_responsion_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_int(0), ctypes.c_int(0)))
    wsd = ws_bytes // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc_a = _native.LIB.srmech_responsion(
        ctypes.c_uint32(n), ctypes.c_int(0), ctypes.c_int(0), L_c, u_c,
        ctypes.c_double(zr), ctypes.c_double(zi), out_a, ws,
        ctypes.c_size_t(wsd * 8))
    ws2 = (ctypes.c_double * wsd)()
    rc_b = _native.LIB.srmech_eph_propagate(
        ctypes.c_uint32(n), ctypes.c_int(0), L_c, u_c,
        ctypes.c_double(zr), ctypes.c_double(zi), out_b, ws2,
        ctypes.c_size_t(wsd * 8))
    assert rc_a == _native.SRMECH_OK and rc_b == _native.SRMECH_OK
    assert list(out_a) == list(out_b), (
        "kind=0 must be a byte-identical pass-through to srmech_eph_propagate")


def test_c_peer_kind1_matches_public_op():
    import pytest
    if not _native_responsion_ready():
        pytest.skip("native srmech_responsion not available")
    Lm = _rand_lap(4, 55)
    n = 4
    u0 = [1.0, -0.5, 0.25, 2.0]
    zr, zi = 3.5, 0.8
    flat = [float(x) for r in Lm for x in r]
    L_c = (ctypes.c_double * len(flat))(*flat)
    u_c = (ctypes.c_double * (2 * n))(*[v for x in u0 for v in (x, 0.0)])
    out = (ctypes.c_double * (2 * n))()
    ws_bytes = int(_native.LIB.srmech_responsion_arena_bytes(
        ctypes.c_uint32(n), ctypes.c_int(0), ctypes.c_int(1)))
    assert ws_bytes > 0
    wsd = ws_bytes // 8 + 16
    ws = (ctypes.c_double * wsd)()
    rc = _native.LIB.srmech_responsion(
        ctypes.c_uint32(n), ctypes.c_int(0), ctypes.c_int(1), L_c, u_c,
        ctypes.c_double(zr), ctypes.c_double(zi), out, ws,
        ctypes.c_size_t(wsd * 8))
    assert rc == _native.SRMECH_OK
    got = [complex(out[2 * i], out[2 * i + 1]) for i in range(n)]
    x_vec = L.responsion(Lm, u0, complex(zr, zi), kind="resolvent")
    err = max(_mag(got[i] - complex(x_vec[i])) for i in range(n))
    assert err <= 1e-12, f"direct C kind=1 vs public op err {err:.3e}"
    # And the defining equation holds on the direct-C output too.
    assert _residual(Lm, got, u0, complex(zr, zi), n) <= 1e-9


# ── (h) read-only + contracts + carrier + registration ──────────────────


def test_inputs_unmutated():
    Lm = _L2()
    u0 = [1.0, 0.5]
    Lsnap = [row[:] for row in Lm]
    usnap = u0[:]
    L.responsion(Lm, u0, 0.7 + 0.3j, kind="resolvent")
    L.responsion(Lm, u0, 0.7 + 0.3j, kind="propagator")
    assert Lm == Lsnap, "L mutated"
    assert u0 == usnap, "u0 mutated"


def test_contracts():
    import pytest
    with pytest.raises(ValueError):
        L.responsion(_L2(), [1.0, 0.0], 1.0, kind="green")   # unknown kind
    with pytest.raises(ValueError):
        L.responsion([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], [1.0, 2.0],
                     5.0, kind="resolvent")                  # non-square
    with pytest.raises(ValueError):
        L.responsion([[1.0, 0.0], [0.0, 1.0]], [1.0], 5.0,
                     kind="resolvent")                       # u0 mismatch
    r0 = L.responsion([], [], 5.0, kind="resolvent")         # n = 0
    assert r0.shape == (0,)


def test_return_carrier_is_complex_vec():
    from srmech.math.vec import Vec
    x = L.responsion(_L2(), [1.0, 0.0], 5.0, kind="resolvent")
    assert isinstance(x, Vec)
    assert x.is_complex
    assert x.shape == (2,)


def test_registration_and_count():
    import srmech
    from srmech.introspect.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.math.laplacian.responsion" in names
    assert len(get_tool_schema().tools) == 533
    assert srmech.describe()["tools"]["total"] == 533
    assert "responsion" in L.LAPLACIAN_OPS
    assert "responsion" in L.__all__
