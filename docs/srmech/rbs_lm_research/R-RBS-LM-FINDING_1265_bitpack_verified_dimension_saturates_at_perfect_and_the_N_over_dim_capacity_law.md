# F1265 — **bit-packing verified** (10 bits/cell, EXACT round-trip, 3.20× smaller than `array('i')`, 5.0× the bundle); **the dimension lever saturates at PERFECT recall by dim=16384** (a ceiling, not a plateau); and the **N/dim capacity law is confirmed across a 2× scale change** — `N/dim = 0.122` gives recall 0.800 at *both* (dim 8192, N 1000) and (dim 16384, N 2000). Usable engineering number: **capacity ≈ dim/16 for perfect recall, ≈ dim/4 before collapse.**

**User (2026-07-20):** *"bit-pack the counts and push dim to 32768"* — F1264's NEXT items (b) and (c). Harness `R-RBS-LM-BITPACK_…py`, srmech **0.9.0rc288**.

## (b) BIT-PACKING — verified, not asserted
F1264 measured the count matrix is **dense in cells** but small in **value range**, so the win is bit-width. Built the packed store as a flat `bytearray` addressed at bit granularity (Class-B framing; no third-party bitset), then **checked it cell-for-cell against the plain counts**:

| | |
|---|---|
| bits/cell | **10** = `ceil(log2(1000+1))` |
| round-trip | **EXACT** — 0 mismatching cells of 16,384 |
| plain `array('i')` | 65,536 B |
| **packed** | **20,480 B → 3.20× smaller** |
| vs the bundle (4,096 B) | packed counts are **5.0×** the bundle |
| read cost | **1.0 µs per packed `get`** |

F1264's predicted "~5.5× the bundle, growing as log N" lands at **5.0×** here (10 bits at N=1000 vs the 11 bits it measured at N=4000). **The storage claim is now realised rather than projected** — and the honest price is a ~µs-scale per-cell read against a plain array index.

## (c) THE DIMENSION PUSH — saturation, but at the ceiling
N=1000, FULL read (F1264 refuted the margin-sparse read, so it is not used):

| dim | recall | Δ |
|---|---|---|
| 8192 | 0.800 | — |
| 16384 | **1.000** | +0.200 |
| 32768 | **1.000** | +0.000 |

**The flattening between 16384 and 32768 is a CEILING, not a plateau** — recall is *perfect* at 16384 and there is nothing left to gain at this N. My pre-registered falsifier said "if recall flattens, the lever has saturated and F1259 moves back up the queue." That reading would be **wrong here**, and the distinction matters: the lever did not stop working, it finished the job. **F1259 stays de-prioritised.**

## The capacity law — confirmed across scales
Because saturation-at-ceiling can't locate the limit, the limit was measured directly at dim=16384:

| N | **N/dim** | recall |
|---|---|---|
| 2000 | 0.122 | 0.800 |
| 4000 | 0.244 | 0.800 |
| 8000 | 0.488 | **0.200** |

**The ratio law holds:** `N/dim = 0.122` gives recall **0.800** at *both* (dim 8192, N 1000) and (dim 16384, N 2000) — two different absolute scales, same ratio, same recall. That is the clean confirmation F1264 predicted but could not test.

Combined with the dim sweep, the capacity curve is:

| N/dim | recall |
|---|---|
| ≤ 0.061 | **1.000** |
| 0.122 – 0.244 | 0.800 (plateau) |
| 0.488 | 0.200 (collapsed) |

**Engineering rule: capacity ≈ dim/16 for perfect recall, ≈ dim/4 before collapse.** A 1.1 M-type vocabulary would need dim ≈ 17.6 M for perfect single-store recall — which is the real argument for **chunking** rather than one giant store, and matches `[[feedback_dim_size_2n_capacity_is_D_independent]]`'s "chunk for capacity."

## Verdict / next
Both requested items delivered and both behaved better than expected: the packed store round-trips exactly at the predicted width, and dimension solves the problem outright at N/dim ≤ 0.06. The count structure is now characterised end-to-end — **storage cost (5.0×, log N), read cost (O(N·dim), no shortcut), and capacity (N/dim ≈ 1/16)**.

**NEXT:** (1) the **per-query index** — still the only live route to beating O(N·dim), since F1264 killed the global one; (2) **chunked stores** at dim/16 each, which the capacity law says is the way to reach corpus scale, and which is testable against the melange discipline (couple, never merge); (3) a C-native packed-count read, since 1.0 µs/get in Python is the current floor.

Composes **F1264** (whose storage projection and saturation falsifier are both resolved here — the falsifier's *reading* corrected), **F1263** (the count structure), **F1259** (stays de-prioritised, correctly), **F1216**, `[[feedback_dim_size_2n_capacity_is_D_independent]]` (chunk for capacity — now with a measured ratio), **F1205/#263**, #231/PKG-3.
