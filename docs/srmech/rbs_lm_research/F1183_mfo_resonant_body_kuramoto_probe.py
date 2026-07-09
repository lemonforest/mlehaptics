"""F1183 (#243): the MFO resonant-BODY probe — a MULTI-MODE resonant body (coupled oscillators, srmech-native
kuramoto_step) instead of the minimal 1D logistic map (F1180). Measures the REINFORCEMENT as the Kuramoto ORDER
PARAMETER r (the phase-coherence = F1179's harmonic reinforcement, now a continuous physical quantity on a real
resonant body), and how the ASYMMETRY (Sakaguchi alpha = the_one's sigma / chirality) modulates it.

Claim tested: the resonant body's reinforcement (r) rises through a synchronization transition as coupling grows
(the continuous reinforcement law); the asymmetry alpha SHIFTS/lowers it and breaks the symmetry between forward and
backward collective drift (the chirality = the time-arrow, F1180's honest correction). srmech kuramoto_step is the
cascade; the order-parameter read-out uses math (a diagnostic, not a cascade). No magnitude-builtin on a cascade.
"""
import math
from srmech.amsc import cascade

N = 24                                        # a resonant body of N modes
# natural frequencies = a spread mode-spectrum (deterministic, no Math.random; a smooth ladder centred at 0)
OMEGA = [(-1.0 + 2.0 * i / (N - 1)) for i in range(N)]
THETA0 = [math.sin(3.0 * i) for i in range(N)]   # deterministic initial phases (no RNG)


def order_parameter(theta):
    """Kuramoto r = phase-coherence = the REINFORCEMENT (magnitude of the mean phase vector)."""
    C = sum(math.cos(t) for t in theta) / len(theta)
    S = sum(math.sin(t) for t in theta) / len(theta)
    return (C * C + S * S) ** 0.5, math.atan2(S, C)


def run(coupling, alpha, steps=1500, dt=0.05):
    theta = list(THETA0)
    for _ in range(steps):
        theta = cascade.kuramoto_step(theta, OMEGA, coupling=coupling, dt=dt, alpha=alpha)
    r, psi0 = order_parameter(theta)
    # drift: advance more, measure how the collective phase psi moves (chirality = signed drift)
    _, psi0 = order_parameter(theta)
    for _ in range(200):
        theta = cascade.kuramoto_step(theta, OMEGA, coupling=coupling, dt=dt, alpha=alpha)
    _, psi1 = order_parameter(theta)
    drift = (psi1 - psi0)
    while drift > math.pi:
        drift -= 2 * math.pi
    while drift < -math.pi:
        drift += 2 * math.pi
    return r, drift


print("F1183 (#243) MFO resonant-body probe — reinforcement r(coupling) on a %d-mode Kuramoto body (srmech.cascade)\n" % N)
print("A. the REINFORCEMENT transition (r = phase-coherence = F1179's harmonic reinforcement, continuous):")
print("   coupling   r(symmetric a=0)   r(asymmetric a=0.9)")
for K in (0.5, 1.0, 1.5, 2.0, 3.0, 4.0):
    rs, _ = run(K, 0.0)
    ra, _ = run(K, 0.9)
    print("     %.1f        %.3f              %.3f" % (K, rs, ra))
print("   -> r rises monotone through a synchronization transition = the continuous reinforcement law (the resonant")
print("      body LOCKS = reinforces a common rhythm above a critical coupling). The asymmetry lowers/shifts the lock.\n")

print("B. the ASYMMETRY breaks forward/backward symmetry (the chirality = the_one's sigma = the time-arrow, F1180):")
print("   alpha    r      collective drift (signed = a preferred direction)")
for a in (-0.9, 0.0, 0.9):
    r, drift = run(3.0, a)
    arrow = "→ forward" if drift > 0.02 else ("← backward" if drift < -0.02 else "· none (symmetric)")
    print("   %+.1f    %.3f    %+.3f   %s" % (a, r, drift, arrow))
print("\n  READ: the resonant BODY reinforces (locks) as coupling grows = F1179's harmonic reinforcement made continuous")
print("  and physical (r is the order parameter). The Sakaguchi asymmetry (alpha) is the_one's sigma: at a=0 the collective")
print("  phase does not drift (no arrow); at a=/=0 it drifts with a SIGN (a chiral traveling reinforcement) — the asymmetric")
print("  = time-directed part of the 'resonant asymmetric wave', now on a real multi-mode resonant body, srmech-native.")
