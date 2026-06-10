"""Path A vs Path B operation registry — ``srmech.signal_processing``.

Phase 1 scaffolding (v0.4.2rc1) — pairs operation names with their
Path A (closed-form algebra; composes ``srmech.amsc.*`` primitives) and
Path B (RBS-HDC bound-vector at D=8192) implementations. The dispatcher
(see :mod:`srmech.signal_processing.cascade_dispatcher`) reads from this
registry to resolve a given operation invocation.

Per the plan's §3.3 API surface:

    # Default dispatch
    from srmech.signal_processing import fft
    result = fft(signal_bytes)

    # Override
    result_a = fft(signal_bytes, path="A")
    result_b = fft(signal_bytes, path="B")
    result = fft(signal_bytes, path="verify")

The Phase 1 stub registers no operations — Phase 2 (Path A) and Phase 4
(Path B) populate it. The API surface (`register`, `lookup`,
`registered_ops`, `has_path`) is stable from Phase 1 onward.

Discipline anchors:

- 14 A-N intact per ``[[feedback_no_privileged_primitive_classes]]`` —
  every registered op is a *composition* over existing classes, never a
  new class promotion.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]`` — Path A and
  Path B both *instantiate* the same class composition; neither
  implements the framework.
- SSoT discipline per
  ``[[feedback_no_binding_layer_carveout]]`` — Path A composes from
  existing ``srmech.amsc.*`` primitives at module-load time; Path B
  composes from B-native primitives that reference the same Path A
  primitive definitions (no duplicate primitive implementations).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterator, Optional, Tuple

from ._paths import PATH_A, PATH_B, VALID_PATHS

__all__ = [
    "OperationEntry",
    "RegistryError",
    "DuplicateRegistrationError",
    "UnknownOperationError",
    "register",
    "register_lazy_loader",
    "lookup",
    "has_path",
    "registered_ops",
    "clear_registry",
]


# ──────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────


class RegistryError(RuntimeError):
    """Base error for path-registry failures."""


class DuplicateRegistrationError(RegistryError):
    """Raised when re-registering an (op_name, path) pair with a
    different callable. Idempotent re-registration of the same callable
    is silently allowed."""


class UnknownOperationError(RegistryError):
    """Raised when :func:`lookup` is called for an unregistered op."""


# ──────────────────────────────────────────────────────────────────────
# Entry shape
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OperationEntry:
    """One signal-processing operation's (Path A, Path B) pair.

    Phase 1 ships ``path_a`` and ``path_b`` as optional callables; both
    start ``None`` and get populated by Phase 2 (Path A) / Phase 4
    (Path B) module-load side-effects.

    Attributes
    ----------
    op_name:
        Canonical operation name (e.g. ``"fft"``, ``"matched_filter"``).
        Matches the public re-export under ``srmech.signal_processing``.
    path_a:
        Path A implementation (closed-form algebra; composes
        ``srmech.amsc.*`` primitives). ``None`` until Phase 2 lands.
    path_b:
        Path B implementation (RBS-HDC bound-vector at D=8192). ``None``
        until Phase 4 lands.
    ssot_citation:
        Spike #178 §1 citation pointer (free-form string; Phase 2+
        modules populate). Phase 1 leaves empty.
    classes:
        Tuple of 14-class A-N primitive labels this op composes over
        (e.g. ``("A", "I", "K")`` for cyclic FFT per Spike #176). Phase
        1 leaves empty; Phase 2+ populates from Spike #178 §1.
    """

    op_name: str
    path_a: Optional[Callable[..., object]] = None
    path_b: Optional[Callable[..., object]] = None
    ssot_citation: str = ""
    classes: Tuple[str, ...] = field(default_factory=tuple)


# ──────────────────────────────────────────────────────────────────────
# Registry storage (module-level; bounded growth — one entry per op_name)
# ──────────────────────────────────────────────────────────────────────


_REGISTRY: Dict[str, OperationEntry] = {}

#: Lazy registration (rc71): op_name → a loader callable that imports the op's
#: module (which self-registers via its module-load ``_register()``). Ops whose
#: module pulls numpy (e.g. ``matched_filter``) register a loader at the
#: numpy-free ``path_b_ops`` import instead of importing eagerly — so
#: ``import srmech.signal_processing`` stays numpy-free, yet ``lookup`` /
#: ``has_path`` / ``dispatch`` still resolve the op by importing-on-demand.
_LAZY_LOADERS: Dict[str, Callable[[], None]] = {}


def register_lazy_loader(op_name: str, loader: Callable[[], None]) -> None:
    """Register a deferred loader for ``op_name`` (rc71 lazy op-registration).

    ``loader`` imports the op's module on first :func:`lookup` / :func:`has_path`
    of ``op_name`` (the import self-registers the op). Idempotent; a later eager
    self-registration simply makes the loader a no-op."""
    assert isinstance(op_name, str) and op_name, (
        "register_lazy_loader: op_name must be a non-empty string"
    )
    assert callable(loader), "register_lazy_loader: loader must be callable"
    _LAZY_LOADERS[op_name] = loader


def _ensure_loaded(op_name: str) -> None:
    """If ``op_name`` is not yet in ``_REGISTRY`` but has a lazy loader, run it
    (imports + self-registers the op). No-op once loaded."""
    if op_name not in _REGISTRY:
        loader = _LAZY_LOADERS.get(op_name)
        if loader is not None:
            loader()


def register(
    op_name: str,
    *,
    path: str,
    impl: Callable[..., object],
    ssot_citation: str = "",
    classes: Tuple[str, ...] = (),
) -> None:
    """Register an implementation for ``op_name`` under ``path``.

    Idempotent on identical re-registration (same callable identity);
    raises :class:`DuplicateRegistrationError` on a different callable.

    Phase 1 stub: callable storage works; Phase 5+ dispatcher reads
    from here. Phase 1 itself registers no operations.

    Parameters
    ----------
    op_name:
        Canonical operation name.
    path:
        ``"A"`` or ``"B"``. Verification path ``"verify"`` is dispatcher-
        side (runs both A and B); it is never registered as a path here.
    impl:
        Callable implementing the operation on the named path.
    ssot_citation:
        Optional Spike #178 §1 citation pointer (Phase 2+ populates).
    classes:
        Optional 14-class A-N primitive labels this op composes over.
        Empty tuple in Phase 1; populated by Phase 2+ per Spike #178 §1.

    Raises
    ------
    ValueError
        On invalid ``path`` value.
    DuplicateRegistrationError
        On re-registration with a different callable.
    """
    assert isinstance(op_name, str) and op_name, (
        "register: op_name must be non-empty string"
    )
    if path not in (PATH_A, PATH_B):
        raise ValueError(
            f"register: path must be {PATH_A!r} or {PATH_B!r}; got {path!r}. "
            f"Use {VALID_PATHS!r} only on the dispatcher's path= kwarg, not "
            "for registry registration."
        )
    assert callable(impl), f"register: impl must be callable; got {type(impl)}"
    existing = _REGISTRY.get(op_name)
    if existing is None:
        entry = OperationEntry(
            op_name=op_name,
            path_a=impl if path == PATH_A else None,
            path_b=impl if path == PATH_B else None,
            ssot_citation=ssot_citation,
            classes=classes,
        )
        _REGISTRY[op_name] = entry
        return
    # Existing entry — update only the requested path side.
    if path == PATH_A:
        if existing.path_a is not None and existing.path_a is not impl:
            raise DuplicateRegistrationError(
                f"Path A for op {op_name!r} already registered to a "
                f"different callable ({existing.path_a!r}); re-registration "
                f"with {impl!r} would clobber."
            )
        new_entry = OperationEntry(
            op_name=existing.op_name,
            path_a=impl,
            path_b=existing.path_b,
            ssot_citation=existing.ssot_citation or ssot_citation,
            classes=existing.classes or classes,
        )
    else:  # PATH_B
        if existing.path_b is not None and existing.path_b is not impl:
            raise DuplicateRegistrationError(
                f"Path B for op {op_name!r} already registered to a "
                f"different callable ({existing.path_b!r}); re-registration "
                f"with {impl!r} would clobber."
            )
        new_entry = OperationEntry(
            op_name=existing.op_name,
            path_a=existing.path_a,
            path_b=impl,
            ssot_citation=existing.ssot_citation or ssot_citation,
            classes=existing.classes or classes,
        )
    _REGISTRY[op_name] = new_entry


def lookup(op_name: str) -> OperationEntry:
    """Return the :class:`OperationEntry` for ``op_name``.

    Raises :class:`UnknownOperationError` if the op isn't registered.

    Phase 1 stub: no ops are registered; this raises for all callers.
    Phase 2+ populates registrations as modules import.
    """
    assert isinstance(op_name, str) and op_name, (
        "lookup: op_name must be non-empty string"
    )
    _ensure_loaded(op_name)  # rc71: import-on-demand for lazily-registered ops
    entry = _REGISTRY.get(op_name)
    if entry is None:
        raise UnknownOperationError(
            f"signal_processing op {op_name!r} not registered. "
            f"Phase 1 (v0.4.2rc1) scaffolding ships no operations; "
            f"Phase 2+ populates Path A; Phase 4+ populates Path B."
        )
    return entry


def has_path(op_name: str, path: str) -> bool:
    """Return True if ``op_name`` has an implementation registered for
    ``path`` (one of ``"A"`` / ``"B"``)."""
    if path not in (PATH_A, PATH_B):
        raise ValueError(
            f"has_path: path must be {PATH_A!r} or {PATH_B!r}; got {path!r}"
        )
    _ensure_loaded(op_name)  # rc71: import-on-demand for lazily-registered ops
    entry = _REGISTRY.get(op_name)
    if entry is None:
        return False
    if path == PATH_A:
        return entry.path_a is not None
    return entry.path_b is not None


def registered_ops() -> Iterator[str]:
    """Iterate over all known op_names — eagerly-registered first (in
    registration order), then any lazily-registrable ops not yet loaded.

    rc71: declarative — a lazily-registrable op (e.g. ``matched_filter``) is
    listed as a known op without forcing its (numpy-pulling) import. The op
    materialises in ``_REGISTRY`` on first :func:`lookup` / :func:`has_path`."""
    loaded = tuple(_REGISTRY.keys())
    pending = tuple(name for name in _LAZY_LOADERS if name not in _REGISTRY)
    return iter(loaded + pending)


def clear_registry() -> None:
    """Drop every registered entry. Test-isolation utility; not part
    of the public API surface."""
    _REGISTRY.clear()
