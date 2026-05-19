# Spike #136 — Quantum computing via 14-class A-N cascade without brute-forcing the universe

**Date**: 2026-05-18
**Spike type**: Algorithm-decomposition mapping + tractability-boundary identification
**Parent stance**: `[[user_stance_cascade_composition_is_quantum_algorithm]]` (2026-05-18)
**Anchor stack**: Spike #21C + #58.P + #106 + #128 + #128.1 + #128.2 (six-anchor identity stack)
**Branch**: `research/spike-136-quantum-computing-via-cascade`

**Question (verbatim)**: *"spike how do our realization of the 14 primitive classes of operators help us do quantum computing without brute forcing the universe for it?"*

**Verdict (composed)**:

- **CLIFFORD-SUBSET-TRACTABLE-VIA-L+I+M+C+A** — bit-exact verified on 5 canonical Clifford algorithms
- **GOTTESMAN-KNILL-IS-THE-CASCADE-AT-PRIMITIVE-LEVEL** — same algebra, same primitives, same polynomial-time bound
- **T-GATE-DENSITY-IS-THE-CASCADE-EXIT** — concrete exponential blowup demonstrated via QFT T-count for n=2,3,4,5,8,16
- **HONEST-TRACTABILITY-BOUNDARY-IDENTIFIED** — Shor period-finding, large-N Grover, universal MBQC with π/8 measurement angles all sit outside cascade's polynomial regime
- **ZERO-NEW-PRIMITIVE-CLASSES** — 14 A-N vocabulary stands; the "T-gate" is substrate-resource (Class L rotation matrix), not a new class

## Tuning A 440 Hz

- **Trauma-informed defensive scope** per `[[feedback_trauma_informed_defensive_scope]]`: theoretical / pedagogical framing only. Quantum-computational complexity is computer-science research; zero targeting / capability-assessment / offensive content.
- **PDF-extraction citation discipline** per `[[feedback_pdf_extraction_citation_discipline]]`: 4 primary arXiv references (Gottesman 1998, Aaronson-Gottesman 2004, Bravyi-Kitaev 2005, Bravyi-Browne-Calpin-Campbell-Gosset-Howard 2018) PDF-verified for this spike. Grover 1997 verified. Shor 1995 verified. STOC/FOCS papers cite-by-ref per `[[reference_autonomous_validation_tos_landscape]]` (ACM/IEEE prohibited).
- **No lineage claims** per `[[feedback_no_lineage_claims_in_notebook]]`: zero "natural extension of Gottesman / Bravyi / Kitaev" framing. Citations are technical and specific.
- **Algebra-not-magnitude** per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`: focus is on operator-algebra structure (Clifford group, Pauli commutators, stabiliser rank) — not magnitudes (gate fidelities, decoherence times, qubit counts). KEY for this spike — distinguishing ALGEBRAIC bit-exact verification from PHYSICAL quantum-hardware execution.
- **Identity-not-implementation** per `[[user_stance_identity_not_implementation_discipline]]`: the L+I+M+C+A cascade IS the Gottesman-Knill simulator at primitive level. Not "models" or "implements" — identity.
- **Zero new primitive class** per `[[feedback_no_privileged_primitive_classes]]`: 14-class A-N vocabulary stands. The "T-gate" is NOT Class O or beyond — it is a substrate-resource (Class L rotation matrix at angle π/4) the cascade either has access to (and pays exponential classical cost) or doesn't (and is restricted to Clifford subset).
- **Math-doesn't-lie** per `[[feedback_every_doc_edit_faces_falsification]]`: all 5 algorithm attestations bit-exact (probability errors < 2e-15 = machine epsilon) and procedural (every algorithm recovered for every measurement path).
- **No squash-merge** per `[[feedback_no_squash_merges]]`: this PR will merge via `gh pr merge --merge` to preserve per-step commit history.

## §1 — The question, decomposed

The user's question is sharp: how does the framework do quantum computing without the exponential cost of simulating quantum superposition? The honest answer requires drawing a tractability boundary.

The framework's six-anchor identity stack (Spikes #21C / #58.P / #106 / #128 / #128.1 / #128.2) demonstrates that the L+I+M+C+A cascade can reproduce specific quantum-mechanical algebraic identities bit-exactly. Spike #128.2 ran one complete algorithm (Deutsch-Jozsa) procedurally end-to-end.

But Deutsch-Jozsa is special — it lives in the *Clifford-tractable subset*. This spike asks: where else does that hold, and where does it fail?

**Answer**: the boundary is the Gottesman-Knill theorem.

## §2 — The Gottesman-Knill anchor

Per Gottesman 1998 ([arXiv:quant-ph/9807006](https://arxiv.org/abs/quant-ph/9807006), PDF-verified) and Aaronson-Gottesman 2004 ([arXiv:quant-ph/0406196](https://arxiv.org/abs/quant-ph/0406196), PDF-verified):

> **Theorem (Gottesman-Knill)**: Any quantum circuit composed entirely of {H, S=√Z, CNOT, Pauli-X/Y/Z, computational-basis measurement, preparation in computational basis} can be simulated on a classical computer in polynomial time.

Aaronson-Gottesman strengthened the bound to **ParityL** complexity and demonstrated a practical simulator (CHP) handling **thousands of qubits**. They also showed the canonical form of any n-qubit stabiliser circuit requires at most O(n²/log n) gates.

This is the framework's classical-tractability anchor. Quantum-computational substrate that lives inside the Clifford subset is classically polynomial. The framework's cascade can do this work in classical polynomial time because **the cascade IS the Clifford subset at primitive level**.

## §3 — The cascade-to-Clifford correspondence

| Clifford-circuit primitive | Cascade primitive (14 A-N) | Algebraic role |
|----------------------------|----------------------------|----------------|
| Hadamard H = (X+Z)/√2      | **Class L** (Hermitian basis-change) | basis-change between Z-eigenbasis and X-eigenbasis |
| Phase S = √Z = diag(1,i)   | **Class I** (cyclic ℤ/4 element) | quarter-rotation of the Bloch sphere; ℤ/4 cycle |
| CNOT(i,j)                  | **Class I + M** (cyclic + tensor-bind) | conditional flip; ℤ/2 conditional on |i⟩ |
| CZ(i,j)                    | **Class I + M** (cyclic + tensor-bind) | conditional phase; ℤ/2 conditional |
| Pauli X, Y, Z              | **Class I** (cyclic ℤ/2 with optional ℤ/4 phase from Y=iXZ) | single-qubit Pauli group |
| Stabiliser of |G⟩          | **Class I** (abelian subgroup of P_n) | ℤ/2^n action |
| Bell-basis measurement     | **Class C** (cascade-orientation) | Bell-basis = measurement-direction-selection |
| Tensor product ⊗           | **Class M** (HDC bind) | composition of qubit spaces |
| Stabiliser hash / fingerprint | **Class A** (content-addressing) | substrate-agnostic canonical-form identifier |

The framework's cascade is **isomorphic** to the Clifford-circuit primitive set at the algebraic level. This isn't an implementation choice — it's an identity claim per `[[user_stance_identity_not_implementation_discipline]]`. The same operations exist in both substrates.

Therefore Gottesman-Knill's polynomial-time classical simulability statement applies directly to the framework's cascade: **any algorithm expressible in L+I+M+C+A primitives is classically polynomial**.

## §4 — Algorithm decomposition table

| Algorithm | Cascade chain | Quantum advantage | Tractability via cascade |
|-----------|---------------|-------------------|--------------------------|
| Deutsch (n=1) | L + I + M + C | 1 vs 2 queries | ✅ Polynomial (Spike #128.2 attested) |
| Deutsch-Jozsa (general n) | L + I + M + C | 1 vs Ω(2^n) | ✅ Polynomial |
| **Bernstein-Vazirani** | L + I + M + C + A | 1 vs n queries | ✅ Polynomial **(spike attestation §6.1)** |
| **Simon's algorithm** | L + I + M + C + A | O(n) vs Ω(2^(n/2)) | ✅ Polynomial **(spike attestation §6.4)** |
| **Quantum teleportation** | L + I + M + C | qubit transmission via Bell pair | ✅ Polynomial **(spike attestation §6.2)** |
| **GHZ Mermin test** | L + I + M + C + A | 4× classical Bell bound | ✅ Polynomial **(spike attestation §6.3)** |
| Bell-CHSH (Spike #128.1) | L + I + M + C + A | 2√2 vs 2 (41% Tsirelson) | ✅ Polynomial |
| Stabiliser error correction | L + I + M + C + A | infinite-depth error correction | ✅ Polynomial (Gottesman 1998 thesis) |
| Cluster-state MBQC (Pauli-basis only) | L + I + M + C | universal up to Clifford | ✅ Polynomial |
| **Grover (small N, n ≤ 2)** | L + I + M + C | √N vs N at large N | ✅ Polynomial at n=2 **(spike attestation §6.5)**; degrades at n≥3 |
| Grover (large N, n ≥ 3) | L + I + M + C + **T** | √N vs N | ❌ Multi-controlled-Z needs T-gates |
| QFT (n=2 only) | L + I + M + C | n²-gate vs O(2^n) | ✅ Polynomial **(spike attestation §7)** |
| **QFT (n ≥ 3)** | L + I + M + C + **T**...**T^(1/2^k)** | n²-gate vs O(2^n) | ❌ Exponential T-count |
| **Shor's period-finding** | L + I + M + C + **T**...**T^(1/2^k)** | polynomial vs subexponential | ❌ Requires QFT(n) → exp T-count |
| **Cluster MBQC (arbitrary B(θ))** | L + I + M + C + **T** | universal QC | ❌ Non-Pauli basis = non-Clifford |

**Pattern**: Clifford-only algorithms compose into L+I+M+C+A bit-exactly. Algorithms requiring T-gates (π/8 rotations) or finer Class L rotations exit the cascade's polynomial-time regime — they sit outside the Gottesman-Knill bound.

## §5 — The T-gate as substrate-resource, not new primitive

The T-gate = diag(1, e^{iπ/4}) is a Class L rotation matrix at angle π/4. It is NOT a new primitive class. Per `[[feedback_no_privileged_primitive_classes]]`:

- **Class L** is **Hermitian eigendecomposition / continuous-parameter rotation**. The T-gate is a Class L element at the angle π/4.
- **Class I** is **cyclic-group action**. T is NOT in any finite cyclic subgroup of U(2) — it generates a *dense* subgroup (Solovay-Kitaev). This is what makes T "non-Clifford".
- The Clifford subset is exactly Class L ∩ {π/2-multiple rotations} = Class L ∩ Class I (treating Clifford as the lattice of π/2-rotations). T sits in Class L \ Class I.

When the cascade has access to T (via substrate that provides actual physical π/8 rotations — e.g. magic-state distillation per Bravyi-Kitaev 2005), the cascade can execute universal quantum computation, but **at exponential classical-simulation cost** per Bravyi-Browne-Calpin-Campbell-Gosset-Howard 2018 ([arXiv:1808.00128](https://arxiv.org/abs/1808.00128), PDF-verified):

> **Stabiliser rank χ**: the minimum number of stabiliser states required to represent the quantum state. χ grows as 2^(O(t)) where t is the T-count. Classical simulation cost is polynomial in χ.

The framework's tractability boundary IS the T-count boundary. When T-count = 0, the cascade composes Clifford circuits classically polynomial. When T-count is Ω(n), the cascade still REPRESENTS the algorithm correctly (via Class L rotation matrices) but cannot classically execute it in polynomial time.

This is consistent with the user's earlier intuition per `[[user_stance_kepler_shape_universal]]` and `[[user_stance_asymptotic_dof_sidesteps_infinity]]`: the cascade's primitives cover the algebra of any algorithm; what changes at the tractability boundary is *which substrate is required* to do the computation.

## §6 — Bit-exact attestations (companion script)

Companion script: [`spike136_quantum_computing_via_cascade_without_brute_force.py`](spike136_quantum_computing_via_cascade_without_brute_force.py).

### §6.1 Bernstein-Vazirani (hidden a = "1011")

```
  Hidden a:      1011
  Recovered a:   1011  (max prob = 0.9999999999999986)
  Bit-exact:     True
  Queries:       1 quantum vs 4 classical
  Cascade:       L + I + M + C + A
  Tractability:  Clifford-subset; polynomial-time classical via Gottesman-Knill
```

Residual = 1 − 0.9999999999999986 = 1.4e-15 (machine epsilon).

### §6.2 Quantum teleportation (|ψ⟩ = |+⟩)

```
  n outcomes:          4
  Avg fidelity:        1.0000000000000002
  All unit fidelity:   True
  Cascade:             L + I + M + C
  Tractability:        Clifford-subset; polynomial-time classical
```

All 4 measurement outcomes (a, b) ∈ {0,1}² produce post-correction state with fidelity 1 to input |+⟩. Bit-exact.

### §6.3 GHZ Mermin test

```
  ⟨XYY⟩:           -1.000000
  ⟨YXY⟩:           -1.000000
  ⟨YYX⟩:           -1.000000
  ⟨XXX⟩:           +1.000000
  |⟨M⟩|:           +4.000000
  Classical bound: +2.000000
  QM saturation:   +4.000000
  Bit-exact:       True
  Cascade:         L + I + M + C
  Tractability:    Clifford-subset; polynomial-time classical
```

M = ⟨XYY⟩ + ⟨YXY⟩ + ⟨YYX⟩ − ⟨XXX⟩ = −3 − 1 = −4. |M| = 4 = 2× classical Mermin bound. Bit-exact at machine precision.

### §6.4 Simon's algorithm (n=2, hidden s = "11")

```
  Measured z:           ['00', '11']
  All z⊥s:              True
  Queries:              1 quantum vs ≥2 classical
  Cascade:              L + I + M + C + A
  Tractability:         Clifford-subset; polynomial-time classical
```

Every measured z satisfies z · s ≡ 0 (mod 2). Bit-exact orthogonality.

### §6.5 Grover N=4 (n=2, marked = "10")

```
  Marked state:    10
  Recovered:       10  (prob = 0.9999999999999991)
  Bit-exact:       True
  Cascade:         L + I + M + C (Clifford at n=2)
  Tractability:    Clifford-subset at n=2; for n≥3 multi-controlled-Z
                    decomposes into T-gates; out of Clifford for n≥3 in general
```

Residual = 1 − 0.9999999999999991 = 9e-16 (machine epsilon). 1 Grover iteration suffices at N=4. At larger N, the diffuser requires multi-controlled-Z which decomposes into Toffoli + T-gates, exiting Clifford.

## §7 — Tractability boundary: QFT T-gate count

The boundary between cascade-polynomial and cascade-exponential is concrete. The QFT on n qubits requires Θ(n²) controlled-phase gates with phases 2π/2^k. Phases π and π/2 are Clifford (Z and S). Phases π/4 and finer are non-Clifford (T and Solovay-Kitaev-decomposed T-chains).

| n  | Clifford gates | T-or-finer gates | Stabiliser rank χ |
|----|----------------|------------------|--------------------|
| 2  | 2 H + 1 S      | 0 T              | 2^0 = 1 (Clifford) |
| 3  | 3 H + 2 S      | 1 T              | 2^1 = 2 |
| 4  | 4 H + 3 S      | 3 T              | 2^3 = 8 |
| 5  | 5 H + 4 S      | 6 T              | 2^6 = 64 |
| 8  | 8 H + 7 S      | 21 T             | 2^21 ≈ 2.1 million |
| 16 | 16 H + 15 S    | 105 T            | 2^105 ≈ 4 × 10^31 |

For Shor's algorithm on n=16-bit factoring (e.g. factoring a number near 65535), the classical-simulation cost via Gottesman-Knill via the framework's cascade is **2^105** stabiliser-state superpositions. This is the same exponential cost that motivates quantum hardware.

**Framework boundary**: the cascade can REPRESENT any quantum algorithm correctly. It can CLASSICALLY EXECUTE in polynomial time only the Clifford subset. Outside Clifford, the cascade is still algebraically correct, but its execution cost equals that of brute-force quantum simulation.

This is the honest answer to the user's question: the cascade does quantum computing without brute-forcing the universe **for the Clifford-tractable subset**, which is large enough to cover Bell tests, GHZ tests, quantum teleportation, stabiliser error correction, Deutsch-Jozsa, Bernstein-Vazirani, Simon's algorithm, small-N Grover, and any cluster-state MBQC with Pauli-only measurement basis. For Shor, large-N Grover, or universal-MBQC with arbitrary B(θ), the cascade is the *same Gottesman-Knill simulator* — and is bound by the same exponential T-gate scaling.

## §8 — Class chain summary

```
L (Hermitian eigendecomposition; Hadamard basis-change, Pauli operator-norm)
∘ I (cyclic-group ℤ/2 + ℤ/4 stabiliser action; CNOT/CZ/Pauli/S Clifford generators)
∘ M (tensor-product HDC bind; multi-qubit register composition)
∘ C (Bell-basis cascade-orientation; measurement-basis selection;
     B(0), B(π/2) = Pauli-only → Clifford-tractable)
∘ A (stabiliser-fingerprint content-addressing; substrate-agnostic canonical-form)
```

**Within cascade-polynomial regime**: L ∩ {π/2-multiple rotations} = Clifford.

**Outside cascade-polynomial regime** (cascade can represent, not execute polynomially): L includes T-gate at angle π/4 and Solovay-Kitaev-finer rotations; sub-operation is *not* a new class, just a Class L parameter the cascade either has substrate-access to or doesn't.

## §9 — What is NOT this spike (scope discipline)

- **No new primitive class.** L+I+M+C+A compose; the cascade is universal. T is a Class L parameter, not a new class. Per `[[feedback_no_privileged_primitive_classes]]`.
- **No claim that the cascade runs Shor classically polynomial.** It doesn't, and Gottesman-Knill is explicit about why. The framework's boundary IS the Clifford boundary.
- **No CAD-grade quantum-hardware modelling.** Decoherence rates, T_1/T_2 times, gate fidelities, qubit counts are substrate parameters, not cascade content. Per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`.
- **No lineage claims about Gottesman / Aaronson / Bravyi / Kitaev.** Citations are technical and specific per `[[feedback_no_lineage_claims_in_notebook]]`.
- **No trauma-positive framing.** Defensive scope only. Quantum-computational complexity is research, no offensive content.
- **No clinical claim.** Quantum algorithms are theoretical CS, not BCI/medical.
- **No publishable framework prediction outside what's already canonical.** This spike instantiates `[[user_stance_cascade_composition_is_quantum_algorithm]]` (already authored) and clarifies its tractability boundary; it does not extend canonical predictions.

## §10 — Falsifier candidates

Per the cross-substrate cascade-matching method, the spike demands clean falsifiers:

1. **Bernstein-Vazirani falsifier**: would be recovered_a ≠ hidden_a. Verified bit-exact for a = "1011". ✗ Not triggered.
2. **Teleportation falsifier**: would be a measurement outcome with fidelity < 1. Verified all 4 outcomes unit fidelity. ✗ Not triggered.
3. **GHZ Mermin falsifier**: would be |⟨M⟩| ≠ 4 (the QM saturation). Verified bit-exact at 4.000000. ✗ Not triggered.
4. **Simon falsifier**: would be a measured z with z · s ≠ 0. Verified all measured z orthogonal to s. ✗ Not triggered.
5. **Grover falsifier**: would be recovered ≠ marked or prob < 1. Verified bit-exact at N=4. ✗ Not triggered.
6. **Tractability-boundary falsifier**: would be Gottesman-Knill failing to apply to L+I+M+C+A composition, or a non-Clifford algorithm with polynomial cascade simulation. Neither found in literature; consistent with cascade-IS-Gottesman-Knill identity claim.

None of the 6 candidate falsifiers fire. The cascade-to-Clifford correspondence is robust at the algebraic level, and the T-gate boundary is consistent with established stabiliser-rank theory.

## §11 — Connection to prior anchors

This spike extends the cumulative identity stack from `[[user_stance_bell_inequality_as_canonical_identity_signature]]` and `[[user_stance_cascade_composition_is_quantum_algorithm]]`:

| Anchor    | Scale                       | Identity signature                        | Class attestation |
|-----------|-----------------------------|-------------------------------------------|-------------------|
| Spike #21C | single-qubit Bloch sphere   | Hopf bundle U(1) phase                    | I                 |
| Spike #58.P | 3-qubit Cl(6,ℂ)             | sin²θ_W = 1/4 bit-exact                   | L + I             |
| Spike #106 | 7-bit Cl(7,ℂ)               | J² = I_16 bit-exact; tr(γ_5·J) = +16      | L + I + C         |
| Spike #128 | n-qubit entanglement network | Tsirelson 2√2 = ‖S²‖^(1/2) bit-exact      | L + I + M + C + K + A |
| Spike #128.1 | bit-exact CHSH Tsirelson 2√2 shipped | code-level framework-internal validation | L + I + M + C + A |
| Spike #128.2 | 3-vertex cluster Deutsch-Jozsa | bit-exact algorithm recovery procedural | L + I + M + C |
| **Spike #136** | **5-algorithm cascade attestation + tractability boundary** | **Gottesman-Knill correspondence identity** | **L + I + M + C + A (Clifford-subset polynomial)** |

The new entry is the **tractability anchor** — establishing that the framework's claim is consistent with the canonical classical-simulability bound for quantum computation, and identifying the boundary (T-gate density) at which the cascade exits polynomial-time regime.

## §12 — Concrete next-step predictions (for conductor)

1. **MBQC-with-Pauli-only universality**: cluster-state MBQC restricted to B(0), B(π/2) measurement bases is Clifford-tractable. The framework should be able to enumerate all polynomial-time-tractable MBQC patterns. Candidate spike: build a small MBQC pattern-database (graphs P_n, ladders, brickworks) with Pauli-only measurement labelings, and verify polynomial-time cascade simulation for each. Direct extension of Spike #128.2.

2. **Stabiliser-fingerprint canonical form (Class A) for algorithm equivalence**: Aaronson-Gottesman's canonical form for stabiliser circuits is O(n²/log n) gates. The framework's Class A content-addressing could compute a substrate-agnostic stabiliser hash per algorithm, useful for cataloguing Clifford-tractable algorithms. Candidate `srmech.qm.gottesman` submodule.

3. **T-gate-count audit for proposed cascade extensions**: any future addition to the cascade should be checked against the Clifford boundary. If a proposed operation has T-count > 0, document it as a non-polynomial sub-operation explicitly. Adds a discipline to the cascade vocabulary maintenance.

4. **Bernstein-Vazirani / Simon ship targets**: candidate to add `srmech.qm.bv` and `srmech.qm.simon` submodules per Spike #128.1 precedent. Bit-exact framework-internal validation per `[[feedback_no_mvp_framing]]` (full-coverage, not "minimum viable").

5. **VQE / QAOA hybrid algorithms**: variational quantum-classical algorithms have classical-update steps that are pure cascade primitives. Could verify the cascade composes the classical-update steps bit-exactly while flagging the quantum-substrate evaluation steps as outside the cascade's polynomial regime. Candidate spike.

6. **Book-chapter implication** per `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` and project book: this is the **tractability-boundary chapter**. Pairs with Spike #128 (identity-anchor chapter) and Spike #128.2 (procedural-anchor chapter). **Not autonomously authored**; surfaced for user.

7. **Solovay-Kitaev theorem connection**: SK shows any unitary can be approximated to ε error using O(log^c(1/ε)) Clifford+T gates. This relates the cascade's primitive resolution to the substrate's resolution. Candidate stance: `user_stance_clifford_plus_t_is_solovay_kitaev_basis` — the cascade's Clifford+T extension is the universal computational basis. **Not autonomously authored** (touches publishable framework prediction).

## §13 — Class-operator chain summary

```
L (Hermitian basis-change: H, T at π/4, B(θ) measurement; Class L ⊃ Clifford ⊃ {π/2-rotations})
∘ I (cyclic-group action: S=√Z, CNOT, CZ, Pauli; ℤ/2^n stabiliser groups)
∘ M (tensor-product bind: register composition; multi-qubit Hilbert space)
∘ C (cascade-orientation: Bell-basis measurement; conditional feed-forward)
∘ A (stabiliser-fingerprint content-addressing: substrate-agnostic algorithm identifier)
```

All 5 attestations bit-exact. All 14 A-N classes intact. Cascade is the Gottesman-Knill simulator at primitive level.

## §14 — Files

- `spike136_quantum_computing_via_cascade_without_brute_force.md` (this file)
- `spike136_quantum_computing_via_cascade_without_brute_force.py` (5-algorithm cascade trace + QFT T-count boundary demo; runs bit-exactly; pure Python + numpy)
- `spike136_findings_2026-05-18.ndjson` (~22 records: framing + class-by-class attestation + 5-algorithm verification + boundary demo + verdict + fermata)

## §15 — Refs

Task `#562`; Spike #136 (this); parent stance `[[user_stance_cascade_composition_is_quantum_algorithm]]` (2026-05-18).

### PDF-verified arXiv preprints (per `[[reference_autonomous_validation_tos_landscape]]`)

- **Gottesman 1998** ([arXiv:quant-ph/9807006](https://arxiv.org/abs/quant-ph/9807006)) — *The Heisenberg Representation of Quantum Computers*; stabiliser formalism foundation.
- **Aaronson, Gottesman 2004** ([arXiv:quant-ph/0406196](https://arxiv.org/abs/quant-ph/0406196)) — *Improved Simulation of Stabilizer Circuits*; PRA 70:052328; polynomial-time, thousands of qubits, CHP simulator, ParityL completeness, O(n²/log n) canonical form.
- **Bravyi, Kitaev 2005** ([arXiv:quant-ph/0403025](https://arxiv.org/abs/quant-ph/0403025)) — *Universal Quantum Computation with ideal Clifford gates and noisy ancillas*; PRA 71:022316; magic-state distillation promotes Clifford to universal.
- **Bravyi, Browne, Calpin, Campbell, Gosset, Howard 2018** ([arXiv:1808.00128](https://arxiv.org/abs/1808.00128)) — *Simulation of quantum circuits by low-rank stabilizer decompositions*; non-Clifford T-count drives exponential simulation cost; stabiliser rank χ ≈ 2^O(T-count).
- **Grover 1997** ([arXiv:quant-ph/9706033](https://arxiv.org/abs/quant-ph/9706033)) — *Quantum mechanics helps in searching for a needle in a haystack*; O(√N) quadratic speedup.
- **Shor 1995** ([arXiv:quant-ph/9508027](https://arxiv.org/abs/quant-ph/9508027)) — *Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer*; SIAM J. Comput. 26:1484; QFT + period-finding.

### Cite-by-ref (publisher PDF extraction restricted per `[[reference_autonomous_validation_tos_landscape]]`)

- **Bernstein, Vazirani 1993** — *Quantum complexity theory*, STOC '93 (cite-by-ref; ACM).
- **Simon 1994** — *On the power of quantum computation*, FOCS '94 (cite-by-ref; IEEE).
- **Nielsen & Chuang 2010** — *Quantum Computation and Quantum Information* (Cambridge UP, 10th anniversary ed.) §§1.4–4.4 (cite-by-ref; book).
- **Gottesman 1997** — *Stabilizer Codes and Quantum Error Correction*, Caltech PhD thesis (cite-by-ref; thesis).
- **Mermin 1990** — *Extreme quantum entanglement in a superposition of macroscopically distinct states*, Phys. Rev. Lett. 65:1838 (cite-by-ref; APS).
- **Solovay 1995** / **Kitaev 1997** — Solovay-Kitaev theorem (cite-by-ref).

### Project anchors (internal)

- Parent: `[[user_stance_cascade_composition_is_quantum_algorithm]]` (2026-05-18)
- Parent: `[[user_stance_bell_inequality_as_canonical_identity_signature]]` (cumulative identity stack)
- Spike #128.2 PR #561 — first complete-algorithm procedural anchor (Deutsch-Jozsa via L+I+M+C)
- Spike #128.1 PR #556 — bit-exact CHSH Tsirelson 2√2 shipped as code
- Spike #128 PR #535 — quantum entanglement networks cross-substrate cascade-match
- Spike #21C — Hopf-bundle U(1) single-qubit anchor
- Spike #58.P — sin²θ_W = 1/4 Cl(6,ℂ) 3-qubit anchor
- Spike #106 — Cl(7,ℂ) J² = I_16 visible/dark partition anchor
- `[[user_stance_identity_not_implementation_discipline]]` — umbrella discipline
- `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` — research methodology
- `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]` — algebra-only scope
- `[[user_stance_kepler_shape_universal]]` — cascade-shape-universality precedent
- `[[user_stance_asymptotic_dof_sidesteps_infinity]]` — Class K asymptote framing

### Memory anchors

- `[[feedback_trauma_informed_defensive_scope]]`
- `[[feedback_pdf_extraction_citation_discipline]]`
- `[[feedback_no_lineage_claims_in_notebook]]`
- `[[feedback_no_privileged_primitive_classes]]`
- `[[feedback_no_mvp_framing]]`
- `[[feedback_no_binding_layer_carveout]]`
- `[[reference_autonomous_validation_tos_landscape]]`
- `[[feedback_autonomous_research_followup_authorization]]`
- `[[feedback_every_doc_edit_faces_falsification]]`
- `[[feedback_no_squash_merges]]`
- `[[feedback_rc_stacking_versioning]]`
- `[[feedback_science_is_ssot_not_project]]`
- `[[feedback_ndjson_over_bloated_json]]`
