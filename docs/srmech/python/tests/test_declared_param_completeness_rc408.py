"""v0.9.0rc408 (`#T1078`) — THE CONVERSE RATCHET: a ToolEntry must declare
EVERY parameter its own callable accepts.

``tests/test_mcp.py::test_schema_signature_alignment_no_drift`` (v0.5.0rc13)
has guarded ONE direction since rc13: every DECLARED param must be bindable to
the real callable, so no tool is uncallable. Nothing guarded the OTHER
direction — a real parameter that the declaration simply omits.

Under *introspect IS the API contract*, an incomplete declaration is the same
severity as a false one. The failure mode is only different: not "calls
something that errors" but **"cannot reach a capability that exists"**. A
consumer reading the registry — an LLM, the MCP ``tools/list`` catalog, a
human calling ``describe()`` — is told the op has N parameters when it has
N+k, and the k are unreachable by anyone who believes the contract.

WHAT MEASURED IT. rc408 census over the 556-entry registry: **27 entries hid
35 real parameters**, every one of them OPTIONAL (all had defaults), so no
caller was broken — the capability was simply invisible. The canonical case is
``srmech.cascade.the_one``, which declared ``sigma, theta_num, theta_den,
terms`` while the live signature is ``the_one(sigma, theta_num, theta_den=1,
terms=24, w=(0, 0, 0))``. The winding triad ``w`` — which ``One.unwrapped_phase()``
demonstrably consumes (``w=(1, 0, 0)`` -> ``turns=1`` on saros) — was absent
from the contract while the capability shipped.

WHY NOTHING CAUGHT IT. Nine test files in this tree call ``inspect.signature``
and NONE of them also reads ``tool_schema``. The two surfaces had never been
compared in this direction. This gate compares them.

THE RULE (strict-zero, no ceiling). For every ToolEntry, the declared parameter
names must be a SUPERSET of the live signature's parameter names:

  * ``self`` is excluded (bound-method entries).
  * ``VAR_POSITIONAL`` (``*args``) IS required. The rc10 varargs convention
    exposes that slot under a clean name (``polar_bundle(*vectors)`` declares
    ``vectors``), so it is a real, named operand and all three current cases
    already declare it. A leading ``*`` on the declared side is stripped before
    comparison, matching the rc13 gate.
  * ``VAR_KEYWORD`` (``**kwargs``) is NOT required — it is tolerated when
    declared but never demanded. A ``**kwargs`` is an OPEN NAMESPACE, not a
    named capability, so "declaring" it would state something false: the sole
    case in the tree is ``op_provenance.reproject(**rung_override)``, whose
    keys are validated against ``spec.rung_keys`` and would REJECT a literal
    key named ``rung_override``. Declaring it by name would manufacture exactly
    the declared-but-not-real defect the rc13 gate exists to catch, and the
    capability is already reachable through the declared ``overrides=`` dict
    ("both merge; kwargs win"). Requiring VAR_KEYWORD is the one place this
    gate's first draft over-reached; the distinction is deliberate.
  * A callable whose signature cannot be read (a C builtin) is skipped, not
    failed — there is nothing to compare against.

There is deliberately NO ceiling and NO allowlist. A parameter that cannot
cross the MCP wire is still DECLARED; the wire limitation is carried by its
declared TYPE (see ``srmech.mcp._tools._TYPE_LEXICON``, where the host-side
types publish JSON-schema ``"null"`` — the only legal wire value is "absent"),
not by omitting it from the contract. Omission is the defect this gate exists
to prevent; "it cannot ride JSON" is a fact about the TYPE, not a licence to
hide the PARAMETER.
"""

from __future__ import annotations

import inspect
from typing import Dict, List, Set, Tuple

from srmech.introspect.tool_schema import get_tool_schema, warmup_all


def _live_param_names(fn: object) -> Set[str]:
    """The set of parameter names the callable really accepts.

    Returns an empty set when the signature is unreadable (a C builtin), which
    the caller treats as "nothing to compare", not as a pass.
    """
    try:
        sig = inspect.signature(fn)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return set()
    return {
        p.name
        for p in sig.parameters.values()
        if p.name != "self"
        and p.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
            # VAR_POSITIONAL is in; VAR_KEYWORD is deliberately NOT — see the
            # module docstring. An open keyword namespace is not a named
            # capability, and declaring it by name would be false.
            inspect.Parameter.VAR_POSITIONAL,
        )
    }


def _undeclared() -> Dict[str, List[str]]:
    """Map ToolEntry name -> sorted real-but-undeclared parameter names."""
    from srmech.mcp._tools import _resolve_dotted_callable

    warmup_all()
    gaps: Dict[str, List[str]] = {}
    for entry in get_tool_schema().tools:
        try:
            fn = _resolve_dotted_callable(entry.name)
        except Exception:
            # Resolution is the rc13 gate's job; a failure there is that
            # gate's finding, not this one's.
            continue
        if not callable(fn):
            continue
        live = _live_param_names(fn)
        if not live:
            continue
        declared = {p.name.lstrip("*") for p in (entry.parameters or ())}
        missing = live - declared
        if missing:
            gaps[entry.name] = sorted(missing)
    return gaps


def test_every_real_parameter_is_declared() -> None:
    """STRICT ZERO: no ToolEntry may hide a parameter of its own callable.

    This is the converse of
    ``test_mcp.py::test_schema_signature_alignment_no_drift``. That one fails
    when the registry declares something the callable does not accept; this one
    fails when the callable accepts something the registry does not declare.

    Measured 27 entries / 35 parameters when written (rc407 tree); drained to
    zero in rc408. It is strict-zero and stays strict-zero: the next rc that
    adds a parameter to a registered op goes red until it declares it.
    """
    gaps = _undeclared()
    n_params = sum(len(v) for v in gaps.values())
    assert not gaps, (
        f"{len(gaps)} ToolEntries hide {n_params} real parameters of their own "
        f"callable — the contract is INCOMPLETE, so a registry consumer cannot "
        f"reach a capability that exists. Declare each one in its ToolEntry "
        f"`parameters` tuple (a parameter that cannot cross the MCP wire is "
        f"still declared; its TYPE carries that limitation — see "
        f"srmech.mcp._tools._TYPE_LEXICON). Offenders: {gaps}"
    )


def test_the_one_declares_the_winding_triad() -> None:
    """The named case that motivated the gate (`#T1078`).

    ``srmech.cascade.the_one`` accepts ``w`` — the winding triad that turns
    S(sigma, theta) into a WOUND phase — and declared it nowhere, so the only
    documented way to reach it was to read the source. Pinned by name so a
    future signature edit cannot quietly drop it back out of the contract.
    """
    entry = next(
        e for e in get_tool_schema().tools if e.name == "srmech.cascade.the_one"
    )
    declared = {p.name for p in entry.parameters}
    assert "w" in declared, (
        f"srmech.cascade.the_one must declare the winding triad `w`; "
        f"declared: {sorted(declared)}"
    )
    w = next(p for p in entry.parameters if p.name == "w")
    assert not w.required, "`w` has a default ((0, 0, 0)) — it is not required"
    assert w.type == "tuple[int, int, int]", (
        f"`w` is the integer winding triad (n_sigma, n_theta, n_phi); "
        f"declared type is {w.type!r}"
    )


def test_host_side_params_are_declared_but_not_wire_passable() -> None:
    """The §101 ``progress`` tick and its host-side peers are DECLARED, and
    publish a JSON-schema type no client can be told to fill.

    This REPLACES the rc275 guard ``test_progress_is_never_a_tool_wire_param``
    (``tests/test_genome_progress.py``), which asserted ``progress`` appeared in
    NO entry's ``parameters``. That guard protected the right thing — a callable
    must never be advertised as a value a JSON-RPC client can send — by the
    wrong mechanism: it made the capability invisible to every consumer of the
    contract, including in-process Python callers who CAN pass it.

    The honest split, which this asserts:
      * DECLARED (so ``describe()`` / the registry tell you the capability
        exists, and what to pass in-process), and
      * never REQUIRED, and
      * published as JSON-schema ``"null"`` — a schema-obedient client can only
        send ``null``, which coerces to "absent" and runs the op with the
        callback disabled, exactly as before.

    ``progress`` is not an awkward edge case: it fires inline on the encode
    thread (zero concurrency, MCU-safe, no RTOS), it is OFF by default, and for
    a multi-hour genome encode it is the ONLY channel that reports working
    status or accepts a cancel. Hiding it hid that.
    """
    from srmech.mcp._tools import _json_schema_type_for

    schema = get_tool_schema()
    host_side = {"progress", "compatible", "rng"}
    seen: Set[str] = set()
    offenders: List[Tuple[str, str, str]] = []
    for entry in schema.tools:
        for p in entry.parameters:
            if p.name not in host_side:
                continue
            seen.add(p.name)
            if p.required:
                offenders.append((entry.name, p.name, "REQUIRED"))
            published = _json_schema_type_for(p.type)
            if published != "null":
                offenders.append(
                    (entry.name, p.name, f"publishes {published!r}, want 'null'")
                )
    assert not offenders, (
        "a host-side parameter must be declared, optional, and publish "
        f"JSON-schema 'null' (no client can be told to send one): {offenders}"
    )
    assert seen == host_side, (
        f"expected every host-side param to be declared somewhere; "
        f"missing: {sorted(host_side - seen)}"
    )


def test_progress_is_declared_on_every_op_that_accepts_it() -> None:
    """Completeness for the §101 tick specifically: all ELEVEN ops.

    The census found ``progress`` live on 11 registered ops and declared on
    none. A count, not a set membership, so an op that gains the kwarg without
    declaring it is caught here as well as by the strict-zero gate above.
    """
    schema = get_tool_schema()
    declaring = {
        e.name
        for e in schema.tools
        if any(p.name == "progress" for p in e.parameters)
    }
    assert len(declaring) == 11, (
        f"expected the 11 rc408-declared `progress` ops; got "
        f"{len(declaring)}: {sorted(declaring)}"
    )
