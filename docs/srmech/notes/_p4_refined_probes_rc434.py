"""`#T1130` P4 — refined probes for the clauses P3 could not decide.

P3's ``dispatch/verify-path`` probe was INADEQUATE and is retracted here: it
passed an UNREGISTERED op name, so ``lookup()`` raised
``UnknownOperationError`` before the ``path="verify"`` branch could be reached.
That is an instrument defect, not a package defect — recorded rather than
quietly re-run.

Also probes the declared trigger CLAUSES P3 skipped (a declared exception with
several stated triggers can be enforced for one and silent for another — which
is exactly how ``cyclic_gcd`` hid), and the ``ZeroDivisionError``-vs-
``ValueError`` precedent question for zero denominators.
"""

from __future__ import annotations

import json
import os
import sys

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
OUT = os.path.join(REPO, "docs/srmech/notes/_p4_refined_probes_rc434.ndjson")

sys.path.insert(0, PKG)


def main() -> int:
    import srmech
    from srmech import _native

    fh = open(OUT, "w", encoding="utf-8")

    def emit(rec):
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
        }
    )

    def probe(pid, declared, fn, *args, **kwargs):
        rec = {"record": "probe", "probe_id": pid, "declared": declared}
        try:
            v = fn(*args, **kwargs)
            rec["outcome"] = "NOT_ENFORCED"
            rec["returned_repr"] = repr(v)[:200]
            rec["returned_type"] = type(v).__name__
        except BaseException as exc:  # noqa: BLE001
            got = type(exc).__name__
            mro = [c.__name__ for c in type(exc).__mro__[:6]]
            rec["observed"] = got
            rec["mro"] = mro
            rec["message"] = str(exc)[:260]
            rec["outcome"] = (
                "ENFORCED" if (got == declared or declared in mro) else "TYPE_MISMATCH"
            )
        emit(rec)
        return rec

    # ---------------------------------------------------------------- P3-RETRACT
    from srmech.signal_processing import path_registry as pr
    from srmech.signal_processing.cascade_dispatcher import dispatch

    ops = sorted(pr.registered_ops())
    emit({"record": "note", "registered_ops_n": len(ops), "sample": ops[:10]})

    if ops:
        probe("dispatch/verify-path-REGISTERED", "DispatcherNotImplementedError",
              dispatch, ops[0], path="verify")
    else:
        emit(
            {
                "record": "probe",
                "probe_id": "dispatch/verify-path-REGISTERED",
                "declared": "DispatcherNotImplementedError",
                "outcome": "UNSUPPORTED",
                "detail": "registry is empty at import time; registering one below",
            }
        )

    # register a probe op so the verify branch is reachable regardless
    try:
        pr.register(
            "t1130_probe_op",
            path_a_fn=lambda *a, **k: 0,
            classes=("A",),
        )
        registered = True
    except TypeError:
        try:
            pr.register("t1130_probe_op", lambda *a, **k: 0)
            registered = True
        except Exception as exc:
            registered = False
            emit(
                {
                    "record": "note",
                    "detail": f"could not register probe op: {type(exc).__name__}: {exc}",
                    "register_signature": str(
                        __import__("inspect").signature(pr.register)
                    ),
                }
            )
    except Exception as exc:
        registered = False
        emit(
            {
                "record": "note",
                "detail": f"register raised {type(exc).__name__}: {exc}",
                "register_signature": str(__import__("inspect").signature(pr.register)),
            }
        )

    if registered:
        probe("dispatch/verify-path-FRESHREG", "DispatcherNotImplementedError",
              dispatch, "t1130_probe_op", path="verify")

    # ---------------------------------------------------- unprobed trigger clauses
    from srmech.math.laplacian import dense_solve, schur_complement
    from srmech.cascade.cayley_dickson import defect_ladder
    from srmech.chemistry.reactions import balance_reaction
    from srmech.music._spectra import common_period
    from srmech.math.cyclic import lcm, gcd
    from srmech.math.primes import factor
    from srmech.cascade.composites import cyclic_gcd

    probe("dense_solve/B-rowcount", "ValueError", dense_solve,
          [[1, 0], [0, 1]], [[1], [1], [1]])
    probe("schur_complement/empty-boundary", "ValueError", schur_complement,
          [[1, 0], [0, 1]], [])
    probe("schur_complement/oob-boundary", "ValueError", schur_complement,
          [[1, 0], [0, 1]], [99])
    probe("schur_complement/dup-boundary", "ValueError", schur_complement,
          [[1, 0], [0, 1]], [0, 0])
    probe("defect_ladder/non-power-of-two", "ValueError", defect_ladder,
          [1, 0, 0], [1, 0, 0], [1, 0, 0])
    probe("defect_ladder/table-dim-disagree", "ValueError", defect_ladder,
          [1, 0], [1, 0], [1, 0], [[[1]]])
    probe("balance_reaction/unbalanceable", "ValueError", balance_reaction,
          ["H2", "O2"])
    probe("common_period/inharmonic", "ValueError", common_period,
          [(1, 1), (3, 2), (7, 5)])

    # self-declared-unreachable clauses: BOUNDED, not REFUTED
    probe("lcm/overflow-clause", "OverflowError", lcm, 2 ** 63, 2 ** 63 - 1)
    probe("factor/overflow-clause", "OverflowError", factor, 2 ** 64 - 1)

    # ---------------------------------------------------- cyclic_gcd, in detail
    for a, b in ((2 ** 64, 5), (2 ** 64 + 7, 3), (2 ** 200, 2 ** 199)):
        probe(f"cyclic_gcd/oversize a={a}", "ValueError", cyclic_gcd, a, b)
        probe(f"cyclic.gcd/oversize a={a}", "ValueError", gcd, a, b)

    # ---------------------------------------------------- zero-denominator precedent
    from srmech.math.covering import linking_number_cwf
    from srmech.cascade.frame_carrier import frame_carrier
    from srmech.math.cyclic import primitive_integer_vector

    probe("PRECEDENT covering.linking_number_cwf/zero-den", "ZeroDivisionError",
          linking_number_cwf, (1, 0), (1, 2))
    probe("PRECEDENT frame_carrier/zero-den", "ZeroDivisionError",
          frame_carrier, "sin", 1, 0, 3)
    probe("PRECEDENT primitive_integer_vector/zero-den", "ZeroDivisionError",
          primitive_integer_vector, [(1, 0), (2, 1)])
    try:
        from srmech.math.rational import Q

        probe("PRECEDENT Q/zero-den", "ZeroDivisionError", Q, 1, 0)
    except Exception as exc:
        emit({"record": "note", "detail": f"Q import: {type(exc).__name__}: {exc}"})

    fh.close()
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
