#!/bin/bash
# rc473 instrument round (`#T1188`): the can-fail runs behind the round's CHANGELOG figures.
#
# Usage (WSL2):
#   bash notes/_rc473_instr_canfail.sh <group> <native clone root> <pure clone root> [<build dir>]
# groups: hook ledger cells manifest leak advice registry kepler layer3 matrix
#
# Both roots are git CLONES whose `.git` is a directory, detached at the commit under test with
# 0 tracked changes; the native clone holds the library built from it (authenticated below), the
# pure clone none. Every plant is exact-once (notes/_rc473_instr_plants.py); every restore is
# `git checkout -- docs/srmech` with the tracked-changes count printed. Refuses a root under /mnt
# (never the live repository) and an exported GIT_DIR / GIT_WORK_TREE. `kepler` rebuilds the
# native library in <build dir> and must restore it to the digest it started from.
# CPython under `uv run --no-project --offline`; numpy absent; SRMECH_ALLOW_STALE_NATIVE unset.
set -u
GROUP=${1:?group}; R=${2:?native clone}; PURE=${3:?pure clone}; BUILD=${4:-}
export PATH="$HOME/.local/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE SRMECH_EXPECT_PURE
n=$(env | grep -c -E '^GIT_(DIR|WORK_TREE)=')
echo "group $GROUP  exported GIT_DIR/GIT_WORK_TREE: $n  $(date -u +%FT%TZ)"
[ "$n" = 0 ] || { echo "REFUSED: exported GIT_DIR/GIT_WORK_TREE"; exit 2; }
for root in "$R" "$PURE"; do
  case "$root" in /mnt/*) echo "REFUSED: $root is under /mnt"; exit 2;; esac
  [ -d "$root/.git" ] || { echo "REFUSED: $root/.git is not a directory"; exit 2; }
  echo "$root HEAD $(git -C "$root" rev-parse HEAD) tracked changes $(git -C "$root" status --porcelain --untracked-files=no | wc -l) libs $(find "$root/docs/srmech/python" -name 'libsrmech*' | wc -l)"
done
UV="uv run --no-project --offline"
NOTES=$R/docs/srmech/notes
auth() { (cd "$1/docs/srmech/python" && $UV --python "$2" python "$NOTES/_rc473_instr_auth.py" "$PWD" | grep -E "python |_native.__file__|HAS_NATIVE|numpy|lib sha256|abi / c|AUTH"); }
plant() { $UV --python 3.12 python "$NOTES/_rc473_instr_plants.py" "$1/docs/srmech" "${@:2}"; }
restore() { git -C "$1" checkout -- docs/srmech; echo "  restored: tracked changes $(git -C "$1" status --porcelain --untracked-files=no | wc -l)"; }
pt() { # <root> <python> <tag> <pytest args...>
  local root=$1 py=$2 tag=$3; shift 3
  local t0; t0=$(date +%s%N)
  (cd "$root/docs/srmech/python" && timeout 1500 $UV --python "$py" --with pytest python -m pytest -q -p no:cacheprovider -rfEs "$@" > "/tmp/ir_$tag.log" 2>&1)
  echo "  [$tag] exit $? in $(( ($(date +%s%N) - t0) / 1000000 )) ms: $(tail -1 "/tmp/ir_$tag.log")"
  grep -E '^(FAILED|ERROR|SKIPPED)' "/tmp/ir_$tag.log" | cut -c1-250 | head -14
}
W=tests/test_worked_examples_execute_rc354.py
A=tests/test_synth_args_provenance_rc430.py
FRESH="$W::test_ledger_is_fresh_against_the_live_schema $A::test_ledger_is_fresh_against_the_live_schema"
BLOB="$W::test_every_row_def_blob_is_its_defining_modules_blob_at_head $A::test_every_row_def_blob_is_its_defining_modules_blob_at_head"
RESO="$W::test_every_row_def_module_is_where_the_live_callable_is_defined $A::test_every_row_def_module_is_where_the_live_callable_is_defined"

case $GROUP in
hook)
  P=$R/docs/srmech/python
  git -C "$R" show 81c55dba6:docs/srmech/python/tools/hooks/derived_ledger_freshness.py > "$P/tools/hooks/_ir_old_hook.py"
  hooks() {
    for h in _ir_old_hook.py derived_ledger_freshness.py; do
      local t0 err c; t0=$(date +%s%N)
      err=$(cd "$P" && echo '{"hook_event_name":"Stop"}' | CLAUDE_PROJECT_DIR=$R $UV --python 3.12 python "tools/hooks/$h" 2>&1 >/dev/null); c=$?
      echo "  $([ "$h" = _ir_old_hook.py ] && echo "81c55dba6 hook" || echo "this hook   ") exit $c ($(( ($(date +%s%N) - t0) / 1000000 )) ms, uv start included)"
      echo "$err" | grep -E "BLOCKED|by clause|failed open|ADVISORY" | cut -c1-210 | sed 's/^/      /'
    done
  }
  echo "== head"; hooks; hooks
  for p in V_worked_d346173fc V_args_d346173fc V_worked_1ab8d405b V_args_1ab8d405b \
           F_worked_defblob_kepler F_args_defblob_kepler F_worked_src_atan2 F_args_src_atan2 S_pin_slot_snippet; do
    echo "== $p"; plant "$R" "$p"; hooks; restore "$R"
  done
  for which in worked args; do for rev in d346173fc 1ab8d405b; do plant "$R" rowdiff $which $rev | head -1; done; done
  echo "== check_hooks.py ledger, this hook"
  (cd "$P" && $UV --python 3.12 python tools/hooks/check_hooks.py ledger 2>&1 | grep -E "\[FAIL\]|passed, ")
  pt "$R" 3.12 hookt tests/test_ledger_freshness_hook_rc468.py
  echo "== the 81c55dba6 hook under the shipped name"
  cp "$P/tools/hooks/_ir_old_hook.py" "$P/tools/hooks/derived_ledger_freshness.py"
  (cd "$P" && $UV --python 3.12 python tools/hooks/check_hooks.py ledger 2>&1 | grep -E "\[FAIL\]|passed, ")
  pt "$R" 3.12 hookt_old tests/test_ledger_freshness_hook_rc468.py
  restore "$R"; rm -f "$P/tools/hooks/_ir_old_hook.py"
  ;;
ledger)
  auth "$R" 3.12
  for cell in "native $R 3.12" "pure $PURE 3.10"; do
    set -- $cell; name=$1; root=$2; py=$3
    [ "$name" = pure ] && export SRMECH_EXPECT_PURE=1 || unset SRMECH_EXPECT_PURE
    echo "== $name $py head"; pt "$root" "$py" "l_${name}_head" $FRESH $BLOB $RESO
    for p in F_worked_defblob_kepler F_args_defblob_kepler F_worked_defmodule_pinslot; do
      echo "== $name $py $p"; plant "$root" "$p"
      pt "$root" "$py" "l_${name}_${p}_fresh" $FRESH
      pt "$root" "$py" "l_${name}_${p}_new" $BLOB $RESO
      restore "$root"
    done
  done
  unset SRMECH_EXPECT_PURE
  X=/tmp/ir_extract; rm -rf $X; mkdir -p $X
  git -C "$PURE" archive HEAD docs/srmech | tar -x -C $X
  echo "== git-free extract (no .git above the package), pure 3.12"
  SRMECH_EXPECT_PURE=1 pt $X 3.12 l_extract $BLOB $RESO
  printf 'gitdir: /nowhere/.git/worktrees/x\n' > $X/.git
  echo "== the same extract with a .git pointer git cannot read"
  SRMECH_EXPECT_PURE=1 pt $X 3.12 l_extract_badgit $BLOB
  rm -rf $X; echo "  extract removed: $([ -e $X ] && echo no || echo yes)"
  ;;
cells)
  for cell in "native $R 3.10" "native $R 3.12" "pure $PURE 3.10" "pure $PURE 3.12"; do
    set -- $cell
    [ "$1" = pure ] && export SRMECH_EXPECT_PURE=1 || unset SRMECH_EXPECT_PURE
    echo "== $1 $3"; [ "$1" = native ] && auth "$2" "$3"
    pt "$2" "$3" "c_$1_$3" $BLOB $RESO
  done
  unset SRMECH_EXPECT_PURE
  ;;
manifest)
  export SRMECH_EXPECT_PURE=1
  M=tests/test_ripple_manifest_covers_known_gates.py
  NEW="$M::test_every_frozen_file_gate_is_listed_as_the_whole_file $M::test_the_manifest_collects_every_test_function_each_frozen_file_defines $M::test_the_runner_refuses_forwarded_options_that_narrow_the_gate_run"
  echo "== head"; pt "$PURE" 3.12 m_head $M -s
  grep -E "^\[rc473\] collection" /tmp/ir_m_head.log | cut -c1-240
  for p in M_node M_deselect_conftest; do
    echo "== $p"; plant "$PURE" "$p"; pt "$PURE" 3.12 "m_$p" $M
    plant "$PURE" revert 81c55dba6 python/$M; pt "$PURE" 3.12 "m_${p}_81c55dba6" $M; restore "$PURE"
  done
  echo "== ripple_check.py with a forwarded -k (this runner, then 81c55dba6's), --list is harmless"
  (cd "$PURE/docs/srmech/python" && $UV --python 3.12 --with pytest python tools/ripple_check.py -- -k pin > /tmp/ir_rk.log 2>&1; echo "  this runner exit $?: $(head -c 160 /tmp/ir_rk.log)")
  ;;
leak)
  export SRMECH_EXPECT_PURE=1
  L=tests/test_git_env_cannot_reach_a_repository_rc473.py
  echo "== head"; pt "$PURE" 3.12 k_head $L
  for p in L1e_invoke_unscrub L1f_hooklib_git_unscrub L2d_redirect_empty L2n_namespace_dropped; do
    echo "== $p"; plant "$PURE" "$p"; pt "$PURE" 3.12 "k_$p" $L
    plant "$PURE" revert 81c55dba6 python/$L; pt "$PURE" 3.12 "k_${p}_81c55dba6" $L; restore "$PURE"
  done
  ;;
advice)
  export SRMECH_EXPECT_PURE=1
  G=tests/test_git_export_advice_absent_rc473.py
  echo "== head"; pt "$PURE" 3.12 a_head $G -s
  grep -E "^\[rc473\]" /tmp/ir_a_head.log
  for p in P1_hooklib_remedy P3_readme_advice P5_notes_shell P6_cmd_prefix P10_allow_reworded P7_changelog_green P13_negated_green; do
    echo "== $p"; plant "$PURE" "$p"; pt "$PURE" 3.12 "a_$p" $G; restore "$PURE"
  done
  BASE=$(dirname "$PURE")/base
  if [ -d "$BASE/.git" ]; then
    echo "== the gate file copied into $BASE at $(git -C "$BASE" rev-parse --short HEAD)"
    cp "$PURE/docs/srmech/python/$G" "$BASE/docs/srmech/python/$G"
    pt "$BASE" 3.12 a_base $G
    grep -c "^  python\|^  notes" /tmp/ir_a_base.log
    grep -E "^  (python|notes)/" /tmp/ir_a_base.log | cut -c1-200 | head -20
    rm -f "$BASE/docs/srmech/python/$G"; echo "  base tracked changes $(git -C "$BASE" status --porcelain --untracked-files=no | wc -l) untracked gate copy removed: $([ -e "$BASE/docs/srmech/python/$G" ] && echo no || echo yes)"
  fi
  ;;
registry)
  auth "$R" 3.12
  T=tests/test_tool_registry_c_rc184.py
  echo "== head"; pt "$R" 3.12 r_head $T
  echo "== R_t1_3b, the JSON node ALONE at -v -rfEs"; plant "$R" R_t1_3b
  pt "$R" 3.12 r_t1_new -v "$T::test_c_json_byte_identical_to_python_ssot"
  grep -E "diverged|first difference" /tmp/ir_r_t1_new.log | cut -c1-300 | head -3
  plant "$R" revert 81c55dba6 python/$T
  t0=$(date +%s%N)
  (cd "$R/docs/srmech/python" && timeout -s INT 240 $UV --python 3.12 --with pytest python -m pytest -p no:cacheprovider -v -rfEs "$T::test_c_json_byte_identical_to_python_ssot" > /tmp/ir_r_t1_old.log 2>&1)
  echo "  [81c55dba6 node, SIGINT at 240 s] exit $? after $(( ($(date +%s%N) - t0) / 1000000 )) ms: $(tail -1 /tmp/ir_r_t1_old.log | cut -c1-160)"
  grep -E "difflib|assertion/util" /tmp/ir_r_t1_old.log | cut -c1-160 | head -4
  restore "$R"
  echo "== R_registry_len, the codegen node at -v"; plant "$R" R_registry_len
  pt "$R" 3.12 r_len_new -v "$T::test_codegen_is_idempotent"
  grep -E "out of date|first difference" /tmp/ir_r_len_new.log | cut -c1-300 | head -3
  restore "$R"
  ;;
kepler)
  [ -n "$BUILD" ] || { echo "REFUSED: kepler needs <build dir>"; exit 2; }
  K=tests/test_kepler_non_finite_slots_rc473.py
  LIB=$R/docs/srmech/python/srmech/_native/libsrmech.so
  start=$(sha256sum "$BUILD/libsrmech.so" | cut -c1-16); echo "build lib at start $start; installed $(sha256sum "$LIB" | cut -c1-16)"
  auth "$R" 3.12
  echo "== head"; pt "$R" 3.12 kp_head $K
  echo "== K_c_revert"; plant "$R" K_c_revert
  cmake --build "$BUILD" > /tmp/ir_kbuild.log 2>&1; echo "  build exit $? warnings $(grep -c 'warning:' /tmp/ir_kbuild.log) errors $(grep -c 'error:' /tmp/ir_kbuild.log)"
  cp "$BUILD/libsrmech.so" "$LIB"; echo "  planted lib $(sha256sum "$LIB" | cut -c1-16)"; auth "$R" 3.12
  pt "$R" 3.12 kp_plant $K
  plant "$R" revert 81c55dba6 python/$K
  pt "$R" 3.12 kp_plant_81c55dba6 $K
  git -C "$R" checkout -- docs/srmech/python/$K
  pt "$R" 3.12 kp_plant_onetext "$K::test_kepler_solve_non_convergence_is_one_text"
  restore "$R"
  cmake --build "$BUILD" > /tmp/ir_kbuild2.log 2>&1; echo "  rebuild exit $? warnings $(grep -c 'warning:' /tmp/ir_kbuild2.log)"
  cp "$BUILD/libsrmech.so" "$LIB"; end=$(sha256sum "$LIB" | cut -c1-16)
  echo "  restored lib $end $([ "$end" = "$start" ] && echo MATCH || echo DIFFERS)"; auth "$R" 3.12
  pt "$R" 3.12 kp_restored $K
  ;;
layer3)
  S3=$NOTES/_rc473_final_layer3_geometry.sh
  WK=/mnt/c/Users/sckir/rc473c_win/ir/l3x
  echo "== GITEXE=/bin/false (does not execute)"; GITEXE=/bin/false bash "$S3" "$PURE" "$WK" > /tmp/ir_l3a.log 2>&1; echo "  exit $?"; grep -E "REFUSED|FAILED|removed" /tmp/ir_l3a.log
  echo "== GITEXE=/bin/echo (executes, creates nothing)"; GITEXE=/bin/echo bash "$S3" "$PURE" "$WK" > /tmp/ir_l3b.log 2>&1; echo "  exit $?"; grep -E "REFUSED|FAILED|VERDICT|unchanged|removed" /tmp/ir_l3b.log
  echo "== GIT_INDEX_FILE and GIT_CONFIG_KEY_0 handed to the script's shell, GITEXE=/bin/false"
  env GIT_INDEX_FILE=/tmp/nowhere/index GIT_CONFIG_KEY_0=user.name GIT_CONFIG_VALUE_0=x GITEXE=/bin/false bash "$S3" "$PURE" "$WK" > /tmp/ir_l3c.log 2>&1; echo "  exit $?"; grep -E "REFUSED|removed" /tmp/ir_l3c.log
  rm -rf "$WK"; echo "  work dir removed: $([ -e "$WK" ] && echo no || echo yes)"
  ;;
matrix)
  bash "$NOTES/_rc473_instr_git_env_matrix.sh" /tmp/ir_matrix
  ;;
*) echo "unknown group $GROUP"; exit 2;;
esac
for root in "$R" "$PURE"; do echo "$root tracked changes at end $(git -C "$root" status --porcelain --untracked-files=no | wc -l)"; done
echo "end $(date -u +%FT%TZ)"
