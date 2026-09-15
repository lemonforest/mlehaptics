#!/bin/bash
# rc473 instrument repair 1 (`#T1188`): is the ripple manifest's one failure environmental at this head?
#
# The committed, runnable form of notes/_rc473_scratch/fr1/w_env428.sh and w_env428_norm.sh (archived
# records whose paths name the scratch directory). Runs
#   tests/test_citation_manifest_rc428.py::test_the_validate_entry_point_exits_nonzero_on_a_failing_control
# ALONE in the native clone at the commit under test and in the base clone at 1ab8d405b — clone paths of
# equal length — and compares the failure lines with the clone path and uv's per-run interpreter
# directory normalised out.
#
# Usage (WSL2):  bash notes/_rc473_instr_r1_env428.sh <native clone root> <base clone root>
# Both roots are git clones (`.git` a directory) with 0 tracked changes; the base clone must already be
# at 1ab8d405b (this script refuses rather than move it). Refuses an exported GIT_DIR / GIT_WORK_TREE.
set -u
R=${1:?native clone}; BASE=${2:?base clone}
export PATH="$HOME/.local/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE SRMECH_EXPECT_PURE PYTEST_ADDOPTS
n=$(env | grep -c -E '^GIT_(DIR|WORK_TREE)=')
echo "exported GIT_DIR/GIT_WORK_TREE: $n  live .git/config $(sha256sum /mnt/d/GitHub/mlehaptics/.git/config | cut -c1-16)  $(date -u +%FT%TZ)"
[ "$n" = 0 ] || { echo "REFUSED: exported GIT_DIR/GIT_WORK_TREE"; exit 2; }
[ "$(git -C "$BASE" rev-parse HEAD)" = "$(git -C "$BASE" rev-parse 1ab8d405b)" ] || { echo "REFUSED: $BASE is not at 1ab8d405b"; exit 2; }
O=$HOME/rc473c/out/ir1_env428; mkdir -p "$O"
NODE="tests/test_citation_manifest_rc428.py::test_the_validate_entry_point_exits_nonzero_on_a_failing_control"
for t in "$R" "$BASE"; do
  tag=$(basename "$t")
  case "$t" in /mnt/*) echo "REFUSED: $t is under /mnt"; exit 2;; esac
  echo "=== $tag HEAD $(git -C "$t" rev-parse HEAD) path chars $(printf %s "$t" | wc -c) tracked changes $(git -C "$t" status --porcelain --untracked-files=no | wc -l) libs $(find "$t/docs/srmech/python" -name 'libsrmech*' | wc -l)"
  (cd "$t/docs/srmech/python" && uv run --python 3.12 --no-project --offline --with pytest python -m pytest -q -p no:cacheprovider -rfE "$NODE") > "$O/$tag.log" 2>&1
  echo "  exit $?: $(tail -1 "$O/$tag.log")"
  grep -E "^E " "$O/$tag.log" | sed "s#$t#<clone>#g" | sed -E 's#/builds-v0/\.tmp[A-Za-z0-9_]+/#/builds-v0/<uv-tmp>/#g' > "$O/$tag.norm"
  echo "  normalised E lines: $(wc -l < "$O/$tag.norm")"
done
if cmp -s "$O/$(basename "$R").norm" "$O/$(basename "$BASE").norm"; then
  echo "normalised failure lines IDENTICAL"
else
  echo "normalised failure lines DIFFER:"; diff "$O/$(basename "$R").norm" "$O/$(basename "$BASE").norm" | head -20
fi
head -3 "$O/$(basename "$R").norm" | cut -c1-240
for t in "$R" "$BASE"; do echo "$t tracked changes at end $(git -C "$t" status --porcelain --untracked-files=no | wc -l)"; done
echo "end live .git/config $(sha256sum /mnt/d/GitHub/mlehaptics/.git/config | cut -c1-16)  $(date -u +%FT%TZ)"
