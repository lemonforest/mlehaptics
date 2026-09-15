#!/bin/bash
# rc473 final round: incremental pedantic build of the native clone's working tree,
# install the library, authenticate. Usage: w_build.sh
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
S=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
echo "HEAD $(git -C $G/repo rev-parse HEAD) tracked changes $(git -C $G/repo status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ)"
cmake --build $G/build -- -k 0 > $G/logs/final_build.log 2>&1
echo "build exit $?  warnings: $(grep -c 'warning:' $G/logs/final_build.log)  errors: $(grep -c 'error:' $G/logs/final_build.log)  last: $(tail -1 $G/logs/final_build.log | cut -c1-80)"
echo "__assert_fail: $(nm -D $G/build/libsrmech.so | grep -c __assert_fail)"
cp $G/build/libsrmech.so $G/repo/docs/srmech/python/srmech/_native/
echo "lib $(sha256sum $G/build/libsrmech.so | cut -c1-16)"
cd $G/repo/docs/srmech/python
uv run --python 3.12 --no-project --offline python $S/auth.py $PWD | grep -E "_native.__file__|lib sha256|abi / c|AUTH"
date -u +%FT%TZ
