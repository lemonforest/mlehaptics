"""TOML cascade-catalog runtime loader for the DSL runner.

Reads the 8 TOML descriptors under
``srmech/amsc/_research/cascade_catalog/`` and resolves each op-name to
its canonical :mod:`srmech.amsc.cascade` Python entry point (which itself
routes to a C peer when ``HAS_NATIVE`` is True).

The catalog file IS the SSoT for which cascade ops exist — the DSL
runner does not maintain its own hard-coded list of names. ``chain()
.then("foo")`` is rejected for any ``foo`` not declared in a descriptor.

The descriptors carry ``[cascade].name`` (the canonical op name) plus
optional ``[cascade.native]`` C symbol names + ``[cascade.delegates_to]``
metadata. The DSL runner consults the *name* only — the Python entry
point in :mod:`srmech.amsc.cascade` handles the C-dispatch routing
internally, so the DSL doesn't reach into that machinery.

Framework reading: this loader is Class E (catalog enumeration) ∘
Class F (template-style descriptor render) composed against the on-disk
descriptor set. The cache-once-then-reuse pattern (via
:func:`functools.lru_cache`) mirrors the existing
:mod:`srmech.amsc.tool_schema` discipline.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List

# tomllib is stdlib on 3.11+; tomli is the back-port for 3.10. Mirror
# the same fallback pattern used elsewhere in srmech.
if sys.version_info >= (3, 11):
    import tomllib as _toml
else:  # pragma: no cover — 3.10-only branch
    import tomli as _toml  # type: ignore[no-redef]

#: On-disk directory housing the cascade-catalog TOML descriptors.
#: Resolved relative to ``srmech.dsl._catalog`` so editable installs
#: and wheel installs both work.
CATALOG_DIR: Path = (
    Path(__file__).parent.parent / "amsc" / "_research" / "cascade_catalog"
)


@lru_cache(maxsize=1)
def load_catalog() -> Dict[str, Dict[str, Any]]:
    """Load all cascade-catalog TOML descriptors.

    Returns
    -------
    dict[str, dict]
        Mapping ``op_name -> parsed-descriptor-dict``. Cached after
        the first call; the descriptor set is fixed at package-import
        time (TOML files don't appear/disappear at runtime).

    Raises
    ------
    FileNotFoundError
        If the catalog directory is missing entirely (a corrupt /
        partial install — the descriptors ship with the wheel).
    ValueError
        If a descriptor lacks the required ``[cascade].name`` field.
    """
    if not CATALOG_DIR.exists() or not CATALOG_DIR.is_dir():
        raise FileNotFoundError(
            f"cascade-catalog directory not found at {CATALOG_DIR}; "
            f"srmech install appears incomplete"
        )
    catalog: Dict[str, Dict[str, Any]] = {}
    for toml_path in sorted(CATALOG_DIR.glob("*.toml")):
        with open(toml_path, "rb") as fh:
            desc = _toml.load(fh)
        cascade_section = desc.get("cascade")
        if not isinstance(cascade_section, dict):
            raise ValueError(
                f"cascade-catalog descriptor {toml_path.name} is missing "
                f"the required [cascade] section"
            )
        op_name = cascade_section.get("name")
        if not isinstance(op_name, str) or not op_name:
            raise ValueError(
                f"cascade-catalog descriptor {toml_path.name} is missing "
                f"the required [cascade].name field"
            )
        catalog[op_name] = desc
    return catalog


def lookup_cascade_op(op_name: str) -> Callable:
    """Resolve ``op_name`` to its Python entry point in :mod:`srmech.amsc.cascade`.

    The descriptor declares the canonical name; the cascade module
    exposes a Python callable of the same name (which routes through
    a C peer when ``HAS_NATIVE`` is True). This indirection keeps the
    DSL agnostic to the C-dispatch surface — the DSL only sees the
    Python callable.

    Parameters
    ----------
    op_name
        The canonical cascade op-name (as listed in the descriptor).

    Returns
    -------
    callable
        The resolved cascade op (a ``srmech.amsc.cascade`` callable).

    Raises
    ------
    ValueError
        If ``op_name`` is not present in any catalog descriptor.
    RuntimeError
        If the descriptor exists but :mod:`srmech.amsc.cascade` does
        not expose a matching Python callable (an install integrity
        failure).
    """
    # Local import to avoid an import cycle at module-load time —
    # srmech.amsc.cascade imports srmech.introspect which imports
    # srmech.dsl in some test configurations.
    from srmech.amsc import cascade as _cascade

    catalog = load_catalog()
    if op_name not in catalog:
        raise ValueError(
            f"unknown cascade op {op_name!r}; "
            f"catalog: {sorted(catalog)}"
        )
    fn = getattr(_cascade, op_name, None)
    if fn is None or not callable(fn):
        raise RuntimeError(
            f"cascade-catalog has descriptor for {op_name!r} but "
            f"srmech.amsc.cascade does not expose a matching callable "
            f"(install integrity failure)"
        )
    return fn


def list_cascade_ops() -> List[str]:
    """Return all op-names declared in the cascade catalog.

    Returns
    -------
    list[str]
        Sorted ascending. The list is consumed by :func:`srmech.cli.dsl.ops`
        (the ``srmech dsl ops`` subcommand) and by the test-suite's
        descriptor-coverage check.
    """
    return sorted(load_catalog())


def cascade_op_kind(op_name: str) -> str:
    """Return the DSL role of ``op_name`` — ``"stage"`` or ``"combinator"``.

    Read from the descriptor's optional ``[cascade].kind`` field; absent
    means ``"stage"`` (the default — a plain unary ``value → value`` op
    usable as an ``op=`` chain stage). ``"combinator"`` marks a
    higher-order special form (``parallel_sector_dispatch`` — a 1→N
    fan-out that takes a *body* op + data) that is NOT a plain ``op``
    stage and must be driven by its own discriminator (the ``parallel``
    stage / :meth:`srmech.dsl.Chain.parallel_sectors`). The chain builder
    consults this to reject a combinator used as ``op=`` with a guided
    error instead of a raw ``TypeError`` (v0.6.0rc11).

    Returns ``"stage"`` for an unknown name (the caller's own resolution
    via :func:`lookup_cascade_op` raises the authoritative "unknown op"
    error; this helper does not duplicate that gate).
    """
    catalog = load_catalog()
    desc = catalog.get(op_name)
    if not isinstance(desc, dict):
        return "stage"
    kind = desc.get("cascade", {}).get("kind", "stage")
    return kind if isinstance(kind, str) and kind else "stage"


def get_descriptor(op_name: str) -> Dict[str, Any]:
    """Return the raw TOML descriptor for ``op_name``.

    Used by ``srmech dsl visualize`` (per-stage descriptor render) and
    by tests inspecting the ``class_composition`` / ``delegates_to``
    metadata. Returns a deep-copy-safe view (the dict is mutable;
    callers should treat it as read-only).
    """
    catalog = load_catalog()
    if op_name not in catalog:
        raise ValueError(
            f"unknown cascade op {op_name!r}; "
            f"catalog: {sorted(catalog)}"
        )
    return catalog[op_name]


__all__ = [
    "CATALOG_DIR",
    "load_catalog",
    "lookup_cascade_op",
    "list_cascade_ops",
    "cascade_op_kind",
    "get_descriptor",
]
