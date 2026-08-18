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

#: one `{ "bare", 12u, "srmech.dotted.name" }` row of either C index
_INDEX_ROW = re.compile(
    r'\{\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*,\s*(\d+)u\s*,\s*"([A-Za-z0-9_.]+)"\s*\}')

#: `cr_op_is(op, opl, "gcd", 3u)` — the compose dispatch arms
_CR_OP_IS = re.compile(r'cr_op_is\(op,\s*opl,\s*"([A-Za-z0-9_]+)",\s*(\d+)u\)')

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


def _parse_index(path: Path, marker: str) -> Dict[str, Tuple[int, str]]:
    """Parse a C name-to-name index into {bare: (declared_len, full_name)}."""
    text = path.read_text(encoding="utf-8")
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
    _check_index(_parse_index(_COMPOSE_C, "} CR_OP_REG[20] = {"), "CR_OP_REG", 0)


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


def test_compose_index_covers_exactly_the_dispatch_arms() -> None:
    """Same closure for ``cr_dispatch`` / ``cr_dispatch_real``.

    ``cr_op_is`` is also used by a FORM predicate further down the file
    (``orientation_compose``), which is not a dispatch arm — so the arms are
    read from the two dispatch functions only, not from the whole file.
    """
    text = _COMPOSE_C.read_text(encoding="utf-8")
    arms: Dict[str, int] = {}
    for fn in ("static srmech_status_t cr_dispatch_real(",
               "static srmech_status_t cr_dispatch("):
        body = text[text.index(fn):]
        body = body[:body.index("\n}\n")]
        for name, ln in _CR_OP_IS.findall(body):
            arms[name] = int(ln)
    index = _parse_index(_COMPOSE_C, "} CR_OP_REG[20] = {")
    assert set(arms) == set(index), (
        f"CR_OP_REG and the compose dispatch arms disagree.\n"
        f"  dispatch-only (UNVALIDATED, still silently dropping): "
        f"{sorted(set(arms) - set(index))}\n"
        f"  index-only (validated but never run): "
        f"{sorted(set(index) - set(arms))}")
    for name, ln in arms.items():
        assert index[name][0] == ln, (
            f"{name}: dispatch matches on length {ln}, index declares "
            f"{index[name][0]}")


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
