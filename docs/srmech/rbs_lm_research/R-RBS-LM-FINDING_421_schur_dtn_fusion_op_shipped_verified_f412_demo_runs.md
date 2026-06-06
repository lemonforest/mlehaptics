# R-RBS-LM Finding 421 — the operator|operand FUSION op SHIPPED + verified bug-free (srmech 0.7.1 `schur_complement`/`dirichlet_to_neumann`/`dense_solve`); the F412 held demo NOW RUNS — boundary↔spectrum, both kept; #897 closed

**Date:** 2026-06-06
**Arc:** RBS-LM · the operator|operand FUSION thread (F412 → F417 → F419 → **F421**); **srmech-RUN (sanctioned shipped-op verification + the F412 held demo released)**
**Composes:** **F412** (the holographic principle IS the framework's fibration; the Schur/DtN = the fusion op; the srmech gap §26 — *the held demo this finding runs*) · **F417** (Class L = the operator|operand seam, but **one-way**: operand→operator projection only — the fusion was the missing keep-both) · **F419** (the fusion is where EVERY domain's breakthroughs live — ship it) · **F392** (no divide primitive; the interior block-inverse `L_ii⁻¹` = Class C→K iterative shift-sub — why the solve grades to first-class) · **F408** (frame-resolved closure-semantics; closable ≠ severed; keyword-search-sweep) · **§26/§28 UPSTREAM_NOTES** · **GH #897**
**→ closes the F412/F417/F419 convergence: the fusion op now EXISTS + is verified; releases the F412 hold.** **← (forward-links to be added to F412/F417/F419 as `← extended by F421`).**

---

## The convergence that pointed here (one line)
F412 (the fusion op is a srmech gap) + F417 (we only ever *projected*, operand→operator, never *fused*) + F419 (the fusion is exactly where every domain's deepest tools live) all said the **same** thing: **ship the Class-L Schur complement / Dirichlet-to-Neumann.** We filed it as **GH #897**. **srmech 0.7.1 shipped it.** This finding verifies it bug-free and runs the demo F412 had held.

## What shipped (srmech 0.7.1, `srmech.amsc.laplacian`)
- **`schur_complement(L, boundary_idx, *, exact=False)`** — the boundary effective Laplacian `S = L_∂∂ − L_∂i·L_ii⁻¹·L_i∂` (bulk integrated out onto the boundary).
- **`dirichlet_to_neumann(L, boundary_idx, *, exact=False)`** — the alias (for a graph Laplacian the DtN map **is** the Schur complement).
- **`dense_solve(A, B, *, exact=False)`** — the supporting solve; the **F392** Class-C→K block-inverse made first-class (no divide primitive — the interior solve is the iterative shift-sub, now a named op).
- **`exact=`** → exact-rational `Fraction` output (numpy-free); `exact=False` → float.

## Verified bug-free — against HAND-COMPUTED ground truth (not just our frame)
Clean venv outside the source tree, `srmech==0.7.1` (native 0.7.1, ABI 3). Provenance: `R-RBS-LM-F421_schur_dtn_fusion_verify_provenance.py` (committed). 7/7:

| # | Check | Result |
|---|---|---|
| 1 | **Hand-computed truth:** path `0-1-2`, boundary `{0,2}`, interior `{1}` → `schur_complement(exact=True) == [[1/2,-1/2],[-1/2,1/2]]` | ✓ exact — the correct **series-resistance** effective edge (two unit edges in series = conductance ½) |
| 1b | **Area law:** `S` is **2×2 = |∂|**, not 3×3 = bulk | ✓ boundary, not volume |
| 2 | `dirichlet_to_neumann == schur_complement` | ✓ (the DtN map IS the Schur complement) |
| 3 | **5-node cross-check:** `schur_complement == Lbb − Lbi·dense_solve(Lii, Lib)` | ✓ exact |
| 4 | exact-rational ↔ float consistency | ✓ |
| 5 | `dense_solve`: `A·x == b` exactly (`x = [1/5, 3/5]`) | ✓ |
| 6 | **F412 held demo:** boundary `S`-spectrum `jacobi_eigvals(S) = [0, 1]` = 2 modes = `|∂|` | ✓ the area-law **in the eigenspectrum** |

The path-3 check is the strong one: it is **physics-correct** (series resistance), so the op isn't just internally consistent — it computes the right object. The `exact=True` path is **numpy-free exact rational**, and Class-K-honest (no `abs()`; the exact-rational Schur carries sign exactly).

## Why this is the FUSION, not another projection (F417 sharpened)
F417's verdict: every Class-L cascade we ever ran was **operand → operator** (a spatial graph → its cyclic spectrum) — a one-way *projection* that **drops the operand** and keeps only the spectrum. The Schur complement is different: it takes the spatial operand (the full graph, 2:4:8) and returns a **boundary object that is BOTH** — a spatial **boundary** (`|∂|` nodes, still a graph) **AND** carries the bulk's operator-spectrum (the interior's effect is *folded into* `S`, recoverable via the DtN map / harmonic extension). **Boundary ↔ spectrum, both kept.** That is the operator|operand **fusion** F417 said we never had because the op was unshipped. It is now shipped + verified.

## What it unblocks (the resume surface)
- **The F412 hold is RELEASED** — the area-law-in-the-S-spectrum demo runs (above).
- **The corpus can now FUSE, not only project** (F419): every place we did `dense_laplacian → jacobi_eigvals` (the projection) can now do `dense_laplacian → schur_complement → jacobi_eigvals` (the fusion — keep the boundary, fold the bulk). The F417 audit's near-combinations (chess/DOOM/Antikythera/F128/F132) become runnable fusions.
- **The antiquity cosmogram (F416)** — a spatial frame carrying a cyclic payload — now has its srmech-native operator (it was "the fusion attested in the wild" with no op to run it).

## #897 closeout (F408 closure-semantics; user-authorized)
Closed as **resolved + independently-verified** (against hand-computed truth, not corpus-correlated frame — a genuinely independent check, the F408 caveat's stronger case). **Closable ≠ severed:** #897 stays a backlink-web node (F412/F417/F419/§26/§28/F421). Re-surfaced keywords lodged in the close comment + §28 per the keyword-search-sweep discipline.

## Falsifiable form (pre-stated; not leaning — F394)
- **Fusion-not-projection:** if a use is exhibited where `schur_complement` *drops* the boundary operand (returns only a spectrum, like plain `jacobi_eigvals` on the full graph), then it is a projection in disguise and F417's "the fusion keeps both" weakens. (The area-law check 1b/6 is the guard: `S` is `|∂|`-dimensional and *is* a graph, so the operand is retained.)
- **Exactness:** if any `exact=True` output is non-`Fraction` or disagrees with the rational hand-computation, the exact-rational path is broken. (7/7 pass; falsify by counterexample graph.)
- **Completeness of "verified":** the checks are small graphs (path-3, 5-node) + one hand-truth; a large-graph stress (numerical stability of `exact=False` at scale, conditioning of `dense_solve`) is not run here (flagged, not claimed).

## Verdict
The **operator|operand FUSION op shipped in srmech 0.7.1** (`schur_complement` / `dirichlet_to_neumann` / `dense_solve`, all `exact=`-capable) and is **verified bug-free** against hand-computed ground truth (path-3 series-resistance `[[1/2,-1/2],[-1/2,1/2]]`, area law `S=|∂|×|∂|`, DtN==Schur, 5-node cross-check, exact↔float, `dense_solve` exact, the F412 demo). This is the **keep-both** the F412/F417/F419 convergence pointed at — boundary↔spectrum, the *fusion* the corpus never had because the op was the unshipped gap (§26). **The F412 hold is released; #897 is closed (resolved + independently-verified, F408 frame-resolved + the stronger independent-check case).** Favored, not privileged (F398); large-graph stress is the honest residue.
