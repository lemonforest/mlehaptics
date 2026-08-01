"""LANE 2 — fossil-as-sequence probe. Exact ints only; no floats, no numpy, no abs().

Subject = SHIPPED srmech ops:
  genome.quad_turn                  (base / per-position deposit)
  genome.genome_fiber_holonomy      (Q8 ordered fold ENDPOINT)
  genome.genome_octonion_holonomy   (O ordered fold ENDPOINT)
  genome.genome_octonion_associator (1-bit defect)
  q8.q8_bind / octonion.oct_bind    (the same folds, used to build PREFIXES)
  amsc.format.sha256_bytes          (Class A, the EMPTY control)
  signal_processing.rbs_hdc_instrument.mint_cascade_composition

Hand-rolled code is LABELLED ORACLE only.
"""
from __future__ import annotations
import itertools, random, sys, os
sys.path.insert(0, '/mnt/d/GitHub/mlehaptics/docs/srmech/python')

from srmech.biology import genome as G
from srmech.biology.genome import (
    quad_turn, chromosome, genome_fiber_holonomy,
    genome_octonion_holonomy, genome_octonion_associator,
    ELEMENT_TYPE_Q8, ELEMENT_TYPE_KLEIN4, ELEMENT_TYPE_OCTONION,
    _cap_kind, _hv_bytes,
)
from srmech.biology.q8 import q8_bind, q8_project_v4, q8_from_one
from srmech.amsc.octonion import oct_bind
from srmech.amsc.hdc import klein4_from_one
from srmech.amsc.cascade.one import the_one
from srmech.amsc.hv import HV
from srmech.amsc.format import sha256_bytes

OUT = []
import json as _json
def rec(**kw):
    OUT.append(kw)
    print(_json.dumps(kw), flush=True)


# ── candidate records (each returns a hashable "record" for one ordering) ────
def cand_endpoint_q8(turns, LD):
    return genome_fiber_holonomy(turns, LD)

def cand_trajectory_q8(turns, LD):
    acc = bytes(LD); out = []
    for t in turns:
        acc = q8_bind(acc, t); out.append(acc)
    return tuple(out)

def cand_prefix_sign_word_q8(turns, LD):
    """per slot, the k-bit word of prefix CENTER SIGNS. k*LD bits."""
    acc = bytes(LD); cols = [[] for _ in range(LD)]
    for t in turns:
        acc = q8_bind(acc, t)
        for s in range(LD):
            cols[s].append(acc[s] >> 2)
    return tuple(tuple(c) for c in cols)

def cand_cumsign_q8(turns, LD):
    """per slot, the INTEGER count of prefix center-signs. ceil(log2(k+1))*LD bits."""
    acc = bytes(LD); c = [0] * LD
    for t in turns:
        acc = q8_bind(acc, t)
        for s in range(LD):
            c[s] += (acc[s] >> 2)
    return tuple(c)

def cand_prefix_v4_word_q8(turns, LD):
    """per slot, the k-symbol word of prefix V4 INDICES (sign DROPPED). 2k*LD bits."""
    acc = bytes(LD); cols = [[] for _ in range(LD)]
    for t in turns:
        acc = q8_bind(acc, t)
        v4 = bytes(q8_project_v4(acc))
        for s in range(LD):
            cols[s].append(v4[s])
    return tuple(tuple(c) for c in cols)

def cand_base_bag(stored):
    return tuple(sorted(stored))

def cand_base_positional(stored):
    return tuple(stored)

def cand_sha_chain(turns):
    """EMPTY CONTROL — Class A prefix hash chain. Separates all k! BY CONSTRUCTION."""
    h = b""
    for t in turns:
        h = sha256_bytes(h + bytes(t)).encode("ascii")
    return h


def nclasses(vals):
    return len({v for v in vals})


# ═══ PART A — random Q8 data, endpoint vs prefix candidates, k=3,4,5 ═══════
def part_a(seed=20260729):
    rng = random.Random(seed)
    for LD in (1, 2, 4, 8, 16, 64):
        for k in (3, 4, 5):
            trials = 40
            tallies = {}
            for _ in range(trials):
                turns = [bytes(rng.randrange(8) for _ in range(LD)) for _ in range(k)]
                perms = list(itertools.permutations(range(k)))
                for name, fn in (
                    ("endpoint", cand_endpoint_q8),
                    ("cumsign", cand_cumsign_q8),
                    ("prefix_sign_word", cand_prefix_sign_word_q8),
                    ("prefix_v4_word", cand_prefix_v4_word_q8),
                    ("trajectory", cand_trajectory_q8),
                ):
                    n = nclasses([fn([turns[i] for i in p], LD) for p in perms])
                    tallies.setdefault(name, []).append(n)
                n = nclasses([cand_sha_chain([turns[i] for i in p]) for p in perms])
                tallies.setdefault("sha_chain_EMPTY_CTL", []).append(n)
            for name, xs in tallies.items():
                rec(part="A", carrier="Q8", LD=LD, k=k, kfact=len(perms),
                    cand=name, min=min(xs), max=max(xs),
                    full=sum(1 for x in xs if x == len(perms)), trials=trials)


# ═══ PART B — NEGATIVE CONTROL: klein4 (provably commuting) ════════════════
def part_b(seed=20260729):
    rng = random.Random(seed)
    one4 = None
    LD = 16
    for k in (3, 4, 5):
        perms = list(itertools.permutations(range(k)))
        worst = {}
        for _ in range(40):
            turns = [bytes(rng.randrange(4) for _ in range(LD)) for _ in range(k)]
            # klein4 fold = XOR (abelian). Build the SAME candidate shapes.
            def k4_prefixes(ts):
                acc = bytes(LD); out = []
                for t in ts:
                    acc = bytes(a ^ b for a, b in zip(acc, t)); out.append(acc)
                return out
            for name, fn in (
                ("endpoint", lambda ts: k4_prefixes(ts)[-1]),
                ("cumsign", lambda ts: tuple(
                    sum(p[s] >> 1 for p in k4_prefixes(ts)) for s in range(LD))),
                ("prefix_sign_word", lambda ts: tuple(
                    tuple(p[s] >> 1 for p in k4_prefixes(ts)) for s in range(LD))),
                ("trajectory", lambda ts: tuple(k4_prefixes(ts))),
            ):
                n = nclasses([fn([turns[i] for i in p]) for p in perms])
                worst[name] = max(worst.get(name, 0), n)
            n = nclasses([cand_sha_chain([turns[i] for i in p]) for p in perms])
            worst["sha_chain_EMPTY_CTL"] = max(worst.get("sha_chain_EMPTY_CTL", 0), n)
        for name, n in worst.items():
            rec(part="B_negctl", carrier="KLEIN4_abelian", LD=LD, k=k,
                kfact=len(perms), cand=name, max_classes=n)


# ═══ PART C — ADVERSARIAL: every slot carries the SAME anticommutation pattern
# (this is where the endpoint is provably capped at 2 classes; does any
#  intermediate record beat it?)
def part_c():
    for k in (3, 4, 5):
        perms = list(itertools.permutations(range(k)))
        LD = 64
        # all k turns pairwise ANTICOMMUTE in every slot: cycle indices 1,2,3,1,2...
        # (repeats COMMUTE, so k>3 cannot be fully pairwise-anticommuting; report it)
        idx = [1 + (t % 3) for t in range(k)]
        turns = [bytes([idx[t]] * LD) for t in range(k)]
        for name, fn in (
            ("endpoint", cand_endpoint_q8),
            ("cumsign", cand_cumsign_q8),
            ("prefix_sign_word", cand_prefix_sign_word_q8),
            ("prefix_v4_word", cand_prefix_v4_word_q8),
            ("trajectory", cand_trajectory_q8),
        ):
            n = nclasses([fn([turns[i] for i in p], LD) for p in perms])
            rec(part="C_adversarial_uniform_slots", carrier="Q8", LD=LD, k=k,
                kfact=len(perms), cand=name, classes=n, turn_indices=idx)


# ═══ PART D — how many SLOTS does the endpoint need to separate all k! ? ════
# theory: sign(pi) per slot = <A_s, inv(pi)> over F2, A_s(a,b)=[idx_a!=idx_b,
# both nonzero]. Singleton-edge A is reachable (colour a=1,b=2, rest 0), so the
# A_s SPAN all of F2^C(k,2) -> LD >= C(k,2) suffices for FULL separation.
def part_d():
    for k in (3, 4, 5):
        perms = list(itertools.permutations(range(k)))
        C = k * (k - 1) // 2
        # construct the SINGLETON-EDGE slot basis: one slot per pair
        pairs = list(itertools.combinations(range(k), 2))
        cols = []
        for (a, b) in pairs:
            col = [0] * k
            col[a] = 1; col[b] = 2
            cols.append(col)
        LD = len(cols)
        turns = [bytes(cols[s][t] for s in range(LD)) for t in range(k)]
        n = nclasses([cand_endpoint_q8([turns[i] for i in p], LD) for p in perms])
        rec(part="D_edge_basis", carrier="Q8", k=k, kfact=len(perms),
            LD=LD, C_k_2=C, cand="endpoint", classes=n,
            note="LD == C(k,2) singleton-edge slots")
        # and the MINIMUM LD reached by random draws
        rng = random.Random(7)
        best = None
        for LD2 in range(1, C + 2):
            hits = 0
            for _ in range(200):
                ts = [bytes(rng.randrange(8) for _ in range(LD2)) for _ in range(k)]
                if nclasses([cand_endpoint_q8([ts[i] for i in p], LD2)
                             for p in perms]) == len(perms):
                    hits += 1
            if hits and best is None:
                best = LD2
            rec(part="D_random_LD_sweep", carrier="Q8", k=k, LD=LD2,
                full_sep_of_200=hits)
        rec(part="D_min_LD", carrier="Q8", k=k, min_LD_with_any_full_sep=best,
            C_k_2=C)


# ═══ PART E — OCTONION rung: endpoint + associator ═════════════════════════
def part_e(seed=11):
    rng = random.Random(seed)
    for LD in (1, 4, 16, 64):
        for k in (3, 4, 5):
            perms = list(itertools.permutations(range(k)))
            tal = {}
            for _ in range(30):
                turns = [bytes(rng.randrange(16) for _ in range(LD)) for _ in range(k)]
                for name, fn in (
                    ("oct_endpoint", genome_octonion_holonomy),
                    ("oct_associator", genome_octonion_associator),
                ):
                    n = nclasses([bytes(fn([turns[i] for i in p], LD)) for p in perms])
                    tal.setdefault(name, []).append(n)
            for name, xs in tal.items():
                rec(part="E", carrier="OCT", LD=LD, k=k, kfact=len(perms),
                    cand=name, min=min(xs), max=max(xs),
                    full=sum(1 for x in xs if x == len(perms)))


# ═══ PART F — DOES THE POLYMER EXIST? the packed strand + its content address
def part_f():
    LD = 16
    one = q8_from_one(the_one(1, 1, 3, 6), LD)
    for k in (3, 4, 5):
        perms = list(itertools.permutations(range(k)))
        leaves = [HV.from_sequence(bytes([(1 + 2 * j + i) % 8 for i in range(LD)]),
                                   sectors=8) for j in range(k)]
        strand_bytes, body_sha, bags, holos = [], [], [], []
        for p in perms:
            ch = chromosome([leaves[i] for i in p], one, label="chrP",
                            element_type=ELEMENT_TYPE_Q8)
            data = [_hv_bytes(hv) for hv in ch if _cap_kind(hv) is None]
            flat = b"".join(data)
            strand_bytes.append(flat)
            body_sha.append(sha256_bytes(flat))
            bags.append(tuple(sorted(data)))
            holos.append(genome_fiber_holonomy(data, LD))
        rec(part="F_polymer", k=k, kfact=len(perms),
            packed_strand_bytes_classes=nclasses(strand_bytes),
            body_sha256_classes=nclasses(body_sha),
            multiset_bag_classes=nclasses(bags),
            fiber_holonomy_classes=nclasses(holos),
            bytes_per_ordering=len(strand_bytes[0]))


# ═══ PART G — mint_cascade_composition ordered= (item 4) ═══════════════════
def part_g():
    from srmech.signal_processing.rbs_hdc_instrument import mint_cascade_composition
    for k, cls in ((3, "ACK"), (4, "ACKM"), (5, "ACKML")):
        perms = list(itertools.permutations(cls))
        for ordered in (False, True):
            n = nclasses([mint_cascade_composition(list(p), D=8192, ordered=ordered)
                          for p in perms])
            rec(part="G_mint_cascade", k=k, kfact=len(perms),
                ordered=ordered, classes=n)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    fns = {"a": part_a, "b": part_b, "c": part_c, "d": part_d,
           "e": part_e, "f": part_f, "g": part_g}
    if which == "all":
        for f in fns.values():
            f()
    else:
        for ch in which:
            fns[ch]()
