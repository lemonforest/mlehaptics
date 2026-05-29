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

# v0.3.0 — Task #199 profile pattern. Top-level `srmech.profile("name")`
# is the activation API; `srmech.list_profiles()` enumerates installed
# profiles. The loader walks `importlib.metadata.entry_points(group=
# "srmech.profiles")` eagerly on first access (ADR-0001 §5.5).
from .profile_loader import (
    AbiMismatchError,
    InvalidProfileError,
    Profile,
    ProfileError,
    ProfileNotFoundError,
    ProfileSchemaVersionError,
    ProfileStatus,
    SmokeTestFailedError,
    list_profiles,
    profile,
)

# v0.4.6rc2 — out-of-band introspection (talk-to-running-PID API).
# Per user direction 2026-05-28: long sweeps (30 min to hours) become
# observable from a second process via a file-based status backend at
# ``~/.srmech/run-{pid}-{start_time_ns}.ndjson``. OFF by default; the
# import itself MUST NOT create any file. The env-var opt-in
# ``SRMECH_PUBLISH_STATUS=1`` activates a process-wide publish context
# at import time per the spec — implemented via the
# ``_maybe_auto_publish`` hook below.
from . import introspect as _introspect

_introspect._maybe_auto_publish()

__all__ = [
    "__version__",
    # profile loader API (Task #199, ADR-0001)
    "AbiMismatchError",
    "InvalidProfileError",
    "Profile",
    "ProfileError",
    "ProfileNotFoundError",
    "ProfileSchemaVersionError",
    "ProfileStatus",
    "SmokeTestFailedError",
    "list_profiles",
    "profile",
    # introspect module exposure (v0.4.6rc2)
    "introspect",
    # self-recognition root (v0.5.0rc11)
    "warmup_all",
]

# Expose ``srmech.introspect`` as a regular attribute (the module is
# already importable via the ``from . import introspect`` above; this
# just records it for symbol-exposure tests that check
# ``hasattr(srmech, "introspect")``).
introspect = _introspect

# v0.5.0rc11 — Self-recognition root. ``warmup_all()`` is THE single
# registration entry-point: it imports every submodule that registers
# ToolEntries (``srmech.bus`` / ``srmech.introspect``) so the registry
# is fully populated no matter how srmech was entered. Per user
# direction 2026-05-29 it fires here in ``__init__`` — substrate-
# coherent: every consumer sees the complete tool-schema from t=0,
# permanently closing the orphan-registration bug class (the rc9 bus
# miss). Placed at the END of package init (after ``__version__`` /
# profile loader / introspect are all set up) so the
# ``from .amsc.tool_schema import warmup_all`` import — which fully
# initialises ``srmech.amsc`` — sees a complete core ``srmech``
# namespace and cannot trip an import cycle.
from .amsc.tool_schema import warmup_all  # noqa: E402

warmup_all()
