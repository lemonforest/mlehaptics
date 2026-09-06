"""rc468 (`#T1188`) — the EXECUTED exact-round-trip proof, run before and after
the op consolidation so "the exact routes stay exact" is a measurement rather
than a hope.

    python3 docs/srmech/notes/_rc468_exact_roundtrip_f1360.py

MEASURED: 70/70 before the removal (on `hypercomplex_turn`) and 70/70 after
(on `hypercomplex_exp(k_axes=..., turn=(k, n))`), in the numpy-absent WSL2
cell, on both the native and the pure library projections.

The Cayley-Dickson product below is written HERE rather than imported from
`srmech.cascade.cd_mult`, deliberately: a proof that the shipped ops are exact
must not be conducted with the shipped multiplication, or a shared defect
would cancel out of both sides.

Every row asserts the N-th power of the twiddle is the EXACT identity with
``==`` (never a tolerance) and that the norm is exactly one. The one negative
control asserts the FLOAT route satisfies NEITHER, so the file cannot go
vacuous by the two routes converging.
"""
from __future__ import annotations

import os
import sys

# Run me from anywhere: the package root is two levels up from docs/srmech/notes.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, "python"))

from srmech.math.q import Q
from srmech.math import qalg as _qalg
from srmech.math.qalg import Qalg, cos_sin_2pi_k_over_n
from srmech.physics.qm.quaternion import quaternion_twiddle
from srmech.physics.qm.octonion import octonion_twiddle


def _one_of(v):
    return v.one() if isinstance(v, Qalg) else Q(1, 1)


def _zero_of(v):
    return (v - v) if isinstance(v, Qalg) else Q(0, 1)


def _mult(a, b):
    """Exact Cayley-Dickson product over a list of Q / Qalg (dim 1, 2, 4, 8)."""
    n = len(a)
    if n == 1:
        return [a[0] * b[0]]
    h = n // 2
    a1, a2, b1, b2 = a[:h], a[h:], b[:h], b[h:]
    # (a1, a2)(b1, b2) = (a1 b1 - conj(b2) a2,  b2 a1 + a2 conj(b1)).
    # The conjugations are Class-K pin-slot sign flips on the imaginary
    # coordinates, never an abs().
    conj_b1 = [b1[0]] + [-x for x in b1[1:]]
    conj_b2 = [b2[0]] + [-x for x in b2[1:]]
    lo = [x - y for x, y in zip(_mult(a1, b1), _mult(conj_b2, a2))]
    hi = [x + y for x, y in zip(_mult(b2, a1), _mult(a2, conj_b1))]
    return lo + hi


def _power(w, n):
    acc = [_one_of(w[0])] + [_zero_of(w[0]) for _ in w[1:]]
    for _ in range(n):
        acc = _mult(acc, w)
    return acc


def _is_identity(w):
    return w[0] == _one_of(w[0]) and all(c == _zero_of(w[0]) for c in w[1:])


def _norm_sq(w):
    acc = w[0] * w[0]
    for c in w[1:]:
        acc = acc + c * c
    return acc


def main() -> int:
    rows = []

    # ── the scalar constructor: c*c + s*s == 1 and (c + s*i)**n == 1 ────────
    for n in (3, 5, 7, 8, 12, 16, 64):
        c, s = cos_sin_2pi_k_over_n(n)
        assert c * c + s * s == _one_of(c), ("pythagoras", n)
        rows.append(("cos_sin_2pi_k_over_n", n, "c*c+s*s==1", True))

    # (c + s*i)**n == 1, with i = zeta_N**(N/4)
    for n in (3, 5, 7, 8, 12, 16):
        index = 4 * n // _qalg._gcd(n, 4)
        cq, sq = _qalg._cos_sin_in_field(index, n, 1)
        omega = Qalg.alpha(_qalg._cyclotomic_m(index))
        i = omega ** (index // 4)
        w = cq + sq * i
        assert w ** n == cq.one(), ("closure", n)
        rows.append(("cos_sin_2pi_k_over_n", n, "(c+s*i)**n==1", True))

    # ── the quaternion twiddle, every named axis ────────────────────────────
    for axis in ("i", "j", "k", "ijk"):
        for n in (3, 4, 5, 8, 12, 16):
            w = quaternion_twiddle(1, 1, n, mu=axis, sigma=1, exact=True)
            assert _is_identity(_power(w, n)), ("qtw", axis, n, w)
            assert _norm_sq(w) == _one_of(w[0]), ("qtw-norm", axis, n)
            rows.append(("quaternion_twiddle", f"{axis}/{n}", "W**N==1", True))

    # ── the octonion twiddle, every named axis incl. 1/sqrt(7) ─────────────
    for axis in ("i", "e4", "e7", "ijk", "diagonal"):
        for n in (3, 4, 7, 8):
            w = octonion_twiddle(1, 1, n, mu=axis, sigma=1, exact=True)
            assert _is_identity(_power(w, n)), ("otw", axis, n, w)
            assert _norm_sq(w) == _one_of(w[0]), ("otw-norm", axis, n)
            rows.append(("octonion_twiddle", f"{axis}/{n}", "W**N==1", True))

    # ── the equal-weight rotor, all three rungs ─────────────────────────────
    # rc468 (`#T1188`): this surface was `hypercomplex_turn(k, n, k_axes)` when
    # the BEFORE run was taken, and is `hypercomplex_exp(k_axes=..., turn=)`
    # after the fold. Both runs were 70/70. There is deliberately NO try/except
    # here selecting between them: a fallback to a removed op is exactly the
    # legacy path this rc refuses, and the removed spelling cannot come back.
    from srmech.cascade import hypercomplex_exp as _rotor

    def rotor(k, n, k_axes):
        return list(_rotor(k_axes=k_axes, turn=(k, n)))

    surface = "hypercomplex_exp(k_axes=..., turn=(k, n))"

    for k_axes, ns in ((1, (3, 4, 8, 12)), (3, (3, 4, 8, 12)), (7, (4, 7, 8))):
        for n in ns:
            w = rotor(1, n, k_axes)
            assert _is_identity(_power(w, n)), ("rotor", k_axes, n, w)
            assert _norm_sq(w) == _one_of(w[0]), ("rotor-norm", k_axes, n)
            rows.append((surface, f"k_axes={k_axes}/n={n}", "W**N==1", True))

    # the measured all-rational third turn at k_axes = 3
    assert rotor(1, 3, 3)[:4] == [Q(-1, 2), Q(1, 2), Q(1, 2), Q(1, 2)]
    rows.append((surface, "1/3 @ k_axes=3", "binary-tetrahedral rational", True))

    # ── NEGATIVE CONTROL: the float route satisfies NEITHER ────────────────
    for n in (3, 5, 7, 8, 12):
        w = [Q.from_float(c) for c in quaternion_twiddle(1, 1, n, sigma=1)]
        assert _norm_sq(w) != Q(1, 1), ("float-norm", n)
        assert not _is_identity(_power(w, n)), ("float-closure", n)
    rows.append(("quaternion_twiddle (float route)", "3..12",
                 "NEITHER identity holds", True))

    for label, arg, claim, ok in rows:
        print(f"{'OK ' if ok else 'FAIL'} {label:44s} {str(arg):22s} {claim}")
    print(f"\n{len(rows)} strict-zero rows, all EXECUTED. surface = {surface}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
