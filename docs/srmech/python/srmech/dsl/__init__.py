"""srmech.dsl — cascade DSL (v0.5.0rc8; task #235 / ADR-0002 Phase 2-v2).

The fluent :func:`chain` builder composes the 11 cascade-catalog ops
(``srmech.cascade.*``) + the loop / fold / reduce control-flow
primitives into a single executable pipeline. The runner reads the TOML
cascade-catalog descriptors at construction time and dispatches through
the corresponding ``srmech.cascade.*`` Python entry points (which
themselves route to C peers when ``HAS_NATIVE`` is True).

Per-stage events emit ``dsl.<chain_name>.stage.<N>`` lines to the
introspection bus when a publish context is active
(``srmech.introspect.publish()`` or ``SRMECH_PUBLISH_STATUS=1``);
observable from a second process via ``srmech status`` or
``srmech bus tap``.

Quick start
-----------
::

    from srmech.dsl import chain

    # Single op.
    result = chain().then("magnitude").run(-3.14)
    # → 3.14

    # Reduce over a sequence.
    result = chain().reduce("cyclic_gcd").run([12, 8, 4])
    # → 4

    # Loop a sub-chain.
    sub = chain("inner").then("chiral_flip")
    result = chain("outer").loop(2, sub).run([1, 2, 3])
    # → [1, 2, 3]  (two flips cancel)

    # List available cascade ops (read from the TOML catalog).
    from srmech.dsl import list_cascade_ops
    list_cascade_ops()
    # → ['best_rational_signed', 'chiral_dual', 'chiral_flip',
    #    'cyclic_gcd', 'magnitude', 'net_chirality',
    #    'pin_slot_at_zero', 'reorient']

Framework reading
-----------------
The DSL is Class M (cross-class bind) ∘ Class F (declarative render of
the cascade structure) ∘ Class E (catalog enumeration of cascade ops).
loop / fold / reduce are Class I (cyclic repetition) / Class M
(accumulator bind); no new primitive class is introduced.
"""

from __future__ import annotations

from ._catalog import (
    CATALOG_DIR,
    get_descriptor,
    list_cascade_ops,
    load_catalog,
    lookup_cascade_op,
    register_catalog_dir,
)
from ._chain import Chain, chain
from ._class_catalog import (
    CLASS_CATALOG_DIR,
    CatalogClass,
    get_class_descriptor,
    list_classes,
    load_class_catalog,
    make_class,
    register_class_dir,
)
from ._class_surface import (
    describe_class,
    generate_class_descriptor,
    list_class_surface,
    run_class_method,
)
from ._alias import (
    ALIAS_CATALOG_DIR,
    alias,
    build_aliases_from_toml_str,
    list_alias_descriptors,
    load_aliases_toml,
    register_alias_dir,
    resolve_alias_descriptor,
)
from ._tool_surface import list_catalog_ops, list_ops, run_toml_chain
from ._toml_chain import (
    build_chain_from_dict,
    build_chain_from_toml,
    build_chain_from_toml_str,
    load_chain_toml,
)

__all__ = [
    # Fluent builder
    "Chain",
    "chain",
    # Catalog introspection
    "list_cascade_ops",
    "lookup_cascade_op",
    "load_catalog",
    "get_descriptor",
    "CATALOG_DIR",
    # Bring-your-own external cascade-catalog dirs (F289 D2)
    "register_catalog_dir",
    # TOML loader
    "load_chain_toml",
    "build_chain_from_toml",
    "build_chain_from_toml_str",
    "build_chain_from_dict",
    # Declarative one-shot surface (v0.5.0rc12 — LLM tool entry points)
    "run_toml_chain",
    "list_catalog_ops",
    # §17 U3 (rc45): unified op-discovery — cascade-ops + catalog-chains in one list
    "list_ops",
    # rc261 (§95.2 / #1407): config-driven FUNCTION ALIASING — bind a user's own name to
    # any srmech.* function via TOML (the domain-agnostic naming layer; ADR-0004).
    "alias",
    "build_aliases_from_toml_str",
    "load_aliases_toml",
    # rc364 (ADR-0010 amendment B): the naming layer gets the same catalog shape the
    # class layer already had — a shipped descriptor dir + a registration API. Without
    # it, rc362's and rc271's alias descriptors landed in tests/data/ by default rather
    # than by decision, and tests/** is NOT in the wheel.
    "ALIAS_CATALOG_DIR",
    "register_alias_dir",
    "list_alias_descriptors",
    "resolve_alias_descriptor",
    # User-declared classes from [class] TOML (#962 Part 2; rc39) — declarative,
    # generic runtime objects; methods bind to cascade ops by dotted path.
    "make_class",
    "CatalogClass",
    "list_classes",
    "get_class_descriptor",
    "load_class_catalog",
    "register_class_dir",
    "CLASS_CATALOG_DIR",
    # Class-aware DSL surface (rc40) — one-shot introspect + run for CLI / LLM
    "describe_class",
    "list_class_surface",
    "run_class_method",
]
