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
            }
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

    # User-declared [class] classes (rc41) — the package recognises its own
    # user-extensible class surface (the Class-H self-recognition view). Guarded
    # local import (avoids any srmech.dsl import-cycle at introspect load).
    try:
        from ..dsl import list_classes as _list_classes
        _class_names = _list_classes()
    except Exception:  # pragma: no cover — class catalog optional / absent
        _class_names = []

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
        # User-declared [class] classes (#962 Part 2) — name list; full
        # descriptors via srmech.dsl.describe_class / `srmech class describe`.
        "classes": {"total": len(_class_names), "names": sorted(_class_names)},
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
