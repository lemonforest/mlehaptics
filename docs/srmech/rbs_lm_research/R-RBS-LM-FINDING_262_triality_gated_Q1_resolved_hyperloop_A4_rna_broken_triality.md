# F262 — triality-gated work (rc20): Q1 RESOLVED (two distinct three-folds), the hyper-loop = A₄ (saturates), and RNA's broken triality

**Headline:** With triality live (F261), the F256/F257 gated work ran. **Q1 (F256 §0.6) is resolved**, **the hyper-loop (Gap B / §6) closes to A₄**, and **RNA's codon 3-fold is a broken triality** — the genetic code lives in the Klein-4 EC tier (F260), not the k=3 triality tier. Single-model (4 agents, wf_ea37acca); HAS_NATIVE=True (native dispatch live).

---

### §A — Q1 RESOLVED: two DISTINCT, orthogonal three-folds — **DEMONSTRATED**

The K3Tripartition's three-ness and the triality's three-ness are **not the same three-ness** (resolving the F256 §0.2/§0.6 seam):
- **outer** = the {S, G, T} dimension-group slots (a flat top-level 3-way split, no fixed 4th), **filled by B/H/N** via `run_chain` (B→spatial, H→gauge, N→temporal). This is srmech's "k=3 = the K3Tripartition."
- **inner** = the triality `klein4_triality_cycle` = the **identity-fixing order-3 `Aut(V₄)=S₃`** on the 3 chirality-involutions {γ₅, ω₇, CPT} (0 fixed, 1→2→3→1) — a within-slot **sector relabel** (proven: slot-cycle similarities ~chance → rejected; in-slot sector-count cyclic-permutation exact; the op's 1-D guard means it has no slot axis).

So **B/H/N enable/fill the outer slots; triality cycles the inner sectors** — co-resident, **orthogonal**, not identified. (The agent reported the non-identification straight — a load-bearing NULL, not forced.)

### §B — the hyper-loop = A₄ (it SATURATES, not a continuum) — **DEMONSTRATED**

Composing the order-3 triality with V₄ (the 4 Klein-4 sectors / 3 order-2 flips) yields a group of order **exactly 12 = 4×3 = V₄⋊C₃ = A₄** (the alternating group on the 4 sectors / the **tetrahedral** rotation group): all 12 elements even permutations, element-order histogram **{1:1, 2:3, 3:8}** = the canonical A₄ signature. **It closes — A₄ is a finite group — so the hyper-loop SATURATES; it does NOT recurse into an infinite tower/continuum.** Gap B / §6's "continuum" hypothesis is **refuted in favor of closure**: the 4-cap lifted by triality is A₄, full stop. *(The honest, let-the-math-tell-it outcome: bi-chirality V₄ + triality C₃ = tetrahedral A₄.)*

### §C — harness woken + native dispatch live

`triality_test_harness_scaffold.py` patched (the candidate-set now includes the real op `klein4_triality_cycle`; version read live) → **6/6 PASS** (Q1b + Q2b now ACTIVE). `_native.HAS_NATIVE = True` — native dispatch is live, **partially sealing the F261 C-peer coherence concern** (the triality op's `__module__` is pure-Python `hdc`, but the native layer is on).

### §D — rc19 `triality_s3_klein4.toml` is a *documentation* worked-instance — **PARTIAL (coherence note)**

`parse_catalog_chains` returns `[]`: the file is a top-level `[worked_instance]` table, **not** a runnable `[catalog].operator_chain`, and it self-discloses *"NOT a srmech.dsl runnable chain… verified by tests/test_triality_s3_worked_instance.py (not by run_toml_chain)"* — and that verifying test **is not shipped in the wheel**. The documented order-3-triality ∘ klein4-flip conjugation cascade **validates bit-exactly in Python** (all 4 ops resolve callable). *Coherence note for the rework: to make the Option-1 continuum-instance engine-runnable it needs to be a `[catalog].operator_chain`, not a `[worked_instance]` doc-table — and the verifying test should ship.* (No bug filed.)

### §E — triality maths on RNA: the codon is a BROKEN triality — **DEMONSTRATED (honest NULL + a cross-substrate hit)**

Applying `klein4_triality_cycle` to the F256 §5 nucleotide map (A=0 fixed; **G→U→C→G** base-cycle) on the standard genetic code:
- **NOT a genetic-code symmetry:** only **2/64** codons conserve their amino acid; only **1/22** triality-orbits is AA-constant — the base-cycle **scrambles** the amino-acid assignments. So the genetic code is **not triality-symmetric**; it lives in the **Klein-4 (bi-chirality) EC tier** (F260), *not* the k=3 triality tier.
- **The codon's 3-fold is a BROKEN triality:** the 3 positions are asymmetric (pos-1/pos-2 = information, pos-3 = the wobble/redundancy register, F256 §5 / F260) — a *broken* position-triality, not a symmetric one.
- **Clean orbit structure:** 64 = **21 triality-triples + 1 fixed** (AAA → Lys, the all-fixed-base codon).
- **Orthogonality CONFIRMED at the RNA scale (= §A):** the inner base-triality (sector-cycle within a position) and the outer position-roll (across the 3 positions) **commute on all 64 codons** — two distinct, orthogonal three-folds co-resident in the codon, exactly §A.
- **CROSS-SUBSTRATE MATCH:** the codon's broken triality (pos-1,pos-2 info / pos-3 wobble) is the **same shape** as the CMB's broken triality (TT ≫ EE ≫ BB) — both are **broken triality where the breaking pattern IS the code/signal** (the widen-2 phase-transition lock: symmetry-breaking = which member of the triple is selected). *Honest: the result is map-relative — the triality-fixed base is whichever maps to sector 0 (A here).*

---

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (Q1 resolution, A₄ closure, harness, RNA broken-triality) / PARTIAL (rc19 toml = doc-instance). Single-model / no-twin. No-magic (A₄ order-12 = V₄⋊C₃, the {1:1,2:3,3:8} signature, the 21·3+1 codon partition are attested-to-structure A; the 2/64, 1/22 are measured B). Class-K (no `abs()`; comparisons via `klein4_similarity`). CAD-ban. No srmech bug filed (rework directive; rc19-toml + C-peer are honest coherence notes). Resolves F256 §0.2/§0.6 (Q1) + F257 §6/Gap B (hyper-loop → A₄). Gap A (directed eigen-op) still open. Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv` outside source tree. Provenance: wf_ea37acca (4 agents, 247k tok). Ties F260 (genetic code = Klein-4 EC) + the CMB broken-triality (the triality-CMB extension, teed up).
