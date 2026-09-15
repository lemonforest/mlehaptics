#!/bin/bash
# rc473 final round: WITNESS_RC416 on the native clone's working tree (the regenerated
# content), determinism in three fresh interpreters, the search witness, a pure
# snapshot, and the cause isolated against 52371629a's blobs in BOTH directions:
# each differing package file reverted ALONE (then restored), and each applied ALONE
# onto an all-reverted tree (then reverted), then all together. No GIT_DIR exported.
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
S=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
BASE=52371629a1cca618e33472320a0b35c24e6a15cb
PY="uv run --python 3.12 --no-project --offline python"
cd $G/repo/docs/srmech/python
echo "HEAD $(git -C $G/repo rev-parse HEAD) tracked changes $(git -C $G/repo status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ)"
$PY $S/auth.py $PWD | grep -E "_native.__file__|lib sha256|abi / c|AUTH"
cat > $G/out/final_wdig.py <<'PYEOF'
import os
import sys
sys.path.insert(0, os.getcwd())
from srmech.introspect import search as S
from srmech import _native as n
reps = int(sys.argv[1]) if len(sys.argv) > 1 else 1
ds = set()
for _ in range(reps):
    frames, w = S._build_frames("all")
    ds.add(w)
ops, _ = S._build_frames("ops")
car, _ = S._build_frames("carriers")
print(len(frames), "=", len(ops), "+", len(car), "digests", sorted(ds), "native", n.HAS_NATIVE)
PYEOF
echo "=== package files differing from $BASE (working tree)"
git -C $G/repo diff --name-only $BASE -- docs/srmech/python/srmech
echo "=== determinism: 5 builds in each of 3 fresh interpreters"
for i in 1 2 3; do $PY $G/out/final_wdig.py 5; done
echo "=== search('rank', k=1).witness"
$PY -c "from srmech.introspect.search import search; print(search('rank', k=1).witness)"
FILES="srmech/introspect/_tool_docs.py srmech/introspect/_tool_docs_curated.py srmech/math/kepler.py"
mkdir -p $G/wsave_final
for f in $FILES; do cp $f $G/wsave_final/$(basename $f); done
echo "=== each ALONE reverted to $BASE"
for f in $FILES; do
  git -C $G/repo show $BASE:docs/srmech/python/$f > $f
  echo "--- $f reverted alone"; $PY $G/out/final_wdig.py 1
  cp $G/wsave_final/$(basename $f) $f
done
echo "=== all three reverted"
for f in $FILES; do git -C $G/repo show $BASE:docs/srmech/python/$f > $f; done
$PY $G/out/final_wdig.py 1
echo "=== each ALONE applied onto the all-reverted tree"
for f in $FILES; do
  cp $G/wsave_final/$(basename $f) $f
  echo "--- $f applied alone"; $PY $G/out/final_wdig.py 1
  git -C $G/repo show $BASE:docs/srmech/python/$f > $f
done
echo "=== restored all"
for f in $FILES; do cp $G/wsave_final/$(basename $f) $f; done
$PY $G/out/final_wdig.py 1
echo "restored byte-identical: $(for f in $FILES; do cmp -s $f $G/wsave_final/$(basename $f) && echo same || echo DIFF; done | sort | uniq -c | tr '\n' ' ')"
echo "=== pure snapshot"
rm -rf $G/wpure_final && mkdir -p $G/wpure_final && cp -a $G/repo/docs $G/wpure_final/ && rm -f $G/wpure_final/docs/srmech/python/srmech/_native/libsrmech.so
cd $G/wpure_final/docs/srmech/python && echo "libs=$(find . -name 'libsrmech*' | wc -l)" && SRMECH_EXPECT_PURE=1 GIT_CEILING_DIRECTORIES=$G/wpure_final $PY $G/out/final_wdig.py 1
rm -rf $G/wpure_final
echo "tracked changes in the clone now: $(git -C $G/repo status --porcelain --untracked-files=no | wc -l)"
date -u +%FT%TZ
