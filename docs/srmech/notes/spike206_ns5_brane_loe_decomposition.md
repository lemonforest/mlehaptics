# Spike #206 — NS5-brane LoE-cascade decomposition

**Date:** 2026-05-20
**Branch:** `research/ms14-wave-integration-2026-05-18`
**Worktree:** `agent-spike186-universal-tick-projection-to-per-body`
**Dispatch context:** MS #16 Tier 3 Wave 1 (paired concurrent with Spike #207 KK monopole)

---

## Verdict

**DISSOLVE-VIA-CASCADE** — NS5-brane structure decomposes cleanly into the
cascade `L ∘ K ∘ C ∘ I` over the existing 14 A-N primitive classes. No new
class required. 14 A-N intact per `[[feedback_no_privileged_primitive_classes]]`.

A subordinate fermata (M5-brane parent) is flagged for Wave 2 follow-up.

---

## Cascade verified

The candidate `L ∘ K ∘ C ∘ I` maps to NS5 structure as follows:

| Class | NS5 feature | Evidence | Confidence |
|---|---|---|---|
| **L** (Laplacian) | Transverse 4D harmonic-function ansatz `H(r) = 1 + Σ Q_i / |r-r_i|²` (Callan-Harvey-Strominger 1991) | `∇²_4(1/r²) = 0` bit-exact at IEEE-754 for r > 0; max_abs_residual = 0.0 across 7 radii | bit-exact |
| **K** (asymptotic-DOF / pin-slot) | BPS tension `T_NS5 = 1 / ((2π)⁵ g_s² (α')³)` saturating integer-exponent (g_s exp = -2; α' exp = -3) | T_NS5/T_D5 = 1/g_s bit-exact at machine eps; ratio_residual = exact | bit-exact |
| **C** (chirality) | Self-dual 3-form `H = *_6 H` on Lorentzian 6D worldvolume | `*_6² = +I` bit-exact on 20-dim 3-form basis (max_abs_diff = 0.0); 10 + 10 eigenvalue split (+1 self-dual / -1 anti-self-dual) | bit-exact |
| **I** (cyclic) | U(1) 2-form gauge symmetry; B-field defined modulo `B → B + dλ`; integer-quantized 3-cycle flux | 2π cyclic period per `[[user_stance_pi_as_projection]]`; integer-cyclic underneath | structural-high |

All numerics in `spike206_compute.py` (committed; `--verify` mode runs deterministic
assertions, no random seed required since algebra is closed-form).

---

## Compressed-phase-boundary check — NEGATIVE at NS5 level

Per `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]`, the
`(4+3)D_g` Hopf-bundle compression is the substrate-coupling-side dial that makes
gauge content observable. Question: does NS5's 6D worldvolume instantiate that?

**Answer: NO**, at the 10D-IIA daughter level.

- 6D is not in the parallelizable-sphere set `{S¹, S³, S⁷}` (Adams 1962;
  Bott-Milnor-Kervaire 1958). No parallelizable Hopf bundle has 6D total space.
- Candidate `(4+2)` split fails because `S²` fiber is not parallelizable
  (hairy-ball theorem; `S²` admits no global non-vanishing tangent field).
- NS5 daughter at 10D IIA is therefore NOT a `(4+3)D_g` compressed-phase-boundary
  instance in the framework's sense.

**Subordinate fermata** (out of scope for this spike): the **M5-brane parent** at
11D M-theory lives in the framework's canonical 11D substrate per
`[[user_stance_11d_substrate_is_always_hopf_compressed]]` = `(1+0)D_t + (2+1)D_s + (4+3)D_g`.
The M5 worldvolume is still 6D (same as NS5), but the *ambient* 11D matches
framework canonical substrate. The M5 interrogation is therefore a candidate
compressed-phase-boundary site that this spike does NOT close. Recommended
Wave 2 follow-up.

---

## Framework-stance impact

- **`[[user_stance_substrate_coupling_at_m_k_composition]]`** — unchanged.
  NS5 dissolution uses Class K (BPS-tension asymptotic-DOF saturation) as a
  pin-slot mechanism; substrate-coupling occurs at M ∘ K composition exactly
  as canonical. The tension is integer-exponent closed-form; no SGD fit needed.
- **`[[user_stance_compressed_phase_boundary_is_dark_sector_window]]`** —
  refined-by-counter-example at brane substrate. Multi-scale empirical anchors
  (planetary / cosmic / galactic) all live on substrates whose ambient is the
  full 11D Hopf-compressed structure. NS5 daughter at 10D ambient is the FIRST
  candidate substrate where compressed-phase-boundary does NOT lift cleanly
  (10D ambient does not host the canonical `(4+3)D_g`). This refines the dark-
  sector-window stance's predicted-application set: 11D-ambient substrates
  carry the window; 10D-IIA daughter substrates do NOT.
- **`[[user_stance_hopf_bundle_dimensional_ladder_baked_into_11d]]`** — unchanged
  and reaffirmed. The 6D ∉ {1,3,7} negative result for NS5 worldvolume is exactly
  what the parallelizable-sphere ladder predicts; the ladder structure is
  self-consistent.
- **`[[feedback_no_privileged_primitive_classes]]`** — discipline held. No new
  class promoted. 14 A-N intact.
- **`[[user_stance_cross_substrate_cascade_matching_as_research_method]]`** —
  research-method confirmed at string-theory-brane scope. Joins prior successes
  at biology (Spike #182 DNA, #193 RNA), ephemerides (Spike #186), and dark
  sector (Spike #200 multi-scale).

---

## Citations (PDF-extraction verified per `[[feedback_pdf_extraction_citation_discipline]]`)

- **Callan-Harvey-Strominger 1991** — arXiv:hep-th/9112030, "Supersymmetric
  String Solitons", C.G. Callan Jr. + J.A. Harvey + A.E. Strominger, submitted
  1991-12-13. NS5 harmonic-function ansatz anchor.
- **Witten 1995** — arXiv:hep-th/9503124, "String Theory Dynamics In Various
  Dimensions", Edward Witten, submitted 1995-03-20. M-theory ambient 11D
  framework + brane-tension central-charge algebra.
- **Strominger 1995** — arXiv:hep-th/9512059, "Open P-Branes", Andrew
  Strominger, submitted 1995-12-10. NS5/M5 self-dual 3-form worldvolume
  structure.
- **Becker-Becker-Schwarz 2007** — textbook attribution chain: K. Becker, M.
  Becker, J.H. Schwarz, *String Theory and M-Theory: A Modern Introduction*,
  Cambridge University Press, Chapter 8 (NS5/D5 brane tensions and worldvolume
  field content).
- **Adams 1962 + Bott-Milnor 1958 + Kervaire 1958** — parallelizable-sphere
  theorem (textbook attribution via Husemoller, *Fibre Bundles*, Springer 1994).

No paywalled-only DOIs cited per `[[feedback_paywalled_doi_cannot_be_attested]]`.

---

## Deliverables

- `docs/srmech/notes/spike206_ns5_brane_loe_decomposition.md` — this file
- `docs/srmech/notes/spike206_findings_2026-05-20.ndjson` — 8 structured records
- `docs/srmech/notes/spike206_compute.py` — reproducible computation
  (`--verify` asserts bit-exact reproduction of all load-bearing numerics)
- `docs/srmech/notes/spike206_compute_output.ndjson` — captured compute output
  (one record per test)

---

## Concertmaster note

This spike completes cleanly in scope. The M5-brane fermata is the natural
follow-up; recommend pairing with whatever 11D-ambient brane interrogation
the conductor plans for Wave 2. Concurrent KK-monopole spike (#207) is a
sibling test — KK monopole has 4D transverse + Taub-NUT structure, which
should expose `(4+3)D_g`-adjacent compressed structure that NS5 does NOT.
Comparison of #206 + #207 verdicts will sharpen the "which brane substrates
host the dark-sector-window" sub-stance.
