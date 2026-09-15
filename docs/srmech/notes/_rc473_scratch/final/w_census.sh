#!/bin/bash
# rc473 final round: the demotion census regenerated from an EMPTY manifest (pure
# column first, native column merged), then diffed against the committed census by
# tools/census_regen_diff.py. Usage: w_census.sh <pure|native|diff>
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
STEP=$1
G=~/rc473c
H=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
OUT=$G/out/final_census_regen.ndjson
PY="uv run --python 3.12 --no-project --offline python"
RUN='import sys, time
from pathlib import Path
sys.path.insert(0, "tools")
import demotion_probe as d
from srmech import _native as n
print("HAS_NATIVE", n.HAS_NATIVE, n.__file__, "cell", d.cell())
t = time.time()
m = d.merge_cell(Path(sys.argv[1]), progress=False)
print("seconds %.1f" % (time.time() - t))
print({k: m.get(k) for k in ("n_rows", "n_ops", "cells_measured", "by_verdict")})'
echo "step $STEP $(date -u +%FT%TZ) exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')]"
case $STEP in
  pure)
    cd $G/pure/docs/srmech/python
    echo "HEAD $(git -C $G/pure rev-parse HEAD) libs $(find $G/pure -name 'libsrmech*' | wc -l)"
    rm -f $OUT
    echo "manifest before: $(test -f $OUT && echo PRESENT || echo EMPTY)"
    PYTHONPATH=$PWD SRMECH_EXPECT_PURE=1 timeout 590 $PY -c "$RUN" $OUT 2>&1 | tail -4 ;;
  native)
    cd $G/repo/docs/srmech/python
    echo "HEAD $(git -C $G/repo rev-parse HEAD) libs $(find . -name 'libsrmech*' | wc -l)"
    $PY $H/auth.py $PWD | grep -E "_native.__file__|lib sha256|abi / c|AUTH"
    PYTHONPATH=$PWD timeout 590 $PY -c "$RUN" $OUT 2>&1 | tail -4 ;;
  diff)
    cd $G/repo/docs/srmech/python
    git -C $G/repo show HEAD:docs/srmech/python/tests/demotion_census.ndjson > $G/out/final_census_committed.ndjson
    $PY tools/census_regen_diff.py $G/out/final_census_committed.ndjson $OUT 2>&1 | tail -40 ;;
esac
date -u +%FT%TZ
