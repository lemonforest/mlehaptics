"""rc431 `#T1129` -- K3 FIXTURE AUDIT: can each new assertion actually go red?

WHY THIS EXISTS
---------------
rc431 added two gate files and four op repairs. A gate that cannot fail is not a
gate, and this rc already produced two instruments that returned false results
before anyone noticed (a harness ``TypeError`` recorded as an op refusing input;
an ``is`` check between two module objects of the same file, which could never
succeed and reported SKIPPED = 0 on every run). Both were caught by execution,
neither by reading. So the fixtures get the same treatment as the ops.

PRE-REGISTERED FALSIFIER (fixed before any mutation ran)
--------------------------------------------------------
For every assertion added or changed by rc431, apply the MINIMAL mutation that
assertion claims to catch, and require the assertion to FAIL.

    verdict DISCRIMINATES -- green unmutated, red under its own mutation
    verdict DEAD          -- green under its own mutation; must be made to
                             discriminate or deleted, never left passing
    verdict SLACK         -- a ratchet that holds but is not tight; the number
                             is reported rather than asserted away
    verdict UNMUTATED     -- no in-process mutation exists; stated, not hidden

A fixture is judged by whether the SUBJECT can be broken under it, never by
whether the fixture reads convincingly.

NULL CLASSIFICATION
-------------------
If zero DEAD fixtures are found, the null is **BOUNDED, not EMPTY**: this audit
mutates the subject of each assertion in-process, so it covers exactly the
assertions for which such a mutation exists. Rows carrying UNMUTATED are outside
the bound and are named individually.

CONTROL (mandatory)
-------------------
This auditor must itself be able to report DEAD. A planted dead fixture -- an
assertion that is true regardless of the subject -- is run through the same
harness and must come back DEAD. Without it a run of all-DISCRIMINATES means
nothing.

Run:
    PYTHONPATH=docs/srmech/python:docs/srmech/python/tests \\
    SRMECH_EXPECT_PURE=1 python3 docs/srmech/notes/_k3_fixture_audit_rc431.py
"""

from __future__ import annotations

import json
import pathlib
import sys

OUT = pathlib.Path(__file__).with_suffix(".ndjson")
ROWS = []


def emit(**kw):
    ROWS.append(kw)
    print(json.dumps(kw, ensure_ascii=False))


def probe(fn):
    """Run an assertion body; True == it held, False == it went red."""
    try:
        fn()
        return True
    except AssertionError:
        return False
    except Exception as exc:                                  # noqa: BLE001
        return ("ERROR", f"{type(exc).__name__}: {exc}")


def audit(fixture, subject, assertion, mutate, unmutate, note=""):
    """Green-unmutated AND red-under-its-own-mutation, or it is not a gate."""
    before = probe(assertion)
    if before is not True:
        emit(row="fixture", fixture=fixture, subject=subject,
             verdict="BROKEN_BASELINE", detail=before, note=note)
        return
    mutate()
    try:
        after = probe(assertion)
    finally:
        unmutate()
    restored = probe(assertion)
    verdict = "DISCRIMINATES" if after is not True else "DEAD"
    emit(row="fixture", fixture=fixture, subject=subject, verdict=verdict,
         under_mutation=("held" if after is True else "went red"),
         restored=(restored is True), note=note)


def main():
    import srmech
    emit(row="env", srmech_file=srmech.__file__, version=srmech.__version__,
         python=sys.version.split()[0])

    from srmech.cascade import leaves, vec_add
    from srmech.cascade import matrix_cascades as mc
    from srmech.signal_processing.closed_form_ops import iir

    # -- CONTROL: a planted DEAD fixture must be reported DEAD ---------------
    audit(
        fixture="CONTROL_planted_dead_fixture",
        subject="srmech.cascade.vec_add",
        # asserts nothing about its subject -- the shape of every fixture that
        # reads well and measures nothing
        assertion=lambda: None,
        mutate=lambda: setattr(leaves, "vec_add", lambda a, b: "mutated"),
        unmutate=lambda: setattr(leaves, "vec_add", vec_add),
        note="asserts nothing about its subject; if this comes back "
             "DISCRIMINATES the auditor is broken",
    )

    # -- 1. iir direct-form front door --------------------------------------
    real_check = iir._check_ba

    def _iir_guard_removed():
        iir._check_ba = lambda b, a, where="": (list(b), list(a))

    def _iir_guard_restored():
        iir._check_ba = real_check

    def _a_direct():
        for b, a in (([], [1.0]), ([1.0], []), ([1.0], [0.0])):
            try:
                iir.op([1.0, 2.0, 3.0], b, a)
            except ValueError as exc:
                assert "iir:" in str(exc)
                continue
            except Exception:                                 # noqa: BLE001
                raise AssertionError("not a ValueError")
            raise AssertionError("returned a value")

    audit("test_iir_front_door_refuses_what_its_c_peer_refuses[3]",
          "signal_processing.closed_form_ops.iir.op (direct b/a branch)",
          _a_direct, _iir_guard_removed, _iir_guard_restored,
          note="mutation = the rc430 state: no front-door domain guard")

    # -- 2. iir BIQUAD branch (the rc431-repair finding) ---------------------
    def _a_biquad():
        for sec in ([1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]):
            try:
                iir.op([1.0, 2.0, 3.0], [1.0], [1.0], biquad_sections=[sec])
            except ValueError as exc:
                assert "iir:" in str(exc) and "biquad section 0" in str(exc)
                continue
            except Exception:                                 # noqa: BLE001
                raise AssertionError("not a ValueError")
            raise AssertionError("returned a value")

    audit("test_iir_biquad_branch_refuses_a0_zero_too[2]",
          "signal_processing.closed_form_ops.iir.op (biquad branch)",
          _a_biquad, _iir_guard_removed, _iir_guard_restored,
          note="mutation = rc431's FIRST cut, which guarded only the direct "
               "branch; this assertion is the one that cut had no equivalent of")

    # -- 3. the negative control on the same guard --------------------------
    def _a_valid():
        assert iir.op([1.0, 0.0, 0.0, 0.0], [1.0], [1.0, -0.5]) == \
            [1.0, 0.5, 0.25, 0.125]
        assert iir.op([1.0, 2.0], [1.0], [1.0],
                      biquad_sections=[[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]]) == \
            [1.0, 2.0]

    def _iir_guard_over_broad():
        def _always(b, a, where=""):
            raise ValueError("iir: mutation -- refuses everything")
        iir._check_ba = _always

    audit("test_iir_still_filters_valid_input",
          "signal_processing.closed_form_ops.iir.op (valid input)",
          _a_valid, _iir_guard_over_broad, _iir_guard_restored,
          note="mutation = a guard bought by rejecting valid input")

    # -- 4. vec_add, both orientations --------------------------------------
    def _a_vec_add():
        import srmech.cascade as csc
        for a, b in (([1.0], [1.0, 2.0]), ([1.0, 2.0], [1.0])):
            try:
                csc.vec_add(a, b)
            except ValueError as exc:
                assert "vec_add:" in str(exc)
                continue
            except Exception:                                 # noqa: BLE001
                raise AssertionError("not a ValueError")
            raise AssertionError("returned a value")

    import srmech.cascade as csc
    real_vec_add = csc.vec_add

    def _vec_add_rc430():
        csc.vec_add = lambda a, b: [a[i] + b[i] for i in range(len(a))]

    def _vec_add_restore():
        csc.vec_add = real_vec_add

    audit("test_vec_add_refuses_mismatched_lengths_in_both_orientations",
          "srmech.cascade.vec_add",
          _a_vec_add, _vec_add_rc430, _vec_add_restore,
          note="mutation = the rc430 body verbatim (range(len(a)) alone). The "
               "SILENT half is the first orientation; a fixture asserting only "
               "the raising half would stay green here")

    # -- 4b. does the fixture catch the SILENT half specifically? ------------
    def _a_vec_add_silent_only():
        import srmech.cascade as c2
        try:
            c2.vec_add([1.0], [1.0, 2.0])
        except ValueError:
            return
        raise AssertionError("silently returned")

    audit("test_vec_add ... [SILENT orientation, isolated]",
          "srmech.cascade.vec_add",
          _a_vec_add_silent_only, _vec_add_rc430, _vec_add_restore,
          note="isolates the data-corrupting orientation, so a future edit "
               "cannot satisfy the fixture with the noisy half alone")

    # -- 5. lll_reduce shape guard ------------------------------------------
    real_lll_check = mc._lll_check_basis

    def _a_lll_shape():
        for bad in (5, None, [1, 2]):
            try:
                mc.lll_reduce(bad)
            except ValueError as exc:
                assert "lll_reduce:" in str(exc)
                continue
            except Exception:                                 # noqa: BLE001
                raise AssertionError("not a ValueError")
            raise AssertionError("returned a value")

    audit("test_lll_reduce_and_signed_sum_squared_refuse_shape_in_house_style",
          "srmech.cascade.matrix_cascades.lll_reduce (shape)",
          _a_lll_shape,
          lambda: setattr(mc, "_lll_check_basis", lambda basis: basis),
          lambda: setattr(mc, "_lll_check_basis", real_lll_check),
          note="mutation = the rc430 state: no shape guard at all")

    # -- 6. lll_reduce one-shot basis (the guard's own silent wrong answer) --
    rows = [[1, 1, 1], [-1, 0, 2], [3, 5, 6]]

    def _a_lll_oneshot():
        expected = mc.lll_reduce([list(r) for r in rows])
        assert expected
        assert mc.lll_reduce(iter([list(r) for r in rows])) == expected
        assert mc.lll_reduce([iter(r) for r in rows]) == expected
        assert mc.lll_reduce(r for r in rows) == expected

    real_lll_reduce = mc.lll_reduce

    def _lll_discard_return():
        """rc431's FIRST cut: validate, then pass the ORIGINAL object on."""
        def _mut(basis, delta=(3, 4)):
            real_lll_check(basis)              # return value discarded
            return mc._lll_reduce_pure(basis, delta)
        mc.lll_reduce = _mut

    audit("test_lll_reduce_shape_guard_does_not_eat_a_one_shot_basis",
          "srmech.cascade.matrix_cascades.lll_reduce (one-shot iterable)",
          _a_lll_oneshot, _lll_discard_return,
          lambda: setattr(mc, "lll_reduce", real_lll_reduce),
          note="mutation = rc431's first cut, which returned [] for a valid "
               "generator basis that rc430 reduced correctly")

    # -- 7. the overloaded-None residual ratchet: TIGHTNESS, not liveness ----
    sys.path.insert(0, str(pathlib.Path(__file__).resolve()
                           .parents[1] / "python" / "tests"))
    import test_native_contract_parity_rc431 as ncp

    cands = ncp._overloaded_none_candidates()
    adjudicated = {"iir_lfilter_f64_c", "svd_f64_c", "sturm_isolate_c",
                   "split_defect_c", "bessel_j_fixed_c"}
    residual = [c for c in cands if c[0] not in adjudicated]
    emit(row="ratchet", fixture="test_overloaded_none_residual_is_down_only",
         subject="_overloaded_none_candidates()",
         candidates=len(cands), residual=len(residual),
         ceil=ncp.CEIL_UNDECIDED,
         slack=ncp.CEIL_UNDECIDED - len(residual),
         verdict=("TIGHT" if len(residual) == ncp.CEIL_UNDECIDED else "SLACK"),
         note="a down-only ceil is a ratchet, not a mutation-testable "
              "assertion; the number is reported rather than asserted away")

    def _a_scanner_control():
        assert "iir_lfilter_f64_c" in {c[0] for c in
                                       ncp._overloaded_none_candidates()}

    real_native_py = ncp.NATIVE_PY

    audit("test_scanner_finds_the_known_site",
          "the wrapper-source scanner",
          _a_scanner_control,
          lambda: setattr(ncp, "NATIVE_PY", ncp.SRMECH_PY / "srmech"
                          / "version.py"),
          lambda: setattr(ncp, "NATIVE_PY", real_native_py),
          note="mutation = point the scanner at a file with no wrappers, the "
               "silent-parse-failure mode this control exists for")

    # -- 8. the floor gate's own controls -----------------------------------
    import test_invocable_returned_floor_rc431 as floor

    entries = floor._advertised_entries()
    emit(row="floor_env", advertised=len(entries))

    # 8a. the mutation control's zero must be capable of being non-zero
    ret_live, tol_live, skip_live = floor._classify(
        entries[:40], lambda _n, _a: None, floor._safe_synth)
    ret_mut, tol_mut, _ = floor._classify(
        entries[:40],
        lambda _n, _a: (_ for _ in ()).throw(ValueError("mutation")),
        floor._safe_synth)
    emit(row="fixture",
         fixture="test_classifier_cannot_report_returns_when_every_op_raises",
         subject="floor._classify (40-entry runtime-axis subset)",
         verdict=("DISCRIMINATES" if ret_live and not ret_mut else "DEAD"),
         returned_when_invoke_succeeds=len(ret_live),
         returned_when_every_op_raises=len(ret_mut),
         tolerated_under_mutation=len(tol_mut),
         note="the control asserts ZERO RETURNED under mutation; this shows "
              "the same classifier reports NON-zero when invocation succeeds, "
              "so its zero is a measurement and not a constant. Subset is a "
              "stated RUNTIME axis: the shipped gate runs all 650")

    # 8b. the SKIPPED-bucket control -- the exact false-zero shape rc431 hit
    synth_for = floor._synth_source()
    sentinel = floor._unsynthesizable_sentinel()
    foreign = object()          # the "wrong module object" the draft compared to
    carrying = [e.name for e in entries
                if any(v is sentinel for v in (synth_for(e) or {}).values())]
    carrying_foreign = [e.name for e in entries
                        if any(v is foreign
                               for v in (synth_for(e) or {}).values())]
    emit(row="fixture",
         fixture="test_skipped_bucket_is_populated_not_decorative",
         subject="the UNSYNTHESIZABLE sentinel identity",
         verdict=("DISCRIMINATES" if carrying and not carrying_foreign
                  else "DEAD"),
         carrying_consumers_sentinel=len(carrying),
         carrying_foreign_sentinel=len(carrying_foreign),
         note="the mutation is the defect this control was written for: "
              "comparing against a sentinel object the consumer does not hold "
              "yields 0, which is what shipped silently before it")

    # 8c. the floor set itself
    floor_names = {ln.strip() for ln
                   in floor.FLOOR_PATH.read_text(encoding="utf-8").splitlines()
                   if ln.strip() and not ln.startswith("#")}
    live = {e.name for e in entries}
    emit(row="fixture", fixture="test_invocable_returned_floor_holds",
         subject="tests/invocable_returned_rc431.txt",
         verdict=("DISCRIMINATES" if floor_names and floor_names <= live
                  else "DEAD"),
         floor_size=len(floor_names),
         stale_names=sorted(floor_names - live)[:5],
         note="a SET, so a regression names the op; non-empty and fully "
              "resident in the live advertised set, therefore each member is "
              "an assertion that can individually go red")

    dead = [r for r in ROWS if r.get("verdict") == "DEAD"
            and not r["fixture"].startswith("CONTROL_")]
    control = [r for r in ROWS if r.get("fixture", "").startswith("CONTROL_")]
    emit(row="summary",
         fixtures_audited=len([r for r in ROWS if r.get("row") == "fixture"]),
         dead=len(dead), dead_names=[r["fixture"] for r in dead],
         control_reported_dead=all(r["verdict"] == "DEAD" for r in control),
         null_classification="BOUNDED",
         bound="covers assertions with an in-process subject mutation; the "
               "down-only ceil row is a ratchet and is reported, not mutated")

    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                           for r in ROWS), encoding="utf-8", newline="\n")
    print(f"\n-> wrote {OUT}")
    if not all(r["verdict"] == "DEAD" for r in control):
        raise SystemExit("AUDITOR BROKEN: the planted dead fixture was not "
                         "reported DEAD; every other verdict here is void")
    if dead:
        raise SystemExit(f"DEAD FIXTURES: {[r['fixture'] for r in dead]}")


if __name__ == "__main__":
    main()
