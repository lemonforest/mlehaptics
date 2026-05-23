"""
Riemann Hypothesis cascade -- A o L o K o N o M.

Search across candidate substrate-class-instance Hermitian operator constructions
for spacing-statistics match to non-trivial zeta zeros (Hilbert-Polya direction).

Class L builds the operator (cyclic-graph Laplacian on Z/p, path-graph Laplacian,
cycle-graph Laplacian, complete-graph Laplacian).
Class K unfolds the spectrum to mean spacing 1 and extracts consecutive-spacing
ratios s_{n+1}/s_n.
Class N best_rational approximates the mean spacing-ratio.
Class M HDC-encodes the spacing-ratio distribution and computes cosine similarity
against the zeta-zero spacing-ratio HDC.

Per [[feedback_dont_pre_commit_spike_query_operators]]: enumerate operators
broadly. Don't lean toward GUE; let the cascade tell us which operator family
(if any) is structurally consistent at this N.
"""

import datetime
import hashlib
import json
import math
import pathlib

import numpy as np

from srmech.amsc.format import sha256_bytes
from srmech.amsc.primes import is_prime
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals
from srmech.amsc.rational import best_rational
from srmech.amsc.hdc import bind, bundle, similarity

SCHEMA_ID = "srmech.hilbert.riemann_hypothesis.zero_spectrum_match.v1"
SOURCE_DOI = "10.1090/pspum/024/9944"        # Montgomery 1973 (AMS PSPUM 24)
SOURCE_PUBLISHED = "1973-01-01"
HDC_DIM_BYTES = 1024  # 8192-bit BSC vectors
HDC_BIN_COUNT = 64    # discretise spacing-ratio range into 64 bins for HDC encoding

# First 50 non-trivial zeta-zero imaginary parts (Odlyzko public table; classical constants).
# Source: https://www-users.cse.umn.edu/~odlyzko/zeta_tables/zeros1
ZETA_ZEROS_IMAG = [
    14.134725141734693, 21.022039638771555, 25.010857580145688, 30.424876125859513,
    32.935061587739189, 37.586178158825671, 40.918719012147495, 43.327073280914999,
    48.005150881167159, 49.773832477672302, 52.970321477714460, 56.446247697063394,
    59.347044002602353, 60.831778524609810, 65.112544048081606, 67.079810529494173,
    69.546401711173979, 72.067157674481907, 75.704690699083933, 77.144840068874805,
    79.337375020249368, 82.910380854086030, 84.735492980517050, 87.425274613125229,
    88.809111207634465, 92.491899270558484, 94.651344040519886, 95.870634228245309,
    98.831194218193198, 101.317851005731391, 103.725538040478339, 105.446623052068133,
    107.168611184276672, 111.029535543169030, 111.874659176553523, 114.320220915452712,
    116.226680320857554, 118.790782866263239, 121.370125002420645, 122.946829293872455,
    124.256818554345355, 127.516683879596495, 129.578704199956555, 131.087688530932658,
    133.497737203718456, 134.756509753373688, 138.116042055412874, 139.736208952130198,
    141.123707403719002, 143.111845807994546,
]


def expand_hdc(seed: bytes, dim_bytes: int = HDC_DIM_BYTES) -> bytes:
    """Deterministic seed-to-fixed-length BSC vector via SHA-256 chained hashing."""
    out = bytearray()
    counter = 0
    while len(out) < dim_bytes:
        h = hashlib.sha256(seed + counter.to_bytes(8, "big")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:dim_bytes])


def unfold_spacings(eigenvalues):
    """Class K: unfold eigenvalue sequence so that mean nearest-neighbor spacing = 1.

    Returns the array of unfolded consecutive spacings.
    """
    sorted_eigs = sorted(eigenvalues)
    raw_spacings = [sorted_eigs[i + 1] - sorted_eigs[i] for i in range(len(sorted_eigs) - 1)]
    # remove any zero or near-zero spacings (degenerate eigenvalues)
    spacings = [s for s in raw_spacings if s > 1e-12]
    if not spacings:
        return []
    mean_s = sum(spacings) / len(spacings)
    return [s / mean_s for s in spacings]


def spacing_ratios(unfolded_spacings):
    """Class K asymptotic-DoF: consecutive spacing ratios s_{n+1}/s_n."""
    ratios = []
    for i in range(len(unfolded_spacings) - 1):
        if unfolded_spacings[i] > 1e-12:
            ratios.append(unfolded_spacings[i + 1] / unfolded_spacings[i])
    return ratios


def hdc_encode_distribution(ratios, bin_lo=0.0, bin_hi=4.0, n_bins=HDC_BIN_COUNT):
    """Class M: encode a 1D distribution of ratios as a single HDC vector.

    Each bin has an anchor vector; the distribution-HDC is the bundle of the
    bin-anchors weighted by count (one bind per occurrence). Counts are clipped
    so bundle vector count stays under MAX_BUNDLE_N.
    """
    counts = [0] * n_bins
    width = (bin_hi - bin_lo) / n_bins
    for r in ratios:
        if r < bin_lo:
            counts[0] += 1
        elif r >= bin_hi:
            counts[n_bins - 1] += 1
        else:
            idx = int((r - bin_lo) / width)
            counts[idx] += 1

    # Build bin anchors deterministically
    bin_anchors = [expand_hdc(b"riemann|spacing_ratio_bin|" + i.to_bytes(8, "big"))
                   for i in range(n_bins)]

    # Visit each bin once, repeated by count (capped to keep under MAX_BUNDLE_N).
    # Total components <= MAX_BUNDLE_N (257). Cap per-bin to ceil(257 / n_bins).
    cap_per_bin = max(1, 250 // n_bins)
    total = sum(min(c, cap_per_bin) for c in counts)
    if total == 0:
        return bin_anchors[0]

    components = []
    for i in range(n_bins):
        if counts[i] > 0:
            n_use = min(counts[i], cap_per_bin)
            components.extend([bin_anchors[i]] * n_use)
    # bundle requires odd
    if len(components) % 2 == 0:
        components.append(bin_anchors[0])
    return bundle(components)


# ---------- Candidate substrate operators ----------

def operator_cyclic_zp(p: int):
    """Cyclic-group graph Laplacian on Z/pZ (each vertex connected to +1 and -1)."""
    n = p
    edges = [(i, (i + 1) % n) for i in range(n)]
    L = dense_laplacian(n, edges)
    return jacobi_eigvals(L)


def operator_path(n: int):
    """Path-graph Laplacian on n vertices."""
    edges = [(i, i + 1) for i in range(n - 1)]
    L = dense_laplacian(n, edges)
    return jacobi_eigvals(L)


def operator_cycle(n: int):
    """Cycle-graph Laplacian on n vertices."""
    edges = [(i, (i + 1) % n) for i in range(n)]
    L = dense_laplacian(n, edges)
    return jacobi_eigvals(L)


def operator_complete(n: int):
    """Complete-graph K_n Laplacian (eigenvalues: 0, n with multiplicity n-1)."""
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    L = dense_laplacian(n, edges)
    return jacobi_eigvals(L)


def main():
    out_path = pathlib.Path(__file__).parent / "zero_spectrum_match.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Zeta zeros loaded: {len(ZETA_ZEROS_IMAG)} (first {ZETA_ZEROS_IMAG[0]:.4f}, last {ZETA_ZEROS_IMAG[-1]:.4f})")

    # ----- Zeta-zero side: Class K unfold + spacing ratios + HDC -----
    zeros_unfolded = unfold_spacings(ZETA_ZEROS_IMAG)
    zeros_ratios = spacing_ratios(zeros_unfolded)
    mean_ratio_zeros = float(np.mean(zeros_ratios))
    zeros_hdc = hdc_encode_distribution(zeros_ratios)
    print(f"Zeta-zero spacing-ratio mean = {mean_ratio_zeros:.6f}  (n_ratios={len(zeros_ratios)})")

    # ----- Candidate operator catalog -----
    candidates = []
    for p in [11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]:
        if is_prime(p):
            candidates.append((f"cyclic_Zp_{p:02d}", f"cyclic_graph_Z_mod_{p}", lambda p=p: operator_cyclic_zp(p)))
    for n in [20, 30, 40, 50, 60]:
        candidates.append((f"path_N{n:02d}", f"path_graph_n={n}", lambda n=n: operator_path(n)))
    for n in [20, 30, 40, 50, 60]:
        candidates.append((f"cycle_N{n:02d}", f"cycle_graph_n={n}", lambda n=n: operator_cycle(n)))
    for n in [10, 15, 20]:
        candidates.append((f"complete_K{n:02d}", f"complete_graph_K_{n}", lambda n=n: operator_complete(n)))

    records = []
    diagnostics = []

    for op_id, substrate_label, fn in candidates:
        eigs = list(fn())
        eigs_unfolded = unfold_spacings(eigs)
        if len(eigs_unfolded) < 3:
            continue
        ratios = spacing_ratios(eigs_unfolded)
        if len(ratios) < 2:
            continue
        mean_ratio_op = float(np.mean(ratios))
        # Class N best-rational of mean ratio
        try:
            nf, df = best_rational(mean_ratio_op, max_denominator=20)
        except Exception:
            nf, df = 0, 1
        # Class M HDC similarity
        op_hdc = hdc_encode_distribution(ratios)
        sim = similarity(op_hdc, zeros_hdc)

        payload = json.dumps({
            "operator_id": op_id,
            "n_eigenvalues": len(eigs),
            "mean_spacing_ratio_operator": mean_ratio_op,
        }, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "operator_id":                  op_id,
            "substrate_class_instance":     substrate_label,
            "n_eigenvalues":                len(eigs),
            "n_zero_samples":               len(ZETA_ZEROS_IMAG),
            "mean_spacing_ratio_operator":  round(mean_ratio_op, 6),
            "mean_spacing_ratio_zeros":     round(mean_ratio_zeros, 6),
            "spacing_ratio_rational_n":     int(nf),
            "spacing_ratio_rational_d":     int(df),
            "hdc_similarity_score":         round(float(sim), 6),
            "class_cascade":                "A-compose-L-compose-K-compose-N-compose-M",
            "computation_hash":             chash,
            "source_doi":                   SOURCE_DOI,
            "source_published_date":        SOURCE_PUBLISHED,
            "entered_locally_at":           now_iso[:10],
        }
        records.append(rec)
        diagnostics.append((op_id, mean_ratio_op, float(sim), nf, df, len(ratios)))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print(f"Cascade target: mean spacing-ratio of zeta-zero unfolded sequence = {mean_ratio_zeros:.4f}")
    print(f"(GUE asymptotic Wigner-Dyson surmise predicts ~1.17 for the ratio of consecutive spacings)")
    print()

    diagnostics.sort(key=lambda r: -r[2])  # sort by similarity desc
    print(f"{'operator_id':<20} {'mean_ratio':>10} {'sim':>10} {'best_rat':>10} {'n_ratios':>10}")
    for d in diagnostics:
        print(f"  {d[0]:<18} {d[1]:>10.4f} {d[2]:>10.4f} {d[3]}/{d[4]:<6} {d[5]:>10}")


if __name__ == "__main__":
    main()
