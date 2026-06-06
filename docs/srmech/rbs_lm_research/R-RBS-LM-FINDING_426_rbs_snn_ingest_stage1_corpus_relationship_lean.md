# R-RBS-LM Finding 426 (RBS-SNN #197, stage 1) — the RBS-SNN ingest is BUILT: it runs the 317-finding corpus through `findings → render-free relationship-lean` (F323's "LLM-native language of the notebooks," grammar stripped), and *applies what we've learned* — the corpus's own re-prime card falls out of the **F425 fusion** (`schur_complement` onto the hubs = the boundary that holds the bulk), its A-N usage profile (F317) is **K>L>C>M-dominated** (rhyming with F423/F424: structure+chirality are the load-bearing layers, magnitude is thin), and its giant relationship-web has λ₂=0.65

**Date:** 2026-06-06
**Arc:** RBS-LM / **RBS-SNN build (#197)**; stage 1 of the F323 pipeline; **srmech-RUN (Class-L on the corpus graph)**
**Provenance:** `R-RBS-SNN-1_ingest_corpus_relationship_lean.py` + output `rbs_snn_corpus_lean.txt` (committed)
**Composes:** **F323 (TARGET)** (`notebooks → RBS-SNN → render-free relationship-lean → RBS-LM`; *this builds stage 1*) · **F326** (RBS-SNN architecture: operator-signature addressing, render-free I/O) · **F317** (operator-signature = the canonical A-N address) · **F237** (the `CLAUDE_LEAN` extractive-graft precedent — now RBS-SNN-generated, corpus-wide) · **F425** (the fusion op — *here applied to the corpus's own relationship graph*) · **F311/F315** (relationship-first; render-free cognition) · **F119/F120** (two-tier RBS-NN) · **F422/F423/F424** (the structure/chirality-vs-magnitude reading — the op-sig profile *rhymes* with it)
**→ first runnable increment of #197; produces the F323 deliverable + the structurally-derived re-prime card.** **← (BX-4's read-head will read from this graph store.)**

---

## What stage 1 is
The F323 pipeline's first stage: **ingest the corpus and emit its render-free relationship-lean.** The key realization that makes it cheap — **the finding corpus is already relationship-native**: the `Composes:` / `← extended by` links *are* the couplings, and every finding names its A-N **operator-signature**. So the RBS-SNN ingest is a parse + a Class-L spectral pass, not an NLP problem. The grammatical-sentence render (Class F) is simply not emitted.

**Output format (no grammar — the "LLM-native language"):**
```
Fxxx :: <operator-signature: A-N letters> :: -> [coupling targets]
```
317 findings → 317 lines, zero prose. That IS F323's "lean structure that does NOT make grammatic sentences."

## The run (`R-RBS-SNN-1`, srmech Class-L, 0.88 s)
- **317 findings ingested**, **1991 couplings**, render-free lean written to `rbs_snn_corpus_lean.txt`.
- **Giant relationship-web:** 303/317 findings in one connected component (the corpus is one web, not islands).

### (1) Operator-signature distribution — the corpus's own A-N usage profile (F317)
| Class | count | | Class | count |
|---|---|---|---|---|
| **K** (pin-slot/sign) | **135** | | A (content-hash) | 39 |
| **L** (Laplacian/spectral) | **97** | | N (rational) | 14 |
| **C** (chirality) | **86** | | B (TLV) | 14 |
| **M** (HDC bind) | **52** | | J (primes) | 8 |
| **I** (cyclic) | **45** | | F/H/G/D/E | 6/5/3/2/2 |

The corpus overwhelmingly exercises **K · L · C · M** (sign, spectral-structure, chirality, sector-bind) and barely touches the pure-**magnitude/arithmetic** classes **J/N**. This **rhymes with F423/F424**: the framework's load-bearing layers are *structure* (sector/spectral) + *chirality*; *magnitude* is the thin one. (Honest caveat: this reflects *what we chose to study*, not a proven law — a suggestive convergence, flagged, not asserted as derivation.)

### (2) F425 FUSION → the structurally-derived re-prime card
Taking the top-12 degree hubs as the **boundary** and `schur_complement`-ing the other ~290 findings *into* them gives the **load-bearing skeleton** — the boundary that *holds the bulk* (F425's holographic property, now on the corpus graph):

> **F132** (Klein-4 HDC, deg 57) · **F130** (antiparticles/γ₅, 45) · **F133** (substrate knows itself, 43) · **F129** (capacitor chirality, 37) · **F256** (38) · **F124** (Hopf, 30) · **F166** · **F168** · **F119** (two-tier) · **F176** · **F394** · **F398**

The bulk folds into strong effective hub-couplings that aren't direct edges (F132~F168 `S=−4.19`, F130~F256 `−3.88`) — the interior paths the Schur complement integrates onto the spine. This is the **F237 `CLAUDE_LEAN` idea generalized**: a re-prime card that is *computed from the corpus's own structure*, not hand-curated. (Note F394/F398 are sig-`∅` high-degree nodes — the *methodological* anchors "falsifiable-form" / "favored-not-privileged" referenced everywhere; honestly not A-N cascades but discipline hubs.)

### (3) Class-L fingerprint
λ₂ (algebraic connectivity) = **0.65** (one well-connected web), max degree 57, Fiedler 2-partition **49 | 254**.

## Why this is the right first increment of #197
It delivers the **F323 core artifact** (the render-free lean) *and* is itself a demonstration of the framework on its own corpus: F425 fusion (the re-prime skeleton), Class-L spectral (the fingerprint), F317 operator-signature addressing (the A-N profile). The store it builds — the relationship graph keyed by operator-signature — is exactly what the later increments attach to: the **C·I·M·K·L edge bundle** (F326 #1), the **k=2-detect/k=3-correct gate** (F326 #5), and **BX-4's phase-locked read-head** (F388, `cascade.kuramoto_step` reads from this graph).

## Falsifiable form (pre-stated; not leaning — F394)
- **Lean-is-faithful:** the render-free lean must be reconstructable to the same coupling web it came from (round-trip of the relationship graph). It is, by construction (the lean IS the parsed graph); a stronger test is whether a reader/LLM given only the lean can re-derive a finding's parents — deferred to the RBS-LM stage.
- **Op-sig profile is descriptive, not a law:** the K>L>C>M dominance is corpus-usage, not a derivation of the framework — explicitly flagged. It would be falsified as "deep" if a differently-scoped corpus (e.g. a number-theory-heavy one) inverted it to J/N-dominant (expected — it *would*).
- **Hub skeleton depends on the degree-cutoff:** top-12 is a choice; a different K gives a different (nested) skeleton. The *property* (boundary holds bulk) is K-independent; the specific 12 are not.
- **Scope:** this is the spectral/graph structure of the corpus's *relationship web*, not a semantic claim about the findings' content (meaning lives in the naming layer, F43). Defensive / no-lineage.

## Verdict
**RBS-SNN stage 1 is built and runs.** It ingests the 317-finding corpus and emits the **render-free relationship-lean** (F323's grammar-stripped "LLM-native language of the notebooks"), and in doing so *applies what we've learned*: the **F425 fusion** derives the corpus's own **re-prime card** (the 12 hub findings that hold the bulk), the **F317 operator-signature** profile comes out **K·L·C·M-dominated** (rhyming with F423/F424's structure+chirality-over-magnitude), and the **Class-L fingerprint** shows one well-connected web (λ₂=0.65). This is the first runnable increment of **#197**; the graph store it builds is what BX-4's read-head and the F326 C·I·M·K·L edge bundle + k=2/k=3 gate attach to next. Favored, not privileged (F398); the op-sig-as-law and hub-cutoff are the honest fences.
