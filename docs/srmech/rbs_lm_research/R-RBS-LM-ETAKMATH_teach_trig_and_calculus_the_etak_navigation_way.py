r"""R-RBS-LM-ETAKMATH (the user, 2026-06-08): "research how to teach TRIG and CALCULUS the ETAK navigation way. both are
asking how to find a SOLUTION in this field of continuous math."

The thesis: trig and calculus are both taught as ABSOLUTE-COORDINATE formula machines (memorize sin/cos, memorize the
derivative rules). The ETAK way (F551/F575) teaches FINDING A SOLUTION as NAVIGATION: you do NOT compute an absolute
position; you HOLD A MOVING REFERENCE and steer by the DEVIATION from it (the bearing), accumulating signed steps until
the deviation vanishes -- you have arrived. This is the DISCRETE cascade under the continuous-looking formula (the
continuous-number-line-as-obstacle pedagogy: everything is discrete; pi is a cascade, not a continuous mystery), and it
is EXACTLY what the silicon already does (CORDIC = shift-add+sign) and what srmech.calculus computes (Class-N series).

  TRIG the etak way = CORDIC. The unit circle is the STAR COMPASS (fixed bearing references atan(2^-k)). To find
  sin/cos of a target angle you do NOT look it up -- you NAVIGATE to the target bearing by a sequence of signed known
  micro-rotations, each step's sign = the BEARING DECISION (am I left or right of the reference?), driven by the
  DEVIATION (target - current). The deviation shrinks to zero = you have arrived; the (x,y) you carried IS (cos,sin).
  Solving a triangle = triangulating from bearings (the etak 'pencil of lines from a vertex', F575).

  CALCULUS the etak way. The DERIVATIVE = the RATE the reference's bearing changes as you move (etak progress reckoning:
  you measure progress by how fast the reference sweeps, not by absolute position) -- a discrete cascade of shrinking
  steps h, not a continuous limit-mystery. FINDING A ROOT / a number = NAVIGATE to it by deviation-corrections from a
  MOVING REFERENCE (Newton: the moving reference is the tangent line / the current bearing; each step corrects the
  deviation f(x); arrive when the deviation vanishes). INTEGRATION = dead reckoning (accumulate the signed bearing-steps
  along the path). srmech's best_rational navigates to a number by the Stern-Brocot bearing-tree -- the same etak move.

srmech 0.7.4: CORDIC uses srmech.calculus.atan2 for the star-compass bearings + shift-add (no multiply; powers of 2 =
shift), checked against srmech.calculus.{sin,cos}. Class-K sign = the bearing decision (no abs()). No CAD; no Workflow
tool; no sub-agents.
"""
import numpy as np
import srmech
from srmech import calculus


def sgn(x):
    return 1 if x >= 0 else -1                                            # Class-K bearing decision (no abs)


def main():
    print(f"=== R-RBS-LM-ETAKMATH — teach TRIG + CALCULUS the etak way: find a solution by NAVIGATING deviations from a moving reference  (srmech {srmech.__version__}) ===\n")

    # ===================== TRIG the etak way = CORDIC =====================
    NK = 24
    atan_tbl = [calculus.atan2(1.0 / (2 ** k), 1.0) for k in range(NK)]   # the STAR COMPASS: fixed bearings atan(2^-k)
    K = 1.0
    for k in range(NK):
        K *= 1.0 / (1.0 + 2.0 ** (-2 * k)) ** 0.5                         # CORDIC gain (a one-time attested constant)

    def cordic(target):
        """NAVIGATE to the target bearing by signed star-compass steps; return (cos,sin) + the shrinking deviations."""
        x, y, ang = K, 0.0, 0.0
        devs = []
        for k in range(NK):
            d = sgn(target - ang)                                        # BEARING DECISION = sign of the deviation
            x, y = x - d * (y / (2 ** k)), y + d * (x / (2 ** k))        # rotate by d*atan(2^-k): shift-add only
            ang += d * atan_tbl[k]
            devs.append(target - ang)
        return x, y, devs

    print("(A) TRIG = etak navigation (CORDIC): find sin/cos by steering to the target BEARING, not by lookup.")
    print(f"    {'target(rad)':>11}{'cos (navigated)':>17}{'srmech.cos':>13}{'sin (navigated)':>17}{'srmech.sin':>13}")
    for tgt in (0.3, 0.7854, 1.2):                                       # incl. 45deg = 0.7854
        cx, sy, devs = cordic(tgt)
        sc = calculus.cos_series_truncate(int(round(tgt * 1000)), 1000, 22); rc = sc[0] / sc[1]
        ss = calculus.sin_series_truncate(int(round(tgt * 1000)), 1000, 22); rs = ss[0] / ss[1]
        print(f"    {tgt:>11.4f}{cx:>17.6f}{rc:>13.6f}{sy:>17.6f}{rs:>13.6f}")
    _, _, devs = cordic(1.2)
    print(f"    the DEVIATION (target - current bearing) shrinks as you navigate: {[round(d,3) for d in devs[:7]]} ... -> 0")
    print(f"    -> you ARRIVE when the deviation vanishes; the (x,y) you carried IS (cos,sin). Each step's SIGN was the")
    print(f"    bearing decision; the bearings are the fixed star-compass atan(2^-k); no multiply -- shift-add (the silicon op).\n")

    # ===================== CALCULUS the etak way =====================
    print("(B) CALCULUS = etak navigation.")
    # (B1) the DERIVATIVE = the rate the reference's bearing changes (etak progress) -- a DISCRETE cascade of shrinking steps
    print("  (B1) the DERIVATIVE is the etak PROGRESS RATE (how fast the reference's bearing sweeps), a DISCRETE cascade:")
    x0 = 3.0
    f = lambda x: x * x                                                  # f(x)=x^2; true bearing-rate at x0 is 2*x0 = 6
    print(f"       f(x)=x^2 at x0={x0}: bearing-rate over a shrinking step h (NOT a continuous mystery -- a cascade):")
    for h in (1.0, 0.5, 0.25, 0.125, 0.0625):
        rate = (f(x0 + h) - f(x0)) / h
        print(f"         h={h:<7} progress-rate (f(x0+h)-f(x0))/h = {rate:.4f}   (-> 6 as the step shrinks)")
    print(f"       the h-cascade is the moving reference closing on 'beyond the horizon'; the limit 6 is where you arrive.\n")

    # (B2) FINDING A ROOT / a number = navigate by deviation-corrections from a MOVING REFERENCE (Newton = the tangent bearing)
    print("  (B2) FIND A SOLUTION (sqrt2) = NAVIGATE by deviation-corrections from a moving reference (Newton: the tangent is")
    print("       the current bearing; each step corrects the deviation f(x)=x^2-2; arrive when the deviation vanishes):")
    x = 1.0
    print(f"       {'step':>5}{'position x':>13}{'deviation x^2-2':>17}{'bearing decision':>18}")
    for k in range(6):
        dev = x * x - 2.0                                               # the deviation of the moving reference from the target
        print(f"       {k:>5}{x:>13.8f}{dev:>17.2e}{('overshoot->turn in' if dev>0 else 'undershoot->turn out'):>18}")
        x = x - dev / (2.0 * x)                                         # steer toward the moving reference (the tangent)
    print(f"       arrived: x={x:.10f} (sqrt2={2**0.5:.10f}); the deviation navigated to ~0 -- you did not COMPUTE sqrt2, you")
    print(f"       NAVIGATED to it. srmech.amsc.rational.best_rational does the same as a Stern-Brocot BEARING-TREE walk.\n")

    print("VERDICT (the etak way to teach trig + calculus):")
    print(f"  • BOTH ARE NAVIGATION, NOT LOOKUP: 'find a solution in continuous math' = HOLD A MOVING REFERENCE and steer by")
    print(f"    the DEVIATION (the bearing) until it vanishes. TRIG: navigate to a target BEARING by signed star-compass")
    print(f"    steps (CORDIC) -- the (x,y) carried is (cos,sin). CALCULUS: the DERIVATIVE is the progress-RATE of the")
    print(f"    reference's bearing; finding a ROOT is steering by deviation-corrections from the moving tangent (Newton).")
    print(f"  • THIS IS THE DISCRETE CASCADE UNDER THE CONTINUOUS FORMULA (the continuous-number-line-as-obstacle pedagogy):")
    print(f"    the angle is reached by DISCRETE signed bearing-steps; the derivative is a DISCRETE shrinking-step cascade;")
    print(f"    pi enters only as the star-compass calibration (a cascade, not a continuous mystery). The etak frame turns")
    print(f"    'continuous math' into a sequence of bearing decisions a learner (or the silicon) actually DOES.")
    print(f"  • IT IS ALREADY THE SUBSTRATE + srmech: CORDIC = shift-add+sign is exactly how rotation is done; srmech.calculus")
    print(f"    (Class-N series) and best_rational (Stern-Brocot bearing-tree) ARE the etak navigators. So 'teach the etak way'")
    print(f"    is teaching what the cascade already computes. Composes F551/F575 (etak = moving-reference navigation) +")
    print(f"    srmech.calculus + CORDIC + best_rational + the continuous-number-line pedagogy. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
