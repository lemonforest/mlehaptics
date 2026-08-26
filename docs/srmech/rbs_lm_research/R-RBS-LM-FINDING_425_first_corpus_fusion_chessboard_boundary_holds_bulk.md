# R-RBS-LM Finding 425 — the FIRST real corpus fusion: the chessboard grid graph run through the Schur/DtN op (F421) instead of `jacobi_eigvals`. The 28 rim squares are KEPT (operand) and the 36-square interior is FOLDED IN (operator); the decisive holographic test passes — same boundary + different bulk (an interior wall) → different `S` in 576 entries. The boundary genuinely HOLDS the bulk

**Date:** 2026-06-06
**Arc:** RBS-LM · operator|operand FUSION thread (F412→F417→F419→F421 → **F425**); **srmech-RUN (0.7.1 live fusion op)**
**Provenance:** `R-RBS-LM-F425_first_corpus_fusion_chessboard_schur_provenance.py` (committed; 4/4)
**Composes:** **F421** (the Schur/DtN fusion op shipped + verified bug-free — *this is its first corpus application*) · **F412** (the holographic principle IS the framework's fibration; boundary↔spectrum) · **F417** (Class L = the operator|operand seam, but **one-way** — we only ever *projected*) · **F419** (the fusion is where every domain's breakthroughs live) · **F416** (the Mesoamerican cosmogram = fusion attested in the wild) · the **chess-maths notebook** (chess as a spectral lattice) · **#897** (closed; the op)
**→ delivers the "first real corpus fusion": the F417 audit's near-combinations are now runnable as fusions, not projections.** **← (forward-link to be added to F421 as `← extended by F425`).**

---

## The shift this finding makes concrete
Every Class-L cascade our corpus ever ran was a **projection** (F417): a spatial graph (operand) → its eigen-spectrum (operator), with the spatial layout **dropped**:
```
   dense_laplacian(board) → jacobi_eigvals     # 64 anonymous eigenvalues; board positions GONE
```
With the 0.7.1 fusion op (F421), the same corpus object runs as a **fusion** — the boundary is **kept** and the bulk is **folded into it**:
```
   dense_laplacian(board) → schur_complement(rim)   # 28 LABELED rim squares; interior FOLDED IN
```

## The corpus object + the result (4/4)
**The 8×8 chessboard grid graph** (chess-maths "spectral lattice"): 64 squares, rook-adjacency edges. **Boundary** = the 28 rim squares; **bulk** = the 36 interior squares.

| Check | Result |
|---|---|
| **(1) AREA LAW** | `S` is **28×28 = \|rim\|**, not 64 = board-volume — boundary, not bulk |
| **(2) FUSION (bulk folds in)** | **256** effective rim–rim couplings appear that are **not board-adjacent** — interior paths folded into boundary couplings (e.g. `(r0,c1)~(r0,c3)`, coupled *only through* the interior) |
| **(3) HOLOGRAPHY — the decisive test** | add an interior **wall** (remove one inner edge): the rim is identical, yet the boundary `S` **changes in 576 entries** (max `\|ΔS\|=0.00258`). **The boundary `S` is a function of the bulk** ⇒ it *holds* the interior |
| **(4) fusion vs projection** | projection = **64 anonymous** eigenvalues (positions dropped); fusion = **28 positionally-labeled** rim squares + interior folded in — **both operand and operator kept** |

## Why check (3) is the one that matters
A *projection* (`jacobi_eigvals`) of just the boundary subgraph would be **blind** to the interior — change the bulk, the boundary's own spectrum is unchanged. The **fusion** is precisely the operation for which **altering the bulk alters the boundary object**: the 36-square interior is integrated out *onto* the 28 rim squares, so a single interior wall ripples into 576 boundary-matrix entries. That is the **holographic property** (F412) — *the boundary encodes the bulk* — now demonstrated on a real corpus graph, not a toy. It is the exact-arithmetic content of F416's "cosmogram = a spatial frame carrying a cyclic payload, both kept."

## What it unlocks (the F417 audit, now runnable)
F417 listed our corpus's near-combinations — every one was a projection we can now re-run as a fusion:
- **Antikythera**: dials (boundary) ← gear-train (bulk folded in) — the dial face *holds* the gear ratios;
- **chess/DOOM/Othello boards**: a region-of-interest (boundary) holding the rest of the board (bulk);
- **F128/F129 capacitor**, **F132/Path-2 Klein-4 graph**: plate/sector boundary holding the interior.
This finding is the **template**; each is now a `schur_complement(boundary_of_interest)` call.

## Falsifiable form (pre-stated; not leaning — F394)
- **Fusion-not-projection (the F417 guard):** if a use is found where `schur_complement` returns something **independent of the bulk** (the wall-test `ΔS=0`), it would be a projection in disguise. Here `ΔS≠0` on 576 entries — the guard holds.
- **Boundary choice is a modeling choice, not a result:** "rim vs interior" is a natural but chosen split; a different boundary (e.g. a single file, or the four center squares) gives a different `S`. The *property* (boundary holds bulk) is boundary-independent; the specific numbers are not (flagged, not over-claimed).
- **Float vs exact:** run with `exact=False` (float) for the 36-node interior solve; the `exact=True` rational path is available (F421) but heavier here. The qualitative result (area law, bulk-sensitivity) is exact-path-independent; the specific `\|ΔS\|` is float.
- **No semantic claim:** this is the *spectral/graph* fusion of the board lattice. It does **not** claim anything about chess *play/meaning* — meaning lives in the naming layer (F43), not the lattice. (no-lineage / lens-fenced.)

## Verdict
The **first real corpus fusion runs.** The chessboard grid graph — which our corpus only ever *projected* (`jacobi_eigvals`, board dropped) — now *fuses* via the 0.7.1 Schur/DtN op (F421): the 28 rim squares are **kept** (operand) and the 36-square interior is **folded in** (operator), `S` is `\|rim\|`-sized (area law), and the **decisive holographic test passes** — a single interior wall changes the boundary `S` in 576 entries, so **the boundary holds the bulk**. This is the operator|operand fusion (F417/F419) made concrete on a real corpus object, and the holographic property (F412/F416) demonstrated, not just named. The F417 near-combination audit is now a runnable template. Favored, not privileged (F398); boundary-choice + exact-path + the no-semantic-claim are the honest fences.
