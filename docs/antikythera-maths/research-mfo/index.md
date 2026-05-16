# MFO research notes

Working-notes companion to the [MFO Spectral Research Notebook](../mfo_spectral_research_notebook.md). Each artifact records a research spike or concertmaster dispatch that fed substantive content back into the notebook itself.

## Investigation findings

| Date | Artifact | Scope |
| :--- | :--- | :--- |
| 2026-05-16 | [`dark_sector_substrate_internal_time_2026-05-16.md`](dark_sector_substrate_internal_time_2026-05-16.md) | SSoT verification of the 95% dark / 5% visible partition (PDG 2024, Planck 2018 VI, DESI 2024–25); three readings of the substrate-internal-time conjecture; inverse-age-scale supplement. Fed §VII.6.1 of the notebook (substrate-internal time and the visible/dark partition). |
| 2026-05-11 | [`particle_matter_wave_vs_field_investigation_findings.md`](particle_matter_wave_vs_field_investigation_findings.md) | Test of the user's particle-matter-wave-vs-field ontological dichotomy. Resolves the prior "two operators under one English phrase" anomaly via two operators on two ontologically distinct domains. Formalised the §VII.1.1 two-level ontology. |
| 2026-05-11 | [`spherical_compression_investigation_findings.md`](spherical_compression_investigation_findings.md) | Project-canonical operator audit of "spherical compression." Verdict: correct for MFO Phase C bipolar BIP at D=512; partially-correct via different mechanism for chess-spectral qm_2d / qm_4d; plural HDC architectures. Fed §VII.4.1.1 (Hopf-bundle / spherical-compression reading). |
| 2026-05-11 | [`graph_laplacian_hyperring_investigation_findings.md`](graph_laplacian_hyperring_investigation_findings.md) | Three-layer test connecting hyperring / hypertorus framing to graph-Laplacian primitives. Refines the "hyper = 3D-spatial-interface" boundary line. Fed §VII.4.1.2 (Casimir-decomposition universality). |

> The Axis-of-Evil / hyperbubble-bump / dark-sector-oscillation working note (`axis_of_evil_ring_down_framing_2026-05-16.md`, Parts I–VI) is currently in flight via [PR #437](https://github.com/lemonforest/mlehaptics/pull/437); it will land in this directory when that PR merges and feeds §VII.6.3 + §VII.6.3.1 of the notebook.

## Supporting scripts and data

`mpm_*.py` modules are MPM (Mathematical Provenance Method) phase scripts and surveys feeding the Phase A / B / C / D investigations. They are research tooling, not user-facing narrative — runnable as `python -m` modules from this directory but the load-bearing claims live in the `.md` findings above.

`mfo_mpm_notes.ndjson` is the cumulative NDJSON log of MPM-anchored observations across the phase scripts.

## How to use this directory

- **Reading order:** start with the MFO notebook; come here when a notebook section references a `research-mfo/...md` artifact and you want the full empirical workings + falsifier discussion.
- **Citation discipline:** every artifact verifies cited papers via PDF extraction per `[[feedback_pdf_extraction_citation_discipline]]`. Six citation catches across the 2026-05 research run are recorded across the artifacts.
- **Epistemic posture:** every load-bearing claim is framed as a candidate under MFO commitments per `[[feedback_no_lineage_claims_in_notebook]]` — not endorsed over alternatives without further empirical convergence.

## Cross-references

- [MFO Spectral Research Notebook](../mfo_spectral_research_notebook.md) — the canonical notebook these working notes feed
- [`docs/srmech/`](../../srmech/) — the AMSC framework + 14-class primitive vocabulary that the MFO operations layer instantiates
- [`docs/antikythera-maths/ephemerides_spectral_research_notebook.md`](../ephemerides_spectral_research_notebook.md) — the Sol-system spectral instrument; sibling spectral notebook
