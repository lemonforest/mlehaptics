#!/bin/bash
# rc473 final round: at the FINAL head, prove the code trees equal the validated code
# head's, then run the CHANGELOG-reading gates in both cells. No GIT_DIR exported.
# Usage: w_final_head.sh <code head sha> <final head sha>
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
CODE=$1; FINAL=$2
G=~/rc473c
H=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
echo "exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] $(date -u +%FT%TZ)"
for d in docs/srmech/c docs/srmech/python/srmech docs/srmech/python/tools docs/srmech/python/tests docs/srmech/notes; do
  a=$(git -C $G/repo rev-parse $CODE:$d); b=$(git -C $G/repo rev-parse $FINAL:$d)
  echo "$d  code ${a:0:12}  final ${b:0:12}  $([ "$a" = "$b" ] && echo identical || echo DIFFER)"
done
echo "files changed $CODE..$FINAL: $(git -C $G/repo diff --name-only $CODE $FINAL | tr '\n' ' ')"
FILES="tests/test_rc473_a6_phrase_gate_runs.py tests/test_pypi_readme_changelog.py tests/test_ref_notation_emitted_rc348.py tests/test_search_glyph_tokenizer_rc416.py"
for cell in native pure; do
  if [ $cell = pure ]; then P=$G/pure/docs/srmech/python; export SRMECH_EXPECT_PURE=1; else P=$G/repo/docs/srmech/python; unset SRMECH_EXPECT_PURE; fi
  cd $P
  TREE=$(dirname $(dirname $(dirname $P)))
  echo "=== $cell HEAD $(git -C $TREE rev-parse HEAD) tracked changes $(git -C $TREE status --porcelain --untracked-files=no | wc -l) libs $(find $TREE -name 'libsrmech*' | wc -l)"
  uv run --python 3.12 --no-project --offline python $H/auth.py $P | grep -E "_native.__file__|lib sha256|abi / c|AUTH|HAS_NATIVE"
  uv run --python 3.12 --no-project --offline --with pytest python -m pytest -q -p no:cacheprovider -rfEXs $FILES > $G/logs/final_changelog_$cell.log 2>&1
  echo "pytest exit $?: $(tail -1 $G/logs/final_changelog_$cell.log)"
  grep -E "^(FAILED|ERROR|XPASS|SKIPPED)" $G/logs/final_changelog_$cell.log | cut -c1-200 | head -10
done
date -u +%FT%TZ
