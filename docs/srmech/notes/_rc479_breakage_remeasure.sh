#!/bin/bash
# rc479 (`#T1188`) — GENERATING CODE for the CHANGELOG's
# "THE BREAKAGE, CLASSIFIED AND RESTATED — 43 FAILURES OVER SIX FILES" table.
#
# WHY IT EXISTS. That heading first read "45 FAILURES" over a table summing to
# 51 (29 + 18 + 1 + 1 + 2). Both figures came from a running tally kept while
# the restatements were being written, not from one run — so neither could be
# reproduced and they did not agree with each other. A heading a reader can
# disprove with addition is a measurement claim with no measurement behind it.
#
# WHAT STATE IS MEASURED, and why that one. `53ee85b9b` is the commit where
# contract A's reader is IN, the five reader rules and three guards are IN, the
# declarations are widened, and NOT ONE loader gate has been restated. That is
# precisely "the breakage contract A causes", before any of it is answered. A
# commit earlier would miss the reader rules' own ripple; a commit later would
# be measuring the repairs.
#
# THE CELL. PURE — no .so / .pyd / .dll / .pyc / __pycache__ / *.dist-info —
# with SRMECH_EXPECT_PURE=1 declared, numpy absent, PYTHONDONTWRITEBYTECODE=1,
# foreground under `timeout`, whole files, never a `-k` filter. The version on
# the line at that commit is 0.9.0rc478 (the SSoT bump lands later in the
# release), which is printed rather than assumed.
#
# HOW TO RE-RUN IT (from the repo, any checkout that has the commit):
#   git archive --format=tar -o /tmp/tree53.tar 53ee85b9b docs/srmech
#   bash docs/srmech/notes/_rc479_breakage_remeasure.sh /tmp/tree53.tar
#
# MEASURED OUTPUT, 2026-09-21, CPython 3.12.3, WSL2:
#
#   version 0.9.0rc478
#   HAS_NATIVE False
#   43 failed, 288 passed, 114 skipped in 24.68s
#
#   by file (six of the nine carry a failure; three are clean):
#     test_json_read_selfhost_rc401.py   36
#       test_corpus_json_file_parity[row.schema.json1..5]            5
#       test_corpus_ndjson_line_parity                               1
#       test_battery_value_parity[float …]                          11
#       test_float_bit_exact[…]                                     18
#       test_pure_floor_is_reachable_and_correct                     1
#     test_toml_dedup_parity_rc400.py     1   test_corpus_parity_pure
#     test_dsl_catalog_selfhost_rc392.py  1   test_cascade_catalog_self_hosts_to_the_same_registry
#     test_format.py                      1   test_mpr_record_round_trip_through_json_line
#     test_exact_carrier_drain_rc466.py   3   the float-carrier election + the TWO declared-return rows
#     test_wire_round_trip_rc414.py       1   test_carriers_round_trip_over_the_wire
#     test_toml_selfhost_parity_rc391.py  0
#     test_adapters.py                    0
#     test_attestation_of_record_rc418.py 0
#
#   The CHANGELOG's class partition is those node ids grouped, and it sums to
#   43 by construction rather than by assertion.
#
# WHAT THIS DOES NOT MEASURE. The six `TypeError: Object of type Q is not JSON
# serializable` rows and the fifteen rc420 chain-vs-op pairs were fixed at root
# in commits BEFORE `53ee85b9b`, so a run here cannot see them; they are
# recorded in the CHANGELOG separately and are not part of the 43. The nine
# files are the loader-touching candidates, not a predicate-derived population
# — the predicate-derived population is 138 files and running it is the ripple
# gate's job, not this one's.
set -e
TAR=${1:-/mnt/c/Users/sckir/AppData/Local/Temp/rc479stage/tree53.tar}
SRC=/tmp/rc479_53
rm -rf $SRC
mkdir -p $SRC
tar -xf "$TAR" -C $SRC
cd $SRC/docs/srmech/python
echo "--- banner (printed, not assumed) ---"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$SRC/docs/srmech/python python3 -c \
  "import srmech; print('version', srmech.__version__); import srmech._native as n; print('HAS_NATIVE', n.HAS_NATIVE)"
echo "--- nine loader-touching gate files, whole files, no -k ---"
PYTHONDONTWRITEBYTECODE=1 SRMECH_EXPECT_PURE=1 \
  PYTHONPATH=$SRC/docs/srmech/python \
  timeout 2400 python3 -m pytest \
    tests/test_json_read_selfhost_rc401.py \
    tests/test_toml_selfhost_parity_rc391.py \
    tests/test_toml_dedup_parity_rc400.py \
    tests/test_dsl_catalog_selfhost_rc392.py \
    tests/test_format.py \
    tests/test_adapters.py \
    tests/test_exact_carrier_drain_rc466.py \
    tests/test_wire_round_trip_rc414.py \
    tests/test_attestation_of_record_rc418.py \
    -q --no-header -p no:cacheprovider 2>&1 | grep -E "^FAILED|passed|failed"
