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

# Scientific tier: numpy is optional as of v0.7.0 (the cascade core is numpy-
# free). As of rc71 the eager package-level ``_require_numpy`` gate is GONE and
# op-registration is lazy; since #564 completed there are no numpy ops left at
# all, so the ``closed_form_ops`` / ``path_b_ops`` ``__getattr__`` are plain
# lazy imports with no ``[scientific]`` hint to raise. So
# ``import srmech.signal_processing`` succeeds with numpy ABSENT — the infra
# surface (dispatcher / registry / profiling / Path-B core) and every op
# family are reachable numpy-free.

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
    cell_grid,
    clear_records,
    iter_records,
    record_profile,
)

# Phase 3 (v0.4.2rc3) — Path B core: RBS-HDC instrument + form-function
# rotation. Imports trigger module-load registration with
# :mod:`srmech.signal_processing.path_registry` so the dispatcher can
# route to Path B ops via :func:`dispatch`.
from . import rbs_hdc_instrument as _rbs_hdc_instrument  # noqa: F401
from . import form_function_rotation as _form_function_rotation  # noqa: F401

# Phase 4 (v0.4.2rc4) — Path B per-op MVP: 6 ops (fft, ifft, sign_quantise,
# matched_filter, wiener, hdc_truncation). Each module registers BOTH its
# Path A counterpart (from Phase 2 closed_form_ops) and its Path B
# implementation with :mod:`srmech.signal_processing.path_registry` at
# module-load time. Phase 2's broader 38-op Path A registration script
# remains deferred per the implementation plan.
from . import path_b_ops as _path_b_ops  # noqa: F401

# rc424 (`#T1113`) — music_doa is Path-A-ONLY (no Path B dual until Phase 6),
# so no path_b_ops sidecar imports it and closed_form_ops is PEP-562 lazy;
# without this line its module-load `_register()` would never fire and the op
# would stay undispatchable. Imported EAGERLY rather than through a lazy
# loader on purpose: `test_path_registry_registered_ops_iteration` pins that
# the only PENDING lazy ops are the three numpy-shaped ones, and a fourth
# lazy loader would trip it. The module is numpy-free and pulls only carriers
# already loaded, so the eager cost is nil.
from .closed_form_ops import music_doa as _cf_music_doa  # noqa: F401

#: MUSIC (MUltiple SIgnal Classification) direction-of-arrival estimation.
#: Bound at PACKAGE level, not left inside ``closed_form_ops``, because rc424
#: registers it as ``srmech.signal_processing.music_doa`` and a ToolEntry name
#: must resolve to a live object. The module keeps its ``op`` spelling for
#: symmetry with its 40 Path-A siblings; this is the advertised public path.
music_doa = _cf_music_doa.op

# ──────────────────────────────────────────────────────────────────────
# rc425 (`#T1112`) — the other 37 Path-A ops reach the package surface.
#
# WHY A LAZY __getattr__ AND NOT 37 MORE EAGER IMPORTS. rc424 bound
# ``music_doa`` eagerly for a reason that does NOT generalise: that module
# (with ``pi_cascade``) is one of only two under ``closed_form_ops`` carrying a
# module-load ``_register()`` against ``path_registry``, so an import is what
# makes it dispatchable. Measured at rc425: the other 37 modules register
# nothing at import time, so eager-importing them would buy no dispatch and
# would spend the very cost ``closed_form_ops``'s own PEP-562 loader exists to
# avoid. They resolve through this ``__getattr__`` instead — which is enough,
# because a ToolEntry name only has to resolve to a live object when something
# asks for it, and ``srmech._resolve.resolve_dotted_callable`` walks attributes
# with ``getattr``.
#
# The name bound is the module's ``op`` callable, NOT the module: a ToolEntry
# name must resolve to the thing that gets CALLED. The modules keep their ``op``
# spelling internally for symmetry across all 41 siblings; these are the
# advertised public paths, and they are what the registry registers.
# ──────────────────────────────────────────────────────────────────────
_CLOSED_FORM_PUBLIC = (
    "allpass", "arithmetic_coding", "beamforming_fixed", "cross_spectral",
    "dct", "esprit", "farrow", "fir", "fsk", "hdc_truncation", "heat_kernel",
    "huffman", "ica_jade", "iir", "jpeg", "lmmse", "lz77", "map_ml",
    "matched_filter", "mimo_svd", "mlse", "multirate", "multitaper", "ofdm",
    "polyphase", "psk_qam", "rfft", "rle", "sign_quantise", "sinc_interp",
    "spectral_subtraction", "spectrogram", "stft", "vector_quantisation",
    "viterbi", "wavelet", "wiener",
)


def __getattr__(name):
    """Resolve a Path-A op name to its ``op`` callable, importing on demand.

    ``fft`` / ``ifft`` / ``pi_cascade`` are deliberately ABSENT from
    ``_CLOSED_FORM_PUBLIC``: each is value-identical (measured bit-exact at
    rc425 over integer, float, complex, power-of-two and non-power-of-two
    inputs) to an op the registry already ships — ``srmech.cascade.
    spectral_cascades.fft`` / ``.ifft`` and ``srmech.math.rational.
    pi_cascade_digits`` — so binding them here would advertise a second public
    path to the same values. They stay reachable at
    ``srmech.signal_processing.closed_form_ops.<name>``.
    """
    if name in _CLOSED_FORM_PUBLIC:
        import importlib
        mod = importlib.import_module(
            f".closed_form_ops.{name}", __name__)
        fn = mod.op
        globals()[name] = fn
        return fn
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_CLOSED_FORM_PUBLIC))


from .rbs_hdc_instrument import (
    CANONICAL_CASCADES,
    CLASS_DEFINITIONS,
    CLASS_NAMES,
    Cascade,
    ClassOperator,
    K3Tripartition,
    MEMORY_PATHWAYS,
    MemorySlot,
    PERMUTE_ORDER_STRIDE,
    RBSHDCInstrument,
    SAMPLE_STANCES,
    Stance,
    decode_loe_fingerprint,
    encode_loe_content,
    mint_cascade_composition,
    mint_class_operator,
    mint_stance_fingerprint,
    mint_vector,
)
from .form_function_rotation import (
    cascade_compose_rotations,
    compute_content_stride,
    form_function_rotate,
    inverse_form_function_rotate,
    verify_rotation_class_n_cycle_order,
)

# Phase 1 scaffolding: closed-form operations themselves are
# NotImplementedError at the public surface until Phase 2 (Path A)
# populates them. The dispatch / registry / profiling APIs above are
# stable from Phase 1. Phase 3 ships the Path B core surface
# (rbs_hdc_instrument + form_function_rotation) directly importable
# from the package root.

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
    # Closed-form ops promoted to the package surface (rc424, `#T1113`)
    "music_doa",
    # The other 37 Path-A ops (rc425, `#T1112`) — lazy via __getattr__.
    # fft / ifft / pi_cascade are deliberately absent: each is value-identical
    # to an op the registry already ships under another name.
    "allpass",
    "arithmetic_coding",
    "beamforming_fixed",
    "cross_spectral",
    "dct",
    "esprit",
    "farrow",
    "fir",
    "fsk",
    "hdc_truncation",
    "heat_kernel",
    "huffman",
    "ica_jade",
    "iir",
    "jpeg",
    "lmmse",
    "lz77",
    "map_ml",
    "matched_filter",
    "mimo_svd",
    "mlse",
    "multirate",
    "multitaper",
    "ofdm",
    "polyphase",
    "psk_qam",
    "rfft",
    "rle",
    "sign_quantise",
    "sinc_interp",
    "spectral_subtraction",
    "spectrogram",
    "stft",
    "vector_quantisation",
    "viterbi",
    "wavelet",
    "wiener",
    # Profiling API
    "record_profile",
    "iter_records",
    "clear_records",
    "cell_grid",
    "ProfileRecord",
    "ProfileCellKey",
    "DEFAULT_INPUT_SIZES",
    "DEFAULT_CASCADE_DEPTHS",
    # Phase 3 — Path B core: RBS-HDC instrument
    "RBSHDCInstrument",
    "ClassOperator",
    "Cascade",
    "Stance",
    "MemorySlot",
    "K3Tripartition",
    "CLASS_NAMES",
    "CLASS_DEFINITIONS",
    "CANONICAL_CASCADES",
    "SAMPLE_STANCES",
    "MEMORY_PATHWAYS",
    "PERMUTE_ORDER_STRIDE",
    "mint_class_operator",
    "mint_cascade_composition",
    "mint_stance_fingerprint",
    "mint_vector",
    "encode_loe_content",
    "decode_loe_fingerprint",
    # Phase 3 — Path B core: form-function rotation
    "form_function_rotate",
    "inverse_form_function_rotate",
    "verify_rotation_class_n_cycle_order",
    "cascade_compose_rotations",
    "compute_content_stride",
]
