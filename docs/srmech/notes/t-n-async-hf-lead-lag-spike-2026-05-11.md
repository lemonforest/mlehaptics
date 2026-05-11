# T^N quantum-walk lift vs Hayashi-Yoshida — async-HF lead-lag spike findings (2026-05-11)

**Spike:** Does the project's T^N quantum-walk lift `U(t) = exp(−i L_corr t)` on a correlation Laplacian recover asynchronous lead-lag relationships at competitive accuracy with the Hayashi-Yoshida (2005) estimator on synthetic async-sampled price series with KNOWN lead-lag structure?

**Method:** Concertmaster role; MPM-discipline (closed-form numpy/scipy; no SGD; deterministic seed `20260511`). Synthetic 6-asset benchmark with known fixed lags `τ ∈ {0,1,2,3,5,10}`; horizon `T=5000` time units; independent Poisson async sampling (mean inter-arrival 1.0); follower noise std 0.005 vs leader vol 0.01. 20 independent trials. Three diagnostic methods: (i) Hayashi-Yoshida 2005 (canonical finance baseline); (ii) T^N quantum-walk lift on real correlation Laplacian (control — magnitude only); (iii) T^N quantum-walk lift on **complex** correlation Laplacian via cross-spectrum (load-bearing test, per srmech §3.5.1 layer (b)). Plus three anomaly chases: initial-state choice, omega-band sensitivity, easier-SNR regime, and a **direct cross-spectrum phase counter-experiment** that exposes the failure mode.

**Dispatch:** [financial-scoping-2026-05-11.md](financial-scoping-2026-05-11.md) Fermata 2 + [fiedler-vs-hrp-vs-gics-spike-2026-05-11.md](fiedler-vs-hrp-vs-gics-spike-2026-05-11.md) Fermata 2 deferred lift test.

**Bottom line: T^N quantum-walk lift UNDERPERFORMS Hayashi-Yoshida at the load-bearing benchmark.** Best Spearman ρ = +0.362 on the canonical setup (HY = 1.000 perfect); ρ = -0.96 in the easier-SNR regime (sign systematically wrong); ρ = +0.92 from DIRECT cross-spectrum phase (Welch coherence) which the T^N lift purportedly unifies. **The financial round's most novel claim (finding #7) does NOT survive the dedicated benchmark.** Honest data; the L_H propagator aggregation destroys the lag information that pairwise cross-spectrum preserves.

---

## 1 — Setup + data recipe

**Synthetic price-series benchmark.** Leader follows a discrete GBM on a fine reference grid (`fine_dt = 0.05` units; drift 0; volatility 0.01 per unit time). Followers are lagged copies of the leader at fixed integer lags + independent Gaussian noise:

| Parameter | Value | Source |
|---|---|---|
| `N_ASSETS` | 6 | leader + 5 followers |
| `LAG_SCHEDULE` | `[0, 1, 2, 3, 5, 10]` | known ground truth |
| `T_HORIZON` | 5000.0 | time units; ~5000 samples/asset at λ=1 |
| `SAMPLING_INTENSITY` | 1.0 / unit | Poisson process per asset (independent) |
| `VOL` | 0.01 / unit time | leader GBM volatility |
| `FOLLOWER_NOISE_STD` | 0.005 | additive per-follower noise |
| `N_TRIALS` | 20 | independent realizations per trial |
| `TN_TIMES` | `[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]` | propagator evolution sweep |
| `HY_LAG_MAX` | 15 | HY-grid search range (±15 units) |
| `Seed` | `20260511` | deterministic |

**Ground-truth lag matrix.** `L_true[i, j] = τ_j − τ_i` with sign convention: `τ_ij > 0` iff asset i leads asset j.

**Sampling.** Each asset independently drawn from a homogeneous Poisson process; the lead/follow structure is encoded in **price values** (interpolated from the leader at the asset's lag-shifted time), not in sampling timestamps. Sampling is genuinely asynchronous: each asset has a different set of observation times.

**Sign conventions verified** by walkthrough: leader at lag 0, follower at lag 1; HY argmax should occur at `lag = -1` per the shift logic; `tau_ij = -argmax_lag = +1` matches `L_true[leader, follower1] = +1`. The implementation matches.

---

## 2 — Three methods implemented

| Method | Library calls | Lag extraction |
|---|---|---|
| **(i) Hayashi-Yoshida 2005** | Vectorized cumulative covariance estimator (`np.searchsorted` for overlap-range indexing + `cumsum` for fast j-increment sums) | `tau_ij = -argmax_{lag ∈ [-15, 15]} HY_cov(i, j, lag)` |
| **(ii) T^N real Laplacian (control)** | `eigh(L_real)`; `L_real = D − \|C\|` from `np.corrcoef` on grid-aligned returns | `tau_ij = -arg(U(t)[i,j]) / omega_band` where `omega_band` is FFT-band midpoint |
| **(iii) T^N complex Laplacian (load-bearing)** | `eigh(L_complex)` Hermitian; `L_complex = D − C_complex` where `C_complex` is band-averaged Welch cross-spectrum normalized to coherence | Same lag extraction; `U(t) = V·diag(exp(−i·λ·t))·V†` |

All three methods are closed-form numerical linear algebra. No SGD. No test-set tuning. Deterministic seed.

**HY implementation note (algorithmic).** The naive HY estimator costs `O(N_i × N_lag)` per pair via interval search; with N_i ~ 5000 and N_lag = 31 and 30 pairs × 20 trials, this is ~93 million Python loop iterations (~5+ minutes wall clock and the first attempt locked up). The vectorized variant uses precomputed cumulative sums on `dp_j` and computes the j-interval range per i-interval via `np.searchsorted` on `(e_j_shifted, s_j_shifted)` simultaneously. Total runtime: 8 seconds for the full 20-trial spike. Listed here because the speed-up is load-bearing for the 20-trial bootstrap; algorithmically equivalent to the original HY 2005 sum.

---

## 3 — Metric table

### 3.1 Headline metrics (20 trials, default benchmark)

| Method | Spearman ρ | MAE | Sign accuracy | Verdict |
|---|---|---|---|---|
| **(i) Hayashi-Yoshida 2005** | **1.000** [1.000, 1.000] | **0.000** [0.000, 0.000] | **1.000** [1.000, 1.000] | **PERFECT** |
| (ii) T^N real Laplacian (control) | −0.629 to −0.743 across t | 8.24 to 10.42 | 0.000 to 0.160 | Fails by construction (symmetric U) |
| **(iii) T^N complex Laplacian LIFT** | **+0.362** best (t=0.05) | 9.57 | 0.41 | **WEAK; underperforms HY by far** |

HY is **deterministically perfect** on this synthetic benchmark across all 20 trials. The clean leader/follower structure, ~5000 observations/asset, and integer-grid lags are well within HY's regime of strong identifiability — but this is exactly the regime in which an alternative method would need to compete to claim "competitive with HY."

**T^N complex Laplacian best result: ρ = +0.362 at t = 0.05.** Weakly positive, but the gap to HY's 1.000 is enormous. The implicit unification claim from `financial-scoping-2026-05-11.md` finding #7 ("T^N lift unifies Hayashi-Yoshida + Welch coherence + Onnela dynamic asset trees on the same eigenbasis") is not borne out at this benchmark.

### 3.2 T^N complex-lift evolution sweep

| t | MAE | Spearman ρ | Sign accuracy |
|---|---|---|---|
| 0.05 | 9.565 | **+0.362** | 0.410 |
| 0.10 | 9.592 | +0.348 | 0.407 |
| 0.20 | 9.824 | +0.307 | 0.373 |
| 0.50 | 10.151 | +0.229 | 0.310 |
| 1.00 | 10.752 | −0.008 | 0.220 |
| 2.00 | 10.609 | −0.228 | 0.160 |
| 5.00 | 7.682 | −0.191 | 0.370 |

Maximum ρ is at the shortest evolution time tested. As `t → 0`, `U(t) → I + O(t)` and `arg(U(t)[i,j]) ≈ -t · (L_complex)[i,j]` to first order; **the lift's information content at small t is just the original off-diagonals of L_complex**, which already encode cross-spectrum phase. The lift adds nothing at small t. At larger t, eigenmode mixing destroys the per-pair phase structure (ρ degrades, then becomes negative).

### 3.3 T^N real-Laplacian control

| t | MAE | Spearman ρ | Sign accuracy |
|---|---|---|---|
| 0.05 | 10.390 | −0.629 | 0.000 |
| 0.50 | 10.405 | −0.631 | 0.000 |
| 2.00 | 9.909 | −0.655 | 0.000 |
| 5.00 | 8.238 | −0.743 | 0.160 |

**Sign accuracy 0% across most of the sweep** is the expected pathology: a real symmetric Laplacian has real symmetric eigendecomposition, so `U(t) = exp(−i L_real t)` is COMPLEX-SYMMETRIC, i.e., `U(t)[i,j] = U(t)[j,i]`. Therefore `arg(U[i,j]) = arg(U[j,i])`, giving `tau_ij = tau_ji`. Lag is asymmetric (`L_true[i,j] = -L_true[j,i]`), so 100% of estimated pairs have the WRONG sign. This control confirms the test logic and shows definitively that **magnitude-only correlation cannot encode lead-lag direction.**

---

## 4 — The diagnostic: direct cross-spectrum phase WORKS where T^N FAILS

The dispatch flagged the T^N lift as unifying Welch coherence + Hayashi-Yoshida + dynamic asset trees. If the lift truly unifies them, the lift should perform at least as well as Welch coherence alone. We tested this:

### 4.1 Direct cross-spectrum phase (Welch coherence) at single frequencies

| omega (cycles/unit) | MAE | Spearman ρ | Sign accuracy |
|---|---|---|---|
| **0.020** | 21.524 | **+0.923** | **0.933** |
| 0.050 | 24.693 | +0.596 | 0.867 |
| 0.100 | 14.453 | −0.496 | 0.267 |
| 0.200 | 9.516 | −0.169 | 0.600 |
| 0.300 | 7.257 | −0.213 | 0.533 |
| 0.400 | 6.324 | −0.186 | 0.400 |

**At low frequency (omega = 0.020), direct cross-spectrum phase gives ρ = +0.923 and sign accuracy 0.933 — recovers lead-lag well.** Wraparound dominates at higher frequencies (lag 10 × omega 0.1 = π ≈ 3.14 rad ⇒ wraparound; at omega 0.2 lag 10 = 6.28 rad ≈ 2π full wrap), so the higher-omega bins fail. This is the standard Welch coherence finance practice (Hayashi & Yoshida 2005 surface a similar caveat about Nyquist-style wraparound limits).

### 4.2 Why this matters

The T^N lift's BEST result is ρ = +0.362 at t=0.05. The direct cross-spectrum phase's result is ρ = +0.923 at omega = 0.020. **Direct cross-spectrum phase OUTPERFORMS the T^N lift by 2.5×** on the same data with the same FFT preprocessing.

Mechanically, the T^N lift starts from `C_complex` (the same band-averaged cross-spectrum matrix that direct Welch coherence uses), but then it **constructs `L_complex = D − C_complex`** and propagates `U(t) = exp(−i L_complex t)`. The Laplacian aggregation step mixes pairwise phases through the global eigenstructure: the dominant low-eigenvalue eigenmodes (close to constant on the graph) dominate `arg(U[i,j])`, and these eigenmodes carry GLOBAL phase info (largely the leader's overall phase) NOT per-pair lag.

**The lift loses information** that direct cross-spectrum phase preserves. The dispatch's "T^N lift unifies Welch coherence + HY + dynamic asset trees" framing is INCORRECT at this benchmark: the lift is strictly worse than Welch coherence alone.

### 4.3 Easier-SNR regime probe

To rule out an SNR-bound failure, we ran a more favorable benchmark: shorter lags `[0,1,2,3,4,5]` (max lag 5 not 10; less wraparound risk) and 10× lower follower noise (0.001):

| Method | MAE | Spearman ρ | Sign accuracy |
|---|---|---|---|
| Hayashi-Yoshida | 0.000 | +1.000 | 1.000 |
| **T^N complex t=1.00** | 11.301 | **−0.959** | 0.000 |
| **T^N complex t=2.00** | 9.459 | **−0.968** | 0.000 |
| T^N complex t=5.00 | 6.920 | −0.581 | 0.400 |
| Direct cross-spectrum ω=0.05 | 15.338 | +0.679 | 0.867 |
| Direct cross-spectrum ω=0.10 | 13.735 | +0.417 | 0.600 |

**The T^N lift gives ρ ≈ −0.96 (strongly ANTI-correlated) in this easier-SNR regime.** The sign of every off-diagonal estimate is systematically WRONG (sign_acc = 0.0). This is a structural failure, not an SNR-bound limitation: at higher SNR, the lift's sign error becomes MORE consistent, not less.

The mechanism: the dominant low-eigenvalue eigenmode of L_complex is `~constant` on the graph and carries the leader's overall phase trajectory. When we evolve by `t = 1.0`, the propagator's arg mostly encodes the negative of this dominant phase — and that has the **wrong relative sign** to encode pairwise lag. Higher SNR amplifies this systematic sign error.

---

## 5 — Anomaly chase: initial-state choice

Per the previous Fiedler spike's anomaly 3 (uniform initial state is an eigenvector of the trivial λ=0 eigenvalue), we tested three initial-state choices. Used per-trial single benchmark for diagnostic purposes:

| Initial state | MAE | Spearman ρ | Sign accuracy |
|---|---|---|---|
| `uniform` (`ψ_0 = 1/√N`) | 4.182 | −0.477 | **0.600** |
| `per-asset impulses via U` (this is what the main metric used) | 9.556 | +0.198 | 0.267 |
| `random unit-norm complex` | 9.058 | −0.499 | 0.267 |

Interestingly the `uniform` state has BETTER sign accuracy (60%) than the impulse approach (27%), with a low MAE (4.18) — though Spearman ρ is anticorrelated. **Mechanism:** uniform state IS very close to the eigenvector of the trivial mode of L_complex (small eigenvalue), so `U(t) ψ_uniform ≈ ψ_uniform · exp(-i λ_0 t)`; the differential phase across assets reflects only second-order corrections from the mode mixing with higher eigenmodes. The differential phase happens to inherit some sign information from the spectral structure but at degraded accuracy.

**None of the three initial-state choices give competitive ρ.** The lift's failure is not an initial-state choice problem; it is a Laplacian-aggregation problem.

---

## 6 — Anomaly chase: omega band sensitivity

We tested 5 frequency-band choices for the cross-spectrum averaging that builds `C_complex`:

| Band | omega_midpoint | t_test | MAE | Spearman ρ |
|---|---|---|---|---|
| `very_low` (0.005–0.05) | 0.028 | 5.00 | 48.871 | −0.285 |
| `low` (0.01–0.10) | 0.055 | 5.00 | 33.971 | −0.681 |
| `wide_default` (0.01–0.50) | 0.255 | 3.92 | 9.558 | −0.530 |
| `mid` (0.05–0.20) | 0.125 | 5.00 | 10.257 | +0.077 |
| `high` (0.10–0.50) | 0.300 | 3.33 | 7.995 | **+0.333** |

The highest-frequency band gives the best ρ (+0.333), but it's still poor and barely above the main-default-band ρ = +0.362. **Omega-band tuning does not rescue the lift.** This confirms the structural failure — the issue is the L-aggregation, not the cross-spectrum preprocessing.

---

## 7 — Honest verdict per metric

**Load-bearing-question answer:** **The T^N quantum-walk lift `U(t) = exp(−i L_corr t)` on the complex correlation Laplacian DOES NOT recover async-HF lead-lag relationships at competitive accuracy with the Hayashi-Yoshida estimator.** At best ρ = +0.362 (vs HY 1.000); in the easier-SNR regime ρ = −0.96 (sign systematically wrong); the natural Welch-coherence baseline gives ρ = +0.92 (i.e., the lift is strictly worse than the Welch coherence it claims to unify).

The financial-scoping (2026-05-11) round's most novel claim (finding #7) **does not survive** the dedicated benchmark.

**Caveats — what was tested:**

- Synthetic clean GBM leader + lagged copies + low-magnitude Gaussian noise (not real market data; the easier regime here is the strongest claim regime).
- Fixed integer lags (real HF data has continuous lags; HY handles continuous lags too).
- 6 assets with one clear leader (small-N benchmark; real markets have hundreds of assets with diffuse lead-lag).
- Single time horizon (5000 units, ~5000 samples/asset on average; longer doesn't change the conclusion — it's a structural issue).
- Single sampling intensity (Poisson rate 1.0 per unit); we did not test microstructure-style very-high-intensity sampling, but Welch coherence already works in our test, so SNR is not the limiting factor.

**Caveats — what was NOT tested:**

- Tick-data microstructure noise (bid-ask bounce, etc.). Per the financial-scoping anomaly 2, T^N on raw HF data would need Realized-Kernel or HY pre-filtering; we operate on synthetic clean returns here.
- Adversarial Laplacian-construction variants (e.g., using `L = D^{-1/2}(D−A)D^{-1/2}` normalized, or `L = I − D^{-1/2} A D^{-1/2}`); we used combinatorial `L = D − A`. The structural failure mode is independent of this choice (the eigenvector mixing happens for any choice of L on a small dense graph).
- Real S&P 500 high-frequency cross-spectrum data (would require WRDS / NYSE TAQ access).
- Larger N (e.g., 50 or 500 assets) — the structural failure mode is expected to PERSIST at larger N since the dominant low-eigenvalue eigenmode of L_complex remains close-to-constant on the graph and dominates `arg(U)`.

**Caveats — methodological:**

- Single deterministic seed (`20260511`); bootstrap CIs on the headline metrics are tight (HY perfect across all 20 trials).
- HY's perfect recovery is partly an artifact of the synthetic clean recipe; on real data HY would be noisier but still the canonical benchmark.

---

## 8 — Anomaly log

**Anomaly 1: T^N complex lift gives weak positive correlation in default benchmark (ρ ≈ +0.36), strong NEGATIVE correlation in easier-SNR regime (ρ ≈ −0.96).** Higher SNR amplifies a SYSTEMATIC sign error in the lift's lag extraction. **Mechanism:** the dominant low-eigenvalue eigenmode of L_complex carries the leader's overall phase trajectory (close-to-constant on the graph); `arg(U(t)[i,j])` at moderate t is dominated by this mode's phase, which mostly inverts the per-pair lag direction. Higher SNR makes this dominant mode cleaner ⇒ the inversion is more systematic.

**Anomaly 2: T^N complex lift IS STRICTLY WORSE than direct cross-spectrum phase from the same `C_complex` matrix.** Direct Welch coherence at omega = 0.020 gives ρ = +0.92, sign_acc = 0.93; T^N lift gives ρ = +0.36 at best. The Laplacian aggregation step `D − C_complex` and propagator `exp(-i L t)` DESTROY information that the raw cross-spectrum matrix already contained. The dispatch's "lift unifies Welch + HY + dynamic asset trees" framing is incorrect; the lift is a LOSSY transform of `C_complex`, not a unification.

**Anomaly 3: T^N real-Laplacian control gives sign_acc = 0% across most evolution times.** Confirms by construction: real symmetric L gives `U(t)` complex-symmetric, so `arg(U[i,j]) = arg(U[j,i])` and the estimated lag is symmetric. Lag is anti-symmetric ⇒ 100% wrong sign. This is the expected behavior; useful control showing the test logic is correct.

**Anomaly 4: Omega-band tuning + initial-state choice + evolution-time sweep all fail to rescue the lift.** No combination of these hyperparameters produces ρ > 0.4 at the canonical benchmark. The structural failure mode is robust to hyperparameter choice.

**Anomaly 5 — partial-credit caveat: T^N lift DOES show weakly-positive ρ in the canonical benchmark.** Not zero, not random-chance: ρ ≈ +0.36 is detectable signal. The lift IS extracting some lag information; it just does so much less effectively than the simpler baseline. **Honest framing:** the lift is not a no-op; it just is not competitive.

---

## 9 — Fermata records

**Fermata 1: Most-novel claim of the financial-scoping round falls.** The financial-scoping (2026-05-11) headline finding #7 explicitly framed the T^N lift as the first project → external-domain new-information offering in finance. **The dedicated benchmark refutes this claim.** Conductor decision: how should §3.5.1 layer (b) of the srmech notebook update? Options:

- **(a)** Demote the T^N lift from "first cross-pollination project → external-domain win" to "candidate that did not survive its dedicated benchmark." Document the failure mode (Laplacian aggregation as lossy transform) honestly.
- **(b)** Re-scope the lift's claim: the lift may still be useful in OTHER settings (e.g., spectral graph clustering with phase-coherent dynamics, where the goal isn't per-pair lag extraction). The financial-scoping framing was specifically about cross-spectrum lead-lag, which the dedicated test refutes.
- **(c)** Investigate whether a DIFFERENT operator construction (not `exp(-i L t)` from `L = D − C_complex`) might preserve the per-pair phase information that direct cross-spectrum already contains. Speculative; no current candidate.

**Recommendation:** (a) + (b). Demote the cross-spectrum lead-lag claim explicitly; document the failure mode; re-scope the lift to settings where its inherent eigenmode-mixing behavior is feature not bug (e.g., spectral graph clustering with quantum-walk evolution; the lift's natural setting is closer to the chess-spectral and ephemerides-spectral existing applications cited in srmech notebook line 230).

**Fermata 2: Direct cross-spectrum phase IS the right finance baseline.** The Welch coherence approach at low frequency gives ρ = +0.92 with sign accuracy 0.93 on this synthetic benchmark — the natural finance baseline already works. The financial-scoping round identified this method (Welch coherence) as a sibling of HY and the lift's purported unification target. **The data say: Welch coherence is a valid finance baseline; HY is the gold standard; the T^N lift offers no improvement on either.**

**Fermata 3: srmech §3.5.1 layer (b) eigenphase-torus framework as math identity.** The T^N lift's math is correct (unitary evolution on a Hermitian L gives a T^N propagator). The math identity stands. **What falls is the practical claim** that this propagator is information-preserving for per-pair lag in a finance setting. The structural reason (L-aggregation as lossy transform) is mathematical, not numerical — applies to any cross-domain attempt to use the lift for per-pair phase extraction. The lift remains useful where its eigenmode-mixing IS the desired behavior (project's existing uses in chess_spectral and ephemerides_spectral — these are spectral graph-clustering / state-evolution applications, NOT pairwise-phase-extraction applications).

**Fermata 4: Conductor decision on financial-scoping headline.** Updates needed to financial-scoping-2026-05-11.md if conductor agrees with the recommended demotion:
- Headline finding #7: re-scope from "T^N lift unifies HY + Welch + dynamic asset trees" to "T^N lift is a math-identity that DOES NOT competitively recover per-pair lead-lag on the dedicated benchmark."
- EMDR-project-specific assessment win (10d): re-scope from "first project → external-domain pollination win on T^N quantum-walk lift" to "first project → external-domain candidate that did not survive its dedicated test."
- Sub-investigation 3 "verdict": update from "T^N lift IS new and useful" to "T^N lift IS new but is NOT competitive at the load-bearing setting."

---

## 10 — Recommended next actions

1. **srmech notebook update**: in §3.5.1 layer (b), preserve the eigenphase-torus math identity but document that the cross-spectrum / lead-lag application of the lift was tested at its dedicated benchmark and underperformed. The lift remains as project canon for the chess_spectral and ephemerides_spectral existing uses; the finance application is descriptive-only.

2. **financial-scoping-2026-05-11.md update**: demote finding #7 from "novel cross-pollination win" to "candidate that did not survive its dedicated benchmark." Add a §3.5.1-layer-(b) test-result row to the cross-pollination table.

3. **Honest publication / vocabulary**: the project should not claim "T^N quantum-walk lift extends Hayashi-Yoshida 2005" or "unifies Welch coherence + HY + dynamic asset trees." Honest framing: "T^N lift is a mathematically clean unitary evolution on the correlation Laplacian; tested at the async-HF lead-lag benchmark, it underperforms classical methods." This is the math-doesn't-lie discipline.

4. **Math-identity for future work**: if a future project domain has a SPECIFIC need where eigenmode-mixing IS the desired behavior (not per-pair extraction), the T^N lift is the right primitive. Candidates include: graph-spectral clustering with phase-coherent dynamics (chess, ephemerides); coherence between dominant eigenmodes; spectral-gap-based stability analysis. The lift is not falsified as a general math construct; only its specific finance application fails.

5. **No real-data follow-up needed for THIS claim.** The structural failure mode (L-aggregation as lossy transform of `C_complex`) is independent of whether the data is synthetic or real. Real S&P 500 high-frequency data would not rescue the lift; it would only add real-data noise on top of the structural issue.

6. **Direct Welch coherence at low frequency is the right finance baseline.** If srmech wants a "first-class finance offering" cross-pollination, the candidate should be Welch coherence as the §3.5.1 layer (b) projection onto a SINGLE frequency — not the full Laplacian propagator. (This is a much weaker claim than the original finding #7 and is essentially just Welch coherence's existing finance practice in srmech vocabulary.)

---

## 11 — Reproducibility

**Script:** [t-n-async-hf-lead-lag-spike-script.py](t-n-async-hf-lead-lag-spike-script.py)

**Per-metric NDJSON output:** [t-n-async-hf-lead-lag-spike-per-metric-2026-05-11.ndjson](t-n-async-hf-lead-lag-spike-per-metric-2026-05-11.ndjson) (91 records: 3 HY aggregates + 21 real-control + 21 complex-lift per-t + 3 initial-state + 5 omega-band + 6 direct-cross-spectrum + 10 easier-SNR + 20 per-trial + 1 verdict + 1 final).

**Reproduction:** `python docs/srmech/notes/t-n-async-hf-lead-lag-spike-script.py`

**Runtime:** ~8 seconds (20 trials full sweep + 4 anomaly chases) on commodity workstation. Deterministic across runs (seed `20260511`).

**Library versions tested:** numpy / scipy (versions as installed; closed-form numerical linear algebra only). No SGD, no learned parameters, no test-set tuning.
