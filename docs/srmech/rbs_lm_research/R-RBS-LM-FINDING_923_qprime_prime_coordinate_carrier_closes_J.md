# F923 — prototype: the Class-J prime-coordinate carrier (`Qprime`) closes the open rung J. A quantity → its prime-exponent vector via `primes.factor`, with EXACT carrier arithmetic (multiply = add-exponents, gcd = min, lcm = max) verified **200/200** against `cyclic.gcd`/`cyclic.lcm`, and an exact rational similarity (cosine², shared-prime support). The lens it opens — the multiplicative/factor/period structure we could not read: coprime quantities score similarity 0, factor-sharing quantities score nonzero (12·18 = 16/25 exact), and `cyclic_period` reads recurrence (ord₇(10)=6 = the period of 1/7). Built by an opus sub-agent; verified against rc28.

**Date:** 2026-06-22 · **srmech:** 0.9.0rc28 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_923_qprime_prime_coordinate_carrier_closes_J.py` · **Composes:** F922 (the open-rung map — J), F921 (encode-sense), `primes`/`cyclic` (Class J/I) · **User direction (2026-06-22):** "prototype the J prime-basis encode … give them to opus max-effort sub-agents."

## Verified (rc28, exact-rational; 200 random pairs, seed 20260622)
- `primes.factor(n) -> [(p,e),…]` ascending; `[]` for n<2. Carrier = `{prime: exponent}`, reconstruct `∏ p**e`.
- round-trip `as_int(to_vec(n))==n`: **200/200**.
- **multiply = add exponents** == `factor(a*b)`: **200/200**.
- **gcd = min exponents** == `cyclic.gcd(a,b)` (NOT stdlib): **200/200**.
- **lcm = max exponents** == `cyclic.lcm(a,b)`: **200/200**.
- **similarity exact**: `sim² = Fraction(dot², ‖a‖²·‖b‖²)` over shared primes — `sim²(12,18)=16/25`, coprime → `0`; never leaves ℚ.

## The lens (the multiplicative-structure reading, previously unreadable)
- shared-factor relatedness: `12=2²·3`, `18=2·3²` → cosine 0.8 (`16/25`); `12` vs `25` (coprime) → `0`.
- `primes.cyclic_period` as a recurrence feature: `ord₇(10)=6` = length of the repeating block of 1/7 = 0.(142857); `ord₁₁(2)=10`.

## Proposed carrier API (`Qprime`, peer to `qi.Qi`/`qalg.Qalg`; minimal, exact, numpy-free)
`Qprime.from_int(n)` / `from_factors(pairs)` / `one()`; `.multiply` (add) / `.gcd` (min) / `.lcm` (max) / `.similarity → Fraction` (cosine²) / `.overlap → Fraction` (Jaccard-on-exponents); `.as_int` / `.as_pairs` / `.radical` / `.is_prime_power` / `.order_mod(n)` (via `cyclic_period`). Invariants: exponents ≥ 1 (zero dropped → canonical gcd/lcm + well-defined `==`), primes sorted, empty = multiplicative identity (== int 1). Composes `primes.factor`/`is_prime`/`cyclic_period` + `cyclic.gcd`/`lcm` + `Fraction`.

## Gap notes
- No Class-J carrier exists (confirmed `HARMONIC_LADDER_OPEN_RUNGS[3]=('J',)`); ops are fine — `Qprime` fills the rung.
- Minor doc discrepancy: `primes.FACTOR_MAX_DISTINCT_PRIMES = 64` vs `factor.__doc__` "≤15 distinct primes for uint64" — reconcile (15 is the true uint64 bound).

## Verdict
The J open rung is closed by a thin exact carrier over already-shipped `primes`/`cyclic` ops. Feeds §74 (consolidated ask).
