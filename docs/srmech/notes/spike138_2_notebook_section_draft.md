### §3.8.X (TBD) Alternate-substrate roster validation of {B,D,E,F,L} closure subgroup (Spike #138.2, 2026-05-18)

**Status:** Spike findings for conductor review; placement number reserved by conductor (between §3.8.30 wave-2 close and current end). Companion section to §3.8.X-138-base and §3.8.X-138.1 (depth-4/5).

Spike #138.2 multi-DOMAIN validation companion to Spike #138.1 (depth-4/5 closure on SAME substrates). Question: does Spike #138's depth-2 closure-subgroup pattern hold on a substrate roster DIFFERENT from chess / image / ephemeris / quantum / physarum? Result: **YES, exactly**.

**Alternate substrate roster (5 NEW from project canon):**

| Substrate | n | period | Project origin | Geometric distinctness |
|-----------|--:|-------:|----------------|------------------------|
| sparse_coding | 64 | 8 | Spike #117 substrate-A | power-law-coupled all-pairs |
| geomagnetic | 60 | 2 | Spike #131 core-mantle | spherical-shell with Coriolis E-W weighting |
| genetic_code | 64 | 3 | Spike #81 codon graph | Hamming-1 on (alphabet=4)×(positions=3) |
| cmb_acoustic | 64 | 6 | Spike #103 l_n peaks | cyclic-chain Class I Cauchy-form |
| bipartite | 64 | 2 | Spike #135 BBB-substitute | K_{32,32} − perfect matching |

Spike #135's BBB substrate asset is not in tree; we substitute the structurally cleanest bipartite Class L candidate (bipartite K_{32,32}−matching; documented in NDJSON framing record).

**Three structural findings replicate exactly:**

1. **{B, D, E, F, L} closure-subgroup: 25/25 universal identity-attractors** across 5 substrates × 5 inspection orderings. Identical to Spike #138's 25/25.
2. **Self-inverse {H·H, K·K, M·M}: 3/3 universal identity-attractors**. Identical to Spike #138.
3. **Inspection-ordering invariance: 0/980 cascades order-dependent**. Identical to Spike #138's 0/1196.

**Total universal identities: 28** — EXACT match to Spike #138's 28. Form-attractor fingerprint distribution `{25: 196}` (every depth-2 cascade produces 25 distinct fixed-points) — EXACT match to Spike #138's `{25: 1196}` pattern.

**One NEW finding surfaced** (substrate-conditional, not closure-falsifier):

**{J, ·} cascade family (11 cascades involving Class J prime-factorisation) is identity-attractor on substrates with prime periods.** Spike #138's roster had only one prime-period substrate (physarum=7), so {J,·} hit at most 5/25 — below the 50% partial threshold. Spike #138.2's roster has three prime-period substrates (geomagnetic=2, genetic_code=3, bipartite=2), raising {J,·} hits to 15/25 and surfacing the pattern. Mechanism: Class J operator is no-op on HDC/spectrum/period when period is already prime (only bumps `tag`, which is not in the identity criterion). **Substrate-conditional identity**; does NOT promote a new class; integrates as a Class J discriminator field per `[[feedback_multi_domain_multi_round_survival_falsification_method]]`'s demotion-with-additional-fields pattern.

**Multi-domain × multi-round status:**
- Spike #138 (parent): depth-2/3 closure on 5 substrates (chess/image/ephemeris/quantum/physarum)
- Spike #138.1 (parallel dispatch, same wave): depth-4/5 closure on SAME 5 substrates
- Spike #138.2 (this section): depth-2/3 closure on 5 NEW substrates (sparse_coding/geomagnetic/genetic_code/cmb_acoustic/bipartite)

Combined 10-substrate × 2-5-depth verification matrix. Per `[[feedback_multi_domain_multi_round_survival_falsification_method]]`: multi-domain × multi-round survival is the canonical-promotion gate. **The closure-subgroup pattern is now substrate-class-universal at the 10 substrates collectively tested.**

**Per `[[feedback_no_privileged_primitive_classes]]`**: vocabulary stays at 14 classes A–N. Zero new primitive class proposed.

**Cross-references**: `[[feedback_multi_domain_multi_round_survival_falsification_method]]`; `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`; `[[user_stance_substrate_identity_partition_coexistence_canonical]]` (substrate-coexistence at primitive level); `[[feedback_no_privileged_primitive_classes]]`; §3.8.X-138-base (parent); §3.8.X-138.1 (depth-4/5 companion); Spike #117 / #131 / #81 / #103 substrate origins.

**Outputs**:
- `docs/srmech/notes/spike138_2_alternate_substrates.py` — explorer (imports spike138_explorer machinery)
- `docs/srmech/notes/spike138_2_findings_2026-05-18.ndjson` — full d2+d3 NDJSON (29,906 rows)
- `docs/srmech/notes/spike138_2_alternate_substrate_findings.md` — findings narrative
