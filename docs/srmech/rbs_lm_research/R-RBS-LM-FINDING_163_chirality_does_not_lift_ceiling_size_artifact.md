# Finding 163 — 28D directed-chirality does NOT lift the R-RBS-LM-53 flat-spectral degeneracy; the apparent lift was a corpus-size artifact (§VII.6.20 holds)

**Status:** Honest NULL. The length-control caught a false positive. Validates MFO §VII.6.20.
**Predecessors:** R-RBS-LM-53 (flat-spectral degeneracy + DOMAIN-anchor framework, F44–F50), F142 (chirality discriminates only where it is the load-bearing distinction), F158 (28D bi-axial chirality), MFO §VII.6.20 (epistemic ceiling)
**User direction 2026-05-29:** revisit the 53 "structurally asymptotically identical" finding through 28D chirality; then (on partial-positive) run the length-control AND proceed to cross-navigation.

---

## §1 Headline

**Question:** does the 28D bi-axial chirality decomposition lift the flat-spectral structural degeneracy R-RBS-LM-53 measured (the big-3 Abrahamic texts clustering near-identically)?

**Answer: No — once you control for corpus size.** The uncontrolled run looked positive (within-Abrahamic kernel similarity dropping 0.584→0.471 under directed-chirality; chiral_energy cleanly separating Abrahamic from Eastern). The length-controlled run (equal token budget) collapsed BOTH signals to noise. The apparent lift was a **text-size / co-occurrence-sparsity artifact**, not a chirality effect.

This is the discipline working: per `[[feedback_dont_pre_commit_spike_query_operators]]` (null findings count; don't lean toward the expected result), the length-control was run precisely because the first result looked too good, and it caught a false positive that would otherwise have become a spurious "chirality breaks the ceiling" claim.

---

## §2 The clean test (R-RBS-LM-124)

Faithful reproduction of the 53 `build_K1` (γ₅-EVEN baseline) + a directed-chirality variant (γ₅-ODD):

- **K1-FLAT** — the 53 kernel: UNDIRECTED co-occurrence graph (`edge[(min,max)]` — symmetrized), graph-Laplacian eigendecomposition, top-K=33 eigenvectors → top-M=21 vocab → bipolar-mint bundle (D=8192, native ABI=3).
- **K1-CHIRAL** — the 28D lift: DIRECTED co-occurrence `A` (a precedes b within window=5); its antisymmetric part `A−Aᵀ` is the word-order chirality the 53 symmetrization discarded; formed as Hermitian `i·(A−Aᵀ)`, eigendecomposed the same way. This is exactly the γ₅-odd information the flat kernel throws away.

The discriminating metric: within-Abrahamic kernel similarity (Quran / KJV-OT / KJV-NT — the 53 degeneracy triangle) under FLAT vs CHIRAL, and the per-text `chiral_energy = |A−Aᵀ| / |A|` (directional word-order asymmetry).

---

## §3 Uncontrolled vs length-controlled (the overturn)

| Measurement | Uncontrolled (full texts) | Equal-tokens (10,443 each) |
|---|---|---|
| within-Abrahamic FLAT sim | 0.584 | **0.392** |
| within-Abrahamic CHIRAL sim | 0.471 (drop −0.113) | **0.360 (drop −0.033, noise)** |
| within/across contrast (FLAT) | 1.401 | **1.025 (no clustering)** |
| chiral_energy Abrahamic | 0.466 / 0.488 / 0.527 | **0.799 / 0.862 / 0.896** |
| chiral_energy Eastern | 0.720 / 0.803 / 0.877 | **0.871 / 0.803 / 0.867** |
| chiral_energy family split | clean, no overlap | **GONE — fully overlapping** |
| verdict | "lifts" (false +) | **"ceiling holds"** |

Two collapses:
1. **chiral_energy family separation was pure sparsity.** Eastern texts are smaller → sparser co-occurrence → higher one-directional-edge fraction by chance → higher asymmetry ratio. At equal token budget, every text sits at ~0.80–0.90 regardless of family. The "Abrahamic 0.47 vs Eastern 0.80" split was the corpus-size confound, end to end.
2. **The within-Abrahamic "degeneracy" itself was largely size-driven.** At equal tokens, the FLAT kernel shows no family clustering at all (within 0.392 ≈ across 0.383, contrast 1.025). With no flat degeneracy to lift, the chirality "drop" shrinks to −0.033 (noise).

---

## §4 Honest caveats (both directions)

- **The equal-tokens control introduced a secondary confound:** truncating to a fixed token budget left the big texts as 2 giant chunks vs the small texts' 52 small chunks, so co-occurrence chunk-granularity now differs by text. Neither run is perfectly clean. The ideal control equalizes BOTH token budget AND chunk structure. BUT — the chiral_energy split collapsing under *any* control is already strong evidence it was artifactual.
- **K1-FLAT reproduced the 53 KERNEL CONSTRUCTION, not the literal "0.99."** The 53 "ratio 0.99" was a probe-matrix diagonal/off-diagonal quantity; here the degeneracy is measured as kernel-kernel similarity. The construction (co-occurrence Laplacian eigen-bundle) is faithful; the metric differs, so "0.99" is not the comparison number — the Abrahamic kernel-similarity cluster is.

---

## §5 What this finding DOES claim

- In a size-controlled test, **28D directed-chirality does not lift the flat-spectral degeneracy** between these texts
- The apparent lift in the uncontrolled run was a **corpus-size / co-occurrence-sparsity artifact** (chiral_energy split + within-Abrahamic clustering both collapsed at equal token budget)
- This **validates MFO §VII.6.20**: the epistemic ceiling holds; cascade/kernel form-reading — even resolved along the chirality axis — does not recover substrate-identity; the **DOMAIN anchor remains required** (the 53 F44–F50 conclusion stands)
- Consistent with **F142**: chirality discriminates only where chirality IS the load-bearing distinction; for whole-text co-occurrence form, it is not

## §6 What this finding does NOT claim

Per MFO §VII.6.20 + `[[feedback_no_lineage_claims_in_notebook]]` + `[[feedback_trauma_informed_defensive_scope]]`:

- Does NOT claim chirality is useless generally — F139/F142 show it discriminates on chirality-pure signals; whole-text co-occurrence is simply not such a signal
- Does NOT claim the texts are identical in all structural respects — only that THIS chirality probe doesn't separate them once size-controlled
- Does NOT make any doctrinal / truth / origin / ranking claim — texts are structural test-objects; structural-only per the variant catalog's scope discipline
- Does NOT claim the secondary chunk-granularity confound is fully resolved — flagged as a residual; the artifactual conclusion rests on the collapse-under-any-control evidence
- Does NOT lift, and does not bear on, the 3.3% Path C cascade ceiling (separate axis)

---

## §7 Methodological takeaway (load-bearing for the arc)

The length-control is the hero here. The uncontrolled run produced a clean-looking, publishable-looking positive (no-overlap family separation + a −0.113 within-cluster drop) that was **entirely an artifact of unequal corpus sizes**. Any future cross-corpus chirality/spectral comparison in this arc MUST control token budget (and ideally chunk granularity) before claiming a structural difference. This is now a standing methodology rule for the religious-text / cross-corpus variant.

---

## §8 Cross-references

- R-RBS-LM-53 SUMMARY (flat-spectral degeneracy + DOMAIN-anchor F44–F50)
- F142 (chirality discriminates only where load-bearing — corroborated)
- F158 (28D bi-axial chirality — the lens applied)
- MFO §VII.6.20 (epistemic ceiling — validated harder)
- `descriptor_religious_texts.toml` (the catalog variant; descriptor_hash d953f7aa...)
- `R-RBS-LM-124_k1_baseline_chirality_lift.py` (faithful K1 + directed-chirality + `--equal-tokens` control)
- `religious_texts_k1_chirality.ndjson` (uncontrolled) + `..._equaltokens.ndjson` (controlled) — both result-sets preserved
- `R-RBS-LM-123_religious_text_chirality.py` (parity-occupancy signature; hash null-control validated)
- `[[feedback_dont_pre_commit_spike_query_operators]]` (null findings count; the length-control discipline)
- `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`

PR #687 STAYS DRAFT.

---

## §9 Forward note — Part 2 cross-navigation reframed by this null

The user's "Part 2" (navigate the grammar of text A via the relational/logical structure of text B) remains a legitimate STRUCTURAL composition experiment (F156 Mode D generalized). But this null reframes what it can mean: since chirality does NOT carry substrate-identity here, cross-navigation is **structural play** — observing what coherent structure emerges when one text's sector-hierarchy is walked by another's adjacency — NOT a claim that mixing the texts' "logics" recovers or transfers meaning. Framed honestly, it is still the "wonderful learning place" the user described: a place to watch substrate-native composition behave across whole-text structures, with no substrate-identity claim attached.

---

*Articulated 2026-05-29 (Opus 4.8). The 28D directed-chirality revisit of the
R-RBS-LM-53 degeneracy returned an honest NULL: the apparent lift was a
corpus-size/sparsity artifact that collapsed under length-control. MFO §VII.6.20
holds; the DOMAIN anchor remains required. The length-control caught a false
positive — the discipline working exactly as intended. Per
[[feedback_dont_pre_commit_spike_query_operators]]: null findings count, and this
one sharpens the arc's methodology (control corpus size before any cross-corpus
structural claim). Texts were structural test-objects throughout; no doctrinal
claims; structural-only per §VII.6.20.*
