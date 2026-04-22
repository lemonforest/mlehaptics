"""§12 evaluation: Derivations A, B, C similarity vs is_check_unsafe.

Reads results/phase_operator_experiments/exp3_phase_similarity.csv
(the §11.5 output with is_check_unsafe labels), recomputes king-
attack similarity for each transition under each derivation, appends
those columns to the CSV, and reports Spearman correlations per
derivation and per polarization slice.

Run from docs/chess-maths/:
    python -m king_attack_encoder.evaluate_encoder \
        --input-csv results/phase_operator_experiments/exp3_phase_similarity.csv \
        --out results/phase_operator_experiments/exp5_king_attack_correlation.csv
"""
import argparse
import csv
import random
import sys
import time
from pathlib import Path

# Windows console: default cp1252 cannot encode § or ρ glyphs used in
# the stdout summary. Reconfigure stdout/stderr to UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import chess
import numpy as np
from scipy.stats import spearmanr

from .derivation_a_laplacian import (
    DEFAULT_K, derivation_a_channel, derivation_a_similarity,
    variance_explained,
)
from .derivation_b_d4 import (
    D4_IRREPS, derivation_b_channels, derivation_b_similarity,
    derivation_b_similarity_concat,
)
from .derivation_c_operator import (
    derivation_c_channel, derivation_c_similarity,
    derivation_c_delta, derivation_c_after_magnitude,
)


OUTPUT_COLUMNS_EXTRA = [
    "similarity_a",
    "similarity_b_concat",
    "similarity_b_A1", "similarity_b_A2", "similarity_b_B1",
    "similarity_b_B2", "similarity_b_E",
    "similarity_c",
    "delta_c",         # Phase A2: L2(C_after - C_before)
    "mag_c_after",     # Phase A2: |C_after|
    "var_exp_a",       # Phase A2: parameterized by --k-for-a; was var_exp_a_k5
    "timing_a_ns", "timing_b_ns", "timing_c_ns",
]


def _bool(s: str) -> int:
    return 1 if s.lower() == "true" else 0


def _spearman(xs, ys):
    if len(xs) < 3:
        return float("nan"), len(xs)
    xa = np.asarray(xs, dtype=float)
    ya = np.asarray(ys, dtype=float)
    if np.all(xa == xa[0]) or np.all(ya == ya[0]):
        return float("nan"), len(xs)
    rho, _ = spearmanr(xa, ya)
    return float(rho), len(xs)


def _slice_by_piece(rows, letter):
    return [r for r in rows if r["polarization_type"] == letter]


def _slice_by_capture(rows, want_capture: bool):
    return [r for r in rows if r["is_capture"] == want_capture]


def process_csv(input_csv: Path, out_csv: Path,
                sample_for_diagnostics: int = 50,
                k_for_a: int = 16) -> dict:
    """Single-pass evaluation: read input CSV, compute all three
    derivations' similarities per row, append columns, write output
    CSV. Return a summary dict used by print_summary.

    k_for_a parameterizes Derivation A's eigenvector count (default 16
    per §12.7.1 Phase A2; set to 5 to reproduce Phase A)."""
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with input_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        input_fields = reader.fieldnames or []
        input_rows = list(reader)

    output_fields = list(input_fields) + OUTPUT_COLUMNS_EXTRA
    out_rows: list = []
    enriched: list = []

    total = len(input_rows)
    for idx, row in enumerate(input_rows):
        fen = row["position_fen"]
        uci = row["transition_uci"]
        try:
            board = chess.Board(fen)
            move = chess.Move.from_uci(uci)
        except ValueError:
            continue

        t0 = time.perf_counter_ns()
        sim_a = derivation_a_similarity(board, move, k=k_for_a)
        t1 = time.perf_counter_ns()
        per_irrep = derivation_b_similarity(board, move)
        sim_b_concat = derivation_b_similarity_concat(board, move)
        t2 = time.perf_counter_ns()
        sim_c = derivation_c_similarity(board, move)
        dlt_c = derivation_c_delta(board, move)
        mag_c = derivation_c_after_magnitude(board, move)
        t3 = time.perf_counter_ns()
        var_exp = variance_explained(board, k=k_for_a)

        out_row = dict(row)
        out_row.update({
            "similarity_a": f"{sim_a:.12f}",
            "similarity_b_concat": f"{sim_b_concat:.12f}",
            "similarity_b_A1": f"{per_irrep['A1']:.12f}",
            "similarity_b_A2": f"{per_irrep['A2']:.12f}",
            "similarity_b_B1": f"{per_irrep['B1']:.12f}",
            "similarity_b_B2": f"{per_irrep['B2']:.12f}",
            "similarity_b_E":  f"{per_irrep['E']:.12f}",
            "similarity_c": f"{sim_c:.12f}",
            "delta_c": f"{dlt_c:.12f}",
            "mag_c_after": f"{mag_c:.12f}",
            "var_exp_a": f"{var_exp:.12f}",
            "timing_a_ns": t1 - t0,
            "timing_b_ns": t2 - t1,
            "timing_c_ns": t3 - t2,
        })
        out_rows.append(out_row)

        enriched.append({
            "polarization_type": row["polarization_type"],
            "is_check_unsafe": _bool(row["is_check_unsafe"]),
            "is_capture": row["is_capture"].lower() == "true",
            "sim_a": sim_a,
            "sim_b_concat": sim_b_concat,
            "sim_b_per_irrep": per_irrep,
            "sim_c": sim_c,
            "dlt_c": dlt_c,
            "mag_c": mag_c,
            "var_exp": var_exp,
            "t_a": t1 - t0,
            "t_b": t2 - t1,
            "t_c": t3 - t2,
        })

        if (idx + 1) % 500 == 0:
            print(f"  processed {idx + 1}/{total}")

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        for row in out_rows:
            writer.writerow(row)

    # Pairwise cosine diagnostics on a sample of positions (unique FENs).
    seen_fens: set = set()
    sample_fens: list = []
    rng = random.Random(42)
    shuffled = list(range(len(input_rows)))
    rng.shuffle(shuffled)
    for i in shuffled:
        fen = input_rows[i]["position_fen"]
        if fen in seen_fens:
            continue
        seen_fens.add(fen)
        sample_fens.append(fen)
        if len(sample_fens) >= sample_for_diagnostics:
            break

    cos_ab = []
    cos_ac = []
    cos_bc = []
    for fen in sample_fens:
        try:
            board = chess.Board(fen)
        except ValueError:
            continue
        a = derivation_a_channel(board)
        b_channels = derivation_b_channels(board)
        b_concat = np.concatenate([b_channels[i] for i in D4_IRREPS])
        c = derivation_c_channel(board)

        def _cos(u, v):
            nu = float(np.linalg.norm(u))
            nv = float(np.linalg.norm(v))
            if nu == 0.0 or nv == 0.0:
                return None
            # Align dimensionalities by truncating/padding both to
            # their shorter length. (The three derivations have
            # different native dims; the pairwise-cosine metric below
            # treats them as abstract vectors projected into a common
            # space via zero-padding.)
            n = min(len(u), len(v))
            return float(np.dot(u[:n], v[:n]) / (nu * nv))

        ab = _cos(a, b_concat)
        ac = _cos(a, c)
        bc = _cos(b_concat, c)
        if ab is not None: cos_ab.append(ab)
        if ac is not None: cos_ac.append(ac)
        if bc is not None: cos_bc.append(bc)

    return {
        "enriched": enriched,
        "total": len(enriched),
        "sample_for_diagnostics": len(sample_fens),
        "cos_ab_mean": (float(np.mean(cos_ab)) if cos_ab else float("nan")),
        "cos_ac_mean": (float(np.mean(cos_ac)) if cos_ac else float("nan")),
        "cos_bc_mean": (float(np.mean(cos_bc)) if cos_bc else float("nan")),
        "out_csv": out_csv,
        "input_csv": input_csv,
        "k_for_a": k_for_a,
    }


def _fmt(rho_n):
    rho, n = rho_n
    if rho != rho:
        return f"nan      (n={n})"
    return f"{rho:+.3f}   (n={n})"


def print_summary(summary: dict) -> None:
    enriched = summary["enriched"]
    total = summary["total"]
    print("\n[Section 12 Phase A] king-attack encoder evaluation:")
    print(f"  Input:  {summary['input_csv']}")
    print(f"  Output: {summary['out_csv']}")
    print(f"  Transitions evaluated: {total}")
    print("")

    targets = [r["is_check_unsafe"] for r in enriched]

    def rep(rows, key):
        xs = [r[key] for r in rows]
        ys = [r["is_check_unsafe"] for r in rows]
        return _spearman(xs, ys)

    piece_slices = [("knight", "N"), ("bishop", "B"), ("rook", "R"),
                    ("queen", "Q"), ("king", "K"), ("pawn", "P")]
    cap_rows = _slice_by_capture(enriched, True)
    non_rows = _slice_by_capture(enriched, False)

    print("  Per-derivation |rho(similarity, is_check_unsafe)|:")
    print("")

    # Derivation A
    k_for_a = summary.get("k_for_a", DEFAULT_K)
    var_exps = [r["var_exp"] for r in enriched]
    mean_var_exp = float(np.mean(var_exps)) if var_exps else 0.0
    var_label = ("faithful" if mean_var_exp >= 0.80
                 else ("partial" if mean_var_exp >= 0.50
                       else "inadequate"))
    print(f"  Derivation A (king-centered Laplacian, k={k_for_a}):")
    print(f"    all transitions:   {_fmt(rep(enriched, 'sim_a'))}")
    for name, letter in piece_slices:
        sub = _slice_by_piece(enriched, letter)
        print(f"    {name+' moves:':<19}{_fmt(rep(sub, 'sim_a'))}")
    print(f"    captures:          {_fmt(rep(cap_rows, 'sim_a'))}")
    print(f"    non-captures:      {_fmt(rep(non_rows, 'sim_a'))}")
    print(f"    variance explained (mean over all rows, k={k_for_a}): "
          f"{100 * mean_var_exp:.1f}% ({var_label})")
    print("")

    # Derivation B
    print("  Derivation B (D4 decomposition of attack adjacency, "
          "5 irreps concatenated):")
    print(f"    all transitions:   "
          f"{_fmt(rep(enriched, 'sim_b_concat'))}")
    for name, letter in piece_slices:
        sub = _slice_by_piece(enriched, letter)
        print(f"    {name+' moves:':<19}"
              f"{_fmt(rep(sub, 'sim_b_concat'))}")
    print(f"    captures:          "
          f"{_fmt(rep(cap_rows, 'sim_b_concat'))}")
    print(f"    non-captures:      "
          f"{_fmt(rep(non_rows, 'sim_b_concat'))}")
    # Per-irrep:
    print("    per-irrep |rho|:")
    for irrep in D4_IRREPS:
        xs = [r["sim_b_per_irrep"][irrep] for r in enriched]
        rho, n = _spearman(xs, targets)
        rs = f"{rho:+.3f}" if rho == rho else "nan"
        print(f"      {irrep}_ka: {rs}")
    print("")

    # Derivation C — three scalar summaries of the same 16-dim feature
    print("  Derivation C (attack operator from king's phase, "
          "16-dim feature):")
    for metric_key, metric_label in [
        ("sim_c", "cosine similarity"),
        ("dlt_c", "L2 delta (C_after - C_before)"),
        ("mag_c", "|C_after| (tautological baseline)"),
    ]:
        print(f"    [{metric_label}]")
        print(f"      all transitions:   "
              f"{_fmt(rep(enriched, metric_key))}")
        for name, letter in piece_slices:
            sub = _slice_by_piece(enriched, letter)
            print(f"      {name+' moves:':<19}"
                  f"{_fmt(rep(sub, metric_key))}")
        print(f"      captures:          "
              f"{_fmt(rep(cap_rows, metric_key))}")
        print(f"      non-captures:      "
              f"{_fmt(rep(non_rows, metric_key))}")
    print("")

    # Pairwise cosines
    print(f"  Pairwise cosines (across "
          f"{summary['sample_for_diagnostics']} sampled positions):")
    print(f"    cos(A, B): {summary['cos_ab_mean']:+.3f}")
    print(f"    cos(A, C): {summary['cos_ac_mean']:+.3f}")
    print(f"    cos(B, C): {summary['cos_bc_mean']:+.3f}")
    print("")

    # Timing
    if enriched:
        mean_a_us = float(np.mean([r["t_a"] for r in enriched])) / 1000
        mean_b_us = float(np.mean([r["t_b"] for r in enriched])) / 1000
        mean_c_us = float(np.mean([r["t_c"] for r in enriched])) / 1000
    else:
        mean_a_us = mean_b_us = mean_c_us = 0.0
    print("  Per-call timings (mean over all rows):")
    print(f"    Derivation A: {mean_a_us:.1f} us")
    print(f"    Derivation B: {mean_b_us:.1f} us")
    print(f"    Derivation C: {mean_c_us:.1f} us")
    print("")

    # Decision
    def abs_rho(rows, key):
        rho, _ = rep(rows, key)
        return 0.0 if rho != rho else abs(rho)

    all_slices_a = [
        ("all", enriched, "sim_a"),
        ("captures", cap_rows, "sim_a"),
        ("non-captures", non_rows, "sim_a"),
    ] + [(n, _slice_by_piece(enriched, l), "sim_a")
         for n, l in piece_slices]
    all_slices_b = [
        ("all", enriched, "sim_b_concat"),
        ("captures", cap_rows, "sim_b_concat"),
        ("non-captures", non_rows, "sim_b_concat"),
    ] + [(n, _slice_by_piece(enriched, l), "sim_b_concat")
         for n, l in piece_slices]
    # C-cosine and C-delta participate in the viability decision.
    # C-after-magnitude is the TAUTOLOGICAL baseline per §12.7.1 and
    # is reported separately, not counted toward viability.
    all_slices_c_cosine = [
        (f"all (C cosine)", enriched, "sim_c"),
        (f"captures (C cosine)", cap_rows, "sim_c"),
        (f"non-captures (C cosine)", non_rows, "sim_c"),
    ] + [(f"{n} moves (C cosine)", _slice_by_piece(enriched, l),
          "sim_c") for n, l in piece_slices]
    all_slices_c_delta = [
        (f"all (C delta)", enriched, "dlt_c"),
        (f"captures (C delta)", cap_rows, "dlt_c"),
        (f"non-captures (C delta)", non_rows, "dlt_c"),
    ] + [(f"{n} moves (C delta)", _slice_by_piece(enriched, l),
          "dlt_c") for n, l in piece_slices]
    all_slices_c_mag = [
        (f"all (C |after|)", enriched, "mag_c"),
        (f"captures (C |after|)", cap_rows, "mag_c"),
        (f"non-captures (C |after|)", non_rows, "mag_c"),
    ] + [(f"{n} moves (C |after|)", _slice_by_piece(enriched, l),
          "mag_c") for n, l in piece_slices]

    best_a = max(((abs_rho(rows, key), name, "A")
                  for name, rows, key in all_slices_a),
                 key=lambda t: t[0])
    best_b = max(((abs_rho(rows, key), name, "B")
                  for name, rows, key in all_slices_b),
                 key=lambda t: t[0])
    best_c_cos = max(((abs_rho(rows, key), name, "C-cosine")
                      for name, rows, key in all_slices_c_cosine),
                     key=lambda t: t[0])
    best_c_dlt = max(((abs_rho(rows, key), name, "C-delta")
                      for name, rows, key in all_slices_c_delta),
                     key=lambda t: t[0])
    best_c_mag = max(((abs_rho(rows, key), name, "C-|after|")
                      for name, rows, key in all_slices_c_mag),
                     key=lambda t: t[0])
    # Decision pool EXCLUDES C-|after| (tautological baseline).
    best_overall = max([best_a, best_b, best_c_cos, best_c_dlt],
                       key=lambda t: t[0])
    best_val, best_slice, best_name = best_overall

    print("  Phase A decision (per Section 12.2 + Section 12.7, "
          "excluding tautological C |after|):")
    print(f"    Best |rho| across A / B / C-cosine / C-delta: "
          f"{best_val:.3f} ({best_name}, {best_slice})")
    print("    - If > 0.3: king-attack encoder viable; derivation "
          f"{best_name} carries signal")
    print("              beyond path-1 phasecast_is_check. Proceed to "
          "Phase B (assembly).")
    print("    - If < 0.1: construction pattern does not naturally "
          "produce king-attack")
    print("              signal. Section 11.5 null generalizes. "
          "Record as validated null.")
    print("    - If 0.1-0.3: ambiguous. Researcher decides whether to "
          "refine or accept.")
    if best_val > 0.3:
        label = (f"VIABLE (single-corpus). Derivation {best_name} "
                 f"crosses viability threshold at |rho|={best_val:.3f} "
                 f"in the {best_slice} slice. Three-corpus durability "
                 f"verification required before promotion to viable.")
    elif best_val < 0.1:
        label = (f"VALIDATED NULL. All derivations below 0.1; max "
                 f"|rho|={best_val:.3f} ({best_name}, {best_slice}).")
    else:
        label = (f"AMBIGUOUS. Max |rho|={best_val:.3f} "
                 f"({best_name}, {best_slice}) is in [0.1, 0.3].")
    print(f"    Current: {label}")
    print("")

    # Tautological baseline check: C-|after| should correlate near 1.0
    # with is_check_unsafe since both are defined from C_after's sign.
    print("  Tautological baseline check (C-|C_after| vs "
          "is_check_unsafe):")
    mag_val, mag_slice, _ = best_c_mag
    print(f"    Max |rho| on C-|after|: {mag_val:.3f} ({mag_slice})")
    if mag_val < 0.7:
        print(f"    WARNING: tautological baseline should be near "
              f"1.0; {mag_val:.3f} suggests evaluation-pipeline bug.")
    else:
        print(f"    Tautological baseline recovered as expected "
              f"(|rho| >= 0.7).")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Phase A2 headline: evaluate all three derivations on the
  # drnykterstein §11.5 CSV with k=16 eigenvectors for Derivation A
  python -m king_attack_encoder.evaluate_encoder \\
      --input-csv results/phase_operator_experiments/exp3_phase_similarity.csv \\
      --out results/phase_operator_experiments/exp5_king_attack_correlation_a2.csv \\
      --k-for-a 16
  # -> prints per-derivation max |ρ| per slice, tautological baseline
  #    check, Phase A decision label (VIABLE / AMBIGUOUS / NULL)

  # Three-corpus durability (§12.10.1 validated VIABLE on B king-moves)
  for tag in "" _ashchess _hf; do
    python -m king_attack_encoder.evaluate_encoder \\
        --input-csv results/phase_operator_experiments/exp3_phase_similarity${tag}.csv \\
        --out results/phase_operator_experiments/exp5_king_attack_correlation_a2${tag}.csv \\
        --k-for-a 16
  done

  # Reproduce Phase A (k=5) to compare against Phase A2's k=16 result
  python -m king_attack_encoder.evaluate_encoder \\
      --input-csv results/phase_operator_experiments/exp3_phase_similarity.csv \\
      --out results/phase_operator_experiments/exp5_phase_a_k5.csv \\
      --k-for-a 5

  # Escalate to k=32 if variance-explained at k=16 is below 0.80
  # ("faithful" threshold per §12.7.1)
  python -m king_attack_encoder.evaluate_encoder \\
      --input-csv results/phase_operator_experiments/exp3_phase_similarity.csv \\
      --out results/phase_operator_experiments/exp5_a_k32.csv \\
      --k-for-a 32

see also:
  similarity_experiment.py                   — generates the §11.5 input CSV
  PHASE_OPERATOR_SUPPLEMENT_12.md §12.7.1.1  — Phase A2 evaluation + turn-flip fix
  PHASE_OPERATOR_SUPPLEMENT_12.md §12.10.1   — three-corpus VIABLE verdict
""")
    parser.add_argument(
        "--input-csv", type=Path, required=True,
        help="Path to the §11.5 output CSV (exp3_phase_similarity.csv "
             "or its per-corpus variants). Each row is one pseudo-"
             "legal transition with the is_check_unsafe label this "
             "CLI correlates against. Three separate CSVs exist — "
             "drnykterstein, ashchess, fishtest — per the §12.10.1 "
             "three-corpus durability protocol.")
    parser.add_argument(
        "--out", type=Path, required=True,
        help="Output CSV path (parents created). Same schema as the "
             "input plus Derivation A/B/C similarity columns, delta_c, "
             "mag_c_after, var_exp_a, and per-derivation timings. "
             "Phase A outputs use exp5_..._a2.csv (k=16 post turn-flip "
             "fix); Phase A k=5 outputs used exp5_...csv.")
    parser.add_argument(
        "--sample-for-diagnostics", type=int, default=50,
        help="Number of unique positions used for the pairwise "
             "cos(A,B), cos(A,C), cos(B,C) diagnostics reported in "
             "the stdout summary. Does not affect correlation "
             "numbers (those use all rows). Default 50.")
    parser.add_argument(
        "--k-for-a", type=int, default=16,
        help="Number of Laplacian eigenvectors used for Derivation A. "
             "Default 16 per §12.7.1 (partial variance-explained ~60%% "
             "on drnykterstein; escalate to 32 for \"faithful\" ≥80%%). "
             "Pass 5 to reproduce the original Phase A k setting.")
    args = parser.parse_args()

    t0 = time.perf_counter()
    summary = process_csv(args.input_csv, args.out,
                          args.sample_for_diagnostics,
                          k_for_a=args.k_for_a)
    elapsed = time.perf_counter() - t0
    print_summary(summary)
    print(f"\n  Wall-clock elapsed: {elapsed:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
