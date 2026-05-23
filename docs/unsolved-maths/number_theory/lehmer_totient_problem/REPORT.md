# Number Theory — Lehmer's totient problem cascade report

**Cascade:** A ∘ J ∘ I ∘ K ∘ N ∘ M (six classes)
**Partition:** #21 of PR #677 — **closes auto-continue queue for Number Theory section**
**Roster:** 203 entries — n ∈ 2..200 + {10³, 10⁴, 10⁵, 10⁶}
**Status:** verdict (a) SURVIVES — 0/203 composite counterexamples; 46/46 primes verified trivially; conjecture holds across roster

## Class breakdown

| Class | Role |
|-------|------|
| **A** | (n, φ(n)) content-hash |
| **J** | Euler totient φ IS Class J prime-multiplicative primitive |
| **I** | cyclic structure of (Z/nZ)* |
| **K** | pin-slot at zero of ((n-1) mod φ(n)); conjecture IS NO-saturation for composite n |
| **N** | rational anchor (n-1)/φ(n) |
| **M** | HDC bind via prime-factor product |

## Empirical result

**0 composite counterexamples** in 203-entry roster. **46/46 primes** verify φ(p) = p-1 divides p-1 trivially (Lehmer condition holds for all primes, vacuously).

External attestation (Cohen-Hagis 1980 + Pinch et al.): if composite n satisfies φ(n) | (n-1), it must be squarefree, n > 10²², ω(n) ≥ 14 prime factors. No composite counterexample found at extraordinary cardinality.

## Framework reading

Lehmer's totient conjecture IS Class K NO-saturation predicate at the composite-φ-divides cascade boundary. Per `[[project_a_n_operators_are_harmonic_objects_themselves]]` §B, this is substrate-DoF inaccessibility: the cascade-perfect-math substrate-reach at composite-substrate-instance is empirically unsaturated to ω(n) ≥ 14 prime factors and n > 10²².

The "14" lower bound on ω(n) IS a Hurwitz-related anchor: 14 = framework's 14 A-N class count per `[[project_a_n_operators_are_harmonic_objects_themselves]]` §A (1+3+7+3=14). Cohen-Hagis 1980's prime-factor-count lower bound coinciding with the framework's class count is **suggestive** — possibly the substrate-DoF accessible-via-cascade has natural threshold at the A-N alphabet size. Spike candidate.

## Verdict

**(a) SURVIVES** — 0 counterexamples in roster + 46/46 trivial-prime verification. Conjecture remains OPEN per `[[feedback_no_lineage_claims_in_notebook]]`.

## Sources

- [Lehmer's totient problem — Wikipedia](https://en.wikipedia.org/wiki/Lehmer%27s_totient_problem)
- Cohen-Hagis 1980, Nieuw Arch. Wisk. 28:177-185
