"""rc463 fix pass (`#T1188`) — every entry this rc registered must actually be
CALLABLE THROUGH THE WIRE, not merely present in the registry.

THE DEFECT THIS CLOSES
======================
rc463's headline finding is that seven public names were invisible because they
carried no ``ToolEntry``. It registered eighteen entries — and **no rc463 test
drove a single one of them through** :func:`srmech.mcp._tools.invoke_tool`.
Three of the eighteen were therefore not callable at all, which is the Tier-0
defect class *reproduced inside Tier-0's own fix*:

* ``lstsq_exact`` declared ``a`` as ``Mat`` while its own summary says a float
  entry is **REFUSED by name**. ``Mat`` IS the float carrier, so the inbound
  coercer built ``Mat.from_rows([[1,1],[1,1],[1,2]])`` — float64 — and handed
  the op precisely what the op refuses. Measured:
  ``TypeError: lstsq_exact: a must be EXACT (int / Q / fractions.Fraction /
  QMat)``, raised on an operand of plain Python ints.
* ``singular_values_exact`` declared ``a`` as ``Mat`` and its summary says
  ``a float entry is REFUSED by name``. Same mechanism, same refusal.
* ``qmat_solve``'s **own shipped** ``smoke_test_hint`` —
  ``{"rows": "[[2, 0], [0, 3]]", "b": "[4, 9]"}`` — raised
  ``TypeError: 'int' object is not iterable`` through ``invoke_tool`` while
  working in direct Python, because ``b``'s declared type named only the
  rows-of-rows arm and the op has always accepted a flat exact column.

A fourth was not a refusal but a **silent demotion**, which is worse: the entry
for ``separate_frame_curvature`` advertises TWO CARRIER RUNGS and says exact
operands ride ``QMat`` so ``is_flat`` is a theorem about the true commutator.
Declared as ``Mat``, the wire could reach **only** the float rung — measured,
``invoke_tool`` returned ``Mat`` carriers for a pair of exact Pauli matrices,
i.e. the advertised rung was unreachable by every MCP caller, with no error.

All four were fixed by declaring the HONEST carrier token on the parameter (and
adding the coercer / lexicon rows the new tokens need), never by widening the
ops. The ops were right; the declarations were not.

WHY A GATE AND NOT A ONE-OFF CHECK
==================================
Registration is counted by ``EXPECTED_N`` and drains the registration ratchets.
An entry that counts toward 720 while being uncallable through ``describe()``
and the MCP tool list is a **false green in the count itself** — the exact
shape of the thing rc463 exists to end. Nothing measured wire-invocability, so
nothing could have caught it, which is why this file exists rather than a fix
alone.

⚠️ **This gate deliberately calls ``invoke_tool`` and not the op.** The op works
in direct Python in all four cases; the transport is what was broken. A test
that imported the callables would have passed on the defective tree.

BLIND SPOTS, STATED
===================
* It covers the EIGHTEEN entries this rc added, not the whole registry. The
  every-tool smoke in ``test_mcp.py`` is the population instrument; this is the
  named-witness one.
* It exercises the in-process ``invoke_tool`` seam, so a defect that lives in
  JSON *serialisation of the result* (outbound) is outside it.
* ``smoke_test_hint`` is only present on eight of the eighteen; the other ten
  carry explicit arguments here, chosen so the op returns a real answer rather
  than a tolerated domain error — a domain error would make the row unable to
  distinguish "callable" from "callable and wrong".
"""
from __future__ import annotations

import ast
from typing import Any, Dict, List, Tuple

import pytest

from srmech.introspect.tool_schema import get_tool_schema, warmup_all
from srmech.math.q import Q
from srmech.math.qmat import QMat
from srmech.mcp._tools import invoke_tool

# λ = 2 as an element of ℚ[x]/(x − 2), in the canonical JSON mapping `_to_qalg`
# reads: `m` and `coords` ASCENDING, and `root` PRESENT — a Qalg built without
# `root` is refused by the op's own projection rather than silently naming a
# different conjugate, so a hint that omitted it would not be a wire argument.
LAM_2 = {"m": [-2, 1], "coords": [[2, 1]], "root": 2.0}

#: (tool name, wire arguments) — one row per entry rc463 registered.
#: The arguments are the JSON forms an MCP client would send.
WIRE_ARGS: List[Tuple[str, Dict[str, Any]]] = [
    # ── the exact eigensolver, previously public with no ToolEntry ───────────
    ("srmech.cascade.matrix_cascades.eigvec_exact",
     {"a": [[2, 0], [0, 3]], "lam": LAM_2}),
    ("srmech.cascade.matrix_cascades.eigvec_exact_float",
     {"a": [[2, 0], [0, 3]], "lam": LAM_2}),
    ("srmech.cascade.matrix_cascades.factor_integer_poly",
     {"coeffs": [1, 0, -3, 0, 1]}),          # x⁴ − 3x² + 1, REDUCIBLE
    ("srmech.cascade.matrix_cascades.eig_exact",
     {"a": [[2, 0], [0, 3]]}),
    ("srmech.cascade.matrix_cascades.jordan_chains_exact",
     {"a": [[2, 1], [0, 2]], "lam": LAM_2}),  # defective: one 2-chain
    ("srmech.cascade.matrix_cascades.jordan_form_exact",
     {"a": [[2, 1], [0, 2]]}),
    ("srmech.cascade.matrix_cascades.separate_frame_curvature",
     {"a": [[0, 1], [1, 0]], "b": [[1, 0], [0, -1]]}),   # σx, σz
    # ── the three exact peers that needed a name ─────────────────────────────
    ("srmech.cascade.matrix_cascades.lstsq_exact",
     {"a": [[1, 1], [1, 1], [1, 2]], "b": [1, 1, 2]}),
    ("srmech.cascade.matrix_cascades.gram_schmidt_exact",
     {"basis": [[1, 1, 0], [1, 0, 1]]}),
    ("srmech.cascade.matrix_cascades.singular_values_exact",
     {"a": [[1, 1], [0, 1]]}),
    # ── exact cyclotomic trigonometry ────────────────────────────────────────
    ("srmech.math.qalg.cos_2pi_over_n", {"n": 8}),
    ("srmech.math.qalg.sin_2pi_over_n", {"n": 12}),
    # ── the six qmat_* flat ops (each also has a shipped hint, checked below) ─
    ("srmech.math.qmat.qmat_rank", {"rows": [[1, 2], [2, 4]]}),
    ("srmech.math.qmat.qmat_det", {"rows": [[1, 2], [3, 4]]}),
    ("srmech.math.qmat.qmat_inverse", {"rows": [[1, 2], [3, 4]]}),
    ("srmech.math.qmat.qmat_rref", {"rows": [[1, 2], [2, 4]]}),
    ("srmech.math.qmat.qmat_solve", {"rows": [[2, 0], [0, 3]], "b": [4, 9]}),
    ("srmech.math.qmat.qmat_nullspace", {"rows": [[1, 2], [2, 4]]}),
]

#: rc463 registered EIGHTEEN entries (702 → 720). Pinned so a row silently
#: dropped from the table above cannot make this file smaller and greener.
EXPECTED_ROWS = 18


def _entry(name: str):
    warmup_all()
    e = get_tool_schema().lookup(name)
    assert e is not None, f"{name} is not in the live registry"
    return e


# ══════════════════════════════════════════════════════════════════════
# 0. the scan is not vacuous
# ══════════════════════════════════════════════════════════════════════

def test_the_table_covers_every_entry_this_rc_registered() -> None:
    """A population assertion whose population must not quietly shrink."""
    assert len(WIRE_ARGS) == EXPECTED_ROWS, (
        f"{len(WIRE_ARGS)} rows for {EXPECTED_ROWS} entries registered by this "
        f"rc. A row removed rather than fixed is how a wire gate goes green.")
    assert len({n for n, _ in WIRE_ARGS}) == EXPECTED_ROWS, "duplicate row"
    for name, _ in WIRE_ARGS:
        assert _entry(name).mcp_callable, (
            f"{name} is registered but NOT advertised — an MCP consumer is "
            f"never offered it, so wire-invocability is not the right question")


# ══════════════════════════════════════════════════════════════════════
# 1. STRICT ZERO — every entry is callable through invoke_tool
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("name,args", WIRE_ARGS, ids=[n for n, _ in WIRE_ARGS])
def test_every_new_entry_is_invocable_through_the_wire(name, args) -> None:
    """The clause the eighteen registrations shipped without.

    ``invoke_tool`` runs the inbound coercion the declared parameter TYPE
    selects, then calls the op. A ``TypeError`` here means the declared type
    manufactured a value the op does not accept — the declaration is wrong even
    though the op is right.
    """
    got = invoke_tool(name, dict(args))
    assert got is not None, f"{name} returned None through the wire"


# ══════════════════════════════════════════════════════════════════════
# 2. the four named witnesses, pinned by VALUE and by CARRIER
# ══════════════════════════════════════════════════════════════════════

def test_qmat_solve_own_smoke_hint_works_through_the_wire() -> None:
    """The sharpest witness: an entry whose OWN shipped hint did not run.

    ``smoke_test_hint`` is the argument set the package publishes as "this is
    how you call me". If it raises through the transport the package documents,
    the entry is not callable in the only sense that matters to a consumer.
    """
    hint = _entry("srmech.math.qmat.qmat_solve").smoke_test_hint
    assert hint, "qmat_solve lost its smoke_test_hint"
    args = {k: ast.literal_eval(v) for k, v in hint.items()}
    assert args == {"rows": [[2, 0], [0, 3]], "b": [4, 9]}
    got = invoke_tool("srmech.math.qmat.qmat_solve", args)
    assert got == [[Q(2, 1)], [Q(3, 1)]], (
        f"qmat_solve's own hint returned {got!r} through the wire")


def test_every_shipped_smoke_hint_runs_through_the_wire() -> None:
    """The same clause over ALL of this rc's entries that publish a hint.

    Eight of the eighteen do. A hint that cannot be executed through the wire
    is a published falsehood about how to call the op, so this is strict zero
    rather than a ceiling.
    """
    checked = 0
    for name, _ in WIRE_ARGS:
        hint = _entry(name).smoke_test_hint
        if not hint:
            continue
        checked += 1
        args = {k: ast.literal_eval(v) for k, v in hint.items()}
        invoke_tool(name, args)
    assert checked >= 8, (
        f"only {checked} of this rc's entries published a smoke_test_hint; "
        f"eight did at rc463, so the population has shrunk")


def test_lstsq_exact_is_not_refused_by_its_own_declared_type() -> None:
    """It declared the FLOAT carrier on an operand it refuses when float.

    The returned value is pinned too, not just the absence of an exception:
    ``b`` IS the second column plus a repeat, so the exact least-squares answer
    is ``[0, 1]`` and nothing else — and it comes back as exact ``Q``, which is
    what proves the exact carrier survived the transport.
    """
    got = invoke_tool("srmech.cascade.matrix_cascades.lstsq_exact",
                      {"a": [[1, 1], [1, 1], [1, 2]], "b": [1, 1, 2]})
    assert got == [Q(0, 1), Q(1, 1)], f"got {got!r}"
    assert all(isinstance(q, Q) for q in got)


def test_singular_values_exact_is_not_refused_by_its_own_declared_type() -> None:
    """Same defect, same shape: ``a`` was ``Mat`` on an INTEGER-only op."""
    got = invoke_tool("srmech.cascade.matrix_cascades.singular_values_exact",
                      {"a": [[1, 1], [0, 1]]})
    assert isinstance(got, list) and got, f"got {got!r}"
    # descending, one dict per distinct σ, each carrying its own exact field.
    assert all("sigma_qalg" in e and "min_poly" in e for e in got)


def test_separate_frame_curvature_reaches_its_EXACT_rung_through_the_wire() -> None:
    """The silent-demotion half, and the reason a no-exception test is not enough.

    Declared as ``Mat`` this op was callable — it just always answered on the
    float rung, because the coercer built the float carrier before the op's own
    exactness gate could see the operand. The entry advertises the exact rung;
    reaching it is the assertion.
    """
    got = invoke_tool("srmech.cascade.matrix_cascades.separate_frame_curvature",
                      {"a": [[0, 1], [1, 0]], "b": [[1, 0], [0, -1]]})
    assert isinstance(got["curvature"], QMat), (
        f"exact operands reached the wire as {type(got['curvature']).__name__}; "
        f"the advertised exact-ℚ rung is unreachable through MCP again")
    assert got["is_flat"] is False
    assert got["curvature"].to_lists() == [[Q(0, 1), Q(-1, 1)],
                                           [Q(1, 1), Q(0, 1)]]
    # and the float rung is still reachable, on float operands.
    from srmech.math.mat import Mat
    flt = invoke_tool("srmech.cascade.matrix_cascades.separate_frame_curvature",
                      {"a": [[0.0, 1.0], [1.0, 0.0]],
                       "b": [[1.0, 0.0], [0.0, -1.0]]})
    assert isinstance(flt["curvature"], Mat)


# ══════════════════════════════════════════════════════════════════════
# 3. the planted defect — the gate must be able to go red
# ══════════════════════════════════════════════════════════════════════

#: The honest carrier token for an operand that REFUSES a float by name.
T_EXACT_ROWS = "QMat | Sequence[Sequence[int | Q]]"


def test_the_declared_token_is_the_causal_variable() -> None:
    """The planted defect, run at the seam where it actually lived.

    Without this, "every entry is invocable" would be indistinguishable from
    "``invoke_tool`` never raises", and every clause above would inherit that
    vacuity. The defect is run FORWARD rather than simulated: the SAME wire
    value is pushed through the OLD declared token and the NEW one, and only the
    old one produces the refusal that shipped.

    It deliberately does not mutate the live registry. ``get_tool_schema()``
    hands back a rebuildable view, so a swapped entry is not reliably the one
    ``invoke_tool`` reads — and a gate whose planted defect depends on that is
    measuring the cache, not the coercion. The coercer IS the mechanism, so the
    coercer is where the demonstration belongs.
    """
    from srmech.cascade.matrix_cascades import lstsq_exact
    from srmech.mcp._coercion import coerce_param

    wire = [[1, 1], [1, 1], [1, 2]]        # plain JSON integers, as sent
    as_mat = coerce_param(wire, "Mat", param="a")
    with pytest.raises(TypeError) as exc:
        lstsq_exact(as_mat, [1, 1, 2])
    assert "EXACT" in str(exc.value), (
        "the `Mat` token no longer manufactures the refusal it shipped; if the "
        "op stopped refusing floats, this whole gate needs re-deriving")

    as_exact = coerce_param(wire, T_EXACT_ROWS, param="a")
    assert lstsq_exact(as_exact, [1, 1, 2]) == [Q(0, 1), Q(1, 1)]

    # and the shipped declaration is the honest one, so the wire really does
    # take the second path.
    a_param = _entry("srmech.cascade.matrix_cascades.lstsq_exact").parameters[0]
    assert a_param.name == "a" and a_param.type == T_EXACT_ROWS, (
        f"lstsq_exact declares a: {a_param.type!r} — back to a carrier its own "
        f"summary says it refuses")
    sve = _entry("srmech.cascade.matrix_cascades.singular_values_exact")
    assert sve.parameters[0].type == T_EXACT_ROWS
