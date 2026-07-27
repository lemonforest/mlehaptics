# F1329 — **three queue items cleared on rc349, and each returns a sharper answer than the item asked for.** (#258/#243) *"Make 'resonant asymmetric wave' a measurement"* → asymmetry is now **exactly definable, float-free**, as `asym(A) = |n₊ − n₋|` off `inertia_signature`, and the result is non-obvious: **ℂ is the ONLY balanced rung** (`(1,1,0)`, asym 0) and asymmetry is **non-monotone in dimension** (1, 0, 2, 6, 14). (#231 PKG-3) `genome_content`'s `n_content` is a **true repartition invariant** — **identical across 7 different chromosome partitions** of the same 24 leaves while `n_turns` (25→36) and `n_chromosomes` (1→12) both move. That is exactly the key a streaming reader needs. (#232 RC-1) Scale-invariance is **lane-specific, not global**: the **index lane is EXACT at every dim probed (2…32)**, associativity **dies after dim 4**, and the trace inertia holds its `(1, dim−1, 0)` shape all the way up — **three different scaling behaviours in one tower**.

**User (2026-07-27):** *"do all unblocked in series. check describe() surface on the operations we need to run to also ensure srmech describes them correctly."*

srmech **0.9.0rc349**, clean venv outside the source tree, `HAS_NATIVE=True`, ABI 10. srmech-first throughout — every number comes from a shipped op; no numpy, no float, no `abs()` (magnitude via the Class-K `cascade.magnitude`).

## 0 — the describe() gate, run first `[DEMONSTRABLE]`
`get_tool_schema()` on rc349 carries **511 tools**. Of the 22 ops this work needed, **20 are described**. Two are not: **`cd_add`** (named in rc349's own CHANGELOG as part of the tested ladder surface, its three siblings all registered) and **`separate_winding_curvature`** (our F1321 winding read). Also measured: **`reads_lane` is populated for 9 of 511 ops**, so the rc347 lane axis cannot yet be used for routing. Filed as issue **#1530** (living tracker; the body is the state).

**One of my own errors is recorded there rather than filed against srmech:** a first pass reported "0/18 undescribed" — that was my wrong lookup key. Schema names are **fully qualified** (`srmech.amsc.cascade.inertia_signature`), not bare.

## 1 — #258/#243: asymmetry, defined exactly `[DEMONSTRABLE]`
```
  rung dim | trace (n+,n-,n0) | asym | balanced?
  R    1   | (1, 0, 0)        |  1   | no
  C    2   | (1, 1, 0)        |  0   | YES
  H    4   | (1, 3, 0)        |  2   | no
  O    8   | (1, 7, 0)        |  6   | no
  S    16  | (1,15, 0)        | 14   | no
```
> **ℂ is the only balanced rung, and asymmetry has its ZERO there — it is not monotone in dimension.**

That is the same place order is lost (F1328): **ℂ is simultaneously the balance point of the trace form and the first rung with a negative-square direction.** The two facts are the same `(1,1,0)`.

**The control that stops this being a dimension read:** rc349 ships split-𝕆 at `(5,3,0)` — **same dim 8 as 𝕆, asym 2 vs 6**. Asymmetry separates two dim-8 algebras, so it is reading the table, not the dimension.

**Honest**: this defines the asymmetry of the **trace form**. It is not a wave, not a resonance, and not a subharmonic. It is the exact float-free asymmetry number the arc lacked — **the quantity a resonance claim would now have to be stated against**, which is what #258 asked for and no more.

## 2 — #231 PKG-3: the repartition invariant `[DEMONSTRABLE]`
24 leaves, cut 7 different ways:
```
   1 chromosome  x 24 -> n_turns=25  n_chrom= 1  n_content=24
   2 chromosomes x 12 -> n_turns=26  n_chrom= 2  n_content=24
   3 chromosomes x  8 -> n_turns=27  n_chrom= 3  n_content=24
   4 x 6 | 6 x 4 | 8 x 3 | 12 x 2  -> n_turns 28,30,32,36   n_content=24
```
**`n_content` is identical across every partition while both other counts move.** So a streaming reader can key on it — which is precisely the "render on the fly, no decode cache" requirement (F1247/#231). The cache-free reader now has a stable handle.

## 3 — #232 RC-1: scale-invariance is lane-specific `[DEMONSTRABLE]`
```
   dim | index-XOR shadow | associates | trace inertia | asym
     2 | EXACT            | True       | (1, 1, 0)     |  0
     4 | EXACT            | True       | (1, 3, 0)     |  2
     8 | EXACT            | False      | (1, 7, 0)     |  6
    16 | EXACT            | False      | (1,15, 0)     | 14
    32 | EXACT            | False      | (1,31, 0)     | 30
```
Against the shipped ceilings (`CD_TURN_MAX_DIM=4`, `CD_COMPOSE_MAX_DIM=8`, `CD_ADDRESS_VERIFIED_DIM=64`, `ASSOCIATIVE_ALGEBRA_DIMS=(1,2,4)`):

> **There is no single "scale invariance". The index lane is exact at every dim probed; associativity dies after 4; the inertia keeps its shape forever. Asking "is it scale-invariant?" is under-specified — you must name the lane.**

That is the answer #232 needed and it reframes the item: RC-1 is not one property to establish but three, and two of them are already settled (index exact; associativity bounded).

## Honest scope
- `[DEMONSTRABLE]`: everything above, on rc349, exhaustive over the stated dims and partitions.
- §1's asymmetry is of the **trace form only**. §2 used one synthetic 24-leaf strand at D=64 with one coupling — **not a real corpus genome**, and not a scaling test.
- §3 probed dims 2–32; `CD_ADDRESS_VERIFIED_DIM` is 64 and `CD_DIMS` runs to 256, so the index-lane claim is verified further by srmech than by me.
- **Nothing here builds the streaming reader** — it identifies the invariant the reader should key on. #231 remains open as an implementation.
- The `(1, dim−1, 0)` inertia shape is **definitional** per rc349 (`n₋ = dim − 1` on every shipped rung). Only the split-algebra separation in §1 is a non-dimension read.

Composes **F1328** (ℂ as the rung where order is lost — *now also the balance point*), **F1324** (the metric that picks a seam — *`inertia_signature` does NOT supply it; see #1530 §E*), **F1319** (the three ceilings — now shipped constants), **F1247** (encode once, render on the fly). Generating code: `R-RBS-LM-QUEUE258_*.py`, `R-RBS-LM-QUEUE231232_*.py` (both exit 0 on rc349).
