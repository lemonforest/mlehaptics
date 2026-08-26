"""Is there a pattern before vs after the flip -- a mirrored direction of the cascade,
"1->2->3->2->1", in exact operators or in type of behaviour?

User 2026-07-25: "is there a pattern to the before and after a flip, like is it a mirrored
direction of the cascade? like 1->2-3>2>1 either in exact operators or in type of behavior
being performed?"

srmech 0.9.0rc336. Exhaustive. Pure integer -- no float, no abs(), no numpy, no RNG.
"""
from itertools import product
from srmech.amsc.q8 import q8_mult
from srmech.amsc.octonion import oct_mult

fail = []
def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'XX '} {label}: {got}")
    if not ok: fail.append((label, got, want))

Q8, O16 = list(range(8)), list(range(16))
cq = lambda a: a if (a & 3) == 0 else a ^ 4
co = lambda a: a if (a & 7) == 0 else a ^ 8
def fold(w):
    z = w[0]
    for x in w[1:]: z = oct_mult(z, x)
    return z
def trace(w):
    z, out = w[0], [w[0]]
    for x in w[1:]: z = oct_mult(z, x); out.append(z)
    return out

# ============================================= 1. the mirror IS conjugation
print("=== 1. running the cascade BACKWARDS == conjugating it ===")
check("H: conj(a.b) == conj(b).conj(a)   [ANTI-automorphism: it REVERSES order]",
      all(cq(q8_mult(a, b)) == q8_mult(cq(b), cq(a)) for a in Q8 for b in Q8), True)
check("O: conj(a.b) == conj(b).conj(a)",
      all(co(oct_mult(a, b)) == oct_mult(co(b), co(a)) for a in O16 for b in O16), True)
check("H: conj is NOT an automorphism (order-preserving)",
      all(cq(q8_mult(a, b)) == q8_mult(cq(a), cq(b)) for a in Q8 for b in Q8), False)

# ================================ 2. the flip conjugates EVERY operator (exact)
print("\n=== 2. what the FLIP does to an OPERATOR -- the answer to 'exact operators' ===")
check("H: flip . L_q == L_conj(q)  for every imaginary q",
      all(q8_mult(4, q8_mult(q, x)) == q8_mult(cq(q), x) for q in (1, 2, 3) for x in Q8), True)
check("O: flip . L_q == L_conj(q)  for every imaginary q",
      all(oct_mult(8, oct_mult(q, x)) == oct_mult(co(q), x)
          for q in range(1, 8) for x in O16), True)
print("    => AFTER THE FLIP EVERY OPERATOR IS ITS OWN CONJUGATE.")
print("       1 -> 2 -> 3  becomes  3bar -> 2bar -> 1bar. Exact, in the operators.")

# ============================ 3. the plain palindrome is a pure LENGTH PARITY
print("\n=== 3. the plain palindrome 1..n..1 : content-FREE, pure (-1)^n ===")
for n in (2, 3, 4, 5):
    vals = {fold(w + tuple(reversed(w))) for w in product(range(1, 8), repeat=n)}
    check(f"  n={n}: every word gives the SAME value  (-1)^n = {'+1' if n % 2 == 0 else '-1'}",
          sorted(vals), [0] if n % 2 == 0 else [8])
print("    => a plain mirror carries NO content -- only the parity of its own length.")

# ================== 4. the conjugate-palindrome returns EXACTLY to the anchor
print("\n=== 4. the conjugate-palindrome 1..n..1bar : returns EXACTLY to +1 ===")
for n in (2, 3, 4, 5):
    vals = {fold(w + tuple(co(x) for x in reversed(w))) for w in product(range(1, 8), repeat=n)}
    check(f"  n={n}: every word comes home to +1 (the REAL anchor)", sorted(vals), [0])
print("    => x . conj(x) = the norm = the anchor. The mirrored cascade CLOSES.")

# ============ 5. and the TRACE is literally 1->2->3->2->1 (the user's shape)
print("\n=== 5. the partial-holonomy TRACE is a literal palindrome ===")
for w0 in ((1, 2, 4), (1, 2, 3), (3, 5, 6), (7, 1, 6, 2)):
    p = w0 + tuple(co(x) for x in reversed(w0)); t = trace(p); L = len(t)
    pal = all(t[i] == t[L - 2 - i] for i in range((L - 1) // 2))
    print(f"    {w0} -> trace {t}   palindromic: {pal}   ends at anchor: {t[-1] == 0}")
allpal = allhome = 0; tot = 0
for n in (2, 3, 4):
    for w0 in product(range(1, 8), repeat=n):
        p = w0 + tuple(co(x) for x in reversed(w0)); t = trace(p); L = len(t)
        tot += 1
        allpal += all(t[i] == t[L - 2 - i] for i in range((L - 1) // 2))
        allhome += (t[-1] == 0)
check(f"EVERY conj-palindrome trace is a palindrome ({allpal}/{tot})", allpal, tot)
check(f"EVERY conj-palindrome trace ends at the anchor ({allhome}/{tot})", allhome, tot)
print("    => the shape IS '1 -> 2 -> 3 -> 2 -> 1 -> home'. The trace climbs out and")
print("       retraces its own steps exactly, then closes on the real anchor.")

# ================================= 6. so it is a DETECTOR: deviation = defect
print("\n=== 6. the mirror is therefore an ERROR CHECK, not a carrier ===")
per_pos = {}
for w0 in product(range(1, 8), repeat=3):
    for corrupt in (0, 1, 2):                      # perturb ONE post-flip symbol
        p = list(w0 + tuple(co(x) for x in reversed(w0)))
        p[3 + corrupt] = (p[3 + corrupt] % 7) + 1  # a wrong (still legal) symbol
        t = trace(tuple(p)); L = len(t)
        d = per_pos.setdefault(corrupt, [0, 0, 0]); d[2] += 1
        d[0] += (not all(t[i] == t[L - 2 - i] for i in range((L - 1) // 2)))
        d[1] += (t[-1] != 0)
print("    corrupted post-flip position | trace-palindrome catches | come-home catches")
for k in sorted(per_pos):
    a, b, n = per_pos[k]
    print(f"      position {k}                    {a:>4}/{n}                {b:>4}/{n}")
tot_n = sum(v[2] for v in per_pos.values())
check("COME-HOME is a PERFECT single-symbol detector",
      sum(v[1] for v in per_pos.values()), tot_n)
check("trace-palindrome MISSES the final symbol (it sits outside the mirrored region)",
      per_pos[2][0], 0)
check("...but catches every corruption INSIDE the mirrored region",
      per_pos[0][0] + per_pos[1][0], per_pos[0][2] + per_pos[1][2])
print("    => DIVISION OF LABOUR: come-home DETECTS (100%), the trace palindrome LOCALIZES")
print("       (tells you WHERE, but is blind to the last symbol, which lies past the mirror).")
print("    => because a correct mirror carries NO content, ANY deviation is a detected")
print("       defect. The mirror is a k=2 parity CHECK (detect, not correct) -- exactly")
print("       the role F291 gives k=2. Correction needs the k=3 rung.")

print("\n" + ("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)
