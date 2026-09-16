#!/bin/bash
# rc473 final repair 1: re-normalise the two saved logs of w_env428.sh. Its first comparison
# normalised only the clone path and printed DIFFER on one line, which differed only in uv's
# per-invocation interpreter directory (~/.cache/uv/builds-v0/.tmpXXXXXX). This removes that
# too and compares again. No test is re-run. No GIT_DIR / GIT_WORK_TREE exported.
set -u
G=~/rc473c
O=$G/out/fr1
echo "exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] $(date -u +%FT%TZ)"
for t in repo base; do
  grep -E "^E " $O/env428_$t.log | sed "s#$G/$t#<clone>#g" | sed -E 's#/builds-v0/\.tmp[A-Za-z0-9_]+/#/builds-v0/<uv-tmp>/#g' > $O/env428_$t.norm2
  echo "$t: tally [$(tail -1 $O/env428_$t.log)]  normalised E lines $(wc -l < $O/env428_$t.norm2)"
done
if cmp -s $O/env428_repo.norm2 $O/env428_base.norm2; then echo "normalised failure lines IDENTICAL"; else echo "normalised failure lines DIFFER:"; diff $O/env428_repo.norm2 $O/env428_base.norm2 | head -10; fi
