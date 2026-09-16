#!/bin/bash
# rc473 final round: the two derived ledgers, re-harvested LAST, each on the
# interpreter and cell its meta declares, in the clean WSL clone at its HEAD (a real
# git checkout, so head_blob_map answers without any export). Saves the committed
# copy first, diffs rows after, copies the result out.
# Usage: w_harvest.sh we   (worked examples: CPython 3.10, NATIVE)
#        w_harvest.sh ea   (example args:    CPython 3.10, PURE — library moved aside)
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
WHICH=$1
G=~/rc473c
S=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
O=/mnt/c/Users/sckir/rc473c_win/final/ledgers_out
mkdir -p $O $G/out $G/libstash
cd $G/repo/docs/srmech/python
echo "HEAD $(git -C $G/repo rev-parse HEAD) tracked changes $(git -C $G/repo status --porcelain --untracked-files=no | wc -l) exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] $(date -u +%FT%TZ)"
case $WHICH in
  we)
    cp tests/worked_examples_result.ndjson $G/out/final_we_committed.ndjson
    echo "=== auth (3.10, native)"
    uv run --python 3.10 --no-project --offline python $S/auth.py $PWD | grep -E "python|_native.__file__|lib sha256|AUTHENTIC|numpy"
    echo "=== worked examples, full, 3.10, native $(date -u +%FT%TZ)"
    timeout 590 uv run --python 3.10 --no-project --offline python tools/run_worked_examples.py > $G/out/final_we_run.log 2>&1; echo "exit $?"
    tail -3 $G/out/final_we_run.log | cut -c1-300
    head -1 tests/worked_examples_result.ndjson | cut -c1-300
    echo "=== row diff"
    uv run --python 3.12 --no-project --offline python $S/m_ledger_diff.py $G/out/final_we_committed.ndjson tests/worked_examples_result.ndjson name
    cp tests/worked_examples_result.ndjson $O/
    echo "CR bytes: $(tr -cd '\r' < tests/worked_examples_result.ndjson | wc -c)" ;;
  ea)
    cp tests/example_args_ledger.ndjson $G/out/final_ea_committed.ndjson
    mv srmech/_native/libsrmech.so $G/libstash/
    echo "library files under python/: $(find . -name 'libsrmech*' | wc -l)"
    echo "=== example args, full, 3.10, PURE $(date -u +%FT%TZ)"
    SRMECH_EXPECT_PURE=1 timeout 1500 uv run --python 3.10 --no-project --offline python tools/run_example_args.py > $G/out/final_ea_run.log 2>&1; echo "exit $?"
    mv $G/libstash/libsrmech.so srmech/_native/
    echo "library restored: $(find . -name 'libsrmech*' | wc -l)"
    tail -3 $G/out/final_ea_run.log | cut -c1-300
    head -1 tests/example_args_ledger.ndjson | cut -c1-300
    echo "=== row diff"
    uv run --python 3.12 --no-project --offline python $S/m_ledger_diff.py $G/out/final_ea_committed.ndjson tests/example_args_ledger.ndjson op
    cp tests/example_args_ledger.ndjson $O/
    echo "CR bytes: $(tr -cd '\r' < tests/example_args_ledger.ndjson | wc -c)" ;;
esac
git -C $G/repo status --porcelain --untracked-files=no
date -u +%FT%TZ
