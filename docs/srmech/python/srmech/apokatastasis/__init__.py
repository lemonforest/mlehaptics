"""``srmech.apokatastasis`` — the ELLIPTIC / MODULAR / THETA / q-SERIES domain.

ADR-0010 (*namespace declustering*) splits ``srmech`` into **domains** (named by
field), **structure-homes** (named by what they *are*), **provenance**
(``amsc``, shrunk back to attestation) and **cross-cutting meta**
(``introspect``). ``srmech.apokatastasis`` is a *domain* home — the LARGEST
single destination in A.2 (**31 modules, 41 % of the moves**): the elliptic
hypergeometric row (theta / EllMonomial / EllRatio / ThetaSum carriers, the
Cₙ / Aₙ reducers, the WZ / Gosper / Zeilberger certificates), the modular and
q-series machinery, and the Riemann-theta multisum surface.

The name is the Greek *ἀποκατάστασις* — "restoration / reconstitution to the
original state": the elliptic reduction row RECONSTITUTES a theta product as its
exact expanded form (and back), the domain's defining move. It is named by what
the field IS about rather than by the mechanism, which is the domain-vs-structure
distinction ADR-0010 draws (``srmech.cascade`` is a structure home; this is a
domain).

**This package is ADR-0010's first DOMAIN-with-a-registered-op move, so it also
sets the new-namespace template** (rc370, `#T1034`; contrast ``srmech.cascade``
at rc364, which landed a namespace carrying only descriptors and ZERO callables):

1. **A slice relocates a PARENT; it does not rename the LEAF.** The first module
   in, ``elliptic_partial_fraction``, kept its leaf name verbatim across the
   move (B.1 rule 1). One slice changes exactly one thing — *where* a module
   lives — so a red gate has exactly one possible cause.
2. **A module's ops are discovered through its own submodule, not re-exported
   here.** The Rosetta walk reaches ``srmech.apokatastasis.elliptic_partial_
   fraction`` by ``pkgutil.walk_packages`` and reads that submodule's own
   ``__all__``; the package ``__init__`` re-exports nothing (mirrors how
   ``srmech.music`` leaves ``harmonics`` a sibling submodule). So ``__all__``
   here stays empty until the domain grows a package-level surface.
3. **The new-namespace SETUP is two edits beyond a drop-in slice.** Creating
   this ``__init__`` and appending ``srmech.apokatastasis`` to the Rosetta walk
   roots (``tests/rosetta_roots.py`` + the single-source pin), AND naming the
   subset that has landed in the census move-map (``NAMED_DEPARTURES``), are the
   template every remaining member of the 31-module bucket follows.

This module deliberately imports nothing: ``import srmech.apokatastasis`` must
stay free. The domain's callables live in submodules (``elliptic_partial_
fraction`` today), each importing the carriers it needs (``srmech.apokatastasis.ellbase``
/ ``srmech.apokatastasis.thetasum``) directly.
"""

from __future__ import annotations

__all__: list = []
