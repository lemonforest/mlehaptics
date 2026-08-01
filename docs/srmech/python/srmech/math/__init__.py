"""``srmech.math`` — the GENERAL-ALGEBRA / A–N-PRIMITIVE domain.

ADR-0010 (*namespace declustering*) splits ``srmech`` into **domains** (named by
field), **structure-homes** (named by what they *are*), **provenance**
(``amsc``, shrunk back to attestation) and **cross-cutting meta**
(``introspect``). ``srmech.math`` is a *domain* home — A.2's SECOND-largest
destination (**22 modules**): the 14 A–N primitives, the general carriers, and
the general-purpose mathematics (``rational`` / ``primes`` / ``laplacian`` /
``cyclic`` / ``poly`` and kin) that ``amsc`` accreted but never was.

It is named by what the field IS — general mathematics — rather than by any one
mechanism, the domain-vs-structure distinction ADR-0010 draws (``srmech.cascade``
is a structure home; this is a domain, like ``srmech.apokatastasis``).

**This slice (rc372) opens the namespace with its general-ALGEBRA roster** — the
three modules whose mathematics is domain-neutral algebra rather than a
special-functions family: ``octonion`` (the discrete octonion Moufang loop over
4-bit bytes), ``kepler`` (the Class-K equation-of-centre / pin-slot shape
projection), and ``modular_linalg`` (GF(p) finite-field linear algebra). The
last is the **apokatastasis over-count reassignment** ADR-0010 Amendment H.2
recorded: A.2 lumped ``modular_linalg`` into the elliptic/modular-forms count by
name-similarity, but its mathematics is 𝔽_p Gaussian elimination — a general
math primitive — so it lands HERE, not in ``srmech.apokatastasis``.

The new-namespace template (rc370's ``srmech.apokatastasis``, `#T1034`) holds:

1. **A slice relocates a PARENT; it does not rename the LEAF.** ``octonion`` /
   ``kepler`` / ``modular_linalg`` keep their leaf names verbatim across the move
   (B.1 rule 1). One slice changes exactly one thing — *where* a module lives.
2. **A module's ops are discovered through its own submodule, not re-exported
   here.** The Rosetta walk reaches ``srmech.math.octonion`` /
   ``srmech.math.kepler`` / ``srmech.math.modular_linalg`` by
   ``pkgutil.walk_packages`` and reads each submodule's own ``__all__``; this
   package ``__init__`` re-exports nothing (mirrors ``srmech.music`` /
   ``srmech.apokatastasis``). So ``__all__`` here stays empty until the domain
   grows a package-level surface.
3. **The new-namespace SETUP is two edits beyond a drop-in slice.** Creating
   this ``__init__`` and appending ``srmech.math`` to the Rosetta walk roots
   (``tests/rosetta_roots.py`` + the single-source pin), AND naming the subset
   that has landed in the census move-map (``NAMED_DEPARTURES``), are the
   template every remaining member of the 22-module bucket follows.

The carrier ladder / carrier spectrum row (``carrier_ladder`` /
``carrier_spectrum`` and kin) is DEFERRED to the carriers slice (rc374); this
slice is the general-algebra opener only.

This module deliberately imports nothing: ``import srmech.math`` must stay free.
The domain's callables live in submodules, each importing the carriers it needs
(``srmech.amsc._native`` / ``srmech.amsc.cyclic`` / ``srmech.amsc.rational``)
directly.
"""

from __future__ import annotations

__all__: list = []
