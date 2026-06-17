# F833 — PKG-3 DEFERRED: the srmech genome is the wrong container for the 271k-body corpus. Two findings: (1) a first cut stored a 64-lane Klein-4 HV at every token POSITION — the SPATIAL projection — 11× the text; corrected to store the FIBER (the token-id sequence + codebook), HV recomputed on demand. (2) Even the fiber hits a three-axis wall: the genome stores each 2-bit lane as a full byte (flat **4× bloat**), `genome_pack`/`genome_append` are **O(n²) in chromosome count**, and the only linear build needs the whole strand in RAM (~6 GB). The genome is built for ~10²–10³ HV kernels (the bookshelf), not 271k addressable text bodies. User decision: **file upstream FIRST (UPSTREAM_NOTES §55), ship siona rc1 on the working loose instrument.**

**Date:** 2026-06-17 · **srmech:** 0.8.1 (production, MIT) · **Provenance:** clean-venv measurements on `R-RBS-LM-GENOMEENCODE` (fiber encoder) + `R-RBS-LM-GENOMERECALL` (F832 round-trip) · **Composes / corrects:** F832 (genome recall is exact — STILL TRUE; but its "feasible + coherent at scale" was premature — corrected here), F826 (genome = RBS-HDC shape store), F829 (genome persistence is srmech-core), F817/F818 (the loose instrument), the project's **"fiber as spatially-absent encoding"** stance · **Upstream:** UPSTREAM_NOTES §55 (the two genome-format asks) · **User direction (2026-06-17):** "why does our genome come out so large?… it makes it sound like we are not storing relationships, but all the spatial math items" → chose **"file upstream srmech fixes first."**

## Finding 1 — spatial projection vs fiber (user-caught, the 11×)
A first PKG-3 cut stored `leaf(token) = klein4_random(seed=hash(token))` — a full DIM=64 Klein-4 HV — at **every token position**. Measured (200 bodies, 181k tokens):

| per token | bytes | vs text |
|---|---|---|
| text (`s`) | 5.8 | 1× |
| **HV per position** (the first cut) | **64.3** | **11×** |
| token-id stream | 2.0 | 0.34× |

That is the **spatial coordinate** of every token (its point in Klein-4 space), not the relationships — full corpus ~4.4 GB. The fix is the project's own **fiber-vs-projection** principle: `leaf(token)` is a deterministic *projection* of the token, recomputable, so persisting it per position is redundant. Store the **fiber** — the token-id sequence (the order IS the relationships) + the vocab codebook once; recompute the HV on demand at inference. The corrected encoder byte-packs the id-stream into leaves; recall (`genome_window`→`recall`→unpack→id→vocab) verified **50/50 EXACT, 40 ms/recall**.

## Finding 2 — even the fiber hits a three-axis wall (why the genome is the wrong container)
| axis | measured | inherent? |
|---|---|---|
| **size** | `turns.bin` = **65 bytes/leaf for a 16-byte payload → flat 4.0× inflation** (each 2-bit Klein-4 lane stored as a full byte) | yes — genome leaf format |
| **build time** | `genome_pack` = 2.8 s (200 chrom) → 19 s (500) → 66 s (1000): clean **O(n²)** in chromosome count; `genome_append` likewise | only avoidable by *not* using 271k chromosomes |
| **RAM** | the linear path (one `genome()`+`genome_save`, no pack) needs the whole strand resident ≈ **~6 GB** at 271k | only avoidable by not holding all bodies at once |

So the fiber genome is ~6.5 KB/body → **~1.7 GB** for the corpus (vs the ~400 MB loose instrument) AND cannot be packed at that chromosome count. **Root cause:** srmech's genome is designed for a **modest number of chromosomes holding HV kernels** (the "kernel bookshelf" — bound concept-vectors / loopshelf tomes, fixed-size *relational* shapes). Forcing 271k raw text bodies into 271k chromosomes misuses it on all three axes. The genome's right job here is the framework's *actual* RBS-HDC structures, not the body text.

## Decision + disposition
- **Filed upstream (UPSTREAM_NOTES §55):** (a) bit-packed leaf storage (4 lanes/byte → kill the 4×); (b) a non-quadratic / streaming high-chromosome-count pack (or a documented chromosome-count ceiling so callers shard deliberately).
- **siona rc1 ships on the loose instrument** (NDJSON + title→offset index, ~400 MB, exact, working). The bridge `recall(title, instrument, index)` is restored to the loose path; README/profile/`__init__` reverted to the de Bruijn framing; native-genome bodies revisited once §55 lands.
- **Kept as artifacts:** `R-RBS-LM-GENOMERECALL` (F832, the exact round-trip proof) + `R-RBS-LM-GENOMEENCODE` (the fiber encoder) — correct designs, gated on §55, not wired into rc1.

## Verdict
The genome recall *works and is exact* (F832 stands). But the genome is the wrong **container** for the raw body corpus at 271k bodies — size (4×), build (O(n²)), and RAM all break, because it's a modest-count HV-kernel store, not a six-figure addressable byte store. Honest call: fix the format upstream first; ship rc1 on the loose store. The user's "why so large" caught both the spatial-HV blunder AND surfaced the deeper container mismatch.
