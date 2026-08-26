#!/usr/bin/env python3
"""R-RBS-SNN-4 — stage 4 of #197 / BX-4: the phase-locked read-head (the RBS-SNN read
mechanism), F388 temporal error-correction applied to the corpus store.

A finding q's couplings are a row of the store's adjacency: ψ*_j = phase 0 if j∈N(q),
phase π if j∉N(q) — the "stored fiber" (F386). Reading the store is NOISY (a real
device read). F388: a read-head that LOCKS to the fiber and TIME-AVERAGES recovers the
pattern bit-exact-ish from noise — temporal EC, ONE copy, ordinary silicon.

Mechanism (`cascade.kuramoto_step`, the pin term = the lock):
  each step draws a noisy read sample  o_t = ψ* + 𝒩(0,σ)
  the read-head relaxes toward o_t      θ_{t+1} = step(θ_t; pin_anchor=o_t, K=pin_strength, coupling=0)
  → a leaky integrator that AVERAGES OUT the read-noise; decode θ → recovered N(q).

Compares UNLOCKED (one noisy read = the "guess", F388 k=1/K=0) vs LOCKED (K>0, time-
averaged) → retrieval recall climbs with the lock. This IS the read mechanism BX-4 asked
for. srmech-first (kuramoto pin). Class-K decode (sign of the phase, never abs()).

Run:  <clean-venv>/bin/python R-RBS-SNN-4_phase_lock_readhead.py   (numpy-free OK)
Composes F388 (phase-lock = temporal EC) · F386 (couple the observer to the fiber) ·
F426 (the store) · cascade.kuramoto_step pin term. Defensive / no-lineage.
"""
import re
import glob
import os
import math
import random
from collections import defaultdict, deque
from srmech.amsc import cascade

HERE = os.path.dirname(os.path.abspath(__file__))


def parse_adj():
    sig = {}
    blob = {}
    for path in sorted(glob.glob(os.path.join(HERE, "R-RBS-LM-FINDING_*.md"))):
        m = re.search(r'FINDING_(\d+)', os.path.basename(path))
        if not m:
            continue
        fid = int(m.group(1))
        blob[fid] = open(path, encoding='utf-8').read()
        sig[fid] = True
    present = set(sig)
    adj = defaultdict(set)
    for fid, text in blob.items():
        for r in re.findall(r'\bF(\d{1,3})\b', text):
            t = int(r)
            if t in present and t != fid:
                adj[fid].add(t)
                adj[t].add(fid)
    return adj, present


def giant(adj, present):
    seen, best = set(), []
    for s in present:
        if s in seen:
            continue
        comp, q = [], deque([s])
        seen.add(s)
        while q:
            u = q.popleft()
            comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        if len(comp) > len(best):
            best = comp
    return best


def wrap(x):
    return (x + math.pi) % (2 * math.pi) - math.pi


def read_head(psi, sigma, K, W, rng):
    """F388 locked read: time-average noisy reads of psi via the kuramoto pin (coupling=0)."""
    M = len(psi)
    omega0 = [0.0] * M
    theta = [psi[j] + rng.gauss(0, sigma) for j in range(M)]   # first (noisy) read
    if K == 0.0:                                               # UNLOCKED = single noisy read (the guess)
        return theta
    for _ in range(W):                                         # LOCKED = integrate noisy reads
        obs = [psi[j] + rng.gauss(0, sigma) for j in range(M)]
        theta = cascade.kuramoto_step(theta, omega0, coupling=0.0, dt=0.05,
                                      pin_anchor=obs, pin_strength=K)
    return theta


def recall(theta, true_idx, M):
    rec = {j for j in range(M) if abs(wrap(theta[j])) < math.pi / 2}   # phase≈0 → in-neighborhood
    tp = len(rec & true_idx)
    return tp / len(true_idx) if true_idx else 0.0, (tp / len(rec) if rec else 0.0)


def main():
    adj, present = parse_adj()
    g = giant(adj, present)
    idx = {fid: i for i, fid in enumerate(sorted(g, key=lambda x: x))}
    M = len(g)
    rng = random.Random(20260606)
    # query the top-degree hubs (the load-bearing findings, F426)
    hubs = sorted(g, key=lambda fid: len(adj[fid]), reverse=True)[:5]

    print("=== RBS-SNN stage 4 / BX-4 — the phase-locked read-head (F388 temporal EC) ===")
    print(f"store: giant component {M} findings; read a finding's coupling-row through noise σ\n")
    sigma = 1.0
    print(f"read-noise σ = {sigma:.1f}  |  recall@N(q) and precision, UNLOCKED vs LOCKED:")
    print(f"   {'query':6} {'deg':>4} | {'UNLOCKED (K=0, 1 read)':>24} | {'LOCKED (K=3, W=300)':>22}")
    agg = {'unlock': [], 'lock': []}
    for h in hubs:
        true_idx = {idx[t] for t in adj[h] if t in idx}
        psi = [0.0 if j in true_idx else math.pi for j in range(M)]
        th_u = read_head(psi, sigma, K=0.0, W=0, rng=rng)
        th_l = read_head(psi, sigma, K=3.0, W=300, rng=rng)
        ru, pu = recall(th_u, true_idx, M)
        rl, pl = recall(th_l, true_idx, M)
        agg['unlock'].append(ru)
        agg['lock'].append(rl)
        print(f"   F{h:<5}{len(adj[h]):>4} | recall {ru:.2f}  prec {pu:.2f}        | recall {rl:.2f}  prec {pl:.2f}")
    mu = sum(agg['unlock']) / len(agg['unlock'])
    ml = sum(agg['lock']) / len(agg['lock'])
    print(f"\n   mean recall — UNLOCKED {mu:.2f}  →  LOCKED {ml:.2f}   "
          f"(lock recovers the coupling-set from read-noise)")

    # K-sweep on one hub (F388's K knob = coupling-over-time)
    print(f"\nF388 EC curve — lock strength K vs recall (query F{hubs[0]}, σ={sigma:.1f}):")
    h = hubs[0]
    true_idx = {idx[t] for t in adj[h] if t in idx}
    psi = [0.0 if j in true_idx else math.pi for j in range(M)]
    for K in (0.0, 0.5, 1.0, 2.0, 4.0):
        rr = sum(recall(read_head(psi, sigma, K, 300 if K else 0, random.Random(7 + i)), true_idx, M)[0]
                 for i in range(3)) / 3
        tag = "unlocked (1 read)" if K == 0 else "locked"
        print(f"   K={K:<4} {tag:18}: recall {rr:.2f}")
    print("\n  ⇒ the read-head LOCKS to the stored coupling-fiber and time-averages the read-noise away")
    print("    — bit-exact-ish recall of a finding's couplings from ONE noisy store, on ordinary silicon (F388).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
