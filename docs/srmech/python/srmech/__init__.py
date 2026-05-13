"""srmech — Stored-Relationship Mechanism research package.

Phase 2 (Task #197) ships srmech as the home of the Attested
Multi-Source Collector (AMSC) framework — previously living inside
ephemerides-spectral's ``_research/`` mirror. The framework is the
mechanical-provenance discipline (every ground-proof row carries
mandatory attestation) generalised so downstream packages can
declare their own catalog SSOTs and consume them through one universal
bridge surface (``srmech.amsc.catalog``).

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
