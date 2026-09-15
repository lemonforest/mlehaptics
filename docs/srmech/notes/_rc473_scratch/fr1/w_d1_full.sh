#!/bin/bash
# rc473 final repair 1: D1's analysis printed in FULL (the final round's w_d1d2.sh pipes it
# through `tail`, which cut the filed-24 / extra-21 lines at this head), over the d1.json that
# w_d1d2.sh dumped at this head, plus a full diff of the two served-value witness outputs (its
# `^V` count predicate matches no line that witness prints). No GIT_DIR / GIT_WORK_TREE exported.
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
PP=$G/pure/docs/srmech/python
N=$G/repo/docs/srmech/notes
O=$G/out/final_d1d2
echo "exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] repo HEAD $(git -C $G/repo rev-parse HEAD) pure HEAD $(git -C $G/pure rev-parse HEAD) pure libs $(find $G/pure -name 'libsrmech*' | wc -l) d1.json $(stat -c '%y %s' $O/d1.json) $(date -u +%FT%TZ)"
SRMECH_EXPECT_PURE=1 uv run --python 3.12 --no-project --offline python $N/_rc473_twin_d1_analyze.py $PP after $O/d1.json > $O/d1_analyze_full.txt 2>&1
echo "analyze exit $?, $(wc -l < $O/d1_analyze_full.txt) lines:"
grep -v -E "^door " $O/d1_analyze_full.txt
echo "=== witness outputs: native $(wc -l < $O/witness_native.txt) lines, pure $(wc -l < $O/witness_pure.txt) lines, differing lines: $(diff $O/witness_native.txt $O/witness_pure.txt | grep -c '^[<>]')"
echo "end $(date -u +%FT%TZ)"
