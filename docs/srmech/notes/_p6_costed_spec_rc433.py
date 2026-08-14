"""`#T1131` P6 — the COSTED SPEC, emitted as NDJSON so every number is on disk.

This file is the join of P1 (population), P2/P2b (executed ``-O`` behaviour),
P4 (static-gate classification) and P5/P5b (`#T1130` overlap). It carries no new
measurement — it carries the RULING per site plus the edit cost, each traceable
to the artifact that produced it.

RULINGS (the brief's three-way vocabulary)
  (a) PROMOTE    — the assert is the only guard, a public caller reaches it, and
                   ``-O`` yields a silent-wrong or a crash-later.
  (b) REDUNDANT  — a real ``raise`` already covers the input class. The assert is
      /MISORDERED  dead weight, or fires FIRST and changes the type in DEFAULT mode.
  (c) NOT-A-DEFECT — a meta-gate, or an assert no public caller can reach.

EXCEPTION-TYPE PRECEDENT (grepped from the shipped package, not invented)
  ValueError        srmech/math/modular_linalg.py:98  "all rows must have equal length"
                    srmech/math/vec.py:203            "Vec elementwise length mismatch"
                    srmech/signal_processing/form_function_rotation.py:141
                                                      "D must be a multiple of 8; got {D}"
                    srmech/cascade/matrix_cascades.py:646  "a must be square 2-D"
  IndexError        srmech/math/qmat.py:260           "QMat row index out of range"
                                                      (the exact structural twin of
                                                       Vec.__getitem__: same i += n
                                                       normalisation, real raise)
                    srmech/cascade/one.py:1196        "index {i} out of range 0..{n}"
  TypeError         283 shipped sites, house shape "X must be a Y; got {z!r}"
  FileNotFoundError srmech/dsl/_catalog.py:146        "registered cascade-catalog
                                                       directory not found: {base}"
                                                      — the SAME condition, already
                                                       declared in load_catalog's
                                                       Raises block
  ZeroDivisionError user ruling for a zero denominator; tree precedent
                    rational_div((1,2),(0,1)) -> ZeroDivisionError
"""

from __future__ import annotations

import json

OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p6_costed_spec_rc433.ndjson"

#: One row per `#T1131` test site. ``guard`` is the PACKAGE line to edit.
SITES = [
    dict(
        site="tests/test_mat_carrier_rc69.py:72",
        op="srmech.math.mat.Mat.from_rows",
        guard="srmech/math/mat.py:92",
        input_class="ragged list-of-rows",
        dash_o="SILENT_WRONG. long-row-first -> Mat(shape=(2,2), buflen=3), tolist() "
               "IndexError. short-row-first -> Mat(shape=(2,1), buflen=3), tolist() "
               "returns [[1.0],[2.0]] with NO error and the value 3.0 SILENTLY DROPPED.",
        ruling="a",
        exc="ValueError",
        precedent="srmech/math/modular_linalg.py:98 'all rows must have equal length'",
        in_registry=False,
        cost_pkg_lines=4, cost_test_lines=2, cost_doc_lines=5,
        note="TOP SEVERITY. Asymmetric exactly like the rc431 vec_add defect: the "
             "shipped test drives only the NOISY orientation. Fixing on the tested "
             "orientation alone would leave the corrupting one intact.",
    ),
    dict(
        site="tests/test_vec_carrier_rc129.py:90",
        op="srmech.math.vec.Vec.__getitem__",
        guard="srmech/math/vec.py:122",
        input_class="index outside [-n, n)",
        dash_o="SPLIT. i >= n -> IndexError (array bounds). i < -n -> SILENT_WRONG: "
               "v[-5] on n=3 returns v[1] (20.0 real; (2+2j) complex). The shipped "
               "test drives ONLY the positive half.",
        ruling="a",
        exc="IndexError",
        precedent="srmech/math/qmat.py:260 — the exact structural twin (same i += n "
                  "then range check) already uses a real raise IndexError",
        in_registry=False,
        cost_pkg_lines=3, cost_test_lines=2, cost_doc_lines=4,
        note="IndexError, not ValueError: the sibling carrier already does this, and "
             "the sequence protocol is defined in terms of IndexError. This FOLLOWS "
             "the user's ruling ('follow existing tree precedent where one exists') "
             "rather than departing from it.",
    ),
    dict(
        site="tests/test_loop_bind_hd.py:115",
        op="srmech.math.hdc.loop_bind_hd",
        guard="srmech/math/hdc.py:3164 (_as_hd)",
        input_class="length not a positive multiple of 8",
        dash_o="SILENT_WRONG. len 25 -> returns a length-24 result: one element "
               "silently TRUNCATED. len 0 -> returns [].",
        ruling="a",
        exc="ValueError",
        precedent="srmech/signal_processing/form_function_rotation.py:141 "
                  "'D must be a multiple of 8; got {D}' (exact input class, twice in tree)",
        in_registry=True,
        cost_pkg_lines=4, cost_test_lines=1, cost_doc_lines=0,
        note="ONE edit in _as_hd fixes FIVE ops (loop_bind_hd / loop_unbind_hd / "
             "loop_conj_hd / loop_inv_hd / loop_runbind_hd) and FOUR test sites.",
    ),
    dict(
        site="tests/test_loop_bind_hd.py:117",
        op="srmech.math.hdc.loop_unbind_hd",
        guard="srmech/math/hdc.py:3164 (_as_hd) — SHARED",
        input_class="length not a positive multiple of 8",
        dash_o="SILENT_WRONG (silent truncation, as above).",
        ruling="a", exc="ValueError",
        precedent="shared with _as_hd", in_registry=True,
        cost_pkg_lines=0, cost_test_lines=1, cost_doc_lines=0,
        note="Covered by the single _as_hd edit; test-side only.",
    ),
    dict(
        site="tests/test_loop_hd_division.py:186",
        op="srmech.math.hdc.loop_conj_hd / loop_inv_hd (parametrized)",
        guard="srmech/math/hdc.py:3164 (_as_hd) — SHARED",
        input_class="length not a positive multiple of 8",
        dash_o="SILENT_WRONG (silent truncation).",
        ruling="a", exc="ValueError",
        precedent="shared with _as_hd", in_registry=True,
        cost_pkg_lines=0, cost_test_lines=1, cost_doc_lines=0,
        note="The `match=` string must move from 'positive multiple' to whatever the "
             "new ValueError says; keep the phrase so the edit is one token.",
    ),
    dict(
        site="tests/test_loop_hd_division.py:192",
        op="srmech.math.hdc.loop_runbind_hd",
        guard="srmech/math/hdc.py:3164 (_as_hd) — SHARED",
        input_class="length not a positive multiple of 8",
        dash_o="SILENT_WRONG (silent truncation).",
        ruling="a", exc="ValueError",
        precedent="shared with _as_hd", in_registry=True,
        cost_pkg_lines=0, cost_test_lines=1, cost_doc_lines=0,
        note="Covered by the single _as_hd edit.",
    ),
    dict(
        site="tests/test_loop_hd_division.py:195",
        op="srmech.math.hdc.loop_runbind_hd",
        guard="srmech/math/hdc.py:3286 (+ :3197 loop_bind_hd, :3216 loop_unbind_hd)",
        input_class="both operands multiples of 8 but UNEQUAL length",
        dash_o="CRASH_LATER. 56 vs 48 -> IndexError('list index out of range') from "
               "bb[6]. Same for loop_bind_hd / loop_unbind_hd (measured).",
        ruling="a",
        exc="ValueError",
        precedent="srmech/math/vec.py:203 'Vec elementwise length mismatch {n} vs {m}'",
        in_registry=True,
        cost_pkg_lines=9, cost_test_lines=1, cost_doc_lines=0,
        note="THREE sibling asserts share this shape (loop_bind_hd :3197, "
             "loop_unbind_hd :3216, loop_runbind_hd :3286); promote all three in one "
             "pass or the two untested ones stay broken.",
        retracted_claim="A first draft of this spec flagged a NATIVE HAZARD here — "
                        "'the assert sits above _try_native_*, so under -O with "
                        "libsrmech present a mismatched pair reaches the C kernel'. "
                        "REFUTED by reading all five wrappers: _try_native_loop_bind_hd "
                        ":2822, _loop_unbind_hd :2881, _loop_conj_hd :2844, _loop_inv_hd "
                        ":2863 and _loop_runbind_hd :2901 EACH re-check `n % LOOP_DIM` "
                        "and (where binary) `len(b_) != n`, returning None so the pure "
                        "path runs. No C kernel is reached with bad input in either "
                        "interpreter mode. Recorded because the claim was written before "
                        "it was checked.",
    ),
    dict(
        site="tests/test_loop_hd_native_parity.py:178",
        op="srmech.math.hdc.loop_inv_hd",
        guard="srmech/math/hdc.py:3265 (+ :3058 loop_inv)",
        input_class="an all-zero 8-block (no Moufang inverse)",
        dash_o="CORRECT_REJECT. -O raises ZeroDivisionError('float division by zero') "
               "from 1.0/nsq — which is the type the USER RULED for a zero denominator.",
        ruling="b",
        exc="ZeroDivisionError",
        precedent="user ruling + rational_div((1,2),(0,1)) -> ZeroDivisionError",
        in_registry=True,
        cost_pkg_lines=4, cost_test_lines=1, cost_doc_lines=4,
        note="REDUNDANT/MISORDERED: the assert fires FIRST in default mode and MASKS "
             "the ruled-correct ZeroDivisionError. Promote to an explicit "
             "ZeroDivisionError so both modes agree and the message names WHICH block. "
             "Same for the single-element loop_inv at :3058 (measured identically).",
    ),
    dict(
        site="tests/test_bell_chsh.py:334",
        op="srmech.physics.qm.bell.operator_norm",
        guard="srmech/physics/qm/bell.py:281",
        input_class="non-square Mat",
        dash_o="CORRECT_REJECT. -O raises ValueError('mat_hermitian_eigendecompose: H "
               "must be square; got (3, 4)') — a real raise sits BELOW the assert. "
               "Confirmed on both a zero and a nonzero non-square.",
        ruling="b",
        exc="ValueError",
        precedent="mat_hermitian_eigendecompose already raises exactly this",
        in_registry=True,
        cost_pkg_lines=-1, cost_test_lines=1, cost_doc_lines=0,
        note="THE THIRD INSTANCE of the rc431 inversion. The assert BREAKS the contract "
             "in DEFAULT mode (the worse half — almost nobody runs -O). Cheapest correct "
             "fix: DELETE the assert, let the downstream ValueError through, and pin -O "
             "INVARIANCE rather than -O rejection.",
    ),
    dict(
        site="tests/test_bell_chsh.py:344",
        op="srmech.physics.qm.bell.operator_norm",
        guard="srmech/physics/qm/bell.py:279",
        input_class="an object carrying ndim == 1",
        dash_o="MOSTLY CORRECT_REJECT. A genuine 1-D iterable -> TypeError('float object "
               "is not iterable'). But an object that LIES about ndim while yielding 2-D "
               "rows -> -O RETURNS 1.0 (SILENT_WRONG).",
        ruling="b",
        exc="TypeError",
        precedent="283 shipped 'X must be a Y; got {z!r}' TypeError sites",
        in_registry=True,
        cost_pkg_lines=3, cost_test_lines=1, cost_doc_lines=0,
        note="Mostly redundant; the residual (lying ndim) is a contrived input class. "
             "Promote to TypeError for -O invariance rather than delete, because the "
             "downstream type is an accident of list() rather than a stated contract.",
    ),
    dict(
        site="tests/test_mat_matmul_bridge_rc72.py:131",
        op="srmech.math.laplacian.mat_matmul",
        guard="srmech/math/laplacian.py:1768",
        input_class="a non-Mat operand",
        dash_o="CRASH_LATER. -O raises AttributeError(\"'list' object has no attribute "
               "'n_rows'\") — leaks an implementation detail. Same for the mixed "
               "(one Mat, one list) orientation.",
        ruling="a",
        exc="TypeError",
        precedent="283 shipped TypeError sites, house shape 'must be a ...; got ...'",
        in_registry=True,
        cost_pkg_lines=4, cost_test_lines=1, cost_doc_lines=4,
        note="AttributeError is not a contract; it names the callee's private attribute. "
             "The op already raises ValueError for an incompatible SHAPE two lines "
             "below, so the file's own convention is a real raise.",
    ),
    dict(
        site="tests/test_byo_cascade_toml.py:156",
        op="srmech.dsl.register_catalog_dir",
        guard="srmech/dsl/_catalog.py:104",
        input_class="a path that is missing, or exists but is a FILE",
        dash_o="DEFERRED. -O returns CLEANLY and APPENDS the bad path to the "
               "module-global _USER_CATALOG_DIRS. FileNotFoundError surfaces only at the "
               "next load_catalog() — after the global mutation, and then on EVERY "
               "subsequent catalog load for the life of the process.",
        ruling="a",
        exc="FileNotFoundError",
        precedent="srmech/dsl/_catalog.py:146 raises exactly this for the same "
                  "condition, and load_catalog's Raises block already DECLARES it",
        in_registry=False,
        cost_pkg_lines=5, cost_test_lines=1, cost_doc_lines=5,
        note="JUDGMENT CALL, stated openly: a real raise DOES cover the input class, so "
             "this is arguably (b). Ruled (a) because the deferred raise does not cover "
             "the REGISTRATION contract — it converts a caller error into persistent "
             "global-state poisoning. The promotion is about WHEN, not WHETHER.",
    ),
    # ---- class (c) ----
    dict(
        site="tests/test_frame_scope_rc430.py:587",
        op="tests.test_frame_scope_rc430.assert_declaration_matches (TEST-LOCAL)",
        guard="n/a",
        input_class="a deliberately mis-declared ToolEntry copy",
        dash_o="n/a — the subject is a test-local gate function, not package code.",
        ruling="c", exc="n/a", precedent="n/a", in_registry=False,
        cost_pkg_lines=0, cost_test_lines=0, cost_doc_lines=0,
        note="Meta-gate. Its own docstring records that rc430 REPAIRED it from exactly "
             "the vacuous shape this scope hunts. Leave alone.",
    ),
    dict(
        site="tests/test_owner_axis_rc410.py:659",
        op="tests.test_tool_schema.test_unregister_profile_tools_removes_all (A TEST)",
        guard="n/a",
        input_class="another TEST driven through its own failure path",
        dash_o="n/a. MEASURED: the target test compiles 3 LOAD_ASSERTION_ERROR ops in "
               "default mode and 0 under -O, so under -O the meta-gate and the test it "
               "drives vanish together.",
        ruling="c", exc="n/a", precedent="n/a", in_registry=False,
        cost_pkg_lines=0, cost_test_lines=0, cost_doc_lines=0,
        note="Meta-gate over test code. Leave alone.",
    ),
    dict(
        site="tests/test_genome_q8_coupling_rc311.py:233",
        op="srmech.biology.genome._q8_couple (the SHIPPED peer)",
        guard="srmech/biology/genome.py:2629",
        input_class="UNREACHABLE — a wrong-side couple",
        dash_o="n/a. MEASURED unreachability: 240 in-range trials across dim 1/2/8/64, "
               "assert fired 0 times; out-of-range Q8 bytes raise ValueError from "
               "q8_bind BEFORE the assert is reached.",
        ruling="c", exc="n/a",
        precedent="q8_bind already raises ValueError for out-of-range elements",
        in_registry=False,
        cost_pkg_lines=0, cost_test_lines=0, cost_doc_lines=0,
        note="The shipped assert is a SELF-CHECK on the algebra (the code always "
             "right-couples), not an input contract. The test knows this — it "
             "re-implements a LEFT-couple locally precisely because the shipped guard "
             "cannot be reached by input. Unreachability SHOWN by execution, not asserted.",
    ),
    dict(
        site="tests/test_octonion_carrier_rc324.py:355",
        op="srmech.biology.genome._oct_couple (the SHIPPED peer)",
        guard="srmech/biology/genome.py:2672",
        input_class="UNREACHABLE — a wrong-side couple",
        dash_o="n/a. MEASURED: 240 in-range trials, 0 fires; out-of-range octonion bytes "
               "raise ValueError from oct_bind before the assert.",
        ruling="c", exc="n/a",
        precedent="oct_bind already raises ValueError", in_registry=False,
        cost_pkg_lines=0, cost_test_lines=0, cost_doc_lines=0,
        note="Same shape as the Q8 peer.",
    ),
]

#: The systemic half.
SYSTEMIC = [
    dict(
        item="static gate",
        proposal="tests/test_assert_contract_gate_rc433.py — AST scan of tests/ for "
                 "`with pytest.raises(AssertionError)` whose BODY SUBJECT resolves to "
                 "srmech package code.",
        discrimination="subject resolution: PACKAGE (imported from srmech / an attribute "
                       "on a srmech-bound name / a name assigned from a PACKAGE value) vs "
                       "TEST_LOCAL (def-ed in this file, or imported from tests.*). An "
                       "UNRESOLVABLE subject counts as PACKAGE so a new spelling turns "
                       "the gate RED rather than silently exempting.",
        threshold="STRICT ZERO on CANDIDATE_DEFECT, with an EMPTY exemption table at ship.",
        why_strict_zero="The (a)/(c) split is STRUCTURAL, not enumerated — the gate "
                        "derives it, so no residual has to be carried. All 12 candidate "
                        "sites are fixed by this same rc, so zero is reachable in one "
                        "step and a CEIL would only invite drift.",
        exemption="a `# t1131-exempt: <reason>` pragma on the `with` line. VERIFIED: it "
                  "downgrades a PACKAGE-subject site (NC-5) and a REASONLESS pragma does "
                  "NOT (NC-6).",
        controls="NC-1 16/16 agree with the hand-adjudicated ruling; NC-2 synthetic defect "
                 "CAUGHT; NC-3 synthetic meta-gate NOT caught (proves the gate is not "
                 "'flag everything'); NC-4 module-attribute spelling CAUGHT; NC-5/NC-6 "
                 "exemption pragma behaves.",
        naming="srmech-local invariant. NOT 'Rule 11' — Holzmann's Power of Ten has "
               "exactly ten rules and tests/test_jpl_audit.py iterates range(1, 11).",
        cost_lines=260,
    ),
    dict(
        item="-O contract roster (the cheap systemic win)",
        proposal="EXTEND the SHIPPED _O_INVARIANT_CASES roster in "
                 "tests/test_input_contracts_rc431.py with one row per rc433 promotion.",
        discrimination="n/a — the instrument already exists and already carries a working "
                       "negative control.",
        threshold="n/a",
        why_strict_zero="n/a",
        exemption="n/a",
        controls="FIXTURE AUDIT PASSED: mutating the control's -O arm to optimized=False "
                 "turns it RED with exactly its promised diagnostic. The fixture COULD "
                 "have failed.",
        naming="n/a",
        cost_lines=25,
    ),
]


def main():
    n_a = sum(1 for s in SITES if s["ruling"] == "a")
    n_b = sum(1 for s in SITES if s["ruling"] == "b")
    n_c = sum(1 for s in SITES if s["ruling"] == "c")
    pkg = sum(max(0, s["cost_pkg_lines"]) for s in SITES)
    tst = sum(s["cost_test_lines"] for s in SITES)
    doc = sum(s["cost_doc_lines"] for s in SITES)
    sysl = sum(x["cost_lines"] for x in SYSTEMIC)

    print("rulings: (a)=%d  (b)=%d  (c)=%d  of %d sites" % (n_a, n_b, n_c, len(SITES)))
    print("distinct PACKAGE guard locations to edit: %d" % len(
        {s["guard"] for s in SITES if s["ruling"] in ("a", "b") and s["guard"] != "n/a"}))
    print("cost: package ~%d lines, tests ~%d lines, docstrings ~%d lines, "
          "systemic ~%d lines" % (pkg, tst, doc, sysl))
    print("registry delta: 0 (no new public callable)")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({
            "record": "spec_meta", "task": "#T1131", "target_rc": "0.9.0rc433",
            "baseline_version": "0.9.0rc432", "baseline_registry": 655,
            "baseline_abi": 14,
            "n_sites": len(SITES), "n_promote_a": n_a, "n_redundant_b": n_b,
            "n_not_a_defect_c": n_c,
            "registry_delta": 0,
            "cost_pkg_lines": pkg, "cost_test_lines": tst,
            "cost_doc_lines": doc, "cost_systemic_lines": sysl,
        }, sort_keys=True) + "\n")
        for s in SITES:
            fh.write(json.dumps(dict(s, record="site"), sort_keys=True) + "\n")
        for x in SYSTEMIC:
            fh.write(json.dumps(dict(x, record="systemic"), sort_keys=True) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
