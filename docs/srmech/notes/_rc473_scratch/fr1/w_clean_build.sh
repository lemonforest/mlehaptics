#!/bin/bash
# rc473 final repair 1: a CLEAN gcc pedantic Release build of the WSL native clone's HEAD in
# a fresh build directory (~/rc473c/build_fr1), ctest, library facts, the library installed
# into the native clone, authenticated. The final round's w_clean_build.sh printed no count
# of exported GIT_DIR / GIT_WORK_TREE; this copy prints it. Usage: w_clean_build.sh
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
H=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
B=$G/build_fr1
echo "exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] HEAD $(git -C $G/repo rev-parse HEAD) tracked changes $(git -C $G/repo status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ)"
echo "gcc: $(gcc --version | head -1)  cmake: $(cmake --version | head -1)  free: $(df -h / | tail -1 | tr -s ' ' | cut -d' ' -f4)"
rm -rf $B
cmake -S $G/repo/docs/srmech -B $B -G Ninja -DCMAKE_BUILD_TYPE=Release -DSRMECH_PEDANTIC=ON > $G/logs/fr1_clean_configure.log 2>&1
echo "configure exit $?  $(grep -o 'SRMECH_PEDANTIC=ON[^\"]*' $G/logs/fr1_clean_configure.log | head -1)"
cmake --build $B -- -k 0 > $G/logs/fr1_clean_build.log 2>&1
echo "build exit $?  warnings: $(grep -c 'warning:' $G/logs/fr1_clean_build.log)  errors: $(grep -c 'error:' $G/logs/fr1_clean_build.log)  last: $(tail -1 $G/logs/fr1_clean_build.log | cut -c1-60)"
echo "-Werror in build.ninja: $(grep -o -- '-Werror' $B/build.ninja | wc -l)  nm __assert_fail: $(nm -D $B/libsrmech.so | grep -c __assert_fail)"
echo "lib $(sha256sum $B/libsrmech.so | cut -c1-16)"
(cd $B && ctest 2>&1 | tail -3)
cp $B/libsrmech.so $G/repo/docs/srmech/python/srmech/_native/
cd $G/repo/docs/srmech/python
uv run --python 3.12 --no-project --offline python $H/auth.py $PWD | grep -E "_native.__file__|lib sha256|abi / c|AUTH"
echo "pure clone libs: $(find $G/pure -name 'libsrmech*' | wc -l)  $(date -u +%FT%TZ)"
