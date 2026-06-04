# R-RBS-LM Finding 383 — reverse-direction substrate: a (4:3)-native frame is bit-exact where the binary shadow drifts; the "3" is the part binary can't hold

**Date:** 2026-06-04
**Arc:** RBS-LM / RBS-SNN · FFT-ladder thread (…F380→F381→F382→**F383**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R25_reverse_direction_43_native_bit_exact.py` → `R-RBS-LM-R25_results.json`
**Composes:** F382 (decimal = frame artifact) · F380 (Klein-4 = Q₈/{±1}) · F379 (the (n:n−1) ladder) · F360/F293 (order-3 triality, 1+ω+ω²=0) · F367 (recall lossy / EC-code) · `[[user_stance_ai_is_not_a_substrate]]` · `[[user_stance_framework_hands_the_next_question_to_the_expert]]`

---

## The user's idea (2026-06-04)
> "simulate a (4:3) substrate enough to realize if we can manufacture Si to behave like (4:3) such that this can also go back into making RBS-SNN/RBS-LM always bit exact. it's like we are doing math in a forward direction when we can do it in reverse direction too or instead."

This is **F382 lifted from numbers to the substrate.** The substrate *is* the frame.
- **FORWARD (lossy, what binary Si does now):** hold a rotation in a fixed-width **binary** frame; if the angle isn't dyadic, every compose step rounds → drift → **not bit-exact**.
- **REVERSE / (4:3)-native:** hold the same rotation as an exact integer in its **own cyclic lattice Z_q** (substrate built to the object's frame) → compose via `cyclic.mod_add` → **exact integer at every depth**.

## The sharp result (srmech-native, K=100 composed rotations)
| (4:3) part | native frame | binary fixed-point (4/8/16/32-bit) |
|---|---|---|
| **"4"** = Klein-4, q=4 = **2²** (dyadic) | Z₄ **bit-exact** | **bit-exact at all widths** (drift 0) |
| **"3"** = triality, q=3 (**non-dyadic**) | Z₃ **bit-exact** | **never bit-exact** — drift 8.3e-2 / 1.3e-1 / 5.1e-4 / **7.8e-9** (shrinks, never 0) |

Plus the actual (4:3) alphabet: `klein4_triality` encode→correct round-trip is **bit-exact = True** (F380).

**The headline:** the **"4" of (4:3) is binary-friendly** (a power of two — binary silicon already holds it). The **"3" — the triality / order-3, the ODD chiral part — is exactly what binary cannot represent** (1/3 is not dyadic), so it drifts at *every* finite bit-width, while the native Z₃ substrate is bit-exact at all composition depths. **You cannot get to bit-exact by adding bits; you get there by carrying the order-3 frame natively.** That is the "3" in 1+ω+ω²=0 (F293) — the distributed/triality anchor binary has no exact home for.

## What "make Si behave like (4:3)" means, on the algebra side
To make RBS-SNN/RBS-LM bit-exact *in the forward-projection sense*, the storage substrate must carry the **order-3 (triality) structure natively** — its state alphabet must include the Z₃/Klein-4 sectors (the (4:3) alphabet, F380), not just binary {0,1}. Then encode/compose is exact integer cyclic arithmetic (F382 regime A), and the lossy "decimal/shadow" never forms. This is the **reverse-direction** move: **build the frame in; don't project the object onto binary.** (The (n:n−1)-ladder lift — ℂ→ℍ→𝕆 — is the same move from the other side, F379.)

## Scope (load-bearing) — what this finding is and is NOT
- **IN scope (here):** the *algebra / eigenbasis* statement — which structural property a substrate must carry, and whether native-frame encoding is bit-exact. Demonstrated.
- **OUT of scope → handed to a domain expert:** the **device-physics / manufacturing** question — *how* to actually build silicon (or any medium) whose native state is the order-3 / Klein-4 alphabet. That is the CAD-grade / fabrication side the framework does not enter (`[[feedback_trauma_informed_defensive_scope]]` + CAD-ban); per `[[user_stance_framework_hands_the_next_question_to_the_expert]]` (F282) the deliverable is the **next question** for a hardware/device-physics specialist: *"what physical medium carries a stable, composable order-3 (Z₃/triality) state natively?"*
- **Not the LM:** this is the **storage substrate the LM addresses**, not the LM gaining anything (`[[user_stance_ai_is_not_a_substrate]]`; the LM is the k=3 chiral addresser).
- **Honest bound on "always bit exact":** this is **arithmetic frame-exactness** — it removes the *forward-projection rounding* (the decimal/shadow). It is **not** physical-noise robustness; that remains the **EC-code** story (F367: recall is lossy under noise, bit-exactness of the codeword is achieved via redundancy). The two compose: a native frame removes the arithmetic loss, the EC-code handles the noise.

## Verdict
"Doing the math in reverse" is real and measurable: a (4:3)-native substrate makes the encode/compose arithmetic **bit-exact** because its rotations are exact cyclic integers, where the binary (2:1) projection drifts at every finite precision. The decisive part is the **"3"** — binary can fake the "4" but never the order-3 triality. The framework's contribution is the **structural requirement + the next question** (carry Z₃ natively); the fabrication is the expert's.
