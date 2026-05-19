"""Profiling infrastructure for ``srmech.signal_processing``.

Phase 1 scaffolding (v0.4.2rc1) — data structures + hook API for
empirical Path-A-vs-Path-B benchmarking. Phase 8 (v0.4.2rc8) implements
the benchmark runner, regression pipeline, and learned-dispatch-table
materialisation; Phase 1 ships the surface so Phase 5 dispatcher work
can call into a defined API.

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
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

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
    "ProfilingNotImplementedError",
    "record_profile",
    "iter_records",
    "clear_records",
    "profile_op",
    "update_dispatch_table",
    "cell_grid",
    "DEFAULT_INPUT_SIZES",
    "DEFAULT_CASCADE_DEPTHS",
]


# ──────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────


class ProfilingNotImplementedError(NotImplementedError):
    """Raised by Phase 1 stubs that defer to Phase 8.

    Phase 1 ships the API surface so the dispatcher (Phase 5) and
    learned-table consumers can program against a stable interface;
    the actual benchmark runner + regression pipeline lands in Phase 8
    (v0.4.2rc8) per the implementation plan §6.8.
    """


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


# ──────────────────────────────────────────────────────────────────────
# Phase 8 hooks (Phase 1 stubs raise NotImplementedError)
# ──────────────────────────────────────────────────────────────────────


def profile_op(
    op_name: str,
    *,
    input_sizes: Optional[Tuple[int, ...]] = None,
    cascade_depths: Optional[Tuple[int, ...]] = None,
    substrates: Optional[Tuple[str, ...]] = None,
    n_repeats: int = 5,
    runner: Optional[Callable[..., ProfileRecord]] = None,
) -> List[ProfileRecord]:
    """Run the benchmark suite for one op across the configured grid.

    Phase 1 stub raises :class:`ProfilingNotImplementedError`. Phase 8
    populates the runner; until then the API is locked.

    Parameters
    ----------
    op_name:
        Operation name (must be registered in :mod:`path_registry`).
    input_sizes, cascade_depths, substrates:
        Override default sweeps (see :func:`cell_grid`).
    n_repeats:
        Number of repeat runs per cell underlying the median timing.
    runner:
        Optional cell-runner injection point for test isolation. Phase 8
        provides the default.

    Returns
    -------
    list[ProfileRecord]
        One record per cell in the sweep.

    Raises
    ------
    ProfilingNotImplementedError
        Phase 1 stub — Phase 8 lands the runner.
    """
    raise ProfilingNotImplementedError(
        "profile_op is a Phase 1 scaffolding stub. Benchmark runner "
        "lands in Phase 8 (v0.4.2rc8) per the implementation plan §6.8. "
        f"(op_name={op_name!r}, n_repeats={n_repeats})"
    )


def update_dispatch_table(
    *,
    records: Optional[List[ProfileRecord]] = None,
    locked: bool = True,
) -> Dict[str, Any]:
    """Build / update the learned dispatch table from collected records.

    Phase 1 stub raises :class:`ProfilingNotImplementedError`. Phase 8
    materialises the table per the lock policy in
    :data:`srmech.signal_processing._paths.DISPATCH_TABLE_LOCK_POLICY`.

    Parameters
    ----------
    records:
        Records to regress. Defaults to the module-level buffer
        (:func:`iter_records`).
    locked:
        If True, the materialised table is written to the locked path
        (:data:`srmech.signal_processing._paths.LEARNED_DISPATCH_TABLE_PATH`).
        If False, returned in-memory only.

    Returns
    -------
    dict
        Per-op-per-substrate regression-fit threshold dict.

    Raises
    ------
    ProfilingNotImplementedError
        Phase 1 stub — Phase 8 lands the regression pipeline.
    """
    raise ProfilingNotImplementedError(
        "update_dispatch_table is a Phase 1 scaffolding stub. Regression "
        "pipeline lands in Phase 8 (v0.4.2rc8) per the implementation "
        f"plan §6.8. (locked={locked}, n_records="
        f"{len(records) if records is not None else len(_RECORDS)})"
    )


# ──────────────────────────────────────────────────────────────────────
# Minimal-cell timing helper (Phase 1 — usable in tests, not a runner)
# ──────────────────────────────────────────────────────────────────────


def _time_one_call(
    fn: Callable[..., object],
    args: Tuple[Any, ...] = (),
    kwargs: Optional[Dict[str, Any]] = None,
) -> Tuple[float, float]:
    """Time one call to ``fn(*args, **kwargs)``. Returns (wall_s, cpu_s).

    Phase 1 utility for unit-testing the profiling surface without
    invoking the Phase 8 runner. Not a benchmarking-grade harness —
    use Phase 8's :func:`profile_op` for sweep work.
    """
    kwargs = kwargs or {}
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    fn(*args, **kwargs)
    wall_end = time.perf_counter()
    cpu_end = time.process_time()
    return (wall_end - wall_start, cpu_end - cpu_start)
