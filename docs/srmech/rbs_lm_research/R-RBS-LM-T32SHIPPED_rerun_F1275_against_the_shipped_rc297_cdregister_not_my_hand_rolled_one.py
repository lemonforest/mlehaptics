"""Re-run F1275's T(32) result against the SHIPPED rc297 CDRegister, not my hand-rolled one.
F1275 flagged this exactly: 'the 32-slot register is MINE... a register I wrote could be easier
than srmech's, and "addressing works at 32" would be an artifact of my own construction.'
srmech now ships one, so the caveat is testable instead of standing."""
import time
from srmech.amsc import cascade
NAMES = ["alpha","beta","gamma","delta","epsilon","zeta","eta","theta","iota","kappa","lambda","mu",
         "nu","xi","omicron","pi","rho","sigma","tau","upsilon","phi","chi","psi","omega",
         "aleph","bet","gimel","dalet","he","vav","zayin","het"]
DIRS32 = [1,3,5,7,11,13,17,19,23,29,31]

print("srmech", __import__("srmech").__version__)
print("\n=== the structural premise, via the SHIPPED predicate ===")
for d in cascade.CD_DIMS:
    if d < 2: continue
    print("  dim %-3d cd_navmap_is_signed_permutation -> %s" % (d, cascade.cd_navmap_is_signed_permutation(d)))

print("\n=== F1275's end-to-end T(32) round-trip, on the SHIPPED register ===")
print("  %-8s %-18s %-18s" % ("D", "dim 16 (8 keys)", "dim 32 (32 keys)"))
for D in (4096, 16384):
    out = []
    for dim, keys, dirs in ((16, NAMES[:8], [d for d in DIRS32 if d < 16]), (32, NAMES[:32], DIRS32)):
        hits = tot = 0
        for j in dirs:
            r = cascade.cd_register(dim, D=D)
            for i, k in enumerate(keys):
                r.write(i, k)
            nav = r.navmap(j)
            mv = r.navigate(j)
            for i, k in enumerate(keys):
                dest, sign = nav[i]
                gk, gs = mv.read(dest)
                tot += 1
                hits += (gk == k and gs == sign)
        out.append("%d/%d (%.1f%%)" % (hits, tot, 100.0*hits/tot))
    print("  %-8d %-18s %-18s" % (D, out[0], out[1]))

print("\n=== the involution (F1274's mechanism) on the shipped register ===")
for dim in (16, 32, 64):
    r = cascade.cd_register(dim, D=4096)
    for i, k in enumerate(NAMES[:4]): r.write(i, k)
    before = r.slots(); after = r.navigate(3).navigate(3).slots()
    same = all(before[i][0] == after[i][0] for i in before)
    flip = all(after[i][1] == -before[i][1] for i in before)
    print("  dim %-3d same slots %-5s sign flipped %-5s  (e3.e3 = %s)"
          % (dim, same, flip, cascade.cd_basis_product(dim, 3, 3)))

print("\n=== does the shipped gate reject the known zero divisors? ===")
w = cascade.sedenion_zero_divisor_witness()
r = cascade.cd_register(16, D=4096)
print("  x=%s -> navigable %s ; y=%s -> navigable %s"
      % (w["x_form"], r.is_navigable(w["x"]), w["y_form"], r.is_navigable(w["y"])))
