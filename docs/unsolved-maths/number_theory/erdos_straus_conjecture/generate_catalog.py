"""
Erdős-Straus conjecture cascade.

Statement: For every integer n >= 2, there exist positive integers a, b, c
such that 4/n = 1/a + 1/b + 1/c.

Class cascade: A o I o J o C o K o N o M

  - A: content-hash of (n, a, b, c) decomposition tuple
  - I: cyclic -- residue class n mod 24 determines which "easy" decomposition
       formula applies; non-trivial cases concentrate at n ≡ 1 (mod 24)
  - J: primes -- the conjectured-hard cases are prime n with n ≡ 1 (mod 24)
  - C: cascade-orientation -- symmetric (a=b=c) vs asymmetric decompositions;
       Mordell 1967 closed-form formulas use n mod 840 partition (Class C
       orientation over the prime-residue cascade)
  - K: asymptotic-DoF -- finding ANY decomposition saturates the pin-slot at
       "decomposition exists for this n"; conjecture IS Class K saturation
       for every n >= 2
  - N: rational anchor -- 4/n IS a Class N anchor; 1/a, 1/b, 1/c are unit-
       fraction Class N anchors at denominators a, b, c
  - M: HDC bind -- three-way unit-fraction composition IS Class M ternary bind

Per [[project_a_n_operators_are_harmonic_objects_themselves]] §A: tests whether
(i) the mod-24 residue partition IS Class I cyclic primitive (24 = 2^3 * 3 =
LCM of small primes 1,2,3,4,5,6,7,8 except 5 and 7), and (ii) the hard cases
n ≡ 1 (mod 24) cluster at framework Hurwitz-related residue classes.

Per [[feedback_no_lineage_claims_in_notebook]]: does NOT claim to solve
Erdős-Straus. Documents structural cascade decomposition + empirical 4/n =
1/a + 1/b + 1/c decompositions across a representative roster + Class I mod-24
residue partition.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
via shared _cascade_helpers (best_rat_signed for Class N; cyclic_gcd for Class I).

Roster: n in {2, 3, ..., 24, plus primes n ≡ 1 mod 24 up to ~10^3 + large
verification records}. Decompositions found by bounded search.
"""

import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.number_theory.erdos_straus.decomposition.v1"
SOURCE_DOI = "https://en.wikipedia.org/wiki/Erdős–Straus_conjecture + Mordell 1967 + Allan Swett 1999"
SOURCE_PUBLISHED = "2026-05-23"


def is_prime_small(n):
    """Trial-division primality test (bounded; for small n in roster)."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    d = 3
    BOUND = 100000
    while d * d <= n and d < BOUND:
        if n % d == 0:
            return False
        d += 2
    return True


def find_decomposition(n, a_max=None):
    """Find positive integers (a, b, c) such that 4/n = 1/a + 1/b + 1/c.

    Bounded search over a from ceil(n/4) to a_max (default 4*n). For each a,
    solve 4/n - 1/a = (4a - n)/(n*a) and find pair (b, c) decomposing it as
    1/b + 1/c by trying small b. Returns (a, b, c) or None.
    """
    if n < 2:
        return None
    if a_max is None:
        a_max = max(100, 4 * n)
    # The minimum a satisfies 1/a >= 4/(3n) (each of 1/a, 1/b, 1/c at most 1/a),
    # so a <= 3n/4. Try from ceil(n/4) upward.
    a_lo = max(1, (n + 3) // 4)
    a_hi = min(a_max, 4 * n)
    BOUND_A = 10000  # JPL Rule 2 bound
    BOUND_B = 100000
    a_hi = min(a_hi, BOUND_A)
    for a in range(a_lo, a_hi + 1):
        # 4/n - 1/a = (4a - n) / (n * a)
        num = 4 * a - n
        den = n * a
        if num <= 0:
            continue
        # Need 1/b + 1/c = num/den with b <= c
        # b satisfies b > den / num (so 1/b < num/den) and b <= 2*den/num
        b_lo = den // num + 1
        b_hi = (2 * den) // num
        b_hi = min(b_hi, BOUND_B)
        for b in range(max(a, b_lo), b_hi + 1):
            # 1/c = num/den - 1/b = (b*num - den) / (b*den)
            c_num = b * num - den
            c_den = b * den
            if c_num <= 0:
                continue
            if c_den % c_num == 0:
                c = c_den // c_num
                if c >= b:
                    return (a, b, c)
    return None


# Roster: representative n values
ROSTER_N = [
    # Small baselines (each m = n mod 24 represented)
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,

    # Primes n ≡ 1 mod 24 (the "hard" Erdős-Straus residue class)
    73, 97, 193, 241, 313, 337, 409, 433, 457, 577, 601, 673, 769, 937,

    # Large verification record placeholder (Allan Swett 1999 verified up to 10^14)
    # Use a representative large value for which decomposition exists:
    1000000007,  # large prime; Erdős-Straus verified
]


def main():
    out_path = pathlib.Path(__file__).parent / "decomposition.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for n in ROSTER_N:
        # Class I cyclic: n mod 24
        n_mod_24 = n % 24
        is_prime_n = is_prime_small(n) if n < 10000 else (n == 1000000007)
        hard_class = is_prime_n and (n_mod_24 == 1) and n >= 13

        # Try to find decomposition (skip the huge n for in-script search)
        if n <= 1000:
            decomp = find_decomposition(n)
        else:
            decomp = None  # too large for in-script search; rely on attestation

        if decomp:
            a, b, c = decomp
            # Verify bit-exact: 1/a + 1/b + 1/c = 4/n
            # 4/n = 1/a + 1/b + 1/c <=> 4*a*b*c = n*(b*c + a*c + a*b)
            verify = (4 * a * b * c == n * (b * c + a * c + a * b))
        else:
            a, b, c = 0, 0, 0
            verify = False

        # Class N anchors: 1/a, 1/b, 1/c rationals
        # Sum 1/a + 1/b + 1/c best-rational (should be 4/n bit-exact)
        if a > 0 and b > 0 and c > 0:
            # Verify symbolically: a*b*c * 4/n = b*c + a*c + a*b
            lhs = 4 * a * b * c
            rhs = n * (b * c + a * c + a * b)
            arithmetic_ok = (lhs == rhs)
        else:
            arithmetic_ok = False

        # Class C cascade-orientation: symmetric (a=b=c) or asymmetric?
        is_symmetric = (a == b == c) if a > 0 else False
        # Two-equal case (a, a, c) or (a, b, b)?
        is_two_equal = (a == b or b == c) if a > 0 else False

        payload = json.dumps({"n": n, "a": a, "b": b, "c": c}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        if hard_class:
            anchor = f"prime n = {n} with n ≡ 1 (mod 24); 'hard' residue class"
            fermata = "Erdős-Straus 'hard' case; computational verification only"
        else:
            anchor = f"n = {n}; n mod 24 = {n_mod_24}; easy mod-class"
            fermata = ""

        rec = {
            "n":                          int(n),
            "n_mod_24":                   int(n_mod_24),
            "is_prime":                   bool(is_prime_n),
            "is_hard_class":              bool(hard_class),
            "a":                          int(a),
            "b":                          int(b),
            "c":                          int(c),
            "decomposition_found":        bool(decomp is not None),
            "verified_bit_exact":         bool(verify),
            "arithmetic_ok":              bool(arithmetic_ok),
            "is_symmetric_abc":           bool(is_symmetric),
            "is_two_equal":               bool(is_two_equal),
            "class_cascade":              "A-compose-I-compose-J-compose-C-compose-K-compose-N-compose-M",
            "literature_anchor":          anchor,
            "open_fermata":               fermata,
            "computation_hash":           chash,
            "source_doi":                 SOURCE_DOI,
            "source_published_date":      SOURCE_PUBLISHED,
            "entered_locally_at":         now_iso[:10],
        }
        records.append(rec)
        diag.append((n, n_mod_24, is_prime_n, hard_class, a, b, c, decomp is not None,
                     verify, is_symmetric, is_two_equal))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Diagnostics
    print(f"{'n':>12} {'n%24':>5} {'prime?':>7} {'hard?':>6} {'a':>8} {'b':>8} {'c':>10} {'found':>6} {'verify':>7} {'sym':>5} {'2eq':>5}")
    for d in diag:
        n, m24, pr, hd, a, b, c, found, ver, sym, t2 = d
        print(f"  {n:>10} {m24:>5} {str(pr):>7} {str(hd):>6} {a:>8} {b:>8} {c:>10} {str(found):>6} {str(ver):>7} {str(sym):>5} {str(t2):>5}")

    # Class K saturation: how many n have decompositions?
    print()
    n_found = sum(1 for d in diag if d[7])
    print(f"Class K saturation test: decompositions found for n / total: {n_found} / {len(diag)}")
    if n_found == len(diag):
        print("  100% saturation (all in-script-search n have decompositions)")
    else:
        n_missing = [d[0] for d in diag if not d[7]]
        print(f"  Missing: {n_missing} (large n; relies on Allan Swett 1999 verification)")

    # Class I cyclic: mod-24 residue distribution
    print()
    print("Class I cyclic mod-24 residue distribution:")
    mod_counts = {}
    for d in diag:
        mod_counts[d[1]] = mod_counts.get(d[1], 0) + 1
    for m, c in sorted(mod_counts.items()):
        tag = ""
        if m == 1:
            tag = " <-- hard residue class for prime n"
        print(f"  n mod 24 = {m:>2}: {c} entries{tag}")

    # Hard-class verification: did we find decompositions for n ≡ 1 mod 24 primes?
    print()
    hard_entries = [d for d in diag if d[3]]
    if hard_entries:
        hard_found = sum(1 for d in hard_entries if d[7])
        print(f"Hard class (prime n == 1 mod 24) decompositions found: {hard_found} / {len(hard_entries)}")


if __name__ == "__main__":
    main()
