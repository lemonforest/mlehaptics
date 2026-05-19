"""Path B per-op MVP — RBS-HDC-native signal-processing operations.

Phase 4 of the RBS-HDC-LoE dual-path architecture per the implementation
plan ``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md``.

Each module in this package re-surfaces one signal-processing operation as
a **Path B native** composition over the Phase 3 Path B core surface
(:mod:`srmech.signal_processing.rbs_hdc_instrument` +
:mod:`srmech.signal_processing.form_function_rotation`). The 6 ops in the
Phase 4 MVP correspond to the Spike #178 R4 priority shortlist with IFFT
separated from FFT for dual round-trip testing:

1. :mod:`srmech.signal_processing.path_b_ops.fft` — Class A ∘ Class I ∘
   Class K cyclic-substrate FFT (Spike #176 H1 anchor).
2. :mod:`srmech.signal_processing.path_b_ops.ifft` — Inverse of (1);
   Spike #176 T4 round-trip anchor.
3. :mod:`srmech.signal_processing.path_b_ops.sign_quantise` — Class K
   threshold / pin-slot projection (Spike #174 SHA-256 BER preservation
   anchor).
4. :mod:`srmech.signal_processing.path_b_ops.matched_filter` — Class A ∘
   Class C ∘ Class M form-function cross-correlation (Spike #159 +
   Spike #173 + Spike #176).
5. :mod:`srmech.signal_processing.path_b_ops.wiener` — Class L Laplacian-
   eigenbasis ∘ Class N rational gain (Kay 1993 §11 SSoT-cited).
6. :mod:`srmech.signal_processing.path_b_ops.hdc_truncation` — Class K
   asymptotic-DOF sparse-truncate ∘ Class M bundle (Spike #117 anchor).

Each module exports:

- Module-level constants: ``OPERATION_NAME``, ``CLASS_COMPOSITION``,
  ``PERFORMANCE_HINT``, ``SSOT_CITATION``.
- A single callable ``op(*args, **kwargs)`` that runs the Path B-native
  composition.
- A module-load registration hook that registers the op as Path B with
  :mod:`srmech.signal_processing.path_registry`.

Discipline anchors (load-bearing):

- 14 A-N intact per ``[[feedback_no_privileged_primitive_classes]]`` —
  every Path B op is a *composition* over existing classes; no new
  primitive class promotion.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]`` — Path A
  and Path B both *instantiate* the same algebra. D1 algebra-identity
  is preserved bit-exact at substrate-natural inputs; D2 substrate-
  fingerprint divergence is expected per
  ``[[user_stance_substrate_natural_encoding_is_shadow_projection]]``.
- Algebra-level not magnitude-level per
  ``[[feedback_algebra_not_magnitude]]``.
- Trauma-informed defensive scope per
  ``[[feedback_trauma_informed_defensive_scope]]`` — methodology
  research only.

Canonical SSoT
--------------
- Cooley & Tukey (1965) DOI 10.1090/S0025-5718-1965-0178586-1 (FFT).
- North (1943) + Turin (1960) IRE TIT 6, 311 (matched filter).
- Kay (1993) §11 (Wiener filter).
- Donoho & Johnstone (1994) DOI 10.1093/biomet/81.3.425 (sign-quantise).
- Plate (1995) IEEE TNN 6, 623 (HRR / HDC).
- Kanerva (2009) Cogn. Comp. 1, 139 (HDC).
- Spike #117 — HDC sparse-truncate.
- Spike #159 — matched-filter 31.6× separation.
- Spike #174 — sign-quantise SHA-256 BER preservation.
- Spike #176 — rotation IS Class K (machine ε).
- Spike #178 — closed-form SP roadmap (5-op MVP).
- Spike #179 — CFSP-Kalman alternative.
"""

from __future__ import annotations

from . import (
    fft,
    hdc_truncation,
    ifft,
    matched_filter,
    pi_cascade,
    sign_quantise,
    wiener,
)

#: Canonical roster of Phase 4 Path B MVP op modules (alphabetical).
#: Used by ``tests/test_signal_processing_path_b_mvp.py`` to assert
#: all 6 ops are registered. Spike #184 (2026-05-19) added
#: ``pi_cascade`` as the 7th Path B op for dual-path algebra-benchmark
#: re-run; not part of the Phase 4 MVP roster.
PATH_B_MVP_OPS = (
    "fft",
    "hdc_truncation",
    "ifft",
    "matched_filter",
    "sign_quantise",
    "wiener",
)

__all__ = [
    "PATH_B_MVP_OPS",
    "fft",
    "hdc_truncation",
    "ifft",
    "matched_filter",
    "pi_cascade",
    "sign_quantise",
    "wiener",
]
