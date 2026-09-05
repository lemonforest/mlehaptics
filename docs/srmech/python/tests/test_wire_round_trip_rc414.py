"""rc414 (`#T1092`) — THE OUTBOUND WIRE ROUND-TRIP GATE.

THE HOLE THIS FILLS. ``tests/test_mcp.py::test_all_param_types_json_coercible``
is the INBOUND exhaustiveness ratchet: every advertised *param* type must have a
handler. Its converse had no instrument. Nothing asked whether a value a
producer EMITS can be read back — and the answer, measured across the registry,
was frequently no: a carrier with no ``serialise_native`` branch fell through to
``_json_fallback``'s ``return repr(obj)`` and crossed the wire as a metadata
STRING. ``zeilberger`` handed back ``"certificate": "BiPoly(k_degree=1,
exact-ℚ[n,k])"``, and that certificate is the entire point of the op.

WHY IT IS ITS OWN FILE. It does not belong in ``test_mcp.py``, which already
holds both the inbound ratchet and ``test_coercion_roundtrips_scalar_leaf_types``
(six hand-picked values across three wire types). Putting the outbound sweep
beside them buries the two-directions distinction that is the whole point.
rc408 faced the same choice and landed its new gate in its own rc-numbered file.

THIS GATE IS ADR-0012 CLAUSE C5's INSTRUMENT. C5 (CHAINABLE) says a producer's
output must feed its designed consumer over EVERY ADVERTISED TRANSPORT, not only
in-process. C5 was marked CLOSED in-rc with no instrument that could return
otherwise, and was refuted on its own marquee exhibit — see
``docs/srmech/adr/0012-introspect-as-the-api-contract.md`` §3.1 C5. Every prior
exercise of that exhibit called the op DIRECTLY; none went through
``serialise_result`` / ``coerce_param``. This file is the first thing in the tree
that can report the clause false.

THREE WAYS THIS GATE COULD LIE, AND WHAT STOPS EACH
---------------------------------------------------
1. **Bare ``==`` manufactures green.** ``coerce_param(loads(serialise_result(v)),
   'Vec')`` returns a plain ``list``, and ``Vec.__eq__`` accepts any flat
   sequence — so ``back == v`` is True *while the carrier has been lost*. The
   verdict is therefore the CONJUNCTION ``type(back) is type(v) and back == v``,
   and ``EQUAL_BUT_TYPE_LOST`` is its own reported class, never folded into a
   pass.
2. **A ``has_coercer`` MISS is not a pass.** ``coerce_param`` is keyed on the
   declared type-string and a table miss returns the value UNCHANGED, so a
   value that was never really coerced can compare equal to itself
   (``coerce_param([1.0], 'TOTAL_NONSENSE_TYPE')`` -> ``[1.0]``). Those land in
   ``PASS_NOCOERCER``, which is counted as a FAILURE of the round-trip claim.
   The one honest exception is a value that came back through the STRUCTURAL
   ``$srmech_carrier`` path, which needs no declared-type row by design — that
   is detected positively (the wire carries the sentinel), not assumed.
3. **Enumerating nothing.** A gate whose population silently empties is green
   forever. ``test_the_gate_enumerates_something`` runs first and asserts the
   floors before any population is used.

EQUALITY IS PER-CARRIER, because ``==`` is not the identity operator for every
carrier srmech ships:
  * ``RecoverableFold`` inherits object identity, but srmech ships a
    purpose-built THREE-valued gate for it — ``coupling.fold_identity`` ->
    ``EQUAL`` / ``NOT_EQUAL`` / ``UNKNOWN``. ``UNKNOWN`` is recorded as its own
    bucket rather than being forced into a binary, because an honest decline is
    not a failure (`[[feedback_an_instrument_that_cannot_return_otherwise...]]`).
  * ``CDRegister`` is handle-shaped: it crosses by
    REFERENCE, so the round-trip claim is IDENTITY (``resolve(env) is orig``),
    which is a strictly stronger check than value equality would have been.

numpy-free; the inbound half parses with ``srmech._json.loads`` (srmech's own
JSON front door) rather than stdlib ``json.loads``, so the gate exercises the
native ``srmech_json_parse`` against the very format srmech emits. The gate is
honestly stdlib-OUT / srmech-IN: ``srmech._json`` ships no ``dumps`` by design,
which is why ``serialise_result`` calls stdlib ``json.dumps`` — and that call's
``default=`` is the defect this whole rc is about.
"""
from __future__ import annotations

import pytest

from srmech._json import loads
from srmech.introspect.carrier_schema import carrier_schema
from srmech.introspect.tool_schema import get_tool_schema, warmup_all
from srmech.mcp._coercion import (
    CARRIER_ENVELOPE_KEY,
    coerce_param,
    has_coercer,
    is_carrier_envelope,
)
from srmech.mcp._tools import serialise_result

# ── ceiling seeds, measured on the rc414 tree ────────────────────────────────
#
# Down-only. A ceiling may be LOWERED when a defect is fixed; raising one is a
# deliberate act that must be justified in the rc's CHANGELOG entry.

#: Floor on the registered-op population. A FLOOR, not an equality: ops are
#: added most rcs, and an equality here would be one more count-pin to bump
#: (there are 73 of those already). Its job is to catch the population
#: COLLAPSING, which is the way this gate would go quietly vacuous.
FLOOR_REGISTERED_OPS = 550

#: The carrier registry is a fixed, reviewed set, so this one IS an equality —
#: a carrier appearing or disappearing is exactly the event the gate must not
#: miss.
#: rc466 (`#T1188`, stage 3): 28 -> 29. ``Qi`` — the exact Gaussian-rational
#: scalar that had shipped since rc362 as ``Qalg`` over x²+1 with a fixed
#: embedding — entered declared ToolEntry type strings for the first time when
#: the seventy-row drain gave ``elementwise_multiply_complex`` /
#: ``inner_product_eta`` / ``density_matrix`` / ``magnetic_laplacian(exact=True)``
#: their exact arm, and rc205 flagged the token as absent from the carrier
#: registry. Its wire form is a ``_CARRIER_WIRE`` row (the Qalg / QMat
#: precedent): ``{"re": [num, den], "im": [num, den]}`` inside the
#: ``$srmech_carrier`` envelope, rebuilt structurally on the way in. The
#: Stage-1 cut had emitted a bare ``[[num, den], [num, den]]`` — which this
#: file's sweep correctly filed as a carrier that does NOT round-trip (no
#: envelope, no carrier-level rebuild) before the row existed.
EXPECTED_CARRIERS = 29

#: Ops whose DECLARED return type has no inbound coercer at all. A round-trip
#: claim over these is UNDEFINED, not true — the value comes back unchanged
#: because nothing looked at it. This is the headline residual of `#T1092` and
#: the number the follow-on rcs drain.
#:
#: **131 -> 134 at v0.9.0rc419 (`#T1110`) — a RAISE, and therefore a regression
#: by this file's own rule, recorded here and in the CHANGELOG rather than
#: laundered.** rc419 registers the nine-row ``srmech.signal_processing``
#: dispatcher / path-registry read surface. Six of the nine declare coercible
#: returns (``str`` / ``bool`` / ``Sequence[str]`` / the generic op-result
#: union) or, for ``end_cascade``, no return at all — it genuinely returns
#: ``None``, so it carries ``returns=None`` and this gate correctly skips it.
#: THREE do not, and all three are the SAME shape as the rc414 entry already
#: inside this residual (``srmech.introspect.publish``, whose declared return is
#: ``contextmanager[_PublishHandle]``):
#:
#: * ``cascade_dispatcher.begin_cascade`` -> ``contextmanager[CascadeContext]``
#:   — a ``with``-block SCOPE. There is no encoder for an enter/exit pair.
#: * ``cascade_dispatcher.current_cascade`` -> ``Optional[CascadeContext]`` — the
#:   value's meaning is its POSITION on a per-thread stack, so a copy that
#:   crossed the wire would describe a scope belonging to a finished request.
#: * ``path_registry.lookup`` -> ``OperationEntry`` — the entry holds the two
#:   live implementation CALLABLES, and a function has no wire form.
#:
#: WHY A COERCER WAS NOT LANDED INSTEAD, which is what this gate normally
#: demands. For these three an inbound coercer would be reachability THEATRE:
#: all three are ``mcp_callable=False`` precisely BECAUSE their return has no
#: wire form, so no consumer is offered them over any transport. Writing a
#: coercer that re-resolves an ``OperationEntry`` from its name would let the
#: row drop off this list while nothing whatsoever became reachable — draining
#: a debt ledger by editing the ledger. The honest record is that the residual
#: grew by three, and that each of the three carries a machine-readable
#: ``mcp_callable=False`` + ``mcp_unavailable_reason`` stating the obstruction
#: at the row itself, which is a STRONGER claim than this counter makes.
#: The number falls again when a ``$srmech_scope`` / handle grammar exists that
#: can carry a scope honestly — the same exit condition ``publish`` is waiting on.
#:
#: **134 -> 133 at rc465 (`#T1188`) — a LOWERING, and the interesting half is
#: that it passed through a raise first.** rc465 gave nine ``srmech.physics.qm``
#: ops a second carrier rung, so their declared returns became ``Mat | QMat``
#: (4 ops) and ``list[float] | list[Q]`` (3 ops) — new strings, no coercer, and
#: this counter went 134 -> 140. That is precisely the regression this ceiling
#: exists to report, and the remedy it names was available: both strings ARE
#: coercible, because a ``QMat`` rides as nested ``[num, den]`` leaves and a
#: ``Mat`` as floats, which is the discrimination
#: ``_to_exact_or_float_rows`` / ``_to_exact_or_float_vector`` already make.
#: Landing those two coercers took the count to 133 — one BELOW the pre-rc465
#: figure, because ``triality_apply``'s old bare ``list[float]`` return had no
#: coercer either and its widened union now does. Contrast the three rc419 rows
#: the paragraph above defends: those have no wire form at ALL, so a coercer for
#: them would be theatre. These seven had one and were simply not given it.
#: rc466 (`#T1188`, stage 3): 133 -> 129, a DRAIN. The seventy-row drain widened
#: seven return spellings with no inbound coercer (`Mat | list` x4, `complex | Qi`,
#: `Mat | QMat | list[list[Qi]]`, `Mat | Vec | list[Qi] | list[list[Qi]]`) and
#: moved `klein4_gain_laplacian` to `dict[str, Mat] | dict[str, list]`; measured
#: 140 on the Stage-2 head. Landing the five coercers (each a rebuild of the
#: exact wire leaves Q `[num, den]` / Qi `[[a, b], [c, d]]`, round-tripped by
#: execution) covers those eight AND rc463's three `Mat | list` builders, which
#: had sat inside the 133 since rc463: 140 - 11 = 129.
CEIL_RETURN_TYPES_WITHOUT_COERCER = 129

#: Carriers, constructed from their own shipped example expressions, that do
#: NOT survive a wire round-trip. Counted over the EVALUABLE subset.
#:
#: Measured at rc414: 5 of 26. The residual is TWO distinct problems, kept in
#: one number only because both are "the value came back, the carrier did not":
#:   * ``HV`` / ``Vec`` — EQUAL_BUT_TYPE_LOST. The coercer deliberately produces
#:     the flat Python structure and lets the op's own acceptance build the
#:     carrier (``_to_vec``'s docstring says so outright), so ``back == value``
#:     is True while the carrier is gone. Fixing it means deciding whether the
#:     coercer or the op owns carrier construction — a contract question, not a
#:     missing branch.
#:   * ``octonion`` / ``quaternion`` / ``sedenion`` — the Cayley–Dickson scalar
#:     rows, which the carrier schema represents AS float sequences. They have
#:     no inbound coercer because they have no distinct wire IDENTITY: a
#:     sedenion and a 16-list are the same JSON.
CEIL_CARRIERS_NOT_ROUND_TRIPPING = 5

#: Carriers whose shipped ``construct`` expression does not evaluate. This is a
#: defect in the EXAMPLE, not in the carrier, and it is ceilinged separately so
#: the two never mask each other.
#:
#: Measured at rc414: 3 — ``EllRatio`` (the "example" is prose, not an
#: expression: ``"elliptic_gosper(...) operand — prefactor·∏(num θ)/…"``),
#: ``HarmonicMaass`` (a truncated ``HarmonicMaass(hol=MockQSeries(...),
#: shadow=UnaryTheta(...))``), and ``UnaryTheta`` (``UnaryTheta(char, j, a, b,
#: D)`` — undefined names). These three carriers are consequently ABSENT from
#: the round-trip sweep, so fixing an example is what ADMITS a carrier to the
#: gate; that is why this ceiling exists rather than the names being skipped
#: quietly. ``EllRatio`` in particular DOES have a working wire form (rc414
#: ships it and it round-trips when constructed by hand) — only its example is
#: broken.
CEIL_CARRIER_EXAMPLES_NOT_EVALUABLE = 3


def _example_namespace() -> dict:
    """The namespace the shipped ``construct`` expressions are written against.

    Mirrors ``tools/gen_carrier_examples_probe.py``, which is what PRODUCED
    those expressions. Building the namespace here rather than hand-picking
    values is what makes the population DERIVED: the gate tests the carriers
    srmech says it has, constructed the way srmech says to construct them, and
    a carrier added to the registry without a working example shows up as a
    ``CEIL_CARRIER_EXAMPLES_NOT_EVALUABLE`` regression rather than being
    silently skipped.
    """
    # NOTE no ``fractions`` import. ``tools/gen_carrier_examples_probe.py``
    # carries one (with a named allowance under the self-hosting import ban)
    # because it evaluates the whole example table, which holds a legacy
    # ``Fraction`` row. This gate sweeps ``carrier_schema()`` instead, and
    # ``Fraction`` is not a registered carrier — so the borrowed module is not
    # needed here, and taking the allowance would have been the wrong fix.
    import array

    from srmech.amsc import Poly, ThetaSum, TriPoly
    from srmech.apokatastasis.apagodu_zeilberger import Q
    from srmech.apokatastasis.ellbase import Theta
    from srmech.apokatastasis.harmonic_maass import (
        HarmonicMaass, MockQSeries, UnaryTheta,
    )
    from srmech.apokatastasis.riemann_theta_multisum import ThetaBracketSum
    from srmech.cascade import cd_register, the_one
    from srmech.math import hdc as _hdc
    from srmech.math import laplacian as _lap
    from srmech.math.carrier_ladder import BiPoly, QBiPoly, QPoly
    from srmech.math.carrier_spectrum import (
        CarrierSpectrum, EllMonomial, EllRatio,
    )
    from srmech.math.hdc import HV, Mat
    from srmech.math.qalg import Qalg
    from srmech.math.qi import Qi
    from srmech.math.qmat import QMat
    from srmech.biology.coupling import Vec

    return dict(
        Qalg=Qalg, Qi=Qi,
        array=array, Q=Q, Poly=Poly, BiPoly=BiPoly,
        TriPoly=TriPoly, QPoly=QPoly, QBiPoly=QBiPoly, Mat=Mat, Vec=Vec,
        QMat=QMat, HV=HV, EllMonomial=EllMonomial, EllRatio=EllRatio,
        ThetaSum=ThetaSum, ThetaBracketSum=ThetaBracketSum, Theta=Theta,
        CarrierSpectrum=CarrierSpectrum, MockQSeries=MockQSeries,
        UnaryTheta=UnaryTheta, HarmonicMaass=HarmonicMaass, the_one=the_one,
        cd_register=cd_register,
        dense_laplacian=_lap.dense_laplacian,
        jacobi_eigvals=_lap.jacobi_eigvals,
        fiedler_vector=_lap.fiedler_vector, hdc=_hdc,
    )


def _constructed_carriers() -> "tuple[dict, list[str]]":
    """``{carrier_name: live value}`` plus the names whose example did not
    evaluate.

    The POPULATION is ``carrier_schema()`` — srmech's own carrier registry, the
    same 29 rows pinned above — and the VALUES come from
    ``_carrier_examples.CARRIER_EXAMPLES``. Deliberately not the other way
    round: ``CARRIER_EXAMPLES`` is a probe-authored table that also carries
    legacy rows (``Fraction``) which are not registered carriers, and sweeping
    it would measure the example corpus rather than the shipped carrier set.
    """
    from srmech.introspect._carrier_examples import CARRIER_EXAMPLES

    ns = _example_namespace()
    built, not_evaluable = {}, []
    for name in sorted(carrier_schema()):
        expr = (CARRIER_EXAMPLES.get(name) or {}).get("construct")
        if not expr:
            not_evaluable.append(f"{name}(no-example)")
            continue
        try:
            built[name] = eval(expr, dict(ns))       # noqa: S307 - shipped expr
        except Exception as exc:                     # noqa: BLE001
            not_evaluable.append(f"{name}({type(exc).__name__})")
    return built, not_evaluable


# ──────────────────────────────────────────────────────────────────────
# 0. THE ZERO-ENUMERATION GUARD — runs before any population is used
# ──────────────────────────────────────────────────────────────────────


def test_the_gate_enumerates_something() -> None:
    """A gate that silently enumerates nothing is the canonical false green.

    ``get_tool_schema()`` UNDER-COUNTS without ``warmup_all()`` (registration is
    lazy per module), and ``carrier_schema()`` is a module-level dict that an
    import failure would truncate rather than raise on. Either would leave every
    assertion below vacuously true. So the populations are asserted non-empty
    and at their expected size FIRST, in their own test, so the failure message
    says "the gate is empty" instead of "everything passes".
    """
    warmup_all()
    tools = get_tool_schema().tools
    assert len(tools) >= FLOOR_REGISTERED_OPS, (
        f"only {len(tools)} registered ops — expected at least "
        f"{FLOOR_REGISTERED_OPS}. The registry did not fully populate, so "
        f"every sweep in this file would pass over an empty or truncated set."
    )
    carriers = carrier_schema()
    assert len(carriers) == EXPECTED_CARRIERS, (
        f"carrier_schema() has {len(carriers)} rows, expected "
        f"{EXPECTED_CARRIERS}: {sorted(carriers)}. A carrier appeared or "
        f"vanished — update EXPECTED_CARRIERS deliberately, and give any NEW "
        f"carrier a wire form in the same rc."
    )
    built, _ = _constructed_carriers()
    assert built, "no carrier example evaluated — the round-trip sweep is empty"


# ──────────────────────────────────────────────────────────────────────
# 1. THE CARRIER ROUND-TRIP SWEEP
# ──────────────────────────────────────────────────────────────────────


def _verdict(name: str, value: object) -> "tuple[str, str]":
    """Classify one carrier's round-trip. Returns ``(bucket, detail)``."""
    try:
        wire_text = serialise_result(value)
    except Exception as exc:                          # noqa: BLE001
        return "SERIALISE_RAISED", type(exc).__name__
    try:
        wire = loads(wire_text)
    except Exception as exc:                          # noqa: BLE001
        return "PARSE_RAISED", type(exc).__name__

    # A lossy repr string is the defect this rc exists to remove. Name it
    # explicitly rather than letting it fall into a generic NOT_EQUAL — the
    # remedy is different (add a wire form, not fix a coercer).
    if isinstance(wire, str) and wire.startswith(f"{type(value).__name__}("):
        return "REPR_STRING", wire[:60]

    # Handle-shaped carriers cross BY REFERENCE. The round-trip claim is
    # identity, which is stronger than equality — and is the only claim that
    # makes sense for a mutable register.
    from srmech._handles import get_handle_registry, is_handle_envelope
    if is_handle_envelope(wire):
        try:
            back = get_handle_registry().resolve(wire["$srmech_handle"])
        except Exception as exc:                      # noqa: BLE001
            return "HANDLE_UNRESOLVED", type(exc).__name__
        return ("ROUND_TRIPS" if back is value else "NOT_EQUAL"), "handle"

    structural = is_carrier_envelope(wire)
    if not has_coercer(name) and not structural:
        # coerce_param would return the value UNCHANGED. Whatever comes back,
        # it was not coerced, so a comparison here proves nothing.
        return "NO_INBOUND_COERCER", ""

    try:
        back = coerce_param(wire, name)
    except Exception as exc:                          # noqa: BLE001
        return "COERCE_RAISED", f"{type(exc).__name__}: {exc}"[:90]

    # RecoverableFold: srmech's own three-valued identity gate, not ``==``.
    if type(value).__name__ == "RecoverableFold":
        from srmech.biology.coupling import fold_identity
        try:
            verdict = fold_identity(value, back)
        except Exception as exc:                      # noqa: BLE001
            return "EQ_RAISED", type(exc).__name__
        return ({"EQUAL": "ROUND_TRIPS", "NOT_EQUAL": "NOT_EQUAL"}
                .get(verdict, "UNKNOWN_IDENTITY")), verdict

    # A carrier that ships NO ``__eq__`` inherits object identity, so ``back ==
    # value`` is False for reasons that have nothing to do with the wire. Saying
    # "does not round-trip" there would be a false negative — the instrument
    # cannot return otherwise, so it is not a measurement. The decidable
    # statement available is WIRE identity (emit -> read -> emit is fixed), and
    # it is reported under its own name so it is never read as value equality.
    if type(value).__eq__ is object.__eq__:
        try:
            same_wire = serialise_result(back) == wire_text
        except Exception as exc:                      # noqa: BLE001
            return "EQ_RAISED", type(exc).__name__
        return (("ROUND_TRIPS" if same_wire else "NO_EQUALITY_OP"),
                "wire-identical (no __eq__)" if same_wire else "no __eq__")

    try:
        equal = bool(back == value)
    except Exception as exc:                          # noqa: BLE001
        return "EQ_RAISED", type(exc).__name__

    if type(back) is not type(value):
        # THE MANUFACTURED GREEN. Vec/HV compare equal to a bare list, so
        # ``back == value`` alone would call this a pass while the carrier is
        # gone. Reported as its own class, counted as a failure.
        return ("EQUAL_BUT_TYPE_LOST" if equal else "NOT_EQUAL"), (
            f"{type(value).__name__} -> {type(back).__name__}")
    if not equal:
        return "NOT_EQUAL", ""
    if not has_coercer(name) and not structural:
        return "PASS_NOCOERCER", ""
    return "ROUND_TRIPS", ("structural" if structural else "declared")


def _sweep() -> "tuple[dict, list[str]]":
    built, not_evaluable = _constructed_carriers()
    buckets: "dict[str, list[str]]" = {}
    for name, value in sorted(built.items()):
        bucket, detail = _verdict(name, value)
        buckets.setdefault(bucket, []).append(
            f"{name}({detail})" if detail else name)
    return buckets, not_evaluable


def test_carrier_examples_evaluate() -> None:
    """Every carrier's shipped ``construct`` expression must actually run.

    Ceilinged separately from the round-trip verdict so a carrier that cannot
    be BUILT is never mistaken for one that round-trips (it would otherwise
    just be absent from the sweep, which is a silent pass).
    """
    _, not_evaluable = _constructed_carriers()
    assert len(not_evaluable) <= CEIL_CARRIER_EXAMPLES_NOT_EVALUABLE, (
        f"{len(not_evaluable)} carrier examples do not evaluate "
        f"(ceiling {CEIL_CARRIER_EXAMPLES_NOT_EVALUABLE}): {not_evaluable}"
    )


def test_carriers_round_trip_over_the_wire() -> None:
    """The headline sweep, with every way of lying enumerated as its own class.

    The failure message prints the full bucket breakdown, because "N carriers
    fail" is not actionable and the REMEDY differs per class: a
    ``REPR_STRING`` needs an outbound wire form, a ``NO_INBOUND_COERCER``
    needs a table row, an ``EQUAL_BUT_TYPE_LOST`` needs the coercer to build
    the carrier rather than the bare structure.
    """
    buckets, _ = _sweep()
    total = sum(len(v) for v in buckets.values())
    bad = total - len(buckets.get("ROUND_TRIPS", ()))
    report = "\n".join(f"    {k:22} {len(v):3}  {sorted(v)}"
                       for k, v in sorted(buckets.items()))
    assert bad <= CEIL_CARRIERS_NOT_ROUND_TRIPPING, (
        f"{bad} of {total} evaluable carriers do not survive a wire "
        f"round-trip (ceiling {CEIL_CARRIERS_NOT_ROUND_TRIPPING}):\n{report}"
    )


def test_no_carrier_crosses_as_a_repr_string() -> None:
    """STRICT ZERO on the defect class `#T1092` was opened for.

    A carrier that crosses as ``"Poly(degree=1, exact-rational)"`` has been
    replaced by prose ABOUT itself. There is no ceiling here and there should
    never be one: the whole point of the ``$srmech_carrier`` envelope is that
    a carrier without a wire form is a bug, not a budget line.
    """
    buckets, _ = _sweep()
    repr_leaks = buckets.get("REPR_STRING", [])
    assert repr_leaks == [], (
        f"{len(repr_leaks)} carriers cross the wire as their own repr: "
        f"{sorted(repr_leaks)}. Add an outbound branch in "
        f"srmech.mcp._coercion._CARRIER_WIRE (and its inbound inverse)."
    )


def test_the_silent_corruption_regressions() -> None:
    """The three rc414 silent-corruption defects, as named assertions.

    All three returned a DIFFERENT, well-formed object with NO exception, which
    is the top defect class. They get explicit tests rather than relying on the
    sweep, because the sweep's ceiling could absorb a regression and these must
    never be absorbable.
    """
    from srmech.apokatastasis.ellbase import EllMonomial
    from srmech.cascade import cd_register, the_one
    from srmech.math.q import Q

    # (1) the_one DROPPED the winding triad. rc408 made `w` a declared param,
    #     so a caller could SET winding and never READ it back.
    wound = the_one(1, 1, 4, w=(1, 0, 1))
    back = coerce_param(loads(serialise_result(wound)), "One")
    assert back.winding == (1, 0, 1), (
        f"the winding triad did not survive the wire: {back.winding}")
    assert back.spinor_sign == wound.spinor_sign
    assert back == wound

    # (2) an EllMonomial repr was read back as a SYMBOL NAME, producing
    #     EllMonomial(1·EllMonomial(1·q^2)^1) — a different valid monomial.
    mono = EllMonomial(Q(1, 1), {"q": 2})
    rebuilt = coerce_param(loads(serialise_result(mono)), "EllMonomial")
    assert rebuilt == mono, f"{rebuilt!r} != {mono!r}"
    with pytest.raises(ValueError, match="not a symbol name"):
        coerce_param("EllMonomial(1·q^2)", "EllMonomial")

    # (3) the register emitted a NON-DETERMINISTIC payload: the class had
    #     no __repr__, so the default one carried a memory address and two
    #     identical calls produced different bytes. rc464 removed the 16-slot
    #     register this was found on; the defect was never specific to it (it
    #     is a property of any handle-shaped carrier without a __repr__), so
    #     the regression is re-pointed at the register that survives rather
    #     than deleted with the one it was found on.
    a, b = cd_register(16), cd_register(16)
    assert "object at 0x" not in serialise_result(a), (
        "the register still crosses as a default repr carrying an address")
    assert serialise_result(a) == serialise_result(a), (
        "the same register serialises differently on two calls")
    assert serialise_result(a) != serialise_result(b), (
        "two DISTINCT registers serialise identically — the by-reference id "
        "is not discriminating them")


def test_qpoly_carries_x_low_in_both_directions() -> None:
    """The A.3 capability gap: a LAURENT ``QPoly`` could not be expressed at
    all, in EITHER direction.

    The outbound form was a repr; the inbound ``_to_qpoly`` accepted only the
    bare cell list while ``QPoly.from_coeffs(seq, x_low=0)`` takes ``x_low`` as
    a SEPARATE parameter. So a Laurent polynomial came back re-based at
    ``x_low=0`` — a different polynomial, silently. Both halves land together
    or neither is worth anything.
    """
    from srmech.math.poly import Poly
    from srmech.math.qpoly import QPoly

    for x_low in (-3, -1, 0, 1, 4):
        p = QPoly.from_coeffs(
            [Poly.from_coeffs([1]), Poly.from_coeffs([0, 2])], x_low=x_low)
        back = coerce_param(loads(serialise_result(p)), "QPoly")
        assert isinstance(back, QPoly), type(back).__name__
        assert back.x_low == x_low, f"{back.x_low} != {x_low}"
        assert back == p


def test_chain_spec_round_trips_through_its_own_parser() -> None:
    """``serialise_result`` emitted the step key ``class_id`` while
    ``parse_chain_spec`` requires ``class`` — so a ``ChainSpec`` did not
    survive its OWN parser, and the advertised schema (``spec: "object"``)
    told a client to send exactly the value guaranteed to fail with
    ``AttributeError: 'dict' object has no attribute 'steps'``.
    """
    from srmech.cascade.compose import ChainSpec, parse_chain_spec

    spec = parse_chain_spec({
        "name": "demo", "summary": "s", "returns": "float",
        "steps": [{"class": "K", "op": "pin_slot_at_zero",
                   "args": {"x": -3.0}}],
    })
    wire = loads(serialise_result(spec))
    reparsed = coerce_param(wire, "ChainSpec")
    assert isinstance(reparsed, ChainSpec)
    assert reparsed.steps[0].class_id == "K"
    assert reparsed == spec


def test_nested_carriers_survive_a_bare_dict_return() -> None:
    """THE STRUCTURAL CASE, which no per-type coercer table can reach.

    ``serialise_native`` is structural (it walks the value); ``coerce_param``
    is declared-type (a table read off ``returns.type``). With no structural
    inverse, a carrier nested inside a ``dict`` / ``list`` was emitted and never
    reconstructed — and 119 registered ops declare a bare ``dict``, 39 a
    ``list``, 23 a ``tuple``. That is where the mathematical content lives:
    ``zeilberger``'s certificate is a ``BiPoly`` inside a ``dict``.
    """
    from srmech.apokatastasis.zeilberger import BiPoly
    from srmech.math.poly import Poly
    from srmech.mcp._coercion import deserialise_native

    payload = {
        "order": 1,
        "coeffs": [Poly.from_coeffs([1, 2]), Poly.from_coeffs([3])],
        "certificate": BiPoly.coerce([[1, 1], [-1]]),
        "nested": {"deep": [{"deeper": Poly.from_coeffs([7])}]},
    }
    back = deserialise_native(loads(serialise_result(payload)))
    assert isinstance(back["certificate"], BiPoly)
    assert back["certificate"] == payload["certificate"]
    assert [type(c) for c in back["coeffs"]] == [Poly, Poly]
    assert back["coeffs"] == payload["coeffs"]
    assert back["nested"]["deep"][0]["deeper"] == Poly.from_coeffs([7])
    assert back["order"] == 1


def test_the_envelope_sentinel_is_namespaced_and_stable() -> None:
    """The wire tag is part of the format, so it is pinned like one.

    Namespaced with a leading ``$`` for the same reason
    ``HANDLE_ENVELOPE_KEY`` is: it must be unambiguous against every other wire
    shape in play — a base64 bare string, an ordinary object param, a
    serialised dataclass (which has no sentinel).
    """
    assert CARRIER_ENVELOPE_KEY == "$srmech_carrier"
    from srmech._handles import HANDLE_ENVELOPE_KEY
    assert HANDLE_ENVELOPE_KEY == "$srmech_handle"
    assert CARRIER_ENVELOPE_KEY != HANDLE_ENVELOPE_KEY
    assert not is_carrier_envelope({"$srmech_handle": {}})
    assert not is_carrier_envelope({"value": 1})
    assert is_carrier_envelope({CARRIER_ENVELOPE_KEY: "Poly", "value": []})


def test_adr0012_c5_marquee_exhibit_chains_over_the_wire() -> None:
    """ADR-0012 clause C5 (CHAINABLE), on the exhibit the ADR itself cites.

    C5 requires a producer's output to feed its designed consumer over EVERY
    ADVERTISED TRANSPORT, not only in-process, and the ADR's own illustration is
    12-TET: feed ``equal_temperament_partials``' ``ratios`` back into
    ``spectrum_tier``. The clause was marked CLOSED in-rc; the gate that
    "closed" it called both ops DIRECTLY (``tests/test_music_commensurability_rc362.py``
    does this at four sites), which is the in-process transport — the one
    transport the clause is not about. Over the wire it raised
    ``TypeError: partial[0]: expected Q, Qalg, int or an (int, int) pair; got
    str``, because ``ratios`` are ``Qalg`` and ``Qalg`` had no wire form: ``Q``
    gained its ``[num, den]`` branch at rc231 with the comment "never a lossy
    float, NEVER A BARE REPR STRING", and the algebraic peer never followed.

    This is the assertion that can return otherwise.
    """
    from srmech.mcp._coercion import deserialise_native
    from srmech.mcp._tools import invoke_tool

    raw = invoke_tool("srmech.music.equal_temperament_partials",
                      {"divisions": 12, "degrees": [0, 7, 12]})
    in_process = invoke_tool("srmech.music.spectrum_tier",
                             {"partials": raw["ratios"]})["tier"]

    # The wire leg: serialise, parse with srmech's own JSON front door, rebuild
    # structurally, and feed the SAME consumer.
    over_wire_input = deserialise_native(loads(serialise_result(raw)))["ratios"]
    assert not any(isinstance(r, str) for r in over_wire_input), (
        "the ratios came back as strings — the Qalg wire form regressed to a "
        "repr, which is exactly the C5 refutation")
    over_wire = invoke_tool("srmech.music.spectrum_tier",
                            {"partials": over_wire_input})["tier"]
    assert over_wire == in_process, (
        f"C5 CHAINABLE fails on its own exhibit: in-process tier {in_process}, "
        f"over-the-wire tier {over_wire}")


# ──────────────────────────────────────────────────────────────────────
# 2. THE DECLARED-RETURN-TYPE CENSUS
# ──────────────────────────────────────────────────────────────────────


def test_declared_return_types_without_an_inbound_coercer() -> None:
    """The residual, ratcheted DOWN-ONLY.

    An op whose declared return type has no inbound coercer cannot have its
    output fed back to a consumer by declared type — the value returns
    unchanged because nothing looked at it, so any round-trip claim over it is
    UNDEFINED rather than true. This is the honest size of what `#T1092` did
    NOT finish, kept visible so it drains instead of being forgotten.

    Note the ceiling counts OPS, not distinct type strings: one un-coercible
    type string on twelve ops is twelve unreachable ops, and it is the ops a
    consumer cares about.
    """
    warmup_all()
    tools = get_tool_schema().tools
    missing = sorted(
        t.name for t in tools
        if t.returns is not None and not has_coercer(t.returns.type)
    )
    assert len(missing) <= CEIL_RETURN_TYPES_WITHOUT_COERCER, (
        f"{len(missing)} of {len(tools)} ops declare a return type with no "
        f"inbound coercer (ceiling {CEIL_RETURN_TYPES_WITHOUT_COERCER}). "
        f"Ceilings are DOWN-ONLY — a new op with an un-coercible return type "
        f"must land its coercer in the same rc.\n"
        f"    first 20: {missing[:20]}"
    )


def test_every_carrier_with_a_wire_form_has_its_inverse() -> None:
    """A one-directional wire form is a trap, not a feature.

    An outbound encoder with no inbound rebuild produces JSON that looks
    structured and correct and cannot be sent back — which is strictly worse
    than a repr, because a repr at least announces that it is prose. The two
    tables are therefore asserted to be the same set.
    """
    from srmech.mcp._coercion import _CARRIER_WIRE

    for name, pair in sorted(_CARRIER_WIRE.items()):
        assert len(pair) == 2, name
        encode, decode = pair
        assert callable(encode), f"{name}: no outbound encoder"
        assert callable(decode), f"{name}: no inbound rebuild — a carrier that "
        f"can be emitted and not read back is worse than one that is not "
        f"emitted at all"
