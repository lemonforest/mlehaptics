# F731 — rc138 verify: `the_one` TOML-driven (faster, not slower), 11-helper de-dup, §43 genes-per-chromosome + `tlv_unpack` landed

**Date:** 2026-06-13 · **srmech:** 0.7.5rc138 (test.pypi.org; native dispatching, numpy OPTIONAL/absent) · **Composes:** F727–F730 (carrier arc + §43 ask), F715/F721 (genome), CLAUDE §2 · **Provenance:** `R-RBS-LM-APIDIFF_…` (rc133→rc138) + `R-RBS-LM-REGRESSION_…` (49/0) + `R-RBS-LM-GENOMEDISK_…` (VERIFIED ✓) + `R-RBS-LM-CARRIERAUDIT_…` (17/17) + inline perf A/B + §43 genes round-trip

## What the user shipped in rc138
`the_one` is now **TOML/config-driven** (de-duped from several copies into the config-driven form), plus a batch of duplicate low-level helpers consolidated, plus part of the §43 genome ask.

## "Didn't break anything?" — core is GREEN
- **regression 49 OK / 0 BREAK**, **genome→disk VERIFIED ✓**, **carrier 17/17**, **`the_one` works** (returns `One`; `to_scalar()` = an exact rational Fraction — unchanged public signature `the_one(σ, θn, θd=1, terms=24)`, so the TOML-driving is internal).
- **rc133→rc138 API diff:** 0 import-flips, +5 additions, **1 signature change** (`genome.chromosome` gained `genes=` — additive, old positional call still works), and **11 hard removals** (below).

## "Didn't make anything slower?" — actually FASTER
Perf A/B (rc133 vs rc138), numpy-free:

| op | rc133 | rc138 |
|---|---|---|
| `the_one(1,1,2)` | 423 µs | **247 µs** |
| `the_one(1,3,7,terms=24)` | 495 µs | **290 µs** |
| `dense_laplacian(32)` | 540 µs | 542 µs (=) |
| `jacobi_eigvals(32)` | 6.89 ms | 6.83 ms (=) |

The TOML-driving is **cached, not per-call parsing** — `the_one` got ~1.7× faster (de-dup trimmed redundant work). Class-L path unchanged. No slowdown anywhere.

## The de-dup: 11 `laplacian` helpers removed (the "duplicate items packaged into config-driven")
Removed as duplicates of the `Mat`/`Vec` carrier operators (which gained `@`/`+`/`*` in rc133): `dense_matmul_real/complex`, `dense_matvec_real/complex`, `dense_dot_real/complex`, `dense_norm`, `dense_outer_real/complex`, `mat_dot_real/complex`. **Migration:** `dense_matvec_complex(A, v)` → `Mat(A) @ Vec(v)`; `dense_matmul_*` → `Mat @ Mat` — verified byte-identical (`A@v` = `[5,3]` real, `[2j,1]` complex).
- **Impact on our subtree:** one script, `R-RBS-LM-R16` (F363, a numpy-era ride-and-read), made live `dense_matvec_complex` calls → **migrated** to a carrier-backed `_matvec` helper (`Mat.from_rows @ Vec.from_sequence`); ride-and-read result reproduces (node 1 → [2,4] → [3,5]). (R16 still imports numpy for the rest, so it loads only in a numpy-having venv; the transport is now srmech-native and the carrier equivalence is verified.) Stale UPSTREAM §42.1 advice ("use dense_matmul_*") corrected → use the carrier `@`.

## §43 started landing (the genome file-management ask)
The 5 additions are the §43 pieces I scoped last turn:
- **`genome.chromosome(genes=[(label, leaves), …])` + `genome.genes(strand, the_one)` reader** → **several kernels per chromosome**, round-trips EXACTLY (`[('alpha',2),('beta',3)]` in == out; `GENE_FRAME_TAG=71`='G'). The user's repeated hope is now real.
- **`tlv.tlv_unpack`** (+ `TLV_PREFIX_BYTES`) — the Class-B reader gap I flagged in §43 is closed: `tlv_unpack(tlv_pack(7,b"hello"))` → `(7, b'hello', 10)`.
- `cascade.s_generator` (new) + `dsl.generate_class_descriptor` surfaced.

## Verdict
rc138 is **on track — nothing broke, `the_one` is faster, genome + rbs-lm green.** The de-dup removed 11 carrier-duplicate helpers (one of our scripts migrated, semantics verified); `the_one`'s TOML-driving is internal + cached (no signature change, ~1.7× faster); and §43's several-genes-per-chromosome + `tlv_unpack` landed and round-trip exactly.
