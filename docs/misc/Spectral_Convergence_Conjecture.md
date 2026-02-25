# Spectral Convergence Conjecture

## Status and Purpose

**Status**: HDC branch shelved. UTLP application layer requires scalar time. This document preserves what we learned so that when HDC returns, every implementation is spectrally grounded from day one.

**What this document is**: A precisely stated conjecture with proof sketch, honest gap flags, and a practical design mandate extracted from cross-domain research across six fields. It is a roadmap to a proof, not a claimed proof.

**What this document is not**: A finished theorem. The seams between the three component theorems have not been verified for technical condition matching. A specialist in functional analysis could find errors in the boundary conditions that we cannot catch.

---

## The Conjecture

**Spectral Optimality Conjecture for Finite-Dimensional Representation Systems**

*For any representation system operating on a locally compact group G with inner-product similarity and finite-dimensional approximation constraints, the optimal basis converges to the irreducible representations of G.*

More precisely:

Let G be a locally compact group acting on a domain X. Let Φ: X → ℝ^d be a finite-dimensional encoding such that similarity is measured by inner product ⟨Φ(x), Φ(y)⟩. Let the target be a positive-definite shift-invariant kernel K(x,y) = κ(x⁻¹y) on G. Then among all orthonormal bases for the d-dimensional encoding space, the basis that minimizes mean squared approximation error of K is the truncated set of irreducible representations of G (i.e., the generalized Fourier basis on G).

**Claim**: This single statement, when instantiated with appropriate group actions, explains why six independent research communities converged on spectral structure over randomness:

| Domain | Group G | Encoding Φ | Observed convergence |
|--------|---------|------------|---------------------|
| Neural network init | O(n) orthogonal group | Weight matrices | Orthogonal > Gaussian (Hu et al. 2020) |
| Transformer PE | (ℝ, +) translation | Positional encoding | Sinusoidal/RoPE = Fourier basis on ℝ |
| HDC/VSA | ℤ_p cyclic groups | Phase chord encoding | Structured > random (VFA 2021, SSPs 2020) |
| CDMA | (ℤ₂ⁿ, ⊕) | Spreading codes | Walsh-Hadamard > PN codes |
| Approximation theory | [-1,1] with Chebyshev measure | Polynomial basis | Chebyshev = KLT for Markov processes |
| Grid cells (biology) | ℝ² translation | Neural firing patterns | Hexagonal = irreps of wallpaper group |

---

## Proof Sketch: Three Theorems Chained

The conjecture follows from chaining three classical theorems. Each arrow below is individually proven. The composite chain has not been published as a single result.

### Arrow 1: Symmetry → Spectral Basis (Peter-Weyl Theorem)

**Theorem (Peter-Weyl, 1927)**: Let G be a compact group. Then L²(G) decomposes as a direct sum of finite-dimensional irreducible unitary representations of G. The matrix coefficients of these representations form a complete orthonormal basis for L²(G).

**What it gives us**: Any function on a compact group has a "Fourier series" in terms of the group's irreducible representations. For G = S¹ (the circle), these are the standard Fourier modes e^{inθ}. For G = SO(3), they are spherical harmonics. For finite cyclic groups ℤ_p, they are roots of unity.

**Application**: Marchetti et al. (2023, "Harmonics of Learning") proved that a neural network invariant to a finite group G provably recovers the Fourier transform on G — the irreducible representations emerge as the network's learned features. This demonstrates Peter-Weyl is not just a decomposition theorem but a *convergence attractor* for learning systems with symmetry constraints.

### Arrow 2: Spectral Basis → Kernel Design (Bochner's Theorem)

**Theorem (Bochner, 1933)**: A continuous function κ: ℝ^d → ℂ is positive-definite if and only if it is the Fourier transform of a finite positive Borel measure μ:

κ(x) = ∫ e^{iω·x} dμ(ω)

**What it gives us**: Every valid similarity kernel is fully determined by a spectral measure. Choosing a frequency distribution IS choosing a kernel. This is not analogy — it is mathematical identity.

**Application**: The VFA theorem (Frady et al. 2021) proved that in Vector Symbolic Architectures, the distribution of phases in base vectors determines the reproducing kernel of the representation space. Rahimi & Recht (2007) showed random Fourier features approximate any shift-invariant kernel by sampling from its spectral measure. Both are direct applications of Bochner's theorem: frequency selection = kernel design.

### Arrow 3: Spectral Basis → Optimal Approximation (Karhunen-Loève Theorem)

**Theorem (Karhunen 1947, Loève 1948)**: Let X(t) be a second-order stochastic process with covariance function C(s,t). The eigenfunctions {φ_n} of the covariance operator

∫ C(s,t) φ_n(t) dt = λ_n φ_n(s)

form the orthonormal basis that minimizes the mean squared error for any truncated d-dimensional approximation. No other orthonormal basis can do better.

**What it gives us**: If you must represent a smooth process in d dimensions, the spectral basis of its covariance is provably optimal. For stationary processes, the eigenbasis converges to the Fourier basis (Toeplitz structure of the covariance). For first-order Markov processes on [-1,1], the eigenbasis is asymptotically the DCT — which is Chebyshev evaluation at nodes.

**Application**: This explains why DCT dominates compression (JPEG, MP3, video), why Chebyshev polynomials provide minimax optimal approximation, and why SORF-DCT projections match or beat dense random projections at O(n log n) cost (Yu et al. NeurIPS 2016).

### The Chain

```
Group symmetry on domain          (observed in all six fields)
        │
        ▼ Peter-Weyl
Irreducible representations       (the "natural" spectral basis)
form complete orthonormal basis
        │
        ▼ Bochner
Frequency distribution of basis   (frequency selection = kernel design)
determines the similarity kernel
        │
        ▼ Karhunen-Loève
Spectral eigenbasis minimizes     (spectral basis is provably optimal)
truncated approximation error
        │
        ▼
PREDICTION: Systems that start random and are allowed to learn
will converge toward spectral structure. Systems that are designed
with spectral structure will outperform random counterparts.
```

This prediction matches the observed trajectory in every domain examined.

---

## Gap Flags: Where the Proof Could Break

The following technical conditions are where the three theorems' inputs and outputs may not perfectly match. These are the places a rigorous proof would need to do real work.

### GAP 1: Compactness

Peter-Weyl requires a **compact** group. Several domains operate on non-compact groups:

- Transformer PE encodes position on (ℝ, +), which is not compact
- Grid cells encode position on ℝ², which is not compact
- UTLP phase chords operate on ℤ_p (finite cyclic groups, which ARE compact — no gap here)

**Severity**: Medium. The standard workaround is to work on the Bohr compactification or restrict to bounded domains where the group action is effectively compact. Practical systems always have finite range, making the non-compactness formal rather than operational. But "works in practice because the domain is bounded" is not the same as "the theorem applies."

**What a proof needs**: Quantitative error bounds for Peter-Weyl on bounded subsets of non-compact groups. These exist in specific cases (e.g., windowed Fourier analysis) but would need to be assembled for the general statement.

### GAP 2: Positive-Definiteness and Shift-Invariance

Bochner requires the kernel to be **positive-definite** and **shift-invariant** (depending only on x⁻¹y, not on x and y separately).

- Cosine similarity in HDC is positive-definite and shift-invariant for circular convolution binding ✓
- Dot-product similarity in neural networks is positive-definite but NOT shift-invariant for general weight matrices
- CDMA cross-correlation is shift-invariant for cyclic codes but only approximately so for truncated linear codes

**Severity**: Medium-high. The shift-invariance requirement is the strongest constraint. Many real systems use kernels that are approximately but not exactly shift-invariant. Bochner's theorem is exact only for exact shift-invariance.

**What a proof needs**: Perturbation bounds — if the kernel is ε-close to shift-invariant, how close is the optimal basis to the Fourier basis? Rahimi & Recht (2007) and follow-up work provide some of this machinery but it hasn't been assembled for the general case.

### GAP 3: Stationarity

Karhunen-Loève optimality requires **second-order stationarity** (the covariance function depends only on the time difference, not absolute time).

- UTLP phase chords: stationary by construction (coprime cycles are periodic) ✓
- Natural signals (images, audio): approximately stationary locally, not globally
- Neural network hidden states: stationarity depends on the data distribution

**Severity**: Low-medium. Most practical applications satisfy local stationarity, and KLT optimality degrades gracefully (the spectral basis remains good, just not provably the best). The bigger issue is that KLT optimality is for *linear* approximation — binarization in HDC is nonlinear.

**What a proof needs**: Extension of KLT optimality to quantized/binarized representations. Some work exists (rate-distortion theory, vector quantization) but hasn't been connected to the HDC context specifically.

### GAP 4: The Binarization Boundary

UTLP and standard HDC binarize the superposition: sign(Σ rotated base vectors). This is a hard nonlinearity that the three theorems don't directly address. The theorems predict optimality in continuous L² spaces. Binarization projects onto {-1, +1}^d, where the optimal continuous basis might not remain optimal.

**Severity**: High for formal proof. Low for practical impact. Empirically, spectrally structured vectors outperform random ones even after binarization (Sobol quasi-random results: 9.8-10.8% accuracy improvement). But the formal gap is real — nobody has proved that spectral optimality survives binarization in general.

**What a proof needs**: A quantization-aware version of the KLT optimality result, showing that the spectral basis minimizes post-binarization error. This would likely require tools from dithered quantization theory or sigma-delta modulation analysis.

### GAP 5: Cross-Domain Vocabulary Alignment

The six domains use different mathematical formalisms for what may be the same underlying structure:

| Domain | What they call it | Formal object |
|--------|------------------|---------------|
| Neural nets | Dynamical isometry | Singular values of Jacobian ≈ 1 |
| HDC/VSA | Kernel design via VFA | Spectral measure of reproducing kernel |
| Audio | Resonator transfer function | Frequency response H(ω) |
| CDMA | Spreading code cross-correlation | Aperiodic autocorrelation function |
| Approximation theory | Chebyshev/KLT optimality | Eigenbasis of covariance operator |
| Neuroscience | Grid cell module ratios | Spatial frequency of periodic firing |

**Severity**: Medium. These are plausibly the same mathematical object (spectral measure / frequency response) in different notations, but formally proving their equivalence requires working through each domain's specific definitions and showing they reduce to the same thing under appropriate identification maps.

**What a proof needs**: Explicit isomorphism between each pair of formalisms, or (more elegantly) showing each is an instance of a single abstract framework — which is essentially what the conjecture claims but hasn't proven.

---

## What IS Proven (No Gaps)

To be clear about what stands on solid ground:

1. **Orthogonal initialization outperforms Gaussian in deep networks** — Hu et al. ICLR 2020, Theorem 4.1. Width independent of depth vs linear scaling.

2. **Frequency distribution determines kernel in VSA** — Frady et al. 2021 (VFA theorem). This is a rigorous theorem, not an observation.

3. **DCT = Chebyshev evaluation at nodes** — Mathematical identity: T_n(cos θ) = cos(nθ).

4. **Chebyshev basis is minimax optimal for polynomial approximation** — Equioscillation theorem, 1853.

5. **KLT eigenbasis minimizes MSE for truncated approximation** — Consequence of spectral theorem, textbook result.

6. **Walsh-Hadamard codes achieve zero mutual interference in synchronous CDMA** — Proven and deployed in IS-95, WCDMA.

7. **Grid cells encode position via periodic patterns at multiple scales** — Nobel Prize 2014 (Moser & Moser), extensively replicated.

8. **Grid cell encoding ↔ Transformer positional encoding** — Li et al. 2024 (GridPE), formally published.

9. **Grid cell encoding ↔ VSA phase encoding** — Multiple papers 2020-2025 (Residue HDC, GC-VSA, SSPs).

10. **Neural networks with group invariance provably learn Fourier features** — Marchetti et al. 2023 ("Harmonics of Learning").

The conjecture synthesizes these proven results into a single statement. The proven parts are individually rock-solid. The gaps are in the seams.

---

## Can AI Synthesize the Missing Proof?

Assessed honestly:

**What AI can do**: State the conjecture precisely (done above). Draft the proof sketch showing how the three theorems chain (done above). Identify the gap flags where technical conditions don't match (done above). This scaffolding is genuine — a mathematician could pick it up, verify the solid parts, and focus effort on the flagged gaps.

**What AI cannot reliably do**: Verify that the boundary-condition analysis is watertight. The dangerous territory is generating plausible-sounding measure theory for Gaps 1-4 that passes casual inspection but fails under specialist scrutiny. We will not attempt this.

**The honest position**: The conjecture is almost certainly true (every empirical test across six domains confirms it). The proof strategy is clear (chain Peter-Weyl → Bochner → KL). The gaps are identified and bounded. What remains is technical work at the seams — likely publishable by someone with the right functional analysis background, but not safely automatable.

---

## HDC Design Mandate for UTLP

When HDC returns to UTLP, the following design rules are non-negotiable. They are grounded in convergent evidence from neural networks, neuroscience, communications, approximation theory, and audio synthesis.

### Rule 1: No Random Base Vectors. Ever.

The random-to-structured trajectory is documented in every field that tried both approaches. Random binary vectors (rng.choice([-1, 1])) are the HDC equivalent of Xavier initialization — a reasonable starting point that structured approaches provably outperform.

**Minimum**: Chebyshev-seeded base vectors via DCT-II evaluation at Chebyshev-Gauss nodes:
```
LUT[n][k] = cos(n · (2k - 1) · π / (2D))
```

**Better**: SORF-DCT construction (DCT × random sign flips) — combines structured spectral shaping with diversity. This is the exciter-resonator architecture: DCT = resonator body, sign flips = excitation.

**Best**: Spectrally partitioned Chebyshev vectors with explicit band assignment per coprime cycle (see Rule 3).

### Rule 2: The LUT Is the Instrument Body

The 20K lookup table generated at bootup is not a computational convenience. It is the resonator — the spectral transfer function that shapes every phase chord excitation into a spectrally structured output. This is mathematically identical to the exciter-resonator decomposition in physical modeling synthesis (Karplus-Strong 1983, Smith digital waveguide synthesis).

- **Phase chord** = exciter (impulse pattern, changes every tick)
- **LUT** = resonator (spectral transfer function, fixed at bootup)
- **Regenerated vector** = shaped output (convolution of impulse with transfer function)

Design the LUT deliberately. The Chebyshev degree assignments, spectral weighting, and bandwidth allocation are instrument voicing decisions that determine the timbre of every vector the system produces.

### Rule 3: Spectral Partitioning Over Statistical Orthogonality

Assign each coprime cycle a distinct spectral band:

```
Cycle p₁ (241): Chebyshev degrees 1-30    (bass — coarse temporal structure)
Cycle p₂ (251): Chebyshev degrees 31-60   (low-mid)
Cycle p₃ (239): Chebyshev degrees 61-90   (mid)
...
Cycle p₈ (211): Chebyshev degrees 211-240 (treble — fine temporal detail)
```

This makes inter-cycle interference spectrally separable (DCT decomposition identifies which cycle is corrupted) rather than statistically averaged (random vectors only tell you "something is wrong"). It is the difference between an orchestra (instruments in non-overlapping spectral bands) and white noise (all energy everywhere).

The specific degree assignments above are illustrative. Optimal assignment is an open instrument-voicing problem (the "Stradivarius question"). But ANY spectral partitioning is better than no spectral partitioning.

### Rule 4: Pre-Binarization Magnitudes Are Information

The float32 superposition before sign() binarization contains confidence information at every dimension:

- **Large magnitude** (node): Multiple cycles agree → high confidence
- **Near-zero magnitude** (antinode): Cycles partially cancel → low confidence, carries inter-cycle relationship information

Current implementation discards this with sign(). Future HDC implementation should at minimum:
- Store or transmit magnitude statistics alongside binary vectors
- Use magnitude-weighted similarity (dimensions where the speaker is "loud" count more than dimensions where the speaker "whispers")
- Use antinode locations for Byzantine fault detection (antinodes are where corruption first becomes visible)

### Rule 5: Frequency Selection Is Kernel Design

Per VFA theorem (Frady et al. 2021): the distribution of frequencies in base vectors determines the reproducing kernel of the representation space. This means the Chebyshev degree assignments in Rule 3 are not just "nice to have" spectral structure — they literally define what "similar" means in the vector space.

Choosing low-degree Chebyshev modes = smooth, wide kernel = coarse similarity (nearby times look very similar, distant times look very different, sharp boundary).

Choosing high-degree modes = oscillatory, narrow kernel = fine similarity (even nearby times look somewhat different, enabling high temporal resolution but lower noise tolerance).

The LUT configuration IS the kernel. Design it for the application's similarity requirements.

### Rule 6: Design for Spectral Separability in Multi-Swarm Contexts

When multiple swarms coordinate, their vector spaces should occupy non-overlapping spectral bands — the same principle as OFDM in communications. Swarm A uses bass Chebyshev degrees, Swarm B uses midrange, Swarm C uses treble. Composite vectors from inter-swarm bundling are separable by DCT filtering without codebook lookup.

This is CDMA → OFDM evolution applied to HDC: moving from statistical code separation (random spreading codes / random base vectors) to deterministic spectral separation (orthogonal subcarriers / partitioned Chebyshev bands).

---

## Cross-Domain Evidence Summary

Six independent research communities converged on the same conclusion using different vocabularies. No single paper unifies them. The citation graph fragments at Rahimi & Recht 2007 (the only shared ancestor).

### Published cross-domain connections
- Grid cells ↔ Transformer PE: Li et al. 2024 (GridPE)
- Grid cells ↔ VSA: Kymn et al. 2025 (Residue HDC), Krausse et al. 2025 (GC-VSA), Dumont & Eliasmith 2020 (SSPs)
- HDC ↔ Kernel methods: Frady et al. 2021 (VFA theorem)
- Group invariance ↔ Fourier features in NNs: Marchetti et al. 2023 ("Harmonics of Learning")
- Orthogonal > Gaussian for random features: Yu et al. NeurIPS 2016
- VSA ↔ Transformer attention: emerging ICLR 2025 work

### Unpublished but mathematically grounded
- Dynamical isometry ↔ VFA kernel design (both concern spectral distributions controlling representation quality)
- CDMA spectral partitioning ↔ HDC (Walsh-Hadamard shared tool, no formal analogy published)
- Exciter-resonator ↔ non-audio computation (the LUT-as-resonator insight — Category 3)
- Full six-domain unification under Peter-Weyl + Bochner + KL (this document's conjecture)

### The key unpublished gap (SORF-DCT → HDC)
Zhang & Zhou (Neurocomputing 2024) published SORF-DCT for kernel approximation. VFA (Frady et al. 2021) proved HDC encodings are random Fourier features. The logical connection — apply SORF-DCT to HDC base vector construction — has zero publications. This is the most immediately actionable gap and likely the first thing to implement when HDC returns.

---

## Candidate Unifying Theorems (For Reference)

These are the three theorems whose assembly would close the conjecture. All are individually textbook material.

**Peter-Weyl (1927)**: Functions on compact groups decompose into irreducible representations. *Predicts*: spectral bases emerge from symmetry.

**Bochner (1933)**: Positive-definite shift-invariant kernels are Fourier transforms of positive measures. *Predicts*: frequency distributions determine similarity structure.

**Karhunen-Loève (1947-48)**: Eigenbasis of covariance operator minimizes truncated approximation error. *Predicts*: spectral basis is optimal for finite-dimensional encoding.

**Together they predict**: whenever a domain involves (a) group symmetry, (b) inner-product similarity, and (c) finite-dimensional approximation of smooth structure → spectral basis is optimal. All six domains satisfy conditions (a), (b), and (c).

---

## Future Work

When HDC returns to UTLP:

1. **Implement SORF-DCT base vectors** — the lowest-hanging fruit from the gap analysis
2. **Benchmark spectral vs. random** — partition detection accuracy, similarity curve sharpness, Byzantine fault identification specificity
3. **Test spectral partitioning** — assign Chebyshev degree bands per coprime cycle, measure whether DCT analysis can identify which cycle is corrupted
4. **Explore magnitude-weighted similarity** — compare binary Hamming distance vs float32 magnitude-weighted dot product
5. **Listen to the vectors** — map 10,000 dimensions to audio samples. What does drift sound like? What does Byzantine corruption sound like? The ear catches structure that statistics miss.

When the conjecture is ready for formal publication:

6. **Commission specialist review** — the gap flags (particularly GAP 2: shift-invariance perturbation bounds and GAP 4: binarization survival) need functional analysis expertise
7. **Frame as cross-domain survey with gap analysis** — title: "Spectral Convergence in Representation Systems: A Cross-Domain Survey" — document the pattern, map the citations, propose the three theorems as candidate unifying principles
8. **Do not overclaim** — this is synthesis, not discovery. Every individual result is someone else's theorem. The contribution is seeing that they're all the same theorem in different clothes.

---

*Document version: 2026-02-24*
*Context: HDC branch shelved in favor of scalar time for application layer. This document preserves research from the spectral convergence investigation for future HDC implementation.*
