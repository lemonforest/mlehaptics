"""Built-in descriptor catalogs — the declarative half of the composition layer.

Moved here from ``srmech/amsc/_research/`` by ADR-0010's first execution slice
(rc364). The ADR's reasoning, verbatim: the ``[class]`` / ``[cascade]`` TOML
descriptors were *"buried in ``amsc``"* — a namespace reserved for the
collector/catalog/attestation framework it was named for — while the layer that
actually owns them is composition.

Four sibling directories, one per descriptor KIND, each named for the TOML
section it declares:

===========================  ==========================================  =============================
directory                    declares                                     loader
===========================  ==========================================  =============================
``class_catalog/``           ``[class]``                                  :mod:`srmech.dsl._class_catalog`
``cascade_catalog/``         ``[cascade]``                                :mod:`srmech.dsl._catalog`
``alias_catalog/``           ``[[alias]]`` / ``[genome.type_aliases]``    :mod:`srmech.dsl._alias`
``worked_instances/``        worked-instance descriptors                  ``tests/test_ssot_coherence_scan.py``
===========================  ==========================================  =============================

Each directory is a package (carries an ``__init__.py``) so that BOTH build
backends — scikit-build-core's ``wheel.packages`` and hatchling's
``[tool.hatch.build.targets.wheel].packages`` — include its TOML
unconditionally, rather than by each backend's own package-data heuristic. That
matters: rc364 shipped this move precisely BECAUSE two alias descriptors were
sitting under ``tests/data/``, which ``sdist.include`` carries and the wheel
does not, so the migration path one of them documents raised ``FileNotFoundError``
on every wheel install.

These are the **built-in** catalogs. User-supplied directories — registered via
``register_class_dir`` / ``register_catalog_dir`` / ``register_alias_dir`` or
the ``SRMECH_CLASS_PATH`` / ``SRMECH_CATALOG_PATH`` / ``SRMECH_ALIAS_PATH``
env-vars — are the ``srmech.external.*`` extension point and never live here.
"""

from __future__ import annotations

__all__: list = []
