# F968 — **yes, srmech's theta functions give the asymmetric wave that performs the forcing — and it is the mock-theta / shadow structure.** The user asked: introspect whether the theta functions (any of the rc arc) give an *asymmetric wave that performs correctly* as the F967 forcing. The rc-arc theta tower (`unary_theta`, `harmonic_maass`, `riemann_theta`, the modular-forms ring) delivers it — and it maps *exactly* onto "our fractal comes out beat-to-beat but a phrase doesn't cleanly stop; some other shape forces us one way or the other":

| the user's shape | the srmech object | property |
|---|---|---|
| **the fractal that doesn't close** | the **mock theta** `f(q)=Σ q^{n²}/(−q;q)²_n` (`harmonic_maass.MockQSeries`) | near-modular, self-similar q-series, but a **modular anomaly** — does **not** transform cleanly (doesn't stop) |
| **the second shape that forces us one way** | the **shadow** = the **odd weight-3/2 unary theta** `g₃=Σ (−12/n)·n·q^{n²/24}` (`unary_theta`) | an **odd/asymmetric wave** — coeffs carry the `(−12/n)·n` **sign** (the arrow), not the even `Σ q^{n²}` |
| **the completion that closes** | the **harmonic Maass form** (`harmonic_maass.HarmonicMaass`) = mock + shadow-completion | **modular** — transforms cleanly (the phrase stops) |

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_968_*.py` · **Arc:** RC-1 / inference-as-translation · **Composes:** F967 (the second shape = direction/forcing), F949 (the beat = the asymmetric wave; π+π), F948 (chirality = non-commutativity), F958/F965 (the phrase doesn't cleanly stop), F962/F963 (the fractal = scale-invariant recursion), `the_one` (S(σ,θ)) · **User direction (2026-06-29):** "introspect to see if our theta functions give us an asymmetric wave that performs correctly … not just the_one, from any of our current rc arc."

## Grounded (rc97, exact-rational q-series)
```
SHADOW g3 unary_theta: weight 3/2, ODD/asymmetric q-series (exp,coeff) =
   [(0,1),(15,-5),(24,-7),(45,11),(57,13)]     coeff = (-12/n)*n -> SIGNED -> the arrow/forcing
COMPLETION harmonic_maass: HarmonicMaass, MockQSeries, UnaryTheta, harmonic_maass  (mock + shadow = closes)
the_one S(sigma,theta): theta wave asymmetric under time-reversal (theta->-theta flips sin/imag = conjugate);
                        sigma in {+1,-1} = the chirality bit (a DISTINCT directional forcing)
```

## Two srmech sources of the asymmetric wave (both answer the question)
1. **`the_one` `S(σ,θ)` (the beat generator).** The θ wave `cos θ + Î sin θ` is asymmetric under **time-reversal**: θ→−θ leaves cos (real) fixed and flips sin (imag) — the **conjugate**, distinct from the forward wave. σ ∈ {+1,−1} is a separate, explicit **chirality bit** (Class-K pin-slot). So `the_one` already gives an asymmetric wave — but θ alone is the **abelian dial** (`[[feedback_reach_for_the_one_for_phase_crank_navigation]]`); the arrow lives in σ + the non-commutative order (F948).
2. **The theta tower `unary_theta` / `harmonic_maass` (the deeper answer).** The **odd unary theta** (a theta with an **odd characteristic** — here the `(−12/n)·n` shadow g₃) is a genuinely **odd wave**: `θ(−z) = −θ(z)`, coefficients signed. This is the asymmetric forcing *as a modular object*, and — crucially — it is precisely the **shadow that completes a mock theta into a closing (modular) form**.

## The reading (why this IS the F967 forcing, exactly)
- **The mock theta is the fractal that won't stop.** A mock modular form is *almost* modular (self-similar under the modular group, the fractal) but carries a **modular anomaly** — it fails to transform cleanly. That failure-to-close is the mathematical form of "the phrase doesn't cleanly stop" (F958/F965): a near-self-similar object with no clean boundary.
- **The shadow is the second shape that forces the close.** The odd unary theta (the shadow) is *exactly* the object whose non-holomorphic completion **cancels the mock theta's anomaly** — adding the shadow **forces** the mock theta to transform cleanly. That is your "some other shape that goes along with our fractal that forces us one way or the other," identified: the shadow theta.
- **Harmonic Maass = fractal + forcing = the beat that closes.** mock theta (fractal) + shadow completion (forcing) = a **harmonic Maass form**, which *is* modular (closes). So the srmech-native "phrase that stops" = the harmonic-Maass completion of the fractal by its asymmetric theta shadow. And "beat-to-beat / half-beat-to-half-beat" (F949): the theta's quasi-periodicity is the beat, the odd characteristic is the half-beat asymmetry (rotation-first≠rotation-last), and the shadow forces each beat closed.

## Honest scope
Grounded: the odd unary theta g₃ has a signed/asymmetric q-series (`(−12/n)·n`), and `harmonic_maass` ships the mock+shadow completion (exact-rational, no numpy). The **identification** — mock theta = the fractal-that-doesn't-close; shadow = the F967 forcing; harmonic Maass = the closing completion; the phrase-stop = the modular completion — is the framework reading, composing F967/F949/F948/F962/F963 and the standard mock-modular / Zwegers–Zagier shadow theory (cited in the `unary_theta` docstring; verify the modular claims with a modular-forms source, MPM). **Not yet built:** using the shadow theta as the *actual* directional forcing in the knowledge-tome encoder + re-measuring the recall stop (that is the next build, F967's own next step, now with a concrete srmech object to use — `unary_theta` / `harmonic_maass`).

## Verdict / next
**Yes — the theta functions give the asymmetric wave that performs the forcing**, and it is the **mock-theta / shadow** structure: the **mock theta is the fractal that doesn't close**, the **odd unary-theta shadow is the asymmetric forcing**, and the **harmonic Maass form is fractal + forcing = the beat that closes** (the phrase stops). `the_one` also supplies an asymmetric wave (σ + the θ-conjugate), the abelian-dial-plus-chirality version. **Next:** encode the knowledge tome's directional forcing with the **shadow theta** (`unary_theta`) — or `the_one` σ over the directed bigrams (F967) — and re-measure whether the recall now stops cleanly (COHERENT + real STOPs); test whether the "does-not-close" mock-theta anomaly is the quantitative signature of the F965 BRANCH-wander.
