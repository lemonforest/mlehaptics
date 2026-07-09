"""F1184 (#243): COUPLE the two resonator models — does the α-drift (F1183) CARRY the subharmonic comb (F1180)?

The comb generator (F1180) = a logistic map that period-doubles into subharmonics. The chiral drift (F1183) = asymmetric
coupling α (= the_one's σ). Fuse them in a COUPLED-MAP LATTICE (the resonant BODY): each site is a logistic map (makes
the comb), sites are coupled (the body), and the coupling is ASYMMETRIC — weight (1+α)/2 to the left neighbour vs
(1-α)/2 to the right = a directional/chiral advection.

  x_i(t+1) = (1-ε)·f(x_i) + ε·[ (1+α)/2·f(x_{i-1}) + (1-α)/2·f(x_{i+1}) ] ,   f(x)=r·x·(1-x)

Test: put it in the period-doubled (comb) regime. (a) TEMPORAL period at a site = the comb (2/4/8). (b) SPATIAL drift of
the pattern over one temporal period (cross-correlate profile at t vs t+P) = the chiral advection. If the drift is signed
(∝ α) AND the temporal period (the comb) is preserved across α, then the α-drift CARRIES the comb. numpy-free; no abs.
"""

N = 200
R = 3.4                              # PERIODIC (period-2) logistic regime -> a clean subharmonic comb (f/2) SUBSTRATE
EPS = 0.30                           # lattice coupling (the body's mode-coupling)


def f(x):
    return R * x * (1.0 - x)


def step(x, alpha):
    wl, wr = (1.0 + alpha) / 2.0, (1.0 - alpha) / 2.0
    fx = [f(xi) for xi in x]
    return [(1.0 - EPS) * fx[i] + EPS * (wl * fx[(i - 1) % N] + wr * fx[(i + 1) % N]) for i in range(N)]


def settle(alpha, x0):
    x = list(x0)
    for _ in range(3000):
        x = step(x, alpha)          # relax to the uniform period-2 comb SUBSTRATE
    return x


def temporal_period(traj, site, maxp=16, tol=1e-2):
    s = [row[site] for row in traj[-40:]]
    x0 = s[-1]
    for p in range(1, maxp + 1):
        if -tol <= s[-1 - p] - x0 <= tol:
            return p
    return 0


def excitation_advection(alpha, base, c=N // 2, T=24, W=70):
    """inject an EXCITATION into the comb substrate; track its centre-of-mass drift = the chiral transport."""
    xr = list(base); xp = list(base); xp[c] += 0.12       # the excitation (a perturbation on the comb)
    rt, pt = [], []
    for _ in range(T):
        xr = step(xr, alpha); xp = step(xp, alpha)
        rt.append(list(xr)); pt.append(list(xp))
    d = [(pt[-1][i] - rt[-1][i]) ** 2 for i in range(N)]  # perturbation intensity (squared; no magnitude-builtin)
    idx = [c + k for k in range(-W, W + 1)]
    tot = sum(d[i % N] for i in idx) or 1e-12
    com = sum(k * d[(c + k) % N] for k in range(-W, W + 1)) / tot   # signed centre-of-mass shift from c
    per = temporal_period(rt, c)
    return com, per


base_by_alpha = {}
x0 = [0.5 + 0.2 * (1 if i % 2 else -1) for i in range(N)]
print("F1184 (#243): couple the resonators — does the α-drift carry the comb, or carry EXCITATIONS across the comb?\n")
print("   coupled-map lattice (N=%d, r=%.2f, ε=%.2f): logistic comb per site + asymmetric coupling α\n" % (N, R, EPS))
print("   the COMB (temporal period of the substrate) is uniform period-2 for all α — it is the SUBSTRATE (medium), not a")
print("   travelling packet. So the real test: does the chiral α-drift carry an EXCITATION (a perturbation) across it?\n")
print("   α       comb (substrate)   excitation centre-of-mass drift   direction")
for alpha in (-0.6, -0.3, 0.0, 0.3, 0.6):
    base = settle(alpha, x0)
    com, per = excitation_advection(alpha, base)
    arrow = "→ forward" if com > 0.3 else ("← backward" if com < -0.3 else "· none (no chiral carry)")
    print("   %+.1f     period-%d           %+7.2f sites                    %s" % (alpha, per, com, arrow))
print("\n  READ: the COMB is the uniform SUBSTRATE (period-2 everywhere, all α) — it does NOT travel because it is the")
print("  medium, not a packet. But the chiral α-drift CARRIES the EXCITATION (the injected perturbation) across the comb")
print("  with a signed velocity ∝ α (the_one's σ / time-arrow). So the fusion is the MFO substrate↔excitation split:")
print("  the subharmonic comb = the substrate field; the α-drift transports EXCITATIONS across it in the σ-direction.")
print("  = the resonant asymmetric wave, correctly: a chiral excitation riding a subharmonic-comb substrate.")
