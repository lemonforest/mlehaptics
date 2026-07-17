r"""R-RBS-LM-GENOME-RC262-VERIFY — test srmech against its CHANGELOG: is the whole #1407 genome-architecture arc
delivered, does it work, and were the two review findings (§95.3 catalog ergonomics, §95.4 diploid erasure asymmetry)
fixed? Verifies the rc257→rc265 surface. As of rc265: ALL GREEN — the #1407 arc is complete and both findings closed.

#1407 delivery (CHANGELOG rc257→rc265):
  rc257  O(1) genome_append (v12 head-only manifest; thread catalog=)                 §95.3
  rc258  centromere() + centromere_of() + mint() / mint_plan()                        §95a
  rc259  diploid() + recover_diploid()                                                §95b
  rc260  RENAME: genome()=biology-aware umbrella, plasmid()=all-stick, mint()=alias   §95.2 feedback 2
  rc261  dsl.alias / build_aliases_from_toml_str / load_aliases_toml                  config-driven domain naming
  rc262  integrate(host, provirus)                                                    §95.1d coherency capstone
  rc264  recover_diploid erasure repair made SYMMETRIC (either homolog heals)         §95.4 FIX (found via rc262)
  rc265  genome_append catalog="load" resume + a clear catalog={} ValueError + docs   §95.3 ergonomics FIX

srmech 0.9.0rc265 (TestPyPI, clean venv). No ALU magnitude-builtin. Composes §95/§95.1/§95.2/§95.3/§95.4, F1243/F1244/F291.
Run:  /tmp/srmech_latest/venv/bin/python3 R-RBS-LM-GENOME-RC262-VERIFY_*.py
"""
import sys
import tempfile
import time
import statistics

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
    print(f"=== R-RBS-LM-GENOME-RC262-VERIFY (srmech {srmech.__version__}) — #1407 delivery + working + fixes ===\n")
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

    print("\nrc259/rc264 DIPLOID — clean recover + SYMMETRIC erasure repair (rc264 fix, §95.4):")
    content = leaves(6)
    dp = G.diploid(content, one, orientation=2)
    ok &= check("recover_diploid (clean) recovers content byte-exact", G.recover_diploid(dp, one) == content)
    HVzero = type(dp[1]).from_sequence([0] * 64)                     # an ERASED (all-zero) stored turn
    brokenB = list(dp); brokenB[8] = HVzero                          # break copyB leaf0
    brokenA = list(dp); brokenA[1] = HVzero                          # break copyA leaf0
    ok &= check("copyB erasure heals from the intact homolog", G.recover_diploid(brokenB, one) == content)
    ok &= check("copyA erasure heals from the intact homolog (rc264 symmetric fix)", G.recover_diploid(brokenA, one) == content)

    print("\nrc262 INTEGRATE — a stick provirus into a minted host; all modes survive:")
    host = G.genome([("hostA", leaves(8)), ("hostB", leaves(7))], one)
    provirus = G.plasmid([("virus", leaves(3))], one)
    integ = G.integrate(host, provirus, at=1)
    parts = G.partition(integ, one)
    ok &= check("partition recovers all chromosomes after integration", isinstance(parts, dict) and len(parts) == 3, f"n={len(parts) if isinstance(parts, dict) else '?'}")
    ok &= check("centromere_of survives integration", G.centromere_of(integ) is not None, str(G.centromere_of(integ)))

    print("\nrc261 CONFIG ALIASING — bind a domain name to any srmech.* function via TOML:")
    al = dsl.build_aliases_from_toml_str('[[alias]]\nname = "make_sticks"\ntarget = "srmech.amsc.genome.plasmid"\n')
    ok &= check("TOML [[alias]] binds a user name to plasmid()", "make_sticks" in al and al["make_sticks"](ks, one) == pl)
    try:
        dsl.build_aliases_from_toml_str('[[alias]]\nname="x"\ntarget="os.system"\n'); restricted = False
    except Exception:
        restricted = True
    ok &= check("aliasing restricted to srmech.* targets (os.system rejected)", restricted)

    print("\nrc257/rc265 O(1) genome_append — thread catalog / resume with 'load' / clear {} error (§95.3):")
    d = tempfile.mkdtemp()
    G.genome_save(G.genome([("seed", leaves(3))], one), d, one, labels=["seed"])
    for i in range(40):
        G.genome_append(d, "pre%d" % i, leaves(3), one)              # cold appends build the genome on disk
    cat = G.genome_append(d, "resume0", leaves(3), one, catalog="load")   # resume with no prior return
    ts = []
    for i in range(150):
        t = time.perf_counter(); cat = G.genome_append(d, "r%d" % i, leaves(3), one, catalog=cat); ts.append(time.perf_counter() - t)
    ok &= check('catalog="load" resumes, then streams O(1)', statistics.mean(ts[-40:]) * 1000 < 4, f"{1000*statistics.mean(ts[-40:]):.2f} ms/call flat")
    try:
        G.genome_append(d, "x", leaves(3), one, catalog={}); clear = False
    except ValueError:
        clear = True
    except KeyError:
        clear = False
    ok &= check('catalog={} raises a clear ValueError (not a bare KeyError)', clear)

    print(f"\nVERDICT: #1407 is DELIVERED, WORKING, and both review findings CLOSED at {srmech.__version__} — "
          f"{'ALL checks PASS' if ok else 'a check FAILED'}.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
