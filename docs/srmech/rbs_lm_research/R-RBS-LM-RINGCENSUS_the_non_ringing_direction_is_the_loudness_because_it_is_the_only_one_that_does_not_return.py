"""The ring census: what repeated multiplication DOES along each kind of direction.
The non-ringing direction is the one that does NOT return -- which is why it, and only
it, can carry "how much is left".

User 2026-07-28: "what does non-ringing provide, the resonant shape of now would still be
a ring snapshot, right, kinda stuck on this part."

srmech 0.9.0rc349. Exhaustive. Pure integer -- no float, no abs(), no numpy, no RNG.
"""
from srmech.amsc.octonion import oct_mult
from srmech.amsc.cascade import inertia_signature
from srmech.amsc.cascade.cayley_dickson import cd_mult

fail = []
def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'XX '} {label}: {got}")
    if not ok: fail.append((label, got, want))

def nm(z): return {0: "+1", 8: "-1"}.get(z, f"{'+' if z < 8 else '-'}e{z & 7}")
def orbit(k, n=5):
    z, out = k, []
    for _ in range(n):
        out.append(nm(z)); z = oct_mult(z, k)
    return out

print("=== 1. what repeated multiplication does along each kind of direction ===")
print(f"    the ONE non-ringing direction (real) : {' -> '.join(['+1']*5)}")
for k in (1, 2, 4, 7):
    print(f"    ringing direction e{k}                : {' -> '.join(orbit(k))}")
check("every ringing direction has period 4 (it RETURNS)",
      sorted({next(i + 1 for i in range(1, 9)
                   if (lambda z=k: [z := oct_mult(z, k) for _ in range(i)][-1])() == 0)
              for k in range(1, 8)}), [4])
check("the real direction never leaves itself (no cycle at all)",
      all(oct_mult(0, 0) == 0 for _ in range(1)), True)
print("    => ringing = PHASE: bounded, cyclic, comes back.")
print("       non-ringing = the direction a MAGNITUDE lives on: monotone, never returns.")

print("\n=== 2. the census, per rung ===")
def table(dim):
    return [[[int(getattr(v, 'num', v)) // int(getattr(v, 'den', 1))
              for v in cd_mult([1 if k == i else 0 for k in range(dim)],
                               [1 if k == j else 0 for k in range(dim)])]
             for j in range(dim)] for i in range(dim)]
print("    rung  non-ringing (loudness)  ringing (phases)")
rows = {}
for dim, s in ((1, "R"), (2, "C"), (4, "H"), (8, "O"), (16, "S")):
    r = inertia_signature(table(dim))
    rows[s] = (r["n_plus"], r["n_minus"])
    print(f"    {s:<5} {r['n_plus']:<21} {r['n_minus']}")
check("EVERY rung has exactly ONE non-ringing direction",
      sorted({v[0] for v in rows.values()}), [1])
check("the ringing count is what grows: 0, 1, 3, 7, 15",
      [rows[s][1] for s in ("R", "C", "H", "O", "S")], [0, 1, 3, 7, 15])
print("    => MANY PHASES, ONE LOUDNESS -- at every rung. A chord has many phases and")
print("       one volume; that is the whole content of the 1 + n split.")

print("\n=== 3. why a pure phase snapshot cannot tell you a ring-down HAS happened ===")
print("    a phase returns to its start every 4 steps (section 1), so at steps 0, 4, 8 ...")
print("    the phase reading is IDENTICAL. Nothing in it distinguishes 'just struck' from")
print("    'nearly silent'. Only the non-returning direction carries how-much-is-left.")
check("phase at step 0 and step 4 are the same for every ringing direction",
      all(orbit(k, 5)[0] == orbit(k, 5)[4] for k in range(1, 8)), True)

print("\n" + ("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)
