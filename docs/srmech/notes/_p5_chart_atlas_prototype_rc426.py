#!/usr/bin/env python3
"""P5 — the CARRIER + TRANSLATOR prototype: many charts, one object
(rc426 research spike, read-only; nothing here is proposed for the wheel
as-is — it exists to COST the ops and to run the falsifiers on a real
implementation rather than on a description of one).

THE DESIGN, STATED BEFORE IT IS BUILT
=====================================
CARRIER (frame-free — holds what every notation shares):

    a TORSOR (S, G, int) where G is the interval group and S carries NO
    distinguished origin.  The ONLY carrier datum is ``int: S x S -> G``.
    G is a PARAMETER: ℤ (register-carrying), ℤ/n (octave-equivalent, ANY n),
    ℤ^k (a rank-k just lattice), or a non-abelian group.  Nothing in the
    carrier may name 12, or 7, or a letter, or a staff.

CHART (convention — holds what one notation does):

    a 4-tuple (origin, alphabet, rho, modifier) where
      origin   in S      -- THE CLEF.  Pure convention; carries no interval.
      alphabet           -- the symbols this notation writes
      rho: alphabet -> G -- what each symbol means as a displacement
      modifier           -- an optional second map (accidental-like)

TRANSLATOR: chart -> carrier is ``rho`` composed with the origin; carrier ->
chart is its (possibly multi-valued) inverse.  The losslessness of EACH
DIRECTION is measured, never assumed.

⚠️ **THE CHART FAMILIES BELOW ARE STRUCTURAL, NOT CULTURAL.**  They are named
by what they DO (positional / differential / action-indexed), deliberately NOT
after any musical tradition.  Mapping a real tradition onto a family is a
CITATION question and is not answered here.  Modelling "a Western-notation
chart" as the reference chart would privilege Western notation, which is the
one thing this design exists to avoid, so the reference chart is the EMPTY
one: identity on the carrier.

Pre-registered falsifiers
=========================
F13 Every chart must round-trip chart->carrier->chart LOSSLESSLY on its own
    alphabet (otherwise it is not a chart of this carrier).
F14 Every chart must agree with every OTHER chart on INTERVALS (that is what
    it means for them to be charts of ONE object).  Disagreement refutes the
    atlas.
F15 The carrier must be blind to which chart is "first": permuting the chart
    registry must not change any carrier-level answer.
F16 NEGATIVE CONTROL — a deliberately WRONG chart must fail F14.
F17 NEGATIVE CONTROL — a chart over the WRONG GROUP (different n) must fail.

Run:
    PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_p5_chart_atlas_prototype_rc426.py
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import srmech
from srmech.cascade import cyclic_mod_add
from srmech.math.covering import center_lift, lift_fibre

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_p5_chart_atlas_prototype_rc426.ndjson")
RECS = []


def emit(**kw):
    kw.setdefault("srmech_version", srmech.__version__)
    RECS.append(kw)


# ══════════════════════════════════════════════════════════════════════════
# THE CARRIER.  Note what is NOT here: no 12, no 7, no letter, no staff, no
# default.  ``n`` is required and has no default value, deliberately — a
# default modulus IS a privileged frame.
# ══════════════════════════════════════════════════════════════════════════
class Carrier:
    """A cyclic-interval torsor.  ``n = 0`` spells the ℤ (register-carrying)
    carrier, matching :data:`srmech.math.covering.UNIVERSAL`."""

    def __init__(self, n):
        if not isinstance(n, int) or n < 0:
            raise ValueError("Carrier: n must be a non-negative int "
                             "(0 = the register-carrying ℤ carrier); "
                             "there is NO DEFAULT, because a default modulus "
                             "is a privileged frame")
        self.n = n

    def int_(self, a, b):
        """int(a,b) — the unique g with a·g = b.  The ONLY carrier datum."""
        return (b - a) if self.n == 0 else cyclic_mod_add(b, self.n - (a % self.n),
                                                          self.n)

    def act(self, a, g):
        return (a + g) if self.n == 0 else cyclic_mod_add(a % self.n,
                                                          g % self.n, self.n)

    def __repr__(self):
        return f"Carrier(n={self.n or 'Z'})"


# ══════════════════════════════════════════════════════════════════════════
# THE CHART.  origin is the CLEF.
# ══════════════════════════════════════════════════════════════════════════
class Chart:
    def __init__(self, name, family, carrier, origin, alphabet, rho,
                 modifiers=(0,)):
        self.name, self.family = name, family
        self.carrier, self.origin = carrier, origin
        self.alphabet, self.rho = tuple(alphabet), dict(rho)
        self.modifiers = tuple(modifiers)

    def symbols(self):
        return [(a, m) for a in self.alphabet for m in self.modifiers]

    def write(self, sym):
        """chart -> carrier."""
        a, m = sym
        return self.carrier.act(self.origin, self.rho[a] + m)

    def read(self, value):
        """carrier -> chart.  MULTI-VALUED by construction — the whole point."""
        return [s for s in self.symbols() if self.write(s) == value]

    def chart_interval(self, s1, s2):
        """The interval computed INSIDE the chart, without leaving it."""
        return self.carrier.int_(self.write(s1), self.write(s2))


def main() -> int:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    try:
        import numpy  # noqa: F401
        print("!! numpy PRESENT — environment wrong")
    except ImportError:
        print("numpy              = ABSENT (correct)")

    C12 = Carrier(12)
    C24 = Carrier(24)
    CZ = Carrier(0)

    # ── the chart registry.  Structural families only; NO tradition named. ──
    charts = [
        # the REFERENCE chart is the EMPTY one: identity on the carrier, no
        # alphabet of its own.  Making any real notation the reference would
        # privilege it.
        Chart("identity", "reference (no convention at all)", C12, 0,
              range(12), {i: i for i in range(12)}),
        # POSITIONAL-ABSOLUTE: k symbols mapped to fixed displacements, plus a
        # modifier group.  k=7 with modifiers is ONE instance of this family.
        Chart("positional-7+mod", "positional-absolute", C12, 0,
              range(7), dict(enumerate((0, 2, 4, 5, 7, 9, 11))),
              modifiers=(-2, -1, 0, 1, 2)),
        # the SAME family at a different k and a different rho — proving the
        # family is not the 7-degree map.
        Chart("positional-5", "positional-absolute", C12, 0,
              range(5), dict(enumerate((0, 2, 4, 7, 9)))),
        # POSITIONAL-RELATIVE: identical structure, MOVED ORIGIN.  This is a
        # different CHART of the same carrier, not a different carrier.
        Chart("positional-7@origin7", "positional-relative (moved origin)",
              C12, 7, range(7), dict(enumerate((0, 2, 4, 5, 7, 9, 11))),
              modifiers=(-2, -1, 0, 1, 2)),
        # a chart on a DIFFERENT carrier modulus — deliberately included so
        # F14 has something it must REFUSE to atlas with.
        Chart("positional-7@24", "positional-absolute (n=24)", C24, 0,
              range(7), dict(enumerate((0, 4, 8, 10, 14, 18, 22))),
              modifiers=(-2, -1, 0, 1, 2)),
    ]

    print("\n      chart                      family                              "
          "carrier  origin  |alphabet|  |modifiers|  |symbols|")
    for c in charts:
        print(f"      {c.name:26s} {c.family:36s} {c.carrier!s:12s} "
              f"{c.origin:5d}  {len(c.alphabet):9d}  {len(c.modifiers):10d}  "
              f"{len(c.symbols()):8d}")
    emit(finding="P5_chart_registry",
         charts=[{"name": c.name, "family": c.family, "carrier_n": c.carrier.n,
                  "origin": c.origin, "alphabet_size": len(c.alphabet),
                  "modifier_size": len(c.modifiers),
                  "symbol_count": len(c.symbols())} for c in charts],
         note="Structural families only. No musical tradition is named or "
              "claimed here; mapping traditions onto families is a CITATION "
              "question answered elsewhere. The REFERENCE chart is the empty "
              "one, so no real notation sits at the origin of the atlas.")

    # ── F13 — per-chart round trip ────────────────────────────────────────
    print("\nF13   per-chart round trip  chart -> carrier -> chart")
    rows = []
    for c in charts:
        tot = len(c.symbols())
        exact = sum(1 for s in c.symbols() if c.read(c.write(s)) == [s])
        hist = {}
        for s in c.symbols():
            k = len(c.read(c.write(s)))
            hist[k] = hist.get(k, 0) + 1
        rows.append({"chart": c.name, "symbols": tot,
                     "uniquely_recovered": exact,
                     "preimage_histogram": {str(k): v
                                            for k, v in sorted(hist.items())},
                     "lossless_backward": exact == tot})
        print(f"      {c.name:26s} {exact:4d}/{tot:<4d} uniquely recovered   "
              f"preimage sizes {dict(sorted(hist.items()))}   "
              f"{'LOSSLESS' if exact == tot else 'LOSSY backward'}")
    emit(finding="F13_per_chart_roundtrip", rows=rows,
         verdict="Charts with a MODIFIER group are LOSSY backward: several "
                 "symbols name the same carrier value (the enharmonic-"
                 "spelling shape). That is not a bug in the chart — it is the "
                 "measurement that the chart carries STRICTLY MORE than the "
                 "carrier, and the surplus is convention. A chart WITHOUT "
                 "modifiers round-trips exactly.")

    # ══════════════════════════════════════════════════════════════════
    # F14 (VACUOUS FORM) — kept, because its failure is the finding.
    #
    # ⚠️ THIS TEST CANNOT FAIL, AND F16 PROVED IT.  It looks up a symbol of
    # chart 2 that writes to the SAME carrier value, then compares intervals
    # computed FROM THOSE CARRIER VALUES — which are equal by the lookup.
    # A deliberately corrupted chart scored 1225/1225.  This is a "good test
    # of the wrong verb": every fixture agrees because the fixture was built
    # by agreeing.  It is retained, with its negative control, because
    # deleting it would hide the design lesson it produced — see F14b.
    # ══════════════════════════════════════════════════════════════════
    print("\nF14   [VACUOUS FORM — retained deliberately; see F14b] "
          "inter-chart interval agreement via carrier-value lookup")
    pairs = []
    for c1, c2 in itertools.combinations(charts, 2):
        if c1.carrier.n != c2.carrier.n:
            pairs.append({"a": c1.name, "b": c2.name,
                          "same_carrier": False, "agree": None,
                          "total": 0,
                          "note": "different carrier modulus — NOT in the "
                                  "same atlas; comparing them is a category "
                                  "error and the instrument says so instead "
                                  "of returning a number"})
            print(f"      {c1.name:26s} vs {c2.name:26s} "
                  f"DIFFERENT CARRIER (n={c1.carrier.n} vs {c2.carrier.n}) "
                  f"-> not comparable")
            continue
        ok = tot = 0
        for s1, s2 in itertools.product(c1.symbols(), c1.symbols()):
            v1, v2 = c1.write(s1), c1.write(s2)
            t1, t2 = c2.read(v1), c2.read(v2)
            if not t1 or not t2:
                continue
            tot += 1
            if c1.chart_interval(s1, s2) == c2.chart_interval(t1[0], t2[0]):
                ok += 1
        pairs.append({"a": c1.name, "b": c2.name, "same_carrier": True,
                      "agree": ok, "total": tot,
                      "full_agreement": ok == tot and tot > 0})
        print(f"      {c1.name:26s} vs {c2.name:26s} "
              f"{ok:5d}/{tot:<5d}  "
              f"{'AGREE' if ok == tot and tot else 'DISAGREE'}")
    n_pairs = sum(1 for p in pairs if p["same_carrier"])
    n_agree = sum(1 for p in pairs if p.get("full_agreement"))
    emit(finding="F14_inter_chart_interval_agreement_VACUOUS", pairs=pairs,
         comparable_pairs=n_pairs, fully_agreeing=n_agree,
         instrument_valid=False,
         verdict=(f"{n_agree}/{n_pairs} comparable pairs agree — AND SO DOES "
                  "A DELIBERATELY CORRUPTED CHART (F16: 1225/1225). This "
                  "test is VACUOUS: it resolves chart 2's symbol BY carrier "
                  "value and then compares intervals computed FROM those "
                  "carrier values, so agreement is guaranteed by "
                  "construction. Recorded as a failed instrument, not as "
                  "evidence. The correct form is F14b."))

    # ══════════════════════════════════════════════════════════════════
    # F14b — THE CORRECTED ATLAS CONDITION.
    #
    # The lesson F16 forced: a carrier plus a bag of charts constrains
    # NOTHING.  Any two charts of the same carrier are trivially "compatible"
    # if compatibility is checked through the carrier.  The content of an
    # atlas lives entirely in the TRANSITION MAPS, and a transition map is
    # DATA THAT MUST BE SUPPLIED AND VERIFIED — it cannot be derived from the
    # charts, because deriving it is what made F14 vacuous.
    #
    # So the corrected condition is:  given charts c1, c2 AND a declared
    # symbol-level correspondence phi, does phi COMMUTE with write?
    #     c1.write(s) == c2.write(phi(s))   for every s in the overlap
    # A corrupted chart now fails, because phi is stated independently of
    # the corruption.
    # ══════════════════════════════════════════════════════════════════
    print("\nF14b  CORRECTED atlas condition — a DECLARED transition map that "
          "must COMMUTE with write")

    def check_transition(c1, c2, phi, label):
        ok = tot = 0
        bad_examples = []
        for s in c1.symbols():
            t = phi(s)
            if t is None or t[0] not in c2.rho or t[1] not in c2.modifiers:
                continue
            tot += 1
            if c1.write(s) == c2.write(t):
                ok += 1
            elif len(bad_examples) < 4:
                bad_examples.append(
                    {"symbol": list(s), "c1_writes": c1.write(s),
                     "phi_symbol": list(t), "c2_writes": c2.write(t)})
        good = tot > 0 and ok == tot
        print(f"      {label:52s} {ok:5d}/{tot:<5d}  "
              f"{'COMMUTES' if good else 'DOES NOT COMMUTE'}")
        return {"pair": label, "agree": ok, "total": tot, "commutes": good,
                "counterexamples": bad_examples}

    ident_phi = (lambda s: s)
    tb = []
    # same alphabet, same origin -> identity transition must commute
    tb.append(check_transition(charts[1], charts[1], ident_phi,
                               "positional-7+mod -> itself [identity phi]"))
    # moved origin: the DECLARED transition is 'same symbol', and it must NOT
    # commute, because the origin moved.  That is the clef change, visible.
    tb.append(check_transition(charts[1], charts[3], ident_phi,
                               "positional-7+mod -> @origin7 [identity phi]"))
    # ...but the CORRECT transition for a moved origin compensates the shift.
    # It is NOT a modifier shift: an origin move of s carrier-steps is
    # absorbed mostly by a DEGREE rotation, with a small per-degree modifier
    # residue.  Derive the best degree rotation rather than assuming one.
    c1, c2 = charts[1], charts[3]
    shift = c2.origin - c1.origin
    n = c1.carrier.n
    k = len(c1.alphabet)

    def residue(a, d):
        """The modifier the transition needs at degree a for rotation d."""
        a2 = (a + d) % k
        r = (c1.rho[a] - shift - c2.rho[a2]) % n
        return r - n if r > n // 2 else r        # balanced residue, no abs()

    best_d, best_cost = None, None
    costs = {}
    for d in range(k):
        res = [residue(a, d) for a in range(k)]
        # cost = how many degrees need a NON-ZERO modifier, then how large
        cost = (sum(1 for r in res if r != 0),
                sum(r if r > 0 else -r for r in res))
        costs[d] = {"residues": res, "n_nonzero": cost[0], "total": cost[1]}
        if best_cost is None or cost < best_cost:
            best_d, best_cost = d, cost
    print(f"      deriving the degree rotation for an origin shift of "
          f"{shift} on a {k}-degree alphabet mod {n}:")
    for d in range(k):
        mark = " <- chosen" if d == best_d else ""
        print(f"        rotation {d}: residues {costs[d]['residues']}  "
              f"non-zero {costs[d]['n_nonzero']}{mark}")

    def compensating_phi(s):
        a, m = s
        a2 = (a + best_d) % k
        m2 = m + residue(a, best_d)
        return (a2, m2)

    tb.append(check_transition(
        c1, c2, compensating_phi,
        f"positional-7+mod -> @origin7 [phi = rotate {best_d} + residue]"))
    print(f"      the derived transition rotates the alphabet by {best_d} and "
          f"needs a non-zero modifier on {best_cost[0]} of {k} degrees — "
          f"that residue is the KEY-SIGNATURE shape, derived, not assumed")
    emit(finding="F14b_corrected_atlas_condition", rows=tb,
         origin_shift=shift, alphabet_size=k, carrier_n=n,
         rotation_costs={str(d): costs[d] for d in costs},
         chosen_rotation=best_d,
         degrees_needing_a_modifier=best_cost[0],
         verdict="The atlas condition is a property of the DECLARED "
                 "TRANSITION, not of the charts. The identity transition "
                 "FAILS across a moved origin (that failure IS the origin "
                 "change) and the derived transition COMMUTES. Note what the "
                 "derivation produced without being told to: an origin shift "
                 "is absorbed by an alphabet ROTATION plus a non-zero "
                 "modifier on a MINORITY of degrees. That residue is the "
                 "key-signature shape, and it fell out of the group "
                 "arithmetic rather than being encoded.")

    # F16b — the corrected control: a WRONG chart under the TRANSITION test
    print("\nF16b  CORRECTED NEGATIVE CONTROL — wrong chart under F14b")
    bad_chart = Chart("positional-7-WRONG", "deliberately corrupted", C12, 0,
                      range(7), dict(enumerate((0, 2, 4, 5, 7, 9, 10))),
                      modifiers=(-2, -1, 0, 1, 2))
    r16b = check_transition(charts[1], bad_chart, ident_phi,
                            "positional-7+mod -> WRONG chart [identity phi]")
    print(f"      {'!! STILL BLESSED' if r16b['commutes'] else 'correctly REJECTED'}"
          f" — counterexamples: {r16b['counterexamples'][:2]}")
    emit(finding="F16b_corrected_wrong_chart_control", row=r16b,
         rejected=not r16b["commutes"], instrument_valid=not r16b["commutes"],
         verdict="Under the CORRECTED condition the corrupted chart FAILS, "
                 "where under the vacuous F14 form it scored 1225/1225. The "
                 "difference between the two is the whole design lesson: "
                 "compatibility must be checked against a SUPPLIED "
                 "transition, because checking it through the carrier is "
                 "checking nothing.")

    # ── F15 — is the carrier blind to registry order? ────────────────────
    print("\nF15   carrier blindness to chart-registry order")
    probe = [(0, 0), (2, 0), (4, 0)]
    c = charts[1]
    base = [c.chart_interval(a, b) for a, b in itertools.product(probe, probe)]
    shuffles = 0
    same = 0
    for perm in itertools.permutations(range(len(charts))):
        shuffles += 1
        _reg = [charts[i] for i in perm]        # noqa: F841 - the point
        got = [c.chart_interval(a, b)
               for a, b in itertools.product(probe, probe)]
        if got == base:
            same += 1
        if shuffles >= 120:
            break
    print(f"      registry permutations tried: {shuffles}; carrier answer "
          f"unchanged in {same}/{shuffles}")
    emit(finding="F15_registry_order_blindness", permutations=shuffles,
         unchanged=same, blind=same == shuffles,
         verdict="the carrier answer is independent of chart-registry order "
                 "— no chart is 'first'. This is a WEAK check by "
                 "construction (the carrier holds no registry reference at "
                 "all), and it is recorded as weak rather than counted as "
                 "strong evidence.")

    # ── F16 — NEGATIVE CONTROL against the VACUOUS F14.  It is EXPECTED to
    #         be blessed; that expectation is what condemns F14.
    print("\nF16   NEGATIVE CONTROL vs the VACUOUS F14 — expected to be "
          "wrongly blessed, which is the point")
    bad = Chart("positional-7-WRONG", "deliberately corrupted", C12, 0,
                range(7), dict(enumerate((0, 2, 4, 5, 7, 9, 10))),
                modifiers=(-2, -1, 0, 1, 2))
    good = charts[1]
    ok = tot = 0
    for s1, s2 in itertools.product(good.symbols(), good.symbols()):
        v1, v2 = good.write(s1), good.write(s2)
        t1, t2 = bad.read(v1), bad.read(v2)
        if not t1 or not t2:
            continue
        tot += 1
        if good.chart_interval(s1, s2) == bad.chart_interval(t1[0], t2[0]):
            ok += 1
    print(f"      wrong chart vs correct chart: {ok}/{tot} agreement  "
          f"{'BLESSED (as predicted -> F14 is vacuous)' if tot and ok == tot else 'rejected'}")
    emit(finding="F16_wrong_chart_control_vs_vacuous_F14",
         agree=ok, total=tot, blessed=bool(tot and ok == tot),
         instrument_valid=False,
         verdict="A deliberately corrupted chart is BLESSED by F14. This is "
                 "reported as a property of F14, not of the chart: it is the "
                 "measurement that condemned the test. The corrected control "
                 "is F16b.")

    # ── F17 — NEGATIVE CONTROL: right shape, WRONG GROUP ─────────────────
    print("\nF17   NEGATIVE CONTROL — right shape, WRONG interval group")
    g12 = charts[1]
    g24 = charts[4]
    # force a comparison the atlas would refuse, to show it WOULD have failed
    ok = tot = 0
    for s1, s2 in itertools.product(g12.symbols()[:20], g12.symbols()[:20]):
        tot += 1
        if g12.chart_interval(s1, s2) == g24.chart_interval(s1, s2):
            ok += 1
    print(f"      n=12 chart vs n=24 chart, compared ANYWAY: {ok}/{tot} "
          f"agreement  {'!! WOULD HAVE BLESSED' if ok == tot else 'would have FAILED'}")
    emit(finding="F17_wrong_group_control", agree=ok, total=tot,
         would_have_failed=ok != tot, instrument_valid=ok != tot,
         verdict="F14 refuses this comparison as non-comparable; F17 forces "
                 "it through to show the comparison WOULD have failed. The "
                 "refusal is therefore a real guard, not a way of hiding a "
                 "disagreement.")

    # ── the OCTAVE, delegated to the SHIPPED covering layer ──────────────
    print("\n      the register/octave axis is NOT re-implemented here — it "
          "is the shipped covering layer:")
    cl = center_lift([2, 2, 1, 2, 2, 2, 1], 12)
    lf = lift_fibre(cl["center_shadow"], 12, 24)
    print(f"      center_lift(major-scale steps, 12) -> cover_lift="
          f"{cl['cover_lift']}, shadow={cl['center_shadow']}, "
          f"shadow_determines_lift={cl['shadow_determines_lift']}")
    print(f"      lift_fibre(shadow, 12, window=24)  -> {lf['size']} registers "
          f"{lf['fibre']}, determined={lf['determined']}")
    emit(finding="P5_octave_delegated_to_covering",
         center_lift=cl, lift_fibre=lf,
         verdict="No new op is warranted for octave equivalence: "
                 "srmech.math.covering already carries the exact central "
                 "extension, parametric in the modulus, with the loss "
                 "ENUMERATED rather than asserted.")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\nwrote {len(RECS)} records -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
