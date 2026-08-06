"""srmech — Stored-Relationship Mechanism research package.

Public surfaces
---------------
* ``srmech.describe()`` — **START HERE**: the capability index
  (shape/counts). Drill into
  ``srmech.introspect.tool_schema.get_tool_schema()`` for the per-op
  registry. The same object is bound as ``srmech.describe`` and as
  ``srmech.introspect.describe``; since rc407 the payload's ``tools``
  block carries that drill-down route in-band, so a JSON / MCP
  consumer — which has no ``dir()`` — is told where the registry
  lives. It is a Python import route: ``get_tool_schema`` is not
  itself a registered tool, so an MCP-only client reads it as a
  location, not as a call.
* ``srmech.introspect`` — the self-recognition package. It holds the
  op registry (``tool_schema``), the operand carriers
  (``carrier_schema``), the responsion surface
  (``responsion_schema``), and the out-of-band "talk to a running
  srmech by PID" API (``publish`` / ``list`` / ``by_pid``), which is
  OFF by default and writes no file on import.
* ``srmech.native_status`` — the one call that answers whether
  ``libsrmech`` loaded, ABI-matched, and is really dispatching, as
  against the pure-Python fallback. ``srmech.describe()['native']``
  is the same status folded into the index.
* ``srmech.warmup_all`` — THE registration entry point: it imports
  every submodule that registers ops, so the registry is complete no
  matter how srmech was entered (library / CLI / MCP / Anthropic
  adapter). Package import already calls it; call it again yourself
  only after registering something new.
* ``srmech.amsc`` — the Attested Multi-Source Collector/Catalog
  framework, and the on-disk crystallisation of the Mathematical
  Provenance Method: every ground-proof row carries a mandatory
  attestation block, and a downstream package declares its own
  catalog SSOT through
  ``srmech.amsc.catalog.register_attested_root(path, source=...)``.
* **The profile loader** — ``srmech.profile`` activates a named
  profile and ``srmech.list_profiles`` enumerates the installed ones;
  ``srmech.Profile`` and ``srmech.ProfileStatus`` are the records they
  hand back. Every failure is a ``srmech.ProfileError`` or a subclass
  of it: ``srmech.ProfileNotFoundError``,
  ``srmech.InvalidProfileError``,
  ``srmech.ProfileSchemaVersionError``,
  ``srmech.SmokeTestFailedError``, ``srmech.AbiMismatchError``.
* ``srmech.__version__`` — package version string (SSOT in
  ``srmech.version``).

**Naming note — Collector or Catalog?** Both work, and both
abbreviate to AMSC. At collection time the adapters are *collecting*
attested rows from upstream archives — *Attested Multi-Source
Collector*. Once those rows are committed as NDJSON SSOTs and read
back through the universal bridge, the same object is a *Catalog* of
attested data. Pick whichever fits the lifecycle stage you are
describing.

**Why this index is written out here** and not left to
``help(srmech)``. It is not that pydoc hides anything — it renders
``__all__`` regardless, and ``describe`` appears 13 times in the dump.
The defect this replaces was BURIAL and CURATION. Measured rc407: the
pydoc dump of this package is ~45,900 characters over ~1,018 lines;
the DESCRIPTION block a reader actually scans is characters 122-2,283;
and the first FUNCTIONS entry for ``describe()`` sits at character
~19,600, 43% in, below nine profile-loader symbols. A reader who scans
the top and stops sees exactly what this docstring lists — and through
rc406 it listed two things, ``srmech.amsc`` and ``srmech.__version__``,
so a census over the 15 names in ``__all__`` found ONE of them here.
The entry point is now first, and every exported name is present.
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
    # top-level self-recognition help-anchor (v0.6.0rc15)
    "describe",
    # top-level native-dispatch status (v0.5.0rc19; issue #733)
    "native_status",
    # self-recognition root (v0.5.0rc11)
    "warmup_all",
]

# Expose ``srmech.introspect`` as a regular attribute (the module is
# already importable via the ``from . import introspect`` above; this
# just records it for symbol-exposure tests that check
# ``hasattr(srmech, "introspect")``).
introspect = _introspect

# v0.5.0rc19 — top-level native-dispatch status (issue #733). The
# discoverable one-call check that ``libsrmech`` is loaded + ABI-matched
# + actually dispatching (vs. the pure-Python fallback). The native shim
# lives at ``srmech._native``; this surfaces it where ``dir(srmech)``
# finds it. Equivalent to ``describe()['native']`` plus expected-ABI +
# dispatching + load-error fields.
native_status = _introspect.native_status

# v0.6.0rc15 — top-level self-recognition help-anchor. ``describe()`` is the
# one-call "what IS srmech?" root (version + native + tool counts +
# by_category). It already lives at ``srmech.introspect.describe()``;
# surfacing it where ``dir(srmech)`` finds it mirrors the rc19 graduation of
# ``native_status``. Stays a counts/index ROOT — the full per-tool list is
# ``tool_schema_view()``; single-tool detail is ``ToolSchema.resolve()``.
describe = _introspect.describe

# v0.5.0rc11 — Self-recognition root. ``warmup_all()`` is THE single
# registration entry-point: it imports every submodule that registers
# ToolEntries (``srmech.bus`` / ``srmech.introspect``) so the registry
# is fully populated no matter how srmech was entered. Per user
# direction 2026-05-29 it fires here in ``__init__`` — substrate-
# coherent: every consumer sees the complete tool-schema from t=0,
# permanently closing the orphan-registration bug class (the rc9 bus
# miss). Placed at the END of package init (after ``__version__`` /
# profile loader / introspect are all set up) so the
# ``from .introspect.tool_schema import warmup_all`` import — which fully
# initialises ``srmech.amsc`` — sees a complete core ``srmech``
# namespace and cannot trip an import cycle.
from .introspect.tool_schema import warmup_all  # noqa: E402

warmup_all()
