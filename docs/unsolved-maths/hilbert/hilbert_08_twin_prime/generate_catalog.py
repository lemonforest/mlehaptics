"""
Twin Prime cascade — A o J o K o I o M.

For twin pairs (p, p+2) with p <= N_MAX, record:
  - residues mod primorials {6, 30, 210}  (Class I)
  - cumulative density observed_to_p divided by p/(log p)^2  (Class K)
  - density residual against Hardy-Littlewood 2*C_2  (Class K asymptotic-DoF)
  - HDC-bundled per-scale residue signatures + cross-scale similarity  (Class M)

Per [[feedback_dont_pre_commit_spike_query_operators]]: cascade aims to detect a
scale-invariant residue signature across primorial moduli. Tautology pre-filter
in place: residue classes containing primes >= 5 are restricted by definition to
the units mod each primorial, so the cascade reports the empirical concentration
within those units, not the trivial "primes coprime to primorial" fact.
"""

import datetime
import json
import math
import pathlib
import sys
from collections import Counter

import numpy as np

import hashlib

# Cascade-honesty per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]:
# shared A-N cascade helpers (precursor of srmech.amsc.cascade.* primitives).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes
from srmech.amsc.primes import is_prime
from srmech.amsc.hdc import bind, bundle, similarity

SCHEMA_ID = "srmech.hilbert.twin_prime.gap_distribution.v1"
N_MAX = 200_000
HARDY_LITTLEWOOD_2C2 = 1.32032363169373914785562422002911155686525  # 2 * twin-prime constant
SOURCE_DOI = "10.1007/BF02403921"           # Hardy-Littlewood 1923 (Acta Mathematica)
SOURCE_PUBLISHED = "1923-01-01"
PRIMORIALS = (6, 30, 210)
HDC_DIM_BYTES = 1024  # 8192-bit BSC HDC vectors


def sieve_primes(n):
    return [p for p in range(2, n + 1) if is_prime(p)]


def expand_hdc(seed: bytes, dim_bytes: int = HDC_DIM_BYTES) -> bytes:
    """Deterministic seed-to-fixed-length BSC vector via SHA-256 chained hashing."""
    out = bytearray()
    counter = 0
    while len(out) < dim_bytes:
        h = hashlib.sha256(seed + counter.to_bytes(8, "big")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:dim_bytes])


def make_residue_hdc(residue_to_count: dict, modulus: int) -> bytes:
    """Class M: per primorial scale, bundle one vector per VISITED residue class.

    Set-membership signature (which residue classes are visited by twin-pair lowers).
    Counts are reported separately as a distribution shape; the HDC vector encodes
    cross-scale support equivalence under primorial refinement.

    Note: bundle() is bounded by MAX_BUNDLE_N (257) which suits primorial unit counts
    phi(6)=2, phi(30)=8, phi(210)=48 -- well within bound.
    """
    anchor = expand_hdc(b"hilbert_08_twin_prime|scale_anchor")
    visited_residues = sorted(r for r in residue_to_count
                              if cyclic_gcd(r, modulus) == 1 and residue_to_count[r] > 0)
    if not visited_residues:
        return anchor
    components = []
    for r in visited_residues:
        residue_seed = b"residue|" + modulus.to_bytes(8, "big") + b"|" + r.to_bytes(8, "big")
        residue_vec = expand_hdc(residue_seed)
        components.append(bind(anchor, residue_vec))
    # bundle requires odd vector count
    if len(components) % 2 == 0:
        components.append(anchor)
    return bundle(components)


def main():
    out_path = pathlib.Path(__file__).parent / "twin_prime_gap_distribution.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    primes = sieve_primes(N_MAX)
    prime_set = set(primes)
    print(f"Sieved {len(primes)} primes up to {N_MAX}")

    twin_pairs = []
    for p in primes:
        if (p + 2) in prime_set:
            twin_pairs.append((p, p + 2))
    print(f"Found {len(twin_pairs)} twin pairs (gap=2)")

    # Per-scale residue counters (built incrementally so we can record cumulative density)
    residue_counters = {m: Counter() for m in PRIMORIALS}

    records = []
    for i, (p_low, p_high) in enumerate(twin_pairs, start=1):
        for m in PRIMORIALS:
            residue_counters[m][p_low % m] += 1

        # Class K asymptotic-DoF: HL-normalised cumulative density at p_low.
        # Twin-prime count(x) ~ 2*C_2 * x / (log x)^2 .
        # Normalised observed = count_so_far * (log p)^2 / p .
        log_p = math.log(p_low) if p_low > 1 else 1.0
        observed_norm = i * (log_p ** 2) / p_low
        residual = observed_norm - HARDY_LITTLEWOOD_2C2

        payload = json.dumps(
            {"p_low": p_low, "p_high": p_high, "twin_index": i},
            sort_keys=True,
        ).encode()
        chash = sha256_bytes(payload)

        records.append({
            "twin_index": i,
            "p_low": p_low,
            "p_high": p_high,
            "p_low_mod_6": p_low % 6,
            "p_low_mod_30": p_low % 30,
            "p_low_mod_210": p_low % 210,
            "twin_density_observed_to_p": round(observed_norm, 6),
            "hardy_littlewood_predicted_to_p": round(HARDY_LITTLEWOOD_2C2, 6),
            "density_residual": round(residual, 6),
            "class_cascade": "A-compose-J-compose-K-compose-I-compose-M",
            "computation_hash": chash,
            "source_doi": SOURCE_DOI,
            "source_published_date": SOURCE_PUBLISHED,
            "entered_locally_at": now_iso[:10],
        })

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {out_path}")

    # Class M: cross-scale HDC similarity
    # For each primorial scale build a single HDC vector representing the residue
    # distribution; then compare pairwise via similarity().
    hdc_vectors = {}
    for m in PRIMORIALS:
        hdc_vectors[m] = make_residue_hdc(residue_counters[m], m)

    sims = {}
    sims["6_vs_30"] = similarity(hdc_vectors[6], hdc_vectors[30])
    sims["6_vs_210"] = similarity(hdc_vectors[6], hdc_vectors[210])
    sims["30_vs_210"] = similarity(hdc_vectors[30], hdc_vectors[210])

    # Diagnostics
    final = records[-1]
    print()
    print("Twin-prime density (Hardy-Littlewood normalised) at largest sampled p:")
    print(f"  p_low = {final['p_low']}; twin_index = {final['twin_index']}")
    print(f"  observed_norm = {final['twin_density_observed_to_p']}")
    print(f"  predicted    = {final['hardy_littlewood_predicted_to_p']}")
    print(f"  residual     = {final['density_residual']}")
    print()
    print("Class I residue distributions (top-5 per primorial):")
    for m in PRIMORIALS:
        top5 = residue_counters[m].most_common(5)
        total_units = sum(1 for r in range(m) if cyclic_gcd(r, m) == 1)
        print(f"  mod {m:3d} (units count {total_units}): {top5}")
    print()
    print("Class M cross-scale HDC similarity (cosine in [-1, 1]):")
    for k, v in sims.items():
        print(f"  {k}: {v:.6f}")

    # Convergence ratio of observed to predicted -- as N grows this should approach 1
    ratio = final['twin_density_observed_to_p'] / HARDY_LITTLEWOOD_2C2
    print()
    print(f"observed / predicted = {ratio:.6f}   (Hardy-Littlewood: -> 1 as N -> inf)")


if __name__ == "__main__":
    main()
