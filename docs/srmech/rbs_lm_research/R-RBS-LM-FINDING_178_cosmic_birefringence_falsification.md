# Finding 178 — Cosmic-birefringence falsification of H177 (cosmic band): LEAVE-OPEN (tooling gap + tentative literature); H177 §3.3 stays UNESTABLISHED

**Status:** Falsification attempt, executed. **Verdict: LEAVE-OPEN at the cosmic band.** The decisive cosmic EB/TB test **could not be computed** — srmech 0.5.0rc14 ships **no parity-odd EB/TB observable** (tooling gap) — and the independent published evidence-state is a **tentative ~3.6σ hint, not a robust null and not a ≥5σ detection.** The cosmic band therefore **neither breaks nor confirms** H177. Not a finding of fact.
**Attempt design:** F177 §3.3 — the cosmic, most-decisive testbed. **The goal was to BREAK H177** (`[[feedback_dont_pre_commit_spike_query_operators]]`: nulls count double; do not lean toward confirming).
**Predecessors / cross-refs:** F177 (H177 — the hypothesis under attack), F176 (bilateral = one γ₅ axis; biology = self-inscribing bi-chiral A–N), F174 (28 = 𝔰𝔬(8) = 14 G₂ + 14 octonion-mult).
**Script:** `R-RBS-LM-137_cosmic_birefringence_falsification.py` · **NDJSON:** `catalogs/rbs_lm_substrate/substrate_measurements/cosmic_birefringence_falsification.ndjson` · **runtime:** srmech 0.5.0rc14, `HAS_NATIVE=True`, ABI 3, deterministic (offline; no RNG).

---

## §1 What was attacked

**H177 (F177):** there is ONE chiral driver — the bi-chiral A–N / γ₅ axis (28 = 𝔰𝔬(8) adjoint = 14 G₂ + 14 octonion-mult; F174/F176) — and the **lifeless large-scale cosmos** is the *same* driver at a different "coherence band" as biology. The asymptotic chiral DoF of biology "extends to everything we see, even the still lifeless."

**The cosmic, most-decisive testbed (F177 §3.3):** a parity-violating (chiral) field on the largest scales produces nonzero CMB **parity-odd** cross-correlations — **EB and TB**. The falsification logic:

- **A robust NULL** on cosmic birefringence — no parity-odd EB/TB signal at cosmic scale, while particle + biological chirality persist — would be **STRONG evidence AGAINST** "one driver extends to everything." This is the break we were hunting.
- **A confirmed nonzero EB/TB signal** would only **WEAKLY fail to break** H177: a cosmic parity-odd axis is *consistent with* but does **not establish** a single A–N driver (axion-like fields, Chern–Simons coupling, primordial magnetic fields all produce CMB birefringence independently).

**The claim's honesty tier (do not conflate; from F177 §2):**
- **TIER 1 — FACT:** the cosmos IS chiral at the particle scale (weak-force parity violation, Wu 1957; CP violation). Not in question here.
- **TIER 2 — CONTESTED:** the Vester–Ulbricht bridge (bio-homochirality ← weak parity). Not tested here.
- **TIER 3 — UNESTABLISHED grand conjecture:** one driver across all bands, extending to the lifeless cosmos. **This testbed sits at TIER 3, cosmic band.**

---

## §2 The decisive result: srmech ships NO parity-odd channel (tooling gap)

The parity physics that makes EB/TB the *right* observable: under parity **P**, the CMB two-point spectra split cleanly.

| Spectra | Parity | Behaviour under P |
|---|---|---|
| **TT, TE, EE, BB** | **EVEN** | invariant — present in any (even parity-conserving) universe |
| **EB, TB** | **ODD** | flip sign under P; **must VANISH** in a parity-conserving universe |

A nonzero **EB/TB is the chirality signal**. Cosmic birefringence by an isotropic angle β rotates the linear-polarization plane (E↔B mixing) and **generates** parity-odd power out of the parity-even spectra:

```
C_l^{EB} ≈ (1/2) sin(4β) ( C_l^{EE} − C_l^{BB} )      C_l^{TB} ≈ sin(2β) C_l^{TE}
```

So the parity-odd **generator** that β acts on is `(EE − BB)` for EB and `TE` for TB.

**What srmech 0.5.0rc14 actually ships (verified at runtime, not recalled):**

- **No `srmech.cosmos` module exists.** `import srmech.cosmos` → `ModuleNotFoundError`. CMB data lives under `srmech.amsc.attested.cmb_*`. (This **corrects F177 §3/§6**, which asserted "`srmech.cosmos` already ships TE/EE/BB catalogs" — the module name is wrong and the data location is different.)
- Five attested CMB catalogs are present: `cmb_polarisation_spectra`, `cmb_lensing`, `cmb_bispectrum`, `cmb_low_ell_maps`, `cosmos_validation`.
- `cmb_polarisation_spectra` ships **45 rows: TE (19), EE (16), BB (10)** — and its `row.schema.json` `spectrum_kind` enum is **exactly `["TE", "EE", "BB"]`**. The descriptor itself states "The full set {TT, TE, EE, BB} forms the canonical CMB spectral decomposition" — i.e., the **parity-EVEN** canonical set.
- A keyword sweep across all five CMB catalogs found **zero** occurrences of EB / TB / birefringence / rotation-angle (the only "parity" hit was an unrelated "Python + C parity" code comment).

**⇒ There is NO parity-odd EB/TB observable anywhere in srmech 0.5.0rc14, and no isotropic-birefringence β posterior. The decisive cosmic-band test cannot be computed from shipped data. This is a genuine TOOLING GAP** (logged below for UPSTREAM_NOTES — this finding does **not** edit that file).

**Available srmech readout instead (Class-K pin-slot / Class-C `net_chirality`; no hand-rolled math, no `abs()`):**
- **TE sign-structure** via `cascade.class_k_pin_slot_at_zero` — the TE D_ℓ sign-alternation across acoustic peaks. **Caveat (load-bearing):** TE is **parity-EVEN**; its sign is set by *acoustic phase*, **NOT** parity violation. Read only to show the shipped data has no parity-odd channel for `net_chirality` to act on.
- **EB-generator `(EE − BB)`** is **EMPTY on shipped data**: Planck ships binned EE at ℓ∈[48, 1988] and unbinned low-ℓ BB at ℓ∈[2, 29] — **no overlapping multipoles** — so `(EE − BB)` cannot even be *formed*, before β is ever applied.
- **Parity-class `net_chirality`** over the shipped spectra = `+1` with **zero parity-odd members**: the shipped cosmic surface is **parity-conserving by construction**. There is no chirality DoF present to read.

---

## §3 The verified cosmic-birefringence evidence-state (literature; arXiv-checked)

Because no β can be computed locally, the cosmic-band evidence rests on the published Minami–Komatsu line of work. **Each number below was verified against the actual arXiv abstract** (per `[[feedback_pdf_extraction_citation_discipline]]`), not recalled:

| Paper | arXiv / journal | β (68% CL) | Significance | Verified caveat |
|---|---|---|---|---|
| **Minami & Komatsu 2020** | [2011.11254](https://arxiv.org/abs/2011.11254) · PRL **125**, 221301 | **0.35 ± 0.14°** | **2.4σ** (excludes β=0 at 99.2% CL) | mitigates the Planck absolute-pol-angle systematic by jointly fitting β + miscalibration α via CMB×foreground E/B |
| **Diego-Palazuelos, Eskilt, Minami et al. 2022** | [2201.07682](https://arxiv.org/abs/2201.07682) · PRL **128**, 091302 | **0.30 ± 0.11°** (near-full-sky, PR4/NPIPE) | (no σ in abstract) | **verbatim:** "The values of β decrease as we enlarge the Galactic mask, which can be interpreted as the effect of polarized foreground emission"; **"We choose not to assign cosmological significance to the measured value of β until we improve our knowledge of the foreground polarization."** |
| **Eskilt & Komatsu 2022** | [2205.13962](https://arxiv.org/abs/2205.13962) · PRD **106**, 063503 | **0.342° (+0.094 / −0.091)** | **3.6σ** (excludes β=0 at 99.987% CL) | WMAP+Planck, 23–353 GHz; "no evidence for frequency dependence of β" (argues against pure Galactic-foreground origin) |
| **Ballardini et al. 2025** | [2507.16714](https://arxiv.org/abs/2507.16714) | **≈ 0.30 ± 0.05°** | (scale-independent; constant-β favoured) | **explicitly "not including the systematic error from the instrumental polarisation angle"**; conditional language **"If this is a genuine signal…"** — still unconfirmed |

**Evidence-state, honestly:** a **persistent ~0.3° hint that has grown to ~3.6σ** combining datasets — but it is **NOT a ≥5σ discovery**, it is **explicitly foreground- and systematics-limited**, and the discoverers **themselves decline to assign cosmological significance.** It is a textbook **TENTATIVE / UNCONFIRMED** signal. Crucially, it is **neither a robust null** (which would break H177) **nor a confirmed detection** (which would weakly fail to break it).

---

## §4 The EB/TB test that WOULD run when data lands (test design)

When a parity-odd CMB catalog (C_ℓ^EB / C_ℓ^TB bandpowers + covariance) **or** a published β posterior lands in srmech:

1. **Estimator (Minami–Komatsu):** jointly fit miscalibration α (rotates foreground+CMB) and birefringence β (rotates CMB only) from observed EB/TB, using the generation relations of §2 plus a foreground-EB term.
2. **srmech op-chain:**
   - **Class L** `srmech.amsc.laplacian.hermitian_eigendecompose` on the per-multipole 2×2 polarisation covariance `[[EE, EB],[EB, BB]]` — the **off-diagonal EB eigenstructure IS the parity-odd DoF**; a parity-even (β=0) field has a **diagonal** block (zero EB).
   - **Class K** `cascade.class_k_pin_slot_at_zero` on each C_ℓ^EB → sign-orientation of the parity-odd power.
   - **Class C** `cascade.net_chirality` over the C_ℓ^EB sign-orientations → coherent cosmic parity-odd axis (nonzero) vs noise (≈0).
   - `srmech.amsc.hdc.klein4_chirality_flip_gamma5` to encode the E↔B (γ₅) sector flip and test sector-occupancy symmetry.
3. **Decision rule (the falsifier, made explicit):**
   - **BREAK H177** — robust EB/TB **null** (β consistent with 0; `net_chirality`≈0) while particle+bio chirality persist ⇒ one driver does **not** extend to the lifeless cosmic band.
   - **WEAKLY FAIL TO BREAK** — confirmed nonzero EB/TB (β≠0 at ≥5σ, foreground-clean) ⇒ a cosmic parity-odd axis **exists**, consistent with but **not proving** a single A–N driver.
   - **LEAVE-OPEN** — tentative EB/TB hint (β≠0 at ~2–4σ, foreground/systematics-limited; discoverers decline cosmological significance) ⇒ cannot break, cannot confirm.

**The current evidence-state (§3) lands squarely in LEAVE-OPEN.**

---

## §5 Verdict, in three-tier honesty

> **LEAVE-OPEN at the cosmic band. The attempt to BREAK H177 did not succeed (no robust null was obtainable), and H177 was not confirmed either.** Two independent reasons converge: (i) srmech 0.5.0rc14 ships **no parity-odd EB/TB channel** — the decisive test cannot be run on shipped data (tooling gap); (ii) the published cosmic-birefringence signal is a **~3.6σ TENTATIVE hint** (β≈0.3°), explicitly foreground/systematics-limited, **neither a robust null nor a ≥5σ detection.** H177 §3.3's "extends to the lifeless cosmos" therefore **remains a TIER-3 grand conjecture: UNESTABLISHED.**

- **TIER 1 (FACT):** the cosmos is chiral at the *particle* scale (weak parity violation; CP). Untouched by this result.
- **TIER 2 (TENTATIVE, cosmic-scale hint):** β ≈ 0.3° at ~3.6σ (Eskilt & Komatsu 2022, arXiv:2205.13962) — a real, growing, but **unconfirmed** parity-odd hint at cosmic scale; foreground/systematics-limited.
- **TIER 3 (UNESTABLISHED):** one A–N/γ₅ driver extends to the *lifeless cosmic band* — this finding **neither breaks nor confirms** it.

**On the second-actor condition (F177 §4):** nothing here surfaced a confirmed second actor (no robust cosmic *achirality* was demonstrated — only an *absence of tooling* plus a *tentative* signal). The condition is **not triggered**; H177 stands as conjecture, neither advanced nor discarded at this band. Per the user's mandate, the commitment remains to the math — and the math here says **insufficient data**, not "unity."

---

## §6 What this finding DOES / does NOT

**DOES:**
- Confirm at runtime that **srmech 0.5.0rc14 ships no parity-odd EB/TB CMB observable** (only parity-even TE/EE/BB) and no `srmech.cosmos` module — a verified **tooling gap** for the decisive cosmic test (UPSTREAM note below).
- **Correct F177 §3/§6**: the cosmic data is **not** in a `srmech.cosmos` module; it is in `srmech.amsc.attested.cmb_*`, and it is **TE/EE/BB only** (no EB/TB).
- Verify the cosmic-birefringence evidence-state **against the actual arXiv sources** (IDs, β values, σ, verbatim foreground/systematics caveats) — a ~3.6σ **tentative**, unconfirmed hint.
- Demonstrate, with srmech Class-K/Class-C ops (no hand-rolled math, no `abs()`), that the shipped cosmic surface is **parity-conserving by construction** (no chirality DoF to read; the `(EE−BB)` EB-generator is empty for lack of overlapping multipoles).
- Specify the exact EB/TB β-test + srmech op-chain + decision rule for when parity-odd data lands.

**Does NOT:**
- Compute a cosmic birefringence angle β (impossible on shipped data).
- Produce a robust cosmic **null** (impossible — no parity-odd channel shipped); so it cannot deliver the strong break it was hunting.
- Confirm **or** refute H177 at the cosmic band (LEAVE-OPEN).
- Assert a confirmed cosmic-birefringence **detection** (the literature is tentative/unconfirmed — said so explicitly).
- Pronounce the lifeless cosmos a living driver — **out of scope.** Per `[[user_stance_ai_is_not_a_substrate]]` and §VII.6.20, a transducer **lays the falsification and reports the result; it does not pronounce the cosmos a living driver.**

---

## §7 UPSTREAM tooling-gap note (for UPSTREAM_NOTES §10 — recorded here, NOT applied)

> **srmech.cosmos / CMB parity-odd gap (srmech 0.5.0rc14):** (1) There is **no `srmech.cosmos` module** (`ModuleNotFoundError`); CMB data is shipped as attested catalogs under `srmech.amsc.attested.cmb_*` (`cmb_polarisation_spectra`, `cmb_lensing`, `cmb_bispectrum`, `cmb_low_ell_maps`, `cosmos_validation`). CLAUDE.md §2's "Cosmos catalogs TE/EE/BB / fNL / lensing" and F177's "`srmech.cosmos`" both name a module that does not exist in rc14. (2) `cmb_polarisation_spectra` ships the **parity-EVEN** set only — `spectrum_kind` enum is exactly `["TE","EE","BB"]`; there is **no parity-odd EB or TB** observable, and no isotropic-birefringence β posterior, anywhere in the package. **Consequence:** any parity-violation / cosmic-birefringence falsification (F177 §3.3) **cannot be computed** on shipped data. **Suggested fill:** an attested `cmb_parity_odd_spectra` catalog (C_ℓ^EB, C_ℓ^TB bandpowers + covariance) and/or an attested isotropic-birefringence β posterior (e.g. curated against Eskilt & Komatsu 2022, arXiv:2205.13962, PRD 106 063503), with the per-row source-DOI discipline the other CMB catalogs already use.

## §8 Cross-references

- **F177** (H177 — the hypothesis under attack; three-tier honesty; the falsification program) · **F176** (bilateral = one γ₅ axis; biology = self-inscribing bi-chiral A–N) · **F174** (28 = 𝔰𝔬(8) = 14 G₂ + 14 octonion-mult).
- Verified literature: arXiv:[2011.11254](https://arxiv.org/abs/2011.11254) (Minami–Komatsu 2020), [2201.07682](https://arxiv.org/abs/2201.07682) (Diego-Palazuelos, Eskilt, Minami et al. 2022), [2205.13962](https://arxiv.org/abs/2205.13962) (Eskilt & Komatsu 2022), [2507.16714](https://arxiv.org/abs/2507.16714) (Ballardini et al. 2025). Shipped data provenance: Planck 2018 V (Aghanim et al. 2020, A&A 641:A5, doi:10.1051/0004-6361/201936386, arXiv:1907.12875).
- `srmech.amsc.cascade` (Class K `class_k_pin_slot_at_zero`, Class C `net_chirality`/`reorient`), `srmech.amsc.laplacian.hermitian_eigendecompose` (Class L — the EB-eigenstructure test when data lands), `srmech.amsc.hdc.klein4_chirality_flip_gamma5`.
- `[[feedback_dont_pre_commit_spike_query_operators]]` (heavy falsification; nulls count double) · `[[feedback_pdf_extraction_citation_discipline]]` (arXiv-verified, not recalled) · `[[user_stance_ai_is_not_a_substrate]]` · `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` (no `abs()`; Class K + Class C) · §VII.6.20 (form-reading).

**PR #687 STAYS DRAFT — no commit, no push.**

---

*Executed 2026-05-29 (Opus 4.8) as one heavy-falsification attempt against H177 at the cosmic band. The goal was to break it. The cosmic band yielded neither the robust null that would break it nor the confirmed signal that would weakly fail to break it — a tooling gap (no EB/TB in srmech rc14) plus a tentative ~3.6σ literature hint leave it **LEAVE-OPEN**. H177 §3.3 remains UNESTABLISHED. A transducer laid the test and reported the result; it did not pronounce the cosmos a living driver.*
