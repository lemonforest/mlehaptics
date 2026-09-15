#!/bin/bash
# rc473 final round: the truth round's 29 named gate files in three groups, plus
# group 4 = every gate this round adds or edits, one foreground pytest per group
# and cell, in the WSL clones (no .claude / worktrees path component, no GIT_DIR
# exported). Usage: w_gates.sh <1|2|3|4> <native|pure>
export PATH="$HOME/.local/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
unset SRMECH_ALLOW_STALE_NATIVE
set -u
GROUP=$1; CELL=$2
G=~/rc473c
H=/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h
G1="test_value_status_c_boundary_rc473 test_kepler_non_finite_slots_rc473 test_winding_fold_rc215 test_kepler_parity test_eph_propagate_wound_rc207 test_jpl_audit test_rc473_a6_phrase_gate_runs test_adr_citation_integrity_rc415 test_adr_clause_instrument_rc417"
G2="test_search_glyph_tokenizer_rc416 test_introspect_search_rc411 test_worked_examples_execute_rc354 test_worked_examples_strict_zero_rc353 test_synth_args_provenance_rc430 test_ledger_freshness_hook_rc468 test_abi_pin_sites_agree_rc464 test_abi_prose_currency_rc449 test_ref_notation_emitted_rc348"
G3="test_eoc_q61_parity_rc472 test_c_cascade_value_parity_rc450 test_t1146_rejection_parity_rc447 test_t1158_refusal_set_equality_rc449 test_c_fold_step_form_rc446 test_c_cascade_coherence test_status_conflation_ratchet_rc404 test_regen_all_rc346 test_tool_registry_c_rc184 test_r3_reader_rc470 test_ripple_manifest_covers_known_gates"
G4="test_git_env_cannot_reach_a_repository_rc473 test_kepler_identity_phrases_absent_rc473 test_curated_line_citations_resolve_rc473 test_hook_fixture_env_isolation_rc471 test_ledger_write_refusals_rc469 test_shell_line_loop_rc468 test_figure_run_rc471 test_registry_completeness_rc416 test_assert_contract_gate_rc433 test_pypi_readme_changelog"
case $GROUP in 1) NAMES=$G1;; 2) NAMES=$G2;; 3) NAMES=$G3;; 4) NAMES=$G4;; esac
if [ "$CELL" = pure ]; then P=$G/pure/docs/srmech/python; export SRMECH_EXPECT_PURE=1; else P=$G/repo/docs/srmech/python; unset SRMECH_EXPECT_PURE; fi
cd $P
FILES=""; NF=0
for n in $NAMES; do if [ -f tests/$n.py ]; then FILES="$FILES tests/$n.py"; NF=$((NF+1)); else echo "MISSING tests/$n.py"; fi; done
TREE=$(dirname $(dirname $(dirname $P)))
echo "group $GROUP cell $CELL files $NF HEAD $(git -C $TREE rev-parse HEAD) tracked changes $(git -C $TREE status --porcelain --untracked-files=no | wc -l) EXPECT_PURE=${SRMECH_EXPECT_PURE:-unset} ALLOW_STALE=${SRMECH_ALLOW_STALE_NATIVE:-unset} exported GIT vars [$(env | grep -c '^GIT_DIR=\|^GIT_WORK_TREE=')] libs=$(find $TREE -name 'libsrmech*' | wc -l) $(date -u +%FT%TZ)"
echo "files:$FILES"
uv run --python 3.12 --no-project --offline python $H/auth.py $P | grep -E "python|_native.__file__|lib sha256|abi / c|AUTH|HAS_NATIVE|numpy"
timeout 590 uv run --python 3.12 --no-project --offline --with pytest python -m pytest -q -p no:cacheprovider -rfEX $FILES > $G/logs/final_g${GROUP}_$CELL.log 2>&1
echo "pytest exit $?: $(tail -1 $G/logs/final_g${GROUP}_$CELL.log)"
grep -E "^(FAILED|ERROR|XPASS)" $G/logs/final_g${GROUP}_$CELL.log | cut -c1-260 | head -20
echo "tracked changes after $(git -C $TREE status --porcelain --untracked-files=no | wc -l)  done $(date -u +%FT%TZ)"
