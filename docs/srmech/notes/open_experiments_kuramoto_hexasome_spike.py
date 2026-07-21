#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provenance script for `open_experiments_kuramoto_hexasome_spike.md`.

Generates EVERY load-bearing number in that note
(`[[feedback_computational_provenance_discipline]]`).

DISCIPLINE
----------
* No ``numpy`` / ``math`` / ``fractions`` — srmech Class-N rationals only
  (`srmech.amsc.rational`), exact integer pairs ``(num, den)``.
* **No ``abs()``.** Sign is Class-K pin-slot
  (`srmech.amsc.cascade.pin_slot_at_zero` -> ``(sign, magnitude)``);
  sign re-application is Class C
  (`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`).
* The integrator under test is srmech's OWN shipped op
  `srmech.amsc.cascade.kuramoto_step` (v0.6.0rc14 generalisation:
  ``adjacency`` / ``alpha`` / ``pin_anchor`` / ``pin_strength``).
  This spike is srmech testing srmech's own hypothesis.

Run:  python open_experiments_kuramoto_hexasome_spike.py
"""

from __future__ import annotations

from srmech.amsc import rational as R
from srmech.amsc.cascade import kuramoto_step, pin_slot_at_zero

# ─────────────────────────────────────────────────────────────────────────
# Class-K helpers — magnitude / comparison WITHOUT abs()
# ─────────────────────────────────────────────────────────────────────────


def mag(x: float) -> float:
    """Class-K pin-slot magnitude. ``pin_slot_at_zero`` -> (sign, magnitude)."""
    _sign, m = pin_slot_at_zero(float(x))
    return m


def sign_of(x: float) -> int:
    """Class-K pin-slot sign (the phase boundary), -1 / 0 / +1."""
    s, _m = pin_slot_at_zero(float(x))
    return s


def lt(a: float, b: float) -> bool:
    """magnitude(a) < magnitude(b), Class-K routed."""
    return mag(a) < mag(b)


# ─────────────────────────────────────────────────────────────────────────
# Class-N exact rational helpers (integer pairs; no `fractions`)
# ─────────────────────────────────────────────────────────────────────────


def q_to_float(q) -> float:
    """Exact-rational -> float. Accepts BOTH srmech carriers:
    ``rational_*`` return integer ``(num, den)`` tuples; the float-argument
    convenience wrappers (``R.sin`` / ``R.cos`` / ``R.atan`` / ``R.sqrt``)
    return a ``srmech.amsc.q.Q``. Both are exact until this boundary.
    """
    if hasattr(q, "as_pair"):
        n, d = q.as_pair()
        return n / d
    return q[0] / q[1]


TWO_PI = 2.0 * float(R.pi_cascade_digits(30))


def rsin(x: float) -> float:
    return q_to_float(R.sin(float(x)))


def rcos(x: float) -> float:
    return q_to_float(R.cos(float(x)))


def rasin(x: float) -> float:
    """arcsin via Class-N atan: asin(x) = atan(x / sqrt(1 - x^2))."""
    one_minus = 1.0 - float(x) * float(x)
    if not (one_minus > 0.0):
        # |x| == 1 -> pi/2 with the Class-K sign re-applied (Class C)
        return sign_of(x) * (TWO_PI / 4.0)
    root = q_to_float(R.sqrt(one_minus))
    return q_to_float(R.atan(float(x) / root))


# ─────────────────────────────────────────────────────────────────────────
# BLOCK 0 — the attested detuning, exact integer arithmetic
# ─────────────────────────────────────────────────────────────────────────

# ATTESTED [PMC6162219, Segura et al. 2018]: surface helical repeat
# h_s ~ 10.2 bp/turn; solution helical repeat h_0 ~ 10.5 bp/turn.
# ATTESTED [PMC4512544, Hodges et al. 2015]: k = 14 minor-groove contacts.
H_S = (51, 5)      # 10.2 bp/turn  (surface)
H_0 = (21, 2)      # 10.5 bp/turn  (solution / ideal)
N_BP = 147         # wrapped bp
K_CONTACTS = 14

RESULTS: list[dict] = []


def rec(**kw) -> None:
    RESULTS.append(kw)


def block0() -> dict:
    # 1/h_s - 1/h_0 exactly, in turns per bp
    inv_hs = R.rational_div((1, 1), H_S)
    inv_h0 = R.rational_div((1, 1), H_0)
    neg_inv_h0 = (-inv_h0[0], inv_h0[1])
    d_turn_per_bp = R.rational_add(inv_hs, neg_inv_h0)      # 1/357
    d_phi = R.rational_mul((N_BP, 1), d_turn_per_bp)         # 7/17

    # exact commensuration check: N / h_0 == k
    comm = R.rational_div((N_BP, 1), H_0)                    # 14/1

    # physical angular detuning, rad per bp
    d_omega = TWO_PI * q_to_float(d_turn_per_bp)
    om_ideal = TWO_PI / q_to_float(H_0)
    om_surf = TWO_PI / q_to_float(H_S)

    print("=" * 74)
    print("BLOCK 0 — the attested detuning (exact Class-N integer arithmetic)")
    print("=" * 74)
    print(f"  h_s = {H_S[0]}/{H_S[1]} = {q_to_float(H_S):.4f} bp/turn   [PMC6162219]")
    print(f"  h_0 = {H_0[0]}/{H_0[1]} = {q_to_float(H_0):.4f} bp/turn   [PMC6162219]")
    print(f"  N   = {N_BP} bp,  k = {K_CONTACTS} contacts               [PMC4512544]")
    print(f"  exact commensuration  N/h_0 = {comm[0]}/{comm[1]}"
          f"  -> {q_to_float(comm):.6f}  (== k? {q_to_float(comm) == float(K_CONTACTS)})")
    print(f"  detuning 1/h_s - 1/h_0 = {d_turn_per_bp[0]}/{d_turn_per_bp[1]} turns/bp")
    print(f"  dPhi = N x that       = {d_phi[0]}/{d_phi[1]}"
          f" = {q_to_float(d_phi):.6f} turns   [reproduces prior spike]")
    print(f"  omega_ideal = 2pi/h_0 = {om_ideal:.9f} rad/bp")
    print(f"  omega_surf  = 2pi/h_s = {om_surf:.9f} rad/bp")
    print(f"  Domega                = {d_omega:.9f} rad/bp")
    rec(block="0", kind="setup", d_phi_exact=f"{d_phi[0]}/{d_phi[1]}",
        d_turn_per_bp_exact=f"{d_turn_per_bp[0]}/{d_turn_per_bp[1]}",
        d_omega_rad_per_bp=d_omega, commensuration_exact=f"{comm[0]}/{comm[1]}")
    return {"d_omega": d_omega, "om_ideal": om_ideal, "om_surf": om_surf,
            "d_phi_turns": q_to_float(d_phi)}


# ─────────────────────────────────────────────────────────────────────────
# integrator — drives srmech's shipped kuramoto_step
# ─────────────────────────────────────────────────────────────────────────


def run(theta, omega, *, coupling, dt, steps, adjacency=None, alpha=0.0,
        pin_anchor=None, pin_strength=1.0):
    th = list(theta)
    for _ in range(steps):
        th = kuramoto_step(th, omega, coupling=coupling, dt=dt,
                           adjacency=adjacency, alpha=alpha,
                           pin_anchor=pin_anchor, pin_strength=pin_strength)
    return th


def locked_pair(d_omega, k, *, alpha=0.0, adjacency=None, dt=0.02,
                settle=2000, probe=1000):
    """Integrate a 2-oscillator pair; return (is_locked, phi_star, drift_rate).

    SCALE INVARIANCE (exact, and load-bearing for the runtime budget):
    ``dphi/dt = Domega - K_eff sin(phi)`` is invariant under
    ``(Domega, K, t) -> (L*Domega, L*K, t/L)``.  So a tongue measured with
    ``Domega = 1`` IS the physical tongue, with ``K_phys = Domega_nuc * k``.
    Lock test: the phase difference stops winding over the probe window.
    """
    omega = [0.0, float(d_omega)]
    th = run([0.0, 0.0], omega, coupling=k, dt=dt, steps=settle,
             adjacency=adjacency, alpha=alpha)
    phi_a = th[1] - th[0]
    th2 = run(th, omega, coupling=k, dt=dt, steps=probe,
              adjacency=adjacency, alpha=alpha)
    phi_b = th2[1] - th2[0]
    drift = (phi_b - phi_a) / (probe * dt)          # d(phi)/dt residual
    # locked iff the winding rate is a tiny fraction of the free detuning
    is_locked = lt(drift, d_omega / 1000.0)
    return is_locked, phi_b, drift, th2


# ─────────────────────────────────────────────────────────────────────────
# BLOCK A — N=2, alpha=0: does it lock, and is the residual retained?
# ─────────────────────────────────────────────────────────────────────────


def block_a(cfg) -> None:
    d_omega = cfg["d_omega"]
    print()
    print("=" * 74)
    print("BLOCK E1-A — N=2, alpha=0, coupling sweep (PHYSICAL units, rad/bp)")
    print("=" * 74)
    print("  closed form (all-to-all n=2, weight K/n):  dphi/dt = Domega - K sin(phi)")
    print(f"  => predicted K_c = Domega = {d_omega:.9f} rad/bp")
    print()
    print("     K/K_c    locked   phi* (rad)  phi* (turns)   sin(phi*)   "
          "predicted Domega/K")
    print("     " + "-" * 74)
    for ratio in (0.50, 0.90, 0.99, 1.00, 1.01, 1.10, 1.50, 2.00, 4.00, 10.0):
        k = d_omega * ratio
        # PHYSICAL units: dt = 2 bp, T_settle = 16000 bp, T_probe = 8000 bp
        is_lk, phi, drift, _ = locked_pair(d_omega, k, dt=2.0,
                                           settle=8000, probe=4000)
        sphi = rsin(phi)
        pred = (d_omega / k) if k > 0 else float("nan")
        flag = "LOCK " if is_lk else "drift"
        print(f"     {ratio:6.2f}   {flag}   {phi:10.6f}  {phi / TWO_PI:11.6f}"
              f"   {sphi:9.6f}   {pred:12.6f}")
        rec(block="E1-A", kind="pair_alpha0", k_over_kc=ratio,
            coupling=k, locked=bool(is_lk), phi_star_rad=phi,
            phi_star_turns=phi / TWO_PI, sin_phi_star=sphi,
            predicted_sin_phi=pred, drift=drift)
    print()
    print("  READ: above threshold the pair locks to ONE frequency, but phi* is")
    print("        NON-ZERO and satisfies sin(phi*) = Domega/K exactly.")
    print("        The residual is NOT eliminated - it is CONVERTED from a")
    print("        frequency residual into a RETAINED phase offset.")
    print("        phi* -> 0 only as K -> infinity (infinite coupling).")


# ─────────────────────────────────────────────────────────────────────────
# BLOCK B — the Arnold tongue: lock region vs K, and width scaling
# ─────────────────────────────────────────────────────────────────────────


def block_b(cfg) -> None:
    print()
    print("=" * 74)
    print("BLOCK E1-B — Arnold tongue (normalised: detuning in units of Domega_nuc)")
    print("=" * 74)
    print("  Normalised: detuning + coupling in units of Domega_nuc"
          f" = {cfg['d_omega']:.6f} rad/bp.")
    print("  Scale invariance is EXACT (see locked_pair docstring), so this")
    print("  normalised tongue IS the physical tongue.")
    detunings = [i * 0.25 for i in range(-6, 7)]  # -1.5 .. +1.5
    couplings = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

    print()
    print("     K |  " + "".join(f"{d:>5.2f}" for d in detunings))
    print("   ----+" + "-" * (5 * len(detunings) + 2))
    grid = []
    for k in couplings:
        rowchars = []
        for d in detunings:
            if mag(d) < 1e-12:
                is_lk = True
            else:
                is_lk, _phi, _dr, _ = locked_pair(d, k)
            rowchars.append("  #  " if is_lk else "  .  ")
            grid.append({"k": k, "detuning": d, "locked": bool(is_lk)})
        print(f"   {k:4.2f}|  " + "".join(rowchars))
    print()
    print("   '#' = phase-locked, '.' = drifting.  The V opens LINEARLY:")
    print("   the lock condition is |Domega| <= K (n=2 mean-field weight K/n).")
    print()
    print("   tongue-width scaling (measured half-width vs K):")
    print("      K       measured half-width   K (predicted)   ratio")
    for k in (0.25, 0.5, 1.0, 1.5, 2.0):
        # bisect the lock boundary in detuning
        lo, hi = 0.0, 4.0 * k + 1.0
        for _ in range(16):
            mid = 0.5 * (lo + hi)
            is_lk, _p, _d, _ = locked_pair(mid, k)
            if is_lk:
                lo = mid
            else:
                hi = mid
        half = 0.5 * (lo + hi)
        ratio = (half / k) if k > 0 else float("nan")
        print(f"    {k:5.2f}        {half:10.6f}        {k:10.6f}   {ratio:7.4f}")
        rec(block="E1-B", kind="tongue_width", coupling=k,
            half_width_measured=half, half_width_predicted=k, ratio=ratio)
    print()
    print("   READ: half-width / K = 1.000 across the sweep => the tongue opens")
    print("         LINEARLY in K. Canonical 1:1 Arnold tongue.")
    for g in grid:
        rec(block="E1-B", kind="tongue_cell", **g)


# ─────────────────────────────────────────────────────────────────────────
# BLOCK C — the alpha knob: what does Sakaguchi frustration actually do?
# ─────────────────────────────────────────────────────────────────────────


def block_c(cfg) -> None:
    d_omega = cfg["d_omega"]
    print()
    print("=" * 74)
    print("BLOCK E1-C — Sakaguchi alpha (N=2). THE LOAD-BEARING KNOB.")
    print("=" * 74)
    print("  Two coupling branches differ under alpha and BOTH are reported:")
    print("   (i)  adjacency=None  -> mean-field, the sum RUNS OVER j==i, so a")
    print("        self-term (K/n)*sin(-alpha) enters as a COMMON-MODE drift.")
    print("        (This is the standard Kuramoto-Sakaguchi mean-field")
    print("         convention, not a defect - noted because it is easy to miss.)")
    print("   (ii) adjacency=[[0,1],[1,0]] -> zero diagonal, NO self-term:")
    print("        pure pairwise Sakaguchi.")
    print()
    adj = [[0.0, 1.0], [1.0, 0.0]]

    # --- (ii) pure pairwise: K_c(alpha), phi*(alpha), Omega offset ---
    print("  (ii) pure pairwise  dphi/dt = Domega - 2K sin(phi) cos(alpha)")
    print("       => K_c(alpha) = Domega / (2 cos alpha)   [tongue NARROWS]")
    print("       => Omega_lock = omega_bar - K cos(phi*) sin(alpha)  [ASYMMETRY]")
    print()
    print("  (normalised: Domega = 1; multiply K_c by Domega_nuc for rad/bp)")
    print()
    print("     alpha     K_c meas.   K_c pred.   phi* (rad)   Omega-omega_bar"
          "   residual split")
    print("     " + "-" * 76)
    d_n = 1.0                       # normalised detuning
    k_fixed = 4.0 * d_n
    om_bar = 0.5 * (0.0 + d_n)
    for adeg in (0, 15, 30, 45, 60, 75):
        alpha = TWO_PI * adeg / 360.0
        # bisect K_c at this alpha
        lo, hi = 0.0, 40.0 * d_n
        for _ in range(18):
            mid = 0.5 * (lo + hi)
            is_lk, _p, _d, _ = locked_pair(d_n, mid, alpha=alpha,
                                           adjacency=adj)
            if is_lk:
                hi = mid
            else:
                lo = mid
        kc = 0.5 * (lo + hi)
        ca = rcos(alpha)
        kc_pred = d_n / (2.0 * ca) if ca > 0 else float("inf")

        # locked state at a fixed supercritical K
        is_lk, phi, _dr, th = locked_pair(d_n, k_fixed, alpha=alpha,
                                          adjacency=adj, settle=4000,
                                          probe=2000)
        # common locked frequency: advance further and difference
        th_next = run(th, [0.0, d_n], coupling=k_fixed, dt=0.02,
                      steps=2000, adjacency=adj, alpha=alpha)
        omega_lock = (th_next[0] - th[0]) / (2000 * 0.02)
        off = omega_lock - om_bar
        # how the detuning residual is APPORTIONED between the two oscillators
        pull0 = omega_lock - 0.0
        pull1 = omega_lock - d_n
        split = pull0 / d_n               # fraction borne by oscillator 0
        print(f"     {adeg:3d} deg   {kc:9.6f}   {kc_pred:9.6f}"
              f"   {phi:10.6f}   {off:+13.6f}   {split:6.3f}/{1 - split:.3f}")
        rec(block="E1-C", kind="alpha_pairwise", alpha_deg=adeg,
            alpha_rad=alpha, kc_measured=kc, kc_predicted=kc_pred,
            phi_star_rad=phi, omega_lock=omega_lock,
            omega_offset_from_mean=off, pull_osc0=pull0, pull_osc1=pull1,
            residual_fraction_osc0=split, locked=bool(is_lk))

    # --- (i) mean-field self-term demonstration, incl. n=1 ---
    print()
    print("  (i) mean-field branch (adjacency=None) - the j==i self-term:")
    print("      n=1, omega=0, K=1: one step of dt=1 should give -K sin(alpha)")
    for adeg in (0, 30, 90):
        alpha = TWO_PI * adeg / 360.0
        out = kuramoto_step([0.0], [0.0], coupling=1.0, dt=1.0, alpha=alpha)
        print(f"        alpha={adeg:3d} deg -> theta = {out[0]:+.9f}"
              f"   (-sin alpha = {-rsin(alpha):+.9f})")
        rec(block="E1-C", kind="selfterm_n1", alpha_deg=adeg,
            theta_after_one_step=out[0], minus_sin_alpha=-rsin(alpha))
    # --- (iii) THE CLAUSE-(d) TEST: a PURE allocation knob ----------------
    print()
    print("  (iii) THE CLAUSE-(d) TEST — is the allocation UNDERDETERMINED by")
    print("        the closure condition?  Directed coupling at alpha=0, holding")
    print("        the SUM A12+A21 fixed and varying only the RATIO.")
    print("        Closed form:  dphi/dt = Domega - K(A12+A21) sin(phi)")
    print("          -> the LOCK THRESHOLD depends ONLY on the SUM")
    print("          -> Omega = w1 + Domega*A12/(A12+A21)")
    print("             i.e. the SPLIT depends ONLY on the RATIO")
    print()
    print("      A12   A21   sum    Omega      split(osc0)   phi*      "
          "split pred.")
    print("      " + "-" * 68)
    d_n2, k2 = 1.0, 2.0
    for a12, a21 in ((1.0, 1.0), (1.5, 0.5), (1.9, 0.1), (0.5, 1.5), (0.1, 1.9)):
        adj2 = [[0.0, a12], [a21, 0.0]]
        th = run([0.0, 0.0], [0.0, d_n2], coupling=k2, dt=0.02, steps=6000,
                 adjacency=adj2)
        th2 = run(th, [0.0, d_n2], coupling=k2, dt=0.02, steps=2000,
                  adjacency=adj2)
        om_lock = (th2[0] - th[0]) / (2000 * 0.02)
        phi = th2[1] - th2[0]
        pred = a12 / (a12 + a21)
        print(f"     {a12:4.1f}  {a21:4.1f}  {a12 + a21:4.1f}  {om_lock:9.5f}"
              f"   {om_lock / d_n2:10.4f}   {phi:8.5f}   {pred:9.4f}")
        rec(block="E1-C", kind="pure_allocation_directed", a12=a12, a21=a21,
            adj_sum=a12 + a21, omega_lock=om_lock,
            split_measured=om_lock / d_n2, split_predicted=pred,
            phi_star_rad=phi)
    print()
    print("      READ: phi* is IDENTICAL across every row (the closure state is")
    print("            untouched) while the split runs 0.05 -> 0.95. The lock")
    print("            threshold is BLIND to the allocation. This is exactly")
    print("            music-spike clause (d): allocation-underdetermination.")

    print()
    print("  READ: alpha does THREE things, and NONE of them is the clean")
    print("        allocation the dispatch expected:")
    print("        1. it NARROWS the tongue (K_c grows as 1/cos alpha);")
    print("        2. in the mean-field branch it adds a common-mode drift")
    print("           (the j==i self-term above);")
    print("        3. it moves the locked frequency off the mean -- but as a")
    print("           COMMON-MODE DRAG ON BOTH members, not a re-partition")
    print("           between them: at alpha=0 the split is exactly")
    print("           0.500/0.500, and at alpha != 0 the split leaves [0,1]")
    print("           entirely (-0.53/1.53, ...), i.e. BOTH oscillators are")
    print("           pulled the same way. The CLEAN allocation knob is the")
    print("           directed adjacency of block (iii), not alpha.")


# ─────────────────────────────────────────────────────────────────────────
# BLOCK D — does a 14:1 commensuration lock?  (predicted NULL)
# ─────────────────────────────────────────────────────────────────────────


def block_d(cfg) -> None:
    print()
    print("=" * 74)
    print("BLOCK E1-D — higher-order p:q locking: what this model CANNOT do.")
    print("=" * 74)
    print("  Test: two oscillators at frequency ratio ~14:1, swept over strong")
    print("        coupling. Does a 14:1 tongue exist in the sinusoidal model?")
    print()
    print("  Framing note (corrected): the NUCLEOSOME's commensuration is 1:1,")
    print("  not 14:1 - one DNA helical turn PER CONTACT (10.5 vs 10.2 bp, a")
    print("  2.9% detuning). So the absence of high-order tongues is NOT a")
    print("  defect for this application. It IS a hard limit for MUSIC's comma,")
    print("  which is a 12:7 commensuration this model cannot express.")
    print()
    print("      K        omega2/omega1    locked at 1:1?   winding ratio")
    om1 = 1.0
    om2 = 14.0 * om1 * 1.02          # 2% off exact 14:1
    for k in (0.1, 1.0, 5.0, 10.0, 13.0, 20.0):
        th = run([0.0, 0.0], [om1, om2], coupling=k, dt=0.005, steps=20000)
        th2 = run(th, [om1, om2], coupling=k, dt=0.005, steps=20000)
        r1 = (th2[0] - th[0]) / (20000 * 0.005)
        r2 = (th2[1] - th[1]) / (20000 * 0.005)
        wr = (r2 / r1) if mag(r1) > 1e-12 else float("nan")
        onelock = lt(r2 - r1, 1e-6)
        print(f"    {k:6.2f}      {om2 / om1:10.4f}       "
              f"{'yes' if onelock else 'no ':^12}     {wr:10.6f}")
        rec(block="E1-D", kind="pq_lock", coupling=k, omega_ratio=om2 / om1,
            rate1=r1, rate2=r2, winding_ratio=wr, locked_1to1=bool(onelock))
    print()
    print("  READ: the sinusoidal Kuramoto coupling has ONE resonance, 1:1.")
    print("        No 14:1 tongue exists at any coupling; the pair either")
    print("        drifts or collapses to 1:1 once K exceeds the (large)")
    print("        1:1 threshold |Domega| = 13.28. Higher-order p:q tongues")
    print("        require harmonics in the coupling function that this model")
    print("        does not have.  [NULL - reported in the note.]")


# ─────────────────────────────────────────────────────────────────────────
# BLOCK E — N=14 pinned open chain: is the residual DISTRIBUTED?
# ─────────────────────────────────────────────────────────────────────────


def chain_adjacency(n: int, *, forward=1.0, backward=1.0) -> list[list[float]]:
    """Open nearest-neighbour chain, zero diagonal (no self-term).

    ``forward != backward`` makes the matrix NON-SYMMETRIC, i.e. DIRECTED
    coupling — the shipped op's documented one-way-coupling mode. The DNA
    duplex has an intrinsic 5'->3' sense, so a directed chain is the honest
    encoding of a handed backbone; the symmetric chain is the achiral control.
    """
    a = [[0.0] * n for _ in range(n)]
    for i in range(n - 1):
        a[i][i + 1] = float(forward)      # i sees its i+1 neighbour
        a[i + 1][i] = float(backward)     # i+1 sees its i neighbour
    return a


def block_e(cfg) -> None:
    d_omega = cfg["d_omega"]
    n = K_CONTACTS
    print()
    print("=" * 74)
    print(f"BLOCK E1-E — N={n} contacts, open chain, pinned to the exact lattice")
    print("=" * 74)
    print("  Frame: theta_i = the DNA helical phase at contact i MEASURED")
    print("         RELATIVE TO the octamer's exact lattice demand.")
    print("         The ideal (h_0) state is theta_i == 0 for all i.")
    print("  omega_i = Domega (the detuning drives every contact off the lattice)")
    print("  pin_anchor psi_i = 0 (the lattice demands zero residual at each")
    print("                       arginine anchor); pin_strength p = the grip.")
    print("  adjacency = open nearest-neighbour chain (the DNA backbone).")
    print()
    print("  (normalised: Domega = 1, so theta* is in radians of retained")
    print("   residual per contact; K and p in units of Domega_nuc.)")
    print()
    adj = chain_adjacency(n)
    d_n = 1.0
    omega = [d_n] * n
    psi = [0.0] * n

    print("  (a) uniform pinning, alpha=0 — sweep grip strength p:")
    print()
    print("       p/Domega    mean theta*    end theta*   centre theta*"
          "   end/centre")
    for pr in (0.5, 1.0, 2.0, 5.0, 20.0):
        p = d_n * pr
        th = run([0.0] * n, omega, coupling=2.0 * d_n, dt=0.02,
                 steps=2500, adjacency=adj, alpha=0.0,
                 pin_anchor=psi, pin_strength=p)
        meanth = sum(th) / n
        end = 0.5 * (th[0] + th[n - 1])
        centre = 0.5 * (th[n // 2 - 1] + th[n // 2])
        rr = (end / centre) if mag(centre) > 1e-15 else float("nan")
        print(f"      {pr:7.2f}   {meanth:12.6f}  {end:11.6f}  {centre:12.6f}"
              f"   {rr:9.4f}")
        rec(block="E1-E", kind="chain_pin_sweep", p_over_domega=pr,
            pin_strength=p, mean_theta=meanth, end_theta=end,
            centre_theta=centre, end_over_centre=rr, profile=list(th))
    print()
    print("      READ: theta* is NON-ZERO at every grip strength. The pin")
    print("            cannot drive the residual to zero - it can only trade")
    print("            phase offset against grip.  Residual RETAINED.")

    # --- (b) the chirality test: alpha breaks the end-to-end symmetry ---
    print()
    print("  (b) THE CHIRALITY TEST — 2x2: {symmetric, directed} x {alpha=0, alpha!=0}")
    print("      K = 1, p = 4 (chosen so the state stays LOCKED at every alpha;")
    print("      at K=4/p=2 the alpha drive K*deg*sin(alpha) overwhelms the pin")
    print("      and the chain DRIFTS - a drifting profile is not a locked")
    print("      allocation and must not be read as one).")
    print()
    p_c, k_c = 4.0 * d_n, 1.0 * d_n
    adj_dir = chain_adjacency(n, forward=1.0, backward=0.5)
    for label, a_use in (("SYMMETRIC          ", adj),
                         ("DIRECTED f=1.0 b=0.5", adj_dir)):
        for adeg in (0, 30, -30):
            alpha = TWO_PI * adeg / 360.0
            th = run([0.0] * n, omega, coupling=k_c, dt=0.02, steps=2500,
                     adjacency=a_use, alpha=alpha, pin_anchor=psi,
                     pin_strength=p_c)
            th2 = run(th, omega, coupling=k_c, dt=0.02, steps=500,
                      adjacency=a_use, alpha=alpha, pin_anchor=psi,
                      pin_strength=p_c)
            drift = max(mag(th2[i] - th[i]) for i in range(n)) / (500 * 0.02)
            asym = th[0] - th[n - 1]      # Class-K signed, NOT abs
            s = sign_of(asym)
            print(f"    {label} alpha={adeg:+4d}  locked={drift < 1e-9}"
                  f"  ends {th[0]:+.5f} / {th[n - 1]:+.5f}"
                  f"  centre {th[n // 2]:+.5f}")
            print(f"    {'':20s}   theta_1 - theta_14 = {asym:+.6e}"
                  f"   (Class-K sign {s:+d})")
            rec(block="E1-E", kind="chain_chirality_2x2",
                topology=label.strip(), alpha_deg=adeg, alpha_rad=alpha,
                profile=list(th), end_to_end_asymmetry=asym,
                class_k_sign=s, drift=drift, locked=bool(drift < 1e-9))
    print()
    print("      READ: chirality is an AND-GATE. NEITHER factor alone breaks the")
    print("            end-to-end symmetry:")
    print("              symmetric + any alpha  -> asym EXACTLY 0")
    print("              directed  + alpha = 0  -> asym EXACTLY 0")
    print("              directed  + alpha != 0 -> asym != 0, and the SIGN")
    print("                                        REVERSES with sign(alpha)")
    print("            The symmetric-chain zero is exact, not small: the")
    print("            reflection i -> n+1-i maps the alpha-frustrated")
    print("            SYMMETRIC chain to ITSELF, because alpha enters both")
    print("            neighbour terms identically.")


# ─────────────────────────────────────────────────────────────────────────
# BLOCK E2 — S2's causal chain k -> h_s -> dPhi -> dTw -> dLk, tested
#            against the ONE non-canonical particle with an attested dLk.
# ─────────────────────────────────────────────────────────────────────────

# ATTESTED [PMC4623960, Vlijm et al. 2015 PLoS ONE, CC BY]: the (H3.3-H4)2
# tetrasome linking number "was rather observed to change between -0.80 +- 0.05
# and +0.86 +- 0.39 turns". Two states, opposite handedness.
TETRA_LEFT = (-0.80, 0.05)
TETRA_RIGHT = (+0.86, 0.39)
# ATTESTED [PMC6162219, Segura et al. 2018, CC BY]: canonical dLk = -1.26.
CANON_DLK = -1.26


def s2_closed_form(n_bp: float, shape: float):
    """S2's chain in closed form.

    ATTESTED FORMS: dPhi = N(1/h_s - 1/h_0);  Wr = -n(1 - sin delta).
    OURS (auxiliary, NOT attested - flagged, and load-bearing for the verdict):
      * superhelical turns n scale LINEARLY with N   (n = 1.65 * N/147)
      * the surface-twist correction dSTw scales LINEARLY with N
    Both auxiliaries are needed to get from k to dLk at all; neither is
    independently pinned for a tetrasome.
    """
    d_phi = n_bp / 357.0                       # attested form
    n_turns = 1.65 * n_bp / 147.0              # AUX (ours)
    wr = -n_turns * shape                      # attested form
    d_stw = -0.19 * n_bp / 147.0               # AUX (ours)
    d_tw = d_phi + d_stw
    return d_phi, n_turns, wr, d_stw, d_tw, wr + d_tw


def block_e2() -> None:
    print()
    print("=" * 74)
    print("BLOCK E2 — S2's k -> h_s -> dPhi -> dTw -> dLk chain, tested")
    print("=" * 74)
    shape = 1.0 - q_to_float(R.sin(TWO_PI * 4.0 / 360.0))
    print(f"  1 - sin(4 deg) = {shape:.6f}   (Segura's pitch angle)")
    print()
    print("   N     dPhi       n         Wr        dSTw      dTw      dLk_pred")
    print("   " + "-" * 66)
    for n_bp in (147, 70, 63, 166):
        d = s2_closed_form(float(n_bp), shape)
        print(f"  {n_bp:4d}  " + "  ".join(f"{v:+8.5f}" for v in d))
        rec(block="E2", kind="s2_closed_form", n_bp=n_bp, d_phi=d[0],
            n_turns=d[1], wr=d[2], d_stw=d[3], d_tw=d[4], dlk_pred=d[5])
    print()
    print("  Comparison to ATTESTED measurements:")
    print()
    print("   N    particle       dLk_pred   dLk_meas   residual   sigma")
    print("   " + "-" * 62)
    cases = (
        (147, "canonical NCP", CANON_DLK, 0.05, "PMC6162219 CC BY"),
        (70, "tetrasome (obs N)", TETRA_LEFT[0], TETRA_LEFT[1],
         "PMC4623960 CC BY"),
        (63, "tetrasome (S2 N)", TETRA_LEFT[0], TETRA_LEFT[1],
         "PMC4623960 CC BY"),
    )
    for n_bp, label, meas, err, src in cases:
        pred = s2_closed_form(float(n_bp), shape)[5]
        resid = meas - pred
        s = sign_of(resid)                     # Class-K, NOT abs
        sigma = mag(resid) / err
        print(f"  {n_bp:4d}  {label:16s} {pred:+8.5f}  {meas:+8.2f}"
              f"  {resid:+8.5f}   {sigma:5.2f}  [{src}]")
        rec(block="E2", kind="s2_vs_measured", n_bp=n_bp, particle=label,
            dlk_pred=pred, dlk_measured=meas, measurement_error=err,
            residual=resid, residual_class_k_sign=s, sigma=sigma, source=src)
    print()
    print("  THE TWO FINDINGS:")
    print("  (1) The residual SIGN FLIPS between the two particles:")
    print("      canonical resid = +0.053 (model too NEGATIVE),")
    print("      tetrasome resid = -0.175 / -0.237 (model too POSITIVE).")
    print("      => NO linear-in-N law fits both. The miss is not an offset.")
    print("  (2) The tetrasome dLk is BISTABLE and SIGN-FLIPPING:")
    print(f"      {TETRA_LEFT[0]:+.2f} +- {TETRA_LEFT[1]:.2f} (left) and "
          f"{TETRA_RIGHT[0]:+.2f} +- {TETRA_RIGHT[1]:.2f} (right).")
    lsum = TETRA_LEFT[0] + TETRA_RIGHT[0]
    print(f"      The two states sum to {lsum:+.2f} — near-symmetric about 0.")
    print("      S2 is a single-valued commensuration detuning: it emits ONE")
    print("      number with ONE sign. It cannot produce a two-state")
    print("      sign-flipping particle at all. This is a STRUCTURAL problem,")
    print("      independent of any numerical miss.")
    rec(block="E2", kind="tetrasome_bistability", left=TETRA_LEFT[0],
        left_err=TETRA_LEFT[1], right=TETRA_RIGHT[0],
        right_err=TETRA_RIGHT[1], sum_of_states=lsum,
        source="PMC4623960 CC BY")


# ─────────────────────────────────────────────────────────────────────────
# BLOCK E3 — anomaly A4: the Chen 2010 ledger, exact
# ─────────────────────────────────────────────────────────────────────────


def block_e3() -> None:
    print()
    print("=" * 74)
    print("BLOCK E3 — anomaly A4: Chen et al. 2010 (PMC2887952) SLk ledger")
    print("=" * 74)
    slk = (-18, 10)                 # -1.8
    dlk = (-10, 10)                 # -1.0
    phi_minus = (-8, 10)            # -0.8  (as extracted)
    phi_plus = (8, 10)              # +0.8
    for name, phi in (("as printed/extracted  phi = -0.8", phi_minus),
                      ("sign-flipped          phi = +0.8", phi_plus)):
        tot = R.rational_add(slk, phi)
        neg_dlk = (-dlk[0], dlk[1])
        resid = R.rational_add(tot, neg_dlk)
        s = sign_of(q_to_float(resid))
        closes = (resid[0] == 0)
        print(f"  {name}:  dSLk + dphi = {tot[0]}/{tot[1]}"
              f" = {q_to_float(tot):+.2f}   vs dLk = {q_to_float(dlk):+.2f}"
              f"   residual = {q_to_float(resid):+.2f}"
              f"   {'CLOSES' if closes else 'DOES NOT CLOSE'}")
        rec(block="E3", kind="a4_ledger", variant=name,
            sum_exact=f"{tot[0]}/{tot[1]}", residual_exact=f"{resid[0]}/{resid[1]}",
            residual=q_to_float(resid), closes=bool(closes), class_k_sign=s)
    print()
    print("  The magnitude 0.8 is consistent with the ledger; only the sign as")
    print("  printed is not.  Resolution of WHERE the sign lives (paper vs")
    print("  extraction) is a fetch question, reported in the note.")


# ─────────────────────────────────────────────────────────────────────────


NDJSON_PATH = "open_experiments_kuramoto_hexasome_spike.ndjson"
SPIKE_DATE = "2026-07-19"


def write_ndjson(path: str) -> int:
    """One record per line (`[[feedback_ndjson_over_bloated_json]]`)."""
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    full = os.path.join(here, path)
    with open(full, "w", encoding="utf-8") as fh:
        for r in RESULTS:
            row = {"date": SPIKE_DATE, "phase": "concertmaster_dispatch",
                   "spike": "open_experiments_kuramoto_hexasome"}
            row.update(r)
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return len(RESULTS)


def main() -> None:
    cfg = block0()
    block_a(cfg)
    block_b(cfg)
    block_c(cfg)
    block_d(cfg)
    block_e(cfg)
    block_e2()
    block_e3()
    n = write_ndjson(NDJSON_PATH)
    print()
    print("=" * 74)
    print(f"{n} records written to {NDJSON_PATH}")
    print("=" * 74)


if __name__ == "__main__":
    main()
