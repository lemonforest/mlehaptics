"""``srmech.physics`` — the PHYSICS domain (QM / QFT / SM).

ADR-0010 (*namespace declustering*) splits ``srmech`` into **domains** (named by
field), **structure-homes** (named by what they *are*), **provenance**
(``amsc``, shrunk back to attestation) and **cross-cutting meta**
(``introspect``). ``srmech.physics`` is a *domain* home — the destination the
ADR's namespace table names ``srmech.physics.* | domain | the qm layer
(QM/QFT/SM)``. It is the LAST of ADR-0010's new namespaces to land, and it is a
whole SUBPACKAGE move rather than a flat module batch: the 15-module ``qm``
subpackage relocates verbatim to ``srmech.physics.qm`` (v0.9.0rc381, `#T1052`).

It is named by what the field IS — the physics substrate — rather than by any
one mechanism, the domain-vs-structure distinction ADR-0010 draws
(``srmech.cascade`` is a structure home; this is a domain, like
``srmech.math`` / ``srmech.biology`` / ``srmech.apokatastasis``).

**This slice (rc381) opens the namespace with the whole ``qm`` subpackage**
(single_particle / spin / bell / potentials / relativistic / propagators /
pseudo_hermitian / gauge / sm / octonion / quaternion / hurwitz / so8 / so9 /
triality). Because ``srmech.qm`` has been a public API since v0.4.0, the break
is SOFT for one release: ``srmech.qm`` survives as a DEPRECATION ALIAS that
re-exports ``srmech.physics.qm`` and warns (``srmech/qm/__init__.py``). The
alias will be removed in a future release. The qm C peers (``srmech_octonion_*``
/ ``srmech_quaternion_*`` / the so8/triality/gauge/sm kernels) are
capability-named and DO NOT rename — the ABI stays 10.

The new-namespace / subpackage-move template (rc370's ``srmech.apokatastasis`` /
rc372's ``srmech.math`` / rc375's ``srmech.biology`` / rc377's
``srmech.cascade``, `#T1034`) holds:

1. **A slice relocates a PARENT; it does not rename the LEAF.** The 15 ``qm``
   submodules keep their leaf names verbatim across the move (B.1 rule 1). One
   slice changes exactly one thing — *where* the subpackage lives. Here the
   moved parent is itself a subpackage, so the dotted depth grows by one
   (``srmech.qm.spin`` -> ``srmech.physics.qm.spin``), but no leaf is renamed.
2. **A module's ops are discovered through its own submodule, not re-exported
   here.** The Rosetta walk reaches ``srmech.physics.qm`` and its submodules by
   ``pkgutil.walk_packages`` (the walk root is the DOMAIN, ``srmech.physics``,
   which recurses into ``qm``) and reads each submodule's own ``__all__``; this
   package ``__init__`` re-exports nothing (mirrors ``srmech.math`` /
   ``srmech.biology``). So ``__all__`` here stays empty.
3. **The new-namespace SETUP is two edits beyond a drop-in slice.** Creating
   this ``__init__`` and appending ``srmech.physics`` to the Rosetta walk roots
   (``tests/rosetta_roots.py`` + the single-source pin), AND migrating
   ``srmech.physics`` from ``_ADR0010_NEW_NAMESPACES`` to
   ``_ADR0010_EXISTING_DESTINATIONS`` in the same rc, are the template the arc's
   earlier domain slices established.

This module deliberately imports nothing: ``import srmech.physics`` must stay
free. The domain's callables live under ``srmech.physics.qm.*``, each submodule
importing the carriers it needs (``srmech._native`` / ``srmech.math.*`` / its
intra-qm siblings) directly.
"""

from __future__ import annotations

__all__: list = []
