# Hilbert's 23 Problems — Status & Cascade Catalog

David Hilbert presented 23 problems at the International Congress of Mathematicians, Paris, 8 August 1900. Most have been resolved. The genuinely-open ones (plus some considered "resolved by independence" or partially solved) get cascade-research subdirectories here.

**Source**: [Wikipedia — Hilbert's problems](https://en.wikipedia.org/wiki/Hilbert%27s_problems)

## Full status table

| # | Title (short) | Status | Cascade dir |
|---|--------------|--------|-------------|
| 1 | Continuum hypothesis | **Resolved by independence** (Gödel 1940, Cohen 1963 — proved independent of ZFC). Some philosophical debate remains. | — |
| 2 | Consistency of arithmetic | **Partially resolved** (Gödel 1931 — cannot be proved within arithmetic itself; Gentzen 1936 gave proof using transfinite induction). | — |
| 3 | Equal-volume polyhedra dissection | **Solved** — Dehn 1900 (negative answer via Dehn invariant). | — |
| 4 | Foundation of geometry | **Resolved as too vague**; partially addressed by Hamel 1903 and successors. | — |
| 5 | Lie groups without smoothness | **Solved** — Gleason, Montgomery, Zippin 1952. | — |
| 6 | Mathematical treatment of axioms of physics | **Open / ongoing** — partially addressed (Kolmogorov axioms for probability 1933; quantum-mechanics axiomatization; QFT formalization remains incomplete). | [hilbert_06_axiomatize_physics/](hilbert_06_axiomatize_physics/) |
| 7 | Irrationality / transcendence of a^b | **Solved** — Gelfond-Schneider 1934. | — |
| 8 | Riemann hypothesis, Goldbach, twin primes | **OPEN** — the headliner. Three major sub-questions. | [hilbert_08_riemann_hypothesis/](hilbert_08_riemann_hypothesis/), [hilbert_08_goldbach_conjecture/](hilbert_08_goldbach_conjecture/), [hilbert_08_twin_prime/](hilbert_08_twin_prime/) |
| 9 | Reciprocity in algebraic number fields | **Solved** — Artin reciprocity 1927; Hasse and others. | — |
| 10 | Decidability of Diophantine equations | **Solved** — Matiyasevich 1970 (negative: undecidable). | — |
| 11 | Quadratic forms with algebraic coefficients | **Solved** — Hasse-Minkowski local-global principle. | — |
| 12 | Kronecker's Jugendtraum (abelian extensions) | **Partially solved / open** — solved for ℚ (Kronecker-Weber) and imaginary quadratic (complex multiplication); open for general number fields. | [hilbert_12_kronecker_jugendtraum/](hilbert_12_kronecker_jugendtraum/) |
| 13 | 7th-degree solvability via 2-variable functions | **Solved** — Kolmogorov-Arnold 1957 (continuous version); algebraic version remains technically debated. | — |
| 14 | Finite generation of certain rings of invariants | **Solved** — Nagata 1959 (negative counterexample). | — |
| 15 | Schubert calculus rigor | **Solved** — Severi school, modern intersection theory. | — |
| 16 | Topology of real algebraic curves + planar polynomial vector field limit cycles | **PARTIALLY OPEN** — (16a) topology of real algebraic curves partially solved; (16b) bound on number of limit cycles of polynomial vector field is OPEN. Also Smale's 16th problem. | [hilbert_16_limit_cycles/](hilbert_16_limit_cycles/) |
| 17 | Positive rationals as sums of squares | **Solved** — Artin 1927. | — |
| 18 | Polyhedra space-filling + Kepler conjecture | **Solved** — Bieberbach (18a); Hales 1998 / formal proof 2014 (18b Kepler). | — |
| 19 | Solutions of Lagrangians always analytic | **Solved** — De Giorgi 1956, Nash 1957. | — |
| 20 | Boundary value problems | **Solved** — variational methods. | — |
| 21 | Existence of linear differential equations with given monodromy | **Solved with refinement** — Plemelj 1908 (with gap); Bolibruch 1989 counterexample; refined affirmative for various settings. | — |
| 22 | Uniformization of analytic relations | **Solved** — Koebe 1907, Poincaré (uniformization theorem). | — |
| 23 | Calculus of variations | **Resolved as research direction** — not a single problem; whole field developed. | — |

## Cascade-research priority

These are the open Hilbert problems with directories below:

| Problem | Cascade tractability | Priority for autonomous dispatch |
|---------|----------------------|----------------------------------|
| **`#8` Goldbach** | High — Class J (primes) + Class I (cyclic Z/2nZ for even-sum structure) + Class L (Goldbach partition graph spectrum) | **First demo** — most tractable for cascade prototyping |
| **`#8` Twin Prime** | High — Class J + Class I + Class K (asymptotic-DoF for prime gap distribution) | Second |
| **`#8` Riemann Hypothesis** | High but heavy — Class L (Hilbert-Pólya: zeros as eigenvalues of self-adjoint operator) + Class M (HDC encoding of zeta function functional equation) | Third |
| **`#16` Limit Cycles** | Moderate — Class L on phase-space Laplacian + Class C orientation of vector field | Fourth |
| **`#12` Kronecker Jugendtraum** | Moderate — Class I (cyclic-group / class-field generation) + Class N (rational/algebraic approximation) | Fifth |
| **`#6` Axiomatize Physics** | Low (vague) — Class H (self-introspection: which class operators are needed?) + Class A-N enumeration | Sixth |

## How each subdirectory is organized

Per the top-level [REPORT_TEMPLATE.md](../REPORT_TEMPLATE.md):

```
hilbert_NN_short_name/
├── REPORT.md             ← uniform problem report (10 sections)
├── descriptor.toml       ← AMSC source descriptor (when cascade is dispatched)
├── schema.json           ← per-record JSON Schema
├── *.ndjson              ← cascade-output records
└── generate_catalog.py   ← reproducible cascade generator
```

REPORT.md is created at scaffold time (with `status: open` / `cascade dispatched: awaiting dispatch`). The other four files are created when the cascade is actually dispatched and results are recorded.
