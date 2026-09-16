#!/bin/bash
# rc473 final repair 1: the gate_f1 can-fail lens's phrase plants (its own driver, unchanged,
# over a slice of its 111 plans) in the WSL PURE clone at the pushed head. No GIT_DIR /
# GIT_WORK_TREE exported. Usage: w_phr.sh <start> <end> | summary
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
H=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
T=$G/pure
O=$G/out/fr1
mkdir -p $O
export SRMECH_EXPECT_PURE=1
echo "exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] HEAD $(git -C $T rev-parse HEAD) tracked changes $(git -C $T status --porcelain --untracked-files=no | wc -l) libs $(find $T -name 'libsrmech*' | wc -l) $(date -u +%FT%TZ)"
if [ "$1" = summary ]; then
  uv run --python 3.12 --no-project --offline python - $O/m4_phrases.ndjson <<'PYEOF'
import json, sys
from collections import Counter
rows = [json.loads(l) for l in open(sys.argv[1])]
print("plants", len(rows), "distinct (key, surface, form)", len({(r["key"], r["surface"], r["form"]) for r in rows}))
c = Counter((r["form"], r["surface"] if r["form"] != "native" else "all six surfaces", r["gate_red"], r["direct_scan"]) for r in rows)
for (form, surf, red, scan), n in sorted(c.items()):
    print(f"  form={form:6s} surface={surf:48s} gate_red={red!s:5s} own-phrase scan={scan!s:5s} : {n}")
print("GREEN plants:", [r["key"] + "@" + r["surface"] + "[" + r["form"] + "]" for r in rows if not r["gate_red"]])
print("non-1 exits:", sorted({r["exit"] for r in rows}))
PYEOF
else
  [ "$1" = 0 ] && rm -f $O/m4_phrases.ndjson
  # --with pytest: the driver imports the gate module, which imports pytest (a first run
  # without it exited 1 at the import, before any plant: an instrument error, not counted).
  uv run --python 3.12 --no-project --offline --with pytest python $H/fr1/phrase_plants_part.py $T $O/m4_phrases.ndjson $1 $2 > $O/m4_phrases_$1.log 2>&1
  echo "driver exit $?"
  grep -E "^driver sha256|^plans" $O/m4_phrases_$1.log
  grep -c -E "^RED " $O/m4_phrases_$1.log | sed 's/^/RED lines: /'
  grep -E "^GREEN " $O/m4_phrases_$1.log | cut -c1-200
fi
echo "tracked changes after $(git -C $T status --porcelain --untracked-files=no | wc -l)  $(date -u +%FT%TZ)"
