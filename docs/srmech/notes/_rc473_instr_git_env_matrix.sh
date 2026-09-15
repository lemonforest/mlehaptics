#!/bin/bash
# rc473 instrument round (`#T1188`): which inherited git variables move a sentinel
# repository, measured on WHICHEVER git runs this script — so tests/_git_env.py's
# docstring can state the matrix per git rather than for one.
#
# For each variable, with a FRESH sentinel S (extensions.worktreeConfig on, one commit,
# one worktree SW) and a fresh temp directory T under the sandbox, the fixture sequence
#   git init; git config --local user.name; git config --local user.email; git add; git commit
# runs in T with that ONE variable given to each command by `env NAME=VALUE` — never
# exported in this shell. S's gitdir outside objects/ is digested with its object count
# before and after. Each git step's exit status is printed, so a sequence that FAILED
# (and therefore moved nothing) is not read as a variable that is harmless.
# GIT_CONFIG is also run as `git config user.name` WITHOUT --local.
#
# Usage:  bash notes/_rc473_instr_git_env_matrix.sh <sandbox dir, removed and recreated>
# Runs under WSL2 bash and under Git Bash on Windows (where `git` is Git for Windows).
# Read-only outside <sandbox dir>. numpy-free; no hashlib; no abs().
set -u
E=${1:?sandbox dir}
case "$E" in /|"$HOME"|/mnt/[a-z]|/[a-z]) echo "REFUSED: sandbox dir $E is not a scratch directory"; exit 2;; esac
n_exported=$(env | grep -c -E '^GIT_(DIR|WORK_TREE)=')
echo "exported GIT_DIR/GIT_WORK_TREE: $n_exported  $(date -u +%FT%TZ)"
[ "$n_exported" = 0 ] || { echo "REFUSED: never run under an exported GIT_DIR/GIT_WORK_TREE"; exit 2; }
for v in $(git rev-parse --local-env-vars) GIT_NAMESPACE GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM; do unset "$v"; done
echo "git: $(git --version)  uname: $(uname -s)"
export GIT_CEILING_DIRECTORIES=$E
digest() {
  (cd "$1/.git" && find . -path ./objects -prune -o -type f -print0 | sort -z | xargs -0 cat | sha256sum | cut -c1-12
   find "$1/.git/objects" -type f | wc -l) | tr '\n' ' '
}
mk() {
  rm -rf "$E"; mkdir -p "$E/S"
  git -C "$E/S" init -q -b main
  git -C "$E/S" config --local user.name "Sentinel Owner"
  git -C "$E/S" config --local user.email s@example.invalid
  git -C "$E/S" config --local extensions.worktreeConfig true
  echo x > "$E/S/f.txt"; git -C "$E/S" add -- f.txt
  git -C "$E/S" -c commit.gpgsign=false commit -q -m s
  git -C "$E/S" worktree add -q -b w "$E/SW" > /dev/null 2>&1
}
seq_with() { # NAME=VALUE -> prints "init=<rc> cfg1=<rc> cfg2=<rc> add=<rc> commit=<rc>"
  local T; T=$(mktemp -d "$E/t.XXXX")
  (cd "$T" || exit 9
   env "$1" git init -q -b main > /dev/null 2>&1; a=$?
   env "$1" git config --local user.name fixture > /dev/null 2>&1; b=$?
   env "$1" git config --local user.email fixture@example.invalid > /dev/null 2>&1; c=$?
   echo a > a.txt; env "$1" git add -- a.txt > /dev/null 2>&1; d=$?
   env "$1" git -c user.name=fixture -c user.email=f@example.invalid -c commit.gpgsign=false commit -q -m t > /dev/null 2>&1; e=$?
   echo "init=$a cfg1=$b cfg2=$c add=$d commit=$e")
}
for v in "GIT_DIR=@S/.git/worktrees/SW" "GIT_DIR=@S/.git" "GIT_INDEX_FILE=@S/.git/index" \
         "GIT_OBJECT_DIRECTORY=@S/.git/objects" "GIT_COMMON_DIR=@S/.git" "GIT_CONFIG=@S/.git/config"; do
  mk; spec=${v/@/$E/}; before=$(digest "$E/S")
  steps=$(seq_with "$spec"); after=$(digest "$E/S")
  [ "$before" = "$after" ] && r=unchanged || r=MOVED
  printf '%-36s steps [%s] sentinel [%s] -> [%s] %s; S user.name %s\n' "${v%%=*}=${v#*=}" "$steps" \
    "$before" "$after" "$r" "$(git -C "$E/S" config --local --get user.name)"
done
mk; before=$(digest "$E/S"); T=$(mktemp -d "$E/t.XXXX")
(cd "$T" && env GIT_CONFIG="$E/S/.git/config" git config user.name redirected > /dev/null 2>&1; echo "GIT_CONFIG, git config WITHOUT --local: exit $?")
after=$(digest "$E/S")
echo "  sentinel [$before] -> [$after] $([ "$before" = "$after" ] && echo unchanged || echo MOVED); S user.name $(git -C "$E/S" config --local --get user.name)"
rm -rf "$E"
echo "end $(date -u +%FT%TZ) sandbox removed: $([ -e "$E" ] && echo no || echo yes)"
