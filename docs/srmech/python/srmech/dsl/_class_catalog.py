"""TOML class-catalog loader — user-declared classes, constructed at runtime.

The op-level config-driven pattern (:mod:`srmech.dsl._catalog`: a ``[cascade]``
TOML declares an op; the user drops their own in a ``register_catalog_dir`` dir
and it resolves identically to a shipped op) — **lifted from ops to classes**
(#962 Part 2 / #566; user direction 2026-06-09).

A researcher authors a ``[class]`` TOML descriptor (fields + methods-as-cascade-
op-refs) and this loader constructs a generic, class-aware :class:`CatalogClass`
from it — **zero user Python, 100% declarative**. Each method ``binds`` to a
shipped cascade op resolved by dotted srmech path (e.g.
``srmech.amsc.genome.chromosome``); the genome surface's flat functions are the
primitives the methods compose. The genome/chromosome/telomere storage class
ships as the built-in seed worked-instance
(``srmech/amsc/_research/class_catalog/genome.toml``).

Discovery mirrors :mod:`srmech.dsl._catalog` exactly: the packaged catalog
(A-tier) PLUS any external dirs from ``SRMECH_CLASS_PATH`` /
:func:`register_class_dir` (B-tier, attested to the user's descriptor hash). A
user class-name may NOT shadow a shipped one.

Framework reading: this loader is Class E (catalog enumeration) ∘ Class F
(template-style descriptor render); a :class:`CatalogClass` method is a Class B/N
bind-resolution (the ``binds`` name-list) composed against the dotted-path op
resolution (Class A content-of-name → callable). DSL / CLI / tool_schema
class-awareness compose ON this loader in subsequent bricks.
"""

from __future__ import annotations

import importlib
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

if sys.version_info >= (3, 11):
    import tomllib as _toml
else:  # pragma: no cover — 3.10-only branch
    import tomli as _toml  # type: ignore[no-redef]

#: On-disk directory housing the packaged [class] TOML descriptors.
CLASS_CATALOG_DIR: Path = (
    Path(__file__).parent.parent / "amsc" / "_research" / "class_catalog"
)

_PROVENANCE_SHIPPED = "srmech"

#: External class-catalog dirs registered at runtime via register_class_dir.
_USER_CLASS_DIRS: List[Path] = []


def _env_class_dirs() -> List[Path]:
    """External class-catalog dirs from ``SRMECH_CLASS_PATH`` (os.pathsep list)."""
    raw = os.environ.get("SRMECH_CLASS_PATH", "")
    return [Path(p) for p in raw.split(os.pathsep) if p.strip()]


def _user_class_dirs() -> List[Path]:
    """Active external dirs: env-var first, then :func:`register_class_dir`."""
    dirs: List[Path] = []
    for p in _env_class_dirs() + _USER_CLASS_DIRS:
        if p not in dirs:
            dirs.append(p)
    return dirs


def register_class_dir(path: Any) -> None:
    """Register an external class-catalog directory (bring-your-own classes).

    A researcher drops their own ``*.toml`` ``[class]`` descriptors in ``path``
    and registers it; the classes then construct and surface identically to the
    shipped seed (genome) — flagged ``provenance="user"`` (B-tier, attested to
    the descriptor hash). ``SRMECH_CLASS_PATH`` (os.pathsep dirs) is the zero-API
    equivalent. A user class-name may NOT shadow a shipped one.
    """
    p = Path(path)
    assert p.exists() and p.is_dir(), (
        f"register_class_dir: not an existing directory: {p}"
    )
    if p not in _USER_CLASS_DIRS:
        _USER_CLASS_DIRS.append(p)
    load_class_catalog.cache_clear()


@lru_cache(maxsize=1)
def load_class_catalog() -> Dict[str, Dict[str, Any]]:
    """Load all ``[class]`` TOML descriptors (packaged + user-registered).

    Returns a mapping ``class_name -> parsed-descriptor-dict`` (each tagged with
    ``_provenance`` and ``_source``). Cached; cleared by :func:`register_class_dir`.

    Raises ``FileNotFoundError`` if the packaged dir / a registered dir is
    missing, and ``ValueError`` on a missing ``[class].name`` or a user
    class-name that shadows a shipped or earlier one.
    """
    if not CLASS_CATALOG_DIR.exists() or not CLASS_CATALOG_DIR.is_dir():
        raise FileNotFoundError(
            f"class-catalog directory not found at {CLASS_CATALOG_DIR}; "
            f"srmech install appears incomplete"
        )
    catalog: Dict[str, Dict[str, Any]] = {}
    sources: List[Tuple[Path, str]] = [(CLASS_CATALOG_DIR, _PROVENANCE_SHIPPED)]
    sources += [(d, "user") for d in _user_class_dirs()]
    for base, tier in sources:
        if not base.exists() or not base.is_dir():
            raise FileNotFoundError(
                f"registered class-catalog directory not found: {base}"
            )
        for toml_path in sorted(base.glob("*.toml")):
            raw = toml_path.read_bytes()
            desc = _toml.loads(raw.decode("utf-8"))
            class_section = desc.get("class")
            if not isinstance(class_section, dict):
                raise ValueError(
                    f"class-catalog descriptor {toml_path} is missing the "
                    f"required [class] section"
                )
            class_name = class_section.get("name")
            if not isinstance(class_name, str) or not class_name:
                raise ValueError(
                    f"class-catalog descriptor {toml_path} is missing the "
                    f"required [class].name field"
                )
            if class_name in catalog:
                raise ValueError(
                    f"class-name conflict: {class_name!r} in {toml_path} is "
                    f"already defined by {catalog[class_name]['_source']}; user "
                    f"descriptors may not shadow shipped or earlier class-names"
                )
            if tier == _PROVENANCE_SHIPPED:
                desc["_provenance"] = _PROVENANCE_SHIPPED
            else:
                from srmech.amsc.format import sha256_bytes
                desc["_provenance"] = f"user:{sha256_bytes(raw)}"
            desc["_source"] = str(toml_path)
            catalog[class_name] = desc
    return catalog


@lru_cache(maxsize=None)
def _resolve_op(dotted: str) -> Callable:
    """Resolve a dotted srmech path (e.g. ``srmech.amsc.genome.chromosome``) to
    its callable. Split on the last dot → ``import_module(parent)`` + getattr."""
    if "." not in dotted:
        raise ValueError(f"class method op must be a dotted path; got {dotted!r}")
    mod_path, _, attr = dotted.rpartition(".")
    mod = importlib.import_module(mod_path)
    fn = getattr(mod, attr, None)
    if fn is None or not callable(fn):
        raise RuntimeError(
            f"class method op {dotted!r} does not resolve to a callable "
            f"(checked {mod_path}.{attr})"
        )
    return fn


def _field_default(ftype: Any) -> Any:
    """Default for a declared field type: ``[]`` for a ``list*`` type, ``{}`` for
    a ``dict*`` type, else None (a scalar/object supplied at construction)."""
    if isinstance(ftype, str):
        if ftype.startswith("list"):
            return []
        if ftype.startswith("dict"):
            return {}
    return None


class CatalogClass:
    """A user-declared srmech class, constructed from a ``[class]`` TOML descriptor.

    Generic + runtime: fields hold state; declared methods dispatch to named
    cascade ops (resolved by dotted srmech path). No codegen, no user Python.
    Construct via :func:`make_class` (which binds the descriptor) and call the
    declared methods by name::

        Genome = make_class("Genome")
        g = Genome(the_one=one)
        g.shape(n=5000)                                  # -> the encode-shape dict
        strand = g.add_chromosome(leaves=[...], label="astronomy")  # appended
        leaves = g.recall(strand=strand, telomere=g.cap(label="astronomy"))

    A method has ONE op-source — either ``op`` (a single cascade op, ``binds``
    resolved positionally from call kwargs then fields; leftover call kwargs pass
    through, e.g. ``label=``) or ``chain`` (a VISIBLE multi-op pipeline: a list of
    ``{op, binds, as}`` stages, each stage's ``binds`` from a prior stage's ``as``
    / call kwargs / fields; the method returns the last stage's result). State
    routing is mutually exclusive, at most one of: ``appends`` (``list.append``
    one field), ``sets`` (replace one field), ``mutates`` (a field-name list — the
    op returns ``(return_value, {field: new})`` and each named field is replaced),
    or ``returns = "self"`` (a self-returning method — the op/chain returns the new
    instance's ``{field: value}`` state-dict and a FRESH same-class instance is
    constructed; ``self`` is untouched).
    """

    def __init__(self, descriptor: Dict[str, Any], **fields: Any) -> None:
        object.__setattr__(self, "_descriptor", descriptor)
        spec = descriptor["class"]
        object.__setattr__(self, "_class_name", spec["name"])
        declared = spec.get("field", {})
        if not isinstance(declared, dict):
            declared = {}
        unknown = set(fields) - set(declared)
        if unknown:
            raise TypeError(
                f"{spec['name']}: unknown field(s) {sorted(unknown)}; "
                f"declared: {sorted(declared)}"
            )
        state = {
            fname: fields.get(fname, _field_default(ftype))
            for fname, ftype in declared.items()
        }
        object.__setattr__(self, "_fields", state)

    @property
    def class_name(self) -> str:
        return self._class_name

    @property
    def fields(self) -> Dict[str, Any]:
        """A read-only view of the instance's current field values."""
        return dict(self._fields)

    def __getattr__(self, name: str) -> Any:
        # Only called when normal lookup fails. Underscore names are never
        # methods — raising here also breaks the __init__ recursion risk.
        if name.startswith("_"):
            raise AttributeError(name)
        methods = self._descriptor["class"].get("method", {})
        if name in methods:
            def _bound(**call_kwargs: Any) -> Any:
                return self._invoke(name, **call_kwargs)
            _bound.__name__ = name
            _bound.__doc__ = str(methods[name].get("doc", f"{self._class_name}.{name}"))
            return _bound
        raise AttributeError(
            f"{self._class_name!r} object has no method {name!r}; "
            f"declared: {sorted(methods)}"
        )

    def _invoke(self, mname: str, **call_kwargs: Any) -> Any:
        spec = self._descriptor["class"]["method"][mname]
        chain = spec.get("chain")
        has_op = "op" in spec
        if has_op == (chain is not None):
            raise ValueError(
                f"{self._class_name}.{mname}: a method needs exactly one of "
                f"'op' (single cascade op) or 'chain' (a visible multi-op pipeline)"
            )
        if chain is not None:
            result = self._run_chain(mname, chain, call_kwargs)
        else:
            op = _resolve_op(spec["op"])
            args: List[Any] = []
            for b in spec.get("binds", []):
                if b in call_kwargs:
                    args.append(call_kwargs.pop(b))
                elif b in self._fields:
                    args.append(self._fields[b])
                else:
                    raise ValueError(
                        f"{self._class_name}.{mname}: cannot resolve bind {b!r} "
                        f"(not a call kwarg, not a field)"
                    )
            result = op(*args, **call_kwargs)   # leftover kwargs pass through (e.g. label=)
        # ── state routing: at most one of appends / sets / mutates / returns ──
        routes = {k: spec.get(k) for k in ("appends", "sets", "mutates", "returns")}
        active = {k: v for k, v in routes.items() if v is not None}
        if len(active) > 1:
            raise ValueError(
                f"{self._class_name}.{mname}: a method may route its result via at "
                f"most one of 'appends' / 'sets' / 'mutates' / 'returns'; "
                f"declared {sorted(active)}"
            )
        if "returns" in active:
            return self._apply_returns(mname, active["returns"], result)
        if "mutates" in active:
            return self._apply_mutates(mname, active["mutates"], result)
        if "appends" in active:
            self._fields.setdefault(active["appends"], []).append(result)
        elif "sets" in active:
            self._fields[active["sets"]] = result
        return result

    def _run_chain(self, mname: str, chain: Any, call_kwargs: Dict[str, Any]) -> Any:
        """Run a method declared as a VISIBLE multi-op pipeline — a list of
        ``{op, binds, as}`` stages. Each stage resolves its ``binds`` positionally
        from (1) a prior stage's ``as`` result, then (2) the call kwargs, then (3)
        the instance fields; its non-(op/binds/as) keys are static stage kwargs;
        its result is stashed under ``as`` (if given) for later stages. The method
        returns the LAST stage's result (then state-routed like a single op).

        This is the multi-op generalisation of the single-``op`` method — the
        cascade composition is declared IN THE TOML (the config-driven point),
        not buried inside one flat op. (The linear ``srmech.dsl.Chain`` threads a
        single field-free value; a class method needs per-stage field binds, so
        this is the class-aware engine.)"""
        if not isinstance(chain, list) or not chain:
            raise ValueError(
                f"{self._class_name}.{mname}: 'chain' must be a non-empty list of "
                f"{{op, binds, as}} stage tables; got {chain!r}"
            )
        scope: Dict[str, Any] = {}
        last: Any = None
        for idx, stage in enumerate(chain):
            if not isinstance(stage, dict) or "op" not in stage:
                raise ValueError(
                    f"{self._class_name}.{mname}: chain stage {idx} must be a table "
                    f"with an 'op' dotted-path; got {stage!r}"
                )
            sop = _resolve_op(stage["op"])
            args: List[Any] = []
            for b in stage.get("binds", []):
                if b in scope:
                    args.append(scope[b])
                elif b in call_kwargs:
                    args.append(call_kwargs[b])      # read (not pop) — stages may share
                elif b in self._fields:
                    args.append(self._fields[b])
                else:
                    raise ValueError(
                        f"{self._class_name}.{mname}: chain stage {idx} cannot "
                        f"resolve bind {b!r} (not a prior 'as', call kwarg, or field)"
                    )
            static = {k: v for k, v in stage.items()
                      if k not in ("op", "binds", "as")}
            last = sop(*args, **static)
            name = stage.get("as")
            if name is not None:
                scope[str(name)] = last
        return last

    def _apply_returns(self, mname: str, returns: Any, result: Any) -> Any:
        """Self-returning method: the op/chain returns the NEW instance's full
        ``{field: value}`` state-dict, and this constructs a FRESH instance of the
        same class from it (the SedenionRegister ``navigate`` shape — a method that
        yields a new register rather than mutating in place). ``self`` is NOT
        touched. ``returns`` currently supports only the literal ``"self"``."""
        if returns != "self":
            raise ValueError(
                f"{self._class_name}.{mname}: 'returns' supports only the literal "
                f"\"self\" (a new same-class instance); got {returns!r}"
            )
        if not isinstance(result, dict):
            raise TypeError(
                f"{self._class_name}.{mname}: a returns=\"self\" method's op must "
                f"return a {{field: value}} dict (the new instance's fields); got "
                f"{type(result).__name__}"
            )
        unknown = sorted(set(result) - set(self._fields))
        if unknown:
            raise ValueError(
                f"{self._class_name}.{mname}: returns=\"self\" field-dict names "
                f"undeclared field(s) {unknown}; declared: {sorted(self._fields)}"
            )
        return CatalogClass(self._descriptor, **result)

    def _apply_mutates(self, mname: str, mutates: Any, result: Any) -> Any:
        """Multi-field state routing: a ``mutates`` op returns
        ``(return_value, {field: new_value})``. Validate the update keys against
        the declared ``mutates`` field-list (⊆ declared fields), apply each, and
        return only the ``return_value``. This is the contract richer classes
        (e.g. a register whose ``write`` touches two fields) need beyond the
        single-field ``appends`` / ``sets`` routing."""
        if not isinstance(mutates, list) or not all(
            isinstance(f, str) for f in mutates
        ):
            raise ValueError(
                f"{self._class_name}.{mname}: 'mutates' must be a list of "
                f"field-name strings; got {mutates!r}"
            )
        undeclared = [f for f in mutates if f not in self._fields]
        if undeclared:
            raise ValueError(
                f"{self._class_name}.{mname}: 'mutates' names undeclared "
                f"field(s) {sorted(undeclared)}; declared: {sorted(self._fields)}"
            )
        if not (
            isinstance(result, tuple)
            and len(result) == 2
            and isinstance(result[1], dict)
        ):
            raise TypeError(
                f"{self._class_name}.{mname}: a 'mutates' method's op must return "
                f"(return_value, {{field: new_value}}); got "
                f"{type(result).__name__}"
            )
        ret, updates = result
        allowed = set(mutates)
        not_allowed = sorted(set(updates) - allowed)
        if not_allowed:
            raise ValueError(
                f"{self._class_name}.{mname}: op updated field(s) {not_allowed} "
                f"not in declared mutates={sorted(allowed)}"
            )
        for fname, value in updates.items():
            self._fields[fname] = value
        return ret

    def __repr__(self) -> str:  # pragma: no cover — display only
        return f"<CatalogClass {self._class_name} fields={sorted(self._fields)}>"


def make_class(name: str) -> Callable[..., CatalogClass]:
    """Return a factory that constructs the user-declared class ``name``.

    ``Genome = make_class("Genome"); g = Genome(the_one=...)``. The factory
    carries ``.class_name`` and ``.descriptor`` for introspection (the hook
    DSL / CLI / tool_schema class-awareness composes on).
    """
    catalog = load_class_catalog()
    if name not in catalog:
        raise ValueError(
            f"unknown srmech class {name!r}; catalog: {sorted(catalog)}"
        )
    descriptor = catalog[name]

    def _factory(**fields: Any) -> CatalogClass:
        return CatalogClass(descriptor, **fields)

    _factory.class_name = name              # type: ignore[attr-defined]
    _factory.descriptor = descriptor        # type: ignore[attr-defined]
    _factory.__name__ = name
    _factory.__doc__ = str(descriptor["class"].get("doc", f"srmech class {name}"))
    return _factory


def list_classes() -> List[str]:
    """Return all class-names declared in the class catalog (sorted)."""
    return sorted(load_class_catalog())


def get_class_descriptor(name: str) -> Dict[str, Any]:
    """Return the raw ``[class]`` TOML descriptor for ``name`` (read-only view)."""
    catalog = load_class_catalog()
    if name not in catalog:
        raise ValueError(
            f"unknown srmech class {name!r}; catalog: {sorted(catalog)}"
        )
    return catalog[name]


__all__ = [
    "CLASS_CATALOG_DIR",
    "register_class_dir",
    "load_class_catalog",
    "CatalogClass",
    "make_class",
    "list_classes",
    "get_class_descriptor",
]
