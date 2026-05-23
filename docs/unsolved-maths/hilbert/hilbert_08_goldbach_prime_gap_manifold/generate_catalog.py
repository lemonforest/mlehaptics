"""
Prime gap manifold cascade.

For each consecutive prime pair (p_i, p_{i+1}) up to N_MAX, record gap g_i,
Cramer-normalized gap g_i / log(p_i). Class L applied to gap-weighted path
graph on primes (aggregate). Composes with twin-prime cascade (gap=2 special case).
"""

import json
import math
import datetime
import pathlib
from collections import Counter

import numpy as np

from srmech.amsc.format import sha256_bytes
from srmech.amsc.primes import is_prime
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals

SCHEMA_ID = "srmech.hilbert.goldbach.prime_gap_manifold.v1"
N_MAX = 2000
SOURCE_DOI = "10.4064/aa-2-1-23-46"   # Cramér 1936 Acta Arithmetica
SOURCE_PUBLISHED = "1936-01-01"


def sieve_primes(n):
    return [p for p in range(2, n + 1) if is_prime(p)]


def main():
    out_path = pathlib.Path(__file__).parent / "prime_gap_manifold.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    primes = sieve_primes(N_MAX)
    print(f"Sieved {len(primes)} primes up to {N_MAX}")

    records = []
    gaps = []
    norm_gaps = []

    for i in range(len(primes) - 1):
        p_low = primes[i]
        p_high = primes[i + 1]
        gap = p_high - p_low
        log_p = math.log(p_low)
        norm_gap = gap / log_p
        gaps.append(gap)
        norm_gaps.append(norm_gap)

        payload = json.dumps({"p_low": p_low, "p_high": p_high, "gap": gap}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        records.append({
            "prime_index": i + 1,
            "prime_low": p_low,
            "prime_high": p_high,
            "gap": gap,
            "gap_normalized": round(norm_gap, 6),
            "log_prime_low": round(log_p, 6),
            "class_cascade": "A-compose-J-compose-I-compose-L-compose-K",
            "computation_hash": chash,
            "source_doi": SOURCE_DOI,
            "source_published_date": SOURCE_PUBLISHED,
            "entered_locally_at": now_iso[:10],
        })

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    # Class L: weighted path Laplacian; edge weight = gap value itself
    n_v = len(primes)
    edges = [(i, i + 1) for i in range(n_v - 1)]
    weights = [float(g) for g in gaps]
    L = dense_laplacian(n_v, edges, weights)
    eigs = sorted(float(x) for x in jacobi_eigvals(L))

    # Class K asymptotic-DoF: gap distribution
    gap_counts = Counter(gaps)
    twin_count = gap_counts.get(2, 0)

    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print("Gap statistics:")
    print(f"  Min gap: {min(gaps)} (twin primes — {twin_count} pairs)")
    print(f"  Max gap: {max(gaps)}")
    print(f"  Mean gap: {np.mean(gaps):.3f}")
    print(f"  Mean normalized gap (g/log p): {np.mean(norm_gaps):.4f}  (Cramer-asymptotic ~1)")
    print()
    print(f"Top-5 most common gaps: {gap_counts.most_common(5)}")
    print()
    print(f"Class L weighted-path Laplacian spectrum:")
    print(f"  Eigenvalues: min={eigs[0]:.4f}, fiedler={eigs[1]:.4f}, max={eigs[-1]:.4f}")
    print(f"  Spectral gap (fiedler / max): {eigs[1]/eigs[-1]:.6f}")
    print(f"  Effective resistance proxy (max/fiedler ratio): {eigs[-1]/eigs[1]:.4f}")


if __name__ == "__main__":
    main()
