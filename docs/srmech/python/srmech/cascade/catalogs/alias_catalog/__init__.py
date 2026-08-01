"""Alias descriptors — the config-driven NAMING layer's built-in catalog (rc364).

srmech lets a researcher declare CLASSES in TOML (``srmech.dsl.make_class``),
PIPELINES in TOML (the ``[chain]`` DSL), and — since rc261 — NAME BINDINGS in
TOML (``srmech.dsl.alias``). This directory is the naming layer's packaged
catalog, the peer of ``class_catalog/`` and ``cascade_catalog/`` that rc261 and
rc271 both needed and neither had.

**Why it did not exist until now, stated plainly.** ``srmech.dsl._alias``
exposed only ``load_aliases_toml(path)`` — a bare filesystem path with no
``ALIAS_CATALOG_DIR`` peer to ``CLASS_CATALOG_DIR`` and no ``register_alias_dir``.
With no shipped home to land in, rc362's first-ever ``[[alias]]`` descriptor
went to ``tests/data/`` **by default rather than by decision**, and rc271's
value-alias example had gone to the same place a hundred rcs earlier. Neither
shipped: ``tests/**`` is in ``sdist.include`` and NOT in the wheel, so a wheel
user following ``genome_type_aliases_legacy.toml``'s own documented one-call
migration path got ``FileNotFoundError``. The absent directory constant was the
cause; this directory plus :data:`srmech.dsl.ALIAS_CATALOG_DIR` and
:func:`srmech.dsl.register_alias_dir` is the fix.

Two descriptor shapes live here, because srmech has two aliasing mechanisms and
both are naming:

``[[alias]]`` — FUNCTION aliasing (rc261, :func:`srmech.dsl.load_aliases_toml`)
    An array of ``{name, target}`` tables binding a user's own name to any
    ``srmech.*`` callable. ``music_domain_aliases.toml`` is the worked example:
    the acoustic domain's vocabulary (``partials``, ``bell_tuning``,
    ``overtone_series``, …) as a config binding over the general ops.

``[genome.type_aliases]`` — VALUE aliasing (rc271,
:func:`srmech.biology.genome.load_type_aliases_toml`)
    A canonical→display mapping applied as a pure presentation layer over
    ``genome_census`` / ``genome_registry`` / ``genome_catalog`` output.
    ``genome_type_aliases_legacy.toml`` is the worked example and the documented
    migration path for rc271's BREAKING ``stick``→``plasmid`` /
    ``minted``→``nuclear`` rename.

Both are resolvable **by bare filename** against this directory — that is what
makes the documented one-liners work from a wheel install rather than only from
a source checkout. See :func:`srmech.dsl.resolve_alias_descriptor`.

Neither mechanism mints an op, so neither owes C parity: ``alias`` returns a
``functools.wraps`` duplicate of a callable that already exists on every
implementation, and the value-alias layer post-transforms canonical output
identically on the native and pure paths. The rosetta ledger classifies the
alias layer ``dev_tooling`` = never-owed-C.
"""

from __future__ import annotations

__all__: list = []
