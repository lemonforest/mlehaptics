# F1045 (PKG-3: package siona's instrument as a native srmech genome — the "again", now with the dim-agnostic layer) — **the genome storage scaffolding for siona's kernel SHIPS: `siona.genome_store` packs the D=8192 Klein-4 instrument into ONE native srmech genome via rc123's §60 `kernel_pack`/`kernel_unpack` — the DIM-AGNOSTIC layer that fixes the earlier dense blow-up. Each named body (a tool vector / stored-kernel article) is `kernel_pack`ed: chunked into 256-wide leaves + a §60 header (marker 0x4B) that SELF-RECORDS its true D, `element_type="klein4"` (the identity codec — F1043 option 2, verified: siona's kernel IS the 2-bit {0,1,2,3} symbol), and leaf_dim; the per-body strands concatenate into a multi-chromosome genome with a title→offset manifest. Recall pages one chromosome by label (`genome_window`) and `kernel_unpack` self-trims to the exact D — NO external length index (the loose NDJSON+index it replaces). Measured on 24 REAL siona grounding vectors: all 24 round-trip EXACT, mixed dims fine, turns.bin = 0.316 B/symbol (near the 2-bit floor 0.25; overhead = per-chromosome telomere+header+leaf caps) → 6.3× smaller than the loose NDJSON. The corrected SPARSE store: no dense matrices, Klein-4 end to end, no numpy.**

**Date:** 2026-07-04 · **srmech:** 0.9.0rc123 (TestPyPI) · **Branch:** `research/rbs-lm-rolling-2` (PR #687); siona synced to PR #1 · **PKG-3** (task #231): package siona's full-body instrument as a native genome, not loose NDJSON+index · **Files:** `siona/genome_store.py` (NEW: pack_instrument / load_kernel / load_instrument), `siona/tests/` (real-vector round-trip test) · **Composes:** F1044 (the genome bit-pack this rides — the 256 leaf_dim cap is now MOOT via the kernel_pack chunker), F1043 (option-2 Klein-4 identity codec — the element_type we specified), F1035 (the foundational kernel this can now store natively), `[[feedback_stay_rbs_hdc_sparse_never_dense]]` (the dense-blow-up this corrects). srmech §60 `kernel_pack`/`kernel_unpack` (rc123), W1 (record true D) + W2 (chunker) + W3 (klein4 identity codec).

## Grounded (rc123, real siona vectors)
```
The earlier genome attempt (F1044 era) hit two walls: leaf_dim capped at 256 (native genome_save),
  and a dense storage cost. rc123's §60 kernel_pack CLOSES both -- it chunks ANY-D kernel into
  256-wide leaves + a self-recording header, so D=8192 stores as 32 leaves, dim-agnostic, bit-packed.
LIVE (24 real siona grounding-index tool vectors, D=8192 Klein-4):
  pack_instrument -> one native genome (24 chromosomes, title->offset manifest)
  load_instrument -> ALL 24 recovered EXACT ; single-label load_kernel EXACT ; mixed dims OK
  turns.bin 62208 B for 196608 symbols = 0.316 B/symbol  [2-bit floor 0.25]  -> 6.3x < loose NDJSON
API: pack_instrument(named_vectors, path) / load_kernel(path, label) / load_instrument(path)
  the_one = a deterministic Klein-4 coupler (seed 0), stored in the manifest; kernel_unpack self-trims to true D.
```

## The reading
- **The "again" is closed by the layer, not by us re-fighting the cap.** Last time the genome store was dense and leaf_dim-capped; rc123's `kernel_pack` is exactly the dim-agnostic + bit-packed primitive that makes siona's D=8192 kernel a first-class genome citizen. The scaffolding is a thin, public-API layer over it (no private deps except none — `_default_the_one` avoided by carrying our own deterministic coupler).
- **The header IS the index.** The §60 self-recording header means the genome needs no external length sidecar — recall self-trims to the true D. That is the loose NDJSON+index collapsed into the store itself (self-describing, Class-H shaped).
- **Sparse, by measurement.** 0.316 B/symbol on real vectors ≈ 2 bits/symbol + small cap overhead — the `[[feedback_stay_rbs_hdc_sparse_never_dense]]` discipline honoured, and 6.3× under the loose form. Scales linearly in Σ D_i (F1044's O(1) append still applies per chromosome).

## Verdict / next
**PKG-3 storage scaffolding SHIPS on rc123: `siona.genome_store` packs the D=8192 Klein-4 instrument into one native, self-describing, bit-packed genome; 24 real vectors round-trip exact at 6.3× under loose. The dim-agnostic `kernel_pack` layer retires the 256 leaf_dim wall for siona's kernel.** Next: wire `genome_store` into the Session as the default instrument backend (load-by-genome instead of NDJSON); pack the full F1035 foundational kernel; O(1) `genome_append` for incrementally taught kernels.
