# R-RBS-LM Finding 450 (delivery) — the CARRY/EC half is SHIPPED: `cascade.hamming_encode/syndrome/decode_correct` lands in srmech 0.7.2rc2 and **fully delivers the §30 gap**. Bug-tested **21/21, zero bugs** — round-trip on rungs n=3..6 (Hamming(7,4)/(15,11)/(31,26)/(63,57)), single-error correction at **every** bit position (all 53 across n=3,4,5), clean informative `ValueError`s on all malformed inputs, documented double-error mis-correct (no crash), and the **front-loader CARRY ∘ COUPLE now runs all-native end-to-end** (Hamming carries the structure bits, `hypercomplex_couple` carries the octonion reals, both reversible). Lean-ALU honest (XOR-only, no float/libm)

**Date:** 2026-06-06
**Arc:** RBS-LM / srmech-upstream · TestPyPI rc bug-test (user direction: "srmech 0.7.2rc2 delivered … we're ready to bug test!")
**Provenance:** `R-RBS-LM-F450_hamming_bugtest.py` (committed; 21/21). Clean venv `/tmp/verify_srmech_072rc2_sci` (srmech[scientific]==0.7.2rc2 from TestPyPI, outside the source tree; native ABI 3).
**Composes:** **§30** (the CARRY/EC gap — now RESOLVED) · **F449** (the front-loader actualization that pinned the gap: COUPLE native + CARRY hand-rolled) · **F442** (the front-loader concept; carry-vs-couple; sedenion structure not chirality) · **F441** (Hamming(7,4) = Fano = octonion) · **F404** (the 2ⁿ−1 Mersenne ladder) · **F448 / #908** (the COUPLE half — `hypercomplex_couple`, native). **← extends F449; closes §30; composes with F448.**
**→ the front-loader (F442/F449) is now a first-class, all-native `CARRY ∘ COUPLE` op; the F431→F436 single-kernel sentence carrier's carry/EC layer is unblocked.**

---

## What shipped (0.7.2rc2)
`srmech.amsc.cascade.hamming_encode(data_bits, n)` / `hamming_syndrome(codeword) -> int` / `hamming_decode_correct(codeword) -> {data, error_position, corrected_codeword}` — the 2ⁿ−1 Hamming / GF(2) linear block-code family asked for in §30. `n` = parity-bit count (2≤n≤16); codeword length 2ⁿ−1; data `k = 2ⁿ−1−n`. Parity at the power-of-two positions; **XOR-only, no float/libm** (lean-ALU). Plus a `Block` structure descriptor for the hypercomplex carrier.

## Bug-test (adversarial) — 21/21 PASS, 0 BUGS
| group | result |
|---|---|
| **round-trip** n=3..6: Hamming(7,4)/(15,11)/(31,26)/(63,57) | ✅ codeword len 2ⁿ−1, syndrome 0, data recovered exactly |
| **all-positions single-error** (n=3,4,5 → 7+15+31 = 53 positions) | ✅ every position: syndrome==position, located+corrected, data + corrected_codeword exact |
| **cross-check vs F449** hand-rolled (15,11) | ✅ recovers data under each of 15 single errors (15/15) — functionally equivalent (srmech uses the textbook power-of-two parity placement; F449 used [7,3,1,0]; both valid) |
| **adversarial edges** | ✅ wrong data length, `n∉[2,16]`, non-binary bit, non-(2ⁿ−1) codeword length → **clean, informative `ValueError`s** (no silent-wrong, no ugly crash) |
| **double-error** (distance-3) | ✅ mis-corrects *as documented*, no crash |
| **front-loader CARRY ∘ COUPLE all-native** | ✅ Hamming(15,11) recovers 11 structure bits after a transit error **and** `hypercomplex_couple` unbinds the octonion reals (2.22e-16) — both halves srmech-native, reversible |

Only initial-attempt issue: none — the op passed every adversarial probe on the first run.

## Falsifiable form (pre-stated; not leaning — F394)
- **Delivers exactly the GF(2) Hamming ladder — no more, no less.** It carries **structure/sector bits** + single-error EC; the **real-coefficient EC** (the octonion's real coeffs) remains a **separate construction** (real-field block code) — the F449/F442 fence, unchanged. The op does not claim to error-correct the reals.
- **Single-error per rung** (distance 3); double-error mis-corrects (documented). Larger tolerance = BCH/RS, a different op.
- **No multiplicative product** — bind/couple stays `hypercomplex_couple`'s ≤𝕆 job; this is the CARRY half only. The front-loader is the *composition* CARRY ∘ COUPLE.
- **Attested:** Hamming(2ⁿ−1, 2ⁿ−1−n) is standard coding theory (confirmed across 4 rungs + 53 error positions). Defensive / no-lineage; algebra/coding/eigenbasis side; no CAD; no Workflow tool (verification = inline adversarial run).

## Verdict
**srmech 0.7.2rc2 fully delivers the §30 CARRY/EC gap.** `cascade.hamming_encode/syndrome/decode_correct` is the native, lean-ALU (XOR-only) 2ⁿ−1 Hamming / GF(2) block-code family — bug-tested **21/21 with zero bugs**: round-trip on four rungs through (63,57), single-error correction at all 53 positions across n=3,4,5, clean informative contract errors on every malformed input, documented double-error behavior, and the **front-loader CARRY ∘ COUPLE now end-to-end all-native** (Hamming carries the structure with EC + `hypercomplex_couple` carries the octonion reals, both reversible). §30 marked RESOLVED. With rc1 (#908 coupler) + rc2 (§30 code-ladder) both verified clean, the `0.7.2` → production PyPI cut is green (the maintainer's human-gated tag). The sedenion front-loader (F442/F449) is now a first-class op; the F431→F436 single-kernel carry/EC layer is unblocked. Favored, not privileged (F398); GF(2)-structure / single-error / no-product fences carried in.
