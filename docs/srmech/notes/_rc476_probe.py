"""rc476 (`#T1188`) D1 — the before/after PROBE, one NDJSON row per measurement.

Run in a cell, redirect to a file, run again in the other cell, diff::

    cd docs/srmech/python
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 ../notes/_rc476_probe.py > before.ndjson

Two halves, deliberately separated, because D1 has two halves and the design's
own ripple table conflated them:

* ``defect.*`` rows measure the PRIMITIVE (``rational.sqrt`` / ``hypot``)
  against the integer oracle in ``_rc476_oracle.py``;
* ``site.*`` rows measure the SERVED VALUE of each consumer the 19 site
  rewrites touch, so "which rewrite moved a served value" is answered by a
  diff and not by an argument.

Every float is reported as its IEEE bit pattern, never as a decimal, because a
decimal repr is lossy exactly where this round is interesting.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _rc476_oracle import (  # noqa: E402
    certify,
    cr_sqrt_bits,
    float_bits,
    unpack_positive,
)

ROWS = []


def emit(name, **kw):
    ROWS.append(dict(probe=name, **kw))


def step(name, fn):
    """Run one probe.  A probe that cannot run says so IN A ROW rather than
    taking the rest of the run with it — a missing row and a moved row must
    never look the same in the diff."""
    try:
        emit(name, **fn())
    except Exception as exc:                       # noqa: BLE001 — reported, not hidden
        emit(name, error=f"{type(exc).__name__}: {exc}")


def bits(x) -> str:
    return "0x%016x" % float_bits(float(x))


def qpair(q) -> str:
    n, d = q.as_pair()
    return f"{n}/{d}"


# ── half 1: the primitive, against the integer oracle ────────────────────
def defect_rows():
    from srmech.math import rational as R
    from srmech import _native

    # M1a — integers 2..2000, non-squares, through the FLOAT route
    bad = low = 0
    worst = 0
    first = []
    for x in range(2, 2001):
        r = 1
        while (r + 1) * (r + 1) <= x:
            r += 1
        if r * r == x:
            continue
        got = float_bits(float(R.sqrt(float(x))))
        want = cr_sqrt_bits(x, 1)
        if got != want:
            bad += 1
            d = got - want
            if d < 0:
                low += 1
            if d < worst:
                worst = d
            if len(first) < 5:
                first.append(x)
    emit("defect.M1a_float_route_ints", bad=bad, of=1956, low=low,
         worst_ulps=worst, first=first)

    # M1b — the RECIPROCAL composition, the site-rewrite motivation
    bad = 0
    for k in range(2, 201):
        r = 1
        while (r + 1) * (r + 1) <= k:
            r += 1
        if r * r == k:
            continue
        got = float_bits(1.0 / float(R.sqrt(float(k))))
        want = cr_sqrt_bits(1, k)
        if got != want:
            bad += 1
    emit("defect.M1b_reciprocal_compose", bad=bad, of=186)

    # M1c — the rc474 EXACT-operand route
    bad = 0
    for x in range(2, 2001):
        r = 1
        while (r + 1) * (r + 1) <= x:
            r += 1
        if r * r == x:
            continue
        if float_bits(float(R.sqrt(x))) != cr_sqrt_bits(x, 1):
            bad += 1
    emit("defect.M1c_exact_route_ints", bad=bad, of=1956)

    # M1d — EVERY subnormal mantissa 1..4096
    import struct
    bad = 0
    worst = 0
    for mant in range(1, 4097):
        xv = struct.unpack("<d", struct.pack("<Q", mant))[0]
        got = float_bits(float(R.sqrt(xv)))
        want = cr_sqrt_bits(mant, 1 << 1074)
        if got != want:
            bad += 1
            d = got - want
            if d < worst:
                worst = d
    emit("defect.M1d_subnormal_mantissas", bad=bad, of=4096, worst_ulps=worst)

    # positive control for the subnormal predicate: the MIN NORMAL is fine
    minnorm = struct.unpack("<d", struct.pack("<Q", 1 << 52))[0]
    emit("defect.M1d_control_min_normal",
         delta=float_bits(float(R.sqrt(minnorm))) - cr_sqrt_bits(1 << 52, 1 << 1074))

    # M1e — the native (root, p) width through the shipped C entry
    if _native.has_native_trans_q61():
        mn, mx = 999, 0
        rows = [float(x) for x in range(2, 2001)]
        rows += [struct.unpack("<d", struct.pack("<Q", m))[0] for m in range(1, 4097)]
        for xv in rows:
            root, _p = _native.sqrt_q61_c(xv)
            w = int(root).bit_length()
            if w < mn:
                mn = w
            if w > mx:
                mx = w
        emit("defect.M1e_native_root_width", min_bits=mn, max_bits=mx, rows=len(rows))
    else:
        emit("defect.M1e_native_root_width", min_bits=None, note="no native lib")

    # certificate cross-check on the served value of a handful of anchors
    for p, q in ((2, 1), (3, 1), (1, 2), (1, 3), (3, 4), (8, 1)):
        b = cr_sqrt_bits(p, q)
        m, f = unpack_positive(b)
        emit("defect.certificate", p=p, q=q, cr="0x%016x" % b,
             certified=certify(m, f, p, q),
             rejects_up=not certify(*unpack_positive(b + 1), p, q),
             rejects_down=not certify(*unpack_positive(b - 1), p, q))


# ── half 2: served values, one row per consumer ──────────────────────────
def site_rows():
    from srmech.math import rational as R
    from srmech.math import laplacian as L
    from srmech.physics.qm import gauge, bell, sm, potentials
    from srmech.signal_processing.closed_form_ops import wavelet, psk_qam
    from srmech.biology import coupling

    from srmech.math.laplacian import elementwise_sqrt, elementwise_hypot
    from srmech.physics.qm import quaternion

    step("site.rational_sqrt_2",
         lambda: dict(q=qpair(R.sqrt(2.0)), f=bits(R.sqrt(2.0))))
    step("site.rational_sqrt_3",
         lambda: dict(q=qpair(R.sqrt(3.0)), f=bits(R.sqrt(3.0))))
    step("site.rational_sqrt_exact_2p53p1",
         lambda: dict(q=qpair(R.sqrt(2 ** 53 + 1))))
    step("site.rational_sqrt_prec200",
         lambda: dict(q=qpair(R.sqrt(2.0, precision=200))))
    step("site.rational_hypot_1_1",
         lambda: dict(q=qpair(R.hypot(1.0, 1.0)), f=bits(R.hypot(1.0, 1.0))))
    step("site.rational_hypot_3_4", lambda: dict(q=qpair(R.hypot(3.0, 4.0))))
    step("site.rational_hypot_tiny", lambda: dict(q=qpair(R.hypot(1e-17, 0.0))))

    # CF-012 / CF-014 — gauge
    step("site.CF012_gauge_lambda8", lambda: _lambda8(gauge))
    step("site.CF014_gauge_f458", lambda: _f458(gauge))

    # CF-016 / CF-017 — bell
    step("site.CF017_tsirelson", lambda: dict(v=bits(bell.TSIRELSON_BOUND)))
    step("site.CF016_chsh_operator_norm",
         lambda: dict(v=bits(bell.chsh_operator_norm())))
    step("site.CF016_chsh_operator",
         lambda: dict(v=[bits(z) for z in _flat(bell.chsh_operator())][:16]))

    # CF-018 — sm
    step("site.CF018_sm_fermion_mass",
         lambda: dict(v=bits(sm.fermion_mass_from_yukawa(0.0102, 246.21965))))
    step("site.CF018_sm_higgs_vev",
         lambda: dict(v=bits(sm.higgs_vev(15129.0, 0.129))))

    # CF-019 — potentials
    step("site.CF019_ladder", lambda: _ladder(potentials))

    # CF-021 — wavelet
    step("site.CF021_wavelet", lambda: dict(
        v=[bits(z) for z in _flat(wavelet.op(
            [1.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0, 34.0], levels=2))][:8]))

    # CF-023 / CF-025 / CF-027 — laplacian
    ed = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    step("site.CF023_normalized_laplacian", lambda: dict(
        v=[bits(z) for z in _flat(L.normalized_laplacian(4, ed))][:16]))
    step("site.CF025_mass_normalized_laplacian", lambda: dict(
        v=[bits(z) for z in _flat(L.mass_normalized_laplacian(
            4, ed, None, [2.0, 3.0, 5.0, 7.0]))][:16]))
    step("site.CF027_fiedler_sparse", lambda: dict(
        v=[bits(z) for z in _flat(L.fiedler_sparse(
            6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 3)]))][:6]))

    # CF-030 — coupling (the 1/√n constant mode)
    step("site.CF030_coupling_kext", lambda: dict(v=_coupling_probe(coupling)))

    # CF-031 — psk_qam: the raise must survive on every shipped M
    step("site.CF031_psk_qam_M", lambda: _qam_sweep(psk_qam))

    # ripple-only consumers
    step("site.ripple_jacobi_eigvals_3x3", lambda: dict(
        v=[bits(z) for z in L.jacobi_eigvals(L.Mat.from_rows(
            [[2.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]]))]))
    step("site.ripple_jacobi_eigvals_5x5", lambda: dict(
        v=[bits(z) for z in L.jacobi_eigvals(L.Mat.from_rows(
            [[4.0, 1.0, 0.0, 0.0, 1.0],
             [1.0, 5.0, 1.0, 0.0, 0.0],
             [0.0, 1.0, 6.0, 1.0, 0.0],
             [0.0, 0.0, 1.0, 7.0, 1.0],
             [1.0, 0.0, 0.0, 1.0, 8.0]]))]))
    step("site.ripple_mat_svd_2x2", lambda: dict(
        v=[bits(z) for z in L.mat_svd(
            L.Mat.from_rows([[3.0, 1.0], [0.0, 2.0]]))[1]]))
    step("site.ripple_mat_norm", lambda: dict(
        v=bits(L.mat_norm(L.Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])))))
    step("site.ripple_elementwise_sqrt", lambda: dict(
        v=[bits(z) for z in elementwise_sqrt([2.0, 3.0, 5.0, 7.0])]))
    step("site.ripple_elementwise_hypot", lambda: dict(
        v=[bits(z) for z in elementwise_hypot([1.0, 3.0], [1.0, 4.0])]))
    step("site.ripple_quaternion_log", lambda: dict(
        v=[bits(z) for z in _flat(quaternion.quaternion_log((1.0, 1.0, 1.0, 1.0)))]))


def _lambda8(gauge):
    l8 = gauge.su3_gell_mann_matrices()[7]
    return dict(d00=bits(l8[0, 0].real), d22=bits(l8[2, 2].real))


def _f458(gauge):
    f = gauge.su3_structure_constants()
    return dict(f347=bits(f[3][4][7]), f567=bits(f[5][6][7]))


def _ladder(potentials):
    a, _ad = potentials.harmonic_oscillator_ladder(n_dim=5)
    return dict(r=[bits(a[i, i + 1].real) for i in range(4)])


def _qam_sweep(psk_qam):
    """CF-031: the square-QAM raise must survive on EVERY shipped ``M``.

    Squares must map; non-squares must raise ``ValueError``.  Both halves are
    recorded, because a rewrite that stops raising and one that stops mapping
    fail the same way in a count-only summary.
    """
    ok, raised, other, pts = [], [], [], {}
    for M in (4, 16, 64, 256, 1024, 4096, 8, 32, 2, 3, 5, 12, 1023):
        try:
            got = psk_qam.op(list(range(min(M, 4))), modulation="qam", M=M,
                             demodulate=False)
            ok.append(M)
            pts[str(M)] = [bits(z.real) for z in got[:2]]
        except ValueError:
            raised.append(M)
        except Exception as exc:                   # noqa: BLE001
            other.append(f"{M}:{type(exc).__name__}")
    return dict(accepted=ok, raised=raised, other=other, points=pts)


def _flat(obj):
    """Flatten a Mat / nested list / Vec into a flat list of floats."""
    if hasattr(obj, "to_rows"):
        obj = obj.to_rows()
    if hasattr(obj, "tolist"):
        obj = obj.tolist()
    out = []
    stack = [obj]
    while stack:
        cur = stack.pop(0)
        if isinstance(cur, (list, tuple)):
            stack = list(cur) + stack
        elif isinstance(cur, complex):
            out.append(cur.real)
        else:
            out.append(float(cur))
    return out


def _coupling_probe(coupling):
    """CF-030's 1/√n constant mode, reached through the public sparse entry."""
    res = coupling.resonant_spectrum_sparse(
        [(0, 1), (1, 2), (2, 3), (3, 0)], None, k=2, n=4)
    ten = res.get("tensions") or res.get("eigen_tensions") or []
    return dict(keys=sorted(res.keys()),
                tensions=[bits(z) for z in _flat(ten)][:8])


def main() -> int:
    import srmech
    from srmech import _native
    emit("cell", version=srmech.__version__, has_native=_native.HAS_NATIVE,
         native_abi=getattr(_native, "NATIVE_ABI_VERSION", None),
         expected_abi=getattr(_native, "EXPECTED_ABI_VERSION", None),
         q61=_native.has_native_trans_q61())
    defect_rows()
    try:
        site_rows()
    except Exception as exc:                       # a probe that cannot run says so
        emit("site.ERROR", exc=f"{type(exc).__name__}: {exc}")
    for row in ROWS:
        print(json.dumps(row, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
