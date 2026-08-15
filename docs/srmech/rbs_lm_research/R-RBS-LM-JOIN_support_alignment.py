#!/usr/bin/env python3
"""R-RBS-LM-JOIN — verify the support_aligned_rows cascade descriptor (F1342).

Runs every [[cascade.chain.proof_cases]] declared in
cascade_catalog/support_aligned_rows.toml through srmech.dsl.run_cascade_chain
and compares the emitted F_2 parity rows against a reference computed by an
INDEPENDENT code path in this file:

  * its own trial-division factorizer (not srmech.math.primes.factor),
  * its own support-union + canonical sort (not the lcm identity the
    descriptor uses — a genuinely different route to the same object),
  * its own GF(2) rank via bitmask XOR elimination (not gf_rref).

The srmech gf_rref rank of the emitted rows is additionally checked against
the independent rank, closing the loop the f2_rank descriptor consumes.

Exit status: 0 iff every case matches on rows AND both ranks agree.
Exact-integer arithmetic throughout; stdlib only.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG_DIR = HERE / "cascade_catalog"
DESCRIPTOR = CATALOG_DIR / "support_aligned_rows.toml"
CHAIN_NAME = "support_aligned_rows"


# ── independent reference path (deliberately NOT the descriptor's route) ────

def ref_factor(n: int) -> list[tuple[int, int]]:
    """Trial-division factorization, ascending primes. Independent of srmech."""
    if n < 1:
        raise ValueError(f"radicand must be >= 1; got {n}")
    out: list[tuple[int, int]] = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            e = 0
            while n % d == 0:
                n //= d
                e += 1
            out.append((d, e))
        d += 1
    if n > 1:
        out.append((n, 1))
    return out


def ref_rows(ns: list[int]) -> tuple[list[int], list[list[int]]]:
    """Union support (sorted) + parity rows, via explicit set-union — the
    route the descriptor deliberately does NOT take."""
    facts = [ref_factor(n) for n in ns]
    support: set[int] = set()
    for f in facts:
        for p, _e in f:
            support.add(p)
    union = sorted(support)
    rows = []
    for f in facts:
        exp = {p: e for p, e in f}
        rows.append([exp.get(q, 0) % 2 for q in union])
    return union, rows


def ref_rank_gf2(rows: list[list[int]]) -> int:
    """GF(2) rank by bitmask XOR elimination. Independent of gf_rref."""
    basis: list[int] = []
    for row in rows:
        v = 0
        for bit in row:
            v = (v << 1) | (bit & 1)
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


# ── the cascade under test ──────────────────────────────────────────────────

def main() -> int:
    import srmech.dsl as D
    from srmech.math.modular_linalg import gf_rref

    D.register_catalog_dir(str(CATALOG_DIR))

    with DESCRIPTOR.open("rb") as fh:
        doc = tomllib.load(fh)
    cases = doc["cascade"]["chain"][0]["proof_cases"]

    failures = 0
    for case in cases:
        covers = case["covers"]
        ns = case["inputs"]["ns"]
        union, expected_rows = ref_rows(ns)
        expected_rank = ref_rank_gf2(expected_rows)

        got_rows = D.run_cascade_chain(CHAIN_NAME, {"ns": ns})
        got_rank = gf_rref(got_rows, 2)["rank"] if got_rows and got_rows[0] else 0

        row_ok = got_rows == expected_rows
        rank_ok = got_rank == expected_rank
        ok = row_ok and rank_ok
        failures += 0 if ok else 1

        tag = "ok  " if ok else "FAIL"
        print(f"{tag} {covers}: ns={ns}")
        print(f"     union support = {union}")
        for n, row in zip(ns, got_rows):
            print(f"     {n} -> {row}")
        print(f"     rank: cascade+gf_rref={got_rank} independent={expected_rank}")
        if not row_ok:
            print(f"     EXPECTED ROWS: {expected_rows}")

    total = len(cases)
    print(f"\n{total - failures}/{total} proof cases ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
