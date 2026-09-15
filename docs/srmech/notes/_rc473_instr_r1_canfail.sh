#!/bin/bash
# rc473 instrument repair 1 (`#T1188`): the can-fail runs behind the repair's CHANGELOG figures.
#
# Usage (WSL2):
#   bash notes/_rc473_instr_r1_canfail.sh <group> <native clone root> <pure clone root> [<build dir>]
# groups: runner_new runner_old manifest advice hook kepler figures
#
# The clones and conditions are those of notes/_rc473_instr_canfail.sh: git CLONES whose `.git`
# is a directory, detached at the commit under test with 0 tracked changes; the native clone holds
# the library built from it, the pure clone none. Plants come from notes/_rc473_instr_plants.py,
# each exact-once; "old" is a file as of 20bda4ffe (the instrument round's head), written in by
# `plants.py revert`; every restore is `git checkout -- docs/srmech` with the count printed.
# Refuses a root under /mnt and an exported GIT_DIR / GIT_WORK_TREE. PYTEST_ADDOPTS is unset here
# and set only where a run names it. numpy absent; SRMECH_ALLOW_STALE_NATIVE unset.
set -u
GROUP=${1:?group}; R=${2:?native clone}; PURE=${3:?pure clone}; BUILD=${4:-}
export PATH="$HOME/.local/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE SRMECH_EXPECT_PURE PYTEST_ADDOPTS
n=$(env | grep -c -E '^GIT_(DIR|WORK_TREE)=')
echo "group $GROUP  exported GIT_DIR/GIT_WORK_TREE: $n  live .git/config $(sha256sum /mnt/d/GitHub/mlehaptics/.git/config | cut -c1-16)  $(date -u +%FT%TZ)"
[ "$n" = 0 ] || { echo "REFUSED: exported GIT_DIR/GIT_WORK_TREE"; exit 2; }
for root in "$R" "$PURE"; do
  case "$root" in /mnt/*) echo "REFUSED: $root is under /mnt"; exit 2;; esac
  [ -d "$root/.git" ] || { echo "REFUSED: $root/.git is not a directory"; exit 2; }
  echo "$root HEAD $(git -C "$root" rev-parse HEAD) tracked changes $(git -C "$root" status --porcelain --untracked-files=no | wc -l) libs $(find "$root/docs/srmech/python" -name 'libsrmech*' | wc -l)"
done
UV="uv run --no-project --offline"
NOTES=$R/docs/srmech/notes
OLD=20bda4ffe
auth() { (cd "$R/docs/srmech/python" && $UV --python 3.12 python "$NOTES/_rc473_instr_auth.py" "$PWD" | grep -E "_native.__file__|lib sha256|abi / c|AUTH"); }
plant() { $UV --python 3.12 python "$NOTES/_rc473_instr_plants.py" "$1/docs/srmech" "${@:2}"; }
restore() { git -C "$1" checkout -- docs/srmech; echo "  restored: tracked changes $(git -C "$1" status --porcelain --untracked-files=no | wc -l)"; }
pt() { # <root> <tag> <pytest args...>   (pure cell, CPython 3.12)
  local root=$1 tag=$2; shift 2
  local t0; t0=$(date +%s%N)
  (cd "$root/docs/srmech/python" && timeout 900 $UV --python 3.12 --with pytest python -m pytest -q -p no:cacheprovider -rfEs "$@" > "/tmp/ir1_$tag.log" 2>&1)
  echo "  [$tag] exit $? in $(( ($(date +%s%N) - t0) / 1000000 )) ms: $(tail -1 "/tmp/ir1_$tag.log")"
  grep -E '^(FAILED|ERROR)' "/tmp/ir1_$tag.log" | cut -c1-230 | head -10
}
runner() { # <root> <tag> <command...>   (run under uv from the python root; prints exit and the verdict lines)
  local root=$1 tag=$2; shift 2
  local t0; t0=$(date +%s%N)
  (cd "$root/docs/srmech/python" && timeout 900 $UV --python 3.12 --with pytest "$@" > "/tmp/ir1_$tag.log" 2>&1)
  echo "  [$tag] exit $? in $(( ($(date +%s%N) - t0) / 1000000 )) ms"
  grep -E "REFUSED|FAILED --|collection kept|[0-9]+ (passed|failed|deselected)|no tests ran" "/tmp/ir1_$tag.log" | cut -c1-240 | sed 's/^/      /' | tail -4
}
M=/tmp/ir1_manifest.txt
printf 'tests/test_jpl_audit.py\ntests/test_git_export_advice_absent_rc473.py\n' > "$M"
MT=tests/test_ripple_manifest_covers_known_gates.py
RUNNER_TESTS="$MT::test_the_runner_refuses_forwarded_options_that_narrow_the_gate_run $MT::test_the_runner_fails_a_green_run_whose_collection_lost_items $MT::test_the_collection_count_plugin_sees_a_removal_at_every_granularity"
export SRMECH_EXPECT_PURE=1

case $GROUP in
runner_new)
  echo "== the refusal, by spelling (this runner)"
  $UV --python 3.12 python "$NOTES/_rc473_instr_r1_probe.py" spellings "$PURE/docs/srmech/python"
  echo "== the runner on a two-file manifest: $(tr '\n' ' ' < "$M")"
  runner "$PURE" n_base python tools/ripple_check.py --manifest "$M"
  runner "$PURE" n_qk python tools/ripple_check.py --manifest "$M" -- -qk advises
  runner "$PURE" n_xk python tools/ripple_check.py --manifest "$M" -- -xk advises
  runner "$PURE" n_oaddopts python tools/ripple_check.py --manifest "$M" -- -o "addopts=-k advises"
  runner "$PURE" n_setupplan python tools/ripple_check.py --manifest "$M" -- --setup-plan
  runner "$PURE" n_envaddopts env PYTEST_ADDOPTS="-k advises" python tools/ripple_check.py --manifest "$M"
  echo "== R_allowlist_off: the allow-list switched off, so only the count check stands"
  plant "$PURE" R_allowlist_off
  runner "$PURE" n_off_k python tools/ripple_check.py --manifest "$M" -- -k advises
  runner "$PURE" n_off_oaddopts python tools/ripple_check.py --manifest "$M" -- -o "addopts=-k advises"
  restore "$PURE"
  echo "== the runner's tests, head file"
  pt "$PURE" n_tests $RUNNER_TESTS
  ;;
runner_old)
  echo "== the runner as of $OLD"
  plant "$PURE" revert "$OLD" python/tools/ripple_check.py
  $UV --python 3.12 python "$NOTES/_rc473_instr_r1_probe.py" spellings "$PURE/docs/srmech/python"
  runner "$PURE" o_qk python tools/ripple_check.py --manifest "$M" -- -qk advises
  runner "$PURE" o_oaddopts python tools/ripple_check.py --manifest "$M" -- -o "addopts=-k advises"
  runner "$PURE" o_setupplan python tools/ripple_check.py --manifest "$M" -- --setup-plan
  echo "== this repair's runner tests against the $OLD runner"
  pt "$PURE" o_tests $RUNNER_TESTS
  restore "$PURE"
  ;;
manifest)
  echo "== head, the whole meta-test"; pt "$PURE" m_head $MT -s
  grep -E "^\[rc473\] collection" /tmp/ir1_m_head.log | cut -c1-260
  for p in M_param_conftest M_wrapper_conftest M_node M_deselect_conftest; do
    echo "== $p"; plant "$PURE" "$p"; pt "$PURE" "m_$p" $MT
    grep -E "REMOVED items|missing [1-9]" "/tmp/ir1_m_$p.log" | cut -c1-200 | head -2
    [ "$p" = M_param_conftest ] && pt "$PURE" "m_${p}_advice" tests/test_git_export_advice_absent_rc473.py
    plant "$PURE" revert "$OLD" "python/$MT"; pt "$PURE" "m_${p}_old" $MT; restore "$PURE"
  done
  ;;
advice)
  G=tests/test_git_export_advice_absent_rc473.py
  echo "== head"; pt "$PURE" a_head $G -s
  grep -E "^\[rc473\]" /tmp/ir1_a_head.log
  for p in P20_settings_env P21_readme_set_one P22_readme_point_at P23_notes_declare P24_readme_setx \
           P25_readme_dotnet P26_readme_prefix_tool P27_readme_prefix_make; do
    echo "== $p"; plant "$PURE" "$p"; pt "$PURE" "a_$p" $G
    plant "$PURE" revert "$OLD" "python/$G"; pt "$PURE" "a_${p}_old" $G; restore "$PURE"
  done
  for p in P1_hooklib_remedy P3_readme_advice P5_notes_shell P6_cmd_prefix P10_allow_reworded P7_changelog_green P13_negated_green; do
    echo "== $p (the instrument round's plant, this gate)"; plant "$PURE" "$p"; pt "$PURE" "a_$p" $G; restore "$PURE"
  done
  ;;
hook)
  unset SRMECH_EXPECT_PURE
  P=$R/docs/srmech/python
  git -C "$R" show "$OLD:docs/srmech/python/tools/hooks/derived_ledger_freshness.py" > "$P/tools/hooks/_ir1_old_hook.py"
  hookrun() { # <hook file> <tag>
    local t0; t0=$(date +%s%N)
    (cd "$P" && echo '{"hook_event_name":"Stop"}' | CLAUDE_PROJECT_DIR=$R $UV --python 3.12 python "tools/hooks/$1" > /dev/null 2> "/tmp/ir1_$2.err")
    echo "  $([ "$1" = _ir1_old_hook.py ] && echo "$OLD hook" || echo "this hook") exit $? ($(( ($(date +%s%N) - t0) / 1000000 )) ms, uv start included), stderr lines $(grep -c . "/tmp/ir1_$2.err")"
  }
  echo "== head, both committed ledgers"; hookrun derived_ledger_freshness.py h_head1; hookrun derived_ledger_freshness.py h_head2
  for spec in "V_args_1ab8d405b example_args_ledger op" "V_worked_1ab8d405b worked_examples_result name"; do
    set -- $spec; p=$1; led=$2; key=$3
    echo "== $p"; plant "$R" "$p"
    for h in derived_ledger_freshness.py _ir1_old_hook.py; do
      tag="h_${p}_${h%.py}"; hookrun "$h" "$tag"
      $UV --python 3.12 python "$NOTES/_rc473_instr_r1_probe.py" named "$P/tests/$led.ndjson" "$key" "/tmp/ir1_$tag.err"
      grep -E "BLOCKED|IN FULL|every unverified row|\(\+[0-9]+ more\)" "/tmp/ir1_$tag.err" | cut -c1-160 | sed 's/^/      /'
    done
    restore "$R"
  done
  echo "== check_hooks.py ledger, this hook"
  (cd "$P" && $UV --python 3.12 python tools/hooks/check_hooks.py ledger 2>&1 | grep -E "\[FAIL\]|passed, ")
  pt "$R" h_rc468 tests/test_ledger_freshness_hook_rc468.py
  echo "== the $OLD hook under the shipped name"
  cp "$P/tools/hooks/_ir1_old_hook.py" "$P/tools/hooks/derived_ledger_freshness.py"
  pt "$R" h_rc468_old tests/test_ledger_freshness_hook_rc468.py
  restore "$R"; rm -f "$P/tools/hooks/_ir1_old_hook.py"; echo "  old hook copy removed: $([ -e "$P/tools/hooks/_ir1_old_hook.py" ] && echo no || echo yes)"
  ;;
kepler)
  unset SRMECH_EXPECT_PURE
  [ -n "$BUILD" ] || { echo "REFUSED: kepler needs <build dir>"; exit 2; }
  KP=$NOTES/_rc473_scratch/instr/m_kep_partition.py
  LIB=$R/docs/srmech/python/srmech/_native/libsrmech.so
  echo "partition script $(sha256sum "$KP" | cut -c1-16); build source $(grep CMAKE_HOME_DIRECTORY "$BUILD/CMakeCache.txt" | cut -d= -f2)"
  start=$(sha256sum "$BUILD/libsrmech.so" | cut -c1-16); echo "build lib at start $start; installed $(sha256sum "$LIB" | cut -c1-16)"
  auth
  echo "== head"; (cd "$R/docs/srmech/python" && $UV --python 3.12 python "$KP" "$PWD" 2>&1 | grep -E "^HAS_NATIVE|^part|^one-text|^EXTENDED")
  echo "== K_c_revert"; plant "$R" K_c_revert
  cmake --build "$BUILD" > /tmp/ir1_kbuild.log 2>&1; echo "  build exit $? warnings $(grep -c 'warning:' /tmp/ir1_kbuild.log) errors $(grep -c 'error:' /tmp/ir1_kbuild.log)"
  cp "$BUILD/libsrmech.so" "$LIB"; auth
  (cd "$R/docs/srmech/python" && $UV --python 3.12 python "$KP" "$PWD" 2>&1 | grep -E "^HAS_NATIVE|^part|^one-text|^EXTENDED")
  restore "$R"
  cmake --build "$BUILD" > /tmp/ir1_kbuild2.log 2>&1; echo "  rebuild exit $? warnings $(grep -c 'warning:' /tmp/ir1_kbuild2.log)"
  cp "$BUILD/libsrmech.so" "$LIB"; end=$(sha256sum "$LIB" | cut -c1-16)
  echo "  restored lib $end $([ "$end" = "$start" ] && echo MATCH || echo DIFFERS)"; auth
  ;;
figures)
  P=$R/docs/srmech/python
  echo "== the codegen pair's size"
  echo "  git cat-file -s HEAD:docs/srmech/c/src/srmech_tool_registry.c -> $(git -C "$R" cat-file -s HEAD:docs/srmech/c/src/srmech_tool_registry.c) bytes"
  (cd "$P" && $UV --python 3.12 python -c "from pathlib import Path; t = Path('../c/src/srmech_tool_registry.c').read_text(encoding='utf-8'); print('  characters', len(t))")
  echo "== which manifest gates run tools/hooks/check_hooks.py, and with which argument"
  grep -n -E "^tests/test_(ledger_freshness_hook_rc468|git_env_cannot_reach_a_repository_rc473)\.py" "$P/tools/ripple_gates.txt"
  grep -n -E "subprocess.run\(\[sys.executable, str\(CHECKER\)" "$P/tests/test_ledger_freshness_hook_rc468.py" "$P/tests/test_git_env_cannot_reach_a_repository_rc473.py"
  echo "  test files naming check_hooks.py together with jpl: $(grep -l -E "CHECKER\).*jpl|check_hooks.py.*\"jpl\"" "$P"/tests/*.py | wc -l)"
  echo "== the five truth-round instruments the rc473 section names"
  for t in truth/t04_citations.py m_stale.py g_cite_samples.py t09_atan2_symbol.py w_sym.sh; do
    echo "  $t: CHANGELOG lines $(grep -n -F "$t" "$P/CHANGELOG.md" | cut -d: -f1 | tr '\n' ' ') archived under notes/_rc473_scratch: $(git -C "$R" ls-files docs/srmech/notes/_rc473_scratch | grep -c -F "$(basename "$t")")"
  done
  echo "  archived files: $(git -C "$R" ls-files docs/srmech/notes/_rc473_scratch | wc -l)"
  ;;
*) echo "unknown group $GROUP"; exit 2;;
esac
for root in "$R" "$PURE"; do echo "$root tracked changes at end $(git -C "$root" status --porcelain --untracked-files=no | wc -l)"; done
echo "end live .git/config $(sha256sum /mnt/d/GitHub/mlehaptics/.git/config | cut -c1-16)  $(date -u +%FT%TZ)"
