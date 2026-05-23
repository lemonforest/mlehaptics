# Number Theory — Gilbreath conjecture cascade report

**Cascade:** A ∘ J ∘ I ∘ K ∘ C ∘ N ∘ M (seven classes)
**Partition:** #20 of PR #677
**Status:** verdict (a) SURVIVES — **50/50 rows verified: Gilbreath holds; first element = 1 throughout (except row 0 = 2)**. CANONICAL Class K pin-slot use case via `_cascade_helpers.magnitude()` at every iterated difference step.

## Class breakdown

| Class | Role |
|-------|------|
| **A** | content-hash of (row, first-element) |
| **J** | primes (row-0 base) |
| **I** | cyclic sign-flip across absolute differences |
| **K** | **pin-slot at zero of (prev[i+1] - prev[i])** — the canonical Class K primitive in action |
| **C** | cascade-orientation across iterated difference rows |
| **N** | Class N anchor at integer 1 |
| **M** | HDC bind across rows |

## Empirical verification

Starting from first 100 primes, computed 50 rows. **50/50 rows verified**: first element = 1 for every row r ≥ 1 (row 0 starts with 2, the first prime).

External attestation: Odlyzko 1993 verified to >10¹³ rows.

## Framework reading

This is the **canonical Class K pin-slot use case** per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: the cascade uses `_cascade_helpers.magnitude()` at every iterated absolute-difference step, NOT Python `abs()`. The Gilbreath cascade IS Class K saturation iterated — each row applies Class K pin-slot at zero to the previous row, and the conjecture asserts the saturation propagates indefinitely starting from a value of 1.

Per `[[user_stance_epicycle_via_gear_plus_pin]]`: iterated absolute differences IS cascade-orientation sign-flip composition (Class K + Class C); the Gilbreath conjecture predicts the iterated cascade has a **stable Class N anchor at 1** in the leading column.

## Verdict

**(a) SURVIVES** — 50/50 row-by-row verification + external Odlyzko 1993 attestation to enormous depth. Per `[[feedback_no_lineage_claims_in_notebook]]`: conjecture remains open (not proved).

## Sources

- [Gilbreath's conjecture — Wikipedia](https://en.wikipedia.org/wiki/Gilbreath%27s_conjecture)
- Odlyzko AM (1993). Math. Comp. 61(203):373-380
