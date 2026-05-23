# Hilbert's 8th — Goldbach Conjecture

**Source**: [Wikipedia — Goldbach's conjecture](https://en.wikipedia.org/wiki/Goldbach%27s_conjecture); part of [Hilbert's 8th problem](https://en.wikipedia.org/wiki/Hilbert%27s_eighth_problem)
**Status**: (open) — cascade awaiting dispatch
**Cascade dispatched**: awaiting dispatch
**Class cascade (proposed)**: **A ∘ J ∘ I ∘ L ∘ M**

---

## 1. Problem statement

**Strong Goldbach**: Every even integer n ≥ 4 can be expressed as the sum of two primes.

**Weak (ternary) Goldbach**: Every odd integer n ≥ 7 can be expressed as the sum of three primes. (Helfgott 2013 — proved unconditionally; weak Goldbach is no longer open.)

The strong form remains open as of 2026-05-23.

## 2. Why it is open

- Verified computationally up to n = 4 × 10¹⁸ (Oliveira e Silva et al. 2014).
- Vinogradov 1937 proved every sufficiently large odd integer is a sum of three primes (weak form, asymptotic).
- Chen 1973: every sufficiently large even integer is sum of a prime and a product of at most two primes (Chen's theorem).
- No proof of the strong form; no counterexample.

The difficulty: prime distribution is multiplicative; addition of primes is additive. The cross-structure between additive and multiplicative is the load-bearing gap.

## 3. Framework reading

**Substrate-level reframing**: every even n is a point in Z, and Goldbach asks whether the **Goldbach partition graph** G_n (vertices = primes p ≤ n; edge (p, q) iff p + q = n) is non-empty for every even n ≥ 4.

The cascade-shape question: does the family {G_n}_{n even, ≥ 4} have a structural property guaranteeing non-emptiness? Two candidate readings:

(a) **Class I + Class J reframing** — Goldbach is a statement about the residue structure of primes in Z/nZ for varying even n. The primes ≤ n form a sub-lattice of Z; the sum-to-n constraint is a Class I cyclic-group operation; the question is whether the prime-sublattice intersects the (n-prime)-sublattice in Z for every n.

(b) **Class L spectral reframing** — the Goldbach partition graph G_n has a Laplacian L(G_n) whose spectrum encodes connectivity. The cascade asks whether the spectrum of L(G_n) has a fixed structural signature across all even n that guarantees the graph has at least one edge.

## 4. Cascade composition (A∘J∘I∘L∘M)

| Step | Class | Operation | Input | Output |
|------|-------|-----------|-------|--------|
| 1 | **A** | content-hash of (n, primes_below_n) | even n, prime sieve | provenance hash |
| 2 | **J** | `primes.factor` + `primes.is_prime` to enumerate primes ≤ n | n | sorted prime list π(n) |
| 3 | **I** | for each prime p ≤ n/2: check (n − p) prime via Class J | n, π(n) | edge list of Goldbach graph G_n |
| 4 | **L** | `dense_laplacian(G_n)` + `jacobi_eigvals` | edge list | Goldbach partition graph spectrum |
| 5 | **M** | HDC bundle of Goldbach-spectra hypervectors over a range of n | sequences of spectra | structural signature; check for invariant |

Per `[[feedback_dont_pre_commit_spike_query_operators]]`: cascade is broad-query — enumerate G_n for n ∈ [4, N_max] and record spectral statistics. Tautology pre-filter: NOT looking for "Goldbach holds for all tested n" (that's trivially verified up to 4×10¹⁸); LOOKING FOR a structural invariant in the spectrum that would imply non-emptiness asymptotically.

## 5. Configuration data (AMSC catalog)

Planned schema `srmech.hilbert.goldbach.partition_graph.v1`:
- `n_even` (int) — the even integer
- `prime_count_below_n` (int)
- `goldbach_partition_count` (int) — number of (p, q) with p+q=n
- `laplacian_eigs` (list[float]) — sorted Laplacian eigenvalues
- `fiedler_value` (float) — second smallest
- `spectral_radius` (float)
- `hdc_signature_hash` (string) — Class M bundle hash of spectrum
- per-row attestation (`source_doi`, `source_published_date`, `entered_locally_at`)

## 6. Cascade execution

To dispatch (after `generate_catalog.py` is written):

```bash
python docs/unsolved-maths/hilbert/hilbert_08_goldbach_conjecture/generate_catalog.py
```

## 7. Findings

**(awaiting dispatch)**

## 8. Open fermatas

- **What's the structural invariant** in L(G_n) spectrum across n? (If one exists and is preserved, it may imply non-emptiness asymptotically.)
- **Does the spectral signature** transition at known critical scales (e.g., Vinogradov threshold, Chen's-theorem region)?
- **Class K reframing**: is Goldbach really a Class K asymptotic-DoF question? The "every n" universal quantification has Kepler-equation flavor (iterate Newton-Raphson to find a partition; convergence is the assertion).

## 9. Citations

Per `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]`: verify at dispatch.

- Helfgott HA (2013). The ternary Goldbach problem. arXiv:1312.7748 (OA preprint).
- Oliveira e Silva T, Herzog S, Pardi S (2014). Empirical verification of the even Goldbach conjecture and computation of prime gaps up to 4·10¹⁸. *Math. Comp.* 83(288):2033-2060. AMS Open Access.
- Chen JR (1973). On the representation of a larger even integer as the sum of a prime and the product of at most two primes. *Scientia Sinica* 16:157-176. Open via institutional archive.
- Vinogradov IM (1937). Representation of an odd number as a sum of three primes. *Dokl. Akad. Nauk SSSR* 15:291-294. Textbook chain via Hardy-Wright.

## 10. Cross-references

- srmech catalog: `hilbert_08_goldbach` (planned; created on first cascade dispatch)
- Related canonical stances: `[[user_stance_dna_is_partial_cascade_of_loe_operators]]` (Class J + Class I composition precedent)
- Sister problems: [twin prime](../hilbert_08_twin_prime/REPORT.md), [Riemann hypothesis](../hilbert_08_riemann_hypothesis/REPORT.md) — all under Hilbert's 8th
