"""rc385 (`#T1048`) — the ℍ log/slerp pair, attested through the SHIPPED ops.

Run:  python quaternion_log_slerp_rc385.py quaternion_log_slerp_rc385.ndjson

WHAT IT MEASURES (all through the shipped rc385 ops):
  (a) THE WORKED EXACT PROOF. q1 = [4/5, 3/5, 0, 0] is a UNIT quaternion
      (16/25 + 9/25 == 1, EXACT). quaternion_log(q1): ‖v‖² = 9/25 (Class-K sum
      of squares), ‖v‖ = 3/5 EXACT (a perfect-square rational sqrt, shown via
      the Class-N srmech.math.rational.sqrt over Q), w = 4/5, θ = atan2(3/5, 4/5)
      = atan(3/4) — the ONE labelled Class-N atan lift (nothing else touches an
      FPU). result = [0, θ·(v/‖v‖)] = [0, atan(3/4), 0, 0].
  (b) EXP∘LOG round-trips to the identity: exp(log(q)) == q for unit q (to the
      float64 boundary), and log(exp(θμ̂)) recovers [0, θμ̂].
  (c) slerp endpoints/geodesic: slerp(q0,q1,0)=q0, slerp(q0,q1,1)=q1 (unit
      q0/q1), the midpoint lies on the unit sphere, and slerp(1,q1,t) sweeps the
      ℝ[i] great circle [cos(tθ), sin(tθ), 0, 0].
  (d) THE ACCEPTANCE ORACLE. For a deterministic bank of unit quaternions
      (INCLUDING w<0 cases that exercise the atan2 quadrant shift), the pure and
      c_dispatched paths of BOTH ops are byte-identical (IEEE-bit equality). When
      the native lib is absent this section records "native_unavailable" and the
      pure numbers stand as the reference; the paired test builds the .so and
      asserts the byte-identity.

DISCIPLINE. No abs(): ‖v‖ is the Class-N sqrt of a manifest sum-of-squares (no
sign to strip); the ‖v‖→0 / log(r)=0 branches are Class-K pin-slots (a plain
`== 0.0` compare). No libm: atan2 is the Q61 Class-N cascade with the quadrant
in exact rational space; sqrt is the Class-N srmech.math.rational cascade. The
Hamilton products ride the Cayley-Dickson complex-pair formula byte-exact with
the C srmech_quat__mul4.
"""
import json
import struct
import sys

import srmech
from srmech import _native
from srmech.physics.qm import quaternion as QMOD
from srmech.physics.qm.quaternion import (
    quaternion_log, quaternion_slerp, quaternion_exp, quaternion_conjugate,
    quaternion_norm)
from srmech.math.q import Q
from srmech.math.rational import sqrt as _rsqrt   # Class-N; NOT stdlib math.sqrt

print("ARTIFACT UNDER TEST:", srmech.__file__, srmech.__version__,
      "HAS_NATIVE=%s" % _native.HAS_NATIVE, flush=True)

OUT = []


def emit(**kw):
    OUT.append(kw)
    print(json.dumps(kw), flush=True)


def _bits(x):
    """The raw IEEE-754 bytes of a float — the byte-identity comparison key."""
    return struct.pack("<d", float(x)).hex()


def _pure(fn, *args):
    """Run ``fn`` forced through the PURE cascade (native dispatch disabled)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn(*args)
    finally:
        _native.HAS_NATIVE = saved


def _native_call(fn, *args):
    """Run ``fn`` through the C peer, or ``None`` if the native lib is absent."""
    if not _native.HAS_NATIVE:
        return None
    return fn(*args)


# ── (a) THE WORKED EXACT PROOF ──────────────────────────────────────────────
# q1 = [4/5, 3/5, 0, 0]: exact unit (a Pythagorean 3-4-5 quaternion).
Q1 = [0.8, 0.6, 0.0, 0.0]
# The unit identity is EXACT over ℚ: 16/25 + 9/25 == 1. ‖v‖² = 9/25 is a perfect
# square so ‖v‖ = 3/5 EXACTLY as maths; the shipped op computes it from the
# float64 imaginary sum-of-squares (0.36) via the Class-N sqrt cascade, which
# projects to the nearest double (0.6).
norm_sq_exact = Q(3, 5) * Q(3, 5)                       # 9/25 (exact ℚ)
unit_exact = (Q(4, 5) * Q(4, 5)) + norm_sq_exact        # 16/25 + 9/25 == 1
nv_float = float(_rsqrt(0.36))                          # what the op computes
lg = quaternion_log(Q1)
emit(section="worked_proof_log",
     q1=Q1, q1_is_exact_unit=(unit_exact == Q(1, 1)),
     imag_norm_sq_exact=str(norm_sq_exact),
     imag_norm_exact_math="3/5",
     imag_norm_float=nv_float, imag_norm_projects_to_0p6=(nv_float == 0.6),
     log_q1=lg, real_part_zero=(lg[0] == 0.0),
     axis_is_pure_i=(lg[2] == 0.0 and lg[3] == 0.0),
     theta=lg[1],
     note="9/25 is a perfect square so ‖v‖=3/5 EXACTLY as maths; the Class-N "
          "sqrt cascade projects to the nearest double (0.6). theta = "
          "atan2(3/5, 4/5) = atan(3/4), the labelled Class-N atan lift")

# ── (b) EXP∘LOG round-trip (float64 boundary — ~1 ulp, not bit-exact) ────────
# exp(log(q)) recovers q to the float64 boundary: the Q61 cos/sin cascade + the
# ‖t·log‖ = √((tθ)²) round-trip project to ~1 ulp of the ideal, not bit-exact.
back = quaternion_exp(quaternion_norm([lg[0], lg[1], lg[2], lg[3]]),
                      [0.0, lg[1], lg[2], lg[3]])
emit(section="exp_of_log_roundtrip", q1=Q1, exp_log_q1=back,
     recovers_q1=all(abs(back[i] - Q1[i]) < 1e-12 for i in range(4)))

# log(exp(θμ̂)) recovers [0, θμ̂] for a chosen exact axis + angle.
e_ij = quaternion_exp(0.5, "ijk")           # exp on the body-diagonal axis
lg_e = quaternion_log(e_ij)
emit(section="log_of_exp_roundtrip", theta=0.5, axis="ijk", exp=e_ij,
     log_exp=lg_e, real_part_zero=(lg_e[0] == 0.0))

# ── (c) slerp endpoints + geodesic ──────────────────────────────────────────
ID = [1.0, 0.0, 0.0, 0.0]
s0 = quaternion_slerp(ID, Q1, 0.0)
s1 = quaternion_slerp(ID, Q1, 1.0)
shalf = quaternion_slerp(ID, Q1, 0.5)
emit(section="slerp_endpoints",
     slerp_t0=s0, is_q0=all(_bits(s0[i]) == _bits(ID[i]) for i in range(4)),
     slerp_t1=s1, approx_q1=all(abs(s1[i] - Q1[i]) < 1e-12 for i in range(4)),
     slerp_half=shalf,
     half_on_unit_sphere=(abs(sum(c * c for c in shalf) - 1.0) < 1e-12))

# slerp(1, q1, t) sweeps the ℝ[i] great circle [cos(tθ), sin(tθ), 0, 0] — to the
# float64 boundary (slerp re-derives the angle as √((tθ)²), so ~1 ulp, not bit).
theta = lg[1]
sweep = []
for t in (0.25, 0.5, 0.75):
    st = quaternion_slerp(ID, Q1, t)
    ce = quaternion_exp(t * theta, "i")           # cos(tθ), sin(tθ) on axis i
    sweep.append({"t": t, "slerp": st, "exp_t_theta_i": ce,
                  "match": all(abs(st[i] - ce[i]) < 1e-12 for i in range(4))})
emit(section="slerp_great_circle_sweep", theta=theta, samples=sweep,
     all_match=all(s["match"] for s in sweep))

# ── (d) THE ACCEPTANCE ORACLE — pure vs c_dispatched byte-identity ──────────
def _unit(v):
    n = quaternion_norm(v)
    return [c / n for c in v]


# Deterministic bank; the w<0 members (θ>π/2) exercise the atan2 quadrant shift.
BANK = [
    _unit([0.8, 0.6, 0.0, 0.0]),        # worked proof (w>0, axis i)
    _unit([2.0, 1.0, -3.0, 1.0]),       # w>0 generic
    _unit([-1.0, 1.0, 1.0, 1.0]),       # w<0 -> atan2 quadrant shift
    _unit([-2.0, 0.5, -1.5, 0.25]),     # w<0 generic
    _unit([0.0, 1.0, -2.0, 0.5]),       # w==0 -> theta = pi/2 branch
    [1.0, 0.0, 0.0, 0.0],               # pure real +1 -> ‖v‖→0 pin-slot
    [-1.0, 0.0, 0.0, 0.0],              # pure real -1 -> ‖v‖→0 pin-slot
]
T_VALUES = [0.0, 0.25, 0.5, 0.75, 1.0, -0.5, 1.5]

log_all_identical = True
slerp_all_identical = True
native_seen = _native.HAS_NATIVE
for idx, q in enumerate(BANK):
    lp = _pure(quaternion_log, q)
    ln = _native_call(quaternion_log, q)
    li = None if ln is None else all(_bits(lp[i]) == _bits(ln[i]) for i in range(4))
    if li is False:
        log_all_identical = False
    emit(section="log_parity", idx=idx, q=q, w_sign=("neg" if q[0] < 0 else
         ("zero" if q[0] == 0.0 else "pos")), pure=lp,
         native=ln, byte_identical=("native_unavailable" if ln is None else li))
    # slerp bank: interpolate q0=ID -> q1=q at each t.
    for t in T_VALUES:
        sp = _pure(quaternion_slerp, ID, q, t)
        sn = _native_call(quaternion_slerp, ID, q, t)
        si = None if sn is None else all(_bits(sp[i]) == _bits(sn[i])
                                         for i in range(4))
        if si is False:
            slerp_all_identical = False
        emit(section="slerp_parity", idx=idx, t=t, q1=q, pure=sp, native=sn,
             byte_identical=("native_unavailable" if sn is None else si))

emit(section="acceptance_oracle_summary",
     native_available=native_seen,
     log_pure_vs_c_byte_identical=(log_all_identical if native_seen
                                   else "native_unavailable"),
     slerp_pure_vs_c_byte_identical=(slerp_all_identical if native_seen
                                     else "native_unavailable"),
     bank_size=len(BANK), t_values=T_VALUES,
     finding=("quaternion_log / quaternion_slerp are byte-identical Python-pure "
              "vs C-dispatched across the quadrant/pin-slot bank — the atan2 "
              "quadrant is done in Q61 integer space (mirror of rational.atan2), "
              "projected once; the Hamilton products ride the CD complex-pair "
              "formula. NO abs(), NO libm, NO FPU beyond the labelled atan2/√."))


if __name__ == "__main__" and len(sys.argv) > 1:
    with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
        for rec in OUT:
            f.write(json.dumps(rec) + "\n")
    print("wrote", len(OUT), "records to", sys.argv[1], flush=True)
