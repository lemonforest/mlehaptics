"""
abc conjecture cascade (Oesterlé-Masser 1985).

Class cascade: A o J o L o K o N o C o M

  - A: content-hash of (a, b, c) coprime triple with a + b = c
  - J: primes -- radical rad(n) = product of distinct primes dividing n
       IS literally Class J primes primitive
  - L: Laplacian / composition -- rad(abc) IS multiplicative-additive
       coupling structure on the triple
  - K: asymptotic-DoF -- the conjecture IS that only FINITELY MANY triples
       saturate q(a,b,c) = log(c)/log(rad(abc)) > 1 + epsilon for any
       epsilon > 0. This is Class K pin-slot saturation at q = 1 from above.
  - N: rational anchor -- q(a,b,c) is a small-denom rational best-fit candidate;
       record q approx 1.6299 (Reyssat 1986)
  - C: cascade-orientation -- INTEGER substrate (Z, has exceptions) vs
       POLYNOMIAL substrate (Q[t], Mason-Stothers 1981 PROVED no exceptions).
       The substrate-orientation difference IS Class C cascade-orientation
  - M: HDC bind -- triple structure composes via Class M across coprime parts

Per [[project_a_n_operators_are_harmonic_objects_themselves]] §A: tests whether
(i) the integer-vs-polynomial substrate difference IS Class C cascade-orientation
(Mason-Stothers polynomial proof IS the substrate-perfect-math case;
integer substrate has the Class K finite-exceptions residual), and
(ii) record-quality q ~ 1.6299 sits at a small-denom Class N anchor.

Per [[feedback_no_lineage_claims_in_notebook]]: does NOT claim to solve abc
(or assess Mochizuki's IUT claim). Documents structural cascade decomposition
+ substrate-orientation reading + Class K finite-exceptions saturation test.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
via shared _cascade_helpers (best_rat_signed for Class N).

Roster: famous abc triples with attested high quality from Wikipedia /
Browkin-Brzezinski 1994 / Reyssat / de Weger / ABC@Home database + polynomial
Mason-Stothers analog. All q values computed bit-exact from log(c)/log(rad).
"""

import datetime
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.number_theory.abc_conjecture.triple.v1"
SOURCE_DOI = "https://en.wikipedia.org/wiki/Abc_conjecture + ABC@Home + Reyssat 1986"
SOURCE_PUBLISHED = "2026-05-23"


def rad(n):
    """Squarefree radical: product of distinct prime factors. Class J primes primitive."""
    if n <= 0:
        return 0
    result = 1
    d = 2
    BOUND = 1000000  # JPL Rule 2 bounded loop
    while d * d <= n and d < BOUND:
        if n % d == 0:
            result *= d
            while n % d == 0:
                n //= d
        d += 1
    if n > 1:
        result *= n
    return result


def is_coprime(a, b):
    """Class I cyclic GCD test."""
    return cyclic_gcd(a, b) == 1


# Roster: famous abc triples with attested high quality
# Format: (label, a, b, c, anchor, fermata)
ROSTER = [
    # Trivial baselines
    dict(label="1+1=2", a=1, b=1, c=2,
         anchor="trivial baseline; q = 1.0",
         fermata="rad(1*1*2) = 2; q = log(2)/log(2) = 1.0 EXACT"),
    dict(label="1+2=3", a=1, b=2, c=3,
         anchor="small baseline",
         fermata="rad(1*2*3) = 6; q = log(3)/log(6) approx 0.613"),
    dict(label="1+3=4", a=1, b=3, c=4,
         anchor="small example",
         fermata="rad(1*3*4) = 6; q approx 0.774"),
    dict(label="1+8=9", a=1, b=8, c=9,
         anchor="3^2 - 2^3 = 1 (Catalan); high q",
         fermata="rad(1*8*9) = 6; q approx 1.226 -- crosses pin-slot"),
    dict(label="5+27=32", a=5, b=27, c=32,
         anchor="2^5 - 3^3 = 5",
         fermata="rad(5*27*32) = 30; q approx 1.019"),
    dict(label="1+48=49", a=1, b=48, c=49,
         anchor="49 - 48 = 1 (7^2 - 2^4*3)",
         fermata="rad = 42; q approx 1.041"),
    dict(label="3+125=128", a=3, b=125, c=128,
         anchor="2^7 - 5^3 = 3",
         fermata="rad = 30; q approx 1.427 high quality"),
    dict(label="13+243=256", a=13, b=243, c=256,
         anchor="2^8 - 3^5 = 13",
         fermata="rad(13*243*256) = 78; q approx 1.273"),

    # Higher quality classic examples
    dict(label="1+80=81", a=1, b=80, c=81,
         anchor="3^4 - 2^4 * 5 = 1",
         fermata="rad = 30; q approx 1.292"),
    dict(label="1+512=513", a=1, b=512, c=513,
         anchor="2^9 + 1 = 513 = 27 * 19",
         fermata="rad = 2*3*19 = 114; q approx 1.317"),

    # High-quality record-setters
    # Reyssat 1986 record: q = 1.6299
    # 2 + 3^10 * 109 = 23^5
    dict(label="Reyssat: 2 + 3^10*109 = 23^5",
         a=2, b=3**10 * 109, c=23**5,
         anchor="Reyssat 1986 record q = 1.6299; quality-record-holder",
         fermata="3^10 = 59049; 3^10*109 = 6436341; 23^5 = 6436343; rad approx 23*3*109*2 = 15042"),

    # de Weger 2007 / Granville q approx 1.6260
    # 11^2 + 3^2 * 5^6 * 7^3 = 2^21 * 23
    dict(label="Browkin-Brzezinski 1994: 11^2 + 3^2*5^6*7^3 = 2^21*23",
         a=11**2, b=3**2 * 5**6 * 7**3, c=2**21 * 23,
         anchor="Browkin-Brzezinski 1994 catalog entry; q approx 1.6260",
         fermata=""),

    # Catalan-like (Mihailescu solved Catalan conjecture in 2002: only 8,9 case)
    dict(label="Catalan-like 1+8=9 revisit", a=1, b=8, c=9,
         anchor="Catalan conjecture: ONLY 9-8=1 solution to x^p - y^q = 1 with p,q>=2",
         fermata="Mihailescu 2002 PROVED Catalan; SOLO Catalan exception"),

    # Polynomial Mason-Stothers analog (PROVED; substrate-perfect-math case)
    # Encode as label-only since polynomials don't fit integer roster
    # Use a synthetic placeholder triple (1, polynomial-anchor, polynomial-anchor)
    # to register the substrate-orientation contrast in the cascade
    dict(label="Mason-Stothers PROVED polynomial substrate",
         a=1, b=1, c=2,
         anchor="Mason 1984; Stothers 1981; PROVED for coprime polynomials over field K with characteristic 0",
         fermata="POLYNOMIAL SUBSTRATE: deg(c) < deg(rad(abc)) STRICT (no exceptions). Integer abc has finite exceptions; polynomial has ZERO. Substrate-perfect-math via Class C cascade-orientation reset on Q[t]"),

    # Mochizuki IUT (defensive-scope only -- framework reads the claim status)
    dict(label="Mochizuki IUT 2012 (status disputed)", a=1, b=1, c=2,
         anchor="Mochizuki 2012 IUT claimed proof; PRIMS 2020 accepted; widely disputed (Scholze-Stix 2018)",
         fermata="framework reads: contested claim; not assessing IUT validity. Defensive-scope only."),
]


def main():
    out_path = pathlib.Path(__file__).parent / "triple.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        label = entry["label"]
        a = entry["a"]
        b = entry["b"]
        c = entry["c"]
        anchor = entry["anchor"]
        fermata = entry["fermata"]

        # Verify a + b = c (sanity)
        sum_ok = (a + b == c)

        # Verify coprimality (a, b, c pairwise coprime is sufficient)
        coprime = is_coprime(a, b) and is_coprime(b, c) and is_coprime(a, c)

        # Class J primes: radical
        rad_abc = rad(a * b * c)

        # Class K pin-slot at zero of (log c - log rad): quality q
        if rad_abc > 1 and c > 1:
            q = math.log(c) / math.log(rad_abc)
            q_num, q_den = best_rat_signed(q, max_d=100)
        else:
            q = 1.0
            q_num, q_den = 1, 1

        # Saturates Class K pin-slot at q > 1?
        crosses_pin_slot = (q > 1.0)

        # High-quality (q > 1.4)?
        high_quality = (q > 1.4)

        payload = json.dumps({"label": label, "a": a, "b": b, "c": c},
                             sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "label":                       label,
            "a":                           int(a),
            "b":                           int(b),
            "c":                           int(c),
            "sum_equals_c":                bool(sum_ok),
            "pairwise_coprime":            bool(coprime),
            "rad_abc":                     int(rad_abc),
            "quality_q":                   round(q, 6),
            "q_rational_num":              int(q_num),
            "q_rational_den":              int(q_den),
            "crosses_class_k_pin_slot":    bool(crosses_pin_slot),
            "high_quality_q_gt_1p4":       bool(high_quality),
            "class_cascade":               "A-compose-J-compose-L-compose-K-compose-N-compose-C-compose-M",
            "literature_anchor":           anchor,
            "open_fermata":                fermata,
            "computation_hash":            chash,
            "source_doi":                  SOURCE_DOI,
            "source_published_date":       SOURCE_PUBLISHED,
            "entered_locally_at":          now_iso[:10],
        }
        records.append(rec)
        diag.append((label, a, b, c, sum_ok, coprime, rad_abc, q, q_num, q_den,
                     crosses_pin_slot, high_quality))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Diagnostics
    print(f"{'label':<55} {'a':>10} {'b':>14} {'c':>14} {'sum_ok':>7} {'coprime':>8} {'rad':>10} {'q':>8} {'Class N':>10} {'q>1':>5} {'q>1.4':>7}")
    for d in diag:
        label, a, b, c, sok, cop, r, q, qn, qd, cross, hq = d
        print(f"  {label:<53} {a:>10} {b:>14} {c:>14} {str(sok):>7} {str(cop):>8} {r:>10} {q:>8.4f} {f'{qn}/{qd}':>10} {str(cross):>5} {str(hq):>7}")

    # Class K pin-slot saturation distribution
    print()
    print("Class K pin-slot test: how many triples cross q > 1?")
    cross_count = sum(1 for d in diag if d[10])
    hq_count = sum(1 for d in diag if d[11])
    print(f"  Triples with q > 1.0:   {cross_count} / {len(diag)}")
    print(f"  Triples with q > 1.4:   {hq_count} / {len(diag)} (high quality)")

    # Record quality
    q_values = [d[7] for d in diag if d[7] > 0]
    if q_values:
        print()
        print(f"Record quality in roster: q = {max(q_values):.4f}")
        print(f"  Best Class N best-rational: {best_rat_signed(max(q_values), max_d=200)}")

    # Substrate-orientation contrast: integer (this roster) vs polynomial (Mason-Stothers)
    print()
    print("Substrate-orientation contrast (Class C cascade-orientation):")
    print("  INTEGER substrate: HAS exceptions (q > 1 + epsilon for many concrete triples)")
    print("  POLYNOMIAL substrate (Mason-Stothers 1981): ZERO exceptions -- deg(c) < deg(rad(abc)) STRICT")
    print("  Reading: substrate-perfect-math holds on Q[t]; Z has finite Class K residual")


if __name__ == "__main__":
    main()
