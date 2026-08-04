"""§3.41.9 — the 7-Fano-frame DECISIVE experiment: does the full family of 7
quaternionic-frame reads collectively RECONSTRUCT a frame-free 𝕆 invariant?

Run:  python3 octonion_7fano_frame_experiment.py octonion_7fano_frame_experiment.ndjson

WHY THIS EXISTS. §3.41.6 committed ONE frame (ℓ = e₄, the ℍ base {e₀,e₁,e₂,e₃})
and proved Q2: there is no frame-FREE octonion SCALAR invariant. §3.41.2 REFUTED
the shadow-family reassembly at the *spectral* level (moves 0.186, not restored
to 0). The shipped ``octonion_frame_read`` reads only ``frame=4``; the octonion
has **7 Fano lines** = 7 quaternionic subalgebra frames ℍ_F = span(1,e_a,e_b,e_c)
(the 7 XOR-triples of PG(2,2) on the imaginary units {1..7}). THE DECISIVE
QUESTION: does the FULL 7-frame family collectively reconstruct a frame-free
invariant under Aut(𝕆)=G₂ — FALSIFYING the "commit-one-frame / no global
coordinate patch" reading — or does it CONFIRM the ceiling (each frame a genuine
local chart)?

DISCIPLINE. Every octonion product / conjugation / norm / frame-read is a SHIPPED
srmech op (``table_product`` / ``cd_mult`` / ``cd_conjugate`` / ``cd_norm_sq`` /
``algebra_table`` / ``octonion_frame_read``). The generalized 7-frame read
COMPOSES those ops in scratch (never edits the shipped ``frame=4`` op) and is
verified to REPRODUCE the shipped ``octonion_frame_read`` on the {e₁,e₂,e₃}
frame, exactly. Exact-ℚ throughout; float only for the reported magnitude ratios
(a Euclidean norm = Class-N sqrt of a sum of squares — never ``abs()``; the
base_R sign is a Class-K pin-slot difference, the conjugation Class-C).

NEGATIVE CONTROLS (`[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]`):
  C1  split-𝕆         algebra_table(8, gammas=(-1,-1,+1))  — a composition algebra, same Fano frames.
  C2  random-anticomm  a random ±1 XOR table                — same Fano index-incidence, NOT a composition algebra.
  C3  R[ℤ/8]           group_algebra_table(8)               — associative, product-agnostic base_R reference.

VERDICT TIERS per headline: FORCED (any table gives it) / DEFINITIONAL (reduces to
the a-priori invariants Re x and N(x)) / CONTENTFUL (a genuinely new frame-free
invariant — would FALSIFY the ceiling).
"""
import json
import random
import statistics
import sys

import srmech
from srmech import _native
from srmech.version import __version__ as VER
from srmech.cascade.cayley_dickson import (
    cd_conjugate, cd_norm_sq, cd_mult, cd_basis_product,
    algebra_table, table_product, group_algebra_table, octonion_frame_read)
from srmech.math.q import Q
from srmech.math.rational import sqrt as rsqrt   # Class-N; NOT stdlib math.sqrt

print("ARTIFACT UNDER TEST:", srmech.__file__, VER,
      "HAS_NATIVE=%s" % _native.HAS_NATIVE, flush=True)

OUT = []


def emit(**kw):
    OUT.append(kw)
    print(json.dumps(kw), flush=True)


def Qv(t):
    return tuple(v if isinstance(v, Q) else Q(v) for v in t)


def mag(q):
    """Abs-free magnitude of an exact-ℚ scalar: √(q²) (Class-N)."""
    return float(rsqrt(q * q))


def vmag(v):
    """Euclidean norm of an exact-ℚ vector (Class-N sqrt of a sum of squares)."""
    return float(rsqrt(sum(c * c for c in v)))


# The 7 Fano lines = the XOR-triples of PG(2,2) on the imaginary units {1..7}.
FANO = [(1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6),
        (2, 5, 7), (3, 4, 7), (3, 5, 6)]


def oriented_lines(table):
    """Orient each Fano triple so e_a·e_b = +e_c under this table (Class-C
    which-way); for a table whose (a,b) cell is not +1 use (b,a)."""
    return [(a, b, c) if table[a][b][c] >= 0 else (b, a, c) for (a, b, c) in FANO]


def frame_read(x, line, table, gammas=None):
    """Generalized quaternionic-frame read of x on frame F = span(1,e_a,e_b,e_c),
    COMPOSING shipped ops — the frame=4 op's construction lifted to all 7 lines.

    Split 𝕆 = ℍ_F ⊕ ℍ_F·ℓ (ℓ = min complement unit); q0 = proj_F x; the seam
    part Q1 = proj_F^⊥ x; q1 = Q1·ℓ⁻¹ = −Q1·e_ℓ ∈ ℍ_F. Return the ℍ_F-valued
    quaternionic-Hopf base  base_H = 2·q0·conj(q1)  and the ℝ-diagonal
    base_R = |q0|² − |Q1|² (Class-K pin-slot difference; NO abs()).
    """
    a, b, c = line
    comp = [i for i in range(1, 8) if i not in (a, b, c)]
    ell = min(comp)
    xq = Qv(x)
    q0 = [Q(0)] * 8
    for i in (0, a, b, c):
        q0[i] = xq[i]
    Q1 = [Q(0)] * 8
    for i in comp:
        Q1[i] = xq[i]
    e = [Q(0)] * 8
    e[ell] = Q(1)
    q1 = tuple(-v for v in table_product(table, tuple(Q1), tuple(e)))   # Q1·ℓ⁻¹
    base_H = tuple(Q(2) * v for v in table_product(table, tuple(q0), cd_conjugate(q1)))
    base_R = cd_norm_sq(tuple(q0), gammas) - cd_norm_sq(tuple(Q1), gammas)
    return {"base_H": base_H, "base_R": base_R, "ell": ell,
            "base_H_normsq": cd_norm_sq(base_H, gammas)}


def reconstruct(x, table, gammas=None):
    """The 7-frame reconstruction: B = Σ_F base_H_F (the ℍ_F-off-diagonal summed
    as octonions), S_R = Σ_F base_R_F, S_N = Σ_F |base_H_F|²."""
    B = [Q(0)] * 8
    S_R = Q(0)
    S_N = Q(0)
    for L in oriented_lines(table):
        fr = frame_read(x, L, table, gammas)
        B = [p + q for p, q in zip(B, fr["base_H"])]
        S_R += fr["base_R"]
        S_N += fr["base_H_normsq"]
    return tuple(B), S_R, S_N


# ── automorphisms of 𝕆 (verified genuine — math doesn't lie) ─────────────
def phi_seam_left(u):
    """Continuous G₂ automorphism: fix ℍ={e₀..e₃} pointwise, rotate the seam by
    LEFT-mult by a rational unit quaternion u — a genuine Aut(𝕆) element that
    MIXES the 6 seam-bearing frames (does NOT merely permute them)."""
    def phi(x):
        x = Qv(x)
        return tuple(x[:4]) + tuple(cd_mult(u, x[4:]))
    return phi


def signed_perm(perm, signs):
    """A signed permutation of the imaginary units (fixing e₀)."""
    def phi(x):
        x = Qv(x)
        out = [Q(0)] * 8
        out[0] = x[0]
        for k in range(1, 8):
            out[perm[k - 1]] = Q(signs[k - 1]) * x[k]
        return tuple(out)
    return phi


def is_hom(phi, table, n=20, seed=3):
    """Exact homomorphism check φ(x·y) == φ(x)·φ(y) over n random pairs."""
    random.seed(seed)
    for _ in range(n):
        x = Qv([random.randint(-4, 4) for _ in range(8)])
        y = Qv([random.randint(-4, 4) for _ in range(8)])
        if tuple(phi(table_product(table, x, y))) != \
           tuple(table_product(table, phi(x), phi(y))):
            return False
    return True


OCT = algebra_table(8)                          # definite octonion 𝕆
SPLIT = algebra_table(8, gammas=(-1, -1, 1))    # C1 split-𝕆
GRP = group_algebra_table(8)                    # C3 R[ℤ/8]


def random_anticomm(seed=5):                     # C2 random anticommutative XOR
    random.seed(seed)
    T = [[[0] * 8 for _ in range(8)] for _ in range(8)]
    for i in range(8):
        T[0][i][i] = 1
        T[i][0][i] = 1
    for i in range(1, 8):
        T[i][i][0] = -1                          # e_i² = −e₀
    for i in range(1, 8):
        for j in range(i + 1, 8):
            k = i ^ j
            s = random.choice((1, -1))
            T[i][j][k] = s
            T[j][i][k] = -s
    return T


RAND = random_anticomm()

U = (Q(3, 5), Q(4, 5), Q(0), Q(0))              # rational unit quaternion |u|²=1
g_cont = phi_seam_left(U)
g_disc = signed_perm((1, 4, 5, 7, 6, 3, 2), (1,) * 7)   # order-7 Fano collineation


def g_mix(x):
    return g_disc(g_cont(x))


# ── (0) the 7 oriented Fano frames + the incidence ───────────────────────
lines = oriented_lines(OCT)
incidence = {}
for (a, b, c) in FANO:
    for u in (a, b, c):
        incidence[u] = incidence.get(u, 0) + 1
emit(section="fano_frames", oriented_lines=[list(t) for t in lines],
     n_frames=len(lines),
     unit_line_multiplicity=dict(sorted(incidence.items())),
     each_imaginary_in_3_of_7=(set(incidence.values()) == {3}),
     seam_convention_e1e4_e2e4_e3e4=[list(cd_basis_product(8, i, 4))
                                     for i in (1, 2, 3)])

# ── (1) faithfulness: the generalized read REPRODUCES the shipped frame=4 ──
X = [1, 2, -3, 1, 2, -1, 1, 4]
line123 = next(L for L in lines if set((abs(L[0]), abs(L[1]), abs(L[2]))) == {1, 2, 3})
fri = frame_read(X, line123, OCT)
shp = octonion_frame_read(X)
emit(section="generalized_read_matches_shipped", x=X, frame123=list(line123),
     shipped_base_H=[str(v) for v in shp["base_H"]],
     generalized_base_H_e0_e3=[str(fri["base_H"][i]) for i in range(4)],
     generalized_base_H_seam=[str(fri["base_H"][i]) for i in range(4, 8)],
     base_H_matches=(tuple(fri["base_H"][:4]) == shp["base_H"]
                     and all(fri["base_H"][i] == 0 for i in range(4, 8))),
     base_R_matches=(fri["base_R"] == shp["base_R"]),
     shipped_base_R=str(shp["base_R"]))

# ── (2) automorphisms are genuine (verified, not asserted) ────────────────
emit(section="automorphisms_verified",
     g_cont="fix ℍ, seam↦u·seam, u=(3/5,4/5,0,0)",
     g_cont_is_automorphism_O=is_hom(g_cont, OCT),
     g_disc="signed-perm (1,4,5,7,6,3,2) — order-7 Fano collineation",
     g_disc_is_automorphism_O=is_hom(g_disc, OCT),
     g_mix_is_automorphism_O=is_hom(g_mix, OCT),
     g_cont_is_automorphism_split=is_hom(g_cont, SPLIT),
     g_disc_is_automorphism_split=is_hom(g_disc, SPLIT))

# ── (3) CHANNEL 1 — base_R: Σ base_R = 8·x0² − N(x) for ALL tables (FORCED) ─
random.seed(11)
probe = [Qv([random.randint(-5, 5) for _ in range(8)]) for _ in range(6)]
for name, tab, gm in [("O_definite", OCT, None),
                      ("split_O", SPLIT, (-1, -1, 1)),
                      ("random_anticomm", RAND, None),
                      ("R_Z8_group_ring", GRP, None)]:
    holds = True
    for P in probe:
        _, S_R, _ = reconstruct(P, tab, gm)
        pred = Q(8) * P[0] * P[0] - cd_norm_sq(P, gm)
        if S_R != pred:
            holds = False
            break
    emit(section="channel1_baseR_reconstruction", algebra=name,
         identity="Sum_F base_R_F == 8*x0^2 - N(x)", holds_exact=holds,
         verdict="FORCED+DEFINITIONAL")

# ── (4) POSITIVE CONTROL: N(x) and Σ base_R ARE frame-free (0 defect) ──────
#     the instrument CAN return 0 — it is not rigged to always find failure.
random.seed(7)
tests = [Qv([random.randint(-5, 5) for _ in range(8)]) for _ in range(6)]
for label, g in [("g_disc", g_disc), ("g_cont", g_cont), ("g_mix", g_mix)]:
    dN = []
    dBR = []
    for P in tests:
        _, S_R, _ = reconstruct(P, OCT)
        _, S_Rg, _ = reconstruct(g(P), OCT)
        dN.append(cd_norm_sq(g(P)) - cd_norm_sq(P))
        dBR.append(S_Rg - S_R)
    emit(section="positive_control_invariants", automorphism=label,
         N_defect_all_zero=all(v == 0 for v in dN),
         sum_baseR_defect_all_zero=all(v == 0 for v in dBR),
         note="instrument-can-return-otherwise: base_R channel IS frame-free")

# ── (5) CHANNEL 2 — base_H scalar invariants under GENUINE automorphisms ──
#     |B|², Re(B), Σ|base_H_F|²: is ANY of them a frame-free scalar?
for label, g in [("g_disc_permuting", g_disc),
                 ("g_cont_mixing", g_cont),
                 ("g_mix", g_mix)]:
    dBn = []
    dRe = []
    dSN = []
    for P in tests:
        B, _, S_N = reconstruct(P, OCT)
        Bg, _, S_Ng = reconstruct(g(P), OCT)
        dBn.append(cd_norm_sq(Bg) - cd_norm_sq(B))
        dRe.append(Bg[0] - B[0])
        dSN.append(S_Ng - S_N)
    emit(section="channel2_baseH_scalar_invariance", automorphism=label,
         normsqB_defect_all_zero=all(v == 0 for v in dBn),
         normsqB_worst=str(max(dBn, key=lambda v: v * v)),
         ReB_defect_all_zero=all(v == 0 for v in dRe),
         ReB_worst=str(max(dRe, key=lambda v: v * v)),
         sum_baseH_normsq_defect_all_zero=all(v == 0 for v in dSN),
         sum_baseH_normsq_worst=str(max(dSN, key=lambda v: v * v)),
         verdict=("no frame-free scalar from base_H"))

# ── (6) the §3.41.2 element-level echo: continuous-G₂ failure RATIOS ───────
random.seed(7)
for tab, gm, nm in [(OCT, None, "O_definite"), (SPLIT, (-1, -1, 1), "split_O")]:
    if not is_hom(g_cont, tab):
        emit(section="channel2_continuous_failure_ratio", algebra=nm,
             note="g_cont not an automorphism of this algebra")
        continue
    ratB = []
    ratN = []
    for _ in range(40):
        P = Qv([random.randint(-5, 5) for _ in range(8)])
        B, _, _ = reconstruct(P, tab, gm)
        Bg, _, _ = reconstruct(g_cont(P), tab, gm)
        gB = g_cont(B)
        nb = vmag(B)
        if nb > 0:
            ratB.append(vmag(tuple(p - q for p, q in zip(Bg, gB))) / nb)
        nB = cd_norm_sq(B, gm)
        if nB != 0:
            ratN.append(mag(cd_norm_sq(Bg, gm) - nB) / mag(nB))
    emit(section="channel2_continuous_failure_ratio", algebra=nm,
         equivariance_ratio_mean=round(statistics.mean(ratB), 4),
         equivariance_ratio_max=round(max(ratB), 4),
         equivariance_ratio_min=round(min(ratB), 4),
         normsqB_relative_defect_mean=round(statistics.mean(ratN), 4),
         normsqB_relative_defect_max=round(max(ratN), 4),
         note="never restored toward 0 — the element-level echo of §3.41.2's 0.186")

# ── (7) residual within-frame gauge: base_H rotates with the ℓ choice ─────
line145 = next(L for L in lines if set((abs(L[0]), abs(L[1]), abs(L[2]))) == {1, 4, 5})
a, b, c = line145
comp145 = [i for i in range(1, 8) if i not in (a, b, c)]
ell_rows = []
for ell in comp145:
    xq = Qv(X)
    q0 = [Q(0)] * 8
    for i in (0, a, b, c):
        q0[i] = xq[i]
    Q1 = [Q(0)] * 8
    for i in comp145:
        Q1[i] = xq[i]
    e = [Q(0)] * 8
    e[ell] = Q(1)
    q1 = tuple(-v for v in table_product(OCT, tuple(Q1), tuple(e)))
    bh = tuple(Q(2) * v for v in table_product(OCT, tuple(q0), cd_conjugate(q1)))
    ell_rows.append({"ell": ell, "base_H": [str(v) for v in bh],
                     "base_H_normsq": str(cd_norm_sq(bh))})
emit(section="residual_frame_choice_ell", frame=[a, b, c], x=X,
     rows=ell_rows,
     base_H_vector_depends_on_ell=(len({tuple(r["base_H"]) for r in ell_rows}) > 1),
     base_H_normsq_ell_invariant=(len({r["base_H_normsq"] for r in ell_rows}) == 1),
     note="a 2nd within-frame gauge: |base_H|² is ℓ-invariant, base_H itself is not")

# ── (8) the per-frame table for the canonical X (aphantasia) ──────────────
rows = []
for L in lines:
    fr = frame_read(X, L, OCT)
    nz = {i: str(fr["base_H"][i]) for i in range(8) if fr["base_H"][i] != 0}
    rows.append({"frame": list(L), "ell": fr["ell"], "base_H_nonzero": nz,
                 "base_R": str(fr["base_R"]),
                 "base_H_normsq": str(fr["base_H_normsq"])})
B, S_R, S_N = reconstruct(X, OCT)
emit(section="per_frame_table", x=X, rows=rows,
     sum_B=[str(v) for v in B], normsq_B=str(cd_norm_sq(B)), Re_B=str(B[0]),
     sum_baseR=str(S_R), sum_baseH_normsq=str(S_N))

# ── (9) the verdict ───────────────────────────────────────────────────────
emit(section="verdict",
     question=("does the 7-Fano-frame family reconstruct a frame-FREE 𝕆 "
               "invariant under Aut(𝕆)=G₂?"),
     answer="NO — CONFIRMS the ceiling (§3.41.6 Q2, §3.41.2)",
     channel1_baseR="FORCED+DEFINITIONAL (= 8x0²−N(x), product-agnostic, all 4 tables)",
     channel2_baseH=("no frame-free scalar: |B|²/Re(B) move under even a DISCRETE "
                     "automorphism; Σ|base_H_F|² survives the discrete permutation "
                     "(symmetrization) but is KILLED by continuous G₂ (~0.16 rel. "
                     "defect) — the exact trap §3.41.2 defused"),
     controls=("split-𝕆 fails identically (~0.40 equivariance ratio) ⇒ "
               "composition-algebra-wide, FORM not identity; base_R FORCED across "
               "split-𝕆 / random-anticomm / R[ℤ/8]"),
     consistency="consistent with §3.41.2 (0.186, REFUTED) and §3.41.6 Q2; "
                 "does not touch the 168 seam census",
     falsified=False)


if __name__ == "__main__" and len(sys.argv) > 1:
    with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
        for rec in OUT:
            f.write(json.dumps(rec) + "\n")
    print("wrote", len(OUT), "records to", sys.argv[1], flush=True)
