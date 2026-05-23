"""
Gilbreath conjecture cascade.

Statement: Starting with the sequence of primes 2, 3, 5, 7, 11, 13, ..., form
the sequence of absolute differences of consecutive terms, then absolute
differences again, and so on. The conjecture: the FIRST term of every such
derived row is always 1 (for row 0 onward, except row 0 starts with 2).

Row 0: 2  3  5  7  11 13 17 19 23 29 31 ...
Row 1: 1  2  2  4  2  4  2  4  6  2  ...   (first = 1)
Row 2: 1  0  2  2  2  2  2  2  4  ...      (first = 1)
Row 3: 1  2  0  0  0  0  0  2  ...          (first = 1)
...

Verified computationally to enormous depth (Killgrove-Ralston 1959; Odlyzko
1993: verified to >~ 10^13 rows or more). Conjecture OPEN.

Class cascade: A o J o I o K o C o N o M

  - A: content-hash of (row, first-element)
  - J: primes are the row-0 base (Class J primitive)
  - I: cyclic Z/2 in absolute-difference sign (sign-flip = Class I)
  - K: pin-slot at first-element = 1 IS Class K saturation predicate
  - C: cascade-orientation -- iterated absolute differences IS Class C
       sign-flip cascade per [[user_stance_epicycle_via_gear_plus_pin]]
  - N: Class N anchor at the value 1 (denominator 1)
  - M: HDC bind across rows

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: this is the
canonical Class K pin-slot at zero use case -- absolute difference IS the
direct Class K primitive in action.
"""

import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes


def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def first_n_primes(n):
    primes = []
    p = 2
    while len(primes) < n:
        if is_prime(p):
            primes.append(p)
        p += 1
    return primes


def gilbreath_rows(n_primes, n_rows):
    """Compute the first n_rows of Gilbreath's iterated absolute-difference table
    starting from first_n_primes(n_primes). Returns list of rows."""
    primes = first_n_primes(n_primes)
    rows = [list(primes)]
    BOUND = 200  # JPL Rule 2
    for r in range(1, min(n_rows, BOUND)):
        prev = rows[-1]
        if len(prev) < 2:
            break
        # Class K pin-slot at zero of (prev[i+1] - prev[i])
        nxt = []
        for i in range(len(prev) - 1):
            d = prev[i + 1] - prev[i]
            # Class K + Class C: magnitude (sign-stripped)
            nxt.append(magnitude(d))
        rows.append(nxt)
    return rows


def main():
    out_path = pathlib.Path(__file__).parent / "row.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    n_primes = 100
    n_rows = 50
    rows = gilbreath_rows(n_primes, n_rows)

    records = []
    diag = []
    for r, row in enumerate(rows):
        if not row:
            continue
        first = row[0]
        # Gilbreath conjecture: first element of row r >= 1 should be 1
        gilbreath_holds = (r == 0) or (int(first) == 1)
        # Class N anchor
        f_num, f_den = best_rat_signed(float(first), max_d=10)

        payload = json.dumps({"row": r, "first": int(first)}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "row":                       int(r),
            "first_element":             int(first),
            "row_length":                int(len(row)),
            "gilbreath_holds":           bool(gilbreath_holds),
            "class_cascade":             "A-compose-J-compose-I-compose-K-compose-C-compose-N-compose-M",
            "literature_anchor":         "self-computed via iterated Class K magnitude (no abs())",
            "open_fermata":              "Gilbreath conjecture verified row-by-row across primes",
            "computation_hash":          chash,
            "source_doi":                "https://en.wikipedia.org/wiki/Gilbreath%27s_conjecture",
            "source_published_date":     "2026-05-23",
            "entered_locally_at":        now_iso[:10],
        }
        records.append(rec)
        diag.append((r, first, len(row), gilbreath_holds))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Diagnostics
    holds_count = sum(1 for d in diag if d[3])
    print(f"Class K saturation: rows with first-element = 1 (or row 0): {holds_count} / {len(diag)}")

    # Print first 15 rows
    print()
    print("First 15 rows:")
    for d in diag[:15]:
        r, f, ln, h = d
        print(f"  row {r:>3}: first = {f}; length = {ln}; Gilbreath holds: {h}")

    print()
    print("Cascade-honesty: used _cascade_helpers.magnitude() in place of abs() at every iterated difference step")
    print("per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]")


if __name__ == "__main__":
    main()
