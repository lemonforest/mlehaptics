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
)
