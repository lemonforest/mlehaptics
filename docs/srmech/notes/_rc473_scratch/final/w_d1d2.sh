#!/bin/bash
# rc473 final round: D1 + D2 on the WSL clones with the SHIPPED probes (notes/), the
# kepler symbol fuzz against kepler._kepler_q61 and the served-value witnesses.
# Same instruments as truth repair 1's rr1_d1d2.sh; outputs under out/final_d1d2.
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
G=~/rc473c
H=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
NP=$G/repo/docs/srmech/python
PP=$G/pure/docs/srmech/python
N=$G/repo/docs/srmech/notes
O=$G/out/final_d1d2
rm -rf $O && mkdir -p $O
PY="uv run --python 3.12 --no-project --offline python"
echo "start $(date -u +%FT%TZ) repo HEAD $(git -C $G/repo rev-parse HEAD) pure HEAD $(git -C $G/pure rev-parse HEAD) pure libs=$(find $G/pure -name 'libsrmech*' | wc -l) exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')]"
$PY $H/auth.py $NP | grep -E "python|_native.__file__|lib sha256|abi / c|AUTH|numpy"
echo "=== D2 slot sweep"
$PY $N/_rc473_twin_d2_slot_sweep.py $NP $O/slots_native.json > $O/slots_native.txt 2>&1; echo "native exit $?"
SRMECH_EXPECT_PURE=1 $PY $N/_rc473_twin_d2_slot_sweep.py $PP $O/slots_pure.json > $O/slots_pure.txt 2>&1; echo "pure exit $?"
$PY $N/_rc473_twin_d2_diff.py $O/slots_native.json $O/slots_pure.json | tail -3
echo "=== D2 tolerance frontier"
$PY $N/_rc473_twin_d2_tol_frontier.py $NP $O/front_native.json > $O/front_native.txt 2>&1; echo "native exit $?"
SRMECH_EXPECT_PURE=1 $PY $N/_rc473_twin_d2_tol_frontier.py $PP $O/front_pure.json > $O/front_pure.txt 2>&1; echo "pure exit $?"
$PY $N/_rc473_twin_d2_diff.py $O/front_native.json $O/front_pure.json | tail -3
echo "=== D1: 24 filed + 21 further named + 40000 fuzzed, at the symbol and through the wrapper"
$PY $N/_rc473_twin_d1_dump.py $NP $O/d1.json 40000 | tail -5
SRMECH_EXPECT_PURE=1 $PY $N/_rc473_twin_d1_analyze.py $PP after $O/d1.json | tail -8
echo "=== kepler symbol fuzz vs _kepler_q61, 200000 rows, seed 9131"
$PY $H/r1/fuzz_kepler.py $NP 200000 9131 | tail -2
echo "=== served-value witnesses, native vs pure"
cp $G/out/final/witness.py $O/witness.py
echo "witness script sha256 $(sha256sum $O/witness.py | cut -c1-16)"
$PY $O/witness.py $NP > $O/witness_native.txt 2>&1; echo "native exit $?"
SRMECH_EXPECT_PURE=1 $PY $O/witness.py $PP > $O/witness_pure.txt 2>&1; echo "pure exit $?"
tail -1 $O/witness_native.txt | cut -c1-160; tail -1 $O/witness_pure.txt | cut -c1-160
echo "witness V lines: native $(grep -c '^V' $O/witness_native.txt) pure $(grep -c '^V' $O/witness_pure.txt); differing: $(diff <(grep '^V' $O/witness_native.txt) <(grep '^V' $O/witness_pure.txt) | grep -c '^[<>]')"
echo "tracked changes: repo $(git -C $G/repo status --porcelain --untracked-files=no | wc -l) pure $(git -C $G/pure status --porcelain --untracked-files=no | wc -l)"
echo "end $(date -u +%FT%TZ)"
