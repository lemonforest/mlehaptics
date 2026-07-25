# F1320 — **the fiber is a FUNCTION, not storage** — and my "~2× space" claim for the compounded carrier (F1317 §5, filed as issue #1514 §3) was **WRONG**. The sign decomposes exactly as `sign(a·b) = sign(a) ⊕ sign(b) ⊕ F(basis(a), basis(b))` (**0/256 violations**), where **`F` — the Cayley–Dickson cocycle, the fibration's own structure map — is a pure function of the BASIS INDICES (the shadow)**. It is never content. So the 4th bit of an 𝕆 symbol is three different things, and only one of them is irreducible: for **shadow-valued content the tower costs ZERO extra storage** (measured end-to-end, bit-exact), and only **genuine winding** costs 1 bit/symbol.

**User (2026-07-25):** *"we talked about octonion storage causing us to have to go 2x, why aren't the fiber dims derivable from the real octonion fibration? like are we trying to store the fibre when we should be able to compute it?"* — **Correct. We were.**

## The decomposition `[DEMONSTRABLE]`
```
  sign(a·b) == sign(a) XOR sign(b) XOR F(basis(a), basis(b))     0/256 violations
```
`F` is built from the *positive* units alone and depends only on the two **basis indices** — i.e. on the **shadow**. This is not a new discovery so much as a *recognition*: srmech already knows it. `q8.py` derives `F` from `cd_basis_product` and says so explicitly — *"no hand-entered table."* **The fibration's twist was always computed. We just weren't reading the consequence for storage.**

## The 4th bit is three things — only one is content
| component | what it is | cost |
|---|---|---|
| **(a) fibration TWIST** | `F(basis, basis)` — the CD cocycle | **0** — a pure function of the shadow, always |
| **(b) COUPLING sign** | a declared function of `the_one` (F1318) | **one leaf per genome**, not per symbol |
| **(c) DATUM's own sign** | content **iff** the data genuinely carries winding | **1 bit/symbol — irreducible** |

## Measured end-to-end `[DEMONSTRABLE]`
Content: `klein4_encode_bytes(...)` — **shadow-valued, symbols 0..3, the sign bit is structurally absent.**
```
  materialized (store the sign)  ==  rebuilt (recompute it on read)   : True   (bit-exact)
  genome_octonion_holonomy(materialized) == ...(rebuilt)              : True   (identical fold)

  ledger:  full-O 512 bits  |  shadow-only 384 bits  |  V4 content 256 bits
           the_one = ONE leaf for the WHOLE genome, not per symbol
```
**Storing the shadow and recomputing the fiber gives the identical 𝕆-rung read.** The 𝕆 fold over the *rebuilt* element is bit-identical to the fold over the *materialized* one — so the "widest-rung storage" premise was unnecessary for this (dominant) case.

## The honest split — when the sign IS content
```
  genuine-winding content (the directed which-way, F1307/F1309)
  reproducible from the_one alone : False  ->  must be STORED, 1 bit/symbol
```
This is exactly F1307's point standing: the winding sign `b^4` is **invisible to V₄** and klein4 *could not represent it*. When the which-way is real information — the beat-WSD direction, a directed edge charge — it is content, it is irreducible, and it must be stored. **That is the case the extra bit is for, and only that case pays.**

## The correction, stated plainly
> **Not** "the compounded carrier costs ~2× at the V₄ rung."
> **But** "the compounded carrier costs **zero** for shadow-valued content (store shadow, compute fiber) and **1 bit/symbol** for genuinely sign-bearing content — and *only the second case pays*."

The error was conflating **the algebra needs 4 bits** with **the storage needs 4 bits**. The algebra's 4th bit is mostly *cocycle* (computed) plus a *coupling* (stored once); the storage only ever owes the part the data itself carries. **Issue #1514 §3 is corrected by comment.**

## What this changes downstream
- The compounded-carrier design (F1317 §5) is **cheaper than proposed**, possibly free for the dominant corpus case (klein4 text lifted by `the_one`), which weakens the main argument *against* it.
- It sharpens what a genome should actually store: **shadow + one coupling leaf + the winding bits that are genuinely content** — never the cocycle, never a derivable sign.
- It composes with F1318's ledger (`n shadow bits + 1 sign = symbol bits`) by splitting that `+1` into *derivable* vs *content*, which the ledger did not distinguish.

## Honest scope
- `[DEMONSTRABLE]`: the decomposition (exhaustive, all 256 𝕆 pairs), the end-to-end rebuild + identical fold, the non-derivability of injected winding.
- `[SPECULATIVE]`: what fraction of a *real corpus* genome is shadow-valued vs genuinely sign-bearing. The directed-corpus work (F1309) is sign-bearing by construction; plain text is not. **Unmeasured on a real corpus** — and it is the number that decides how much the compounded carrier actually costs in practice. That is the concrete next measurement.
- Not addressed: whether a *partially* sign-bearing strand can store only the non-derivable residue (sign XOR predicted-sign) — a sparse-residue encoding. Plausible, unbuilt.

## Verdict
The user's question was the right one and the answer is that **we were trying to store something the fibration computes**. Generating code: `R-RBS-LM-FIBERISCOMPUTED_*.py` (exit 0).

Composes **F1317** (the compounded carrier — *its cost claim is corrected here*), **F1318** (the constructor / the bit ledger — *the `+1` is now split derivable vs content*), **F1307/F1309** (the winding sign as genuine content — the case that DOES pay), **F1319** (the open-items closeout), `[[feedback_computational_provenance_discipline]]`.

**→ corrects F1317 §5 and issue #1514 §3** — the "~2× space" trade is not a blanket cost; it applies only to genuinely sign-bearing content.

**→ extended by F1321** — the fiber bit this finding says *must be supplied* is **already being computed and then discarded**: `the_one` holds a winding `w` whose `separate_winding_curvature()` yields a `spinor_sign` (−1 on odd holonomy), but `klein4_from_one` produces a **byte-identical coupling for every `w`** (θ moves it; `w` does not). So we throw away the very quantity we then have to re-supply. Same defect class as F1307/F1315/F1320, now at the coupling boundary.
