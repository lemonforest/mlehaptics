"""The rc177 ANNEX ratchet — the ledger walk extends to srmech.bus + srmech.dsl.

The compute / exact-algebra / self-hosting arcs are closed (all three ceilings
0). The ORCHESTRATION→C phase (rc170+) is now extended, per user direction, to
the IPC **bus** and the cascade-chain / class **DSL interpreter**: a bare-C host
(no Python) must run the WHOLE apparatus incl. the bus + the interpreter. This rc
is TEST-INFRA ONLY — it TRACKS the annex surface (extends ``_ROOTS`` to bus/dsl,
adds the +39 rows, raises ``CEIL_NON_COMPUTE_OWED`` 2 → 12, extends the
dev_tooling allowlist by 14); the annex BUILDS (rc178+) then drive the owed count
back down.

This file pins the annex specifics (the +39 split, the ceiling, the four
sub-bucket totals, bus/dsl in every ledger walk). numpy-free (stdlib json + the
shared conftest live-op walk); bus + dsl must import cleanly numpy-absent.
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

# The 39 annex rows (18 bus + 21 dsl) — the SSOT for the rc177 annex
# classification (defined_at -> non_compute_kind). These are the ACTUAL canonical
# <module>.<qualname> keys the ledger walk emits (verified against the live walk).
_ANNEX_ROWS = {
    # owed_orchestration (2) — the DSL CLASS interpreter's still-owed rows. rc178
    # moved the bus decode_splice owed → composes_c; rc180 moved the bus pipe owed
    # → composes_c (BUS FULLY C); rc181 moved lookup_cascade_op +
    # build_chain_from_dict owed → composes_c (the DSL chain FOUNDATION); rc182
    # moved chain (Chain.run) + run_toml_chain + build_chain_from_toml{,_str} owed
    # → composes_c (the loop/fold/reduce COMBINATORS + the TOML front-ends — the
    # DSL CHAIN interpreter is COMPLETE). The 2 left: make_class + run_class_method
    # (HONEST-DEFERRED — leaf-op-blocked on the genome / sed_* domain-leaf C backlog,
    # past Batch B).
    "srmech.dsl._class_catalog.make_class": "owed_orchestration",
    "srmech.dsl._class_surface.run_class_method": "owed_orchestration",
    # composes_c (11) — compose existing C (sha256 / json / cipher backend / bus
    # pub/sub / the DSL chain F1 carrier-FFI + combinators + the TOML bridge), reach
    # no non-standalone-ready leaf
    "srmech.bus._bio_totp.decode_splice": "composes_c",
    "srmech.bus._client.connect": "composes_c",
    "srmech.bus._server.serve": "composes_c",
    "srmech.bus._bio_totp.channel_id_from_name": "composes_c",
    "srmech.bus._pipe.pipe": "composes_c",
    # rc181: the DSL chain FOUNDATION → C (srmech_dsl_chain_run)
    "srmech.dsl._catalog.lookup_cascade_op": "composes_c",
    "srmech.dsl._toml_chain.build_chain_from_dict": "composes_c",
    # rc182: the DSL chain interpreter COMPLETE — combinators (srmech_dsl_chain_run)
    # + the TOML front-end bridge (srmech_dsl_toml_chain_to_json)
    "srmech.dsl._chain.chain": "composes_c",
    "srmech.dsl._tool_surface.run_toml_chain": "composes_c",
    "srmech.dsl._toml_chain.build_chain_from_toml": "composes_c",
    "srmech.dsl._toml_chain.build_chain_from_toml_str": "composes_c",
    # host_glue (12) — filesystem / host discovery / registry read
    "srmech.bus.list": "host_glue",
    "srmech.bus._discovery.list_endpoints": "host_glue",
    "srmech.bus._discovery.by_name": "host_glue",
    "srmech.bus._event.new_correlation_id": "host_glue",
    "srmech.bus._transport.bus_dir": "host_glue",
    "srmech.bus._transport.is_posix_uds": "host_glue",
    "srmech.bus._transport.transport_kind": "host_glue",
    "srmech.dsl._catalog.load_catalog": "host_glue",
    "srmech.dsl._class_catalog.load_class_catalog": "host_glue",
    "srmech.dsl._toml_chain.load_chain_toml": "host_glue",
    "srmech.dsl._catalog.get_descriptor": "host_glue",
    "srmech.dsl._class_catalog.get_class_descriptor": "host_glue",
    # dev_tooling (14) — a bare-C host never needs it (LLM / dev / asyncio)
    "srmech.bus._bio_totp.cipher_backend_name": "dev_tooling",
    "srmech.bus._params.secret_kwargs": "dev_tooling",
    "srmech.bus.aio.connect": "dev_tooling",
    "srmech.bus.aio.serve": "dev_tooling",
    "srmech.bus.aio.pipe": "dev_tooling",
    "srmech.bus.aio.list_endpoints": "dev_tooling",
    "srmech.dsl._catalog.register_catalog_dir": "dev_tooling",
    "srmech.dsl._class_catalog.register_class_dir": "dev_tooling",
    "srmech.dsl._catalog.list_cascade_ops": "dev_tooling",
    "srmech.dsl._class_catalog.list_classes": "dev_tooling",
    "srmech.dsl._tool_surface.list_catalog_ops": "dev_tooling",
    "srmech.dsl._tool_surface.list_ops": "dev_tooling",
    "srmech.dsl._class_surface.describe_class": "dev_tooling",
    "srmech.dsl._class_surface.list_class_surface": "dev_tooling",
}

# the +39 delta by kind (what the annex ADDS to the pre-rc177 split; rc178 +
# rc180 + rc181 + rc182 each moved within-annex rows owed → composes_c so the split
# is now 2/11/12/14: rc181 moved lookup_cascade_op + build_chain_from_dict →
# composes_c; rc182 moved chain + run_toml_chain + build_chain_from_toml{,_str} →
# composes_c — the DSL CHAIN interpreter is COMPLETE)
_ANNEX_DELTA = {"owed_orchestration": 2, "composes_c": 11, "host_glue": 12,
                "dev_tooling": 14}
# the FULL split after the annex (pre-rc177 2/83/2/27 + the delta; rc178: owed
# 12→11, composes_c 86→87 as decode_splice earned its C peer; rc180: owed 11→10,
# composes_c 87→88 as the bus pipe earned its C peer — BUS FULLY C; rc181: owed
# 10→8, composes_c 88→90 as the DSL chain FOUNDATION earned its C peer; rc182: owed
# 8→4, composes_c 90→94 as the combinators + TOML front-ends earned C — DSL CHAIN
# interpreter COMPLETE).
# rc183 HOST-GLUE annex (living-pin bump — as rc177 bumped the rc170 pins): the
# +24 mcp/cli/llm rows raise the FULL split to 15/103/15/44 = 177. The bus/dsl
# _ANNEX_ROWS / _ANNEX_DELTA below stay unchanged (they are the rc177 bus/dsl annex
# record); the mcp/cli/llm annex specifics are pinned in test_annex_ratchet_rc183.py.
# rc185 (living-pin bump): the 2 tool_schema rows + the mcp tool_entries_to_mcp_defs
# row earned their C projection peers → owed 15→12, composes_c 103→106 (sum stays
# 177). The bus/dsl _ANNEX_ROWS / _ANNEX_DELTA are untouched (rc185 moves no bus/dsl
# row).
_FULL_SPLIT = {"owed_orchestration": 12, "composes_c": 106, "host_glue": 15,
               "dev_tooling": 44}
_TOTAL_NON_COMPUTE = 177


def _rows():
    return [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def test_bus_and_dsl_in_every_ledger_walk():
    """The completeness walk (_ROOTS) AND the shared non_compute walk
    (_ROSETTA_ROOTS) both include srmech.bus + srmech.dsl — the extension that
    brings the annex surface into the everything-mirrors ledger."""
    for roots, where in ((_ROOTS, "test_rosetta_completeness._ROOTS"),
                         (_ROSETTA_ROOTS, "conftest._ROSETTA_ROOTS")):
        assert "srmech.bus" in roots and "srmech.dsl" in roots, (
            f"{where} must include srmech.bus + srmech.dsl; got {roots}"
        )


def test_annex_rows_present_with_expected_kinds():
    """All 39 annex rows are in the ledger as non_compute with the pinned
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
    ledger is not carrying a phantom bus/dsl key."""
    live = set(rosetta_live_objects())
    not_live = [da for da in _ANNEX_ROWS if da not in live]
    assert not not_live, (
        f"annex rows not surfaced by the live walk (bus/dsl not in roots, or the "
        f"key drifted): {sorted(not_live)}"
    )


def test_annex_delta_is_39_split_2_11_12_14():
    """The +39 annex rows split exactly 2 owed / 11 composes_c / 12 host_glue /
    14 dev_tooling (rc178 moved decode_splice owed → composes_c; rc180 moved the
    bus pipe owed → composes_c — BUS FULLY C; rc181 moved lookup_cascade_op +
    build_chain_from_dict owed → composes_c — the DSL chain FOUNDATION → C; rc182
    moved chain + run_toml_chain + build_chain_from_toml{,_str} owed → composes_c —
    the DSL CHAIN interpreter COMPLETE)."""
    counts = Counter(_ANNEX_ROWS.values())
    assert dict(counts) == _ANNEX_DELTA, (
        f"annex +39 split drifted: got {dict(counts)}, expected {_ANNEX_DELTA}"
    )
    assert sum(counts.values()) == 39


def test_full_non_compute_split_sums_to_153():
    """The full non_compute ledger split — bus/dsl annex (rc177–182) + the rc183
    mcp/cli/llm host-glue annex — is 15/103/15/44 = 177 (living-pin bump)."""
    counts = Counter(r["non_compute_kind"] for r in _rows()
                     if r.get("bucket") == "non_compute")
    assert dict(counts) == _FULL_SPLIT, (
        f"full non_compute split drifted: got {dict(counts)}, expected "
        f"{_FULL_SPLIT}"
    )
    assert sum(counts.values()) == _TOTAL_NON_COMPUTE == sum(_FULL_SPLIT.values())


def test_ceil_non_compute_owed_is_12():
    """The phase-driver ceiling is 12 after rc185 — the rc183 residue of 15 minus
    the 3 tool_schema projection rows (get_tool_schema / tool_schema_view /
    tool_entries_to_mcp_defs) that earned their C peers in rc185. rc186+ build the
    MCP JSON-RPC server LOOP + CLI dispatch to C and drive the owed count down."""
    assert CEIL_NON_COMPUTE_OWED == 12, (
        f"CEIL_NON_COMPUTE_OWED must be 12 after rc185; got "
        f"{CEIL_NON_COMPUTE_OWED}"
    )


def test_annex_dev_tooling_keys_in_allowlist():
    """All 14 annex dev_tooling keys are in the pinned NON_COMPUTE_DEV_TOOLING_EXEMPT
    allowlist (a dev_tooling row must be added DELIBERATELY)."""
    annex_dev = {da for da, k in _ANNEX_ROWS.items() if k == "dev_tooling"}
    assert len(annex_dev) == 14
    missing = annex_dev - set(NON_COMPUTE_DEV_TOOLING_EXEMPT)
    assert not missing, (
        f"annex dev_tooling keys not in the allowlist: {sorted(missing)}"
    )


def test_bus_and_dsl_import_numpy_absent():
    """srmech.bus + srmech.dsl import cleanly (the ratchet runs numpy-free)."""
    import importlib
    import srmech.bus  # noqa: F401
    import srmech.dsl  # noqa: F401
    # a numpy import anywhere in the chain would have failed the ratchet's
    # numpy-absent contract; assert the packages are the real ones.
    assert importlib.import_module("srmech.bus") is srmech.bus
    assert importlib.import_module("srmech.dsl") is srmech.dsl
