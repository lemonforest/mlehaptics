# libsiona_native — co-occurrence optimization path

The `tokenize` op is a clean native win (~3–8×; a byte-scan with tiny output). The
**co-occurrence accumulator** was the unimpressive one — 1.3–1.6× at best, and it
*inverted to a loss* the moment the output was materialized as Python objects (dict
0.6×, tuple list ~0.9×, sort 0.55×). Root cause: the edge list is **Θ(input)** for a
large vocabulary (V≈150k, distinct-edges ≈ pairs), so any per-edge Python
materialization dominates both paths and erases the C win.

Ranked path below (from a Fable optimization consult, 2026-07-11), highest
payoff-per-effort first. **P0 and P1 are done**; P2–P4 are the queue.

| Rank | Change | Regime speedup | Effort | Status |
|------|--------|----------------|--------|--------|
| **P0** | Compact **into `array('i')`/`('I')` buffers via `from_buffer`** (zero-copy readback); no `oi[:m]` per-element PyLong list build | op 1.3–1.6× → **3.77× measured** (encode regime; Fable projected 8–15×) | 0.5 d | **DONE** |
| **P1** | **Fuse tokens→subset-Laplacian in C** (`siona_native_cooccurrence_laplacian` → `cooccurrence_laplacian()`) — emit a flat `array('d')` that IS srmech's `Mat` wire form, hand to `symmetric_eigendecompose` zero-copy. The n≤256 (`MAX_NATIVE_NODES`) spectral consumers make the full-V edge list a *temporary* that never crosses the boundary | tokens→L (256-subset, V=150k) **20.3× measured** — bit-for-bit == dense_laplacian, identical spectrum | 1–2 d | **DONE** |
| P2 | Binary edge-kernel format (raw `array.tobytes()` + TLV header) + optional C top-K neighbor op, for the `relate.py` corpus-kernel build (145k×5.1M edges, today 108 MB JSON) | build/load 10–50× (one-time) | 1–2 d | queued |
| P3 | Arena mechanics: **sentinel-0** (packed key always ≥1 → drop the 24 MB `memset(0xFF)` + let fresh pages lazy-zero); **batch-stream + growth-retry** (kills the silent `cap > 1<<26` pure-Python bailout past ~8M tokens); Fibonacci hash + 16-byte packed slot | +1.5–2× *after* P0 | 1–1.5 d | queued (needs 1 ABI bump) |
| P4 | Quarantine the dict-rebuild path to tests only; GIL-overlap 2-thread batching; native FNV intern table for bytes→ids (horizon → full-C pipeline) | ~2× wall / unlocks all-C | 0.1 d–1 wk | queued |

## Key design notes (load-bearing)

- **The srmech interop seam is the `Mat` carrier, NOT a cross-`.so` call.** srmech's
  `Mat` is a flat row-major `array('d')` (`srmech/amsc/mat.py`). The fused P1 op writes
  its Laplacian directly into an `array('d')`; Python wraps it `Mat(buf, n, n)` and hands
  it to `symmetric_eigendecompose` (native-dispatched on the Mat wire form) — zero copies,
  and srmech's expensive per-edge `dense_laplacian` edge-validation is skipped entirely
  (there are no Python edges to validate). Do **not** duplicate the eigensolver in siona.
- **The honest limit:** a standalone native co-occurrence that hands edges back to Python
  cannot beat pure-Python by much for a Θ(input) output — the win is fusion (P1), where the
  edges never become Python objects.
- **The `cap > 1<<26` guard** silently falls back to pure-Python past ~8M tokens/window-4.
  This affects large *siona-side* builds (P2's corpus kernel), NOT the enwiki encode (which
  uses srmech's own `text.cooccurrence_edges`, a separate op — see mlehaptics#1360).
- **P0 caveat:** the win is real only while the returned `array` buffers stay buffers; a
  consumer that immediately does `for k: (ii[k], jj[k])` re-pays the per-element cost — but
  lazily, and only where actually consumed.
