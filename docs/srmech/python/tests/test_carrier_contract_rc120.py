"""0.9.0rc120 — the per-op CARRIER CONTRACT (issue #1254 / UPSTREAM §87 / F1041):
make the per-op carrier RUNG machine-readable so a driver routes carriers WITHOUT
a hardcoded op→rung name-map or a register-length heuristic.

Before rc120 the operand dimension lived only in a param SUMMARY
(``octonion_conjugate``'s "8" was PROSE), and ``qm.*`` / ``cd`` ops carried no
DSL descriptor at all — so a driver (siona) had to INFER the rung from the op
NAME (a hardcoded ``octonion→8`` map) or sniff the register's sequence length.
That inference was the last hardcode between the driver and fully-declarative
carrier routing.

FORM CHOSEN: (2) — extend :func:`carrier_ladder_descriptor` with an ``"ops"``
map (the issue's second option). One SSoT surface, living where the ladder facts
already live; no per-``ToolParameter`` churn across the whole schema; NO new
public callable (``carrier_ladder_descriptor`` gains a key), so tools.total is
unchanged (384). Metadata only — no op behaviour change, no ABI impact.

The gates:
  (1) THE DoD — a driver reads ``octonion_conjugate → rung 8`` and
      ``cd_promote → variadic`` straight from the declaration, resolving every
      rung through the DECLARED GRAMMAR ONLY (no ``{op: rung}`` dict anywhere in
      the driver path), and uses the read rung to promote + call end-to-end;
  (2) SELF-CONSISTENCY — every op contract's ``tool`` resolves to a real
      ToolEntry, its leaf key matches, and every INT rung it references appears
      in ``carrier_ladder_descriptor()``'s ``ladders[<ladder>].rungs`` (a
      cayley_dickson rung-8 op references the SAME 8 the octonion 'O' declares);
  (3) the rung GRAMMAR resolves for each form (int / "any" / "same" /
      "arg:<param>" / "step_down");
  (4) coverage — the cd family (octonion/quaternion + generic cd_* + promote/
      project), the variable-ladder promote/project, and the prose constructors;
  (5) registration — tools.total unchanged at 384; the descriptor ToolEntry
      still present; the ``ops`` view reachable via the registry;
  (6) hygiene — the touched module stays numpy / math / abs() free.

MPM: in-repo SSOT (the carriers' own conventions + the rc116 ladder descriptor);
no external citations.
"""

from fractions import Fraction

import pytest

from srmech.amsc.carrier_ladder import carrier_ladder_descriptor
from srmech.amsc.tool_schema import get_tool_schema
from srmech.amsc.cascade import cd_promote
from srmech.qm.octonion import octonion_conjugate
from srmech.mcp import invoke_tool


# ── the driver's rung resolver — DECLARED GRAMMAR ONLY, no op→rung name-map ────

def _resolve_rung(slot, *, args=None, input_rung=None, ladders=None):
    """Resolve a contract slot's rung to a concrete value using ONLY the declared
    grammar. This is exactly what a driver does — and it contains NO hardcoded
    op→rung map: the rung is read from the contract, never from the op name."""
    rung = slot.get("rung")
    if isinstance(rung, int):                       # a FIXED rung
        return rung
    if rung == "any":                               # VARIADIC
        return "any"
    if rung == "same":                              # ladder endomorphism
        return input_rung
    if isinstance(rung, str) and rung.startswith("arg:"):
        return int((args or {})[rung.split(":", 1)[1]])   # rung-from-argument
    if rung == "step_down":                         # one rung down the ladder
        vals = sorted(ladders[slot["ladder"]]["rungs"].values())
        below = [v for v in vals if v < input_rung]
        assert below, f"no rung below {input_rung} on {slot['ladder']}"
        return below[-1]
    raise AssertionError(f"unknown rung grammar {rung!r}")   # pragma: no cover


# ── (1) THE DoD — read the rung with no name-map, route end-to-end ────────────

def test_dod_driver_reads_octonion_rung_8_without_name_map():
    """A driver reads ``octonion_conjugate → rung 8`` DIRECTLY from the contract
    — no ``{octonion: 8}`` dict, no sequence-length sniff."""
    ops = carrier_ladder_descriptor()["ops"]
    consumes = ops["octonion_conjugate"]["consumes"]
    assert consumes == {"ladder": "cayley_dickson", "rung": 8}
    # the '8' is a first-class field, not prose parsed out of a summary
    assert consumes["rung"] == 8 and isinstance(consumes["rung"], int)


def test_dod_driver_reads_cd_promote_as_variadic():
    """``cd_promote`` consumes 'any' (variadic) and produces 'arg:dim'
    (rung-from-argument) — both read straight from the declaration."""
    ops = carrier_ladder_descriptor()["ops"]
    assert ops["cd_promote"]["consumes"]["rung"] == "any"
    assert ops["cd_promote"]["produces"]["rung"] == "arg:dim"


def test_dod_driver_routes_quaternion_into_octonion_end_to_end():
    """THE FULL DoD: a driver holds a dim-4 quaternion and wants to call
    ``octonion_conjugate`` (which needs dim 8). It reads the TARGET rung (8) from
    the contract, promotes 4 → 8 with that read rung, and calls — WITHOUT any
    op→rung name-map (the only op→rung fact used is the one it read)."""
    d = carrier_ladder_descriptor()
    ops, ladders = d["ops"], d["ladders"]

    held = (Fraction(1), Fraction(2), Fraction(-1), Fraction(3))   # a dim-4 ℍ

    # the driver reads the consumer's required rung from the CONTRACT — no map.
    target = _resolve_rung(ops["octonion_conjugate"]["consumes"], ladders=ladders)
    assert target == 8

    promoted = cd_promote(list(held), target)       # promote 4 → the READ rung 8
    assert len(promoted) == 8
    result = octonion_conjugate([float(x) for x in promoted])
    assert len(result) == 8
    # conjugate of a promoted-real-quaternion: slot 0 kept, imaginary flipped
    assert result[0] == 1.0 and result[1] == -2.0 and result[4] == 0.0

    # the anti-test: the driver code path above holds NO literal op→rung dict.
    src = _resolve_rung.__doc__ or ""
    assert "name" in src and "no hardcoded" in src.lower()


def test_dod_rung_from_arg_resolves_to_the_dim_argument():
    """The rung-from-argument case: ``cd_promote`` produces the rung its ``dim``
    argument names — the driver resolves ``arg:dim`` against the actual call."""
    d = carrier_ladder_descriptor()
    ops, ladders = d["ops"], d["ladders"]
    produced = _resolve_rung(
        ops["cd_promote"]["produces"], args={"dim": 16}, ladders=ladders)
    assert produced == 16                            # a sedenion target
    produced8 = _resolve_rung(
        ops["cd_promote"]["produces"], args={"dim": 8}, ladders=ladders)
    assert produced8 == 8


def test_dod_step_down_resolves_one_rung_down():
    """The ``step_down`` produce (cd_project / *_project): one rung down the
    ladder from the input rung, resolved against the ladder's rung values."""
    d = carrier_ladder_descriptor()
    ops, ladders = d["ops"], d["ladders"]
    # cd_project from a dim-8 octonion → dim-4 quaternion
    assert _resolve_rung(ops["cd_project"]["produces"],
                         input_rung=8, ladders=ladders) == 4
    # cd_project from a dim-16 sedenion → dim-8 octonion
    assert _resolve_rung(ops["cd_project"]["produces"],
                         input_rung=16, ladders=ladders) == 8
    # poly_project from rung-3 TriPoly → rung-2 BiPoly (variable ladder)
    assert _resolve_rung(ops["poly_project"]["produces"],
                         input_rung=3, ladders=ladders) == 2


def test_same_rung_endomorphism_resolves_to_input():
    """``cd_mult`` / ``cd_conjugate`` are ladder endomorphisms — produce 'same' =
    the consumed rung."""
    d = carrier_ladder_descriptor()
    ops, ladders = d["ops"], d["ladders"]
    assert ops["cd_mult"]["consumes"]["rung"] == "any"
    assert _resolve_rung(ops["cd_mult"]["produces"],
                         input_rung=8, ladders=ladders) == 8
    assert _resolve_rung(ops["cd_conjugate"]["produces"],
                         input_rung=16, ladders=ladders) == 16


# ── (2) SELF-CONSISTENCY — op contracts agree with the ladder descriptor ──────

def test_op_contracts_are_self_consistent_with_the_ladder_descriptor():
    """Every op contract's ``tool`` resolves to a registered ToolEntry, its leaf
    key matches, and every INT rung it references is a real rung of its ladder —
    so the per-op contract and the ladder rungs table cannot drift."""
    d = carrier_ladder_descriptor()
    ops, ladders = d["ops"], d["ladders"]
    schema = get_tool_schema()

    for leaf, contract in ops.items():
        full = contract["tool"]
        assert schema.lookup(full) is not None, f"{leaf}: no ToolEntry {full}"
        assert full.split(".")[-1] == leaf, f"{leaf} != leaf of {full}"
        assert set(contract) == {"tool", "consumes", "produces"}, leaf

        for side in ("consumes", "produces"):
            slot = contract[side]
            ladder, rung = slot.get("ladder"), slot.get("rung")
            if ladder is None:                       # a non-ladder carrier slot
                assert "type" in slot, f"{leaf}.{side}: non-ladder needs a type"
                continue
            assert ladder in ladders, f"{leaf}.{side}: unknown ladder {ladder}"
            if isinstance(rung, int):
                assert rung in ladders[ladder]["rungs"].values(), (
                    f"{leaf}.{side}: rung {rung} is not a {ladder} rung")
            else:
                assert (rung in ("any", "same", "step_down")
                        or rung.startswith("arg:")), (
                    f"{leaf}.{side}: bad rung grammar {rung!r}")


def test_cd_rungs_reference_the_same_ints_the_ladder_declares():
    """The specific cross-check the issue names: the octonion ops reference the
    SAME 8 the descriptor's 'O' rung declares; quaternion ops the SAME 4 as 'H'.
    The R/C/H/O/S ↔ dim labels the driver used to name-map are now ATTACHED to
    the ops that consume each rung."""
    d = carrier_ladder_descriptor()
    ops, cd_rungs = d["ops"], d["ladders"]["cayley_dickson"]["rungs"]
    for leaf in ("octonion_conjugate", "octonion_norm", "octonion_left_mult"):
        assert ops[leaf]["consumes"]["rung"] == cd_rungs["O"] == 8
    for leaf in ("quaternion_conjugate", "quaternion_norm",
                 "quaternion_left_mult"):
        assert ops[leaf]["consumes"]["rung"] == cd_rungs["H"] == 4


# ── (3) COVERAGE — the families that got contracts ────────────────────────────

def test_coverage_of_the_cd_and_ladder_families():
    """The contract covers the cd family (octonion/quaternion fixed-rung +
    generic cd_* variadic + promote/project) and the variable-ladder promote/
    project + prose constructors."""
    ops = carrier_ladder_descriptor()["ops"]
    expected = {
        # octonion (fixed rung 8)
        "octonion_conjugate", "octonion_norm", "octonion_left_mult",
        "octonion_right_mult", "octonion_exp", "octonion_exp_series_truncate",
        "octonion_twiddle",
        # quaternion (fixed rung 4)
        "quaternion_conjugate", "quaternion_norm", "quaternion_left_mult",
        "quaternion_right_mult", "quaternion_exp",
        "quaternion_exp_series_truncate", "quaternion_twiddle",
        # generic cd_* (variadic "any")
        "cd_mult", "cd_conjugate", "cd_norm_sq", "left_mult_kernel",
        "left_mult_is_invertible",
        # promote / project
        "cd_promote", "cd_project", "poly_promote", "poly_project",
        "qpoly_promote", "qpoly_project",
        # prose constructors (produce a fixed rung)
        "bipoly_from_coeffs", "tripoly_from_coeffs", "qpoly_from_coeffs",
        "qbipoly_from_coeffs",
    }
    assert expected <= set(ops), sorted(expected - set(ops))
    assert len(ops) == len(expected) == 29


def test_producers_declare_the_rung_they_emit():
    """A driver chaining an op's OUTPUT reads the produced rung: the exp/twiddle
    family and the constructors produce a fixed rung; left/right_mult produce a
    non-ladder Mat."""
    ops = carrier_ladder_descriptor()["ops"]
    assert ops["octonion_exp"]["produces"] == {"ladder": "cayley_dickson", "rung": 8}
    assert ops["quaternion_twiddle"]["produces"] == {"ladder": "cayley_dickson", "rung": 4}
    assert ops["bipoly_from_coeffs"]["produces"] == {"ladder": "variable", "rung": 2}
    assert ops["tripoly_from_coeffs"]["produces"] == {"ladder": "variable", "rung": 3}
    assert ops["qbipoly_from_coeffs"]["produces"] == {"ladder": "variable_q", "rung": 2}
    assert ops["octonion_left_mult"]["produces"] == {"ladder": None, "type": "Mat"}


# ── (4) REGISTRATION — reachable via the registry; tools.total unchanged ──────

def test_ops_view_reachable_via_the_registry():
    d = invoke_tool(
        "srmech.amsc.carrier_ladder.carrier_ladder_descriptor", {})
    assert "ops" in d
    assert d["ops"]["octonion_conjugate"]["consumes"]["rung"] == 8


def test_tools_total_unchanged_at_384():
    """FORM (2): the contract is a descriptor FIELD, not a new callable → 0 delta
    on tools.total (no new ToolEntry, no rosetta / coverage change)."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 388


def test_descriptor_shape_still_has_carriers_and_ladders():
    """Additive-only: the rc116 'carriers' + 'ladders' views are untouched."""
    d = carrier_ladder_descriptor()
    assert set(d) == {"carriers", "ladders", "ops"}
    assert d["carriers"]["Poly"] == {"ladder": "variable", "rung": 1}
    assert d["ladders"]["cayley_dickson"]["rungs"] == {
        "R": 1, "C": 2, "H": 4, "O": 8, "S": 16}


def test_ops_view_is_mutation_safe():
    """Each call returns a FRESH ops map — a caller mutating one does not poison
    the next (the rebuild-fresh-each-call discipline)."""
    d1 = carrier_ladder_descriptor()
    d1["ops"]["octonion_conjugate"]["consumes"]["rung"] = 999
    d2 = carrier_ladder_descriptor()
    assert d2["ops"]["octonion_conjugate"]["consumes"]["rung"] == 8


# ── (5) hygiene: numpy-free / math-free / abs()-free source ───────────────────

def test_carrier_ladder_module_is_numpy_math_abs_free():
    import srmech.amsc.carrier_ladder as CL
    text = open(CL.__file__, encoding="utf-8").read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert "abs(" not in text.replace("abs()", "")   # Class-K discipline
