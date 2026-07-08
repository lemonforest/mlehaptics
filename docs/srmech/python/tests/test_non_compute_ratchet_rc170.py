"""The rc170 non_compute four-way-split ratchet — the orchestration→C phase.

The compute (CEIL_PYTHON_ONLY_DEBT=0), exact-algebra (CEIL_BIGNUM_REFERENCE=0)
and self-hosting (CEIL_C_EXISTS_UNBOUND=0) arcs are CLOSED. ``non_compute`` (the
last un-ceilinged bucket, 114 rows) is the honest next frontier: making a bare-C
host (no Python) run the WHOLE apparatus — dispatch, catalogs, IPC, the genome,
the chain-runner — in C.

This rc splits the 114 ``non_compute`` rows into FOUR honest sub-buckets (the
``non_compute_kind`` field in ``rosetta_classification.ndjson``) and pins the
split:

  owed_orchestration  (9) — genuine control/dispatch LOGIC a bare-C host needs;
                            owed-C, DOWN-ONLY (CEIL_NON_COMPUTE_OWED, the phase
                            driver, in test_rosetta_completeness.py). rc171: the
                            5 op_provenance verdict/carry ops earned C → composes_c.
                            rc172: 6 catalog registry/kernel/audit ops → composes_c.
  composes_c        (76) — thin: composes existing C, or a pure accessor /
                            constructor / validator; TRANSITIVE-REACHABILITY
                            assert (hides no Python kernel), not a ceiling.
  host_glue          (2) — filesystem / host I/O; tracked, no ceiling this rc.
  dev_tooling       (27) — a bare-C host never needs it; PINNED exempt allowlist.

This file proves the split is COMPLETE (sums to 114), DISJOINT, and TIGHT (the
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
_EXPECTED_SPLIT = {
    "owed_orchestration": 2,
    "composes_c": 83,
    "host_glue": 2,
    "dev_tooling": 27,
}
_TOTAL_NON_COMPUTE = 114


def _rows():
    return [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _non_compute_kind_counts() -> Counter:
    return Counter(r["non_compute_kind"] for r in _rows()
                   if r.get("bucket") == "non_compute")


def test_non_compute_total_is_114():
    """The non_compute bucket is exactly 114 rows (the population this rc splits)."""
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
