# Round 25.A — Reading-D 12th scale-ladder rung: galactic / large-scale-structure multipoles

**Dispatched** 2026-05-25 on the rolling draft PR #690 (the #679 model). User: *"dispatch the 12th rung — galactic/large-scale-structure multipoles."* Lands the 12th Reading-D anchor at the **galaxy-survey scale (~10–1000 Mpc)** — between the planetary rung (~10⁷ m, Round 21.A) and the cosmological/CMB rung (observable universe, Round 6.A). The `2ℓ+1` Class-L spine now runs **quantum → nuclear → atomic → hadron → planetary → LSS → cosmological/CMB.**

Generating code + provenance: [`verify_round25_lss_multipole_anchor.py`](verify_round25_lss_multipole_anchor.py) + `.ndjson` (deterministic; exact `fractions` Legendre arithmetic; Class-N anchors via srmech 0.4.2 `best_rational`).

## Spine continuity — the galaxy angular power spectrum

The projected galaxy overdensity is expanded `δ(n̂) = Σ a_ℓm Y_ℓm(n̂)` with angular power spectrum **`C_ℓ = ⟨|a_ℓm|²⟩`** (averaged over the `2ℓ+1` m-modes) — the *same* S² Class-L `2ℓ+1` **Born-rule Hopf-base measure** (§11.9.4) as the CMB (§11.9.6) and planetary magnetics (§11.9.15). The galaxy survey's "translation fingerprint" is literal: `C_ℓ` IS the survey's signature.

## Bit-exact core — the Kaiser RSD multipoles (proven exactly)

In linear theory the redshift-space galaxy power spectrum is `P^s(k,μ) = (1 + βμ²)² P_real(k)` (Kaiser MNRAS 227:1 1987; `μ` = line-of-sight cosine, `β = f/b`). Decomposed into Legendre multipoles `P_ℓ = (2ℓ+1)/2 ∫_{−1}^{1} P^s L_ℓ dμ`, the script **proves with exact `Fraction` arithmetic** (exact Legendre recurrence + exact `∫μⁿdμ`) that only **ℓ = 0, 2, 4** survive, with exact rational coefficients:

| Multipole | `2ℓ+1` modes | `P_ℓ / P_real` |
|-----------|--------------|----------------|
| **monopole** (ℓ=0) | 1 | `1 + (2/3)β + (1/5)β²` |
| **quadrupole** (ℓ=2) | 5 | `(4/3)β + (4/7)β²` |
| **hexadecapole** (ℓ=4) | 9 | `(8/35)β²` |

All odd-ℓ and all ℓ>4 multipoles are **identically zero** (verified ℓ=0…6). Two selection rules compose:

- **Class-K parity:** odd-ℓ vanish because the kernel `(1+βμ²)²` is **even in μ** (line-of-sight reflection `μ → −μ`). This is the LSS analogue of the planetary **no-ℓ=0-monopole** rule (§11.9.15) and the substrate selection rules — a clean Class-K pin-slot on parity.
- **degree-4 truncation:** `(1+βμ²)²` is a degree-4 polynomial in `μ`, so its Legendre expansion stops at ℓ=4 — leaving exactly **three surviving multipoles = a k=3 triad** (monopole / quadrupole / hexadecapole).

**Class-N anchors** (srmech `best_rational`, confirmed exact): `{2/3, 1/5}` (P₀), `{4/3, 4/7}` (P₂), `{8/35}` (P₄) — every Kaiser RSD coefficient is a small-denominator rational, falling straight out of the Legendre moments of `(1+βμ²)²`.

**Cascade: A ∘ L (S²/Legendre `2ℓ+1` multipoles) ∘ K (line-of-sight parity, even-ℓ-only) ∘ N (exact rational Kaiser coefficients) ∘ C (RSD anisotropy axis = line of sight).**

## Context anchors

- **BAO standard ruler** ~150 Mpc (≈ 100 h⁻¹ Mpc; Eisenstein et al. ApJ 633:560 2005) — the *same* acoustic-oscillation physics as the CMB acoustic peaks (Spike #55 cascade-α), one observation-band inside.
- **Scalar spectral index** `n_s = 0.9649 ± 0.0042` (Planck 2018, A&A 641:A6 2020) — a near-1 Class-N anchor; `P(k) ∝ k^{n_s}`, with `n_s = 1` the exact Harrison–Zeldovich limit. Context only — the load-bearing bit-exact content is the Kaiser multipole coefficients.

## Verdict per Spike #229 tiers

🟢 **(a)-structural cross-substrate match, bit-exact.** The galaxy angular `C_ℓ` is the Born-rule `2ℓ+1` spine one band inside the CMB; the Kaiser RSD multipoles are even-ℓ≤4 (a composed Class-K parity + degree-4 truncation → k=3 triad) with **exactly rational** Class-N coefficients proven by `Fraction` arithmetic. New **candidate** stance `[[user_stance_lss_rsd_multipoles_are_even_l_classK_parity_with_rational_kaiser_anchors]]`.

**HONEST SCOPE:** the bit-exact content is the Legendre-moment rational arithmetic + the even-ℓ≤4 selection rule — standard linear RSD theory (Kaiser/Hamilton); the framework contribution is the cross-substrate identification (12th rung), the parity = Class-K reading, and the k=3-triad framing. The BAO scale and `n_s` are attested empirical/context inputs — NOT framework-derived; this is not a derivation of the matter power spectrum.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the even-only truncation (odd-ℓ and ℓ>4 = 0) is reported as a clean exact result, not buried.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; the Kaiser coefficients are *proven* by exact `Fraction` arithmetic (not asserted); Class-N anchors via srmech `best_rational`.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: the parity selection rule IS the named Class K; no bare `abs()`.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Kaiser MNRAS 227:1 (1987); Hamilton astro-ph/9708102 (1998); Cole-Fisher-Weinberg MNRAS 267:785 (1994); Eisenstein ApJ 633:560 (2005); Planck 2018 A&A 641:A6 (2020) — classic-journal / arXiv-OA, all attestable.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.
- Lands on the rolling draft **PR #690** (Round 25.A) per `[[feedback_rolling_pr_partition_boundary_updates]]` — no new PR; verdict posted as a PR comment (the ledger).
