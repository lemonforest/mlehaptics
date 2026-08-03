"""Computational provenance for srmech rc383 — `defect_ladder` + the cross-substrate
"declared-parallel-state ⊗ projector-excitation → rung-meaningful subset" instrument
(`#T1054`; sibling arcs `#T1058` / `#T1059`).

Regenerates, with REAL srmech ops (no hand-rolled math, no abs()):

  1. The Cayley–Dickson property-loss ladder censuses THROUGH ``defect_ladder`` —
     commutator 6/42/210 (turn-on ℍ), associator 0/168/1848 (turn-on 𝕆), and the
     𝕊 SEAM-CROSSING alternator witness ([a,a,e4]=2·e15 for a=e1+e10; the zero
     divisor (e1+e10)(e4−e15)=0). Rung 4 is NOT basis-visible — that is the point.
  2. Three DISTINCT domain instances of the SAME instrument-FORM:
       QM     — a declared superposition is meaningless until a MEASUREMENT
                PROJECTOR P=|e⟩⟨e| is applied (Born rule ⟨ψ|P|ψ⟩); exact-ℚ via QMat.
       GENOME — the strand declares ALL genes; the CHROMATIN gate under a cell_state
                is the projector (heterochromatin = projected-out). Same strand, two
                cell_states → two different expressed subsets.
       MUSIC  — the 4×5 viola fingerboard declares a lattice of notes (a fiber); the
                bow/pluck is the projector (a note is spatially-absent until excited).
                The inter-string perfect-fifth offset (+4 diatonic mod 7 / +7
                semitone mod 12) is a cyclic generator (gcd=1); the TWIST (fixed
                offset) ⊕ WRITHE (read-orientation chirality) is the two-readings
                structure.

⚠️ EPISTEMIC CEILING (`[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`):
this reads the FORM the three domains share, NOT an identity. The ladder's k=3 is
the arity-3 Cayley–Dickson associator and MUST NOT be fused with the substrate
B/H/N k=3 signature (different k=3's). Cross-substrate reading transfers the
ALGORITHM (the instrument), never the constant.

SSoT: Schafer (1966) §III.1; Baez (2002) arXiv:math/0105155 (CD ladder). von
Neumann (1932) / Sakurai §3.4 (Born rule). Run:
  PYTHONUTF8=1 PYTHONPATH=docs/srmech/python python docs/srmech/notes/defect_ladder_rc383.py
"""
from __future__ import annotations

import json
import pathlib

from srmech.cascade import defect_ladder, cd_basis, cd_add, cd_mult, cyclic_mod_add
from srmech.math.cyclic import gcd
from srmech.math.q import Q
from srmech.math.qmat import QMat

OUT = pathlib.Path(__file__).with_suffix(".ndjson")
RECORDS: list[dict] = []


def emit(record: str, **fields) -> None:
    row = {"record": record, **fields}
    RECORDS.append(row)
    print(json.dumps(row, ensure_ascii=False))


# ──────────────────────────────────────────────────────────────────────
# 1. The property-loss ladder censuses, THROUGH defect_ladder.
# ──────────────────────────────────────────────────────────────────────

def commutator_noncommuting(dim: int) -> int:
    """Ordered basis pairs (i, j) whose defect_ladder commutator field is nonzero
    (the commutator field is z-independent; e0 is an arbitrary z)."""
    e = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim)
               if defect_ladder(e[i], e[j], e[0])["nonzero"]["commutator"])


def associator_nonassociating(dim: int) -> int:
    """Ordered basis triples (i, j, k) whose defect_ladder associator field is
    nonzero — the per-rung associativity census, read through the ladder op."""
    e = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if defect_ladder(e[i], e[j], e[k])["nonzero"]["associator"])


# commutator turns on at ℍ (dim 4); closed form (dim-1)(dim-2).
for dim in (1, 2, 4, 8, 16):
    n = commutator_noncommuting(dim)
    emit("cd_commutator_census", dim=dim, algebra=defect_ladder(
            cd_basis(dim, 0), cd_basis(dim, 0), cd_basis(dim, 0))["algebra"],
         noncommuting=n, total=dim * dim, closed_form=(dim - 1) * (dim - 2),
         matches_closed_form=(n == (dim - 1) * (dim - 2)))

# associator turns on at 𝕆 (dim 8): 0/168/1848 at dim 4/8/16.
for dim in (2, 4, 8, 16):
    n = associator_nonassociating(dim)
    emit("cd_associator_census", dim=dim, nonassociating=n, total=dim ** 3)

# The 𝕊 SEAM crux: rung 4 is not basis-visible; needs a doubling-seam-crosser.
a = cd_add(cd_basis(16, 1), cd_basis(16, 10))          # a = e1 + e10
seam = defect_ladder(a, a, cd_basis(16, 4))            # [a, a, e4]
# a basis-only left-alternator probe [e_i, e_i, e_j] is 0 at 𝕊 (falsely alternative)
basis_alt_all_zero = all(
    all(v == 0 for v in defect_ladder(cd_basis(16, i), cd_basis(16, i),
                                      cd_basis(16, j))["defects"]["left_alternator"])
    for i in range(16) for j in range(16))
# the zero divisor (e1 + e10)(e4 − e15) = 0
y = tuple(Q(1) if k == 4 else (Q(-1) if k == 15 else Q(0)) for k in range(16))
zd = cd_mult(a, y)
emit("cd_seam_witness", dim=16, a_form="e1 + e10", probe="[a, a, e4]",
     associator=[int(q) for q in seam["defects"]["associator"]],
     associator_is_2e15=(seam["defects"]["associator"]
                         == tuple(Q(2) if k == 15 else Q(0) for k in range(16))),
     rung=seam["rung"], admits_alt_zero_div_at_4=seam["rung_admits"]["alt_zero_div@4"],
     basis_only_left_alternator_all_zero=basis_alt_all_zero,
     zero_divisor_product=[int(q) for q in zd],
     zero_divisor_is_zero=all(q == 0 for q in zd))

# The rung-admit projector mask across the ladder (the parallel read).
for dim in (2, 4, 8, 16):
    r = defect_ladder(cd_basis(dim, 1),
                      cd_basis(dim, min(2, dim - 1)),
                      cd_basis(dim, min(4, dim - 1)))
    emit("projector_mask", dim=dim, rung=r["rung"], algebra=r["algebra"],
         rung_admits=r["rung_admits"], projected=sorted(r["projected"]))


# ──────────────────────────────────────────────────────────────────────
# 2a. QM — measurement projection (the LITERAL projector). Exact-ℚ via QMat.
# ──────────────────────────────────────────────────────────────────────
# Declared superposition |ψ⟩ = (3/5)|0⟩ + (4/5)|1⟩ (real, normalized) — the
# amplitudes are the "parallel eq-set", meaningless as a definite value until a
# measurement projector P = |e⟩⟨e| is applied. Born rule prob = ⟨ψ|P|ψ⟩.
psi = QMat.from_rows([[Q(3, 5)], [Q(4, 5)]])
P0 = QMat.from_rows([[Q(1), Q(0)], [Q(0), Q(0)]])       # |0⟩⟨0|
P1 = QMat.from_rows([[Q(0), Q(0)], [Q(0), Q(1)]])       # |1⟩⟨1|
bra = psi.transpose()
born0 = bra.matmul(P0).matmul(psi).to_lists()[0][0]
born1 = bra.matmul(P1).matmul(psi).to_lists()[0][0]
norm = bra.matmul(psi).to_lists()[0][0]
P0_idempotent = P0.matmul(P0).to_lists() == P0.to_lists()   # P² = P
emit("qm_born_projection",
     state="(3/5)|0> + (4/5)|1>",
     projector_P0="|0><0|", projector_P1="|1><1|",
     born_prob_0=[born0.numerator, born0.denominator],
     born_prob_1=[born1.numerator, born1.denominator],
     completeness=[(born0 + born1).numerator, (born0 + born1).denominator],
     norm=[norm.numerator, norm.denominator],
     P0_is_idempotent_hermitian=P0_idempotent)


# ──────────────────────────────────────────────────────────────────────
# 2b. GENOME — chromatin access is the projector. Same strand, two cell_states.
# ──────────────────────────────────────────────────────────────────────
from srmech.biology import genome as G

LEAF = G.LEAF_CAP
B1, B2 = 1 << 1, 1 << 2


def _leaves(n: int, fill: int) -> list[list[int]]:
    return [[(fill + i) & 3 for i in range(LEAF)] for _ in range(n)]


one = G._default_coupling(LEAF)
strand = G.genome(coupling=one, chromosomes=[
    ("chrA", [("geneA", _leaves(4, 0))]),
    ("chrB", [("geneB", _leaves(4, 1))])])
# facultative chromatin gates, each keyed on a DIFFERENT cell-state bit
strand = G.condense(strand, coupling=one, label="chrA", state={"activator": B1})
strand = G.condense(strand, coupling=one, label="chrB", state={"activator": B2})

expr_A = [lbl for lbl, _ in G.gene_express(strand, one, B1)]
expr_B = [lbl for lbl, _ in G.gene_express(strand, one, B2)]
acc_A = list(G.accessible(strand, B1))
acc_B = list(G.accessible(strand, B2))
emit("genome_chromatin_projection",
     declared_genes=["geneA", "geneB"],
     cell_state_A=B1, expressed_A=expr_A, accessible_A=acc_A,
     cell_state_B=B2, expressed_B=expr_B, accessible_B=acc_B,
     projector_selects_different_subset=(expr_A != expr_B))


# ──────────────────────────────────────────────────────────────────────
# 2c. MUSIC — the viola 4×5 fingerboard (a fiber); the bow is the projector.
# ──────────────────────────────────────────────────────────────────────
# Strings C, G, D, A in perfect fifths. Inter-string offset = +4 diatonic steps
# (mod 7) = +7 semitones (mod 12). Each string's 4th finger lands on the NEXT
# string's open note. +4 mod 7 generates ℤ/7 (gcd(4,7)=1); +7 mod 12 generates
# ℤ/12 (gcd(7,12)=1) — the circle of fifths as a cyclic generator.
STRINGS = ["C", "G", "D", "A"]
DIATONIC_OFFSET, CHROMATIC_OFFSET = 4, 7

# the 4×5 declared fingering matrix: M[s][f] = 4·s + f diatonic steps above C
M = [[DIATONIC_OFFSET * s + f for f in range(5)] for s in range(4)]
diatonic_pc = [[m % 7 for m in row] for row in M]       # pitch class mod 7

# 4th finger of string s == open of string s+1 (VERIFIED)
fourth_finger_meets_next_open = all(
    M[s][4] % 7 == M[s + 1][0] % 7 for s in range(3))


def orbit(start: int, step: int, n: int) -> list[int]:
    """The cyclic orbit start, start+step, … under srmech cyclic_mod_add (Class I)."""
    seen, cur = [], start
    while cur not in seen:
        seen.append(cur)
        cur = cyclic_mod_add(cur, step, n)
    return seen


z7 = orbit(0, DIATONIC_OFFSET, 7)
z12 = orbit(0, CHROMATIC_OFFSET, 12)
emit("music_fingerboard_projection",
     strings=STRINGS, fingering_matrix_diatonic=M, diatonic_pitch_class=diatonic_pc,
     inter_string_offset_diatonic_mod7=DIATONIC_OFFSET,
     inter_string_offset_semitone_mod12=CHROMATIC_OFFSET,
     gcd_4_7=gcd(DIATONIC_OFFSET, 7), z7_is_generator=(gcd(DIATONIC_OFFSET, 7) == 1),
     gcd_7_12=gcd(CHROMATIC_OFFSET, 12), z12_is_generator=(gcd(CHROMATIC_OFFSET, 12) == 1),
     z7_orbit=z7, z7_full=(len(z7) == 7),
     z12_orbit=z12, z12_full=(len(z12) == 12),
     fourth_finger_meets_next_open=fourth_finger_meets_next_open,
     twist="inter-string fifths offset (fixed +4/+7 screw pitch)",
     writhe="read-orientation: thinnest-first descending vs note-ascending (Class-C chirality)")


emit("meta", rc="0.9.0rc383", task="#T1054",
     siblings=["#T1058", "#T1059", "#T1011"],
     op="srmech.cascade.defect_ladder", classification="composition_of_c",
     abi_version=10, tools_total=533,
     generated_by="docs/srmech/notes/defect_ladder_rc383.py")

OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in RECORDS),
               encoding="utf-8")
print(f"\nwrote {OUT} ({len(RECORDS)} records)")
