#!/bin/bash
# rc473 final repair 1: is the ripple manifest's one failure environmental at this head? Run
# test_citation_manifest_rc428.py::test_the_validate_entry_point_exits_nonzero_on_a_failing_control
# ALONE at the code head (~/rc473c/repo) and at the rc473 base 1ab8d405b (~/rc473c/base), clone
# paths of equal length, and compare the failure lines with the clone path normalised out.
# No GIT_DIR / GIT_WORK_TREE exported; git runs are on the WSL clones only.
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
O=$G/out/fr1
mkdir -p $O
NODE="tests/test_citation_manifest_rc428.py::test_the_validate_entry_point_exits_nonzero_on_a_failing_control"
echo "exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] $(date -u +%FT%TZ)"
echo "base clone HEAD before: $(git -C $G/base rev-parse HEAD) tracked changes $(git -C $G/base status --porcelain --untracked-files=no | wc -l)"
if [ "$(git -C $G/base rev-parse HEAD)" != "$(git -C $G/base rev-parse 1ab8d405b)" ]; then
  git -C $G/base checkout -q -f --detach 1ab8d405b
  echo "base clone moved to $(git -C $G/base rev-parse HEAD)"
fi
for t in repo base; do
  P=$G/$t/docs/srmech/python
  echo "=== $t HEAD $(git -C $G/$t rev-parse HEAD) path chars $(printf %s "$G/$t" | wc -c) tracked changes $(git -C $G/$t status --porcelain --untracked-files=no | wc -l) libs $(find $G/$t/docs/srmech/python -name 'libsrmech*' | wc -l)"
  (cd $P && uv run --python 3.12 --no-project --offline --with pytest python -m pytest -q -p no:cacheprovider -rfE "$NODE") > $O/env428_$t.log 2>&1
  echo "  exit $?: $(tail -1 $O/env428_$t.log)"
  grep -E "^E " $O/env428_$t.log | sed "s#$G/$t#<clone>#g" > $O/env428_$t.norm
  echo "  normalised E lines: $(wc -l < $O/env428_$t.norm)"
done
if cmp -s $O/env428_repo.norm $O/env428_base.norm; then echo "normalised failure lines IDENTICAL"; else echo "normalised failure lines DIFFER:"; diff $O/env428_repo.norm $O/env428_base.norm | head -20; fi
head -5 $O/env428_repo.norm | cut -c1-240
echo "end $(date -u +%FT%TZ)"
