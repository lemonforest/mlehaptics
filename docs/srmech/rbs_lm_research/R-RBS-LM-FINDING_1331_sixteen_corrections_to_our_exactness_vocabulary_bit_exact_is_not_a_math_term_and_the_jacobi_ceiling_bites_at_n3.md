# F1331 — **#254 answered, and it returns 16 corrections to our own vocabulary — several landing on shipped claims.** The three that cost most: (1) **"bit-exact" is not a mathematical term.** In numerics it means *bitwise reproducible* — a property you can have **while being wrong** (any deterministic rounding is bit-exact). We use it for a third thing (exactness in a finite algebraic structure, `permute∘permute⁻¹ = id`), which is a **stronger** claim and should be stated as such. (2) **Eigenvalues do NOT force a departure from exactness** — real algebraic numbers have an exact finite integer representation with **decidable** equality (Sturm–Habicht). The true boundary is **transcendentals and limits**. And the real ceiling on `jacobi_eigvals` is far sharper than Abel–Ruffini: **square-root towers reach only degree-2ᵏ extensions, so Jacobi cannot terminate exactly even at n = 3** — verified here on `x³ − 10x² + 28x − 22`, irreducible over ℚ, degree 3. (3) **The data-processing inequality is the wrong theorem for a projection** — DPI is about Markov chains; for a deterministic map the statement is `H(X) ≥ H(f(X))` with **equality iff f is injective on the support**, loss exactly `H(X|f(X))`.

**User (2026-07-27):** *"take the sharpened items not yet unblocked into research subagents."* The brief explicitly asked the agent to **correct my framing where it was muddled**. It did, sixteen times.

Research by a targeted opus agent, MPM discipline, ~30 primary sources fetched and text-extracted (several read as page images where PDFs were scans). **§2's Jacobi ceiling re-verified by me on rc349.**

## 1 — "bit-exact" is four different properties `[the vocabulary correction]`
| property | meaning |
|---|---|
| **exact** | the computed object *is* the mathematically correct one |
| **correctly rounded** | nearest representable value to the exact one |
| **faithful** | within 1 ulp |
| **reproducible / bit-exact** | same bit pattern on every implementation |

**You can be bit-exact and wrong. You can be exact and not bit-exact** (`2/4` and `1/2` are the same rational, different bits). Our usage — e.g. `permute(permute(v,k),-k) == v` — is **exactness in a finite algebraic structure**, a stronger and cleaner claim than "bit-exact", and it should be said that way. Touches CLAUDE.md §0 and shipped docstrings.

## 2 — the Jacobi ceiling, re-verified `[DEMONSTRABLE — mine]`
```
  A = [[2,1,1],[1,3,1],[1,1,5]]     char poly  x^3 - 10x^2 + 28x - 22
  integer candidates (divisors of 22): +-1, +-2, +-11, +-22
  actual rational roots              : NONE   -> irreducible over Q
  [Q(lambda):Q] = 3                  -> 3 is NOT a power of 2
```
Milne Cor. 1.38: a number in a tower of **square-root** extensions has `[ℚ(α):ℚ] = 2ᵏ`. Jacobi rotations use only `√`, so every entry lives in a 2-power tower.

> **Jacobi cannot terminate exactly even for a generic 3×3 rational symmetric matrix.** Abel–Ruffini bites at degree ≥ 5; the square-root-tower ceiling bites at **degree 3**.

And the correction that matters more: **exact eigenvalues of rational matrices ARE available** — as isolating-interval real-algebraic objects (square-free `P ∈ ℤ[X]` + rational interval), with **decidable** equality and order. Just not via Jacobi.

## 3 — what a float-free framework can and cannot claim `[ATTESTED]`
**CAN, with theorems behind it:** exact ℚ arithmetic (decidable equality); exact eigenvalues as real-algebraic objects; exactly invertible finite-group Fourier transforms; **provably bit-exact integer convolution via NTT/CRT — conditional on enforcing three runtime preconditions**; **exact entropy preservation under bijections** (every cyclic permutation, Klein-4 flip, involution — a theorem, not a measurement); exact PSD / reflection-positivity certificates on finite subspaces (rational Gram, no epsilon).

**CANNOT, at any precision:** decidable equality of general reals (**no representation permits it** — Brattka Thm 35; zero-testing *is* the halting problem); exact transcendentals (Hermite–Lindemann / Gel'fond–Schneider — `*_series_truncate` returns an exact rational *approximation of a truncation*, which is an exact object but **not the value**); exact limits (`lim ≡_sW J`, the Turing jump); defeating ill-posedness (exact arithmetic on noisy data gives an **exactly-computed wrong answer**); defeating the sign problem (NP-hardness is arithmetic-model-independent).

## 4 — the corrections that touch shipped or near-shipped claims
- **NTT exactness is conditional.** Three preconditions, all load-bearing: `d > m₁+m₂` (no wraparound), `d | p−1` per prime, modulus `> 2L`. **Without them a wrong answer is a perfectly valid residue with no error signal.** The bound check *is* the correctness proof.
- **`G ≅ Ĝ` is NOT canonical** — *"to prove G ≅ Ĝ we had to choose a generator."* **Any code that indexes characters has silently made that choice**, and it is a *declared parameter*, not a convention-free fact. Only `G ≅ Ĝ̂` is canonical.
- **A complex DFT of length n is not exact in ℚ.** `[ℚ(ζₙ):ℚ] = φ(n)` — it is exact in the cyclotomic field, which you must actually implement, or over a finite field via NTT. *"Anything else is floats wearing a costume."*
- **Landauer licenses nothing about our algebra.** It is a statement about physical substrates with a thermal reservoir, product initial state and unitary evolution — and *"can be violated when any one of our assumptions is dropped."* Landauer's own §4: *"our method of reasoning gives no guarantee that this minimum is in fact achievable."* The mathematical statement we want needs **no physics**: Thm 1.4(f).
- **Osterwalder–Schrader: OS II corrected a LEMMA (8.8), not an axiom** — E0–E4 remain *"certainly necessary"* and their **sufficiency is still open**. The linear growth condition gives a **one-directional** theorem, not the equivalence; equivalence is restored only by `Ē0`, *"difficult to check."* Also **"E0′" is a name collision** — OS I already used it for something weaker.
- **Shannon specifies NO function class.** Not L¹, not L², not finite energy — those words do not appear in 1948 or 1949. L²/Paley–Wiener is the *later* rigorous reconstruction, which is why the theorem is so reliably misquoted.
- **Bandlimited ⟹ entire ⟹ never time-limited.** Every finite sample array came from a signal that was **not** exactly bandlimited. Sampling never certifies losslessness of a real acquisition.

## 5 — where I was specifically wrong, recorded
My brief asserted or implied each of these; all are corrected above: eigenvalues break exactness (no); DPI covers projections (no); "bit-exact" is a term of art we can lean on (no); the table maker's dilemma is a *bound* (it is a **problem**, with no general theorem — and a package that never rounds **does not have it** and must not claim to have solved it); the linear growth condition restored OS equivalence (it did not — *"the single most-often-misstated fact in the area"*); the critical-rate counterexample is excluded by open-vs-closed frequency support (**no — by function class**; in L² the band edge is measure-zero and the theorem is **true at exactly the Nyquist rate**); Poisson summation is *the* underlying identity (overstated — the equivalence claim traces to a **personal communication about an unpublished 1984 report**; do not repeat it).

## Honest scope
- `[DEMONSTRABLE — mine]`: §2 only, on rc349, exact integer arithmetic via `cyclic.gcd` + Class-K `cascade.magnitude`.
- `[ATTESTED — the agent's]`: everything else. ~30 sources fetched; Milne (CC BY-NC-SA), Poonen, Brattka, Reeb–Wolf, Polyanskiy–Wu, Waldschmidt (HAL), Shannon 1948/1949, Higgins, Pollard 1971, Emiris–Tsigaridas, Osterwalder–Schrader I/II, Biskup.
- **Rejected as attestation, per our own rule**: IEEE 754-2019 and 1788-2015 (purchase-only), Schönhage–Strassen 1971 (Springer paywall), Weihrauch's *Computable Analysis*, Rice 1954 (ams.org 403), Bennett 1973, Baker. Each is known only via a source that *was* fetched, and is flagged as such.
- **Two attestation caveats the agent volunteered**: the OS I/II PDFs came from a Project Euclid download endpoint while the *landing* pages claim subscription — content verified, **openness uncertain for a third party**; and Rudin/Folland section numbers **could not be verified, so none are offered rather than guessed ones**.
- Nothing here is built. This is vocabulary and bounds, not code.

Composes **F1101/#254** (the bit-exact ⊕ continuous duality — *its central term is now correctly defined*), **F1330** (the sibling #228 answer), **F1328/F1329** (rc349 work), `[[feedback_stay_rational_collapse_only_at_display]]`, `[[feedback_paywalled_doi_cannot_be_attested]]`.
