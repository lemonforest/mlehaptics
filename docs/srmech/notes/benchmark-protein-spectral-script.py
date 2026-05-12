"""
Protein-folding spectral computational-cost benchmark — 2026-05-11.

Companion to the validation spike (`protein-folding-spectral-spike-script.py`).
Where the validation spike established ACCURACY (ubiquitin GNM B-factor
Pearson r = +0.818, at the top of the Bahar 1997 published range), this
benchmark establishes COMPUTATIONAL COST: runtime of the project's
graph-Laplacian-based protein analysis versus published computation times
for the same proteins.

Math-doesn't-lie / MPM discipline: deterministic seed `20260511`,
median + IQR over N_TRIALS=20 timed runs, numpy + scipy only, no SGD.
Cross-platform reproducibility caveat: numpy.linalg.eigh + scipy.linalg.eigh
are deterministic on the same input + same hardware but not bit-identical
across (e.g.) MKL vs OpenBLAS backends. Timings will vary by hardware; the
script reports its own platform string for provenance.

Honest framing required throughout: the project's GNM produces
  - residue mean-square fluctuations (B-factor proxy)
  - Fiedler partition labels
  - per-mode participation vectors
AlphaFold2/3 produce full 3D atomic coordinates + pLDDT confidence.
MD folding simulation produces time-resolved trajectories.
ProDy / Bio3D / WEBnm@ produce the same GNM mode information.

The first comparison family is APPLES-TO-APPLES (same product); the second
and third are APPLES-TO-ORANGES (different products at very different cost
levels). The benchmark must say which is which.

Extension procedure for future proteins:
  1. Add PDB to `docs/srmech/hoodoos/<protein>-<pdbid>.pdb`
  2. Add `[<protein>_<pdbid>]` entry to
     `docs/srmech/notes/protein-folding-benchmark-reference-times.toml`
  3. Add entry to PROTEIN_ROSTER below
  4. Re-run this script

References (canonical sources for reference timings):
  - Bahar, Atilgan, Erman 1997 *Folding & Design* 2:173-181 — original GNM
  - Atilgan et al 2001 *Biophys. J.* 80:505-515 — ANM
  - Bakan, Meireles, Bahar 2011 *Bioinformatics* 27:1575-1577 — ProDy
  - Hollup, Salensminde, Reuter 2005 *BMC Bioinformatics* 6:52 — WEBnm@
  - Grant, Skjaerven, Yao 2021 *Protein Science* 30:20-30 — Bio3D-NMA
  - Jumper et al 2021 *Nature* 596:583-589 — AlphaFold2 (sup. for timing)
  - Abramson et al 2024 *Nature* 630:493-500 — AlphaFold3
  - Lindorff-Larsen et al 2011 *Science* 334:517-520 — Anton MD folding
  - Piana, Lindorff-Larsen, Shaw 2013 *PNAS* 110:5915-5920 — ubiquitin MD

Author: concertmaster role, 2026-05-11.
Lineage: surfaced from protein-folding spectral spike (commit a02b379).
"""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover — script targets 3.11+
    import tomli as tomllib

from scipy.linalg import eigh
from scipy.spatial.distance import pdist, squareform
from scipy.stats import pearsonr

# ---------------------------------------------------------------------------
# Constants / SSOT
# ---------------------------------------------------------------------------

SEED = 20260511
R_C_ANGSTROM = 8.0
TRIVIAL_EIGENVALUE_TOL = 1e-6
N_TRIALS = 20                     # median + IQR over N_TRIALS timed runs
N_WARMUP = 3                      # warm-up runs (not counted in stats)

HOODOOS_DIR = Path(r"D:\GitHub\mlehaptics\docs\srmech\hoodoos")
OUTPUT_DIR = Path(r"D:\GitHub\mlehaptics\docs\srmech\notes")
NDJSON_PATH = OUTPUT_DIR / "protein-folding-benchmark-per-comparison-2026-05-11.ndjson"
TOML_PATH = OUTPUT_DIR / "protein-folding-benchmark-reference-times.toml"
COMPLETION_RECORD_PATH = Path(
    r"D:\GitHub\mlehaptics\docs\antikythera-maths\research-mfo\mfo_mpm_notes.ndjson"
)

PROTEIN_ROSTER: List[Dict[str, Any]] = [
    {
        "protein_id": "ubiquitin_1ubq",
        "protein_name": "ubiquitin",
        "pdb_id": "1UBQ",
        "pdb_path": HOODOOS_DIR / "ubiquitin-1ubq.pdb",
        "expected_residues": 76,
    },
    {
        "protein_id": "villin_hp35_2f4k",
        "protein_name": "villin_hp35",
        "pdb_id": "2F4K",
        "pdb_path": HOODOOS_DIR / "villin-hp35-2f4k.pdb",
        "expected_residues": 35,
    },
    {
        "protein_id": "mj0366_2efv",
        "protein_name": "mj0366_trefoil_knotted",
        "pdb_id": "2EFV",
        "pdb_path": HOODOOS_DIR / "mj0366-knotted-2efv.pdb",
        "expected_residues": 82,
    },
]

# ---------------------------------------------------------------------------
# Shared primitives (parallel to spike script; intentionally re-implemented
# here so the benchmark module is self-contained and ships separately)
# ---------------------------------------------------------------------------


def parse_pdb_calpha(
    pdb_path: Path, chain_id: str = "A"
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """Parse a PDB file and extract Cα atom data for one chain (first MODEL)."""
    coords_list: List[List[float]] = []
    resnum_list: List[int] = []
    bfact_list: List[float] = []
    resname_list: List[str] = []
    seen_residues = set()
    in_first_model = True

    with open(pdb_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            if line.startswith("MODEL"):
                if not in_first_model:
                    break
                continue
            if line.startswith("ENDMDL"):
                in_first_model = False
                continue
            if not line.startswith("ATOM"):
                continue
            atom_name = line[12:16].strip()
            if atom_name != "CA":
                continue
            altloc = line[16:17]
            if altloc not in (" ", "A"):
                continue
            chain = line[21:22]
            if chain != chain_id:
                continue
            resname = line[17:20].strip()
            try:
                resnum = int(line[22:26].strip())
            except ValueError:
                continue
            key = (chain, resnum)
            if key in seen_residues:
                continue
            seen_residues.add(key)
            try:
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
            except ValueError:
                continue
            try:
                b = float(line[60:66].strip())
            except ValueError:
                b = 0.0
            coords_list.append([x, y, z])
            resnum_list.append(resnum)
            bfact_list.append(b)
            resname_list.append(resname)

    coords = np.asarray(coords_list, dtype=np.float64)
    resnums = np.asarray(resnum_list, dtype=np.int64)
    bfacts = np.asarray(bfact_list, dtype=np.float64)
    return coords, resnums, bfacts, resname_list


def build_contact_laplacian(
    coords: np.ndarray, r_c: float = R_C_ANGSTROM
) -> Tuple[np.ndarray, np.ndarray, int]:
    n = coords.shape[0]
    D_pair = squareform(pdist(coords))
    A = ((D_pair <= r_c) & (D_pair > 0)).astype(np.float64)
    np.fill_diagonal(A, 0.0)
    deg = A.sum(axis=1)
    L = np.diag(deg) - A
    n_edges = int(A.sum() / 2)
    return L, A, n_edges


def compute_gnm_eigendecomposition(L: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    L_sym = 0.5 * (L + L.T)
    return eigh(L_sym)


def predict_b_factors_gnm(
    eigvals: np.ndarray, eigvecs: np.ndarray
) -> np.ndarray:
    nontrivial = eigvals > TRIVIAL_EIGENVALUE_TOL
    inv_lambda = np.zeros_like(eigvals)
    inv_lambda[nontrivial] = 1.0 / eigvals[nontrivial]
    return (eigvecs ** 2) @ inv_lambda


def fiedler_partition(eigvecs: np.ndarray) -> np.ndarray:
    return (eigvecs[:, 1] > 0).astype(int)


# ---------------------------------------------------------------------------
# Benchmark harness
# ---------------------------------------------------------------------------


def _time_block(fn, *args, n_trials: int = N_TRIALS, n_warmup: int = N_WARMUP):
    """Time a callable's runtime; returns dict with median + IQR + raw samples."""
    # Warm up (page caches, JIT, etc.)
    for _ in range(n_warmup):
        fn(*args)
    samples_s: List[float] = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        fn(*args)
        samples_s.append(time.perf_counter() - t0)
    samples_s.sort()
    median = statistics.median(samples_s)
    q1 = samples_s[int(0.25 * n_trials)]
    q3 = samples_s[int(0.75 * n_trials)]
    return {
        "median_seconds": float(median),
        "q1_seconds": float(q1),
        "q3_seconds": float(q3),
        "iqr_seconds": float(q3 - q1),
        "min_seconds": float(samples_s[0]),
        "max_seconds": float(samples_s[-1]),
        "n_trials": n_trials,
        "n_warmup": n_warmup,
    }


def benchmark_protein(
    pdb_path: Path,
    protein_id: str,
    n_trials: int = N_TRIALS,
) -> Dict[str, Any]:
    """Benchmark per-stage runtimes for one protein."""

    # Pre-fetch parsed data (used by stage benchmarks that don't include parse)
    coords, resnums, b_exp, resnames = parse_pdb_calpha(pdb_path)
    n = coords.shape[0]
    if n == 0:
        return {"protein_id": protein_id, "error": "no Cα atoms parsed"}

    # ---------- Stage 1: PDB parse ----------
    parse_stats = _time_block(parse_pdb_calpha, pdb_path, n_trials=n_trials)

    # ---------- Stage 2: contact graph build ----------
    contact_stats = _time_block(build_contact_laplacian, coords, n_trials=n_trials)

    # ---------- Stage 3: eigendecomposition only (input = pre-built L) ----------
    L, _, n_edges = build_contact_laplacian(coords)
    eig_stats = _time_block(compute_gnm_eigendecomposition, L, n_trials=n_trials)

    # ---------- Stage 4: B-factor prediction (post-eigendecomp) ----------
    eigvals, eigvecs = compute_gnm_eigendecomposition(L)

    def bfactor_block():
        return predict_b_factors_gnm(eigvals, eigvecs)

    bfactor_stats = _time_block(bfactor_block, n_trials=n_trials)

    # ---------- Stage 5: Fiedler partition (post-eigendecomp) ----------
    def fiedler_block():
        return fiedler_partition(eigvecs)

    fiedler_stats = _time_block(fiedler_block, n_trials=n_trials)

    # ---------- Stage 6: end-to-end pipeline (parse → B-factors + Fiedler) ----------
    def full_pipeline():
        c, _r, _b, _n = parse_pdb_calpha(pdb_path)
        L_p, _A, _e = build_contact_laplacian(c)
        ev, vc = compute_gnm_eigendecomposition(L_p)
        _ = predict_b_factors_gnm(ev, vc)
        _ = fiedler_partition(vc)

    pipeline_stats = _time_block(full_pipeline, n_trials=n_trials)

    # ---------- Quality check: re-run accuracy from spike to ensure determinism ----------
    msf = predict_b_factors_gnm(eigvals, eigvecs)
    if b_exp.std() > 0 and msf.std() > 0:
        pearson_r, _ = pearsonr(msf, b_exp)
    else:
        pearson_r = float("nan")

    return {
        "protein_id": protein_id,
        "n_residues": int(n),
        "n_edges": int(n_edges),
        "r_cutoff_angstrom": R_C_ANGSTROM,
        "stage_parse": parse_stats,
        "stage_contact_graph": contact_stats,
        "stage_eigendecomp": eig_stats,
        "stage_bfactor_predict": bfactor_stats,
        "stage_fiedler_partition": fiedler_stats,
        "stage_full_pipeline": pipeline_stats,
        "accuracy_check_pearson_r": float(pearson_r),
        "memory_bytes_adjacency_matrix": int(n * n * 8),
        "memory_bytes_eigenvector_matrix": int(n * n * 8),
        "complexity_eigendecomp_O_n3": int(n ** 3),
    }


# ---------------------------------------------------------------------------
# Reference times TOML loader
# ---------------------------------------------------------------------------


def load_reference_times(toml_path: Path) -> Dict[str, Any]:
    with open(toml_path, "rb") as f:
        return tomllib.load(f)


def compare_to_reference(
    ours_seconds: float,
    reference_method: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute ratio + classification for one reference method comparison."""
    apples = bool(reference_method.get("apples_to_apples", False))
    time_str = reference_method.get("time_seconds", "not quoted")
    try:
        ref_seconds = float(time_str)
        ratio = ours_seconds / ref_seconds if ref_seconds > 0 else float("inf")
        if not apples:
            verdict = "different-product-not-direct-comparison"
        elif ratio < 0.5:
            verdict = f"comparable-faster ({1.0 / ratio:.1f}x faster)"
        elif ratio < 2.0:
            verdict = f"comparable-parity ({ratio:.2f}x)"
        elif ratio < 100.0:
            verdict = f"slower ({ratio:.1f}x slower)"
        else:
            verdict = f"orders-of-magnitude-slower ({ratio:.0e}x slower)"
    except (ValueError, TypeError):
        ref_seconds = None
        ratio = None
        verdict = "reference-time-not-quoted"
    return {
        "reference_seconds": ref_seconds,
        "reference_seconds_raw": time_str,
        "ratio_ours_over_theirs": ratio,
        "verdict": verdict,
        "apples_to_apples": apples,
    }


# ---------------------------------------------------------------------------
# Output: NDJSON benchmark records
# ---------------------------------------------------------------------------


def emit_ndjson_records(
    benchmark_results: List[Dict[str, Any]],
    reference_times: Dict[str, Any],
    platform_info: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Emit one record per (protein × reference-method × metric)."""
    records: List[Dict[str, Any]] = []

    for bench in benchmark_results:
        protein_id = bench["protein_id"]

        # First, per-protein stage records (our timings, no reference comparison)
        for stage_key in (
            "stage_parse",
            "stage_contact_graph",
            "stage_eigendecomp",
            "stage_bfactor_predict",
            "stage_fiedler_partition",
            "stage_full_pipeline",
        ):
            stats = bench[stage_key]
            records.append({
                "kind": "ours_stage_timing",
                "protein_id": protein_id,
                "stage": stage_key,
                "median_seconds": stats["median_seconds"],
                "iqr_seconds": stats["iqr_seconds"],
                "min_seconds": stats["min_seconds"],
                "max_seconds": stats["max_seconds"],
                "n_trials": stats["n_trials"],
                "n_warmup": stats["n_warmup"],
                "n_residues": bench["n_residues"],
                "n_edges": bench["n_edges"],
                "platform": platform_info["machine_summary"],
                "seed": SEED,
            })

        # Then per-reference-method comparison records (full pipeline vs reference)
        ours_seconds = bench["stage_full_pipeline"]["median_seconds"]
        ref_entry = reference_times.get(protein_id)
        if ref_entry is None:
            records.append({
                "kind": "comparison_missing_reference",
                "protein_id": protein_id,
                "note": "no reference-times entry found for this protein",
            })
            continue
        for ref_method in ref_entry.get("reference_methods", []):
            comparison = compare_to_reference(ours_seconds, ref_method)
            records.append({
                "kind": "comparison",
                "protein_id": protein_id,
                "n_residues": bench["n_residues"],
                "ours_full_pipeline_median_seconds": ours_seconds,
                "ours_full_pipeline_iqr_seconds": bench["stage_full_pipeline"]["iqr_seconds"],
                "reference_method_name": ref_method.get("name"),
                "reference_source": ref_method.get("source"),
                "reference_hardware": ref_method.get("hardware"),
                "reference_what_computed": ref_method.get("what_computed"),
                "reference_seconds_raw": comparison["reference_seconds_raw"],
                "reference_seconds": comparison["reference_seconds"],
                "ratio_ours_over_theirs": comparison["ratio_ours_over_theirs"],
                "verdict": comparison["verdict"],
                "apples_to_apples": comparison["apples_to_apples"],
                "reference_notes": ref_method.get("notes", ""),
                "ours_platform": platform_info["machine_summary"],
                "seed": SEED,
            })

        # Per-protein meta record (memory, complexity)
        records.append({
            "kind": "ours_meta",
            "protein_id": protein_id,
            "n_residues": bench["n_residues"],
            "n_edges": bench["n_edges"],
            "memory_bytes_adjacency_matrix": bench["memory_bytes_adjacency_matrix"],
            "memory_bytes_eigenvector_matrix": bench["memory_bytes_eigenvector_matrix"],
            "complexity_eigendecomp_O_n3": bench["complexity_eigendecomp_O_n3"],
            "accuracy_check_pearson_r": bench["accuracy_check_pearson_r"],
            "platform": platform_info["machine_summary"],
            "seed": SEED,
        })

    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def collect_platform_info() -> Dict[str, Any]:
    return {
        "machine": platform.machine(),
        "system": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "machine_summary": f"{platform.system()} {platform.machine()} Python {platform.python_version()} numpy {np.__version__}",
    }


def main():
    rng = np.random.default_rng(SEED)
    platform_info = collect_platform_info()
    print(f"[ ] Platform: {platform_info['machine_summary']}")

    # Load reference times
    if not TOML_PATH.exists():
        print(f"[!!] Reference times TOML not found: {TOML_PATH}")
        print("[!!] Create it before running benchmark. Aborting.")
        sys.exit(1)
    reference_times = load_reference_times(TOML_PATH)
    print(f"[OK] Reference times loaded from {TOML_PATH.name}: "
          f"{len(reference_times)} protein entries")

    # Benchmark each protein
    benchmark_results: List[Dict[str, Any]] = []
    for protein_entry in PROTEIN_ROSTER:
        print(f"[ ] Benchmarking {protein_entry['protein_id']} "
              f"({N_TRIALS} trials + {N_WARMUP} warmups)...")
        result = benchmark_protein(
            protein_entry["pdb_path"],
            protein_entry["protein_id"],
        )
        benchmark_results.append(result)
        print(f"[OK] {protein_entry['protein_id']}: "
              f"n={result['n_residues']}, "
              f"full-pipeline median={result['stage_full_pipeline']['median_seconds'] * 1000:.2f}ms "
              f"(IQR {result['stage_full_pipeline']['iqr_seconds'] * 1000:.2f}ms), "
              f"eigendecomp={result['stage_eigendecomp']['median_seconds'] * 1000:.2f}ms, "
              f"accuracy check r={result['accuracy_check_pearson_r']:.3f}")

    # Generate NDJSON records
    ndjson_records = emit_ndjson_records(benchmark_results, reference_times, platform_info)

    # Write NDJSON (idempotent overwrite)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with NDJSON_PATH.open("w", encoding="utf-8") as f:
        for rec in ndjson_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[OK] NDJSON written: {NDJSON_PATH.name} ({len(ndjson_records)} records)")

    # Print headline comparison table
    print("\n=== HEADLINE COMPARISONS ===")
    for bench in benchmark_results:
        protein_id = bench["protein_id"]
        ours_ms = bench["stage_full_pipeline"]["median_seconds"] * 1000
        print(f"\n--- {protein_id} (n={bench['n_residues']}, ours full-pipeline median = {ours_ms:.2f} ms) ---")
        ref = reference_times.get(protein_id, {})
        for rm in ref.get("reference_methods", []):
            comparison = compare_to_reference(
                bench["stage_full_pipeline"]["median_seconds"], rm
            )
            apple_tag = "A2A" if comparison["apples_to_apples"] else "A2O"
            print(f"  [{apple_tag}] {rm['name']:<24} {comparison['reference_seconds_raw']:<14} "
                  f"-> {comparison['verdict']}")

    # Append completion record to MFO MPM notes (idempotent)
    completion_record = {
        "date": "2026-05-11",
        "phase": "srmech_absorption",
        "kind": "protein_folding_benchmark_completion",
        "surfaced_from": "protein_folding_spectral_spike_2026-05-11",
        "note": (
            "Protein-folding computational-cost benchmark done. Companion to "
            "validation spike (commit a02b379). Per-stage timings on 3 vendored "
            "proteins (ubiquitin 1UBQ, villin HP35 2F4K, MJ0366 2EFV); median + "
            "IQR over " + str(N_TRIALS) + " timed trials with " + str(N_WARMUP) +
            " warmups. Full-pipeline (PDB parse → contact graph → eigendecomp → "
            "B-factor + Fiedler) median runtimes: "
            + ", ".join(
                f"{b['protein_id']}={b['stage_full_pipeline']['median_seconds']*1000:.2f}ms"
                for b in benchmark_results
            )
            + ". Apples-to-apples comparators (ProDy GNM, Bio3D NMA, WEBnm@) are "
            "same-product GNM implementations; project's spectral approach is "
            "directly comparable. Apples-to-oranges comparators (AlphaFold2/3, "
            "MD folding) produce different products (3D structure, time-resolved "
            "trajectories) at fundamentally different cost levels. Math-doesn't-lie "
            "framing: project does NOT replace AlphaFold; it provides fast "
            "post-structure spectral characterization."
        ),
        "platform": platform_info["machine_summary"],
        "n_trials": N_TRIALS,
        "n_warmup": N_WARMUP,
        "outputs": [
            "docs/srmech/notes/benchmark-protein-spectral-script.py",
            "docs/srmech/notes/protein-folding-benchmark-reference-times.toml",
            "docs/srmech/notes/protein-folding-benchmark-per-comparison-2026-05-11.ndjson",
            "docs/srmech/notes/protein-folding-benchmark-2026-05-11.md",
        ],
    }
    completion_marker = '"kind": "protein_folding_benchmark_completion"'
    existing = COMPLETION_RECORD_PATH.read_text(encoding="utf-8")
    if completion_marker not in existing:
        with COMPLETION_RECORD_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(completion_record, ensure_ascii=False) + "\n")
        print(f"[OK] Completion record appended to {COMPLETION_RECORD_PATH.name}")
    else:
        print(f"[SKIP] Completion record already present in "
              f"{COMPLETION_RECORD_PATH.name} (idempotent).")


if __name__ == "__main__":
    main()
