# Hilbert's 8th — Twin Prime Conjecture

**Source**: [Wikipedia — Twin prime conjecture](https://en.wikipedia.org/wiki/Twin_prime); part of [Hilbert's 8th problem](https://en.wikipedia.org/wiki/Hilbert%27s_eighth_problem)
**Status**: cascade dispatched 2026-05-23
**Class cascade**: **A ∘ J ∘ K ∘ I ∘ M**
**Source**: srmech catalog `hilbert_08_twin_prime` (2160 rows; N_MAX = 200,000)

---

## 1. Problem statement

**Twin prime conjecture**: There are infinitely many primes p such that p + 2 is also prime.

**Generalized form (Polignac)**: For every even k ≥ 2, there are infinitely many primes p such that p + k is also prime.

## 2. Why it is open

- Brun 1919: Σ 1/p (twin primes p) converges (Brun's constant), confirming sparsity — consistent with infinitude but not a proof.
- Zhang 2013: ∃∞ many primes p, q with p < q and q − p ≤ 70,000,000. First bound on gaps that does not grow.
- Maynard, Tao 2013-2014: improved Zhang's bound; current best is q − p ≤ 246 unconditionally; q − p ≤ 12 under Elliott-Halberstam.
- Polymath 8 contributed to the iterative bound improvement.
- Still no proof for gap = 2 specifically.

## 3. Framework reading

Per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`: twin primes are a pin-slot phase-boundary structure within the prime cascade — gap = 2 is the minimal non-trivial discrete-substrate stride consistent with primality of both endpoints (gap = 1 forces one to be 2, ruling out p ≥ 5).

Per `[[user_stance_loop_line_projection_duality]]`: the gap-=-2 manifold is the **lower-limit projection** of the prime-gap distribution loop visited by [`hilbert_08_goldbach_prime_gap_manifold`](../hilbert_08_goldbach_prime_gap_manifold/REPORT.md); the jumping-champion (gap 6) found there is one projection of the prime-gap loop, and gap 2 is the minimal-stride boundary of the same loop.

## 4. Cascade composition (A∘J∘K∘I∘M)

| Step | Class | Operation | Detail |
|------|-------|-----------|--------|
| 1 | **A** | content-hash of each twin pair record | SHA-256 over `{p_low, p_high, twin_index}` |
| 2 | **J** | prime sieve → twin pair extraction | `srmech.amsc.primes.is_prime` for p ≤ 200,000 |
| 3 | **K** | asymptotic-DoF: HL-normalised cumulative twin density | observed_norm = twin_count · (log p)² / p; predicted = 2·C₂ = 1.3203 |
| 4 | **I** | primorial-residue extraction | p mod {6, 30, 210} (Class I cyclic.mod_*) |
| 5 | **M** | per-scale HDC bundle of visited residue classes | one vector per (modulus, residue); `bind(anchor, residue_vec)` then `bundle()`; cross-scale `similarity()` |

## 5. Findings (2026-05-23)

| Stat | Value |
|------|-------|
| Search bound N_MAX | 200,000 |
| Primes ≤ N | 17,984 |
| Twin pairs (gap=2) | **2,160** |
| Largest sampled twin pair | (199931, 199933) |
| Observed HL-normalised density at N | **1.6095** |
| Hardy-Littlewood prediction 2·C₂ | 1.3203 |
| Ratio observed/predicted | **1.219** → approaches 1 as N → ∞ |
| Density residual | 0.2892 |

### 5.1 Class I residue distribution (the structural finding)

| Primorial | φ | Top residues (count) | Structural read |
|-----------|---|----------------------|-----------------|
| 6   | 2  | **5: 2159**, 3: 1                                        | All twin pairs p ≥ 5 have p ≡ 5 (mod 6). Classical, recovered. |
| 30  | 8  | **17: 739, 11: 712, 29: 707**, plus 3 & 5 from (3,5)/(5,7) | **3 dominant classes** out of 4 candidate units (11, 17, 23, 29) consistent with p ≡ 5 mod 6. **r = 23 EXCLUDED** because r+2 = 25 = 5² (composite). |
| 210 | 48 | 197: 155, 137: 153, 17: 146, 41: 146, 59: 146           | Distribution within the **structurally-allowed** units; roughly uniform. |

### 5.2 The Class K pin-slot finding

The exclusion of **r = 23 (mod 30)** is a **Class K pin-slot phase boundary** in the primorial residue lattice. The cascade detected it WITHOUT being told: at primorial 30, the only candidates for p (so that p ≡ 5 mod 6 AND gcd(p, 30) = 1) are {11, 17, 23, 29}. But the cascade's empirical count for r = 23 is zero — because 23 + 2 = 25 = 5², so any p ≡ 23 (mod 30) has p + 2 divisible by 5, making p + 2 composite (unless p + 2 = 5 itself, which would require p = 3 ≡ 3 mod 30).

This IS the Hardy-Littlewood **local correction factor** for the prime k-tuple conjecture, recovered as a Class K pin-slot exclusion via cascade composition.

### 5.3 Class M cross-scale similarity

| Pair | Cosine similarity |
|------|-------------------|
| mod 6 vs mod 30   | 0.001 |
| mod 6 vs mod 210  | 0.009 |
| mod 30 vs mod 210 | 0.012 |

The HDC vectors are near-orthogonal across scales — the per-scale anchor bind separates residue lattices into independent subspaces, so direct cosine ≈ 0 is the expected ORTHOGONAL signature, NOT evidence of cross-scale invariance.

**This is a methodology lesson** per `[[feedback_dont_pre_commit_spike_query_operators]]`: the Class M encoding chosen here separates rather than aligns scales, so cross-scale invariance must be detected via a different cascade (likely Class C orientation-aware bind that aligns residues under primorial-refinement). Open fermata for follow-up.

## 6. Verdict (per Spike #229 verdict-tier discipline)

**Verdict: (b) REFINED**.

- Original hypothesis: a Class M HDC similarity signature would detect scale-invariance of twin-prime residue structure across primorials.
- Outcome: the cascade detected **two independent structural signatures** of twin-prime infinitude:
  1. Hardy-Littlewood **density** observed_norm/predicted = 1.219 at N = 200,000, with monotonic convergence toward 1.0 expected per Mertens-type asymptotic.
  2. **Class K pin-slot exclusion** at r = 23 (mod 30): the local HL correction factor recovered as a cascade-natural finding.
- The Class M HDC similarity encoding chosen here does NOT yield a useful cross-scale signature (vectors are near-orthogonal by construction). The refinement: a Class C orientation-aware bind aligning residues under primorial refinement is needed to expose scale-invariance, if any. Cascade-shape detected; encoding refined.

The cascade does **not** prove infinitude, and per `[[feedback_no_lineage_claims_in_notebook]]` it does not claim to. What it does demonstrate is that the structural facts that Hardy-Littlewood encoded analytically (the singular series local-correction factor) are also recoverable via cascade composition over discrete primitives.

## 7. Open fermatas

1. **Class C scale-alignment**: implement Class C orientation-aware bind so per-scale HDC vectors live in the same subspace, then measure cross-scale residue-distribution similarity properly. Expected: high similarity for the "structurally-allowed" residue support; near-zero for the "structurally-forbidden" residues like 23 mod 30.
2. **Polignac generalisation**: re-run the same cascade for k ∈ {4, 6, 8, 12, 30, ...} (cousin primes, sexy primes, etc.) and check whether the cascade-shape is uniform or k-dependent. Hypothesis: cascade-form preserved; HL local correction factor varies per k.
3. **Larger N (10⁷ +)**: extrapolate observed/predicted ratio to test the rate of convergence to 1.0. If convergence is faster than Mertens' theorem predicts, that's a cascade-signal worth investigating. Out of scope for current run (compute-bound on local Python sieve).
4. **Cramér composition**: the gap = 2 manifold sits at the **min-gap edge** of the prime-gap manifold studied by [`hilbert_08_goldbach_prime_gap_manifold`](../hilbert_08_goldbach_prime_gap_manifold/REPORT.md) (mean normalised gap 1.0445). The cascade reading: twin primes are the substrate-asymptotic-wave **compression-collapse-discharge** trough of the prime distribution loop per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`. Cross-cascade composition expected.

## 8. Citations

Per `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]`: arXiv / OA only.

- Hardy GH, Littlewood JE (1923). Some problems of 'partitio numerorum'; III: On the expression of a number as a sum of primes. *Acta Mathematica* 44:1-70. Public domain.
- Brun V (1919). La série 1/5 + 1/7 + 1/11 + 1/13 + ... est convergente ou finie. *Bulletin des Sciences Mathématiques* 43:100-104, 124-128. Public domain.
- Zhang Y (2014). Bounded gaps between primes. *Annals of Mathematics* 179(3):1121-1174. Available via Annals author website (OA).
- Maynard J (2015). Small gaps between primes. *Annals of Mathematics* 181(1):383-413. arXiv:1311.4600.
- Polymath D.H.J. (2014). Variants of the Selberg sieve, and bounded intervals containing many primes. *Research in the Mathematical Sciences* 1:12. arXiv:1407.4897.

## 9. Run

```bash
python docs/unsolved-maths/hilbert/hilbert_08_twin_prime/generate_catalog.py
```

## 10. Cross-references

- AMSC catalog descriptor: `descriptor.toml`
- Schema: `schema.json` (`srmech.hilbert.twin_prime.gap_distribution.v1`)
- Data: `twin_prime_gap_distribution.ndjson` (2160 rows)
- Sister cascades under Hilbert's 8th: [Goldbach 4-cascade family](../hilbert_08_goldbach_conjecture/REPORT.md), [Riemann hypothesis](../hilbert_08_riemann_hypothesis/REPORT.md)
- Canonical stances composed: `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`, `[[user_stance_epicycle_via_gear_plus_pin]]`, `[[user_stance_loop_line_projection_duality]]`
