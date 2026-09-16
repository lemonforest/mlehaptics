#!/bin/bash
# rc473 final repair 1 (`#T1188`): Layer 3 of the git-environment fix, measured in the
# geometry the export existed for.
#
# WSL git cannot follow a worktree whose `.git` is a pointer FILE holding a Windows path
# (`gitdir: C:/...`), and exporting GIT_DIR / GIT_WORK_TREE was the old advice for it —
# the export under which a test fixture wrote the live repository's shared .git/config.
# Layer 3 (tests/_git_env.py:git_location_args) hands that pointer's /mnt twin to ONE git
# invocation instead. A checkout whose `.git` is a DIRECTORY never exercises it: the walk
# answers [] there. So this builds the real geometry in a sandbox:
#
#   * repository M, made by WINDOWS git (git.exe through WSL interop), holding the
#     docs/srmech python/, c/ and notes/ trees of the checkout under test, with
#     extensions.worktreeConfig on (the live repository's shape);
#   * worktree MW, made by Windows git, whose `.git` therefore says `gitdir: <drive>:/...`;
#
# and then, driven from WSL git, nothing exported in this shell:
#   1. CONTROL — plain WSL `git rev-parse HEAD` inside MW must FAIL (else the geometry is
#      not the one the export existed for, and nothing below measures Layer 3);
#   2. the shipped lookups must answer for M's own HEAD: git_location_args, _hooklib.git,
#      run_worked_examples.head_blob_map / _head_commit, figure_run.git_available and
#      test_shell_line_loop_rc468._is_checkout;
#   3. the git-touching gate files, run in MW with nothing exported, then with the
#      incident export (GIT_DIR / GIT_WORK_TREE at MW's gitdir) handed to that ONE pytest
#      command, must pass;
#   4. tools/hooks/check_hooks.py ledger, run directly (no pytest guard) under that export,
#      must run at least one case and pass all of them;
#   5. M's config, refs, commit count and MW's index are snapshotted at every step and must
#      never move.
#
# Usage (from WSL2):
#   bash notes/_rc473_final_layer3_geometry.sh <checkout-root> <work-dir-on-a-/mnt-drive> [<file to guard>]
# <checkout-root>  a git checkout holding the commit under test (its HEAD is archived);
#                  NOT a Windows worktree, and never the live repository's gitdir.
# <work-dir>       must live under /mnt/<drive>/ so Windows git writes a drive-letter pointer;
#                  removed and recreated.
# <file to guard>  optional; its sha256 is printed at the start and the end.
# PY               the interpreter command, default `python3`; it must import pytest.
# Exit 0 only if every expectation above held. numpy-free; no abs(); read-only outside <work-dir>.
set -u
SRC=${1:?checkout root}; WORK=${2:?work dir}; GUARD=${3:-}
PY=${PY:-python3}
say() { echo "$*"; }
fail=0; bad() { say "  EXPECTATION FAILED: $*"; fail=1; }

n_exported=$(env | grep -c -E '^GIT_(DIR|WORK_TREE)=')
say "exported GIT_DIR/GIT_WORK_TREE: $n_exported  $(date -u +%FT%TZ)"
[ "$n_exported" = 0 ] || { say "REFUSED: this instrument never runs under an exported GIT_DIR/GIT_WORK_TREE"; exit 2; }
# rc473 instrument round (`#T1188`): every OTHER repository-local variable is removed
# from this shell too, so none of this script's own git calls (config --get, status,
# show-ref, rev-list, archive) can answer for another repository. The list is the
# running git's own, plus the three write-redirect names and the numbered pairs.
scrubbed=0
for v in $(git rev-parse --local-env-vars) GIT_NAMESPACE GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM \
         $(env | sed -n -E 's/^(GIT_CONFIG_(KEY|VALUE)_[0-9]+)=.*/\1/p'); do
  [ -n "${!v+x}" ] && scrubbed=$((scrubbed + 1)); unset "$v"
done
say "repository-local variables removed from this shell: $scrubbed"
case "$WORK" in /mnt/[a-z]/*) ;; *) say "REFUSED: <work-dir> must be under /mnt/<drive>/"; exit 2;; esac
# GITEXE may be given (default: git.exe on PATH). It must EXECUTE, not merely exist:
# without WSL interop `command -v git.exe` still finds it, and every call then fails
# with "Exec format error" while the snapshots below compare empty strings.
GITEXE=${GITEXE:-$(command -v git.exe)} || true
[ -n "$GITEXE" ] || { say "REFUSED: git.exe (Windows git) is not reachable"; exit 2; }
"$GITEXE" --version > /dev/null 2>&1 || { say "REFUSED: $GITEXE does not execute (is WSL interop available?)"; exit 2; }
[ -n "$GUARD" ] && say "guard $GUARD sha256 $(sha256sum "$GUARD" | cut -c1-64)"
say "WSL $(git --version); Windows $("$GITEXE" --version | tr -d '\r')"
say "source $(git -C "$SRC" rev-parse HEAD) tracked changes $(git -C "$SRC" status --porcelain --untracked-files=no | wc -l)"

M=$WORK/M; MW=$WORK/MW; P=$MW/docs/srmech/python
BT=$(mktemp -d /tmp/l3bt.XXXXXX)
export GIT_CEILING_DIRECTORIES=$(dirname "$WORK") PYTHONDONTWRITEBYTECODE=1 SRMECH_EXPECT_PURE=1
unset SRMECH_ALLOW_STALE_NATIVE SRMECH_HOOK_GIT
rm -rf "$M" "$MW"; mkdir -p "$M"
git -C "$SRC" archive HEAD -- docs/srmech/python docs/srmech/c docs/srmech/notes | tar -x -C "$M" \
  || { say "REFUSED: archive of $SRC failed"; exit 2; }
WM=$(wslpath -w "$M"); WMW=$(wslpath -w "$MW")
"$GITEXE" -C "$WM" init -q -b main
"$GITEXE" -C "$WM" config --local core.autocrlf false
"$GITEXE" -C "$WM" config --local user.name "Replica Owner"
"$GITEXE" -C "$WM" config --local user.email replica@example.invalid
"$GITEXE" -C "$WM" config --local extensions.worktreeConfig true
"$GITEXE" -C "$WM" add -- docs
"$GITEXE" -C "$WM" -c commit.gpgsign=false commit -q -m replica
"$GITEXE" -C "$WM" worktree add -q -b w "$WMW"
# rc473 instrument round (`#T1188`): a sandbox that was never created FAILS here. Until
# then every snapshot below compared empty fields and printed "unchanged".
[ -d "$M/.git" ] && [ -f "$MW/.git" ] || { say "FAILED: repository M or worktree MW was never created (M/.git dir: $([ -d "$M/.git" ] && echo yes || echo no), MW/.git file: $([ -f "$MW/.git" ] && echo yes || echo no))"; say "VERDICT: FAILED"; exit 1; }
HEAD_M=$("$GITEXE" -C "$WM" rev-parse HEAD | tr -d '\r')
[ -n "$HEAD_M" ] || { say "FAILED: M has no HEAD"; say "VERDICT: FAILED"; exit 1; }
say "M (Windows git) HEAD $HEAD_M tracked $("$GITEXE" -C "$WM" ls-files | wc -l)"
POINTER=$(tr -d '\r' < "$MW/.git")
say "MW/.git: $POINTER"
echo "$POINTER" | grep -q -E '^gitdir: [A-Za-z]:/' || bad "MW/.git is not a drive-letter pointer"

snap() {
  printf 'name=%s worktree=[%s] cfg=%s refs=%s commits=%s idx=%s' \
    "$(git -C "$M" config --local --get user.name)" "$(git -C "$M" config --local --get core.worktree)" \
    "$(sha256sum "$M/.git/config" | cut -c1-16)" "$(git -C "$M" show-ref | sha256sum | cut -c1-12)" \
    "$(git -C "$M" rev-list --all --count)" "$(sha256sum "$M/.git/worktrees/MW/index" | cut -c1-12)"
}
START=$(snap); say "M[start] $START"
check() { local now; now=$(snap); if [ "$now" = "$START" ]; then say "M[$1] unchanged"; else say "M[$1] MOVED: $now"; bad "M moved at $1"; fi; }

say "=== 1. control: plain WSL git inside MW"
(cd "$P" && git rev-parse HEAD) > "$BT/control.txt" 2>&1; rc=$?
say "  exit $rc: $(tail -1 "$BT/control.txt" | cut -c1-160)"
[ "$rc" != 0 ] || bad "plain WSL git read MW, so this is not the geometry Layer 3 exists for"

say "=== 2. the shipped lookups, nothing exported"
(cd "$P" && $PY - "$P" "$HEAD_M" <<'PYEOF'
import importlib.util
import sys
from pathlib import Path

root, head = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ok = True
from tests import _git_env
args = _git_env.git_location_args(root)
print("  git_location_args:", args)
ok &= len(args) == 2 and args[0].startswith("--git-dir=/mnt/")
H = load("_hooklib", root + "/tools/hooks/_hooklib.py")
got = H.git(["rev-parse", "HEAD"], cwd=Path(root))
print("  _hooklib.git rev-parse HEAD:", got)
ok &= got[0] == 0 and got[1].strip() == head
rwe = load("run_worked_examples", root + "/tools/run_worked_examples.py")
blobs, commit = rwe.head_blob_map(), rwe._head_commit()
print("  run_worked_examples.head_blob_map entries:", len(blobs), " _head_commit:", commit)
ok &= len(blobs) > 0 and commit == head
fr = load("figure_run", root + "/tools/figure_run.py")
print("  figure_run.git_available:", fr.git_available())
ok &= fr.git_available() is True
from tests import test_shell_line_loop_rc468 as T
print("  test_shell_line_loop_rc468._is_checkout:", T._is_checkout())
ok &= T._is_checkout() is True
print("  LOOKUPS:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
PYEOF
) || bad "a shipped lookup did not answer for M's own HEAD"
check after-lookups

FILES="tests/test_git_env_cannot_reach_a_repository_rc473.py tests/test_hook_fixture_env_isolation_rc471.py tests/test_ledger_freshness_hook_rc468.py tests/test_shell_line_loop_rc468.py tests/test_figure_run_rc471.py tests/test_ledger_write_refusals_rc469.py tests/test_registry_completeness_rc416.py"
say "=== 3a. pytest in MW, nothing exported  $(date -u +%FT%TZ)"
(cd "$P" && $PY -m pytest -q -p no:cacheprovider -rfEs --basetemp="$BT/a" $FILES) > "$BT/pytest_a.txt" 2>&1; rc=$?
say "  exit $rc: $(tail -1 "$BT/pytest_a.txt")"; grep -E "^(FAILED|ERROR|SKIPPED)" "$BT/pytest_a.txt" | cut -c1-220
[ "$rc" = 0 ] || bad "pytest in MW failed with nothing exported"
check after-pytest-noexport
say "=== 3b. pytest in MW with the incident export handed to this one command  $(date -u +%FT%TZ)"
(cd "$P" && env GIT_DIR="$M/.git/worktrees/MW" GIT_WORK_TREE="$MW" \
   $PY -m pytest -q -p no:cacheprovider -rfEs --basetemp="$BT/b" $FILES) > "$BT/pytest_b.txt" 2>&1; rc=$?
say "  exit $rc: $(tail -1 "$BT/pytest_b.txt")"; grep -E "^(FAILED|ERROR|SKIPPED)" "$BT/pytest_b.txt" | cut -c1-220
[ "$rc" = 0 ] || bad "pytest in MW failed under the incident export"
check after-pytest-export

say "=== 4. check_hooks.py ledger directly, no pytest guard, under the incident export  $(date -u +%FT%TZ)"
(cd "$P" && env GIT_DIR="$M/.git/worktrees/MW" GIT_WORK_TREE="$MW" $PY tools/hooks/check_hooks.py ledger) \
  > "$BT/ledger.txt" 2>&1; rc=$?
summary=$(grep -E '^[0-9]+ passed, [0-9]+ failed, [0-9]+ skipped \([0-9]+ cases\)$' "$BT/ledger.txt" | tail -1)
say "  exit $rc: $summary"; grep -E "\[FAIL\]" "$BT/ledger.txt" | head
cases=$(echo "$summary" | sed -n -E 's/^([0-9]+) passed, ([0-9]+) failed, ([0-9]+) skipped \(([0-9]+) cases\)$/\4/p')
passed=$(echo "$summary" | sed -n -E 's/^([0-9]+) passed, .*/\1/p')
[ "$rc" = 0 ] && [ "${cases:-0}" -ge 1 ] && [ "${passed:-0}" = "${cases:-x}" ] || bad "check_hooks.py ledger did not run and pass every case"
check after-ledger

say "=== 5. end"
say "  MW tracked changes (per-invocation --git-dir/--work-tree): $(git --git-dir="$M/.git/worktrees/MW" --work-tree="$MW" status --porcelain --untracked-files=no | wc -l)"
say "  exported GIT_DIR/GIT_WORK_TREE: $(env | grep -c -E '^GIT_(DIR|WORK_TREE)=')"
[ -n "$GUARD" ] && say "  guard $GUARD sha256 $(sha256sum "$GUARD" | cut -c1-64)"
rm -rf "$BT"
say "VERDICT: $([ "$fail" = 0 ] && echo 'LAYER 3 EXERCISED AND HELD' || echo 'FAILED')  $(date -u +%FT%TZ)"
exit "$fail"
