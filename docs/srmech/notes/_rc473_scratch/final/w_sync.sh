#!/bin/bash
# rc473 final round: bring the two WSL clones (~/rc473c/repo native, ~/rc473c/pure
# pure) to a pushed SHA of srmech-rc473, read-only on the live repository (a fetch
# of its remote-tracking ref), then rebuild the native library incrementally and
# install it. No GIT_DIR / GIT_WORK_TREE is exported anywhere in this script.
# Usage: w_sync.sh <sha>
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
SHA=$1
G=~/rc473c
S=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
echo "exported GIT vars: [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')]  $(date -u +%FT%TZ)"
for t in repo pure; do
  git -C $G/$t fetch -q origin refs/remotes/origin/srmech-rc473:refs/remotes/origin/srmech-rc473 2>&1 | tail -2
  git -C $G/$t checkout -q -f --detach $SHA
  echo "$t HEAD $(git -C $G/$t rev-parse HEAD) tracked changes $(git -C $G/$t status --porcelain --untracked-files=no | wc -l)"
done
rm -f $G/pure/docs/srmech/python/srmech/_native/libsrmech*
echo "pure libs: $(find $G/pure -name 'libsrmech*' | wc -l)"
cmake --build $G/build -- -k 0 > $G/logs/final_sync_build.log 2>&1
echo "build exit $?  warnings: $(grep -c 'warning:' $G/logs/final_sync_build.log)  errors: $(grep -c 'error:' $G/logs/final_sync_build.log)  last: $(tail -1 $G/logs/final_sync_build.log | cut -c1-80)"
echo "__assert_fail: $(nm -D $G/build/libsrmech.so | grep -c __assert_fail)  -Werror: $(grep -o -- '-Werror' $G/build/build.ninja | wc -l)"
cp $G/build/libsrmech.so $G/repo/docs/srmech/python/srmech/_native/
echo "lib $(sha256sum $G/build/libsrmech.so | cut -c1-16)"
cd $G/repo/docs/srmech/python
uv run --python 3.12 --no-project --offline python $S/auth.py $PWD | grep -E "python|_native.__file__|lib sha256|abi / c|AUTH|numpy"
date -u +%FT%TZ
