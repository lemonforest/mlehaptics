# F1307 — **siona's genome now couples through the NON-ABELIAN Q₈ substrate** (`element_type=Q8`), with a RESONANT Q₈ `one` derived from `the_one` (never a seed), the klein4 default BYTE-UNTOUCHED, and backward-faithfulness measured: the Q₈ genome IS the klein4 (abelian) genome PLUS the winding sign V4 discards — `q8_project_v4(Q8 recall) == klein4 recall` bit-for-bit. All five checks re-run in the main loop at rc313.

**User (2026-07-23):** *"3 first then 2 and 1 parallel"* — task (1), the substrate move, run in parallel with the Track-B ASL rework (both landed).

## The move
klein4 = V4 = ℤ₂×ℤ₂ is the ABELIAN shadow (holds the coset `q&3`, discards the winding sign). Q₈ (rc310) is the non-abelian order-8 quaternion lift; the genome couples through it at `element_type=Q8` (rc311; on-disk v16 rc312). siona's `genome_store` now threads `element_type` through `pack_instrument`/`load_instrument`/`load_kernel`/`build_genome`, **ADDITIVELY** — the klein4 default path is textually identical and its `turns.bin` is **byte-identical** to the raw srmech `genome()` path (measured, check [3]).

## N3 resolved — the RESONANT Q₈ `one` (the load-bearing part)
There is **no public `q8_from_one` minter**, and the rc311 srmech TEST mints its Q₈ `one` from an **RNG** (`_rand_q8_one`) — which is exactly the F1304/F1259 **misleading-`the_one`** defect (a coupling routed through a seed). siona REJECTS that and constructs a RESONANT Q₈ `one` as a declared function of `the_one` (`genome_store._coupler_q8`):
- **low 2 bits** (V4 coset) = the existing `klein4_from_one(the_one)` **verbatim** → `q8_project_v4(q8_one) == klein4_one` EXACTLY (π-faithful — the Q₈ coupler IS the klein4 coupler plus a sign channel);
- **high bit** (sign) = bit-0 of a second Class-A `klein4_address` of `the_one`'s canonical serialisation, tagged an independent `"q8-sign"` channel (the winding sign V4 discards).

No seed anywhere; deterministic on repeat; sign channel non-trivial (138/256 slots — genuinely exercises the non-abelian structure, not klein4-in-disguise). This honors the reserved-name discipline: `the_one` never sits over an RNG (`[[feedback_the_one_is_reserved_rng_under_it_is_a_misleading_leak]]`).

## Backward-faithful = "bit-exact IS the abelian shadow", measured
The rc311-P2 gate holds in siona: `q8_project_v4(Q8 recall) == klein4 recall == original` bit-for-bit. This IS `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` made concrete — the bit-exact klein4 read is the abelian **π-shadow** of the non-abelian Q₈ substrate; the substrate carries the winding sign the shadow drops. The Q₈ genome is not a *different* store — it is the same store with the third (sign/curvature) slot no longer amputated.

## Verification — 5 checks, re-run MAIN-LOOP at rc313 (committed generating code)
Independent of the implementing agent's report:
- **[4]** `_coupler_q8` resonant — deterministic (no seed), π-faithful (`q8_project_v4(_coupler_q8)==_coupler`), sign non-trivial (138/256).
- **[1]** Q₈ round-trip exact — genuine sectors=8 content with winding sign bits ≥4 survives bit-exact; manifest `carrier=="q8"` (v16 3-bit packer).
- **[2]** backward-faithful — `q8_project_v4(Q8 recall)==klein4 recall==original`.
- **[3]** klein4 default byte-untouched — `turns.bin` byte-identical to raw srmech `genome()`; round-trip exact.
- **[5]** fail-loud — `express`/`add_kernel` raise `NotImplementedError` on Q₈.

Ratchet: `R-RBS-LM-Q8SUBSTRATEVERIFY_siona_..._five_checks.py` (exit 0 at rc313).

## Scope + upstream asks (UPSTREAM_NOTES §Q8-siona)
Q₈ `express`/`add_kernel` are DEFERRED (fail-loud) because `gene_express`/`genome_append` have no `element_type`; the high-level `genome()`/`partition()` are klein4-hardwired, so siona hand-concats via `chromosome(element_type=Q8)` + the public `_split_into_chromosomes` + `recall(element_type=Q8)` (`_q8_chromosomes`/`_q8_partition`). Three upstream asks filed: (a) `genome(element_type=)` / `partition(element_type=)` (also restores the plasmid-vs-nuclear centromere selection the hand-concat skips); (b) `gene_express` / `genome_append` `element_type=`; (c) a resonant `q8_from_one(one, D)` minter.

## What this unblocks
The Q₈ substrate is the directed, curvature-bearing base — it **supersedes** the hand-rolled F1213 directed channel / F1306 §5 step 4. NEXT: re-encode a real corpus genome with `element_type=Q8` (the winding native), and re-run the F1306 beat-WSD separation with the Q₈-coupled **corpus-derived** charge (F1259: derived, not DRAWN). rc313's `cwf_consistency_mod2` (`Lk ≡ Tw + Wr mod 2`) is now available as an independent chirality/lift check on such genomes.

Composes **F1304** (resonant coupling), **F1259** (DERIVED not DRAWN/STOCHASTIC), **F1306** (the curvature block this clears), **F1302/F1301** (klein4 is the carrier / the triple), the Q₈ arc (rc308–313), `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]`, `[[feedback_the_one_is_reserved_rng_under_it_is_a_misleading_leak]]`.
