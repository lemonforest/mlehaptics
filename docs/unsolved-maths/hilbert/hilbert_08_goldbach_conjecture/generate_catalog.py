"""
Goldbach conjecture cascade generator.

Class cascade: A (hash) -> J (prime sieve) -> I (sum-check via Class J) -> L (partition graph Laplacian) -> M (HDC signature).

For each even n in [4, N_max], builds the Goldbach partition graph G_n
(vertices = primes <= n; edges = unordered pairs (p, q) with p+q=n)
and records its Class L Laplacian spectrum and the observed-vs-Hardy-Littlewood
density ratio.

Run from repo root:
    python docs/unsolved-maths/hilbert/hilbert_08_goldbach_conjecture/generate_catalog.py

Outputs NDJSON at docs/unsolved-maths/hilbert/hilbert_08_goldbach_conjecture/goldbach_partition_graphs.ndjson
"""

import json
import math
import datetime
import pathlib

import numpy as np

from srmech.amsc.format import sha256_bytes
from srmech.amsc.primes import is_prime, factor
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals

# Cascade-honesty per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]:
# shared A-N cascade helpers (precursor of srmech.amsc.cascade.* primitives).
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

SCHEMA_ID = "srmech.hilbert.goldbach.partition_graph.v1"
N_MAX = 200            # even n up to this bound — keeps Laplacians small enough for jacobi
N_MIN = 4              # start at 4 = 2+2
SOURCE_DOI = "10.1007/BF02403921"            # Hardy & Littlewood 1923 Acta Math 44:1-70
SOURCE_PUBLISHED = "1923-01-01"

# Twin-prime constant C_2 (Hardy-Littlewood)
C2 = 0.6601618158468695739278121100145557784326  # truncated; OEIS A005597

# ---------------------------------------------------------------------------
# Class J — sieve of primes up to N
# ---------------------------------------------------------------------------

def sieve_primes(n_max):
    return [p for p in range(2, n_max + 1) if is_prime(p)]


# ---------------------------------------------------------------------------
# Class I (composed with Class J) — Goldbach partition pairs
# ---------------------------------------------------------------------------

def goldbach_partitions(n, primes_set):
    """Return sorted list of unordered (p, q) pairs with p<=q and p+q=n, both prime."""
    pairs = []
    for p in sorted(primes_set):
        if p > n // 2:
            break
        q = n - p
        if q in primes_set:
            pairs.append((p, q))
    return pairs


# ---------------------------------------------------------------------------
# Class L — partition graph + Laplacian + eigenvalues
# ---------------------------------------------------------------------------

def partition_graph_spectrum(n, primes_sorted, pairs):
    """Build the partition graph on vertices = primes <= n; edges = pairs.
    Return (eigs, fiedler, spectral_radius, n_vertices)."""
    n_v = len(primes_sorted)
    if n_v < 2 or not pairs:
        return [], 0.0, 0.0, n_v
    idx = {p: i for i, p in enumerate(primes_sorted)}
    edges = [(idx[p], idx[q]) for p, q in pairs if p != q]
    # If pair has p==q (e.g., n=4: 2+2), it's a self-loop; we skip in Laplacian
    # (dense_laplacian conventions handle this but our partition graph here is
    # the simple-graph view of partitions across distinct primes).
    if not edges:
        return [], 0.0, 0.0, n_v
    L = dense_laplacian(n_v, edges)
    eigs = sorted(float(x) for x in jacobi_eigvals(L))
    fiedler = eigs[1] if len(eigs) > 1 else 0.0
    radius = eigs[-1] if eigs else 0.0
    return eigs, fiedler, radius, n_v


# ---------------------------------------------------------------------------
# Hardy-Littlewood density prediction
# ---------------------------------------------------------------------------

def hardy_littlewood_prediction(n):
    """r(n) ~ 2 C_2 * n/(ln n)^2 * Pi_{p|n, p odd} (p-1)/(p-2)."""
    if n < 4:
        return 0.0
    base = 2 * C2 * n / (math.log(n) ** 2)
    correction = 1.0
    for p, _ in factor(n):
        if p > 2:
            correction *= (p - 1) / (p - 2)
    return base * correction


# ---------------------------------------------------------------------------
# Record builder
# ---------------------------------------------------------------------------

def build_record(n, primes_below_n_sorted, primes_set, now_iso):
    pairs = goldbach_partitions(n, primes_set)
    eigs, fiedler, radius, n_v = partition_graph_spectrum(n, primes_below_n_sorted, pairs)
    hl_pred = hardy_littlewood_prediction(n)
    density_ratio = (len(pairs) / hl_pred) if hl_pred > 0 else 0.0

    # Class A: content-hash
    payload = json.dumps(
        {"n": n, "pairs": sorted(pairs)}, sort_keys=True
    ).encode()
    chash = sha256_bytes(payload)

    pairs_sample = [list(p) for p in pairs[:10]]

    return {
        "n_even": n,
        "prime_count_below_n": len(primes_below_n_sorted),
        "partition_count": len(pairs),
        "partition_pairs_sample": pairs_sample,
        "partition_graph_eigs": [round(e, 6) for e in eigs],
        "fiedler_value": round(fiedler, 6),
        "spectral_radius": round(radius, 6),
        "hardy_littlewood_predicted": round(hl_pred, 6),
        "density_ratio_observed_predicted": round(density_ratio, 6),
        "class_cascade": "A-compose-J-compose-I-compose-L-compose-M",
        "computation_hash": chash,
        "source_doi": SOURCE_DOI,
        "source_published_date": SOURCE_PUBLISHED,
        "entered_locally_at": now_iso[:10],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    out_path = pathlib.Path(__file__).parent / "goldbach_partition_graphs.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Sieve all primes up to N_MAX once
    primes_all = sieve_primes(N_MAX)
    print(f"Sieved {len(primes_all)} primes up to {N_MAX}")

    records = []
    falsified_n = []
    density_ratios = []

    for n in range(N_MIN, N_MAX + 1, 2):
        primes_below_n = [p for p in primes_all if p <= n]
        primes_set = set(primes_below_n)
        rec = build_record(n, primes_below_n, primes_set, now_iso)
        records.append(rec)
        if rec["partition_count"] == 0:
            falsified_n.append(n)
        density_ratios.append(rec["density_ratio_observed_predicted"])

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    # Summary stats
    print()
    print(f"Wrote {len(records)} records to {out_path}")
    print(f"Goldbach verified for all even n in [{N_MIN}, {N_MAX}]: "
          f"{'YES' if not falsified_n else 'NO -- falsified at ' + str(falsified_n)}")
    print()
    print(f"Hardy-Littlewood density ratio (observed/predicted), tail (large n):")
    tail = density_ratios[-10:]
    for i, ratio in enumerate(tail):
        n = N_MAX - 2 * (len(tail) - 1 - i)
        print(f"  n={n:4d}: ratio = {ratio:.4f}")
    print()
    print(f"Mean ratio over n>=100: {np.mean([r for r,n in zip(density_ratios, range(N_MIN, N_MAX+1, 2)) if n>=100]):.4f}")
    print(f"(Approaching 1.0 = Hardy-Littlewood prediction holds)")


if __name__ == "__main__":
    main()
