#!/usr/bin/env python3
"""P6 — the chart-freedom group: the ORIGIN part is a torsor, the RENAMING
part is not (rc426 research spike, read-only).

Why this exists
===============
The Mazzola verification (P-cite) returned a REFUTATION of "clef as a chart in
the atlas sense" and a CONSTRUCTIVE correction: the construct in Mazzola that
actually does *same space, different naming convention* is **Syn** (synonymy)
/ address change, and his own worked instance is the fifth-circle automorphism
of ``ℤ₁₂``.  That is an AUTOMORPHISM, not a translation — a different kind of
freedom from the clef.

So a chart carries (at least) TWO independent freedoms, and this script
measures whether they behave the same way.  They do not, and the difference is
exactly the user's hypothesis sharpened:

    ORIGIN  choice  — a translation.  FREE (no fixed point) => TORSOR.
    RENAMING choice — an automorphism. HAS a fixed point     => NOT a torsor.

Pre-registered falsifiers
=========================
F18 Is the translation action free at every n?  (predicts: yes, 0 fixed points)
F19 Is the automorphism action free?  (predicts: NO — every automorphism fixes
    the identity, so the renaming freedom is NOT torsorial)
F20 What is the full chart-freedom group, and is IT a torsor on the carrier?
    (the holomorph ℤ/n ⋊ Aut(ℤ/n) — the affine group)
F21 Is "the fifth" special to n=12, or generic?  Measured as: how many
    generators does ℤ/n have, i.e. |Aut(ℤ/n)| = φ(n).  If 12 is unremarkable
    in this table, the circle-of-fifths structure is not a reason to privilege
    it.
NEG A non-automorphism (a non-unit multiplier) must FAIL to be a renaming.

Everything runs through shipped srmech ops: Class I (``cyclic_mod_add``,
``gcd``) and Class J (``factor``).  No ``abs()``, no float, no numpy.

Run:
    PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_p6_chart_freedom_group_rc426.py
"""
from __future__ import annotations

import json
import os
import sys

import srmech
from srmech.cascade import cyclic_mod_add
from srmech.math.cyclic import gcd
from srmech.math.primes import factor

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_p6_chart_freedom_group_rc426.ndjson")
RECS = []

MODULI = (5, 7, 12, 17, 19, 22, 24, 31, 41, 53)


def emit(**kw):
    kw.setdefault("srmech_version", srmech.__version__)
    RECS.append(kw)


def units(n):
    """(ℤ/n)* via the shipped Class-I gcd — Aut(ℤ/n) as a set."""
    return [u for u in range(1, n) if gcd(u, n) == 1]


def main() -> int:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    try:
        import numpy  # noqa: F401
        print("!! numpy PRESENT — environment wrong")
    except ImportError:
        print("numpy              = ABSENT (correct)")

    # ══════════════════════════════════════════════════════════════════
    # F18/F19 — the two freedoms, measured side by side
    # ══════════════════════════════════════════════════════════════════
    print("\nF18/F19  the two chart freedoms, and whether each is FREE")
    print("      n   |G|  translations  fixed pts   |Aut|  automorphisms  "
          "fixed pts   holomorph  torsor?")
    rows = []
    for n in MODULI:
        U = units(n)
        # translations: t_g(x) = x + g.  fixed points of NON-identity g
        t_fixed = sum(1 for g in range(1, n) for x in range(n)
                      if cyclic_mod_add(x, g, n) == x)
        # automorphisms: a_u(x) = u*x.  fixed points of NON-identity u
        a_fixed = sum(1 for u in U if u != 1 for x in range(n)
                      if (u * x) % n == x)
        # every non-identity automorphism fixes 0 -> at least |U|-1
        min_expected = len(U) - 1
        holo = n * len(U)
        rows.append({"n": n, "group_order": n, "n_translations": n,
                     "translation_fixed_points": t_fixed,
                     "translation_action_free": t_fixed == 0,
                     "aut_order": len(U), "automorphism_fixed_points": a_fixed,
                     "automorphism_action_free": a_fixed == 0,
                     "min_expected_aut_fixed_points": min_expected,
                     "holomorph_order": holo})
        print(f"      {n:3d}  {n:3d}  {n:12d}  {t_fixed:9d}   {len(U):5d}  "
              f"{len(U):13d}  {a_fixed:9d}   {holo:9d}  "
              f"origin={'FREE' if t_fixed == 0 else 'not free'} / "
              f"rename={'FREE' if a_fixed == 0 else 'NOT free'}")
    all_t_free = all(r["translation_action_free"] for r in rows)
    any_a_free = any(r["automorphism_action_free"] for r in rows)
    print(f"\n      translation action FREE at every n: {all_t_free}")
    print(f"      automorphism action free at ANY n : {any_a_free}  "
          f"(every non-identity automorphism fixes 0 — the identity element "
          f"is a canonical point the renaming CANNOT move)")
    emit(finding="F18_F19_two_chart_freedoms", rows=rows,
         translation_free_everywhere=all_t_free,
         automorphism_free_anywhere=any_a_free,
         verdict=("THE TWO FREEDOMS ARE DIFFERENT IN KIND. The ORIGIN "
                  "(clef) freedom is a free action at every n — no origin is "
                  "distinguished, so it IS a torsor and 'a clef is an origin "
                  "choice, not data' is exactly right. The RENAMING (Syn / "
                  "automorphism) freedom is NOT free at any n: every "
                  "non-identity automorphism fixes the identity element, so "
                  "a renaming DOES distinguish a point. Conflating the two "
                  "would have made the torsor claim false."))

    # ══════════════════════════════════════════════════════════════════
    # F20 — the full chart-freedom group is the holomorph / affine group
    # ══════════════════════════════════════════════════════════════════
    print("\nF20   the FULL chart-freedom group = ℤ/n ⋊ Aut(ℤ/n) (affine)")
    n = 12
    U = units(n)
    aff = [(u, g) for u in U for g in range(n)]

    def apply_aff(e, x):
        u, g = e
        return cyclic_mod_add((u * x) % n, g, n)

    # is the affine action on the carrier free?  transitive?
    hist = {}
    for x in range(n):
        for y in range(n):
            k = sum(1 for e in aff if apply_aff(e, x) == y)
            hist[k] = hist.get(k, 0) + 1
    transitive = 0 not in hist
    free = set(hist) == {1}
    print(f"      n={n}: |affine| = {len(aff)} = {n}·{len(U)};  "
          f"transitive on the carrier: {transitive};  free: {free}")
    print(f"      (x -> y) multiplicity histogram: {dict(sorted(hist.items()))}")
    print(f"      so the affine group is TRANSITIVE but NOT FREE — it is NOT "
          f"a torsor. Only its TRANSLATION subgroup is.")
    emit(finding="F20_full_chart_freedom_group", modulus=n,
         affine_order=len(aff), translation_subgroup_order=n,
         aut_order=len(U), transitive=transitive, free=free,
         multiplicity_histogram={str(k): v for k, v in sorted(hist.items())},
         verdict="The full chart-freedom group is the holomorph "
                 "ℤ/n ⋊ Aut(ℤ/n) (the 1-dimensional affine group). It acts "
                 "TRANSITIVELY but NOT FREELY, so it is not a torsor. The "
                 "torsor is exactly the NORMAL TRANSLATION SUBGROUP. That is "
                 "the precise sense in which 'a clef is an origin choice': "
                 "the clef lives in the torsorial part, and the key/mode/"
                 "renaming conventions live in the part that is not.")

    # ══════════════════════════════════════════════════════════════════
    # F21 — is n=12 special?  Measured through Class-J factor().
    # ══════════════════════════════════════════════════════════════════
    print("\nF21   is n=12 special?  |Aut(ℤ/n)| = φ(n), with the factorisation")
    print("      n    factorisation        φ(n)  φ(n)/n     #generators")
    tbl = []
    for n in MODULI:
        f = factor(n)
        U = units(n)
        tbl.append({"n": n, "factorisation": [list(t) for t in f],
                    "phi": len(U), "generators": U})
        fs = "·".join(f"{p}^{m}" if m > 1 else str(p) for p, m in f)
        print(f"      {n:3d}  {fs:18s} {len(U):5d}  {len(U)}/{n:<8d} {U}")
    twelve = [r for r in tbl if r["n"] == 12][0]
    ranks = sorted(tbl, key=lambda r: -r["phi"])
    pos = [r["n"] for r in ranks].index(12) + 1
    print(f"\n      n=12 has φ(12)={twelve['phi']} generators "
          f"{twelve['generators']} — rank {pos} of {len(tbl)} in this table")
    print(f"      the PRIMES in the table (7, 17, 19, 31, 41, 53) all have "
          f"φ(n)=n−1, the MAXIMUM — so by 'number of available renamings', "
          f"12 is one of the POOREST rows, not the richest")
    emit(finding="F21_is_twelve_special", table=tbl,
         twelve_phi=twelve["phi"], twelve_generators=twelve["generators"],
         rank_by_phi=pos, total_rows=len(tbl),
         verdict=("n=12 is NOT distinguished. Its automorphism group has "
                  f"order {twelve['phi']} and it ranks {pos} of {len(tbl)} "
                  "by that measure; every prime modulus in the sweep beats "
                  "it. Whatever makes 12 musically prevalent, it is not a "
                  "property the interval algebra can see — which is exactly "
                  "what a frame-free carrier is supposed to report."))

    # ══════════════════════════════════════════════════════════════════
    # NEG — a non-unit multiplier must FAIL to be a renaming
    # ══════════════════════════════════════════════════════════════════
    print("\nNEG   a NON-unit multiplier must fail to be an automorphism")
    n = 12
    bad = [m for m in range(2, n) if gcd(m, n) != 1]
    rows = []
    for m in bad:
        img = {(m * x) % n for x in range(n)}
        injective = len(img) == n
        rows.append({"multiplier": m, "gcd_with_n": gcd(m, n),
                     "image_size": len(img), "is_automorphism": injective})
    n_blessed = sum(1 for r in rows if r["is_automorphism"])
    print(f"      non-units mod {n}: {bad}")
    print(f"      image sizes: {[(r['multiplier'], r['image_size']) for r in rows]}")
    print(f"      wrongly accepted as automorphisms: {n_blessed}/{len(bad)}  "
          f"{'!! INSTRUMENT BROKEN' if n_blessed else 'instrument OK'}")
    emit(finding="NEG_non_unit_multiplier", modulus=n, rows=rows,
         n_wrongly_accepted=n_blessed, instrument_valid=n_blessed == 0)

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\nwrote {len(RECS)} records -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
