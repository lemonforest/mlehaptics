"""
Lonely runner conjecture cascade.

Statement: k runners on a circular track of unit length, starting at the same
point. Each runner has a distinct non-zero constant integer speed. The
conjecture asserts that for each runner there is some time at which that
runner is "lonely" -- at distance >= 1/k along the track from all other
runners.

Equivalently (gap formulation): for any set of k-1 positive integers
{v_1, ..., v_{k-1}}, there exists a real t such that
||t * v_i|| >= 1/k for all i, where ||x|| denotes distance from nearest integer.

Status: PROVED for k <= 7 (Barajas-Serra 2008); OPEN for k >= 8.

Class cascade: A o I o C o J o K o N o M

  - A: content-hash of (k, speeds, lonely-distance)
  - I: cyclic -- track is S^1 (unit circle); Class I cyclic primitive
  - C: cascade-orientation -- each runner's frame IS a Class C orientation
       on the cyclic substrate
  - J: primes -- speeds often anchored at prime values; relative speeds
  - K: asymptotic-DoF -- "lonely at distance >= 1/k" IS Class K pin-slot
       saturation for the runner; conjecture IS k-fold saturation
  - N: rational anchor -- 1/k IS the canonical Class N anchor; speeds are
       small-denom rationals when normalized
  - M: HDC bind -- multi-runner system IS Class M k-way bind

Per [[feedback_no_lineage_claims_in_notebook]]: does NOT claim to solve.
"""

import datetime
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.number_theory.lonely_runner.case.v1"
SOURCE_DOI = "https://en.wikipedia.org/wiki/Lonely_runner_conjecture + Barajas-Serra 2008"
SOURCE_PUBLISHED = "2026-05-23"


# Roster: number-of-runners cases k from 2 to 12
# Format: (k, status, anchor, fermata)
ROSTER = [
    (2, "PROVED (trivial)", "k=2 trivial; any speed difference; 1/2 gap available", ""),
    (3, "PROVED", "Wills 1967 / Betke-Wills 1972 (independently)", ""),
    (4, "PROVED", "Cusick-Pomerance 1984; alternative proofs since", ""),
    (5, "PROVED", "Bienia-Goddyn-Gvozdjak-Sebő-Tarsi 1998", ""),
    (6, "PROVED", "Bohman-Holzman-Kleitman 2001", ""),
    (7, "PROVED", "Barajas-Serra 2008 -- Hurwitz heptadic anchor", "Hurwitz heptadic"),
    (8, "OPEN", "open since 2008; Beck-Hopen 2024 partial progress", "OPEN at 8 = first non-proved case"),
    (9, "OPEN", "open", ""),
    (10, "OPEN", "open", ""),
    (11, "OPEN", "open -- 11 = Hurwitz sum 1+3+7", "Hurwitz partition sum coincidence"),
    (12, "OPEN", "open", ""),
]


def main():
    out_path = pathlib.Path(__file__).parent / "case.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for k, status, anchor, fermata in ROSTER:
        is_proved = "PROVED" in status
        is_open = "OPEN" in status

        # Class N anchor: 1/k canonical loneliness threshold
        one_over_k = 1.0 / k
        n_num, n_den = best_rat_signed(one_over_k, max_d=30)

        # Class K saturation: Hurwitz dim?
        is_hurwitz = k in {1, 3, 7}

        payload = json.dumps({"k": k, "status": status}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "k_runners":                int(k),
            "status":                   status,
            "is_proved":                bool(is_proved),
            "is_open":                  bool(is_open),
            "lonely_threshold":         round(one_over_k, 6),
            "threshold_rational_num":   int(n_num),
            "threshold_rational_den":   int(n_den),
            "is_hurwitz_dim":           bool(is_hurwitz),
            "class_cascade":            "A-compose-I-compose-C-compose-J-compose-K-compose-N-compose-M",
            "literature_anchor":        anchor,
            "open_fermata":             fermata,
            "computation_hash":         chash,
            "source_doi":               SOURCE_DOI,
            "source_published_date":    SOURCE_PUBLISHED,
            "entered_locally_at":       now_iso[:10],
        }
        records.append(rec)
        diag.append((k, status, one_over_k, n_num, n_den, is_proved, is_open, is_hurwitz))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    print(f"{'k':>3} {'status':<48} {'1/k':>8} {'Class N':>10} {'Hurwitz?':>9}")
    for d in diag:
        k, status, oover, nn, nd, pr, op, hd = d
        print(f"  {k:>3} {status:<48} {oover:>8.4f} {f'{nn}/{nd}':>10} {str(hd):>9}")

    print()
    proved_count = sum(1 for d in diag if d[5])
    open_count = sum(1 for d in diag if d[6])
    print(f"Proved: {proved_count} / {len(diag)}")
    print(f"Open: {open_count} / {len(diag)}")
    print()
    print("Class K threshold: k=7 PROVED (Hurwitz heptadic anchor); k=8 OPEN (first non-proved)")
    print("Framework reading: Hurwitz boundary at k=7 IS substrate-perfect-math closure;")
    print("k >= 8 IS substrate-DoF inaccessibility per [[project_a_n_operators_are_harmonic_objects_themselves]] §B")


if __name__ == "__main__":
    main()
