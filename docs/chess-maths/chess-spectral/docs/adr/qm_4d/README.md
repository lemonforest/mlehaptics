# qm_4d Track B — Architecture Decision Records

Design records for the chess-spectral v1.5.0 QM extension Track B (full
move-as-unitary dynamics). Track A (kinematic-only `qm_4d`) shipped in
[python/chess_spectral/qm_4d.py](../../../python/chess_spectral/qm_4d.py)
on branch `chess-spectral/qm-4d-kinematic`. Track B implementation begins
after these ADRs are accepted.

| ADR | Title | Status (post-Phase-3.5) | Phase 4 milestone |
|---|---|---|---|
| [001](ADR-001-phase-convention-for-unitary-moves.md) | Phase convention for unitary moves | ✅ **Accepted** (Phase 3.5 PASS) | B[1] |
| [002](ADR-002-time-evolution-semantics.md) | Time-evolution semantics | ✅ **Accepted** (Zeno; Stinespring deferred to v1.7+) | B[2] |
| [003](ADR-003-per-channel-move-transformation.md) | Per-channel move-transformation derivation | ⚠️ **Accepted with two amendments** — (1) Phase 3.5: FIB channels fall back to measurement-only re-encode (§3.3); (2) [Phase 4 B1](ADR-003-AMENDMENT-orbit-restriction.md): strict-unitary tier restricted to same-orbit non-capture moves (cross-orbit → measurement-only) | B[3] |
| [004](ADR-004-z2-superselection-structure.md) | Z_2 superselection structure | ⚠️ **Accepted with amendment** — §3.4 weakened to sector-flip-via-state_to_psi | B[4] |
| [005](ADR-005-pawn-pseudo-hermitian-eta-metric.md) | Pawn pseudo-Hermitian η-metric | ⚠️ **Accepted with amendment** — decompose M_pawn = M_single + M_double (η-metric on single only) | B[5] |

**Phase 3.5 empirical validation:** [`PHASE_3_5_PROBE_RESULTS.md`](PHASE_3_5_PROBE_RESULTS.md) is the authoritative validation record. Three of five ADRs got amendments based on probe results; their original bodies are preserved as the design record at the time of decision, but Phase 4 implementation reads ADR + probe-results doc together, with the probe-results doc winning on design-level decisions.

**Phase 4 B1 amendment (ADR-003):** [`ADR-003-AMENDMENT-orbit-restriction.md`](ADR-003-AMENDMENT-orbit-restriction.md) is the second amendment to ADR-003, surfaced by PR #76's projector-sandwich implementation. The strict-unitary tier (A_1, predicted STD4_*) is restricted to same-orbit non-capture moves on `Z_8^4`'s 35 B_4 orbits; cross-orbit moves route through the measurement-only re-encode path established by the Phase 3.5 FIB amendment. v1.7+ orbit-quotient refactor (Option (b)) deferred.

**Notebook context:** [chess_spectral_research_notebook.md §15-§17](../../../../chess_spectral_research_notebook.md#15-cross-disciplinary-applications-what-travels-beyond-chess), [chess_spectral_4d_notebook.md qm_4d Pre-flight Findings](../../../../chess_spectral_4d_notebook.md#qm_4d-pre-flight-findings-phase-1-2026-04-29).
