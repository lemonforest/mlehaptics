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
#: The POPULATION-file arms are the scoreable pair — both modes measured, so a
#: failure present in BOTH is environmental (this box has no libsrmech.so) and
#: only the DELTA is attributable to ``-O``. The whole-suite ``-O`` log is kept
#: as a raw upper bound; its default-mode twin was killed at the summary line
#: after ~65 min, so the suite-wide baseline is NOT known and the suite-wide
#: figure must not be quoted as an ``-O`` count.
LOG = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p3_suite_population_dashO_rc433.log"
LOG_DEFAULT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p3_suite_population_default_rc433.log"

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


def _failed_set(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            log = fh.read()
    except OSError:
        return None, ""
    got = set()
    for ln in log.splitlines():
        m = _FAILLINE.match(ln.strip())
        if m:
            got.add(m.group(1).split("[")[0])
    return got, log


def score():
    got_o, log = _failed_set(LOG)
    got_d, _ = _failed_set(LOG_DEFAULT)
    if got_o is None or got_d is None:
        print("logs not present yet")
        return None
    env = sorted(got_o & got_d)
    print("failures in BOTH modes (environmental, native-absent): %d" % len(env))
    for e in env:
        print("      %s" % e)
    got = got_o - got_d
    print("\n-O-ATTRIBUTABLE failures (the delta): %d" % len(got))
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
           "hit": hit, "missed": missed, "extra": extra, "log_tail": tail,
           "environmental_both_modes": env,
           "why_the_misses": (
               "All four MISSES are the class-(c) meta-gates, and they were "
               "mispredicted for one reason, measured in P9: pytest's assertion "
               "REWRITER replaces every `assert` in a collected TEST module with "
               "explicit raising bytecode, so `-O` has nothing to strip there. "
               "Test-module asserts SURVIVE `-O`; package asserts do not. The "
               "prediction assumed the P7 `compile()` result described pytest, and "
               "it does not. The consequence is favourable for the gate: the `-O` "
               "boundary falls EXACTLY on the PACKAGE / TEST_LOCAL line P4 already "
               "uses, so the gate's rule tracks the mechanism rather than "
               "approximating it."),
           }
    # The whole-suite `-O` arm: the run reached the end of execution but was
    # killed before the summary line flushed, so the tally is recovered from the
    # progress GLYPH stream (one glyph per test). The `.log` files are gitignored,
    # so the tally is written HERE and nothing dangles.
    whole = _glyph_tally(
        "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p3_suite_dashO_rc433.log")
    if whole:
        print("\nWHOLE-SUITE -O tally (from the progress glyph stream): %s" % whole)
        print("  ^ UPPER BOUND on `-O`-attributable failures, NOT the count: the "
              "whole-suite DEFAULT arm was killed before reporting, so the "
              "native-absent baseline is unknown. In the population files that "
              "baseline was 4 of 15.")
        rec["whole_suite_dash_O_glyph_tally"] = whole
        rec["whole_suite_caveat"] = (
            "Execution completed; the summary line did not flush before the job "
            "was killed. Tally recovered from progress glyphs. The default-mode "
            "whole-suite twin was never obtained, so this is an UPPER BOUND on "
            "`-O`-attributable failures, not a count — this environment has no "
            "libsrmech.so and native-absent tests fail identically in BOTH modes.")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "prediction",
                             "predicted_fail": PREDICTED_FAIL,
                             "predicted_vacuous": PREDICTED_VACUOUS,
                             "python": sys.version.split()[0]},
                            sort_keys=True) + "\n")
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    print("\nwrote", OUT)
    return rec


def _glyph_tally(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            s = fh.read()
    except OSError:
        return None
    s = re.sub(r"\[\s*\d+%\]", "", s)
    glyphs = [ch for ch in s if ch in ".sFEx"]
    out = {}
    for ch in glyphs:
        out[ch] = out.get(ch, 0) + 1
    return {"passed": out.get(".", 0), "skipped": out.get("s", 0),
            "failed": out.get("F", 0), "errored": out.get("E", 0),
            "total_glyphs": len(glyphs)}


if __name__ == "__main__":
    score()
