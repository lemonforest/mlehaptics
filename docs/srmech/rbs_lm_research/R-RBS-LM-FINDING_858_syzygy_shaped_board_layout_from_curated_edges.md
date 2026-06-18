# F858 — "Syzygy" shaped + the first board laid out from the v082 curated edges. **Syzygy = the relational arrangement of clumps, its two senses being the two parts of a board**: astronomical *alignment* → the GRID (spectral embedding positions the cells), algebraic *Hilbert syzygy* (relations among generators) → the RULES (inter-clump relations = legal moves). Built on the v082 curated [[outlink]] edges: **132 concept-cells → 6 domain-cells** (science / sports / antiquity / mythology / + a hub), spectrally arranged into a grid (core domains clustered, satellites pushed out) with legal-move adjacencies. Curated edges ≫ co-occurrence for clumping (F817 confirmed — clean domains where the F848 Jaccard attempt gave one blob). srmech Class-L, live 0.8.2.

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `/tmp/board_layout.py` (`srmech.amsc.laplacian.{dense_laplacian, symmetric_eigendecompose}`) on 2,000 articles' curated edge-lists from `simplewiki_rawbody_instrument_v082` · **Composes:** F856 (the board/syzygy arc), F854 (the curated edges, 5.78M), F778 (clump don't divide), F817 (curated edges > co-occurrence), F849/F850 (the hub = masses), F853 (about-mode de-lens), R-RBS-LM-55/F77 (relations-of-relations = the algebraic syzygy), Class-L Laplacian · **User direction (2026-06-18):** "board-layout probe now, and please shape the 'syzygy' definition … not new branch, same PR687 rolling branch."

## Syzygy — the shaped definition
**SYZYGY = the relational arrangement of the clumps**; the two classical senses are the two parts of a board:
1. **Astronomical syzygy (alignment) → the GRID (positions).** Clumps *placed* so their relations are geometric: the spectral embedding of the clump-graph (Laplacian low eigenvectors) puts related clumps near/aligned. *Where the cells sit.*
2. **Algebraic syzygy (Hilbert — relations among generators) → the RULES (legal moves).** Clumps as generators of the knowledge module; a syzygy is a dependency `Σ aᵢ·clumpᵢ = 0`. The syzygy *module* = which clump-combinations are dependent/legal = the **legal-move adjacencies**. This is "relations of relations" (R-RBS-LM-55/F77) made into board rules. *Which moves mean something.*
So **board = grid (alignment) + rules (algebraic syzygy)**, both read off the clump-graph's Class-L structure — the pre-planned playing field that makes a *move* well-defined (F856).

## The board (2,000 articles, 132 concept-cells → 6 clumps)
| cell | domain (top concepts) | grid pos (alignment) | inter-clump weight |
|---|---|---|---|
| 0 | the, language, united, states, war, list | (−0.082, −0.245) core | 34,534 (the hub) |
| 1 | computer, water, human, chemical, science, earth, space | (−0.085, −0.269) core | 13,790 |
| 2 | football, cup, league, england, park, season | (−0.090, −0.255) core | 16,353 |
| 4 | ancient, greek | (−0.089, −0.330) core | 4,567 |
| 3 | f.c. | (−0.501, +0.762) **outlier** | 935 |
| 5 | mythology | (+0.848, +0.337) **outlier** | 709 |
- **Grid works**: interlinked core domains cluster; satellites (`f.c.`, `mythology`) are pushed far out — a sensible board layout from the alignment-syzygy embedding.
- **Legal moves (algebraic syzygy, top)**: 0↔2 (15797), 0↔1 (13165), 0↔4 (4188), then domain↔domain (1↔2: 314) and satellite↔parent (2↔3: 160).
- **Clumping is real + domain-coherent** (science / sports / antiquity / mythology) — the curated relationships give clean cells where small-sample Jaccard failed (F848). "Clump, don't divide" holds at the board level.

## Honest notes / next
- **Cell 0 is the gravitational hub** (function-word masses + broad topics, F849/F850) showing up *as a clump* and dominating the legal-move graph. The board layout (a meaning-structure: which domains relate) therefore wants the **de-lensed about-mode read** (F853) — drop the hub/mass concepts so the real domains and their relations separate cleanly. (De-lens the BOARD, which is meaning; never the within-cell walk.)
- **Next probe**: **fixed-frame legal-move traversal** — connect two concepts in different cells as a *legal path on the board* (cell→adjacent-cell along syzygy edges, walk within each cell), vs free-drift and vs slingshot (F850). This is "movement that means something because the field is pre-arranged."
- **Composition** (the all-lenses stance, F856): board = the RULES; forces (F849/F850) = the physics on it; fractal (F852) = the board self-similar at every zoom (cells-within-cells); two-mode/scale-covariant recall (F851/F853/F857) = how you read a move.

## Verdict
Syzygy is shaped (alignment→grid + algebraic→rules) and the first board is laid out from the curated relationships: 6 coherent domain-cells, a working spectral grid, legal-move adjacencies. The field exists; next is moving a piece on it (legal-move traversal) and de-lensing the layout so the hub doesn't dominate. Framework reading + Class-L measurement; evaluate by groundedness.
