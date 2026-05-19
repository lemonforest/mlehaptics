"""Internal path constants for ``srmech.signal_processing``.

Phase 1 scaffolding (v0.4.2rc1) — defines locked architectural defaults +
filesystem anchors that downstream modules (dispatcher / profiling /
registry) read at module-load time. Centralised here so Phase 2-8 file
authors can reference one SSoT instead of duplicating constants.

Locks per the 8 accepted conductor decisions (2026-05-19):

- ``D_DEFAULT = 8192`` (decision #6 — D=8192 lock for v0.4.2 baseline,
  matches Spike #170/#172/#173/#176/#177 anchors). Phase 1+ APIs accept
  optional ``D`` parameter for downstream experiments.
- ``SUBSTRATES`` tuple includes all 4 substrates (decision #2 —
  cross-substrate coverage Phase 7).
- ``DISPATCH_TABLE_LOCK_POLICY = "lock-at-release"`` (decision #7 —
  reproducibility).
- Profiling supports per-op × per-cascade-depth × per-substrate (decision
  #3 — 1920-cell granularity).

Discipline anchors:

- 14 A-N intact per ``[[feedback_no_privileged_primitive_classes]]``.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]``.
- Algebra-level not magnitude-level per ``[[feedback_algebra_not_magnitude]]``.
- Trauma-informed defensive scope per
  ``[[feedback_trauma_informed_defensive_scope]]`` — signal-processing
  methodology research/educational only; no clinical/military framing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, Tuple

# ──────────────────────────────────────────────────────────────────────
# RBS-HDC instrument dimension lock
# ──────────────────────────────────────────────────────────────────────

D_DEFAULT: Final[int] = 8192
"""Default RBS-HDC bound-vector bit-dimension.

Locked at 8192 for v0.4.2 baseline per conductor decision #6 (2026-05-19).
Matches Spike #170 §3 prototype invariants (14/14 mint determinism),
Spike #172 (DNA helical-pitch), Spike #173 (chess natural-stride D2
orthogonality), Spike #176 (rotation IS Class K at machine ε), Spike
#177 (pin-slot-resonate music-box). Downstream experiments may pass
optional ``D`` parameter to operations; the locked default ensures
cross-spike anchor compatibility within v0.4.2.
"""

D_MIN: Final[int] = 256
"""Minimum supported bound-vector dimension. Below this, Class M HDC
algebra loses statistical near-orthogonality (Plate 1995 / Kanerva 2009)."""

D_MAX: Final[int] = 65536
"""Maximum supported bound-vector dimension. Practical upper bound for
in-memory Python composition; native-C surface may extend in v0.4.3+."""


# ──────────────────────────────────────────────────────────────────────
# Substrate enumeration (Phase 7 cross-substrate coverage)
# ──────────────────────────────────────────────────────────────────────

SUBSTRATES: Final[Tuple[str, ...]] = ("bci", "audio", "rf", "ephemeris")
"""Four substrates supported per conductor decision #2 (2026-05-19).

Each substrate's Class N rational catalog ships in Phase 7 under
``substrate_rationals/<substrate>.py``. Phase 1 reserves the names;
no catalog content is shipped at scaffolding stage.

- ``bci`` — Brain-Computer Interface (192/96/24 electrode counts,
  30000/24000/1000 Hz sampling — methodology-research only; per
  trauma-informed defensive scope no clinical/military framing).
- ``audio`` — 44100/48000=147/160; Z₁₂ chromatic intervals (RBJ EQ
  Cookbook canonical SSoT).
- ``rf`` — 802.11 subcarrier counts; LTE/5G subcarrier spacing
  (civilian-comms framing only per defensive scope).
- ``ephemeris`` — 52-body resonance ratios; cite-by-ref ephemerides-
  spectral package's existing catalog (no re-derivation in srmech).
"""


# ──────────────────────────────────────────────────────────────────────
# Dispatch path discriminator
# ──────────────────────────────────────────────────────────────────────

PATH_A: Final[str] = "A"
"""Closed-form algebra path identifier. Routes operations through the
existing ``srmech.amsc.*`` primitive surfaces (composition layer)."""

PATH_B: Final[str] = "B"
"""RBS-HDC bound-vector instrument path identifier. Routes operations
through the D=8192 bound-vector composition (Phase 3+ surface)."""

PATH_VERIFY: Final[str] = "verify"
"""Verification path identifier. Runs both Path A and Path B and asserts
D1 algebra-content equivalence via ``_algebra_check.assert_algebra_equivalent``.

Per ``[[feedback_algebra_not_magnitude]]``: D1 algebra-content identity
is required (structural content bit-exact); D2 substrate-fingerprint
divergence is expected (Path A may return float64 numpy, Path B may
return D=8192 bound vector — these are different *projections* of the
same algebra content)."""

VALID_PATHS: Final[Tuple[str, ...]] = (PATH_A, PATH_B, PATH_VERIFY)
"""Accepted values for the ``path=`` kwarg on signal-processing operations."""


# ──────────────────────────────────────────────────────────────────────
# Dispatch table lock policy (conductor decision #7)
# ──────────────────────────────────────────────────────────────────────

DISPATCH_TABLE_LOCK_POLICY: Final[str] = "lock-at-release"
"""Lock policy for the learned dispatch table.

Per conductor decision #7 (2026-05-19): the Phase 8 learned dispatch
table is locked at each release tag (v0.4.2rc{N} and v0.4.2 ship a
specific ``_learned_dispatch_table.ndjson``). Users wanting different
thresholds set the override flag or rerun ``update_dispatch_table()``
on their own machine (local override; doesn't pollute package's locked
table). Choice prioritises reproducibility over per-environment tuning.
"""


# ──────────────────────────────────────────────────────────────────────
# Filesystem anchors (relative to this package)
# ──────────────────────────────────────────────────────────────────────

_PKG_DIR: Final[Path] = Path(__file__).resolve().parent
"""``srmech/signal_processing/`` package directory (resolved absolute)."""

LEARNED_DISPATCH_TABLE_PATH: Final[Path] = (
    _PKG_DIR / "_learned_dispatch_table.ndjson"
)
"""Path to the locked learned dispatch table (NDJSON; per
``[[feedback_ndjson_over_bloated_json]]``). Phase 1 ships an empty
file at this path; Phase 8 populates with regression-fit thresholds."""


# ──────────────────────────────────────────────────────────────────────
# Profiling granularity (conductor decision #3)
# ──────────────────────────────────────────────────────────────────────

# Per conductor decision #3: full per-op × per-cascade-depth × per-substrate
# profiling granularity. Phase 8 benchmark suite cell count =
#   N_OPS × N_INPUT_SIZES × N_CASCADE_DEPTHS × N_SUBSTRATES × N_PATHS
# = 10 × 6 × 4 × 4 × 2 = 1920 records.

PROFILING_INPUT_SIZES_DEFAULT: Final[Tuple[int, ...]] = (
    256, 1024, 4096, 16384, 65536, 262144,
)
"""Default input sizes covered by the Phase 8 benchmark suite (6 sizes;
six orders of magnitude). Per plan §5.1."""

PROFILING_CASCADE_DEPTHS_DEFAULT: Final[Tuple[int, ...]] = (1, 3, 5, 10)
"""Default cascade depths covered by the Phase 8 benchmark suite (4
depths; single-op vs short cascade vs deep cascade). Per plan §5.1."""

CASCADE_DEPTH_THRESHOLD_FOR_PATH_B: Final[int] = 3
"""Cascade depth at which Path B becomes preferred (encode overhead
amortises). Per plan §3.1 criterion #2: cascades of ≥3 ops at the
same substrate prefer Path B. Initial seed threshold; Phase 8 learning
may revise per (op, cascade-depth, substrate) cell."""


__all__ = [
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
]
