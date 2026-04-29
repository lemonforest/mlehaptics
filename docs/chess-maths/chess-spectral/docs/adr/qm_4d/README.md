# qm_4d Track B — Architecture Decision Records

Design records for the chess-spectral v1.5.0 QM extension Track B (full
move-as-unitary dynamics). Track A (kinematic-only `qm_4d`) shipped in
[python/chess_spectral/qm_4d.py](../../../python/chess_spectral/qm_4d.py)
on branch `chess-spectral/qm-4d-kinematic`. Track B implementation begins
after these ADRs are accepted.

| ADR | Title | Status | Phase 4 milestone |
|---|---|---|---|
| [001](ADR-001-phase-convention-for-unitary-moves.md) | Phase convention for unitary moves | Proposed | B[1] |
| [002](ADR-002-time-evolution-semantics.md) | Time-evolution semantics | Proposed (Zeno; Stinespring deferred to v1.7+) | B[2] |
| [003](ADR-003-per-channel-move-transformation.md) | Per-channel move-transformation derivation | Proposed (mixed scope) | B[3] |
| [004](ADR-004-z2-superselection-structure.md) | Z_2 superselection structure | Proposed | B[4] |
| [005](ADR-005-pawn-pseudo-hermitian-eta-metric.md) | Pawn pseudo-Hermitian η-metric | Proposed (best-effort v1.5; full v1.6+) | B[5] |

**Notebook context:** [chess_spectral_research_notebook.md §15-§17](../../../../chess_spectral_research_notebook.md#15-cross-disciplinary-applications-what-travels-beyond-chess), [chess_spectral_4d_notebook.md qm_4d Pre-flight Findings](../../../../chess_spectral_4d_notebook.md#qm_4d-pre-flight-findings-phase-1-2026-04-29).
