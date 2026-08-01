"""THE canonical Rosetta walk roots — one definition, four consumers.

rc361 (`#T1034`), the first prerequisite rc of the ADR-0010 declustering arc.

WHY THIS FILE EXISTS
====================
Before rc361 this 12-entry tuple was HARDCODED IN FOUR PLACES:

  * ``tests/test_rosetta_completeness.py``        ``_ROOTS``
  * ``tests/conftest.py``                         ``_ROSETTA_ROOTS``
  * ``tests/test_rosetta_transitive_standalone.py`` ``_ROOTS``
  * ``notes/_rosetta_inventory.py``               ``ROOTS``

All four were MEASURED identical in content at rc361 (same 12 entries, same
order; ``notes/`` spelled it as a ``list`` rather than a ``tuple`` — the only
divergence, and a shape one, not a value one). Each copy additionally carried
its own hand-maintained comment saying "keep this IDENTICAL to the other
three", which is the tell: four sites agreeing by *convention* is a
convention that eventually stops holding.

WHY IT MATTERS FOR THE ARC, AND NOT MERELY FOR TIDINESS
=======================================================
This tuple is the DENOMINATOR of the Rosetta ledger. ADR-0010 moves ~73
modules between top-level namespaces, and a root that is not listed here is
a namespace whose ops are simply not walked — so they vanish from
``rosetta_live_objects()`` and the ledger's STALE assertion fires (a
classified row with no live op) while its UNCLASSIFIED assertion (a live op
with no bucket) never does. The failure therefore reads as "the ledger has
stale rows", which is the symptom of a *deletion*, when what actually
happened was a *move*. Four copies means four chances to update one and
forget another, and a partial update produces exactly that misleading
diagnosis.

rc361 collapses the four to this one definition so the later rename edits a
single tuple.

⚠️ DELIBERATELY NOT WIDENED AT rc361. ADR-0010's new namespaces
(``srmech.math`` / ``physics`` / ``biology`` / ``apokatastasis`` /
``cascade`` / ``external``) DO NOT EXIST YET, and a root naming a
non-existent package is silently skipped by every walker here
(``importlib.import_module`` raises, the ``except`` continues) — so
pre-adding them would look like preparation while changing nothing, and
would make the eventual real move indistinguishable from the no-op. Widen
this tuple in the SAME rc that moves the modules, never before. The gap is
asserted, not merely described, in
``tests/test_rosetta_roots_single_source_rc361.py``.

⚠️ AND WIDENED AT rc362, FOR EXACTLY THAT REASON. ``srmech.music`` was
listed above as not-yet-existing until v0.9.0rc362 landed the acoustic
slice; it is the first of ADR-0010's new namespaces to become real, so it
is appended below IN THE SAME rc as the modules, which is the rule stated
positively. Nine ``srmech.music.*`` ops enter the walk with it, one of them
(``bell_partials``) as a ``non_compute``/``composes_c`` row — the annex
ratchets in ``tests/test_annex_ratchet_rc177.py`` and ``…_rc183.py`` move
by exactly that +1, and the other eight are compute buckets. If a future
namespace lands and the split moves by anything other than its
``non_compute`` row count, that is a finding rather than a pin bump.

⚠️ THIS MODULE IMPORTS NOTHING, ON PURPOSE. ``notes/_rosetta_inventory.py``
lives OUTSIDE the package and outside ``tests/``, so it cannot ``import``
from ``tests/`` on ``sys.path``; it loads this file BY PATH
(``importlib.util.spec_from_file_location``). That works only while this
module has no imports of its own to resolve. Keep it dependency-free: no
``pytest``, no ``srmech``, no stdlib beyond nothing at all.

HISTORY OF THE ROOT SET (why it is 12 and not 3)
================================================
The walk began at the three compute roots (``amsc`` / ``qm`` /
``signal_processing``) and was extended three times, each time because a
bare-C host genuinely runs that surface too and it therefore owes a C
mirror:

  * rc177 annex — ``bus`` + ``dsl`` (the IPC bus + the cascade-chain /
    ``[class]`` interpreter): +39 rows, all ``non_compute``.
  * rc183 HOST-GLUE annex — ``mcp`` + ``cli`` + ``llm`` (the MCP tool
    surface, the CLI dispatch grammar, the optional LLM agent driver):
    +24 rows, all ``non_compute``.
  * rc218 PARITY-COMPLETENESS annex — ``spectral`` + ``rbs_lm`` +
    ``introspect`` + ``profile_loader``, the last four untracked
    Python-only modules: +30 rows.

See ``tests/test_rosetta_completeness.py`` and ``ROSETTA_LEDGER.md`` for the
per-annex row accounting and the issue history.
"""

#: The public submodule roots of the Rosetta ledger walk.
#:
#: ORDER IS PART OF THE VALUE: the walk de-duplicates by canonical
#: ``defined_at`` (``<module>.<qualname>``) via ``setdefault``, so when one
#: object is reachable from two roots the FIRST root wins the row. Reordering
#: would not change the SET of ops but can change which module a re-exported
#: op is attributed to. Append; do not reshuffle.
ROSETTA_ROOTS = (
    "srmech.amsc",
    "srmech.qm",
    "srmech.signal_processing",
    "srmech.bus",
    "srmech.dsl",
    "srmech.mcp",
    "srmech.cli",
    "srmech.llm",
    "srmech.spectral",
    "srmech.rbs_lm",
    "srmech.introspect",
    "srmech.profile_loader",
    # v0.9.0rc362 — the ADR-0010 srmech.music domain namespace (the
    # acoustic surface). APPENDED, per the order-is-part-of-the-value note.
    "srmech.music",
    # v0.9.0rc364 — the ADR-0010 srmech.cascade STRUCTURE namespace, landed by
    # the arc's first execution slice (the built-in [class]/[cascade]/[[alias]]
    # /worked-instance catalogs moved out of srmech/amsc/_research/).
    #
    # ⚠️ IT CONTRIBUTES ZERO ROWS TODAY, AND THAT IS THE POINT OF ADDING IT
    # NOW RATHER THAN LATER. The package exists and imports cleanly, so the
    # walk genuinely reaches it and MEASURES an empty public surface — the
    # namespace holds descriptors, not callables, and its __init__ declares
    # __all__ = []. That is a real zero census, not the silent ImportError
    # skip rc361 refused: a non-existent root is EMPTY-because-unsupported,
    # an existing empty root is 0-because-measured, and only the second can
    # go red the moment something lands in it. When a later slice moves
    # `compose` / `atoms` / `the_one` / `cd_register` in, their rows enter the
    # denominator with no root edit — which is the sequencing this file asks
    # for, done at the earliest honest moment rather than the latest.
    "srmech.cascade",
    # v0.9.0rc370 — the ADR-0010 srmech.apokatastasis DOMAIN namespace (the
    # elliptic / modular / theta / q-series row, A.2's LARGEST bucket at 31
    # modules / 41%), landed by its first module-moving slice
    # (elliptic_partial_fraction). APPENDED, per the order-is-part-of-the-value
    # note. Unlike srmech.cascade (rc364, zero ops), this root enters carrying
    # ONE walked op — the first DOMAIN-with-a-registered-op to land — so the
    # ledger denominator grows by exactly one c_dispatched row this rc, and the
    # walk must reach it in the SAME rc the module moves or the move would read
    # as a deletion (a classified row whose live op vanished).
    "srmech.apokatastasis",
    # v0.9.0rc372 — the ADR-0010 srmech.math DOMAIN namespace (the 14 A-N
    # primitives + carriers + general math, A.2's SECOND-largest bucket at 22
    # modules), landed by its FIRST slice: the general-algebra roster
    # octonion / kepler / modular_linalg. APPENDED (order-is-part-of-the-value).
    # Like srmech.apokatastasis (and unlike the zero-op srmech.cascade), this
    # root enters carrying WALKED ops (10 names across the 3 modules — 7
    # c_dispatched, 3 composition), so the walk MUST reach it in the SAME rc the
    # modules move or the moves would read as deletions. modular_linalg is the
    # H.2 apokatastasis over-count reassignment: GF(p) finite-field LA is a
    # general math primitive, not a modular-forms module, so it lands HERE.
    "srmech.math",
    # v0.9.0rc375 — the ADR-0010 srmech.biology DOMAIN namespace (the biological
    # substrate: genome persistence / gene-expression + the carriers it composes),
    # landed by its ONLY slice: the whole 4-module roster genome / plasmid / q8 /
    # coupling in one move (A.2's fifth destination, 4 modules). APPENDED
    # (order-is-part-of-the-value). Like srmech.apokatastasis / srmech.math and
    # UNLIKE the zero-op srmech.cascade, this root arrives carrying WALKED ops (the
    # genome / q8 / coupling operator surface), so the walk MUST reach it in the
    # SAME rc the modules move or the moves would read as deletions. genome is the
    # arc's single largest C surface; its srmech_genome_* C symbols are
    # capability-named and DO NOT rename, so the ABI stays 10.
    "srmech.biology",
    # v0.9.0rc379 (`#T1050`) — the srmech.chemistry DOMAIN namespace
    # (reaction networks as exact-integer linear algebra). NOT an ADR-0010
    # declustering destination — a BRAND-NEW domain born here, not migrated — so
    # it is absent from both ADR-0010 tuples in
    # test_rosetta_roots_single_source_rc361.py (the blindness test asserts ADR
    # destinations are present; extra roots are fine). It arrives carrying FOUR
    # walked rows: 3 composition_of_c (balance_reaction / conservation_laws /
    # deficiency) + 1 c_dispatched (parse_formula, backed by srmech_parse_formula).
    "srmech.chemistry",
)
