"""TOML cascade-catalog runtime loader for the DSL runner.

Reads the packaged TOML descriptors under
``srmech/cascade/catalogs/cascade_catalog/`` — PLUS any external dirs a user
registers via ``SRMECH_CASCADE_PATH`` / :func:`register_catalog_dir` (the
bring-your-own cascade-TOML surface, F289 D2) — and resolves each op-name to
its Python entry point: a shipped :mod:`srmech.cascade` callable (routes
to a C peer when ``HAS_NATIVE``), or, for a user ``[composite]`` descriptor, a
unary stage that runs its pure-TOML sub-chain (no Python required).

The catalog IS the SSoT for which cascade ops exist — the DSL runner keeps no
hard-coded name list. ``chain().then("foo")`` is rejected for any BARE ``foo``
not declared in a descriptor. User descriptors are B-tier
(``provenance="user"``, attested to their own descriptor hash) and may NOT
shadow a shipped A-tier op-name (that raises at load).

**The dotted arm, and its bound** (rc420 `#T1114` BLK-REGMAP). A step name
containing a dot is NOT a catalog lookup at all: it resolves by import
(``rpartition(".")`` + a callable guard, see :func:`lookup_cascade_op`), so
``chain().then("srmech.cascade.leaves.seq_len")`` runs even though no
descriptor declares ``seq_len``. That arm exists for ONE job — letting a
descriptor or a chain step point at a **shipped srmech callable that has no
descriptor of its own**, so the registered-leaf inventory
(:mod:`srmech.cascade.leaves` and friends) is addressable without minting a
descriptor per leaf. Catalog names never contain a dot —
:func:`load_catalog` REJECTS a dotted ``[cascade].name`` at load (`#T1137`
adjudication guard) — so the two forms cannot collide. Measured before the
guard existed: an unimportable dotted name loaded as
listed-but-unlookupable, and an IMPORTABLE one (``name =
"srmech.cascade.magnitude"``) loaded, listed, answered
:func:`get_descriptor` with the USER descriptor — and then ran the SHIPPED
import instead (``chain().then("srmech.cascade.magnitude").run(-5)`` gave
``5``, not the descriptor's chain), because the dot routes resolution to
the import arm before any catalog consultation. A dotted catalog name was
never a collision the user could win; the guard makes it a load error
instead of a silent wrong answer.

It is **NOT a general extension point**, and the catalog's guarantees do not
follow the callable through it. MEASURED at rc434:

- **No descriptor, so no provenance tier.**
  ``get_descriptor("srmech.cascade.magnitude")`` raises ``ValueError:
  unknown cascade op`` — the A/B-tier attestation above is a property of the
  DESCRIPTOR, and a dotted step has none. (The bare name ``magnitude`` is
  A-tier; the dotted spelling of the SAME function is untiered.)
- **Introspection visibility is keyed by the SPELLING, not the callable.**
  ``get_tool_schema().resolve(...)`` answers a registered name (or a
  dotted-suffix shortening of one); it never follows a callable to its
  other names. ``resolve("srmech.cascade.magnitude")`` HITs — that exact
  string is a registered ``ToolEntry`` — while
  ``resolve("srmech.cascade.leaves.seq_len")`` is ``None`` even though it
  is the SAME object as the registered ``srmech.cascade.seq_len``.
  Measured over the 36 distinct dotted spellings in shipped
  ``[[cascade.chain]]`` steps: 2 resolve, 32 return ``None`` while their
  target is registered under its published ``srmech.cascade.<name>``
  re-export, and 2 (the RBS-HDC ``mint_vector`` and the Class-F
  ``srmech.amsc.descriptor.render_template``) are registered under NO
  spelling. The census moved 35 → 36 at rc438 (`#T1140`), when
  ``klein4_from_one.toml`` landed and its Class-F render step named
  ``render_template`` — an op that ships and runs but carries no
  ``ToolEntry`` under any spelling, so it joins ``mint_vector`` in the
  genuinely-unregistered bucket rather than the invisible-while-registered
  one. That bucket is NOT the down-only census (the invisible set is, and it
  is unchanged at 32 — the new descriptor's other steps all reuse spellings
  already pinned there); registering ``render_template`` is a live
  follow-up, deliberately not taken in an rc whose registry total is
  otherwise unchanged. Every one of the 32 has
  a published spelling that BOTH runs through this same import arm AND
  resolves — prefer ``op = "srmech.cascade.chiral_flip"`` over
  ``op = "srmech.cascade.atoms.chiral_flip"`` when a dotted step should
  stay introspectable. (``describe()["cascade_catalog"]`` is a different
  surface: it lists every DESCRIPTOR by bare name regardless of how its
  chain steps are spelled.)
- **A dotted step evicts the whole chain from BOTH native run loops.**
  The op itself is ONE self-routing object under either spelling (its own
  internal C kernel is unaffected) — but the chain-level engines key their
  dispatch on the bare catalog spelling (``_RUN_C_OPS`` in
  :mod:`srmech.cascade.compose`; ``dsl_leaf_dispatch`` /
  ``cr_dispatch`` in C), so ONE dotted step makes the whole chain
  ineligible and the pure loop runs. Measured at rc434 with an ABI-14
  ``.so``: ``chain().then("magnitude")`` runs end-to-end in C;
  ``chain().then("srmech.cascade.magnitude")`` is a native MISS with the
  IDENTICAL value — the cost is the C fast path, never the answer (rc103
  inform-don't-limit).
- **Nothing constrains the target to srmech at all.**
  ``chain().then("builtins.set")`` resolves and runs, and it re-imports
  hash-order nondeterminism into the cascade: over ``PYTHONHASHSEED`` 0–3 a
  ``str`` payload came back in four different orders (``['b','a','d','c','e']``
  / ``['a','e','b','d','c']`` / ``['d','e','a','c','b']`` /
  ``['c','a','e','b','d']``). Small ints are stable, which is precisely why a
  casual ``set`` → ``sorted`` smoke test does NOT surface the hazard.

Reach for a descriptor — the shipped catalog for an A-tier op, a user
``[composite]`` for a B-tier one — whenever the op is meant to BE cascade
vocabulary. The dotted form is addressing, not declaration.

The descriptors carry ``[cascade].name`` (the canonical op name) plus
optional ``[cascade.native]`` C symbol names + ``[cascade.delegates_to]``
metadata. The DSL runner consults the *name* only — the Python entry
point in :mod:`srmech.cascade` handles the C-dispatch routing
internally, so the DSL doesn't reach into that machinery.

Framework reading: this loader is Class E (catalog enumeration) ∘
Class F (template-style descriptor render) composed against the on-disk
descriptor set. The cache-once-then-reuse pattern (via
:func:`functools.lru_cache`) mirrors the existing
:mod:`srmech.introspect.tool_schema` discipline.
"""

from __future__ import annotations

import importlib
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

# srmech's own internal TOML front door (`#T907` slice 2). Native `srmech_toml`
# parser first, stdlib ``tomllib`` (3.11+) / ``tomli`` (3.10) floor otherwise —
# the cascade-catalog descriptors now self-host on the C parser wherever it is
# present. A float-bearing descriptor (e.g. ``best_rational_signed.toml``'s
# ``dead_band = 1e-12``) is DECLINED by the C path and rides the bit-exact stdlib
# parser, so the parsed value — and any ``TOMLDecodeError`` on a malformed
# descriptor — is identical to the previous stdlib-only parse either way.
# ``srmech._toml`` is a leaf module (it imports ``srmech._native`` lazily inside
# ``loads()``), so this module-top import introduces no package-init cycle.
from srmech import _toml as srmech_toml

#: On-disk directory housing the cascade-catalog TOML descriptors.
#: Resolved relative to ``srmech.dsl._catalog`` so editable installs
#: and wheel installs both work.
#:
#: Moved out of ``srmech/amsc/_research/`` by ADR-0010's first execution slice
#: (rc364), alongside :data:`~srmech.dsl.CLASS_CATALOG_DIR` and
#: :data:`~srmech.dsl.ALIAS_CATALOG_DIR`. The composition layer owns the
#: built-in catalogs; ``amsc`` keeps only attestation.
CATALOG_DIR: Path = (
    Path(__file__).parent.parent / "cascade" / "catalogs" / "cascade_catalog"
)

#: Provenance tier for the shipped (packaged) catalog — A-tier, attested to
#: srmech's verified ground-proof. User dirs are B-tier ("user:<sha256>").
_PROVENANCE_SHIPPED = "srmech"

#: External cascade-catalog dirs registered at runtime via
#: :func:`register_catalog_dir`. The ``SRMECH_CASCADE_PATH`` env-var is the
#: zero-API equivalent (read fresh on each (re)load). Bring-your-own; F289 D2.
_USER_CATALOG_DIRS: List[Path] = []

#: Stage-dict keys that name a referenced cascade op (for composite validation).
#: MUST list EVERY op-naming discriminator the stage grammar accepts. A key that
#: is missing here does not merely skip one check — it silently lapses BOTH
#: composite load-time guarantees at once, because :func:`_composite_op_refs`
#: feeds both unknown-op validation and cycle detection from this one tuple.
#: ``map_op`` was absent from rc? through rc445 (`#T1142`, gh #1653): a composite
#: whose ``map_op`` named a non-existent op loaded clean, and a cycle routed
#: through a ``map_op`` was undetectable. Both are gated now, with planted
#: failures and covered-key controls in
#: ``tests/test_composite_op_keys_closed_rc446.py``.
_COMPOSITE_OP_KEYS = ("op", "fold_op", "reduce_op", "parallel_body", "map_op")


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
    ops — no Python) or a primitive (needs a matching ``srmech.cascade``
    callable). A user op-name may NOT shadow a shipped one.

    Raises:
        FileNotFoundError: if ``path`` does not exist, or exists but is not a
            directory. :func:`load_catalog` already DECLARES this same error
            for the same condition, and raises it a few lines below.

    A real ``raise``, not an ``assert`` (rc433, `#T1131`): the promotion here
    is about WHEN, not WHETHER. Under ``python -O`` the assert vanished, this
    function RETURNED CLEANLY, and the bad path was appended to the
    module-global ``_USER_CATALOG_DIRS``. The error then surfaced at the next
    :func:`load_catalog` — after the global mutation, and on EVERY subsequent
    catalog load for the life of the process. A caller error became persistent
    global-state poisoning.
    """
    p = Path(path)
    if not (p.exists() and p.is_dir()):
        raise FileNotFoundError(
            f"register_catalog_dir: not an existing directory: {p}")
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
        On a missing ``[cascade].name``, a DOTTED ``[cascade].name`` (see the
        guard below), a user op-name that shadows a shipped or earlier op, or
        a composite body that references an unknown op / forms a cycle
        (validated loudly here, not silently at run).
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
            desc = srmech_toml.loads(raw.decode("utf-8"))
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
            if "." in op_name:
                # `#T1137` adjudication guard: a dotted [cascade].name can
                # NEVER be looked up — lookup_cascade_op routes any dotted
                # name to the import arm before consulting the catalog. So
                # a dotted name here is either listed-but-unlookupable (the
                # module is not importable) or, worse, silently SHADOWED by
                # the import (measured: a user descriptor named
                # "srmech.cascade.magnitude" listed and introspected as the
                # user's composite while chains ran the shipped op). Catalog
                # names are BARE; the dotted form is a chain-step ADDRESS,
                # not a declarable name.
                raise ValueError(
                    f"cascade-catalog descriptor {toml_path}: [cascade].name "
                    f"{op_name!r} contains a dot; a dotted catalog name can "
                    f"never be resolved (the dot routes lookup to the import "
                    f"arm before any catalog consultation). Use a BARE name; "
                    f"the dotted form is for chain-step addressing only."
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
    """Resolve ``op_name`` to its Python entry point in :mod:`srmech.cascade`.

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
        The resolved cascade op: a shipped ``srmech.cascade`` callable,
        or — for a user ``[composite]`` descriptor — a unary stage that runs
        the composite's pure-TOML sub-chain (F289 D2 BYO).

    Raises
    ------
    ValueError
        If ``op_name`` is not present in any catalog descriptor (bare
        form), or a dotted name does not resolve to a callable.
    RuntimeError
        If a (non-composite) descriptor exists but :mod:`srmech.cascade`
        does not expose a matching Python callable (an install integrity
        failure).
    """
    # rc420 (`#T1114` BLK-REGMAP): a FULLY-QUALIFIED dotted op_name resolves
    # by import — the caller-side twin of the §17 U2 descriptor-side dotted
    # `[cascade].op` below (same rpartition + callable guard). This is what
    # makes "dotted-or-bare NAME" true for every builder (`then` / `fold` /
    # `reduce` / `parallel_sectors` / `map_indexed`): any shipped registered
    # op can serve as a stage or combinator body without a catalog
    # descriptor of its own. Catalog names never contain a dot (load_catalog
    # REJECTS a dotted [cascade].name — the `#T1137` guard), so the two
    # forms cannot collide.
    if "." in op_name:
        mod_path, _, attr = op_name.rpartition(".")
        try:
            mod = importlib.import_module(mod_path)
        except ImportError as exc:
            raise ValueError(
                f"dotted cascade op {op_name!r}: module {mod_path!r} not "
                f"importable: {exc}"
            ) from exc
        fn = getattr(mod, attr, None)
        if fn is None or not callable(fn):
            raise ValueError(
                f"dotted cascade op {op_name!r} does not resolve to a "
                f"callable (checked {mod_path}.{attr})"
            )
        return fn
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
    # §17 U2: a descriptor may name a DOTTED entry point — `[cascade].op =
    # "srmech.signal_processing.encode_loe_content"` — so an EXISTING op that
    # lives outside `srmech.cascade` (e.g. a text→instrument encoder) is
    # DSL-registrable without re-exporting it. Mirrors the rc39 class-catalog's
    # dotted-path method resolution; lets a catalog's text rows get a one-line
    # kernel chain (`[[stage]] op="encode_loe_content"`).
    dotted = desc.get("cascade", {}).get("op")
    if isinstance(dotted, str) and "." in dotted:
        mod_path, _, attr = dotted.rpartition(".")
        mod = importlib.import_module(mod_path)
        fn = getattr(mod, attr, None)
        if fn is None or not callable(fn):
            raise RuntimeError(
                f"cascade-catalog descriptor for {op_name!r} declares "
                f"op={dotted!r} which does not resolve to a callable "
                f"(checked {mod_path}.{attr})"
            )
        return fn
    # Local import to avoid an import cycle at module-load time —
    # srmech.cascade imports srmech.introspect which imports
    # srmech.dsl in some test configurations.
    from srmech import cascade as _cascade

    fn = getattr(_cascade, op_name, None)
    if fn is None or not callable(fn):
        raise RuntimeError(
            f"cascade-catalog has descriptor for {op_name!r} but "
            f"srmech.cascade does not expose a matching callable "
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
        Sorted ascending. The list is consumed by
        :func:`srmech.cli.dsl.run_ops` (the ``srmech dsl ops`` subcommand)
        and by the test-suite's descriptor-coverage check.
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
