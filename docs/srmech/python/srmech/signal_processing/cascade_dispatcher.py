"""Cascade-aware Path A vs Path B dispatcher for ``srmech.signal_processing``.

Phase 1 scaffolding (v0.4.2rc1) — routing API + ``begin_cascade``
context-manager + ``path=`` kwarg semantics. Phase 5 (v0.4.2rc5)
implements full rule-based routing per plan §3.1; Phase 8 lands the
empirical learned-threshold table per plan §3.2.

Per conductor decision #5 (2026-05-19): ``begin_cascade`` API is a
**context-manager** (Pythonic; auto-flush on exception). Phase 1 ships
the context-manager skeleton; the dispatcher honours an active cascade
hint by preferring Path B for nested ops at the same substrate.

Per conductor decision #7 (2026-05-19): dispatch-table lock policy is
**lock-at-release**. Phase 1 ships lock-state tracking; Phase 8
materialises the locked table.

Per conductor decision #6 (2026-05-19): ``D=8192`` is locked as the
v0.4.2 baseline; the dispatcher accepts an optional ``D`` kwarg that
operations forward to their Path B implementations.

Discipline anchors:

- 14 A-N intact — dispatcher routes between *instantiations* of class
  composition; never promotes new classes per
  ``[[feedback_no_privileged_primitive_classes]]``.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]`` — Path A
  and Path B both *instantiate* the same class composition over the
  14 A-N vocabulary; the dispatcher chooses a substrate, never an
  identity.
- Algebra-level not magnitude-level per
  ``[[feedback_algebra_not_magnitude]]`` — ``path="verify"`` mode
  asserts D1 algebra-content identity, never D2 substrate-fingerprint
  equality.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, Optional, Tuple

from ._paths import (
    CASCADE_DEPTH_THRESHOLD_FOR_PATH_B,
    D_DEFAULT,
    DISPATCH_TABLE_LOCK_POLICY,
    PATH_A,
    PATH_B,
    PATH_VERIFY,
    SUBSTRATES,
    VALID_PATHS,
)
from .path_registry import (
    OperationEntry,
    UnknownOperationError,
    has_path,
    lookup,
)

__all__ = [
    "CascadeContext",
    "DispatchError",
    "DispatcherNotImplementedError",
    "begin_cascade",
    "end_cascade",
    "current_cascade",
    "dispatch",
    "resolve_path",
    "is_dispatch_table_locked",
    "lock_dispatch_table",
    "unlock_dispatch_table",
    "DEFAULT_PATH_PER_CLASS",
]


# ──────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────


class DispatchError(RuntimeError):
    """Base error for dispatcher failures."""


class DispatcherNotImplementedError(NotImplementedError):
    """Raised by Phase 1 stubs that defer to Phase 5 / Phase 8.

    Phase 1 ships the API surface; Phase 5 lands rule-based routing;
    Phase 8 lands empirical learned thresholds.
    """


# ──────────────────────────────────────────────────────────────────────
# Default-path-per-class (plan §3.4)
# ──────────────────────────────────────────────────────────────────────

DEFAULT_PATH_PER_CLASS: Dict[str, str] = {
    # Path B defaults (per plan §3.4):
    #   - Class K rotation
    #   - Class M bind/bundle/permute
    #   - A∘C∘M form-function rotation (cascade hint substitutes)
    "K": PATH_B,
    "M": PATH_B,
    # All other classes default to Path A (plan §3.4).
    "A": PATH_A,
    "B": PATH_A,
    "C": PATH_A,
    "D": PATH_A,
    "E": PATH_A,
    "F": PATH_A,
    "G": PATH_A,
    "H": PATH_A,
    "I": PATH_A,
    "J": PATH_A,
    "L": PATH_A,
    "N": PATH_A,
}
"""Default path per 14 A-N primitive class.

Plan §3.4: Path A is the default for all unspecified-path calls except
Class K rotation, Class M bind/bundle/permute, A∘C∘M form-function
rotation, and any call inside a :func:`begin_cascade` context. Path B
is the default for the four exceptions; substrate-portable output
requires Path B regardless.

Phase 1 ships the table; the dispatcher reads it via :func:`resolve_path`
once Phase 5 implements full routing.
"""


# ──────────────────────────────────────────────────────────────────────
# Cascade context (conductor decision #5 — context-manager API)
# ──────────────────────────────────────────────────────────────────────


@dataclass
class CascadeContext:
    """Cascade-context state visible to the dispatcher.

    Per plan §3.3: the ``begin_cascade(substrate=...)`` context-manager
    signals the dispatcher to prefer Path B for nested ops at the same
    substrate (Path B amortises encode overhead over cascade depth).

    Phase 1 ships the state container; Phase 5 wires it into the
    rule-based routing. Phase 1 honours nothing beyond bookkeeping —
    the operations themselves are unimplemented until Phase 2+.

    Attributes
    ----------
    substrate:
        Substrate label (one of
        :data:`srmech.signal_processing._paths.SUBSTRATES`); ``None``
        means substrate-agnostic cascade.
    depth:
        Cascade depth counter; increments on each nested op call,
        decrements on op return. Per plan §3.1 criterion #2, depth ≥
        ``CASCADE_DEPTH_THRESHOLD_FOR_PATH_B`` (default 3) prefers Path B.
    D:
        RBS-HDC bound-vector dimension override; defaults to
        :data:`srmech.signal_processing._paths.D_DEFAULT` (8192).
    closed:
        True after :func:`end_cascade` (or context-manager exit) has
        flushed Path B internal state.
    state:
        Per-cascade scratch dict; Phase 1 leaves empty. Phase 5+ uses
        for accumulating Path B bound-vector handles across ops in the
        same cascade.
    """

    substrate: Optional[str] = None
    depth: int = 0
    D: int = D_DEFAULT
    closed: bool = False
    state: Dict[str, Any] = field(default_factory=dict)


# Thread-local cascade-context stack. Multiple nested begin_cascade
# blocks are supported; the innermost wins for substrate hint.
_CASCADE_STACK: threading.local = threading.local()


def _get_stack() -> list:
    """Return the per-thread cascade-context stack (creating if needed)."""
    stack = getattr(_CASCADE_STACK, "stack", None)
    if stack is None:
        stack = []
        _CASCADE_STACK.stack = stack
    return stack


def current_cascade() -> Optional[CascadeContext]:
    """Return the innermost active :class:`CascadeContext`, or ``None``.

    Used by the dispatcher (Phase 5+) to detect cascade-hint mode.
    """
    stack = _get_stack()
    if not stack:
        return None
    return stack[-1]


@contextmanager
def begin_cascade(
    substrate: Optional[str] = None,
    *,
    D: int = D_DEFAULT,
) -> Iterator[CascadeContext]:
    """Open a cascade context — prefer Path B for nested ops.

    Per conductor decision #5 (2026-05-19): context-manager API (Pythonic;
    auto-flush on exception). The ``end_cascade`` function is exposed for
    explicit-API users who prefer the imperative form, but the
    context-manager is the recommended surface.

    Per plan §3.3 example::

        from srmech.signal_processing import fft, sign_quantise, matched_filter
        from srmech.signal_processing import begin_cascade

        with begin_cascade(substrate="bci"):
            spectrum = fft(signal_bytes)
            thresholded = sign_quantise(spectrum)
            detected = matched_filter(thresholded, template_bytes)
        # End of cascade flushes Path B internal state.

    Parameters
    ----------
    substrate:
        Substrate label (one of
        :data:`srmech.signal_processing._paths.SUBSTRATES`); ``None``
        means substrate-agnostic cascade. Phase 1 validates only that
        non-None values are in the known set.
    D:
        RBS-HDC bound-vector dimension; defaults to 8192 per conductor
        decision #6.

    Yields
    ------
    CascadeContext
        The opened context; safe to inspect but not directly mutated
        by callers.

    Raises
    ------
    ValueError
        If ``substrate`` is not None and not in
        :data:`srmech.signal_processing._paths.SUBSTRATES`.
    """
    if substrate is not None and substrate not in SUBSTRATES:
        raise ValueError(
            f"begin_cascade: substrate must be None or one of "
            f"{SUBSTRATES!r}; got {substrate!r}"
        )
    if D <= 0:
        raise ValueError(f"begin_cascade: D must be positive; got {D}")
    ctx = CascadeContext(substrate=substrate, depth=0, D=D)
    stack = _get_stack()
    stack.append(ctx)
    try:
        yield ctx
    finally:
        # Auto-flush on normal exit *and* exception. Phase 1: bookkeeping
        # only; Phase 5+ flushes Path B accumulated bound-vector handles
        # via the dispatcher.
        _flush_cascade(ctx)
        # Pop only if the top of the stack is still our context (defensive
        # against misuse where a caller calls end_cascade manually
        # inside the with-block).
        if stack and stack[-1] is ctx:
            stack.pop()


def end_cascade(ctx: Optional[CascadeContext] = None) -> None:
    """Imperative-form cascade flush.

    Per plan §3.3: ``end_cascade()`` flushes Path B internal state.
    Equivalent to exiting a ``with begin_cascade(...)`` block. Use the
    context-manager form when possible; this exists for callers that
    can't structure their code around a ``with`` block.

    Parameters
    ----------
    ctx:
        Specific cascade context to flush. If ``None``, flushes the
        innermost active context. No-op if no cascade is active.
    """
    stack = _get_stack()
    if not stack:
        return
    target = ctx if ctx is not None else stack[-1]
    _flush_cascade(target)
    # Remove from stack if present (defensive — preserves stack
    # ordering otherwise).
    for i in range(len(stack) - 1, -1, -1):
        if stack[i] is target:
            stack.pop(i)
            break


def _flush_cascade(ctx: CascadeContext) -> None:
    """Mark a :class:`CascadeContext` as closed.

    Phase 1 stub: sets ``closed = True``. Phase 5+ wires in Path B
    internal-state flush (accumulated bound-vector handles).
    """
    if not ctx.closed:
        ctx.closed = True
        # Phase 5+ TODO: flush Path B internal state from ctx.state
        # (currently empty).


# ──────────────────────────────────────────────────────────────────────
# Path resolution (Phase 5 implements full routing; Phase 1 stub)
# ──────────────────────────────────────────────────────────────────────


def resolve_path(
    op_name: str,
    *,
    explicit_path: Optional[str] = None,
    input_size: Optional[int] = None,
    substrate: Optional[str] = None,
) -> str:
    """Resolve the path (``"A"`` / ``"B"`` / ``"verify"``) for one
    operation invocation.

    Phase 1 routing logic (rule-based; first cut per plan §3.1):

    1. If ``explicit_path`` is given, honour it unconditionally
       (per plan §3.4 — override always honoured).
    2. If a :func:`begin_cascade` context is active, prefer Path B
       (per plan §3.1 criterion #2).
    3. Otherwise, look up the op's primary class (Phase 2+ populates
       this on registration) and route per
       :data:`DEFAULT_PATH_PER_CLASS`.
    4. Phase 1 fallback: default to Path A for any op whose primary
       class is unknown (Phase 1 ships no registered ops).

    Phase 8 (v0.4.2rc8) replaces this with learned thresholds from the
    benchmark suite per plan §3.2.

    Parameters
    ----------
    op_name:
        Canonical operation name (must exist in
        :mod:`srmech.signal_processing.path_registry`).
    explicit_path:
        Caller-supplied ``path=`` kwarg; if not ``None`` overrides
        all other routing rules. Must be one of
        :data:`srmech.signal_processing._paths.VALID_PATHS`.
    input_size:
        Optional input size hint (Phase 8 learned thresholds will use).
    substrate:
        Optional substrate hint (overrides the active cascade context
        if any).

    Returns
    -------
    str
        One of ``"A"`` / ``"B"`` / ``"verify"``.

    Raises
    ------
    ValueError
        If ``explicit_path`` is not in :data:`VALID_PATHS`.
    """
    if explicit_path is not None:
        if explicit_path not in VALID_PATHS:
            raise ValueError(
                f"resolve_path: explicit_path must be one of {VALID_PATHS!r}; "
                f"got {explicit_path!r}"
            )
        return explicit_path
    cascade = current_cascade()
    if cascade is not None and not cascade.closed:
        return PATH_B
    # Phase 1 stub: any unregistered op defaults to Path A; the
    # `lookup` raises UnknownOperationError which we catch and treat
    # as "no class info available".
    try:
        entry = lookup(op_name)
    except UnknownOperationError:
        return PATH_A
    if entry.classes:
        # Use first class as primary; Phase 5 may add weighted
        # multi-class logic per the §2 hypothesis table.
        primary = entry.classes[0]
        return DEFAULT_PATH_PER_CLASS.get(primary, PATH_A)
    return PATH_A


def dispatch(
    op_name: str,
    *args: Any,
    path: Optional[str] = None,
    D: int = D_DEFAULT,
    **kwargs: Any,
) -> Any:
    """Dispatch one operation invocation.

    Phase 1 stub: looks up the op in :mod:`path_registry`, resolves the
    path via :func:`resolve_path`, and invokes the registered callable
    with the locked-default ``D=8192`` (or the caller's override).

    Phase 1 itself ships no registered ops, so this always raises
    :class:`srmech.signal_processing.path_registry.UnknownOperationError`
    until Phase 2 populates the registry. The API is stable from
    Phase 1.

    Parameters
    ----------
    op_name:
        Canonical operation name.
    *args:
        Positional arguments forwarded to the operation.
    path:
        Optional explicit path override (``"A"`` / ``"B"`` / ``"verify"``);
        bypasses rule-based routing.
    D:
        RBS-HDC bound-vector dimension; defaults to 8192 per conductor
        decision #6. Forwarded to Path B implementations.
    **kwargs:
        Keyword arguments forwarded to the operation.

    Returns
    -------
    Any
        The operation's return value.

    Raises
    ------
    srmech.signal_processing.path_registry.UnknownOperationError
        If ``op_name`` isn't registered.
    DispatcherNotImplementedError
        If ``path="verify"`` is requested in Phase 1 (algebra-check
        primitives land in Phase 4+ tests).
    """
    chosen = resolve_path(op_name, explicit_path=path)
    entry = lookup(op_name)
    if chosen == PATH_VERIFY:
        # Phase 1: verify-mode needs both paths registered + the
        # algebra-check canonicaliser (Phase 4 tests + per-op
        # canonicalisers). Defer with a structured stub.
        raise DispatcherNotImplementedError(
            "path='verify' lands in Phase 5 (v0.4.2rc5) per plan §6.5. "
            "Phase 1 stub does not run dual-path with D1 equivalence "
            f"check. (op_name={op_name!r})"
        )
    if chosen == PATH_A:
        if entry.path_a is None:
            raise DispatchError(
                f"op {op_name!r} has no Path A implementation registered. "
                f"Phase 2 (v0.4.2rc2) populates Path A; Phase 1 is "
                "scaffolding only."
            )
        # Inject D only if the underlying callable accepts it; Phase 5+
        # adds signature-introspection. Phase 1 forwards D and lets
        # the callee ignore if irrelevant.
        return entry.path_a(*args, D=D, **kwargs) if _accepts_D(entry.path_a) \
            else entry.path_a(*args, **kwargs)
    # chosen == PATH_B
    if entry.path_b is None:
        raise DispatchError(
            f"op {op_name!r} has no Path B implementation registered. "
            f"Phase 4 (v0.4.2rc4) populates Path B; Phase 1 is "
            "scaffolding only."
        )
    return entry.path_b(*args, D=D, **kwargs) if _accepts_D(entry.path_b) \
        else entry.path_b(*args, **kwargs)


def _accepts_D(fn: Callable[..., Any]) -> bool:
    """Return True if ``fn`` accepts a keyword ``D`` parameter.

    Phase 1 utility: lightweight signature check so the dispatcher can
    forward ``D=8192`` (the locked default) only to ops that take it,
    without forcing every Path A op to accept-and-ignore the kwarg.
    """
    try:
        import inspect
        sig = inspect.signature(fn)
        return "D" in sig.parameters or any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
    except (ValueError, TypeError):  # pragma: no cover (builtins / C extensions)
        return False


# ──────────────────────────────────────────────────────────────────────
# Dispatch-table lock state (conductor decision #7 — lock-at-release)
# ──────────────────────────────────────────────────────────────────────


_LOCK_STATE: Dict[str, Any] = {
    "locked": True,  # Phase 1: defaults to locked per lock-at-release policy
    "policy": DISPATCH_TABLE_LOCK_POLICY,
    "phase": "phase-1-scaffolding",
}


def is_dispatch_table_locked() -> bool:
    """Return True if the learned dispatch table is locked.

    Per conductor decision #7 (2026-05-19): lock-at-release policy —
    each ``v0.4.2rc{N}`` ship locks a specific dispatch table for
    reproducibility. Phase 1 defaults to locked (no learned table
    exists yet to override).
    """
    return bool(_LOCK_STATE["locked"])


def lock_dispatch_table() -> None:
    """Re-lock the dispatch table.

    Phase 1 utility; Phase 8 calls after materialising the locked
    ``_learned_dispatch_table.ndjson``.
    """
    _LOCK_STATE["locked"] = True


def unlock_dispatch_table() -> None:
    """Unlock the dispatch table (for local override per plan §3.5).

    Users wanting different thresholds may unlock, rerun
    :func:`srmech.signal_processing.profiling.update_dispatch_table`
    on their own machine, and ship a local override. Per plan §3.5
    this does NOT pollute the package's locked table — that's a
    Phase 8 invariant.
    """
    _LOCK_STATE["locked"] = False
