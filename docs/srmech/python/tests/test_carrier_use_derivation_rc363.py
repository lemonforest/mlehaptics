"""rc363 — **ADR-0012 §3.1 C3 (CONSTRUCTIBLE), gated.** Every carrier an op
actually CONSUMES or PRODUCES must hold a ``carrier_schema`` row.

Why a second gate, when rc205 already has one
=============================================
``tests/test_carrier_schema_rc205.py::test_every_tool_type_carrier_token_is_registered``
is the existing C3 ratchet and it is **not being replaced** — it stays, and it is
the right instrument for what it measures. But it derives its population from the
DECLARED type strings, and ADR-0012 §2 states the consequence exactly:

    ``describe()`` and ``carrier_schema()`` report the carriers the op surface
    DECLARES, not the carriers it USES.

rc362 is the measured exhibit. Three ``srmech.music`` ops began consuming
``Qalg`` — the carrier registry's own admission rule (``carrier_schema.py``
docstring, *"Internal exact representations no public op surfaces … join when an
op surfaces them (the drift ratchet … forces the addition)"*) names precisely
that event as its trigger. The addition did not happen, and **the ratchet passed
throughout**: the ops declared ``partials`` as a bare ``Sequence`` (allowlisted),
so the token ``"Qalg"`` occurred in **0 of 525** declared type strings. C parity
was green on the identical hole, because both projections read the same
impoverished SSoT.

**A gate that cannot fire on the case it exists for is a false green.** This
module supplies the missing channel: :mod:`tests.coercion_boundary` reads what
each op's own source BRANCHES ON, so a carrier can be seen even when no string
names it.

What this gate decides
======================
For every registered op, the derivation reports the srmech classes it

* **ACCEPTS** — an ``isinstance(<parameter-derived value>, C)`` guard that does
  not raise, anywhere in the op's coercion boundary (its own body plus the
  module-level helpers a tracked value reaches, imports included);
* **PRODUCES** — a class instantiated on a ``return`` path, or named in the
  runtime signature annotations.

Two structural exclusions apply (:func:`~tests.coercion_boundary.is_operand_carrier_candidate`),
each a RULE rather than a list, so a future class of the same kind needs no edit:
``BaseException`` subclasses (6 measured at rc363) and ``_private`` names (6
measured, all lazy aliases of a registered carrier or an internal handle).

Everything that survives must hold a ``carrier_schema`` row or appear on
:data:`~tests.coercion_boundary.NON_CARRIER_CLASSES` — the six infra/handle types,
**shared with** the rc205 gate rather than re-typed, so the two channels cannot
grant different exemptions.

What it cannot decide
=====================
* **It under-reports, by construction.** Only literal ``isinstance`` targets and
  literal constructor calls are read. A ``type(x) is C`` dispatch, a duck-typed
  operand, a carrier reached through a method rather than a module-level
  function, or one built by a classmethod factory (``return EllRatio.monomial(r)``)
  is invisible. The assertion is therefore one-directional — everything FOUND
  must be registered — and never the converse.
* **It cannot say a registered carrier is unnecessary.** A row with no measured
  use is not evidence of anything here; the ladder-rung rows (``float`` /
  ``complex`` / ``quaternion`` / ``octonion`` / ``sedenion``) are registered
  through the rc120 op-contract, not through any ``isinstance``.

Measured residual at rc363
==========================
27 candidate operand classes surfaced across 525 ops. **6 unregistered, all six
already exempt** as infra/handle types — so this gate ships **STRICT-ZERO with no
CEIL**, which is only possible because the two genuine residuals it found were
FIXED rather than ceilinged in the same rc:

* ``Theta`` — the elliptic ATOM, accepted directly by five ops
  (``elliptic_gosper`` / ``elliptic_recurrence_8w7`` / ``elliptic_zeilberger`` /
  ``elliptic_wz_certificate`` / ``carrier_spectrum``, each of whose prose already
  said *"an EllMonomial / Theta is lifted"*). **ADR-0012's own baseline missed
  this one** — it recorded a single precedent, ``CarrierSpectrum``, because it
  was measuring the declared channel too.
* ``CarrierSpectrum`` — built on ``carrier_spectrum``'s return path and handed
  back under ``'spectrum'``; its own docstring calls it *"a first-class carrier
  object (not a diagnostic dict)"*. This is the one precedent ADR-0012 §3.1 C3
  names, closed here.

Registry: 26 -> 28.

Pure stdlib + srmech; numpy-free; no ``abs()``.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402

from srmech.introspect.carrier_schema import _CARRIERS, _pure_carrier_schema  # noqa: E402
from srmech.introspect.tool_schema import get_tool_schema, warmup_all  # noqa: E402

from coercion_boundary import (  # noqa: E402
    NON_CARRIER_CLASSES,
    boundary_for,
    is_operand_carrier_candidate,
)

warmup_all()

#: The two carriers this rc registered, named so a later removal has to argue
#: with a test rather than pass silently.
_RC363_ADDITIONS = ("CarrierSpectrum", "Theta")


def _surfaced() -> Dict[str, Set[str]]:
    """``{class name: {op names}}`` over every candidate operand carrier the
    derivation measures on the live registry."""
    out: Dict[str, Set[str]] = {}
    for tool in get_tool_schema().tools:
        bnd = boundary_for(tool.name)
        for name in bnd.surfaced:
            cls = bnd.classes.get(name)
            if cls is None or not is_operand_carrier_candidate(name, cls):
                continue
            out.setdefault(name, set()).add(tool.name)
    return out


# ── 0. the instrument must SELECT before its green means anything ────────────

def test_the_derivation_selects_a_real_population() -> None:
    """A strict-zero assertion over an EMPTY selected set passes for the wrong
    reason — the exact failure this gate exists to correct. So the population is
    pinned first: the walk must reach a body for every registered op, and must
    surface a substantial, carrier-rich set of classes."""
    tools = get_tool_schema().tools
    assert len(tools) > 500, "tool registry unexpectedly small"

    reached = [t.name for t in tools if boundary_for(t.name).reached]
    assert len(reached) == len(tools), (
        f"the coercion-boundary walk entered no function for "
        f"{len(tools) - len(reached)} of {len(tools)} ops — the derivation is "
        f"blind there and its green would be uninformative"
    )

    surfaced = _surfaced()
    assert len(surfaced) >= 20, (
        f"only {len(surfaced)} candidate operand classes surfaced across "
        f"{len(tools)} ops — the derivation is not selecting"
    )
    # It must see the carriers whose absence from the DECLARED channel is the
    # whole reason this gate exists.
    for name in ("Qalg", "Theta", "CarrierSpectrum"):
        assert name in surfaced, (
            f"{name} is not surfaced by the use-derivation — the instrument "
            f"cannot fire on the case it was built for"
        )


# ── 1. THE GATE ───────────────────────────────────────────────────────────────

def test_every_used_carrier_is_registered() -> None:
    """**C3, strict-zero.** Every srmech class an op is measured to accept or
    produce holds a ``carrier_schema`` row, or is an allowlisted infra/handle
    type. No CEIL: the two genuine residuals found at rc363 were registered.

    A future landing that surfaces a new carrier fails HERE even if it declares
    a weak type string — which is exactly what rc362 did and what the
    declared-channel ratchet could not see."""
    surfaced = _surfaced()
    unknown: List[Tuple[str, List[str]]] = sorted(
        (name, sorted(ops)) for name, ops in surfaced.items()
        if name not in _CARRIERS and name not in NON_CARRIER_CLASSES
    )
    assert not unknown, (
        "these srmech classes are CONSUMED or PRODUCED by registered ops and "
        "have no carrier_schema row:\n  "
        + "\n  ".join(f"{n} <- {ops}" for n, ops in unknown)
        + "\nAdd each to srmech.introspect.carrier_schema._CARRIERS (with a genuine "
          "description, a _CAPABILITY row and a construction example in "
          "tools/gen_carrier_examples_probe.py), then regenerate with "
          "tools/regen_all.py. If it is NOT a mathematical operand — a handle, "
          "an envelope, an orchestration IR — add it to "
          "tests/coercion_boundary.NON_CARRIER_CLASSES with the justification."
    )


def test_the_exemptions_are_all_still_used() -> None:
    """The allowlist is a liability, so it may not rot. Every name on
    :data:`NON_CARRIER_CLASSES` must still be surfaced by a live op — an entry
    nothing reaches is a silent widening of the gate."""
    surfaced = _surfaced()
    stale = sorted(NON_CARRIER_CLASSES - set(surfaced))
    assert not stale, (
        f"NON_CARRIER_CLASSES exempts {stale}, which no registered op surfaces "
        f"any more — drop the entry rather than leave the gate wider than the "
        f"tree needs"
    )


def test_no_exemption_is_also_a_registered_carrier() -> None:
    """A name cannot be both an operand carrier and a non-carrier. Overlap would
    make the gate's verdict depend on which branch ran first."""
    both = sorted(set(_CARRIERS) & NON_CARRIER_CLASSES)
    assert not both, (
        f"{both} appear in BOTH carrier_schema._CARRIERS and "
        f"NON_CARRIER_CLASSES — decide which one they are"
    )


# ── 2. the rc363 additions are real registry rows, not placeholders ──────────

def test_rc363_additions_carry_a_full_row() -> None:
    """``Theta`` and ``CarrierSpectrum`` must satisfy the same contract every
    other carrier does — description, capability block, construction example —
    so C3's "CONSTRUCTIBLE" is a measurement and not a spelling.

    Reads the Python SSoT rather than the dispatching ``carrier_schema()``: this
    gate is about what the REGISTRY says, and C-vs-pure parity is rc205's
    question (``test_c_json_byte_identical_to_python_ssot``). Conflating the two
    would make this gate red on a merely stale ``libsrmech``."""
    schema = _pure_carrier_schema()
    for name in _RC363_ADDITIONS:
        assert name in schema, f"{name} lost its carrier_schema row"
        row = schema[name]
        assert len(row["description"]) > 80, (
            f"{name}: description is too thin to identify the carrier")
        cap = row["capability"]
        assert set(cap) >= {"product", "address", "compose", "turn",
                            "commutative"}, f"{name}: incomplete capability block"
        assert "example" in row and row["example"].get("construct"), (
            f"{name}: no construction example — "
            f"add it to tools/gen_carrier_examples_probe.py and regenerate")


def test_theta_is_indexed_as_a_consumed_carrier() -> None:
    """The registration is only worth having if the DERIVED ops back-index
    actually reaches it — i.e. the C2 widening and the C3 registration compose.
    Before rc363 the five elliptic ops declared ``EllRatio`` alone, so a
    ``Theta`` row would have shipped with an empty ``consumes`` list: a
    registered carrier nothing is recorded as taking."""
    schema = _pure_carrier_schema()
    consumes = schema["Theta"]["ops"]["consumes"]
    for op in ("srmech.apokatastasis.elliptic_gosper.elliptic_gosper",
               "srmech.math.carrier_spectrum.carrier_spectrum"):
        assert op in consumes, (
            f"Theta.ops.consumes does not name {op} — the declared type strings "
            f"and the registry row have drifted apart again")
