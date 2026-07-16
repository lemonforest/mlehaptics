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

    build = alias("build", "srmech.amsc.genome.genome")     # one binding
    build({"a": leaves}, one)                                # == genome({"a": leaves}, one)

    names = build_aliases_from_toml_str('''                  # many, from TOML
        [[alias]]
        name = "build"
        target = "srmech.amsc.genome.genome"
        [[alias]]
        name = "stick"
        target = "srmech.amsc.genome.plasmid"
    ''')
    names["build"](kernels, one); names["stick"](kernels, one)

**Security.** A ``target`` MUST be a dotted ``srmech.*`` path — the config-driven naming layer
binds names to srmech's OWN surface, never arbitrary imports (a config file cannot be coaxed
into importing / calling an unrelated module). Resolution reuses the robust dotted-name walk
:func:`srmech.mcp._tools._resolve_dotted_callable`; parsing reuses the DSL's native+tomllib
TOML loader. numpy-free; no import cost until called.
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict

__all__ = ["alias", "build_aliases_from_toml_str", "load_aliases_toml"]

#: The config-driven naming layer only binds names to srmech's OWN surface.
_ALIAS_TARGET_PREFIX = "srmech."


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
    the on-disk counterpart of :func:`build_aliases_from_toml_str`."""
    from pathlib import Path
    return build_aliases_from_toml_str(Path(path).read_text(encoding="utf-8"))
