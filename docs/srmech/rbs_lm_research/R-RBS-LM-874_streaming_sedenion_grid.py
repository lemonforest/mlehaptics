"""F874: the streaming sedenion-grid generator -- the convergence build.
The chunked-M pages (F872, each a bounded <=24-bind instrument) live in a SedenionRegister's
slots (the grid, the WHERE; F465/F873). The 1D_t fiber = the_one's sigma/theta crank picks a
navigate-direction each tick; navigate(j) walks the hyper-loop (the address<->Cayley-Dickson
homomorphism) = the streaming cursor (the WHEN). Random-access (read/navigate) x streaming
(the_one crank) = a streaming addressable store. Single-basis navigate is reversible (sigma-
mirror, bidirectional stream); is_navigable is the <=O reversibility gate (F453 horizon).
srmech-native, sparse: cascade.sedenion_register + cascade.the_one.
"""
from srmech.amsc import cascade

D = 8192
reg = cascade.sedenion_register(D=D)
# pages = chunked-M instruments (F872); here keyed by name in the octonion working block e0..e7
PAGES = {0: "scaffold", 1: "antiquity", 2: "computing", 3: "windows",
         4: "liverpool", 5: "myth", 6: "science", 7: "sport"}
for slot, key in PAGES.items():
    reg.write(slot, f"page.{key}")
print("=== the grid: 8 chunked-M pages in the octonion working block e0..e7 ===")
print("  slots:", {s: k for s, (k, _) in reg.slots().items()})

def keys(r): return {s: k for s, (k, _) in r.slots().items()}            # populated slots only
def onehot(idxs, neg=()):
    v = [0] * 16
    for i in idxs: v[i] = 1
    for i in neg: v[i] = -1
    return v

print("\n=== navigate(j) = the streaming-cursor step (addresses, permutes, reversible) ===")
j = 1
nav = reg.navigate(j)
print(f"  navigate(e{j}): content moves e_i -> e_i*e_j = +/-e_k (the hyper-loop walk)")
print("  after :", keys(nav))
# reversibility: single-basis navigate is exactly reversible (e_j^2 = -1 -> keys back, signs flip)
back = nav.navigate(j)
print(f"  navigate(e{j}).navigate(e{j}) keys restored (e_j^2=-1, signs flip): {keys(reg) == keys(back)}")
print(f"  is_navigable(single basis e{j})            : {reg.is_navigable(onehot([j]))}  (reversible step)")
print(f"  is_navigable(e1+e10 = a sedenion zero-div) : {reg.is_navigable(onehot([1, 10]))}  (NON-navigable = the <=O horizon, F453)")
print(f"  is_navigable(e1+e2 generic composite)      : {reg.is_navigable(onehot([1, 2]))}  (navigable)")

def head(r, slot=0):
    k, _ = r.read(slot); return k

print("\n=== the 1D_t STREAM: the_one crank picks the navigate-direction each tick ===")
def the_one_dir(t, sigma):
    o = cascade.the_one(1 if sigma > 0 else -1, t, 12)   # crank tick t (theta = t/12)
    fr = o.to_flat_rational()
    s = fr[4][0] / fr[4][1]                                # epicycle sin(theta) -> direction selector
    return 1 + (int(s * 1000) % 7)                        # j in e1..e7 (Python % handles sign; no abs, Class-K-clean)

print("  forward stream (sigma=+1): page at the read-head e0 after each cranked navigate:")
cur, fwd = reg, []
for t in range(1, 8):
    cur = cur.navigate(the_one_dir(t, +1)); fwd.append(head(cur))
print("   ", fwd)
print("  the navigate-sequence IS the 1D_t fiber walk; the read-head trajectory = the streamed page sequence.")

print("\n=== bidirectional: each step is reversible -> the stream decodes (sigma-mirror) ===")
dirs = [the_one_dir(t, +1) for t in range(1, 4)]
cur = reg
for jd in dirs: cur = cur.navigate(jd)                # walk
for jd in reversed(dirs):                              # decode: navigate^3 = inverse (e_j^4=1)
    cur = cur.navigate(jd).navigate(jd).navigate(jd)
print(f"  walk {dirs} then decode (navigate^3=inverse, e_j^4=1): keys restored = {keys(reg) == keys(cur)}")
print("  -> the stream is reversible (decode = replay inverse directions); the box carries the sign (F453).")

print("\n=== the convergence ===")
print("  WHERE = the sedenion grid (8 pages in e0..e7; read/navigate, O(1)/O(log), F873) --")
print("          each page is a chunked-M instrument that holds reproduction flat (F872).")
print("  WHEN  = the_one's sigma/theta crank (the 1D_t fiber) drives the navigate-sequence ->")
print("          a streamed page trajectory = generation; single-basis navigate is reversible")
print("          (bidirectional, <=O contents), the sedenion box carries the story-position (F453).")
print("  => a streaming addressable store: random-access memory + tape head, sparse + srmech-native.")
print("  Honest: this is the addressing+streaming SKELETON on the shipped register; emitting tokens")
print("  by resonating WITHIN the addressed page (F872 recall) is the next integration; the_one->j")
print("  is a first mapping; >16 pages need the nested base-16 recursion (F873).")
