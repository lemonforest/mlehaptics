#!/bin/bash
# rc473 instrument round (`#T1188`): the WSL2 half of the dated validation of a pushed head.
#
# Usage (WSL2):
#   bash notes/_rc473_instr_validate.sh <step> <native clone root> <pure clone root> [arg]
# steps:
#   build <fresh build dir under $HOME>   CLEAN gcc pedantic Release, ctest, library installed, authenticated
#   gates <1..5> <native|pure>            one foreground pytest per named group and cell (below)
#   hook                                  the derived-ledger Stop hook against both committed ledgers
#   d1d2                                  D1 (winding_fold) and D2 (kepler slots + tolerance frontier)
#   ripple_split <n> | ripple_part <i>    the whole manifest in n parts through tools/ripple_check.py
#   census_pure | census_native | census_diff   the demotion census from an EMPTY manifest
#   check_hooks                           tools/hooks/check_hooks.py, every check
#   regen                                 tools/regen_all.py --check
# Both roots are git clones (`.git` a directory) at the commit under test; the pure clone holds no
# library. Refuses a root under /mnt and an exported GIT_DIR / GIT_WORK_TREE. numpy absent; CPython
# under `uv run --no-project --offline`; SRMECH_ALLOW_STALE_NATIVE unset.
set -u
STEP=${1:?step}; R=${2:?native clone}; PURE=${3:?pure clone}; ARG=${4:-}; ARG2=${5:-}
export PATH="$HOME/.local/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE SRMECH_EXPECT_PURE
n=$(env | grep -c -E '^GIT_(DIR|WORK_TREE)=')
echo "step $STEP $ARG $ARG2  exported GIT_DIR/GIT_WORK_TREE: $n  $(date -u +%FT%TZ)"
[ "$n" = 0 ] || { echo "REFUSED: exported GIT_DIR/GIT_WORK_TREE"; exit 2; }
for root in "$R" "$PURE"; do
  case "$root" in /mnt/*) echo "REFUSED: $root is under /mnt"; exit 2;; esac
  [ -d "$root/.git" ] || { echo "REFUSED: $root/.git is not a directory"; exit 2; }
  echo "$root HEAD $(git -C "$root" rev-parse HEAD) tracked changes $(git -C "$root" status --porcelain --untracked-files=no | wc -l) libs $(find "$root/docs/srmech/python" -name 'libsrmech*' | wc -l)"
done
UV="uv run --no-project --offline"
NOTES=$R/docs/srmech/notes
OUT=$HOME/rc473c/out/ir_validate; mkdir -p "$OUT"
auth() { (cd "$1/docs/srmech/python" && $UV --python 3.12 python "$NOTES/_rc473_instr_auth.py" "$PWD" | grep -E "python |_native.__file__|HAS_NATIVE|numpy|lib sha256|abi / c|AUTH"); }
G1="test_value_status_c_boundary_rc473 test_kepler_non_finite_slots_rc473 test_winding_fold_rc215 test_kepler_parity test_eph_propagate_wound_rc207 test_jpl_audit test_rc473_a6_phrase_gate_runs test_adr_citation_integrity_rc415 test_adr_clause_instrument_rc417"
G2="test_search_glyph_tokenizer_rc416 test_introspect_search_rc411 test_worked_examples_execute_rc354 test_worked_examples_strict_zero_rc353 test_synth_args_provenance_rc430 test_ledger_freshness_hook_rc468 test_abi_pin_sites_agree_rc464 test_abi_prose_currency_rc449 test_ref_notation_emitted_rc348"
G3="test_eoc_q61_parity_rc472 test_c_cascade_value_parity_rc450 test_t1146_rejection_parity_rc447 test_t1158_refusal_set_equality_rc449 test_c_fold_step_form_rc446 test_c_cascade_coherence test_status_conflation_ratchet_rc404 test_regen_all_rc346 test_tool_registry_c_rc184 test_r3_reader_rc470 test_ripple_manifest_covers_known_gates"
G4="test_git_env_cannot_reach_a_repository_rc473 test_kepler_identity_phrases_absent_rc473 test_curated_line_citations_resolve_rc473 test_hook_fixture_env_isolation_rc471 test_ledger_write_refusals_rc469 test_shell_line_loop_rc468 test_figure_run_rc471 test_registry_completeness_rc416 test_assert_contract_gate_rc433 test_pypi_readme_changelog"
G5="test_git_export_advice_absent_rc473"

case $STEP in
build)
  B=$ARG
  case "$B" in "$HOME"/rc473c/build_*) ;; *) echo "REFUSED: build dir must be $HOME/rc473c/build_*"; exit 2;; esac
  echo "gcc: $(gcc --version | head -1)  cmake: $(cmake --version | head -1)  ninja $(ninja --version)"
  rm -rf "$B"
  cmake -S "$R/docs/srmech" -B "$B" -G Ninja -DCMAKE_BUILD_TYPE=Release -DSRMECH_PEDANTIC=ON > "$OUT/configure.log" 2>&1
  echo "configure exit $?  $(grep -o 'SRMECH_PEDANTIC=ON[^"]*' "$OUT/configure.log" | head -1)"
  cmake --build "$B" -- -k 0 > "$OUT/build.log" 2>&1
  echo "build exit $?  warnings: $(grep -c 'warning:' "$OUT/build.log")  errors: $(grep -c 'error:' "$OUT/build.log")  last: $(tail -1 "$OUT/build.log" | cut -c1-40)"
  echo "-Werror in build.ninja: $(grep -o -- '-Werror' "$B/build.ninja" | wc -l)  nm __assert_fail: $(nm -D "$B/libsrmech.so" | grep -c __assert_fail)"
  echo "lib $(sha256sum "$B/libsrmech.so" | cut -c1-16)"
  (cd "$B" && ctest 2>&1 | tail -3)
  cp "$B/libsrmech.so" "$R/docs/srmech/python/srmech/_native/"
  auth "$R"
  ;;
gates)
  case $ARG in 1) NAMES=$G1;; 2) NAMES=$G2;; 3) NAMES=$G3;; 4) NAMES=$G4;; 5) NAMES=$G5;; *) echo "group 1..5"; exit 2;; esac
  if [ "$ARG2" = pure ]; then P=$PURE/docs/srmech/python; export SRMECH_EXPECT_PURE=1; else P=$R/docs/srmech/python; auth "$R"; fi
  FILES=""; NF=0
  for f in $NAMES; do if [ -f "$P/tests/$f.py" ]; then FILES="$FILES tests/$f.py"; NF=$((NF + 1)); else echo "MISSING tests/$f.py"; fi; done
  echo "group $ARG cell $ARG2 files $NF:$FILES"
  LOG=$OUT/g${ARG}_${ARG2}.log
  (cd "$P" && timeout 590 $UV --python 3.12 --with pytest python -m pytest -q -p no:cacheprovider -rfEXs $FILES > "$LOG" 2>&1)
  echo "pytest exit $?: $(tail -1 "$LOG")"
  grep -E "^(FAILED|ERROR|XPASS)" "$LOG" | cut -c1-240 | head -20
  echo "XFAIL lines: $(grep -c '^XFAIL' "$LOG")  SKIPPED lines: $(grep -c '^SKIPPED' "$LOG")"
  [ "$ARG" -ge 4 ] && grep -E "^SKIPPED" "$LOG" | cut -c1-200 | sort | uniq -c
  ;;
hook)
  P=$R/docs/srmech/python
  for l in worked_examples_result example_args_ledger; do echo "$l rows $(grep -c -v '"record": "meta"' "$P/tests/$l.ndjson")"; done
  for i in 1 2; do
    t0=$(date +%s%N)
    err=$(cd "$P" && echo '{"hook_event_name":"Stop"}' | CLAUDE_PROJECT_DIR=$R $UV --python 3.12 python tools/hooks/derived_ledger_freshness.py 2>&1 >/dev/null); c=$?
    echo "  hook exit $c ($(( ($(date +%s%N) - t0) / 1000000 )) ms, uv start included) stderr lines $(printf '%s' "$err" | grep -c .)"
    printf '%s\n' "$err" | cut -c1-200 | head -8
  done
  ;;
d1d2)
  NP=$R/docs/srmech/python; PP=$PURE/docs/srmech/python; O=$OUT/d1d2; rm -rf "$O"; mkdir -p "$O"
  auth "$R"
  echo "=== D2 slot sweep"
  $UV --python 3.12 python "$NOTES/_rc473_twin_d2_slot_sweep.py" "$NP" "$O/slots_native.json" > "$O/slots_native.txt" 2>&1; echo "native exit $?"
  SRMECH_EXPECT_PURE=1 $UV --python 3.12 python "$NOTES/_rc473_twin_d2_slot_sweep.py" "$PP" "$O/slots_pure.json" > "$O/slots_pure.txt" 2>&1; echo "pure exit $?"
  $UV --python 3.12 python "$NOTES/_rc473_twin_d2_diff.py" "$O/slots_native.json" "$O/slots_pure.json" | tail -3
  echo "=== D2 tolerance frontier"
  $UV --python 3.12 python "$NOTES/_rc473_twin_d2_tol_frontier.py" "$NP" "$O/front_native.json" > "$O/front_native.txt" 2>&1; echo "native exit $?"
  SRMECH_EXPECT_PURE=1 $UV --python 3.12 python "$NOTES/_rc473_twin_d2_tol_frontier.py" "$PP" "$O/front_pure.json" > "$O/front_pure.txt" 2>&1; echo "pure exit $?"
  $UV --python 3.12 python "$NOTES/_rc473_twin_d2_diff.py" "$O/front_native.json" "$O/front_pure.json" | tail -3
  echo "=== D1: 24 filed + 21 further named + 40000 fuzzed, at the symbol and through the wrapper"
  $UV --python 3.12 python "$NOTES/_rc473_twin_d1_dump.py" "$NP" "$O/d1.json" 40000 | tail -5
  SRMECH_EXPECT_PURE=1 $UV --python 3.12 python "$NOTES/_rc473_twin_d1_analyze.py" "$PP" after "$O/d1.json" | tail -8
  ;;
ripple_split)
  PARTS=$OUT/rparts; rm -rf "$PARTS"
  (cd "$R/docs/srmech/python" && $UV --python 3.12 python "$NOTES/_rc473_scratch/m_ripple_split.py" tools/ripple_gates.txt "$ARG" "$PARTS")
  ;;
ripple_part)
  PARTS=$OUT/rparts; auth "$R"
  echo "targets in part $ARG: $(grep -c . "$PARTS/ripple_part$ARG.txt")"
  (cd "$R/docs/srmech/python" && timeout 590 $UV --python 3.12 --with pytest python tools/ripple_check.py --manifest "$PARTS/ripple_part$ARG.txt" > "$OUT/ripple_part$ARG.log" 2>&1)
  echo "ripple_check exit $?"
  grep -E "^(FAILED|ERROR) " "$OUT/ripple_part$ARG.log" | cut -c1-240 | head -20
  tail -2 "$OUT/ripple_part$ARG.log"
  ;;
census_pure|census_native|census_diff)
  CEN=$OUT/census_regen.ndjson
  RUN='import sys, time
from pathlib import Path
sys.path.insert(0, "tools")
import demotion_probe as d
from srmech import _native as n
print("HAS_NATIVE", n.HAS_NATIVE, n.__file__, "cell", d.cell())
t = time.time()
m = d.merge_cell(Path(sys.argv[1]), progress=False)
print("seconds %.1f" % (time.time() - t))
print({k: m.get(k) for k in ("n_rows", "n_ops", "cells_measured", "by_verdict")})'
  if [ "$STEP" = census_pure ]; then
    cd "$PURE/docs/srmech/python"; rm -f "$CEN"; echo "manifest before: $(test -f "$CEN" && echo PRESENT || echo EMPTY)"
    PYTHONPATH=$PWD SRMECH_EXPECT_PURE=1 timeout 590 $UV --python 3.12 python -c "$RUN" "$CEN" 2>&1 | tail -4
  elif [ "$STEP" = census_native ]; then
    auth "$R"; cd "$R/docs/srmech/python"
    PYTHONPATH=$PWD timeout 590 $UV --python 3.12 python -c "$RUN" "$CEN" 2>&1 | tail -4
  else
    cd "$R/docs/srmech/python"; git -C "$R" show HEAD:docs/srmech/python/tests/demotion_census.ndjson > "$OUT/census_committed.ndjson"
    $UV --python 3.12 python tools/census_regen_diff.py "$OUT/census_committed.ndjson" "$CEN" 2>&1 | tail -40
  fi
  ;;
check_hooks)
  t0=$(date +%s%N)
  (cd "$R/docs/srmech/python" && CLAUDE_PROJECT_DIR=$R timeout 590 $UV --python 3.12 --with pytest python tools/hooks/check_hooks.py > "$OUT/check_hooks.log" 2>&1)
  echo "check_hooks exit $? in $(( ($(date +%s%N) - t0) / 1000 / 1000 )) ms"
  grep -E "\[FAIL\]|\[SKIP\]|passed, " "$OUT/check_hooks.log" | cut -c1-220
  ;;
regen)
  auth "$R"
  (cd "$R/docs/srmech/python" && timeout 590 $UV --python 3.12 python tools/regen_all.py --check 2>&1 | tail -3)
  ;;
*) echo "unknown step $STEP"; exit 2;;
esac
for root in "$R" "$PURE"; do echo "$root tracked changes at end $(git -C "$root" status --porcelain --untracked-files=no | wc -l)"; done
echo "end $(date -u +%FT%TZ)"
