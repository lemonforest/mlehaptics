"""R-RBS-LM-141 — Chiral-coupling Kuramoto (F194, tests F190).

Question (F190): does the 4-way coupled oscillator's chirality require directed /
non-commutative coupling — the oscillator realization of ij != ji?

Two candidate realizations of "non-commutative coupling":
  (a) directed coupling MATRIX  A_ij != A_ji   (adjacency asymmetry)
  (b) phase-frustration alpha   sin(th_j - th_i - alpha)  (Sakaguchi; non-reciprocal)

Result:
  (a) NULL — at identical frequencies, in-phase (achiral; winding 0, Omega 0) is the
      attractor for symmetric AND directed A alike (coupling vanishes at in-phase
      regardless of A's symmetry). Adjacency asymmetry does NOT produce chirality.
  (b) CONFIRMED — phase-frustration alpha gives a handed collective rotation
      Omega(alpha) = -(K(N-1)/N) sin(alpha), ODD in alpha: Omega(-alpha) = -Omega(alpha).
      alpha=0 is achiral (static). +alpha / -alpha are the ij / ji mirror pair.

Refines F190: the oscillator's chirality is the PHASE-LAG (non-reciprocal coupling),
NOT the coupling-matrix direction. Pure numpy ODE (srmech has no integrator; follows
the R-95 Kuramoto precedent). Seeded for reproducibility; no abs() in any cascade.
"""
import numpy as np


def integrate(N, A, omega, K, alpha=0.0, T=80.0, dt=0.01, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2 * np.pi, N)
    for _ in range(int(T / dt)):
        diff = theta[None, :] - theta[:, None]
        theta = theta + dt * (omega + (K / N) * np.sum(A * np.sin(diff - alpha), axis=1))
    diff = theta[None, :] - theta[:, None]
    vel = omega + (K / N) * np.sum(A * np.sin(diff - alpha), axis=1)
    return np.mod(theta, 2 * np.pi), float(np.mean(vel))


def order_param(theta):
    return float(abs(np.mean(np.exp(1j * theta))))


if __name__ == "__main__":
    N, K = 4, 3.0
    omega = np.zeros(N)
    A_all = np.ones((N, N)) - np.eye(N)
    A_sym = np.zeros((N, N)); A_fwd = np.zeros((N, N))
    for i in range(N):
        A_sym[i, (i + 1) % N] = 1; A_sym[i, (i - 1) % N] = 1
        A_fwd[i, (i + 1) % N] = 1

    print("(a) coupling-matrix asymmetry (alpha=0):")
    for name, A in [("symmetric_ring", A_sym), ("directed_ring", A_fwd)]:
        Om = np.mean([integrate(N, A, omega, K, seed=s)[1] for s in range(8)])
        r = np.mean([order_param(integrate(N, A, omega, K, seed=s)[0]) for s in range(8)])
        print(f"   {name:16s}: <Omega>={Om:+.4f}  <r>={r:.3f}  -> {'ACHIRAL (null)' if abs(Om) < 1e-6 else 'chiral'}")

    print("(b) phase-frustration sweep (all-to-all A): Omega(alpha) should be ODD in alpha:")
    for alpha in [-0.7, -0.3, 0.0, 0.3, 0.7]:
        Om = np.mean([integrate(N, A_all, omega, K, alpha=alpha, seed=s)[1] for s in range(6)])
        analytic = -(K * (N - 1) / N) * np.sin(alpha)
        print(f"   alpha={alpha:+.1f}: <Omega>={Om:+.4f}  analytic=-(K(N-1)/N)sin(a)={analytic:+.4f}")
