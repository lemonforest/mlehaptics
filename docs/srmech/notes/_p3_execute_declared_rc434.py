"""`#T1130` P3 — EXECUTE every declared trigger against the shipped op.

For each of the 52 P1 candidates, fire the input class the docstring names and
record what ACTUALLY happens: exception type, message, or the returned value if
it does not raise.  A ruling read off the call site without opening the callee
is exactly the move that produced two wrong diagnoses in this arc, so nothing
here is inferred.

Each probe is bounded by ``signal.alarm`` so a blocking op (``bus.connect``)
cannot stall the run.  Results stream to disk record-by-record and are fsynced,
so a kill at any point still leaves every completed probe on disk.

Falsifier per probe:
    H0: "the declared exception E is raised for this input class"
    observed == E                      -> ENFORCED   (H0 held)
    observed is another exception      -> TYPE_MISMATCH
    no exception (value returned)      -> NOT_ENFORCED
    probe could not construct input    -> UNSUPPORTED (NOT evidence either way)

No numpy, no stdlib math/fractions/decimal, no abs().
"""

from __future__ import annotations

import json
import os
import signal
import sys
import traceback

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
OUT = os.path.join(REPO, "docs/srmech/notes/_p3_execute_declared_rc434.ndjson")

sys.path.insert(0, PKG)


class _Timeout(Exception):
    pass


def _alarm(_sig, _frm):
    raise _Timeout("probe exceeded 20s")


# (probe_id, dotted_path, declared_exception, args, kwargs, what_it_tests)
PROBES: list[tuple] = [
    # ---- biology.genome -------------------------------------------------
    ("genome.discrete_writhe/self-meet", "srmech.biology.genome.discrete_writhe",
     "ValueError", ([(0, 0, 0), (1, 0, 0), (0, 0, 0), (1, 0, 0)],), {},
     "strand meets itself in 3D"),
    ("genome.cwf_consistency_mod2/tree", "srmech.biology.genome.cwf_consistency_mod2",
     "ValueError", ([(0, 1)], [0]), {"n": 2},
     "tree has zero fundamental cycles"),
    ("genome.genome_fiber_holonomy/no-leaf-dim",
     "srmech.biology.genome.genome_fiber_holonomy",
     "ValueError", (b"\x00\x01",), {}, "missing leaf_dim"),
    ("genome.genome_fiber_holonomy/bad-byte",
     "srmech.biology.genome.genome_fiber_holonomy",
     "ValueError", (b"\xff\xff",), {"leaf_dim": 2}, "non-Q8 byte"),
    ("genome.genome_octonion_holonomy/bad-byte",
     "srmech.biology.genome.genome_octonion_holonomy",
     "ValueError", (b"\xff\xff",), {"leaf_dim": 2}, "non-octonion byte"),
    ("genome.genome_octonion_associator/bad-byte",
     "srmech.biology.genome.genome_octonion_associator",
     "ValueError", (b"\xff\xff",), {"leaf_dim": 2}, "non-octonion byte"),
    # ---- biology.q8 -----------------------------------------------------
    ("q8.q8_mult/bad", "srmech.biology.q8.q8_mult", "ValueError", (99, 0), {},
     "not a valid Q8 element"),
    ("q8.q8_conjugate/bad", "srmech.biology.q8.q8_conjugate", "ValueError", (99,), {},
     "not a valid Q8 element"),
    ("q8.q8_project_v4/bad", "srmech.biology.q8.q8_project_v4", "ValueError",
     (bytes([99]),), {}, "non-Q8 byte"),
    # ---- bus ------------------------------------------------------------
    ("bus.connect/missing", "srmech.bus._client.connect", "FileNotFoundError",
     ("t1130-no-such-endpoint",), {}, "no endpoint registration"),
    # ---- cascade.atoms --------------------------------------------------
    ("atoms.pin_slot_at_zero/complex", "srmech.cascade.atoms.pin_slot_at_zero",
     "TypeError", (complex(1, 2),), {}, "complex operand"),
    ("atoms.magnitude/complex", "srmech.cascade.atoms.magnitude",
     "TypeError", (complex(1, 2),), {}, "complex operand"),
    # ---- cascade.cayley_dickson ----------------------------------------
    ("cd.table_product/empty-table", "srmech.cascade.cayley_dickson.table_product",
     "ValueError", ([], [1], [1]), {}, "empty table"),
    ("cd.table_product/float-const", "srmech.cascade.cayley_dickson.table_product",
     "TypeError", ([[[1.5]]], [1], [1]), {}, "non-int structure constant"),
    ("cd.defect_ladder/unequal", "srmech.cascade.cayley_dickson.defect_ladder",
     "ValueError", ([1, 0], [1, 0, 0], [1, 0]), {}, "operands of unequal length"),
    ("cd.inertia_signature/empty", "srmech.cascade.cayley_dickson.inertia_signature",
     "ValueError", ([],), {}, "empty table"),
    ("cd.inertia_signature/ragged", "srmech.cascade.cayley_dickson.inertia_signature",
     "ValueError", ([[[1], [0]], [[0]]],), {}, "not dim x dim x dim"),
    ("cd.inertia_signature/float-const",
     "srmech.cascade.cayley_dickson.inertia_signature",
     "TypeError", ([[[1.5]]],), {}, "non-int structure constant"),
    # ---- cascade.composites --------------------------------------------
    ("composites.cyclic_gcd/negative", "srmech.cascade.composites.cyclic_gcd",
     "ValueError", (-1, 5), {}, "negative input"),
    ("composites.cyclic_gcd/oversize", "srmech.cascade.composites.cyclic_gcd",
     "ValueError", (2 ** 64, 5), {}, "exceeds uint64 parity surface"),
    # ---- cascade.frame_carrier -----------------------------------------
    ("frame_carrier/bad-func", "srmech.cascade.frame_carrier.frame_carrier",
     "ValueError", ("no_such_func", 1, 1, 3), {}, "bad func name"),
    ("frame_carrier/zero-den", "srmech.cascade.frame_carrier.frame_carrier",
     "ValueError", ("sin", 1, 0, 3), {}, "zero denominator"),
    ("frame_carrier/bad-sigma", "srmech.cascade.frame_carrier.frame_carrier",
     "ValueError", ("sin", 1, 2, 3), {"sigma": 7}, "sigma not in {+1,-1}"),
    # ---- chemistry ------------------------------------------------------
    ("reactions.balance_reaction/bad-type",
     "srmech.chemistry.reactions.balance_reaction",
     "TypeError", ([1, 2],), {}, "unsupported species entry type"),
    ("reactions.balance_reaction/unbalanceable",
     "srmech.chemistry.reactions.balance_reaction",
     "ValueError", (["H2", "O2"],), {}, "UNBALANCEABLE (trivial kernel)"),
    # ---- dsl ------------------------------------------------------------
    ("dsl.build_chain_from_toml_str/malformed",
     "srmech.dsl._toml_chain.build_chain_from_toml_str",
     "TOMLDecodeError", ("[[[ not toml",), {}, "malformed TOML"),
    ("dsl.build_chain_from_toml_str/schema",
     "srmech.dsl._toml_chain.build_chain_from_toml_str",
     "ValueError", ('[chain]\nname="d"\n[[stage]]\nop="no_such_op_t1130"\n',), {},
     "schema mismatch / unknown op"),
    ("dsl.run_toml_chain/unknown-op", "srmech.dsl._tool_surface.run_toml_chain",
     "ValueError", ('[chain]\nname="d"\n[[stage]]\nop="no_such_op_t1130"\n', 1), {},
     "unknown cascade op"),
    ("dsl.run_toml_chain/malformed", "srmech.dsl._tool_surface.run_toml_chain",
     "ValueError", ("[[[ not toml", 1), {}, "malformed spec"),
    ("dsl.run_toml_chain/not-str", "srmech.dsl._tool_surface.run_toml_chain",
     "TypeError", (123, 1), {}, "spec is not a string"),
    # ---- math.covering --------------------------------------------------
    ("covering.linking_number_cwf/zero-den",
     "srmech.math.covering.linking_number_cwf",
     "ValueError", ((1, 0), (1, 2)), {}, "denominator is 0"),
    ("covering.linking_number_cwf/not-ints",
     "srmech.math.covering.linking_number_cwf",
     "ValueError", ((1.5, 2), (1, 2)), {}, "pair is not two ints"),
    # ---- math.cyclic ----------------------------------------------------
    ("cyclic.lcm/overflow", "srmech.math.cyclic.lcm", "OverflowError",
     (2 ** 63, 2 ** 63 - 1), {}, "RESULT exceeds uint64"),
    ("cyclic.lcm/negative", "srmech.math.cyclic.lcm", "ValueError", (-1, 5), {},
     "negative operand"),
    ("cyclic.lcm/not-int", "srmech.math.cyclic.lcm", "TypeError", ("x", 5), {},
     "non-int operand"),
    ("cyclic.primitive_integer_vector/bad-shape",
     "srmech.math.cyclic.primitive_integer_vector",
     "TypeError", (object(),), {}, "unsupported input shape"),
    ("cyclic.primitive_integer_vector/zero-den",
     "srmech.math.cyclic.primitive_integer_vector",
     "ValueError", ([(1, 0), (2, 1)],), {}, "zero denominator"),
    # ---- math.hdc -------------------------------------------------------
    ("hdc.hamming/zero-len", "srmech.math.hdc.hamming", "ValueError", (b"", b""), {},
     "lengths are zero"),
    ("hdc.hamming/differ", "srmech.math.hdc.hamming", "ValueError",
     (b"\x00", b"\x00\x00"), {}, "lengths differ"),
    ("hdc.similarity/zero-len", "srmech.math.hdc.similarity", "ValueError",
     (b"", b""), {}, "lengths are zero"),
    ("hdc.similarity/differ", "srmech.math.hdc.similarity", "ValueError",
     (b"\x00", b"\x00\x00"), {}, "lengths differ"),
    # ---- math.laplacian -------------------------------------------------
    ("laplacian.dense_solve/singular-exact", "srmech.math.laplacian.dense_solve",
     "ZeroDivisionError", ([[1, 1], [1, 1]], [[1], [1]]), {"exact": True},
     "singular A on the exact path"),
    ("laplacian.dense_solve/nonsquare", "srmech.math.laplacian.dense_solve",
     "ValueError", ([[1, 1, 1], [1, 1, 1]], [[1], [1]]), {}, "non-square A"),
    ("laplacian.schur_complement/singular-interior",
     "srmech.math.laplacian.schur_complement",
     "ZeroDivisionError", ([[0, 0], [0, 0]], [0]), {"exact": True},
     "singular interior block"),
    ("laplacian.schur_complement/nonsquare",
     "srmech.math.laplacian.schur_complement",
     "ValueError", ([[1, 1, 1], [1, 1, 1]], [0]), {}, "non-square L"),
    ("laplacian.quaternion_laplacian/bad-n",
     "srmech.math.laplacian.quaternion_laplacian",
     "ValueError", (-1, []), {}, "bad n"),
    ("laplacian.quaternion_laplacian/bad-gain",
     "srmech.math.laplacian.quaternion_laplacian",
     "ValueError", (2, [(0, 1)]), {"gains": [[0, 0, 0]]}, "non-4-vector gain"),
    ("laplacian.octonion_laplacian/bad-n",
     "srmech.math.laplacian.octonion_laplacian",
     "ValueError", (-1, []), {}, "bad n"),
    ("laplacian.octonion_laplacian/bad-gain",
     "srmech.math.laplacian.octonion_laplacian",
     "ValueError", (2, [(0, 1)]), {"gains": [[0, 0, 0]]}, "non-8-vector gain"),
    ("laplacian.responsion/bad-kind", "srmech.math.laplacian.responsion",
     "ValueError", ([[1, 0], [0, 1]], [1, 0], 0), {"kind": "no_such_kind"},
     "unknown kind"),
    ("laplacian.responsion/resolvent-pole", "srmech.math.laplacian.responsion",
     "ZeroDivisionError", ([[1, 0], [0, 1]], [1, 0], 1), {"kind": "resolvent"},
     "z in the spectrum (resolvent pole)"),
    # ---- math.octonion --------------------------------------------------
    ("octonion.oct_mult/bad", "srmech.math.octonion.oct_mult", "ValueError",
     (999, 0), {}, "not a valid octonion element"),
    ("octonion.oct_conjugate/bad", "srmech.math.octonion.oct_conjugate", "ValueError",
     (999,), {}, "not a valid octonion element"),
    ("octonion.oct_torsor_act/bad", "srmech.math.octonion.oct_torsor_act", "ValueError",
     (999, 0), {}, "not a valid octonion element"),
    # ---- math.primes ----------------------------------------------------
    ("primes.factor/negative", "srmech.math.primes.factor", "ValueError", (-1,), {},
     "negative n"),
    ("primes.factor/not-int", "srmech.math.primes.factor", "TypeError", ("x",), {},
     "non-int n"),
    ("primes.factor/oversize", "srmech.math.primes.factor", "ValueError",
     (2 ** 64,), {}, "exceeds uint64 range"),
    # ---- music ----------------------------------------------------------
    ("spectra.spectrum_tier/empty", "srmech.music._spectra.spectrum_tier",
     "ValueError", ([],), {}, "empty spectrum"),
    ("spectra.spectrum_tier/float", "srmech.music._spectra.spectrum_tier",
     "TypeError", ([1.5, 2.0],), {}, "a float ratio"),
    ("spectra.spectrum_tier/bad-open", "srmech.music._spectra.spectrum_tier",
     "ValueError", ([(1, 1), (2, 1)],), {"open_partials": (99,)},
     "out-of-range open index"),
    ("spectra.commensurability_verdict/empty",
     "srmech.music._spectra.commensurability_verdict",
     "ValueError", ([],), {}, "empty spectrum"),
    ("spectra.commensurability_verdict/float",
     "srmech.music._spectra.commensurability_verdict",
     "TypeError", ([1.5, 2.0],), {}, "a float ratio"),
    ("spectra.common_period/open", "srmech.music._spectra.common_period",
     "ValueError", ([(1, 1), (2, 1)],), {"open_partials": (0,)},
     "spectrum is open"),
    ("spectra.common_period/float", "srmech.music._spectra.common_period",
     "TypeError", ([1.5, 2.0],), {}, "a float ratio"),
    # ---- physics.qm.octonion -------------------------------------------
    ("qm.octonion_left_mult/short", "srmech.physics.qm.octonion.octonion_left_mult",
     "ValueError", ([1, 0, 0],), {}, "not an 8-vector"),
    ("qm.octonion_right_mult/short", "srmech.physics.qm.octonion.octonion_right_mult",
     "ValueError", ([1, 0, 0],), {}, "not an 8-vector"),
    ("qm.octonion_conjugate/short", "srmech.physics.qm.octonion.octonion_conjugate",
     "ValueError", ([1, 0, 0],), {}, "not an 8-vector"),
    ("qm.octonion_norm/short", "srmech.physics.qm.octonion.octonion_norm",
     "ValueError", ([1, 0, 0],), {}, "not an 8-vector"),
    # ---- physics.qm.quaternion -----------------------------------------
    ("qm.quaternion_left_mult/short",
     "srmech.physics.qm.quaternion.quaternion_left_mult",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_right_mult/short",
     "srmech.physics.qm.quaternion.quaternion_right_mult",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_conjugate/short",
     "srmech.physics.qm.quaternion.quaternion_conjugate",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_norm/short", "srmech.physics.qm.quaternion.quaternion_norm",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_log/short", "srmech.physics.qm.quaternion.quaternion_log",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_slerp/short", "srmech.physics.qm.quaternion.quaternion_slerp",
     "ValueError", ([1, 0], [1, 0, 0, 0], 0.5), {}, "q0 not a 4-vector"),
    # ---- physics.qm.triality -------------------------------------------
    ("qm.triality_cycle/unknown", "srmech.physics.qm.triality.triality_cycle",
     "ValueError", ("no_such_frame",), {}, "unknown frame string"),
    ("qm.triality_companions/short", "srmech.physics.qm.triality.triality_companions",
     "ValueError", ([[1, 0], [0, 1]],), {}, "not shape (8,8)"),
    ("qm.triality_relation_residual/short",
     "srmech.physics.qm.triality.triality_relation_residual",
     "ValueError", ([[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 0], [0, 1]]), {},
     "not shape (8,8)"),
    # ---- signal_processing ----------------------------------------------
    ("dispatcher.dispatch/unknown-op",
     "srmech.signal_processing.cascade_dispatcher.dispatch",
     "UnknownOperationError", ("no_such_op_t1130",), {}, "op_name not registered"),
    ("dispatcher.dispatch/verify-path",
     "srmech.signal_processing.cascade_dispatcher.dispatch",
     "DispatcherNotImplementedError", ("decompose",), {"path": "verify"},
     'path="verify" in Phase 1'),
    ("ffr.verify_rotation_class_n_cycle_order/bad-D",
     "srmech.signal_processing.form_function_rotation."
     "verify_rotation_class_n_cycle_order",
     "ValueError", (1,), {"D": 7}, "D is invalid"),
    # ---- spectral -------------------------------------------------------
    ("spectral.similarity/differ", "srmech.spectral.similarity", "ValueError",
     (b"\x00", b"\x00\x00"), {}, "different byte-lengths"),
    ("spectral.similarity/zero-len", "srmech.spectral.similarity", "ValueError",
     (b"", b""), {}, "zero-length inputs"),
]


def resolve(dotted: str):
    parts = dotted.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        modname = ".".join(parts[:cut])
        try:
            mod = __import__(modname, fromlist=["*"])
        except Exception:
            continue
        obj = mod
        try:
            for attr in parts[cut:]:
                obj = getattr(obj, attr)
        except AttributeError:
            continue
        return obj
    raise ImportError(dotted)


def main() -> int:
    import srmech
    from srmech import _native

    fh = open(OUT, "w", encoding="utf-8")

    def emit(rec: dict) -> None:
        fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    emit(
        {
            "record": "meta",
            "srmech_file": srmech.__file__,
            "srmech_version": srmech.__version__,
            "has_native": bool(_native.HAS_NATIVE),
            "python": sys.version.split()[0],
            "n_probes": len(PROBES),
        }
    )

    signal.signal(signal.SIGALRM, _alarm)
    tally: dict[str, int] = {}

    for probe_id, dotted, declared, args, kwargs, what in PROBES:
        rec = {
            "record": "probe",
            "probe_id": probe_id,
            "op": dotted,
            "declared": declared,
            "tests": what,
        }
        try:
            fn = resolve(dotted)
        except Exception as exc:
            rec["outcome"] = "UNSUPPORTED"
            rec["detail"] = f"resolve failed: {type(exc).__name__}: {exc}"
            tally["UNSUPPORTED"] = tally.get("UNSUPPORTED", 0) + 1
            emit(rec)
            continue

        signal.alarm(20)
        try:
            value = fn(*args, **kwargs)
            signal.alarm(0)
            rec["outcome"] = "NOT_ENFORCED"
            rec["returned_type"] = type(value).__name__
            rec["returned_repr"] = repr(value)[:220]
        except _Timeout:
            signal.alarm(0)
            rec["outcome"] = "UNSUPPORTED"
            rec["detail"] = "probe timed out (20s)"
        except BaseException as exc:  # noqa: BLE001 - we are classifying, not handling
            signal.alarm(0)
            got = type(exc).__name__
            rec["observed"] = got
            rec["message"] = str(exc)[:300]
            rec["mro"] = [c.__name__ for c in type(exc).__mro__[:5]]
            if got == declared or declared in rec["mro"]:
                rec["outcome"] = "ENFORCED"
            else:
                rec["outcome"] = "TYPE_MISMATCH"
            tb = traceback.extract_tb(exc.__traceback__)
            if tb:
                last = tb[-1]
                rec["raised_at"] = f"{os.path.relpath(last.filename, PKG)}:{last.lineno}"
                rec["raised_in_this_func"] = len(tb) <= 2
        tally[rec["outcome"]] = tally.get(rec["outcome"], 0) + 1
        emit(rec)

    emit({"record": "tally", "by_outcome": tally})
    fh.close()
    print(f"wrote {OUT}  tally={tally}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
