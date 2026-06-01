"""loop_bind_capacity_812.py — MS#21 / issue #812: loop-bind capacity head-to-head vs Klein-4.

Deferred from the gate (F276): does the NON-associative block-octonion loop bind cost capacity
relative to the commutative + associative Klein-4 XOR bind? Both at matched D, M, K-sweep.

Protocol (standard HDC associative-memory capacity): bundle K (key o val) pairs; for each key,
unbind + clean up against the M-item value codebook; accuracy = fraction retrieved. The loop bind
ADDS order/tree/direction (F274); this asks what (if anything) that costs in capacity.

Class-K clean (octonion cleanup via stacked-matrix argmax = cosine; klein4 via native similarity).
Seed attested-B. The loop bind is hand-rolled (srmech has no native octonion product yet, F271 sec-C).
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loop_bind_hd_gate import loop_bind_hd, unbind_hd, rand_unit_blocks, D    # noqa: E402
from srmech.amsc import hdc                                                   # noqa: E402

M = 128          # value codebook size (matched across binds)
TR = 5           # trials
KS = [2, 4, 8, 16, 32, 64, 128]
SEED = 23


def cap_octonion(rng, K):
    accs = []
    for _ in range(TR):
        Vm = np.stack([rand_unit_blocks(rng) for _ in range(M)])
        Vn = Vm / np.linalg.norm(Vm, axis=1, keepdims=True)
        idx = rng.choice(M, size=K, replace=False)
        keys = [rand_unit_blocks(rng) for _ in range(K)]
        bundle = np.sum([loop_bind_hd(keys[i], Vm[idx[i]]) for i in range(K)], axis=0)
        ok = sum(int(np.argmax(Vn @ unbind_hd(keys[i], bundle))) == idx[i] for i in range(K))
        accs.append(ok / K)
    return float(np.mean(accs))


def cap_klein4(K):
    accs = []
    for t in range(TR):
        V = [hdc.klein4_random(D, seed=10_000 + t * 4000 + m) for m in range(M)]
        keys = [hdc.klein4_random(D, seed=9_000_000 + t * 4000 + i) for i in range(K)]
        idx = np.random.default_rng(700 + t).choice(M, size=K, replace=False)
        bundle = hdc.klein4_bundle(*[hdc.klein4_bind(keys[i], V[idx[i]]) for i in range(K)])
        ok = 0
        for i in range(K):
            rec = hdc.klein4_bind(keys[i], bundle)
            best = max(range(M), key=lambda m: hdc.klein4_similarity(rec, V[m]))
            ok += (best == int(idx[i]))
        accs.append(ok / K)
    return float(np.mean(accs))


def knee(curve):
    below = [K for K, a in curve if a < 0.9]
    return below[0] if below else f">{KS[-1]}"


def main():
    rng = np.random.default_rng(SEED)
    print(f"=== capacity head-to-head  (D={D}, M={M} codebook, {TR} trials) ===")
    print(f"  {'K':>4} | {'loop-bind (k=7)':>16} | {'klein4 XOR':>12}")
    oc, kc = [], []
    for K in KS:
        a_o = cap_octonion(rng, K)
        a_k = cap_klein4(K)
        oc.append((K, a_o)); kc.append((K, a_k))
        print(f"  {K:>4} | {a_o:>16.3f} | {a_k:>12.3f}", flush=True)
    print(f"\n  capacity knee (first K with acc<0.9):  loop-bind={knee(oc)}   klein4={knee(kc)}")
    print("\n  Reading: comparable knees => the loop bind carries order/tree/direction (F274)")
    print("  at NO meaningful capacity cost vs the commutative XOR bind. A large gap => a real cost.")


if __name__ == "__main__":
    main()
