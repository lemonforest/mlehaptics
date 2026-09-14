"""S5 - the record's Kerr-extremal 'super-logarithmic gap-closing sequence' {2.000, 1.485, 0.282, 0.089}:
invert gap = 2*sqrt(1-x^2) to find which a/M values were sampled. Uses srmech Class-N sqrt via best_rational
bracketing is unnecessary here; plain float inversion (instrument, disclosed).
Also: sign flips of sin(r*t) over one outer period (the recursive-Hopf 'depth' count) by exact zero enumeration.
"""
import math
from fractions import Fraction as F
for g in (2.000, 1.485, 0.282, 0.089):
    x = math.sqrt(1 - (g / 2) ** 2)
    print(f"gap {g:.3f} <- a/M = {x:.5f}")
# zeros of sin(r t) in [0, 2*pi): t = k*pi/r, k = 0..2r-1  -> 2r sign changes per closed period
for stack in ((7,), (7, 7), (7, 7, 7), (3, 7), (11, 13)):
    r = 1
    for s in stack:
        r *= s
    zeros = [F(k, r) for k in range(0, 2 * r)]  # in units of pi
    print(f"stack {stack}: frequency {r}, zeros per period {len(zeros)} = 2*prod")
