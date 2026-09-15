#!/bin/bash
# rc473 final round: regenerate on the synced native WSL clone (CPython 3.12,
# authenticated), report the refusal, accept the deliberate curated drift, --check,
# and copy the changed generated outputs out. No GIT_DIR exported.
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
S=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
O=/mnt/c/Users/sckir/rc473c_win/final/regen_out
PY="uv run --python 3.12 --no-project --offline python"
cd $G/repo/docs/srmech/python
echo "HEAD $(git -C $G/repo rev-parse HEAD) tracked changes $(git -C $G/repo status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ)"
$PY $S/auth.py $PWD | grep -E "_native.__file__|lib sha256|abi / c|AUTH"
echo "=== regen (no flags) $(date -u +%FT%TZ)"
$PY tools/regen_all.py > $G/logs/final_regen1.log 2>&1; echo "exit $?"
grep -E "REFUSED|field\(s\)|DESTROYED|WROTE|same|OK" $G/logs/final_regen1.log | cut -c1-400 | tail -12
echo "=== regen --accept-seed-drift $(date -u +%FT%TZ)"
$PY tools/regen_all.py --accept-seed-drift > $G/logs/final_regen2.log 2>&1; echo "exit $?"
tail -12 $G/logs/final_regen2.log | cut -c1-300
echo "=== --check $(date -u +%FT%TZ)"
$PY tools/regen_all.py --check 2>&1 | tail -3
echo "=== numstat in the clone"
git -C $G/repo diff --numstat
mkdir -p $O
cp srmech/introspect/_tool_docs.py $O/_tool_docs.py
cp ../c/src/srmech_tool_registry.c $O/srmech_tool_registry.c
echo "CR bytes: _tool_docs.py $(tr -cd '\r' < $O/_tool_docs.py | wc -c)  registry $(tr -cd '\r' < $O/srmech_tool_registry.c | wc -c)"
sha256sum $O/_tool_docs.py $O/srmech_tool_registry.c | cut -c1-16
date -u +%FT%TZ
