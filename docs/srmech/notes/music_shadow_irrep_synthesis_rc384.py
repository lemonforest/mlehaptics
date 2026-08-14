"""rc384 (`#T1058` / `#T1059` / `#T1060`) — the music-as-carrier / shadow-irrep /
octonion-coherence-ceiling CAPSTONE, every load-bearing number reproduced THROUGH
a shipped rc384 op. Provenance for srmech_research_notebook.md §3.46.

Run:  python music_shadow_irrep_synthesis_rc384.py music_shadow_irrep_synthesis_rc384.ndjson

WHY THIS EXISTS. §3.46 weaves one connective thesis: music is CARRIER
architecture that maps onto the Cayley–Dickson tower — one 1D ℝ-string = one
atomic note; a symphony = the CD-tower automorphism GAUGE; the coherent note it
projects = the frame-free invariant; the octonion Hurwitz WALL = the coherence
ceiling, read four independent ways that all land on the SAME associativity
break. The organizing lens is that every observation is a SHADOW-IRREP (a
projection into a chosen coherency); the invariant is shadow-free; at 𝕆 there is
no canonical shadow. Per the computational-provenance discipline, this script
reproduces each load-bearing number through the shipped surface so the notebook
prose cannot drift from the ops.

⚠️ EPISTEMIC CEILING — FORM, not identity. "symphony / note / coherent" is a
music READING laid on real algebra; what transfers cross-substrate is the
ALGORITHM, never the constant. The CD ladder's k=3 here is the arity-3 ASSOCIATOR
(the 3-cycle triangle), and it MUST NOT be fused with the B/H/N substrate k=3 of
§3.29.3 — that section's whole discipline is that the k=3 senses are DIFFERENT.

NO abs() anywhere: sign is Class-K pin-slot / Class-C reorientation (the shipped
sigma_effective returns ±1 with no abs); spectral deviation is a Euclidean norm
(sum of squares → Class-N sqrt), never an ALU magnitude.

WHAT IT MEASURES (all through shipped ops):
  1. the note-alphabet is ℤ/7 and the circle of fifths is a cyclic GENERATOR
     (cyclic_mod_add, gcd);
  2. violin fifths (+4) vs double-bass fourths (+3) = interval inversion under a
     read-direction WRITHE, 4+3=7 (the octave);
  3. the shadow-irrep MECHANISM = 3-cycle closure: ℍ closes (canonical shadow),
     𝕆 non-associating triple does NOT (cd_cycle_holonomy);
  4. the symphony = the CD-tower automorphism GAUGE — Aut(ℍ)=SO(3) vs Aut(𝕆)=G₂
     (g2_subalgebra=14, an_embedding 14=8+3+3̄, triality τ order-3 Fix(τ)=14);
  5. the coherent note = the gauge-invariant Laplacian spectrum — ℍ is
     Sp(1)-invariant (~1e-15); 𝕆 is gauge-DEPENDENT and the dependence is
     confined to CYCLES (tree ~1e-15, triangle/4-cycle not) — the SAME wall;
     the octonion_frame_read ℍ-base is frame-free UNDER the S³ fiber;
  6. the genuinely NEW parallel — a basis-free 3-tier commensurability LADDER
     (ℚ/harmonic → algebraic/stiff-string → transcendental/membrane) set against
     the Hurwitz dimension ladder, both "basis-free coherence with a ceiling";
  7. cube→SIGN ships (winding_tower → sigma_effective); cube→full-NOTE is open.
"""
import json
import sys

import srmech
from srmech import _native
from srmech.cascade import (cyclic_mod_add, cd_cycle_holonomy, cd_basis,
                            octonion_frame_read)
from srmech.cascade.cayley_dickson import cd_mult, cd_norm_sq
from srmech.cascade.one import winding_tower, the_one
from srmech.math.cyclic import gcd
from srmech.math.q import Q
from srmech.math.rational import sqrt as _rsqrt          # Class-N; NOT math.sqrt
from srmech.math.laplacian import (octonion_laplacian, quaternion_laplacian,
                                   mat_hermitian_eigendecompose, mat_matmul)
from srmech.physics.qm import so8, triality
from srmech.physics.qm.octonion import (octonion_norm, octonion_conjugate,
                                        octonion_left_mult)
from srmech.physics.qm.quaternion import (quaternion_norm, quaternion_conjugate,
                                          quaternion_left_mult)
import srmech.music as music

print("ARTIFACT UNDER TEST:", srmech.__file__, srmech.__version__,
      "HAS_NATIVE=%s" % _native.HAS_NATIVE, flush=True)

OUT = []


def emit(**kw):
    OUT.append(kw)
    print(json.dumps(kw), flush=True)


def _sign_from_parity(popcount):
    """Class-K pin-slot ± from a bit parity — a BRANCH, never abs()."""
    return 1 if popcount % 2 == 0 else -1


# ── 1. the note-alphabet is ℤ/7; the circle of fifths is a cyclic generator ──
# Alphabetical index A=1 … G=7. The circle of fifths F·C·G·D·A·E·B is a single
# 7-cycle stepping +4 mod 7; the fourths cycle (reverse) steps +3 mod 7.
LETTER = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
INV = {v: k for k, v in LETTER.items()}
FIFTHS_ORDER = ["F", "C", "G", "D", "A", "E", "B"]

start = LETTER["F"]
cycle, cur = [INV[start]], start
for _ in range(6):
    cur = cyclic_mod_add(cur, 4, 7)          # +4 mod 7 (the fifth)
    cur = 7 if cur == 0 else cur             # 1..7 letter labels (0≡7)
    cycle.append(INV[cur])
# the user's "−3 if left bigger, +4 if right bigger" = the two balanced-residue
# faces of the SAME ℤ/7 step: −3 ≡ +4 (mod 7). Reduce the balanced residue into
# ℤ/7 first (a Class-I reduction), since the op takes a non-negative addend.
neg3_mod7 = (-3) % 7                      # = 4, the non-negative face of −3 in ℤ/7
plus4 = [cyclic_mod_add(i, 4, 7) for i in range(1, 8)]
minus3 = [cyclic_mod_add(i, neg3_mod7, 7) for i in range(1, 8)]
emit(section="circle_of_fifths_generator",
     alphabet="A=1..G=7 (ℤ/7)",
     fifth_step="+4 mod 7", fourth_step="+3 mod 7",
     generated_cycle=cycle,
     matches_circle_of_fifths=(cycle == FIFTHS_ORDER),
     plus4_equals_minus3_mod7=(plus4 == minus3 and neg3_mod7 == 4),
     gcd_4_7=gcd(4, 7), gcd_3_7=gcd(3, 7),
     both_generate_Z7=(gcd(4, 7) == 1 and gcd(3, 7) == 1),
     fourth_plus_fifth=4 + 3,            # = 7, the octave (the conserved Lk-analog)
     odd_modulus_forces_split="7/2 has no integer half → forced 4+3=7",
     note=("+4 and +3 are the two coprime generators an ODD modulus forces; the "
           "chirality of the fifth/fourth pair is Class-C, NOT the abelian ℤ/7 "
           "alphabet"))


# ── 2. violin fifths vs double-bass fourths: interval inversion under WRITHE ──
# Violin strings G·D·A·E ascend by fifths (+4); the double bass is the violin
# REVERSED, E·A·D·G, ascending by fourths (+3). Reversing the read direction
# (a WRITHE) inverts the interval (a TWIST): +4 ↔ +3, and 4+3=7.
VIOLIN = ["G", "D", "A", "E"]
BASS = list(reversed(VIOLIN))            # E·A·D·G — the double bass tuning
viol_steps = [cyclic_mod_add(LETTER[VIOLIN[i]], 4, 7) for i in range(3)]
viol_ok = all((7 if s == 0 else s) == LETTER[VIOLIN[i + 1]]
              for i, s in enumerate(viol_steps))
bass_steps = [cyclic_mod_add(LETTER[BASS[i]], 3, 7) for i in range(3)]
bass_ok = all((7 if s == 0 else s) == LETTER[BASS[i + 1]]
              for i, s in enumerate(bass_steps))
emit(section="violin_bass_twist_writhe",
     violin=VIOLIN, violin_ascends_by_fifths_plus4=viol_ok,
     double_bass=BASS, bass_is_violin_reversed=(BASS == VIOLIN[::-1]),
     bass_ascends_by_fourths_plus3=bass_ok,
     interval_inversion_under_read_reversal=(viol_ok and bass_ok),
     twist_plus_writhe_sum=4 + 3,
     lk_tw_wr_topological_identity="CONJECTURE — 4+3=7 is genuine interval "
         "inversion; the Călugăreanu Lk=Tw+Wr linking identity needs Tw/Wr "
         "definitions a fingerboard may not support",
     fingering_reading="fifths: 4th finger meets next open string; fourths: 3rd "
         "finger meets, 4th overshoots (why the bass frees the pinky) — a "
         "physical performance fact, kept as prose, not modelled (CAD-scope ban)")


# ── 3. the shadow-irrep MECHANISM = 3-cycle closure (ℍ closes, 𝕆 does not) ──
# Observe vertex b of a triangle {a,b,c} → see its two incident edges (a·b, b·c),
# INFER the opposite edge c·a (the SHADOW). Triality cycles which edge is shadow.
# The inferred shadow is consistent across vertices ⟺ the 3-cycle CLOSES ⟺ the
# associator is zero. ℍ closes (canonical, frame-free shadow); a non-associating
# 𝕆 triple does NOT (perspective-relative, no canonical shadow).
e1, e2, e3, e4 = (cd_basis(8, 1), cd_basis(8, 2), cd_basis(8, 3), cd_basis(8, 4))
hH = cd_cycle_holonomy(e1, e2, e3)       # (e1,e2,e3) lives in the ℍ subalgebra
hO = cd_cycle_holonomy(e1, e2, e4)       # (e1,e2,e4) crosses the 𝕆 doubling seam
emit(section="three_cycle_shadow_closure",
     H_triple="(e1,e2,e3)", H_closes=bool(hH["closed"]),
     H_defect_zero=all(v == 0 for v in hH["defect"]),
     O_triple="(e1,e2,e4)", O_closes=bool(hO["closed"]),
     O_defect_nonzero=any(v != 0 for v in hO["defect"]),
     reading=("ℍ has a canonical frame-free shadow (closure); 𝕆's "
              "non-associating triple has none (no canonical shadow) — the "
              "shadow-irrep is perspective-relative exactly where the algebra "
              "stops associating"))


# ── 4. the symphony = the CD-tower automorphism GAUGE; the ceiling is Aut ──
# Aut(ℍ)=SO(3) (dim 3); Aut(𝕆)=G₂=Der(𝕆) (dim 14). The many-1D-strings-at-once
# is the automorphism gauge; its dimension is the coherence ceiling of the rung.
g2 = so8.g2_subalgebra()
emb = so8.an_embedding()
tau = triality.triality_automorphism()          # order-3 outer τ on so(8)=28
n = tau.n_rows


def _mat_id_residual(m):
    # Frobenius norm of (m − I): a sum of squares → Class-N sqrt, no abs().
    rows = m.tolist()
    ss = sum((rows[i][j] - (1.0 if i == j else 0.0)) ** 2
             for i in range(len(rows)) for j in range(len(rows[i])))
    return float(_rsqrt(ss))


tau2 = mat_matmul(tau, tau)
tau3 = mat_matmul(tau2, tau)
id_res = _mat_id_residual(tau3)
# projector onto Fix(τ): P = (I + τ + τ²)/3 ; tr(P) = dim Fix(τ)
d2, d3 = tau2.tolist(), tau.tolist()
fix_trace = sum((1.0 + d3[i][i] + d2[i][i]) / 3.0 for i in range(n))
emit(section="automorphism_gauge_dims",
     aut_H="SO(3), dim 3", aut_O="G2 = Der(O)",
     g2_dim=len(g2),
     an_embedding_adjoint=list(emb["decomposition"]["adjoint_14"]),  # (8,3,3̄)
     an_embedding_is_8_3_3bar=(tuple(emb["decomposition"]["adjoint_14"]) == (8, 3, 3)),
     tau_dim=n, tau_cubed_is_identity=(id_res < 1e-9),
     tau_cubed_residual=id_res,
     fix_tau_projector_trace=round(fix_trace, 6),
     fix_tau_equals_g2_dim=(round(fix_trace) == 14),
     reading=("the coherence ceiling of a rung IS the dimension of its "
              "automorphism gauge; at 𝕆 that gauge is the 14-dim G₂, the same "
              "14 the g2_subalgebra and the τ Fix-trace both report"))


# ── 5. the coherent note = the gauge-invariant spectrum; 𝕆 wall is on CYCLES ──
def _spectrum(mat):
    ev, _ = mat_hermitian_eigendecompose(mat)
    return sorted(complex(ev[i, 0]).real for i in range(ev.n_rows))


def _spec_dev(s1, s2):
    # Euclidean norm of the sorted-spectrum difference (sum of squares → sqrt).
    ss = sum((a - b) * (a - b) for a, b in zip(s1, s2))
    return float(_rsqrt(ss))


def _unit8(v):
    nn = octonion_norm(v)
    return [c / nn for c in v]


def _o(a, b):
    lo = octonion_left_mult(a).tolist()
    return [sum(lo[k][j] * b[j] for j in range(8)) for k in range(8)]


def _unit4(v):
    nn = quaternion_norm(v)
    return [c / nn for c in v]


def _q(a, b):
    lq = quaternion_left_mult(a).tolist()
    return [sum(lq[k][j] * b[j] for j in range(4)) for k in range(4)]


# tree (a path — gains gauge-removable) vs cycles (holonomy well-defined only if
# associative — 𝕆 fails). Deterministic named gains/gauges, no RNG draw.
GRAPHS = {
    "path3_tree": ([(0, 1), (1, 2)], 3, "tree"),
    "triangle_cycle": ([(0, 1), (1, 2), (2, 0)], 3, "cycle"),
    "4cycle": ([(0, 1), (1, 2), (2, 3), (3, 0)], 4, "cycle"),
}
OCT_GAINS = [[1, 2, -1, 3, 0, -2, 1, 1], [2, 0, 1, -1, 1, 1, 0, -1],
             [-1, 1, 2, 1, 0, 1, -1, 1], [1, -1, 0, 2, 1, 0, 1, -1]]
OCT_GAUGE = [[1, 1, 0, 1, 0, 1, 1, 0], [0, 1, 1, 0, 1, 0, 1, 1],
             [1, 0, 1, 1, 0, 1, 0, 1], [1, 1, 1, 0, 1, 0, 0, 1]]
QUAT_GAINS = [[1, 2, -1, 3], [2, 0, 1, -1], [-1, 1, 2, 1], [1, -1, 0, 2]]
QUAT_GAUGE = [[1, 1, 0, 1], [0, 1, 1, 0], [1, 0, 1, 1], [1, 1, 1, 0]]

for name, (edges, nn, kind) in GRAPHS.items():
    g8 = [_unit8(OCT_GAINS[k % 4]) for k in range(len(edges))]
    s8 = [_unit8(OCT_GAUGE[k % 4]) for k in range(nn)]
    gg8 = [_o(_o(s8[u], g), octonion_conjugate(s8[v]))
           for (u, v), g in zip(edges, g8)]
    dev_o = _spec_dev(_spectrum(octonion_laplacian(nn, edges, gains=g8)),
                      _spectrum(octonion_laplacian(nn, edges, gains=gg8)))
    g4 = [_unit4(QUAT_GAINS[k % 4]) for k in range(len(edges))]
    s4 = [_unit4(QUAT_GAUGE[k % 4]) for k in range(nn)]
    gg4 = [_q(_q(s4[u], g), quaternion_conjugate(s4[v]))
           for (u, v), g in zip(edges, g4)]
    dev_h = _spec_dev(_spectrum(quaternion_laplacian(nn, edges, gains=g4))[::4],
                      _spectrum(quaternion_laplacian(nn, edges, gains=gg4))[::4])
    emit(section="laplacian_tree_vs_cycle", graph=name, kind=kind, n=nn,
         O_gauge_deviation=dev_o, O_gauge_invariant=(dev_o < 1e-9),
         H_gauge_deviation=dev_h, H_gauge_invariant=(dev_h < 1e-9),
         localization=("𝕆 dependence confined to CYCLES: tree invariant, "
                       "cycle not — the SAME wall as the 3-cycle non-closure"))

# the octonion_frame_read ℍ-base is frame-free UNDER the S³ fiber (the coherent
# note) — unchanged under a unit-quaternion right-multiply of BOTH halves.
X = [1, 2, -3, 1, 2, -1, 1, 4]
r = octonion_frame_read(X)
LAM = (Q(1, 2), Q(1, 2), Q(1, 2), Q(1, 2))       # unit quaternion, |λ|²=1
q0f, q1f = cd_mult(r["q0"], LAM), cd_mult(r["q1"], LAM)
rf = octonion_frame_read(list(q0f) + list(q1f))
q0n = cd_mult(r["q0"], LAM)                       # non-fiber: rotate q0 only
rn = octonion_frame_read(list(q0n) + list(r["q1"]))
proj_same = all(rf["base_H"][i] * r["base_R"] == r["base_H"][i] * rf["base_R"]
                for i in range(4))
proj_diff = not all(rn["base_H"][i] * r["base_R"] == r["base_H"][i] * rn["base_R"]
                    for i in range(4))
sphere = (cd_norm_sq(r["base_H"]) + r["base_R"] * r["base_R"]
          == r["norm_sq"] * r["norm_sq"])
emit(section="frame_read_coherent_note",
     base_frame_free_under_fiber=(rf["base_H"] == r["base_H"]
                                  and rf["base_R"] == r["base_R"]),
     projective_base_invariant_under_fiber=proj_same,
     base_changed_under_nonfiber_move=proj_diff,
     four_sphere_identity_exact=sphere,
     reading="the ℍ-valued Hopf base is the coherent note — frame-free UNDER "
             "the S³ fiber only; no frame-free 𝕆 SCALAR exists (the ceiling)")


# ── 6. the NEW parallel: a basis-free 3-tier commensurability LADDER ──
# ℚ/harmonic-fused → algebraic/stiff-string → transcendental/membrane. Both this
# ladder and the Hurwitz dimension ladder are "basis-free coherence with a
# ceiling" (field-degree ↔ Hurwitz dimension).
HARMONIC = [1, 2, 3, 4, 5, 6]                    # Tier 1 — the integer series
cv1 = music.commensurability_verdict(HARMONIC)
per1 = music.common_period(HARMONIC)
ET = music.equal_temperament_partials(12)        # Tier 2 — algebraic irrationals
cv2 = music.commensurability_verdict(ET["ratios"])
MEM = music.membrane_partials(3, 3)              # Tier 3 — DECLARED transcendental
cv3 = music.commensurability_verdict(MEM["ratios"], open_partials=MEM["open_partials"])
tier2_raises = tier3_raises = False
try:
    music.common_period(ET["ratios"])
except ValueError:
    tier2_raises = True
try:
    music.common_period(MEM["ratios"], open_partials=MEM["open_partials"])
except ValueError:
    tier3_raises = True
emit(section="commensurability_ladder",
     tier1_rational_verdict=cv1["verdict"], tier1_integer_series=cv1["integer_series"],
     tier1_common_period=per1,
     tier2_algebraic_verdict=cv2["verdict"], tier2_tier=cv2["tier"],
     tier2_field_degrees=list(cv2["field_degrees"]),
     tier2_common_period_raises=tier2_raises,
     tier3_open_verdict=cv3["verdict"], tier3_tier=cv3["tier"],
     tier3_common_period_raises=tier3_raises,
     ceiling=("the ladder has a COHERENCE CEILING: a common period (the "
              "coherent-note analog) exists at Tier 1, and provably does NOT "
              "at the transcendental Tier 3 — the field-degree parallel of the "
              "Hurwitz octonion wall"),
     refuted_alternative=("Kuramoto is NOT this parallel — coupled oscillators "
                          "cohere as a frame-relative MEAN with no ceiling"))


# ── 7. cube→SIGN ships; cube→full-NOTE is the OPEN conjecture ──
# winding_tower(w) = the (ℤ/2)^d hypercube coordinate (LSB-first / little-endian);
# its popcount parity is the scalar SIGN. w=5→(1,0,1)→+1; w=7→(1,1,1)→−1. The
# shipped One.sigma_effective() IS this cube→sign projection (returns ±1, no abs).
t5, t7 = winding_tower(5), winding_tower(7)
sign5_direct = _sign_from_parity(sum(t5))
sign7_direct = _sign_from_parity(sum(t7))
se5 = the_one(1, 0, 1, w=(5, 0, 0)).sigma_effective()
se7 = the_one(1, 0, 1, w=(7, 0, 0)).sigma_effective()
emit(section="cube_to_sign_projection",
     winding_tower_5=list(t5), popcount_5=sum(t5), sign_5=sign5_direct,
     winding_tower_7=list(t7), popcount_7=sum(t7), sign_7=sign7_direct,
     sigma_effective_5=se5, sigma_effective_7=se7,
     shipped_op_matches_direct=(se5 == sign5_direct and se7 == sign7_direct),
     distinguishes_5_from_7=(se5 != se7),
     mod2_would_conflate=((5 % 2) == (7 % 2)),   # both ≡1: the bare quotient loses it
     cube_to_note_conjecture=("cube→full NOTE (pitch+loudness+phase, #T1011) via "
         "ALTERNATING endianness is OPEN; endianness = Class-C chirality with "
         "two semantics (encapsulate-endings vs fast-read); ℝ-rung=one-note / "
         "C·H·O·S=compositions is CONJECTURE"))


if __name__ == "__main__" and len(sys.argv) > 1:
    with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
        for rec in OUT:
            f.write(json.dumps(rec) + "\n")
    print("wrote", len(OUT), "records to", sys.argv[1], flush=True)
