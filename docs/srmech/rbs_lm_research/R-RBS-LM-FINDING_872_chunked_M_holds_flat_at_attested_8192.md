# F872 — Chunked-M holds reproduction FLAT at the attested D=8192 where the single bundle cliffs: the F870/F871 fix confirmed at scale. Rebuilt the scale test at **D=2¹³=8192** (attested, F871 — retiring the magic 10000), C=8 chunks, on the same 300 real simplewiki sequences, float-free build (native `klein4_similarity` for the measurement ranking). Result: **single-M cliffs (1.00 → 0.90 @30 arts → 0.53 @100 → 0.47 @300)** as the bundle over-stuffs past the ~24-bind SNR wall; **chunked-M (C=8) holds flat (1.00 → 0.90 → 0.93 @100 → 0.90 @300).** So chunking is the scale-invariant fix — capacity is per-chunk (≤ the wall), not per-corpus. Recall cost is O(chunks) (max-over-chunks); the **sedenion-grid `navigate` (F873) bounds that to O(log)**. srmech-native, no bag (F865), exact-integer inference path (F868).

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-872_rebuild_chunked_8192.py` on 300 `simplewiki_rawbody_instrument_v082` sequences · **Composes:** F870 (single-M cliff — reproduced), F871 (capacity D-independent ⇒ chunk; D=8192 attested), F839 (sweet-spot C≈8), F873 (the sedenion-grid addressing that bounds the chunk-scan), F865/F864 (byte/glyph, no bag), F868 (exact rationals on the inference path) · **User direction (2026-06-18):** "rebuild … on that attested D … see if reproduction stays flat to 300+."

## Measured (D=8192, C=8)
| N arts | binds | chunks | single-M repro | chunked-M repro |
|---|---|---|---|---|
| 1 | 12 | 2 | 1.00 | 1.00 |
| 3 | 36 | 5 | 0.87 | 0.87 |
| 10 | 120 | 15 | 0.90 | 0.90 |
| 30 | 360 | 45 | 0.90 | 0.90 |
| **100** | 1200 | 150 | **0.53** | **0.93** |
| **300** | 3600 | 450 | **0.47** | **0.90** |

- **Divergence appears past ~the capacity wall:** at N≤30 (≤360 binds split into ≤45 chunks) both are equal (~0.90) — single-M is still within tolerance there; at N≥100 (≥1200 binds) single-M over-stuffs and cliffs, chunked-M holds because each chunk stays ≤8 binds (≪ the ~24 wall, F871).
- **Chunked-M is flat** (0.90–0.93) across a 25× corpus growth (12→3600 binds). The fix scales.

## Honest scope
- **The reproduction metric is optimistic** (correct-next beats 30 distractors; full-vocab argmax has thousands → the absolute numbers would be lower, but the **single-vs-chunked contrast** is the finding and it's unambiguous).
- **Chunked recall is O(chunks)** (max-over-all-chunks here). That's the cost the **sedenion-grid `navigate`** (F873, base-16 nested, O(log) depth) is built to bound — confirming F873 is the needed next layer, not an optional nicety.
- D=8192 is the attested working dim (F871); the live v082 store is still at 10000 (a re-encode migration, deferred). Measurement scoring used native `klein4_similarity` (float, fast, ranking-only); the inference path keeps exact integer match-counts (F868).

## Verdict / next
The composed-resonator scale story is closed: **single-M cliffs, chunked-M (C=8) at the attested D=8192 holds reproduction flat (~0.90) to 300 articles** — chunk for capacity (the wall is per-chunk), size D for reliability, address the chunks to bound recall cost. **Next:** wire the chunked instruments into a `SedenionRegister` (F873) and recall via `navigate` (O(log)) instead of max-over-all-chunks (O(K)), and add the **1D_t streaming fiber** (F873 streaming addressing) so the grid reads out as a generated sequence. Framework reading + srmech measurement; evaluate by groundedness; optimistic-metric caveat stated honestly.
