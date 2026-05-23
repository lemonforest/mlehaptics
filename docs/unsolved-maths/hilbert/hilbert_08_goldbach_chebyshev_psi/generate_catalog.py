"""
Chebyshev psi-function cascade.

psi(N) = sum_{p^k <= N} log(p) over all prime powers up to N.
Sample at N = STEP, 2*STEP, ..., N_MAX. Residual psi(N) - N is the
prime-distribution loop's line-projection per [[user_stance_fiber_as_spatially_absent_encoding]].

RH equivalent: psi(N) - N = O(sqrt(N) * log^2(N)).
"""

import json
import math
import datetime
import pathlib

import numpy as np

from srmech.amsc.format import sha256_bytes
from srmech.amsc.primes import is_prime
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals

SCHEMA_ID = "srmech.hilbert.goldbach.chebyshev_psi.v1"
N_MAX = 2000
STEP = 20
SOURCE_DOI = "10.24033/asens.184"   # Hadamard 1896 zeta-function paper; placeholder DOI for PNT
SOURCE_PUBLISHED = "1896-01-01"


def sieve_primes(n):
    return [p for p in range(2, n + 1) if is_prime(p)]


def chebyshev_psi(N, primes_all):
    """psi(N) = sum_{p^k <= N} log(p)."""
    total = 0.0
    for p in primes_all:
        if p > N:
            break
        pk = p
        while pk <= N:
            total += math.log(p)
            pk *= p
    return total


def main():
    out_path = pathlib.Path(__file__).parent / "chebyshev_psi.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    primes_all = sieve_primes(N_MAX)
    print(f"Sieved {len(primes_all)} primes up to {N_MAX}")

    samples = list(range(STEP, N_MAX + 1, STEP))
    psi_values = []
    residuals = []
    rel_residuals = []
    records = []

    for N in samples:
        psi_N = chebyshev_psi(N, primes_all)
        resid = psi_N - N
        rel_resid = resid / math.sqrt(N) if N > 0 else 0.0
        n_primes = sum(1 for p in primes_all if p <= N)
        psi_values.append(psi_N)
        residuals.append(resid)
        rel_residuals.append(rel_resid)

        payload = json.dumps({"N": N, "psi": round(psi_N, 6)}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        records.append({
            "N_sample": N,
            "psi_value": round(psi_N, 6),
            "residual": round(resid, 6),
            "rel_residual": round(rel_resid, 6),
            "primes_below_N": n_primes,
            "class_cascade": "A-compose-J-compose-L-compose-K",
            "computation_hash": chash,
            "source_doi": SOURCE_DOI,
            "source_published_date": SOURCE_PUBLISHED,
            "entered_locally_at": now_iso[:10],
        })

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    # Class L: path graph on residual time series; weight = |delta_residual|
    n_v = len(samples)
    edges = [(i, i + 1) for i in range(n_v - 1)]
    weights = [abs(residuals[i + 1] - residuals[i]) + 1.0 for i in range(n_v - 1)]
    L = dense_laplacian(n_v, edges, weights)
    eigs = sorted(float(x) for x in jacobi_eigvals(L))

    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print("Chebyshev psi sample statistics:")
    print(f"  N range: [{samples[0]}, {samples[-1]}]")
    print(f"  psi range: [{psi_values[0]:.2f}, {psi_values[-1]:.2f}]")
    print(f"  residual at N_max: {residuals[-1]:.4f}")
    print(f"  rel_residual at N_max: {rel_residuals[-1]:.4f}  (RH bound is O(log^2 N) = O({math.log(N_MAX)**2:.1f}))")
    print(f"  mean |rel_residual|: {np.mean(np.abs(rel_residuals)):.4f}")
    print()
    print(f"Class L path-Laplacian (residual-weighted) spectrum:")
    print(f"  Eigenvalues: min={eigs[0]:.4f}, fiedler={eigs[1]:.4f}, max={eigs[-1]:.4f}")
    print(f"  Spectral gap (fiedler/max): {eigs[1]/eigs[-1]:.6f}")


if __name__ == "__main__":
    main()
