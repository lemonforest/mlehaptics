#!/usr/bin/env python3
"""LANE 1 follow-up — WHICH element is the privileged middle (2026-07-29).

Companion to ``associator_symmetry_type_rung_by_rung.py``. Three things the
first probe left open:

  1. EXHAUSTIVE shipped-op verification of the load-bearing dim-16 number.
     Every one of the NEITHER-class ordered triples at dim 16 is re-derived
     through ``table_product`` ∘ ``table_product`` ∘ ``cd_add`` (no fast path),
     so the headline "1008" rests on the shipped surface, not on an oracle.

  2. MIDDLE-GROUP COHERENCE for the controls. The subject algebras all measured
     ``middle_group_sign_incoherent = 0`` — the two arrangements sharing a
     middle differ ONLY by a sign. Does a random anticommutative table do that
     too? If it does, the measurement is not detecting algebra structure.

  3. WHICH element sits in the distinguished middle. At dim 16 the witness
     (1, 2, 12) is nonzero only with e₁₂ in the middle — and 12 ≥ 8 is a
     NEW-RUNG index. Is that general?

Same guards: shipped srmech ops as subject, exact integers, no float, no
``abs()``, no numpy, no stdlib ``fractions``, Class-A (sha256) randomness.
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    CD_COMPOSE_MAX_DIM,
    algebra_table,
    table_product,
    cd_add,
    cd_basis,
)

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from associator_symmetry_type_rung_by_rung import (   # noqa: E402
    PERMS, assoc_fast, assoc_shipped, magnitude_class, monomial_map,
    rand_anticommutative_table,
)


def orbit_values(mono, base):
    """The 6 (value, parity, middle-slot, triple) rows for one multiset."""
    rows = []
    for perm, parity, mid in PERMS:
        tri = (base[perm[0]], base[perm[1]], base[perm[2]])
        rows.append((assoc_fast(mono, *tri), parity, mid, tri))
    return rows


def characterise(table, name, dim, exhaustive_shipped_on_neither):
    mono = monomial_map(table)
    minus_e0 = tuple([-1] + [0] * (dim - 1))

    incoherent = 0
    neither_orbits = 0
    neither_ordered = 0
    shipped_checks = 0
    # how many of the 3 middle slots carry a NONZERO associator, among the
    # orbits whose middle is observable
    nonzero_middle_count_hist = {}
    # is the distinguished (nonzero-middle) element from the NEWEST rung
    # (index >= dim/2)?  yes / no / mixed
    newest_rung_verdict = {}
    half = dim >> 1

    for base in itertools.combinations_with_replacement(range(dim), 3):
        rows = orbit_values(mono, base)
        orbit = len(set(itertools.permutations(base)))
        ident = rows[0][0]
        alternating = all(
            v == (ident if p == 1 else tuple((i, -c) for i, c in ident))
            for v, p, _m, _t in rows)
        by_mid = {}
        for v, _p, m, _t in rows:
            by_mid.setdefault(m, set()).add(magnitude_class(v))
        if any(len(s) > 1 for s in by_mid.values()):
            incoherent += orbit
        if alternating:
            continue
        neither_orbits += 1
        neither_ordered += orbit

        # which middle slots are NONZERO
        nz_slots = [m for m, s in by_mid.items()
                    if len(s) == 1 and next(iter(s)) != ()]
        if any(len(s) > 1 for s in by_mid.values()):
            nz_slots = [m for m, s in by_mid.items() if s != {()}]
        k = len(nz_slots)
        nonzero_middle_count_hist[str(k)] = \
            nonzero_middle_count_hist.get(str(k), 0) + orbit

        # the ELEMENTS occupying those distinguished middles
        elems = {base[m] for m in nz_slots}
        if elems:
            all_new = all(e >= half for e in elems)
            none_new = all(e < half for e in elems)
            key = "all_newest_rung" if all_new else (
                "none_newest_rung" if none_new else "mixed")
            newest_rung_verdict[key] = newest_rung_verdict.get(key, 0) + orbit

        if exhaustive_shipped_on_neither:
            for _v, _p, _m, tri in rows:
                got = assoc_shipped(table, minus_e0, *tri)
                if got != assoc_fast(mono, *tri):
                    raise AssertionError(f"{name}: shipped/fast split at {tri}")
                shipped_checks += 1

    return {
        "record": "privileged_middle_followup",
        "algebra": name,
        "dim": dim,
        "neither_orbits": neither_orbits,
        "neither_ordered_triples": neither_ordered,
        "middle_group_sign_incoherent_ordered": incoherent,
        "nonzero_middle_slot_count_histogram": nonzero_middle_count_hist,
        "distinguished_middle_is_newest_rung": newest_rung_verdict,
        "exhaustive_shipped_op_checks_on_neither": shipped_checks,
        "shipped_op_disagreements": 0,
    }


def main() -> int:
    recs = []
    # (1) the load-bearing dim-16 number, re-derived EXHAUSTIVELY through the
    #     shipped table_product / cd_add composition.
    recs.append(characterise(algebra_table(16), "CD-definite", 16, True))
    recs.append(characterise(algebra_table(32), "CD-definite", 32, False))
    recs.append(characterise(algebra_table(8), "CD-definite", 8, True))
    recs.append(characterise(algebra_table(4), "CD-definite", 4, True))
    # split control at the rung where alternativity dies
    recs.append(characterise(algebra_table(16, [1, -1, -1, -1]),
                             "CD-split-gammas+---", 16, False))
    recs.append(characterise(algebra_table(8, [1, -1, -1]),
                             "CD-split-gammas+--", 8, True))
    # (2)/(3) the random anticommutative controls
    for dim in (8, 16):
        for lab in ("A", "B"):
            recs.append(characterise(
                rand_anticommutative_table(dim, "randsign" + lab, True),
                f"RAND-SIGN-{lab}", dim, False))
            recs.append(characterise(
                rand_anticommutative_table(dim, "randfull" + lab, False),
                f"RAND-FULL-{lab}", dim, False))
    for r in recs:
        print(json.dumps(r, separators=(",", ":"), sort_keys=True), flush=True)
    print(json.dumps({"record": "note",
                      "CD_COMPOSE_MAX_DIM": CD_COMPOSE_MAX_DIM},
                     separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
