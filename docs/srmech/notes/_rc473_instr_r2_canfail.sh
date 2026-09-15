#!/bin/bash
# rc473 instrument repair 2 (`#T1188`): the can-fail runs behind the repair's CHANGELOG figures.
#
# Usage (WSL2):
#   bash notes/_rc473_instr_r2_canfail.sh <group> <native clone root> <pure clone root>
# groups: probe manifest runner old_tests figures
#
# Clones and conditions as notes/_rc473_instr_r1_canfail.sh: git CLONES whose `.git` is a directory,
# detached at the commit under test with 0 tracked changes; the pure clone holds no library. The
# groups run on the files AT that commit, so the same group run at the commit before the repair and
# at the repair measures the defect and the fix. Plants come from notes/_rc473_instr_plants.py, each
# exact-once; a PYTEST_PLUGINS module is written by `plants.py envplug` under /tmp, never into the
# tree; every restore is `git checkout -- docs/srmech` with the count printed. "old" is a file as of
# c13529f73 (instrument repair 1's record head), written in by `plants.py revert`.
# Refuses a root under /mnt and an exported GIT_DIR / GIT_WORK_TREE. PYTEST_ADDOPTS and PYTEST_PLUGINS
# are unset here and set only where a run names them. numpy absent; SRMECH_ALLOW_STALE_NATIVE unset.
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
OLD=c13529f73
T=/tmp/ir2_$GROUP; rm -rf "$T"; mkdir -p "$T"
plant() { $UV --python 3.12 python "$NOTES/_rc473_instr_plants.py" "$1/docs/srmech" "${@:2}"; }
restore() { git -C "$1" checkout -- docs/srmech; echo "  restored: tracked changes $(git -C "$1" status --porcelain --untracked-files=no | wc -l)"; }
pt() { # <tag> <env assignments or -> <pytest args...>   (pure clone, CPython 3.12)
  local tag=$1 envs=$2; shift 2; [ "$envs" = - ] && envs=""
  local t0; t0=$(date +%s%N)
  (cd "$PURE/docs/srmech/python" && env $envs timeout 900 $UV --python 3.12 --with pytest python -m pytest -q -p no:cacheprovider -rfEs "$@" > "$T/$tag.log" 2>&1)
  echo "  [$tag] exit $? in $(( ($(date +%s%N) - t0) / 1000000 )) ms: $(tail -1 "$T/$tag.log")"
  grep -E '^(FAILED|ERROR)' "$T/$tag.log" | cut -c1-200 | head -8
  grep -E "^\[rc473\] collection" "$T/$tag.log" | sed -E 's/^.*(missing [0-9]+, items [^}]*\}).*$/      \1/'
}
runner() { # <tag> <env assignments or -> <ripple_check args...>   (pure clone, CPython 3.12)
  local tag=$1 envs=$2; shift 2; [ "$envs" = - ] && envs=""
  local t0; t0=$(date +%s%N)
  (cd "$PURE/docs/srmech/python" && env $envs timeout 900 $UV --python 3.12 --with pytest python tools/ripple_check.py "$@" > "$T/$tag.log" 2>&1)
  echo "  [$tag] exit $? in $(( ($(date +%s%N) - t0) / 1000000 )) ms"
  grep -E "REFUSED|FAILED --|red --|collection kept|ran all|[0-9]+ (passed|failed|deselected|skipped)|no tests ran" "$T/$tag.log" | cut -c1-230 | sed 's/^/      /' | tail -4
}
EP=$T/envplug
envs_for() { echo "PYTHONPATH=$EP PYTEST_PLUGINS=r2_envplug"; }
MT=tests/test_ripple_manifest_covers_known_gates.py
COLL="$MT::test_the_manifest_collects_every_test_function_each_frozen_file_defines"
ADV=tests/test_git_export_advice_absent_rc473.py
M=$T/manifest.txt; printf '%s\n' "$ADV" > "$M"
CONFTEST_PLANTS="M_wrapper_conftest M_wrapper_old_before_yield M_wrapper_new_before_yield M_finish_trylast M_runtestloop_wrapper M_protocol_returns_true LIMIT_make_collect_report LIMIT_setup_skips"
ENV_PLANTS="E_wrapper_old_before_yield E_wrapper_new_before_yield E_finish_trylast E_runtestloop_wrapper"
export SRMECH_EXPECT_PURE=1
has_env_refusal=$(grep -c 'for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS"):' "$PURE/docs/srmech/python/tools/ripple_check.py")
has_ran_check=$(grep -c 'or ran != collected:' "$PURE/docs/srmech/python/tools/ripple_check.py")
echo "this runner: PYTEST_PLUGINS refusal lines $has_env_refusal, ran comparison lines $has_ran_check"

case $GROUP in
probe)
  git -C "$PURE" show "$OLD:docs/srmech/python/tests/_collection_count_plugin.py" > "$T/old_plugin.py"
  for which in tree old; do
    if [ "$which" = tree ]; then f=$PURE/docs/srmech/python/tests/_collection_count_plugin.py; else f=$T/old_plugin.py; fi
    for v in 3.12 3.10; do
      echo "== the sandbox over the $which plugin ($(sha256sum "$f" | cut -c1-16)), CPython $v"
      (cd "$T" && timeout 900 $UV --python $v --with pytest python "$NOTES/_rc473_instr_r2_order_probe.py" "$f" > "$T/probe_${which}_$v.log" 2>&1)
      echo "  exit $?: $(head -1 "$T/probe_${which}_$v.log" | cut -d' ' -f1-6)"
      awk '/collect-only exit/ {name=$1; co=$NF; if ($(NF-1)=="not") co="not-seen"} /runner predicate/ {r=($0 ~ /runner predicate SEEN/) ? "SEEN" : (($0 ~ /NO COUNTS/) ? "NO-COUNTS" : "not-seen"); s=$0; sub(/^.*\| /, "", s); printf "    %-42s collect-only %-9s run %-9s | %s\n", name, co, r, s}' "$T/probe_${which}_$v.log"
    done
  done
  ;;
manifest)
  echo "== head, the whole meta-test"; pt m_head - $MT -s
  for p in $CONFTEST_PLANTS; do
    echo "== $p"; plant "$PURE" "$p"; pt "m_$p" - "$COLL" -s; restore "$PURE"
  done
  for p in $ENV_PLANTS; do
    echo "== $p (PYTEST_PLUGINS)"; rm -rf "$EP"; plant "$PURE" envplug "$EP" "$p"; pt "m_$p" "$(envs_for)" "$COLL" -s
  done
  ;;
runner)
  echo "== head, manifest: $ADV"; runner r_head - --manifest "$M"
  for p in $CONFTEST_PLANTS; do
    echo "== $p"; plant "$PURE" "$p"; runner "r_$p" - --manifest "$M"; restore "$PURE"
  done
  for p in $ENV_PLANTS; do
    echo "== $p (PYTEST_PLUGINS)"; rm -rf "$EP"; plant "$PURE" envplug "$EP" "$p"
    runner "r_$p" "$(envs_for)" --manifest "$M"
    if [ "$has_env_refusal" = 1 ]; then
      plant "$PURE" R_env_refusal_off; runner "r_${p}_refusal_off" "$(envs_for)" --manifest "$M"; restore "$PURE"
    fi
  done
  if [ "$has_ran_check" = 1 ]; then
    for p in M_runtestloop_wrapper M_finish_trylast; do
      echo "== $p under R_ran_check_off"; plant "$PURE" R_ran_check_off; plant "$PURE" "$p"; runner "r_${p}_ran_off" - --manifest "$M"; restore "$PURE"
    done
  fi
  ;;
old_tests)
  N="$MT::test_the_runner_refuses_forwarded_options_that_narrow_the_gate_run $MT::test_the_runner_fails_a_green_run_whose_collection_lost_items $MT::test_the_collection_count_plugin_reports_the_planted_removals"
  echo "== the runner and plugin tests, this tree"; pt o_tree - $N
  echo "== the same tests with the $OLD runner and plugin written in"
  plant "$PURE" revert "$OLD" python/tools/ripple_check.py python/tests/_collection_count_plugin.py
  pt o_old - $N; restore "$PURE"
  ;;
figures)
  P=$PURE/docs/srmech/python
  echo "== B3: tests/*.py lines naming both check_hooks.py and jpl (any spelling), and every CHECKER subprocess call"
  grep -n -H -E "check_hooks\.py" "$P"/tests/*.py | grep -i "jpl" | sed "s|$P/||" | cut -c1-200
  echo "  lines naming both: $(grep -h -E "check_hooks\.py" "$P"/tests/*.py | grep -c -i "jpl")"
  grep -n -H -E "str\(CHECKER\)" "$P"/tests/*.py | sed "s|$P/||" | cut -c1-200
  echo "  CHECKER calls passing a jpl case: $(grep -h -E "str\(CHECKER\)" "$P"/tests/*.py | grep -c -i "jpl")"
  echo "== B2: the advice gate's forms, and every form count the tree states for it"
  echo "  PATTERNS keys: $(sed -n '/^PATTERNS = {/,/^}/p' "$P/$ADV" | grep -c -E '^    "[a-z_]+"')"
  grep -rn -i -E "(eight|thirteen|[0-9]+) (phrase )?forms" "$P/tools" "$P/tests" "$P/srmech" "$PURE/docs/srmech/notes" --include='*.py' --include='*.txt' --include='*.md' --include='*.sh' --include='*.json' | sed "s|$PURE/docs/srmech/||" | cut -c1-220
  ;;
*) echo "unknown group $GROUP"; exit 2;;
esac
rm -rf "$EP"
for root in "$R" "$PURE"; do echo "$root tracked changes at end $(git -C "$root" status --porcelain --untracked-files=no | wc -l)"; done
echo "end live .git/config $(sha256sum /mnt/d/GitHub/mlehaptics/.git/config | cut -c1-16)  $(date -u +%FT%TZ)"
