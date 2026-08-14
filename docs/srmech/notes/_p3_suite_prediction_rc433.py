"""`#T1131` P3-pre — the `-O` suite failure prediction, WRITTEN BEFORE THE RESULT.

The scope asks for the `-O` whole-suite failure count "whatever it is, including
zero". A count with no prior attached is not a test of anything, so the
prediction is committed here before the run reports, and scored against the log
afterwards by :func:`score`.

THE REASONING BEING TESTED
==========================
P7 measured that ``-O`` strips 100% of the suite's own 17,356 assertions. So a
test whose body is a chain of ``assert``\\ s cannot FAIL under ``-O`` — it passes
vacuously. The only tests that can go red are those expecting an exception that
no longer arrives, i.e. the ``pytest.raises(AssertionError)`` population, plus
whatever crashes on the resulting bad state.

If that reasoning is right, the failure set should be almost exactly the P1
population's test functions. If the measured failure set is MUCH LARGER, the
reasoning is incomplete and the extra failures are the interesting finding. If
it is much SMALLER, some of these sites are not reached at all.
"""

from __future__ import annotations

import json
import re
import sys

OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p3_suite_prediction_rc433.ndjson"
LOG = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p3_suite_dashO_rc433.log"

#: Predicted to FAIL under -O, with the reason. One row per test FUNCTION
#: (parametrized cases collapse to their function).
PREDICTED_FAIL = {
    "tests/test_bell_chsh.py::test_operator_norm_rejects_non_square":
        "-O raises ValueError from mat_hermitian_eigendecompose, not AssertionError",
    "tests/test_bell_chsh.py::test_operator_norm_rejects_non_2d":
        "-O raises TypeError from list(row), not AssertionError",
    "tests/test_byo_cascade_toml.py::test_register_dir_rejects_nonexistent_path":
        "-O does not raise at all — registration succeeds",
    "tests/test_loop_bind_hd.py::test_length_must_be_multiple_of_eight":
        "-O does not raise — silently truncates",
    "tests/test_loop_hd_division.py::test_hd_unary_requires_multiple_of_8":
        "-O does not raise — silently truncates (2 params)",
    "tests/test_loop_hd_division.py::test_loop_runbind_hd_requires_multiple_of_8_and_equal_length":
        "-O truncates on the first arm, IndexError on the second",
    "tests/test_loop_hd_native_parity.py::test_inv_hd_zero_block_raises_through_fallback":
        "-O raises ZeroDivisionError; the match='zero vector' also fails",
    "tests/test_mat_carrier_rc69.py::test_ragged_rows_rejected":
        "-O returns a mis-shaped Mat",
    "tests/test_mat_matmul_bridge_rc72.py::test_mat_matmul_rejects_non_mat":
        "-O raises AttributeError",
    "tests/test_vec_carrier_rc129.py::test_negative_index_and_out_of_range":
        "-O raises IndexError",
    "tests/test_genome_q8_coupling_rc311.py::test_p5_wrong_coupling_side_fails_loudly":
        "the test-LOCAL assert is stripped too",
    "tests/test_octonion_carrier_rc324.py::test_wrong_coupling_side_fails_loudly":
        "the test-LOCAL assert is stripped too",
    "tests/test_frame_scope_rc430.py::test_gate_fires_on_a_planted_defect":
        "assert_declaration_matches is test-local; its asserts are stripped (2 params)",
    "tests/test_owner_axis_rc410.py::test_a_failing_unregister_test_cleans_up_after_itself":
        "the driven test's 3 asserts are stripped, so it no longer fails",
}

#: Predicted to PASS VACUOUSLY — named because a green result here is the whole
#: argument against a whole-suite `-O` cell.
PREDICTED_VACUOUS = [
    "tests/test_input_contracts_rc431.py::test_the_dash_O_probe_can_actually_detect_a_stripped_assert",
    "tests/test_input_contracts_rc431.py::test_declared_exception_survives_python_dash_O",
]

_FAILLINE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)")


def score():
    try:
        with open(LOG, "r", encoding="utf-8", errors="replace") as fh:
            log = fh.read()
    except OSError:
        print("log not present yet")
        return None
    got = set()
    for ln in log.splitlines():
        m = _FAILLINE.match(ln.strip())
        if m:
            nodeid = m.group(1)
            got.add(nodeid.split("[")[0])
    pred = set(PREDICTED_FAIL)
    hit = sorted(pred & got)
    missed = sorted(pred - got)
    extra = sorted(got - pred)
    tail = log.strip().splitlines()[-6:]
    print("predicted-fail functions : %d" % len(pred))
    print("measured-fail functions  : %d" % len(got))
    print("  HIT     (predicted and failed) : %d" % len(hit))
    print("  MISSED  (predicted, did NOT fail): %d" % len(missed))
    for m_ in missed:
        print("      %s" % m_)
    print("  EXTRA   (failed, NOT predicted): %d" % len(extra))
    for e in extra:
        print("      %s" % e)
    print("\nlog tail:")
    for t in tail:
        print("   " + t)
    rec = {"record": "score", "n_predicted": len(pred), "n_measured": len(got),
           "hit": hit, "missed": missed, "extra": extra, "log_tail": tail}
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "prediction",
                             "predicted_fail": PREDICTED_FAIL,
                             "predicted_vacuous": PREDICTED_VACUOUS,
                             "python": sys.version.split()[0]},
                            sort_keys=True) + "\n")
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    print("\nwrote", OUT)
    return rec


if __name__ == "__main__":
    score()
