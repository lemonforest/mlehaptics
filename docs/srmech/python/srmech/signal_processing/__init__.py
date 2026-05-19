"""srmech.signal_processing — RBS-HDC-LoE dual-path signal-processing surface.

Phase 1 scaffolding (v0.4.2rc1) — package entry point + public API
skeleton for the dual-path architecture. Phase 2-10 (v0.4.2rc2-v0.4.2)
populate per-op modules; this ``__init__.py`` is the stable surface
from Phase 1 onward.

The package implements the **RBS-HDC-LoE dual-path architecture** per
``[[project_rbs_hdc_loe_dual_path_architecture]]``:

- **Path A** — closed-form algebra (composes the existing
  ``srmech.amsc.*`` 14-class A-N primitive vocabulary). SSoT for
  primitive definitions.
- **Path B** — RBS-HDC bound-vector instrument at D=8192 (per Spike
  #170 / #172 / #173 / #176 / #177 anchors). Composes from Path A
  primitive definitions at module-load time; no duplicate primitive
  implementations.
- **Path C** — cascade-aware dispatcher (see
  :mod:`srmech.signal_processing.cascade_dispatcher`); chooses A or
  B per call based on rule-based (Phase 5) + empirical (Phase 8)
  routing. Neither path replaces the other.

The 8 accepted conductor decisions (2026-05-19) frame Phase 1:

1. **C port deferred** to v0.4.3rc1 (Phase 1 ships no C surface).
2. **Cross-substrate coverage** — stub-level support for all 4
   substrates (BCI / audio / RF / ephemeris) per
   :data:`srmech.signal_processing._paths.SUBSTRATES`.
3. **Profiling granularity** — full per-op × per-cascade-depth ×
   per-substrate (1920 cells) supported by
   :func:`srmech.signal_processing.profiling.cell_grid`.
4. **Spike #179 F4 caveat** — Kalman Q misspecification clarification
   integrates at Phase 9 §3.8.31 (no action in Phase 1).
5. **begin_cascade API** — context-manager (Pythonic; auto-flush on
   exception); see :func:`begin_cascade`.
6. **D=8192 lock** — locked default for v0.4.2 baseline;
   :data:`D_DEFAULT`; optional ``D`` param accepted by ops.
7. **Dispatch table lock policy** — lock-at-release for
   reproducibility; see
   :func:`srmech.signal_processing.cascade_dispatcher.is_dispatch_table_locked`.
8. **Notebook §3.8.31 timing** — Phase 9 (no notebook prose in Phase 1).

Discipline anchors (load-bearing):

- 14 A-N intact per ``[[feedback_no_privileged_primitive_classes]]`` —
  no new primitive class is introduced; every operation is class-
  composition over the existing 14-class vocabulary in ``srmech.amsc.*``.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]`` — Path A
  and Path B both *instantiate* the same class composition; the
  dispatcher routes between substrate-fingerprints (D2), not between
  identities (D1).
- Algebra-level not magnitude-level per
  ``[[feedback_algebra_not_magnitude]]`` — ``path="verify"`` asserts
  D1 algebra-content identity; D2 substrate-fingerprint divergence
  is expected.
- Trauma-informed defensive scope per
  ``[[feedback_trauma_informed_defensive_scope]]`` — signal-processing
  methodology research/educational only; no clinical / military
  framing. BCI / RF substrate labels are methodology-research only.
- SSoT discipline — Path B compositions reference Path A primitives
  at module-load time per ``[[feedback_no_binding_layer_carveout]]``.

Phase 1 public surface
----------------------

Operations (FFT, IFFT, STFT, DCT, matched-filter, etc.) land in Phase
2 (Path A) and Phase 4 (Path B). Phase 1 ships the infrastructure
modules:

- :mod:`srmech.signal_processing.cascade_dispatcher` — routing API +
  ``begin_cascade`` context-manager + ``path=`` semantics.
- :mod:`srmech.signal_processing.path_registry` — Path A vs Path B
  operation registry.
- :mod:`srmech.signal_processing.profiling` — profiling infrastructure
  (Phase 8 lands runner; Phase 1 ships data structures + hooks).
- :mod:`srmech.signal_processing._paths` — internal constants (D=8192
  lock; substrate enumeration; dispatch-table-lock-policy).

Canonical SSoT
--------------
- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Chung (1997) *Spectral Graph Theory*, AMS.
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.).
- Implementation plan: ``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md``.
- Spike #178 §1 (closed-form SP roadmap; ~40 ops surveyed).

Spike anchors
-------------
- Spike #170 — RBS-HDC instrument feasibility (14/14 mint determinism).
- Spike #172 — DNA helical-pitch substrate.
- Spike #173 — chess natural-stride (D2 orthogonality).
- Spike #175 — knowledge-is-gauge-content.
- Spike #176 — rotation IS Class K (machine ε).
- Spike #177 — pin-slot-resonate music-box mechanism.
- Spike #178 — closed-form SP roadmap.
- Spike #179 — CFSP-Kalman alternative (in flight; Phase 9 integration).
"""

from __future__ import annotations

# Re-export the locked architectural constants for ergonomic access.
from ._paths import (
    CASCADE_DEPTH_THRESHOLD_FOR_PATH_B,
    D_DEFAULT,
    D_MAX,
    D_MIN,
    DISPATCH_TABLE_LOCK_POLICY,
    LEARNED_DISPATCH_TABLE_PATH,
    PATH_A,
    PATH_B,
    PATH_VERIFY,
    PROFILING_CASCADE_DEPTHS_DEFAULT,
    PROFILING_INPUT_SIZES_DEFAULT,
    SUBSTRATES,
    VALID_PATHS,
)
from .cascade_dispatcher import (
    CascadeContext,
    DEFAULT_PATH_PER_CLASS,
    DispatchError,
    DispatcherNotImplementedError,
    begin_cascade,
    current_cascade,
    dispatch,
    end_cascade,
    is_dispatch_table_locked,
    lock_dispatch_table,
    resolve_path,
    unlock_dispatch_table,
)
from .path_registry import (
    DuplicateRegistrationError,
    OperationEntry,
    RegistryError,
    UnknownOperationError,
    clear_registry,
    has_path,
    lookup,
    register,
    registered_ops,
)
from .profiling import (
    DEFAULT_CASCADE_DEPTHS,
    DEFAULT_INPUT_SIZES,
    ProfileCellKey,
    ProfileRecord,
    ProfilingNotImplementedError,
    cell_grid,
    clear_records,
    iter_records,
    profile_op,
    record_profile,
    update_dispatch_table,
)

# Phase 1 scaffolding: operations themselves are NotImplementedError
# at the public surface until Phase 2 (Path A) populates them. The
# dispatch / registry / profiling APIs above are stable from Phase 1.

__all__ = [
    # Architectural constants (D-lock, substrates, paths, lock policy)
    "D_DEFAULT",
    "D_MIN",
    "D_MAX",
    "SUBSTRATES",
    "PATH_A",
    "PATH_B",
    "PATH_VERIFY",
    "VALID_PATHS",
    "DISPATCH_TABLE_LOCK_POLICY",
    "LEARNED_DISPATCH_TABLE_PATH",
    "PROFILING_INPUT_SIZES_DEFAULT",
    "PROFILING_CASCADE_DEPTHS_DEFAULT",
    "CASCADE_DEPTH_THRESHOLD_FOR_PATH_B",
    # Dispatcher API
    "begin_cascade",
    "end_cascade",
    "current_cascade",
    "dispatch",
    "resolve_path",
    "is_dispatch_table_locked",
    "lock_dispatch_table",
    "unlock_dispatch_table",
    "CascadeContext",
    "DispatchError",
    "DispatcherNotImplementedError",
    "DEFAULT_PATH_PER_CLASS",
    # Registry API
    "register",
    "lookup",
    "has_path",
    "registered_ops",
    "clear_registry",
    "OperationEntry",
    "RegistryError",
    "DuplicateRegistrationError",
    "UnknownOperationError",
    # Profiling API
    "record_profile",
    "iter_records",
    "clear_records",
    "cell_grid",
    "profile_op",
    "update_dispatch_table",
    "ProfileRecord",
    "ProfileCellKey",
    "ProfilingNotImplementedError",
    "DEFAULT_INPUT_SIZES",
    "DEFAULT_CASCADE_DEPTHS",
]
