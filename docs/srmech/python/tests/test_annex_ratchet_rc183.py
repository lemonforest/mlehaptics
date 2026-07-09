"""The rc183 HOST-GLUE ANNEX ratchet — the ledger walk extends to srmech.mcp +
srmech.cli + srmech.llm.

The compute / exact-algebra / self-hosting arcs are closed (all three ceilings
0), the bus + DSL chain interpreter are C (rc177–182 annex). This rc extends the
ORCHESTRATION→C phase, per user direction, to the last host-facing surfaces: the
MCP tool server, the CLI dispatch grammar, and the (optional) LLM agent — a
bare-C host (no Python) must also serve MCP + run the CLI dispatch. This rc is
TEST-INFRA ONLY — it TRACKS the annex surface (extends ``_ROOTS`` to
mcp/cli/llm, adds the +24 rows, raises ``CEIL_NON_COMPUTE_OWED`` 4 → 15, extends
the dev_tooling allowlist by 3); the annex BUILDS (rc184+) then drive the owed
count back down.

This file pins the rc183 annex specifics (the +24 split, the ceiling, the four
sub-bucket totals, mcp/cli/llm in every ledger walk); it mirrors
``test_annex_ratchet_rc177.py`` one host-facing layer out. numpy-free (stdlib
json + the shared conftest live-op walk); mcp + cli + llm must import cleanly
numpy-absent (AND anthropic-SDK-absent for llm).

Ledger-undercount note (honest): the MCP owed count UNDERSTATES the real C
surface — ``MCPServer`` / ``MCPError`` are CLASSES (skipped by the
callable-non-class walk) and the ``_coercion`` JSON-Schema marshallers are
PRIVATE (``_``-tailed submodule, skipped). A genuine C MCP server needs those
too; they surface as owed when built.
"""
from __future__ import annotations

import json
import os as _os
import sys as _sys
from collections import Counter
from pathlib import Path

_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)

from conftest import _ROSETTA_ROOTS, rosetta_live_objects  # noqa: E402
from test_rosetta_completeness import (  # noqa: E402
    CEIL_NON_COMPUTE_OWED,
    NON_COMPUTE_DEV_TOOLING_EXEMPT,
    _ROOTS,
)

_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"

# The 24 annex rows (4 mcp + 17 cli + 3 llm) — the SSOT for the rc183 host-glue
# annex classification (defined_at -> non_compute_kind). These are the ACTUAL
# canonical <module>.<qualname> keys the ledger walk emits (verified against the
# live walk). The 2 cli.klass re-exports (describe_class / list_class_surface)
# resolve to the already-classified srmech.dsl._class_surface pair and are NOT
# here (they are rc177 dev_tooling rows, deduped by canonical key).
_ANNEX_ROWS = {
    # owed_orchestration (9) — the CLI/MCP control-grammar + dispatch a bare-C
    # host reimplements: the 2 remaining MCP tool-serving ops (invoke_tool +
    # serve_http_sse), the 2 CLI top-level dispatch ops, and the 5 subcommand
    # add_arguments (the argparse grammar). rc185 moved tool_entries_to_mcp_defs
    # owed → composes_c (it earned its C projection peer); rc186 moved serve_stdio
    # owed → composes_c (the MCP JSON-RPC protocol + stdio LOOP earned its C peer).
    "srmech.mcp._tools.invoke_tool": "owed_orchestration",
    "srmech.mcp._sse.serve_http_sse": "owed_orchestration",
    "srmech.cli.main.main": "owed_orchestration",
    "srmech.cli.main.build_parser": "owed_orchestration",
    "srmech.cli.bus.add_arguments": "owed_orchestration",
    "srmech.cli.dsl.add_arguments": "owed_orchestration",
    "srmech.cli.mcp.add_arguments": "owed_orchestration",
    "srmech.cli.klass.add_arguments": "owed_orchestration",
    "srmech.cli.status.add_arguments": "owed_orchestration",
    # composes_c (11) — the mcp tool_entries_to_mcp_defs projection (rc185: earned
    # its C peer srmech_tool_entries_to_mcp_defs) + serve_stdio (rc186: earned its C
    # peer srmech_mcp_serve_stdio — the loop + framing + initialize/tools-list/ping/
    # shutdown run in C; tools/call routes to the still-owed invoke_tool) + the
    # subcommand run/run_* dispatch bodies over already-C / non_compute leaves (the
    # fully-C bus, the C DSL chain, the owed serve/class ops); each reaches no
    # python_only_debt / bignum_reference / c_exists_unbound leaf (all three are 0).
    "srmech.mcp._tools.tool_entries_to_mcp_defs": "composes_c",
    "srmech.mcp._stdio.serve_stdio": "composes_c",
    "srmech.cli.bus.run": "composes_c",
    "srmech.cli.bus.run_list": "composes_c",
    "srmech.cli.bus.run_tap": "composes_c",
    "srmech.cli.bus.run_pipe": "composes_c",
    "srmech.cli.bus.run_send": "composes_c",
    "srmech.cli.bus.run_serve": "composes_c",
    "srmech.cli.dsl.run": "composes_c",
    "srmech.cli.mcp.run": "composes_c",
    "srmech.cli.klass.run": "composes_c",
    # host_glue (1) — reads ~/.srmech/*.ndjson (host FS) via srmech.introspect
    "srmech.cli.status.run": "host_glue",
    # dev_tooling (3) — the srmech.llm Anthropic-agent surface. HONEST-DEFAULT:
    # a bare-C host does NOT need an Anthropic-SDK agent; classified dev_tooling
    # pending a user decision on whether to build a C agent (a separate
    # C-HTTPS/TLS Messages-API arc) — REVERSIBLE to owed_orchestration if elected.
    "srmech.llm.anthropic_agent._to_anthropic_name": "dev_tooling",
    "srmech.llm.anthropic_agent_cli.build_parser": "dev_tooling",
    "srmech.llm.anthropic_agent_cli.main": "dev_tooling",
}

# the +24 annex delta by kind (what the host-glue annex ADDS to the pre-rc183
# split; rc185 moved tool_entries_to_mcp_defs owed → composes_c, rc186 moved
# serve_stdio owed → composes_c, so the annex split is now 9/11/1/3 — the rows are
# still rc183-introduced annex rows, just now C-backed)
_ANNEX_DELTA = {"owed_orchestration": 9, "composes_c": 11, "host_glue": 1,
                "dev_tooling": 3}
# the FULL split after the host-glue annex (post-rc182 4/94/14/41 + the +24 delta;
# rc185 living-pin bump: the 3 tool_schema projection rows earned C → owed 15→12,
# composes_c 103→106; rc186 living-pin bump: serve_stdio earned C → owed 12→11,
# composes_c 106→107; sum stays 177)
_FULL_SPLIT = {"owed_orchestration": 11, "composes_c": 107, "host_glue": 15,
               "dev_tooling": 44}
_TOTAL_NON_COMPUTE = 177
_HOSTGLUE_ROOTS = ("srmech.mcp", "srmech.cli", "srmech.llm")


def _rows():
    return [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def test_hostglue_roots_in_every_ledger_walk():
    """The completeness walk (_ROOTS) AND the shared non_compute walk
    (_ROSETTA_ROOTS) both include srmech.mcp + srmech.cli + srmech.llm — the
    extension that brings the host-glue annex surface into the everything-mirrors
    ledger."""
    for roots, where in ((_ROOTS, "test_rosetta_completeness._ROOTS"),
                         (_ROSETTA_ROOTS, "conftest._ROSETTA_ROOTS")):
        missing = [r for r in _HOSTGLUE_ROOTS if r not in roots]
        assert not missing, (
            f"{where} must include {_HOSTGLUE_ROOTS}; missing {missing} (got {roots})"
        )


def test_annex_rows_present_with_expected_kinds():
    """All 24 annex rows are in the ledger as non_compute with the pinned
    non_compute_kind (the ACTUAL canonical <module>.<qualname> keys)."""
    by_da = {r["defined_at"]: r for r in _rows()}
    missing = [da for da in _ANNEX_ROWS if da not in by_da]
    assert not missing, f"annex rows missing from the ledger: {sorted(missing)}"
    wrong = []
    for da, kind in _ANNEX_ROWS.items():
        row = by_da[da]
        if row.get("bucket") != "non_compute" or row.get("non_compute_kind") != kind:
            wrong.append(
                f"{da}: got bucket={row.get('bucket')!r} "
                f"kind={row.get('non_compute_kind')!r}, expected non_compute/{kind}"
            )
    assert not wrong, "annex row classification drift:\n  " + "\n  ".join(wrong)


def test_annex_rows_are_live():
    """Every annex row is a LIVE public op (the extended walk surfaces it) — the
    ledger is not carrying a phantom mcp/cli/llm key."""
    live = set(rosetta_live_objects())
    not_live = [da for da in _ANNEX_ROWS if da not in live]
    assert not not_live, (
        f"annex rows not surfaced by the live walk (mcp/cli/llm not in roots, a "
        f"module failed to import, or the key drifted): {sorted(not_live)}"
    )


def test_annex_delta_is_24_split_9_11_1_3():
    """The +24 annex rows split exactly 9 owed / 11 composes_c / 1 host_glue /
    3 dev_tooling (rc185 moved tool_entries_to_mcp_defs owed → composes_c;
    rc186 moved serve_stdio owed → composes_c)."""
    counts = Counter(_ANNEX_ROWS.values())
    assert dict(counts) == _ANNEX_DELTA, (
        f"annex +24 split drifted: got {dict(counts)}, expected {_ANNEX_DELTA}"
    )
    assert sum(counts.values()) == 24


def test_full_non_compute_split_sums_to_177():
    """The full non_compute ledger split (the bus/dsl annex + the rc183 host-glue
    annex) is 11/107/15/44 = 177 (rc185 + rc186 living-pin bumps)."""
    counts = Counter(r["non_compute_kind"] for r in _rows()
                     if r.get("bucket") == "non_compute")
    assert dict(counts) == _FULL_SPLIT, (
        f"full non_compute split drifted: got {dict(counts)}, expected "
        f"{_FULL_SPLIT}"
    )
    assert sum(counts.values()) == _TOTAL_NON_COMPUTE == sum(_FULL_SPLIT.values())


def test_ceil_non_compute_owed_is_11():
    """The phase-driver ceiling is 11 after rc186 — the rc185 residue of 12 minus
    the serve_stdio row that earned its C peer (the MCP JSON-RPC protocol + stdio
    LOOP in C). rc187+ build the tools/call arg-marshalling + invoke_tool dispatch
    (+ the CLI dispatch) to C and drive the owed count back down."""
    assert CEIL_NON_COMPUTE_OWED == 11, (
        f"CEIL_NON_COMPUTE_OWED must be 11 after rc186; got "
        f"{CEIL_NON_COMPUTE_OWED}"
    )


def test_annex_dev_tooling_keys_in_allowlist():
    """All 3 annex dev_tooling keys (the srmech.llm surface) are in the pinned
    NON_COMPUTE_DEV_TOOLING_EXEMPT allowlist (a dev_tooling row must be added
    DELIBERATELY — the HONEST-DEFAULT, reversible to owed if a C agent is
    elected)."""
    annex_dev = {da for da, k in _ANNEX_ROWS.items() if k == "dev_tooling"}
    assert len(annex_dev) == 3
    missing = annex_dev - set(NON_COMPUTE_DEV_TOOLING_EXEMPT)
    assert not missing, (
        f"annex dev_tooling keys not in the allowlist: {sorted(missing)}"
    )


def test_mcp_cli_llm_import_numpy_absent():
    """srmech.mcp + srmech.cli + srmech.llm import cleanly (the ratchet runs
    numpy-free, and llm imports anthropic-SDK-absent — the SDK import is
    deferred)."""
    import importlib
    import srmech.mcp  # noqa: F401
    import srmech.cli  # noqa: F401
    import srmech.llm  # noqa: F401
    assert importlib.import_module("srmech.mcp") is srmech.mcp
    assert importlib.import_module("srmech.cli") is srmech.cli
    assert importlib.import_module("srmech.llm") is srmech.llm
