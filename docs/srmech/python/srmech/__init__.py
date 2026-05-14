"""srmech — Stored-Relationship Mechanism research package.

Phase 2 (Task #197) ships srmech as the home of the Attested
Multi-Source Collector/Catalog (AMSC) framework — previously living
inside ephemerides-spectral's ``_research/`` mirror. The framework
is the mechanical-provenance discipline (every ground-proof row
carries mandatory attestation) generalised so downstream packages
can declare their own catalog SSOTs and consume them through one
universal bridge surface (``srmech.amsc.catalog``).

**Naming note — Collector or Catalog?** Both work. At collection
time (T1 / T3 lifecycle stages), AMSC is *collecting* attested rows
from upstream archives via its adapter classes — *Attested Multi-
Source Collector*. After collection, when the rows are committed
as NDJSON SSOTs and downstream consumers read them through the
universal bridge, AMSC is also a *Catalog* of attested data —
*Attested Multi-Source Catalog*. Both names abbreviate to AMSC and
both are correct; pick whichever fits the lifecycle stage you're
describing.

The Phase 3 cutover (planned) rewires ephemerides-spectral's bridge
to import from ``srmech.amsc.*`` instead of its in-tree mirror; the
catalog SSOTs do NOT migrate (ephemerides's 19 catalogs stay where
they are, registered into srmech via
``register_attested_root(path, source=...)`` at package-import time).

Public surfaces
---------------
* ``srmech.amsc`` — Attested Multi-Source Collector framework.
* ``srmech.__version__`` — package version string (SSOT in
  ``srmech.version``).
"""

from .version import __version__

__all__ = ["__version__"]
