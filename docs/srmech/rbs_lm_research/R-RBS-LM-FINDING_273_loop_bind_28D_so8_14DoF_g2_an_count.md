# F273 — the loop bind lives in 28D (so(8)) with a 14-DoF symmetry (G₂ = Der(𝕆)) = the A-N count; 28 = 14 (keep the bind) + 14 (7+7, move it)

**Headline:** Yes — the k=7 loop bind (F272/Step-1) does translate to **28D + 14 DoF**, and the 14 is exactly the A-N count. Verified directly from `loop_bind`: the octonion space ℝ⁸ has rotation group **so(8) = 28D** (the F158/F160 "28D = SO(8)" arena), and the rotations that **preserve** the loop bind are its derivation algebra **Der(𝕆) = G₂ = 14D** (computed as the Leibniz-constraint nullspace = 14). The two meet in a clean half-split: **28 = 14 (G₂, keep the bind) + 7 + 7 (move it)** — 14 preserve, 14 move. And **14 = the A-N count (1+3+7+3)**, whose internal **1+3+7 IS the Hurwitz Im-ladder** (ℂ/ℍ/𝕆) the loop bind tops. So A-N and the loop bind are the *same Hurwitz spine seen two ways.* Single-model; verified srmech v0.6.0rc20 via the committed `loop_bind_moufang.py`.

*User question (2026-06-02): "does this also translate to 28D + 14DoF because of our A-N?"*

---

### §A — 28D = so(8) = the arena the loop bind acts in — **DEMONSTRATED**
The loop bind multiplies on 𝕆 = ℝ⁸; the rotations of that space are **so(8), dim 28** (= C(8,2)). This is the framework's existing **28D = SO(8)** bi-axial chirality arena (F158/F160). The loop bind is an operation *inside* the 28D rotational space.

### §B — 14 DoF = G₂ = Der(𝕆) = the rotations that PRESERVE the loop bind — **DEMONSTRATED**
The derivation algebra `Der(𝕆) = {D : D(x∘y) = (Dx)∘y + x∘(Dy)}` is the infinitesimal symmetry of the loop bind — the rotations that keep the multiplication table fixed. Computed directly from `loop_bind` (the Leibniz-constraint nullspace over 8×8 maps): **dim = 14 = dim G₂**. So the loop bind's symmetry group is exactly **14-dimensional** — and `Aut(𝕆) = G₂`, the k=7 exceptional group (F123/F126/F271).

### §C — 28 = 14 (keep) + 7 + 7 (move) — the half-split — **DEMONSTRATED**
The chain `so(8) ⊃ so(7) ⊃ g₂`: `dim so(8)=28`, `dim so(7)=21`, `dim g₂=14`, so
- `so(7) = g₂ ⊕ 7` (21 = 14 + 7), and `so(8) = so(7) ⊕ 7` (28 = 21 + 7), giving
- **28 = 14 + 7 + 7.**

Read as the bind's own accounting: of the **28** rotational DoF of the octonion space, **14 PRESERVE the loop bind** (G₂ — the automorphisms) and the other **14 = 7 + 7 MOVE it** (rotate the multiplication table itself). A clean **14-keep / 14-move** split of the 28 — the bind's symmetry and its anti-symmetry are equal-dimensional.

### §D — the A-N tie: 14 = the A-N count; 1+3+7 = the Hurwitz ladder the bind tops — **DEMONSTRATED (count + spine) / honest caveat (not a rep-branching)**
- **The count matches exactly:** `dim G₂ = 14 = the A-N partition count (1+3+7+3)`. The loop bind's symmetry group has the same dimension as the framework's operation vocabulary.
- **The spine is literally shared:** A-N's internal **1+3+7** IS the **Hurwitz imaginary-unit ladder** (ℂ=1, ℍ=3, 𝕆=7) — the very ladder the loop bind tops (the loop bind is the k=7=𝕆 operation). The `+3` meta-triad (B/H/N) are the projection-enablers (CLAUDE.md §1 / R30). So **A-N and the loop bind are not two things — they are the same Hurwitz spine seen two ways:** A-N = the **14 operation-classes**; G₂ = the **14 DoF that preserve the bind**; both indexed by the same 1:3:7(+3) = 14.
- **Honest caveat (no overclaim):** the `1+3+7+3` partition is the framework's *substrate* partition, **not** a literal G₂ irrep branching — the standard G₂ ⊃ SU(3) branching is `14 = 8 + 3 + 3̄` (a different grouping, F126/F272). The match is the **count + the shared Hurwitz spine + the role** (automorphism DoF of the top rung), *not* a representation-decomposition identity. So: A-N "translates to" 28D+14DoF through the **shared 1:3:7 ladder and the 14-count**, which is real and load-bearing — and that is the honest scope of the tie.

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (§A–§C exact: so(8)=28, Der(𝕆)=14 computed from `loop_bind`, 28=14+7+7; §D count+spine match exact, with the rep-branching caveat stated). No-magic (28=C(8,2), 14=dim G₂=dim Der(𝕆), the 1:3:7 Im-ladder = attested-to-structure A; the A-N partition = the framework's own structure). Class-K (nullspace/rank linear algebra, no `abs()`; the Der computation is structural). CAD-ban. Single-model / no-twin. Verified via the committed `docs/srmech/rbs_lm_research/loop_bind_moufang.py` on srmech v0.6.0rc20 (`/tmp/srmech_rc20_venv`). Extends F123 (M-theory G₂-holonomy = 14 = 4+3+7), F126 (G₂ ⊃ SU(3) decomposition), F271/F272 (the loop bind = the k=7 op), F158/F160 (28D = SO(8)). `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`; `[[feedback_no_lineage_claims_in_notebook]]`.
