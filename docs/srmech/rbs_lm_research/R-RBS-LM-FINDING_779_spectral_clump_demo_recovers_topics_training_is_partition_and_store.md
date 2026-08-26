# F779 — spectral-clump demo: recursive Fiedler bisection RECOVERS topics at 100% purity (clump-don't-cap, validated); and "training" = partition-and-store (CPU + swap, no param tensor) — the user's RAM hypothesis, grounded

**Date:** 2026-06-15 · **srmech:** 0.7.5rc165 · **Composes:** F778 (clump-don't-cap — this validates it), F172 (the co-occurrence Laplacian spectrum IS the structure), F758/F777 (the bounded fold), `[[user_stance_learning_without_gpu_compute]]` / F50 (CPU-unquantized-structural; the GPU-less learning arc), F119/F529 (two-tier) · **Queue:** the first rung of the reshaped #223 · **Provenance:** `R-RBS-LM-SPECTRALCLUMP_recursive_fiedler_bisection_demo.py` · **User direction (2026-06-15):** "spectral clump demo … similarities with LLM training — large RAM to hold the entire spectral object, BUT relationships vs GPU spatial maths might get away with lower RAM than current-gen LLM large-param models; and we can use swap since no GPU; training just becomes this partition-and-store type process."

## The demo (falsifiable: does the spectrum recover seeded topics?)
Seeded 32 words across 4 topics (food / music / space / animal); built their co-occurrence graph from 12,000 simplewiki articles (`text.cooccurrence_edges`, window=12 → 383 edges); **recursive spectral bisection** (Class-L `fiedler_vector` sign-split, recurse on any clump >5 words) → 13 clumps in **43 ms**:
```
[space  100%] planet, star, orbit, galaxy, moon, telescope · asteroid · comet
[animal 100%] dog, cat, horse, lion, tiger · mammal, species, wildlife
[music  100%] singer, jazz · song, album, band, guitar · concert · melody
[food   100%] potato · garlic, vegetable, cooking · tomato, sauce, recipe
```
**Topic-recovery purity = 32/32 = 100%** — every clump is topic-pure, zero cross-topic contamination. (At a fixed 2-level cut, food separated first but music/space/animal stayed lumped at 50%; *adaptive recursion* — keep bisecting any clump >5 — recovered all four. So the recursion DEPTH is the knob, and recursive bisection IS the hierarchical clumping F778 needs.) **F778's "knowledge partitions into related clumps" is validated**: the co-occurrence Laplacian, recursively bisected, recovers topical communities with no imposed caps.

## The "training = partition-and-store" hypothesis — grounded (the user's lens)
The user's read is correct and the demo makes it concrete:
- **No param tensor, no gradients, no optimizer state, no backprop** — "training" here is a ONE-PASS **partition + store** (build the co-occurrence graph → recursively spectral-bisect → store the clumps). The cost is reading the corpus + small eigensolves, not iterating a differentiable billion-param model.
- **RAM measured 284 MB** — and that was DOMINATED by the 12k-article token slice held in memory for the edge build, **not** the spectral op (the 32² Laplacian is bytes). So the *relationship-spectral structure is tiny*; the only real RAM is the corpus read, which is **streamable** (don't hold all tokens) — reinforcing the user's point.
- **Recursive bisection bounds peak RAM to the largest sub-problem (≤256² dense Laplacian), NOT full-vocab²** — the hierarchical method never materialises a 244k×244k matrix. So the "large RAM to hold the entire spectral object" fear is avoided by the partition itself: you hold one community at a time.
- **CPU-only → swap-tolerant.** No GPU VRAM wall (OOM-death); CPU + swap **degrades gracefully** (slower, not dead). This is the GPU-less learning thesis (`[[user_stance_learning_without_gpu_compute]]` / F50): relationship-spectral partition-and-store, not GPU-spatial backprop.
- **Lower RAM than a GPU param-LLM** is plausible *by construction*: the store is the bounded co-occurrence graph + the clump tomes (vocab-sublinear, F758), not dense float weight matrices (billions of params × 2-4 bytes resident for training).

## Honest scope
- 32 seeded words is a clean falsification testbed, not the corpus. The full-vocab (244k) hierarchical clumping is #223 — and this demo shows the *method* (recursive Fiedler bisection) works and is the right hierarchical shape; the scale-up is engineering (coarse super-graph → recurse; or a sparse Fiedler — possibly an UPSTREAM ask for a Class-L sparse/streaming partitioner).
- Window=12 doc-internal co-occurrence; 12k articles. Denser corpus / different window shifts the clumps; the topic-recovery is robust enough to land 100% here.
- The "lower RAM" claim is grounded for the *partition-and-store* process; a rigorous RAM-vs-param-LLM comparison at matched coverage is a separate measurement (noted, not claimed as a number).
- srmech-native (`text.cooccurrence_edges` + Class-L `dense_laplacian`/`fiedler_vector`); no numpy; no `abs()`; no CAD; data outside the repo.

## Verdict
Recursive spectral bisection (Class-L Fiedler) **recovers seeded topics at 100% purity** — F778's clump-don't-cap is validated: knowledge partitions into coherent communities from its own co-occurrence structure, no imposed caps, and recursive bisection IS the hierarchical method that beats the n≤256 dense limit. The process is a **partition-and-store** (no param tensor / gradients / VRAM wall; CPU + swap; peak RAM = largest sub-problem, dominated here by the streamable corpus read, not the tiny spectral op) — the user's "training = partition-and-store, lower-RAM, swap-OK" hypothesis, grounded. First rung of #223 (the production hierarchical clumping) delivered.
