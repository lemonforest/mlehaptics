#!/bin/bash
# rc473 instrument repair 3 (`#T1188`): the can-fail runs behind the repair's CHANGELOG figures.
#
# Usage (WSL2):
#   bash notes/_rc473_instr_r3_canfail.sh <group> <native clone root> <pure clone root>
# groups: probe manifest runner old_tests figures
#
# Clones and conditions as notes/_rc473_instr_r2_canfail.sh: git CLONES whose `.git` is a directory,
# detached at the commit under test with 0 tracked changes; the pure clone holds no library. The
# groups run on the files AT that commit, so the same group run at gate round j1's head (337258f71)
# and at this repair measures the defect and the fix. Plants come from notes/_rc473_instr_plants.py,
# each exact-once; every restore is `git checkout -- docs/srmech` with the count printed.
# Refuses a root under /mnt and an exported GIT_DIR / GIT_WORK_TREE. PYTEST_ADDOPTS and
# PYTEST_PLUGINS are unset here. numpy absent; SRMECH_ALLOW_STALE_NATIVE unset.
set -u
GROUP=${1:?group}; R=${2:?native clone}; PURE=${3:?pure clone}
export PATH="$HOME/.local/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE SRMECH_EXPECT_PURE PYTEST_ADDOPTS PYTEST_PLUGINS
n=$(env | grep -c -E '^GIT_(DIR|WORK_TREE)=')
echo "group $GROUP  exported GIT_DIR/GIT_WORK_TREE: $n  live .git/config $(sha256sum /mnt/d/GitHub/mlehaptics/.git/config | cut -c1-16)  $(date -u +%FT%TZ)"
[ "$n" = 0 ] || { echo "REFUSED: exported GIT_DIR/GIT_WORK_TREE"; exit 2; }
for root in "$R" "$PURE"; do
  case "$root" in /mnt/*) echo "REFUSED: $root is under /mnt"; exit 2;; esac
  [ -d "$root/.git" ] || { echo "REFUSED: $root/.git is not a directory"; exit 2; }
  echo "$root HEAD $(git -C "$root" rev-parse HEAD) tracked changes $(git -C "$root" status --porcelain --untracked-files=no | wc -l) libs $(find "$root/docs/srmech/python" -name 'libsrmech*' | wc -l)"
done
UV="uv run --no-project --offline"
NOTES=$PURE/docs/srmech/notes
J1=337258f71                                   # gate round j1's head: the instrument this repair changes
I2=c13529f73                                   # instrument repair 1's record head (the plugin B2 names)
T=/tmp/ir3_$GROUP; rm -rf "$T"; mkdir -p "$T"
plant() { $UV --python 3.12 python "$NOTES/_rc473_instr_plants.py" "$1/docs/srmech" "${@:2}"; }
restore() { git -C "$1" checkout -- docs/srmech; echo "  restored: tracked changes $(git -C "$1" status --porcelain --untracked-files=no | wc -l)"; }
pt() { # <tag> <env assignments or -> <pytest args...>   (pure clone, CPython 3.12)
  local tag=$1 envs=$2; shift 2; [ "$envs" = - ] && envs=""
  local t0; t0=$(date +%s%N)
  (cd "$PURE/docs/srmech/python" && env $envs timeout 900 $UV --python 3.12 --with pytest python -m pytest -q -p no:cacheprovider -rfEs "$@" > "$T/$tag.log" 2>&1)
  echo "  [$tag] exit $? in $(( ($(date +%s%N) - t0) / 1000000 )) ms: $(tail -1 "$T/$tag.log")"
  grep -E '^(FAILED|ERROR)' "$T/$tag.log" | cut -c1-200 | head -8
  grep -E "^\[rc473\] collection" "$T/$tag.log" | sed -E 's/^.*(missing [0-9]+, items .*)$/      \1/'
}
runner() { # <tag> <env assignments or -> <ripple_check args...>   (pure clone, CPython 3.12)
  local tag=$1 envs=$2; shift 2; [ "$envs" = - ] && envs=""
  local t0; t0=$(date +%s%N)
  (cd "$PURE/docs/srmech/python" && env $envs timeout 900 $UV --python 3.12 --with pytest python tools/ripple_check.py "$@" > "$T/$tag.log" 2>&1)
  echo "  [$tag] exit $? in $(( ($(date +%s%N) - t0) / 1000000 )) ms"
  grep -E "REFUSED|FAILED --|red --|collection kept|ran all|by node id|[0-9]+ (passed|failed|deselected|skipped)|no tests ran" "$T/$tag.log" | cut -c1-260 | sed 's/^/      /' | tail -5
}
MT=tests/test_ripple_manifest_covers_known_gates.py
COLL="$MT::test_the_manifest_collects_every_test_function_each_frozen_file_defines"
ADV=tests/test_git_export_advice_absent_rc473.py
M=$T/manifest.txt; printf '%s\n' "$ADV" > "$M"
# the two geometries gate round j1 measured, in the real tree
J1_PLANTS="M_dup_conftest M_conftest_setuponly M_ini_setup_plan M_ini_setup_only"
export SRMECH_EXPECT_PURE=1
PLUG=$PURE/docs/srmech/python/tests/_collection_count_plugin.py
RCHK=$PURE/docs/srmech/python/tools/ripple_check.py
has_ids=$(grep -c 'or ran != collected or off:' "$RCHK")
has_call=$(grep -c 'report.when == "call" or' "$PLUG")
echo "this tree: id-comparison lines $has_ids, call-phase ran lines $has_call"

case $GROUP in
probe)
  git -C "$PURE" show "$J1:docs/srmech/python/tests/_collection_count_plugin.py" > "$T/j1_plugin.py"
  git -C "$PURE" show "$J1:docs/srmech/python/tools/ripple_check.py" > "$T/j1_ripple_check.py"
  git -C "$PURE" show "$I2:docs/srmech/python/tests/_collection_count_plugin.py" > "$T/i2_plugin.py"
  for which in j1 tree; do
    if [ "$which" = tree ]; then PL=$PLUG; RC=$RCHK; else PL=$T/j1_plugin.py; RC=$T/j1_ripple_check.py; fi
    for v in 3.12 3.10; do
      echo "== the ir3 sandbox over the $which plugin ($(sha256sum "$PL" | cut -c1-16)) and runner ($(sha256sum "$RC" | cut -c1-16)), CPython $v"
      (cd "$T" && timeout 900 $UV --python $v --with pytest python "$NOTES/_rc473_instr_r3_probe.py" "$PL" "$RC" > "$T/r3_${which}_$v.log" 2>&1)
      echo "  exit $?: $(head -1 "$T/r3_${which}_$v.log")"
      grep -E "pytest exit|judge_counts ->" "$T/r3_${which}_$v.log" | cut -c1-200 | sed 's/^/    /'
    done
  done
  echo "== instrument repair 2's sandbox over this tree's plugin: its rows must be unchanged"
  (cd "$T" && timeout 900 $UV --python 3.12 --with pytest python "$NOTES/_rc473_instr_r2_order_probe.py" "$PLUG" > "$T/r2_tree.log" 2>&1)
  echo "  exit $?"
  awk '/collect-only exit/ {name=$1; co=($0 ~ /meta-test predicate SEEN/) ? "SEEN" : "not-seen"} /runner predicate/ {r=($0 ~ /runner predicate SEEN/) ? "SEEN" : "not-seen"; s=$0; sub(/^.*\| /, "", s); printf "    %-42s collect-only %-9s run %-9s | %s\n", name, co, r, s}' "$T/r2_tree.log"
  echo "== the five rows gate round j1 disclosure B2 names, over the $I2 plugin ($(sha256sum "$T/i2_plugin.py" | cut -c1-16))"
  (cd "$T" && timeout 900 $UV --python 3.12 --with pytest python "$NOTES/_rc473_instr_r2_order_probe.py" "$T/i2_plugin.py" collection_finish_trylast collection_finish_trylast_ENV runtestloop_wrapper_before_yield runtestloop_wrapper_before_yield_ENV runtest_protocol_returns_true > "$T/r2_i2_five.log" 2>&1)
  echo "  exit $?"
  grep -E "collect-only exit|run exit" "$T/r2_i2_five.log" | cut -c1-190 | sed 's/^/    /'
  ;;
manifest)
  echo "== head, the whole meta-test"; pt m_head - $MT -s
  for p in $J1_PLANTS; do
    echo "== $p"; plant "$PURE" "$p"; pt "m_$p" - "$COLL" -s; restore "$PURE"
  done
  ;;
runner)
  echo "== head, manifest: $ADV"; runner r_head - --manifest "$M"
  for p in $J1_PLANTS; do
    echo "== $p"; plant "$PURE" "$p"; runner "r_$p" - --manifest "$M"; restore "$PURE"
  done
  echo "== instrument repair 2's plants, which must still red"
  for p in M_wrapper_old_before_yield M_finish_trylast; do
    echo "== $p"; plant "$PURE" "$p"; runner "r_$p" - --manifest "$M"; restore "$PURE"
  done
  if [ "$has_ids" = 1 ]; then
    echo "== M_dup_conftest under R_ids_check_off (the id comparison removed)"
    plant "$PURE" R_ids_check_off; plant "$PURE" M_dup_conftest
    runner r_dup_ids_off - --manifest "$M"; restore "$PURE"
  fi
  if [ "$has_call" = 1 ]; then
    echo "== M_ini_setup_plan under P_ran_setup_reports (instrument repair 2's ran rule written back)"
    plant "$PURE" P_ran_setup_reports; plant "$PURE" M_ini_setup_plan
    runner r_setupplan_ran_off - --manifest "$M"; restore "$PURE"
  fi
  ;;
old_tests)
  N="$MT::test_the_runner_refuses_forwarded_options_that_narrow_the_gate_run $MT::test_the_runner_fails_a_green_run_whose_collection_lost_items $MT::test_the_collection_count_plugin_reports_the_planted_removals"
  echo "== the runner and plugin tests, this tree"; pt o_tree - $N
  echo "== the same tests with the $J1 runner and plugin written in"
  plant "$PURE" revert "$J1" python/tools/ripple_check.py python/tests/_collection_count_plugin.py
  pt o_j1 - $N; restore "$PURE"
  ;;
figures)
  P=$PURE/docs/srmech/python
  echo "== B5: every form count this gate's grep roots hold, and every one the CHANGELOG holds"
  grep -rn -i -E "(eight|thirteen|[0-9]+) (phrase )?forms" "$P/tools" "$P/tests" "$P/srmech" "$PURE/docs/srmech/notes" --include='*.py' --include='*.txt' --include='*.md' --include='*.sh' --include='*.json' | sed "s|$PURE/docs/srmech/||" | cut -c1-200
  echo "  --- the same pattern over the CHANGELOG, which that grep does not read:"
  grep -n -i -E "(eight|thirteen) (phrase )?forms" "$P/CHANGELOG.md" | cut -c1-200
  echo "== B4: how far instrument repair 2's Q4 sweep reached over this CHANGELOG range"
  git -C "$PURE" show "$I2:docs/srmech/python/CHANGELOG.md" > "$T/changelog_$I2.md"
  $UV --python 3.12 python "$NOTES/_rc473_scratch/ir3/sweep_reach.py" "$T/changelog_$I2.md" 1527 1866 lines
  ;;
*) echo "unknown group $GROUP"; exit 2;;
esac
for root in "$R" "$PURE"; do echo "$root tracked changes at end $(git -C "$root" status --porcelain --untracked-files=no | wc -l)"; done
echo "end live .git/config $(sha256sum /mnt/d/GitHub/mlehaptics/.git/config | cut -c1-16)  $(date -u +%FT%TZ)"
