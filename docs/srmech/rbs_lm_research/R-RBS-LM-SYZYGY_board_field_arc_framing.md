# R-RBS-LM-SYZYGY (arc opening, F856) — the board / syzygy-field model: arrange the clumps in SYZYGY (a pre-planned playing field) BEFORE fixed-frame traversal, so movement *means* something. And the load-bearing stance: knowledge navigation has its OWN DoF-coherence scale — don't commit to one lens; hold ALL of them.

**Branch:** `research/rbs-lm-syzygy-board` (off `research/rbs-lm-rolling-2` @ F855) · **srmech:** 0.8.2 (live) · **Date:** 2026-06-18 · **User direction:** "a research branch that takes the knowledge relationships to navigate and arranges glumps in syzygy before trying a fix frame traversal as a way to have grid and pieces to move like a board game field … movement doesn't mean anything without a pre planed playing field … take this abstractly … it comes in its own scale of DoF coherence … we can't commit to only one idea but need all ideas."

## The core move: the field comes before the move
A chess knight's move is *meaningless* without the board + the other pieces + the rules. In a board game we **arrange information into rules** so that **movement is only defined relative to a pre-arranged field.** So far we've done **free traversal** (the etak walk on the raw metric — it drifts, F849/F851) and **slingshot** (dynamic gravity-assist routing). This arc adds the missing thing: **arrange the playing field first, then move.**
- **Arrange clumps in SYZYGY** = lay the domains (F778 spectral communities) into a *relational configuration* — the board.
  - *astronomical syzygy*: alignment — the clumps lined up by their relations (gravitational/relational alignment sets the field).
  - *algebraic syzygy (Hilbert)*: the **relations among the generators** — the inter-clump dependencies ARE the board's legal-adjacency **rules**.
- **The board** = clumps arranged by relation (the **curated-edge graph**, now 5.78M edges at corpus scale, F854) → a spectral layout (Class-L low eigenvectors = board coordinates). **Pieces** = within-clump concepts. **Moves** = traversal constrained to legal (syzygy) adjacencies.
- **Fix-frame traversal** = *deliberately* fix the board-frame to play. This is NOT a contradiction of "all frames unfixed" (F850) — it is the resolution: the substrate has all frames floating (the asymptote), but **to navigate a task you fix a frame (a board)**, like a game fixes its board. The board is a *chosen* fixed frame; different tasks fix different boards.

## Why this is a distinct lens (and the synthesis stance)
The metric/forces picture (F849–F852) reads knowledge through cosmology/nature: gravity (mass), magnetic (circulation), fractal (scale-free), frames (duality). **But language navigation only *looks like* parts of cosmology — it has its own scale of DoF-coherence (F851: coherence is a DoF; F852: scale-free fractal).** The board model is a *different* lens (discrete rules + a pre-arranged field), complementary to the continuous forces. The load-bearing stance (user direction): **do not commit to one idea.** Abstract-knowledge navigation needs ALL of them together:
- **board / syzygy** → the rules and the pre-arranged field (movement has meaning),
- **forces** (F849/F850) → the dynamics on the field (gravity/magnetic/dark),
- **fractal / scale** (F852) → the field is self-similar; the board exists at every zoom,
- **frame duality** (F850) → which board you fix is a choice; the substrate floats,
- **two-mode + scale-covariant recall** (F851/F853) → read at the mode and scale the move demands.
None alone navigates abstract knowledge; the arc is to compose them, with the board as the layer that makes *movement* well-defined.

## First experiment (proposed, srmech-native, uses the new corpus-scale data)
Build the **board** from the v082 curated-edge graph:
1. **Clump** the curated-edge graph into domains (F778 Class-L communities) — the cells.
2. **Syzygy-arrange** the clumps: spectral embedding of the *clump-graph* (inter-clump edge weights) via its Laplacian low eigenvectors → board coordinates; strong inter-clump edges = legal adjacencies (the algebraic-syzygy rules).
3. **Show the board**: domains laid out by relation + the legal-move adjacency — the pre-planned playing field. (Then a later probe: fixed-frame legal-move traversal — connect two distant concepts as a *legal path on the board*, vs free-drift, vs slingshot.)

## Open questions
- What IS the right "syzygy" arrangement — spectral embedding, or the literal Hilbert-syzygy module of the clump-generators (the relation-of-relations)?
- Does board-constrained (legal-move) traversal beat free traversal (drift) and slingshot (gravity-assist) on cross-domain connection?
- How do the **static board (rules)** and the **dynamic forces** compose — is the board the "rules" and the forces the "physics" of the same game?
- The DoF-coherence regime of knowledge vs cosmology: where do the analogies hold and where does knowledge's own scale take over (F851)?

## Status
Arc opened (framing only). No experiment run yet — `consider` stage. Next: the first board-layout probe on the v082 curated-edge graph, on confirmation of scope.
