#!/usr/bin/env python3
"""rc347 (`#T985`) — the OP LANE axis: generating code for every number the
``describe()["lanes"]`` payload publishes.

Run from ``docs/srmech/python``::

    python3 ../notes/op_lane_axis_rc347.py            # human table
    python3 ../notes/op_lane_axis_rc347.py --ndjson   # the committed record

rc339 published what each CARRIER can DO. This is the complement: what each OP
READS. The Cayley-Dickson product factors into two lanes and every op consumes
one, the other, or both:

    INDEX lane  e_i * e_j -> e_(i XOR j).  ABELIAN, ORDER-BLIND, exact at every
                rung, unbounded.
    SIGN lane   the cocycle over it. ORDER-CARRYING. Every ceiling srmech
                publishes lives here (rc343).

Everything below is MEASURED on the shipped surface. No float, no numpy, no
``abs()`` (a sign is a Class-K pin-slot read composed with Class C).
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

# SCRIPT-MODE path bootstrap. Python puts the SCRIPT's directory on sys.path,
# not the cwd, so `python3 ../notes/op_lane_axis_rc347.py` from python/ would
# import whatever `srmech` a stale user site-packages happens to hold. Pin the
# in-tree package explicitly and say which one was loaded.
_PY_ROOT = Path(__file__).resolve().parent.parent / "python"
sys.path.insert(0, str(_PY_ROOT))

# ── lane projections on a Q8 byte ────────────────────────────────────────
# A Q8 byte is 3 bits: bits 0..1 are the V4 coset (the INDEX lane), bit 2 is
# the center sign (the SIGN lane). That layout is srmech's, not this probe's --
# q8_project_v4 IS `q & 3` and q8_mult documents `s = q >> 2`.
Q8_INDEX = 3
Q8_SIGN = 4


def q8_index(q: int) -> int:
    return q & Q8_INDEX


def q8_sign_bit(q: int) -> int:
    return (q >> 2) & 1


# The two perturbations the admission rule is built on. Each moves exactly one
# lane and provably leaves the other fixed (asserted in `check_perturbations`).
def sigma_flip_q8(q: int) -> int:
    """SIGN-lane perturbation: XOR the center sign bit. Index untouched."""
    return q ^ Q8_SIGN


#: An index RELABEL from Aut(V4) = S3 -- the swap of the i and j axes. It fixes
#: the identity coset 0 (an automorphism must) and transposes 1 <-> 2. It is an
#: automorphism of V4 and is NOT one of Q8: i*j = k but j*i = -k, so a pure
#: relabel of the index bits that leaves the sign bit alone cannot be a Q8
#: automorphism. That is precisely why an ordered Q8 fold responds to it.
_RHO = (0, 2, 1, 3)


def aut_relabel_q8(q: int) -> int:
    """INDEX-lane perturbation: relabel the V4 coset by rho in Aut(V4) = S3.
    Sign bit untouched."""
    return (q & Q8_SIGN) | _RHO[q & Q8_INDEX]


def check_perturbations() -> dict:
    """Prove each perturbation moves ONE lane and fixes the other, over all 8
    Q8 bytes. This is the admission rule's own precondition."""
    sig_sign_moved = sig_index_moved = 0
    rel_sign_moved = rel_index_moved = 0
    for q in range(8):
        s = sigma_flip_q8(q)
        r = aut_relabel_q8(q)
        sig_sign_moved += int(q8_sign_bit(s) != q8_sign_bit(q))
        sig_index_moved += int(q8_index(s) != q8_index(q))
        rel_sign_moved += int(q8_sign_bit(r) != q8_sign_bit(q))
        rel_index_moved += int(q8_index(r) != q8_index(q))
    return {
        "sigma_flip": {"sign_moved": sig_sign_moved, "index_moved": sig_index_moved,
                       "of": 8},
        "aut_relabel": {"sign_moved": rel_sign_moved, "index_moved": rel_index_moved,
                        "of": 8},
    }


# ── M1: the index lane is XOR, at every granularity ──────────────────────
def m1_index_is_xor() -> list:
    """``cd_basis_product`` index == i XOR j, at every CD rung; and the shipped
    ``q8_mult`` abelian projection. The INDEX lane as Z_2^n under XOR."""
    from srmech.amsc.cascade.cayley_dickson import cd_basis_product
    from srmech.biology.q8 import q8_mult

    rows = []
    for dim in (2, 4, 8, 16):
        ok = bad = 0
        for i in range(dim):
            for j in range(dim):
                idx, _sign = cd_basis_product(dim, i, j)
                if idx == (i ^ j):
                    ok += 1
                else:
                    bad += 1
        rows.append({"surface": "cd_basis_product", "dim": dim,
                     "pairs": dim * dim, "index_is_xor": ok, "violations": bad})
    ok = bad = 0
    for a in range(8):
        for b in range(8):
            if q8_index(q8_mult(a, b)) == (q8_index(a) ^ q8_index(b)):
                ok += 1
            else:
                bad += 1
    rows.append({"surface": "q8_mult", "dim": 4, "pairs": 64,
                 "index_is_xor": ok, "violations": bad})
    return rows


# ── M2: chirality touches the SIGN lane only ─────────────────────────────
def m2_chirality_is_sign_only() -> list:
    """Two independent chirality operators over the 64 basis-product slots at
    dim 8, plus Q8. Both move signs; NEITHER moves an index."""
    from srmech.amsc.cascade.cayley_dickson import cd_basis_product
    from srmech.biology.q8 import q8_mult, q8_conjugate

    rows = []

    # (a) ORDER REVERSAL -- the opposite algebra. The purest statement of the
    # lane split: the index lane is order-BLIND, the sign lane order-CARRYING.
    for dim, label in ((4, "H"), (8, "O"), (16, "S")):
        moved = sign_only = index_moved = index_same = 0
        for i in range(dim):
            for j in range(dim):
                ia, sa = cd_basis_product(dim, i, j)
                ib, sb = cd_basis_product(dim, j, i)
                if ia == ib:
                    index_same += 1
                else:
                    index_moved += 1
                if sa != sb:
                    moved += 1
                    if ia == ib:
                        sign_only += 1
        rows.append({"sigma": "order_reversal", "surface": "cd_basis_product",
                     "dim": dim, "algebra": label, "slots": dim * dim,
                     "moved": moved, "moved_sign_only": sign_only,
                     "index_preserved": index_same, "index_moved": index_moved})

    # (b) CONJUGATION -- the shipped Class-C chirality op, applied to both
    # operands.
    dim = 8
    from srmech.amsc.cascade.cayley_dickson import cd_basis, cd_mult, cd_conjugate
    moved = sign_only = index_same = 0
    for i in range(dim):
        for j in range(dim):
            base = cd_mult(cd_basis(dim, i), cd_basis(dim, j))
            flip = cd_mult(cd_conjugate(cd_basis(dim, i)),
                           cd_conjugate(cd_basis(dim, j)))
            bi = [k for k, v in enumerate(base) if v != 0]
            fi = [k for k, v in enumerate(flip) if v != 0]
            if bi == fi:
                index_same += 1
            if base != flip:
                moved += 1
                if bi == fi:
                    sign_only += 1
    rows.append({"sigma": "cd_conjugate", "surface": "cd_mult", "dim": dim,
                 "algebra": "O", "slots": dim * dim, "moved": moved,
                 "moved_sign_only": sign_only, "index_preserved": index_same,
                 "index_moved": dim * dim - index_same})

    moved = sign_only = index_same = 0
    for a in range(8):
        for b in range(8):
            base = q8_mult(a, b)
            flip = q8_mult(q8_conjugate(a), q8_conjugate(b))
            if q8_index(base) == q8_index(flip):
                index_same += 1
            if base != flip:
                moved += 1
                if q8_index(base) == q8_index(flip):
                    sign_only += 1
    rows.append({"sigma": "q8_conjugate", "surface": "q8_mult", "dim": 4,
                 "algebra": "Q8", "slots": 64, "moved": moved,
                 "moved_sign_only": sign_only, "index_preserved": index_same,
                 "index_moved": 64 - index_same})
    return rows


# ── M3: the granularity inversion, 8:4:2 ─────────────────────────────────
#
# *** CONFLATION GUARD ***  The slot counts below are 8 / 4 / 2 for ONE algebra
# (O) re-addressed at three widths. srmech's BLOCK_DIMS (2, 4, 8) are the real
# dims of THREE DIFFERENT algebras (C, H, O). Same three numbers, different
# objects. The payload labels which reading it is; so does this probe.
_GRAN_SLOTS = {
    "R": [[i] for i in range(8)],
    "C": [[0, 1], [2, 3], [4, 5], [6, 7]],
    "H": [[0, 1, 2, 3], [4, 5, 6, 7]],
}
_GRAN_LABELS = {
    "H": ["H_L", "H_R"],
    "C": ["C_LL", "C_LR", "C_RL", "C_RR"],
}


def m3_granularity() -> dict:
    """O addressed over R / C / H: 8 x 1, 4 x 2, 2 x 4 real dims. One index bit
    per doubling step. At every width exactly ONE slot closes -- the one holding
    the identity: 1 anchor + (n-1) torsors."""
    from srmech.amsc.cascade.cayley_dickson import cd_basis_product

    def closes(slot):
        s = set(slot)
        for i in slot:
            for j in slot:
                idx, _ = cd_basis_product(8, i, j)
                if idx not in s:
                    return False
        return True

    widths = []
    for over, slots in (("R", _GRAN_SLOTS["R"]), ("C", _GRAN_SLOTS["C"]),
                        ("H", _GRAN_SLOTS["H"])):
        per = len(slots[0])
        verdicts = [closes(s) for s in slots]
        labels = _GRAN_LABELS.get(over, [f"R_{k}" for k in range(len(slots))])
        widths.append({
            "over": over, "slots": len(slots), "real_dims_per_slot": per,
            "index_bits": (len(slots) - 1).bit_length(),
            "anchor_slots": sum(1 for v in verdicts if v),
            "torsor_slots": sum(1 for v in verdicts if not v),
            "closure": {labels[k]: {"members": slots[k], "closes": verdicts[k]}
                        for k in range(len(slots))},
        })
    return {"algebra": "O", "algebra_real_dim": 8, "widths": widths}


# ── M4: the op lane responses ────────────────────────────────────────────
def _q8_strand(bytes_):
    return bytes(bytes_)


#: Perturb ONE element, not all of them. A whole-buffer sign flip can CANCEL
#: (an even number of sign flips leaves an ordered product's center parity
#: exactly where it started), which reads as "the op ignores the sign lane"
#: when the op is in fact reading it. The minimal single-slot move cannot
#: cancel against itself. Slot 1 is chosen because its coset is 1, so BOTH
#: perturbations genuinely move it (rho fixes coset 0).
_PERTURB_AT = 1


def _perturb_seq(seq, fn, at=_PERTURB_AT):
    out = bytearray(seq)
    out[at] = fn(out[at])
    return bytes(out)


def _perturb_list(seq, fn, at=0):
    out = list(seq)
    out[at] = fn(out[at])
    return out


def _sq_gain(q8_byte):
    """Q8 byte -> unit-quaternion 4-vector, for the qm.quaternion surface."""
    s = -1 if (q8_byte >> 2) & 1 else 1
    x = q8_byte & 3
    v = [0, 0, 0, 0]
    v[x] = s
    return v


#: A generic 6-vertex backbone with a NON-ZERO writhe (-1). Non-zero matters:
#: a writhe-0 embedding is invariant under reflection for the trivial reason,
#: so it cannot witness the sign response and would silently read as
#: "discrete_writhe ignores orientation". Found by search over integer
#: embeddings; committed as a literal so the measurement is reproducible.
_EMB = [(1, 5, 0), (-7, -6, 7), (4, -4, 1), (-5, 6, 4), (-8, -7, 8), (9, 1, 1)]


def _reflect(emb):
    """SIGN-lane perturbation on a GEOMETRY input: reverse orientation by
    reflecting one coordinate. Magnitudes are untouched."""
    return [(-x, y, z) for (x, y, z) in emb]


def _rescale(emb, num, den):
    """The sign-free half of a geometry input: a POSITIVE rational rescale.
    Every magnitude moves; no orientation determinant changes sign."""
    return [(Fraction(x * num, den), Fraction(y * num, den),
             Fraction(z * num, den)) for (x, y, z) in emb]


_RESCALES = ((1, 1), (3, 1), (100, 1), (1, 7), (999, 4))


#: Every element of Aut(V4) = S3. The identity is excluded where a perturbation
#: is required to actually perturb.
RHOS = [(0, 1, 2, 3), (0, 1, 3, 2), (0, 2, 1, 3), (0, 2, 3, 1),
        (0, 3, 1, 2), (0, 3, 2, 1)]


def m5_cwf_field_adjudication(trials: int = 3000, seed: int = 11) -> dict:
    """The Tw / Wr / Lk adjudication, read off the SHIPPED surface.

    ``cwf_consistency_mod2`` is the one shipped op that computes all three, so
    its per-FIELD response under the two perturbations IS the adjudication. A
    SWEEP, not a sample: a single gain vector can miss the Lk index response
    entirely (measured -- the first draw of this probe did, and would have
    published "Lk is index-blind").

    Expected, and what the ratchet asserts:
      Tw  sign lane, ALGEBRA  geometry -> never; index -> never
      Wr  sign lane, GEOMETRY algebra  -> never; index -> never
      Lk  BOTH lanes, ALGEBRA          index -> sometimes.  The only mixer.
    """
    import random
    from srmech.biology import genome as gm

    rng = random.Random(seed)
    fields = ("lk_mod2", "lk_center_parity", "tw_mod2", "wr", "wr_mod2")
    counts = {f: {"sign_algebra": 0, "index_algebra": 0, "sign_geometry": 0}
              for f in fields}

    def cwf(g, emb):
        return gm.cwf_consistency_mod2(
            _EDGES, [_sq_gain(x) for x in g], n=6, embedding=emb)

    ran = 0
    for _ in range(trials):
        g = [rng.randrange(8) for _ in range(6)]
        at = rng.randrange(6)
        rho = RHOS[rng.randrange(1, 6)]
        sig = list(g)
        sig[at] = sigma_flip_q8(sig[at])
        rel = [(x & Q8_SIGN) | rho[x & Q8_INDEX] for x in g]
        base = cwf(g, _EMB)
        a_sig, a_rel = cwf(sig, _EMB), cwf(rel, _EMB)
        a_geo = cwf(g, _reflect(_EMB))
        ran += 1
        for f in fields:
            counts[f]["sign_algebra"] += int(base[f] != a_sig[f])
            counts[f]["index_algebra"] += int(base[f] != a_rel[f])
            counts[f]["sign_geometry"] += int(base[f] != a_geo[f])
    return {"trials": ran, "op": "srmech.biology.genome.cwf_consistency_mod2",
            "fields": counts}


#: A 6-node cycle: exactly one fundamental cycle, which cwf_consistency_mod2
#: requires, and node k indexes _EMB[k].
_EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]


def m4_op_responses(trials: int = 400, seed: int = 5) -> list:
    """Drive every lane-declaring op through both perturbations and record
    whether the OUTPUT moved. This is the executable admission rule.

    SWEPT, not sampled. A single input can fail to move an op that does read
    the lane -- an even number of sign flips cancels in an ordered product, and
    one gain vector in fifteen shows the Lk index response. A "did not respond"
    verdict is only admissible as the verdict over the whole sweep.
    """
    import random
    from srmech.biology import q8 as q8m
    from srmech.biology import genome as gm
    from srmech.qm.quaternion import quaternion_cycle_holonomy

    rng = random.Random(seed)
    one = _q8_strand([1] * 12)

    #: (name, callable over a 12-byte Q8 buffer). Every one of these takes an
    #: input whose sign lane and index lane can BOTH be moved independently --
    #: which is the admission rule. An op whose input carries only one of the
    #: two (``net_chirality`` takes bare orientations; ``cd_basis_product``
    #: takes bare indices) is INADMISSIBLE: no measurement could contradict its
    #: lane, which is exactly the false green rc339's ``bounded_by`` shipped.
    algebra_ops = [
        ("srmech.biology.q8.q8_project_v4", lambda s: q8m.q8_project_v4(s)),
        ("srmech.biology.q8.q8_conjugate",
         lambda s: bytes(q8m.q8_conjugate(b) for b in s)),
        ("srmech.biology.q8.q8_mult",
         lambda s: bytes(q8m.q8_mult(a, b) for a, b in zip(s, one))),
        ("srmech.biology.q8.q8_bind", lambda s: q8m.q8_bind(s, one)),
        ("srmech.biology.genome.genome_fiber_holonomy",
         lambda s: gm.genome_fiber_holonomy(s, leaf_dim=4)),
        ("srmech.biology.genome.codon_read", lambda s: gm.codon_read(s)),
    ]

    tally = {name: {"sign": 0, "index": 0, "trials": 0}
             for name, _ in algebra_ops}
    tally["srmech.qm.quaternion.quaternion_cycle_holonomy"] = {
        "sign": 0, "index": 0, "trials": 0}
    tally["srmech.biology.genome.cwf_consistency_mod2"] = {
        "sign": 0, "index": 0, "trials": 0, "sign_geometry": 0}

    for _ in range(trials):
        strand = bytes(rng.randrange(8) for _ in range(12))
        at = rng.randrange(12)
        rho = RHOS[rng.randrange(1, 6)]
        sig = _perturb_seq(strand, sigma_flip_q8, at)
        rel = bytes((b & Q8_SIGN) | rho[b & Q8_INDEX] for b in strand)
        for name, fn in algebra_ops:
            base = fn(strand)
            tally[name]["trials"] += 1
            tally[name]["sign"] += int(fn(sig) != base)
            tally[name]["index"] += int(fn(rel) != base)

        g = [rng.randrange(8) for _ in range(6)]
        gat = rng.randrange(6)
        gs = _perturb_list(g, sigma_flip_q8, gat)
        gr = [(x & Q8_SIGN) | rho[x & Q8_INDEX] for x in g]
        k = "srmech.qm.quaternion.quaternion_cycle_holonomy"
        b0 = quaternion_cycle_holonomy(_EDGES, [_sq_gain(x) for x in g], n=6)
        tally[k]["trials"] += 1
        tally[k]["sign"] += int(
            quaternion_cycle_holonomy(
                _EDGES, [_sq_gain(x) for x in gs], n=6) != b0)
        tally[k]["index"] += int(
            quaternion_cycle_holonomy(
                _EDGES, [_sq_gain(x) for x in gr], n=6) != b0)

        def cwf(gg, emb):
            return gm.cwf_consistency_mod2(
                _EDGES, [_sq_gain(x) for x in gg], n=6, embedding=emb)

        k = "srmech.biology.genome.cwf_consistency_mod2"
        c0 = cwf(g, _EMB)
        tally[k]["trials"] += 1
        tally[k]["sign"] += int(cwf(gs, _EMB) != c0)
        tally[k]["index"] += int(cwf(gr, _EMB) != c0)
        tally[k]["sign_geometry"] += int(cwf(g, _reflect(_EMB)) != c0)

    rows = [{"op": name, "sign_response": t["sign"] > 0,
             "index_response": t["index"] > 0, **t}
            for name, t in tally.items()]

    # -- the geometry-input op ---------------------------------------------
    base_wr = gm.discrete_writhe(_EMB)
    rows.append({
        "op": "srmech.biology.genome.discrete_writhe",
        "sign_response": gm.discrete_writhe(_reflect(_EMB)) != base_wr,
        "index_response": any(
            gm.discrete_writhe(_rescale(_EMB, nu, de)) != base_wr
            for nu, de in _RESCALES),
        "trials": 1, "sign": 1, "index": 0,
        "base_writhe": list(base_wr["writhe"]),
        "reflected_writhe": list(gm.discrete_writhe(_reflect(_EMB))["writhe"]),
        "rescales_identical": sum(
            1 for nu, de in _RESCALES
            if gm.discrete_writhe(_rescale(_EMB, nu, de))["writhe"]
            == base_wr["writhe"]),
        "rescales": len(_RESCALES),
    })
    return rows


def main(argv) -> int:
    import srmech
    loaded = Path(srmech.__file__).resolve()
    if _PY_ROOT.resolve() not in loaded.parents:
        raise SystemExit(
            f"refusing to measure a srmech that is not the in-tree one: "
            f"loaded {loaded}, expected under {_PY_ROOT}")
    out = {
        "rc": "0.9.0rc347", "task": "T985",
        "srmech_version": srmech.__version__,
        "srmech_file": str(loaded),
        "perturbations": check_perturbations(),
        "m1_index_is_xor": m1_index_is_xor(),
        "m2_chirality_is_sign_only": m2_chirality_is_sign_only(),
        "m3_granularity": m3_granularity(),
        "m4_op_responses": m4_op_responses(),
        "m5_cwf_field_adjudication": m5_cwf_field_adjudication(),
    }
    if "--ndjson" in argv:
        for key in ("m1_index_is_xor", "m2_chirality_is_sign_only",
                    "m4_op_responses"):
            for row in out[key]:
                print(json.dumps({"measurement": key, **row}, sort_keys=True))
        print(json.dumps({"measurement": "m3_granularity",
                          **out["m3_granularity"]}, sort_keys=True))
        print(json.dumps({"measurement": "m5_cwf_field_adjudication",
                          **out["m5_cwf_field_adjudication"]}, sort_keys=True))
        print(json.dumps({"measurement": "perturbations",
                          **out["perturbations"]}, sort_keys=True))
    else:
        print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
