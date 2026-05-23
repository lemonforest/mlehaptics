"""
Lehmer's totient problem cascade.

Question (Lehmer 1932): Is there a COMPOSITE integer n such that phi(n)
divides (n - 1)?

If n is prime, then phi(n) = n - 1 and trivially phi(n) | (n-1). Lehmer
conjectured: NO COMPOSITE n satisfies this. Equivalent to: phi(n) | (n-1)
implies n is prime.

If such an n exists, it must be:
  - squarefree (Lehmer)
  - have at least 14 prime factors (Cohen-Hagis 1980)
  - n > 10^22 (Pinch et al; later extended)
  - omega(n) >= 14 prime factors

Status: NO COMPOSITE SOLUTION FOUND. OPEN.

Class cascade: A o J o I o K o N o M

  - A: content-hash of (n, phi(n), (n-1)/phi(n) ratio)
  - J: phi IS Euler totient -- Class J primes primitive (multiplicative)
  - I: cyclic structure of (Z/nZ)^*
  - K: pin-slot at composite n where phi(n) | (n-1); conjecture IS Class K
       NO-SATURATION predicate
  - N: rational anchor (n-1)/phi(n)
  - M: HDC bind across prime-factor count

Per [[feedback_no_lineage_claims_in_notebook]].
"""

import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes


def phi(n):
    """Euler totient via prime factorization."""
    if n < 1:
        return 0
    if n == 1:
        return 1
    result = n
    p = 2
    n_work = n
    while p * p <= n_work:
        if n_work % p == 0:
            while n_work % p == 0:
                n_work //= p
            result -= result // p
        p += 1
    if n_work > 1:
        result -= result // n_work
    return result


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


def main():
    out_path = pathlib.Path(__file__).parent / "lehmer.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Test all n in 2..200 + selected larger values
    test_range = list(range(2, 201))
    test_range += [1000, 10000, 100000, 1000000]

    records = []
    diag = []
    composite_satisfying_count = 0

    for n in test_range:
        phi_n = phi(n)
        prime_n = is_prime(n)
        # Lehmer condition: phi(n) divides (n - 1)
        if phi_n > 0:
            divides = ((n - 1) % phi_n == 0)
            ratio_num = n - 1
            ratio_den = phi_n
        else:
            divides = False
            ratio_num = 0
            ratio_den = 1

        # COUNTER-EXAMPLE TEST: composite n with phi(n) | (n-1)?
        is_lehmer_counterexample = (not prime_n) and divides and n > 1
        if is_lehmer_counterexample:
            composite_satisfying_count += 1

        payload = json.dumps({"n": n, "phi": phi_n}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "n":                          int(n),
            "phi_n":                      int(phi_n),
            "is_prime":                   bool(prime_n),
            "phi_divides_n_minus_1":      bool(divides),
            "ratio_num":                  int(ratio_num),
            "ratio_den":                  int(ratio_den),
            "is_lehmer_counterexample":   bool(is_lehmer_counterexample),
            "class_cascade":              "A-compose-J-compose-I-compose-K-compose-N-compose-M",
            "literature_anchor":          "self-computed phi via prime-factorization",
            "open_fermata":               "" if not is_lehmer_counterexample else "POTENTIAL LEHMER COUNTEREXAMPLE",
            "computation_hash":           chash,
            "source_doi":                 "https://en.wikipedia.org/wiki/Lehmer%27s_totient_problem",
            "source_published_date":      "2026-05-23",
            "entered_locally_at":         now_iso[:10],
        }
        records.append(rec)
        diag.append((n, phi_n, prime_n, divides, is_lehmer_counterexample))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print(f"Composite n with phi(n) | (n-1) found in roster: {composite_satisfying_count}")
    print(f"(Lehmer's conjecture: this count should be 0)")
    print()
    # Show all primes verified trivially
    prime_count = sum(1 for d in diag if d[2])
    prime_divides_count = sum(1 for d in diag if d[2] and d[3])
    print(f"Primes in roster: {prime_count}")
    print(f"  Primes where phi(p) = p-1 divides p-1 trivially: {prime_divides_count} (should equal {prime_count})")
    print()
    if composite_satisfying_count == 0:
        print("VERDICT: Lehmer's conjecture holds across roster (NO composite counterexample).")
        print("Conjecture remains OPEN for general n; verified to enormous bounds in literature.")


if __name__ == "__main__":
    main()
