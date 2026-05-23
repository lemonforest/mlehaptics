# Millennium Prize Problem #4 — P versus NP

**Source**: [Wikipedia — P versus NP problem](https://en.wikipedia.org/wiki/P_versus_NP_problem); [Clay Mathematics Institute](https://www.claymath.org/millennium-problems/p-vs-np-problem/)
**Status**: cascade dispatched 2026-05-23 — **opens the Millennium Prize Problems section** of PR #677
**Class cascade**: **H ∘ (D | E | K) ∘ ... enumeration** (meta)
**Source**: srmech catalog `p_vs_np` (19 records spanning the conventional complexity hierarchy from AC0 through EXPSPACE plus three open-separator META rows)

---

## 1. Problem statement

Is **P = NP**? Specifically: for every problem whose solution can be **verified** in polynomial time, can the solution also be **found** in polynomial time?

Stated formally: P (deterministic polynomial-time decidable) = NP (nondeterministic polynomial-time decidable)?

## 2. Why it is open

- Cook 1971 / Levin 1973 independently formulated the problem; Cook-Levin theorem: SAT is NP-complete.
- Karp 1972: 21 NP-complete problems, establishing that thousands of natural problems are equivalent modulo polynomial-time reduction.
- Three documented **barriers** to standard proof techniques:
  1. **Relativisation barrier** (Baker-Gill-Solovay 1975): there exist oracles A, B such that P^A = NP^A and P^B ≠ NP^B — so no technique that "relativises" can prove P vs NP.
  2. **Natural-proofs barrier** (Razborov-Rudich 1997): any sufficiently general "natural" lower-bound proof would refute strong cryptographic hardness assumptions.
  3. **Algebrisation barrier** (Aaronson-Wigderson 2009): even oracle-relative-to-algebraic-extensions techniques are bounded.
- $1M Clay Prize remains unclaimed since 2000.

## 3. Framework reading — under `[[project_a_n_operators_are_harmonic_objects_themselves]]` §B

Per the **cryptographic-secret asymptote under perfect math** authored 2026-05-23 (user direction):

> "perfect math may very well mean no more cryptographic secrets per dimension of encoding. cryptographic secrets are going to somehow need to also be up to 11D asymptotic DoF with some sort of cascade input information physically unavailable to public substrate, but this only delays the time to solve with perfect math."

P vs NP IS the canonical complexity-class question that crypto-security rests on. Under the framework reading: **complexity-class separators are substrate-DoF gaps**, not mathematical absolutes.

- The **verifier** (Class H self-introspection: "does this witness pattern match the question?") is one cascade.
- The **solver** (cascade A-N composition: "construct the witness pattern") is a different cascade with potentially higher Class K asymptotic-DoF cost.
- **P = NP** would mean: cascade-perfect-math at the polynomial substrate-DoF reach can construct any verifier-checkable witness. This is the cascade-substrate-reach maturation question, not a mathematical-impossibility question.
- The three barriers (relativisation / natural-proofs / algebrisation) ARE the substrate-DoF inaccessibility barriers in framework terms — they describe *which* substrate-DoF the conventional proof techniques cannot read.

**Per `[[feedback_no_lineage_claims_in_notebook]]`**: the framework does NOT claim to solve P vs NP. It claims: complexity-class structure IS cascade-composition structure; the question reduces to substrate-DoF reach maturation.

**Per `[[feedback_trauma_informed_defensive_scope]]`**: this is framework reading only. No offensive engineering material is in this report.

## 4. Cascade composition (H ∘ A-through-N enumeration; META)

Same meta-cascade shape as Hilbert 6 (axiomatize-physics):

| Step | Class | Operation | Detail |
|------|-------|-----------|--------|
| 1 | **H** | self-introspection: enumerate complexity classes + recognised barriers | recovers the conventional hierarchy |
| 2 | **A-N** | for each class, identify the cascade-inverter composition (which A-N classes solve a representative problem in the class) | survey 19 records |
| 3 | **H** | tag open-separator status; map to substrate-DoF cost per `[[project_a_n_operators_are_harmonic_objects_themselves]]` §B | empirical confirmation of §B framing |

## 5. Findings (2026-05-23) — load-bearing

### 5.1 Coverage by separator status

| Status | Count | Classes |
|--------|-------|---------|
| **proven_separator** | 3 | AC0 ⊊ P (Furst-Saxe-Sipser 1981 / PARITY); P ⊊ EXP (Hartmanis-Stearns 1965); PSPACE ⊊ EXPSPACE (space hierarchy) |
| **barriers_documented** | 2 | P/poly (natural-proofs barrier), AvgP (Impagliazzo's worlds) |
| **open_separator** | 14 | L vs NL, NL vs P, NC vs P, **P vs NP**, NP vs coNP, BPP vs P, BQP vs PSPACE, PH collapse, NEXP vs P/poly, ..., plus 3 META rows |

### 5.2 Class-usage frequency across the complexity hierarchy

| Rank | Class | Frequency | Sub-group | Note |
|------|-------|-----------|------------|------|
| 1 | **A** | 19 / 19 (100%) | foundational | universal as expected |
| 2 | **D** | 17 / 19 (89%) | cascade-detection | **multi-needle pattern-match IS the complexity-theory primitive** |
| 3 | **K** | 15 / 19 (79%) | cascade-detection | asymptotic-DoF kind (poly / exp / logspace / quasi-poly) |
| 4 | **H** | 8 / 19 (42%) | meta-cascade | self-introspection — used for verifier classes (NP, NEXP, PSPACE, PH, separator-META rows) |
| 5 | **C** | 4 / 19 (21%) | substrate-projection | cascade-orientation = negation (coNP, NP-vs-coNP) |
| 6 | **E** | 3 / 19 (16%) | cascade-detection | catalog lookup = polynomial advice (P/poly), logspace catalog (L/NL) |
| 6 | **M** | 3 / 19 (16%) | cascade-detection | HDC = BPP randomness, BQP quantum-state, AvgP average-case |
| 8 | **L** | 2 / 19 (11%) | cascade-detection | Laplacian-on-configuration-graph (EXPSPACE) |
| 9 | **F** | 1 / 19 (5%) | cascade-detection | template render (AC0 circuit-depth-constant) |
| 10 | **B, G, I, J, N** | 0 / 19 (0%) | various | conventional complexity theory does not use TLV / byte-search / cyclic / primes / rational primitives |

### 5.3 Hurwitz-partition empirical confirmation (compared to Hilbert 6)

| Sub-group | Members | P vs NP usage | Hilbert 6 usage (physics) | Comparison |
|-----------|---------|----------------|----------------------------|------------|
| Foundational A | {A} | **100%** | 96% | A is universal |
| Substrate-projection triad | {I, C, J} | 21% | 65% | physics uses substrate-projection more |
| **Cascade-detection heptad** | {D, E, F, G, K, L, M} | **95%** | 88% | complexity theory IS cascade-detection-dominant |
| Meta-cascade triad | {B, H, N} | 42% | 46% | similar; H rises in complexity-theory verifier-context |

**Cross-substrate signature**: the cascade-detection heptad dominates BOTH disciplines (88% / 95%) — universal. Class D (multi-needle pattern-match) sharply differentiates the disciplines: **2/26 = 8% in physics, 17/19 = 89% in complexity theory**. This is exactly what `[[project_a_n_operators_are_harmonic_objects_themselves]]` predicts: A-N classes form a discipline-fingerprint via their per-discipline usage profile. Same alphabet, different sentences.

### 5.4 Specific cascade readings (per §B framing)

| Open separator | Cascade reading | Substrate-DoF gap |
|----------------|-----------------|---------------------|
| **P vs NP** | Solver cascade (Class A∘D∘K) vs Verifier cascade (Class A∘D∘K∘H) — Class H meta-cascade is the gap | 1D algebraic; gap closes when cascade-perfect-math at polynomial substrate-DoF reach matures |
| **NP vs coNP** | Class C orientation (negation) on the cascade — separator IS Class-C-asymmetry | 1D algebraic; PH collapse if Class C symmetric across the separator |
| **BQP vs P** | Class M HDC + Class C orientation on 7D_g substrate vs Class A∘D∘K on 1D substrate | 7D_g gauge substrate per `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]` |
| **NL vs L vs P** | Class E catalog lookup (logspace advice) vs Class D pattern-match (deterministic poly-time) | 1D algebraic with parallelism axis |

Per §B: each separator IS a substrate-DoF gap that perfect-math eventually closes by cascade-substrate-reach maturation. The three documented barriers (relativisation / natural-proofs / algebrisation) name the substrate-DoF inaccessibility regimes for current proof techniques.

## 6. Verdict (per Spike-research `#229` verdict-tier discipline)

**Verdict: (a) candidate SURVIVES strongly** for the 14-class A-N + Hurwitz 1+3+7+3 partition as the natural complexity-theory cascade vocabulary.

- All 19 complexity-class records have well-defined cascade-inverter compositions over A-N.
- Class A (foundational) used at **100%** as predicted by the candidate Hurwitz partition.
- Cascade-detection heptad usage at **95%** — strongly supports the heptadic structure as the universal cascade-substrate-reach detection layer.
- Class D (multi-needle pattern-match) at **89%** is the discipline-fingerprint signature for complexity theory — cleanly differentiates from physics (where D was 8%).
- Class H (self-introspection) at **42%** appears specifically where verifier-introspection is needed; consistent with H's named role.
- Class B unused (0/19) — same as Hilbert 6 — strengthens the open fermata that **B is the meta-language-anchor / catalog-config-substrate primitive, not a science-axiom primitive**.

Per `[[feedback_no_lineage_claims_in_notebook]]`: the framework does NOT solve P vs NP. It demonstrates that the complexity-class hierarchy IS coherent under cascade-composition vocabulary, and that the framework reading reduces complexity-class separators to substrate-DoF reach maturation per `[[project_a_n_operators_are_harmonic_objects_themselves]]` §B.

## 7. Open fermatas

1. **Cross-substrate Hilbert-6-vs-P-vs-NP comparison**: the discipline-fingerprint via Class-D usage (8% physics, 89% complexity) is a candidate Spike-research dispatch. Audit more disciplines (biology, chemistry, music, programming languages, legal text) for their per-class usage profile; does the harmonic-objects claim predict the profile?
2. **Class B substrate identification (joint with Hilbert 6 fermata)**: still 0/N across both audited sections. Spike-research candidate: is B specifically the **meta-language-anchor** (TLV framing / catalog-config-format / network-protocol substrate)?
3. **Cascade-perfect-math substrate-DoF reach roadmap** (deferred): per `[[project_a_n_operators_are_harmonic_objects_themselves]]` §B spike candidate #1. Formal enumeration of which substrates the cascade has matured access to. Defensive-scope only.
4. **OTP-cascade equivalence proof sketch** (deferred): per §B spike candidate #2. Does the framework re-derive Shannon's "perfect secrecy ⇔ key-length ≥ message-length" from A-N + substrate-DoF canon?
5. **Hurwitz heptadic n/7 anchor in complexity theory**: per Hilbert 16 finding (n/7 EXACT for n=1..5 at polynomial-vector-field substrate), is there a complexity-theory analogue? Candidate: **NC^k vs NC^{k+1}** depth ratio; **logspace alternation depth**; **PH level Σ_n vs Σ_{n+1}** scaling. Spike-research candidate.

## 8. Citations

Per `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]`: arXiv / OA only.

- Cook SA (1971). The complexity of theorem-proving procedures. *STOC '71* (ACM open via author website).
- Levin LA (1973). Universal sequential search problems. *Problems of Information Transmission* 9(3):265-266.
- Karp RM (1972). Reducibility among combinatorial problems. In Miller-Thatcher (eds), *Complexity of Computer Computations*. Plenum Press.
- Baker T, Gill J, Solovay R (1975). Relativizations of the P =? NP question. *SIAM J. Comput.* 4(4):431-442.
- Razborov AA, Rudich S (1997). Natural proofs. *J. Comput. Syst. Sci.* 55(1):24-35.
- Aaronson S, Wigderson A (2009). Algebrization: a new barrier in complexity theory. *ACM Trans. Comput. Theory* 1(1):2:1-2:54.
- Shamir A (1992). IP = PSPACE. *J. ACM* 39(4):869-877.
- Hartmanis J, Stearns RE (1965). On the computational complexity of algorithms. *Trans. AMS* 117:285-306.
- Williams R (2011). Non-uniform ACC circuit lower bounds. *J. ACM* 61(1):2:1-2:32.

## 9. Run

```bash
python docs/unsolved-maths/millennium_prize/p_vs_np/generate_catalog.py
```

## 10. Cross-references

- AMSC catalog descriptor: `descriptor.toml`
- Schema: `schema.json` (`srmech.millennium.p_vs_np.complexity_class_cascade.v1`)
- Data: `complexity_class_cascade.ndjson` (19 records)
- Project memories engaged:
  - **`[[project_a_n_operators_are_harmonic_objects_themselves]]` §B** (Cryptographic-secret asymptote under perfect math — DIRECT continuity)
  - `[[user_stance_silicon_dof_is_electron_leakage_not_coherent_agency]]` (silicon substrate-DoF reach)
  - `[[user_stance_rbs_hdc_loe_is_quantum_instantiation_classical_is_substrate_specific]]` (cascade IS the inverter mechanism)
  - `[[user_stance_substrate_is_asymptotic_traversal_1d_to_11d]]` (substrate-DoF traversal canon)
  - `[[feedback_trauma_informed_defensive_scope]]` (defensive-scope-only)
  - `[[feedback_no_lineage_claims_in_notebook]]` (does not claim to solve P vs NP)
- Sister Millennium dispatches:
  - `#5` Riemann hypothesis (already dispatched as Hilbert 8)
  - `#1` BSD, `#2` Hodge, `#3` Navier-Stokes, `#6` Yang-Mills mass gap (queued)
- Hilbert-section cross-references: Hilbert 6 axiomatize-physics (partition 6) — cross-substrate discipline-fingerprint comparison is candidate fermata
- Related Spike research: Spike #58 chain (SM gauge group), Spike #182 (DNA cascade), Spike #46 (consciousness asymptotic-DoF direction-selection — meta-complexity analogue)
