"""rc462 (`#T1179`) — the ``content_address_fields`` CLASS gate.

rc461's adversarial pass measured that srmech's Class-A payload digests were
**ungated by default**: a field could be replaced with a constant and the
suite stayed green. The instance holes were then closed by hand, one
``test_g14_*`` at a time, in whichever file happened to ship the op. Eleven
such gates exist, rc109 → rc461.

**That is a RATCHET — it covers what somebody remembered.** This file is the
DRAIN. Every content-address field is covered because it is DECLARED in
``tools/content_address.py``, and the declaration is checked STRICT-ZERO IN
BOTH DIRECTIONS against what the ops actually emit when driven from the
example-args ledger. An op that starts emitting a digest is red until it is
declared; a declaration whose field stopped being emitted is red too. Nobody
has to remember anything.

**Two instruments, and they are not redundant.**

* DRIVING finds fields the emitted prose does not mention. MEASURED: 29 ops,
  55 pairs — and ``reversal_law_census``, ``anti_automorphism_witnesses``,
  ``abelianization``, ``direct_sum_representation`` and
  ``tensor_product_representation`` emit digests their ``returns`` prose never
  names.
* The LEXICAL SCAN finds fields the prose PROMISES that the ledger cannot
  drive. MEASURED: ``triality_frame_action`` promises ``action_sha256`` /
  ``frame_sha256`` / ``procedure_sha256`` and is not drivable, so ONLY the
  scan sees it.

**The five kinds are five different CONTRACTS**, derived from the eleven
existing gates rather than invented — and reading all five as "stable and
distinguishing" is what made three of them vacuous. ``procedure`` fields must
be CONSTANT across inputs; a distinguishing assertion on one asserts the
opposite of its contract. See ``tools/content_address.py`` for the vocabulary
and the Phase-2 (ToolEntry) deferral with its measured ripple.

MEASURED at rc462, all on the numpy-absent cell:

===========================================  =====
declared ops                                    29
declared (op, field) pairs                      55
  answer / operand / procedure / echo / pinned  36 / 6 / 9 / 2 / 2
emitted-but-undeclared                           0
declared-but-no-longer-emitted                   0
ops promising a digest in ``returns`` prose     39
  of those, undeclared (the drain's residual)   19
same-named cross-op pairs                       61
  echoing verbatim / correctly differing      15 / 46
===========================================  =====

That last row is the executable argument for DECLARING rather than inferring
by name-match: ``cayley_sha256`` is verbatim-shared by four ops handed the
same table, while ``matrices_sha256`` correctly differs across all three ops
that emit it, because it addresses the NEW matrices.

⚠️ **EXPECTED, AND IT IS THE DRAIN WORKING, NOT A BUG.** ``emitted_over_drivable``
reads ``tests/example_args_ledger.ndjson`` live. rc462's own ledger regen adds
this rc's new ζ-dialect ops (``induced_representation``, ``zeta_conjugate``,
and the widened ``character_of`` / ``decompose_representation`` /
``isotypic_projector``) to the drivable set — up to eight of the nineteen
lexical residuals below. When that lands, ``test_no_drivable_op_emits_an_
undeclared_content_address`` goes RED until each new pair is declared, and
``CEIL_UNDECLARED_LEXICAL`` must be LOWERED in the same commit. That is
exactly the property this file exists for: a new op is covered by DECLARING
it, not by remembering to hand-write a ``test_g14``. Resolve it by adding
``Decl``s, never by widening a skip.

No numpy. No ``hashlib``. No ``abs()`` — all three checked by AST walk, not
substring, because a substring scan cannot tell a ban from its own statement.
"""

import ast
import contextlib
import copy
import inspect
import itertools
import pathlib
import sys

import pytest

_TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import content_address as ca  # noqa: E402
from srmech.amsc.format import sha256_bytes  # noqa: E402

# ── FLOORS. A strict-zero sweep over an EMPTY set passes; these stop that.
MIN_DECLARED_OPS = 29
MIN_DECLARED_PAIRS = 55

#: DOWN-ONLY CEILING on the residual the drain has not reached: ops whose
#: emitted ``returns`` prose promises a content address but which the
#: example-args ledger cannot drive, so the strict-zero clause above cannot
#: see them. Same shape as `tests/test_ref_notation_emitted_rc348.py` — strict
#: zero on the decidable class, a draining ceiling on the rest. It may only
#: go DOWN. MEASURED 19 at rc462.
CEIL_UNDECLARED_LEXICAL = 19


# ══════════════════════════════════════════════════════════════════════════
# 1. THE VOCABULARY IS EXECUTED, NOT ASPIRED TO.
# ══════════════════════════════════════════════════════════════════════════


def test_every_kind_is_executed_by_a_named_function():
    """The clause that stops this becoming a second aspirational taxonomy.

    The precedent gate in this tree prints "N of M strings are of an
    EXECUTABLE kind — NONE is executed yet". A vocabulary with no executor is
    a label, not an instrument.
    """
    assert set(ca.EXECUTED_BY) == set(ca.KINDS), (
        set(ca.EXECUTED_BY) ^ set(ca.KINDS))
    for kind, fn in ca.EXECUTED_BY.items():
        assert callable(fn), kind
        assert fn.__name__ == f"execute_{kind}", (kind, fn.__name__)
        # and each is a real module-level function, not a lambda or a partial
        assert getattr(ca, fn.__name__, None) is fn, kind


def test_every_declared_kind_is_one_of_the_five_and_all_five_are_used():
    used = {d.kind for d in ca.DECLARATIONS.values()}
    assert used <= set(ca.KINDS), used - set(ca.KINDS)
    assert used == set(ca.KINDS), (
        f"kinds declared nowhere: {set(ca.KINDS) - used}. An unused kind is "
        f"an untested executor.")


def test_the_floors_hold_so_a_strict_zero_sweep_cannot_be_vacuous():
    assert len(ca.declared_ops()) >= MIN_DECLARED_OPS, len(ca.declared_ops())
    assert len(ca.DECLARATIONS) >= MIN_DECLARED_PAIRS, len(ca.DECLARATIONS)


# ══════════════════════════════════════════════════════════════════════════
# 2. THE DRAIN — strict zero, BOTH directions.
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def emitted():
    return ca.emitted_over_drivable()


def test_no_drivable_op_emits_an_undeclared_content_address(emitted):
    undeclared = sorted(emitted - ca.declared_paths())
    assert undeclared == [], (
        "these (op, field) pairs emit a content address with no declaration "
        "in tools/content_address.py:\n  "
        + "\n  ".join(f"{o} -> {p}" for o, p in undeclared)
        + "\n\nAdd a Decl naming the KIND. This is the drain: a field is "
          "covered by declaring it, not by remembering to write a test_g14.")


def test_no_declaration_is_dead(emitted):
    dead = sorted(ca.declared_paths() - emitted)
    assert dead == [], (
        "declared but no longer emitted by the driven op:\n  "
        + "\n  ".join(f"{o} -> {p}" for o, p in dead)
        + "\n\nA declaration that cannot be exercised is a claim nobody "
          "checks. Remove it or restore the field.")


def test_the_drain_is_strict_zero_in_both_directions_at_once(emitted):
    assert emitted == ca.declared_paths()


# ══════════════════════════════════════════════════════════════════════════
# 3. EVERY DECLARATION IS EXECUTED BY ITS KIND'S FUNCTION.
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def verdicts():
    return ca.execute_all()


def test_every_declared_field_passes_its_own_contract(verdicts):
    failures = [detail for _key, ok, detail in verdicts if not ok]
    assert failures == [], "\n".join(failures)
    assert len(verdicts) == len(ca.DECLARATIONS)


def test_procedure_verdicts_are_not_vacuous(verdicts):
    """A ``procedure`` field held constant proves nothing unless the ANSWER
    moved under the same perturbation. Asserted directly on the measurement,
    not inferred from the pass."""
    proc = [(op, path) for (op, path), d in ca.DECLARATIONS.items()
            if d.kind == "procedure"]
    assert len(proc) >= 9, len(proc)
    moved = 0
    for op, path in proc:
        m = ca._measure(op, path)
        assert not m["field_moved"], (op, path)
        assert m["answer_moved"], (
            f"{op}.{path}: the procedure digest held constant, but so did the "
            f"answer — nothing was tested")
        moved += 1
    assert moved == len(proc)


def test_the_empty_ok_member_is_declared_with_its_reason():
    """``sha256_bytes(b"")`` is a LIVE emitted value here, so "stable and
    distinguishing" passes on it vacuously. It is declared rather than
    silently satisfying a gate it cannot exercise."""
    empties = [(k, d) for k, d in ca.DECLARATIONS.items() if d.empty_ok]
    assert len(empties) == 1, empties
    (op, path), decl = empties[0]
    assert "EMPTY_OK" in decl.why and len(decl.why) > 80, decl.why
    value = ca.digest_map(ca.call(op, ca.ledger_args(op))).get(path)
    assert value == sha256_bytes(b""), (op, path, value)
    # and no OTHER declared field is silently the empty digest
    for (o, p) in ca.DECLARATIONS:
        if (o, p) == (op, path):
            continue
        v = ca.digest_map(ca.call(o, ca.ledger_args(o))).get(p)
        assert v != sha256_bytes(b""), (
            f"{o}.{p} is the empty digest and is not declared EMPTY_OK")


# ══════════════════════════════════════════════════════════════════════════
# 4. THE CLASSIFIER, unit-tested on synthetic measurements.
# ══════════════════════════════════════════════════════════════════════════


def test_the_classifier_itself_distinguishes():
    """A classifier that always answers one verdict cannot ship."""
    cases = {
        (False, False, False): "unstable",
        (False, True, True): "unstable",
        (True, True, True): "distinguishing",
        (True, True, False): "distinguishing",
        (True, False, True): "constant_under_a_moved_answer",
        (True, False, False): "vacuous",
    }
    got = {k: ca.classify(*k) for k in cases}
    assert got == cases, got
    assert len(set(got.values())) == 4, set(got.values())


# ══════════════════════════════════════════════════════════════════════════
# 5. THE PLANTED-DEFECT MATRIX. Every executor must have an arm that REDS it.
# ══════════════════════════════════════════════════════════════════════════


@contextlib.contextmanager
def planted(mutate):
    """Wrap every op resolution so its payload is mutated before the gate
    sees it. Patches ``example_args.resolve`` rather than adding a hook to
    ``content_address``, so the production module carries no test seam."""
    orig = ca._ea.resolve
    saved = dict(ca._CACHE)

    def fake(op_name):
        got = orig(op_name)
        if got is None:
            return None
        mod, name, fn = got

        def wrapped(**kwargs):
            return mutate(op_name, copy.deepcopy(fn(**kwargs)))

        return (mod, name, wrapped)

    ca._ea.resolve = fake
    ca._CACHE.clear()
    try:
        yield
    finally:
        ca._ea.resolve = orig
        ca._CACHE.clear()
        ca._CACHE.update(saved)


def _set(payload, path, value):
    parts = path.split(".")
    node = payload
    for step in parts[:-1]:
        node = node[step]
    node[parts[-1]] = value
    return payload


_CONST = "0" * 64
_TARGET_ANSWER = ("srmech.math.groups.character_table", "table_sha256")
_TARGET_OPERAND = ("srmech.math.groups.character_table", "cayley_sha256")
_TARGET_PROC = ("srmech.math.weight_lattice.alcove_fold", "procedure_sha256")
_TARGET_ECHO = ("srmech.physics.qm.so8.g2_membership", "frame_sha256")
_TARGET_PIN = ("srmech.physics.qm.so8.an_embedding",
               "attestation.attestation.response_sha256")


def _run(target):
    op, path = target
    decl = ca.DECLARATIONS[target]
    return ca.EXECUTED_BY[decl.kind](op, path, decl)


def test_arm_1_a_constant_answer_digest_reds():
    op, path = _TARGET_ANSWER
    with planted(lambda name, out: _set(out, path, _CONST)
                 if name == op else out):
        ok, detail = _run(_TARGET_ANSWER)
    assert not ok, detail
    assert "must MOVE" in detail, detail


def test_arm_2_an_unstable_digest_reds():
    counter = itertools.count()
    op, path = _TARGET_ANSWER

    def mutate(name, out):
        if name == op:
            _set(out, path, f"{next(counter):064x}")
        return out

    with planted(mutate):
        ok, detail = _run(_TARGET_ANSWER)
    assert not ok, detail
    assert "STABLE" in detail, detail


def test_arm_3_a_frozen_operand_digest_reds():
    op, path = _TARGET_OPERAND
    with planted(lambda name, out: _set(out, path, _CONST)
                 if name == op else out):
        ok, detail = _run(_TARGET_OPERAND)
    assert not ok, detail
    assert "OPERAND" in detail, detail


def test_arm_4_a_procedure_digest_that_moves_with_the_input_reds():
    op, path = _TARGET_PROC
    seen = {}

    def mutate(name, out):
        if name == op:
            key = len(seen)
            seen.setdefault(str(out.get("weight")), key)
            _set(out, path, f"{seen[str(out.get('weight'))]:064x}")
        return out

    with planted(mutate):
        ok, detail = _run(_TARGET_PROC)
    assert not ok, detail
    assert "must NOT move" in detail or "VACUOUS" in detail, detail


def test_arm_5_a_wrong_echo_source_reds():
    op, path = _TARGET_ECHO
    with planted(lambda name, out: _set(out, path, _CONST)
                 if name == op else out):
        ok, detail = _run(_TARGET_ECHO)
    assert not ok, detail
    assert "must equal" in detail, detail


def test_arm_6_a_moved_pin_reds():
    op, path = _TARGET_PIN
    with planted(lambda name, out: _set(out, path, _CONST)
                 if name == op else out):
        ok, detail = _run(_TARGET_PIN)
    assert not ok, detail
    assert "moved" in detail, detail


def test_arm_7_a_forced_empty_digest_reds():
    """Why EMPTY_OK must be DECLARED and never inferred: the empty digest is
    a perfectly stable 64-hex string, so a stability-only gate accepts it."""
    op, path = _TARGET_ANSWER
    empty = sha256_bytes(b"")
    with planted(lambda name, out: _set(out, path, empty)
                 if name == op else out):
        ok, detail = _run(_TARGET_ANSWER)
    assert not ok, detail
    assert len(empty) == 64


def test_the_planted_matrix_covers_every_executor():
    """Mechanical: each of the five kinds has at least one arm above."""
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    arms = [n.name for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_arm_")]
    assert len(arms) >= 7, arms
    targets = {_TARGET_ANSWER: "answer", _TARGET_OPERAND: "operand",
               _TARGET_PROC: "procedure", _TARGET_ECHO: "echo",
               _TARGET_PIN: "pinned"}
    for key, kind in targets.items():
        assert ca.DECLARATIONS[key].kind == kind, key
    assert set(targets.values()) == set(ca.KINDS)


def test_the_planting_harness_is_not_a_no_op():
    """CONTROL. Without this, every arm above could be red for the wrong
    reason — or the harness could be doing nothing and the arms passing
    because the executor is broken."""
    op, path = _TARGET_ANSWER
    before = ca.digest_map(ca.call(op, ca.ledger_args(op)))[path]
    with planted(lambda name, out: _set(out, path, _CONST)
                 if name == op else out):
        during = ca.digest_map(ca.call(op, ca.ledger_args(op)))[path]
    after = ca.digest_map(ca.call(op, ca.ledger_args(op)))[path]
    assert during == _CONST
    assert before == after != _CONST
    ok, _detail = _run(_TARGET_ANSWER)
    assert ok, "the harness leaked — the real payload is still mutated"


# ══════════════════════════════════════════════════════════════════════════
# 6. THE LEXICAL SCAN — the second instrument, and its draining ceiling.
# ══════════════════════════════════════════════════════════════════════════


def test_the_lexical_scan_finds_ops_the_drain_cannot_reach():
    mentions = ca.lexical_mentions()
    assert len(mentions) >= 39, len(mentions)
    undeclared = ca.undeclared_lexical()
    assert len(undeclared) <= CEIL_UNDECLARED_LEXICAL, (
        f"{len(undeclared)} ops promise a content address in emitted prose "
        f"with no declaration, above the ceiling of "
        f"{CEIL_UNDECLARED_LEXICAL}:\n  " + "\n  ".join(undeclared))
    # DOWN-ONLY: if it shrank, lower the ceiling in the same commit.
    assert len(undeclared) == CEIL_UNDECLARED_LEXICAL, (
        f"the residual is now {len(undeclared)}; lower "
        f"CEIL_UNDECLARED_LEXICAL to match. It may only go DOWN.")


def test_the_scan_names_the_op_the_drive_structurally_cannot_see():
    """``triality_frame_action`` emits ``frame_sha256`` / ``procedure_sha256``
    / ``action_sha256`` and has no drivable ledger row, so the strict-zero
    drain is blind to it and only the scan reports it. That asymmetry is why
    both instruments ship."""
    undeclared = set(ca.undeclared_lexical())
    assert "srmech.physics.qm.triality.triality_frame_action" in undeclared
    fields = ca.lexical_mentions()[
        "srmech.physics.qm.triality.triality_frame_action"]
    assert "procedure_sha256" in fields and "frame_sha256" in fields, fields
    assert ("srmech.physics.qm.triality.triality_frame_action"
            not in {op for op, _p in ca.emitted_over_drivable()})


def test_the_attestation_exemption_is_narrow_and_named():
    """The whole-ToolEntry scan finds 115 ops and is dominated by every
    attested op describing the MPR attestation SCHEMA. Scoping to ``returns``
    and naming three schema fields takes it to 39 real ones. The exemption is
    a named frozenset, never a pattern."""
    assert ca.ATTESTATION_FIELDS == frozenset(
        {"response_sha256", "upstream_response_sha256", "srmech_sha256"})
    assert len(ca.ATTESTATION_FIELDS) == 3
    # and it is not so broad that it hides a real payload field
    for _op, fields in ca.lexical_mentions().items():
        assert not (set(fields) & ca.ATTESTATION_FIELDS)


# ══════════════════════════════════════════════════════════════════════════
# 7. WHY DECLARING BEATS NAME-MATCHING — measured, not argued.
# ══════════════════════════════════════════════════════════════════════════


def test_a_shared_field_name_does_not_mean_a_shared_address():
    """61 same-named cross-op pairs: 15 echo verbatim, 46 correctly differ.

    ``cayley_sha256`` is verbatim-shared by the four ops handed the same
    table; ``matrices_sha256`` differs across all three ops that emit it,
    because it addresses the NEW matrices. A gate that inferred "echo" from a
    name match would be wrong 46 times out of 61.
    """
    values = {}
    for op, path in ca.DECLARATIONS:
        values[(op, path)] = ca.digest_map(
            ca.call(op, ca.ledger_args(op))).get(path)
    by_name = {}
    for (op, path), digest in values.items():
        by_name.setdefault(path.rsplit(".", 1)[-1], []).append((op, digest))
    same = differ = 0
    for _name, items in by_name.items():
        for a, b in itertools.combinations(sorted(items), 2):
            if a[1] == b[1]:
                same += 1
            else:
                differ += 1
    assert same + differ == 61, (same, differ)
    assert same == 15, same
    assert differ == 46, differ
    assert same > 0 and differ > 0, "the split must have BOTH halves"


# ══════════════════════════════════════════════════════════════════════════
# 8. DISCIPLINE, by AST walk — never by substring.
# ══════════════════════════════════════════════════════════════════════════


def _banned_calls(path: pathlib.Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "abs":
            bad.append(("abs", node.lineno))
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in ("numpy", "hashlib"):
                    bad.append((alias.name, node.lineno))
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in ("numpy", "hashlib"):
                bad.append((node.module, node.lineno))
    return bad


def test_neither_this_gate_nor_its_module_imports_numpy_or_hashlib_or_calls_abs():
    for path in (pathlib.Path(ca.__file__), pathlib.Path(__file__)):
        assert _banned_calls(path) == [], (path.name, _banned_calls(path))


def test_the_ban_check_can_fire():
    """CONTROL — a scanner that never fires is not a check."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp) / "planted.py"
        p.write_text("import hashlib\nimport numpy\nx = abs(-1)\n",
                     encoding="utf-8")
        found = _banned_calls(p)
    assert sorted(n for n, _ in found) == ["abs", "hashlib", "numpy"], found


def test_the_perturbation_corpus_is_DERIVED_not_inlined():
    """A literal Cayley table here would be a COPY of the object under test.

    Checked structurally: ``corpus()`` calls the shipped constructors and
    contains no nested list literal.
    """
    tree = ast.parse(inspect.getsource(ca.corpus))
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert {"cyclic_group", "dihedral_group", "unit_loop",
            "permutation_representation"} <= called, called
    nested = [n for n in ast.walk(tree) if isinstance(n, ast.List)
              and any(isinstance(e, ast.List) for e in n.elts)]
    assert nested == [], "a nested list literal in the corpus is a copy"
    built = ca.corpus()
    assert len(built["C4"]) == 4 and len(built["Q8"]) == 8
    assert built["C4_REGULAR"]["kind"] == "permutation"


def test_every_declaration_carries_a_reason_where_the_kind_is_not_the_default():
    """``answer`` is the default reading; every other kind must say why."""
    for (op, path), decl in ca.DECLARATIONS.items():
        if decl.kind != "answer":
            assert len(decl.why) >= 30, (op, path, decl.kind, decl.why)
    # and the constructor refuses a malformed declaration
    with pytest.raises(ValueError):
        ca.Decl("not_a_kind", "x")
    with pytest.raises(ValueError):
        ca.Decl("echo", "x")                     # echo without a source
    with pytest.raises(ValueError):
        ca.Decl("answer", "x", echo_source="y")  # a source on a non-echo
    with pytest.raises(ValueError):
        ca.Decl("pinned", "x")                   # pinned without a literal
