"""F860 probe: the_one(sigma,theta) as the Antikythera crank over the de-lensed board.
One crank (theta), bidirectional (sigma), drives every clump-pointer at its own
gear-ratio (= mass). Reads: arrangement-evolution, syzygy alignment angles,
massless clumping center (gauge dimple), dark-star phase horizon (fast hub).
srmech-native: the_one (epicycle), rational.atan2/hypot (Class N). 14-D sparse.
"""
from srmech.amsc import cascade, rational

# de-lensed board cells (F859) + the hub we de-lensed (F858), with masses (weights)
CELLS = [
    ("hub",       34534),   # the de-lensed gravitational hub (the/and/war/list)
    ("scaffold",  10604),   # cell 0  time/state
    ("antiquity",  7078),   # cell 1
    ("computing",  2968),   # cell 2
    ("windows",     455),   # cell 3 satellite
    ("liverpool",   291),   # cell 4 satellite
]
M_REF = 10604               # heaviest DE-LENSED cell = gear-ratio 1 (hub is faster)
GEAR = {n: rational.best_rational(m, M_REF, 24) for n, m in CELLS}
print("gear ratios (best_rational, Class N — Antikythera teeth):")
for n, m in CELLS:
    p, q = GEAR[n]
    print(f"  {n:10s} mass={m:6d}  rate={p}/{q} = {p/q:.3f}")

HORIZON_ARG = 7.0           # 24-term epicycle series converges for |arg| < ~7 rad
def pointer(sigma, name, k):
    """cell's dial pointer at crank step k (Theta=k/4 rad), via the_one epicycle."""
    p, q = GEAR[name]
    num, den = sigma_scale(sigma, p * k), q * 4
    arg = (p * k) / (q * 4)
    o = cascade.the_one(1, num, den) if sigma > 0 else cascade.the_one(1, -num if num else 0, den)
    fr = o.to_flat_rational()
    c, s = fr[3][0] / fr[3][1], fr[4][0] / fr[4][1]   # v3=cos(theta_i), v4=sin(theta_i)
    return arg, c, s

def sigma_scale(sigma, n):
    return n  # sigma handled by negating num below

def unit(c, s):
    r = rational.hypot(c, s)
    return (c / r, s / r) if r > 1e-9 else (c, s), r

def arrangement(sigma, k):
    """return list of (name, angle, ux, uy) for resolvable cells, + dark-star list."""
    res, dark = [], []
    for name, _ in CELLS:
        p, q = GEAR[name]
        arg = (p * k) / (q * 4)
        if arg > HORIZON_ARG:                 # past the epicycle resolution horizon
            dark.append((name, arg)); continue
        num = (-(p * k) if sigma < 0 else (p * k))
        o = cascade.the_one(1, num, q * 4)
        fr = o.to_flat_rational()
        c, s = fr[3][0] / fr[3][1], fr[4][0] / fr[4][1]
        r = rational.hypot(c, s)
        if r > 1.5:                            # series diverged = also unresolvable
            dark.append((name, arg)); continue
        ux, uy = (c / r, s / r)
        ang = rational.atan2(s, c)
        res.append((name, ang, ux, uy))
    return res, dark

def resultant(res):
    """centroid of unit pointers = mean resultant vector R; |R| in [0,1]."""
    if not res: return 0.0, 0.0, 0.0
    mx = sum(u for _, _, u, _ in res) / len(res)
    my = sum(v for _, _, _, v in res) / len(res)
    return mx, my, rational.hypot(mx, my)

print("\n=== FORWARD crank (sigma=+1): arrangement-evolution ===")
print("Theta  | resolvable pointer angles (rad)            | |R|(centroid) | dark-star")
rows = []
for k in range(0, 25, 2):
    res, dark = arrangement(+1, k)
    mx, my, R = resultant(res)
    rows.append((k / 4, R, [a for _, a, _, _ in res], [d for d, _ in dark]))
    angs = " ".join(f"{a:+.2f}" for _, a, _, _ in res)
    print(f" {k/4:4.2f} | {angs:42s} | {R:.3f}        | {','.join(d for d,_ in dark)}")

Rs = [r for _, r, _, _ in rows]
syz = max(rows, key=lambda x: x[1]); mass = min(rows, key=lambda x: x[1])
print(f"\nsyzygy (max |R|, alignment):   Theta={syz[0]:.2f}  |R|={syz[1]:.3f}")
print(f"massless center (min |R|):     Theta={mass[0]:.2f}  |R|={mass[1]:.3f}  <- centroid ~ empty dial hub")

# arrangement reconfigures (not rigid) ? relative angle scaffold->computing across Theta
rel = []
for k in range(0, 25, 2):
    res, _ = arrangement(+1, k)
    d = {n: a for n, a, _, _ in res}
    if "scaffold" in d and "computing" in d:
        rel.append(d["computing"] - d["scaffold"])
spread = max(rel) - min(rel)
print(f"relative-angle(computing - scaffold) range over crank: {spread:.3f} rad  ({'RECONFIGURES' if spread>0.1 else 'rigid'})")

# massless center emerges with MORE spread clumps ? |R| for 2 vs all-5 de-lensed
res5, _ = arrangement(+1, 24)
res5 = [r for r in res5 if r[0] != "hub"]
def Rof(names):
    sub = [r for r in res5 if r[0] in names]
    return resultant(sub)[2]
print(f"\nmassless-center emergence (Theta=6.0):")
print(f"  2 clumps {{scaffold,antiquity}}: |R|={Rof({'scaffold','antiquity'}):.3f}")
print(f"  5 clumps (all de-lensed):       |R|={Rof({n for n,_ in CELLS if n!='hub'}):.3f}  <- more clumps -> centroid collapses toward origin")

print("\n=== BACKWARD crank (sigma=-1): time reversal retraces ===")
for k in [4, 8, 12]:
    rf, _ = arrangement(+1, k); rb, _ = arrangement(-1, k)
    df = {n: a for n, a, _, _ in rf}; db = {n: a for n, a, _, _ in rb}
    s = "scaffold"
    if s in df and s in db:
        print(f"  Theta={k/4:.2f}: scaffold angle fwd={df[s]:+.3f}  bwd={db[s]:+.3f}  (sum={df[s]+db[s]:+.3f} ~0 = mirror)")

print("\n=== DARK-STAR horizon: which cells out-race the epicycle resolution ===")
for k in [8, 16, 24]:
    _, dark = arrangement(+1, k)
    print(f"  Theta={k/4:.2f}: unresolvable (arg>{HORIZON_ARG}) = {[(d,round(a,1)) for d,a in dark]}")
print("  (the hub's gear-ratio races its pointer past the generator's phase-resolution")
print("   horizon -> 'forever in pursuit', an information event-horizon = dark-star boundary.)")
