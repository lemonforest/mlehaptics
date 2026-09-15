#!/bin/bash
# rc473 final round: the WHOLE ripple manifest, native, in the WSL clone
# ~/rc473c/repo (no .claude / worktrees component, no GIT_DIR exported), split
# into foreground parts whose union is the manifest. Usage: w_ripple.sh split <n> | part <i>
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
H=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
PY="uv run --python 3.12 --no-project --offline python"
PARTS=$G/out/final_rparts
cd $G/repo/docs/srmech/python
echo "=== $* HEAD $(git -C $G/repo rev-parse HEAD) tracked changes $(git -C $G/repo status --porcelain --untracked-files=no | wc -l) exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] $(date -u +%FT%TZ)"
case $1 in
  split)
    N=$2
    rm -rf $PARTS && mkdir -p $PARTS
    $PY $H/m_ripple_split.py tools/ripple_gates.txt $N $PARTS > $G/logs/final_rsplit.log 2>&1; echo "split exit $?"; tail -$((N+2)) $G/logs/final_rsplit.log
    $PY - "$PARTS" "$N" <<'PYEOF'
import sys
from pathlib import Path
parts_dir, n = Path(sys.argv[1]), int(sys.argv[2])
def targets(p):
    return [s.strip() for s in p.read_text().splitlines() if s.strip() and not s.strip().startswith('#')]
src = targets(Path('tools/ripple_gates.txt'))
parts = []
for i in range(1, n + 1):
    parts += targets(parts_dir / ('ripple_part%d.txt' % i))
print('manifest targets', len(src), 'in parts', len(parts), 'unique', len(set(parts)), 'union equal', sorted(src) == sorted(parts))
PYEOF
    ;;
  part)
    P=$2
    $PY $H/auth.py $PWD | grep -E "_native.__file__|lib sha256|abi / c|AUTH"
    echo "targets in part $P: $(grep -c . $PARTS/ripple_part$P.txt)"
    timeout 590 uv run --python 3.12 --no-project --offline --with pytest python tools/ripple_check.py --manifest $PARTS/ripple_part$P.txt > $G/logs/final_ripple_part$P.log 2>&1
    echo "ripple_check exit $?"
    grep -E "^(FAILED|ERROR) " $G/logs/final_ripple_part$P.log | cut -c1-240 | head -20
    tail -2 $G/logs/final_ripple_part$P.log
    echo "tracked changes after $(git -C $G/repo status --porcelain --untracked-files=no | wc -l)" ;;
esac
date -u +%FT%TZ
