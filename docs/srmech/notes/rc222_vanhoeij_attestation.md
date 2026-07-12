# rc222 — van Hoeij LLL knapsack recombination: attested construction (MPM)

**Purpose.** Before writing ANY van Hoeij code, the exact lattice construction was
extracted from the actual sources (not coded from memory). This note lodges the
sources, their SHA-256 hashes, and the construction as implemented in rc222.

## Sources (fetched + extracted 2026-07-11)

1. **Mark van Hoeij, "Factoring polynomials and the knapsack problem",
   *J. Number Theory* 95 (2002) 167–189** — author's OA copy:
   - URL: <https://www.math.fsu.edu/~hoeij/knapsack/paper/May16_2001/knapsack.pdf>
   - `sha256(pdf) = 798c43d074c3a23f44b0d9bf1b8e3325fb15c4f0e2d69b6f03fa8727c864c04d`
   - Text extracted with pypdf; the construction below quotes §2 (Lemmas 2.1–2.10,
     Definition 2.2, Theorem 2.1, §2.1 "The knapsack lattice", §2.2 "The
     algorithm", §2.3 remarks 2–4).
2. **Jürgen Klüners, "The van Hoeij Algorithm for Factoring Polynomials"**,
   in *The LLL Algorithm* (Springer, 2010) — author's OA copy:
   - URL: <https://math.uni-paderborn.de/fileadmin-eim/mathematik/AG-Computeralgebra/Publications-klueners/factor_lll.pdf>
   - `sha256(pdf) = 88b7e05a2dc047371e39806c6fcf8084fc4272c22a34deffcb21021f6cb4b183`
   - Confirms the knapsack-lattice shape (§3), the Λ = [[I | traces],[0 | p^a·I]]
     block layout (§4, there stated with the full coefficient vector of Φ(g) =
     f·g′/g; van Hoeij's paper's TRACE form is the one implemented here), the
     Gram–Schmidt cutoff lemma ("Lemma 1", = LLL-paper (1.11)), and the Zassenhaus
     baseline the recombination replaces.
3. **Fujiwara root bound** (used for the trace bounds B_i): Wikipedia,
   "Geometrical properties of polynomial roots" —
   <https://en.wikipedia.org/wiki/Geometrical_properties_of_polynomial_roots>
   (`sha256(fetched html, 2026-07-11) =
   d073c81dd3be55a6e3793195306726eb7f05d9d7b5df0c05307cf471c73e6296`; formula
   verified verbatim in the page's math alttext):
   every root of a_n·x^n + … + a_0 satisfies
   `|α| ≤ 2·max( |a_{n−1}/a_n|, |a_{n−2}/a_n|^{1/2}, …, |a_1/a_n|^{1/(n−1)}, |a_0/(2·a_n)|^{1/n} )`
   (M. Fujiwara, 1916). rc222 uses the exact-integer CEILING of every
   intermediate (ceil-div + integer k-th-root ceilings), so the computed bound
   only ever rounds UP — it stays a valid upper bound. Cross-checked against the
   Cauchy bound `1 + max|a_i|/|a_n|` (von zur Gathen & Gerhard, *Modern Computer
   Algebra*, ch. 6); rc222 takes the MIN of the two (both are valid upper bounds).

## The attested construction (van Hoeij 2002, §2), as implemented

Let `f ∈ ℤ[x]`, square-free, primitive, `deg f = N`, lead coefficient `lc`. The
Zassenhaus pipeline (already in srmech) supplies monic p-adic factors
`f̃_1 … f̃_n` of the monic associate of `f`, lifted to `mod m = p^k` with
`p^k ≥ 2·(Mignotte bound)+1`.

- **Traces (Newton power sums).** `Tr_i(g) = Σ roots^i`. For monic `g` of degree
  `d` with `g = x^d + Ẽ_1·x^{d−1} + … + Ẽ_d` (`Ẽ_i = 0` for `i > d`), the Newton
  identity (paper eq. (2)):
  `P_i = −i·Ẽ_i − Σ_{k=1}^{i−1} P_k·Ẽ_{i−k}` — computed `mod p^k`.
  `Tr_i(g1·g2) = Tr_i(g1) + Tr_i(g2)` (additivity; Lemma 2.3 extends to any
  integer exponent vector v).
- **Non-monic scaling (§2.3 remark 4).** For non-monic `f`, `Tr_i` is replaced by
  `lc^i·Tr_i` (that is an integer for every rational factor because `lc·α_j` are
  algebraic integers).
- **Bounds.** If `B_rt` bounds all complex roots of `f`, then `|Tr_i(g)| ≤
  d·B_rt^i` for any rational factor `g` of degree ≤ d (paper §2 p.8) — rc222 uses
  `B_i = N·(|lc|·B_rt)^i` for the scaled traces. Choose `b_i` with
  `B_i < p^{b_i}/2` and `a_i` with `b_i < a_i ≤ k` (paper: "one must have
  a ≥ a_i > b_i > log(2B_i)/log(p)").
- **Two-sided cut (Definition 2.2 + eq. (8)).** For `r = lc^i·Tr_i(f̃_j) mod
  p^{a_i}`: let `r̄` = symmetric remainder of `r` mod `p^{b_i}`; `u = (r − r̄)/p^{b_i}`;
  the lattice entry is `c̄_{j,i}` = symmetric remainder of `u` mod `p^{a_i−b_i}`.
  ("the i'th entry of C_j is an approximation of the i'th entry of T^b_A(f_j)
  with accuracy a_i − b_i, and is a two-sided cut".)
- **The knapsack lattice (§2.1).** With `L = ℤ^n` (first step), scaling constant
  `C` chosen so the two terms under `M = sqrt(C²·n + s·(n/2)²)` balance, the
  basis of `Λ ⊆ ℤ^{n+s}` is the rows of

  ```
  ( C·I_n | c̄_{j,i} matrix (n×s) )
  ( 0     | p^{a_i−b_i}·I_s      )
  ```

  Every solution subset S (a true factor) yields the M-short vector
  `v_S = (C·v_1 … C·v_n, ε_1 … ε_s)` with `v ∈ {0,1}^n`, `|ε_i| ≤ |S|/2 ≤ n/2`
  (Theorem 2.1; the `γ_i·p^{a_i−b_i}` parts are absorbed by the second block).
- **Read-off (§2.1 + Lemma 2.9).** LLL-reduce `B_Λ`; with the Gram–Schmidt basis
  `V*_k`, let `r ≤ l` be minimal such that `|V*_k| > M` for all `k > r`; then ALL
  M-short vectors lie in `ℤV_1 + … + ℤV_r` (LLL paper (1.11); Klüners Lemma 1).
  `L′ = (1/C)·(projection of span{V_1..V_r} onto the first n coordinates)`, and
  `W ⊆ L′` (Lemma 2.9). If `L = W`, the reduced-row-echelon basis of `L` is
  exactly the set of 0–1 block-indicator vectors `w_1 … w_r` (Lemma 2.8:
  condition A "each column of rref contains precisely one 1, all other entries
  0"; condition B: each candidate `g_k = symmetric-rep(lc·Π_{v_i=1} f̃_i mod p^a)`
  made primitive must divide `f` in ℤ[x] — checked "in exactly the same way as
  in the Berlekamp-Zassenhaus algorithm", §2.3 remark 4 for the non-monic
  lead·product + primitive-part form).

## rc222 implementation choices (within the attested construction)

- **Strategy 1 / one-shot** (§2.3 remark 2): `T_A = Tr_{1..s}` (A = identity —
  the first-s-traces matrix), single lattice reduction with a generous
  information budget `I` (remark 3 recommends `I ≈ 0.12·n²` nats for a one-step
  finish; rc222 targets `(18·n²)/100 + 64` BITS ≥ that), instead of the gradual
  multi-pass L-refinement. If the one shot does not resolve, rc222 falls back to
  the subset enumeration (never iterates the lattice) — a SPEEDUP-only posture.
- **Uniform a_i − b_i = e** (same p-power for every trace row): `e = ⌊t_bits /
  ⌊log2 p⌋⌋ + 1` with per-trace target `t_bits = n + 8` bits. Traces with
  `b_i + e > k` are dropped (never lift further); zero usable traces ⇒ fallback.
- **Exact GSO cutoff**: the `|V*_k| > M` test is done in EXACT rational
  arithmetic (4·‖V*‖²·den-vs-num integer compare against `4M² = 4C²n + s·n²`),
  not the paper's floating-point-plus-error-bound variant — strictly stronger
  (no round-off term needed).
- **Column-equality block decode** (equivalent to rref condition A when
  `W ⊆ L′`): columns j, j′ of the kept projected rows are equal **iff** j, j′
  belong to the same factor block. Proof sketch (from Lemma 2.8's uniqueness
  argument): if `L′ = W`, each kept-basis row is an invertible integer
  combination of the block indicators, so column j equals the λ-column of its
  block, and an invertible matrix has pairwise-distinct columns; conversely a
  merge of two true blocks would force every vector of `L′ ⊇ W ∋ w_A` to be
  constant across the union — contradiction. Requiring #classes = r (the kept
  row count) rejects `L′ ≠ W` over-splits; the replay's exact ℤ trial division
  (condition B) rejects everything else.
- **Byte-identity replay.** The decoded blocks are emitted through the SAME
  candidate/trial-division code as the subset enumeration, in the exact order
  the enumeration would find them (ascending size, lexicographic index tuple),
  INCLUDING the subset-cap and half-bound exits — so a successful van Hoeij pass
  produces output byte-identical to the exponential path, and ANY failure falls
  back to the exponential path wholesale.
