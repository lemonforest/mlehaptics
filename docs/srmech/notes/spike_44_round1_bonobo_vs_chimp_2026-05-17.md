# Spike #44 round 1 — Bonobos vs chimpanzees: spectral shape of SHARING vs SURVIVING (multi-iteration; round 1 of N; USER-GATED no-merge)

**Date:** 2026-05-17
**Research spike artifact, round 1.** Concertmaster dispatch per user direction. **NOT FINAL SHAPE** — round 1 establishes methodology + data + baseline; round 2 awaits conductor review then user-approval.

> **User direction (verbatim):** *"press bonobos vs chips in a deaper research to model the shape of sharing vs the shape of surviving. this isn't a meta thing, this is real, use validated source and preserve references in the notes you make. don't immediately merge this, review and then redispatch the subagent, I don't think that the final shape will come to us upon first glance."*

> **Discipline.** REAL DATA from validated peer-reviewed primatology, NOT theory-only. Every reference: authors / title / journal / year / DOI / PDF-extracted-or-flagged per `[[feedback_pdf_extraction_citation_discipline]]`. Math-doesn't-lie: when simple axis failed, agent investigated and reported. USER-GATED on round 2 dispatch.

---

## §1 Round-1 bottom line

**The simple linear axis "bonobo = sharing-shape, chimp = surviving-shape" does NOT survive contact with data. User predicted this; data confirms.**

What survives, and what round 2 should test: **the two species differ in TOPOLOGY more than in VOLUME**.

- **Bonobos have HIGHER raw aggression than chimps** in some channels (Mouginot 2024: ~3× male-male contact aggression rate; ~6903 vs ~2301 attacks/100,000h)
- **But bonobos NEVER kill** (Wilson 2014 Nature: 0 lethal events across 4+ bonobo communities; chimps had 152 across 18 communities)
- **Both species build hierarchies** (Class K asymptotic-DOF signature present in both); the difference is WHO COALESCES TO REBALANCE
- **Both species share, on NON-OVERLAPPING resource catalogs** (bonobos: food not tools; chimps: tools not food per Krupenye 2018)

Cleanest discriminator at round-1 resolution: **Class L lethal-aggression partition signature**. Chimp social graph fragments into communities with adversarial cross-cut edges (pooled Wrangham 2006: 125/100,000/yr intergroup kill rate); bonobo social graph is cross-community-permeable with defined-zero lethal-partition.

## §2 Per-species per-signature fingerprints

| Signature class | Chimp value | Bonobo value | Discrimination |
|---|---|---|---|
| **Class L** lethal-intergroup partition | 125/100k/y pooled; 6 of 9 communities >0; mean inflated by Gombe-Kahama outlier | DEFINED ZERO across 4+ communities | **CLEAN** (categorical) |
| **Class L** lethal-intragroup | 200-1008/100k/y across communities | ~0 (1 incident report Feb 2025 LuiKotale) | **CLEAN** (rate 200× +) |
| **Class K** steepness (males) | 0.22-0.70 (mean ~0.43) | 0.35-0.70 (mean ~0.52) | NOT clean — overlap |
| **Class K** intersex dominance | Male-dominant nearly always | Female-coalition-dominant 85-98% of conflicts | **CLEAN** (signed) |
| **Class C** grooming-up-hierarchy | Sonso 60% / M-group 49% / Sanctuary 50% | ~50% (no rank effect, Krupenye 2018) | MEDIUM — varies within chimp |
| **Class C** cascade reciprocity | Sonso 0.45 / M-group 0.66 / Sanctuary 0.05 | Symmetric (no rank, no reciprocity) | MEDIUM — varies within chimp |
| **Class E** sharing catalog | Tools (not food) | Food (not tools) | **CLEAN** (disjoint catalogs) |
| **Aggression volume** (male-male) | 2301/100k h | 6903/100k h | INVERTED — bonobos higher |
| **Aggression target** | ~half cross-sex | ~10% cross-sex | **CLEAN** |

Synthetic proto-graph: bonobo Fiedler λ₂ = 2.4 vs chimp Fiedler λ₂ = 1.4 (ratio 1.71×). Bonobo proto-graph more integrated; chimp more partitioned. **But these are CONSTRUCTED graphs from published summary metrics, not raw matrices** — round-2 priority is raw adjacency.

## §3 Five anomalies investigated

1. **Bonobos MORE aggressive than chimps** (Mouginot 2024). Resolution: aggression VOLUME isn't the discriminator; aggression TOPOLOGY is. Bonobo aggression same-sex, non-lethal, asymptotic-DOF de-escalation. Chimp aggression cross-sex/cross-community, escalatable to lethal.
2. **Bonobo male hierarchy can be as steep as chimp** (Stevens 2007). Resolution: steepness alone isn't discriminator; whether COALITION TOPOLOGY CROSSES SEX is. Bonobo female-coalition Class L overrides male Class K. Chimp female-coalition essentially absent.
3. **Non-overlapping sharing catalogs** (Krupenye 2018). Resolution: Class E catalog asymmetry. Round-2 question: does this map to immediate-substrate (food) vs mediated-substrate (tool-as-future-acquisition)?
4. **Funkhouser 2018: grooming non-reciprocal but agonism reciprocal**. Resolution: Class C cascade-reciprocity is edge-type-specific. Cost-cascade and benefit-cascade reciprocate differently.
5. **Transcription anomaly self-caught**: arithmetic-mean kill rate inflated by Gombe-Kahama outlier; pooled rate 125/100k/y vs arithmetic 1494/100k/y. Both numbers real; both retained in records.

## §4 Round-2 proposal (USER-GATED)

**HIGH priority for round 2**:

1. **Fetch raw adjacency matrices** from Torfs 2023 S1, Funkhouser 2018 S1/S2, Kaburu 2015 supplementary. Compute REAL Class L Fiedler / λ₂ / spectral density on raw graphs. Hypothesis: bonobo λ₂/λ_max systematically higher (more integrated).

2. **Signed-graph Laplacian on grooming + aggression merged** (Funkhouser has both for same 7 individuals; Kaburu has both for Sonso + M-group males). Signed Fiedler partition should align by sex-class in chimps, by coalition-role-class in bonobos.

**MEDIUM priority**:

3. Class E catalog overlap (Jaccard) — enumerate documented voluntary-transfer events per species.
4. Class I cyclic-encounter test — do bonobo intergroup encounters show periodic recurrence vs chimp aperiodic patrols? FFT/autocorrelation.
5. Class C cascade-escalation coefficient — mean ratio of severity_(n+1)/severity_n along aggression cascades. Bonobo expected <1 (de-escalating); chimp ≥1.

## §5 14 references with full provenance

**Open-access verified, full PDF extracted** (8): Wrangham/Wilson/Muller 2006 Primates; Krupenye/Tan/Hare 2018 Proc R Soc B; Funkhouser/Mayhew/Mulcahy 2018 PLOS ONE; Kaburu/Newton-Fisher 2015 Animal Behaviour (PMC4287234); Torfs 2023 PLOS ONE (S1 pending round-2); Nolte/Sterck/van Leeuwen 2023 Roy Soc Open Sci; Sandel/Watts 2021 Int J Primatol; Silk 2014 Nature commentary.

**Citation-only per TOS landscape** (paywall; no autonomous PDF) (6): Wilson et al. 2014 Nature; Mouginot et al. 2024 Current Biology; Surbeck et al. 2025 Communications Biology; Tokuyama/Sakamaki/Furuichi 2019 AJPA; Stevens et al. 2007 Int J Primatol; Furuichi 2011 Evolutionary Anthropology.

Full provenance in `spike_44_round1_references.ndjson`.

## §6 Spike #43c connection candidate fermata (flagged, NOT forced)

If bonobo sharing-shape decomposes as `[high cross-community Class L permeability + symmetric Class C cascade + food-class Class E catalog + female-coalition Class K rebalancing]`, AND Spike #43c finds well-spread human knowledge has analogous decomposition `[cross-domain Class L permeability + symmetric cite-flow Class C + open-access Class E catalog + decentralized validation coalitions]`, sharing-shape may be substrate-portable from primate-social to knowledge-transmission. **Discipline**: do NOT force. Compare round-1 outputs after both land. If shapes disagree, sharing-shape is primate-substrate-specific — that's a real finding too.

## §7 Discipline guards honoured

- `[[user_stance_string_theory_instrument_first]]` — data drove conclusion that simple axis fails; framework-arguing rejected
- `[[user_stance_kepler_shape_universal]]` — `c_k = ε^k × K_k(substrate)` extended to primate-social; K_k differs by species
- `[[user_stance_partition_for_understanding]]` — bonobo and chimp shapes both real partitions of Pan substrate; "sharing/surviving" recognised as user-supplied linguistic partition that substrate shape may not map cleanly to
- `[[user_stance_primitives_weave_and_thread]]` — cascade composition framework applied
- `[[user_stance_identity_not_implementation_discipline]]` — bonobo cascade IS food-channel-symmetric; chimp cascade IS tool-channel-asymmetric (identity at substrate level)
- `[[feedback_no_privileged_primitive_classes]]` — zero new classes; 14 A-N suffice
- `[[reference_autonomous_validation_tos_landscape]]` — open-access only for autonomous PDF (PLOS, PMC, Royal Society, bioRxiv author-deposit); commercial titles citation-only
- `[[feedback_pdf_extraction_citation_discipline]]` — every reference has full provenance in NDJSON
- `[[feedback_science_is_ssot_not_project]]` — primatology canonical literature is SSoT; project did NOT generate any primatological claims
- `[[feedback_trauma_informed_defensive_scope]]` — descriptive species behavior only; no human-political projection
- `[[feedback_ndjson_over_bloated_json]]` — NDJSON outputs throughout
- `[[feedback_concertmaster_md_writes]]` — agent inline; conductor captured-and-saved
- `[[feedback_concertmaster_git_worktree_isolation]]` — zero agent git ops

## §8 Artifacts

- [`spike_44_round1_bonobo_data.py`](spike_44_round1_bonobo_data.py) + manifest — 6 bonobo data substrates indexed
- [`spike_44_round1_chimp_data.py`](spike_44_round1_chimp_data.py) + manifest — 6 chimp data substrates indexed
- [`spike_44_round1_signature_analysis.py`](spike_44_round1_signature_analysis.py)
- [`spike_44_round1_synthesis.py`](spike_44_round1_synthesis.py)
- [`spike_44_round1_references.ndjson`](spike_44_round1_references.ndjson) — 14 references with full provenance
- [`spike_44_round1_records_2026-05-17.ndjson`](spike_44_round1_records_2026-05-17.ndjson) — 13 signature-analysis records
- [`spike_44_round1_synthesis_records.ndjson`](spike_44_round1_synthesis_records.ndjson) — 17 synthesis records

---

*End of round 1. USER decides on round-2 dispatch; NO auto-merge.*
