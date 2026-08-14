"""rc355 (`#T993`) — the ``example["input"]`` vs ``inputSchema`` CROSS-CHECK.

THE HOLE THIS CLOSES
====================
Two schemas ship side by side inside every wheel, and until now **nobody
compared them to each other**:

* ``ToolEntry.parameters`` → rendered into ``inputSchema.properties`` /
  ``.required`` by ``srmech/mcp/_tools.py:289`` ``tool_entry_to_mcp_def`` —
  the thing an MCP client validates a call against;
* ``ToolEntry.example["input"]`` — the dict a reader copies to make that call.

``srmech/introspect/tool_schema.py:28`` declares the contract in one line::

    "input":  {"data": "b'abc'"},

i.e. ``input`` is a **kwargs map** — its keys are parameter names. Nothing
enforced it. The existing guards are each sound and each blind to this:

* ``tests/test_mcp.py:128`` checks property KEYS against Anthropic's grammar —
  it never looks at ``example``;
* ``tests/test_mcp.py:155`` checks ``required ⊆ properties`` — both sides come
  from ``parameters``, so ``example`` is again untouched;
* ``tests/test_worked_examples_strict_zero_rc353.py`` stringifies the example
  (``str(t.example or "")``) and greps it — it never compares keys to anything;
* ``tools/run_worked_examples.py:180`` executes ``setup + worked`` and
  ``:198`` selects on ``ex.get("worked")`` — it never reads ``input`` at all.

So a reader could be handed ``jacobi_sncndn_series_truncate(u=…, m=…)`` next to
an ``inputSchema`` whose required set is ``{numerator, denominator, m_numerator,
m_denominator, num_terms}`` and get a ``TypeError``. Measured 2026-07-28 on the
rc354 tree: **189 of 386 input-bearing entries publish an example that is
invalid under their own live inputSchema** — 36.8% of all 513 srmech tools.

REACH — THIS SHIPS
==================
The same dicts are compiled into ``docs/srmech/c/src/srmech_tool_registry.c``
(383 ``"input":`` literals) and live in ``srmech/introspect/_tool_docs.py`` inside the
wheel, so they reach users through ``describe()``, the MCP tool list and the
compiled-in C registry — the same three surfaces the ref-notation arc measured.

WHAT THE COUNT ACTUALLY IS — three conventions wearing one field name
=====================================================================
The 189 are not one defect repeated. Sorting them by shape shows ``input``
carrying **three incompatible conventions**, only one of which the docstring
blesses:

* ``mixed_param_and_prose`` (15) and ``missing_required`` (6) — genuine kwargs
  maps that broke. ``'coupling / dt'`` fuses two real parameters into one key;
  ``'numerator/denominator'`` does the same on ``best_rational``, the very op
  ``CLAUDE.md`` flags as the int-pair trap. **These 21 are unambiguous defects
  under the tree's own documented contract** and are the drain-first target.
* ``numeric_call_index`` (87) — keys ``"1".."6"``, one per call in a
  multi-call transcript. Internally disciplined: see STRICT ZERO 2 below.
* ``all_prose_labels`` (70) — free prose (``"Antikythera dials"``). A different
  field wearing the ``input`` name.
* ``zero_param_with_keys`` (11) — ``parameters=()`` so ``properties`` is empty
  and every key is extra; 3 of them spell the literal ``'(no arguments)'``.

A ceiling alone will never drain the 157 convention rows, because they are not
sloppy kwargs — they are a different field. The landable fix is to move the
numeric and prose forms to a separate ``scenarios`` key so ``input`` is strictly
a kwargs map, which takes 189 → 21 by rename alone; then the 21 are hand-fixed
and the whole thing becomes a third strict zero. That is deliberately NOT done
here: renaming a field touches every consumer plus the generated C registry, and
this rc ships the missing GUARD, not a mechanical batch-convert of 383 literals.

WHY PER-CLASS CEILS AND NOT ONE GLOBAL NUMBER
=============================================
Per the rc354 rule that a regression must not hide behind an unrelated fix: one
global ceiling of 189 would let 15 new ``missing_required`` entries land as long
as someone deleted 15 prose labels the same week. Each class ratchets alone.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from srmech.introspect.tool_schema import get_tool_schema, warmup_all
from srmech.mcp._tools import tool_entry_to_mcp_def

warmup_all()


# ── the down-only ceilings ────────────────────────────────────────────────
#
# MEASURED 2026-07-28 on the rc354 tree (ce7271ec8): 513 srmech-owned tools,
# 386 of them carrying a dict ``example["input"]``, 197 already clean.
#
# ⚠️ THESE ONLY EVER GO DOWN. If a number here is too small, you introduced a
# mismatch — fix the example, do not raise the ceiling. If a number is too
# large, LOWER it in the same commit that drained the rows; a ceiling left
# above the true count is exactly the slack a false green lives in.
CEIL_EXAMPLE_INPUT_KEY_MISMATCH: Dict[str, int] = {
    # rc408 (`#T1078`): 15 -> 14. ``srmech.biology.genome.genome_append``'s
    # example already called the op with a ``catalog`` key, but the ToolEntry
    # did not DECLARE ``catalog`` — so a real, working call read as an entry
    # "mixing parameter names with prose". The converse-ratchet sweep declares
    # it (with the other 33 real-but-undeclared parameters), every key of that
    # example is now a real parameter, and the row drains. Lowered in the SAME
    # commit as the drain.
    "mixed_param_and_prose": 14,
    "missing_required": 6,
    # rc395 (`#T1000`): 11 -> 10. The removed sedenion_zero_divisor_witness was a
    # zero-parameter op carrying a numbered {"1".."4"} example input; its removal
    # drains one row from this bucket, so the ceiling is lowered in the same commit.
    "zero_param_with_keys": 10,
    "all_prose_labels": 70,
    "numeric_call_index": 87,
}

#: The literal a zero-parameter op writes instead of leaving ``input`` out.
_NO_ARGS_LITERAL = "(no arguments)"


def _classified() -> Tuple[
    Dict[str, List[Tuple[str, List[str]]]],
    List[Tuple[str, List[str]]],
    List[Tuple[str, List[str], List[str]]],
    int,
    int,
]:
    """Classify every srmech tool's ``example["input"]`` against its own
    live ``inputSchema``.

    Returns ``(classes, mixed_numeric_named, io_keyset_disagree,
    n_input_bearing, n_clean)``. This function IS the generating code for
    the ceilings above — per ``[[feedback_computational_provenance_discipline]]``
    the numbers are re-derived on every run, never carried as prose.
    """
    schema = get_tool_schema()
    entries = [e for e in schema.tools if e.owner == "srmech"]
    assert len(entries) > 400, f"tool registry unexpectedly small: {len(entries)}"

    classes: Dict[str, List[Tuple[str, List[str]]]] = {
        name: [] for name in CEIL_EXAMPLE_INPUT_KEY_MISMATCH
    }
    mixed_numeric_named: List[Tuple[str, List[str]]] = []
    io_keyset_disagree: List[Tuple[str, List[str], List[str]]] = []
    n_input_bearing = 0
    n_clean = 0

    for entry in entries:
        example = entry.example
        if not isinstance(example, dict):
            continue
        given = example.get("input")
        if not isinstance(given, dict):
            continue
        n_input_bearing += 1

        mcp_def = tool_entry_to_mcp_def(entry)
        properties = set(mcp_def["inputSchema"]["properties"])
        required = set(mcp_def["inputSchema"]["required"])
        keys = list(given)
        extra = [k for k in keys if k not in properties]
        missing = sorted(required - set(keys))
        numeric = [k for k in keys if k.isdigit()]

        # STRICT ZERO 1 — a numeric call index and a parameter name cannot
        # both be what this dict means.
        if numeric and len(numeric) != len(keys):
            mixed_numeric_named.append((entry.name, keys))

        # STRICT ZERO 2 — the numeric-call-index convention, locked.
        produced = example.get("output")
        if isinstance(produced, dict) and set(produced) != set(keys):
            io_keyset_disagree.append(
                (entry.name, sorted(keys), sorted(produced))
            )

        if not extra and not missing:
            n_clean += 1
            continue

        hits = [k for k in keys if k in properties]
        if not properties:
            classes["zero_param_with_keys"].append((entry.name, keys))
        elif len(numeric) == len(keys):
            classes["numeric_call_index"].append((entry.name, keys))
        elif not hits:
            classes["all_prose_labels"].append((entry.name, keys))
        elif extra:
            classes["mixed_param_and_prose"].append((entry.name, keys))
        else:
            classes["missing_required"].append((entry.name, keys + missing))

    return (
        classes,
        mixed_numeric_named,
        io_keyset_disagree,
        n_input_bearing,
        n_clean,
    )


def test_example_input_never_mixes_call_index_with_parameter_names() -> None:
    """STRICT ZERO — an ``input`` dict is EITHER a kwargs map OR a numeric
    multi-call index, never a blend of the two.

    Measured 0 on the rc354 tree and held at 0 here. A blend is the one shape
    from which no consumer can recover the author's intent: ``{"1": ..., "u":
    ...}`` gives an MCP client no way to tell whether ``"u"`` is a parameter
    or a second call it forgot to number. The 87-row ``numeric_call_index``
    ceiling below tolerates the pure form precisely because this test forbids
    the ambiguous one.
    """
    _, offenders, _, _, _ = _classified()
    assert not offenders, (
        "example['input'] mixes numeric call indices with parameter names — "
        "pick one convention per entry: "
        f"{offenders}"
    )


def test_example_input_and_output_keysets_agree_when_both_are_dicts() -> None:
    """STRICT ZERO — when ``input`` and ``output`` are BOTH dicts they are the
    two halves of one indexed transcript, so their keysets must be equal.

    Measured on the rc354 tree: 95 such pairs, 95 agree, 0 disagree. This is
    what makes the ``numeric_call_index`` ceiling safe to hold rather than
    drain immediately — the convention is internally disciplined today, and
    this test is what stops it rotting into slop while it waits its turn. A
    call numbered in ``input`` with no answer in ``output`` (or the reverse)
    is a transcript that lost a line.
    """
    _, _, offenders, _, _ = _classified()
    assert not offenders, (
        "example input/output keysets disagree (each is 'name, input keys, "
        f"output keys'): {offenders}"
    )


def test_example_input_keys_are_real_parameters_down_only_ceiling() -> None:
    """DOWN-ONLY CEIL, per class — every key of ``example["input"]`` should be
    a real parameter name, and every required parameter should appear.

    189 of 386 input-bearing entries fail that today, so this cannot be a
    strict zero yet. It ratchets per class so a genuine kwargs regression
    (``mixed_param_and_prose`` / ``missing_required``) cannot hide behind
    someone deleting prose labels elsewhere.
    """
    classes, _, _, n_input_bearing, n_clean = _classified()
    assert n_input_bearing > 300, (
        f"only {n_input_bearing} entries carry a dict example['input'] — the "
        "classifier is probably reading the wrong field"
    )

    regressions: List[str] = []
    stale: List[str] = []
    for name, ceiling in sorted(CEIL_EXAMPLE_INPUT_KEY_MISMATCH.items()):
        found = len(classes[name])
        if found > ceiling:
            new = [row[0] for row in classes[name]][:8]
            regressions.append(
                f"{name}: {found} > CEIL {ceiling} (+{found - ceiling}); "
                f"offenders include {new}"
            )
        elif found < ceiling:
            stale.append(f"{name}: {found} < CEIL {ceiling} — LOWER the ceiling")

    assert not regressions, (
        "example['input'] key mismatch went UP — fix the example, never the "
        "ceiling. The contract is srmech/introspect/tool_schema.py:28: 'input' is a "
        "kwargs map whose keys are parameter names.\n  "
        + "\n  ".join(regressions)
    )
    assert not stale, (
        "a ceiling is above the true count — drain-then-lower must happen in "
        "ONE commit, or the slack is where the next false green lives.\n  "
        + "\n  ".join(stale)
    )
    assert n_clean + sum(len(v) for v in classes.values()) == n_input_bearing


def test_zero_parameter_ops_do_not_spell_no_arguments_as_a_key() -> None:
    """DOWN-ONLY (folded into ``zero_param_with_keys``) — the literal
    ``'(no arguments)'`` used as a dict KEY.

    Three ops write it (``carrier_ladder_descriptor``, ``carrier_schema``,
    ``responsion_schema``). It is called out separately because it is the one
    row in that class a reader is most likely to copy verbatim into a call:
    an empty ``input`` dict, or no ``input`` key at all, says the same thing
    and is valid under the schema. Named here so the fix is obvious when the
    class is drained; the count is not separately ceilinged.
    """
    classes, _, _, _, _ = _classified()
    literal = [
        name
        for name, keys in classes["zero_param_with_keys"]
        if _NO_ARGS_LITERAL in keys
    ]
    assert len(literal) <= 3, (
        f"more ops now spell {_NO_ARGS_LITERAL!r} as an input KEY: {literal} "
        "— use an empty dict or omit 'input'"
    )
