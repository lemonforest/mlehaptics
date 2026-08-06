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
    # owed_orchestration (0) — NO owed MCP/CLI/LLM annex rows remain.
    # rc185 moved tool_entries_to_mcp_defs owed → composes_c (it earned its C
    # projection peer); rc186 moved serve_stdio owed → composes_c (the MCP JSON-RPC
    # protocol + stdio LOOP earned its C peer); rc188 moved invoke_tool owed →
    # composes_c (the tools/call DISPATCH SPINE srmech_invoke_tool earned its C peer);
    # rc193 moved the 7 CLI grammar rows (main / build_parser + the 5 add_arguments)
    # owed → composes_c (srmech_cli_parse + srmech_cli_dispatch reproduce + route the
    # whole console-script grammar; a bare-C host parses + dispatches the subcommands);
    # rc194 moved serve_http_sse owed → composes_c (the MCP HTTP+SSE transport earned
    # its C peer srmech_mcp_serve_http_sse over the new rc194 TCP PAL).
    # composes_c (20) — the mcp tool_entries_to_mcp_defs projection (rc185: earned
    # its C peer srmech_tool_entries_to_mcp_defs) + serve_stdio (rc186: earned its C
    # peer srmech_mcp_serve_stdio — the loop + framing + initialize/tools-list/ping/
    # shutdown run in C) + invoke_tool (rc188: earned its C peer srmech_invoke_tool —
    # the tools/call DISPATCH SPINE) + the 7 CLI grammar rows (rc193: earned the C
    # peer srmech_cli_parse + srmech_cli_dispatch — main runtime-dispatches through
    # them; build_parser + the 5 add_arguments are the pure-fallback grammar SSoT whose
    # C peer is proven equivalent by the behavior-parity test) + serve_http_sse
    # (rc194: earned its C peer srmech_mcp_serve_http_sse — the whole HTTP+SSE
    # transport in C over the new TCP PAL) + the subcommand run/run_* dispatch bodies
    # over already-C / non_compute leaves (the fully-C bus, the C DSL chain, the owed
    # class ops); each reaches no python_only_debt / bignum_reference /
    # c_exists_unbound leaf (all three are 0).
    "srmech.mcp._sse.serve_http_sse": "composes_c",
    "srmech.mcp._tools.tool_entries_to_mcp_defs": "composes_c",
    "srmech.mcp._tools.invoke_tool": "composes_c",
    "srmech.mcp._stdio.serve_stdio": "composes_c",
    "srmech.cli.main.main": "composes_c",
    "srmech.cli.main.build_parser": "composes_c",
    "srmech.cli.bus.add_arguments": "composes_c",
    "srmech.cli.dsl.add_arguments": "composes_c",
    "srmech.cli.mcp.add_arguments": "composes_c",
    "srmech.cli.klass.add_arguments": "composes_c",
    "srmech.cli.status.add_arguments": "composes_c",
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
# serve_stdio owed → composes_c, rc188 moved invoke_tool owed → composes_c, rc193
# moved the 7 CLI grammar rows owed → composes_c, rc194 moved serve_http_sse owed →
# composes_c, so the annex split is now 0/20/1/3 — the rows are still rc183-
# introduced annex rows, just now all-C-backed)
_ANNEX_DELTA = {"composes_c": 20, "host_glue": 1, "dev_tooling": 3}
# the FULL split after the host-glue annex (post-rc182 4/94/14/41 + the +24 delta;
# rc185 living-pin bump: the 3 tool_schema projection rows earned C → owed 15→12,
# composes_c 103→106; rc186: serve_stdio earned C → owed 12→11, composes_c 106→107;
# rc188: invoke_tool earned C → owed 11→10, composes_c 107→108; rc193: the 7 CLI
# grammar rows earned C → owed 10→3, composes_c 108→115; rc194: serve_http_sse
# earned C → owed 3→2, composes_c 115→116; sum stays 177)
# rc196 (make_class → C leaf-batch 2): genome.encode_shape left non_compute for
# c_dispatched (its C peer srmech_genome_encode_shape) → composes_c 116 → 115;
# non_compute total 177 → 176. (genome.telomere also earned a C peer but moved
# composition_of_c → c_dispatched, not a non_compute row.)
# rc202: owed_orchestration EMPTY (run_class_method discharged -> composes_c 117).
# rc205 (gh #1293): +1 composes_c — srmech.introspect.carrier_schema.carrier_schema (the
# CARRIER introspection surface; dispatches to its C peer srmech_carrier_schema
# over the compiled-in const registry). composes_c 117 -> 118; sum 176 -> 177.
# rc217 (gh #1360): the 3 srmech.math.text COMPUTE kernels moved
# non_compute/composes_c -> c_dispatched (they earned byte-identical
# srmech_text_* C peers; the composes_c mis-classification was the
# self-contained-kernel hiding spot). composes_c 118 -> 115; total 177 -> 174.
# rc218 (#826, living-pin bump — the PARITY-COMPLETENESS annex): the ledger walk
# extends to srmech.spectral / srmech.rbs_lm / srmech.introspect /
# srmech.profile_loader (+30 rows; the 15 non_compute rows split +5 composes_c /
# +6 host_glue / +4 dev_tooling). composes_c 115 -> 120, host_glue 15 -> 21,
# dev_tooling 44 -> 48; total 174 -> 189. The mcp/cli/llm _ANNEX_ROWS /
# _ANNEX_DELTA below are untouched (rc218 moves no mcp/cli/llm row; the rc218
# annex specifics are pinned in test_rosetta_completeness.py +
# test_non_compute_ratchet_rc170.py).
# rc225 (user design 2026-07-12): +1 composes_c —
# srmech.amsc.responsion_schema.responsion_schema (the RESPONSION / stored-
# relationship introspection surface, the k=3 edge face binding tool_schema +
# carrier_schema; dispatches to its C peer srmech_responsion_schema over the
# compiled-in const registry — composes_c FROM BIRTH, the rc205 carrier_schema
# precedent). composes_c 120 -> 121; total 189 -> 190.
# rc362 (ADR-0010 acoustic slice): the walk gains the srmech.music root and its
# NINE ops — and the split moves by exactly +1, not +9. Eight of the nine are
# COMPUTE rows (7 composition_of_c + bessel_j_fixed c_dispatched) and never
# reach this counter; only srmech.music.bell_partials is non_compute, because
# it computes nothing — it returns the Fletcher & Rossing sec. 21.3 tuning
# TARGETS as exact Q constants, the from_bodies / carrier_schema pure-exact-data
# precedent — and it lands composes_c since materialising those Q ratios is a
# reduction through the C-backed Class-I gcd. composes_c 137 -> 138; total
# 209 -> 210. host_glue (21) and dev_tooling (51) are UNMOVED; a music row
# appearing in either would have been a misclassification, not a bump.
_FULL_SPLIT = {"composes_c": 138, "host_glue": 21, "dev_tooling": 53}  # rc407 (`#T1076`): host_glue 22 -> 21, total 213 -> 212 — srmech.introspect stopped exporting the PRIVATE `_maybe_auto_publish` from its __all__ (it also exported `_PublishHandle`; neither belongs on a public surface). _live_ops() walks __all__, falling back to non-underscore dir(), so an underscore name absent from __all__ is off the tracked surface by BOTH routes and its rosetta_classification.ndjson row went stale. The FUNCTION is untouched and still reached by direct attribute access from srmech/__init__.py:63, which __all__ does not govern — what moved is the PUBLISHED surface, which is what this census counts.  # rc364 ADR-0010 first execution slice: +1 host_glue (dsl.resolve_alias_descriptor — descriptor FS DISCOVERY, the load_catalog / load_class_catalog / get_descriptor precedent: a bare-C host must FIND the file before srmech_toml can parse it) and +2 dev_tooling (dsl.list_alias_descriptors + dsl.register_alias_dir — BROWSE and CONFIGURE; exact peers of list_cascade_ops / list_classes and register_catalog_dir / register_class_dir, all four already dev_tooling). host_glue 21 -> 22, dev_tooling 51 -> 53, composes_c UNMOVED at 138 — none of the three composes a C op. The discriminator is NOT "does it touch the filesystem" (all three do) but LOAD/GET vs BROWSE/CONFIGURE, the split srmech.dsl already encodes over the SAME directory (load_class_catalog reads it = host_glue; list_classes browses it = dev_tooling). rc364 first shipped list_alias_descriptors as host_glue and CI caught it at 23/52; the fix was the CLASSIFICATION, not the pin.  # rc325 §𝕆-FIBER/v18: +3 composes_c (genome.genome_octonion_associator + genome_add_octonion_fiber + genome_read_octonion_fiber, the octonion fiber channel's defect/assemble/read ops) 133 -> 136  # rc322 §Q8-FIBER/v17: +2 composes_c (genome.genome_add_fiber + genome_read_fiber, the fiber cap assemble/read ops) 131 -> 133  # rc312 §Q8/v16: +1 composes_c (genome.upgrade_v15_to_v16, the v15->v16 migration op) 130 -> 131  # rc308 #944: +1 composes_c (laplacian.hypercomplex_perspectives reader) 129 -> 130  # rc261: +2 composes_c (dsl alias TOML) + 1 dev_tooling (dsl.alias)  # rc249 #1390 item 2: +2 genome graph codec  # rc267 §96: +2 composes_c (genome_census + genome_registry)  # rc271 §96/F1251: +1 composes_c (genome.load_type_aliases_toml) + 2 dev_tooling (genome.set/clear_type_aliases)  # rc278 §102/F1252: +1 composes_c (plasmid.section_counts; plasmid_extract is composition_of_c)  # rc280 §102/F1253: -1 composes_c (plasmid.section_counts EARNED the srmech_genome_section_counts C peer -> c_dispatched)  # rc290 §102/F1259: +1 host_glue (hdc.klein4_random — the STOCHASTIC regime, alone after the by-regime split; no C peer BY REGIME, not by debt: its output is not a function of any input, so there is no kernel to mirror and nothing to byte-compare. The deterministic mints klein4_expand/_address/_from_one are c_dispatched and klein4_role is composition_of_c, so no debt ceiling moved.)  # rc292 §102/F1259: -1 host_glue (hdc.klein4_random REMOVED — rc290 closed only the seed= door; a SEEDED rng= is equally reproducible and every real call site passed one, so the STOCHASTIC bucket held an op that ran deterministically. Removal, not a bucket; callers compose klein4_encode_bytes.)  # rc297 `#934`: +1 composes_c (cascade.cd_register.cd_register — the general N-slot Cayley-Dickson register's CONSTRUCTOR row; a POPULATION pin, not a debt ceiling. It lands in composes_c (128 -> 129) and NOT host_glue (21, unchanged), and CEIL_WIRE_GLUE_GAPS stays 10 — the family has real C peers reachable through dispatch glue (srmech_cd_navmap / srmech_cd_navigate / srmech_cd_navmap_is_signed_permutation), so this is composition, not a laundered gap. The constructor computes nothing; all compute is in the methods, which route to those three c_dispatched rows.)  # rc345 (task T964): +1 composes_c (genome.genome_content — the repartition-invariant CONTENT accessor; dispatches to the byte-identical C peer srmech_genome_content, the genome_census/genome_registry composes_c precedent) 136 -> 137
_TOTAL_NON_COMPUTE = 212  # rc407 (`#T1076`): host_glue 22 -> 21, total 213 -> 212 — srmech.introspect stopped exporting the PRIVATE `_maybe_auto_publish` from its __all__ (it also exported `_PublishHandle`; neither belongs on a public surface). _live_ops() walks __all__, falling back to non-underscore dir(), so an underscore name absent from __all__ is off the tracked surface by BOTH routes and its rosetta_classification.ndjson row went stale. The FUNCTION is untouched and still reached by direct attribute access from srmech/__init__.py:63, which __all__ does not govern — what moved is the PUBLISHED surface, which is what this census counts.  # rc364 ADR-0010 first execution slice: 210 -> 213, the three srmech.dsl alias-catalog rows (list_alias_descriptors + resolve_alias_descriptor + register_alias_dir)         # rc362 ADR-0010 acoustic slice: 209 -> 210, srmech.music.bell_partials (the ONLY non_compute row among the nine music ops)  # rc325 §𝕆-FIBER/v18: 205 -> 208, the 3 octonion fiber ops (associator + add + read)  # rc322 §Q8-FIBER/v17: 203 -> 205, genome.genome_add_fiber + genome_read_fiber  # rc312 §Q8/v16: 202 -> 203, genome.upgrade_v15_to_v16  # rc308 `#944`: 201 -> 202, the hypercomplex_perspectives reader row  # rc297 `#934`: 200 -> 201, the cd_register constructor row above  # rc345 (task T964): 208 -> 209, genome.genome_content
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


def test_annex_delta_is_24_split_1_19_1_3():
    """The +24 annex rows split exactly 1 owed / 19 composes_c / 1 host_glue /
    3 dev_tooling (rc185 moved tool_entries_to_mcp_defs owed → composes_c;
    rc186 moved serve_stdio owed → composes_c; rc188 moved invoke_tool owed →
    composes_c; rc193 moved the 7 CLI grammar rows owed → composes_c)."""
    counts = Counter(_ANNEX_ROWS.values())
    assert dict(counts) == _ANNEX_DELTA, (
        f"annex +24 split drifted: got {dict(counts)}, expected {_ANNEX_DELTA}"
    )
    assert sum(counts.values()) == 24


def test_full_non_compute_split_matches_pin():
    """The full non_compute ledger split (the bus/dsl annex + the rc183 host-glue
    annex) matches the pinned ``_FULL_SPLIT`` and sums to the single living pin
    ``_TOTAL_NON_COMPUTE`` (updated per-rc; 203 at rc312). The exact numbers live
    in the constants, not this test's name."""
    counts = Counter(r["non_compute_kind"] for r in _rows()
                     if r.get("bucket") == "non_compute")
    assert dict(counts) == _FULL_SPLIT, (
        f"full non_compute split drifted: got {dict(counts)}, expected "
        f"{_FULL_SPLIT}"
    )
    assert sum(counts.values()) == _TOTAL_NON_COMPUTE == sum(_FULL_SPLIT.values())


def test_ceil_non_compute_owed_is_0():
    """The phase-driver ceiling is 0 after rc202 — the FINAL owed row
    run_class_method earned its C peer (srmech_run_class_method: NAME->descriptor
    resolve IN C + the rc201 engine + the 4-key wrap, byte-identical to pure). NO
    owed_orchestration row remains: the everything-to-C program is COMPLETE."""
    assert CEIL_NON_COMPUTE_OWED == 0, (
        f"CEIL_NON_COMPUTE_OWED must be 0 after rc202 (everything-to-C complete); "
        f"got {CEIL_NON_COMPUTE_OWED}"
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
