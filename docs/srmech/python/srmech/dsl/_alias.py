"""Config-driven FUNCTION ALIASING (rc261 / §95.2 / #1407) — bind a user's OWN name to any
existing ``srmech.*`` function via TOML.

This is the domain-agnostic naming layer (ADR-0004): srmech already lets a researcher declare
CLASSES in TOML (:func:`srmech.dsl.make_class`) and PIPELINES in TOML (the ``[chain]`` DSL);
this adds the smallest missing rung — declaring a NAME BINDING. A user's config gives names
that make sense in THEIR domain (alias ``genome`` → ``build``, ``plasmid`` → ``stick``, or any
domain vocabulary), so the framework's own naming (e.g. the rc260 genome/plasmid rename) is a
non-issue at the user layer — anyone re-aliases to taste, in config, no code.

Two entry points::

    from srmech.dsl import alias, build_aliases_from_toml_str

    build = alias("build", "srmech.biology.genome.genome")     # one binding
    build({"a": leaves}, one)                                # == genome({"a": leaves}, one)

    names = build_aliases_from_toml_str('''                  # many, from TOML
        [[alias]]
        name = "build"
        target = "srmech.biology.genome.genome"
        [[alias]]
        name = "stick"
        target = "srmech.biology.genome.plasmid"
    ''')
    names["build"](kernels, one); names["stick"](kernels, one)

**Security.** A ``target`` MUST be a dotted ``srmech.*`` path — the config-driven naming layer
binds names to srmech's OWN surface, never arbitrary imports (a config file cannot be coaxed
into importing / calling an unrelated module). Resolution reuses the robust dotted-name walk
:func:`srmech.mcp._tools._resolve_dotted_callable`; parsing reuses the DSL's native+tomllib
TOML loader. numpy-free; no import cost until called.

**rc364 — THE LAYER GETS A CATALOG DIRECTORY** (ADR-0010 amendment B). rc261 shipped
``load_aliases_toml(path)`` and nothing else: a bare filesystem path, with no
``ALIAS_CATALOG_DIR`` peer to :data:`srmech.dsl.CLASS_CATALOG_DIR` and no
``register_alias_dir`` peer to :func:`srmech.dsl.register_class_dir`. The class and cascade
layers each had *both* halves — a shipped directory for built-in descriptors and a
registration API for user ones — and the naming layer had neither. The consequence was not
theoretical: with no shipped home to land in, rc362's first-ever ``[[alias]]`` descriptor went
to ``tests/data/`` **by default rather than by decision**, and ``tests/**`` is in
``sdist.include`` but NOT in the wheel — so zero alias descriptors shipped, and a wheel user
following ``genome_type_aliases_legacy.toml``'s own documented one-call migration path got a
``FileNotFoundError``.

This module now carries the same shape the class layer already had:

* :data:`ALIAS_CATALOG_DIR` — the packaged descriptors (``srmech/cascade/catalogs/alias_catalog/``)
* :func:`register_alias_dir` / ``SRMECH_ALIAS_PATH`` — user-supplied dirs (the
  ``srmech.external.*`` extension point)
* :func:`list_alias_descriptors` — enumerate what is resolvable
* :func:`resolve_alias_descriptor` — resolve a BARE NAME against those dirs

and :func:`load_aliases_toml` resolves through it, so the documented one-liners work from a
wheel install and not only from a source checkout. What that enables, concretely: a domain can
now SHIP its vocabulary. An acoustic user pip-installs srmech and gets
``music_domain_aliases.toml``; a research group drops its own ``*.toml`` in a directory and
calls ``register_alias_dir`` — the config-driven/plugin stance applied to naming, which until
rc364 was the one rung of the ADR-0004 ladder (classes → pipelines → names) with no
plugin surface.
"""
from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any, Callable, Dict, List

__all__ = [
    "ALIAS_CATALOG_DIR",
    "alias",
    "build_aliases_from_toml_str",
    "list_alias_descriptors",
    "load_aliases_toml",
    "register_alias_dir",
    "resolve_alias_descriptor",
]

#: The config-driven naming layer only binds names to srmech's OWN surface.
_ALIAS_TARGET_PREFIX = "srmech."

#: On-disk directory housing the packaged alias TOML descriptors — the peer of
#: :data:`srmech.dsl.CLASS_CATALOG_DIR` and :data:`srmech.dsl.CATALOG_DIR`, and the
#: home the naming layer lacked from rc261 to rc363. Holds BOTH descriptor shapes the
#: framework aliases with: ``[[alias]]`` function bindings (rc261) and
#: ``[genome.type_aliases]`` value bindings (rc271). Resolved relative to this module so
#: editable installs and wheel installs both work.
ALIAS_CATALOG_DIR: Path = (
    Path(__file__).parent.parent / "cascade" / "catalogs" / "alias_catalog"
)

#: External alias-catalog dirs registered at runtime via :func:`register_alias_dir`.
_USER_ALIAS_DIRS: List[Path] = []


def _env_alias_dirs() -> List[Path]:
    """External alias-catalog dirs from ``SRMECH_ALIAS_PATH`` (os.pathsep list)."""
    raw = os.environ.get("SRMECH_ALIAS_PATH", "")
    return [Path(p) for p in raw.split(os.pathsep) if p.strip()]


def _alias_dirs() -> List[Path]:
    """Search order: packaged first, then env-var dirs, then registered dirs.

    Packaged-first mirrors :func:`srmech.dsl.load_class_catalog`, where the shipped
    A-tier is read before any user B-tier and a user name may not shadow a shipped one.
    """
    dirs: List[Path] = [ALIAS_CATALOG_DIR]
    for p in _env_alias_dirs() + _USER_ALIAS_DIRS:
        if p not in dirs:
            dirs.append(p)
    return dirs


def register_alias_dir(path: Any) -> None:
    """Register an external alias-catalog directory (bring-your-own vocabulary).

    A researcher drops their own ``*.toml`` alias descriptors in ``path`` and registers
    it; :func:`load_aliases_toml` and
    :func:`srmech.biology.genome.load_type_aliases_toml` then resolve those descriptors by
    bare name exactly as they resolve the shipped ones. ``SRMECH_ALIAS_PATH``
    (os.pathsep-separated dirs) is the zero-API equivalent.

    This is the naming layer's half of the ``srmech.external.*`` extension point
    ADR-0010 assigns to user-supplied descriptor dirs — the peer of
    :func:`srmech.dsl.register_class_dir` and :func:`srmech.dsl.register_catalog_dir`.
    """
    p = Path(path)
    if not (p.exists() and p.is_dir()):
        raise ValueError(
            "register_alias_dir: not an existing directory: {}".format(p))
    if p not in _USER_ALIAS_DIRS:
        _USER_ALIAS_DIRS.append(p)


def list_alias_descriptors() -> Dict[str, Path]:
    """Return ``{descriptor-stem: path}`` for every resolvable alias descriptor.

    Packaged descriptors first, then env-var dirs, then dirs registered via
    :func:`register_alias_dir`. A later directory does NOT shadow an earlier one — the
    shipped vocabulary wins, matching the class catalog's A-tier/B-tier rule.
    """
    out: Dict[str, Path] = {}
    for base in _alias_dirs():
        if not (base.exists() and base.is_dir()):
            continue
        for toml_path in sorted(base.glob("*.toml")):
            out.setdefault(toml_path.stem, toml_path)
    return out


def resolve_alias_descriptor(path_or_name: Any) -> Path:
    """Resolve an alias descriptor given as a filesystem path OR a bare name.

    Resolution order, filesystem-first so no existing caller changes meaning:

    1. ``path_or_name`` as given, if it exists on disk;
    2. otherwise, if it names no directory, its stem looked up in
       :func:`list_alias_descriptors` (with or without the ``.toml`` suffix).

    Raises ``FileNotFoundError`` naming every resolvable descriptor when neither hits —
    the message is the discovery surface a bare ``open()`` never had.
    """
    p = Path(path_or_name)
    if p.exists():
        return p
    if p.parent in (Path("."), Path("")):
        stem = p.name[:-5] if p.name.endswith(".toml") else p.name
        found = list_alias_descriptors().get(stem)
        if found is not None:
            return found
    known = sorted(list_alias_descriptors())
    raise FileNotFoundError(
        "alias descriptor {!r} not found on disk and not in the alias catalog. "
        "Shipped + registered descriptors: {}. Add a directory with "
        "srmech.dsl.register_alias_dir(path) or the SRMECH_ALIAS_PATH env-var.".format(
            str(path_or_name), known))


def _resolve_target(target: str) -> Callable[..., Any]:
    """Resolve a dotted ``srmech.*`` path to its live callable — RESTRICTED to the srmech
    namespace (a config must not import arbitrary modules)."""
    if not isinstance(target, str) or not target.startswith(_ALIAS_TARGET_PREFIX):
        raise ValueError(
            "alias target must be a dotted srmech.* path (the config-driven naming layer binds "
            "names to srmech's own surface, not arbitrary imports); got {!r}".format(target))
    from srmech.mcp._tools import _resolve_dotted_callable   # the robust import-and-getattr walk
    fn = _resolve_dotted_callable(target)
    if not callable(fn):
        raise ValueError("alias target {!r} does not resolve to a callable".format(target))
    return fn


def alias(name: str, target: str) -> Callable[..., Any]:
    """Bind ``name`` to the srmech function at the dotted ``target`` path (§95.2 / #1407).

    Returns a callable that forwards to the target (via :func:`functools.wraps`, preserving its
    signature/docstring) but carries the user's ``name`` as ``__name__`` / ``__qualname__`` — so
    a domain user calls the srmech function by their own name. ``target`` is restricted to the
    ``srmech.*`` namespace. Byte-identical behaviour to the target; this is pure naming.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("alias name must be a non-empty str; got {!r}".format(name))
    fn = _resolve_target(target)

    @functools.wraps(fn)
    def _aliased(*args, **kwargs):
        return fn(*args, **kwargs)

    _aliased.__name__ = name
    _aliased.__qualname__ = name
    _aliased.srmech_alias_target = target      # introspection: what this name binds to
    return _aliased


def build_aliases_from_toml_str(spec: str) -> Dict[str, Callable[..., Any]]:
    """Parse a TOML document's ``[[alias]]`` array (each a ``name`` + ``target``) into a
    ``{name: callable}`` mapping — the config-driven naming layer (§95.2 / #1407).

    Each ``target`` is resolved (srmech.*-restricted) to its live callable. The parse routes
    through the C ``srmech_toml`` parser when native (the DSL's :func:`_toml_loads_native`),
    falling back to the stdlib ``tomllib`` / ``tomli`` (same dict, same decode error). Raises
    ``TypeError`` if ``spec`` is not a str, ``ValueError`` on a malformed ``[[alias]]`` entry
    or a non-``srmech.*`` target.
    """
    if not isinstance(spec, str):
        raise TypeError("build_aliases_from_toml_str: spec must be a str of TOML; got {}".format(
            type(spec).__name__))
    from srmech.dsl._toml_chain import _toml, _toml_loads_native
    data = _toml_loads_native(spec)
    if data is None:
        data = _toml.loads(spec)
    entries = data.get("alias", []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        raise ValueError("[[alias]] must be an ARRAY of tables (each a name + target)")
    out: Dict[str, Callable[..., Any]] = {}
    for e in entries:
        if not isinstance(e, dict) or "name" not in e or "target" not in e:
            raise ValueError(
                "each [[alias]] entry needs a 'name' and a 'target'; got {!r}".format(e))
        out[e["name"]] = alias(e["name"], e["target"])
    return out


def load_aliases_toml(path) -> Dict[str, Callable[..., Any]]:
    """Read a TOML file of ``[[alias]]`` entries and build the ``{name: callable}`` mapping —
    the on-disk counterpart of :func:`build_aliases_from_toml_str`.

    ``path`` may be a filesystem path OR the bare name of a shipped / registered
    descriptor (rc364) — see :func:`resolve_alias_descriptor`. So the acoustic vocabulary
    is one call from a wheel install::

        from srmech.dsl import load_aliases_toml
        names = load_aliases_toml("music_domain_aliases")
        names["partials"]()            # == srmech.music.bell_partials()
    """
    return build_aliases_from_toml_str(
        resolve_alias_descriptor(path).read_text(encoding="utf-8"))
