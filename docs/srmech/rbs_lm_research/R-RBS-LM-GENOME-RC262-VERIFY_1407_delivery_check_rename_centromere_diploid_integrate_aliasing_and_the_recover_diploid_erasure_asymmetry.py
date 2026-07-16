r"""R-RBS-LM-GENOME-RC262-VERIFY — test srmech 0.9.0rc262 against its CHANGELOG: is the whole #1407 genome-architecture
arc delivered, and does it work? Verifies the rc258→rc262 surface (the biology-native genome architecture) and
surfaces ONE real bug found by using it.

#1407 delivery (CHANGELOG rc257→rc262):
  rc257  O(1) genome_append (v12 head-only manifest; thread catalog=)           [verified in §95.3]
  rc258  centromere() + centromere_of() + mint() / mint_plan()  (§95a)
  rc259  diploid() + recover_diploid()  (§95b — the erasure/break specialist)
  rc260  RENAME: genome()=biology-aware umbrella, plasmid()=all-stick, mint()=alias  (§95.2 feedback 2)
  rc261  dsl.alias / build_aliases_from_toml_str / load_aliases_toml  (config-driven domain-agnostic naming)
  rc262  integrate(host, provirus)  (§95.1d — a stick provirus into a minted/diploid host, all modes survive)

VERDICT (run on rc262, clean venv): all six delivered + working, EXCEPT recover_diploid erasure repair is ASYMMETRIC —
it heals a copyB erasure (fills from copyA) but a copyA erasure returns the un-coupled-zero garbage, not the intact
homolog. The CHANGELOG rc259 says "exactly one ERASED → fill from the intact homolog" (symmetric); measured, only
copyB heals. Filed to #1407.

srmech 0.9.0rc262 (TestPyPI, clean venv). No ALU magnitude-builtin. Composes §95/§95.1/§95.2/§95.3, F1243/F1244/F291.
Run:  /tmp/srmech_latest/venv/bin/python3 R-RBS-LM-GENOME-RC262-VERIFY_*.py
"""
import sys

import srmech
from srmech.amsc import genome as G, hdc
import srmech.dsl as dsl

one = hdc.klein4_random(64, seed=0)


def leaves(n):
    return [[(i * 7 + j) % 4 for j in range(64)] for i in range(n)]


def check(label, cond, extra=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  — {extra}" if extra else ""))
    return bool(cond)


def main():
    print(f"=== R-RBS-LM-GENOME-RC262-VERIFY (srmech {srmech.__version__}) — #1407 delivery + working check ===\n")
    ok = True
    ks = [("small", leaves(3)), ("big", leaves(8))]                  # small ≤4 = stick; big ≥5 = minted

    print("rc260 RENAME — genome()=umbrella, plasmid()=all-stick, mint()=alias:")
    gu, pl, mi = G.genome(ks, one), G.plasmid(ks, one), G.mint(ks, one)
    ok &= check("genome() == mint() (byte-identical alias)", gu == mi)
    ok &= check("genome() (umbrella) mints a centromere on the ≥5-leaf kernel", G.centromere_of(gu) is not None, str(G.centromere_of(gu)))
    ok &= check("plasmid() (all-stick) has NO centromere", G.centromere_of(pl) is None)

    print("\nrc258 CENTROMERE — round-trip orientation + arm-ratio-from-position:")
    ch = G.chromosome(leaves(12), one, label="chr", centromere=2)
    cen = G.centromere_of(ch)
    ok &= check("centromere_of round-trips (orient + arm_ratio)", cen and cen["orientation"] == 2 and cen["arm_ratio"] == (6, 6), str(cen))

    print("\nrc259 DIPLOID — clean recover + the erasure asymmetry (the bug):")
    content = leaves(6)
    dp = G.diploid(content, one, orientation=2)
    ok &= check("recover_diploid (clean) recovers content byte-exact", G.recover_diploid(dp, one) == content)
    HVzero = type(dp[1]).from_sequence([0] * 64)                     # an ERASED (all-zero) leaf of the strand's HV type
    # strand: [telomere, copyA(1..6), centromere(7), copyB(8..13)]
    brokenB = list(dp); brokenB[8] = HVzero                          # erase copyB leaf0
    brokenA = list(dp); brokenA[1] = HVzero                          # erase copyA leaf0
    healB = (G.recover_diploid(brokenB, one) == content)
    healA = (G.recover_diploid(brokenA, one) == content)
    check("copyB erasure heals from the intact homolog", healB)
    check("copyA erasure heals from the intact homolog", healA, "BUG: returns the un-coupled zero, not the homolog — asymmetric")
    ok &= healB
    # NOTE: healA is EXPECTED to fail on rc262 (the bug). We do NOT gate the verdict on it; we report it.
    print("      -> recover_diploid ERASURE REPAIR IS ASYMMETRIC (copyB heals, copyA does not). Filed to #1407.")

    print("\nrc262 INTEGRATE — a stick provirus into a minted host; all modes survive:")
    host = G.genome([("hostA", leaves(8)), ("hostB", leaves(7))], one)
    provirus = G.plasmid([("virus", leaves(3))], one)
    integ = G.integrate(host, provirus, at=1)
    parts = G.partition(integ, one)
    ok &= check("partition recovers all chromosomes after integration", isinstance(parts, dict) and len(parts) == 3, f"n={len(parts) if isinstance(parts, dict) else '?'}")
    ok &= check("centromere_of survives integration (host's minted chromosome still reads)", G.centromere_of(integ) is not None, str(G.centromere_of(integ)))

    print("\nrc261 CONFIG ALIASING — bind a domain name to any srmech.* function via TOML:")
    spec = '[[alias]]\nname = "make_sticks"\ntarget = "srmech.amsc.genome.plasmid"\n'
    al = dsl.build_aliases_from_toml_str(spec)
    ok &= check("TOML [[alias]] binds a user name to plasmid()", "make_sticks" in al and al["make_sticks"](ks, one) == pl)
    try:
        dsl.build_aliases_from_toml_str('[[alias]]\nname="x"\ntarget="os.system"\n'); restricted = False
    except Exception:
        restricted = True
    ok &= check("aliasing restricted to srmech.* targets (os.system rejected)", restricted)

    print(f"\nVERDICT: #1407 is DELIVERED and working at rc262 — {'ALL core checks PASS' if ok else 'a core check FAILED'}; "
          f"the one open bug is the recover_diploid copyA-erasure asymmetry (reported, not gated).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
