"""rc363 — **ADR-0012 §3.1 C2 (TYPED HONESTLY), gated.**

The clause, verbatim (ADR-0012 §3.1):

    **C2 — TYPED HONESTLY.** Every declared ``parameters[].type`` and
    ``returns.type`` names the carrier union the callable actually accepts or
    produces. **The test is mechanical: does the type string name what the op's
    own coercion ``raise`` text names?**

And §3.2, which is why this file exists rather than a review checklist:

    A clause without an instrument that can return otherwise is not a clause,
    it is a preference.

The mechanical form as literally stated is TOO NOISY — measured
==============================================================
"Does the type string name what the raise text names?" was implemented first in
its plainest form: collect the srmech-carrier tokens appearing in any ``raise``
text in an op's defining module, and require the module's declared param types
to name them. **Measured at rc363: 33 modules had at least one carrier token in
a raise text, and 16 of the 33 were flagged.** Inspection of all 16 found most
were not defects at all:

* ``srmech.amsc.tripoly`` flagged ``BiPoly`` / ``Poly`` / ``Q`` because the
  *constructor* raises on them, while the registered op takes raw coefficients;
* ``srmech.amsc.op_provenance`` flagged ``Mat`` / ``Q`` / ``Vec`` from prose in a
  raise that explains what is NOT provenance-tracked;
* ``srmech.amsc.genome`` (68 ops) flagged ``Q`` from one raise in one helper.

A gate that is wrong roughly half the time is not a gate; it trains the reader
to override it. So the noisy form is **not shipped**, and this file ships the
narrower **decidable subset** instead — which is what ADR-0012 §6.3 already does
for three other candidate requirements it declines by name.

The decidable subset — a CONJUNCT, not a proxy
==============================================
A carrier is flagged for op ``f`` only when BOTH channels agree:

1. **The op ACCEPTS it.** :mod:`tests.coercion_boundary` tracks ``f``'s own
   parameters through assignment / iteration / helper calls and finds an
   ``isinstance(<that value>, C)`` guard that does not raise. This is dataflow,
   not module scoping — the difference is measurable: module scoping reported
   ``coupling.fold_spectrum`` as accepting a ``Poly``, when the guarded value is
   rebuilt from recovered HDC tokens and has no path from any parameter.
2. **The op's own coercion raise text NAMES it.** The same walk collects the
   literal ``raise`` strings inside the functions it reached, so "the op's own
   coercion raise text" means the text on the path the parameter actually takes.

Then: **the carrier must appear in that op's declared ``parameters[].type``.**

The conjunct is what makes the rc362 exhibit decidable — ``_coerce_ratio``
accepts ``Qalg`` on a ``partials`` element AND raises *"expected Q, Qalg, int or
an (int, int) pair"* — while excluding every one of the 16 noisy rows, none of
which satisfies both.

What this gate cannot decide
============================
* **Returns are not gated.** The clause names ``returns.type`` too. The produce
  side has no comparable second channel: a ``dict``-returning op carries its
  real shape in ``returns.shape``, which ADR-0012 §6.3 classifies UNSUPPORTED as
  a gate surface (403 unregistered capitalised-token occurrences over 154
  distinct tokens tree-wide — a wider regex floods). **The return half of C2
  remains ungated after this rc, and that is stated rather than implied.**
* **Non-carrier unions are not gated.** Only names in
  ``carrier_schema._CARRIERS`` are considered, so a param that accepts
  ``bytes | str`` and declares ``bytes`` is invisible here.
* **It under-reports.** Inherited from the derivation: duck-typed and
  ``type(x) is C`` dispatch are not seen.

Measured residual at rc363
==========================
**Selection: 27 of 525 ops** carry at least one accepted-and-raise-named
registered carrier — that is the decidable population, and it is what the green
below is a statement about. Within it, the gate found **8 violations** on the
rc362 tree, every one a genuine widening the declared type withheld:

===================================================  =====================  =========================
op                                                   withheld               was declared
===================================================  =====================  =========================
``carrier_ladder.qpoly_promote``                     ``QBiPoly``            ``QPoly``
``q_gosper.q_gosper`` (x2 params)                    ``Poly``               ``QPoly``
``elliptic_gosper.elliptic_gosper``                  ``EllMonomial``        ``EllRatio``
``elliptic_recurrence.elliptic_recurrence_8w7``      ``EllMonomial``        ``EllRatio``
``elliptic_zeilberger.elliptic_zeilberger``          ``EllMonomial``        ``EllRatio``
``elliptic_wz_certificate.elliptic_wz_certificate``  ``EllMonomial``        ``EllRatio``
``carrier_spectrum.carrier_spectrum``                ``EllMonomial``        ``EllRatio``
``harmonics.classify_chirality_harmonic``            ``Q``                  ``float``
===================================================  =====================  =========================

All eight were FIXED, not ceilinged, so the gate ships **strict-zero with no
CEIL**. The five elliptic rows are the sharpest: each op's own ``description``
prose already read *"an EllMonomial / Theta is lifted"*, so the union was
documented for humans in the same tuple that withheld it from machines — C2's
failure mode in one line of source.

A WIDE channel is also pinned, at zero
======================================
:func:`test_no_op_accepts_an_undeclared_carrier_wide` drops conjunct (2) and
asserts on accepted-but-not-declared alone. It found one further genuine row —
``coupling.fold_spectrum``'s ``margin_floor``, which branches on an exact ``Q``
and declared ``number`` — and that was fixed too. It is pinned as a **down-only
CEIL at 0** rather than a bare assert: if a future op legitimately trips the
wide channel without tripping the conjunct, raising the CEIL with a written
justification is the honest move, and dropping the channel is not.

Pure stdlib + srmech; numpy-free; no ``abs()``.
"""

from __future__ import annotations

import os
import sys
from typing import List, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402

from srmech.amsc.carrier_schema import _CARRIERS  # noqa: E402
from srmech.amsc.tool_schema import get_tool_schema, warmup_all  # noqa: E402

from coercion_boundary import _identifiers, boundary_for  # noqa: E402

warmup_all()

#: Down-only. The WIDE channel (accepted-but-not-declared, without the
#: raise-text conjunct) is at zero on the rc363 tree. Raising this requires a
#: written justification naming the op and why its wider acceptance must stay
#: undeclared; lowering it needs nothing.
CEIL_WIDE_UNDECLARED_OPS = 0

#: The decidable population must not silently shrink. If a refactor removes the
#: raise texts or the isinstance guards this gate reads, the assertions below go
#: green by selecting nothing — the exact false-green shape ADR-0012 §3.2 names.
FLOOR_SELECTED_OPS = 20


def _declared_carrier_tokens(tool) -> Set[str]:
    """Registered-carrier names appearing in this op's declared PARAM type
    strings. Identifier-shaped runs, so ``EllRatio | EllMonomial | Theta`` yields
    all three and ``QPoly`` never matches inside ``QBiPoly``."""
    out: Set[str] = set()
    for param in tool.parameters:
        out |= (_identifiers(param.type) & set(_CARRIERS))
    return out


def _rows() -> List[Tuple[str, Set[str], Set[str], Set[str]]]:
    """``(op, accepted_carriers, conjunct_carriers, declared_carriers)`` per op."""
    rows: List[Tuple[str, Set[str], Set[str], Set[str]]] = []
    carriers = set(_CARRIERS)
    for tool in get_tool_schema().tools:
        bnd = boundary_for(tool.name)
        accepted = bnd.accepted & carriers
        conjunct = accepted & bnd.raise_named
        rows.append((tool.name, accepted, conjunct, _declared_carrier_tokens(tool)))
    return rows


# ── 0. the instrument must SELECT ─────────────────────────────────────────────

def test_the_conjunct_selects_a_real_population() -> None:
    """The green below is a statement about a specific set of ops; pin its size
    so it cannot quietly become the empty set."""
    rows = _rows()
    assert len(rows) > 500, "tool registry unexpectedly small"
    selected = [name for name, _acc, conj, _dec in rows if conj]
    assert len(selected) >= FLOOR_SELECTED_OPS, (
        f"only {len(selected)} ops carry an accepted-and-raise-named registered "
        f"carrier (floor {FLOOR_SELECTED_OPS}) — the conjunct has stopped "
        f"selecting, so its zero-violation result would be uninformative"
    )
    # The exhibits that motivated the clause must be inside the selection.
    for name in ("srmech.music.spectrum_tier",
                 "srmech.amsc.elliptic_gosper.elliptic_gosper"):
        row = [r for r in rows if r[0] == name]
        assert row and row[0][2], (
            f"{name} is not selected by the conjunct — the gate cannot decide "
            f"the very case ADR-0012 C2 cites")


def test_the_music_exhibit_is_decided_not_merely_present() -> None:
    """rc362's exhibit, pinned as a DECISION rather than as a count. The three
    spectra ops must be measured to accept ``Qalg``, must name it in their
    coercion raise text, and must declare it — the state the ratchet that
    existed could not distinguish from its opposite."""
    for name in ("srmech.music.spectrum_tier",
                 "srmech.music.commensurability_verdict",
                 "srmech.music.common_period"):
        bnd = boundary_for(name)
        assert "Qalg" in bnd.accepted, f"{name}: Qalg no longer accepted"
        assert "Qalg" in bnd.raise_named, (
            f"{name}: the coercion raise text no longer names Qalg")
        tool = get_tool_schema().lookup(name)
        assert tool is not None and "Qalg" in _declared_carrier_tokens(tool), (
            f"{name}: the declared param types withhold Qalg again — this is "
            f"the rc362 defect reopening")
        # …and the refusal is a capability statement too: floats are refused on
        # purpose, so a float must NOT read as accepted.
        assert "Qalg" not in bnd.refused


# ── 1. THE GATE ───────────────────────────────────────────────────────────────

def test_declared_types_name_every_accepted_and_raise_named_carrier() -> None:
    """**C2, strict-zero on the decidable subset.** For every op whose coercion
    boundary both accepts a registered carrier and names it in its own raise
    text, the declared param types name it too."""
    bad: List[str] = []
    for name, _accepted, conjunct, declared in _rows():
        missing = sorted(conjunct - declared)
        if missing:
            bad.append(f"{name}: accepts + raise-names {missing}, declares "
                       f"{sorted(declared) or '(no carrier)'}")
    assert not bad, (
        "these ops accept a carrier their own coercion raise text names and "
        "their declared parameters[].type does NOT:\n  " + "\n  ".join(bad)
        + "\nWiden the declared type to the honest union in "
          "srmech/amsc/tool_schema.py, add the new type string to "
          "srmech.mcp._coercion._PARAM_COERCERS (usually mapping to the SAME "
          "coercer the one-carrier key uses — the wire behaviour does not "
          "change, the declaration catches up), keep srmech.mcp._tools."
          "_TYPE_LEXICON from degrading, then run tools/regen_all.py."
    )


def test_no_op_accepts_an_undeclared_carrier_wide() -> None:
    """The WIDE channel — accepted-but-not-declared, without the raise-text
    conjunct. Down-only CEIL, currently 0."""
    bad = [f"{name}: accepts {sorted(accepted - declared)}, declares "
           f"{sorted(declared) or '(no carrier)'}"
           for name, accepted, _conj, declared in _rows()
           if accepted - declared]
    assert len(bad) <= CEIL_WIDE_UNDECLARED_OPS, (
        f"{len(bad)} ops accept a registered carrier their declared parameter "
        f"types do not name (CEIL {CEIL_WIDE_UNDECLARED_OPS}):\n  "
        + "\n  ".join(bad)
        + "\nPrefer widening the declared type. Raising the CEIL requires a "
          "written justification for why the acceptance must stay undeclared."
    )


def test_ceil_is_not_slack() -> None:
    """The CEIL may not sit above the measured value — slack is how a ratchet
    stops ratcheting."""
    actual = sum(1 for _n, acc, _c, dec in _rows() if acc - dec)
    assert actual == CEIL_WIDE_UNDECLARED_OPS, (
        f"CEIL_WIDE_UNDECLARED_OPS is {CEIL_WIDE_UNDECLARED_OPS} but the tree "
        f"measures {actual} — lower the CEIL to {actual}")


# ── 2. the widened type strings must remain callable end-to-end ──────────────

def test_every_widened_type_string_has_an_mcp_coercer() -> None:
    """A declared type with no coercer makes the op uncallable over MCP (the
    65/158 finding the rc14 ratchet exists for). ``tests/test_mcp.py`` asserts
    this over the whole surface; this names the rc363 strings specifically, so a
    revert of the widening without its coercer fails HERE with the reason."""
    from srmech.mcp._coercion import has_coercer

    for type_string in ("QPoly | Poly", "QPoly | QBiPoly",
                        "EllRatio | EllMonomial | Theta",
                        "float | Q", "number | Q"):
        assert has_coercer(type_string), (
            f"the rc363 C2 widening {type_string!r} has no entry in "
            f"srmech.mcp._coercion._PARAM_COERCERS")


def test_widened_types_did_not_degrade_the_published_json_schema() -> None:
    """A union must not cost a param its JSON-schema type. ``float`` and
    ``number`` both publish ``"number"``; the widened spellings must too, or a
    schema-obedient client is told to send a string (ADR-0012 §4.2, row 4 — the
    silent-degradation row)."""
    from srmech.mcp._tools import _json_schema_type_for

    assert _json_schema_type_for("float | Q") == "number"
    assert _json_schema_type_for("number | Q") == "number"
    # the base spellings, for contrast — the union must not be worse
    assert _json_schema_type_for("float") == "number"
    assert _json_schema_type_for("number") == "number"
