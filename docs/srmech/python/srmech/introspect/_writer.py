"""Thread-safe NDJSON writer for srmech.introspect.

Owns the open-file handle and the per-process emit lock. A single
:class:`Writer` is alive at most once per process (the module-global
``_ACTIVE_WRITER`` slot enforces this). Re-entering :func:`publish`
while already active is a no-op (returns the same writer).

Design notes:

* The writer is allocated lazily by :func:`publish` — importing
  ``srmech.introspect`` does NOT create any file.
* Append-binary mode (``'ab'``) + a single :class:`threading.Lock`
  around each write protects against interleaved-line corruption
  from multi-threaded emit sites.
* ``flush()`` is called after every emit so an externally-tailing
  ``Run.follow()`` (another process) sees lines as they land, not
  only at process exit.
* On process exit the writer attempts to emit a final
  ``session_end`` event via an :mod:`atexit` hook. The hook is
  best-effort — interpreter shutdown ordering is not guaranteed so
  failures are swallowed.
* JPL Rule 5 (≥2 asserts per non-exempt function) is non-binding
  here — this is Python, not the C library — but defensive
  invariants are still asserted via runtime checks.
"""

from __future__ import annotations

import atexit
import datetime as _dt
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from . import _event
from ._event import (
    INTROSPECT_DIR_NAME,
    MPR_VERSION_INTROSPECT,
    Event,
    serialize,
)

# Module-global single-writer slot. Re-entering publish() returns the
# same writer (no-op nested behaviour). ``_ACTIVE_LOCK`` guards
# transitions between ``None`` / ``Writer`` — distinct from the
# per-writer ``_emit_lock`` that guards the file-append itself.
_ACTIVE_WRITER: "Optional[Writer]" = None
_ACTIVE_LOCK = threading.Lock()

# Thread-local "publishing" flag. The emit hooks check this FIRST and
# bail immediately when False — zero overhead in the off-path. The
# flag is set on the publishing thread by ``Writer.enter()`` and
# inherited by background threads only by explicit opt-in (the
# auto-publish env-var path activates module-globally; see
# ``_maybe_auto_publish``).
_PUBLISHING_TLS = threading.local()


def _is_publishing() -> bool:
    """Cheap thread-local check: is *this thread* inside a publish
    context? Used by every emit hook as the first branch."""
    # Fast path: attribute is missing on threads that never published.
    return getattr(_PUBLISHING_TLS, "active", False)


def _set_publishing(active: bool) -> None:
    """Toggle the thread-local publishing flag for the current thread."""
    _PUBLISHING_TLS.active = bool(active)


def _utc_iso8601_now() -> str:
    """UTC ISO-8601 timestamp with microsecond resolution + Z suffix.

    Used as the ``started_ts`` / ``finished_ts`` event fields. Format
    matches the canonical srmech attestation timestamp convention
    (see ``srmech.amsc.adapters._base.attest``).
    """
    return (
        _dt.datetime.now(_dt.timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )


def introspect_dir() -> Path:
    """Resolve ``~/.srmech/`` (the on-disk status-file root).

    Lazily creates the directory; idempotent. ``Path.home()`` raises
    ``RuntimeError`` on platforms where ``HOME`` is unset — that's
    fine, callers catch and degrade.
    """
    return Path.home() / INTROSPECT_DIR_NAME


class Writer:
    """One status file's lifecycle.

    Methods are explicit (``enter`` / ``exit`` / ``emit``) rather than
    a context-protocol implementation so that the env-var auto-publish
    path can drive a writer without ``with`` syntax.
    """

    def __init__(self) -> None:
        from srmech.version import __version__ as _srmech_version
        self._pid: int = os.getpid()
        self._start_time_ns: int = time.time_ns()
        self._srmech_version: str = str(_srmech_version)
        # sys.argv may be empty (embedded interpreter); use a sentinel.
        argv = sys.argv if sys.argv else [""]
        self._script_name: str = os.path.basename(argv[0]) or "<embedded>"
        self._path: Path = (
            introspect_dir()
            / f"run-{self._pid}-{self._start_time_ns}.ndjson"
        )
        # File handle + per-writer append lock.
        self._fh = None  # type: ignore[assignment]
        self._emit_lock = threading.Lock()
        self._event_count: int = 0
        self._entered: bool = False
        self._exited: bool = False
        self._atexit_registered: bool = False
        # remove-on-exit flag; default leave-for-list-to-cleanup
        # (matches the spec: "default: leave for list() to auto-clean
        # stale"). Tests can flip to True for tighter teardown.
        self._remove_on_exit: bool = False

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def start_time_ns(self) -> int:
        return self._start_time_ns

    @property
    def file_path(self) -> Path:
        return self._path

    def _attestation(self) -> Dict[str, Any]:
        """Static attestation block — identical across every event.

        Re-uses the canonical srmech MPR attestation shape (see
        ``srmech.amsc.adapters._base.attest``) but with the
        introspection-specific keys (pid, start_time_ns).
        """
        return {
            "pid": self._pid,
            "start_time_ns": self._start_time_ns,
            "srmech_version": self._srmech_version,
        }

    def enter(self) -> None:
        """Open the status file and emit ``session_start``.

        Idempotent — repeated ``enter()`` on the same writer is a
        no-op (returns immediately). The directory is created lazily.
        """
        if self._entered:
            return
        self._entered = True
        # Lazy-create the directory.
        try:
            introspect_dir().mkdir(parents=True, exist_ok=True)
        except OSError:
            # Degrade silently — introspection is OPT-IN, never load-
            # bearing for the host process' work.
            self._entered = False
            return
        try:
            # 'ab' (append-binary, unbuffered at the OS level — Python
            # buffers internally but we flush() after each write).
            self._fh = open(self._path, "ab")  # noqa: SIM115
        except OSError:
            self._entered = False
            return
        # Register the at-exit hook so a crashing publishing process
        # still gets a best-effort session_end emit + cleanup. Only
        # register ONCE per writer (idempotent across nested enter()
        # calls).
        if not self._atexit_registered:
            atexit.register(self._atexit_cleanup)
            self._atexit_registered = True
        # session_start event captures the script_name + version.
        self._emit_raw(
            op_name="session_start",
            class_="",
            input_shape="",
            output_shape=None,
            error=None,
            extra={
                "script_name": self._script_name,
            },
        )
        _set_publishing(True)

    def exit(self, *, error: Optional[BaseException] = None) -> None:
        """Emit ``session_end`` and close the file.

        If ``error`` is supplied, the session_end event carries it
        (the status becomes ``"died"`` for downstream consumers).
        Idempotent — repeated ``exit()`` is a no-op.
        """
        if not self._entered or self._exited:
            return
        self._exited = True
        _set_publishing(False)
        try:
            self._emit_raw(
                op_name="session_end",
                class_="",
                input_shape="",
                output_shape=None,
                error=(
                    None if error is None
                    else f"{type(error).__name__}: {error}"
                ),
                extra={"event_count": self._event_count},
            )
        except Exception:
            pass
        try:
            if self._fh is not None:
                self._fh.close()
        except Exception:
            pass
        finally:
            self._fh = None
        if self._remove_on_exit:
            try:
                self._path.unlink(missing_ok=True)
            except OSError:
                pass

    def _atexit_cleanup(self) -> None:
        """At-exit hook — best-effort session_end emit."""
        try:
            if self._entered and not self._exited:
                self.exit()
        except Exception:
            pass

    def emit(
        self,
        op_name: str,
        *,
        class_: str = "",
        input_shape: str = "",
        output_shape: Optional[str] = None,
        error: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit one event. Thread-safe.

        No-op if the writer isn't entered (defensive — shouldn't
        happen since the public ``emit_if_publishing`` hooks gate on
        the TLS flag first).
        """
        if not self._entered or self._fh is None:
            return
        self._emit_raw(
            op_name=op_name,
            class_=class_,
            input_shape=input_shape,
            output_shape=output_shape,
            error=error,
            extra=extra or {},
        )

    def _emit_raw(
        self,
        *,
        op_name: str,
        class_: str,
        input_shape: str,
        output_shape: Optional[str],
        error: Optional[str],
        extra: Dict[str, Any],
    ) -> None:
        """Build + write one event under the per-writer lock."""
        event = Event(
            mpr_version=MPR_VERSION_INTROSPECT,
            op_name=op_name,
            class_=class_,
            started_ts=_utc_iso8601_now(),
            finished_ts=None,
            input_shape=input_shape,
            output_shape=output_shape,
            error=error,
            attestation=self._attestation(),
            extra=dict(extra),
        )
        line = serialize(event)
        with self._emit_lock:
            try:
                if self._fh is not None:
                    self._fh.write(line)
                    self._fh.flush()
                    self._event_count += 1
            except OSError:
                # Disk full / permission flip mid-run — degrade.
                pass


# ─────────────────────────────────────────────────────────────────────
# Module-level enter/exit + the emit hook used by the cascade /
# AMSC / signal_processing wiring.
# ─────────────────────────────────────────────────────────────────────


def get_active_writer() -> Optional[Writer]:
    """Return the active writer for this process, or ``None``."""
    return _ACTIVE_WRITER


def _activate_writer() -> Writer:
    """Create + enter a writer, or return the already-active one.

    Used by both :func:`publish` (the ctxmgr) and
    :func:`_maybe_auto_publish` (the env-var path).
    """
    global _ACTIVE_WRITER
    with _ACTIVE_LOCK:
        if _ACTIVE_WRITER is not None:
            return _ACTIVE_WRITER
        w = Writer()
        w.enter()
        _ACTIVE_WRITER = w
    return _ACTIVE_WRITER


def _deactivate_writer(error: Optional[BaseException] = None) -> None:
    """Close + clear the active writer (if any)."""
    global _ACTIVE_WRITER
    with _ACTIVE_LOCK:
        w = _ACTIVE_WRITER
        _ACTIVE_WRITER = None
    if w is not None:
        w.exit(error=error)


def emit_if_publishing(
    op_name: str,
    *,
    class_: str = "",
    input_shape: str = "",
    output_shape: Optional[str] = None,
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """The single emit-site primitive used by the cascade / AMSC /
    signal-processing wiring.

    First branch is the thread-local TLS check — if not publishing,
    this returns IMMEDIATELY with zero allocation. The defaults
    avoid temp dicts on the fast path; ``extra`` is only constructed
    by callers that actually pass it.

    Per spec: "this must be a no-op when not publishing — zero
    overhead, zero allocations. Check the thread-local flag first;
    bail immediately if false."
    """
    if not _is_publishing():
        return
    w = _ACTIVE_WRITER
    if w is None:
        return
    w.emit(
        op_name,
        class_=class_,
        input_shape=input_shape,
        output_shape=output_shape,
        error=error,
        extra=extra,
    )


__all__ = [
    "Writer",
    "_activate_writer",
    "_deactivate_writer",
    "_is_publishing",
    "_set_publishing",
    "_utc_iso8601_now",
    "emit_if_publishing",
    "get_active_writer",
    "introspect_dir",
]
