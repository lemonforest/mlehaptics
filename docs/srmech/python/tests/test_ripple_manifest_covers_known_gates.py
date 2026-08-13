"""`#T1063` -- the ripple-gate manifest cannot silently shrink.

``tools/ripple_gates.txt`` is the committed SSOT for the FAST dispatch-surface
gates that a new-op / ``ToolEntry``-change rc must pass (run via
``tools/ripple_check.py``). The value of that manifest is entirely in its
COMPLETENESS: the failure it exists to prevent is a build brief that drops a
gate. So the manifest must never lose a known dispatch-surface family.

This meta-test pins two invariants:

  1. **Coverage** -- the manifest is a superset of a hardcoded FROZEN set of the
     known dispatch-surface gate files (registry / carrier / rosetta / c-claims /
     mcp / regen / worked-example family / count-pin / class-TOML op-ref guard /
     ref-notation / JPL / version-pin / non_compute). Delete a frozen gate from
     the manifest and this reds.

  2. **No dangling** -- every manifest entry resolves to a real file on disk, so
     a rename that orphans a manifest line is caught here, not at ``ripple_check``
     run time.

The FROZEN set is deliberately a FLOOR, not the whole manifest: the manifest may
(and does) list more gates than these. This test only guarantees the floor holds.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # docs/srmech/python/tests
_PKG_ROOT = _HERE.parent                          # docs/srmech/python
_TOOLS = _PKG_ROOT / "tools"

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import ripple_check  # noqa: E402  (tools/ on sys.path above)

_MANIFEST = _TOOLS / "ripple_gates.txt"

# The known dispatch-surface gate FILES -- one or more per family named in the
# `#T1063` brief. Files, not node ids: the manifest may target a single node
# (e.g. the version pin) but coverage is asserted at file granularity.
FROZEN_KNOWN_GATES = frozenset({
    # -- C tool registry / schema / invoke ------------------------------------
    "tests/test_tool_registry_c_rc184.py",
    "tests/test_tool_schema_ops_c_rc185.py",
    "tests/test_invoke_tool_c_rc188.py",
    # -- carrier schema -------------------------------------------------------
    "tests/test_carrier_schema_rc205.py",
    # -- rosetta (transitive standalone-C reachability + completeness) --------
    "tests/test_rosetta_transitive_standalone.py",
    "tests/test_rosetta_completeness.py",
    # -- c-claims resolution --------------------------------------------------
    "tests/test_c_claim_resolution_rc300.py",
    # -- MCP surface (mcpb emitter: "tool list == advertised introspection";
    #    server-free. The heavyweight socket/subprocess test_mcp.py is
    #    deliberately NOT a ripple gate as a WHOLE FILE -- it hangs a fast
    #    runner, see tests/RIPPLE_GATES.md) -------------------------------------
    "tests/test_mcpb_emit.py",
    # -- MCP coercer + signature-drift: the TWO fast NODE-ID gates carved out of
    #    test_mcp.py. These catch the rc273/rc328 class -- a new op's novel param
    #    TYPE with no `_PARAM_COERCERS` handler, and declared params drifting from
    #    the signature. Neither mcpb_emit (no coercion) nor the C-marshalling
    #    gates (wire, not the Python coercer registry) cover this axis. They run
    #    pure (no server / no fixture, ~sub-second). Frozen as NODE-IDS so the
    #    coverage check REQUIRES the exact node, never the hanging whole file. ----
    "tests/test_mcp.py::test_all_param_types_json_coercible",
    "tests/test_mcp.py::test_schema_signature_alignment_no_drift",
    # -- describe() TOP-LEVEL KEY SET (rc430 repair, `#T1127`). Three files pin
    #    that key set exhaustively and an rc adding a key moves ALL THREE at
    #    once. rc430 shipped with all three red behind a green ripple_check,
    #    because only test_mcp.py was in the manifest and only by node ids that
    #    do not run the pin. Frozen as a NODE ID for the hanging file and
    #    whole-file for the two cheap peers, plus the DERIVING gate itself --
    #    that gate is what keeps the manifest roster honest, so it is the one
    #    entry whose quiet loss would restore the original blind spot. --------
    "tests/test_mcp.py::test_describe_shape",
    "tests/test_describe_registry_pointer_rc407.py",
    "tests/test_domain_classes_rc298.py",
    "tests/test_describe_key_set_pins_rc430.py",
    # -- advertised returns.type vs observed, driven by REAL args (rc430
    #    repair, `#T1127`). Its retro-check pins which ops the synth path
    #    cannot reach; rc430 widened that path and un-blocked all six at once,
    #    the check went red as designed, and nothing ran it for an entire rc
    #    because the file was not in the manifest. -----------------------------
    "tests/test_arrow_and_censuses_rc427.py",
    # -- regen-all idempotence / codegen graph --------------------------------
    "tests/test_regen_all_rc346.py",
    # -- worked-example family (strict-zero AND executed ledger AND the
    #    example["input"]-vs-inputSchema cross-check, rc355 `#T993`: every
    #    ToolEntry.example["input"] must be a valid kwargs map against its own
    #    rendered inputSchema. Caught rc388 only via the full suite. ----------
    "tests/test_worked_examples_strict_zero_rc353.py",
    "tests/test_worked_examples_execute_rc354.py",
    "tests/test_tool_example_input_schema_rc355.py",
    # -- composes / preserves: the cascade-identity family (rc423, `#T1113`).
    #    FROZEN for the reason rc423 exists. Its finding is that a surface with
    #    no population instrument does not trickle -- it STALLS, and then reads
    #    as finished because nothing is red (measured: 9 -> 16 rows across ~45
    #    rcs, three correctness gates green throughout). A ratchet that can be
    #    quietly dropped from the manifest is that same failure one level up,
    #    so the population gate and the grain gate it depends on are pinned
    #    here rather than left to a future manifest edit. All three are edited
    #    from the SAME curated file as explanation / example, so an rc touching
    #    any ToolEntry can move them by accident. ------------------------------
    "tests/test_composes_grain_rc412.py",
    "tests/test_composes_population_rc423.py",
    "tests/test_preserves_taxonomy_rc423.py",
    # -- count-pin describe()["tools"]["total"] -------------------------------
    "tests/test_registry_smoke_rc127.py",
    # -- class-TOML op-ref guard (#T930 -- the third generated C table) -------
    "tests/test_class_catalog_oprefs_resolve_930.py",
    # -- ref-notation emitted-artifact guard ----------------------------------
    "tests/test_ref_notation_emitted_rc348.py",
    # -- JPL Power-of-Ten audit ratchet ---------------------------------------
    "tests/test_jpl_audit.py",
    # -- version pin (the single hard version-literal gate) -------------------
    "tests/test_signal_processing_scaffolding.py",
    # -- non_compute / annex split --------------------------------------------
    "tests/test_non_compute_ratchet_rc170.py",
    "tests/test_annex_ratchet_rc177.py",
    "tests/test_annex_ratchet_rc183.py",
    # -- self-hosting import ban (`#T1073`): the ONE table-driven ban list.
    #    A new op-rc's new TEST FILE reaching for stdlib `fractions` trips it
    #    (#845 / #870 -- it reds a fresh CI round, rc386, if the runner omits
    #    it), and so does a new package module reaching for numpy / math /
    #    decimal, or bypassing the `srmech._json` / `srmech._toml` front doors.
    #    Absorbed the three separate ratchets at rc405. Pure-Python. ------------
    "tests/test_selfhosting_import_ban.py",
    # -- decode-aware namespace population pin (rc361, `#T1034`): a new cascade
    #    op bumps the `srmech.cascade` DECODED-channel population (rc387 ran it
    #    by hand at 100 -> 102). Invisible to a text grep; the manifest's only
    #    population-of-namespace gate. Pure-Python, whole file. -----------------
    "tests/test_namespace_prefix_decode_aware_rc361.py",
    # -- search-corpus witness: the introspect corpus is built FROM ToolEntry
    #    prose, so ANY ToolEntry edit moves its content-address. Four
    #    consecutive rcs moved it (rc416/419/420/421); on rc421 ripple_check
    #    went green while CI went red, because it was unlisted. Frozen so a
    #    future manifest trim cannot drop the prose-ripple axis. -------------
    "tests/test_search_glyph_tokenizer_rc416.py",
    # -- notebook currency: the notebook's `Live at rcNNN:` stamps + its two
    #    live cardinals move on EVERY rc (the stamp set is pinned to the
    #    release, so a bare version bump moves it -- no op required). rc427 is
    #    the THIRD round to go green here and red in CI on this exact shape,
    #    after rc421 (search corpus) and rc422 (README). Frozen so the prose-
    #    currency axis cannot be trimmed back out a fourth time. -------------
    "tests/test_notebook_currency_rc420.py",
    # -- op-name-set witness: `EXPECTED_N` + the sha256-pinned name manifest.
    #    Frozen because its count is a bare ASSIGNMENT, not a comparison, so
    #    the `== <total>` count-pin grep every rc runs cannot see it -- the one
    #    count-pin the standard predicate structurally misses. ---------------
    "tests/test_op_name_set_witness_rc361.py",
    # -- owner axis / registry-total restatement (rc428, `#T1126`) ------------
    #    THE FIFTH INSTANCE of the unlisted-gate shape this frozen set exists
    #    to prevent, and the costliest so far: it took SIX CI cells red at
    #    rc427 while appearing in NEITHER the manifest nor this set. Frozen
    #    rather than merely listed because its collision surface is scheduled,
    #    not hypothetical -- measured forward over the next 105 registry
    #    totals, 39 (37%) take it red, the FIRST at 665, ten registrations from
    #    the live 655. Twenty-seven of those 39 are bare `#NNN` refs that
    #    test_ref_notation_emitted_rc348.py MANDATES, so the two known blind
    #    spots are the same blind spot pointed at each other. A gate that can
    #    be quietly dropped from the manifest is that failure one level up.
    "tests/test_owner_axis_rc410.py",
    # -- citation-contains-term (rc428, `#T1126`) ----------------------------
    #    Frozen for the reason the gate exists. Its subject is CITATION PROSE
    #    inside ToolEntry summaries and module docstrings -- prose that is
    #    EMITTED into `_tool_docs.py` and compiled into
    #    `srmech_tool_registry.c`, and therefore edited on ordinary op rcs by
    #    authors not thinking about attestation. Measured at rc428: a FALSE
    #    Baez citation shipped inside published wheels and reached users via
    #    describe() and the MCP tool list while SIX attestation tests stayed
    #    green, because all six asserted `source_url == "<that same url>"` --
    #    the tree asserting the tree. This is the only gate that reads an
    #    EXTERNAL measurement of the cited source, so dropping it from the
    #    manifest restores exactly the ungated surface that shipped the defect.
    "tests/test_citation_manifest_rc428.py",
    # -- the FRAME axis + synthesised-argument provenance (rc430, `#T1127` /
    #    `#T1094`). Frozen together because they share one piece of machinery:
    #    the (op, param) argument provider. Both are ToolEntry-derived, so a
    #    new op moves them WITHOUT any declaration being edited --
    #    test_frame_scope_rc430 derives its admissible set behaviourally and
    #    asserts set equality in both directions, which is precisely how it
    #    avoids `reads_lane`'s fate (9 declarers in 82 rcs, because opt-in).
    #    A gate that can be quietly dropped from the manifest is that same
    #    opt-in failure one level up, which is why they are pinned here rather
    #    than left to a future manifest edit.
    "tests/test_frame_scope_rc430.py",
    "tests/test_synth_args_provenance_rc430.py",
})


def _manifest_targets() -> list[str]:
    assert _MANIFEST.is_file(), f"ripple manifest missing: {_MANIFEST}"
    return ripple_check.load_manifest(_MANIFEST)


def test_manifest_is_nonempty() -> None:
    targets = _manifest_targets()
    assert targets, "ripple manifest resolved to zero targets"


# The two fast NODE-ID gates that carry the novel-param-type axis. Named
# explicitly (not just folded into the generic frozen check) because this is the
# exact axis the ripple memory most warns about, and it is invisible to
# mcpb_emit + the C-marshalling gates.
MCP_COERCER_SIGNATURE_NODE_GATES = (
    "tests/test_mcp.py::test_all_param_types_json_coercible",
    "tests/test_mcp.py::test_schema_signature_alignment_no_drift",
)


def test_mcp_coercer_and_signature_gates_present_by_node_id() -> None:
    """The novel-param-type / signature-drift axis (rc273 / rc328) must be in the
    manifest by EXACT node-id -- never the hanging whole test_mcp.py, never absent."""
    raw_targets = set(_manifest_targets())
    missing = [n for n in MCP_COERCER_SIGNATURE_NODE_GATES if n not in raw_targets]
    assert not missing, (
        "ripple manifest is missing the MCP coercer / signature-drift node-id "
        "gate(s):\n  " + "\n  ".join(missing)
        + "\n\nThese catch a new op's novel param TYPE (no _PARAM_COERCERS handler) "
        "and declared-params-vs-signature drift -- covered by NOTHING else in the "
        f"set. Add them to {_MANIFEST.name} as exact `file::node` targets."
    )


def _is_node_id(entry: str) -> bool:
    """A frozen/manifest entry is a node-id if it names a specific test node."""
    return "::" in entry


def _node_func(entry: str) -> str:
    """The trailing test-function name of a node-id ('f.py::test_x' -> 'test_x')."""
    return entry.split("::", 1)[1]


def test_manifest_covers_every_frozen_gate() -> None:
    """The manifest is a SUPERSET of the frozen known dispatch-surface gates.

    File-level frozen entries are satisfied by ANY manifest target in that file;
    NODE-ID frozen entries (e.g. the two MCP coercer / signature gates carved out
    of the hanging test_mcp.py) require the EXACT node-id -- so the whole file can
    never be silently substituted for the two fast nodes, and the nodes can never
    be silently dropped.
    """
    targets = _manifest_targets()
    raw_targets = set(targets)
    files_in_manifest = {ripple_check.target_file(t) for t in targets}

    frozen_files = {g for g in FROZEN_KNOWN_GATES if not _is_node_id(g)}
    frozen_nodes = {g for g in FROZEN_KNOWN_GATES if _is_node_id(g)}

    missing_files = sorted(frozen_files - files_in_manifest)
    missing_nodes = sorted(n for n in frozen_nodes if n not in raw_targets)
    missing = missing_files + missing_nodes
    assert not missing, (
        "ripple manifest dropped known dispatch-surface gate(s):\n  "
        + "\n  ".join(missing)
        + f"\n\nAdd them back to {_MANIFEST.name}. These gates ripple from any "
        "new-op / ToolEntry change; the manifest is the repo's record of that set."
        "\n(A NODE-ID gate must appear as the exact `file::node`, not just the file.)"
    )


def test_every_manifest_entry_resolves_to_a_real_target() -> None:
    """No dangling manifest line -- every target's file exists, and every
    manifest NODE-ID resolves to a `def <node>` actually present in that file."""
    targets = _manifest_targets()
    dangling = []
    for t in targets:
        rel = ripple_check.target_file(t)
        path = _PKG_ROOT / rel
        if not path.is_file():
            dangling.append(f"{t}  (no such file)")
            continue
        if _is_node_id(t):
            func = _node_func(t)
            src = path.read_text(encoding="utf-8", errors="replace")
            if f"def {func}(" not in src:
                dangling.append(f"{t}  (no `def {func}(` in {rel})")
    assert not dangling, (
        "ripple manifest has entries pointing at non-existent files/nodes:\n  "
        + "\n  ".join(dangling)
        + f"\n\nFix or remove them in {_MANIFEST.name}."
    )


def test_every_frozen_gate_actually_exists() -> None:
    """The frozen set itself must not go stale under a rename -- files must
    exist, and frozen NODE-IDS must still name a real `def <node>`."""
    stale = []
    for g in FROZEN_KNOWN_GATES:
        rel = ripple_check.target_file(g)
        path = _PKG_ROOT / rel
        if not path.is_file():
            stale.append(f"{g}  (no such file)")
            continue
        if _is_node_id(g):
            func = _node_func(g)
            src = path.read_text(encoding="utf-8", errors="replace")
            if f"def {func}(" not in src:
                stale.append(f"{g}  (no `def {func}(` in {rel})")
    assert not stale, (
        "FROZEN_KNOWN_GATES lists gate(s) that no longer exist (a gate was "
        "renamed):\n  " + "\n  ".join(sorted(stale))
        + "\n\nUpdate this frozen set AND the manifest to the new name."
    )


# ── the whole-suite COLLECTION SWEEP (rc424, `#T1113`) ───────────────────────
#
# The sweep is NOT a manifest line, and that is deliberate: the manifest holds
# pytest TARGETS, and this is a sweep over the entire suite. Encoding it as a
# target would misfile it and subject it to the very limit it exists to escape
# — a manifest can only see the files it names, and a rename defect breaks the
# file nobody thought to name.
#
# So it is pinned HERE instead, at the same granularity FROZEN_KNOWN_GATES pins
# the target list: the runner must still perform the sweep, and must still run
# it BEFORE the gates.

def test_the_runner_exposes_a_whole_suite_collection_sweep() -> None:
    """`ripple_check` must still carry the collect-only sweep.

    Measured cause (rc424): ONE stale importer of a renamed module took twelve
    CI jobs red — all six pure shards, every native cell, asserts-live and the
    partition guard — because an import error at COLLECTION kills a shard
    outright. This runner was GREEN on that same tree: every gate it names
    imported fine, and the stale importer sat in a file no gate targets.
    """
    assert hasattr(ripple_check, "run_collect_sweep"), (
        "ripple_check.run_collect_sweep is gone. The whole-suite collection "
        "sweep is the ONLY check in this runner that sees files the manifest "
        "does not name; without it a rename is invisible to the runner and "
        "surfaces as a dozen red CI jobs with a one-line cause.")
    sweep = getattr(ripple_check, "COLLECT_SWEEP", None)
    assert isinstance(sweep, list) and "--collect-only" in sweep, (
        f"COLLECT_SWEEP must still be a --collect-only invocation; got {sweep!r}")
    assert "tests/" in sweep, (
        "the sweep must cover the WHOLE tests/ tree — narrowing it to a subset "
        "reintroduces the blind spot it closes")


def test_the_collection_sweep_runs_before_the_gates_and_aborts_on_failure() -> None:
    """Order and abort-on-failure are the load-bearing half.

    A sweep that ran AFTER the gates, or whose nonzero return did not abort,
    would let the runner print gate results computed on a tree that could not
    be imported — which is worse than not running it, because those results
    look authoritative and are not.
    """
    src = (_TOOLS / "ripple_check.py").read_text(encoding="utf-8")
    body = src.split("def main(", 1)[1]
    call = body.find("run_collect_sweep(")
    pytest_cmd = body.find('"-m", "pytest"')
    assert call != -1, "main() no longer calls run_collect_sweep()"
    assert pytest_cmd != -1, "main() no longer builds the gate pytest command"
    assert call < pytest_cmd, (
        "the collection sweep must run BEFORE the gate command is built — "
        "gate results computed after a collection error are misleading, not "
        "merely incomplete.")
    tail = body[call:pytest_cmd]
    assert "return rc" in tail, (
        "a nonzero collection sweep must ABORT the run; without the early "
        "return the runner would go on to report gate results for a tree that "
        "does not import.")
