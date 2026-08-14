"""LANE 2 part 3 — the REAL wire format (does the polymer exist on disk?) and the
exact capacity law for the fiber endpoint's order channel.

L  genome_save / genome_load round-trip on reordered strands: do the on-disk bytes,
   the manifest body_sha256 (region CHAIN), and genome_load's recovered leaf ORDER
   distinguish all k! orderings? Uses the SHIPPED save/load, not a hand-rolled join.

M  RANK LAW. The endpoint's order channel is the F2 pairing <A_s, inv(pi)>
   (part I, exact). Full k!-separation needs the A_s to span F2^C(k,2). Measure the
   achieved F2 rank of LD random slots for k up to 40 -> the max strand length whose
   ORDER the endpoint can fully hold at a given leaf_dim.
"""
from __future__ import annotations
import itertools, random, sys, tempfile, os
sys.path.insert(0, '/mnt/d/GitHub/mlehaptics/docs/srmech/python')

from srmech.biology import genome as G
from srmech.biology.genome import (
    chromosome, genome_save, genome_load, genome_fiber_holonomy,
    genome_add_fiber, genome_read_fiber,
    ELEMENT_TYPE_Q8, LEAF_CAP, _cap_kind, _hv_bytes,
)
from srmech.biology.q8 import q8_from_one
from srmech.amsc.cascade.one import the_one
from srmech.amsc.hv import HV

import json as _json
def rec(**kw): print(_json.dumps(kw), flush=True)
def nclasses(v): return len(set(v))


# ── L — the REAL wire format ───────────────────────────────────────────────
def part_l(seed=31):
    rng = random.Random(seed)
    LD = 16
    one = q8_from_one(the_one(1, 1, 3, 6), LD)
    rec(part="L_const", LEAF_CAP=LEAF_CAP, GENOME_FORMAT_VERSION=G.GENOME_FORMAT_VERSION)
    for k in (3, 4):
        perms = list(itertools.permutations(range(k)))
        leaves, seen = [], []
        while len(leaves) < k:
            b = bytes(rng.randrange(8) for _ in range(LD))
            if b not in seen:
                seen.append(b); leaves.append(HV.from_sequence(b, sectors=8))
        turns_bin, body_sha, loaded_order, fiber_holo, fiber_cap = [], [], [], [], []
        with tempfile.TemporaryDirectory() as td:
            for n, p in enumerate(perms):
                ch = chromosome([leaves[i] for i in p], one, label="chrW",
                                element_type=ELEMENT_TYPE_Q8)
                d = os.path.join(td, f"g{n}.genome")
                genome_save(ch, d, one, labels=["chrW"], element_type=ELEMENT_TYPE_Q8)
                with open(os.path.join(d, "turns.bin"), "rb") as f:
                    turns_bin.append(f.read())
                import json
                with open(os.path.join(d, "manifest.json")) as f:
                    mf = json.load(f)
                    body_sha.append(mf.get("body_sha256") or mf.get("data", {}).get("body_sha256") or json.dumps(mf, sort_keys=True))
                    if n == 0: rec(part="L_manifest_keys", keys=sorted(mf.keys()))
                back = genome_load(d, coupling=one)
                strand_back = back[0] if isinstance(back, tuple) else back
                loaded_order.append(tuple(bytes(_hv_bytes(x)) for x in strand_back))
                data = [_hv_bytes(hv) for hv in ch if _cap_kind(hv) is None]
                fiber_holo.append(genome_fiber_holonomy(data, LD))
                fib = genome_add_fiber(ch)
                fiber_cap.append(bytes(genome_read_fiber(fib)["holonomy"]))
        rec(part="L_wire", k=k, kfact=len(perms),
            turns_bin_classes=nclasses(turns_bin),
            manifest_body_sha256_classes=nclasses(body_sha),
            genome_load_recovered_order_classes=nclasses(loaded_order),
            fiber_holonomy_classes=nclasses(fiber_holo),
            fiber_CAP_readback_classes=nclasses(fiber_cap),
            turns_bin_bytes=len(turns_bin[0]))


# ── M — exact F2 rank law for the endpoint's order channel ─────────────────
def _f2_rank(rows, ncols):
    """Exact GF(2) rank via int bitmasks. Class-I/Class-K only; no floats."""
    basis = []
    for r in rows:
        for b in basis:
            r = min(r, r ^ b) if False else (r ^ b if (r ^ b) < r else r)
        if r:
            basis.append(r); basis.sort(reverse=True)
    return len(basis)

def _rank_gf2(rows):
    piv = {}
    rank = 0
    for r in rows:
        cur = r
        while cur:
            h = cur.bit_length() - 1
            if h in piv:
                cur ^= piv[h]
            else:
                piv[h] = cur; rank += 1; break
    return rank

def part_m(seed=77):
    rng = random.Random(seed)
    for k in (3, 4, 5, 8, 11, 12, 20, 40):
        C = k * (k - 1) // 2
        pairs = list(itertools.combinations(range(k), 2))
        pidx = {p: i for i, p in enumerate(pairs)}
        for LD in (16, 64, 8192):
            # each slot = a random 4-colouring of the k turns; its A_s row is the
            # "distinct-and-both-nonzero" pair indicator
            best = 0
            for _ in range(5):
                rows = []
                for _s in range(LD):
                    col = [rng.randrange(4) for _ in range(k)]
                    m = 0
                    for (a, b) in pairs:
                        ca, cb = col[a], col[b]
                        if ca and cb and ca != cb:
                            m |= 1 << pidx[(a, b)]
                    rows.append(m)
                best = max(best, _rank_gf2(rows))
            rec(part="M_rank", k=k, C_k_2=C, leaf_dim=LD, achieved_f2_rank=best,
                full_order_channel=(best == C))
    # the exact law: largest k with C(k,2) <= leaf_dim
    for LD in (16, 32, 64, 128, 256, 8192):
        k = 1
        while (k + 1) * k // 2 <= LD:
            k += 1
        # k now smallest failing; largest passing is k-1... recompute cleanly
        best = max(n for n in range(1, 4000) if n * (n - 1) // 2 <= LD)
        rec(part="M_law", leaf_dim=LD, max_turns_fiber_endpoint_fully_orders=best,
            note="largest n with C(n,2) <= leaf_dim")


if __name__ == "__main__":
    for ch in (sys.argv[1] if len(sys.argv) > 1 else "lm"):
        {"l": part_l, "m": part_m}[ch]()
