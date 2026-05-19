"""``srmech.signal_processing`` — RBS-HDC-LoE dual-path signal-processing surface.

This package implements the dual-path signal-processing architecture per the
plan ``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md``.

Phase 2 of the plan ships the 38 Path A op modules under
:mod:`srmech.signal_processing.closed_form_ops`. Phase 1 (running in parallel
in a different worktree) ships the scaffolding (``cascade_dispatcher``,
``path_registry``, ``profiling``). Phase 4+ ship Path B + dispatcher binding.

This package-level ``__init__`` is intentionally minimal in Phase 2 — it does
NOT re-export the closed-form ops at the package surface (consumers reach into
``srmech.signal_processing.closed_form_ops.<op>`` explicitly), and it does NOT
import any Phase 1 modules that may not yet be present.

Post-merge integration (separate work; not Phase 2's job): the Phase 1
scaffolding will populate the dispatcher / registry; a small registration
script will iterate the 38 closed-form ops and register them via the module-
level constants ``OPERATION_NAME`` / ``CLASS_COMPOSITION`` /
``PERFORMANCE_HINT`` / ``SSOT_CITATION``.
"""

from __future__ import annotations

__all__: list[str] = []
