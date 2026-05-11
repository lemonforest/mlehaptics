# Financial scoping for srmech — 2026-05-11 cross-domain absorption round

**Round:** Finance (equity / fixed-income / FX / derivatives / risk / portfolio / market-microstructure / systemic-risk)
**Date:** 2026-05-11
**Method:** Concertmaster role (dispatched per `concertmaster.md`); high-effort independent investigation with citation discipline; standard project dual-agent pattern (`feedback_dual_agent_research_pattern.md`) recorded as a fermata — see Fermata 1.
**Round position:** Sixth scoping round after graphics, audio, protein, telecom, power-grid.

## Headline findings

1. **OFDM-class identity, finance edition: the Carr-Madan FFT option-pricing transform IS the `(Transform=DFT, λ_k=log-strike-frequency, g(λ_k)=ψ(λ_k)·(eᵃˣ/(α²+α−λ²+i(2α+1)λ)))` decomposition.** Carr & Madan (1999) express the European-call price as the discrete inverse Fourier transform of a damping-corrected characteristic-function product (`https://engineering.nyu.edu/sites/default/files/2018-08/CarrMadan2_0.pdf`). §3.0's universal decomposition is *literally* how every modern option-pricing library prices European/Bermudan options under Heston, VG, CGMY, and any Lévy model whose characteristic function is closed-form. **Identity, not analogy** — comparable to OFDM in telecom round. The "Transform" is FFT-on-log-strike-grid; the "λ_k" is log-strike frequency; the "g(λ_k)" is the damped characteristic-function weighting. Finance has been computing this since 1999 without using the §3.0 vocabulary.

2. **Black-Scholes PDE is the heat equation on log-moneyness Euclidean grid.** Change of variables `x = ln(S/K) + (r − σ²/2)(T−t)`, `τ = σ²(T−t)/2` reduces Black-Scholes to `∂U/∂τ = ∂²U/∂x²`. **The §3.5 Euclidean-grid + Neumann-BC row is instantiated for the third time** (graphics image-domain, audio spectrogram, finance option-pricing PDE). Same `g(λ) = exp(−σ²τ·λ)` heat-kernel decay; same DCT/DFT eigenbasis. Implied-volatility-surface evolution = heat-kernel evolution on log-moneyness × time-to-expiry 2D grid. **Project framing offers finance a tighter vocabulary for an already-known math identity.**

3. **Litterman-Scheinkman three-factor yield-curve decomposition IS PCA-on-tenor-Laplacian = same primitive as protein PCA, ephemerides Fiedler, MIMO SVD, telecom CSI fingerprint.** Three principal components (level / slope / curvature) explain ~99% of US Treasury yield variance (Litterman & Scheinkman 1991; `https://link.springer.com/article/10.1007/s12197-010-9142-y`). Tenor structure 1y/2y/.../30y forms a 1D Euclidean grid; covariance matrix's top three eigenvectors are *literally* the first three DCT basis functions of a discrete 1D Laplacian (constant / linear / quadratic). **Fifth-instantiation cousin in the §3.5 framing: same eigendecomposition, different grid topology.**

4. **Random Matrix Theory + Marchenko-Pastur eigenvalue cleaning IS the finance-domain equivalent of MFO Phase B 18-block rep-theory finding's "structural prediction from theory not fit-parameter."** Laloux-Cizeau-Bouchaud-Potters 1999 (`https://arxiv.org/abs/cond-mat/9810255`) showed that the *bulk* of S&P 500 correlation-matrix eigenvalues fits the Marchenko-Pastur distribution for random noise; eigenvalues *outside* the MP support carry real factor information (market mode + sector modes; ~5% of N for typical S&P 500 sample). **Closed-form theoretical prediction from RMT, not SGD-fit.** This is finance's already-existing MPM-discipline-style spectral filter. The "18-block from D₃ irrep" analog would be **factor structure from group-symmetric portfolio constructions** — discussed in headline 6 below. See sub-investigation 4.

5. **Mantegna 1999 MST + Tumminello-Aste-Di Matteo-Mantegna 2005 PMFG + Onnela et al 2003 asset-graph IS the §3.5 general-graph row for finance — direct sibling of ephemerides 52-body Fiedler partition + protein RIN GNM + power-grid Y-bus.** Stock correlation `ρ_ij` becomes distance `d_ij = √(2(1−ρ_ij))` (Mantegna 1999, `https://arxiv.org/abs/cond-mat/9802256`); MST keeps n−1 edges, PMFG keeps 3(n−2) edges with planarity constraint (Tumminello et al 2005, `https://www.its.caltech.edu/~zuev/papers/PMPG.pdf`). **Sixth instantiation of the same graph-Laplacian architectural slot.** Graph-Laplacian on filtered correlation network → graph-spectral clustering → portfolio sector taxonomy. **Five-and-now-six domains; identity not analogy.**

6. **Lopez-de-Prado Hierarchical Risk Parity (2016) IS spectral clustering on correlation-distance graph — direct cousin of Fiedler partition on ephemerides 52-body resonance graph + protein domain decomposition + power-grid islanding analysis.** HRP uses single-linkage hierarchical clustering on `d = √(2(1−ρ))` distance metric, then recursive bisection (`https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678`). **Concrete falsifiable spike-test candidate (Fermata 3):** run Fiedler partition on S&P 500 daily-returns correlation graph; compare to HRP's hierarchical clustering tree and to GICS sector classification. If Matthews φ and Spearman ρ comparable to ephemerides §13 (`φ = +0.336`, `ρ = +0.743`) and power-grid Fiedler-on-IEEE-39-bus benchmark, srmech's universality claim acquires a **fifth quantitative datapoint** in addition to graphics / audio / protein / power. **A real testable cross-domain prediction.**

7. **T^N quantum-walk lift on the correlation graph — REFUTED at dedicated benchmark (status updated 2026-05-11).** Original framing: Hayashi-Yoshida 2005 high-frequency lead-lag estimator (`https://arxiv.org/abs/1111.7103`) shows that asynchronous tick-data preserves *which-asset-leads-which* information lost by sampling at regular intervals; magnitude-only correlation `|ρ_ij|` discards phase; complex coherence `C_ij(ω) = S_ij(ω)/√(S_ii(ω)S_jj(ω))` (Welch cross-spectrum) preserves it; the §3.5.1 layer-(b) eigenphase-torus T^N quantum-walk lift `U(t) = exp(−i L_corr t)` on the correlation Laplacian was proposed as a natural lift unifying both. **Dedicated T^N async-HF lead-lag spike (2026-05-11) refuted this claim.** On synthetic async-sampled price series with known lag structure (5 followers at lags `{0,1,2,3,5,10}` of a GBM leader, Poisson sampling, 20-trial bootstrap), Hayashi-Yoshida achieved Spearman ρ = 1.000 (perfect) and direct Welch coherence at low ω achieved ρ = +0.923, while the T^N complex lift achieved only ρ = +0.362 (not competitive). **Decisive diagnostic**: direct Welch coherence at low ω BEATS the T^N lift on the SAME `C_complex` matrix, proving the Laplacian aggregation + propagator-exponentiation is a **lossy transform** of the raw cross-spectrum, NOT a unification. Mechanism: dominant low-eigenvalue eigenmode of `L_complex` carries the leader's overall phase; `arg(U(t)[i,j])` is dominated by this mode and INVERTS per-pair lag direction. Hyperparameter-robust failure; structural, not SNR-bound. **Valid finance baselines**: Hayashi-Yoshida 2005 remains gold standard for async-HF lead-lag; direct Welch coherence at low ω is the valid spectral baseline. **What stands**: T^N math identity (CTQW on eigenphase torus) remains valid as math; existing chess-spectral `qm_2d`/`qm_4d` and ephemerides T^52 applications remain valid (graph-spectral clustering with phase-coherent dynamics — different use case from per-pair phase extraction). Provenance: [`t-n-async-hf-lead-lag-spike-2026-05-11.md`](t-n-async-hf-lead-lag-spike-2026-05-11.md) + per-metric NDJSON + reproducible script (8s runtime, seed `20260511`). See sub-investigation 3.

8. **Implied-volatility surface as deformed S²-style symmetric pricing manifold — Gatheral SVI parametrization IS the §3.5.3(A) rotational-compression-breaks-pure-sphericity motif for finance.** Black-Scholes assumes constant σ → flat implied-vol surface (perfectly "spherical" in option-pricing-manifold terms). Real market data shows skew (negative correlation between underlying return and volatility) and smile (out-of-money options priced richer than at-money). Gatheral's SVI (`https://arxiv.org/abs/1204.0646`) parametrizes the deformation with 5 parameters (ATM variance, ATM skew, put-wing slope, call-wing slope, asymmetric center). **Same mechanism family as Saturn J₂ + Kerr-oblate + Uranus/Neptune tilt-offset distortion from MFO orchestration:** an idealized rotationally-symmetric base manifold (here: Black-Scholes flat σ) deformed by a real-world coupling (here: investor risk-aversion asymmetry around at-the-money + correlation between return and volatility). Cross-cutting math-identity motif §3.5.3(A) gets its fourth instantiation.

9. **Config-vs-substrate ratio: ~50/50** — finance is the **most-balanced** domain scoped to date. Closed-form `g(λ)` covers Black-Scholes / Heston / VG / CGMY Fourier-pricing (~20 ops); PCA/eigenportfolios (~10 ops); RMT cleaning (~5 ops); spectral clustering (~8 ops); yield-curve PCA (~5 ops); Hawkes-process closed-form kernels (~6 ops); SVI volatility-surface fitting (~4 ops); Almgren-Chriss optimal-execution (~5 ops); copula closed-forms (~6 ops). Substrate dominates GARCH/EGARCH/IGARCH families (~15 primitives); Monte Carlo for path-dependent / American options (~12); rough-Heston substrate calibration (~6); reinforcement-learning execution agents (~8); LSTM / transformer return prediction (~10); HMM regime-switching filtering (Hamilton 1989, `https://users.ssc.wisc.edu/~behansen/718/Hamilton1989.pdf`; ~8); Bayesian factor-model filtering (~6); copula vine sampling (~6). **Calibration pattern: finance sits between telecom (~70/30) and power-grid (~30/70); both passive-signal-processing AND nonlinearly-state-coupled physics apply — yield-curve / option-pricing / RMT-cleaning closed-form; GARCH / Monte Carlo / RL-execution substrate.**

10. **EMDR-project mission relevance: none direct.** Finance is a cross-domain stretch test like protein / power-grid. **Genuine cross-pollination wins:**
   - (a) Carr-Madan FFT + Black-Scholes-as-heat-equation validates §3.5 Euclidean-grid row for a third time at the *foundational-pricing-PDE* level — strongest mathematical-physics rigor in any round so far (Black-Scholes IS rigorously the heat equation under change of variables; this is textbook, not analogy).
   - (b) Mantegna/PMFG/Onnela general-graph row instantiation is the **sixth** cumulative graph-Laplacian validation.
   - (c) RMT Marchenko-Pastur eigenvalue cleaning is a **structural-prediction-from-theory** finding (closed-form noise bulk; cleaning above the noise floor) — directly analogous to MFO Phase B 18-block prediction from D₃ irrep theory. Same MPM-discipline pattern; different application.
   - (d) T^N quantum-walk lift on correlation graph was the candidate **first cross-domain target where the project's framing offers finance NEW information** — **REFUTED at its dedicated benchmark on 2026-05-11**; honest data not papered over. The project's lift is a lossy transform of the cross-spectrum on this application; Hayashi-Yoshida 2005 and direct Welch coherence remain the gold standards for async-HF lead-lag estimation. The T^N math identity stands as math; the lead-lag application falls. See sub-investigation 3 and dedicated spike findings.

## Operator counts

- **Manifolds:** ~22 — 1D Euclidean (yield-curve tenor, strike grid, time-to-expiry grid); 2D Euclidean (implied-vol surface strike × tenor; intraday × calendar-day; multi-strike multi-tenor barrier-option PDE); sphere S² (Black-Scholes-base flat-σ pricing manifold as idealized symmetric form; rare direct use); flat torus T² (intraday × day-of-week × month seasonality; multi-asset phase manifold T^N); triangle mesh (multi-strike multi-tenor irregularly-spaced option-PDE mesh; rare); general graph (correlation networks: MST, PMFG, threshold; interbank-exposure network for systemic risk; cross-asset Granger-causality DAG; supply-chain Bloomberg graphs)
- **Transforms:** ~28 named — DFT/IDFT (Carr-Madan FFT pricing), DCT-on-yield-curve, characteristic-function inversion (Heston / VG / CGMY / Lévy), wavelet decomposition (Gençay et al 2002, `https://www.sciencedirect.com/science/article/abs/pii/S2452306216300144`), STFT-on-returns, Hilbert envelope (HHT EMD), cepstrum-on-volatility, PCA/SVD/KLT (yield-curve; eigenportfolios), Welch cross-spectrum (lead-lag), Hayashi-Yoshida cumulative cross-correlation, copula transform (Sklar), spherical-harmonic (rare; multi-asset rotation models), graph Fourier transform (correlation Laplacian), graph wavelet (Hammond-Vandergheynst), spectral risk decomposition, MUSIC/ESPRIT (high-frequency-tick subspace fitting), DMD (regime detection), Fourier flexible-form intraday seasonality (Andersen-Bollerslev 1997 family, `https://www.sciencedirect.com/science/article/abs/pii/S0927539897000091`), Schwartz-Smith two-factor commodity Kalman filter, Black-Scholes-to-heat-equation change of variables, Carr-Madan damping transform, Gil-Pelaez inversion, Lewis Fourier-formula
- **Closed-form `g(λ)` operators:** ~70+ across 10 thematic groups — option pricing (10: Black-Scholes / Heston / VG / CGMY / Merton-jump / Kou-jump / SABR small-T / Bates / Lévy-stable / fractional Brownian); yield-curve (6: Vasicek / Cox-Ingersoll-Ross / Hull-White / G2++ / Nelson-Siegel / Svensson); volatility-surface (5: Heston / SABR / SVI / SSVI / SVI-JW); RMT cleaning (4: clipping / shrinkage / Ledoit-Wolf / rotationally invariant estimator); spectral clustering (6: Fiedler / normalized cut / random-walk / spectral biclustering / signed Laplacian / motif-spectral); yield-curve PCA (3: level / slope / curvature); Hawkes-kernel families (6: exponential / power-law / sum-of-exponentials / Mittag-Leffler / Ogata thinning / mutually-exciting); SVI no-arbitrage (4: raw SVI / SVI-JW / surface SSVI / arbitrage-free interpolation); Almgren-Chriss optimal execution (5: linear-impact / square-root-impact / quadratic-utility-tradeoff / expected-shortfall-objective / risk-aversion-parameter); copula closed-forms (8: Gaussian / Student-t / Clayton / Gumbel / Frank / Plackett / Joe / symmetrized-Joe-Clayton from Patton 2004)
- **Substrate primitives:** ~50 — GARCH / EGARCH / IGARCH / TGARCH / GJR-GARCH / Realized-GARCH (8); Monte Carlo path-dependent option pricing (4: simple MC / Quasi-MC Sobol / variance-reduction antithetic-control / Longstaff-Schwartz American MC); rough-Heston calibration (Bayer-Friz-Gatheral, 3); LSTM / Transformer return prediction (5); RL execution / market-making agents (5); HMM regime-switching filter (Hamilton 1989 / Baum-Welch / forward-backward / Kim filter, 4); particle filter / Kalman filter / Extended-Kalman / Unscented (4); Bayesian factor-model Gibbs sampling (3); vine-copula sampling (3); cascade-default Monte Carlo (Eisenberg-Noe interbank clearing, 2); DebtRank iterative shock propagation (Battiston et al 2012, `https://www.nature.com/articles/srep00541`, 2); MCMC stochastic-volatility (Jacquier-Polson-Rossi, 2); NMF / ICA / RPCA factor extraction (3); Bayesian online-changepoint detection (Adams-MacKay, 2); reinforcement-learning hierarchical RL for portfolio (3); neural-SDE calibration (Cuchiero-Larsson-Teichmann, 2); high-frequency adaptive lead-lag (Hayashi-Yoshida + Robert-Rosenbaum 2010, 2)
- **HDC cyclic groups:** 12 — Z_252 trading-day year (252 NYSE trading days); Z_22 trading-month; Z_5 trading-week; Z_390 minute-of-trading-day (US 09:30-16:00); Z_24 hour-of-day FX/crypto; Z_7 weekday-FX; Z_4 quarterly-earnings; Z_n strike-grid index; Z_m tenor-grid index; Z_GICS-sectors (currently 11, GICS 2018 revision); Z_p prime-modular high-frequency timestamp; Z_2^k discrete-tick-size (Reg NMS subpenny). **Naming candidates:** `Phase252BIP` (calendar-day phase), `PhaseStrikeBIP` (strike-grid cyclic), `PhaseTenorBIP` (tenor-grid cyclic), `PhaseGICSBIP` (sector-rotation symbol), `PhaseRegimeBIP` (bull/bear/quiet/crisis 4-symbol alphabet — Hamilton-style HMM).

## Cross-pollination — 14 distinct identities / parallels

| Finance feature | srmech primitive | Match strength |
|---|---|---|
| **Carr-Madan FFT option pricing** | `(Transform=DFT, λ_k=log-strike-frequency, g(λ_k)=damped-char-fn)` | **Identity** (textbook math) — same architectural slot as OFDM equaliser, telecom round |
| **Black-Scholes PDE → heat equation under log-moneyness change-of-vars** | §3.5 Euclidean-grid + Neumann-BC row, `g(λ) = exp(−σ²τ·λ)` | **Identity** (textbook math) — third instantiation (graphics, audio spectrogram, options pricing) |
| **Litterman-Scheinkman three-factor yield-curve PCA** | PCA = eigenbasis of 1D tenor-Laplacian; level/slope/curvature = DCT modes 0/1/2 | **Identity** — sixth instantiation of cross-domain PCA primitive |
| **Mantegna 1999 MST on correlation distance** | Graph-Laplacian on filtered correlation network | **Identity** — sixth instantiation of §3.5 general-graph row |
| **Tumminello et al 2005 PMFG** | Planar-filtered graph-Laplacian; richer than MST | **Identity** — same primitive, different filtering rule |
| **Lopez-de-Prado 2016 HRP** | Spectral clustering on `d = √(2(1−ρ))` correlation-distance graph | **Direct cousin** — same hierarchical decomposition as ephemerides §13 + protein domain decomposition + power-grid islanding |
| **Laloux-Cizeau-Bouchaud-Potters 1999 RMT cleaning** | Theoretical noise-bulk prediction (Marchenko-Pastur); structural-prediction-from-theory style | **Math-identity motif** — direct cousin of MFO Phase B 18-block prediction style |
| **DebtRank (Battiston et al 2012) iterative shock propagation** | Power-iteration on interbank-leverage matrix; |λ_max| < 1 = stable | **Identity** — eigenvalue-based stability criterion, same as graph-Laplacian spectral-gap stability |
| **Gatheral SVI implied-vol-surface parametrization** | §3.5.3(A) rotational-compression-breaks-pure-sphericity motif | **Math-identity motif** — fourth instantiation (Saturn J₂ + Kerr + Uranus/Neptune + IV-surface deformation) |
| **Hayashi-Yoshida 2005 high-frequency lead-lag** | Asynchronous-trade cross-spectrum preserving phase | **Bridge to §3.5.1 layer-(b)** — phase-preserving correlation NOT magnitude-only |
| **Hawkes self-exciting point process** (Bacry-Mastromatteo-Muzy 2015) | Reaction-diffusion-on-event-stream graph; sibling of cascade-failure RD-on-graph in power round + biological-pattern RD in graphics §3.7 dynamic generators | **Strong analogy** — same coupled-PDE class on point-process intensity |
| **Hamilton 1989 HMM regime-switching** | Substrate primitive; sibling of cognitive-radio in telecom + voice-activity in audio | **Direct primitive** — same substrate machinery, different observable |
| **Almgren-Chriss optimal execution** | Linear-quadratic stochastic control with closed-form solution; cousin of audio AGC + power AGC | **Direct cousin** — same LQ closed-form structure |
| **Andersen-Bollerslev 1997 intraday-volatility Fourier flexible form** | Spectral expansion on Z_390 intraday-minute cyclic group | **Identity** — direct port of audio cyclic-phase fingerprinting; finance had this in 1997 |

## EMDR-project-specific assessment

**Direct connection: none.** Finance is a cross-domain stretch test like protein / power-grid.

**Genuine cross-pollination wins (real, not stretches):**

1. **Carr-Madan FFT = identity of §3.0 universal decomposition at the foundational option-pricing-PDE level.** This is the *highest mathematical-physics rigor* observed in any round so far: Black-Scholes IS rigorously the heat equation under change of variables; Carr-Madan IS rigorously the DFT-based eigenbasis inversion. Not analogy; textbook math.

2. **Mantegna/PMFG/Onnela general-graph row = sixth cumulative graph-Laplacian instantiation across (chess board-adjacency, ephemerides 52-body resonance, protein RIN GNM, audio mic-array, power Y-bus, now finance correlation network).** Strongest cumulative validation of §3.5 to date — outpaces power-grid's "fifth instantiation" framing.

3. **RMT Marchenko-Pastur cleaning = MPM-discipline-style structural-prediction-from-theory.** Closed-form noise bulk; cleaning above the noise floor; not SGD-fit. Finance already has its own version of MFO Phase B's "math-doesn't-lie" pattern.

4. **Concrete falsifiable spike-test (Fermata 3):** Fiedler-partition on S&P 500 daily-returns correlation graph vs Lopez-de-Prado HRP hierarchical-clustering tree vs GICS sector classification. If Matthews φ + Spearman ρ comparable to ephemerides §13 / power-grid IEEE-39-bus benchmark, finance becomes the **fifth quantitative datapoint** for srmech universality (after graphics / audio / protein / power).

5. **T^N quantum-walk lift on correlation graph — candidate-refuted at dedicated benchmark 2026-05-11.** Originally proposed as the **first cross-domain target where the project's framing offers finance NEW information**: T^N phase-preserving lift on the asset-correlation Laplacian is not in standard finance literature, the lift is well-defined and mathematically valid, and the project's `exp(−i L_corr t)` was hypothesised to unify Welch coherence + Hayashi-Yoshida lead-lag on the same eigenbasis. **Dedicated T^N async-HF lead-lag spike (2026-05-11) refuted this**: direct Welch coherence at low ω beats the T^N lift on the SAME `C_complex` matrix (ρ = +0.923 vs +0.362), proving the Laplacian aggregation + propagator-exponentiation is a lossy transform of the raw cross-spectrum, not a unification. The T^N math identity stands; the specific finance lead-lag application falls. **Valid finance baselines remain Hayashi-Yoshida (gold) + direct Welch coherence (spectral).** Existing T^N applications in chess-spectral `qm_2d`/`qm_4d` and ephemerides T^52 stand (different use case: graph-spectral clustering with phase-coherent dynamics). See dedicated spike findings: [`t-n-async-hf-lead-lag-spike-2026-05-11.md`](t-n-async-hf-lead-lag-spike-2026-05-11.md).

**Tenuous-but-honest stretches (don't force):** finance-as-bilateral-EMDR-stimulation (none); finance UTLP usage (none direct); finance HDC application (calendar phase BIPs are real but not load-bearing for EMDR device).

## Disability-accommodation dimension (per memory)

Finance has disability-accommodation dimensions, though weaker than power-grid or telecom:

- **Cognitive disability / executive function**: complex financial products mismatch user capacity to evaluate risk. Closed-form spectral-decomposition catalogues (e.g., yield-curve level/slope/curvature) provide *more interpretable* portfolio summaries than opaque black-box ML models. Project framing favors interpretable decompositions over deep-learning fit — alignment with cognitive-accessibility principle.
- **Aphantasia (user has it)**: visual-charting-dependent finance UI excludes non-visualizers. Numerical/textual spectral fingerprints (e.g., HRP cluster IDs; eigenportfolio coefficients; PhaseRegimeBIP labels) provide non-visual access to portfolio structure.
- **Motor disability**: high-frequency trading interfaces assume rapid mouse/keyboard; voice-driven or switch-driven portfolio rebalancing aligned with the project's `feedback_disability_accommodation_dimension.md` framing.
- **Numeracy variance / dyscalculia**: complex VaR / CVaR / Greeks computations are user-hostile. Closed-form decompositions allow simpler "level shifted up; slope steepened; curvature compressed" narratives than raw matrix outputs.
- **Trauma-informed dimension**: finance loss-aversion / drawdown-experience can re-trigger trauma for financial-crisis survivors. Defensive-resilience scoring (graph-centrality of a portfolio's exposure to systemically-important nodes via DebtRank) is the trauma-informed contribution; capability-assessment for offensive market-manipulation is NOT (per `feedback_trauma_informed_defensive_scope.md`).

## Trauma-informed defensive scope (per memory)

Per `feedback_trauma_informed_defensive_scope.md`, the boundary for finance:

- ✅ **Ship:** spectral analysis primitives (RMT cleaning, PCA, Fiedler partition); literature refs (Mantegna 1999, Tumminello 2005, Laloux 1999, Litterman-Scheinkman 1991, Battiston DebtRank); defensive-resilience scoring (DebtRank for systemic-risk assessment); interpretable-portfolio frameworks for financial-inclusion.
- ❌ **Do not ship:** market-manipulation playbooks (offensive territory); spoofing / layering attack-vector design; predatory-trading optimization (HFT against retail); credit-discrimination model design. The math is dual-use; the project ships physics + textbook math + standard finance literature, never offensive operational application.
- ✅ **Ship:** anomaly detection in market-microstructure (defensive — abuse-detection blind to attribution); systemic-risk early-warning (`λ_max > 1` of interbank-leverage matrix is defensive).

## Sub-investigation 1 — Existing spectral work in finance

Comprehensive citation-anchored survey. Finance has rich spectral methods; many predate the spectral-collection's articulation of `(Transform, λ_k, g)`.

**Random Matrix Theory in finance** (well-adopted in practice):
- Laloux-Cizeau-Bouchaud-Potters 1999 PRL `https://arxiv.org/abs/cond-mat/9810255` — Marchenko-Pastur eigenvalue cleaning, S&P 500 covariance. ~5% of N eigenvalues are signal; bulk is noise. Practical adoption: virtually all large-portfolio risk-management systems clean covariance via RMT or Ledoit-Wolf shrinkage.
- Plerou-Gopikrishnan-Rosenow-Amaral-Guhr-Stanley 1999/2002 — empirical RMT validation on NYSE daily returns.
- Bouchaud-Potters textbook (2003, *Theory of Financial Risk and Derivative Pricing*) — foundational reference.
- **Cross-domain note:** RMT cleaning style = MFO Phase B 18-block prediction style. Both produce structural predictions from closed-form theory without SGD-fit.

**Correlation networks** (well-adopted in academic risk-management; growing in practice):
- Mantegna 1999 `https://arxiv.org/abs/cond-mat/9802256` — first MST on stock correlation distance. Foundational.
- Tumminello-Aste-Di Matteo-Mantegna 2005 PNAS `https://www.its.caltech.edu/~zuev/papers/PMPG.pdf` — PMFG; planar maximally filtered graph with 3(n−2) edges. More informative than MST.
- Onnela-Chakraborti-Kaski-Kertész-Kanto 2003 `https://arxiv.org/abs/cond-mat/0303579` — asset-graph (threshold network); dynamic asset trees.
- Bonanno-Caldarelli-Lillo-Mantegna 2003 — cross-correlations in financial graphs.
- **Direct sibling of:** chess board-adjacency, ephemerides 52-body resonance, protein RIN, audio mic-array, power Y-bus. Sixth instantiation.

**Eigenportfolios / spectral PCA** (heavily adopted):
- Avellaneda-Lee 2010 *Quantitative Finance* `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1153505` — statistical arbitrage with PCA-based factors. Sharpe 1.44 over 1997-2007 backtests.
- Litterman-Scheinkman 1991 — three-factor yield-curve PCA; 99% variance explained.
- Boyle 2014 — eigenportfolios for risk management.
- **Cross-domain identity:** same primitive as protein-ensemble PCA + chess board-state PCA + ephemerides Fiedler + telecom MIMO SVD.

**Wavelet methods** (academic adoption; thin practical use):
- Gençay-Selçuk-Whitcher 2002 textbook `https://shop.elsevier.com/books/an-introduction-to-wavelets-and-other-filtering-methods-in-finance-and-economics/gencay/978-0-12-279670-8` — multiresolution analysis on volatility / returns / VaR.
- **Direct port** of audio CWT/DWT and graphics wavelet primitives.

**Hawkes processes** (well-adopted in academic HFT; growing in practice):
- Bacry-Mastromatteo-Muzy 2015 *Market Microstructure and Liquidity* `https://arxiv.org/abs/1502.04592` — comprehensive review. Self-exciting + cross-exciting point processes for tick data / volatility / systemic-risk contagion / optimal-execution.
- **Cross-domain sibling:** cascade-failure RD-on-graph in power round; biological-pattern RD-dynamic generators in graphics §3.7.

**Spectral clustering for portfolio construction** (recent academic adoption):
- Lopez-de-Prado 2016 *JPM* `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678` — Hierarchical Risk Parity (HRP). Single-linkage clustering on correlation distance; recursive bisection. **Spectral clustering's finance instantiation.**
- Constrained-HRP variants (Pfitzinger-Katzke etc).

**Yield-curve modeling** (heavily adopted):
- Vasicek (1977), Cox-Ingersoll-Ross (1985), Hull-White (1990), G2++ (Brigo-Mercurio), Nelson-Siegel (1987), Svensson (1994) — analytic ATSM eigenfunction expansions.
- Litterman-Scheinkman (1991) — three-factor PCA.

**Black-Litterman / factor models** (heavily adopted):
- Black-Litterman (1992) — eigenbasis-projection style portfolio construction; combines prior + investor view.
- Fama-French 3/5-factor models (1993, 2015).
- Carhart 4-factor (1997).

**Option-pricing FFT** (universally adopted):
- Carr-Madan 1999 `https://engineering.nyu.edu/sites/default/files/2018-08/CarrMadan2_0.pdf` — FFT pricing via damped characteristic function. **The §3.0 universal decomposition in finance.**
- Lewis 2001 — alternative Fourier formula.
- Bates 1996 / Heston 1993 — characteristic-function pricing precursors.

**Volatility-surface parametrization** (heavily adopted):
- Gatheral SVI `https://arxiv.org/abs/1204.0646` — arbitrage-free SVI parametrization.
- Heston (1993), SABR (Hagan-Kumar-Lesniewski-Woodward 2002), CGMY (2002).

**Verdict:** Finance has **rich spectral history** dating to 1991 (Litterman-Scheinkman), with heavy academic + practical adoption. The `(Transform, λ_k, g)` decomposition is implicitly present in Carr-Madan 1999, Black-Scholes-as-heat-equation, Litterman-Scheinkman level/slope/curvature, RMT cleaning, Mantegna MST, HRP, eigenportfolios. **Finance was doing srmech-style work before srmech existed — the project's contribution is the *unification framing*, not the methods.**

## Sub-investigation 2 — Map finance onto the §3.5 manifold rows

For each §3.5 row, finance instantiations:

| §3.5 row | Finance instantiation | Strength |
|---|---|---|
| **Euclidean grid + Neumann BC** | **Strongest:** Black-Scholes PDE on log-moneyness × time-to-expiry 2D grid (heat equation under change of variables). Also: 1D yield-curve tenor grid for PCA; 1D strike grid for option-PDE; 2D vol-surface fitting; 1D intraday-minute Z_390 sequence | **Strong** — textbook math (Black-Scholes IS heat equation under log-moneyness change of variables) |
| **Sphere S²** | **Weak.** No direct standard usage. Rare: directional-data finance (Carmona-Ludkovski rotational-symmetry models for FX cross-rate manifolds); fundamentalist analysis of multi-currency rotation; spherical wavelet on directional returns (Watson 1983 directional statistics applied to FX) | **Weak** — forced-fit; flag honestly. The closest legitimate instantiation is **Gatheral SVI as deformation of idealized symmetric pricing manifold** (sub-investigation 4) — not a pure S² but the rotational-compression motif §3.5.3(A) applies. |
| **Flat torus T²** | **Moderate-to-strong:** Intraday × calendar-day cyclical patterns (Z_390 minute × Z_252 trading-day, T^(390×252)); intraday × day-of-week × month seasonality (Andersen-Bollerslev 1997 Fourier flexible form `https://www.sciencedirect.com/science/article/abs/pii/S0927539897000091`); FX-pair multi-currency cyclic-week-month patterns; option-expiry cycle (quarterly futures rolls). Multi-asset return-phase manifold T^N on N-asset universe. | **Moderate** — real-domain instantiation; weaker than T² in protein Ramachandran or magnetospheric L-shell |
| **Triangle mesh** | **Weak.** Rare: irregularly-spaced option-strike-tenor mesh for surface fitting (rarely needed because regular SVI parametrization works); 3D moneyness × tenor × vega mesh for sensitivity grids. | **Weak** — forced-fit; flag honestly |
| **General graph** | **STRONGEST:** Mantegna 1999 MST + Tumminello 2005 PMFG + Onnela 2003 asset-graph correlation networks. Also: Battiston DebtRank interbank-exposure graph; Granger-causality cross-asset DAG; supply-chain Bloomberg co-mention graph; cross-asset class graph (equity-bond-FX-commodity). **Sixth instantiation of §3.5 general-graph row.** | **Strong — identity** |
| **Discrete graph + bundle (sheaf-Laplacian)** | **Moderate:** factor-model multi-channel features per asset (return, volatility, momentum, valuation, ESG score); option-Greek bundle (delta, gamma, vega, theta, rho per strike-tenor pair). Sheaf-Laplacian on multi-factor model not yet adopted in standard finance literature; would generalize Litterman-Scheinkman PCA to multi-feature setting. | **Moderate** — research opportunity, not adopted |

**Verdict:** rows 1 (Euclidean grid) and 5 (general graph) instantiate strongly with textbook-math identity; row 3 (T²) moderately; rows 2 (S²), 4 (triangle mesh), 6 (bundle) are weak or research-opportunity. **Honest assessment: finance instantiates strongly on 2 of 6 rows; moderately on 1.** Not as comprehensive as audio (instantiates all 5 rows), comparable to power-grid (3 strong rows).

## Sub-investigation 3 — Spatial operators with phase-lift potential (the dispatch's load-bearing question)

For each spatial finance tool: is this fundamentally spatial, and would the §3.5.1 layer-(b) T^N quantum-walk lift `U(t) = exp(−i L t)` add information?

| Finance tool | Spatial / phase status | Phase-lift verdict |
|---|---|---|
| **Mean-variance optimization (Markowitz 1952)** | Cartesian return-risk space; spatial | **No useful lift.** MV optimization solves quadratic program min `wᵀΣw` s.t. `wᵀμ = μ_target`; this is geometry on Σ's positive cone, not eigenphase dynamics. Phase-lift on the static optimization problem is degenerate. |
| **Distance-based correlation clustering (single-linkage, Mantegna MST)** | `d_ij = √(2(1−ρ_ij))` Euclidean distance on correlation transform; spatial | **No useful lift** for static clustering. The distance metric is real-valued; eigenphase of `exp(−i L_corr t)` doesn't add information for cluster identity. Lift would be useful for *time-varying* MST dynamics — Onnela 2003 dynamic asset trees `https://arxiv.org/abs/cond-mat/0302546` already captures this via window-rolling, but eigenphase quantum-walk lift might reveal phase-coherence between cluster transitions not captured by windowed magnitude. **Speculative; would need spike-test.** |
| **Risk parity (equal risk contribution)** | `(wᵢ ∂σ_p/∂wᵢ) = (wⱼ ∂σ_p/∂wⱼ)` per pair; spatial | **No useful lift.** Static portfolio-construction equation; not dynamical. |
| **Eigenportfolio construction (PCA on Σ)** | Already eigenbasis = cross-polytope on S^(n−1) per §3.5.1 layer (a) | **Algebraic-hyperdimensional layer, not 3D spatial.** Already in eigenbasis. T^N lift gives `U(t) = exp(−i Σ_eigenbasis t)` — useful for phase-coherent factor-momentum analysis. **POTENTIAL WIN:** rotating eigenportfolio weight vectors via unitary evolution preserves cross-correlation phase that magnitude-PCA discards. Speculative; would need spike-test. |
| **VaR / CVaR (quantile of cartesian return distribution)** | Cartesian return-distribution space; spatial | **No useful lift.** Tail risk is a real-distribution-quantile problem; eigenphase doesn't help. |
| **Backtesting (rolling-window Sharpe, drawdown)** | Time-domain, magnitude-only | **No useful lift.** Sharpe and drawdown are not phase-sensitive. |
| **GARCH / ARIMA volatility** | Time-domain ARMA-style autoregression | **No useful lift directly.** GARCH is conditional-variance evolution; eigenphase on a single time series is trivial. *However:* multivariate-GARCH on N-asset correlated volatility could benefit from T^N eigenphase analysis of cross-volatility lead-lag (volatility spillover beyond magnitude). **Speculative.** |
| **Hawkes intensity** | Point-process; phase often discarded by intensity-only formulation | **MODEST LIFT.** Hawkes cross-excitation matrix's eigenvalues drive stability (`λ_max < 1` for stationarity). Eigenphase of `exp(−i K t)` where K is the cross-excitation kernel could surface lead-lag-of-events not captured by magnitude-Hawkes. Mostly equivalent to phase-cross-spectrum of point-process intensity. |
| **High-frequency lead-lag (Hayashi-Yoshida 2005)** | Asynchronous-trade cross-correlation; phase-preserving by construction | **YES — DIRECT PHASE-PRESERVING ALREADY.** HY estimator already preserves phase via asynchronous trade times. The §3.5.1 layer-(b) `exp(−i L_corr t)` framing UNIFIES HY estimator + Welch coherence + cross-spectral analysis on the same Laplacian eigenbasis. **First strong project → finance cross-pollination win.** |
| **Welch cross-spectrum coherence `C_ij(ω)`** | Phase-preserving; already adopted in finance | **YES — DIRECT.** Same as above; project framing offers unification with HY and with §3.5.1 layer-(b) eigenphase-torus T^N. |

**Verdict:** for static / single-asset finance, the T^N lift adds NO new information. For multi-asset, asynchronous, high-frequency, or lead-lag-sensitive analysis, the lift IS new and useful. Specifically:

- **High-frequency multi-asset lead-lag analysis on correlation Laplacian eigenbasis** — project framing `exp(−i L_corr t)` on `L_corr = D − Σ` unifies Hayashi-Yoshida + Welch coherence + Onnela dynamic asset trees with a single closed-form operator. **This IS the genuine project → finance pollination win.**
- **Phase-coherent factor-momentum on Σ_eigenbasis** — `exp(−i Σ t)` operator applied to factor returns preserves cross-factor phase coherence absent from magnitude PCA. Speculative; spike-test candidate.
- **Hawkes cross-excitation eigenphase analysis** — moderate; speculative.

**Honest assessment:** the dispatch's question "does T^N lift surface useful new structure?" → **YES, but specifically on multi-asset asynchronous lead-lag analysis, not on static portfolio construction.** Standard MV, VaR, CVaR, eigenportfolio construction, GARCH are not improved by phase-lift. Hayashi-Yoshida + dynamic asset trees + factor-momentum analysis ARE improved.

## Sub-investigation 4 — Test specific candidate findings

**Finance analog of 18-block geometric count from D₃ representation theory:**

Direct analog: **eigenvalue degeneracies on correlation matrices with sector / group-symmetric structure.**

- **Sector-symmetric portfolios:** if a portfolio has m assets per sector and k sectors (m × k = N), with intra-sector correlation `ρ_in` and inter-sector correlation `ρ_out`, the correlation matrix has a block-structured form whose eigendecomposition admits direct rep-theory analysis. Eigenvalues: one large eigenvalue at `1 + (m−1)ρ_in + (k−1)m·ρ_out` (the "market mode"), `(k−1)` eigenvalues at `1 + (m−1)ρ_in − m·ρ_out` (the "sector contrast modes"), and `k(m−1)` eigenvalues at `1 − ρ_in` (the "intra-sector idiosyncratic modes"). This IS a structural prediction from group theory (S_k × S_m permutation symmetry).
- **GICS 11-sector × ~50-stock-per-sector S&P 500 structure:** expected eigenvalue degeneracy patterns from the above formula. Empirical match to RMT eigenvalue-deviation structure is **a falsifiable spike-test candidate**.
- **Identical math** to MFO Phase B 18-block prediction from D₃ irrep theory: closed-form structural prediction from symmetry group, then empirical test.

**Verdict:** stands as a real cross-domain candidate. Sub-spike could be **GICS 11-sector × N-stock S&P 500 eigenvalue-degeneracy fingerprint match to S_11 × S_N permutation-symmetry prediction.** Concrete falsifiable test queued.

**Finance analog of chain-tier d_S/2 ≈ 0.5 endpoint:**

The MFO 4-tier classification produced d_S/2 ≈ 0.5 for chain/tree graphs across four construction methods (`mpm_survey_v2_findings.md`). Finance question: what tier does S&P 500 daily-returns correlation graph fall in?

Hypothesis: **mid-cap correlation networks should fall in mid-range tier, between chain (d_S/2 ≈ 0.5) and lattice (d_S/2 ≈ 1.5).** The MST representation has chain-like local structure but bushy hub structure (sector-leader stocks dominate); the PMFG adds planar-graph connectivity. Empirical expectation: **d_S/2 likely 0.7–1.0 for S&P 500 PMFG.**

**Verdict:** real testable prediction. Spike-test candidate. Concrete proposal: compute eigenvalue-density slope d_S/2 on S&P 500 daily-returns PMFG; check if value falls between chain endpoint and 2D-lattice tier, consistent with hierarchical-network structure. Could ground-truth against ephemerides §13 quantitative parallel.

**Finance analog of rotational compression breaks pure sphericity (§3.5.3(A)):**

Three real candidates:

1. **Gatheral SVI implied-volatility-surface skew/smile as deformation of Black-Scholes flat-σ ideal manifold.** The Black-Scholes assumption of constant σ across strike and tenor gives a rotationally-symmetric pricing manifold; observed market data shows skew (negative correlation between underlying return and volatility) and smile (out-of-money richness). Gatheral SVI parametrizes the deformation with 5 parameters. **Same mechanism family as Saturn J₂, Kerr-oblate, Uranus/Neptune tilt-offset distortion.**
2. **Risk-factor rotation under regime shifts** (Hamilton 1989 HMM): in bull markets, returns are explained by momentum + size factors (one "axis" of factor space); in bear markets, by quality + low-vol factors (different "axis"). The principal-axis rotation between regimes IS analogous to gravitational figure deformation under rotational acceleration change.
3. **Market-impact tilt** (Almgren-Chriss): linear permanent impact + nonlinear temporary impact create an asymmetric optimal-execution manifold where buy and sell trajectories are not symmetric. Mirror-symmetry break.

**Verdict:** stands; fourth instantiation of §3.5.3(A) motif (Saturn / Kerr / Uranus-Neptune / IV-surface).

**Finance analog of 18-block / generation-block style from group action:**

If a portfolio has natural symmetry group action (S_k × S_m sector × asset permutation), rep theory predicts the eigenspace decomposition.

**Concrete claim:** for S&P 500 with 11 GICS sectors and ~50 stocks/sector, the correlation-matrix eigenspace decomposes as 1 market mode + 10 sector-contrast modes + 11 × 49 = 539 idiosyncratic modes under S_11 × S_50 symmetry (when intra-sector correlations are uniform and inter-sector correlations are uniform — a "block model" assumption). Real data has dispersed eigenvalues but the *expected degeneracy patterns* under the block-model symmetry would predict the rough eigenvalue clustering structure. Same math-identity family as MFO Phase B 22A + 18B + 40E decomposition; same "structural prediction from group theory" pattern.

**Verdict:** stands as MPM-discipline-style prediction; not previously articulated in this form in the finance literature (sectors are usually treated empirically rather than predictively from S_k symmetry); falsifiable spike test.

## Sub-investigation 5 — Anomalies + boundary cases

**Anomaly 1: extreme-event tail behavior — Gaussian-spectral methods break.**

PCA / RMT / spectral clustering all assume approximately-Gaussian return distributions. Real financial returns have heavy tails (Mandelbrot 1963; Lévy-stable distributions; Pareto tails). At tail-event scale, the eigenstructure of the correlation matrix is **not** preserved — correlations spike to 1 in crisis (Onnela et al 2003 dynamic asset-tree shrinkage during Black Monday + 2008 crisis). **The §3.5 framing's universality claim assumes a stable eigenbasis; in crisis regimes finance's correlation matrix has non-stationary eigenstructure on timescale ≤ days.**

**Honest verdict:** the spectral framework fails for tail events. **Hawkes processes + Bayesian online changepoint detection** capture this better. The project's framing should acknowledge this boundary; standard MFO MPM-discipline (math-doesn't-lie) requires saying so.

**Anomaly 2: market microstructure noise dominating signal at sub-minute timescales.**

High-frequency price data has bid-ask bounce, latency-arbitrage noise, and discrete tick-quantization that dominate the "true" price diffusion at sub-second timescales. Hayashi-Yoshida + Realized-Kernel + Two-Scales Realized Volatility (TSRV; Zhang-Mykland-Aït-Sahalia 2005) address this; classical PCA on raw high-frequency returns is contaminated. **The §3.5.1 layer-(b) `exp(−i L_corr t)` lift on raw HF data would be contaminated by microstructure noise; needs Realized-Kernel or HY pre-filtering.**

**Honest verdict:** the lift is useful AFTER microstructure pre-filtering, not on raw tick data. Caveat applies; mirrors telecom round's "encryption breaks spectral analysis" caveat.

**Anomaly 3: SGD / deep-learning approaches dominate state-of-the-art forecasting; MPM-deterministic framing is in tension.**

The project's MPM discipline (closed-form / standard-library deterministic; no SGD; no free parameters) conflicts with finance's state-of-the-art LSTM / transformer / RL approaches for return prediction and execution. **Real finance practitioners use SGD-fit models heavily;** the project's framing is *interpretability + structural-prediction* which is a different value proposition.

**Honest verdict:** project framing offers interpretability win, not predictive-accuracy win. Documentary, not competitive against deep-learning. Same boundary identified in power-grid round (substrate-dominated SGD numerics).

**Anomaly 4: non-stationarity makes eigendecomposition unstable across regimes.**

S&P 500 correlation structure in 1990s ≠ 2020s. The "market mode" eigenvector's composition shifts with sector dominance (tech bubble, energy crisis, banking crisis). PCA's "level / slope / curvature" on yield curve has held for ~35 years; correlation-network structure is far less stable. **Time-windowing is necessary; eigenstructure is regime-dependent.**

**Honest verdict:** mirrors brain-network non-stationarity in protein round; common to all spectral-network methods on real-world data; not unique to finance. Project framing should ship time-varying-graph-Laplacian primitives (akin to power-grid time-varying graph for ISL constellation in telecom).

## AMSC ingestion paths

### `literature_curated`

Standard finance + econometrics canon: Black-Scholes (1973) · Merton (1973) · Vasicek (1977) · CIR (1985) · Heston (1993) · SABR (2002) · CGMY (2002) · Carr-Madan (1999) · Gatheral SVI (`https://arxiv.org/abs/1204.0646`) · Markowitz (1952) · Litterman-Scheinkman (1991) · Black-Litterman (1992) · Fama-French (1993/2015) · Carhart (1997) · Almgren-Chriss (2001) · Laloux-Cizeau-Bouchaud-Potters (1999) `https://arxiv.org/abs/cond-mat/9810255` · Plerou-Gopikrishnan-Rosenow-Amaral-Guhr-Stanley (1999/2002) · Mantegna (1999) `https://arxiv.org/abs/cond-mat/9802256` · Tumminello-Aste-Di Matteo-Mantegna (2005) · Onnela-Chakraborti-Kaski-Kertész-Kanto (2003) · Bonanno-Caldarelli-Lillo-Mantegna (2003) · Lopez-de-Prado (2016) `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678` · Ledoit-Wolf shrinkage (2003) · Hayashi-Yoshida (2005) · Andersen-Bollerslev (1997) intraday Fourier · Bacry-Mastromatteo-Muzy (2015) `https://arxiv.org/abs/1502.04592` · Hamilton (1989) `https://users.ssc.wisc.edu/~behansen/718/Hamilton1989.pdf` · Battiston DebtRank (2012) `https://www.nature.com/articles/srep00541` · Cont-Stoikov-Talreja (2010) · GICS classification standard · ISDA documentation · FRTB (Fundamental Review of the Trading Book) · Basel III/IV · ESMA MiFID II / MiFIR · CFTC / SEC public filings

**Standards corpus:** ISO 10962 (Classification of Financial Instruments / CFI codes); ISO 6166 (ISIN); ISO 4217 (currency codes); ISO 20022 (financial messaging); FIX protocol (Financial Information eXchange 4.4 / 5.0); SWIFT MT messages; FpML (Financial products Markup Language); ISDA OTC contract standards; CME / NYSE / NASDAQ exchange rule books.

### `binary_archive`

CRSP equity tick + daily data (1925-present; ~50 TB Wharton WRDS); TAQ NYSE consolidated tape (high-frequency tick + quote data; multi-TB per year); TRACE FINRA fixed-income; LOBSTER limit-order-book reconstruction; OptionMetrics IvyDB option implied-volatility surfaces; FRED Federal Reserve Economic Data; Compustat fundamentals; Refinitiv Eikon / Bloomberg Terminal data archives; LIBOR historical (pre-2021); SOFR replacement; ICAP fixed-income; Bloomberg yield-curve archives.

**Same forcing function as protein AlphaFold DB + power-grid PMU archives** for streaming / partial-fetch design.

### `csv_bulk` / `json_api`

CRSP via WRDS (academic) · Yahoo Finance API (free / unofficial) · Alpha Vantage · IEX Cloud · Polygon.io · CoinGecko / CoinMarketCap (crypto) · QuantConnect · Quandl · CME Group quotes API · FRED API · World Bank GFD · IMF IFS · BIS statistics.

## Comparison: Concertmaster vs standard dual-agent pattern (Fermata 1)

This round was dispatched as concertmaster role (per `concertmaster.md`) rather than as standard dual-agent main + sub. The dispatch explicitly assigned anomaly-chase authority and "high effort, broad scope." I executed independent breadth + citation-discipline + memory-application + framework-edge cautions in a single agent, with parallel web-search for citation specificity.

**Fermata 1:** Should this round be redone as standard dual-agent (main + sub) pattern per established practice in audio / protein / telecom / power-grid? Or is concertmaster-as-solo sufficient when explicitly dispatched? **Conductor decision needed** — established practice across four prior rounds is dual-agent; a single concertmaster (with explicit high-effort + anomaly-chase + citation-discipline + memory-application) is a reasonable substitute but produces single-perspective output. Convergence-check from a parallel sub-agent would confirm load-bearing claims.

**Convergent-check honesty:** if I were a sub-agent reading the srmech notebook fresh, I would likely converge on the load-bearing claims 1-10 above. Sub-agent unique catches that I may have missed: (i) more specific FINRA / ISDA standards citations; (ii) emerging-market / fixed-income / FX specifics beyond US-equity focus; (iii) crypto-asset / DeFi spectral applications (NB: crypto is genuinely a "decentralized correlation network" with cleaner topology than traditional finance); (iv) accounting-graph network analysis (Atkinson-Rivers-Wright on supply-chain shocks); (v) Bayesian network finance applications (Bishop / Pearl style on financial-event chains); (vi) reinforcement-learning portfolio control beyond what I covered.

## Takeaways for landing in master srmech notebook

- **§3.5 cross-manifold table:** finance instantiation column added.
  - **Euclidean grid + Neumann BC row:** Black-Scholes PDE on log-moneyness × time-to-expiry (heat equation); yield-curve tenor PCA; intraday-minute grid. **Third instantiation** (graphics + audio spectrogram + options pricing).
  - **General graph row:** Mantegna 1999 MST + Tumminello 2005 PMFG + Onnela 2003 asset-graph; DebtRank interbank; Granger-causality DAG. **Sixth instantiation** of the same graph-Laplacian architectural slot.
  - **Flat torus T² row:** intraday Z_390 × calendar-day Z_252; Andersen-Bollerslev 1997 Fourier flexible-form intraday seasonality; multi-asset return-phase manifold T^N. **Moderate** instantiation.

- **§4.2 calibration:** finance profile is **~50/50, most-balanced**. Closed-form covers FFT pricing, yield-curve PCA, RMT cleaning, spectral clustering, Hawkes kernels, SVI parametrization, Almgren-Chriss optimal execution. Substrate dominates GARCH, Monte Carlo, regime-switching HMM, RL execution, deep-learning forecasting. **Pattern confirmed across six rounds:** substrate dominates where physics is nonlinearly state-coupled (proteins ~20/80, power ~30/70); closed-form dominates in passive signal-processing (graphics ~80/20, audio ~80/20); intermediate where both apply (telecom ~70/30, finance ~50/50).

- **§5.6 absorption-round subsection (next):** headline findings + link to this file. **Sixth-instantiation framing** + **first project → external-domain pollination win on T^N quantum-walk lift** is the load-bearing contribution.

- **§1.5 future-notebook candidates:** finance row added (status: scoped; sixth-instantiation cross-domain validation; T^N quantum-walk lift on correlation Laplacian is first project → external-domain new-information offering; no direct EMDR connection).

- **§3.5.3(A) rotational-compression motif:** fourth instantiation (Saturn J₂ + Kerr-oblate + Uranus/Neptune + Gatheral-SVI-IV-surface-deformation). Cross-cutting math-identity motif now spans four physical/financial domains.

- **§3.5.3(C) 18-block structural-prediction-from-group-theory motif:** finance analog candidate — eigenvalue degeneracies on S_11 × S_50 GICS-sector-symmetric S&P 500 correlation matrix. Concrete spike-test candidate.

## Anomaly log

1. **Tail-event regime fails Gaussian-spectral methods.** RMT / PCA / spectral-clustering assume approximately-Gaussian returns; crisis regimes have heavy-tailed non-stationary correlations. Framework boundary; document, don't paper-over.
2. **Microstructure noise dominates high-frequency raw signal.** T^N lift on raw tick data is contaminated; pre-filter with Realized-Kernel or HY estimator required.
3. **SGD / deep-learning state-of-the-art conflicts with MPM-deterministic discipline.** Project offers interpretability win, not predictive-accuracy win against transformer-based forecasters. Documentary, not competitive.
4. **Non-stationary eigenstructure across regimes.** Correlation structure shifts decadally; time-windowed graph-Laplacian needed; not unique to finance but acute.
5. **No direct EMDR-project connection.** Finance is cross-domain stretch test like protein / power-grid; document genuine wins (1c/d in headline 10), don't force EMDR connection.

## Fermata records

**Fermata 1: dual-agent pattern vs concertmaster-as-solo.** This round was dispatched as concertmaster role. Established practice across four prior rounds is dual-agent. Conductor decision needed: redo as dual-agent for convergence-check, or accept concertmaster-as-solo for this round? My recommendation: accept concertmaster-as-solo for this round; flag dual-agent as default for future rounds.

**Fermata 2: T^N quantum-walk lift on correlation Laplacian — first cross-pollination project → external-domain win.** All five prior rounds (graphics, audio, protein, telecom, power) found existing-external-knowledge mapping to project framing. The T^N lift on `L_corr = D − Σ` returns Laplacian is NOT in standard finance literature; it IS in §3.5.1 layer (b); it unifies Hayashi-Yoshida + Welch coherence + Onnela dynamic asset trees. **Recommendation:** elevate to first-class srmech offering; queue as potential publication candidate ("Phase-preserving correlation analysis on the asset-return Laplacian: a quantum-walk generalization of Hayashi-Yoshida"). Conductor decision: pursue as concrete deliverable or stay descriptive?

**Fermata 3: falsifiable spike-test candidates queued.**
- (a) Fiedler-partition on S&P 500 daily-returns correlation graph vs HRP vs GICS sectors (Matthews φ + Spearman ρ comparison to ephemerides §13 / power-grid IEEE-39-bus).
- (b) d_S/2 4-tier classification of S&P 500 PMFG (expected mid-range 0.7–1.0).
- (c) Eigenvalue-degeneracy prediction from S_11 × S_50 GICS-sector symmetry vs empirical S&P 500 correlation spectrum.
- (d) T^N lift `exp(−i L_corr t)` on S&P 500 high-frequency cross-spectrum vs Hayashi-Yoshida lead-lag estimates (parity check).

Each spike has clear success criteria. Conductor decision: which spike to prioritize? My recommendation: (a) first, lowest cost + highest pedagogical value; (d) second, highest novelty.

**Fermata 4: §3.5 row instantiation honesty.** Finance instantiates strongly on rows 1 (Euclidean grid) and 5 (general graph); moderately on row 3 (T²); weakly on rows 2 (S²), 4 (triangle mesh), 6 (bundle). Honest 2-of-6-strong fit. Audio remains the only round to instantiate all rows strongly. Conductor decision: how to characterize finance in §1.5 (e.g., "2-of-6 strong instantiation" vs "sixth general-graph-row instantiation")?

## Recommended next actions

1. **§1.5 update:** add finance row to future-notebook candidates table with status "scoped; sixth-instantiation cross-domain validation; first project → external-domain pollination win on T^N quantum-walk lift; no direct EMDR connection."
2. **§3.5 cross-manifold table:** add finance column with strong instantiation on rows 1 (Euclidean grid: Black-Scholes PDE) and 5 (general graph: MST/PMFG/asset-graph/DebtRank).
3. **§3.5.3(A) update:** add Gatheral-SVI-IV-surface as fourth instantiation of rotational-compression-breaks-pure-sphericity motif.
4. **§4.2 calibration update:** add finance ~50/50 ratio; confirm pattern (substrate dominates state-coupled physics; closed-form dominates passive signal-processing; finance + telecom intermediate).
5. **§5.6 absorption-round subsection:** create as next round in sequence after §5.5 power-grid.
6. **Fermata-2 follow-up:** conductor decision on T^N lift as first-class offering or descriptive observation.
7. **Fermata-3 follow-up:** queue spike-tests (a) and (d) as concrete experiments; success criteria identical to ephemerides §13 quantitative parallel.
8. **NDJSON records** at `notes/financial-scoping-per-locus-2026-05-11.ndjson` (one record per finance method surveyed).
9. **MFO MPM notes** completion record (single line) — added.
