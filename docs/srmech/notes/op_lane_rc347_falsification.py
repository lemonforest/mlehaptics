"""rc347 (`#T985`) — the falsification harness for the missing-lane defect.

WHY THIS FILE EXISTS
--------------------
rc347 adds a ratchet asserting that a declared lane must be one a perturbation
can CONTRADICT. A ratchet that has not been run against the tree it targets is
not proven — and ``tests/test_op_lane_rc347.py`` cannot itself be run against
``origin/main``: it imports ``LANES`` / ``LANE_INPUTS`` and reads
``ToolEntry.reads_lane``, none of which main has, so it would ERROR ON IMPORT
rather than FAIL on the defect. **An import error proves nothing about whether
the rule detects anything.**

So the rule is factored out here against NOTHING BUT SURFACES MAIN ALREADY
PUBLISHES — ``describe()``, ``get_tool_schema()``, ``q8.*``, ``genome.*``,
``qm.quaternion.*``, ``cascade.cayley_dickson.cd_basis_product`` — and run
against both trees.

THE RULE
--------
An op's LANE is measurable on the shipped surface: perturb its input's SIGN
lane alone (XOR the Q8 center bit / reverse orientation) and its INDEX lane
alone (relabel the V4 coset by an element of ``Aut(V4) = S3`` / rescale by a
positive rational), and see which perturbation moves the output.

  1. If an op HAS a measurable lane, ``describe()`` must REPORT it. A lane that
     is a fact about the shipped op and appears nowhere in the self-description
     is the same defect class rc298/rc339/rc343 removed one layer at a time:
     introspection silent on a property that binds the caller.
  2. If ``describe()`` reports a lane, the REPORT MUST MATCH THE MEASUREMENT.
     A declared lane no measurement can contradict is rc339's
     ``bounded_by: "associativity"`` in a new place.

Rule 1 is what fires on main. Rule 2 is what protects rc347 from becoming the
next rc339 — it is exercised in ``--selftest`` mode, which injects a
deliberately WRONG declaration and requires the rule to catch it. A rule that
has only ever seen correct data has not been shown to discriminate.

USAGE
-----
    cd docs/srmech/python && PYTHONPATH=$PWD python3 \\
        ../notes/op_lane_rc347_falsification.py
    ... --selftest      # also prove the rule catches a wrong declaration

Exit 0 if the payload satisfies the rule, 1 if it violates it. Against clean
``origin/main`` (ea71fcbc3) it exits 1; against rc347+, 0.

No float, no numpy, no ``abs()``.
"""
from __future__ import annotations

import itertools
import random
import sys
from fractions import Fraction

from srmech.biology import genome as G
from srmech.biology import q8 as Q
from srmech.amsc.cascade.cayley_dickson import cd_basis_product
from srmech.amsc.tool_schema import get_tool_schema, warmup_all
from srmech.introspect import describe
from srmech.qm.quaternion import quaternion_cycle_holonomy

Q8_INDEX, Q8_SIGN = 3, 4
RHOS = [(0,) + p for p in itertools.permutations((1, 2, 3))]
EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]
EMB = [(1, 5, 0), (-7, -6, 7), (4, -4, 1), (-5, 6, 4), (-8, -7, 8), (9, 1, 1)]
RESCALES = ((1, 1), (3, 1), (100, 1), (1, 7), (999, 4))
ONE12 = bytes([1] * 12)


def sigma(q):
    return q ^ Q8_SIGN


def relabel(q, rho):
    return (q & Q8_SIGN) | rho[q & Q8_INDEX]


def gain(q):
    s = -1 if (q >> 2) & 1 else 1
    v = [0, 0, 0, 0]
    v[q & Q8_INDEX] = s
    return v


def reflect(emb):
    return [(-x, y, z) for (x, y, z) in emb]


def rescale(emb, n, d):
    return [(Fraction(x * n, d), Fraction(y * n, d), Fraction(z * n, d))
            for (x, y, z) in emb]


def cwf(g, emb):
    return G.cwf_consistency_mod2(EDGES, [gain(x) for x in g], n=6,
                                  embedding=emb)


DRIVERS = {
    "srmech.biology.q8.q8_project_v4": ("algebra", Q.q8_project_v4),
    "srmech.biology.q8.q8_conjugate":
        ("algebra", lambda s: bytes(Q.q8_conjugate(b) for b in s)),
    "srmech.biology.q8.q8_mult":
        ("algebra", lambda s: bytes(Q.q8_mult(a, b) for a, b in zip(s, ONE12))),
    "srmech.biology.q8.q8_bind": ("algebra", lambda s: Q.q8_bind(s, ONE12)),
    "srmech.biology.genome.genome_fiber_holonomy":
        ("algebra", lambda s: G.genome_fiber_holonomy(s, leaf_dim=4)),
    "srmech.biology.genome.codon_read": ("algebra", G.codon_read),
    "srmech.qm.quaternion.quaternion_cycle_holonomy":
        ("gains",
         lambda g: quaternion_cycle_holonomy(EDGES, [gain(x) for x in g], n=6)),
    "srmech.biology.genome.cwf_consistency_mod2": ("gains+geometry", None),
    "srmech.biology.genome.discrete_writhe": ("geometry", G.discrete_writhe),
}


def measure(kind, fn, trials=120, seed=347):
    """(sign_moved, index_moved) over a SWEEP. Never a single sample: an even
    number of sign flips cancels inside an ordered product, and roughly one
    gain vector in fifteen exposes the Lk index response."""
    rng = random.Random(seed)
    sm = im = False
    if kind == "geometry":
        base = fn(EMB)
        return (fn(reflect(EMB)) != base,
                any(fn(rescale(EMB, n, d)) != base for n, d in RESCALES))
    for _ in range(trials):
        rho = RHOS[rng.randrange(1, 6)]
        if kind == "algebra":
            b = bytes(rng.randrange(8) for _ in range(12))
            s = bytearray(b)
            at = rng.randrange(12)
            s[at] = sigma(s[at])
            base = fn(b)
            sm = sm or fn(bytes(s)) != base
            im = im or fn(bytes(relabel(x, rho) for x in b)) != base
        elif kind == "gains":
            g = [rng.randrange(8) for _ in range(6)]
            s = list(g)
            at = rng.randrange(6)
            s[at] = sigma(s[at])
            base = fn(g)
            sm = sm or fn(s) != base
            im = im or fn([relabel(x, rho) for x in g]) != base
        else:
            g = [rng.randrange(8) for _ in range(6)]
            s = list(g)
            at = rng.randrange(6)
            s[at] = sigma(s[at])
            base = cwf(g, EMB)
            sm = sm or cwf(s, EMB) != base or cwf(g, reflect(EMB)) != base
            im = im or cwf([relabel(x, rho) for x in g], EMB) != base
        if sm and im:
            break
    return sm, im


def lane_of(sm, im):
    if sm and im:
        return "both"
    if sm:
        return "sign"
    if im:
        return "index"
    return None


def reported_lanes(payload):
    """Whatever the payload says about op lanes, tolerant of a tree that has
    no such key at all — which is precisely the main case."""
    return {k: v.get("lane") for k, v in
            payload.get("lanes", {}).get("ops", {}).items()}


def main(argv) -> int:
    warmup_all()
    payload = describe()
    reported = reported_lanes(payload)
    schema = get_tool_schema()
    registered = {t.name for t in schema.tools}

    print("srmech %s — %d registered tools" %
          (payload["srmech_version"], len(schema.tools)))
    print("describe() top-level keys: %s" % ", ".join(sorted(payload)))
    print("describe()['lanes'] present: %s\n"
          % ("YES" if "lanes" in payload else "NO"))

    violations = []
    measured = {}
    print("%-52s %-9s %-9s %s" % ("op", "MEASURED", "REPORTED", "verdict"))
    print("-" * 88)
    for name in sorted(DRIVERS):
        if name not in registered:
            print("%-52s %s" % (name, "NOT REGISTERED — skipped"))
            continue
        kind, fn = DRIVERS[name]
        sm, im = measure(kind, fn)
        lane = lane_of(sm, im)
        measured[name] = lane
        rep = reported.get(name)
        if lane is None:
            verdict = "no measurable lane (not admissible)"
        elif rep is None:
            verdict = "VIOLATION rule 1 — measurable, UNREPORTED"
            violations.append((name, lane, rep, "rule 1"))
        elif rep != lane:
            verdict = "VIOLATION rule 2 — reported %r, measures %r" % (rep, lane)
            violations.append((name, lane, rep, "rule 2"))
        else:
            verdict = "ok"
        print("%-52s %-9s %-9s %s" % (name, lane, rep or "-", verdict))

    # The geometry-side sign check, independent of any payload key.
    base = G.discrete_writhe(EMB)["writhe"]
    same = sum(1 for n, d in RESCALES
               if G.discrete_writhe(rescale(EMB, n, d))["writhe"] == base)
    mirror = G.discrete_writhe(reflect(EMB))["writhe"]
    print("\ndiscrete_writhe magnitude-blindness: %d/%d scales identical "
          "(W=%s); reflection -> %s" % (same, len(RESCALES), base, mirror))

    # The index lane, at every granularity — true on both trees, reported on
    # neither before rc347.
    xor_ok = all(cd_basis_product(d, i, j)[0] == (i ^ j)
                 for d in (2, 4, 8, 16) for i in range(d) for j in range(d))
    print("index == XOR at dims 2/4/8/16: %s" % ("0 violations" if xor_ok
                                                 else "VIOLATED"))

    if "--selftest" in argv:
        print("\n--- selftest: does rule 2 catch a WRONG declaration? ---")
        wrong = dict(reported)
        wrong["srmech.biology.genome.discrete_writhe"] = "index"
        wrong["srmech.biology.q8.q8_project_v4"] = "sign"
        caught = [n for n, lane in measured.items()
                  if lane is not None and wrong.get(n) not in (None, lane)]
        print("injected 2 mis-declarations; rule 2 caught %d: %s"
              % (len(caught), sorted(caught)))
        if len(caught) != 2:
            print("SELFTEST FAILED — the rule does not discriminate")
            return 1
        print("selftest OK — the rule discriminates")

    print("\n%d violation(s)" % len(violations))
    for name, lane, rep, which in violations:
        print("  %s: %s — measures %r, payload says %r"
              % (which, name, lane, rep))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
