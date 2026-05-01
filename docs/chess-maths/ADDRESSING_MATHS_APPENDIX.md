# Addressing-Maths Research Thread: Appendix

**Status:** Reference document. Captures findings from the coprime-indexed addressing on ℤ/Dℤ research thread that frame chess's coprime construction in a broader mathematical context but do not directly bind on the chess representation. The one finding that *did* augment chess-maths landed in [chess_spectral_research_notebook.md §9f](chess_spectral_research_notebook.md#9f-coprime-roll-binding-utlp-s3--spatial-hdc) as the "Packing-optimality side-result" paragraph; everything else is preserved here.

**Source thread:** "Coprime-Indexed Addressing on ℤ/Dℤ — A Working Research Notebook" (Phase 1 hypothesis battery A-H1…B-H2) plus its A-H2/A-H3 corrections and the 15/16 ceiling theorem document.

**Position in the project.** The addressing-maths thread is the foundation/generalization layer under chess-maths, [Othello-maths](../othello-maths/) (chess notebook §10), and [logo-maths](../logo-maths/) (chess notebook §9l). All three are empirical instances of the same coprime-folded addressing pattern φ(i₁,…,i_k) = Σ pⱼ·iⱼ mod D with the cyclic group algebra ℂ[ℤ/Dℤ] as the efficient-operation class. This appendix records what the foundation says.

**Scope discipline.** Findings here are preserved as research artifacts. They do not modify the chess construction, do not introduce new chess claims, and do not require the chess notebook to be re-read in light of them. The chess construction at D ∈ {512, 640} is a single embedding of an 8×8 grid; the multi-grid packing results below describe the structure of ℤ_D under that embedding pattern but the chess representation never packs multiple grids.

---

## A.0 — Phase 1 hypothesis battery summary

| Hypothesis | Question | Status | Headline |
|---|---|---|---|
| A-H1-strict | Two 8×8 grids pack into ℤ_1024 with odd-unit 4-tuple (p,q,r,s) and disjoint images | **FAIL** | Structural: φ(0,0) = 0 always, so images share 0 |
| A-H1-offset | Same with per-grid offset b₂ added (5-tuple) | **PASS** | 94,703 valid second-pairs admit some disjoint b₂ |
| A-H2 | max N grows linearly with D/64 for 2-power D | **PASS** (corrected to 15/16 ceiling) | True max N(D) = (15/16)·(D/64) by CP-SAT, not the original greedy "+7" |
| A-H3 | Non-2 prime-power D packs closer to volume bound than 2-power D | **PASS** | non-2 prime-power D saturates ratio 1.000; 2-power D plateaus at 15/16 |
| A-H4 | CRT-factored packing equals direct packing | **PASS** | Identical valid-pair sets at D = 1001 (7·11·13) and D = 323 (17·19) |
| B-H1 | Every chess piece operator is in ℂ[ℤ/Dℤ] | **PASS** (primary) | 384/384 on (D=640, p=67, q=7); structural tautology by construction |
| B-H2 | NTT agrees with direct; crossover depends on \|S\| | **PASS** | Up to 5.93× speedup; knight loses at D=4096 (\|S\|=8 too small for FFT constants) |

**Status flag.** A-H1-strict was the plan's anticipated "publishable infeasibility note." A-H2's "+7 closed form" was a path-dependent greedy artifact, replaced by the 15/16 structural ceiling under exact CP-SAT enumeration.

---

## A.1 — The 15/16 Ceiling Theorem (Z₁₆ Fourier Obstruction)

This is the structural result that explains the 1/16 packing slack on 2-power D. The chess notebook §9f cites it briefly; the full statement and proof live here.

### A.1.1 — Setup

For (p, q) odd-units in ℤ_{2^m} (m ≥ 4), let

    image(p, q) = {p·r + q·c mod 2^m : r, c ∈ {0..7}}

This is the standard 8×8 Sidon image used throughout chess-maths and addressing-maths.

### A.1.2 — Theorem (mod-16 non-uniformity)

`image(p, q)` projected to ℤ₁₆ is non-uniform.

**Proof.** Let A_u = {u·c mod 16 : c ∈ {0..7}}, an 8-element subset of ℤ₁₆. The DFT of `1_{A_u}` on ℤ₁₆ is

    F_u(k) = Σ_{c=0}^{7} ω^(u·c·k)     where ω = exp(2πi/16).

If k ≠ 0 mod 16:

    F_u(k) = (ω^(8uk) − 1) / (ω^(uk) − 1).

For k odd: uk is odd (u is a unit), so 8uk ≡ 8 (mod 16), giving ω^(8uk) = −1. Numerator = −2, denominator = ω^(uk) − 1 ≠ 0. Hence |F_u(k)| = 2 / |ω^(uk) − 1| = 1 / |sin(π·uk/16)| > 0.

For k even nonzero (k = 2j, j ∈ {1..7}): 8uk = 16uj ≡ 0 (mod 16), giving ω^(8uk) = 1. Numerator = 0. Hence F_u(k) = 0.

So F_u vanishes precisely at the 7 even nonzero frequencies of ℤ₁₆ and is nonzero at the 8 odd frequencies.

The image's mod-16 multiplicity vector is m_I = 1_{A_p} ∗ 1_{A_q} (ℤ₁₆ convolution). By the convolution theorem, m̂_I(k) = F_p(k) · F_q(k). At odd k: F_p(k) ≠ 0 and F_q(k) ≠ 0, so m̂_I(k) ≠ 0.

A constant function has DFT supported only at k=0. Since m̂_I has 8 nonzero entries at odd frequencies, m_I is non-constant. □

### A.1.3 — Corollaries

**Corollary 1.** `image(p, q)` does not tile ℤ_{2^m} for any m ≥ 10.

A tiling I ⊕ S = ℤ_{2^m} with |I|=64, |S|=2^(m−6) requires the projection to ℤ₁₆ to satisfy `1̂_I(k) · 1̂_S(k) = 0` for all k ≠ 0 in ℤ₁₆. By the theorem, m̂_I is nonzero at all 8 odd frequencies, so m̂_S would need to vanish there. The same argument applies at finer projections (ℤ₃₂, ℤ₆₄, …), each adding constraints. Empirically all 243,712 valid Sidon-injective images on ℤ_1024 fail mod-16-balance, and CP-SAT confirms no image reaches N=16.

**Corollary 2.** Maximum disjoint-translate packing of `image(p, q)` on ℤ_{2^m} satisfies N ≤ 2^(m−6) − 1 = volume − 1 (for m ≥ 10).

Volume bound is 2^(m−6); equality requires perfect tiling, which Corollary 1 forbids.

### A.1.4 — Conjecture (15/16 sharp ceiling)

For odd-unit p, q on ℤ_{2^m} (m ≥ 10) with `image(p, q)` Sidon-injective on the 8×8 grid:

    max packing N(p, q, 2^m) ≤ (15/16) · 2^(m−6) = 15 · 2^(m−10).

**Evidence.**
- Verified TIGHT and OPTIMAL at m=10 (N=15) and m=11 (N=30) by CP-SAT.
- Verified ACHIEVABLE at m=12 (N≥60 by CP-SAT FEASIBLE).
- Theorem A.1.2 alone gives N ≤ vol − 1 (loose: 31 at m=11 vs actual 30; 63 at m=12 vs conjectured 60).
- The constant 15/16 ratio across m=10, 11, 12 strongly suggests a structural law.

The full proof of the conjecture likely uses the ℤ₁₆ obstruction at all higher finer-projection levels jointly (ℤ₃₂, ℤ₆₄, …, ℤ_{2^m}), in the spirit of Coven–Meyerowitz / Tijdeman tiling theory.

### A.1.5 — Why uniform up to mod-8, broken at mod-16

The image is uniform mod 2, 4, 8 (multiplicities {32,32}, {16,16,16,16}, {8,8,8,8,8,8,8,8}) but breaks at mod 16. The reason: for odd u in ℤ_{2^k}, the set u·{0..7} mod 2^k reduces SURJECTIVELY onto ℤ₈ (each ℤ₈ coset hit exactly once when 2^k ≥ 8), so mod 8 every image element falls into a unique ℤ₈ coset of the relevant 2^k group.

At mod 16: u·{0..7} mod 16 has 8 elements but only fills 8 of the 16 possible residues (a transversal mod 8 inside ℤ₁₆). The distribution among ℤ₁₆ residues depends on u, and the convolution of two such 8-element-ℤ₁₆-transversals is never uniform.

In bit-flag language: side = 2³ = 8 elements is uniform up to bit 3 of the address but loses uniformity at bit 4. That is the obstruction.

---

## A.2 — A-H1: Strict 4-tuple FAIL → Offset-Aware 5-tuple PASS

### A.2.1 — The strict 4-tuple is structurally impossible

The plan asked: "Do there exist 4-tuples (p, q, r, s) ∈ ((ℤ/1024ℤ)*)⁴ such that (p, q) and (r, s) each embed the 8×8 board injectively and the two images are disjoint in ℤ_1024?"

For any D and any generator pair (p, q), φ(0, 0) = (p·0 + q·0) mod D = 0. Both grids therefore always contain phase 0, and the two images can never be disjoint. The prediction is infeasible for *all* D, not just ℤ_1024.

**Verdict (strict): FAIL.** Trivial infeasibility from the common corner. This is the "publishable infeasibility note" the addressing-maths plan §6.2 anticipated.

### A.2.2 — The research-relevant 5-tuple

The chess §11 phase-operator construction treats `phi_origin` as an additive offset:

    P_rook(φ_origin) = {φ_origin + delta mod D : delta ∈ S_rook}.

VSA role-binding (Plate 1995; Kanerva 2009) does the same with a different name (per-object HV offset). Generalizing to two grids:

    φ_g(r, c) = (b_g + p_g·r + q_g·c) mod D

WLOG b₁ = 0 (overall translation is a group symmetry of ℤ_D). The research-relevant question becomes: do there exist (p₁, q₁, p₂, q₂, b₂) with both pairs injective and the two offset images disjoint?

This reduces to finding b₂ in the complement of the difference set image_1 − image_2 in ℤ_D.

### A.2.3 — Numbers (D = 1024)

```
valid (odd-unit) pairs on ℤ_1024:           243,712  (92.97% of odd²)
canonical first (67, 7) valid:              True
seconds admitting SOME disjoint offset:      94,703  (38.86% of valid seconds)
example 5-tuple (p₁, q₁, p₂, q₂, b₂):       (67, 7, 1, 9, 519)
sample mean admissible b₂ per second:        36.1 (SE 6.7, n=200)
est. 5-tuples with canonical first:         ~8.8 × 10⁶
```

**Verdict (offset): PASS.** Existence is confirmed constructively. 38.9% of valid second-pairs admit at least one disjoint offset; on average each admissible second-pair has ~36 valid offsets out of D = 1024.

### A.2.4 — What this means for chess

The infeasibility of A-H1-strict is not a counterexample to the plan; it is the plan's own worst-case flag realized. The trivial (0, 0) corner forces that outcome, and the offset-aware version is what the chess §11 and Othello §1c constructions were doing all along without stating it as a formal definition. The corrected primitive is a 5-tuple (p₁, q₁, p₂, q₂, b₂), not a 4-tuple, and chess §11.2.1's `phi_origin` parameter is exactly this offset.

This formalizes what chess-maths §11 implicitly does: per-piece origin offsets are not a convenience, they are a structural requirement once two grids must coexist in the same ℤ_D.

---

## A.3 — Ring-Theoretic Findings (A-H2, A-H3, A-H4)

### A.3.1 — A-H2: Linear scaling on 2-power D

Translation packing (disjoint translates of `image(67, 7)`) on D ∈ {1024, 2048, 4096, 8192} initially gave N = 7, 21, 49, 105 under smallest-b-first greedy, fitting N(D) = 7·(D−512)/512 with R²=1.0000. **This was a path-dependent algorithm artifact.**

Under exact CP-SAT (proven OPTIMAL where reported):

| D       | greedy N | random multistart | CP-SAT          | volume bound | true_max / vol |
|--------:|---------:|------------------:|:----------------|-------------:|---------------:|
| 1024    | 7        | 13–14             | **15** OPTIMAL  | 16           | 15/16 = 0.9375 |
| 2048    | 21       | 24                | **30** OPTIMAL  | 32           | 30/32 = 0.9375 |
| 4096    | 49       | 47                | ≥60 FEASIBLE    | 64           | ≥60/64 = 0.9375 |
| 8192    | 105      | 86                | (not solved)    | 128          | (≥0.67)        |

Greedy continues with greedy(16384)=217, greedy(32768)=434, greedy(65536)=868 — the "+7" pattern breaks at m=15 then resumes, characteristic of a path-dependent algorithm rather than a theorem.

**Corrected verdict.** True maximum disjoint-translate packing of `image(67, 7)` on ℤ_{2^m} for m=10, 11 is exactly (15/16) · volume, proven by CP-SAT. The 15/16 ratio is explained by the §A.1 ℤ₁₆ Fourier obstruction.

### A.3.2 — A-H3: Prime-power D vs 2-power D anomaly

Translation packing across 2-power and non-2 prime-power D, with canonical generator chosen per D (smallest (p, q) with p ≠ q in units(ℤ_D)² that embeds 8×8 injectively, excluding bases 2, 5):

| D    | Factor | Volume (D/64) | (p, q) | Nmax | Ratio |
|-----:|-------:|--------------:|-------:|-----:|------:|
| 1024 |   2¹⁰  |            16 | (1, 9) |   14 | 0.875 |
| 2048 |   2¹¹  |            32 | (1, 9) |   28 | 0.875 |
| 4096 |   2¹²  |            64 | (1, 9) |   57 | 0.891 |
|  729 |    3⁶  |            11 | (1, 8) |   11 | **1.000** |
| 2401 |    7⁴  |            37 | (1, 8) |   37 | **1.000** |

Mean ratio (2-power D) = 0.880 (greedy); mean ratio (non-2 prime-power D) = 1.000.

**Corrected reading.** The 12% gap on 2-power D is greedy; under true CP-SAT max it's exactly 1/16 = 6.25%. Non-2 prime-power D continues to saturate exactly (verified at D=625, 729, 2401, 3125, 4913). The original direction (2-power D harder than prime-power D) is correct, but magnitude ~doubles when moved from greedy to true max, and the structural reason is the §A.1 mod-16 obstruction specific to 2-power D.

**Verdict: PASS.** Non-2 prime-power D saturates the volume bound exactly. 2-power D plateaus at the 15/16 structural ceiling.

### A.3.3 — A-H4: CRT decomposition equivalence

The ring isomorphism ℤ_D ≅ ∏ ℤ_{m_j} (Ding–Pei–Salomaa 1996) lets us either enumerate (p, q) directly in units(ℤ_D)² or factor each into residue tuples (p_j, q_j) ∈ units(ℤ_{m_j})² and reconstruct via CRT. Both must produce the same valid-pair set.

| D    | Moduli       | Direct count | CRT count | Equivalent |
|-----:|:------------:|-------------:|----------:|:----------:|
| 1001 | 7 × 11 × 13  |      478,080 |   478,080 |    True    |
|  323 | 17 × 19      |       62,784 |    62,784 |    True    |

**Verdict: PASS.** The plan's "15-threshold" qualifier (each m_j ≥ 15) is *not* required for set equivalence (D = 1001 works despite m_j ∈ {7, 11, 13}); it is required for per-factor injectivity to hold independently. When some m_j < side, per-factor injectivity fails in those factors but the combined Diophantine constraint over ℤ_D can still be satisfied because the other factors compensate.

### A.3.4 — Practical consequence

Pick D as a product of non-2 prime powers for tight packing; factor via CRT for search efficiency. The chess regime ℤ_640 = 2⁷ × 5 has the 2-adic slack from §A.1 in its 2⁷ factor. Pure non-2 prime-power D (e.g., ℤ_729·2401) would pack tighter by §A.3.2 + §A.3.3. This is the Residue-HDC pattern (Kymn et al. 2025) realized on the addressing-maths substrate.

---

## A.4 — Group-Algebra Closure (B-H1) and NTT Acceleration (B-H2)

### A.4.1 — B-H1: Every chess piece operator is in ℂ[ℤ/Dℤ]

Six piece shift sets per chess §11.2:

```
S_rook(p, q)         = {±k·p : k ∈ [1, 7]} ∪ {±k·q : k ∈ [1, 7]}
S_bishop(p, q)       = {±k·(p+q) : k ∈ [1, 7]} ∪ {±k·(p−q) : k ∈ [1, 7]}
S_queen(p, q)        = S_rook ∪ S_bishop
S_king(p, q)         = {±p, ±q, ±(p+q), ±(p−q)}
S_knight(p, q)       = {±(2p+q), ±(2p−q), ±(p+2q), ±(p−2q)}
S_pawn_advance(p, q) = {p, 2p}
```

**Numbers — primary case (p, q) = (67, 7), D = 640:**

```
rook      |S|=28   origins matching: 64/64  (100.00%)
bishop    |S|=28   origins matching: 64/64  (100.00%)
queen     |S|=56   origins matching: 64/64  (100.00%)
king      |S|= 8   origins matching: 64/64  (100.00%)
knight    |S|= 8   origins matching: 64/64  (100.00%)
pawn_adv  |S|= 2   origins matching: 64/64  (100.00%)
overall: 384/384  (100.00%)
```

This reproduces chess §11.3's 416/416 result generically (not hard-coded to 640).

**Secondary structural probes** (six combinations of (p, q, D) including 2-power D and prime-power D) hit 2014/2688 = 74.9% overall — geometric equivalence depends on (D, p, q), not on ℂ[ℤ/Dℤ] membership alone.

**Structural reading.** Group-algebra closure is a *structural tautology by construction* — each P_piece IS Σ_{δ ∈ S_piece} S^δ ∈ ℂ[ℤ/Dℤ] because that is how we defined it. The substantive test is whether the phase reachable set clips to the geometric reachable set, and that clipping is (D, p, q)-dependent. The chess answer ((67, 7), D ∈ {512, 640, 768}) is exactly the chess construction; the addressing-maths generalization is a question about when the phase-operator torus and the geometric board share enough structure that the torus-clip (chess §11.3.3) yields the geometric moves.

### A.4.2 — B-H2: NTT crossover

For a fixed piece P with shift set S_P and an occupation vector o ∈ {0, 1}^D, the reachability vector is

    r = circular_convolve(o, χ_{S_P})     in ℤ/D arithmetic,

where χ_{S_P}[δ] = 1 iff δ ∈ S_P. Two implementations benchmarked at 32-piece occupation, 20 trials each:

| D    | Piece  | \|S\| | direct (ms) | NTT (ms) | Speedup | Correct? |
|-----:|:------:|----:|------------:|---------:|--------:|:--------:|
|  640 | queen  |  56 |      0.141  |   0.103  |  1.37×  |     ✓    |
|  640 | knight |   8 |      0.020  |   0.010  |  1.94×  |     ✓    |
|  640 | rook   |  28 |      0.070  |   0.012  |  5.93×  |     ✓    |
| 1024 | queen  |  56 |      0.137  |   0.028  |  4.92×  |     ✓    |
| 1024 | knight |   8 |      0.020  |   0.014  |  1.46×  |     ✓    |
| 4096 | queen  |  56 |      0.138  |   0.047  |  2.96×  |     ✓    |
| 4096 | knight |   8 |      0.021  |   0.039  |  **0.54×**  |     ✓    |
| 4096 | king   |   8 |      0.021  |   0.039  |  **0.55×**  |     ✓    |

Correctness holds everywhere (max discrepancy < 1e-6). The crossover is in shape: queen (|S|=56) consistently benefits; knight/king (|S|=8) lose at D=4096 because numpy.fft constants dominate for small shift sets.

**Verdict: PASS.** O(D log D) versus O(D·|S|) reproduced with crossover quantified. For chess move generation the queen is where NTT matters most; small-|S| pieces favor direct on small D.

**Connection to chess-maths §11.4.5.** §11.4.5 reports a 6.5×–7.5× speedup of phase-native arithmetic over python-chess at pseudo-legal scope. That is the operational manifestation of B-H1 + B-H2: piece operators are in ℂ[ℤ/Dℤ] (so the speedup class is well-defined) and NTT is one realization of that class (so the asymptotic is O(D log D)). Chess §11.4.5's measurement is naive Python integer arithmetic vs python-chess's reference, not NTT; an NTT-backed implementation at D=640 with |S|=56 (queen) would extract additional benefit per A.4.2's 1.37× direct-vs-NTT delta.

---

## A.5 — Synthesis: Crossovers between A and B

The six hypotheses braid onto a single substrate: linear Diophantine conditions on tuples (p, q) ∈ (ℤ/Dℤ)², plus the group algebra ℂ[ℤ/Dℤ], plus CRT factorization. Four concrete crossovers surfaced:

1. **A-H1 ↔ A-H2.** The offset-aware 5-tuple primitive from A-H1 is what A-H2 counts at scale. Without the offset b, two grids share (0, 0) and N > 1 is impossible; with b, N grows linearly with D/64 at the corrected 15/16 ceiling.

2. **A-H3 ↔ A-H4.** A-H3 quantifies the 2-adic slack (1/16 = 6.25% on 2-power D under true CP-SAT max; 0% on non-2 prime-power D). A-H4 verifies the ring isomorphism ℤ_D ≅ ∏ ℤ_{m_j}. Together: pick D as a product of non-2 prime powers for tight packing, factor via CRT for search efficiency. This is Residue-HDC (Kymn et al. 2025) realized on the addressing-maths substrate.

3. **A-H1/A-H2/A-H3 ↔ B-H1.** The "valid 2D generators" set used by A-experiments is the same set whose geometric equivalence B-H1 tests. A-experiments count *how many* valid pairs exist; B-H1 tests *which* of those pairs reproduce chess-geometric behavior on an 8×8 clip. The chess canonical (67, 7) is a single member of A-H1's 243,712-element valid set, and the question of which other members give geometric equivalence is open (secondary probes hit 75% overall, not 100%).

4. **B-H1 ↔ B-H2.** B-H1 certifies that piece operators ∈ ℂ[ℤ/Dℤ]; B-H2 certifies that this class is NTT-accelerable. Composition: if your operation is an element of the group algebra, you get O(D log D) via NTT with crossover quantified by B-H2. Anything *outside* ℂ[ℤ/Dℤ] (non-circulant matrices, graph-specific operations on non-Cayley graphs) does not benefit.

The cross-sub-question crossovers A ↔ C (Diophantine independence ↔ RRNS range-check duality), A ↔ D (Singleton as upper envelope), and C ↔ D (RRNS subsumes D for pure-CRT) are addressing-maths Phase 2 items not addressed in this appendix.

---

## A.6 — Connections to chess-maths sections

Where each addressing-maths finding lands in (or relates to) the chess notebook:

| Addressing-maths finding | Chess-maths section | Relationship |
|---|---|---|
| Diophantine condition `p·Δr + q·Δc ≢ 0 (mod D)` | §9f "Generator-selection requirement" | Already in chess-maths verbatim (discovered via Othello Phase 1 pass) |
| (3, 7) on D=1024 collision counterexample | §9f, §10.12 bug 2 | Already in chess-maths |
| (67, 7) packing-optimality at D=1024 (15/16, CP-SAT) | §9f "Packing-optimality side-result" | **Distilled into chess-maths** (this appendix's only direct chess-notebook contribution) |
| 15/16 ceiling theorem (ℤ₁₆ Fourier obstruction) | §9f reference | Cited briefly in chess-maths; full proof in §A.1 of this appendix |
| A-H1-strict structural impossibility → 5-tuple offset | §11.2.1 `phi_origin` | Implicit in chess-maths; formalized here |
| A-H2 linear scaling (corrected to 15/16) | (none direct) | Background; chess uses single embedding, not multi-grid packing |
| A-H3 prime-power D saturates | (none direct) | Structural background |
| A-H4 CRT decomposition equivalence | (none direct) | Structural background |
| B-H1 group-algebra closure | §11.3 (chess validation 416/416) | B-H1 is the structural framing of what §11 verifies |
| B-H2 NTT speedup | §11.4.5 phase-native speedup measurement | B-H2 is the asymptotic theory; §11.4.5 is the empirical chess measurement |
| Othello (7, 11) on D=768 | §10.12 H7 | Othello instance of the same construction |
| Logo HDC vocab × syntax | §9l | Logo instance (different projection on same substrate) |

**Summary.** One finding (packing-optimality of (67, 7)) was pulled into chess-maths §9f. The rest is preserved here as structural background that frames why the chess construction works and what its mathematical neighborhood looks like.

---

## A.7 — Literature grounding

Consolidated from the addressing-maths research plan §3–§5, ordered roughly by recurrence:

- Erdős, P. & Turán, P. (1941). On a problem of Sidon in additive number theory. *J. London Math. Soc.* 16.
- Bose, R.C. & Chowla, S. (1962). Theorems in the additive theory of numbers. *Comment. Math. Helv.* 37.
- Davis, P.J. (1979/1994). *Circulant Matrices*. Wiley.
- Pollard, J.M. (1971). The fast Fourier transform in a finite field. *Math. Comp.* 25.
- Plate, T.A. (1995). Holographic reduced representations. *IEEE TNN* 6(3).
- Plate, T.A. (2003). *Holographic Reduced Representation: Distributed Representation for Cognitive Structures*. CSLI.
- Kanerva, P. (2009). Hyperdimensional computing. *Cognitive Computation* 1(2).
- Mandelbaum, D. (1972). Error correction in residue arithmetic. *IEEE TIT* IT-18.
- Yau, S.S. & Liu, Y.C. (1973). Error correction in redundant residue number systems. *IEEE TC* C-22.
- Ramsey, J.L. (1970). Realization of optimum interleavers. *IEEE TIT* 16(3).
- Forney, G.D. (1971). Burst-correcting codes for the classic bursty channel. *IEEE TCT* 19(5).
- Sun, J. & Takeshita, O.Y. (2005). Interleavers for turbo codes using permutation polynomials over integer rings. *IEEE TIT* 51(1).
- Bibak, K., Kapron, B.M., Srinivasan, V., Tauraso, R. & Tóth, L. (2017). Restricted linear congruences. *J. Number Theory* 171.
- Hedayat, A.S., Sloane, N.J.A. & Stufken, J. (1999). *Orthogonal Arrays*. Springer.
- Ding, C., Pei, D. & Salomaa, A. (1996). *Chinese Remainder Theorem: Applications in Computing, Coding, Cryptography*. World Scientific.
- Kymn, C.J., Kleyko, D., Frady, E.P., Bybee, C., Kanerva, P. & Sommer, F.T. (2025). Residue hyperdimensional computing. *Neural Computation* 37.
- Biggs, N. (1974/1993). *Algebraic Graph Theory*. Cambridge University Press.
- Vaidyanathan, P.P. & Pal, P. (2011). Sparse sensing with co-prime samplers and arrays. *IEEE TSP* 59(2).

**Coven–Meyerowitz / Tijdeman tiling theory** is the natural literature for proving the §A.1.4 conjecture (15/16 sharp ceiling); the partial proof in §A.1.2 uses the ℤ₁₆ obstruction alone, whereas the full sharp bound likely requires the joint obstruction across all finer projections ℤ₃₂, ℤ₆₄, …, ℤ_{2^m}.

---

## A.8 — Open directions (out of scope here)

These are flagged for completeness; none modify the chess construction.

1. **Freiman–Plünnecke–Ruzsa ↔ RRNS distance bridge.** Characterizes when image(φ) has small doubling (structured GAP complement, sharp bounds) vs pseudo-random complement (looser bounds). Components exist separately in the literature; no published paper writes the bridge explicitly.

2. **Memory-system Pareto analysis.** "Is a specific coprime multiplier optimal against empirically-characterized DRAM/flash burst distributions under a given outer code?" — legitimate research direction but requires hardware burst-length data not surveyed in this thread.

3. **Synthesis paper.** The addressing-maths thread's eventual deliverable: a packaging document positioning "coprime-folded addressing on finite cyclic groups, with the group algebra ℂ[ℤ/Dℤ] as the efficient-operation class and the image-set complement as the bounds/fault primitive" as a unified VSA-compatible design principle, with chess/Othello/logo as empirical instances. Working title: "Coprime-folded addressing on finite cyclic groups as a VSA design principle: packing feasibility, group-algebra closure, and RRNS duality."

4. **Sharp 15/16 ceiling proof.** §A.1.4 conjecture; the structural Fourier obstruction at ℤ₁₆ is established but the sharp bound likely requires the joint obstruction at all finer projections.

---

*This appendix is a research-record document. It may be amended as the addressing-maths thread produces additional findings, but its scope is bounded: capture what the foundation says about chess-maths's coprime construction, do not duplicate chess-maths content, do not invent new chess claims.*







