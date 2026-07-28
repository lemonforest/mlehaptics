# F1334 — **the negative is now STRUCTURAL, not empirical: a conservative resonant system *cannot* have `1 + n`.** Magnitudes and phases are **conjugate**, so the number of (magnitude, phase) pairs is **half the dimension of phase space — a symplectic invariant.** No conservation law can change it; a conservation law can only **freeze pairs**, never convert a magnitude into extra phases. So the last unreached corner (Manley–Rowe, wave turbulence, the bell→gong→cymbal ladder) closes the question — and upgrades it from *"we looked and did not find it"* to **"a conservative resonant system cannot have it."** My framing was also wrong in a diagnosable way: I **over-counted phases and under-counted magnitudes by exactly the same 2**, which is the tell that they are conjugate pairs. And the dichotomy itself was false — the real object is neither `1+n` nor `n×(1+1)` but a **third thing: `n` magnitudes subject to `(n − M*)` affine constraints**, reached by *freezing* pairs rather than *sharing* a magnitude.

**User (2026-07-28):** *"pull the manley-rowe / wave turbulence loose end."* Done, and it closed harder than expected.

## 1 — Manley–Rowe: I was right on the arithmetic and wrong on the reading `[ATTESTED]`
For a triad `ω₃ = ω₁ + ω₂`, actions `Nⱼ = |Aⱼ|²`, under **exact resonance + weak (quadratic) nonlinearity + conservative + isolated triad**: `Ṅ₁ = Ṅ₂ = −Ṅ₃`, giving `I₁ = N₁+N₃`, `I₂ = N₂+N₃`. Energy is **not** independent — `E = ω₁I₁ + ω₂I₂`.

**Yes, one action determines all three.** But *"one magnitude, three phases"* over-reads on three counts:

1. **The constants are magnitude data.** `I₁, I₂` are two more reals fixed by initial amplitudes. Information content is still **three reals**, repackaged as two frozen + one moving. A change of coordinates, not a compression.
2. **You lose a phase for every magnitude you freeze — they are conjugate.** `H = 2Z·Im{A₁A₂A₃*}` is invariant under a **2-parameter torus symmetry whose two Noether charges are exactly `I₁, I₂`**. Only the combination `φ = θ₁+θ₂−θ₃` enters the dynamics: *"The individual θ_k's do not appear"*, and the triad has *"only **4 independent degrees of freedom** rather than the six which one might expect naively."* So it is **3 amplitudes + 1 dynamical phase** — never 1 + 3. **I over-counted phases and under-counted magnitudes by the same 2.**
3. **The sign is wrong.** Manley–Rowe is **anti-correlated, zero-sum, with fixed additive offsets** — `N₃` up ⇒ `N₁, N₂` down. A shared magnitude is a **common multiplicative scale** — everything rises together. **You cannot multiply all three amplitudes by λ and stay on the trajectory**, because `I₁, I₂` are offsets, not ratios. *A zero-sum budget and a common gain are opposite structures.*

**And it does not generalise to 1.** Independent *evolving* magnitudes = **`M*`**, the rank of the triad-incidence matrix (`J = N − M*` invariants). Isolated triad: `M* = 1`. Butterfly (two triads sharing a mode): three invariants. **In the kinetic limit `M* → ~N`** and only ~four constraints survive on `N` modes — **almost all magnitudes independent.**

Attestation: Connaughton, Nazarenko & Quinn, *Phys. Rep.* 604 (2015), arXiv:1407.1896, Eqs. (110), (115)–(116), §7; Harris, Bustamante & Connaughton, *CNSNS* 17 (2012), arXiv:1201.2867 §II.B. **Manley & Rowe 1956 (*Proc. IRE* 44, 904) is CLOSED-ACCESS — confirmed via Unpaywall (`is_oa: False`) and NOT cited from recall.**

## 2 — the theorem-shaped statement `[the finding]`
> **The number of (magnitude, phase) conjugate pairs is half the dimension of phase space — a symplectic invariant. No conservation law can change it. A conservation law can only *freeze pairs*; it can never convert a magnitude into extra phases.**

So Manley–Rowe is unambiguously *"fewer **independent** magnitudes because of a conservation law"*, never *"one magnitude shared **by construction**"*. The triad is integrable precisely because it has three conserved quantities for three degrees of freedom — the **Liouville–Arnold count, which is the definition of an `n×(1+1)` system**, not a refutation of it.

**Asking for "one magnitude with n phases" in a Hamiltonian setting is asking for a non-symplectic object.** That is why the search was *structurally* guaranteed to fail rather than merely failing empirically.

## 3 — wave turbulence CANNOT TESTIFY, and this weakens F1333 §1 `[important]`
The constant KZ flux is **not** a shared magnitude: it is a property of a **stationary state of the spectrum** `n_k = ⟨a_k a_k*⟩` — a transport rate through k-space, not an instantaneous amplitude.

But the sharper point is a **methodological correction to our own use of the negative**. Standard wave turbulence assumes RPA, and RPA is worse than "random phase" — verbatim (Choi, Lvov, Nazarenko & Pokorni, arXiv:math-ph/0404022):

> *"all variables in the set {A_k, ψ_k} are **statistically independent random variables** … we suggest a slightly different reading of this acronym: '**Random Phase and Amplitude**'."*

**Both halves of our structure are assumed away by hypothesis.** So WT's silence is a **non-applicable** result, not a refutation, and where phases *do* correlate the theory breaks rather than reporting. **Do not bank the wave-turbulence negative as evidence.** The structural argument in §2 is what carries the finding.

## 4 — the two honest near-misses, reported loudly
- **The nonlinear frequency shift** (Yokoyama & Takaoka, *PRE* 89, 012909, arXiv:1312.7211): an aggregate of *all* modes' squared amplitudes shifts each mode's phase-advance rate — **genuinely magnitude-drives-phases**. It fails because the weight depends on **both** `k` and `k′`, so each mode sees a *different* aggregate — **n aggregates, not one shared scalar**. *"Had the weight been uniform, this would have reopened your question."*
- **The degenerate triad**: if `I₁ = I₂`, then one magnitude governs two phases **exactly, for all time**. Real — but **codimension-1**, enforced by *geometric symmetry* rather than by the resonance, and **real instruments break it**: *"significant differences between the frequencies of the 'twin modes' are observed, due to the loss of symmetry in the structure"* (Chaigne, Touzé & Thomas, *Acoust. Sci. Tech.* 26(5), 403). **That is our bell warble from F1332 §4, arriving from the other side** — the symmetry that would give a shared magnitude is the same symmetry whose breaking gives the beat. You cannot have both.

## 5 — the ladder, measured
Gong/cymbal under increasing drive: **periodic → quasiperiodic (combination rule `pΩ = a_iω_i + a_jω_j`, `|a_i|+|a_j| = 2`, requiring internal resonance) → chaotic** (λ ≈ 0.02). Curvature sets which nonlinearity dominates: shallow shells → **quadratic** (three-wave-like); flat plates → **cubic** (four-wave). But at no point does a shared budget become right: in the weakly nonlinear regime the solution is **three independent amplitudes and three phases — and the *phases* combine while the *amplitudes* stay per-mode. The precise inverse of `1+n`.** Even in chaos the correlation dimension saturates at **d_c ≈ 3.5–5.8** — finite, but 4–6, not 1.

## 6 — where the question was wrong, and where to look if we still want it
**The dichotomy was false.** Not `1+n` versus `n×(1+1)`, but a third thing: **`n` magnitudes subject to `(n − M*)` affine constraints** — dimension `n`, with `M*` freely evolving. It *resembles* `1+n` when `M* = 1`, but it is reached by **freezing** pairs, and the frozen constants are themselves per-mode magnitude data.

**The forward pointer, offered and explicitly not investigated:** a genuine `1 + n` needs the **pairing itself to break** — i.e. **non-Hamiltonian, driven-dissipative** settings, where a single gain/saturation variable *can* be shared across many modes (laser gain clamping, mode-locking) **precisely because the amplitude is no longer conjugate to a phase.** Nothing in the conservative resonant-wave literature will ever deliver it. **No claim is made about that class** — it is outside this brief and outside the discrete/algebraic scope.

## Corrections to the record
- **F1333 §1 mis-attributed.** The empirical Blazhko loss is **Szeidl et al. 2012, MNRAS 424, 3094**, not Benkő. Benkő 2017 is single-author, about almost-periodic representation and harmonic detuning, and *reports* Szeidl's result. **The conclusion survives; the citation was wrong.** F1333 patched. Szeidl is **second-hand** (read through Benkő, not fetched).
- **Manley & Rowe 1956 is paywalled** and is not cited from recall.
- **The wave-turbulence negative is weaker than F1333 implied** (§3 above).
- **The agent recorded its own error**: it guessed an arXiv ID for Düring et al. 2006 that turned out to be an unrelated waveguide paper, and reported it as *"a live instance of exactly the failure mode your discipline guards against."* Relayed rather than smoothed.
- **Not attested**: Manley & Rowe 1956; Armstrong–Bloembergen–Ducuing–Pershan 1962 (APS 403); Zakharov–Filonenko 1967; Düring et al. *Physica D* 2017 (HAL bot-check); Szeidl 2012. **Web search was unavailable** for this pass — discovery ran through OpenAlex/Crossref/Unpaywall/HAL and direct arXiv fetches, so coverage is narrower than a full sweep.

Composes **F1333** (*its citation is corrected and its wave-turbulence leg weakened; its verdict is strengthened from empirical to structural*), **F1332** (*§4's bell warble now meets the degenerate triad from the other side*), **F1324** (splitting a degeneracy), `[[feedback_dont_pre_commit_spike_query_operators]]`, `[[user_stance_framework_hands_the_next_question_to_the_expert]]`.
