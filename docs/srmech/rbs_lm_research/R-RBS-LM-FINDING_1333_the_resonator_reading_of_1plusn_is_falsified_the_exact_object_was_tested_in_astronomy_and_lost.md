# F1333 — **the resonator reading of `1 + n` is dead, and the strongest reason is that somebody already tried exactly our object and it lost.** A wide attested sweep (synchronisation, black-hole ringdown, seismology, condensed matter, bundle geometry) returns a decisive negative on "many phases sharing one magnitude" as a physical resonator structure. Three findings do the work. (1) **The Blazhko modulated-signal model is literally our shape** — one envelope `g^A(t)` multiplying the whole Fourier sum, one FM function entering every phase — and Szeidl et al. fitted **per-harmonic** modulation instead because *"this format fits better the observed light curves"*; Benkő then proved the shared-envelope form is a **strict special case** and concluded *"the Blazhko effect cannot be an external modulation on the pulsation."* **Proposed, tested against per-component bookkeeping, lost.** (2) **A shared drive does not produce a shared magnitude, quantitatively** — Chaplin et al. drove two modes with 100 % identical forcing and amplitude correlation still fell to 0.5 at `Δν/Γ ≈ 2` and to ≈0 beyond `Δν ≈ 5 μHz`, against a real solar spacing of `≈135 μHz`. (3) **Harmonics of one mode are not `n` modes** — a slaved-overtone `1+n` collapses to `1+1`, and **our 7 directions are independent generators** (verified: each generates only itself and the real; no single axis reaches the others), which puts us on precisely the side where both fields say no.

**User (2026-07-28):** the linearity confound, then *"we need a faster scale of same resonant shape to see where loudness is scaled by some other value perhaps."*

## 1 — the verdict `[ATTESTED]`
**The linearity argument dissolves the resonator reading.** In a linear resonator the amplitude is a pure scale factor set by the strike; each mode decays at its own rate independently. That is `n × (1+1)`. F1332 §4b already conceded this; the sweep now closes it from two further directions.

**Attestation.** Benkő 2017, MNRAS, DOI `10.1093/mnras/stx2338`, arXiv:1709.02143 — the Blazhko falsification, quoted verbatim. Chaplin, Elsworth & Toutain, *Astron. Nachr.*, DOI `10.1002/asna.200710977`, arXiv:0804.3338 — the decorrelation numbers.

## 2 — what survives, and it is not nothing
- **Genuine `1+n` structures do exist — over CONSERVED NORMS**, not over resonator amplitudes. That is a different object and it is the one worth keeping.
- **Kuramoto's `r` is causally active** — it does act back on the dynamics, so it is not merely a diagnostic readout. But it is a **feedback closure, not a fibration**. The analogy half-survives and the half that dies is the geometric half.
- The cleanest `1+n` algebraic template in the whole survey sits on the **frequency** axis, not the amplitude axis: `b(t) = exp[i(H + I·ω̄)t]·a(0)` — one scalar times the identity plus an `n×n` perturbation.

## 3 — the rescue hypothesis, sharpened into something testable
The user's *"it likely scales, and at cosmic timescales it looks fixed — we need a faster scale"* has a precise target, and it is **not** the time scale. Chaplin's decorrelation is governed by the **dimensionless ratio `Δν/Γ`** — mode spacing over linewidth. Going faster changes nothing on its own; what matters is **mode overlap**.

> **Correlation survives only where `Δν/Γ ≲ 2`. The Sun sits at `135/Γ`, deep in the decorrelated regime.**

So the honest reformulation: **look for strongly overlapping modes, not fast ones.** And the sweep already pointed at the one attested place a magnitude axis is genuinely shared across *distinct* modes — **cross-coupled hybrid multiplet pairs in Earth's free oscillations**, where *"the sets of singlet frequencies repel each other but the attenuation is 'shared'."* Hybridisation, not degeneracy. That is a narrow special case, **not a rehabilitation of the general reading.**

## 4 — the correction that lands hardest on us `[DEMONSTRABLE — verified here]`
Both surviving tiers made this independently: **harmonics of one mode are not `n` modes.** The Blazhko envelope and Camalet's `x(t) = Σ xₙe^{inωt}` both *look* like `1+n` and both collapse to `1+1`, because the higher components are slaved to the fundamental with phases locked at integer multiples. **Any nonlinear periodic oscillator has this form trivially.**

So: are ours slaved? Verified on rc349 —
```
  e1 generates basis-indices [0,1]   e2 -> [0,2]   ...   e7 -> [0,7]
  every axis generates ONLY itself and the real : True
  any single axis reaches all 7 (they are its harmonics) : False
```
**Our 7 are independent generators, not overtones of a fundamental.** That is the good news for the algebra and the bad news for the analogy: the genuine test is across *independent* modes, and that is exactly where both fields report no shared magnitude.

## 5 — sourcing honesty, relayed rather than smoothed
The researching agent **withdrew an entire delegated tier of its own work**: two sub-reports disagreed about their own inputs (one presented a full table for scopes the other marked NOT COVERED). Everything in it — cicada tymbal, cricket wing, bird syrinx, spider web, fish swim bladder, bat pinna, insect thorax, plant/tree — is **NOT COVERED**, and must be treated as neither attested nor null.

It also **self-corrected a claim it had already made**: a "mirror result" resting on two convergent findings lost one of them when the agent re-checked the tree-damping paper itself (Theckes, de Langre & Boutillon, arXiv:1106.1283) and found the abstract does not mention 1:2 internal resonance or phase locking, and it had not read the body. *"The result is unchanged, the corroboration is gone. It is one field, not two."*

**Unreached, and the one substantive gap in the brief as posed:** the named nonlinear shared-amplitude-budget literature — Manley–Rowe relations, wave turbulence in plates, the bell→gong→cymbal hardness ladder. The search budget ran out first.

## Honest scope
- `[DEMONSTRABLE — mine]`: §4's generator check only, on rc349.
- `[ATTESTED — the agent's]`: §1–§3. Headline sources were read directly by it (Strogatz, Ott–Antonsen, Marvel–Mirollo–Strogatz, Berti–Cardoso–Will, Cotesta, Baibhav, Ho, Kawaguchi–Ueda, Cushman–Śniatycki, Mosseri–Dandoloff); Buchler & Goupil via an ADS OA scan.
- **What is NOT falsified**: our own `1 + n`. It is exact and definitional in the algebra (F1328), there is no input force in an algebra, and no window either. **What is falsified is the claim that it describes a resonator.** F1332 §1–§3 stand; §4/§4b's physical reading does not.
- The word **"loudness"** should now be used only with the fence attached, or dropped. It imported a physical reading that the measurement does not support.

Composes **F1332** (*its §4 reading is now closed, not merely fenced*), **F1328/F1329** (the signature; the `1+n` is definitional), **F1324** (distinct weights = a beat — *unaffected: that is about degeneracy splitting, not shared amplitude*), `[[feedback_dont_pre_commit_spike_query_operators]]` (null findings count), `[[feedback_paywalled_doi_cannot_be_attested]]`.
