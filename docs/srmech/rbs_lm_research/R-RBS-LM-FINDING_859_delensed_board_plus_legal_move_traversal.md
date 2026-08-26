# F859 — De-lensed board (item 2) + legal-move traversal (item 1): the syzygy field is navigable. Removing the top-30 gravitational-hub concepts (de-lens, F853 about-mode applied to the BOARD layout) cleans the board to **5 domain-cells** (time-scaffold / antiquity-myth / computing / windows / liverpool) — the "the/and/war/list" noise of F858's hub-cell is gone. **Legal-move traversal works**: connecting two concepts in different cells is a path whose cell-sequence follows only legal syzygy adjacencies (`december→state→computer` = cells [0]→[2], every cell-step legal). Honest residual: cell 0 is still a *time/scaffold* hub most paths route through (via "state") — the mass-effect isn't fully removed by top-30 de-lens. srmech Class-L, live 0.8.2, PR #687.

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `/tmp/board2.py` (`srmech.amsc.laplacian.{dense_laplacian, symmetric_eigendecompose}` + BFS) on 2,000 articles' curated edges, v082 · **Composes:** F858 (the board + shaped syzygy), F853 (de-lens = about-mode, for the board which IS a meaning-structure), F849/F850 (the hub = masses), F778 (clump don't divide), F856 (the arc) · **User direction (2026-06-18):** "each of those three items" (legal-move traversal + de-lensed re-layout + figure).

## Item 2 — de-lensed board (top-30 hub concepts removed)
| cell | domain (top concepts) | grid (x,y) | weight | role |
|---|---|---|---|---|
| 0 | december, july, state, north, october, system | (−0.123,−0.307) core | 10,604 | time/scaffold (residual hub) |
| 1 | ancient, mythology, greek, sun | (−0.129,−0.337) core | 7,078 | antiquity / myth |
| 2 | computer, mario, internet | (−0.143,−0.376) core | 2,968 | computing |
| 3 | windows | (−0.462,+0.765) **outlier** | 455 | computing satellite |
| 4 | liverpool | (+0.857,+0.255) **outlier** | 291 | place/sport satellite |
Cleaner than F858's 6-cell board (the generic-word hub collapsed); antiquity+myth merged sensibly; satellites still pushed out by the alignment embedding. De-lensing the BOARD (a meaning-structure) is the right move (F853 about-mode) — distinct from the within-cell WALK, which keeps the full metric.

## Item 1 — legal-move traversal (the field is navigable)
Legal moves (top): 0↔1 (7019), 0↔2 (2880), 0↔3 (414), 0↔4 (291), 1↔2 (53), 2↔3 (35). Connecting two concepts in different cells via the shortest concept-path, then mapping to its cell-sequence:
- `december → computer`: cells [0,2], **every cell-step legal = True** (path: december → state → computer)
- `december → ancient`: cells [0,1], **legal = True** (december → state → ancient)
- `december → liverpool`: cells [0,4], **legal = True** (december → state → liverpool)
**Movement on the board is meaningful** (each cell-transition is a legal syzygy adjacency — F856's "a move means something because the field is pre-arranged"). Residual: all three route through cell 0 ("state") — the scaffold-hub is the connective tissue (the mass still bridges); diversifying needs deeper de-lensing or per-domain sub-boards.

## Verdict / next
The de-lensed syzygy field (item 2) is navigable by legal moves (item 1); the figure (item 3) renders it. The field + legal-move traversal validate the board model on the curated relationships. Next: deeper de-lens (drop date/scaffold hubs too) so paths diversify off cell 0; and compose with the forces/scale lenses (F856 all-lenses stance). Framework reading + Class-L; evaluate by groundedness.
