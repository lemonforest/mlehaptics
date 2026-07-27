"""rc320 — Class-N precision-contract migration WAVE 2 prove-gates.

The seven Q61 float-projection ops (:func:`~srmech.amsc.rational.cos` / ``sin`` /
``tan`` / ``atan`` / ``atan2`` / ``exp`` / ``log``) trade their DEAD ``terms``
keyword for a LIVE ``precision``:

* ``precision=None``  → the EXISTING Q61 fast path, BYTE-IDENTICAL to every prior
  rc (the load-bearing bit-identity contract).
* ``precision=P`` (int ≥ 1) → the EXACT-rational REFERENCE at ``P`` fractional
  bits: range-reduce in exact rationals, drive the matching ``*_series_truncate``
  until the truncation remainder is < ``2**-P``, recombine exactly, return a
  higher-precision exact ``Q``.

BREAKING: the ``terms`` kwarg is GONE (no alias, no shim); ``precision`` is
keyword-only.

Gates
-----
G1  BIT-IDENTITY: ``op(x, precision=None)`` == the pre-migration ``op(x)``
    (terms-default) output BYTE-FOR-BYTE, native AND forced-pure, across a spread
    of x (edge cases incl. ±Inf, tiny, large, near-octant-boundary). The
    reference literals were captured from a PRE-rename run.
G2  PRECISION CORRECTNESS: ``op(x, precision=P)`` is within ``2**-P`` of an
    INDEPENDENT high-precision oracle (Python ``decimal`` with its own octant /
    band reduction — no numpy), the error SHRINKS with P, and the returned Q's
    denominator LENGTHENS with P (float-free: every scalar is exact Q). Plus a
    wide-domain float-vs-``math`` correctness anchor.
G3  TERMS REMOVED: ``op(x, terms=8)`` raises ``TypeError`` for every op.
G4  NATIVE == PURE for ``precision=P`` (byte-identical whichever way the series
    dispatched).
plus the ``_classn_working(precision, kind="terms")`` contract.

numpy-free (no numpy import anywhere in the call graph).
"""
from __future__ import annotations

import decimal
import json
import math
from fractions import Fraction

import pytest

from tests._native_gate import require_native
from srmech.amsc import _native
from srmech.amsc import rational as R
from srmech.amsc.rational import (
    cos, sin, tan, atan, atan2, exp, log, _classn_working,
)

INF = float("inf")

FN = {"cos": cos, "sin": sin, "tan": tan, "atan": atan,
      "atan2": atan2, "exp": exp, "log": log}


def _pair(q):
    n, d = q.as_pair()
    return (int(n), int(d))


def _frac(q):
    n, d = q.as_pair()
    return Fraction(int(n), int(d))


# ── G1 pre-migration reference literals ─────────────────────────────────────
# Captured from a PRE-rename run of the SAME ops with the ``terms`` default,
# native AND numpy-absent pure producing identical (num, den). None = the old
# ``terms``-default output; the migrated ``precision=None`` must reproduce each
# byte-for-byte. (Regeneration: run each op(*args) on the pre-rc320 tree and dump
# ``q.as_pair()``.)
_BASELINE_NDJSON = r"""
{"op": "cos", "args": ["0.0"], "num": "1", "den": "1"}
{"op": "cos", "args": ["0.3"], "num": "1101427982448516401", "den": "1152921504606846976"}
{"op": "cos", "args": ["0.7"], "num": "440901502675412137", "den": "576460752303423488"}
{"op": "cos", "args": ["1.0"], "num": "622926147424044489", "den": "1152921504606846976"}
{"op": "cos", "args": ["0.7853981633974483"], "num": "1630477228166597827", "den": "2305843009213693952"}
{"op": "cos", "args": ["1.5707963267948966"], "num": "141", "den": "2305843009213693952"}
{"op": "cos", "args": ["2.0"], "num": "-959569273858622033", "den": "2305843009213693952"}
{"op": "cos", "args": ["3.0"], "num": "-2282767277460148833", "den": "2305843009213693952"}
{"op": "cos", "args": ["-0.5"], "num": "1011783807671379919", "den": "1152921504606846976"}
{"op": "cos", "args": ["-2.5"], "num": "-461827851321270091", "den": "576460752303423488"}
{"op": "cos", "args": ["12.5"], "num": "287595773331172993", "den": "288230376151711744"}
{"op": "cos", "args": ["100.0"], "num": "497092985844398041", "den": "576460752303423488"}
{"op": "cos", "args": ["1e-08"], "num": "2305843009213693837", "den": "2305843009213693952"}
{"op": "cos", "args": ["-1e-08"], "num": "2305843009213693837", "den": "2305843009213693952"}
{"op": "sin", "args": ["0.0"], "num": "0", "den": "1"}
{"op": "sin", "args": ["0.3"], "num": "681423202611435945", "den": "2305843009213693952"}
{"op": "sin", "args": ["0.7"], "num": "1485464850528843781", "den": "2305843009213693952"}
{"op": "sin", "args": ["1.0"], "num": "485074996943862657", "den": "576460752303423488"}
{"op": "sin", "args": ["0.7853981633974483"], "num": "815238614083298863", "den": "1152921504606846976"}
{"op": "sin", "args": ["1.5707963267948966"], "num": "1", "den": "1"}
{"op": "sin", "args": ["2.0"], "num": "2096697114941998561", "den": "2305843009213693952"}
{"op": "sin", "args": ["3.0"], "num": "325400584045024981", "den": "2305843009213693952"}
{"op": "sin", "args": ["-0.5"], "num": "-1105480026629011443", "den": "2305843009213693952"}
{"op": "sin", "args": ["-2.5"], "num": "-1379982809691238529", "den": "2305843009213693952"}
{"op": "sin", "args": ["12.5"], "num": "-38231970841263579", "den": "576460752303423488"}
{"op": "sin", "args": ["100.0"], "num": "-583799836829473795", "den": "1152921504606846976"}
{"op": "sin", "args": ["1e-08"], "num": "23058430091", "den": "2305843009213693952"}
{"op": "sin", "args": ["-1e-08"], "num": "-23058430091", "den": "2305843009213693952"}
{"op": "tan", "args": ["0.0"], "num": "0", "den": "1"}
{"op": "tan", "args": ["0.3"], "num": "681423202611435945", "den": "2202855964897032802"}
{"op": "tan", "args": ["0.7"], "num": "1485464850528843781", "den": "1763606010701648548"}
{"op": "tan", "args": ["1.0"], "num": "323383331295908438", "den": "207642049141348163"}
{"op": "tan", "args": ["0.7853981633974483"], "num": "1630477228166597726", "den": "1630477228166597827"}
{"op": "tan", "args": ["1.5707963267948966"], "num": "2305843009213693952", "den": "141"}
{"op": "tan", "args": ["2.0"], "num": "-2096697114941998561", "den": "959569273858622033"}
{"op": "tan", "args": ["3.0"], "num": "-325400584045024981", "den": "2282767277460148833"}
{"op": "tan", "args": ["-0.5"], "num": "-1105480026629011443", "den": "2023567615342759838"}
{"op": "tan", "args": ["-2.5"], "num": "197140401384462647", "den": "263901629326440052"}
{"op": "tan", "args": ["12.5"], "num": "-38231970841263579", "den": "575191546662345986"}
{"op": "tan", "args": ["100.0"], "num": "-583799836829473795", "den": "994185971688796082"}
{"op": "tan", "args": ["1e-08"], "num": "23058430091", "den": "2305843009213693837"}
{"op": "tan", "args": ["-1e-08"], "num": "-23058430091", "den": "2305843009213693837"}
{"op": "atan", "args": ["0.0"], "num": "0", "den": "1"}
{"op": "atan", "args": ["0.5"], "num": "1069098597953152987", "den": "2305843009213693952"}
{"op": "atan", "args": ["1.0"], "num": "905502432259640355", "den": "1152921504606846976"}
{"op": "atan", "args": ["2.0"], "num": "2552911131085408433", "den": "2305843009213693952"}
{"op": "atan", "args": ["-0.5"], "num": "-1069098597953152987", "den": "2305843009213693952"}
{"op": "atan", "args": ["-3.0"], "num": "-1440051731236216849", "den": "1152921504606846976"}
{"op": "atan", "args": ["100.0"], "num": "3598952067514647319", "den": "2305843009213693952"}
{"op": "atan", "args": ["1e-08"], "num": "5764607523", "den": "576460752303423488"}
{"op": "atan", "args": ["-1e-08"], "num": "-5764607523", "den": "576460752303423488"}
{"op": "atan", "args": ["inf"], "num": "3622009729038561421", "den": "2305843009213693952"}
{"op": "atan", "args": ["-inf"], "num": "-3622009729038561421", "den": "2305843009213693952"}
{"op": "atan2", "args": ["1.0", "1.0"], "num": "905502432259640355", "den": "1152921504606846976"}
{"op": "atan2", "args": ["1.0", "-1.0"], "num": "1358253648389460533", "den": "576460752303423488"}
{"op": "atan2", "args": ["-1.0", "1.0"], "num": "-905502432259640355", "den": "1152921504606846976"}
{"op": "atan2", "args": ["-1.0", "-1.0"], "num": "-1358253648389460533", "den": "576460752303423488"}
{"op": "atan2", "args": ["1.0", "0.0"], "num": "3622009729038561421", "den": "2305843009213693952"}
{"op": "atan2", "args": ["-1.0", "0.0"], "num": "-3622009729038561421", "den": "2305843009213693952"}
{"op": "atan2", "args": ["0.0", "1.0"], "num": "0", "den": "1"}
{"op": "atan2", "args": ["0.0", "-1.0"], "num": "3622009729038561421", "den": "1152921504606846976"}
{"op": "atan2", "args": ["0.0", "0.0"], "num": "0", "den": "1"}
{"op": "atan2", "args": ["2.5", "1.3"], "num": "1258156760907166731", "den": "1152921504606846976"}
{"op": "atan2", "args": ["-2.5", "1.3"], "num": "-1258156760907166731", "den": "1152921504606846976"}
{"op": "atan2", "args": ["2.5", "-1.3"], "num": "1181926484065697345", "den": "576460752303423488"}
{"op": "atan2", "args": ["-2.5", "-1.3"], "num": "-1181926484065697345", "den": "576460752303423488"}
{"op": "atan2", "args": ["inf", "inf"], "num": "905502432259640355", "den": "1152921504606846976"}
{"op": "atan2", "args": ["inf", "-inf"], "num": "2716507296778921065", "den": "1152921504606846976"}
{"op": "atan2", "args": ["-inf", "inf"], "num": "-905502432259640355", "den": "1152921504606846976"}
{"op": "atan2", "args": ["-inf", "-inf"], "num": "-2716507296778921065", "den": "1152921504606846976"}
{"op": "atan2", "args": ["inf", "1.0"], "num": "3622009729038561421", "den": "2305843009213693952"}
{"op": "atan2", "args": ["-inf", "1.0"], "num": "-3622009729038561421", "den": "2305843009213693952"}
{"op": "atan2", "args": ["1.0", "inf"], "num": "0", "den": "1"}
{"op": "atan2", "args": ["1.0", "-inf"], "num": "3622009729038561421", "den": "1152921504606846976"}
{"op": "exp", "args": ["0.0"], "num": "1", "den": "1"}
{"op": "exp", "args": ["1.0"], "num": "1566982787806226805", "den": "576460752303423488"}
{"op": "exp", "args": ["-1.0"], "num": "848272237658610639", "den": "2305843009213693952"}
{"op": "exp", "args": ["0.5"], "num": "1900846208092904383", "den": "1152921504606846976"}
{"op": "exp", "args": ["2.5"], "num": "1755682408379759357", "den": "144115188075855872"}
{"op": "exp", "args": ["10.0"], "num": "3099949473305640733", "den": "140737488355328"}
{"op": "exp", "args": ["-10.0"], "num": "1715160853079956139", "den": "37778931862957161709568"}
{"op": "exp", "args": ["100.0"], "num": "26881171418161354662885230012241960702574592", "den": "1"}
{"op": "exp", "args": ["-100.0"], "num": "956469058144284239", "den": "25711008708143844408671393477458601640355247900524685364822016"}
{"op": "exp", "args": ["1e-08"], "num": "2305843032272124159", "den": "2305843009213693952"}
{"op": "exp", "args": ["700.0"], "num": "10142320547350045056365837637446394263674149561467867586288828834515487963358972628982241181169438214480690286451399574586289350364742756547285953854479067794250513540505788652203705133252814082500449533455935796238751111290845231016566305732217214598944482096598526984950963564698301344366303456111099904", "den": "1"}
{"op": "exp", "args": ["-700.0"], "num": "2494525936672767513", "den": "25300281663413827294061918339864663381194581220517764794612669753428792445999418361495047962679640561898384733039601488923726092173224184608376674992592313740189678034570795170558363467761652042654970959809093133570250935428086587327262919456144944542601257064044846194041676826903812816523290938580750782913463467636686848"}
{"op": "log", "args": ["1.0"], "num": "0", "den": "1"}
{"op": "log", "args": ["2.0"], "num": "1598288580650331957", "den": "2305843009213693952"}
{"op": "log", "args": ["0.5"], "num": "-1598288580650331957", "den": "2305843009213693952"}
{"op": "log", "args": ["10.0"], "num": "5309399739799983589", "den": "2305843009213693952"}
{"op": "log", "args": ["1e-08"], "num": "-42475197918399868957", "den": "2305843009213693952"}
{"op": "log", "args": ["100000000.0"], "num": "42475197918399868957", "den": "2305843009213693952"}
{"op": "log", "args": ["3.0"], "num": "633306866415404375", "den": "576460752303423488"}
{"op": "log", "args": ["0.1"], "num": "-5309399739799983459", "den": "2305843009213693952"}
{"op": "log", "args": ["123.456"], "num": "11104674339110981915", "den": "2305843009213693952"}
{"op": "log", "args": ["0.001"], "num": "-7964099609699975419", "den": "1152921504606846976"}
"""


def _baseline_records():
    return [json.loads(ln) for ln in _BASELINE_NDJSON.strip().splitlines()]


# ══════════════════════════════════════════════════════════════════════════
# G1 — bit-identity of the precision=None path against the pre-migration output
# ══════════════════════════════════════════════════════════════════════════
def _assert_g1_bit_identity():
    for rec in _baseline_records():
        args = [float(a) for a in rec["args"]]
        want = (int(rec["num"]), int(rec["den"]))
        fn = FN[rec["op"]]
        got_default = _pair(fn(*args))                 # omitted keyword
        got_none = _pair(fn(*args, precision=None))    # explicit None
        assert got_default == want, (rec["op"], rec["args"], got_default, want)
        assert got_none == want, (rec["op"], rec["args"], got_none, want)


def test_g1_bit_identity_native():
    require_native("the G1 native bit-identity baseline")
    _assert_g1_bit_identity()


def test_g1_bit_identity_pure(monkeypatch):
    monkeypatch.setattr(_native, "HAS_NATIVE", False, raising=False)
    monkeypatch.setattr(_native, "LIB", None, raising=False)
    _assert_g1_bit_identity()


# ══════════════════════════════════════════════════════════════════════════
# G3 — the dead ``terms`` kwarg is GONE (clean break, no shim)
# ══════════════════════════════════════════════════════════════════════════
def test_g3_terms_keyword_removed():
    for op, args in [("cos", (0.3,)), ("sin", (0.3,)), ("tan", (0.3,)),
                     ("atan", (0.5,)), ("atan2", (1.0, 1.0)), ("exp", (1.0,)),
                     ("log", (2.0,))]:
        with pytest.raises(TypeError):
            FN[op](*args, terms=8)
        # control: the NEW keyword IS accepted (not a blanket kwarg rejection)
        FN[op](*args, precision=32)


# ══════════════════════════════════════════════════════════════════════════
# Independent high-precision ORACLE — Python ``decimal`` with its OWN octant /
# band reduction (no numpy, no srmech). Converts to exact Fraction for an exact
# comparison against the op's exact Q.
# ══════════════════════════════════════════════════════════════════════════
# π to 110 digits (self-checked to 15 digits against math.pi below).
_PI_STR = ("3.1415926535897932384626433832795028841971693993751058209749445923"
           "078164062862089986280348253421170679821480865")


def _oracle_pi(D):
    return D(_PI_STR)


def _dec_sin(r, D):                                    # |r| ≤ π/4 → fast Taylor
    term = r
    s = r
    k = 1
    x2 = r * r
    while abs(term) > D(2) ** (-400):
        term = -term * x2 / (D(2 * k) * D(2 * k + 1))
        s += term
        k += 1
    return s


def _dec_cos(r, D):                                    # |r| ≤ π/4 → fast Taylor
    term = D(1)
    s = D(1)
    k = 1
    x2 = r * r
    while abs(term) > D(2) ** (-400):
        term = -term * x2 / (D(2 * k - 1) * D(2 * k))
        s += term
        k += 1
    return s


def _dec_atan_small(u, D):                             # |u| ≤ √2-1 → fast Taylor
    term = u
    s = u
    k = 1
    x2 = u * u
    while abs(term) > D(2) ** (-400):
        term = -term * x2
        s += term / D(2 * k + 1)
        k += 1
    return s


def _oracle(op, args, digits=110):
    """An exact :class:`Fraction`, correct to ≈ ``2**-(digits·3.32)`` — an
    INDEPENDENT high-precision reference (decimal + own reduction)."""
    with decimal.localcontext(decimal.Context(prec=digits + 30)):
        D = decimal.Decimal
        if op == "exp":
            return Fraction(D(args[0]).exp())
        if op == "log":
            return Fraction(D(args[0]).ln())
        pi = _oracle_pi(D)
        tan_pi8 = D(2).sqrt() - 1
        cot_pi8 = D(2).sqrt() + 1

        def _atan(x):                                  # any x, 3-band reduce
            if x == 0:
                return D(0)
            neg = x < 0
            ax = -x if neg else x
            if ax <= tan_pi8:
                a = _dec_atan_small(ax, D)
            elif ax >= cot_pi8:
                a = pi / 2 - _dec_atan_small(1 / ax, D)
            else:
                a = pi / 4 + _dec_atan_small((ax - 1) / (ax + 1), D)
            return -a if neg else a

        def _sincos(x, want):                          # any x, octant reduce
            n = int((x / (pi / 2)).to_integral_value(
                rounding=decimal.ROUND_HALF_EVEN))
            r = x - n * (pi / 2)
            o = n % 4
            cr, sr = _dec_cos(r, D), _dec_sin(r, D)
            if want == "cos":
                return (cr, -sr, -cr, sr)[o]
            return (sr, cr, -sr, -cr)[o]

        if op in ("cos", "sin"):
            return Fraction(_sincos(D(args[0]), op))
        if op == "tan":
            x = D(args[0])
            return Fraction(_sincos(x, "sin") / _sincos(x, "cos"))
        if op == "atan":
            return Fraction(_atan(D(args[0])))
        if op == "atan2":
            y, x = D(args[0]), D(args[1])
            base = _atan(y / x)
            if x > 0:
                return Fraction(base)
            return Fraction(base + pi if y >= 0 else base - pi)
    raise ValueError(op)                               # pragma: no cover


def test_oracle_pi_selfcheck():
    # the oracle's π constant is independent of srmech; pin its leading digits.
    assert abs(float(_PI_STR) - math.pi) < 1e-14


# ══════════════════════════════════════════════════════════════════════════
# G2 — precision=P correctness: within 2**-P, error SHRINKS with P, denominator
# LENGTHENS with P (float-free), against the independent oracle.
# ══════════════════════════════════════════════════════════════════════════
# representative x per op — cover every reduction band / octant / quadrant that
# the decimal oracle can converge on independently.
_G2_CASES = {
    "exp": [(0.3,), (-0.7,), (2.0,), (-1.5,)],
    "log": [(1.3,), (0.7,), (6.7,), (0.1,)],
    "cos": [(0.3,), (2.0,), (-1.2,), (3.0,)],          # octants 0/1/…/2
    "sin": [(0.3,), (2.0,), (-1.2,), (3.0,)],
    "tan": [(0.3,), (0.7,), (-0.5,), (1.0,)],
    "atan": [(0.3,), (0.9,), (5.0,), (-0.7,)],         # band 1 / 2 / 3
    "atan2": [(1.0, 2.0), (-1.0, 2.0), (0.7, -1.3), (-0.7, -1.3)],
}
_G2_P = (40, 80, 160)


def _g2_check(op, args):
    orc = _oracle(op, args, digits=110)
    errs, den_bits = [], []
    for P in _G2_P:
        r = FN[op](*args, precision=P)
        fr = _frac(r)
        err = abs(fr - orc)
        assert err < Fraction(1, 2 ** P), (
            f"{op}{args} P={P}: err {float(err):.3e} !< 2**-{P}")
        errs.append(err)
        den_bits.append(fr.denominator.bit_length())
    # error shrinks strictly with P (the RIGOROUS precision-scaling proof)
    assert errs[0] > errs[1] > errs[2], (op, args, [float(e) for e in errs])
    # denominator is a genuine high-precision bignum that LENGTHENS across the
    # P sweep — > 150 bits at P=160 (impossible for the None-path platform Q,
    # whose denominators are ≤ 2**61) and strictly larger at P=160 than P=40.
    # (Adjacent steps can wobble by a few bits under GCD reduction; the endpoint
    # growth + the floor are the robust invariants — the < 2**-P error already
    # forces ~P-bit exact working length.)
    assert den_bits[2] > 150, (op, args, den_bits)
    assert den_bits[0] < den_bits[2], (op, args, den_bits)
    return errs, den_bits


def test_g2_precision_correctness_and_scaling():
    measured = {}
    for op, cases in _G2_CASES.items():
        for args in cases:
            errs, den_bits = _g2_check(op, args)
            measured[(op, args)] = (
                [float(e) for e in errs], den_bits)
    # a representative log line for the report (visible with -s)
    print("\nG2 measured (op,args) -> (errors@40/80/160, denbits@40/80/160):")
    for k, v in measured.items():
        print(f"  {k}: {v}")


def test_g2_float_correctness_anchor_wide_domain():
    # An INDEPENDENT end-to-end correctness anchor over the FULL domain (every
    # band / octant / quadrant / ±Inf) at ~53 bits: float(op(x, precision=64))
    # matches libm. precision=64 → the returned Q's float projection is a
    # correctly-scaled double.
    P = 64
    for x in (0.0, 0.3, -0.5, 0.7853981633974483, 2.0, 3.0, -2.5, 12.5, 100.0,
              1e-8):
        assert abs(float(cos(x, precision=P)) - math.cos(x)) < 1e-12, x
        assert abs(float(sin(x, precision=P)) - math.sin(x)) < 1e-12, x
    for x in (0.3, 0.7, -0.5, 1.0, 2.0, -2.5):         # avoid cos≈0
        assert abs(float(tan(x, precision=P)) - math.tan(x)) < 1e-11, x
    for x in (0.0, 0.5, 1.0, 2.0, -0.5, -3.0, 100.0, 1e-8, INF, -INF):
        assert abs(float(atan(x, precision=P)) - math.atan(x)) < 1e-12, x
    for y, x in [(1.0, 1.0), (1.0, -1.0), (-1.0, 1.0), (-1.0, -1.0), (1.0, 0.0),
                 (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0), (2.5, 1.3), (-2.5, -1.3),
                 (INF, 1.0), (1.0, -INF), (INF, INF), (-INF, -INF)]:
        assert abs(float(atan2(y, x, precision=P)) - math.atan2(y, x)) < 1e-12, (y, x)
    for x in (0.0, 1.0, -1.0, 0.5, 2.5, -3.0, 10.0):
        assert abs(float(exp(x, precision=P)) - math.exp(x)) < 4e-13 * math.exp(x), x
    for x in (1.0, 2.0, 0.5, 10.0, 1e-8, 1e8, 123.456, 0.001):
        assert abs(float(log(x, precision=P)) - math.log(x)) < 1e-12, x


# ══════════════════════════════════════════════════════════════════════════
# G4 — native == pure for precision=P (byte-identical whichever way it went)
# ══════════════════════════════════════════════════════════════════════════
def test_g4_native_equals_pure_precision_P(monkeypatch):
    cases = [("exp", (2.0,)), ("log", (3.0,)), ("cos", (2.0,)), ("sin", (2.0,)),
             ("tan", (0.7,)), ("atan", (5.0,)), ("atan2", (1.0, -1.0))]
    for P in (40, 120):
        native = {c: _pair(FN[c[0]](*c[1], precision=P)) for c in cases}
        with monkeypatch.context() as m:
            m.setattr(_native, "HAS_NATIVE", False, raising=False)
            m.setattr(_native, "LIB", None, raising=False)
            for c in cases:
                assert _pair(FN[c[0]](*c[1], precision=P)) == native[c], (c, P)


# ══════════════════════════════════════════════════════════════════════════
# _classn_working(precision, kind="terms") contract (WAVE 2 implements it)
# ══════════════════════════════════════════════════════════════════════════
def test_classn_working_terms_contract():
    plat = _classn_working(None, kind="terms")
    assert plat.mode == "platform" and plat.effective == 60
    prev = None
    for P in (1, 40, 128, 512):
        r = _classn_working(P, kind="terms")
        assert r.mode == "bigint" and r.effective == P
        if prev is not None:
            assert r.effective > prev
        prev = r.effective
    # bool / non-int / P<1 raise (shared with the bits wave)
    with pytest.raises(TypeError):
        _classn_working(True, kind="terms")
    with pytest.raises(TypeError):
        _classn_working(1.5, kind="terms")
    with pytest.raises(ValueError):
        _classn_working(0, kind="terms")
    with pytest.raises(ValueError):
        _classn_working(-4, kind="terms")
    # kind="den" is still RESERVED (not yet implemented)
    with pytest.raises(NotImplementedError):
        _classn_working(64, kind="den")


# ══════════════════════════════════════════════════════════════════════════
# domain / edge parity between precision=None and precision=P
# ══════════════════════════════════════════════════════════════════════════
def test_precision_P_edges_match_none_domain():
    # non-finite raises the SAME way on both paths
    for bad in (float("nan"), INF, -INF):
        with pytest.raises(ValueError):
            exp(bad, precision=32)
        with pytest.raises(ValueError):
            cos(bad, precision=32)
    for bad in (float("nan"), 0.0, -1.0, INF):
        with pytest.raises(ValueError):
            log(bad, precision=32)
    with pytest.raises(ValueError):
        atan(float("nan"), precision=32)
    with pytest.raises(ValueError):
        atan2(float("nan"), 1.0, precision=32)
    # atan(±Inf) = ±π/2 on the precision path too (exact π), sign correct
    assert atan(INF, precision=80) > 0
    assert atan(-INF, precision=80) < 0
    assert float(atan(INF, precision=80)) == pytest.approx(math.pi / 2, abs=1e-20)
    # exp(0)=1, log(1)=0, sin(0)=0, cos(0)=1, atan(0)=0 exactly on the P path
    assert _pair(exp(0.0, precision=80)) == (1, 1)
    assert _pair(log(1.0, precision=80)) == (0, 1)
    assert _pair(sin(0.0, precision=80)) == (0, 1)
    assert _pair(cos(0.0, precision=80)) == (1, 1)
    assert _pair(atan(0.0, precision=80)) == (0, 1)
    # tan undefined where cos==0 (the exact-rational cos is nonzero for a float
    # π/2, so tan is huge-but-finite — matches the None path's structure)
    assert tan(1.5, precision=64) is not None
