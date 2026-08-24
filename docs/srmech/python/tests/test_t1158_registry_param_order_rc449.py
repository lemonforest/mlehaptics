"""v0.9.0rc449 (`#T1158`, gh #1653 residual) — the DRIFT GATES under rc449's
C key-set validators.

rc449 teaches both C chain interpreters to REFUSE a step / stage that declares an
op-argument key the op does not have. The legal key set is not a new table: it is
read from the compiled tool registry (``srmech_tool_registry_find`` over
``c/src/srmech_tool_registry.c``), because that registry is ALREADY pinned
set-equal to the live Python signatures from both directions —
``tests/test_mcp.py::test_schema_signature_alignment_no_drift`` (rc13: declared
subset-of bindable) and ``tests/test_declared_param_completeness_rc408.py``
(rc408: declared superset-of live). Two-sided pinning is what makes it a SOURCE OF
TRUTH rather than a third copy, and ``#T1146`` existed precisely because two
independent notions of "accepted keys" had drifted apart.

Reading the registry buys two NEW obligations, and this module is both of them.

──────────────────────────────────────────────────────────────────────────────
G4-ORDER — the registry's parameter ORDER, which nothing pinned before.

The DSL surface's legal set is ``params[1..]``: ``params[0]`` is the DATA CARRIER,
threaded into the leaf as the chain value, and refusing it as a stage kwarg is
what closes the measured 7/7 residual (``.then('magnitude', x=5)`` built a C stage
the pure path rejects with "got multiple values for argument 'x'"). That rule is
an assumption about ORDER, and the rc13 / rc408 gates pin SETS only.

WHAT MEASURED IT: 8 of the 609 set-equal registry entries were
same-set-but-REORDERED at rc448 head. Seven drifted only among KEYWORD-ONLY
parameters, where order carries no binding meaning. The eighth did not:

    srmech.math.hdc.polar_random
        declared:  (D, seed, rng)
        live:      (D, rng=None, seed=None)      # all POSITIONAL_OR_KEYWORD

A consumer who trusts the published contract and calls ``polar_random(8192, 42)``
binds ``42`` to ``rng``, not ``seed``, and gets
``AttributeError: 'int' object has no attribute 'randrange'`` — an error naming
neither parameter it wrote. Loud, but only by luck: any object with a
``randrange`` would have been silently accepted as the wrong argument. rc408 added
``rng`` to that declaration and appended it instead of placing it where the
signature has it, so the drift arrived with the fix for a different gap.

──────────────────────────────────────────────────────────────────────────────
G4-A — the C-side op-name indexes, which are NEW ARTIFACTS.

Neither runner can look an op up directly: a stage spells ``magnitude`` while the
registry is keyed ``srmech.cascade.magnitude``, and a compose step spells ``gcd``
while the registry is keyed ``srmech.math.cyclic.gcd``. So each runner carries a
static NAME-to-NAME index (``DSL_LEAF_REG`` / ``CR_OP_REG``). Those indexes carry
no key names — the key names still come from the registry — but they are new
artifacts, and a new artifact with no gate is how ``#T1146`` happened.

⚠️ THE FAILURE THIS PREVENTS IS INVISIBLE TO EVERY OTHER TEST. A typo in one index
entry makes ``srmech_tool_registry_find`` return NULL for an op the dispatch table
really runs. rc449 returns ``SRMECH_ERR_INTERNAL`` there rather than falling
through to "accept" precisely so the failure is loud — but nothing except this
gate would notice the typo itself, and every op except that one would stay green.
MEASURED (rc449 sabotage arm 3): one character into the ``gcd`` entry turned 7 of
the 32 bare-C rows red, acceptance rows included.

Both indexes are parsed out of the C SOURCE TEXT rather than reimplemented here —
the ``tests/test_combinator_kernel_closure.py`` pattern, where the gate READS the
compiled-in table so it cannot drift from it by construction.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import Dict, List, Tuple

from srmech._resolve import resolve_dotted_callable
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

_HERE = Path(__file__).resolve()
_C_SRC = _HERE.parents[2] / "c" / "src"
_DSL_C = _C_SRC / "srmech_dsl_chain_run.c"
_COMPOSE_C = _C_SRC / "srmech_compose_run.c"

#: the parameter kinds a caller can actually name — mirrors the rc408 gate
_KINDS = (
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.KEYWORD_ONLY,
    inspect.Parameter.VAR_POSITIONAL,
)

#: one `{ "bare", 12u, "srmech.dotted.name" }` row of the DSL index (3 members)
_INDEX_ROW = re.compile(
    r'\{\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*,\s*(\d+)u\s*,\s*"([A-Za-z0-9_.]+)"\s*\}')

#: one `{ "bare", 12u, "srmech.dotted.name", dom, sub, bin }` row of ``CR_OP_REG``.
#:
#: ⚠️ SIX MEMBERS SINCE the rc452 A1 (Rule-9-clean) dispatch. The compose index
#: stopped being a name-to-NAME table within rc452 because ``cr_dispatch`` was
#: measured at 57 of JPL Rule 4's 60 lines and the 32 op spellings the eight
#: blocked chains need could not be added as an if-chain AT ALL. The first cut
#: gave rows two FUNCTION-POINTER columns — which JPL Rule 9 bans outright and
#: the mechanical audit never saw (it tests Rules 1/3/4/5/8 only) — so the
#: rows now carry three small-int ENUM columns instead: ``dom`` (which
#: ``cr_exec_<domain>()`` runs the op), ``sub`` (the case label inside that
#: exec) and ``bin`` (which fold body, or ``CR_BIN_NONE``). Each reshape made
#: the previous regex match ZERO rows and this file's own ``assert rows`` fire
#: loudly — the parse refusing to observe rather than silently reporting an
#: empty table. It keeps its own regex rather than being generalised, so the
#: DSL surface (still 3 members) cannot start accepting a shape it does not
#: have. ``sub`` may be a bare ``0u`` (the CR_DOM_NONE fold-only row has no
#: domain enum), so its group admits digits where ``dom``/``bin`` require an
#: identifier.
_COMPOSE_ROW = re.compile(
    r'\{\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*,\s*(\d+)u\s*,\s*"([A-Za-z0-9_.]+)"\s*,'
    r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z0-9_]+)\s*,'
    r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}')

#: `cr_op_is(op, opl, "gcd", 3u)` — kept to prove ``cr_dispatch`` has NONE.
_CR_OP_IS = re.compile(r'cr_op_is\(op,\s*opl,\s*"([A-Za-z0-9_]+)",\s*(\d+)u\)')

#: The ``CR_OP_REG`` declaration marker. ONE literal, deliberately: the DECLARED
#: SIZE is itself a gate (a size that outran its rows would otherwise pass), so
#: growing the table must be an explicit edit here. It is not derived from the
#: file, because deriving it would make the gate agree with whatever it found.
_COMPOSE_MARKER = "} CR_OP_REG[51] = {"

#: `opl == 9u && memcmp(op, "magnitude", 9u)` — the DSL dispatch arms
_DSL_ARM = re.compile(
    r'opl\s*==\s*(\d+)u\s*&&\s*memcmp\(op,\s*"([A-Za-z0-9_]+)",\s*(\d+)u\)')


def _live_params(name: str) -> List[str] | None:
    """The callable's real parameter names, in signature order. None = unreadable."""
    try:
        fn = resolve_dotted_callable(name)
    except Exception:
        return None
    if not callable(fn):
        return None
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        return None
    live = [p.name for p in sig.parameters.values()
            if p.name != "self" and p.kind in _KINDS]
    return live or None


def _declared(entry) -> List[str]:
    return [p.name.lstrip("*") for p in (entry.parameters or ())]


def _order_drift() -> List[Tuple[str, List[str], List[str]]]:
    """Entries whose declared params are the same SET but a different ORDER.

    Set-drift is deliberately skipped: it is the rc13 / rc408 gates' finding, and
    reporting it here too would make one defect fail three gates with three
    different explanations.
    """
    warmup_all()
    drift = []
    for entry in get_tool_schema().tools:
        live = _live_params(entry.name)
        if live is None:
            continue
        decl = _declared(entry)
        if set(decl) != set(live):
            continue
        if decl != live:
            drift.append((entry.name, decl, live))
    return drift


def test_declared_param_order_matches_the_live_signature() -> None:
    """STRICT ZERO. The published order is the real order."""
    drift = _order_drift()
    assert not drift, (
        "ToolEntry parameters are declared in a different ORDER than the live "
        "signature:\n"
        + "\n".join(f"  {n}\n      declared {d}\n      live     {l}"
                    for n, d, l in drift)
        + "\n\nOrder is load-bearing twice over: params[0] is the DATA CARRIER "
          "that rc449's DSL validator excludes from the legal stage-kwarg set, "
          "and any drift among POSITIONALLY BINDABLE parameters silently "
          "rebinds a caller's arguments.")


def test_params_zero_is_the_first_live_parameter() -> None:
    """The premise rc449's ``params[1..]`` rule rests on, stated by itself.

    Kept separate from the full-order assertion on purpose. If a future entry
    ever needs a genuine order exception, this is the part that may NOT be
    relaxed: the C validator would start refusing a real operand, or accepting
    the data-carrier name, depending on which way the head moved.
    """
    warmup_all()
    bad = []
    for entry in get_tool_schema().tools:
        live = _live_params(entry.name)
        if live is None:
            continue
        decl = _declared(entry)
        if not decl or set(decl) != set(live):
            continue
        if decl[0] != live[0]:
            bad.append((entry.name, decl[0], live[0]))
    assert not bad, (
        "params[0] is not the first live parameter for:\n"
        + "\n".join(f"  {n}: declared {d!r}, live {l!r}" for n, d, l in bad))


def _parse_compose_table(marker: str) -> Dict[str, Tuple[int, str, str, str, str]]:
    """Parse ``CR_OP_REG`` into {bare: (declared_len, full, dom, sub, bin)}.

    The compose table carries the A1 enum columns (``dom``/``sub``/``bin``) as
    of rc452, so it gets its own parse. ``dom == CR_DOM_NONE`` with
    ``bin == CR_BIN_NONE`` is a DEAD ROW and is asserted against below, since
    such a row would be key-set-validated and then never runnable by any path.
    """
    text = _COMPOSE_C.read_text(encoding="utf-8")
    assert marker in text, (
        f"{_COMPOSE_C.name} no longer contains the index marker {marker!r}. If "
        f"the array's DECLARED SIZE changed, update this marker in the same "
        f"commit — the marker IS the array-size gate.")
    i = text.index(marker)
    j = text.index("};", i)
    rows = _COMPOSE_ROW.findall(text[i:j])
    assert rows, (
        f"no CR_OP_REG rows parsed out of {_COMPOSE_C.name} at {marker!r}. An "
        f"empty parse is not an empty table — re-point _COMPOSE_ROW at the row "
        f"shape the file actually has; do not delete the assertion.")
    out: Dict[str, Tuple[int, str, str, str, str]] = {}
    for bare, ln, full, dom, sub, bn in rows:
        out[bare] = (int(ln), full, dom, sub, bn)
    assert len(out) == len(rows), "CR_OP_REG has a DUPLICATE bare spelling"
    return out


def _parse_index(path: Path, marker: str) -> Dict[str, Tuple[int, str]]:
    """Parse a C name-to-name index into {bare: (declared_len, full_name)}."""
    text = path.read_text(encoding="utf-8")
    # rc451 (`#T1164`): the marker lookup gets its OWN assert. It used to be a
    # bare ``text.index(marker)``, which raises ``ValueError: substring not
    # found`` — no file, no marker, no instruction — BEFORE the friendly
    # message below can evaluate. That is exactly what a builder growing the
    # table hits (measured this rc, on the 20 -> 24 bump), and the message
    # written for the case was unreachable.
    assert marker in text, (
        f"{path.name} no longer contains the index marker {marker!r}. If the "
        f"array's DECLARED SIZE changed, update this marker in the same commit "
        f"— the marker IS the array-size gate. (The loop bounds inside "
        f"cr_args_keyset_ok are derived by sizeof since rc451 and need no "
        f"edit; before that they were hand-written literals nothing read, so a "
        f"stale bound silently disabled key-set validation for the tail "
        f"entries.)")
    i = text.index(marker)
    j = text.index("};", i)
    rows = _INDEX_ROW.findall(text[i:j])
    assert rows, f"no index rows parsed out of {path.name} at {marker!r}"
    return {bare: (int(ln), full) for bare, ln, full in rows}


def _check_index(index: Dict[str, Tuple[int, str]], surface: str,
                 legal_from: int) -> None:
    """Every index entry resolves, has a truthful length, and matches its signature.

    ``legal_from`` is the first param index the C validator treats as a legal
    key — 1 on the DSL surface (params[0] is the threaded carrier), 0 on the
    compose surface (every operand arrives by name inside ``args``).
    """
    warmup_all()
    by_name = {t.name: t for t in get_tool_schema().tools}
    for bare, (ln, full) in sorted(index.items()):
        assert len(bare) == ln, (
            f"{surface}: index row {bare!r} declares length {ln}, but the "
            f"string is {len(bare)} bytes. The C matcher compares this length "
            f"BEFORE memcmp, so a wrong one silently disables the row.")
        assert full in by_name, (
            f"{surface}: index row {bare!r} points at {full!r}, which is not a "
            f"registered ToolEntry. srmech_tool_registry_find returns NULL for "
            f"it, so rc449 returns SRMECH_ERR_INTERNAL on every {bare!r} step — "
            f"this is the typo the gate exists to catch.")
        live = _live_params(full)
        assert live is not None, f"{surface}: {full} has no readable signature"
        declared = _declared(by_name[full])
        assert declared == live, (
            f"{surface}: {full} declares {declared} but its signature is "
            f"{live} — the key set the C validator reads is not the one the "
            f"callable accepts.")
        assert len(declared) > legal_from - 1, (
            f"{surface}: {full} declares {len(declared)} params; the validator "
            f"reads params[{legal_from}..] and would have an empty legal set.")


def test_dsl_leaf_index_resolves_and_matches_signatures() -> None:
    """G4-A, Surface B — ``DSL_LEAF_REG`` against the registry."""
    _check_index(_parse_index(_DSL_C, "} DSL_LEAF_REG[7] = {"), "DSL_LEAF_REG", 1)


def test_compose_op_index_resolves_and_matches_signatures() -> None:
    """G4-A, Surface A — ``CR_OP_REG`` against the registry."""
    table = _parse_compose_table(_COMPOSE_MARKER)
    _check_index({b: (ln, full) for b, (ln, full, _d, _s, _n) in table.items()},
                 "CR_OP_REG", 0)


def test_dsl_index_covers_exactly_the_dispatch_arms() -> None:
    """The index and the dispatch table name the SAME ops.

    An op in the dispatch table but not the index is UNVALIDATED — it keeps the
    rc448 silent-drop behaviour while every other op looks fixed. An op in the
    index but not the table is validated but never run, which means the index is
    describing a surface that no longer exists.
    """
    text = _DSL_C.read_text(encoding="utf-8")
    body = text[text.index("static srmech_status_t dsl_leaf_dispatch("):]
    body = body[:body.index("\n}\n")]
    arms = {name: int(a) for a, name, b in _DSL_ARM.findall(body)
            if a == b}
    index = _parse_index(_DSL_C, "} DSL_LEAF_REG[7] = {")
    assert set(arms) == set(index), (
        f"DSL_LEAF_REG and dsl_leaf_dispatch disagree.\n"
        f"  dispatch-only (UNVALIDATED, still silently dropping): "
        f"{sorted(set(arms) - set(index))}\n"
        f"  index-only (validated but never run): "
        f"{sorted(set(index) - set(arms))}")
    for name, ln in arms.items():
        assert index[name][0] == ln, (
            f"{name}: dispatch matches on length {ln}, index declares "
            f"{index[name][0]}")


def test_compose_dispatch_is_TABLE_ONLY_not_an_if_chain_beside_it() -> None:
    """THE ANTI-GAMING PIN for rc452's atom-table conversion.

    The cheap way to make the conversion "land" is to add the table BESIDE the
    existing if-chain and leave the chain doing the work — every signature gate
    goes green, the table is decorative, and the next 32 arms still cannot be
    added. So this asserts the shape directly: ``cr_dispatch`` contains ZERO
    ``cr_op_is`` calls of its own and reaches its op through ``CR_OP_REG``.

    ``cr_op_is`` legitimately survives in ``cr_op_row`` (the single matcher) —
    which is why the scan is scoped to ``cr_dispatch``'s body, not the file.
    """
    text = _COMPOSE_C.read_text(encoding="utf-8")
    marker = "static srmech_status_t cr_dispatch("
    assert marker in text, (
        "cr_dispatch is gone from srmech_compose_run.c — if the dispatch was "
        "renamed, re-point this gate in the same commit.")
    body = text[text.index(marker):]
    body = body[:body.index("\n}\n")]
    arms = _CR_OP_IS.findall(body)
    assert not arms, (
        f"cr_dispatch still matches ops with its own cr_op_is arms {arms!r}. "
        f"The atom table is then decorative and JPL Rule 4 still binds the "
        f"op count — which is the exact condition rc452 exists to remove.")
    assert "CR_OP_REG[" in body, (
        "cr_dispatch does not reference CR_OP_REG — it is not dispatching "
        "through the atom table at all.")
    assert "static srmech_status_t cr_dispatch_real(" not in text, (
        "cr_dispatch_real is back. It existed ONLY to absorb arms that would "
        "have broken Rule 4 in cr_dispatch; with a table there is nothing for "
        "it to absorb, and re-adding it means the if-chain has returned.")


def test_every_compose_table_row_is_REACHABLE_by_some_path() -> None:
    """No dead rows: each row runs as a plain op, as a fold body, or both.

    A row with ``dom == CR_DOM_NONE`` and ``bin == CR_BIN_NONE`` would be
    key-set-validated (so it LOOKS covered — ``cr_args_keyset_ok`` resolves it
    and enforces its params) while no execution path could ever call it. That
    is a validated surface with no implementation behind it, which is
    precisely the shape this file's own ``full in by_name`` assertion exists
    to refuse one level up.
    """
    table = _parse_compose_table(_COMPOSE_MARKER)
    dead = sorted(b for b, (_l, _f, dom, _s, bn) in table.items()
                  if dom == "CR_DOM_NONE" and bn == "CR_BIN_NONE")
    assert not dead, f"CR_OP_REG rows with neither a domain nor a fold bin: {dead}"


def _exec_case_labels(text: str, fn_name: str) -> set:
    """The ``case`` labels of one dispatch function's switch, parsed."""
    marker = f"static srmech_status_t {fn_name}("
    assert marker in text, (
        f"{fn_name} is gone from {_COMPOSE_C.name} — if the exec was renamed, "
        f"re-point this gate in the same commit.")
    body = text[text.index(marker):]
    body = body[:body.index("\n}\n")]
    labels = set(re.findall(r"case\s+([A-Za-z_][A-Za-z0-9_]*)\s*:", body))
    assert labels, f"{fn_name} has NO case labels — the parse stopped observing"
    return labels


def test_exec_case_labels_are_SET_EQUAL_to_the_tables_sub_column() -> None:
    """THE BIJECTION GATE for the A1 (Rule-9-clean) dispatch.

    The compiler already enforces one direction: an enum member with no
    ``case`` in a no-default switch is a -Wswitch error under -Werror (and
    C4062 under /w44062 /WX on MSVC). What the compiler CANNOT see is the
    table: a row whose ``sub`` names an enum member that a DIFFERENT row also
    names would compile clean and silently dispatch two spellings to one op.
    So the mapping is parsed end-to-end here: ``cr_dispatch``'s own arms say
    which exec serves which ``dom``, each exec's case labels are extracted,
    and the table's per-domain ``sub`` column must be SET-EQUAL to them.

    ⚠️ SET-equality is the right strength, not row-count equality:
    ``mod_mul`` and ``mod_mul_wide`` are deliberately DISTINCT case labels
    dispatching the same driver arm, so the row-to-case mapping stays 1:1 and
    a shared label would be visible here as a set-size mismatch.
    """
    text = _COMPOSE_C.read_text(encoding="utf-8")
    table = _parse_compose_table(_COMPOSE_MARKER)

    # which exec serves which dom — parsed from cr_dispatch, not assumed
    body = text[text.index("static srmech_status_t cr_dispatch("):]
    body = body[:body.index("\n}\n")]
    dom_to_exec = dict(re.findall(
        r"case\s+(CR_DOM_[A-Z0-9_]+)\s*:\s*return\s+(cr_exec_[a-z0-9_]+)\(",
        body))
    assert dom_to_exec, (
        "cr_dispatch dispatches to NO cr_exec_* — the domain-switch parse has "
        "stopped observing")
    assert "CR_DOM_NONE" not in dom_to_exec, (
        "CR_DOM_NONE reaches an exec — the fold-body-only state must return "
        "NOT_IMPL from cr_dispatch itself")

    # every dom the table uses (bar NONE) is served by exactly one exec …
    table_doms = {dom for (_l, _f, dom, _s, _b) in table.values()}
    assert table_doms - {"CR_DOM_NONE"} == set(dom_to_exec), (
        f"table domains {sorted(table_doms - {'CR_DOM_NONE'})} != dispatched "
        f"domains {sorted(dom_to_exec)}")

    # … and that exec's case labels are set-equal to the domain's sub column.
    for dom, exec_fn in sorted(dom_to_exec.items()):
        subs = {s for (_l, _f, d, s, _b) in table.values() if d == dom}
        labels = _exec_case_labels(text, exec_fn)
        assert subs == labels, (
            f"{exec_fn} and the CR_OP_REG {dom} rows disagree.\n"
            f"  case-only (an arm no row reaches): {sorted(labels - subs)}\n"
            f"  row-only (an op with no arm — should be a compile error; if "
            f"you are reading this the build gate is off): {sorted(subs - labels)}")

    # the fold half rides the same table: cr_fold_body's labels == the bin
    # column's values plus its explicit CR_BIN_NONE decline arm.
    bins = {b for (_l, _f, _d, _s, b) in table.values()}
    fold_labels = _exec_case_labels(text, "cr_fold_body")
    assert fold_labels == bins | {"CR_BIN_NONE"}, (
        f"cr_fold_body case labels {sorted(fold_labels)} != table bin values "
        f"{sorted(bins | {'CR_BIN_NONE'})}")


def test_the_order_gate_would_have_fired_on_the_rc448_registry() -> None:
    """RETRO-CHECK. A gate that would not have caught the drift that motivated
    it is not the gate.

    The eight rc448-head drifts are reproduced verbatim and run through the same
    comparison the live gate uses. ``polar_random`` is asserted separately
    because it is the only one that drifted among POSITIONALLY BINDABLE
    parameters — the others are keyword-only, where order misstates the contract
    without changing what a call binds.
    """
    rc448_drift = {
        "srmech.biology.genome.chromosome": (
            ["leaves", "coupling", "label", "genes", "element_type", "kernel",
             "active_count", "centromere", "centromere_at"],
            ["leaves", "coupling", "label", "genes", "kernel", "active_count",
             "centromere", "centromere_at", "element_type"]),
        "srmech.biology.genome.mint": (
            ["kernels", "coupling", "chromosomes", "element_type", "progress"],
            ["kernels", "coupling", "chromosomes", "progress", "element_type"]),
        "srmech.biology.genome.genome": (
            ["kernels", "coupling", "element_type", "chromosomes", "progress"],
            ["kernels", "coupling", "chromosomes", "progress", "element_type"]),
        "srmech.biology.genome.genome_save": (
            ["strand", "path", "coupling", "labels", "element_type",
             "attestation"],
            ["strand", "path", "coupling", "labels", "attestation",
             "element_type"]),
        "srmech.biology.genome.mint_strand": (
            ["strand", "coupling", "orientation", "centromere_at", "repeats",
             "handle", "element_type", "progress"],
            ["strand", "coupling", "orientation", "centromere_at", "repeats",
             "handle", "progress", "element_type"]),
        "srmech.biology.genome.genome_from_graph": (
            ["n", "edges", "weights", "charges", "coupling", "path", "leaf_dim",
             "max_tome", "n_bins", "centromere_at", "attestation",
             "element_type", "progress"],
            ["n", "edges", "weights", "charges", "coupling", "path", "leaf_dim",
             "max_tome", "n_bins", "centromere_at", "progress", "attestation",
             "element_type"]),
        "srmech.math.hdc.polar_random": (
            ["D", "seed", "rng"], ["D", "rng", "seed"]),
        "srmech.cascade.parallel_sector_dispatch": (
            ["body", "x", "n_sectors", "combine", "verify"],
            ["body", "x", "n_sectors", "verify", "combine"]),
    }
    assert len(rc448_drift) == 8
    for name, (decl, live) in rc448_drift.items():
        assert set(decl) == set(live), f"{name}: not a pure REORDER"
        assert decl != live, f"{name}: rc448 text is no longer a drift"

    # and all eight are repaired in the live tree
    warmup_all()
    by_name = {t.name: t for t in get_tool_schema().tools}
    for name, (_, live) in rc448_drift.items():
        assert name in by_name, f"{name} is no longer registered"
        assert _declared(by_name[name]) == live, (
            f"{name} has drifted back out of signature order")


def test_polar_random_positional_prefix_is_the_consequential_case() -> None:
    """The one drift with a BINDING consequence, pinned as its own claim.

    Seven of the eight rc448 drifts were keyword-only. This one was not, and the
    difference is what separates "the published contract is untidy" from "the
    published contract rebinds your arguments".
    """
    fn = resolve_dotted_callable("srmech.math.hdc.polar_random")
    kinds = [(p.name, p.kind) for p in inspect.signature(fn).parameters.values()]
    assert [n for n, _ in kinds] == ["D", "rng", "seed"], (
        f"polar_random signature moved: {[n for n, _ in kinds]}")
    assert all(k is inspect.Parameter.POSITIONAL_OR_KEYWORD for _, k in kinds), (
        "polar_random params are no longer all positionally bindable — the "
        "rc448 drift's consequence description in this module needs revisiting.")
    warmup_all()
    entry = {t.name: t for t in get_tool_schema().tools}[
        "srmech.math.hdc.polar_random"]
    assert _declared(entry) == ["D", "rng", "seed"], (
        "the published contract no longer states the binding order, so "
        "polar_random(D, x) binds a parameter the reader did not name.")
