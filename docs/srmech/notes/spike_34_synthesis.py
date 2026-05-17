"""Spike #34 synthesis NDJSON — consolidate all findings into one file."""

import io
import json
import math
import re
import sys

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


def parse_record(line, file_label):
    rec = json.loads(line)
    return rec


def parse_console_output(path, file_label):
    """Parse 'β_DV=+0.4107, Δβ=+0.0774' lines from console output files."""
    records = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    current_substrate = None
    current_pred_dS = None
    for line in lines:
        # Substrate header
        m_hdr = re.search(r'=== (.+?) \(n=(\d+), d_S_pred=(.+?)\)', line)
        if m_hdr:
            current_substrate = m_hdr.group(1)
            current_pred_dS = float(m_hdr.group(3))
            continue
        # Rho result line: "   rho= 0.005 (n_traps=   5): beta_DV=+0.5095, delta_beta=+0.1762, ..."
        # Handle both Unicode β/Δβ and ASCII beta/delta_beta variants
        m = re.search(r'rho=\s*([\d.]+)\s*\(n_traps=\s*(\d+)\):\s*(?:β_DV|beta_DV)=([+\-][\d.]+),\s*(?:Δβ|delta_beta)=([+\-][\d.]+),\s*S_min=([\d.eE+\-]+)', line)
        if m and current_substrate:
            rho = float(m.group(1))
            n_traps = int(m.group(2))
            beta_DV = float(m.group(3))
            delta_beta = float(m.group(4))
            S_min = float(m.group(5))
            records.append({
                "source": file_label,
                "substrate": current_substrate,
                "predicted_d_S": current_pred_dS,
                "rho": rho,
                "n_traps": n_traps,
                "beta_DV": beta_DV,
                "delta_beta": delta_beta,
                "S_at_min": S_min,
            })
    return records


def main():
    from pathlib import Path as _Path
    _HERE = _Path(__file__).resolve().parent
    # Read main NDJSON
    main_records = []
    with open(str(_HERE / "spike_34_v2_records_2026-05-17.ndjson"), "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            main_records.append({
                "source": "spike_34_v2",
                "substrate": r["substrate"],
                "n_vertices": r["n_vertices"],
                "trap_density_rho": r["trap_density_rho"],
                "n_realisations": r["n_realisations"],
                "predicted_d_S": r["predicted_d_S"],
                "predicted_beta_canonical": r["predicted_beta_canonical"],
                "DV_beta": r["DV_beta"],
                "delta_beta_DV_vs_canonical": r["delta_beta_DV_vs_canonical"],
                "DV_S_at_min": r["DV_S_at_min"],
                "DV_r2_at_min": r["DV_r2_at_min"],
                "fit_stretched_exp_DV_r2": (r.get("fit_stretched_exp_DV_window", {}) or {}).get("r2"),
                "fit_single_exp_DV_r2": (r.get("fit_single_exp_DV_window", {}) or {}).get("r2"),
                "fit_power_law_DV_r2": (r.get("fit_power_law_DV_window", {}) or {}).get("r2"),
                "winner_form_DV": r["winner_form_DV_window"],
                "fit_stretched_exp_tail_r2": (r.get("fit_stretched_exp_tail", {}) or {}).get("r2"),
                "fit_single_exp_tail_r2": (r.get("fit_single_exp_tail", {}) or {}).get("r2"),
                "fit_power_law_tail_r2": (r.get("fit_power_law_tail", {}) or {}).get("r2"),
                "S_dynamic_range": r["S_dynamic_range"],
            })

    # Parse console outputs (agent-local; absent in committed notes/ — script gracefully skips)
    def _maybe(path, label):
        try:
            return parse_console_output(path, label)
        except FileNotFoundError:
            print(f"  (skipping {label}: console output not in notes/ — committed synthesis NDJSON is canonical)")
            return []
    extra1 = _maybe("D:/temp/spike_34/convergence_skip_L7_output.txt", "convergence_skip_L7")
    extra2 = _maybe("D:/temp/spike_34/sparse_rho_output.txt", "sparse_rho")
    extra2b = _maybe("D:/temp/spike_34/sparse_rho_continued_output.txt", "sparse_rho_continued")
    extra3 = _maybe("D:/temp/spike_34/convergence_output.txt", "convergence")
    extra2 = extra2 + extra2b

    all_records = main_records + extra1 + extra2 + extra3

    # Write synthesis NDJSON
    with open(str(_HERE / "spike_34_synthesis_records_2026-05-17.ndjson"), "w") as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(all_records)} synthesis records")
    print(f"   Main records: {len(main_records)}")
    print(f"   Convergence (path/cycle/torus): {len(extra1)}")
    print(f"   Sparse-rho: {len(extra2)}")
    print(f"   Convergence (sierpinski partial): {len(extra3)}")

    # Print summary
    print()
    print("FUNCTIONAL-FORM SUMMARY (from main records):")
    print(f"   Total cases: {len(main_records)}")
    winners = {}
    for r in main_records:
        w = r["winner_form_DV"]
        winners[w] = winners.get(w, 0) + 1
    for w, count in winners.items():
        print(f"   {w}: {count} cases")

    print()
    print("CASCADE-SUBSTRATE PASS RATE (delta_beta < 0.05):")
    cascade_records = [r for r in main_records if r["predicted_beta_canonical"] is not None and r["DV_beta"] is not None]
    passing = sum(1 for r in cascade_records if abs(r["delta_beta_DV_vs_canonical"]) < 0.05)
    print(f"   {passing} / {len(cascade_records)} cascade-substrate cases PASS at Δβ < 0.05")
    print(f"   Pass rate: {100*passing/max(1,len(cascade_records)):.1f}%")
    for r in cascade_records:
        if abs(r["delta_beta_DV_vs_canonical"]) < 0.05:
            print(f"     PASS: {r['substrate']}: beta_DV={r['DV_beta']:.4f}, "
                  f"delta_beta={r['delta_beta_DV_vs_canonical']:+.4f}")

    # Per-substrate-family β statistics
    print()
    print("PER-SUBSTRATE-FAMILY beta statistics (all data sources):")
    all_data = main_records + extra1 + extra2 + extra3
    families = {
        "sierpinski": [r for r in all_data if "sierp" in r["substrate"].lower()],
        "path": [r for r in all_data if "path" in r["substrate"].lower()],
        "cycle": [r for r in all_data if "cycle" in r["substrate"].lower()],
        "torus": [r for r in all_data if "torus" in r["substrate"].lower()],
        "random_3reg": [r for r in all_data if "random_3reg" in r["substrate"].lower() or "3regular" in r["substrate"].lower()],
    }
    for name, recs in families.items():
        betas = []
        for r in recs:
            b = r.get("DV_beta") or r.get("beta_DV")
            if b is not None:
                betas.append(b)
        if betas:
            pred = None
            for r in recs:
                p = r.get("predicted_beta_canonical") or (
                    r.get("predicted_d_S") / (r.get("predicted_d_S") + 2.0)
                    if r.get("predicted_d_S") else None
                )
                if p is not None and not (isinstance(p, float) and math.isnan(p)):
                    pred = p
                    break
            beta_mean = sum(betas) / len(betas)
            beta_min = min(betas)
            beta_max = max(betas)
            pred_s = f"{pred:.4f}" if pred is not None else "n/a"
            print(f"  {name}: n_cases={len(betas)}, beta_range=[{beta_min:.4f}, {beta_max:.4f}], "
                  f"mean={beta_mean:.4f}, predicted={pred_s}")


if __name__ == "__main__":
    main()
