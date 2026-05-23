# Hilbert's 8th — Twin Prime Conjecture

**Source**: [Wikipedia — Twin prime conjecture](https://en.wikipedia.org/wiki/Twin_prime); part of [Hilbert's 8th problem](https://en.wikipedia.org/wiki/Hilbert%27s_eighth_problem)
**Status**: (open) — cascade awaiting dispatch
**Cascade dispatched**: awaiting dispatch
**Class cascade (proposed)**: **A ∘ J ∘ K ∘ I ∘ M**

---

## 1. Problem statement

**Twin prime conjecture**: There are infinitely many primes p such that p + 2 is also prime.

**Generalized form (Polignac)**: For every even k ≥ 2, there are infinitely many primes p such that p + k is also prime.

## 2. Why it is open

- Brun 1919: sum of reciprocals of twin primes converges (Brun's constant), confirming twin primes are sparse — consistent with infinitude but doesn't prove it.
- Zhang 2013 breakthrough: there exist infinitely many primes p, q with p < q and q − p ≤ 70,000,000. First bound on prime gaps that doesn't grow.
- Maynard, Tao 2013-2014: independently improved Zhang's bound; current best (as of 2026 published literature) is q − p ≤ 246 unconditionally; q − p ≤ 12 under Elliott-Halberstam.
- Polymath project 8 contributed to the iterative bound improvement.
- Still no proof for gap = 2 specifically.

## 3. Framework reading

**Substrate-level reframing**: twin primes are pairs (p, p+2) in Z. The cascade-shape question:

> Is the **prime-pair adjacency graph** (vertices = primes; edge (p, q) iff |p−q| = 2) infinite? And more generally, what is the structural signature of the prime-gap distribution?

Two cascade readings:

(a) **Class J + Class K (asymptotic-DoF)** — twin primes are a pin-slot structure in the prime sequence. The Hardy-Littlewood prime k-tuple conjecture predicts the asymptotic density of twin primes as 2 C₂ ∫₂^x dt/(log t)². This is a Class K asymptotic-DoF claim — the cascade asks whether the density formula is structurally inevitable given the cascade-composition of primes.

(b) **Class I cyclic structure** — for primes p ≥ 5, the pair (p, p+2) has joint residues mod m. Restricting to m ∈ {6, 30, 210, ...} (primorial moduli), the twin-prime pair occupies specific residue classes. Class I cascade examines this residue structure for invariants.

## 4. Cascade composition (A∘J∘K∘I∘M)

| Step | Class | Operation | Input | Output |
|------|-------|-----------|-------|--------|
| 1 | **A** | content-hash of prime range and gap histogram | N (search up to) | provenance hash |
| 2 | **J** | `primes.is_prime` for p ∈ [3, N]; extract twin pairs | N | list of twin prime pairs |
| 3 | **K** | asymptotic-DoF: fit gap density to Hardy-Littlewood prediction | twin pair list, x | density fit residuals |
| 4 | **I** | `cyclic.mod_*` to extract residue classes mod primorial 30, 210, 2310 | twin pairs | residue-class distribution |
| 5 | **M** | HDC bundle of residue-class signatures across primorial scales | distributions | invariance score (Class M similarity over scales) |

Per `[[feedback_dont_pre_commit_spike_query_operators]]`: cascade aims to detect a SCALE-INVARIANT structural signature in twin-prime residues. Tautology pre-filter: avoid "twin primes have residues compatible with being prime" (definitional); require a non-trivial Class M similarity invariant across primorial scales.

## 5. Configuration data (AMSC catalog)

Planned schema `srmech.hilbert.twin_prime.gap_distribution.v1`:
- `prime_range_upper` (int) — search bound N
- `twin_pair_count` (int)
- `gap_2_density_observed` (float)
- `hardy_littlewood_prediction` (float)
- `density_residual` (float)
- `residue_class_distribution_mod_30` (dict[int, int])
- `residue_class_distribution_mod_210` (dict[int, int])
- `hdc_scale_invariance_score` (float)
- per-row attestation

## 6. Cascade execution

```bash
python docs/unsolved-maths/hilbert/hilbert_08_twin_prime/generate_catalog.py
```

(File created on first dispatch.)

## 7. Findings

**(awaiting dispatch)**

## 8. Open fermatas

- **Scale-invariance signature**: does the residue distribution of twin pairs have a fixed structure across primorial moduli? Per Class M similarity, this would be a structural marker of infinitude.
- **Class K asymptotic match**: how closely does the actual twin-prime density match Hardy-Littlewood at the cascade's best-rational precision (Class N)? Deviations would signal either an HL error or a deeper structural correction.
- **Polignac generalization**: does the cascade extend uniformly to k = 4, 6, 8, ... or does k = 2 (twin) exhibit a distinct signature?

## 9. Citations

Per `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]`: verify at dispatch.

- Zhang Y (2014). Bounded gaps between primes. *Annals of Mathematics* 179(3):1121-1174. Annals open via author website.
- Maynard J (2015). Small gaps between primes. *Annals of Mathematics* 181(1):383-413. arXiv:1311.4600.
- Polymath D.H.J. (2014). Variants of the Selberg sieve, and bounded intervals containing many primes. *Research in the Mathematical Sciences* 1:12. arXiv:1407.4897.
- Hardy GH, Littlewood JE (1923). Some problems of 'partitio numerorum'; III: On the expression of a number as a sum of primes. *Acta Mathematica* 44:1-70. Public domain.
- Brun V (1919). La série 1/5 + 1/7 + 1/11 + 1/13 + ... est convergente ou finie. *Bulletin des Sciences Mathématiques* 43:100-104, 124-128. Public domain.

## 10. Cross-references

- srmech catalog: `hilbert_08_twin_prime` (planned)
- Related canonical stances: `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]` (does twin-prime density exhibit recursive-Hopf signature?)
- Sister problems: [Goldbach](../hilbert_08_goldbach_conjecture/REPORT.md), [Riemann hypothesis](../hilbert_08_riemann_hypothesis/REPORT.md) — all under Hilbert's 8th
