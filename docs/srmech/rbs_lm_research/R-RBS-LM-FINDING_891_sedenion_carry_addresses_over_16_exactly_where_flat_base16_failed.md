# F891 (thread 1) — The sedenion-grid navigate+carry addresses >16 pages EXACTLY (1.00) and error-correctingly, where F880's flat base-16 resonance-nesting diluted to 0.16 — and the e_j²=−1 sign-flip IS the Möbius half-twist carry. Using the rc11 `SedenionRegister` (introspected §65): `navigate(j)` is the signed Cayley–Dickson permutation, **`navigate(j).navigate(j)` = global −1** (the σ↔θ Möbius half-twist, F888/F889), and **`carry(overflow_bits, n=3)`** encodes bits past the ≤7 working set into a **Hamming(7,4) EC codeword** in the e8..e15 block (`correct()` is single-error-correcting). **Measured:** (a) `navigate(2)×2` returns `page.A` to slot 1 with **sign −1** — the half-twist, native to the address carry; (b) `carry→correct` round-trips 4-bit payloads **6/6 clean and 6/6 after a 1-bit codeword error**; (c) addressing **64 pages** via (base-slot, carried high-bits) = **64/64 = 1.00 exact**, and **64/64 even with a single-bit error injected in each address carry** — versus **F880's flat base-16 resonance-nesting = 0.16**. So the sedenion grid is the correct >16-page structure: **exact signed-permutation addressing + Hamming EC carry**, with the Möbius half-twist (e_j²=−1) as the native overflow/reversibility mechanism — exactly where F889 said the Möbius belongs (the carry, not the flat router).

**Date:** 2026-06-20 · **srmech:** 0.9.0rc11 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-891_sedenion_carry_addressing.py` (rc11 `SedenionRegister.navigate`/`navmap`/`carry`/`correct`) · **Resolves:** F889 (the Möbius is a carry rule — now demonstrated in the sedenion carry), F880 (flat base-16 nesting failed at 0.16 — the sedenion grid does it exactly), F888 (the e_j²=−1 = the σ↔θ half-twist), F873 (base-16 nesting — done right = navigate+carry, not resonance-bundle-nesting), [[feedback_sedenion_no_division_is_the_addressing_feature]], [[feedback_hyperloop_addressing_is_a_2axis_mobius]] · **User direction (2026-06-20):** "build the sedenion-grid half-twist carry for >16 pages (does it beat flat base-16 nesting?)."

## Measured (sparse, srmech-native; rc11)
| test | result |
|---|---|
| (a) `navigate(2)×2` → slot 1 | `page.A`, **sign −1** (e_j²=−1 = the Möbius half-twist) |
| (b) `carry→correct` clean | **6/6** 4-bit payloads round-trip |
| (b) `carry→correct` + 1-bit error | **6/6** (single-error-correcting) |
| (c) address 64 pages (navigate+carry) | **64/64 = 1.00 exact** |
| (c) + 1-bit error in each address carry | **64/64 = 1.00** (EC-protected) |
| **vs F880 flat base-16 resonance-nesting** | **0.16** |

## Reading
- **The >16-page address problem is solved by the sedenion grid, not by bundling.** F880's hierarchy bundled node-signatures (superposition → dilution → 0.16); the sedenion grid addresses by a **signed permutation** (`navigate`, exact and reversible) with **Hamming EC carry** for the bits past 16 (the e8..e15 block). Exact (1.00) + error-correcting (1.00 under 1-bit faults).
- **The Möbius is the carry.** `navigate(j).navigate(j) = −1` — going around the loop twice flips the sign (σ), the σ↔θ half-twist (F888). So the address space is genuinely a Möbius/double-cover at the carry boundary, and the framework's own `navigate` already implements it. F889's "the Möbius is a carry rule, not a routing lever" is now concrete.
- **This is exact INDEX addressing, not content routing.** The 1.00 is "given the page index, navigate+carry fetches it exactly + EC." It does NOT decide *which* page a novel query wants — that remains the resonance-routing ceiling (F880 0.70 / F882 0.81). The grid is the exact substrate the router addresses INTO.

## Honest scope
- The win is **addressing** (exact + EC), not the open **routing-discrimination** problem (still the storage-density arc). Two distinct layers: route (resonance, ≤0.81) → address (sedenion grid, 1.00).
- 64 pages demonstrated (16 base slots × 4 carried groups via 2 overflow bits padded to the Hamming(7,4) 4-bit payload); scales further by widening the carry payload / nesting registers.
- rc11 gotchas logged (§65): `carry(n=3)` needs exactly 4 data bits; `correct()` payload under key `"data"`. Sparse: register ops only; no dense, no numpy, no bag.

## Verdict / next
The sedenion-grid **navigate+carry beats flat base-16 nesting decisively** for >16 pages — **1.00 exact + error-correcting vs F880's 0.16** — and the **e_j²=−1 sign-flip is the Möbius half-twist carry** (F888/F889 made concrete). The address layer is solved; the routing-discrimination ceiling (0.81) is the remaining frontier and lives in the storage-density arc, not the addressing. **Next:** (1) wire the sedenion grid as Siona's page-address layer under the F879/F882 router (route→address→stream); (2) widen the carry for 256+ pages (nested registers / wider Hamming); (3) the routing ceiling stays with Q1–Q4. Framework reading → srmech measurement; addressing solved exactly; the Möbius placed where it works.
