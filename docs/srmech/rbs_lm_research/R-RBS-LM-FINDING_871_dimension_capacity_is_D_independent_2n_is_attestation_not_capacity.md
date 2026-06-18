# F871 — Don't pick a random dim: capacity is DIMENSION-INDEPENDENT (~24 binds, the VSA SNR wall), 2ⁿ wins on attestation + packing NOT capacity. Measured the dimension question instead of assuming it ("don't assume a thing"). Swept D across powers-of-2 and nearby non-powers; the result overturns the "bigger D = more capacity" intuition (including F870's): **N\* = 24 binds for EVERY D from 1000 to 16384** — the number of bindings a single Klein-4 bundle holds above a *relative* gate (1.3×chance) is **independent of dimension**. **2ⁿ does not beat non-2ⁿ** (mean N\*/D: powers-of-2 8.42 vs non-powers 8.30 — equal); baseline is clean binomial (random-pair excess +2/+39/+38, all ≤1 predicted std); speed is **linear in D** (1.2→19 ms/bind), no 2ⁿ speedup at the current 1-byte-per-slot representation. **Why:** the superposition SNR law — a bound item's *normalized* overlap in an N-bundle decays ~1/√N, **independent of D**; D only shrinks the *relative variance* (reliability ∝ √D), not the mean capacity. So you cannot dimension your way past the ~24-bind wall — **chunked-M is unavoidable at any D** (corrects F870's "capacity scales with D"). 2ⁿ is still the right choice — for **attestation** (D=2ⁿ is Class-A; 10000 is an unattested magic number) and **future 2-bit packing** (the boolean belly is 2 bits/slot → 4 slots/byte once srmech bit-packs; latent today), NOT capacity/speed. srmech-native, integer match-counts (no float).

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-871_dimension_sweep.py` (`hdc.klein4_{random,bind,bundle,unbind}` + `.tolist()` match-count) · **Composes / corrects:** F870 ("capacity scales with D" — corrected to D-independent), F837/F839 (chunked-M — now shown *unavoidable*, not just helpful), the no-magic-numbers / `D=2ⁿ` Class-A attestation (CLAUDE.md), F132 (Klein-4 = Z₂×Z₂ boolean belly), [[feedback_stay_rational_collapse_only_at_display]] · **User direction (2026-06-18):** "don't pick random dim size … 2^n sized given the boolean belly. find what works better and learn why, don't assume a thing."

## Measured (no prior)
| D | 2ⁿ? | chance D/4 | gate 1.3× | N\* (binds ≤ gate) | N\*/D ×1000 | ms/bind |
|---|---|---|---|---|---|---|
| 1000 | no | 250 | 325 | **24** | 24.0 | 1.7 |
| 1024 | **yes** | 256 | 332 | **24** | 23.4 | 1.2 |
| 4096 | **yes** | 1024 | 1331 | **24** | 5.86 | 5.3 |
| 5000 | no | 1250 | 1625 | **24** | 4.80 | 7.3 |
| 8192 | **yes** | 2048 | 2662 | **24** | 2.93 | 9.2 |
| 10000 | no | 2500 | 3250 | **24** | 2.40 | 11.2 |
| 12000 | no | 3000 | 3900 | **24** | 2.00 | 14.8 |
| 16384 | **yes** | 4096 | 5324 | **24** | 1.46 | 19.1 |

- **Capacity (N\*) is flat at 24 across a 16× range of D** → dimension-independent. If capacity scaled with D, N\* would vary wildly; it doesn't.
- **2ⁿ vs non-2ⁿ: equal** capacity-per-dimension (8.42 vs 8.30). No 2ⁿ capacity effect.
- **Variance check** (theory: chance D/4, std √(3D/16)): observed random-pair excesses (+2, +39, +38) sit within ~1 std of zero → clean binomial, no 2ⁿ anomaly.
- **Speed ∝ D** (no 2ⁿ jump) — because slots are 1 byte each today, not 2-bit-packed.

## What it means (the design rule)
- **CHUNK for capacity.** A single bundle holds ~24 binds above a relative gate *regardless of D*. Growing D will NOT raise that (it's the 1/√N SNR wall). So chunked-M (C ≈ 8–24, F839) is **mandatory at scale**, not an optimization — F870's break was the wall, and D can't move it.
- **SIZE D for reliability.** D buys margin/√variance ∝ √D — bigger D ⇒ fewer mis-retrievals at the same N (the F870 real-data errors at 30 arts were partly variance; a larger D sharpens them) — but never more capacity.
- **MAKE D a 2ⁿ** — not for capacity/speed (measured: no effect today), but because (a) D=2ⁿ is **attested** (Class-A; 10000 is a magic number to retire), and (b) the Klein-4 **boolean belly** (2 bits/slot) packs 4 slots/byte at 2ⁿ once srmech bit-packs (4× memory + SIMD) — a latent win to realize at the C layer ([[feedback_srmech_c_python_parity_plugin_surface]]).

## Honest caveats
- N\*=24 is the crossing of the *relative* 1.3×chance gate; the exact number is gate-dependent, but its **D-independence** is the finding (holds for any relative threshold).
- The grid resolves N\* to {24,32}; finer grids would pin it, but the 16×-D-range flatness is unambiguous.
- The 2ⁿ packing win is **latent** — it requires srmech to store Klein-4 slots as 2-bit-packed (currently 1 byte/slot). Logged as the reason to prefer 2ⁿ now even though no current metric rewards it.

## Verdict / next
Don't pick a random dim — and don't assume 2ⁿ helps capacity (it doesn't; measured). The substrate truth: **capacity is dimension-independent (~24-bind SNR wall) ⇒ chunk; reliability ∝ √D ⇒ size D for error-rate; use a 2ⁿ for attestation + boolean-belly packing.** **Adopt D = 2¹³ = 8192** as the attested working default (≈ the old 10000's scale, Class-A, packing-ready), retiring the magic 10000; step to 16384 when reliability demands. **Next:** rebuild the F870 scale test as chunked-M (C≈8) + routing + relative gate, on D=8192, and confirm reproduction stays flat to 300+ articles (the wall is per-chunk, so chunking should hold it). Framework reading + srmech measurement; assumption tested + overturned; evaluate by groundedness.
