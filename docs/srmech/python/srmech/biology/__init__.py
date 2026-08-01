"""``srmech.biology`` — the BIOLOGICAL-substrate domain.

ADR-0010 (*namespace declustering*) splits ``srmech`` into **domains** (named by
field), **structure-homes** (named by what they *are*), **provenance**
(``amsc``, shrunk back to attestation) and **cross-cutting meta**
(``introspect``). ``srmech.biology`` is a *domain* home — A.2's fifth
destination (**4 modules**): the genome persistence / expression surface and
the three carriers it composes over (``genome`` / ``plasmid`` / ``q8`` /
``coupling``).

It is named by what the field IS — the biological substrate — rather than by
any one mechanism, the domain-vs-structure distinction ADR-0010 draws
(``srmech.cascade`` is a structure home; this is a domain, like
``srmech.math`` / ``srmech.apokatastasis``).

**This slice (rc375) opens AND drains the namespace with its whole 4-module
roster** — the biology bucket is small enough to move in one slice:
``genome`` (the telomere-partitioned on-disk chromosome set + gene-expression
cascade, the arc's single largest C surface), ``plasmid`` (the
section-counted extrachromosomal strand), ``q8`` (the discrete quaternion
carrier the genome's octonion fibers ride), and ``coupling`` (the
signed-sum-squared / resonant-spectrum coupling meter). The genome's C peers
(``srmech_genome_*``, ``srmech_q8_*``, ``srmech_coupling_*``) are
capability-named and DO NOT rename — the ABI stays 10.

The new-namespace template (rc370's ``srmech.apokatastasis`` / rc372's
``srmech.math``, `#T1034`) holds:

1. **A slice relocates a PARENT; it does not rename the LEAF.** ``genome`` /
   ``plasmid`` / ``q8`` / ``coupling`` keep their leaf names verbatim across the
   move (B.1 rule 1). One slice changes exactly one thing — *where* a module
   lives.
2. **A module's ops are discovered through its own submodule, not re-exported
   here.** The Rosetta walk reaches ``srmech.biology.genome`` and kin by
   ``pkgutil.walk_packages`` and reads each submodule's own ``__all__``; this
   package ``__init__`` re-exports nothing (mirrors ``srmech.math`` /
   ``srmech.apokatastasis``). So ``__all__`` here stays empty.
3. **The new-namespace SETUP is two edits beyond a drop-in slice.** Creating
   this ``__init__`` and appending ``srmech.biology`` to the Rosetta walk roots
   (``tests/rosetta_roots.py`` + the single-source pin), AND landing the roster
   in the census move-map (``NAMED_DEPARTURES`` / ``LANDED``), are the template
   the arc's earlier domain slices established.

This module deliberately imports nothing: ``import srmech.biology`` must stay
free. The domain's callables live in submodules, each importing the carriers it
needs (``srmech._native`` / ``srmech.math.*`` / its intra-biology siblings)
directly.
"""

from __future__ import annotations

__all__: list = []
