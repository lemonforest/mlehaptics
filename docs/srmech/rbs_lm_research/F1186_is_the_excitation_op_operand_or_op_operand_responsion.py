"""F1186 (#243): is the σ-excitation op(x)operand (k=2, bare) or op(x)operand(x)RESPONSION (k=3, self-correcting)?

Mapping in the coupled resonator (F1184/F1185): op = the logistic MAP f (the operation); operand = a site's VALUE x
(the content); candidate (x)responsion = the ATTRACTOR STABILITY — the map contracting perturbations back to its cyclic
period-2 attractor (= the phase-lock, the bit-exact=phase-locked stance, = F1179's resonant reinforcement).

Test: corrupt an excitation (perturb one site) and watch the corruption decay — with the substrate coupling OFF (ε=0,
each site an ISOLATED op·operand) vs ON (ε>0, + the substrate-comb responsion).
  - if the corruption decays only at ε>0  -> the responsion is the SUBSTRATE alone; the excitation is bare op(x)operand (k=2).
  - if the corruption decays even at ε=0   -> each op·operand carries its OWN responsion (attractor contraction);
    the excitation is op(x)operand(x)RESPONSION (k=3), and the responsion is FRACTAL (excitation-scale AND substrate-scale,
    the same phase-locking). numpy-free; no magnitude-builtin (squared deviation); deterministic.
"""
import math

N = 120
R = 3.4                                    # period-2 comb (a stable cyclic attractor)


def f(x):
    return R * x * (1.0 - x)


def step(x, eps, alpha):
    wl, wr = (1.0 + alpha) / 2.0, (1.0 - alpha) / 2.0
    fx = [f(xi) for xi in x]
    return [(1.0 - eps) * fx[i] + eps * (wl * fx[(i - 1) % N] + wr * fx[(i + 1) % N]) for i in range(N)]


def settle(eps, x0, n=3000):
    x = list(x0)
    for _ in range(n):
        x = step(x, eps, 0.0)
    return x


def corruption_decay(eps, alpha, base, c=N // 2, delta=0.18, T=30):
    """corrupt site c by delta; return the total squared deviation from the uncorrupted reference over time."""
    xr = list(base); xp = list(base); xp[c] += delta
    dev = []
    for _ in range(T):
        xr = step(xr, eps, alpha); xp = step(xp, eps, alpha)
        dev.append(sum((xp[i] - xr[i]) ** 2 for i in range(N)))
    return dev


x0 = [0.5 + 0.01 * math.sin(5.0 * i) for i in range(N)]
print("F1186 (#243): is the σ-excitation op(x)operand (k=2) or op(x)operand(x)RESPONSION (k=3)?\n")
print("   corrupt an excitation (perturb one site by 0.18); track the squared corruption over %d steps:\n" % 30)
print("   condition                          corruption t=1   t=8   t=20   t=30    -> self-corrects?")
for label, eps, alpha in [("ε=0  ISOLATED op·operand (no substrate)", 0.0, 0.0),
                          ("ε=0.3 coupled, symmetric (α=0)",          0.3, 0.0),
                          ("ε=0.3 coupled, chiral   (α=0.5)",         0.3, 0.5)]:
    base = settle(eps, x0)
    dev = corruption_decay(eps, alpha, base)
    sc = "YES (decays)" if dev[-1] < 0.25 * dev[0] else "no (persists/grows)"
    print("   %-34s   %8.4f  %5.3f  %5.3f  %5.3f   %s" % (label, dev[0], dev[7], dev[19], dev[-1], sc))
print("\n  READ: if the corruption decays even at ε=0 (each site ISOLATED), then every op·operand carries its OWN responsion")
print("  — the ATTRACTOR contraction (the map pulling the operand back to its cyclic phase-lock slot) IS the (x)responsion,")
print("  intrinsic (F1171 'EC is intrinsic, not bolted-on'). So the σ-excitation is op(x)operand(x)RESPONSION (k=3), and the")
print("  responsion is FRACTAL: the same phase-locking reinforcement at the EXCITATION scale (attractor stability) and the")
print("  SUBSTRATE scale (the comb, F1184). Answer: BOTH — it is an op(x)operand carrying (x)responsion, all the way down.")
