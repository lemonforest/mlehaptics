"""LANE 2 part 2 — the DECISIVE in-carrier negative control + capacity crossover.

H  IN-CARRIER ABELIAN CONTROL. Same SHIPPED op (q8_bind / genome_fiber_holonomy),
   but turns drawn from the COMMUTING subgroup <i> = Z4 = {+1,+i,-1,-i} = bytes
   {0,1,4,5}. The fold is then provably order-free. Any candidate that still
   separates orderings here is separating on the PREFIX SUBSET, not on order.

I  SIGN-COCYCLE THEOREM CHECK. Claim: for Q8, reordering can change ONLY the
   center sign, and the flip is
       sign(pi) ^ sign(id) = sum_{a<b inverted by pi} A(a,b)  (mod 2),
       A(a,b) = [idx_a != idx_b AND idx_a != 0 AND idx_b != 0].
   Verified against the SHIPPED genome_fiber_holonomy.

J  CAPACITY CROSSOVER (exact ints). Largest k with k! <= 2^D.

K  POLYMER, non-degenerate leaves.
"""
from __future__ import annotations
import itertools, random, sys
sys.path.insert(0, '/mnt/d/GitHub/mlehaptics/docs/srmech/python')

from srmech.biology.genome import (
    chromosome, genome_fiber_holonomy, ELEMENT_TYPE_Q8, _cap_kind, _hv_bytes,
)
from srmech.biology.q8 import q8_bind, q8_project_v4, q8_from_one
from srmech.amsc.cascade.one import the_one
from srmech.amsc.hv import HV
from srmech.amsc.format import sha256_bytes

import json as _json
def rec(**kw): print(_json.dumps(kw), flush=True)
def nclasses(v): return len(set(v))

def prefixes(turns, LD):
    acc = bytes(LD); out = []
    for t in turns:
        acc = q8_bind(acc, t); out.append(acc)
    return out

def _cand_endpoint(pre, LD):  return pre[-1]
def _cand_cumsign(pre, LD):   return tuple(sum(p[s] >> 2 for p in pre) for s in range(LD))
def _cand_sign_word(pre, LD): return tuple(tuple(p[s] >> 2 for p in pre) for s in range(LD))
def _cand_v4_word(pre, LD):
    v4 = [bytes(q8_project_v4(p)) for p in pre]
    return tuple(tuple(p[s] for p in v4) for s in range(LD))
def _cand_traj(pre, LD):      return tuple(pre)

CANDS = {
    "endpoint":         _cand_endpoint,
    "cumsign":          _cand_cumsign,
    "prefix_sign_word": _cand_sign_word,
    "prefix_v4_word":   _cand_v4_word,
    "trajectory":       _cand_traj,
}

def sha_chain(ts):
    h = b""
    for t in ts:
        h = sha256_bytes(h + bytes(t)).encode("ascii")
    return h


# ── H — IN-CARRIER ABELIAN CONTROL: Q8 turns inside <i> = Z4 ────────────────
def part_h(seed=4242):
    rng = random.Random(seed)
    Z4 = (0, 1, 4, 5)                       # +1, +i, -1, -i  — provably commuting
    for LD in (16, 64):
        for k in (3, 4, 5):
            perms = list(itertools.permutations(range(k)))
            worst = {}
            for _ in range(20):
                ts = [bytes(rng.choice(Z4) for _ in range(LD)) for _ in range(k)]
                # PROVE the control is abelian on this data with the shipped op:
                hs = {genome_fiber_holonomy([ts[i] for i in p], LD) for p in perms}
                assert len(hs) == 1, "control is NOT abelian — bad control data"
                pres = [prefixes([ts[i] for i in p], LD) for p in perms]
                for name, fn in CANDS.items():
                    worst[name] = max(worst.get(name, 0),
                                      nclasses([fn(pre, LD) for pre in pres]))
                worst["sha_chain_EMPTY_CTL"] = max(
                    worst.get("sha_chain_EMPTY_CTL", 0),
                    nclasses([sha_chain([ts[i] for i in p]) for p in perms]))
            for name, n in worst.items():
                rec(part="H_INCARRIER_ABELIAN_CTL", carrier="Q8 turns in <i>=Z4",
                    LD=LD, k=k, kfact=len(perms), cand=name, max_classes=n,
                    verdict=("PROBE BROKEN (separates on a commuting fold)"
                             if n > 1 else "clean"))


# ── I — sign cocycle theorem, checked against the SHIPPED op ────────────────
def part_i(seed=99):
    rng = random.Random(seed)
    for k in (3, 4, 5):
        perms = list(itertools.permutations(range(k)))
        LD = 24
        idx_ok = sign_ok = trials = 0
        for _ in range(30):
            ts = [bytes(rng.randrange(8) for _ in range(LD)) for _ in range(k)]
            base = genome_fiber_holonomy(ts, LD)
            for p in perms:
                h = genome_fiber_holonomy([ts[i] for i in p], LD)
                trials += 1
                # (i) the V4 index is order-INVARIANT
                if bytes(q8_project_v4(h)) == bytes(q8_project_v4(base)):
                    idx_ok += 1
                # (ii) the sign flip == the anticommuting-inversion parity
                inv = [(a, b) for a in range(k) for b in range(a + 1, k)
                       if p.index(a) > p.index(b)]
                pred_ok = True
                for s in range(LD):
                    par = 0
                    for (a, b) in inv:
                        ia, ib = ts[a][s] & 3, ts[b][s] & 3
                        if ia and ib and ia != ib:
                            par ^= 1
                    if ((base[s] >> 2) ^ par) != (h[s] >> 2):
                        pred_ok = False; break
                if pred_ok:
                    sign_ok += 1
        rec(part="I_sign_cocycle", k=k, checks=trials,
            v4_index_order_invariant=idx_ok,
            sign_flip_matches_anticommuting_inversion_parity=sign_ok,
            all_pass=(idx_ok == trials and sign_ok == trials))


# ── J — exact capacity crossover: largest k with k! <= 2^D ──────────────────
def part_j():
    for D in (1, 4, 8, 16, 32, 64, 128, 256, 8192):
        cap = 1 << D
        f, k = 1, 1
        while True:
            nf = f * (k + 1)
            if nf > cap: break
            f = nf; k += 1
        rec(part="J_capacity", leaf_dim_bits=D,
            max_turns_whose_full_order_fits=k,
            note="k! <= 2^D; the endpoint holds exactly D bits of order")
    # what n=40 costs, exact
    f = 1
    for i in range(2, 41): f *= i
    rec(part="J_n40", n=40, log2_40fact_floor=f.bit_length() - 1,
        bits_needed=f.bit_length(),
        note="T979's 159 bits reproduced exactly")


# ── K — POLYMER with non-degenerate leaves ─────────────────────────────────
def part_k(seed=5):
    rng = random.Random(seed)
    LD = 16
    one = q8_from_one(the_one(1, 1, 3, 6), LD)
    for k in (3, 4, 5):
        perms = list(itertools.permutations(range(k)))
        leaves, seen = [], set()
        while len(leaves) < k:
            b = bytes(rng.randrange(8) for _ in range(LD))
            if b not in seen:
                seen.add(b); leaves.append(HV.from_sequence(b, sectors=8))
        sb, sh, bag, ho = [], [], [], []
        for p in perms:
            ch = chromosome([leaves[i] for i in p], one, label="chrP",
                            element_type=ELEMENT_TYPE_Q8)
            data = [_hv_bytes(hv) for hv in ch if _cap_kind(hv) is None]
            flat = b"".join(data)
            sb.append(flat); sh.append(sha256_bytes(flat))
            bag.append(tuple(sorted(data))); ho.append(genome_fiber_holonomy(data, LD))
        rec(part="K_polymer", k=k, kfact=len(perms),
            packed_strand_bytes_classes=nclasses(sb),
            body_sha256_classes=nclasses(sh),
            multiset_bag_classes=nclasses(bag),
            fiber_holonomy_classes=nclasses(ho),
            strand_bytes=len(sb[0]))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "hijk"
    for ch in which:
        {"h": part_h, "i": part_i, "j": part_j, "k": part_k}[ch]()
