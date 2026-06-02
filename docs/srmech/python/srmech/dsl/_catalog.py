"""TOML cascade-catalog runtime loader for the DSL runner.

Reads the packaged TOML descriptors under
``srmech/amsc/_research/cascade_catalog/`` — PLUS any external dirs a user
registers via ``SRMECH_CASCADE_PATH`` / :func:`register_catalog_dir` (the
bring-your-own cascade-TOML surface, F289 D2) — and resolves each op-name to
its Python entry point: a shipped :mod:`srmech.amsc.cascade` callable (routes
to a C peer when ``HAS_NATIVE``), or, for a user ``[composite]`` descriptor, a
unary stage that runs its pure-TOML sub-chain (no Python required).

The catalog IS the SSoT for which cascade ops exist — the DSL runner keeps no
hard-coded name list. ``chain().then("foo")`` is rejected for any ``foo`` not
declared in a descriptor. User descriptors are B-tier (``provenance="user"``,
attested to their own descriptor hash) and may NOT shadow a shipped A-tier
op-name (that raises at load).

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

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

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

#: Provenance tier for the shipped (packaged) catalog — A-tier, attested to
#: srmech's verified ground-proof. User dirs are B-tier ("user:<sha256>").
_PROVENANCE_SHIPPED = "srmech"

#: External cascade-catalog dirs registered at runtime via
#: :func:`register_catalog_dir`. The ``SRMECH_CASCADE_PATH`` env-var is the
#: zero-API equivalent (read fresh on each (re)load). Bring-your-own; F289 D2.
_USER_CATALOG_DIRS: List[Path] = []

#: Stage-dict keys that name a referenced cascade op (for composite validation).
_COMPOSITE_OP_KEYS = ("op", "fold_op", "reduce_op", "parallel_body")


def _env_catalog_dirs() -> List[Path]:
    """External catalog dirs from ``SRMECH_CASCADE_PATH`` (os.pathsep list)."""
    raw = os.environ.get("SRMECH_CASCADE_PATH", "")
    return [Path(p) for p in raw.split(os.pathsep) if p.strip()]


def _user_catalog_dirs() -> List[Path]:
    """Active external dirs: env-var first, then :func:`register_catalog_dir`."""
    dirs: List[Path] = []
    for p in _env_catalog_dirs() + _USER_CATALOG_DIRS:
        if p not in dirs:
            dirs.append(p)
    return dirs


def register_catalog_dir(path: Any) -> None:
    """Register an external cascade-catalog directory (bring-your-own; F289 D2).

    A domain specialist drops their own ``*.toml`` cascade descriptors in
    ``path`` and registers it; the ops then resolve, run, and surface (in
    :func:`list_cascade_ops` / ``srmech dsl ops`` / the LLM tool surface)
    identically to shipped ops — flagged ``provenance="user"`` (B-tier: attested
    to the user's descriptor hash, NOT an A-tier srmech primitive). The
    ``SRMECH_CASCADE_PATH`` env-var (os.pathsep-separated dirs) is the zero-API
    equivalent. A user descriptor may be a PURE-TOML **composite** (a
    ``[composite]`` body whose ``[[composite.stage]]`` array is a chain of named
    ops — no Python) or a primitive (needs a matching ``srmech.amsc.cascade``
    callable). A user op-name may NOT shadow a shipped one.
    """
    p = Path(path)
    assert p.exists() and p.is_dir(), (
        f"register_catalog_dir: not an existing directory: {p}"
    )
    if p not in _USER_CATALOG_DIRS:
        _USER_CATALOG_DIRS.append(p)
    load_catalog.cache_clear()


@lru_cache(maxsize=1)
def load_catalog() -> Dict[str, Dict[str, Any]]:
    """Load all cascade-catalog TOML descriptors (packaged + user-registered).

    Merges the packaged catalog (A-tier) with any external dirs from
    ``SRMECH_CASCADE_PATH`` + :func:`register_catalog_dir` (B-tier; F289 D2).
    Each descriptor is tagged with ``_provenance`` (``"srmech"`` /
    ``"user:<sha256>"``) and ``_source`` (path). Cached; the cache is cleared by
    :func:`register_catalog_dir`.

    Returns
    -------
    dict[str, dict]
        Mapping ``op_name -> parsed-descriptor-dict``.

    Raises
    ------
    FileNotFoundError
        If the packaged catalog dir, or a registered user dir, is missing.
    ValueError
        On a missing ``[cascade].name``, a user op-name that shadows a shipped
        or earlier op, or a composite body that references an unknown op /
        forms a cycle (validated loudly here, not silently at run).
    """
    if not CATALOG_DIR.exists() or not CATALOG_DIR.is_dir():
        raise FileNotFoundError(
            f"cascade-catalog directory not found at {CATALOG_DIR}; "
            f"srmech install appears incomplete"
        )
    catalog: Dict[str, Dict[str, Any]] = {}
    sources: List[Tuple[Path, str]] = [(CATALOG_DIR, _PROVENANCE_SHIPPED)]
    sources += [(d, "user") for d in _user_catalog_dirs()]
    for base, tier in sources:
        if not base.exists() or not base.is_dir():
            raise FileNotFoundError(
                f"registered cascade-catalog directory not found: {base}"
            )
        for toml_path in sorted(base.glob("*.toml")):
            raw = toml_path.read_bytes()
            desc = _toml.loads(raw.decode("utf-8"))
            cascade_section = desc.get("cascade")
            if not isinstance(cascade_section, dict):
                raise ValueError(
                    f"cascade-catalog descriptor {toml_path} is missing "
                    f"the required [cascade] section"
                )
            op_name = cascade_section.get("name")
            if not isinstance(op_name, str) or not op_name:
                raise ValueError(
                    f"cascade-catalog descriptor {toml_path} is missing "
                    f"the required [cascade].name field"
                )
            if op_name in catalog:
                raise ValueError(
                    f"cascade op-name conflict: {op_name!r} in {toml_path} is "
                    f"already defined by {catalog[op_name]['_source']}; user "
                    f"descriptors may not shadow shipped or earlier op-names"
                )
            if tier == _PROVENANCE_SHIPPED:
                desc["_provenance"] = _PROVENANCE_SHIPPED
            else:
                # Route the hash through the native-dispatching sha256_bytes
                # (no direct hashlib.sha256 — Phase B5 discipline).
                from srmech.amsc.format import sha256_bytes
                desc["_provenance"] = f"user:{sha256_bytes(raw)}"
            desc["_source"] = str(toml_path)
            catalog[op_name] = desc
    # Second pass: validate composite bodies against the full catalog (every
    # referenced op resolves; the composite graph is acyclic — fail loud here).
    for name, desc in catalog.items():
        if isinstance(desc.get("composite"), dict):
            _validate_composite(name, catalog, ())
    return catalog


def _composite_op_refs(composite: Dict[str, Any]) -> List[str]:
    """Op-names a composite body references (flattening nested sub_chains)."""
    refs: List[str] = []
    stages = composite.get("stage", [])
    if not isinstance(stages, list):
        return refs
    for st in stages:
        if not isinstance(st, dict):
            continue
        for key in _COMPOSITE_OP_KEYS:
            v = st.get(key)
            if isinstance(v, str):
                refs.append(v)
        sub = st.get("sub_chain")
        if isinstance(sub, list):
            refs.extend(_composite_op_refs({"stage": sub}))
        elif isinstance(sub, dict):
            refs.extend(_composite_op_refs({"stage": sub.get("stage", [])}))
    return refs


def _validate_composite(
    name: str, catalog: Dict[str, Dict[str, Any]], path: Tuple[str, ...],
) -> None:
    """Validate a composite at load: referenced ops resolve + the graph is acyclic.

    Raises ValueError on an unknown referenced op, an empty ``[composite]``
    body, or a composite cycle — the F289 D2 "follow srmech naming" load-time
    gate (a typo fails loud here, not silently at run).
    """
    if name in path:
        raise ValueError(
            f"composite cascade cycle: {' -> '.join(path + (name,))}"
        )
    desc = catalog.get(name)
    if not isinstance(desc, dict):
        raise ValueError(f"composite references unknown cascade op {name!r}")
    composite = desc.get("composite")
    if not isinstance(composite, dict):
        # A primitive op — its shipped callable is verified by lookup_cascade_op.
        return
    stages = composite.get("stage")
    if not isinstance(stages, list) or not stages:
        raise ValueError(
            f"composite {name!r} ({desc.get('_source')}): [composite] needs a "
            f"non-empty [[composite.stage]] array"
        )
    for ref in _composite_op_refs(composite):
        if ref not in catalog:
            raise ValueError(
                f"composite {name!r} references unknown op {ref!r}; "
                f"catalog: {sorted(catalog)}"
            )
        _validate_composite(ref, catalog, path + (name,))


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
        The resolved cascade op: a shipped ``srmech.amsc.cascade`` callable,
        or — for a user ``[composite]`` descriptor — a unary stage that runs
        the composite's pure-TOML sub-chain (F289 D2 BYO).

    Raises
    ------
    ValueError
        If ``op_name`` is not present in any catalog descriptor.
    RuntimeError
        If a (non-composite) descriptor exists but :mod:`srmech.amsc.cascade`
        does not expose a matching Python callable (an install integrity
        failure).
    """
    catalog = load_catalog()
    if op_name not in catalog:
        raise ValueError(
            f"unknown cascade op {op_name!r}; "
            f"catalog: {sorted(catalog)}"
        )
    desc = catalog[op_name]
    if isinstance(desc.get("composite"), dict):
        # A user PURE-TOML composite (F289 D2): a chain of named ops, no
        # Python. Resolve to a unary stage that builds + runs its sub-chain.
        return _make_composite_runner(op_name, desc)
    # Local import to avoid an import cycle at module-load time —
    # srmech.amsc.cascade imports srmech.introspect which imports
    # srmech.dsl in some test configurations.
    from srmech.amsc import cascade as _cascade

    fn = getattr(_cascade, op_name, None)
    if fn is None or not callable(fn):
        raise RuntimeError(
            f"cascade-catalog has descriptor for {op_name!r} but "
            f"srmech.amsc.cascade does not expose a matching callable "
            f"(install integrity failure)"
        )
    return fn


def _make_composite_runner(op_name: str, desc: Dict[str, Any]) -> Callable:
    """Build a unary stage that runs a composite's pure-TOML sub-chain (F289 D2).

    The composite's ``[[composite.stage]]`` array is the same stage grammar a
    top-level TOML chain uses; we build it via :func:`build_chain_from_dict`
    and wrap ``chain.run`` as the unary ``value -> value`` op the DSL expects.
    Built eagerly (at lookup time) so a malformed stage discriminator fails
    loud here rather than mid-run.
    """
    # Local import: _toml_chain imports _chain which imports this module —
    # deferring to call time breaks the import cycle.
    from ._toml_chain import build_chain_from_dict

    chain = build_chain_from_dict({
        "chain": {"name": op_name},
        "stage": list(desc["composite"]["stage"]),
    })

    def _run(value: Any) -> Any:
        return chain.run(value)

    _run.__name__ = op_name
    _run.__doc__ = str(
        desc.get("cascade", {}).get("purpose", f"user composite cascade {op_name}")
    )
    return _run


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
    "register_catalog_dir",
    "load_catalog",
    "lookup_cascade_op",
    "list_cascade_ops",
    "cascade_op_kind",
    "get_descriptor",
]
