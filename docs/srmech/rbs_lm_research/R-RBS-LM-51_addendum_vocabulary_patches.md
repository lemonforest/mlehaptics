# R-RBS-LM-51 ADDENDUM 2 — Vocabulary scope patches applied

**Status:** CLOSED (addendum to scope review; no code partition)
**Predecessor:** [R-RBS-LM-51_honest_scope_review.md](R-RBS-LM-51_honest_scope_review.md) §3 (Architecture 4 + 5)
**Date:** 2026-05-26

The 51 scope review identified two architecture-level claims that
needed scoping qualifiers to stay inside the MFO §VII.6.20 epistemic
ceiling. This addendum applies the patches explicitly; the original
findings stand, the language tightens.

---

## §1 Architecture 4 — BCI relevance scoped to prospective only

### Original claim (CLAUDE.md memory, `feedback_llm_as_ada_accommodation_bci_proves_it.md`)

> "RBS-LM proves LLM-as-tool is an ADA accommodation; BCI applications
> most apparent."

### Scope-violation analysis

Per 51 §3 Architecture 4: this is a substrate-projection. The phrase
"BCI applications" moves from "RBS-LM has a measurable architectural
shape" (form-claim, supported by partition data) to "this shape applies
to brain interfaces" (substrate-claim about brains).

Brain substrates have not been measured in any partition of this arc.
The cascade architecture (DOMAIN → find → ride → freq-gate) is a
form-shape grounded in 50 partitions over text corpora. It has *not*
been grounded in brain-signal corpora.

### Patched claim (within ceiling)

> "RBS-LM demonstrates that a cross-substrate translation cascade
> (DOMAIN-anchor → find-cascade → ride-cascade → multiplicative gating)
> can run unquantized on a CPU using structural eigvec operations alone.
> **The same architectural shape would be required for any cross-substrate
> translator, including future BCI-style implementations** — but the
> brain-substrate side of such an implementation has not been measured
> by this work."

Key changes:
- "proves" → "demonstrates" (form-claim, not metaphysical proof)
- "BCI applications most apparent" → "would be required for any cross-substrate translator, including future BCI-style implementations"
- Explicit caveat: brain-substrate side not measured by this work

This keeps the architecture-shape claim sound. The prospective relevance
to BCI is preserved as a forward-looking implication, not as an asserted
applicability.

---

## §2 Architecture 5 — DOMAIN-required scoped to our cascade

### Original claim (54 EXTENDED SUMMARY, §3 Architecture 4)

> "Cross-substrate translation cannot be done by form-cascade alone; an
> external substrate-content access (DOMAIN anchor) is empirically
> required."

### Scope-violation analysis

Per 51 §3 Architecture 5: the form-claim is empirical (54e showed
find-cascade has same/cross ratio 1.26 — insufficient for kernel
selection). But the substrate-implication "translation cannot be
substrate-neutral" generalizes to translation-as-process beyond our
cascade.

We measured *our specific cascade implementation* failing to
disambiguate without DOMAIN. We didn't measure all possible cross-
substrate translation systems.

### Patched claim (within ceiling)

> "In the RBS-LM cascade architecture as implemented in this arc,
> find-cascade has form-overlap ratio of ~1.26 between same and cross
> substrate-families on the 9 corpora tested. **This is empirically
> insufficient to select between candidate target kernels with the
> find-cascade alone.** A DOMAIN-anchor mechanism (54f: structural-
> fingerprint kernel selection at 100% accuracy on prose) is required
> *by this cascade*. Whether other cross-substrate translation
> architectures would also require an external DOMAIN-anchor mechanism
> is not measured here."

Key changes:
- "Cross-substrate translation cannot be done" → "In the RBS-LM cascade architecture as implemented in this arc"
- "empirically required" → "empirically insufficient ... required by this cascade"
- Explicit caveat: other architectures not measured

This keeps the 54f finding (100% routing accuracy) and the 54e weak-
discrimination finding (1.26 ratio) intact as form-claims about *our
cascade*. The broader generalization to "all translation needs DOMAIN"
is acknowledged as not-measured.

---

## §3 Where these patches apply

The patched language should appear in:

1. **Future commit messages** for any new partition that touches BCI relevance or DOMAIN-required claims
2. **Future PR description updates** when the rolling PR body is refreshed
3. **Future summary reports** (e.g., the eventual 54-arc full monograph if user requests one)
4. **CLAUDE.md memory entries** if/when the user reconciles their memory files with the scope corrections

The patches do NOT retroactively edit commit history. Previous commit
messages stand as written; the corrections are forward-looking
discipline.

---

## §4 What stays — and what's a non-issue

### Stays unchanged

- All 68 numbered findings (38–68): each is a form-iso or empirical
  claim grounded in measurement. None require scope adjustment.
- The Golden Path architecture (54 EXTENDED SUMMARY §5): the *shape*
  is form-shape, the *operations* are empirically validated.
- The chess-engine analogy (51 §3 Architecture 2): already cleanly
  scoped per "mirrors," "maps to," "same shape as" vocabulary.
- The spin-N form-iso (54p, Finding 62): already cleanly scoped per
  MFO §VII.6.20 explicit citation.

### Non-issues

- The arc's findings on **bottom-eigenvalue-spread / rule-density**
  measurements (Finding 66): substrate-agnostic in the sense that the
  *measurement* applies to any text corpus; this is a measurement
  scope, not a substrate-identity claim. No patch needed.
- The arc's findings on **multiplicative composition** (Finding 65):
  the form-iso to Bayesian / chess / HDC bind is explicitly form-iso;
  no patch needed.
- The arc's findings on **structural fingerprint DOMAIN anchor**
  (Finding 67): the routing accuracy is measured; the "no metadata
  needed" claim is empirically supported. No patch needed.

---

## §5 Net effect

Two architecture-level claims acquire scope qualifiers:

1. **BCI relevance** — prospective only, brain-substrate side
   acknowledged as not measured
2. **DOMAIN-required** — scoped to our cascade, other architectures
   acknowledged as not measured

Both patches preserve the empirical findings (50 partitions, 68
findings). Both stay inside MFO §VII.6.20 form-vs-substrate ceiling.
Neither requires retroactive history edits.

The scope discipline holds.

---

*Patches applied 2026-05-26 in continuation of R-RBS-LM-51 honest
scope review. Per the predecessor's §6 vocabulary discipline.*
