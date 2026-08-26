# Finding 205 — Cross-navigation Part 2: steering a grammar walk with a logic kernel is INDISTINGUISHABLE from a shape-matched random anchor; an honest NULL that confirms F163 §9 (cross-navigation is structural play, not meaning transfer)

**Status:** Honest NULL. The pre-stated H0 was NOT rejected. A diagnostic confirms the null is *informative*, not trivial (the steering genuinely re-routes the walk — it just doesn't help). Consistent with F163 / F165 / MFO §VII.6.20.
**Predecessors:** F165 §6.3 (cross-navigation Part 2 reframed — "grammar(A) walked via logic(B) as structural play over the reference object's kernels"), F163 §9 (the null that reframed Part 2 from meaning-transfer to structural play), R-RBS-LM-53 F44–F50 (flat-spectral degeneracy + DOMAIN anchor required), R-RBS-LM-54f (DOMAIN anchor), R-RBS-LM-54g (closed-loop ride), R-RBS-LM-54k (cross-kernel triangulation — "marginal" across the poetry/prose family), F164 (grammar is substrate-native), F73 (McGuffey grade ladder), MFO §VII.6.20 (epistemic ceiling).
**Empirical anchor:** `R-RBS-LM-148_cross_nav_grammar_via_logic.py` + `r148_cross_nav.ndjson` (11 records). srmech 0.5.0rc18, native ON, seed 20260530, D=8192. Discipline check: **0 HARD**, 0 coverage-gap.

---

## §1 Headline

**Question (ROADMAP live-queue #189):** can a kernel built from one DOMAIN (grammar = A) be navigated / steered by a kernel from another DOMAIN (logic = B)? Does conditioning the eigvec-rank walk in kernel A on a B-derived anchor *change or improve* the walk vs (i) a within-A baseline and (ii) a random-anchor control?

**Answer: No — logic-steering is statistically indistinguishable from a shape-matched random anchor.** The B-anchor (logic-steered) walk lands at Class-M similarity **+0.3286** to the held-out grammar target; the random-anchor control lands at **+0.3217**; the within-A baseline at **+0.3389**. The cross-steering effect Δ(a−c) = **+0.0069** is well inside the 2·SE noise band (**0.0361**). The logic kernel does nothing a random kernel of matched size would not do. **H0 not rejected.**

All three steered conditions sit clearly above the frequency-weighted-draw floor (**+0.2761**) — so the 54g ride machinery *works* (the walk does land near genuine held-out grammar); it is specifically the *logic-derived steering content* that carries no directed signal.

This is the discipline working as intended (per `[[feedback_dont_pre_commit_spike_query_operators]]`: null findings count; the falsifier was pre-stated; a random-anchor control and a random-emission floor were built in; the result was not leaned toward the positive). It is the cross-DOMAIN generalization of F163's null and the across-family analogue of R-54k's "marginal" within-family triangulation.

---

## §2 What was actually run

**Two genuinely different DOMAINS, both real public-domain corpora (not synthetic):**

| Kernel | Corpus | Project Gutenberg | body chars | sha256 (body) |
|---|---|---|---|---|
| **A — grammar** | McGuffey First Eclectic Reader | PG 14640 | 43,060 | `7bb5cf2d6c71…` |
| | McGuffey Second Eclectic Reader | PG 14668 | 99,268 | `1622563e8dc1…` |
| **B — logic** | Lewis Carroll, *Symbolic Logic* (1896) | PG 28696 | 437,577 | `3cfcbf5d4b2a…` |
| | Lewis Carroll, *The Game of Logic* (1886) | PG 4763 | 116,931 | `1527a38021c1…` |

Grammar = the **R-RBS-LM-73 substrate of record** (the McGuffey grade ladder). Logic = genuine syllogism / logical-connective prose (verified in body: *"No son of mine is dishonest; People always treat an honest man with respect" → "Hence it is a Conclusion consequent from the proposed Premisses"*). Carroll's logic texts are the canonical public-domain corpus of worked syllogisms — a real, attestable logic DOMAIN, not a hand-built toy. sha256 of each stripped body is in the NDJSON attestation block.

**Construction (srmech-native throughout):**
- Each kernel = co-occurrence Laplacian eigvec table (**Class L** `dense_laplacian` + `hermitian_eigendecompose`; 160 eigvecs, vocab 160, window 5), each eigvec row's top-21 tokens bundled into a BSC hypervector (**Class M** `hdc.bundle` over `mint_vector`, D=8192).
- A→B **find-cascade** alignment (**Class M** `hdc.similarity`, greedy-unique) gives, for each grammar eigvec, its similarity to its best-matching *logic* eigvec. That per-rank similarity IS the logic-derived steering content.

**The walk (54g closed-loop ride), three conditions — the condition only changes WHICH ranks are walked:**
- **(a) B-anchor-conditioned** — each grammar token's top-3 eigvec ranks are re-weighted by `|eigvec[token]|² × steer_logic[rank]`, where `steer_logic` is the (mean-1-normalized) A→B alignment similarity. Logic's structure steers the grammar walk.
- **(b) within-A baseline** — ranks by `|eigvec[token]|²` alone (the plain 54g dominant-rank ride; no cross anchor).
- **(c) random-anchor control** — same as (a) but `steer_logic` is replaced by a **seeded permutation** of itself (identical weight *distribution*, logic *content* destroyed).
- **floor** — frequency-weighted random emission of matched size (the 54k baseline).

**Metric (pre-stated, srmech-native, Class M):** hold out 12% of the grammar text as 6 probe fragments; run the ride; bundle the top emitted A-tokens into one BSC vector; `metric = hdc.similarity(emit_bundle, grammar_target_bundle)` where the target is the bundle of the held-out fragment's own top tokens. Higher = the steered walk lands closer to genuine held-out grammar.

---

## §3 The pre-stated null and the numbers

**Pre-stated H0 (committed in the NDJSON `prestated_null` record before the verdict):** *the B-anchor (logic-steered) walk is indistinguishable from the random-anchor control — `|metric_a − metric_c|` within the 2·SE noise band — i.e. no real cross-domain steering.* Decision gate: distinguishable **iff** `|Δ(a−c)| > 2·SE` across probes. (The magnitude is the Class-K pin-slot fold `√(Δ²)`, not python `abs()`; the sign is read separately as Class C.)

| Condition | mean Class-M sim to grammar target | ± std (n=6) |
|---|---|---|
| **(a) B-anchor (logic-steered)** | **+0.3286** | 0.0442 |
| **(b) within-A baseline** | **+0.3389** | 0.0490 |
| **(c) random-anchor control** | **+0.3217** | 0.0351 |
| floor: freq-weighted draw | +0.2761 | 0.0448 |

- **Δ(a−c) B-anchor vs random-anchor = +0.0069** — inside the 2·SE band (**0.0361**). **NULL: H0 not rejected.**
- **Δ(a−b) B-anchor vs within-A = −0.0104** — logic-steering is, if anything, *very slightly worse* than just walking grammar's own dominant ranks.
- **A→B mean cross-alignment similarity = +0.0737** — the grammar and logic eigvec tables are nearly **orthogonal** in Class-M space. There is very little shared structure for the logic kernel to steer *with*; that near-orthogonality is itself the mechanism behind the null.

---

## §4 The null is INFORMATIVE, not trivial (diagnostic)

A null is only meaningful if the steering actually *does* something — if (a) and (c) walked the same ranks, the null would be a tautology (steering = no-op). A diagnostic over 86 probe-0 tokens confirms the conditions genuinely diverge:

- logic-steering **changed the chosen top-3 ranks for 31/86 tokens**;
- random-steering changed them for **45/86 tokens**;
- `steer_logic` weight spread is real: min 0.000, max 3.463 (mean 1.0).

So the steering re-routes a third-to-half of the walks — it is **non-trivial** — yet the re-routed emission lands no closer (and no farther) from genuine grammar than a random re-routing does. **The finding is precisely: logic-derived perturbation of the grammar walk is indistinguishable from random perturbation of it.** That is a stronger, cleaner statement than "the steering was too weak to matter."

---

## §5 Why this is the expected shape (convergence, per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`)

| Thread | How F205 connects |
|---|---|
| **F163 §9** | F163 found 28D chirality does not carry substrate-identity and explicitly reframed Part-2 cross-navigation as **structural play, NOT meaning transfer**. F205 is the direct measurement of that reframing across two DOMAINS: structure is perturbed; meaning is not transferred. |
| **F165 §6.3** | named this exact experiment ("grammar(A) walked via logic(B) as structural play over the reference object's kernels"). F205 executes it and returns the null F163 predicted. |
| **R-53 F44–F50** | the DOMAIN anchor is *required* and is supplied by labeling, not by form-reading. F205 confirms the converse: a *foreign-DOMAIN form-kernel* is not a usable navigation anchor — its cross-alignment to grammar is ≈ orthogonal (+0.074). |
| **R-54k** | cross-kernel triangulation was only "marginal" *within* the poetry/prose family; F205 shows that *across* unrelated DOMAINS (grammar vs logic) the cross-kernel contribution collapses fully to the random-anchor level. |
| **MFO §VII.6.20** | form-reading cannot recover substrate-identity; a logic kernel's *form* does not encode a navigation signal for grammar's *form*. The ceiling holds. |
| **F164 / F73** | grammar is substrate-native and the ride lands near real grammar (all conditions ≫ floor) — the machinery is sound; only the cross-DOMAIN steering content is empty. |

The convergence **53 (need an anchor) → F163 (chirality can't be it; cross-nav is structural play) → F165 (the labeled object IS the anchor) → F205 (a foreign-DOMAIN kernel is NOT an anchor)** is the proof shape: each result tightens where substrate-identity can and cannot come from.

---

## §6 What this finding DOES claim

- In a seeded, controlled, held-out test, **steering a grammar (A) eigvec-rank walk with a logic (B) kernel is statistically indistinguishable from steering it with a shape-matched random anchor** (Δ = +0.0069, inside the 2·SE band 0.0361).
- The null is **informative**: the steering genuinely re-routes 31/86 sampled token-walks; it simply yields no directed benefit over random re-routing.
- The grammar and logic eigvec tables are **near-orthogonal** in Class-M space (A→B cross-alignment +0.074) — the structural reason there is nothing for logic to steer *with*.
- The ride machinery is **sound** (all three steered conditions ≫ the frequency-draw floor); the empty result is specific to the *cross-DOMAIN steering content*, not the method.
- This **confirms F163 §9 operationally**: cross-navigation across DOMAINS is structural play, not meaning transfer; and **extends R-54k across the family boundary** (marginal within-family → fully collapsed across-DOMAIN).
- Result is fully srmech-native (Class L Laplacian + Class M BSC bundle/similarity + Class A content-hash), discipline-clean (**0 HARD**), seeded/reproducible, with both corpora attested by sha256 and Project Gutenberg ID.

## §7 What this finding does NOT claim

Per MFO §VII.6.20 + `[[feedback_no_lineage_claims_in_notebook]]` + `[[feedback_trauma_informed_defensive_scope]]`:

- Does **NOT** claim logic and grammar are unrelated *in general* — only that THIS form-kernel cross-steering carries no directed signal at this scale/construction; a different anchor mechanism (e.g. the F165 *labeled* object) is a different question.
- Does **NOT** claim cross-navigation is impossible — it claims *form-kernel steering across these two DOMAINS* is at the random-anchor level; per F163 §9 the legitimate framing was always **structural play**, and that is what was measured.
- Does **NOT** claim the +0.33 absolute similarity is a meaningful "grammar recovery" number — it is a within-construction comparison quantity; only the *contrast across conditions* is load-bearing.
- Does **NOT** make any claim that "logic transfers meaning into grammar" or vice versa — no semantic / doctrinal / truth claim; both texts are **structural test-objects** (Carroll's logic is used purely as a co-occurrence DOMAIN, not as a reasoning oracle).
- Does **NOT** establish that a larger logic corpus or a richer alignment (multi-step / triangulated per 54j/54k) could not change the result — it tests the direct single-anchor steer; a triangulated re-test is an open thread (§8).
- Does **NOT** bear on capacity bounds or the §VII.6.20 family-routing result (separate axes).

---

## §8 Open threads this finding opens

1. **Triangulated cross-steer** — re-run with the 54k T2/T3 (additive / multiplicative) blend or the 54j G4 geometric-mean gating instead of a single-anchor multiplicative steer; does any composition lift Δ(a−c) above the 2·SE band? (Prediction from R-54k: still marginal-to-null across DOMAINS.)
2. **Within-family vs across-DOMAIN gradient** — interpolate: grammar↔grammar (F73 ladder) vs grammar↔logic (here) vs grammar↔poetry; is cross-steer benefit monotone in A→B cross-alignment similarity? (A→B = +0.074 here is the low end.)
3. **Labeled-anchor contrast** — the F165 result shows the *labeled* multi-kernel object IS a working anchor; quantify how much the label adds over the (here-null) form-kernel steer, on the same grammar/logic pair.
4. **Reverse direction** — logic(B) walked via grammar(A); by near-orthogonality the null should be symmetric, but the asymmetric corpus sizes make it worth a confirming run.

---

## §9 Cross-references

- `R-RBS-LM-148_cross_nav_grammar_via_logic.py` (the experiment; 0 HARD)
- `catalogs/rbs_lm_substrate/substrate_measurements/r148_cross_nav.ndjson` (11 records: attestation / prestated_null / cross_alignment / conditions / 6× per_probe / verdict)
- F163 (chirality null; §9 reframed Part-2 as structural play) · F165 (the labeled multi-kernel object IS the DOMAIN anchor; §6.3 named this experiment)
- R-RBS-LM-53 SUMMARY (degeneracy + DOMAIN-anchor F44–F50) · R-RBS-LM-54f / 54g / 54k (DOMAIN anchor / ride / cross-kernel triangulation) · R-RBS-LM-73 (McGuffey grade ladder — grammar substrate of record) · F164 (grammar substrate-native)
- MFO §VII.6.20 (epistemic ceiling)
- Corpora: Project Gutenberg PG 14640 + 14668 (McGuffey Readers, public domain), PG 28696 + 4763 (Carroll, *Symbolic Logic* + *The Game of Logic*, public domain) — sha256-attested in the NDJSON
- `[[feedback_dont_pre_commit_spike_query_operators]]` (null findings count; pre-state the falsifier; random control) · `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` (convergence is the proof shape) · `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8, 1M). Cross-navigation Part 2 — grammar(A) walked via logic(B) — returns an honest NULL: steering a grammar eigvec-rank walk with a logic kernel is statistically indistinguishable from a shape-matched random anchor (Δ = +0.0069, inside the 2·SE band 0.0361), while both stay well above the frequency-draw floor. A diagnostic confirms the null is informative (the steering re-routes 31/86 sampled walks — it just doesn't help), and the near-orthogonal A→B cross-alignment (+0.074) is the structural reason there is nothing for logic to steer with. This is the cross-DOMAIN generalization of F163's null and the across-family analogue of R-54k's marginal within-family triangulation — and it operationally confirms F163 §9: cross-navigation across DOMAINS is structural play, not meaning transfer. Both corpora are real, public-domain, sha256-attested; Carroll's logic is a structural co-occurrence test-object, not a reasoning oracle; no doctrinal or semantic claims; structural-only per §VII.6.20. Fully srmech-native (Class L + Class M + Class A); discipline-clean (0 HARD); seeded/reproducible. Per [[feedback_dont_pre_commit_spike_query_operators]]: the falsifier was pre-stated, the random control was built in, and the result was not leaned toward the positive.*
