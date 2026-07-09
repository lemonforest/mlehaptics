# F1176 (the coupling-community PARALLEL-FINDER built + honestly characterized — the low-eigenmode community (the F1172 identity applied to community-finding) selects a **better formula-FAMILY** than raw content-nearest-neighbour: SPECTRAL-community consensus beats RAW-KNN consensus by **+2–3pp** (consistent across runs) with identical family size and consensus threshold, so the spectral structure genuinely pulls in formula-family members that raw overlap under-ranks; BUT for filling a SINGLE lacuna the simple global single-best content-match (F1175c, 0.089) remains best — the spectral-constrained single-best (0.075) can't beat it because constraining the search to a community subset only *removes* candidates the global search sees — so the finder's real value is **family GROUPING** ("which broken fragments are the same formula"), the F1172 low-mode COMMUNITY affordance, not single-lacuna filling, where the direct parallel-match is the right tool; the two affordances are distinct exactly as the arc's structure predicts (community = grouping; direct match = fill)) — **user: "build the coupling-community parallel-finder." BUILT — honest split: spectral wins family-grouping (+2–3pp over raw-KNN), simple global-match wins single-fill.**

**Date:** 2026-07-09 · **srmech:** 0.7.5rc135 · **User direction:** build the coupling-community parallel-finder (the F1175 refinement (a)). · **Corpus (Gutenberg-attested):** 28282 "Egyptian Literature" (Budge — hymns / litanies / Book of the Dead). srmech Class-L (`signed_laplacian` + `symmetric_eigendecompose`); numpy-free; no magnitude-builtin. · **Composes:** F1175 (which reached global-NN 0.086–0.089 and flagged this refinement), F1172 (the low-eigenmode↔recurrence-community identity being applied), F282 (grouping fragments = a next-question tool for the expert). **Honest partial: the spectral community is the right tool for grouping, not for single-fill.**

## What was built

A spectral parallel-finder: for a damaged line (surviving half `S`), take the top-K=140 content-neighbours as a local candidate set, add `S` as a query node, build the coupling graph, Class-L eigendecompose, embed all nodes in the first m=5 low eigenmodes, and take the query's T=12 spectrally-nearest candidates as its **formula-family** — then reconstruct from that family. The clean control isolates the spectral step: **RAW-KNN** and **SPECTRAL-COMMUNITY** use the *same* family size T and the *same* consensus threshold; they differ only in *how* the T members are chosen (raw content-overlap vs nearest in the low-eigenmode embedding).

## Result (150 masked trials; survive half → recover the lacuna)

| method | lacuna-word recall |
|---|---|
| PRIOR (global frequency) | 0.052 |
| **GLOBAL-NN** (single best raw match over all candidates, F1175c) | **0.089** |
| RAW-KNN consensus (T=12 raw content-neighbours) | 0.043 |
| **SPECTRAL-COMMUNITY consensus** (T=12, low-modes=5) | **0.073** |
| SPECTRAL-COMMUNITY → single best-in-family (combined) | 0.075 |

- **Spectral family-selection gain: SPECTRAL consensus vs RAW-KNN consensus = +2.9pp** (this run; +2.0pp the prior run — consistent). Same T, same threshold, so the gain is attributable purely to the low-eigenmode community picking better family members. **The coupling-community finder works — for FAMILY SELECTION.**
- **Single-lacuna fill: the combined (spectral family → single best-in-it) = 0.075 < GLOBAL-NN 0.089** (−1.4pp). Constraining the single-best search to a ~12-member community can only *drop* candidates the unconstrained global search evaluates; if the true best parallel is outside the community, constraining loses it. **For filling one lacuna, the simplest global content-match remains best.**

(Run-to-run recalls fluctuate ~±0.5pp from hash-randomised set iteration affecting the survive/masked split; the +2–3pp spectral gain sits clearly above that noise, the small recalls do not — this is a modest, consistent effect, not a large one.)

## The honest reading — two distinct affordances

The finder does not make single-lacuna reconstruction better, but it *is* the right tool for a different, arguably more useful, question. It maps onto the arc's own structure:

- **Family GROUPING** ("which of these broken fragments are instances of the same formula?") = the **low-eigenmode COMMUNITY** (F1172). Here the spectral finder beats raw content-similarity (+2–3pp) — it groups fragments through the coupling graph, catching family members whose direct overlap is diluted by damage. This is the genuine payoff: a tool that clusters fragmentary lines into their formula-families for an Egyptologist (F282).
- **Single-lacuna FILL** ("what were the missing words of *this* line?") = the **direct parallel match**. Here the simple global single-best content-match (F1175c) is best; the spectral community adds nothing (and slightly hurts by restricting the search).

So the coupling-community structure is for *grouping*, the direct match is for *filling* — the same community-vs-specific split the whole arc has drawn (low modes = communities/EC, F1161/F1172; specific parallel = the operand recovery). And the unique operand still needs the Rosetta k=3 parallel-version EC (F1175) regardless of how well you group or match within one text.

## Verdict / next
**The coupling-community parallel-finder is BUILT and honestly characterized: the low-eigenmode community selects a better formula-family than raw content-KNN (+2–3pp, consistent), so it is the right tool for GROUPING fragmentary lines into formula-families — but it does NOT beat a simple global single-best content-match for filling a single lacuna (0.075 vs 0.089), because constraining the search to a community subset only removes candidates. The two affordances are distinct exactly as the arc predicts: community = grouping (spectral wins), direct match = fill (simple wins), unique operand = the Rosetta k=3 parallel-EC (F1175). NEXT: package the finder as a `siona` fragment-grouping helper (its real use); transliterated-Egyptian + a genuine Rosetta-trilingual operand-EC demo remain the arc's open refinements. Read-independent-verified (isolated spectral-vs-raw control, baseline-controlled); Gutenberg-attested; composes F1175/F1172/F282.**
