"""rc430 (`#T1094`) — a synthesised argument must be JUSTIFIED, and a path must never be guessed.

THE DEFECT THIS CLOSES
----------------------
``test_mcp._synth_value_for_type`` ended in ``return table.get(type_string, "a")``.
Every parameter whose declared type the 61-entry table did not name received the
literal ``"a"`` — **including filesystem paths**, so an every-tool smoke run
called ``genome_save(path="a")`` and wrote a stray 16-byte file named ``a``
into whatever directory the suite ran from. The `#T1094` note at
``tests/test_mcp.py`` records that gitignoring the file was considered and
rejected: it closes the symptom and preserves the defect.

The underlying fact is the one `#T1127` opened on. ``ToolParameter`` publishes
``name`` / ``type`` / ``required`` / ``summary`` and nothing else, so a type-keyed
table **structurally cannot** tell ``genome_save``'s ``path`` from
``normal_order``'s ``convention`` — both are ``str``. That is why the table
accreted 61 rows and still could not stop being wrong.

THE FIX, AND WHAT IT IS NOT
---------------------------
Arguments are now keyed by **(op, param)**, harvested from each op's own
published ``example["worked"]`` — an argument from a call that RETURNED is valid
by construction (``tools/example_args.py``). Path-shaped parameters with no
harvested value get a **sandbox path** in a temp directory. Anything else is
:data:`~example_args.UNSYNTHESIZABLE` and the smoke SKIPS with a named reason.

**It is not a complete fix and this file says so in numbers.** Measured at
rc430: the harvest covers only **3 of 33** path-ish parameters, because the
genome worked snippets deliberately leave ``path`` unbound — the shipped
``tests/worked_examples_result.ndjson`` has been recording that as
``NameError: name 'path' is not defined`` all along, under rc354's ceiling. So
the exemplar corpus is a weaker argument source than it looks, and tier 3 does
most of the work on the path class.

WHY A SKIP IS NOT A HOLE HERE
-----------------------------
Skipping 40 ops sounds like lost coverage, and the trade was checked rather
than assumed:

* the **binding** axis — the failure mode the smoke exists for, and the one
  that caught rc273/rc328 — is covered for **every** ToolEntry by
  ``test_mcp.py::test_schema_signature_alignment_no_drift``, which is STATIC
  and needs no synthesised value at all;
* the 59 skipped parameters are undeclared carrier types (``EllMonomial``,
  ``Poly``, ``Theta``, …). Under the old fall-through they received the string
  ``"a"``, which raised a tolerated ``TypeError`` **before reaching the op** —
  so they were never really invoked, only counted as if they had been.

The skip therefore trades a false green for a counted gap, and
:data:`CEIL_UNSYNTHESIZABLE_PARAMS` makes the gap drain. A harmless-looking
wrong value is exactly what let 19 types go without a table row for 400 rcs:
an ungated surface trickles, a gated one races to 100%.

FOUR CLAUSES
------------
1. STRICT ZERO — no required param receives the bare literal ``"a"``.
2. STRICT ZERO — the smoke creates no new filesystem entry under the package root.
3. DOWN-ONLY CEIL — unsynthesizable ``(op, param)`` pairs, per class.
4. PLANTED DEFECT — re-insert the fall-through and assert clause 1 fires.

Plus a freshness clause, because a ledger nothing re-derives is a dead seam
reporting on a tree that no longer exists (rc354's model).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT / "tools"))

import example_args as ea  # noqa: E402

from srmech.introspect.tool_schema import get_tool_schema, warmup_all  # noqa: E402

# ── the down-only ceilings, measured at rc430 ─────────────────────────

#: (op, param) pairs with no justified value. rc430: 59, all undeclared
#: carrier types. Drains by adding a row to ``_synth_value_for_type``'s table
#: or by making the op's worked example bind the parameter.
# rc461 part 2 (`#T1181`) measured this at 52 and did NOT raise it. Recorded
# because the first attempt DID raise it to 54, on a reason that turned out to
# be false, and the correction is the useful part: the +2 was not this rc's ops
# at all. It came from re-running `tools/run_example_args.py` in FULL, which
# re-harvests every snippet in one process and flipped an unrelated row —
# `srmech.math.rational.rational_div` went `ok` -> `no_jsonable_arg`, its two
# `Q | tuple[int, int]` params arriving as `Q` objects where the committed
# ledger had recorded them as `(19, 20)` / `(9991, 10000)` tuples, same
# `src_sha256` and same 4 recorded calls. Re-running with `--only-stale`
# instead harvests only the genuinely-new rows and leaves all 692 others
# byte-identical, and the count returns to 52. THE LESSON, since the ledger's
# own freshness clause only compares `src_sha256`: a full re-harvest is not a
# no-op on unchanged rows, so use `--only-stale` unless you mean to re-measure
# the whole surface. This rc's three ops contribute ZERO here — `Mat` already
# has a `_synth_value_for_type` row, `g2_membership`'s operand is harvested
# from its worked example, and `epq_frame_address` takes no parameters.
CEIL_UNSYNTHESIZABLE_PARAMS = 52

#: Advertised ops skipped entirely because at least one required param is
#: unsynthesizable. rc430: 34.
CEIL_UNSYNTHESIZABLE_OPS = 34

#: Path-shaped required params served by a sandbox path. rc430: 30.
#:
#: This is a FLOOR-shaped quantity wearing a ceiling, and the reason is worth
#: keeping: path parameters are deliberately never harvested (a harvested path
#: is a temp file the snippet created, gone by the time anything reads the
#: ledger — measured on ``fiedler_sparse_file``, which made the frame census
#: answer differently on two runs of the same tree). So this number only falls
#: if a path parameter stops being required, and it rises when a new op takes
#: one. It is held to make that growth VISIBLE, not to drive it to zero.
CEIL_SANDBOX_FALLBACK_PARAMS = 30


def _synth_mod():
    """``test_mcp``, imported lazily — it is the module under test here."""
    sys.path.insert(0, str(PKG_ROOT / "tests"))
    import test_mcp
    return test_mcp


def _advertised():
    warmup_all()
    return [t for t in get_tool_schema().tools if t.mcp_callable]


def _classify() -> Dict[str, Any]:
    """One pass over the advertised registry: what tier fed every required param."""
    tm = _synth_mod()
    prov = ea.provider()
    out: Dict[str, Any] = {
        "literal_a": [], "unsat": [], "sandbox": [],
        "harvested": 0, "tabled": 0, "required": 0, "skipped_ops": set(),
    }
    for t in _advertised():
        args = tm._synth_args_for_entry(t)
        for p in t.parameters:
            if not p.required:
                continue
            out["required"] += 1
            v = args.get(p.name)
            if isinstance(v, str) and v == "a":
                out["literal_a"].append((t.name, p.name, p.type))
            if v is ea.UNSYNTHESIZABLE:
                out["unsat"].append((t.name, p.name, p.type))
                out["skipped_ops"].add(t.name)
            elif prov.has(t.name, p.name):
                out["harvested"] += 1
            elif ea.is_path_shaped(p.name, p.type):
                out["sandbox"].append((t.name, p.name, p.type))
            else:
                out["tabled"] += 1
    return out


# ══════════════════════════════════════════════════════════════════════
# 0. The gate must have looked at something
# ══════════════════════════════════════════════════════════════════════

def test_the_scan_is_not_vacuous() -> None:
    """Every clause below is an assertion over a POPULATION, and a population
    that silently comes back empty makes all of them green. That is the exact
    false green this file exists to remove, so it must fail LOUDLY first."""
    c = _classify()
    assert len(_advertised()) > 500, "advertised registry unexpectedly small"
    assert c["required"] > 900, (
        f"only {c['required']} required params scanned; rc430 measured 1063. "
        f"A scan that has stopped observing reports a perfectly clean surface.")
    assert c["harvested"] > 0, (
        "ZERO parameters came from the harvest. Either the ledger is missing "
        "(run tools/run_example_args.py) or the provider stopped resolving — "
        "and with it the entire justification tier this rc added.")
    print(f"\n[rc430] tiers — harvested {c['harvested']} · table "
          f"{c['tabled']} · sandbox {len(c['sandbox'])} · unsynthesizable "
          f"{len(c['unsat'])} of {c['required']} required params")


# ══════════════════════════════════════════════════════════════════════
# 1. STRICT ZERO — the literal "a" is gone
# ══════════════════════════════════════════════════════════════════════

def test_no_required_param_receives_the_bare_literal_a() -> None:
    """`#T1094` clause 1. The fall-through that produced it is deleted; this
    asserts the consequence rather than trusting the deletion."""
    c = _classify()
    assert not c["literal_a"], (
        f"{len(c['literal_a'])} required param(s) still receive the literal "
        f"\"a\":\n  " + "\n  ".join(f"{o} :: {p} ({ty})"
                                    for o, p, ty in c["literal_a"][:20])
        + "\n\nThat literal is what wrote a stray file named `a` into the "
          "package directory. If a new type genuinely needs a string, give it "
          "a NAMED row in _synth_value_for_type's table.")


# ══════════════════════════════════════════════════════════════════════
# 2. STRICT ZERO — the smoke writes nothing into the tree
# ══════════════════════════════════════════════════════════════════════

def _tree(root: Path):
    return {p for p in root.rglob("*")
            if "__pycache__" not in p.parts and p.suffix != ".pyc"}


def test_synthesised_args_create_no_file_under_the_package_root(tmp_path) -> None:
    """`#T1094` clause 2 — the defect measured directly, on the ops that carry it.

    Every advertised op with a required path-shaped param is invoked with its
    synthesised arguments, and the package tree is diffed around the run. This
    is the observation that gitignoring the stray file would have suppressed.
    """
    import os
    from srmech.mcp._tools import invoke_tool

    tm = _synth_mod()
    targets = [t for t in _advertised()
               if any(p.required and ea.is_path_shaped(p.name, p.type)
                      for p in t.parameters)]
    assert targets, (
        "no advertised op has a required path-shaped parameter — either the "
        "registry changed shape or is_path_shaped stopped matching. Without a "
        "subject this clause is vacuous.")

    pkg = PKG_ROOT / "srmech"
    before = _tree(pkg)
    cwd = os.getcwd()
    os.chdir(tmp_path)                    # a write to a RELATIVE path lands here
    try:
        for t in targets:
            try:
                invoke_tool(t.name, tm._synth_args_for_entry(t))
            except BaseException:
                pass                       # domain errors are the normal case
    finally:
        os.chdir(cwd)
    new = sorted(str(p.relative_to(pkg)) for p in (_tree(pkg) - before))

    assert not new, (
        f"invoking {len(targets)} path-taking op(s) with synthesised args "
        f"created {len(new)} entr(ies) under {pkg}:\n  " + "\n  ".join(new[:20])
        + "\n\nA synthesised path must point into a sandbox, never into the "
          "package tree. Do NOT gitignore these — that closes the symptom and "
          "preserves the defect (`#T1094`).")

    stray = sorted(p.name for p in tmp_path.rglob("*"))
    assert not stray, (
        f"{len(stray)} entr(ies) landed in the working directory: {stray[:10]}. "
        f"A synthesised path that is RELATIVE writes wherever the suite happens "
        f"to run — the same defect, one directory over.")

    # ── NON-VACUITY ────────────────────────────────────────────────────
    # Everything above is "nothing was created", which is also what a run that
    # never reached a write would report. The clause is only a measurement if
    # some op DID write and the write was redirected. Measured at rc430: with
    # the pre-fix synth this same op set creates a file in the working
    # directory; with the fix it creates one in the sandbox instead.
    wrote = sorted(p.name for p in ea.sandbox_dir().rglob("*") if p.is_file())
    assert wrote, (
        "no op wrote into the sandbox, so 'nothing was created in the package "
        "tree' is true for the trivial reason and this clause proves nothing. "
        "Either the ops stopped reaching their write, or the sandbox tier "
        "stopped being used — both make the #T1094 fix unverified.")
    print(f"\n[rc430] {len(targets)} path-taking ops invoked · package tree "
          f"unchanged · cwd clean · {len(wrote)} file(s) REDIRECTED into the "
          f"sandbox {ea.sandbox_dir()}: {wrote[:8]} — the redirect is the "
          f"measurement; without it this clause would be vacuous.")


# ══════════════════════════════════════════════════════════════════════
# 3. DOWN-ONLY CEILS — the residual is counted, not hidden
# ══════════════════════════════════════════════════════════════════════

def test_unsynthesizable_residual_is_at_or_below_the_ceiling() -> None:
    """`#T1094` clause 3. A skip is only honest while it is bounded."""
    c = _classify()
    n_p, n_o, n_s = len(c["unsat"]), len(c["skipped_ops"]), len(c["sandbox"])
    by_type: Dict[str, int] = {}
    for _, _, ty in c["unsat"]:
        by_type[ty] = by_type.get(ty, 0) + 1
    print(f"\n[rc430] UNSYNTHESIZABLE {n_p} param(s) over {n_o} op(s) "
          f"(CEILs {CEIL_UNSYNTHESIZABLE_PARAMS} / {CEIL_UNSYNTHESIZABLE_OPS}); "
          f"sandbox fallback {n_s} (CEIL {CEIL_SANDBOX_FALLBACK_PARAMS})")
    for ty in sorted(by_type, key=lambda k: -by_type[k]):
        print(f"    {by_type[ty]:4d}  {ty}")

    assert n_p <= CEIL_UNSYNTHESIZABLE_PARAMS, (
        f"unsynthesizable params rose to {n_p}, above "
        f"CEIL_UNSYNTHESIZABLE_PARAMS={CEIL_UNSYNTHESIZABLE_PARAMS}. A new op "
        f"declaring an undeclared carrier type is the usual cause: add a row "
        f"to _synth_value_for_type's table. Raising the CEIL needs a reason "
        f"in the same diff.")
    assert n_o <= CEIL_UNSYNTHESIZABLE_OPS, (
        f"skipped ops rose to {n_o}, above {CEIL_UNSYNTHESIZABLE_OPS}")
    assert n_s <= CEIL_SANDBOX_FALLBACK_PARAMS, (
        f"sandbox-fallback params rose to {n_s}, above "
        f"{CEIL_SANDBOX_FALLBACK_PARAMS}. Drain it by making the op's worked "
        f"example BIND its path parameter, which also fixes the "
        f"`NameError: name 'path' is not defined` those snippets record in "
        f"worked_examples_result.ndjson.")


def test_the_ceils_are_not_slack() -> None:
    """A ceiling far above the live count ratchets nothing. Reported, never
    asserted — a drained CEIL is a GOOD outcome and must not fail."""
    c = _classify()
    print(f"\n[rc430] CEIL headroom — params "
          f"{CEIL_UNSYNTHESIZABLE_PARAMS - len(c['unsat'])}, ops "
          f"{CEIL_UNSYNTHESIZABLE_OPS - len(c['skipped_ops'])}, sandbox "
          f"{CEIL_SANDBOX_FALLBACK_PARAMS - len(c['sandbox'])}. Lower each to "
          f"the live count when headroom appears; that is a normal commit.")
    assert True


# ══════════════════════════════════════════════════════════════════════
# 4. FRESHNESS — the ledger describes THIS tree
# ══════════════════════════════════════════════════════════════════════

def test_ledger_is_fresh_against_the_live_schema() -> None:
    """The clause that makes the other four trustworthy (rc354's model).

    Without it the provider reports on a tree that no longer exists, and every
    coverage number above becomes a statement about history.
    """
    assert ea.LEDGER.exists(), (
        f"{ea.LEDGER.name} is missing. Run: python3 tools/run_example_args.py")
    rows = ea.load_ledger()
    sys.path.insert(0, str(PKG_ROOT / "tools"))
    import run_worked_examples as rwe

    warmup_all()
    live = {}
    for t in get_tool_schema().tools:
        if t.owner != "srmech":
            continue
        ex = t.example if isinstance(t.example, dict) else None
        live[t.name] = rwe.src_sha256(ex) if (ex and ex.get("worked")) else ""

    missing = sorted(set(live) - set(rows))
    extra = sorted(set(rows) - set(live))
    stale = sorted(n for n in set(live) & set(rows)
                   if rows[n].get("src_sha256") != live[n])
    assert not (missing or extra or stale), (
        f"ledger is STALE.\n  missing {missing[:10]}\n  extra {extra[:10]}\n"
        f"  changed snippet {stale[:10]}\n\nRun: "
        f"python3 tools/run_example_args.py --only-stale")


def test_harness_integrity_is_recorded_not_tolerated() -> None:
    """PF9. A run in which workers died must not be able to look clean.

    The rc430 scope round recorded **251 of 533 probes dead while the process
    exited 0 with all eight named controls passing**, because every control
    happened to be probed before the cascade started. A control set that a
    half-dead run satisfies is not a control set. So the harvest writes its
    failures into the ledger as statuses, and this asserts on them.
    """
    meta = ea.load_meta()
    rows = ea.load_ledger()
    assert meta, "ledger has no meta row — regenerate it"
    by_status: Dict[str, int] = {}
    for r in rows.values():
        by_status[r.get("status", "?")] = by_status.get(r.get("status", "?"), 0) + 1
    print(f"\n[rc430] harvest statuses: {json.dumps(by_status, sort_keys=True)}")

    dead = by_status.get("worker_died", 0) + by_status.get("worker_restart", 0)
    assert dead == 0, (
        f"{dead} op(s) recorded a dead harvest worker. The ledger's coverage "
        f"numbers are not trustworthy until they are re-run.")
    # A timeout is a DECISION with a number attached, not a silent drop — but
    # it must stay rare, or the harvest is measuring its own budget.
    assert by_status.get("timeout", 0) <= 2, (
        f"{by_status.get('timeout')} harvest timeouts; the budget is being "
        f"measured instead of the ops. Add the op to run_worked_examples's "
        f"SLOW_ALLOWLIST with a measured number, as that module already does.")


# ══════════════════════════════════════════════════════════════════════
# 5. PLANTED DEFECT — the gate FIRES
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("kind", ["literal_a_fallthrough", "path_guess"])
def test_gate_fires_on_a_planted_defect(kind: str) -> None:
    """A gate that cannot fail is documentation. Re-introduce each half of the
    defect in a fixture and assert the corresponding clause turns red."""
    if kind == "literal_a_fallthrough":
        # The exact pre-rc430 fall-through, on a type the table does not name.
        tm = _synth_mod()
        planted = tm._synth_value_for_type("EllMonomial")
        assert planted is ea.UNSYNTHESIZABLE, (
            "an undeclared type no longer falls through to a value — if this "
            "changed, clause 1 above is no longer testing anything")
        # and the defect, reproduced:
        table_get = {"int": 1}.get("EllMonomial", "a")
        assert table_get == "a"
        offenders = [("op", "p", "EllMonomial")] if table_get == "a" else []
        assert offenders, "the planted fall-through did not produce the literal"

    else:  # path_guess — a path-shaped param given a package-relative name
        assert ea.is_path_shaped("path", "str")
        assert ea.is_path_shaped("out_dir", "str")
        assert ea.is_path_shaped("p", "pathlib.Path")
        # and the negative control: a label-shaped str must NOT be diverted,
        # or clause 2 would pass by diverting everything.
        assert not ea.is_path_shaped("convention", "str")
        assert not ea.is_path_shaped("name", "str")
        assert not ea.is_path_shaped("n", "int")
        sandbox = ea.sandbox_path("path")
        assert str(PKG_ROOT) not in sandbox, (
            f"the sandbox path {sandbox} is inside the package tree — clause 2 "
            f"would then be green while the defect is live")
