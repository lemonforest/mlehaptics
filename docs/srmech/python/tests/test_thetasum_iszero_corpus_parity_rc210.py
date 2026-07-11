"""rc210 — the ``ThetaSum.is_zero`` shipped-corpus NO-REGRESSION + C↔pure PARITY guard.

``tests/data/thetasum_iszero_corpus_rc210.ndjson`` is the deduplicated corpus of every
distinct cleared numerator the shipped elliptic / thetasum suites decided through the
pure ``is_zero`` path at the rc209 baseline (126 objects: 74 shipped-True identities +
52 shipped-False non-identities), captured by tracing ``ThetaSum._is_zero_py`` across
the 19 elliptic test modules (computational provenance: the trace harness serialised
``(prefactor, theta-args)`` exactly as marshalled to the C peer).

Three guards:

  1. NO REGRESSION (pure): every shipped-True object is still CERTIFICATE-PROVEN zero
     by the rc210 sound recursion — through the normal two-stage decision AND through
     the certificate recursion alone (fast path off, the stronger claim).
  2. NO FALSE ZERO (pure): every shipped-False object is proven NONZERO (none may
     flip to a zero certificate).
  3. C↔PURE PARITY (native builds): for every corpus object the rebuilt
     ``srmech_thetasum_is_zero_interpolation`` verdict EQUALS the pure certificate
     bool — the rc99 pattern extended to the whole shipped corpus. A non-None native
     verdict differing from pure on ANY object is a BLOCKER (the worst outcome of the
     rc210 rebuild would be a NEW false zero from the C mirror). Declines
     (SRMECH_ERR_OVERFLOW → None) are counted and must not occur on this corpus.
"""
import json
import os

import pytest

from srmech.amsc import ThetaSum
from srmech.amsc.ellbase import EllMonomial, Theta
from srmech.amsc.q import Q
from srmech.amsc.thetasum import _NONZERO, _ZERO, _decide_thetasum
from srmech.amsc import _native

_NDJ = os.path.join(os.path.dirname(__file__), "data",
                    "thetasum_iszero_corpus_rc210.ndjson")


def _mono(ser):
    n, d, exps = ser
    return EllMonomial(Q(int(n), int(d)), {s: int(e) for s, e in exps})


def _build(obj):
    return ThetaSum(terms=[(Q(1, 1), _mono(p), tuple(Theta(_mono(a)) for a in args))
                           for p, args in obj])


def _corpus():
    with open(_NDJ, encoding="utf-8") as f:
        recs = [json.loads(line) for line in f if line.strip()]
    assert len(recs) == 126
    assert sum(1 for r in recs if r["verdict"]) == 74
    return recs


def test_corpus_shipped_true_stays_proven_zero_pure():
    fails = []
    for r in _corpus():
        if not r["verdict"]:
            continue
        ts = _build(r["object"])
        if _decide_thetasum(ts, use_fastpath=True) != _ZERO:
            fails.append((r["test"], "two-stage"))
        if _decide_thetasum(ts, use_fastpath=False) != _ZERO:
            fails.append((r["test"], "certificate-recursion-alone"))
    assert not fails, f"shipped-True objects no longer proven zero: {fails[:10]}"


def test_corpus_shipped_false_proven_nonzero_pure():
    flips = []
    weak = []
    for r in _corpus():
        if r["verdict"]:
            continue
        ts = _build(r["object"])
        v = _decide_thetasum(ts, use_fastpath=True)
        if v == _ZERO:
            flips.append(r["test"])
        elif v != _NONZERO:
            weak.append((r["test"], v))
    assert not flips, f"shipped-False objects FALSELY proven zero: {flips[:10]}"
    # the rc210 recursion proves every shipped-False corpus object outright NONZERO
    assert not weak, f"shipped-False objects merely declined (expected NONZERO): {weak[:10]}"


@pytest.mark.skipif(not _native.has_native_thetasum_interpolation(),
                    reason="native structural-certificate peer not loaded")
def test_corpus_native_equals_pure_on_every_object():
    mismatches = []
    declines = []
    for r in _corpus():
        ts = _build(r["object"])
        cv = ts._is_zero_interpolation_c()
        pv = ts._is_zero_interpolation()
        if cv is None:
            declines.append(r["test"])
        elif cv != pv:
            mismatches.append((r["test"], {"c": cv, "py": pv}))
        # the full dispatched decision must agree with the pure oracle either way
        assert ts.is_zero == ts._is_zero_py()
    assert not mismatches, f"NATIVE≠PURE (BLOCKER): {mismatches[:10]}"
    assert not declines, f"native peer declined on corpus objects: {declines[:10]}"
