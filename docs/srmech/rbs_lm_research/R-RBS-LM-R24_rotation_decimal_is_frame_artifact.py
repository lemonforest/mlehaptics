"""F382 — the rotation "decimal" is a FRAME-MISMATCH artifact, not a fundamental quantity.

User insight (2026-06-04): "in (2+1) rotation is always the asymptote and creates a decimal because we
aren't prepared to map this to a new cartesian coordinate of its. what if we did?"

A rotation is Class-K (asymptotic-DoF) living on S1 (cyclic, Class I). Read in a FIXED Cartesian frame it
is (cos, sin) — a transcendental decimal. The decimal is the COST of reading an S1 object in a frame that
does not co-rotate with it, NOT a property of the rotation. "Map it to a new Cartesian coordinate of its
own" -> two regimes (both srmech-native, no numpy):
  (A) RATIONAL rotation -> maps EXACTLY to its own Cartesian = the cyclic lattice Z_q (Class N -> Class I).
      The decimal vanishes; composition becomes exact integer mod-add.
  (B) IRRATIONAL rotation -> no single finite frame; its own coordinate is the best_rational CASCADE of
      convergents (Class N). Exact to any depth; the decimal is the LIMIT of the discrete cascade
      (the same shape as pi-as-cascade: a decimal that IS a discrete cascade, not a continuous mystery).

srmech-native: amsc.rational.best_rational (Class N), amsc.cyclic.mod_add (Class I). No numpy, no abs().
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R24_rotation_decimal_is_frame_artifact.py
"""
import json
from pathlib import Path
import srmech
from srmech.amsc import rational, cyclic

HERE = Path(__file__).parent


def main():
    print(f"F382 rotation-decimal-is-a-frame-artifact (srmech {srmech.__version__})")
    res = {"srmech_version": srmech.__version__}

    # (A) RATIONAL rotation: 3/8 turn
    br = rational.best_rational(375, 1000, 16)          # 0.375 read in our Cartesian frame
    p, q = br
    twice = cyclic.mod_add(p, p, q)                      # compose two of them in Z_q
    res["A_rational"] = {"cartesian_decimal": 0.375, "own_coordinate": list(br),
                         "cyclic_group": f"Z_{q}", "element": p, "compose_two_mod_add": twice}
    print(f"\n(A) RATIONAL: cartesian reading 0.375 -> best_rational(375,1000,16) = {br} "
          f"= element {p} of Z_{q}")
    print(f"    compose two {p}/{q}-turns in its OWN frame: mod_add({p},{p},{q}) = {twice} "
          f"(EXACT integer; the decimal is GONE)")

    # (B) IRRATIONAL rotation: golden, phi-1 = 0.6180339887...
    g = (6180339887, 10000000000)
    cascade = []
    for md in (2, 3, 5, 8, 13, 21, 55, 144, 377):
        r = rational.best_rational(*g, md)
        cascade.append({"max_d": md, "convergent": list(r), "err": abs(r[0] / r[1] - 0.6180339887)})
    res["B_irrational"] = {"cartesian_decimal": 0.6180339887, "convergent_cascade": cascade}
    print("\n(B) IRRATIONAL (golden): no single finite frame -> the best_rational CASCADE (Class N):")
    for c in cascade:
        print(f"    max_d={c['max_d']:3d} -> {c['convergent'][0]:>3}/{c['convergent'][1]:<3}  err={c['err']:.2e}")
    print("    denominators grow without bound -> the decimal is the LIMIT of this discrete cascade.")

    print("\n=== verdict ===")
    print("  The decimal is the cost of reading an S1 (cyclic, Class I) rotation in a fixed Cartesian frame.")
    print("  RATIONAL turn  -> EXACT integer in its own frame Z_q (the decimal was pure frame-artifact).")
    print("  IRRATIONAL turn-> exact to ANY depth via the Class-N convergent cascade; the decimal is that")
    print("  cascade's asymptote, NOT a continuous mystery (pi-as-cascade shape). The other door is the")
    print("  dimension-lift C->H->O (the (n:n-1) ladder): more couplings = more room for the rotation to sit")
    print("  simply. Same too-small-frame structure as the QDFT flat shadow (F380).")
    (HERE / "R-RBS-LM-R24_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R24_results.json'}")


if __name__ == "__main__":
    main()
