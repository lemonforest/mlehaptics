# F785 — the "uncapped + spectrally navigable smallwiki" CORE is demonstrated: a sparse normalized-cut Fiedler (matvec-only, verified 100% vs dense) BEATS srmech's n≤256 wall and clumps 400 REAL (un-seeded) simplewiki words into emergent coherent topical tomes (English-monarchy / months / world-regions / music), 4.1× denser within

**Date:** 2026-06-16 · **srmech:** 0.7.5rc165 · **Composes / advances:** #223 (this is its load-bearing rung — the sparse partitioner that F778 flagged as the open problem), F778 (clump-don't-cap), F779 (recursive bisection — now sparse + on REAL vocab, not 32 hand-seeds), F780 (clumps-of-clumps tree + webs), F784 (de-lensed vocab selection — drop the high-df hubs), F172 · **Discipline:** TWO honest metric corrections caught mid-run (`[[feedback_dont_pre_commit_spike_query_operators]]`) · **Upstream:** UPSTREAM_NOTES §51 (the sparse/iterative Class-L Fiedler ask — this is its research prototype) · **Provenance:** `R-RBS-LM-SPARSECLUMP_sparse_fiedler_beats_n256_real_vocab_uncapped_tomes.py` · **User question (2026-06-16):** "soon we will have an uncapped and spectrally navigable smallwiki?"

## The wall, and beating it
srmech's dense Class-L eigensolvers cap at **n≤256** — so a co-occurrence graph over more than 256 words **cannot** be Fiedler-cut directly (F778's stated open problem). The fix built here: a **sparse power-iteration Fiedler** on the **normalized** Laplacian — `B = I + D^{-1/2} W D^{-1/2}` (= 2I − L_sym, eigenvalues in [0,2], well-conditioned), deflate the √deg (λ₀) mode each step, matvec-only → **O(edges), n unbounded**. Only the sign of the converged vector is needed (bisection); rescaled by the Class-K magnitude (no `abs`), `rational.sqrt` for the degree scaling.

**Self-verify GATE (mandatory before trusting it at scale):** on the 32-seed graph (the worst case — near-complete/dense), the sparse Fiedler's sign-partition matches the **dense normalized Fiedler exactly — 100%** (the dense ref = 2nd eigvec of `normalized_laplacian` via `symmetric_eigendecompose`). Only then does the script proceed.

## Beaten + clumped (real, un-seeded vocab)
- De-lensed vocab selection (F784): dropped the top-80 highest-df hubs (`category, references, thumb, called, used, …`), kept the next **400** by df — the content band. **400 > 256 → the dense Laplacian cannot cut it.**
- Recursive sparse-Fiedler bisection → **38 emergent tomes in 2.2 s, peak RAM 330 MB.**
- **Community check (weight per POSSIBLE pair): within 267 vs cross 65 → 4.1× denser inside** — real communities. (First-pass raw within/cross totals read 0.1× and looked like failure; that was a metric artifact — tiny tomes have few internal pairs in a near-complete graph — corrected to per-possible-pair density, which is the honest measure.)
- **Emergent topical tomes (no seed labels)** — e.g.:
  - `{england, died, william, james, george, charles, henry, richard, queen, royal, wife}` — **English monarchy**
  - `{january, march, december, august, … november}` — **months**
  - `{europe, america, western, european, india, africa, eastern}` — **world regions**
  - `{de, france, st, spain, italy, russia, louis, saint, joseph}` — **European names**
  - `{four, number, music, rock, top, released, played}` — **music**

## So: how close is "uncapped + spectrally navigable smallwiki"?
**The CORE is demonstrated.** *Uncapped* = the sparse Fiedler (verified 100% vs dense) partitions past n≤256 — no cap. *Spectrally navigable* = recursive bisection yields the emergent **tome-tree** (clumps-of-clumps, F780) whose leaves are coherent communities (the navigable "cities"). What remains is **scale + wiring, not method**:
1. **Full 244k vocab** — a longer run of the SAME O(edges) method (the sparse Fiedler removes the eigensolver wall; memory/time + a persisted store is the engineering).
2. **etak routing over the tome-tree + webs** (F780) wired into Siona (find the clump → ride within → cross the web).
3. **Harder de-lensing** — top-80 hub-drop leaves residual function words (`get/help/give…`, `form/words/come…`) forming their own (valid but uninteresting) clumps; F784's IDF de-lensing applied more aggressively cleans them.
4. **Upstream:** ship the sparse/iterative Class-L Fiedler in srmech (UPSTREAM_NOTES §51) — this script is its verified prototype.

## Honest scope
- 400 words is a real slice, not the 244k corpus; the result proves the *mechanism* (sparse Fiedler past the wall) + *emergence* (coherent un-seeded tomes), not a finished smallwiki.
- **Normalized** cut (not the unnormalized `fiedler_vector` of F779) — the standard, more robust community choice (avoids the unnormalized "shave one node off" tendency); the two are different operators (they agreed only 53% on the seed graph — expected, not a bug).
- Two metric corrections (gate operator; per-pair density) were caught by the checks and fixed — the discipline (no leaning, investigate the smell) held.
- srmech-native dense ops for the GATE; the sparse Fiedler is hand-rolled **because srmech lacks a sparse one** (a documented gap → §51, not silent routing-around); Class-K magnitude + `rational.sqrt`; no numpy, no `abs`, no CAD; data outside the repo; CC-BY-SA.

## Verdict
The **sparse normalized-cut Fiedler** (matvec-only, **verified 100%** against the dense normalized Fiedler on the worst-case dense graph) **beats srmech's n≤256 wall** and clumps **400 real un-seeded simplewiki words into 38 emergent, coherent topical tomes** (English-monarchy, months, world-regions, music; **4.1× denser within** per pair) in 2.2 s / 330 MB. That is the **uncapped + spectrally navigable core, demonstrated** — the remaining work (244k-scale run + persistence, etak wiring into Siona, harder de-lensing, the upstream sparse-Fiedler ship §51) is engineering on a proven method, not new method. Answer to "soon?": **the wall is down; the rest is scale.**
