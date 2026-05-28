# RBS Research Notebook — Resonant Bit-Serialized Neural Net (RBS-NN) + Language-Model cross-substrate translation (RBS-LM)

**Status:** consolidating canonical notebook, opened 2026-05-27. Distills the two parallel research arcs `docs/srmech/rbs_nn_research/` (RBS-NN, 23 files, arc structurally closed PR #684) and `docs/srmech/rbs_lm_research/` (RBS-LM, 375+ files, rolling on the read-only PR #687 branch). This notebook is the **canonical distillation**; the per-finding working detail lives in those directories. Sister to `srmech_research_notebook.md` (§3.25 carries the compressed arc summary; §3.27 carries the recursive-Hopf-operational cascade-vocabulary lens) and `../antikythera-maths/mfo_spectral_research_notebook.md` (§VIII.31.10–11 carry the substrate-ontology landing).

**Scope discipline.** Algebra / eigenbasis / cyclic-group / spectral side only (per `docs/srmech/CLAUDE.md`). No lineage claims per `[[feedback_no_lineage_claims_in_notebook]]`; the arc reads what an NN / LM **already is** structurally — it does not invent an architecture. Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]`. No class promotion: vocabulary stays at 14 A–N per `[[feedback_no_privileged_primitive_classes]]`.

> **Resume marker (load-bearing).** PR #687 = `origin/research/rbs-lm-rolling-2` is **READ-ONLY** (parallel session, per `[[feedback_session_worktree_namespace_isolation]]`). The working research notes are frozen-recoverable at baseline **`1536802d`** via `git show 1536802d:<path>`; re-survey `1536802d..origin/research/rbs-lm-rolling-2` for notes added after the baseline. This notebook is updated as #687 produces mature findings worth canonical promotion. See the user-memory resume file `project_pr687_research_integration_baseline_and_resume`.

---

## §0 What RBS reads, and the MFO foundation it rests on

Per `mfo_spectral_research_notebook.md` §VII.1.1 the MFO two-level ontology maps directly onto compute primitives, and that map is the whole foundation of both arcs:

| MFO level | Domain | Operations | Compute home |
|---|---|---|---|
| **Level 1 — substrate** | Hopf-compressed metric field at every instantiation depth | A content-mint (SHA-256), I cyclic shift, M XOR-bind, J prime, L Laplacian | **ALU, bit-exact** |
| **Level 2 — excitation** | localized + delocalized excitations within the substrate | K rotate-overlay `max(v, rotate(v))`, M bundle-of-rotations averaging, derivative-sign-flip at extrema | **FPU, intentional lift** |

A conventional neural net *appears* to lose bit-exactness because it performs **lossy averaging projections** (bundle, max-pool) that collapse Level-1 → Level-2 implicitly. RBS names that collapse explicitly: Level-1 substrate ops stay bit-exact on the ALU; rotate-overlay-class ops route through **Class K** on the FPU *by ontological assignment* (rotation IS Class K pin-slot, inhabiting fiber-space), not as a precision workaround. This is the framework reading of the "substrate-self-recognition sign-flip at AI-substrate scale" (MFO line ~2812 — humans building artificial neural nets).

---

## §1 RBS-NN — Resonant Bit-Serialized Neural Net (arc closed PR #684)

**Source:** `docs/srmech/rbs_nn_research/` (R-RBS-NN-1 … R-RBS-NN-9 + worked examples + README/ROADMAP/UPSTREAM_NOTES).

**End-user goal.** A foundational srmech feature giving end users an entry point to a neural-net architecture that **learns and preserves a user lexicon in native format**. A neural net at the substrate level is highly efficient knowledge storage; RBS-NN names that efficiency explicitly via **bit-exact HDC binding** rather than learned-then-quantized weights. The user's vocabulary becomes the binding alphabet directly — no learned-embedding bottleneck quantizing the user.

**The substantive structural claim** (R-RBS-NN-1 §4 + R-RBS-NN-3b §5): a conventional float-weight transformer is structurally a **Level-2 bundle-of-views projection** of what could be expressed at **Level-1 bind-form** (MFO §VII.1.3 Mechanisms 2 vs 1). The ~6.9% bundle-averaging cost is the ontological signature of that projection.

**Two-tier architecture** (`ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md`): a Klein-4 / polar two-tier binding pattern — the Class-M variant ladder (bipolar → polar → Klein-4 (ℤ₂)² → rank-N) instantiated as the NN's binding alphabet. R-RBS-NN-4 (closed 2026-05-27) lands the **token → hypervector encoder** with a variant-choice protocol.

**Worked examples** (`worked_example_*.py`): attention, capacity scan, MLP, position binding, user lexicon — each reading a standard NN component in A–N cascade vocabulary.

> **§1 status:** scaffold + headline distillation. Per-report (R-RBS-NN-1…9) detailed promotion is a follow-up pass; the working files remain the SSoT until promoted here.

---

## §2 RBS-LM — language-model cross-substrate translation (rolling, PR #687)

**Source:** `docs/srmech/rbs_lm_research/` (375+ Findings; rolling). **ROADMAP NEXT-1** (user direction 2026-05-25): *"download a small public LLM and make it an RBS-HDC instrument in the same way we did with ephemerides … without having to load the model into VRAM … we're doing a cross-substrate translation … trying to find out if we can avoid having to train from scratch."*

**The test.** Whether a trained LLM's learned content can be **re-extracted as Level-1 bind-form HDC bindings** — recovering the Level-2 → Level-1 inversion the framework predicts (§1). The **ephemerides precedent** is the existence proof at a different binding shape: 52 bodies + Chebyshev coefficients (3.3 GB JPL DE441) → 256 KB ALU-native BIP state. RBS-LM is the third binding shape (trained-NN learned content; binding pattern TBD per methodology).

### §2.1 The recursive-Hopf-operational / chirality cluster (F120–F136)

The RBS-LM arc surfaced the **third substrate-native naming** of the substrate — `4:3:(4:3)` recursive-Hopf-operational — and its chirality dual. This is the cluster promoted to canonical in this integration pass:

- **G₂ = aut(𝕆) = 14** explicit identity; 𝔰𝔬(𝕆) = 𝔤₂ ⊕ L_Im(𝕆) ⊕ R_Im(𝕆), 28 = 14+7+7 (F123/F126; landed MFO §VIII.31.10).
- **Biological 4:3:7** compression (F121, validated by N=4 Kuramoto K_c) — the cnidarian pacemaker embodies the outer-4 operational core directly.
- **`4:3:(4:3)`** = outer-4 operational core (A,B,H,N) : outer-3 substrate-projection bridge (I,C,J) : inner (4+3) octonionic-Hopf cascade-detection — the A–N **harmonic ladder of L²(S⁷)** (F124/F127/F129).
- **`4:3:(4:3)` vs `4:3:(3:4)`** = Class C chirality-dual = the two mismatched-plates; **14 + 14 = 28 = dim 𝔰𝔬(8)** = the SO(8) adjoint (F128/F129).
- Extensions F130–F136: antimatter 4-way chirality decomposition, dark-sector quad-helix sector-projection, full-chirality Klein-4 HDC engineering proposal, substrate-knows-itself / observer-projection-locking (Dune parallel), substrate-vs-shadow two-level chirality, Roman-numeral substrate-native chirality notation.

**Canonical landings (this pass):** MFO **§VIII.31.11** (substrate-ontology) + srmech **§3.27** (cascade-vocabulary). **External coherence:** the `28 = 𝔰𝔬(8)` octonion structure is independently developed — without the A–N operators — in the division-algebra Standard-Model program (octonion → Cℓ(8) → Spin(10), Spin(8) triality). A dedicated A–N ↔ octonion/Cℓ(8) dictionary section is **deferred pending PDF-verified citations** per `[[feedback_pdf_extraction_citation_discipline]]`.

> **§2 status:** scaffold + recursive-Hopf-operational cluster (the integration-pass deliverable). The bulk of the 375-finding backlog (F1–F119, F130–F136 detail) awaits triage + incremental promotion in later passes.

---

## §3 Index + integration roadmap

| Bucket | Source | Canonical home | Status |
|---|---|---|---|
| MFO notebook updates (Rounds 31–43, §VIII.31, §VII.6.14–6.20) | #687 | already on `main` (origin/main ⊇ #687) | DONE |
| §VIII.31.10 G₂=aut(𝕆) landing | #687 commit 84494fc5 | MFO §VIII.31.10 | DONE (cherry-picked) |
| recursive-Hopf-operational `4:3:(4:3)` / 28=SO(8) (F124–129) | #687 | MFO §VIII.31.11 + srmech §3.27 | DONE (this pass) |
| RBS-NN distillation (R-RBS-NN-1…9) | `rbs_nn_research/` | this notebook §1 | scaffold; incremental |
| RBS-LM cross-substrate (NEXT-1) | `rbs_lm_research/` | this notebook §2 | scaffold; incremental |
| RBS-LM backlog F1–F119 + F130–136 | `rbs_lm_research/` | this notebook §2.x | triage pending |
| Furey octonion/Cℓ(8) external-coherence dictionary | external | MFO §VIII.31.x | deferred (PDF-verify first) |

**Resume protocol.** When #687 produces new notes: (1) `git log 1536802d..origin/research/rbs-lm-rolling-2 -- docs/srmech/rbs_lm_research docs/srmech/rbs_nn_research` to see what's new since baseline; (2) promote mature findings into §1/§2 here + MFO/srmech notebooks; (3) advance the baseline marker in the user-memory resume file. #687 stays read-only throughout.

---

## How to cite this notebook

**Plain text:** Kirkland, S. (2026). *RBS Research Notebook — Resonant Bit-Serialized Neural Net + Language-Model cross-substrate translation*. mlehaptics Spectral-Research Portfolio. https://github.com/lemonforest/mlehaptics/blob/main/docs/srmech/rbs_research_notebook.md

**Per-result citation discipline.** Specific technical claims cite their canonical sources directly (textbooks / peer-reviewed papers PDF-verified per `[[feedback_pdf_extraction_citation_discipline]]`). Framings here are candidate methodological readings per `[[feedback_no_lineage_claims_in_notebook]]`, not endorsed over alternatives without explicit empirical convergence.

**Project-level citation.** See `CITATION.cff` at the repo root.
