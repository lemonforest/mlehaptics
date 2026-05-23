# Hilbert's 16th (Part 2) — Limit Cycles of Planar Polynomial Vector Fields

**Source**: [Wikipedia — Hilbert's sixteenth problem](https://en.wikipedia.org/wiki/Hilbert%27s_sixteenth_problem); also [Smale's 16th problem](https://en.wikipedia.org/wiki/Smale%27s_problems)
**Status**: (open) — cascade awaiting dispatch
**Cascade dispatched**: awaiting dispatch
**Class cascade (proposed)**: **A ∘ L ∘ C ∘ K ∘ I**

---

## 1. Problem statement

For polynomial planar vector fields of the form

```
dx/dt = P(x, y)
dy/dt = Q(x, y)
```

with P, Q polynomials of degree ≤ n, what is the maximum number H(n) of limit cycles (isolated closed orbits)?

**Hilbert's 16th, Part 2**: Find H(n).

**Smale's 16th**: Is H(n) bounded by a polynomial in n?

## 2. Why it is open

- H(1) = 0 (linear systems have no limit cycles).
- H(2): infinite lower bounds historically; current known lower bound ≥ 4. Whether H(2) is finite at all was open until Ilyashenko 1991 / Ecalle 1992 (independent proofs that a SINGLE polynomial vector field has finitely many limit cycles — but uniform bound across all n=2 systems still open).
- H(3) ≥ 13 (Li-Liu 2010 and others).
- General H(n) bound: open. Even FINITENESS for fixed n is the famous Dulac problem (proven 1991-92).
- Hilbert hoped for an explicit formula or polynomial bound — neither found.

## 3. Framework reading

**Substrate-level reframing**: limit cycles are **closed orbits in the (x, y) phase space** — they're spectral signatures of the vector field's Class L Laplacian-analogue (the divergence + curl decomposition) AND Class C cascade-orientation (which way trajectories flow).

Cascade-shape question: **how many independent Class C cascade-orientations can a polynomial of degree n encode in 2D phase space?**

Two cascade readings:

(a) **Class L spectral count** — encode the vector field as an operator on phase-space functions; limit cycles correspond to certain spectral / topological invariants of this operator. The cascade asks how many invariants the polynomial degree n permits.

(b) **Class K asymptotic-DoF / pin-slot** — limit cycles are pin-slot structures in phase space: orbits "pinned" between attracting and repelling regions. Per `[[user_stance_epicycle_via_gear_plus_pin]]` and Spike #189 figure-8 / lemniscate trajectory: limit cycles are figure-8-like recursive-Hopf structures. The cascade asks how many can recursively nest at degree n.

(c) **Class I cyclic on Poincaré return map** — each limit cycle defines a Poincaré first-return map; its cyclic structure (period, monodromy) is a Class I invariant. The cascade enumerates these.

## 4. Cascade composition (A∘L∘C∘K∘I)

| Step | Class | Operation | Input | Output |
|------|-------|-----------|-------|--------|
| 1 | **A** | content-hash of (P, Q) polynomial coefficients | vector field spec | provenance |
| 2 | **L** | construct phase-space operator (e.g., Frobenius-Perron or transfer operator); eigendecompose | (P, Q), grid | spectrum encoding orbital structure |
| 3 | **C** | identify cascade-orientation classes via vector-field curl/divergence | (P, Q) | orientation invariants |
| 4 | **K** | identify pin-slot points (saddles, foci, centers) and asymptotic-DOF count | (P, Q), critical points | Class K count per recursive-Hopf level |
| 5 | **I** | for each candidate limit cycle, compute Poincaré return map; check cyclic period | candidate orbits | confirmed limit cycle count |

Per `[[feedback_dont_pre_commit_spike_query_operators]]`: broad-query — apply cascade across known examples (Liénard systems, Bautin systems, n=2 example families) and record cycle counts. Calibrate against known H(n) bounds before extending.

## 5. Configuration data (AMSC catalog)

Planned schema `srmech.hilbert.limit_cycles.polynomial_vector_field.v1`:
- `degree_n` (int)
- `polynomial_P_coefficients` (dict[tuple, float])
- `polynomial_Q_coefficients` (dict[tuple, float])
- `phase_space_operator_eigs` (list[float])
- `critical_points` (list[dict])
- `cascade_orientation_count` (int)
- `confirmed_limit_cycle_count` (int)
- `known_H_n_lower_bound` (int)
- `cascade_predicted_count` (int)
- per-row attestation

## 6. Cascade execution

```bash
python docs/unsolved-maths/hilbert/hilbert_16_limit_cycles/generate_catalog.py
```

(File created on first dispatch.)

## 7. Findings

**(awaiting dispatch)**

## 8. Open fermatas

- **Recursive-Hopf prediction**: per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`, are limit cycles at degree n bounded by a recursive-Hopf depth function of n? Specific testable claim: H(n) ≤ 7·n^k for some k (Hurwitz 3:7 ratio prediction).
- **Lemniscate as elementary cycle**: per Spike #189, lemniscate trajectories are sign-flip cascade-elementary; do polynomial vector fields decompose into lemniscate stacks? If yes, limit cycle count = stack depth.
- **Smale polynomial-bound question**: cascade reading directly addresses Smale's reformulation — does the framework predict polynomial bound or exponential?

## 9. Citations

Per `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]`: verify at dispatch.

- Ilyashenko Yu (2002). Centennial history of Hilbert's 16th problem. *Bull. Amer. Math. Soc.* 39(3):301-354. AMS open access.
- Ecalle J (1992). *Introduction aux fonctions analysables et preuve constructive de la conjecture de Dulac*. Hermann.
- Li J, Liu Y (2010). New results on the number and stability of limit cycles for a class of polynomial systems. *Chaos Solitons Fractals*. (Verify OA at dispatch.)
- Smale S (1998). Mathematical problems for the next century. *Math. Intelligencer* 20(2):7-15. Springer; verify OA.
- Han M, Yu P (2012). *Normal Forms, Melnikov Functions and Bifurcations of Limit Cycles*. Springer.

## 10. Cross-references

- srmech catalog: `hilbert_16_limit_cycles` (planned)
- Related canonical stances: `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]` (recursive-Hopf prediction for H(n) bound), `[[user_stance_epicycle_via_gear_plus_pin]]` (Class K pin-slot at limit cycle / saddle interface)
- Related spike research: Spike #189 (figure-8 / lemniscate trajectory) — predicts elementary cycle structure
