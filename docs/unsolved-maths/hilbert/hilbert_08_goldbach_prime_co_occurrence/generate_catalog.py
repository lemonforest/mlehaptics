"""
Goldbach prime-co-occurrence cascade.

For each prime p <= N_MAX, count its Goldbach degree = number of even n in
[4, 2*N_MAX] where p appears in SOME partition pair of n. Class L is applied
to the resulting sorted-degree-sequence path graph (aggregate structure).
"""

import json
import datetime
import pathlib

import numpy as np

from srmech.amsc.format import sha256_bytes
from srmech.amsc.primes import is_prime
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals

SCHEMA_ID = "srmech.hilbert.goldbach.prime_co_occurrence.v1"
N_MAX = 200
N_MAX_SEARCH = 2 * N_MAX  # i.e., 400; we ask Goldbach for n up to 400
SOURCE_DOI = "10.1007/BF02403921"
SOURCE_PUBLISHED = "1923-01-01"


def sieve_primes(n):
    return [p for p in range(2, n + 1) if is_prime(p)]


def goldbach_degree_per_prime(primes, n_max_search):
    """For each prime, count even n where it appears in any partition."""
    primes_set = set(primes)
    degrees = {p: 0 for p in primes}
    even_n_list = list(range(4, n_max_search + 1, 2))
    for n in even_n_list:
        primes_used_for_this_n = set()
        for p in primes:
            if p > n // 2:
                break
            q = n - p
            if q in primes_set:
                primes_used_for_this_n.add(p)
                primes_used_for_this_n.add(q)
        for p in primes_used_for_this_n:
            degrees[p] += 1
    return degrees, len(even_n_list)


def main():
    out_path = pathlib.Path(__file__).parent / "prime_co_occurrence.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    primes = sieve_primes(N_MAX)
    print(f"Sieved {len(primes)} primes up to {N_MAX}")
    degrees, even_n_count = goldbach_degree_per_prime(primes, N_MAX_SEARCH)
    print(f"Computed Goldbach degrees over {even_n_count} even n in [4, {N_MAX_SEARCH}]")

    # Rank by degree
    sorted_primes = sorted(primes, key=lambda p: degrees[p])
    rank = {p: i + 1 for i, p in enumerate(sorted_primes)}

    # Class L: build path graph on primes sorted by degree, weighted by absolute degree-diff
    # to surface "jumps" in the degree sequence
    sorted_degrees = [degrees[p] for p in sorted_primes]
    n_v = len(sorted_primes)
    edges = [(i, i + 1) for i in range(n_v - 1)]
    weights = [abs(sorted_degrees[i + 1] - sorted_degrees[i]) + 1.0 for i in range(n_v - 1)]
    L = dense_laplacian(n_v, edges, weights)
    eigs = sorted(float(x) for x in jacobi_eigvals(L))

    records = []
    for p in primes:
        payload = json.dumps({"prime": p, "degree": degrees[p]}, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        records.append({
            "prime": p,
            "n_max_search": N_MAX_SEARCH,
            "even_n_count": even_n_count,
            "goldbach_degree": degrees[p],
            "degree_normalized": round(degrees[p] / even_n_count, 6),
            "rank_in_degree_sequence": rank[p],
            "class_cascade": "A-compose-J-compose-I-compose-L",
            "computation_hash": chash,
            "source_doi": SOURCE_DOI,
            "source_published_date": SOURCE_PUBLISHED,
            "entered_locally_at": now_iso[:10],
        })

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print("Degree-sequence statistics:")
    print(f"  Min degree: prime {sorted_primes[0]} -> {sorted_degrees[0]} of {even_n_count} ({100*sorted_degrees[0]/even_n_count:.1f}%)")
    print(f"  Max degree: prime {sorted_primes[-1]} -> {sorted_degrees[-1]} of {even_n_count} ({100*sorted_degrees[-1]/even_n_count:.1f}%)")
    print(f"  Mean degree: {np.mean(sorted_degrees):.1f} of {even_n_count}")
    print(f"  Std degree: {np.std(sorted_degrees):.1f}")
    print()
    print(f"Class L (path Laplacian on sorted-degree-difference-weighted graph) spectrum:")
    print(f"  Eigenvalues: min={eigs[0]:.4f}, fiedler={eigs[1]:.4f}, max={eigs[-1]:.4f}")
    print(f"  Number of zero eigenvalues (connected components): {sum(1 for e in eigs if abs(e) < 1e-9)}")


if __name__ == "__main__":
    main()
