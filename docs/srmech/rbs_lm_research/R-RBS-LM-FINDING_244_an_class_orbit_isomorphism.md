# Finding 244 — does the SPECIFIC A-N class assignment carry the division-algebra ORBIT structure? First probe: NULL (weak, usage-confounded) — the class↔orbit map stays F243's lens

**Headline:** F243 left an explicit open thread (its §4): the *theorems* (|Im ℍ|=3, |Im 𝕆|=7, the 3 close as a Lie algebra, the 7 carry 7 Fano-line ℍ-copies, dim G2=14) are proven, but that the **substrate-projection triad I/C/J IS Im ℍ** and the **cascade-detection heptad D/E/F/G/K/L/M IS Im 𝕆** is the framework *lens*, not a theorem. This finding runs the first falsifiable probe and **the pre-stated NULL fires**: the corpus's own co-occurrence structure does **not** carry the predicted **vertex-transitivity ("alike") orbit signature** on the blocks — so the operator-by-operator identification **remains a lens**. The F243 size+symmetry match is untouched; what does **not** follow (here) is the class-by-class isomorphism.

**Status:** **DEMONSTRATED** (srmech-native, rc9, bit-attested `response_sha256 = 8211b80e1a8d1183…`, `0 HARD`) for the measured co-occurrence structure + the permutation test. **NULL** verdict on the orbit-transitivity prediction, with an explicit **usage-frequency confound** that makes the NULL *weak* (it locates where the structure *isn't*, doesn't refute the iso). **FRAMEWORK-READING** for what that means. No biology; CAD-ban holds. `[[feedback_dont_pre_commit_spike_query_operators]]` (pre-stated reachable null, no leaning); `[[feedback_no_privileged_primitive_classes]]` (transitivity = the no-privileged-class signature, made testable).

**Predecessor:** **F243** (the Hurwitz-ladder confirmation + the §4 open thread this answers).

---

## §1 The test (falsifiable, pre-stated NULL)

The orbit signature is **vertex-transitivity**: Im ℍ's 3 units are one SO(3)-orbit (no privileged member), Im 𝕆's 7 are one G2-orbit. Transitivity ⟹ **degree-regularity** (every member equally coupled ⟹ low coefficient-of-variation of within-block degree). So: build the A-N classes' **co-occurrence Laplacian** from the findings corpus (the F172 Class-L storage signature — which classes the research invokes together; `dense_laplacian` + `jacobi_eigvals`), then test against a 4000-sample permutation null of random same-size class subsets:
- **H1** — is I/C/J more degree-regular (lower CV) than ≥90% of random 3-subsets?
- **H2** — is D/E/F/G/K/L/M more degree-regular than ≥90% of random 7-subsets?

**Pre-stated NULL (reachable, fired):** *"neither block reaches the ≥90th-pct transitive tail, so the corpus co-occurrence does not carry the predicted orbit structure; the class↔orbit identification stays the lens."*

## §2 Result (67 findings ≥2 classes, 91 co-occurrence edges)

| block | members | within-block degree-CV | transitive percentile | verdict |
|---|---|---|---|---|
| **3 = Im ℍ?** | I, C, J | **0.351** | 80th (I=92, C=103 close; **J=40 drags**) | weak hint, **not** ≥90th |
| **7 = Im 𝕆?** | D,E,F,G,K,L,M | **0.770** | **12th** (K=125, L=109, M=116 dominate; E=19, F=13 weak) | **NON-transitive** |

`H1 = H2 = False` → **NULL.** Class total degrees: K125 · M116 · L109 · C103 · I92 · A81 · N46 · J40 · G28 · B/D/H24 · E19 · F13.

## §3 The confound — why this NULL is WEAK (honest)

Co-occurrence **degree is dominated by raw corpus-usage frequency**: K/L/M/C/I are simply invoked far more often than E/F/D across the research, so the degree-CV measures *usage-uniformity*, **not algebraic orbit-transitivity**. The heptad's non-transitivity is mostly "the project leans on Laplacian/pin-slot/HDC (L/K/M) a lot," a sociological fact about the research, not a statement about 𝕆. So the NULL **does not refute** the class↔orbit iso — it shows that **raw corpus usage is not where the orbit structure (if any) would appear**. A genuine test must control for usage frequency (e.g. usage-normalised coupling, or a conditional/partial-correlation graph) or test an *algebraic* relation among the operators directly (a multiplication/composition table), not a prose co-occurrence count.

## §4 Disposition + the real next step

- The **F243 result stands**: 3=Im ℍ, 7=Im 𝕆 by **size and symmetry** (theorem). 
- The **class-by-class iso stays a lens** (F243 §4) — this first probe gives it no empirical support and (weakly) suggests the corpus's own usage isn't where to look.
- **Honest next step:** build a **composition/cascade-adjacency table** among the 14 operators (which class's output feeds which class's input — a directed *functional* structure, not prose co-occurrence) and test whether the I/C/J and D-M induced structures carry the K3 / Fano incidence. That is the algebraic test; this was the corpus-usage probe that clears the ground by ruling the usage-graph out.

**Files:** `R-RBS-LM-244_an_class_orbit_isomorphism.py` (+ this finding). No ndjson (structural probe, like F243). PR #687 stays draft.
