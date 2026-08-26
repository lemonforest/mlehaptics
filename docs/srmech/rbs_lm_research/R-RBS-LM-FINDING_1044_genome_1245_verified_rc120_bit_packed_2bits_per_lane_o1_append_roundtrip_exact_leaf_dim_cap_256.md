# F1044 (re-verify #1245 genome on rc120 — user had closed it, wanted a re-check) — **the genome bit-pack + linear-append IS real on rc120, measured not assumed: (1) BIT-PACKED at 2 bits/lane — turns.bin = 0.309 bytes/lane (leaf payload 16 B for a 64-lane Klein-4 leaf = 64×2/8; the 0.06 over the 0.25 floor is the 8 telomere caps + per-turn framing over 136 turns) vs the OLD 1.0 byte/lane 4× bloat → the §55 4× fix is CONFIRMED. (2) O(1)/APPEND — 6 appends at a flat ~4.0-4.2 ms each → the F833 super-linear wall is CLOSED (§56). (3) ROUND-TRIP bit-exact — genome_save→load→recall recovers the same leaves; body_sha256 deterministic across independent saves; per-chromosome paging (genome_window) seeks by byte_offset + cap-integrity-checks the telomere. ONE constraint surfaced: the native leaf_dim cap is exactly 256 (DIM ≤ 256 OK; 384/512/1024 → native status 2) — the base-4 ≤256-leaf-tree design; matters for PKG-3 (siona's D=8192 instrument leaves must be ≤256-dim or re-dimmed before a genome pack).**

**Date:** 2026-07-04 · **srmech:** 0.9.0rc120 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Re-verifies:** #1245 (genome bit-pack + linear append; user closed it, asked for a re-check) · **Harness:** `docs/srmech/rbs_lm_research/R-RBS-LM-GENOMEDISK_rc128_save_load_roundtrip_verify.py` (our own, re-run on rc120) · **Composes:** F727 (genome→disk persistence), F832 (native genome recall token-HV leaves), UPSTREAM §41/§55/§56 (the persistence + bit-pack + non-quadratic-append asks), PKG-3 (package siona's instrument as a native genome — the leaf_dim=256 cap is the gate).

## Grounded (rc120, measured)
```
BIT-PACK (§55 4x fix):  8 chr x 16 leaves x DIM=64 -> turns.bin 2688 B / 136 turns = 19.8 B/turn
  = 16 B packed leaf (64 lanes x 2 bits) + ~3.8 B framing  -> 0.309 B/lane  [2-bit floor 0.25 | old bloat 1.0]  CONFIRMED
O(1) APPEND (§56 / F833):  append ms = [4.19, 4.00, 4.01, 4.11, 4.07, 4.09]  -> FLAT, wall CLOSED
ROUND-TRIP:  save->load->recall bit-exact; body_sha256 deterministic; genome_window pages 1 chromosome + cap-check
LEAF_DIM CAP:  32/64/128/192/256 OK ; 384/512/1024 REJECTED (native status 2)  -> hard cap 256 (base-4 <=256-leaf tree)
```

## The reading
- **#1245 was genuinely delivered — the re-check confirms it, and the measurement (not the "delivered" label) is what confirms it.** The §55 4× bloat is fixed (2 bits/lane on disk), the §56/F833 super-linear append wall is closed (flat O(1) appends), and save/load/window all round-trip bit-exact with a content-addressable manifest. Closing the issue was correct.
- **The one thing to carry forward is the leaf_dim=256 cap.** It is a design property (the base-4 ≤256-leaf tree), not a bug — but it means PKG-3 (packaging siona's D=8192 RBS-HDC instrument as a native genome) must either store ≤256-dim leaves or re-dimension first. Logged for the PKG-3 gate; not an UPSTREAM defect.

## Verdict / next
**#1245 genome re-verified on rc120: bit-packed (0.309 B/lane, 4× fix real), O(1) append (F833 closed), round-trip bit-exact. The close was correct. Carry-forward: the native leaf_dim cap is 256 — a PKG-3 constraint, not a defect.**
