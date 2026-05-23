"""
Skewes number cascade.

Question: Where does pi(x) first exceed Li(x)? (Where does the sign of
Li(x) - pi(x) first change?)

The Prime Number Theorem predicts pi(x) ~ Li(x); Riemann initially conjectured
pi(x) < Li(x) always. Littlewood 1914 PROVED that Li(x) - pi(x) changes sign
infinitely often. Skewes 1933 gave first explicit upper bound on x at which
the first crossing occurs (~ 10^{10^{10^34}}); successive refinements have
dramatically reduced this bound but NO ONE has pinpointed the exact crossing
location.

Class cascade: A o J o L o K o N o M

  - A: content-hash of bound + year
  - J: primes -- pi(x) counts primes
  - L: Li(x) IS the logarithmic-integral function (Class L)
  - K: pin-slot at zero of Li(x) - pi(x); conjecture IS the sign-change location
  - N: rational anchor in the bound exponent structure
  - M: HDC bind across iterated upper-bound improvements

Per [[feedback_no_lineage_claims_in_notebook]].
"""

import datetime
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes


# Roster: known upper bounds on Skewes number across history
# (label, year, log_bound, anchor, fermata)
ROSTER = [
    dict(label="Skewes 1933 (assuming RH)", year=1933, log_bound=10**34,
         anchor="Skewes 1933 -- first upper bound; assumed Riemann Hypothesis",
         fermata="~ 10^{10^{10^34}}; astronomically large"),
    dict(label="Skewes 1955 (no RH)", year=1955, log_bound=10**963,
         anchor="Skewes 1955 -- unconditional bound",
         fermata="~ 10^{10^{10^963}}; even larger without RH"),
    dict(label="Lehman 1966", year=1966, log_bound=1.65e1165,
         anchor="Lehman 1966 -- first improvement",
         fermata="~ 1.65 * 10^{1165}"),
    dict(label="te Riele 1987", year=1987, log_bound=6.658e370,
         anchor="te Riele 1987",
         fermata="~ 6.658 * 10^{370}"),
    dict(label="Bays-Hudson 2000", year=2000, log_bound=1.397e316,
         anchor="Bays-Hudson 2000 -- current best published bound",
         fermata="~ 1.397 * 10^{316}; current best (defensive)"),
    dict(label="Lower bound: x > 10^19", year=2025, log_bound=10**19,
         anchor="Computational verification: first crossing has NOT occurred by x = 10^19",
         fermata="lower bound; first crossing somewhere between 10^19 and 1.397 * 10^316"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "bound.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        label = entry["label"]
        year = entry["year"]
        bound = entry["log_bound"]
        anchor = entry["anchor"]
        fermata = entry["fermata"]

        # Use log10 of bound; for absurdly large int bounds, compute log10 via integer length
        if isinstance(bound, int):
            log_log_bound = float(len(str(bound)) - 1)  # rough log10 for huge ints
            bound_repr = f"~10^{int(log_log_bound)}"
        elif bound > 0:
            log_log_bound = math.log10(bound)
            bound_repr = f"{bound:.4e}"
        else:
            log_log_bound = 0.0
            bound_repr = "0"

        payload = json.dumps({"label": label, "year": year}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "label":                   label,
            "year":                    int(year),
            "bound_repr":              bound_repr,
            "log10_bound":             round(log_log_bound, 4),
            "class_cascade":           "A-compose-J-compose-L-compose-K-compose-N-compose-M",
            "literature_anchor":       anchor,
            "open_fermata":            fermata,
            "computation_hash":        chash,
            "source_doi":              "https://en.wikipedia.org/wiki/Skewes%27s_number",
            "source_published_date":   "2026-05-23",
            "entered_locally_at":      now_iso[:10],
        }
        records.append(rec)
        diag.append((label, year, bound, log_log_bound))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print(f"{'label':<40} {'year':>6} {'log10(bound)':>14}")
    for d in diag:
        print(f"  {d[0]:<40} {d[1]:>6} {d[3]:>14.4f}")


if __name__ == "__main__":
    main()
