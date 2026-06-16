# F786 — harder de-lensing → 30× cleaner communities + etak tome-tree/web NAVIGATION works, and the sparse Fiedler STRESS-PASSES at 1500 words (192 bisections, 0 non-converged) — ready for the §51 upstream ask

**Date:** 2026-06-16 · **srmech:** 0.7.5rc165 · **Composes / advances:** F785 (the sparse Fiedler — this stress-tests it before §51), F784 (IDF = mass-sheet de-lensing — applied to the GRAPH here), F780 (the clumps-of-clumps TREE + cut-edge WEB — both now built + navigated), F778/F779, #223 parts 3+2 · **User direction (2026-06-16):** "do 3 and 2 ... to stress-test the new code before we send it to srmech ... then 4, then after srmech delivers native, do 1." · **Provenance:** `R-RBS-LM-ETAKNAV_de_lensed_tome_tree_web_navigation.py`

## PART 3 — harder de-lensing (three levers) → 30× cleaner communities
Applied all three at K=1500 content words (vs 400 in F785):
1. **drop the top-120 highest-df hubs** (vocab-level);
2. **IDF-weight every edge** by endpoint inverse-frequency `w' = w·(1−df_a/Ndoc)·(1−df_b/Ndoc)` (F784 mass-sheet subtraction applied to the GRAPH → suppress hub-incident edges);
3. **sparsify to each node's top-20 edges** (kills the near-complete-graph artifact that misled F783/F785).

Result: **965,881 raw edges → 25,434** (genuinely sparse), and **community density 30.0× denser inside** (weight per possible pair: within 51.8 vs cross 1.7) — a **7× improvement over F785's 4.1×.** The residual function-word contamination (F785's `get/help/give…` clumps) is gone; the tomes are clean topical/semantic communities. **De-lensing the graph (not just dropping hubs) is what sharpened the communities** — the F784 principle, validated as a clumping pre-process.

## STRESS TEST — the sparse Fiedler holds at 4× the scale
- **192 sub-bisections across a depth-5..13 tree, 0 non-converged (capped).** The normalized-cut power iteration converges everywhere, even on the many small/deep sub-graphs — no tuning, no failures. 6.1 s, 462 MB.
- Gate re-verified **100%** (sparse vs dense normalized Fiedler) at the top of the run — the solver is intact.
- The graph is now **genuinely sparse** (25k edges / 1500 nodes ≈ avg degree 17), which is the *real* O(edges) regime the full 244k vocab will be in — so this stresses the actual production shape, not the near-complete toy.

## PART 2 — etak navigation over the tome-tree + web (F780), working
Recursive bisection now records the **tree** (clumps-of-clumps); cut edges between leaf tomes are the **web**. The etak walk **find → ride → web-hop** runs on real tomes:
- **`political`** → FIND tome #15 (tree path `LLRRLL`, zoom depth 6) → RIDE `{political, party, parliament, democratic, election, majority, victory}` → WEB-hop to `{president, elected, office, egypt, secretary}` via bridge **`president`~`presidential`**.
- **`becomes`** → `{australia, minister, canada, prime, israel, belgium}` (nations+government) → hop to `{writer, composer, politician, historian, engineer}` (professions) via **`minister`~`politician`**.
- **`spanish`** → `{japanese, polish, footballer, portuguese, mexican, argentine}` (nationalities) → hop to professions via **`politician`~`footballer`**.

So all three F780 pieces are exercised: **FIND** descends the tree (the zoom path = the multi-resolution address), **RIDE** returns the coherent within-tome neighbourhood (the "city"), **WEB-HOP** crosses the strongest cut-edge bridge to a related tome — and the bridges are *meaningful* (`minister~politician`, `politician~footballer` are genuine semantic links; `president~presidential` a morphological one).

## Honest scope
- 1500 words is still a slice (the full 244k is #1, after srmech ships the sparse Fiedler native). This validates the *method + the new code* at the genuinely-sparse production shape, not the finished smallwiki.
- simplewiki's mid-frequency band is people/places/politics/occupation-heavy, so the emergent tomes reflect that (biography/geography/government); this is faithful to the corpus, not a bug.
- Some web bridges are **morphological** (`president~presidential`), some genuinely **semantic** (`politician~footballer`) — both are real co-occurrence bridges; a lemmatiser would merge the morphological ones (a downstream nicety, not needed here).
- srmech-native dense ops for the gate; the sparse Fiedler is the F785 prototype (UPSTREAM_NOTES §51); Class-K magnitude + `rational.sqrt`; no numpy, no `abs`, no CAD; data outside the repo; CC-BY-SA.

## Verdict
Harder de-lensing (drop hubs + **IDF edge-weighting** + top-k sparsify) produces a genuinely sparse 1500-word graph whose communities are **30× denser inside** (7× cleaner than F785) — the F784 de-lensing principle, validated as the clumping pre-process. The sparse Fiedler **stress-passes**: 192 sub-bisections, **0 non-converged**, gate 100%. And **etak navigation works** over the tome-tree + cut-edge web (F780): find (zoom path) → ride (coherent tome) → web-hop (meaningful bridge). Parts 3 + 2 of #223 delivered; the new code is **stress-tested and ready for the §51 upstream ask** (#4). Full 244k vocab (#1) waits on srmech shipping the sparse Fiedler native.
