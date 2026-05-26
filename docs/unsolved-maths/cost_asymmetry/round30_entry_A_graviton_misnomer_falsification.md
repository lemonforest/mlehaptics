# Round 30.A — Falsification: is "graviton" a misnomer? (honest NEGATIVE)

**Dispatched** 2026-05-25 on the rolling draft PR #690. User (from the R27/R28/R29 work, where the graviton appears as the spin-weight `|s|=2` member of the spin-weighted Class-L family): *"identify if graviton is a misnomer that just 'seems' gravity related but isn't. do the falsification tests for this."*

This is a **falsification of a user-proposed hypothesis**, run per `[[feedback_dont_pre_commit_spike_query_operators]]` — report whichever way it falls, with the negative as prominent as a positive would be. **It falls against the hypothesis.**

Generating code + provenance: [`verify_round30_graviton_misnomer_falsification.py`](verify_round30_graviton_misnomer_falsification.py) + `.ndjson` (deterministic; srmech 0.4.2).

## Hypothesis H

> "Graviton" mislabels a generic spin-2 excitation as gravity-specific. The spin-2-ness is the real content; "gravity" is a misattribution; a massless spin-2 field need not be gravity.

## Falsification battery (5 tests)

A test **FALSIFIES H** if it shows the spin-2-ness *forces* gravity.

| | test | result | finding |
|--|------|--------|---------|
| **T1** | Weinberg soft-graviton theorem (Phys Rev 135:B1049 1964; 138:B988 1965) | **FALSIFIES** | a consistent massless helicity-2 field *must* couple with **universal** strength to all energy-momentum → equivalence principle → gravity. (Helicity-1 couples to a conserved *charge* = gauge force; helicity-2 couples *universally* to `T_μν`; helicity ≥3 long-range coupling is forced to zero.) |
| **T2** | Deser self-coupling bootstrap (GRG 1:9 1970; gr-qc/0411023) | **FALSIFIES** | a massless spin-2 made self-consistent by coupling to its own stress-energy bootstraps **uniquely** to the full nonlinear Einstein equations = GR |
| **T3** | Unique `T_μν` rank-2 sink (Noether / Coleman–Mandula) | **FALSIFIES** | `T_μν` (translation Noether current) is the unique conserved symmetric rank-2 current; there is **no "other" rank-2 charge** for a spin-2 to couple to instead of energy-momentum |
| **T4** | Empirical quadrupole energy loss (Hulse–Taylor; LIGO) | **FALSIFIES** | PSR B1913+16 orbital decay = **0.997 ± 0.002** of the GR `ℓ=2` quadrupole prediction (Weisberg-Nice-Taylor ApJ 722:1030 2010); GW150914 shows exactly the **2 transverse-traceless** polarizations of a massless spin-2 (Abbott+ PRL 116:061102 2016). The spin-2 radiation does gravitational work at the GR rate. |
| **T5** | The framework's own `ℓ≥|s|` floor (§11.9.21 / §11.9.22) | **NULL** | the `ℓ≥2` (no monopole/dipole) floor is a property of *any* spin-2; it cannot distinguish "graviton = gravity" from "generic spin-2" → non-distinguishing |

**Verdict: 4 FALSIFY, 1 NULL → H is FALSIFIED.** A consistent massless spin-2 is *forced* to be gravity. The spin-2 label and the gravity label are the **same thing by theorem** (Weinberg + Deser uniqueness), not a coincidence — confirmed empirically by the Hulse–Taylor quadrupole energy-loss and LIGO's TT polarizations. **"Graviton" is not a misnomer.**

## Framework refinement (the payoff)

The falsification *sharpens* the R28/R29 picture rather than just negating the question. The spin-weighted Class-L family has a **sharp helicity ceiling for long-range forces** (Weinberg soft theorem):

| `|s|` | long-range force? | couples to |
|------|-------------------|------------|
| 0 | allowed (scalar) | — (no soft-theorem constraint) |
| 1 | allowed (gauge) | a conserved **charge** Q (not universal) |
| **2** | **allowed (gravity)** | **`T_μν` universally** (equivalence principle) |
| ≥3 | **FORBIDDEN** | soft theorem forces coupling → 0 |

So the **allowed long-range helicities are exactly `{0,1,2}`**, and the **graviton (`|s|=2`) is the forced top rung** — the unique helicity that couples universally to energy-momentum. This is a bounded ladder, echoing the framework's Hurwitz-ceiling theme (no continuation past the bound). The graviton is the `|s|=2` entry of the spin-weighted Class-L family (the QNM rung, §11.9.20), *correctly* gravity-tied because the `|s|=2` slot is the one theorem-forced to be gravity.

Where the framework *does* read gravity differently is **fundamental vs emergent**: per Spike #70 (Verlinde emergent-G), #107 (bulk-to-gauge), #71 (2D phase boundary), "gravity" is the emergent substrate-geometry sector, and the graviton is its spin-2 excitation (more like a phonon of substrate-geometry than a fundamental Yukawa carrier). But that is a *fundamental-vs-emergent* nuance — it does **not** make the graviton "not gravity-related." The user's specific hypothesis ("seems gravity related but isn't") is false on every distinguishing test.

## Verdict per Spike #229 tiers

🔴→🟢 **Honest NEGATIVE on H + (a)-structural refinement.** "Graviton is a misnomer" is **falsified** (4/5 tests; 1 null). The constructive payoff: the `{0,1,2}` helicity ceiling places the graviton as the forced top rung of the spin-weighted Class-L family — a bounded-ladder result. New **candidate** stance `[[user_stance_graviton_is_forced_gravity_top_of_helicity_ceiling]]`.

**HONEST SCOPE:** the falsification rests on standard, attested theorems (Weinberg, Deser, Weinberg–Witten, Coleman–Mandula) + attested empirical results (Hulse–Taylor, LIGO); the framework contribution is *only* the placement (graviton = `|s|=2` top rung of the long-range-force helicity ceiling, within the R28/R29 spin-weighted Class-L family) and the emergent-gravity cross-reference — no new physics. No lean toward the framework's prior emergent-gravity preference: the physics forbids "graviton ≠ gravity" outright.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the result is the *negative* of the user's hypothesis, reported plainly; the framework's own `ℓ≥|s|` floor is honestly logged as NULL (non-distinguishing), not bent to support a desired answer.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; the helicity ceiling + battery tabulated and asserted.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Weinberg PR 135:B1049 / 138:B988; Deser GRG 1:9 (gr-qc/0411023); Weinberg-Witten PLB 96:59; Weisberg-Nice-Taylor ApJ 722:1030 (arXiv:1011.0718); Abbott+ PRL 116:061102 (arXiv:1602.03837) — all attestable.
- Per `[[feedback_no_lineage_claims_in_notebook]]`: reads what the uniqueness theorems already establish; claims no new gravity physics.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.
- Lands on the rolling draft **PR #690** (Round 30.A) — no new PR; verdict posted as a PR comment (the ledger).
