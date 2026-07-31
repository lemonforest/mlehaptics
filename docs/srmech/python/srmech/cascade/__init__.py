"""``srmech.cascade`` — the COMPOSITION layer, and ADR-0010's first new namespace.

ADR-0010 (*namespace declustering*) splits ``srmech`` into **domains** (named by
field), **structure-homes** (named by what they *are*), **provenance**
(``amsc``, shrunk back to attestation), and **cross-cutting meta**
(``introspect``). ``srmech.cascade`` is a *structure* home: it owns
composition — how the 14 A–N primitives are chained into ops, classes and
pipelines — as distinct from the primitives themselves.

**This package is the arc's first executed namespace, so it also sets the
pattern.** Three rules were established here and are meant to be applied to
every later slice:

1. **A slice relocates a PARENT; it does not rename the LEAF.** ``class_catalog``
   / ``cascade_catalog`` / ``worked_instances`` kept their directory names
   verbatim across the move. One slice changes exactly one thing — *where* a
   thing lives — so a red gate has exactly one possible cause. Renaming while
   moving makes every red ambiguous between "the move broke it" and "the rename
   broke it", which is the same unattributable-red hazard ADR-0010's own
   prerequisite section forbids one level up ("an instrument built in the same
   arc as the change it detects has no green baseline").
2. **Declarative descriptors live under ``catalogs/``; imperative modules live
   beside it.** When the later slices move ``compose`` / ``atoms`` /
   ``the_one`` / ``cd_register`` in, they land at ``srmech/cascade/*.py`` and
   the TOML stays under ``srmech/cascade/catalogs/``. The two kinds of content
   are visually separated at the top of the package rather than interleaved.
3. **Every catalog directory carries an ``__init__.py`` marker.** Two of the
   three moved directories already did; ``worked_instances`` and the new
   ``alias_catalog`` were given one. The marker is what makes wheel inclusion
   unconditional under BOTH build backends rather than resting on each one's
   package-data heuristics, and it is where the directory documents itself. It
   also rules out naming a catalog directory after a Python keyword — which is
   why the leaf is ``class_catalog`` and not ``class``.

What lives here today
---------------------
``catalogs/`` — the **built-in** descriptor catalogs, moved out of
``srmech/amsc/_research/`` where ADR-0010 found them buried:

* ``catalogs/class_catalog/`` — ``[class]`` descriptors (``srmech.dsl.make_class``)
* ``catalogs/cascade_catalog/`` — ``[cascade]`` op descriptors (the DSL chain runner)
* ``catalogs/alias_catalog/`` — ``[[alias]]`` / ``[genome.type_aliases]`` descriptors
* ``catalogs/worked_instances/`` — worked-instance descriptors

The **user-supplied** counterparts are NOT here: ``register_class_dir`` /
``register_catalog_dir`` / ``register_alias_dir`` and their ``SRMECH_*_PATH``
env-vars are the extension point ADR-0010 assigns to ``srmech.external.*``.
Built-in descriptors ship inside the wheel; user descriptors are registered at
runtime and attested to the user's own descriptor hash.

The **loaders** stay at :mod:`srmech.dsl` — ADR-0010 §"``make_class``
re-homed" moves the *descriptors*, not the functions, and ``srmech.dsl`` was
already their correct home.

This module deliberately imports nothing: ``import srmech.cascade`` must stay
free, because the loaders reach the TOML by path (``CLASS_CATALOG_DIR`` and
peers) rather than by import.
"""

from __future__ import annotations

__all__: list = []
