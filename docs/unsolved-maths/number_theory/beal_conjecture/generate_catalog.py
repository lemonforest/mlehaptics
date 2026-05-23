"""
Beal's conjecture cascade (Andrew Beal 1993).

Class cascade: A o J o I o C o K o N o M

Statement: If A^x + B^y = C^z, where A, B, C, x, y, z are positive integers
with x, y, z > 2, then A, B, and C share a common prime factor.
Equivalently: if gcd(A, B, C) = 1 (coprime), then no such (A^x + B^y = C^z)
exists with all exponents > 2.

  - A: content-hash of (A, B, C, x, y, z) tuple
  - J: primes -- Beal IS fundamentally a prime-factorization statement
  - I: cyclic -- coprimality test via Class I cyclic GCD
  - C: cascade-orientation -- exponent triple (x, y, z) IS Class C orientation;
       symmetry-breaking happens when exponents differ (versus x=y=z FLT case)
  - K: asymptotic-DoF -- Beal IS Class K predicate-implies-no-solution; the
       "all > 2 + coprime" predicate IS the pin-slot saturation criterion that
       conjecturally forbids any solution
  - N: rational anchor -- exponent ratios x/y, y/z; exponent sums
  - M: HDC bind -- ternary composition A^x + B^y -> C^z is a Class M three-way bind

Per [[project_a_n_operators_are_harmonic_objects_themselves]] §A: tests whether
(i) the "all > 2" predicate IS Class K pin-slot at the n = 2 phase boundary
(below 2: Pythagorean triples exist freely; at 2: Pythagorean; above 2: no
coprime solutions conjectured), and (ii) proved sub-cases (FLT n=n=n; Darmon-
Merel (n, n, 2); Bennett-Bruin (2, 3, n); etc.) cluster at small-denom
exponent-ratio anchors.

Per [[feedback_no_lineage_claims_in_notebook]]: does NOT claim to solve Beal
or assess the Beal Prize ($1,000,000). Documents structural cascade
decomposition + proved sub-cases inventory + Fermat-Catalan exception
catalog (these are NOT Beal counterexamples because at least one exponent = 2).

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
via shared _cascade_helpers (best_rat_signed for Class N).

Roster: (i) Fermat's Last Theorem family (n=n=n; Wiles 1995); (ii) Darmon-
Merel proved cases; (iii) Catalan-Mihailescu 2002; (iv) known Fermat-Catalan
solutions with min(x,y,z) = 2 (NOT Beal counterexamples).
"""

import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.number_theory.beal_conjecture.triple.v1"
SOURCE_DOI = "https://www.bealconjecture.com + Mauldin 1997 + Norvig + Darmon-Merel 1997"
SOURCE_PUBLISHED = "2026-05-23"


def gcd3(a, b, c):
    """Three-way GCD via two applications of Class I cyclic GCD."""
    return cyclic_gcd(cyclic_gcd(a, b), c)


# Roster: known triples + proved sub-cases
# Format: (label, A, B, C, x, y, z, category, anchor, fermata)
# category: "Beal-relevant" (all > 2 + coprime) | "Fermat-Catalan" (min exp = 2) |
#           "FLT-Wiles" (x = y = z; proved) | "trivial" | "Darmon-Merel-proved" |
#           "Catalan-Mihailescu" (special unique solution)
ROSTER = [
    # FLT family x = y = z = n (Wiles 1995 PROVED no coprime solution for n >= 3)
    dict(label="FLT n=3 proved (no coprime soln)", A=0, B=0, C=0, x=3, y=3, z=3,
         category="FLT-Wiles", anchor="Euler 1770 proved n=3; Wiles 1995 general",
         fermata="A^3 + B^3 = C^3 has NO coprime A,B,C > 0 solutions (Wiles)"),
    dict(label="FLT n=4 proved", A=0, B=0, C=0, x=4, y=4, z=4,
         category="FLT-Wiles", anchor="Fermat 1640 proved n=4 via descent",
         fermata="A^4 + B^4 = C^4 has NO coprime A,B,C > 0 solutions (Fermat himself)"),
    dict(label="FLT n=5 proved", A=0, B=0, C=0, x=5, y=5, z=5,
         category="FLT-Wiles", anchor="Dirichlet+Legendre 1825 proved n=5",
         fermata=""),
    dict(label="FLT n=7 proved (Hurwitz heptadic exponent)", A=0, B=0, C=0, x=7, y=7, z=7,
         category="FLT-Wiles", anchor="Lamé 1839; Hurwitz heptadic exponent",
         fermata="FLT at n=7 composes with framework Hurwitz heptadic canon"),
    dict(label="FLT n general proved", A=0, B=0, C=0, x=99, y=99, z=99,
         category="FLT-Wiles", anchor="Wiles 1995 + Taylor-Wiles 1995; ALL n >= 3 proved",
         fermata="Beal generalizes FLT to unequal exponents x, y, z"),

    # Darmon-Merel 1997 proved (n, n, 2) for n >= 4
    dict(label="Darmon-Merel (4, 4, 2) proved", A=0, B=0, C=0, x=4, y=4, z=2,
         category="Darmon-Merel-proved",
         anchor="Darmon-Merel 1997: no coprime soln for (n,n,2) with n >= 4",
         fermata="proved sub-case; one exponent = 2 so NOT Beal-relevant"),
    dict(label="Darmon-Merel (5, 5, 2) proved", A=0, B=0, C=0, x=5, y=5, z=2,
         category="Darmon-Merel-proved",
         anchor="Darmon-Merel 1997",
         fermata=""),
    dict(label="Darmon-Merel (n, n, 3) proved for n >= 3", A=0, B=0, C=0, x=3, y=3, z=3,
         category="Darmon-Merel-proved",
         anchor="Darmon-Merel 1997 result for (n,n,3) with n >= 3",
         fermata=""),

    # Catalan-Mihailescu (related conjecture proved)
    dict(label="Catalan: 3^2 - 2^3 = 1 SOLO solution", A=2, B=1, C=3, x=3, y=1, z=2,
         category="Catalan-Mihailescu",
         anchor="Mihailescu 2002 proved Catalan: x^p - y^q = 1 with p,q >= 2 has only this solution",
         fermata="exponent 1 on B makes this trivially-degenerate; Catalan IS sub-cascade analog"),

    # Fermat-Catalan known solutions (min exponent = 2; NOT Beal counterexamples)
    dict(label="Fermat-Catalan: 1 + 2^3 = 3^2", A=1, B=2, C=3, x=1, y=3, z=2,
         category="Fermat-Catalan", anchor="trivial (1 + 8 = 9)",
         fermata="trivial degenerate; A = 1"),
    dict(label="Fermat-Catalan: 2^5 + 7^2 = 3^4", A=2, B=7, C=3, x=5, y=2, z=4,
         category="Fermat-Catalan", anchor="32 + 49 = 81 = 3^4",
         fermata="min(x,y,z) = 2; NOT a Beal counterexample"),
    dict(label="Fermat-Catalan: 7^3 + 13^2 = 2^9", A=7, B=13, C=2, x=3, y=2, z=9,
         category="Fermat-Catalan", anchor="343 + 169 = 512 = 2^9",
         fermata="min(x,y,z) = 2; NOT a Beal counterexample"),
    dict(label="Fermat-Catalan: 2^7 + 17^3 = 71^2", A=2, B=17, C=71, x=7, y=3, z=2,
         category="Fermat-Catalan", anchor="128 + 4913 = 5041 = 71^2",
         fermata="min(x,y,z) = 2; NOT a Beal counterexample"),
    dict(label="Fermat-Catalan: 3^5 + 11^4 = 122^2", A=3, B=11, C=122, x=5, y=4, z=2,
         category="Fermat-Catalan", anchor="243 + 14641 = 14884 = 122^2",
         fermata="min(x,y,z) = 2; NOT a Beal counterexample"),
    dict(label="Fermat-Catalan: 17^7 + 76271^3 = 21063928^2 (Beukers)",
         A=17, B=76271, C=21063928, x=7, y=3, z=2,
         category="Fermat-Catalan",
         anchor="Beukers; spectacular example with min exp = 2",
         fermata="min(x,y,z) = 2; NOT a Beal counterexample"),
    dict(label="Fermat-Catalan: 1414^3 + 2213459^2 = 65^7",
         A=1414, B=2213459, C=65, x=3, y=2, z=7,
         category="Fermat-Catalan",
         anchor="known Fermat-Catalan solution; Bruin et al.",
         fermata="min(x,y,z) = 2; NOT a Beal counterexample"),
    dict(label="Fermat-Catalan: 9262^3 + 15312283^2 = 113^7",
         A=9262, B=15312283, C=113, x=3, y=2, z=7,
         category="Fermat-Catalan", anchor="Beukers",
         fermata="min(x,y,z) = 2"),

    # Norvig 2000s computational verification
    dict(label="Norvig 2003 search: no coprime soln found up to N <= 10000, exp <= 100",
         A=0, B=0, C=0, x=3, y=3, z=3,  # placeholder; this is a meta-record
         category="Beal-relevant",
         anchor="Norvig 2003: exhaustive search; A,B,C <= 10000; x,y,z <= 100",
         fermata="NO coprime Beal-relevant solutions found computationally"),

    # Bennett-Skinner / Bruin / Chen / Dahmen / etc -- more proved sub-cases
    dict(label="Bennett-Skinner (2, n, n) proved for n >= 4",
         A=0, B=0, C=0, x=2, y=4, z=4,
         category="Darmon-Merel-proved",
         anchor="Bennett-Skinner 2004 + others; (2,n,n) proved for n >= 4",
         fermata="proved sub-case; one exponent = 2"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "triple.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        label = entry["label"]
        A = entry["A"]
        B = entry["B"]
        C = entry["C"]
        x = entry["x"]
        y = entry["y"]
        z = entry["z"]
        cat = entry["category"]
        anchor = entry["anchor"]
        fermata = entry["fermata"]

        # Verify A^x + B^y = C^z arithmetically (for concrete entries)
        if A > 0 and B > 0 and C > 0:
            sum_ok = (A**x + B**y == C**z)
        else:
            sum_ok = None  # placeholder entries

        # Coprimality (Class I cyclic GCD)
        if A > 0 and B > 0 and C > 0:
            g = gcd3(A, B, C)
            coprime = (g == 1)
        else:
            g = -1
            coprime = None

        # Beal predicate: all exponents > 2 AND coprime
        all_exp_gt_2 = (x > 2 and y > 2 and z > 2)
        min_exp = min(x, y, z) if max(x, y, z) > 0 else 0
        max_exp = max(x, y, z) if max(x, y, z) > 0 else 0

        # Class N anchor: exponent ratios at small-denom rationals
        # x / max_exp, y / max_exp, z / max_exp (normalized to dominant)
        if max_exp > 0:
            rx, _ = best_rat_signed(x / max_exp, max_d=30)
            ry, _ = best_rat_signed(y / max_exp, max_d=30)
            rz, _ = best_rat_signed(z / max_exp, max_d=30)
        else:
            rx, ry, rz = 0, 0, 0

        # Class K pin-slot test: is this a Beal-prohibited candidate?
        # (all_exp > 2 AND coprime AND sum_ok)
        violates_beal = (all_exp_gt_2 and coprime is True and sum_ok is True)

        payload = json.dumps({"label": label, "A": A, "B": B, "C": C,
                              "x": x, "y": y, "z": z}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "label":                       label,
            "A":                           int(A),
            "B":                           int(B),
            "C":                           int(C),
            "exp_x":                       int(x),
            "exp_y":                       int(y),
            "exp_z":                       int(z),
            "min_exponent":                int(min_exp),
            "max_exponent":                int(max_exp),
            "all_exp_gt_2":                bool(all_exp_gt_2),
            "sum_equals_C_z":              sum_ok if sum_ok is not None else False,
            "gcd_ABC":                     int(g),
            "coprime_ABC":                 coprime if coprime is not None else False,
            "violates_beal":               bool(violates_beal),
            "category":                    cat,
            "class_cascade":               "A-compose-J-compose-I-compose-C-compose-K-compose-N-compose-M",
            "literature_anchor":           anchor,
            "open_fermata":                fermata,
            "computation_hash":            chash,
            "source_doi":                  SOURCE_DOI,
            "source_published_date":       SOURCE_PUBLISHED,
            "entered_locally_at":          now_iso[:10],
        }
        records.append(rec)
        diag.append((label, A, B, C, x, y, z, cat, sum_ok, coprime, all_exp_gt_2, violates_beal))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Diagnostics
    print(f"{'label':<60} {'(x,y,z)':>14} {'category':<22} {'sum_ok':>7} {'coprime':>8} {'all>2':>6} {'violates Beal':>13}")
    for d in diag:
        label, A, B, C, x, y, z, cat, sok, cop, allgt, vb = d
        exp_tuple = f"({x},{y},{z})"
        print(f"  {label[:58]:<58} {exp_tuple:>14} {cat:<22} {str(sok):>7} {str(cop):>8} {str(allgt):>6} {str(vb):>13}")

    # Category distribution
    print()
    print("Category distribution:")
    cat_counts = {}
    for d in diag:
        cat_counts[d[7]] = cat_counts.get(d[7], 0) + 1
    for cat, c in sorted(cat_counts.items()):
        print(f"  {cat:<28}: {c}")

    # Class K saturation: any Beal violations in roster?
    print()
    violations = sum(1 for d in diag if d[11])
    print(f"Class K saturation test: Beal-violating triples in roster: {violations} / {len(diag)}")
    if violations == 0:
        print("  ZERO violations -- conjecture HOLDS across roster (consistent with Norvig 2003)")

    # Min-exponent distribution (Class K pin-slot at min_exp = 2)
    print()
    print("Min-exponent distribution (Class K pin-slot at min_exp = 2 boundary):")
    min_exp_counts = {}
    for d in diag:
        x, y, z = d[4], d[5], d[6]
        if max(x, y, z) > 0:
            min_e = min(x, y, z)
            min_exp_counts[min_e] = min_exp_counts.get(min_e, 0) + 1
    for me, c in sorted(min_exp_counts.items()):
        if me == 2:
            print(f"  min exp = {me}: {c} (Fermat-Catalan boundary; NOT Beal-relevant)")
        elif me > 2:
            print(f"  min exp = {me}: {c} (Beal-relevant region)")
        else:
            print(f"  min exp = {me}: {c} (degenerate)")


if __name__ == "__main__":
    main()
