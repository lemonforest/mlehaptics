#!/bin/bash
# rc473 final repair 1: the planted regressions of the final-round gate's blocking findings,
# in the WSL PURE clone (~/rc473c/pure, 0 library files), at the pushed head. No GIT_DIR /
# GIT_WORK_TREE exported anywhere in this script; git runs here are read-only on the clone.
# Usage: w_plants.sh <leak|phrases>
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
WHAT=$1
G=~/rc473c
H=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
T=$G/pure
O=$G/out/fr1
mkdir -p $O
export SRMECH_EXPECT_PURE=1
echo "exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] ALLOW_STALE=${SRMECH_ALLOW_STALE_NATIVE:-unset} HEAD $(git -C $T rev-parse HEAD) tracked changes $(git -C $T status --porcelain --untracked-files=no | wc -l) libs $(find $T -name 'libsrmech*' | wc -l) $(date -u +%FT%TZ)"
cd $T/docs/srmech/python
uv run --python 3.12 --no-project --offline python $H/auth.py $PWD | grep -E "python |HAS_NATIVE|numpy"
case $WHAT in
  leak)
    git -C $T show 52371629a:docs/srmech/python/tests/test_hook_fixture_env_isolation_rc471.py > $O/rc471_at_52371629a.py
    echo "rc471 blob at 52371629a: $(wc -c < $O/rc471_at_52371629a.py) bytes; tree $(wc -c < tests/test_hook_fixture_env_isolation_rc471.py) bytes"
    rm -f $O/plants_wsl.ndjson
    export FR1_RC471_BLOB=$O/rc471_at_52371629a.py FR1_BASETEMP=$O/bt
    uv run --python 3.12 --no-project --offline python $H/fr1/plants.py $PWD $O/plants_wsl.ndjson \
      arm3_zero_cases,m1_helpers_inherit,m1_file_revert,m2_unwire,x_walk_dir,gap_single_backslash \
      -- uv run --python 3.12 --no-project --offline --with pytest python -m pytest
    echo "driver exit $?" ;;
  phrases)
    uv run --python 3.12 --no-project --offline python $H/gate_f1_canfail/phrase_plants.py $T $O/m4_phrases.ndjson > $O/m4_phrases.log 2>&1
    echo "driver exit $?"
    uv run --python 3.12 --no-project --offline python - $O/m4_phrases.ndjson <<'PYEOF'
import json, sys
from collections import Counter
rows = [json.loads(l) for l in open(sys.argv[1])]
c = Counter((r["form"], r["surface"] if r["form"] != "native" else "all six", r["gate_red"], r["direct_scan"]) for r in rows)
print("plants", len(rows))
for (form, surf, red, scan), n in sorted(c.items()):
    print(f"  form={form:6s} surface={surf:48s} gate_red={red!s:5s} own-phrase scan={scan!s:5s} : {n}")
green = [r["key"] + "@" + r["surface"] + "[" + r["form"] + "]" for r in rows if not r["gate_red"]]
print("GREEN plants:", green)
PYEOF
    ;;
esac
echo "tracked changes after $(git -C $T status --porcelain --untracked-files=no | wc -l)  $(date -u +%FT%TZ)"
