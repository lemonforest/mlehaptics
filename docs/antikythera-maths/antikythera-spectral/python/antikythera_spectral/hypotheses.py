"""Hypothesis-battery facade — direct re-exports for phase 2.

The full ``run_hypothesis_battery`` and ``get_hypothesis`` bridge
methods land in phase 12 of the v0.1.0 release. For now this module
re-exports every per-hypothesis evaluator function from
``_research.consolidated_tests`` so callers can drive individual
hypotheses today.

Each ``hypothesis_*()`` function returns a ``(row_dict, detail_dict)``
tuple per the H-battery contract:

- ``row_dict`` — the CSV row: ``{id, statement, computed_value,
  threshold, status, notes}``.
- ``detail_dict`` — per-hypothesis JSON detail blob (varies in shape).

The 31 hypotheses correspond to the 31 rows in
``../../research/results/phase1_hypotheses.csv``.
"""

from __future__ import annotations

from antikythera_spectral._research import consolidated_tests as _ctests

# A-series (addressing-maths Pareto + prime spectrum)
hypothesis_A_H1a = _ctests.hypothesis_A_H1a
hypothesis_A_H1b = _ctests.hypothesis_A_H1b
hypothesis_A_H2 = _ctests.hypothesis_A_H2
hypothesis_A_H3 = _ctests.hypothesis_A_H3
hypothesis_A_H4 = _ctests.hypothesis_A_H4

# B-series (encoder algebra)
hypothesis_B_H1 = _ctests.hypothesis_B_H1
hypothesis_B_H2 = _ctests.hypothesis_B_H2
hypothesis_B_H3 = _ctests.hypothesis_B_H3

# C-series (channel-basis bijection / aliasing)
hypothesis_C_H1 = _ctests.hypothesis_C_H1
hypothesis_C_H2 = _ctests.hypothesis_C_H2

# D-series (pin-and-slot / T-symmetry / equant anharmonicity)
hypothesis_D_H1 = _ctests.hypothesis_D_H1
hypothesis_D_H2 = _ctests.hypothesis_D_H2
hypothesis_D_H3 = _ctests.hypothesis_D_H3

# E-series (ephemeris ground-truth)
hypothesis_E_H1a = _ctests.hypothesis_E_H1a
hypothesis_E_H1b = _ctests.hypothesis_E_H1b
hypothesis_E_H1c = _ctests.hypothesis_E_H1c
hypothesis_E_H2 = _ctests.hypothesis_E_H2
hypothesis_E_H3 = _ctests.hypothesis_E_H3
hypothesis_E_H4 = _ctests.hypothesis_E_H4

# F-series (open exploration; emit UNDETERMINED with prose)
hypothesis_F_E1 = _ctests.hypothesis_F_E1
hypothesis_F_E2 = _ctests.hypothesis_F_E2
hypothesis_F_E3 = _ctests.hypothesis_F_E3

# G-series (manufacturing tolerance + architectural-mode evaluators)
hypothesis_G_H1a = _ctests.hypothesis_G_H1a
hypothesis_G_H1b = _ctests.hypothesis_G_H1b
hypothesis_G_H2 = _ctests.hypothesis_G_H2
hypothesis_G_H3 = _ctests.hypothesis_G_H3
hypothesis_G_H6 = _ctests.hypothesis_G_H6
hypothesis_G_H7 = _ctests.hypothesis_G_H7
hypothesis_G_H8 = _ctests.hypothesis_G_H8

# H-series (historical cross-references)
hypothesis_H_H1 = _ctests.hypothesis_H_H1
hypothesis_H_H2 = _ctests.hypothesis_H_H2

ALL_HYPOTHESIS_IDS: tuple[str, ...] = (
    "A-H1a", "A-H1b", "A-H2", "A-H3", "A-H4",
    "B-H1", "B-H2", "B-H3",
    "C-H1", "C-H2",
    "D-H1", "D-H2", "D-H3",
    "E-H1a", "E-H1b", "E-H1c", "E-H2", "E-H3", "E-H4",
    "F-E1", "F-E2", "F-E3",
    "G-H1a", "G-H1b", "G-H2", "G-H3", "G-H6", "G-H7", "G-H8",
    "H-H1", "H-H2",
)
"""Frozen tuple of every hypothesis ID in the v0.1.0 battery (31 rows)."""

__all__ = [
    "ALL_HYPOTHESIS_IDS",
    "hypothesis_A_H1a", "hypothesis_A_H1b", "hypothesis_A_H2",
    "hypothesis_A_H3", "hypothesis_A_H4",
    "hypothesis_B_H1", "hypothesis_B_H2", "hypothesis_B_H3",
    "hypothesis_C_H1", "hypothesis_C_H2",
    "hypothesis_D_H1", "hypothesis_D_H2", "hypothesis_D_H3",
    "hypothesis_E_H1a", "hypothesis_E_H1b", "hypothesis_E_H1c",
    "hypothesis_E_H2", "hypothesis_E_H3", "hypothesis_E_H4",
    "hypothesis_F_E1", "hypothesis_F_E2", "hypothesis_F_E3",
    "hypothesis_G_H1a", "hypothesis_G_H1b", "hypothesis_G_H2",
    "hypothesis_G_H3", "hypothesis_G_H6", "hypothesis_G_H7",
    "hypothesis_G_H8",
    "hypothesis_H_H1", "hypothesis_H_H2",
]
