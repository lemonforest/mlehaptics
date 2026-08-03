"""rc384 (`#T957` / `#T959`) — the 𝕆 frame-committed coherence read, attested
through the SHIPPED rc384 ops. Exact-ℚ where the object is exact; float only for
the eigensolver spectra.

Run:  python octonion_frame_read_rc384.py octonion_frame_read_rc384.ndjson

WHY THIS EXISTS (`#T959`). §3.41's gauge-deviation numbers (0.188 / 0.155) + the
ℍ 3.3e-15 gauge-invariance were "asserted, not attested" — their generating
scripts (wf_c08557de / wf_ee97aaa2) never landed in the tree. This script CLOSES
that breach by reproducing the load-bearing FINDING through shipped ops, and adds
a stronger EXACT-ℚ seam census. It is BOTH the #T959 attestation AND the rc384
differential gate (mirrored in tests/test_octonion_frame_read_rc384.py).

WHAT IT MEASURES (all through shipped ops):
  (a) the ℍ base subalgebra is FULLY coherent (0/64) and ALL 168 of 𝕆's
      non-closures CROSS the doubling seam (0 non-seam) — via srmech.cascade.associator;
  (b) srmech.cascade.octonion_frame_read is frame-free UNDER the S³ fiber (base
      unchanged under a unit-λ right-multiply of both halves, changed under a
      non-fiber move) + the exact four-sphere identity + the degenerate branch;
  (c) srmech.math.laplacian.octonion_laplacian's spectrum is NOT gauge-invariant
      at 𝕆 (~0.06–0.49) versus srmech.math.laplacian.quaternion_laplacian's
      Sp(1)-invariance at ℍ (~1e-15) — the CEILING, now from shipped ops.

⚠️ HONEST FINDING (even failures illuminate). The frame-committed SPECTRAL read
does NOT recover a clean invariant at 𝕆 — the associator leak defeats
gauge-invariance in all imaginary directions, not just ℍℓ. So the coherence that
survives is the ℍ-valued ELEMENT Hopf base (octonion_frame_read), NOT a
gauge-invariant 𝕆 spectrum (octonion_laplacian). No abs() anywhere — the
base_R sign is a Class-K pin-slot difference; spectral deviation is a Euclidean
norm (sum of squares → sqrt), never an ALU magnitude.
"""
import json
import sys

import srmech
from srmech import _native
from srmech.cascade import octonion_frame_read, associator, cd_basis
from srmech.cascade.cayley_dickson import cd_mult, cd_norm_sq
from srmech.math.q import Q
from srmech.math.laplacian import (octonion_laplacian, quaternion_laplacian,
                                   mat_hermitian_eigendecompose)
from srmech.physics.qm.octonion import (octonion_norm, octonion_conjugate,
                                        octonion_left_mult)
from srmech.physics.qm.quaternion import (quaternion_norm, quaternion_conjugate,
                                          quaternion_left_mult)
from srmech.math.rational import sqrt as _rsqrt   # Class-N; NOT stdlib math.sqrt

print("ARTIFACT UNDER TEST:", srmech.__file__, srmech.__version__,
      "HAS_NATIVE=%s" % _native.HAS_NATIVE, flush=True)

OUT = []


def emit(**kw):
    OUT.append(kw)
    print(json.dumps(kw), flush=True)


# ── (a) ℍ base coherence + 𝕆 seam-confinement — the EXACT-ℚ census ──────
def _e(i):
    return cd_basis(8, i)


def _half(i):
    return 0 if i < 4 else 1   # ℍ (0) vs ℍℓ seam (1)


HBASE = (0, 1, 2, 3)
h_nonzero = sum(
    1 for i in HBASE for j in HBASE for k in HBASE
    if any(v != 0 for v in associator(_e(i), _e(j), _e(k))))
emit(section="H_subalgebra_coherence", h_base_indices=list(HBASE),
     associator_nonzero=h_nonzero, of=len(HBASE) ** 3,
     coherent=(h_nonzero == 0))

o_nonzero = o_seam = o_nonseam = 0
for i in range(8):
    for j in range(8):
        for k in range(8):
            if any(v != 0 for v in associator(_e(i), _e(j), _e(k))):
                o_nonzero += 1
                if _half(i) + _half(j) + _half(k) > 0:
                    o_seam += 1
                else:
                    o_nonseam += 1
emit(section="O_seam_confinement", associator_nonzero=o_nonzero, of=512,
     seam_crossing=o_seam, non_seam=o_nonseam,
     all_seam_confined=(o_nonzero == o_seam and o_nonseam == 0))


# ── (b) octonion_frame_read: frame-free UNDER the fiber, non-tautological ─
X = [1, 2, -3, 1, 2, -1, 1, 4]
r = octonion_frame_read(X)
sphere_lhs = cd_norm_sq(r["base_H"]) + r["base_R"] * r["base_R"]
sphere_rhs = r["norm_sq"] * r["norm_sq"]
emit(section="frame_read_sphere_identity", x=X,
     base_H=[str(q) for q in r["base_H"]], base_R=str(r["base_R"]),
     norm_sq=str(r["norm_sq"]),
     sphere_holds=(sphere_lhs == sphere_rhs))

# UNIT quaternion λ = (1/2)(1,1,1,1), |λ|² = 1 (a nontrivial Hurwitz unit).
LAM = (Q(1, 2), Q(1, 2), Q(1, 2), Q(1, 2))
lam_nsq = cd_norm_sq(LAM)
q0f, q1f = cd_mult(r["q0"], LAM), cd_mult(r["q1"], LAM)
rf = octonion_frame_read(list(q0f) + list(q1f))
# NON-fiber move: right-multiply ONLY q0 (breaks the diagonal fiber).
q0n = cd_mult(r["q0"], LAM)
rn = octonion_frame_read(list(q0n) + list(r["q1"]))
# projective base ratio: base_H[i]*base_R' == base_H'[i]*base_R  (cross-mult)
proj_same = all(rf["base_H"][i] * r["base_R"] == r["base_H"][i] * rf["base_R"]
                for i in range(4))
proj_diff = not all(rn["base_H"][i] * r["base_R"] == r["base_H"][i] * rn["base_R"]
                    for i in range(4))
emit(section="frame_read_fiber_invariance",
     unit_lambda="(1/2)(1,1,1,1)", lambda_norm_sq=str(lam_nsq),
     base_H_unchanged_under_unit_fiber=(rf["base_H"] == r["base_H"]),
     base_R_unchanged_under_unit_fiber=(rf["base_R"] == r["base_R"]),
     norm_sq_unchanged=(rf["norm_sq"] == r["norm_sq"]),
     writhe_changed_under_fiber=(rf["writhe"] != r["writhe"]),
     projective_base_invariant_under_fiber=proj_same,
     base_changed_under_nonfiber_move=proj_diff)

# degenerate branch: q1 == 0 → point at infinity (base_R = +norm_sq, writhe None)
rd = octonion_frame_read([3, 1, 0, 2, 0, 0, 0, 0])
emit(section="frame_read_degenerate", q1_zero=True,
     writhe_none=(rd["writhe"] is None),
     canonical_affine_none=(rd["canonical_affine"] is None),
     base_R_eq_norm_sq=(rd["base_R"] == rd["norm_sq"]))


# ── (c) the CEILING: 𝕆 gauge-dependence vs ℍ Sp(1)-invariance ────────────
def _spectrum(mat):
    ev, _ = mat_hermitian_eigendecompose(mat)
    return sorted(complex(ev[i, 0]).real for i in range(ev.n_rows))


def _spec_dev(s1, s2):
    # Euclidean norm of the sorted-spectrum difference. Class-N sqrt of a
    # sum of squares — NO abs() (a magnitude would be the ALU shortcut this
    # discipline forbids).
    ss = sum((a - b) * (a - b) for a, b in zip(s1, s2))
    return float(_rsqrt(ss))


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


# deterministic named gains/gauges (no draw)
GRAPHS = {
    "triangle": ([(0, 1), (1, 2), (2, 0)], 3),
    "path3": ([(0, 1), (1, 2)], 3),
    "4cycle": ([(0, 1), (1, 2), (2, 3), (3, 0)], 4),
}
OCT_GAINS = [
    [1, 2, -1, 3, 0, -2, 1, 1], [2, 0, 1, -1, 1, 1, 0, -1],
    [-1, 1, 2, 1, 0, 1, -1, 1], [1, -1, 0, 2, 1, 0, 1, -1],
]
OCT_GAUGE = [
    [1, 1, 0, 1, 0, 1, 1, 0], [0, 1, 1, 0, 1, 0, 1, 1],
    [1, 0, 1, 1, 0, 1, 0, 1], [1, 1, 1, 0, 1, 0, 0, 1],
]
QUAT_GAINS = [[1, 2, -1, 3], [2, 0, 1, -1], [-1, 1, 2, 1], [1, -1, 0, 2]]
QUAT_GAUGE = [[1, 1, 0, 1], [0, 1, 1, 0], [1, 0, 1, 1], [1, 1, 1, 0]]

o_devs, h_devs = [], []
for name, (edges, n) in GRAPHS.items():
    # 𝕆 leg
    g8 = [_unit8(OCT_GAINS[k % 4]) for k in range(len(edges))]
    s8 = [_unit8(OCT_GAUGE[k % 4]) for k in range(n)]
    gg8 = [_o(_o(s8[u], g), octonion_conjugate(s8[v]))
           for (u, v), g in zip(edges, g8)]
    dev_o = _spec_dev(_spectrum(octonion_laplacian(n, edges, gains=g8)),
                      _spectrum(octonion_laplacian(n, edges, gains=gg8)))
    o_devs.append(dev_o)
    emit(section="laplacian_gauge_O", graph=name, n=n, gauge_deviation=dev_o,
         gauge_invariant=(dev_o < 1e-9))
    # ℍ control (shipped quaternion_laplacian; dedupe every 4th)
    g4 = [_unit4(QUAT_GAINS[k % 4]) for k in range(len(edges))]
    s4 = [_unit4(QUAT_GAUGE[k % 4]) for k in range(n)]
    gg4 = [_q(_q(s4[u], g), quaternion_conjugate(s4[v]))
           for (u, v), g in zip(edges, g4)]
    dev_h = _spec_dev(_spectrum(quaternion_laplacian(n, edges, gains=g4))[::4],
                      _spectrum(quaternion_laplacian(n, edges, gains=gg4))[::4])
    h_devs.append(dev_h)
    emit(section="laplacian_gauge_H_control", graph=name, n=n,
         gauge_deviation=dev_h, gauge_invariant=(dev_h < 1e-9))

emit(section="ceiling",
     O_gauge_dev_min=min(o_devs), O_gauge_dev_max=max(o_devs),
     H_gauge_dev_max=max(h_devs),
     O_spectrum_gauge_invariant=all(d < 1e-9 for d in o_devs),
     H_spectrum_gauge_invariant=all(d < 1e-9 for d in h_devs),
     finding=("the frame-committed SPECTRAL read does NOT recover a "
              "gauge-invariant 𝕆 spectrum (associator leak, ~0.1); the "
              "coherence that survives is the ℍ-valued ELEMENT Hopf base "
              "of octonion_frame_read, frame-free UNDER the S³ fiber"))


if __name__ == "__main__" and len(sys.argv) > 1:
    with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
        for rec in OUT:
            f.write(json.dumps(rec) + "\n")
    print("wrote", len(OUT), "records to", sys.argv[1], flush=True)
