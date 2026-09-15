#!/bin/bash
# rc473 final round: run the COMMITTED citation census scripts in report mode at the
# clone's HEAD, then replay truth repair 1's applied run on d346173fc's curated file
# in a separate throwaway clone checkout (pass 1 --apply --overrides, then pass 2
# --apply), printing each verdict tally. No GIT_DIR exported; the scripts' own
# `git ls-files` runs with cwd = the checkout, which is a real clone here.
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
set -u
G=~/rc473c
R=$G/repo/docs/srmech
PY="uv run --python 3.12 --no-project --offline python"
O=$G/out/final_cite
rm -rf $O && mkdir -p $O
echo "=== HEAD $(git -C $G/repo rev-parse HEAD) report mode $(date -u +%FT%TZ)"
cd $R
$PY notes/_rc473_truth_repair1_cite_pass1.py . $O/pass1_head.tsv | tail -3
$PY notes/_rc473_truth_repair1_cite_pass2.py . $O/pass2_head.tsv | tail -2
echo "tracked changes after report mode: $(git -C $G/repo status --porcelain --untracked-files=no | wc -l)"
echo "=== replay on d346173fc (throwaway clone) $(date -u +%FT%TZ)"
rm -rf $G/replay_d346
git clone -q --no-checkout $G/repo $G/replay_d346
git -C $G/replay_d346 checkout -q --detach d346173fc45b398e588dfdfd1cb690b70bc823e8
echo "replay HEAD $(git -C $G/replay_d346 rev-parse HEAD)"
# the scripts are committed AFTER d346173fc: run the HEAD copies against the old tree
mkdir -p $O/scripts
cp $R/notes/_rc473_truth_repair1_cite_pass1.py $R/notes/_rc473_truth_repair1_cite_pass2.py $R/notes/_rc473_truth_repair1_cite_overrides.py $O/scripts/
cd $G/replay_d346/docs/srmech
$PY $O/scripts/_rc473_truth_repair1_cite_pass1.py . $O/pass1_replay.tsv --apply --overrides $O/scripts/_rc473_truth_repair1_cite_overrides.py | tail -6
$PY $O/scripts/_rc473_truth_repair1_cite_pass2.py . $O/pass2_replay.tsv --apply | tail -3
rm -rf $G/replay_d346
echo "replay clone removed: $(test -d $G/replay_d346 && echo no || echo yes)  $(date -u +%FT%TZ)"
