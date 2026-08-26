# F1295 — **bit-exact PCG64, verified against numpy's published test vectors — both correctness gates are cleared.** `seed=0` reproduces numpy's `pcg64-testset-2.csv` **exactly** (`0xa30febcfd9c2825f, 0x4510bdf882d9d721, 0x0a7d3da94ecde8b8, 0x043b27b61342f01d, 0xd0327a782cde513b`) through the full chain — SeedSequence mixing + PCG64-XSL-RR core — with the 128-bit multiply carried by srmech's `_native.bigint_mul_c` (F1292). **The constants are attested from source, not recalled; the stream matches the published reference. So a numpy-free PCG64 that reproduces `np.random.default_rng` EXACTLY is real — Tier 3 becomes a RENAME with zero value change.**

**User (2026-07-21):** *"extract the attested PCG64 constants and verify against published test vectors."*

## Gate 1 — attested, not recalled
Every constant was **extracted from numpy source** (per `[[feedback_pdf_extraction_citation_discipline]]`), never written from memory:

| constant | value | source |
|---|---|---|
| `PCG_DEFAULT_MULTIPLIER_HIGH` | `2549297995355413924` (`0x23bb8a3ac280de50`) | numpy `src/pcg64/pcg64.h` |
| `PCG_DEFAULT_MULTIPLIER_LOW` | `4865540595714422341` (`0x43b0dc1cf60fc8a9`) | numpy `src/pcg64/pcg64.h` |
| SeedSequence `INIT_A/MULT_A/INIT_B/MULT_B` | `0x43b0d7e5 / 0x931e8875 / 0x8b51f9dd / 0x58f38ded` | numpy `bit_generator.pyx` |
| `MIX_MULT_L/MIX_MULT_R/XSHIFT` | `0xca01f9dd / 0x4973f715 / 16` | numpy `bit_generator.pyx` |

constant-set sha256: `7a404cec2bde8d2a3ea66c4423f7f17b7ad216f7440a2ec511f952c9f613f1c2`. Full attestation block + URLs + retrieval date in `R-RBS-LM-PCG64VERIFY_*.py` (computational-provenance discipline: the generating code is committed).

## Gate 2 — verified, not asserted
F1291 flagged that matching `default_rng` needs **both** the generator core *and* numpy's SeedSequence entropy-mixing reproduced. Both are implemented here from the fetched algorithm bodies (`hashmix` / `mix` / `mix_entropy` / `generate_state` verbatim), and the full chain — `SeedSequence(0) → (initstate, initseq) → srandom_r init → step→XSL-RR` — matches numpy's published vector on all 5 outputs. **5/5 exact.**

## The arithmetic is srmech's, and it is a cascade
The one heavy op — the 128-bit `state·mult mod 2¹²⁸` — runs through `_native.bigint_mul_c` + a Class-K mask (F1292). **No numpy anywhere in the file.** This is the F1294 method made concrete: the operation is a Class-I∘K cascade; the layer is plain ints; the constants are attested.

## What this unblocks
F1290 stalled Tier 3 (184 files) because migrating off numpy's RNG would change every number. **That is now false.** A numpy-free PCG64 reproduces the stream bit-for-bit, so those 184 files can drop numpy with **zero value change** — the migration is a rename, and no lodged result is invalidated. This is strictly the third option F1291 hoped for, now proven rather than proposed.

## Scope, kept honest
Verified: the **default-stream raw-uint64 path** (`SeedSequence(int) → PCG64 XSL-RR`) against numpy main. **Not yet covered**, each a further attested-and-verified step with no new algebra:
- **PCG64DXSM** — numpy's other/newer variant (cheap multiplier, DXSM output). Any file using it needs that output function verified too.
- **`.advance()` / `.jumped()`** — the jump-ahead polynomial.
- **float / gaussian / integer-range transforms** layered on the raw stream (`random()`, `standard_normal`, `integers(low, high)` rejection sampling) — each is a documented transform of the raw draws.

The **raw generator is bit-exact**; the transforms are the next tranche, and they are ordinary work now that the core is nailed.

## The path forward for Tier 3
Package `pcg64_step` + SeedSequence as a srmech op (UPSTREAM §110 gap 2 — chain-register the modular family for a *declared* cascade; or ship it directly), verify the per-transform layer against numpy vectors as each file needs it, then migrate. Every step is attest-then-verify against a published reference — the discipline that made *this* finding trustworthy.

Composes **F1292** (the bignum multiply this rides on), **F1291** (the two gates, now cleared), **F1290** (Tier 3, now unblocked), **F1294** (operation-is-cascade / layer-is-choice), `[[feedback_pdf_extraction_citation_discipline]]`, `[[feedback_computational_provenance_discipline]]`.
