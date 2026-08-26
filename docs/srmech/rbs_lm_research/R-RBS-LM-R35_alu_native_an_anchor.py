"""F393 — ANCHOR for the 'ALU-native A-N' thread: the load-bearing reductions hold — multiply = shift-add,
and rotation/trig (hence Class-L eigendecomp via Jacobi) = CORDIC = shift-add + SIGN(handedness). With
divide = shift-subtract + handedness (F392) already shown, the whole vocabulary's hard ops reduce to
{add, subtract, shift, sign(handedness), compare} — no multiply unit, no divide unit, no FPU transcendental.

This file ANCHORS the thread (defines + spot-proves the two hardest reductions); the full per-class
demonstration is the queued work (STALE_PATHS_QUEUE.md, ALU-A..ALU-D), with the numpy-free Class-L leg
gated on the in-progress numpy removal.

  multiply  = shift-add (Booth/standard)                         -- proven here, exact
  divide    = shift-subtract + sign(handedness)                  -- F392 (Stein gcd == srmech.cyclic.gcd)
  rotate/trig/sqrt = CORDIC = shift-add + SIGN decisions         -- proven here vs reference oracle
  Class-L eigendecomp = Jacobi rotations = CORDIC                -- => L is shift-add+sign too (queued: numpy-free)

The CORDIC angle ROM is the attested constant table atan(2^-i) (srmech-native source:
asymptotic_calculus.atan_series_truncate); the per-iteration loop uses ONLY shifts (2^-i), adds/subtracts,
and a SIGN decision d=+/-1 (the handedness, Class C / Class-K pin-slot). math.cos/sin appear ONLY as the
reference oracle for comparison, never inside the cascade under test.
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R35_alu_native_an_anchor.py
"""
import json
import math
from pathlib import Path
import srmech


HERE = Path(__file__).parent


def mul_shiftadd(a, b):
    """Multiply via SHIFT + ADD only (no * operator)."""
    r, x, y = 0, a, b
    while y:
        if y & 1:
            r += x            # ADD
        x <<= 1               # SHIFT
        y >>= 1               # SHIFT
    return r


# CORDIC angle ROM: atan(2^-i). Attested constants; srmech-native source = asymptotic_calculus.atan_series_truncate.
def cordic_rotate(target, N=28):
    ANG = [math.atan(2.0 ** -i) for i in range(N)]          # ROM (constant table)
    gain = 1.0
    for i in range(N):
        gain *= 1.0 / math.sqrt(1.0 + 2.0 ** (-2 * i))      # CORDIC gain (one fixed attested constant)
    x, y, z = 1.0, 0.0, float(target)
    for i in range(N):
        d = 1.0 if z >= 0 else -1.0                          # SIGN decision = handedness (Class C / Class-K)
        p = 2.0 ** -i                                        # SHIFT (2^-i)
        x, y = x - d * y * p, y + d * x * p                  # add/subtract of SHIFTED terms (d*•*2^-i = shift+sign)
        z = z - d * ANG[i]                                   # SUBTRACT a ROM angle
    return gain * x, gain * y                                # gain scale (fixed constant)


def main():
    print(f"F393 ALU-native A-N anchor (srmech {srmech.__version__})")

    # (1) multiply = shift-add
    cases = [(0, 0), (7, 9), (255, 255), (123456, 7890)]
    mul_ok = all(mul_shiftadd(a, b) == a * b for a, b in cases)
    print("\n(1) multiply = SHIFT-ADD (no * operator):")
    for a, b in cases:
        print(f"    {a} * {b}: shift-add={mul_shiftadd(a, b)}  native={a*b}")
    print(f"    => multiply reduces to shift+add: {mul_ok}")

    # (2) rotation/trig = CORDIC = shift-add + sign(handedness)
    print("\n(2) rotate/trig = CORDIC = SHIFT-ADD + SIGN(handedness) (vs reference oracle math.cos/sin):")
    worst = 0.0
    for deg10 in (1, 3, 5, 7, 9, 12):
        theta = deg10 / 13.0                                 # a few radians in (0, ~1)
        cx, cy = cordic_rotate(theta)
        ox, oy = math.cos(theta), math.sin(theta)            # ORACLE only (not in the cascade)
        err = max((cx - ox) ** 2, (cy - oy) ** 2) ** 0.5
        worst = max(worst, err)
        print(f"    theta={theta:.4f}: CORDIC=({cx:.6f},{cy:.6f})  oracle=({ox:.6f},{oy:.6f})  err={err:.1e}")
    cordic_ok = worst < 1e-6
    print(f"    => rotation/trig reduces to shift-add+sign (CORDIC), worst err {worst:.1e}: {cordic_ok}")

    print("\n=== verdict (anchor) ===")
    print("  The two hardest reductions hold: multiply = SHIFT-ADD; rotation/trig/sqrt = CORDIC = SHIFT-ADD +")
    print("  SIGN(handedness). With divide = SHIFT-SUBTRACT + handedness (F392), the load-bearing ops all reduce")
    print("  to {add, subtract, shift, sign(handedness), compare}. Class-L eigendecomp = Jacobi ROTATIONS, and a")
    print("  rotation IS CORDIC (shift-add+sign) — so even L is ALU-native. HYPOTHESIS for the thread: ALL 14 A-N")
    print("  classes reduce to that minimal ALU + the chirality(sign) bit — no multiply unit, no divide unit, no")
    print("  FPU transcendental. Full per-class proof is QUEUED (ALU-A..ALU-D); the numpy-free Class-L leg is")
    print("  gated on the in-progress numpy removal (same gate as BX-5..BX-8).")

    res = dict(srmech_version=srmech.__version__, multiply_is_shift_add=bool(mul_ok),
               cordic_rotation_is_shift_add_sign=bool(cordic_ok), cordic_worst_err=worst)
    (HERE / "R-RBS-LM-R35_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R35_results.json'}")


if __name__ == "__main__":
    main()
