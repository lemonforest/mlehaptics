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
    #    deliberately NOT a ripple gate -- it hangs a fast runner, see
    #    tests/RIPPLE_GATES.md) --------------------------------------------------
    "tests/test_mcpb_emit.py",
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
})


def _manifest_targets() -> list[str]:
    assert _MANIFEST.is_file(), f"ripple manifest missing: {_MANIFEST}"
    return ripple_check.load_manifest(_MANIFEST)


def test_manifest_is_nonempty() -> None:
    targets = _manifest_targets()
    assert targets, "ripple manifest resolved to zero targets"


def test_manifest_covers_every_frozen_gate() -> None:
    """The manifest is a SUPERSET of the frozen known dispatch-surface gates."""
    targets = _manifest_targets()
    files_in_manifest = {ripple_check.target_file(t) for t in targets}
    missing = sorted(FROZEN_KNOWN_GATES - files_in_manifest)
    assert not missing, (
        "ripple manifest dropped known dispatch-surface gate(s):\n  "
        + "\n  ".join(missing)
        + f"\n\nAdd them back to {_MANIFEST.name}. These gates ripple from any "
        "new-op / ToolEntry change; the manifest is the repo's record of that set."
    )


def test_every_manifest_entry_resolves_to_a_real_file() -> None:
    """No dangling manifest line -- every target's file exists on disk."""
    targets = _manifest_targets()
    dangling = []
    for t in targets:
        rel = ripple_check.target_file(t)
        if not (_PKG_ROOT / rel).is_file():
            dangling.append(t)
    assert not dangling, (
        "ripple manifest has entries pointing at non-existent files:\n  "
        + "\n  ".join(dangling)
        + f"\n\nFix or remove them in {_MANIFEST.name}."
    )


def test_every_frozen_gate_file_actually_exists() -> None:
    """The frozen set itself must not go stale under a rename."""
    stale = sorted(g for g in FROZEN_KNOWN_GATES if not (_PKG_ROOT / g).is_file())
    assert not stale, (
        "FROZEN_KNOWN_GATES lists file(s) that no longer exist (a gate was "
        "renamed):\n  " + "\n  ".join(stale)
        + "\n\nUpdate this frozen set AND the manifest to the new name."
    )
