"""Profiling infrastructure for ``srmech.signal_processing``.

Data structures + hook API for empirical Path-A-vs-Path-B
benchmarking: the :class:`ProfileCellKey` / :class:`ProfileRecord`
shapes, the in-memory record buffer (:func:`record_profile` /
:func:`iter_records` / :func:`clear_records`), and the
:func:`cell_grid` benchmark-cell enumerator the dispatcher work
programs against.

Granularity per conductor decision #3 (2026-05-19): **full per-op ×
per-cascade-depth × per-substrate**. Benchmark suite cell count =
10 ops × 6 input sizes × 4 cascade depths × 4 substrates × 2 paths
= 1920 cells (plan §5.1). Each cell emits one NDJSON record per
``[[feedback_ndjson_over_bloated_json]]``.

Discipline anchors:

- 14 A-N intact — profiling does not introduce new primitive classes.
- Trauma-informed defensive scope per
  ``[[feedback_trauma_informed_defensive_scope]]`` — benchmark records
  carry no clinical / military framing; substrate labels are
  methodology-research only.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]`` — profiling
  observes substrate-fingerprint (D2) cost; the underlying algebra-
  content (D1) is path-invariant.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ._paths import (
    PATH_A,
    PATH_B,
    PROFILING_CASCADE_DEPTHS_DEFAULT,
    PROFILING_INPUT_SIZES_DEFAULT,
    SUBSTRATES,
)

__all__ = [
    "ProfileRecord",
    "ProfileCellKey",
    "record_profile",
    "iter_records",
    "clear_records",
    "cell_grid",
    "DEFAULT_INPUT_SIZES",
    "DEFAULT_CASCADE_DEPTHS",
]


# ──────────────────────────────────────────────────────────────────────
# Public defaults (re-exported from _paths for ergonomic access)
# ──────────────────────────────────────────────────────────────────────

DEFAULT_INPUT_SIZES: Tuple[int, ...] = PROFILING_INPUT_SIZES_DEFAULT
"""Public re-export of Phase 8 benchmark default input sizes (6 sizes)."""

DEFAULT_CASCADE_DEPTHS: Tuple[int, ...] = PROFILING_CASCADE_DEPTHS_DEFAULT
"""Public re-export of Phase 8 benchmark default cascade depths (4 depths)."""


# ──────────────────────────────────────────────────────────────────────
# Record shape — emitted as one NDJSON line per benchmark cell
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProfileCellKey:
    """Cartesian key identifying one benchmark cell.

    Per conductor decision #3 (2026-05-19): full per-op × per-cascade-
    depth × per-substrate granularity. The (op_name, path, input_size,
    cascade_depth, substrate) tuple is the canonical lookup key for the
    learned dispatch table.
    """

    op_name: str
    path: str  # "A" or "B"
    input_size: int
    cascade_depth: int
    substrate: str  # one of SUBSTRATES


@dataclass(frozen=True)
class ProfileRecord:
    """One profiling record — wall time + CPU time + memory for one cell.

    NDJSON-serialisable per ``[[feedback_ndjson_over_bloated_json]]``;
    Phase 8 emits records to
    ``notes/signal_processing_benchmark_<date>.ndjson``.

    Attributes
    ----------
    key:
        Cartesian key for this benchmark cell.
    wall_time_s:
        Median wall-clock time over ``n_repeats`` runs (seconds).
    cpu_time_s:
        Median ``time.process_time()`` over ``n_repeats`` runs (seconds).
    memory_bytes:
        Peak resident memory observed (bytes); Phase 8 uses
        ``tracemalloc``. Phase 1 stub allows zero placeholder.
    n_repeats:
        Number of repeat runs underlying the medians (Phase 8 default 5).
    notes:
        Free-form metadata field (e.g. "anomaly: cascade-depth=10 BO95
        confidence interval too wide; recommend re-profile").
    extra:
        Reserved dict for Phase 8 to attach regression-fit residuals,
        run-environment metadata, etc.
    """

    key: ProfileCellKey
    wall_time_s: float
    cpu_time_s: float
    memory_bytes: int = 0
    n_repeats: int = 1
    notes: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_ndjson_line(self) -> str:
        """Render as one NDJSON line (no trailing newline)."""
        payload = {
            "op_name": self.key.op_name,
            "path": self.key.path,
            "input_size": self.key.input_size,
            "cascade_depth": self.key.cascade_depth,
            "substrate": self.key.substrate,
            "wall_time_s": self.wall_time_s,
            "cpu_time_s": self.cpu_time_s,
            "memory_bytes": self.memory_bytes,
            "n_repeats": self.n_repeats,
            "notes": self.notes,
            "extra": self.extra,
        }
        return json.dumps(payload, sort_keys=False)


# ──────────────────────────────────────────────────────────────────────
# In-memory record buffer (Phase 1 stub; Phase 8 flushes to disk)
# ──────────────────────────────────────────────────────────────────────


_RECORDS: List[ProfileRecord] = []


def record_profile(record: ProfileRecord) -> None:
    """Append a :class:`ProfileRecord` to the in-memory buffer.

    Phase 1 stub: buffer is module-level list; Phase 8 adds disk flush.
    Hook API is stable from Phase 1 — Phase 5 dispatcher's `path="verify"`
    mode may emit timing records via this entry point if the user opts in.
    """
    assert isinstance(record, ProfileRecord), (
        f"record_profile: expected ProfileRecord, got {type(record).__name__}"
    )
    _RECORDS.append(record)


def iter_records() -> Iterator[ProfileRecord]:
    """Iterate over the in-memory record buffer in insertion order."""
    return iter(tuple(_RECORDS))


def clear_records() -> None:
    """Drop the in-memory record buffer. Test-isolation utility."""
    _RECORDS.clear()


# ──────────────────────────────────────────────────────────────────────
# Cell enumeration helper (Phase 1 — supports Phase 8 sweep building)
# ──────────────────────────────────────────────────────────────────────


def cell_grid(
    *,
    op_names: Tuple[str, ...],
    input_sizes: Optional[Tuple[int, ...]] = None,
    cascade_depths: Optional[Tuple[int, ...]] = None,
    substrates: Optional[Tuple[str, ...]] = None,
    paths: Tuple[str, ...] = (PATH_A, PATH_B),
) -> Iterator[ProfileCellKey]:
    """Enumerate the cartesian product of benchmark cells.

    Default cardinality (per plan §5.1):
    ``len(op_names) × 6 × 4 × 4 × 2`` cells.

    Phase 1 ships the enumeration helper; Phase 8 wires it into the
    runner.

    Parameters
    ----------
    op_names:
        Sequence of operation names to profile.
    input_sizes:
        Defaults to :data:`DEFAULT_INPUT_SIZES` (6 sizes).
    cascade_depths:
        Defaults to :data:`DEFAULT_CASCADE_DEPTHS` (4 depths).
    substrates:
        Defaults to :data:`srmech.signal_processing._paths.SUBSTRATES`
        (4 substrates).
    paths:
        Defaults to ``("A", "B")`` — both paths run per cell so the
        regression has data for the crossover threshold.

    Yields
    ------
    ProfileCellKey
        One per cell in the cartesian product.
    """
    if input_sizes is None:
        input_sizes = DEFAULT_INPUT_SIZES
    if cascade_depths is None:
        cascade_depths = DEFAULT_CASCADE_DEPTHS
    if substrates is None:
        substrates = SUBSTRATES
    for op_name in op_names:
        for input_size in input_sizes:
            for cascade_depth in cascade_depths:
                for substrate in substrates:
                    for path in paths:
                        yield ProfileCellKey(
                            op_name=op_name,
                            path=path,
                            input_size=input_size,
                            cascade_depth=cascade_depth,
                            substrate=substrate,
                        )


