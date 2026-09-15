#!/bin/bash
# rc473 final repair 1: D1's two measurements.
#  (a) the final round's group-4 clones: is their .git a directory?
#  (b) Layer 3 end to end: notes/_rc473_final_layer3_geometry.sh from the Windows worktree
#      (LF bytes, compared below with the file the CHANGELOG commit will carry), over the
#      pure clone's HEAD, in a Windows-made worktree under C:/Users/sckir/rc473c_win/fr1/l3.
# No GIT_DIR / GIT_WORK_TREE exported anywhere in this script.
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
INSTR=/mnt/d/GitHub/mlehaptics/.claude/worktrees/wf_5285136b-875-6/docs/srmech/notes/_rc473_final_layer3_geometry.sh
echo "exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] $(date -u +%FT%TZ)"
for t in repo pure; do
  echo "~/rc473c/$t/.git: $(test -d $G/$t/.git && echo directory || (test -f $G/$t/.git && echo FILE || echo absent))  HEAD $(git -C $G/$t rev-parse HEAD)"
done
echo "instrument sha256 $(sha256sum $INSTR | cut -c1-64)  CR bytes $(tr -cd '\r' < $INSTR | wc -c)"
PY="uv run --python 3.12 --no-project --offline --with pytest python" bash $INSTR $G/pure /mnt/c/Users/sckir/rc473c_win/fr1/l3 /mnt/d/GitHub/mlehaptics/.git/config
echo "instrument exit $?  $(date -u +%FT%TZ)"
