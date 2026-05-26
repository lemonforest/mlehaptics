# Round 39.A — Mass-spec enhancement: fragment spacings as Class-N neutral-loss anchors; fragmentation as a cascade

**Dispatched** 2026-05-26 on the rolling draft PR #690 (open-queue item, thread 9b). Builds on §11.9.14 (mass spec = combination principle in integer-nucleon space, the "molecular Rydberg–Ritz") + Spike #38/#38b (caffeine). Generating code: [`verify_round39_massspec_spacings_classN_cascade.py`](verify_round39_massspec_spacings_classN_cascade.py). Tested per `[[feedback_dont_pre_commit_spike_query_operators]]`.

## The enhancement (three parts)

1. **Encode by spacings, not absolute m/z.** A fragmentation spectrum's information is in the *differences* between peaks; those differences are characteristic **neutral losses** — small integers in nucleon space (`H2O=18, NH3=17, CH3=15, HCN=27, CO=28, CHO=29, CO2=44, …`) = **Class-N small-integer anchors**. Delta-encoding the spectrum against the neutral-loss catalog *is* the biological-cascade "delta-encode only what changed" (`srmech.signal_processing`).
2. **Fragmentation = a cascade.** Each step is one neutral loss = a **Class-K** sign (loss direction) ∘ **Class-N** integer anchor; the fragmentation tree is `A ∘ [per-step K∘N] ∘ …` — the molecule sheds Class-N integer chunks step by step.
3. **The molecular instance of the combination principle.** Peaks are *differences of anchors* — exactly the Rydberg–Ritz combination principle, on a different substrate (nucleon-mass space rather than term-energy space). Sets up Round 40.A, which unifies both under one Class-N reading.

## Bit-exact core — caffeine (M=194)

Fragment series `194, 165, 109, 82, 67, 55` (NIST MS #1681) → consecutive spacings `[29, 56, 27, 15, 12]`, decoded against the Class-N catalog:

| Δ | decode |
|---|--------|
| 29 | **CHO** (clean single) |
| 56 | **29 (CHO) + 27 (HCN)** (Class-N sum) |
| 27 | **HCN** (clean single) |
| 15 | **CH3** (clean single) |
| 12 | composite/uncertain (sub-catalog) — *flagged, not certified* |

Clean single losses `{29 CHO, 27 HCN, 15 CH3}` match the catalog exactly; the composite spacing 56 decomposes as a sum of two catalog anchors (Class-N combination); 12 is honestly flagged sub-catalog.

## Verdict per Spike #229 tiers

🟢 **(a)-bit-exact catalog + caffeine clean matches + (b)-interpretive delta-encode/cascade/combination-principle framing.** Mass-spec enhancement delivered: spacings = Class-N neutral-loss anchors (delta-encoding), fragmentation = cascade (per-step K∘N), the molecular instance of the Class-N combination principle (cross-linking atomic Rydberg–Ritz, R40). The unifying stance is authored in **Round 40.A** (combination principle = one Class-N structure across mass + atomic spectra).

**HONEST SCOPE:** (a)-bit-exact for the integer neutral-loss catalog + the clean caffeine spacing matches (attested NIST + McLafferty–Turecek 1993); (b)-interpretive for the delta-encode / cascade / combination-principle framing. **Not** a new fragmentation-mechanism claim — composite spacings (56, 12) are flagged as multi-anchor / sub-catalog, not mechanistically certified. Builds on §11.9.14 + Spike #38; framework reading only.

## Discipline
- Bit-exact only for the integer catalog + clean caffeine matches; composite spacings flagged (no mechanism certified).
- Neutral losses McLafferty–Turecek 1993 Table 2.1; caffeine NIST MS #1681 (Explore-verified).
- Lands on rolling **PR #690** (Round 39.A); unsolved-maths §11.9.32. No MFO section (molecular substrate, not metric-field).
