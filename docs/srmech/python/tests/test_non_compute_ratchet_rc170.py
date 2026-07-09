"""The rc170 non_compute four-way-split ratchet — the orchestration→C phase.

The compute (CEIL_PYTHON_ONLY_DEBT=0), exact-algebra (CEIL_BIGNUM_REFERENCE=0)
and self-hosting (CEIL_C_EXISTS_UNBOUND=0) arcs are CLOSED. ``non_compute`` (the
last un-ceilinged bucket, rc177 annex: 153 rows after extending the ledger walk
to srmech.bus + srmech.dsl) is the honest next frontier: making a bare-C host
(no Python) run the WHOLE apparatus — dispatch, catalogs, IPC, the genome, the
chain-runner, the DSL chain / class interpreter — in C.

This rc splits the ``non_compute`` rows into FOUR honest sub-buckets (the
``non_compute_kind`` field in ``rosetta_classification.ndjson``) and pins the
split (rc177 annex counts):

  owed_orchestration (11) — genuine control/dispatch LOGIC a bare-C host needs;
                            owed-C, DOWN-ONLY (CEIL_NON_COMPUTE_OWED, the phase
                            driver, in test_rosetta_completeness.py). rc177 annex
                            +10: the bus Bio-TOTP cipher stream kernel + the DSL
                            chain / class interpreter; rc178 −1: decode_splice
                            earned its C peer.
  composes_c        (87) — thin: composes existing C, or a pure accessor /
                            constructor / validator; TRANSITIVE-REACHABILITY
                            assert (hides no Python kernel), not a ceiling.
  host_glue         (14) — filesystem / host I/O; tracked, no ceiling.
  dev_tooling       (41) — a bare-C host never needs it; PINNED exempt allowlist.

This file proves the split is COMPLETE (sums to 153), DISJOINT, and TIGHT (the
live owed count == CEIL_NON_COMPUTE_OWED). numpy-free (stdlib json + the shared
conftest live-op walk).
"""
from __future__ import annotations

import json
import os as _os
import sys as _sys
from collections import Counter
from pathlib import Path

# pytest's prepend import-mode does not add a package dir (tests/ has an
# __init__.py) to sys.path on isolated collection — guard the tests dir on first
# (the test_immolation.py / test_rosetta_completeness.py precedent), so the
# sibling `from test_rosetta_completeness import ...` (the SSOT for the ceiling +
# allowlist) and `from conftest import ...` resolve.
_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)

from conftest import rosetta_live_objects  # noqa: E402
from test_rosetta_completeness import (  # noqa: E402
    CEIL_NON_COMPUTE_OWED,
    NON_COMPUTE_DEV_TOOLING_EXEMPT,
    _NON_COMPUTE_KINDS,
)

_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"

# The pinned four-way split — the SSOT for this rc's classification. The three
# ratchet tests in test_rosetta_completeness.py (owed ceiling / composes_c
# reachability / dev_tooling allowlist) enforce the semantics; this pins the
# COUNTS so the split stays complete + tight.
# rc171: the 5 op_provenance verdict/carry ops earned C peers → moved
# owed_orchestration → composes_c (owed 20→15, composes_c 65→70; sum stays 114).
# rc172: the catalog registry/kernel/audit batch — 6 catalog ops earned C
# (list_registered_roots / get_local_kernel_state / use_local_kernel /
# clear_local_kernel / attestation_audit → their srmech_catalog_* peers;
# list_attested_sources classified composes_c directly, consistent with the
# already-composes_c get_attested_dataset / get_attested_descriptor) → moved
# owed_orchestration → composes_c (owed 15→9, composes_c 70→76; sum stays 114).
# rc173: the amsc.compose chain-runner PARSE half — parse_chain_spec +
# parse_catalog_chains earned C peers (srmech_chain_spec_parse /
# srmech_chain_catalog_parse) → moved owed_orchestration → composes_c
# (owed 9→7, composes_c 76→78; sum stays 114). resolve_chain / run_chain stay
# owed (arbitrary-op FFI over the live object graph → rc174).
# rc174: the amsc.compose chain-runner RUN LOOP — resolve_chain + run_chain
# earned a C peer (srmech_chain_run runs the whole shipped apparatus — pi /
# series / Friedmann — end-to-end in C to byte-identical OUTPUT; the pure path
# runs any out-of-table op / non-raise policy / @catalog ref) → moved
# owed_orchestration → composes_c (owed 7→5, composes_c 78→80; sum stays 114).
# rc175: the 2 catalog CHAIN-ORCHESTRATION dependents earned C peers
# (list_catalog_chains → srmech_catalog_list_chains; run_catalog_chain →
# srmech_catalog_run_chain, each composing the rc173 parse + rc174 chain-runner)
# → moved owed_orchestration → composes_c (owed 5→3, composes_c 80→82; sum stays
# 114). HONEST SPLIT: dispatch.infer (the F929 router) STAYS owed → rc176 (its
# relationship payloads carry live non-JSON carriers — a multi-carrier FFI arc,
# not one clean rc). The 3 remaining owed = dispatch.infer + the 2 tool_schema
# rows (get_tool_schema / tool_schema_view → built with the host-glue MCP server).
# rc176: dispatch.infer earned a C peer — srmech_infer (the ORCHESTRATION→C
# spine, batch 6; the CARRIER-FFI foundation). The smallest sound foundation:
# the TWO exact-symbolic bignum-carrier rows sharing ONE carrier-FFI marshal
# (cyclic → the_one; sigma-gosper → gosper). srmech_infer detects the row from
# the marshalled operand, dispatches + verifies the C reducer, emits the DECISION
# (the Python caller rebuilds closed_form via the same reducer; native == pure).
# The 5 heavier-carrier rows (wz / spectral / multivar / q / elliptic) fall to
# pure via non-OK (inform-don't-limit) → rc177+. → moved owed_orchestration →
# composes_c (owed 3→2, composes_c 82→83; sum stays 114). The 2 remaining owed =
# the tool_schema pair (get_tool_schema / tool_schema_view — host-glue MCP).
# rc177 (2026-07-08): the ANNEX — extend the ledger walk (_ROOTS) to srmech.bus +
# srmech.dsl (+39 rows: 18 bus + 21 dsl, all non_compute). The +39 split by kind:
# +10 owed_orchestration (the bus Bio-TOTP cipher stream kernel decode_splice /
# pipe + the DSL chain / class interpreter chain / run_toml_chain /
# lookup_cascade_op / build_chain_from_{dict,toml,toml_str} / make_class /
# run_class_method), +3 composes_c (bus connect / serve / channel_id_from_name),
# +12 host_glue (bus discovery/transport/registry-read + DSL catalog/class
# descriptor loaders), +14 dev_tooling (bus cipher-backend / secret-kwargs /
# asyncio-aio wrappers + DSL register/list introspection). Test-infra ONLY (no
# C, no compute-op change); CEIL_NON_COMPUTE_OWED 2 → 12; rc178+ build the annex
# to C + drive the owed count back down. owed 2→12 / composes_c 83→86 /
# host_glue 2→14 / dev_tooling 27→41; sum 114 → 153.
# rc178 (2026-07-08): ANNEX Batch A part 1 — the bus Bio-TOTP wire cipher earned
# its C peer (srmech_hmac_sha256 + srmech_bio_totp_derive_key / keystream_xor /
# decode_splice). decode_splice moved owed_orchestration → composes_c (the DEFAULT
# stdlib HMAC-CTR path is now a thin compose over srmech_sha256 + srmech_json; the
# AES-128-CTR `[crypto]` extra stays Python). owed 12 → 11, composes_c 86 → 87;
# sum stays 153. CEIL_NON_COMPUTE_OWED 12 → 11.
# rc180 (2026-07-08): ANNEX Batch A part 2b — the bus pub/sub earned its C peer
# (PAL mutex + srmech_bus_broadcast / subscribe / pubsub_accept /
# subscriber_count / pipe). The last owed bus row srmech.bus._pipe.pipe moved
# owed_orchestration → composes_c (it now composes the C subscribe + forward).
# BUS FULLY C. owed 11 → 10, composes_c 87 → 88; sum stays 153.
# CEIL_NON_COMPUTE_OWED 11 → 10. ABI 3 → 4.
# rc181 (2026-07-08): ANNEX Batch B part 1 — the DSL chain interpreter FOUNDATION
# earned its C peer (srmech_dsl_chain_run: the F1 carrier-FFI + leaf-dispatch table
# + build_chain_from_dict stage-IR + LINEAR chain.run over the C-backed atoms).
# lookup_cascade_op + build_chain_from_dict moved owed_orchestration → composes_c.
# owed 10 → 8, composes_c 88 → 90; sum stays 153. CEIL_NON_COMPUTE_OWED 10 → 8.
# rc182 (2026-07-08): ANNEX Batch B part 2 — the DSL chain interpreter is COMPLETE.
# The loop/fold/reduce COMBINATORS completing srmech_dsl_chain_run + the TOML
# front-end bridge srmech_dsl_toml_chain_to_json. chain (Chain.run) + run_toml_chain
# + build_chain_from_toml + build_chain_from_toml_str moved owed_orchestration →
# composes_c. owed 8 → 4, composes_c 90 → 94; sum stays 153. CEIL_NON_COMPUTE_OWED
# 8 → 4 (the 4 left = 2 tool_schema + make_class + run_class_method).
# rc183 (2026-07-08): the HOST-GLUE ANNEX — extend the ledger walk (_ROOTS) to
# srmech.mcp + srmech.cli + srmech.llm (+24 rows: 4 mcp + 17 cli + 3 llm). The +24
# split by kind: +11 owed_orchestration (the 4 MCP tool-serving ops + cli.main.main
# / build_parser + the 5 subcommand add_arguments), +9 composes_c (the cli.*.run /
# run_* dispatch bodies over the C bus / C DSL chain / owed serve+class ops),
# +1 host_glue (cli.status.run reads ~/.srmech FS), +3 dev_tooling (the srmech.llm
# Anthropic-agent surface — HONEST-DEFAULT pending a C-agent decision). Test-infra
# ONLY (no C, no compute-op change); CEIL_NON_COMPUTE_OWED 4 → 15; rc184+ build the
# MCP server + CLI dispatch to C + drive the owed count back down. owed 4→15 /
# composes_c 94→103 / host_glue 14→15 / dev_tooling 41→44; sum 153 → 177.
# rc185 (2026-07-08): the tool_schema PROJECTION ops in C (srmech_get_tool_schema /
# srmech_tool_schema_view / srmech_tool_entries_to_mcp_defs over the rc184 const
# table). The 2 tool_schema rows (get_tool_schema / tool_schema_view) + the mcp row
# (tool_entries_to_mcp_defs) moved owed_orchestration → composes_c. owed 15 → 12;
# composes_c 103 → 106; sum stays 177. CEIL_NON_COMPUTE_OWED 15 → 12.
# rc186 (2026-07-08): the MCP-server CONTROL SPINE — the JSON-RPC protocol +
# stdio LOOP in C (srmech_mcp_handle / srmech_mcp_serve_stdio / build_attestation
# over the rc185 tool-defs projection). serve_stdio moved owed_orchestration →
# composes_c: a bare-C host now serves initialize/tools-list/ping/shutdown natively
# (its loop + framing genuinely run in C; tools/call routes to the still-owed
# invoke_tool via inform-don't-limit). owed 12 → 11; composes_c 106 → 107; sum stays
# 177. CEIL_NON_COMPUTE_OWED 12 → 11. The 11 owed left = invoke_tool + serve_http_sse
# + the 2 CLI top-level dispatch ops + the 5 cli subcommand add_arguments + ... .
# rc188 (2026-07-09): the tools/call DISPATCH SPINE — srmech_invoke_tool (+ the
# parsed-args srmech_invoke_tool_json) makes MCP tools/call RUN in C for a clean
# 20-tool batch (registry_find → marshal_arg → signature-shape thunk table →
# serialise; the 383 no-single-kernel tools defer to the pure invoke_tool). invoke_tool
# moved owed_orchestration → composes_c. owed 11 → 10; composes_c 107 → 108; sum stays
# 177. CEIL_NON_COMPUTE_OWED 11 → 10. The 10 owed left = serve_http_sse + the 2 CLI
# top-level dispatch ops + the 5 cli subcommand add_arguments + make_class/run_class_method.
_EXPECTED_SPLIT = {
    "owed_orchestration": 10,
    "composes_c": 108,
    "host_glue": 15,
    "dev_tooling": 44,
}
_TOTAL_NON_COMPUTE = 177


def _rows():
    return [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _non_compute_kind_counts() -> Counter:
    return Counter(r["non_compute_kind"] for r in _rows()
                   if r.get("bucket") == "non_compute")


def test_non_compute_total_is_153():
    """The non_compute bucket is exactly 153 rows (rc177 annex population: the
    original 114 + the 39 bus/dsl rows the extended _ROOTS surfaces)."""
    n = sum(1 for r in _rows() if r.get("bucket") == "non_compute")
    assert n == _TOTAL_NON_COMPUTE, (
        f"non_compute bucket has {n} rows, expected {_TOTAL_NON_COMPUTE} — the "
        f"four-way split is pinned to this population; reconcile the split if a "
        f"non_compute op was added / removed."
    )


def test_kind_field_only_on_non_compute_rows():
    """Only ``non_compute`` rows carry a ``non_compute_kind`` — the sub-bucket is a
    property OF the non_compute bucket, not of the compute buckets."""
    misplaced = [r["defined_at"] for r in _rows()
                 if r.get("bucket") != "non_compute" and "non_compute_kind" in r]
    assert not misplaced, (
        f"{len(misplaced)} non-non_compute row(s) carry a non_compute_kind field "
        f"(remove it):\n  " + "\n  ".join(sorted(misplaced))
    )


def test_every_non_compute_row_has_a_kind_in_the_four():
    """Every non_compute row is sub-classified into exactly one of the four kinds
    (no row left unclassified — the split is a partition)."""
    bad = [r["defined_at"] for r in _rows()
           if r.get("bucket") == "non_compute"
           and r.get("non_compute_kind") not in _NON_COMPUTE_KINDS]
    assert not bad, (
        f"{len(bad)} non_compute row(s) have a missing / unknown non_compute_kind "
        f"(must be one of {_NON_COMPUTE_KINDS}):\n  " + "\n  ".join(sorted(bad))
    )


def test_four_way_split_sums_to_114():
    """The four sub-bucket counts partition the 114 non_compute rows exactly."""
    counts = _non_compute_kind_counts()
    # every counted kind is one of the four
    assert set(counts) <= set(_NON_COMPUTE_KINDS), (
        f"unexpected non_compute_kind values: {set(counts) - set(_NON_COMPUTE_KINDS)}"
    )
    assert dict(counts) == _EXPECTED_SPLIT, (
        f"the four-way split drifted: got {dict(counts)}, expected "
        f"{_EXPECTED_SPLIT}. Re-pin _EXPECTED_SPLIT (and the ceiling / allowlist) "
        f"if a non_compute op moved sub-bucket."
    )
    assert sum(counts.values()) == _TOTAL_NON_COMPUTE == sum(_EXPECTED_SPLIT.values()), (
        f"the four sub-buckets must sum to {_TOTAL_NON_COMPUTE}; got "
        f"{sum(counts.values())}."
    )


def test_owed_ceiling_is_tight():
    """CEIL_NON_COMPUTE_OWED equals the LIVE owed_orchestration count — the phase
    driver is pinned tight (a drop must lower it, a rise is a bare-C-host
    regression). Cross-checks the ledger against the ceiling constant."""
    live = set(rosetta_live_objects())
    live_owed = sum(1 for r in _rows()
                    if r.get("bucket") == "non_compute"
                    and r.get("non_compute_kind") == "owed_orchestration"
                    and r["defined_at"] in live)
    assert CEIL_NON_COMPUTE_OWED == live_owed == _EXPECTED_SPLIT["owed_orchestration"], (
        f"CEIL_NON_COMPUTE_OWED ({CEIL_NON_COMPUTE_OWED}) must equal the live "
        f"owed_orchestration count ({live_owed}) and the pinned "
        f"{_EXPECTED_SPLIT['owed_orchestration']}."
    )


def test_dev_tooling_allowlist_matches_the_split():
    """The pinned dev_tooling allowlist has exactly the dev_tooling count — the
    allowlist IS the dev_tooling sub-bucket (justified, never owed-C)."""
    assert len(NON_COMPUTE_DEV_TOOLING_EXEMPT) == _EXPECTED_SPLIT["dev_tooling"], (
        f"the dev_tooling allowlist has {len(NON_COMPUTE_DEV_TOOLING_EXEMPT)} "
        f"entries, expected {_EXPECTED_SPLIT['dev_tooling']}."
    )
    ledger_dev = {r["defined_at"] for r in _rows()
                  if r.get("bucket") == "non_compute"
                  and r.get("non_compute_kind") == "dev_tooling"}
    assert ledger_dev == set(NON_COMPUTE_DEV_TOOLING_EXEMPT), (
        "the ledger's dev_tooling rows and the pinned allowlist disagree:\n"
        f"  in ledger only: {sorted(ledger_dev - set(NON_COMPUTE_DEV_TOOLING_EXEMPT))}\n"
        f"  in allowlist only: {sorted(set(NON_COMPUTE_DEV_TOOLING_EXEMPT) - ledger_dev)}"
    )
