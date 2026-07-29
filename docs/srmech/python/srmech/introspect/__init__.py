"""srmech.introspect — out-of-band introspection for a running srmech.

Per user direction 2026-05-28: "we need some way to expose [srmech's
internal current state] safely over API... talks to the current
running srmech by pid or something along those lines... this might
also introduce an ability for srmech/siona to call itself."

Long-running sweeps (30 min to hours) become observable from a
second process without monkey-patching, GDB attach, or ``top`` /
``ps`` polling. A status file at
``~/.srmech/run-{pid}-{start_time_ns}.ndjson`` carries one NDJSON
line per cascade-op / AMSC-fetch / signal-processing call. The
``Run.follow()`` generator tails that file across the process
boundary.

Framework reading
-----------------
Introspection IS **Class H (self-introspection)** projected across
the OS-process boundary. The running process is the spatial
manifold; the NDJSON file is the algebraic projection of its state
per ``[[user_stance_fiber_as_spatially_absent_encoding]]``.
Substrate-self-recognition extended to "the running srmech process"
is a literal instance of the
``[[user_stance_substrate_self_recognition_inevitable_per_loe]]``
cascade — composes with Spike #219 / MFO §VII.6.11.

Public API
----------
* :func:`publish` — context manager that turns ON event emission.
  OFF by default; importing :mod:`srmech.introspect` does not
  create any file.
* :func:`list` — enumerate live (and recently-died) runs filtered
  by file ownership. Returns a list of :class:`Run` records.
* :func:`by_pid` — look up one :class:`Run` by PID; returns the
  most-recent file if PID was recycled (the ``start_time_ns`` suffix
  in the filename defeats PID recycling).
* :class:`Run` — frozen dataclass; metadata about one publishing
  process.
* :class:`Event` — frozen dataclass; one NDJSON line decoded.

Environment-variable opt-in
---------------------------
Setting ``SRMECH_PUBLISH_STATUS=1`` BEFORE ``import srmech`` auto-
activates a process-wide publish context. Same effect as wrapping
``main()`` in ``with publish():``. The detection lives in
:mod:`srmech.__init__` which calls
:func:`_maybe_auto_publish` at import time.

Cross-platform notes
--------------------
* Linux / macOS: ``os.kill(pid, 0)`` + ``os.stat().st_uid`` for
  liveness + ownership.
* Windows: ``OpenProcess`` + ``GetExitCodeProcess`` via ctypes
  (avoids the ``pywin32`` dep). Ownership uses a simpler check —
  files in the user's profile dir + ``os.access`` readable.
* Pyodide / WASM: :func:`publish` raises a degraded warning and
  becomes a no-op (no filesystem available); :func:`list` /
  :func:`by_pid` return empty / ``None``.
"""

from __future__ import annotations

import builtins
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from . import _event, _writer
from ._event import (
    INTROSPECT_DIR_NAME,
    MPR_VERSION_INTROSPECT,
    Event,
    describe_shape,
    parse,
    serialize,
)
from ._writer import (
    _activate_writer,
    _deactivate_writer,
    _is_publishing,
    emit_if_publishing,
    get_active_writer,
    introspect_dir,
)

# ─────────────────────────────────────────────────────────────────────
# Pyodide degradation
# ─────────────────────────────────────────────────────────────────────


def _is_pyodide() -> bool:
    """Detect Pyodide / WASM environment.

    Pyodide sets ``sys.platform == 'emscripten'`` and an ``__pyodide__``
    builtin; the spec-required env-var check ``PYODIDE=1`` is honoured
    as a test hook.
    """
    if os.environ.get("PYODIDE") == "1":
        return True
    if sys.platform == "emscripten":
        return True
    return False


# ─────────────────────────────────────────────────────────────────────
# Liveness + ownership probes (cross-platform)
# ─────────────────────────────────────────────────────────────────────


def _process_is_alive(pid: int) -> bool:
    """Return True if a process with this PID is currently alive.

    POSIX path: ``os.kill(pid, 0)`` raises ``ProcessLookupError`` if
    dead, ``PermissionError`` if alive-but-owned-by-another (which
    we treat as alive). Windows path: ``OpenProcess(QUERY_LIMITED) +
    GetExitCodeProcess`` — STILL_ACTIVE (259) means alive.
    """
    if pid <= 0:
        return False
    if os.name == "posix":
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we lack signal permission — alive.
            return True
        except OSError:
            return False
    if os.name == "nt":
        return _process_is_alive_windows(pid)
    # Unknown OS — fall back to optimistic "alive".
    return True


def _process_is_alive_windows(pid: int) -> bool:
    """Win32 OpenProcess + GetExitCodeProcess probe.

    Uses :mod:`ctypes` to avoid the ``pywin32`` dependency. Returns
    False on any access denial — we treat unreachable processes as
    "not ours", which is the safer reading for cleanup purposes.
    """
    try:
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        OpenProcess = kernel32.OpenProcess
        OpenProcess.restype = wintypes.HANDLE
        OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        GetExitCodeProcess = kernel32.GetExitCodeProcess
        GetExitCodeProcess.restype = wintypes.BOOL
        GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        CloseHandle = kernel32.CloseHandle

        handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            exit_code = wintypes.DWORD(0)
            ok = GetExitCodeProcess(handle, ctypes.byref(exit_code))
            if not ok:
                return False
            return int(exit_code.value) == STILL_ACTIVE
        finally:
            CloseHandle(handle)
    except Exception:
        return False


def _file_belongs_to_user(path: Path) -> bool:
    """Return True if this introspect file looks owned by the current user.

    POSIX: ``os.stat().st_uid == os.getuid()``.
    Windows: path under the current user's profile dir (``Path.home()``)
    + readable via ``os.access(... R_OK)``.
    """
    try:
        if not path.exists():
            return False
        if os.name == "posix":
            try:
                return path.stat().st_uid == os.getuid()  # type: ignore[attr-defined]
            except AttributeError:
                # Should not happen on POSIX but defend anyway.
                return os.access(path, os.R_OK)
        # Windows / other.
        try:
            home = Path.home().resolve()
            resolved = path.resolve()
            # Same-anchor check; cheaper than ACL inspection.
            if home in resolved.parents or resolved.parent == home:
                return os.access(path, os.R_OK)
            # Outside home dir — fall back to readability only.
            return os.access(path, os.R_OK)
        except OSError:
            return False
    except OSError:
        return False


# ─────────────────────────────────────────────────────────────────────
# Run + Event reader API
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Run:
    """Metadata about one publishing process.

    Materialised by :func:`list` / :func:`by_pid` by tailing the
    NDJSON file once (cheap: usually a handful of lines).
    """

    pid: int
    start_time_ns: int
    script_name: str
    current_op: str
    current_class: str
    elapsed_ms: int
    status: str  # "running" | "finished" | "died"
    event_count: int
    file_path: Path

    @property
    def start_time(self) -> str:
        """UTC ISO-8601 wall-clock derived from ``start_time_ns``."""
        import datetime as _dt
        seconds = self.start_time_ns / 1e9
        return (
            _dt.datetime.fromtimestamp(seconds, tz=_dt.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )

    def follow(
        self,
        *,
        poll_interval_s: float = 0.5,
        timeout_s: Optional[float] = None,
    ) -> Iterator[Event]:
        """Tail the NDJSON file and yield events as they land.

        Yields all already-written events first, then polls for new
        lines. Stops when the publishing process status transitions
        to ``"finished"`` or ``"died"`` (detected by the
        ``session_end`` event landing in the file OR the PID going
        dead).

        Parameters
        ----------
        poll_interval_s
            How often to re-check the file for new lines (seconds).
            Default 0.5s.
        timeout_s
            Optional safety timeout — generator returns after this
            many wall-clock seconds even if the publisher is still
            running. ``None`` means follow indefinitely.
        """
        path = self.file_path
        if not path.exists():
            return
        deadline = None if timeout_s is None else (time.time() + timeout_s)
        offset = 0
        # We track the trailing partial-line bytes to recover from a
        # mid-line poll (the publishing process may have flushed
        # half-way through writing a line).
        tail = b""
        while True:
            try:
                with open(path, "rb") as fh:
                    fh.seek(offset)
                    chunk = fh.read()
                    offset = fh.tell()
            except OSError:
                return
            if chunk:
                data = tail + chunk
                lines = data.split(b"\n")
                # Last element may be a partial line (no trailing \n).
                tail = lines[-1]
                for raw in lines[:-1]:
                    if not raw:
                        continue
                    try:
                        ev = parse(raw)
                    except Exception:
                        continue
                    yield ev
                    if ev.op_name == "session_end":
                        return
            # Liveness check: if the writer's process is gone AND the
            # file no longer has a session_end coming, we're done.
            if not _process_is_alive(self.pid):
                # Drain any final tail bytes after the writer's exit.
                try:
                    with open(path, "rb") as fh:
                        fh.seek(offset)
                        chunk = fh.read()
                except OSError:
                    return
                if chunk:
                    data = tail + chunk
                    for raw in data.split(b"\n"):
                        if not raw:
                            continue
                        try:
                            ev = parse(raw)
                        except Exception:
                            continue
                        yield ev
                return
            if deadline is not None and time.time() >= deadline:
                return
            time.sleep(poll_interval_s)


def _parse_filename(name: str) -> Optional[Tuple[int, int]]:
    """Parse ``run-{pid}-{start_time_ns}.ndjson`` → (pid, start_time_ns)."""
    if not name.startswith("run-") or not name.endswith(".ndjson"):
        return None
    body = name[len("run-"): -len(".ndjson")]
    parts = body.split("-")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _tail_events(path: Path, *, max_events: int = 4096) -> List[Event]:
    """Read up to ``max_events`` events from the file.

    Cheap: most status files stay small (an op every ~ms / sec).
    Used by :func:`list` and :func:`by_pid` to compute the
    current-op / event-count summary.
    """
    events: List[Event] = []
    try:
        with open(path, "rb") as fh:
            for raw in fh:
                if not raw.strip():
                    continue
                try:
                    events.append(parse(raw))
                except Exception:
                    continue
                if len(events) >= max_events:
                    # Keep the tail — last events have the most-recent op.
                    events = events[-max_events:]
    except OSError:
        return []
    return events


def _run_from_file(path: Path) -> Optional[Run]:
    """Build a :class:`Run` from the status-file at ``path``."""
    parsed = _parse_filename(path.name)
    if parsed is None:
        return None
    pid, start_time_ns = parsed
    events = _tail_events(path)
    if not events:
        # Empty file; still report with sensible defaults.
        alive = _process_is_alive(pid)
        return Run(
            pid=pid,
            start_time_ns=start_time_ns,
            script_name="",
            current_op="",
            current_class="",
            elapsed_ms=0,
            status=("running" if alive else "died"),
            event_count=0,
            file_path=path,
        )
    # Recover script_name from session_start (always first event).
    script_name = ""
    for ev in events:
        if ev.op_name == "session_start":
            script_name = str(ev.extra.get("script_name", ""))
            break
    last = events[-1]
    # Determine status: session_end → finished/died (based on error);
    # otherwise alive-check on PID.
    if last.op_name == "session_end":
        status = "died" if last.error else "finished"
    else:
        status = "running" if _process_is_alive(pid) else "died"
    # elapsed_ms: from session_start to last event (or now if running).
    elapsed_ms = max(0, int((time.time_ns() - start_time_ns) / 1_000_000))
    return Run(
        pid=pid,
        start_time_ns=start_time_ns,
        script_name=script_name,
        current_op=last.op_name,
        current_class=last.class_,
        elapsed_ms=elapsed_ms,
        status=status,
        event_count=len(events),
        file_path=path,
    )


def _list_runs(*, cleanup: bool = True) -> List[Run]:
    """Implementation backing :func:`list`. Separated so the shadowing
    of builtin ``list`` in the public API doesn't bleed inside."""
    if _is_pyodide():
        return []
    try:
        root = introspect_dir()
    except RuntimeError:
        return []
    if not root.exists():
        return []
    runs: List[Run] = []
    try:
        children = builtins.list(root.iterdir())
    except OSError:
        return []
    for path in children:
        if not path.is_file():
            continue
        if not path.name.startswith("run-"):
            continue
        if not path.name.endswith(".ndjson"):
            continue
        if not _file_belongs_to_user(path):
            continue
        run = _run_from_file(path)
        if run is None:
            continue
        # Auto-cleanup on read: dead PIDs whose session_end emitted
        # cleanly get removed. Files for live processes stay put.
        if cleanup and run.status in ("finished", "died"):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        runs.append(run)
    # Most-recent first.
    runs.sort(key=lambda r: r.start_time_ns, reverse=True)
    return runs


def list() -> List[Run]:  # noqa: A001 — public API name; shadows builtin
    """Enumerate active (+ recently-died) runs owned by the current user.

    Returns
    -------
    list[Run]
        Sorted most-recent-first by ``start_time_ns``. Dead-PID files
        are removed from disk as a side effect (auto-cleanup on read);
        their Run records are still returned for the caller to inspect
        the final state.
    """
    return _list_runs(cleanup=True)


def by_pid(pid: int) -> Optional[Run]:
    """Look up the most-recent run for one PID.

    PID recycling defence: if two files share the same PID (because
    the OS reused the PID), the one with the larger ``start_time_ns``
    wins (the more-recent run).

    Parameters
    ----------
    pid
        Process ID to look up.

    Returns
    -------
    Run | None
        The most-recent run, or ``None`` if no file matches.
    """
    if _is_pyodide():
        return None
    matches = [r for r in _list_runs(cleanup=False) if r.pid == pid]
    if not matches:
        return None
    matches.sort(key=lambda r: r.start_time_ns, reverse=True)
    return matches[0]


# ─────────────────────────────────────────────────────────────────────
# publish() context manager + env-var auto-activation
# ─────────────────────────────────────────────────────────────────────


@contextmanager
def publish(*, remove_on_exit: bool = False) -> Iterator["_PublishHandle"]:
    """Context manager that turns ON introspection emission.

    Inside the ``with`` block, every cascade-op / AMSC-fetch /
    signal-processing call emits one NDJSON event to
    ``~/.srmech/run-{pid}-{start_time_ns}.ndjson``. Outside the
    block, those emit hooks are no-ops (zero cost when off).

    Re-entering :func:`publish` while already publishing is a no-op
    (returns a handle to the existing writer).

    Parameters
    ----------
    remove_on_exit
        If True, the status file is unlinked when the block exits.
        Default False — leave the file for :func:`list` to auto-clean
        on next read (mirrors the spec).

    Yields
    ------
    _PublishHandle
        Lightweight handle exposing ``pid``, ``start_time_ns``,
        ``file_path`` of the active writer.
    """
    if _is_pyodide():
        # Pyodide degradation — yield a no-op handle.
        yield _PublishHandle(
            pid=os.getpid(),
            start_time_ns=time.time_ns(),
            file_path=Path("/dev/null"),
            active=False,
        )
        return
    was_already_active = get_active_writer() is not None
    writer = _activate_writer()
    if remove_on_exit:
        writer._remove_on_exit = True  # type: ignore[attr-defined]
    handle = _PublishHandle(
        pid=writer.pid,
        start_time_ns=writer.start_time_ns,
        file_path=writer.file_path,
        active=True,
    )
    error: Optional[BaseException] = None
    try:
        yield handle
    except BaseException as exc:
        error = exc
        raise
    finally:
        # Only the outermost publish() deactivates; nested re-entries
        # leave the writer in place.
        if not was_already_active:
            _deactivate_writer(error=error)


@dataclass(frozen=True)
class _PublishHandle:
    """Handle yielded by :func:`publish` to the ``with`` block."""

    pid: int
    start_time_ns: int
    file_path: Path
    active: bool


def _maybe_auto_publish() -> None:
    """If ``SRMECH_PUBLISH_STATUS=1``, activate a process-wide writer.

    Called once from :mod:`srmech.__init__` at import time. No-op if
    the env var isn't set, if we're under Pyodide, or if a writer is
    already active.
    """
    if os.environ.get("SRMECH_PUBLISH_STATUS") != "1":
        return
    if _is_pyodide():
        return
    if get_active_writer() is not None:
        return
    _activate_writer()
    # Note: no atexit teardown here beyond the Writer's own — atexit
    # ordering vs. interpreter shutdown is finicky. The Writer's
    # internal atexit hook emits session_end best-effort.


# ─────────────────────────────────────────────────────────────────────
# The GRANULARITY inversion (rc347 `#T985`) — one algebra, three widths
# ─────────────────────────────────────────────────────────────────────
#
# *** CONFLATION GUARD — READ THE `reading` KEY BEFORE COMPARING NUMBERS ***
#
# The slot counts below are 8 / 4 / 2, and srmech's
# :data:`srmech.amsc.cascade.one.BLOCK_DIMS` is (2, 4, 8). SAME THREE NUMBERS,
# DIFFERENT OBJECTS:
#
#   * BLOCK_DIMS (2, 4, 8) = the real dims of THREE DIFFERENT ALGEBRAS,
#     C and H and O.
#   * the slot counts here  = ONE ALGEBRA (O) re-addressed at THREE WIDTHS.
#
# The collision is only at 2:4:8 — 11D = 1 + 3 + 7 is unambiguous. The guard
# ships INSIDE the payload rather than as a comment because a reader of
# describe() never sees this file, and a report that does not label which
# reading it is teaches the confusion instead of removing it.
#
# The structure at each width is 1 ANCHOR + (n-1) TORSORS: the identity sits in
# exactly one slot and only that slot is closed under the product. MEASURED via
# the INDEX lane (closure under XOR) — which is itself the point that lane is
# ORTHOGONAL to granularity: the index identity holds at every width.
_GRANULARITY: Dict[str, Any] = {
    "reading": "one_algebra_three_widths",
    "algebra": "O",
    "algebra_real_dim": 8,
    "not_this_reading": {
        "name": "block_dims",
        "value": [2, 4, 8],
        "symbol": "srmech.amsc.cascade.one.BLOCK_DIMS",
        "means": "the real dims of THREE algebras: C, H, O",
    },
    "collision_note": (
        "the slot counts below (8, 4, 2) are ONE algebra (O) re-addressed at "
        "three widths; BLOCK_DIMS (2, 4, 8) are the real dims of THREE "
        "algebras (C, H, O). Same three numbers, different objects — check "
        "`reading` before comparing them. (11D = 1+3+7 has no such collision.) "
        "A SECOND axis collides the same way: `index_bits` is an EXPONENT "
        "(log2 of `slots`), NEVER a dimension. The (Z/2)^d grading cube of a "
        "dim-2^d algebra has 2^d vertices, one per basis direction, so the "
        "4-cube (tesseract) grades the SEDENIONS at dim 16 — H's grading cube "
        "is the SQUARE (Z/2)^2. The tesseract that lives IN H is a third "
        "object: 16 unit POINTS of R^4 (the half-integer Hurwitz units), not a "
        "grading — 128 of their 256 products leave the set (measured "
        "2026-07-28), so no sign-bit XOR grades them. "
        "A FOURTH sense (rc354, F1336) — and it is the one that makes the "
        "tesseract genuinely ambiguous. An algebra of real dim n does not have "
        "n units; it has 2n SIGNED units (±e_0 … ±e_{n-1}), so a unit LABEL "
        "needs log2(n)+1 bits: log2(n) for the index and ONE MORE for the "
        "sign. H (dim 4) therefore has 8 signed units = a 3-CUBE, and O (dim 8) "
        "has 16 signed units = a 4-CUBE. The 16-vertex tesseract is ALSO O's "
        "UNIT-LABEL cube, not only S's grading cube — two different 16s: S has "
        "16 basis DIRECTIONS, O has 16 signed UNITS. That is why 8 is the "
        "middle ground: O addresses 16 units in 4 bits AND contains H seven "
        "times (the seven Fano lines, each {0,a,b,c} verified closed under the "
        "product). THE SHADOW, DERIVED THEN MEASURED on cd_basis_product: under "
        "a flat (log2(n)+1)-bit XOR label the low log2(n) bits XOR EXACTLY (0 "
        "violations at every rung), but the TOP (sign) bit does NOT — the "
        "violating ordered pairs of signed units number exactly 2*dim*(dim-1) "
        "(4 / 24 / 112 / 480 at dims 2/4/8/16), a fraction (dim-1)/(2*dim) = "
        "1/4, 3/8, 7/16, 15/32 -> 1/2. THE FLAT HYPERCUBE IS WRONG EXACTLY "
        "WHERE THE ALGEBRA ANTICOMMUTES, and it worsens up the ladder. "
        "BOUNDS, so this is not over-read: the closed form is DERIVED and "
        "CHECKED at six rungs (2/4/8/16/32/64), NOT proved for all n; 'O is THE "
        "right carrier' is a DESIGN argument from those two facts, NOT a "
        "measurement; and (dim-1)/(2*dim) is about BASIS-PAIR PRODUCTS under a "
        "flat label — it is NOT a strand-misread rate and must not enter an "
        "error budget."
    ),
    "unit_label_cube": {
        "reading": "signed_unit_labels",
        "rule": "an algebra of real dim n has 2n signed units, labelled in "
                "log2(n)+1 bits (log2(n) index bits + 1 sign bit)",
        "vs_grading_cube": "the grading cube (Z/2)^log2(n) has n vertices, one "
                           "per basis DIRECTION; the unit-label cube has 2n, "
                           "one per SIGNED unit",
        "the_two_sixteens": {
            "S_grading_cube": {"algebra": "S", "real_dim": 16,
                               "vertices": 16, "counts": "basis directions"},
            "O_unit_label_cube": {"algebra": "O", "real_dim": 8,
                                  "vertices": 16, "counts": "signed units"},
        },
        "why_8_is_the_middle_ground": (
            "O addresses 16 signed units in 4 bits AND contains H seven times "
            "(the Fano lines) — a DESIGN argument, not a measurement"),
        "shadow": {
            "index_bits_xor": "exact at every rung (0 violations measured)",
            "sign_bit_xor": "fails; violations = 2*dim*(dim-1)",
            "violations_by_dim": {"2": 4, "4": 24, "8": 112, "16": 480,
                                  "32": 1984, "64": 8064},
            "fraction_wrong": {"2": [1, 4], "4": [3, 8], "8": [7, 16],
                               "16": [15, 32], "32": [31, 64], "64": [63, 128]},
            "limit": "(dim-1)/(2*dim) -> 1/2",
            "reads_as": "the flat hypercube is wrong exactly where the algebra "
                        "ANTICOMMUTES, and worsens up the ladder",
        },
        "bounds": [
            "DERIVED, then checked at six rungs (2/4/8/16/32/64) — NOT proved "
            "for all n",
            "'O is THE right carrier' is a DESIGN argument, not a measurement",
            "(dim-1)/(2*dim) is about BASIS-PAIR PRODUCTS, not a strand-misread "
            "rate — do not carry it into an error budget",
        ],
        "generating_code": "docs/srmech/notes/unit_label_cube_rc354.py",
    },
    "invariant": (
        "1 anchor + (n-1) torsors at every width: the identity sits in exactly "
        "ONE slot and only that slot closes under the product"),
    "measured_by": "closure under the INDEX lane (XOR) — lane is orthogonal "
                   "to granularity, so the same test applies at every width",
    "index_bit_map": {"bit2": "H vs He", "bit1": "C vs Cj", "bit0": "1 vs i"},
    "widths": [
        {"over": "R", "slots": 8, "real_dims_per_slot": 1, "index_bits": 3,
         "anchor_slots": 1, "torsor_slots": 7,
         "closes": {"R_0": True, "R_1": False, "R_2": False, "R_3": False,
                    "R_4": False, "R_5": False, "R_6": False, "R_7": False}},
        {"over": "C", "slots": 4, "real_dims_per_slot": 2, "index_bits": 2,
         "anchor_slots": 1, "torsor_slots": 3,
         "closes": {"C_LL": True, "C_LR": False, "C_RL": False,
                    "C_RR": False}},
        {"over": "H", "slots": 2, "real_dims_per_slot": 4, "index_bits": 1,
         "anchor_slots": 1, "torsor_slots": 1,
         "closes": {"H_L": True, "H_R": False}},
    ],
    "generating_code": "docs/srmech/notes/op_lane_axis_rc347.py",
}


# ─────────────────────────────────────────────────────────────────────
# describe() — the self-recognition ROOT surface (v0.5.0rc11)
# ─────────────────────────────────────────────────────────────────────


def describe() -> Dict[str, Any]:
    """Return a structured, at-a-glance map of srmech's own shape.

    The "what is srmech?" root — the **self-recognition ROOT surface**
    of the v0.5.0 substrate-self-recognition arc. Calls
    :func:`srmech.amsc.tool_schema.warmup_all` first so the counts are
    complete no matter how srmech was entered, then groups the
    registered tool-schema by ``entry.category`` and folds in the
    native-dispatch status.

    Framework reading: this IS **Class H (self-introspection)** at
    package scale — the package recognising and rendering the SHAPE of
    its own A–N tool surface (composes with the per-process Class-H
    projection that the rest of this module implements). It is a ROOT /
    INDEX: it surfaces the shape, not the detail. Per-tool JSON schemas,
    environment, and error-type catalogues are deliberately out of
    scope here (later voxels — rc15 config/data-schemas, rc16 LLM
    agent — add those deeper surfaces).

    v0.5.0rc15 — the ``tools`` block now reports the MCP-callability
    SPLIT: ``mcp_callable`` (advertised across the JSON-RPC / Anthropic
    boundary) vs. ``handle_pending`` (registered for introspection but
    NOT advertised — the 7 ``srmech.spectral.*`` tools whose surface is a
    bare ``SpectralHandle`` JSON cannot carry by value; by-reference id
    grammar lands in rc16). A top-level ``handle_pending`` lists their
    names. The package declaring its own callable shape IS the apparatus
    thesis (Class H self-introspection at package scale).

    Returns
    -------
    dict
        ::

            {
              "srmech_version": <str>,
              "tool_schema_version": <str>,
              "native": {"has_native": <bool>,
                         "abi_version": <int|None>,
                         "native_version": <str|None>},
              "tools": {"total": <int>,
                        "mcp_callable": <int>,
                        "handle_pending": <int>,
                        "by_category": {<category>: <count>, ...}},
              "handle_pending": [<sorted handle-pending tool names>],
              "categories": [<sorted category names>],
              "classes": {"total": <int>,
                          "names": [<sorted domain-class names>],
                          "routes": {<name>: "toml"|"python", ...},
                          "toml_total": <int>},
              "carriers": {"total": <int>,
                           "capabilities": {<carrier>: {
                               "product": <str|None>,
                               "address": "exact"|None,
                               "compose": "full"|"zero_divisors"
                                          |"unclassified"|None,
                               "turn": "non_commuting"|"abelian_only"
                                       |"unclassified"|None,
                               "commutative": <bool|None>,
                               "varies_with": "dim"|"element_type"|None},
                               ...}},
              "limits": {"capabilities": {<capability>: {
                             "means": <str>,
                             "family": <carrier-family name>,
                             "max_dim": <int>,
                             "beyond_ceiling": <str|None>,
                             "bounded_by": <mechanism name>,
                             "holds_through": <element-type name|None>,
                             "exceeded_by": [<carrier>, ...],
                             ...}},
                         "element_types": [{"code": <int>, "name": <str>,
                             "algebra": <str>, "order": <int>,
                             "cd_dim": <int|None>, "commutative": <bool>,
                             "address": <str>, "compose": <str>,
                             "turn": <str>,
                             "commutes": [<pass>, <total>],
                             "associates": [<pass>, <total>],
                             "turns_compose": [<pass>, <total>]}, ...]},
              "c_claims": {"native": <bool>,
                           "checked_ops": <int>,
                           "checked_symbols": <int>,
                           "unresolved": {<op>: [<symbol>, ...]},
                           "unverifiable": <int>,
                           "consistent": <bool>},
              "lanes": {"total": <int>,
                        "by_lane": {"index"|"sign"|"both": <count>, ...},
                        "by_input": {"algebra"|"geometry": <count>, ...},
                        "definitions": {<lane>: <means>, ...},
                        "inputs": {<input>: <means>, ...},
                        "verified_by": {"sign": {...}, "index": {...},
                                        "rule": <str>, "test": <path>},
                        "ops": {<op>: {"lane": <lane>,
                                       "reads": [<input>, ...]}, ...},
                        "worked_example": {...},
                        "granularity": {...}},
            }

    ``lanes`` (rc347, `#T985`) — the OP-side complement of ``carriers``.
    rc339 published what each CARRIER can DO; this publishes **what each OP
    READS**, and it is a different axis rather than a finer grain of the same
    one. The Cayley–Dickson product FACTORS:

    ==========  ======================================  ====================
    lane        what it is                              character
    ==========  ======================================  ====================
    ``index``   ``e_i·e_j → e_{i XOR j}``               ABELIAN, ORDER-BLIND,
                                                        exact at every rung,
                                                        unbounded
    ``sign``    the cocycle over it                     ORDER-CARRYING; every
                                                        published ceiling
                                                        lives here (rc343)
    ==========  ======================================  ====================

    **Lane is ORTHOGONAL to granularity, and both are orthogonal to rc339's
    capability.** The index-lane identity ``index == i XOR j`` was measured
    with ZERO violations at dims 2 / 4 / 8 / 16 (4/4, 16/16, 64/64, 256/256)
    and on the shipped ``q8_mult`` (64/64) — the same statement at every
    addressing width, which is what "orthogonal to granularity" means
    concretely.

    **Chirality is a SIGN-lane operation**, measured three ways over the basis
    products and moving ZERO indices in every one: order reversal (the opposite
    algebra) moves 6/16 signs at ℍ, 42/64 at 𝕆, 210/256 at 𝕊; ``cd_conjugate``
    14/64; ``q8_conjugate`` 24/64.

    **The field is not an assertion — it is verified executably.** A declared
    lane that nothing can contradict is exactly rc339's ``bounded_by:
    "associativity"`` in a new place, so ``reads_lane`` carries the same shape
    of admission rule ``bounded_by`` gained in rc343. An op may declare only
    when BOTH perturbations are applicable to its input (``cascade.
    net_chirality`` takes bare orientations and ``cascade.cd_basis_product``
    bare indices — neither can declare, because neither could be wrong), and
    ``tests/test_op_lane_rc347.py`` then drives every declaring op through a
    sigma flip and an ``Aut(V4) = S3`` index relabel and fails the build when
    the response contradicts the declaration. Verdicts are SWEPT: a single
    input can miss a real response, since an even number of sign flips cancels
    inside an ordered product.

    ``worked_example`` carries the Tw / Wr / Lk adjudication, read off
    ``genome.cwf_consistency_mod2`` — the one shipped op that computes all
    three — over 3000 trials::

        read  field    sign(algebra)  index(algebra)  sign(geometry)  verdict
        Tw    tw_mod2   3000/3000        0/3000          0/3000    SIGN, ALGEBRA
        Wr    wr           0/3000        0/3000       3000/3000    SIGN, GEOMETRY
        Lk    lk_mod2    735/3000      182/3000          0/3000    BOTH, ALGEBRA

    The structural point: **Tw and Wr are not one quantity at two
    resolutions.** They read DIFFERENT INPUTS — a coset-sign count over the
    ALGEBRA versus the sign of orientation determinants over the GEOMETRY — and
    what they share is the LANE. **Lk is the only mixer**: the only one of the
    three whose output responds to a pure index relabel. Wr's
    magnitude-blindness is the geometry-side proof that it reads the sign and
    discards the magnitude it computed: ``discrete_writhe`` is IDENTICAL under
    positive rational rescale ×1, ×3, ×100, ×1/7, ×999/4 (5/5) while NEGATING
    under a reflection.

    ``granularity`` reports the same object at three addressing widths — 𝕆 over
    ℝ (8 slots × 1 real dim), over ℂ (4 × 2), over ℍ (2 × 4), one index bit per
    doubling — with **1 anchor + (n−1) torsors** at each: the identity sits in
    exactly ONE slot and only that slot closes. MEASURED: ``H_L {0,1,2,3}``
    closes, ``H_R {4,5,6,7}`` does not; ``C_LL {0,1}`` closes, ``C_LR`` /
    ``C_RL`` / ``C_RR`` do not.

    **The 2:4:8 collision is labelled IN THE PAYLOAD.** The slot counts (8, 4,
    2) are ONE algebra at three widths; :data:`srmech.amsc.cascade.one.
    BLOCK_DIMS` (2, 4, 8) are the real dims of THREE algebras (ℂ, ℍ, 𝕆). Same
    three numbers, different objects — ``granularity["reading"]`` and
    ``granularity["not_this_reading"]`` say which is which, because a reader of
    ``describe()`` never sees the source comment and an unlabelled report
    teaches the confusion. (11D = 1+3+7 has no such collision.) Generating code
    + NDJSON: ``docs/srmech/notes/op_lane_axis_rc347.py``.

    ``c_claims`` (rc300) answers a question ``native`` cannot: not "is a library
    loaded?" but "does the loaded library actually contain the C symbols our ops
    claim to route to?". Those are different, because the header adds symbols
    ABI-additively — a stale build keeps a matching ABI, so ``native`` reports
    healthy while individual ops fall silently to their pure paths and the
    Rosetta ledger still classifies them ``c_dispatched``. ``consistent`` False
    names exactly which ops and symbols are affected. ``unverifiable`` counts
    ``c_dispatched`` ops whose symbol the static walk cannot attribute, so the
    unchecked region is a reported number rather than an invisible gap. On a
    pure install ``native`` is False, ``consistent`` True, and no claim is
    contradicted because none is made.

    ``limits`` (rc298) reports **capability** ceilings only — what this BUILD
    supports, identical on every platform and in both projections. It is NOT a
    statement about host headroom: no key here reports how much stack THIS
    process has left, because rc298 measures none. A resource key would require
    a real PAL stack-limit query and is deliberately absent rather than
    approximated.

    rc339 (`#T967`) — ``limits`` became CAPABILITY-KEYED and ``carriers`` became
    capability-tagged, because reporting only the permissive ceiling implies a
    capability that does not exist.

    rc298 published exactly two ceilings, ``cd_max_dim`` 256 and
    ``cd_dense_max_dim`` 64, and **both are ADDRESSING bounds**. srmech's
    carriers have THREE ceilings, and the other two are the ones that actually
    bind:

    ==========  ============================================  ==============
    capability  what it means                                 ceiling
    ==========  ============================================  ==============
    address     content-key an element; ``e_i·e_j =            effectively
                ±e_{i XOR j}``                                unbounded
                                                              (verified exact
                                                              to dim 64, 0
                                                              failures / 4096
                                                              pairs; the
                                                              build admits
                                                              256)
    compose     multiply with no zero divisors                dim 8 — 𝕆,
                                                              Hurwitz. Past
                                                              it, zero
                                                              divisors.
    turn        fold two turns into one:                      dim 4 — ℍ. Past
                ``L_x ∘ L_y == L_{x·y}``                      it, abelian-only.
    ==========  ============================================  ==============

    **Every ceiling in that table is a CAYLEY–DICKSON fact, and rc343 (`#T972`)
    made it say so.** rc339 published them unscoped, which is a different false
    green from the one it fixed: as GLOBAL statements the ``compose`` and
    ``turn`` numbers are false, and rows in rc339's own ``carriers`` block
    contradict them. ``Mat``'s product ``mat_matmul`` is associative at every
    dim, so its non-commuting turns keep folding — MEASURED over the matrix
    units of ``M_n(ℝ)`` at 81/81 composing pairs for ``n=3`` (algebra dim 9), 42
    non-commuting, and 256/256 for ``n=4`` (dim 16), 108 non-commuting.
    ``Poly`` and the rest of the polynomial ladder are integral domains at
    unbounded degree, so ``compose`` is ``"full"`` far above 8.

    So each capability row carries ``family`` (the carrier family the number IS
    a fact about) and a DERIVED ``exceeded_by`` naming every carrier row that
    outruns it — ``turn`` → ``["Mat"]``. The payload names its own
    counterexamples, and each carrier row carries its OWN ``max_dim`` /
    ``bounded_by``.

    ``bounded_by`` names a MECHANISM, from the closed
    :data:`srmech.amsc.carrier_schema.CEILING_MECHANISMS` vocabulary, and the
    admission rule is that it must be measurable SEPARATELY from the
    capability's own ``means``. rc339 gave ``turn`` ``bounded_by:
    "associativity"`` — but ``means`` DEFINES turn as ``x·(y·z) == (x·y)·z``,
    so the field restated the definition: anything associative turns, anything
    that turns is associative, and no carrier row could contradict it. The
    replacement is ``"sign_cocycle"``, and it has content. The CD product
    FACTORS, and the halves behave differently (measured over
    ``cd_basis_product``)::

        dim | index == a XOR b | negative signs (C(d,2)) | SIGN COCYCLE assoc
          2 |       4/4        |        1  (1)           |     8/8      100%
          4 |      16/16       |        6  (6)           |    64/64     100%
          8 |      64/64       |       28  (28)          |   344/512     67%
         16 |     256/256      |      120  (120)         |  2248/4096    55%
         32 |    1024/1024     |      496  (496)         | 16808/32768   51%

    The INDEX lane is exact at every rung; the SIGN is what stops being
    associative, abruptly, at dim 8. **Addressing is unbounded because XOR is
    associative at every dim forever; turns and composition break because the
    SIGN COCYCLE stops being associative** — which is also why rc298 (`#T933`)
    could lift ``CD_MAX_DIM`` 64 → 256 by DECOUPLING the caps. (``index == XOR``
    is close to definitional for a CD basis, so that column is a CHECK; the
    READING — a free index and a load-bearing sign — is what it supports.)

    So a caller — or an LLM driving the MCP surface, which is an explicit design
    goal — could read 256 and reach for a TURN there, where non-commuting turn
    composition has been dead since dim 8. That is a false green in the
    self-description, the same failure class as a dead instrumentation seam, not
    a documentation gap.

    Every dimension therefore now lives INSIDE the capability it bounds
    (``limits["capabilities"][<cap>]["max_dim"]``); there is no bare number at
    the top of ``limits`` for a reader to pick up unqualified.
    ``limits["element_types"]`` is the SAME ladder from the rung side — the
    genome's ``ELEMENT_TYPE_*`` codes, which appeared nowhere in ``describe()``
    before this rc, each with its verdict AND the exhaustive measurement the
    verdict was read from. ``holds_through`` on each capability is DERIVED from
    those rows, so the two facets are one fact reported once and cannot drift.

    The precise statement about the octonion rung matters and the imprecise
    version ("turns stop at ℍ") should not be propagated: at Q₈ the
    turn-composing pairs STRICTLY CONTAIN the commuting pairs (24 non-commuting
    pairs still fold), while at 𝕆 the two are **THE SAME SET** — 88 == 88, both
    set differences empty. Turns DEGRADE TO ABELIAN-ONLY at 𝕆; what dies there
    is specifically NON-COMMUTING turn composition. Read ``turn`` together with
    ``commutative``: ``abelian_only`` on a commutative rung is vacuous, on a
    non-commutative one it is the degradation. Generating code + NDJSON:
    ``docs/srmech/notes/carrier_capability_ontology_rc339.py``.

    ``carriers`` gained the same treatment: each carrier reports
    ``{product, address, compose, turn, commutative, varies_with}`` for the
    WORST case over everything it admits — ``CDRegister`` publishes the dim-256
    answer, not the dim-4 one — with ``varies_with`` naming the knob that can
    improve it. Publishing the best case is the failure mode this rc removes.

    rc298 (`#936`) — ``classes`` became CAPABILITY-first, and ``carriers``
    arrived. Both were the same ADR-0009 mechanism-2 defect: introspection
    reporting an implementation detail as if it were the capability surface.

    ``classes`` previously enumerated only the ``[class]`` TOML catalog, so
    ``CDRegister`` — a shipped public class with a registered carrier and three
    C peers — was absent purely because rc297 hand-coded it. It now lists every
    domain class, with the declaration route as a ``routes`` FIELD and the
    TOML-only count preserved as ``toml_total`` for the consumers that need it
    (``srmech.dsl.describe_class`` resolves TOML-declared classes only).

    ``carriers`` did not exist: the 25-entry carrier registry, which carries a
    100% construction-example floor and a compiled-in C peer table, was
    invisible to ``describe()`` entirely. ``tools`` are the verbs and
    ``carriers`` the nouns; reporting one without the other described half a
    package. Per-carrier detail stays in
    :func:`srmech.amsc.carrier_schema.carrier_schema`.
    """
    # Lazy imports: this module is imported during ``srmech.__init__``
    # BEFORE ``warmup_all`` / ``srmech.amsc`` are fully wired, so a
    # module-level import of these would be premature (import cycle).
    from ..amsc import _native
    from ..amsc.tool_schema import (
        TOOL_SCHEMA_VERSION,
        get_tool_schema,
        warmup_all,
    )

    # Populate the registry from every entry-path before we count.
    warmup_all()

    schema = get_tool_schema()

    by_category: Dict[str, int] = {}
    handle_pending: List[str] = []
    mcp_callable_count = 0
    for entry in schema.tools:
        by_category[entry.category] = by_category.get(entry.category, 0) + 1
        if entry.mcp_callable:
            mcp_callable_count += 1
        else:
            handle_pending.append(entry.name)

    # Domain classes (rc41 seeded it as the [class] TOML catalog; rc298 `#936`
    # made it CAPABILITY-first). ``routes`` carries how each class is declared;
    # membership is never decided by it. See introspect._domain_classes.
    from ._domain_classes import list_domain_classes as _list_domain_classes
    _class_routes = _list_domain_classes()
    _toml_total = sum(1 for r in _class_routes.values() if r == "toml")

    # Carriers (rc298 `#936`) — the OPERAND nouns. The registry has a 100%
    # construction-example floor and a compiled-in C peer table, and before
    # rc298 describe() could not see it at all: the same mechanism-2 defect the
    # classes key had. Guarded — carrier_schema is independently optional.
    #
    # rc339 (`#T967`): a flat NAME LIST is the same defect one turn further in.
    # It said which operands exist and nothing about what any of them can DO,
    # while the only ceilings published alongside were both ADDRESSING bounds —
    # so the report answered "how big?" with 256 and stayed silent on the two
    # ceilings that bind. Each carrier now carries its capability row; the names
    # are recoverable as sorted(carriers["capabilities"]).
    try:
        from ..amsc.carrier_schema import (
            _CAPABILITY, _CARRIERS, _domain_word_gap)
        _carrier_caps = {n: dict(_CAPABILITY[n]) for n in sorted(_CARRIERS)}
        # DERIVED from the rows just built — no second registry build, and no
        # chance of the ledger drifting from the capabilities beside it.
        _carrier_domain_gap = _domain_word_gap(_carrier_caps)
    except Exception:  # pragma: no cover — carrier registry optional / absent
        _carrier_caps = {}
        _carrier_domain_gap = {}

    # Dimensional CAPABILITY ceilings (rc298 `#936`). Before this rc describe()
    # could say whether a native library was present and its ABI, but not what
    # it could DO: no dimensional bound of any kind was exposed, so a caller —
    # or an LLM driving the MCP surface — could only discover the largest
    # admissible dim by trying it and failing, or by reading the C header.
    #
    # These are ARTIFACT properties: what this BUILD supports, identical on
    # every platform, and identical in both projections (the Python constants
    # and the C macros are pinned equal by tests/test_cd_rungs_rc298.py). They
    # are deliberately NOT nested under "native" — they bind the pure-Python
    # path too, and would read as native-only there.
    #
    # There is deliberately NO resource/headroom key here. Reporting what THIS
    # HOST can service needs a real measurement (a PAL stack-limit query);
    # rc298 ships none, and a compiled constant published under a name implying
    # runtime headroom would be exactly the kind of wrong number this rc line
    # exists to remove. A missing key is honest.
    # rc339 (`#T967`) — CAPABILITY-KEYED. Both rc298 keys were ADDRESSING bounds
    # and nothing said so, so the block answered "how big can this go?" with 256
    # and was silent on the two ceilings that actually bind. A caller reading 256
    # and reaching for a TURN was reading a permissive number for a capability
    # that died at dim 8. Reporting only the permissive ceiling IMPLIES A
    # CAPABILITY THAT DOES NOT EXIST — the same failure class as a dead
    # instrumentation seam, and not a documentation gap.
    #
    # So every dimension now lives INSIDE the capability it bounds; there is no
    # bare number at the top of ``limits`` for a reader to pick up unqualified.
    # ``element_types`` is the same ladder seen from the rung side (verdict +
    # the measured evidence it was read from), not a second copy of the
    # ceilings — ``holds_through`` is DERIVED from those rows below, so the two
    # facets cannot drift apart.
    try:
        from ..amsc.cascade.cayley_dickson import (
            CD_ADDRESS_VERIFIED_DIM as _CD_ADDR_VERIFIED,
            CD_COMPOSE_MAX_DIM as _CD_COMPOSE_MAX,
            CD_DENSE_MAX_DIM as _CD_DENSE_MAX,
            CD_MAX_DIM as _CD_MAX,
            CD_TURN_MAX_DIM as _CD_TURN_MAX,
        )
        # The ladder these ceilings are facts ABOUT. Same spelling as the
        # carrier registry's `ladder` field, so `family` joins the two views.
        _CD_FAMILY = "cayley_dickson"
        # rc343 (`#T972`) — every ceiling here carries `family`, because every
        # one of these numbers is a CAYLEY-DICKSON fact and rc339 published them
        # unscoped. `bounded_by` names a MECHANISM from
        # carrier_schema.CEILING_MECHANISMS: admissible only if it can be
        # measured SEPARATELY from the capability's own `means`. rc339's
        # "associativity" on `turn` failed that test — `means` IS the
        # associativity condition, so the field restated the definition and no
        # carrier row could contradict it. "sign_cocycle" is measurable on its
        # own and independently predicts 4. `exceeded_by` is DERIVED below.
        _capabilities: Dict[str, Any] = {
            "address": {
                "means": (
                    "content-key an individual element; on the Cayley-Dickson "
                    "ladder the index lane e_i*e_j = +/- e_(i XOR j)"),
                "family": _CD_FAMILY,
                "max_dim": _CD_MAX,
                "dense_max_dim": _CD_DENSE_MAX,
                "verified_exact_to_dim": _CD_ADDR_VERIFIED,
                "beyond_ceiling": None,
                "bounded_by": "tooling",
            },
            "compose": {
                "means": (
                    "multiply with NO zero divisors (a normed composition "
                    "algebra)"),
                "family": _CD_FAMILY,
                "max_dim": _CD_COMPOSE_MAX,
                "beyond_ceiling": "zero_divisors",
                "bounded_by": "hurwitz",
            },
            "turn": {
                "means": (
                    "fold two turns into one: L_x o L_y == L_(x*y), i.e. "
                    "x*(y*z) == (x*y)*z for every z"),
                "family": _CD_FAMILY,
                "max_dim": _CD_TURN_MAX,
                "beyond_ceiling": "abelian_only",
                "bounded_by": "sign_cocycle",
            },
        }
    except Exception:  # pragma: no cover — cascade surface optional
        _capabilities = {}
    try:
        from ..amsc.genome import ELEMENT_TYPE_CAPABILITY as _ET_CAP
        _element_types = [
            {k: (builtins.list(v) if isinstance(v, tuple) else v)
             for k, v in row.items()}
            for row in _ET_CAP
        ]
    except Exception:  # pragma: no cover — genome surface optional
        _element_types = []
    # The verdict value that counts as "this capability holds in FULL" on a
    # rung. ``holds_through`` is then the HIGHEST rung carrying it — derived, so
    # the ceiling and the ladder are one fact reported once, and a rung whose
    # verdict changes moves the ceiling's cross-reference with it.
    _FULL_VERDICT = {"address": "exact", "compose": "full",
                     "turn": "non_commuting"}
    for _cap_name, _cap in _capabilities.items():
        _through = None
        for _row in _element_types:
            if _row.get(_cap_name) == _FULL_VERDICT[_cap_name]:
                _through = _row["name"]
        _cap["holds_through"] = _through

    # ``exceeded_by`` (rc343, `#T972`) — DERIVED: the carriers that deliver this
    # capability in FULL ABOVE the family ceiling. This is the field that stops
    # `max_dim` being read as a universal bound, and it is computed from the
    # carrier rows rather than asserted beside them, so it cannot drift: add a
    # carrier that outruns a ceiling and it appears here on the next call.
    #
    # It is NOT empty. `turn` has a ceiling of 4 and `Mat` — whose product
    # mat_matmul is associative at every dim — composes non-commuting turns at
    # algebra dim 9 and 16 (measured; tests/test_carrier_ceiling_rc343.py).
    # `compose` has a ceiling of 8 and the polynomial ladders are integral
    # domains at unbounded degree. rc339 published both numbers with no carrier
    # attached and no counterexample named, which is how a Cayley-Dickson fact
    # came to read as a statement about every carrier srmech ships.
    for _cap_name, _cap in _capabilities.items():
        _ceiling = _cap.get("max_dim")
        _full = _FULL_VERDICT[_cap_name]
        _over = []
        for _cname, _crow in _carrier_caps.items():
            if _crow.get(_cap_name) != _full:
                continue
            _cmax = _crow.get("max_dim")
            # None == unbounded in dim, so it outruns any finite ceiling.
            if _ceiling is None or _cmax is None or _cmax > _ceiling:
                _over.append(_cname)
        _cap["exceeded_by"] = sorted(_over)
    _limits: Dict[str, Any] = {}
    if _capabilities:
        _limits["capabilities"] = _capabilities
    if _element_types:
        _limits["element_types"] = _element_types

    # C-claim resolution (rc300 `#T938`) — is the C path we advertise really in
    # the library we loaded? ``native`` above says a library loaded and its ABI
    # matched; it does NOT say the library contains the symbols the ops claim,
    # because the header adds symbols ABI-additively. A stale or partial build
    # keeps ABI 8, resolves no new symbol, and every affected op falls silently
    # to its pure path while the ledger still classifies it ``c_dispatched``.
    # This key is what makes that discoverable — including to an LLM on the MCP
    # surface, which could previously see "has_native: true" and reasonably but
    # wrongly conclude the promised C path existed for a given op.
    try:
        _c_claims = _native.c_claim_report()
    except Exception:  # pragma: no cover — manifest optional / absent
        _c_claims = {}

    # The LANE axis (rc347 `#T985`) — what each op READS. `carriers` says what
    # each OPERAND can do; this is the complement over the VERBS, and it is a
    # different axis rather than a finer grain of the same one: lane is
    # orthogonal to granularity (the index-lane XOR identity holds at every
    # addressing width) and both are orthogonal to rc339's capability.
    #
    # DERIVED from the tool schema, never a second list: an op declares its
    # lane on its own ToolEntry and this block counts what is declared, so the
    # two cannot drift.
    _lane_ops = {
        e.name: {"lane": e.reads_lane, "reads": builtins.list(e.reads_input)}
        for e in schema.tools if e.reads_lane is not None
    }
    _by_lane: Dict[str, int] = {}
    _by_input: Dict[str, int] = {}
    for _row in _lane_ops.values():
        _by_lane[_row["lane"]] = _by_lane.get(_row["lane"], 0) + 1
        for _src in _row["reads"]:
            _by_input[_src] = _by_input.get(_src, 0) + 1
    try:
        from ..amsc.tool_schema import LANES as _LANES, LANE_INPUTS as _LANE_IN
        _lane_defs = dict(_LANES)
        _lane_inputs = dict(_LANE_IN)
    except Exception:  # pragma: no cover
        _lane_defs, _lane_inputs = {}, {}
    _lanes: Dict[str, Any] = {
        "total": len(_lane_ops),
        "by_lane": dict(sorted(_by_lane.items())),
        "by_input": dict(sorted(_by_input.items())),
        "definitions": _lane_defs,
        "inputs": _lane_inputs,
        # The admission rule as DATA, not prose: the two perturbations a
        # declaration is checked against. An op that cannot be given both is
        # inadmissible and declares nothing.
        "verified_by": {
            "sign": {
                "algebra": "XOR the Q8 center sign bit (q ^ 4); index untouched",
                "geometry": ("reverse orientation by reflecting one "
                             "coordinate; magnitudes untouched"),
            },
            "index": {
                "algebra": ("relabel the V4 coset by an element of "
                            "Aut(V4) = S3; sign bit untouched"),
                "geometry": ("positive-rational rescale of every coordinate; "
                             "no orientation determinant changes sign"),
            },
            "rule": ("a declared lane must MOVE under its own perturbation and "
                     "NOT move under the other; swept, never sampled"),
            "test": "tests/test_op_lane_rc347.py",
        },
        "ops": _lane_ops,
        # The Tw / Wr / Lk adjudication, measured on the one shipped op that
        # computes all three. Tw and Wr are NOT one quantity at two
        # resolutions: they read DIFFERENT INPUTS and share the LANE.
        "worked_example": {
            "op": "srmech.amsc.genome.cwf_consistency_mod2",
            "trials": 3000,
            "reads": [
                {"name": "Tw", "field": "tw_mod2", "lane": "sign",
                 "input": "algebra", "cascade": "K o I",
                 "means": "coset-SIGN count over the gains, mod 2",
                 "sign_algebra": 3000, "index_algebra": 0,
                 "sign_geometry": 0},
                {"name": "Wr", "field": "wr", "lane": "sign",
                 "input": "geometry", "cascade": "K o C over E o D",
                 "means": ("SIGN of orientation determinants over the "
                           "embedding; magnitudes computed and DISCARDED"),
                 "sign_algebra": 0, "index_algebra": 0,
                 "sign_geometry": 3000},
                {"name": "Lk", "field": "lk_mod2", "lane": "both",
                 "input": "algebra", "cascade": "M o L o C thru I",
                 "means": ("ORDERED non-abelian Q8 bind over the single "
                           "fundamental cycle, reduced mod 2"),
                 "sign_algebra": 735, "index_algebra": 182,
                 "sign_geometry": 0},
            ],
            "reading": ("Lk is the ONLY one of the three that responds to an "
                        "index relabel — the only mixer. Tw and Wr share the "
                        "SIGN lane over different INPUTS."),
        },
        "granularity": _GRANULARITY,
    }

    return {
        "srmech_version": schema.srmech_version,
        "tool_schema_version": TOOL_SCHEMA_VERSION,
        "native": {
            "has_native": bool(_native.HAS_NATIVE),
            "abi_version": _native.NATIVE_ABI_VERSION,
            "native_version": _native.NATIVE_VERSION,
        },
        "tools": {
            "total": len(schema.tools),
            "mcp_callable": mcp_callable_count,
            "handle_pending": len(handle_pending),
            "by_category": dict(sorted(by_category.items())),
        },
        "handle_pending": sorted(handle_pending),
        "categories": sorted(by_category.keys()),
        # Domain classes (#962 Part 2; capability-first since rc298 `#936`).
        # `names`/`total` are EVERY shipped domain class. `routes` says how each
        # is declared ("toml"/"python") — a field, not an admission criterion.
        # `toml_total` is the TOML-catalog-only count, for the consumers that
        # genuinely want it (srmech.dsl.describe_class only resolves those).
        "classes": {
            "total": len(_class_routes),
            "names": sorted(_class_routes),
            "routes": dict(_class_routes),
            "toml_total": _toml_total,
        },
        # Carriers (rc298 `#936`; capability-tagged rc339 `#T967`) — the operand
        # nouns to `tools`' verbs, each with what it can DO. `capabilities` is
        # keyed by carrier name, so sorted(...) recovers the old name list. Full
        # per-carrier detail via srmech.amsc.carrier_schema.carrier_schema().
        # `domain_word_gap` (rc354, F1336) is a NULL shipped AS a null: a
        # four-word MAGNITUDE / PHASE / ORIENTATION / PATH vocabulary was
        # proposed for picking a carrier by what a domain needs, and the
        # published row DETERMINES it for only 3 of 25. The two words the row
        # can decide are returned; the two it cannot are refused. It rides here
        # rather than in a note because a planner who never opens
        # carrier_schema.py is exactly the reader who would otherwise assume
        # the word is derivable.
        "carriers": {
            "total": len(_carrier_caps),
            "capabilities": _carrier_caps,
            "domain_word_gap": _carrier_domain_gap,
        },
        # Compiled CAPABILITY ceilings (rc298 `#936`; capability-KEYED rc339
        # `#T967`) — what this BUILD supports, with every dimension inside the
        # capability it bounds. No resource/headroom key; see the note above.
        "limits": _limits,
        # C-claim resolution (rc300 `#T938`) — every ``c_dispatched`` op's C
        # symbols checked against the LOADED library. ``consistent`` False means
        # a build defect: ops are running pure while claiming C.
        "c_claims": _c_claims,
        # The LANE axis (rc347 `#T985`) — what each op READS, the complement of
        # `carriers`' what-each-operand-can-DO. Every declaration is verified
        # executably against a sigma flip and an Aut index relabel.
        "lanes": _lanes,
    }


def native_status() -> Dict[str, Any]:
    """One-call native-dispatch status — is ``libsrmech`` loaded, ABI-matched, dispatching?

    The discoverable, recipe-stable answer to "is the C backend active on
    this install?" A bare ``pip install srmech`` ships
    ``libsrmech.{so,dll,dylib}`` inside ``srmech/_native/``; this confirms
    it loaded, ABI-matched the Python shim, and is actually dispatched to
    (vs. the pure-numpy fallback). NB the native shim lives at
    ``srmech.amsc._native`` — NOT ``srmech._native``, which is the data
    directory that merely *holds* the binary. Exposed top-level as
    ``srmech.native_status()`` (and as ``describe()['native']``) so it is
    discoverable from ``dir(srmech)`` — the post-rc18 replacement for the
    old ``_native.HAS_NATIVE`` poke in the TestPyPI-before-PyPI discipline
    (issue #733).

    Returns
    -------
    dict
        ``{"has_native": bool, "dispatching": bool, "abi_version": int|None,
        "expected_abi": int, "native_version": str|None,
        "load_error": str|None}``. ``dispatching`` is True iff the binary
        loaded AND its ABI matched ``EXPECTED_ABI_VERSION`` (native ops
        really run); on mismatch/failure it is False, ``load_error`` carries
        the reason, and srmech transparently uses the pure-Python fallback.
    """
    from ..amsc import _native

    return {
        "has_native": bool(_native.HAS_NATIVE),
        "dispatching": bool(_native.HAS_NATIVE),
        "abi_version": _native.NATIVE_ABI_VERSION,
        "expected_abi": _native.EXPECTED_ABI_VERSION,
        "native_version": _native.NATIVE_VERSION,
        "load_error": None if _native.LOAD_ERROR is None else str(_native.LOAD_ERROR),
    }


__all__ = [
    "Event",
    "INTROSPECT_DIR_NAME",
    "MPR_VERSION_INTROSPECT",
    "Run",
    "_PublishHandle",
    "_maybe_auto_publish",
    "by_pid",
    "describe",
    "describe_shape",
    "emit_if_publishing",
    "introspect_dir",
    "list",
    "native_status",
    "parse",
    "publish",
    "serialize",
]
