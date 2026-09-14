"""D1 analysis over dumps from notes/_rc473_twin_d1_dump.py.

Usage: python notes/_rc473_twin_d1_analyze.py <python-root for srmech> <mode> <json...>

mode "before <base.json> [rc472.json]":
    the pre-repair C: w/theta_res agreement on the 24 filed angles, the
    per-turn law, which side an INDEPENDENT 2pi says is accurate, the
    transliterated pre-repair residue == the base C symbol on every row, and
    (with rc472.json) base-C == rc472-C on every row.
mode "after <cur.json>": bit-identity counts at symbol and wrapper, door.
mode "constants": delta of the Q64 2/pi, pi^2*delta, |_EPH_TWO_PI - 2pi|.
"""
import json
import sys
from fractions import Fraction

sys.path.insert(0, sys.argv[1])

from srmech.math import laplacian as lap
from srmech.math import rational as R
from srmech.math.rational import atan_series_truncate

mode = sys.argv[2]
GRID = 2.0 ** -44


def fx(h):
    return float.fromhex(h)


def mag(x):
    return x if x >= 0 else -x


def two_pi_machin(terms):
    a = atan_series_truncate(1, 5, terms)
    b = atan_series_truncate(1, 239, terms)
    return 32 * Fraction(a.numerator, a.denominator) - 8 * Fraction(b.numerator, b.denominator)


def two_pi_stormer(terms):
    # pi/4 = 6 atan(1/8) + 2 atan(1/57) + atan(1/239)  (Stormer 1896)
    a = atan_series_truncate(1, 8, terms)
    b = atan_series_truncate(1, 57, terms)
    c = atan_series_truncate(1, 239, terms)
    q = lambda t: Fraction(t.numerator, t.denominator)
    return 8 * (6 * q(a) + 2 * q(b) + q(c))


TWO_PI = two_pi_machin(120)
TWO_PI_B = two_pi_stormer(120)


def true_res(theta_hex):
    th = Fraction(fx(theta_hex))
    w = th / TWO_PI
    fl = w.numerator // w.denominator
    k = fl + (1 if 2 * (w - fl) >= 1 else 0)
    return th - k * TWO_PI


def old_residue(theta):
    ok, octant, r = R._q61_reduce(theta)
    assert ok
    oct_rel = {0: 0, 1: 1, 3: -1}.get(octant, (-2 if r >= 0 else 2))
    return float(oct_rel * R._Q61_HALF_PI_Q61 + r) / float(1 << 61)


if mode == "constants":
    print("2pi Machin(120) vs Stormer(120): %.4e" % float(mag(TWO_PI - TWO_PI_B)))
    q64 = Fraction(R._Q61_TWO_OVER_PI_Q64, 1 << 64)
    delta = mag(q64 - 2 / (TWO_PI / 2))
    import math
    print("Q64 2/pi = %d ; delta = %.4e = 2^%.2f" % (R._Q61_TWO_OVER_PI_Q64, float(delta), math.log2(float(delta))))
    pi = TWO_PI / 2
    print("pi^2 * delta = %.4e rad/turn" % float(pi * pi * delta))
    ep = Fraction(*lap._EPH_TWO_PI)
    print("|_EPH_TWO_PI - 2pi| = %.4e" % float(mag(ep - TWO_PI)))
    print("_EPH_TWO_PI N = %d (%d bits), limbs hi=0x%X lo=0x%X, N odd %s, N>>37 = %d" % (
        lap._EPH_TWO_PI[0], lap._EPH_TWO_PI[0].bit_length(), lap._EPH_TWO_PI[0] >> 64,
        lap._EPH_TWO_PI[0] & ((1 << 64) - 1), lap._EPH_TWO_PI[0] & 1, lap._EPH_TWO_PI[0] >> 37))
    sys.exit(0)

d = json.load(open(sys.argv[3]))
print("cell native=%s auth=%s version=%s python=%s rows=%d" % (
    d["native"], d["auth"], d["version"], d["python"], len(d["rows"])))

if mode == "before":
    filed = [r for r in d["rows"] if r["tag"] == "filed"]
    w_eq = sum(1 for r in filed if r["w_sym"] == r["w_pure"])
    res_eq = sum(1 for r in filed if fx(r["res_sym"]) == fx(r["res_pure"]))
    over = sum(1 for r in filed if mag(fx(r["res_sym"]) - fx(r["res_pure"])) > GRID)
    print("filed %d: w equal %d, theta_res equal %d, gap > 2^-44 on %d" % (len(filed), w_eq, res_eq, over))
    per = [(mag(fx(r["res_sym"]) - fx(r["res_pure"])) / mag(r["w_pure"]), fx(r["theta"]))
           for r in filed if mag(r["w_pure"]) >= 1e8]
    lo = min(p for p, _ in per); hi = max(p for p, _ in per)
    print("per-turn gap over %d rows with |w|>=1e8: [%.4e, %.4e], spread %.2f%%" % (len(per), lo, hi, 100 * (hi - lo) / lo))
    worst = max(filed, key=lambda r: mag(fx(r["res_sym"]) - fx(r["res_pure"])))
    g = mag(fx(worst["res_sym"]) - fx(worst["res_pure"]))
    print("worst gap %.5e = %.4e x 2^-44 at theta=%r" % (g, g / GRID, fx(worst["theta"])))
    closer = {"old_c": 0, "pure": 0, "tie": 0}
    for r in filed:
        t = true_res(r["theta"])
        eo = mag(Fraction(fx(r["res_sym"])) - t)
        ep = mag(Fraction(fx(r["res_pure"])) - t)
        closer["old_c" if eo < ep else "pure" if ep < eo else "tie"] += 1
    print("closer to independent 2pi residue:", closer)
    for th in (31.41592653589793, 3.1415926535897932e16):
        r = [x for x in filed if fx(x["theta"]) == th][0]
        t = true_res(r["theta"])
        print("  theta=%r |oldC-true| %.4e |pure-true| %.4e" % (
            th, float(mag(Fraction(fx(r["res_sym"])) - t)), float(mag(Fraction(fx(r["res_pure"])) - t))))
    mism = [r for r in d["rows"] if old_residue(fx(r["theta"])) != fx(r["res_sym"])]
    print("transliterated pre-repair residue == base C symbol: %d/%d rows (%d mismatches)" % (
        len(d["rows"]) - len(mism), len(d["rows"]), len(mism)))
    for r in mism[:5]:
        print("   MISMATCH", fx(r["theta"]), old_residue(fx(r["theta"])), fx(r["res_sym"]))
    if len(sys.argv) > 4:
        e = json.load(open(sys.argv[4]))
        print("second dump native=%s auth=%s version=%s rows=%d" % (e["native"], e["auth"], e["version"], len(e["rows"])))
        same = sum(1 for a, b in zip(d["rows"], e["rows"])
                   if a["theta"] == b["theta"] and a["st"] == b["st"] and a["w_sym"] == b["w_sym"] and a["res_sym"] == b["res_sym"])
        print("symbol (st, w, res) identical between the two libraries: %d/%d" % (same, len(d["rows"])))

if mode == "after":
    rows = d["rows"]
    def bad(r, key_w, key_r):
        return not (r[key_w] == r["w_pure"] and r[key_r] == r["res_pure"])
    for tag in ("filed", "extra", "fuzz"):
        rs = [r for r in rows if r["tag"].startswith(tag)]
        sym_bad = sum(1 for r in rs if r.get("st", 0) != 0 or bad(r, "w_sym", "res_sym")) if d["native"] else "n/a"
        disp_bad = sum(1 for r in rs if bad(r, "w_disp", "res_disp"))
        print("%-6s rows %6d  symbol mismatches %s  wrapper mismatches %d" % (tag, len(rs), sym_bad, disp_bad))
    print("fuzz families:", d["fuzz_families"])
    for x in d["door"]:
        print("door", x)
