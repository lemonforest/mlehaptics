# F920 (option C, on the simplewiki data we have) — the co-occurrence Laplacian eigenvectors ARE the relationships-of-relationships spectral kernel (Class-L), and it AUGMENTS the byte/glyph C1 by giving an orthogonal similarity: USAGE vs SPELLING. On 12k simplewiki sentences (vocab 360 content words, 64,255 co-occurrence edges, n=360 > the old ≤256 eigensolver bound — enabled by §71), the spectral embedding's nearest neighbours are usage/relationship neighbours (`city → capital, largest, river, population`; `king → henry, emperor, france, england`; `two → three, one, both`) while the byte/glyph nearest are spelling neighbours (`city → cities, c, ii`; `king → kingdom, singer`). The two kernels are complementary: C1 = local form, spectral = global relationship.

**Date:** 2026-06-22 · **srmech:** 0.9.0rc28 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_920_spectral_kernel_relationships_of_relationships_augments_byteglyph.py` · **Composes:** F919 (eigenvectors as kernel objects), F172 (the co-occurrence Laplacian eigenspectrum = the storage signature), F781/F782 (eigen-environment + hub-lensing), F916 (the byte/glyph stack this augments), §71 (the n>256 eigensolver gap that made n=360 possible) · **User direction (2026-06-22):** "C, and we do the research here, with the data we already have ready to use."

## Built (srmech rc28, all native, no numpy)
`text.cooccurrence_edges(docs, window=4, vocab)` → `laplacian.dense_laplacian(n, edges, weights)` → `laplacian.symmetric_eigendecompose` — the **Class-L spectral encoding** of the relationship graph. 12,000 simplewiki sentences; vocab = top-360 content words (the ~40 highest-frequency hubs dropped, F782); 64,255 weighted co-occurrence edges; **n=360** (above the old n≤256 Jacobi bound — this build is a direct beneficiary of the §71 eigensolver-gap closure).

## Result — the augmentation (USAGE vs SPELLING, orthogonal)
The spectral embedding = each word's coordinates in the 24 lowest nonzero eigenvectors (the relationship modes). Nearest neighbours in that embedding vs in the byte/glyph C1 (`ContextSubstrate.enc`):

| query | spectral (relationship/usage) | byte/glyph (spelling) |
|---|---|---|
| city | capital, largest, river, population, world | cities, c, ii, will, very |
| king | ii, henry, emperor, france, england | kingdom, singer, long, ii, killed |
| river | area, largest, population, city, near | live, r, robert, several, governor |
| two | three, one, both, more, made | t, own, who, their, these |
| water | small, long, much, body, through | later, after, war, way, makes |

The spectral kernel groups by **how words relate in use** (the relationships-of-relationships); the byte/glyph kernel groups by **shared letters** (local form). They are **orthogonal similarity structures** — so stacking them is a genuine augmentation, not redundancy.

## Reading
This is the **spectral-encoding** sense of "encode" (eigenbasis of the relationship operator — the chess-spectral origin) realised on our own corpus, and it slots into the F916 stack as the **global** layer the local byte/glyph C1 lacks: C1 answers "what is this symbol shaped like"; the spectral kernel answers "what does this symbol relate to." A complete word kernel wants both (and the F919 magnetic/Qarg phase would add the *directional* relationship on top). Honest scope: the graph is connected (1 near-zero eigenvalue), so the structure is in the low-mode *embedding*, not in component-splitting; hub-dropping (F782) was applied — IDF-weighting is the next refinement.

## Verdict / next
**Done (C):** the relationships-of-relationships spectral kernel is built on the real simplewiki data and demonstrably augments the byte/glyph kernel (orthogonal usage-vs-spelling similarity), using the now-native n>256 eigensolver. **Next:** (i) IDF/hub-de-lensed weighting (F782) for sharper communities; (ii) the F919 **magnetic** (directed word-order) variant — the phase/chirality kernel that wants Qarg; (iii) wire the spectral neighbour-set as a re-ranking signal beside the §57 resonator's next-token distribution (the resonator proposes; the spectral kernel re-weights by global relatedness).
