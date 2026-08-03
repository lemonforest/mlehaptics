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
    # -- regen-all idempotence / codegen graph --------------------------------
    "tests/test_regen_all_rc346.py",
    # -- worked-example family (BOTH: strict-zero AND executed ledger) --------
    "tests/test_worked_examples_strict_zero_rc353.py",
    "tests/test_worked_examples_execute_rc354.py",
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
    # -- stdlib-fractions ban (new test files, #845 / #870): a new op-rc's new
    #    TEST FILE reaching for stdlib `fractions` trips this. It reds a fresh
    #    CI round (rc386) if the runner omits it. Pure-Python, whole file. ------
    "tests/test_no_stdlib_fractions_import.py",
    # -- decode-aware namespace population pin (rc361, `#T1034`): a new cascade
    #    op bumps the `srmech.cascade` DECODED-channel population (rc387 ran it
    #    by hand at 100 -> 102). Invisible to a text grep; the manifest's only
    #    population-of-namespace gate. Pure-Python, whole file. -----------------
    "tests/test_namespace_prefix_decode_aware_rc361.py",
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
