#!/usr/bin/env python3
"""analyze_channel_deltas.py — per-channel mining on safety_field CSVs.

Reads one or more CSVs produced by ``analyze_safety.py`` (which carry
per-ply ΔE_c for 10 spectral channels plus dEval_mover and NAG) and
answers:

  1. Which channels' Δ track signed vs |ΔEval|?               (Step 1)
  2. Does normalizing by mover SPECTRAL_VALS clean that up?    (Step 2)
  3. Does a multi-channel z-score beat scalar ΔS?              (Step 3)
  4. Do annotated blunders share a channel-signature?          (Step 4)
  5. Does a game's fiber/irrep ratio track its chaos?          (Step 5)

The FD channel is ~3 orders larger than others by construction of the
encoder (preserving C-parity, see tables.DIAG_DEV). All multi-channel
scores are built on within-game z-scores, so FD participates on equal
footing without touching the encoder.

Usage:
    python analyze_channel_deltas.py safety_field_VEYpgB14.csv \\
                                     safety_field_9DrFuzPB.csv

All output is to stdout.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

# Windows default console is cp1252; force UTF-8 so Δ, ρ, σ etc. print.
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chess_spectral.tables import SPECTRAL_VALS  # noqa: E402

# ─── Channel groups ──────────────────────────────────────────────────────

IRREP_CHANNELS = ['A1', 'A2', 'B1', 'B2', 'E']
FIBER_CHANNELS = ['F1', 'F2', 'F3', 'FA', 'FD']
ALL_CHANNELS   = IRREP_CHANNELS + FIBER_CHANNELS

BLUNDER_NAGS = {'??', '?'}
NAG_ALL      = {'??', '?', '?!'}

# Significance threshold for n≈115 plies.
P_SIG = 0.05


# ─── CSV loading ─────────────────────────────────────────────────────────

def load_game(csv_path: str) -> list[dict]:
    """Load a safety_field CSV and coerce numeric fields. Rows without
    dEval_mover are kept but marked None so channel analysis can skip
    them consistently."""
    rows: list[dict] = []
    with open(csv_path, encoding='utf-8') as f:
        for raw in csv.DictReader(f):
            r = dict(raw)
            r['ply']  = int(r['ply'])
            r['dS_mover']     = float(r['dS_mover'])
            de = r.get('dEval_mover', '')
            r['dEval_mover']  = float(de) if de not in ('', None) else None
            for c in ALL_CHANNELS:
                r[f'dE_{c}'] = float(r[f'dE_{c}'])
            rows.append(r)
    return rows


# ─── Spearman wrapper (robust to scipy-missing) ─────────────────────────

def _spearmanr(x: np.ndarray, y: np.ndarray):
    from scipy.stats import spearmanr
    rho, p = spearmanr(x, y)
    return float(rho), float(p)


def _sig_mark(p: float) -> str:
    return '  ' if (p is None or p > P_SIG) else ' *'


# ─── Step 1 & 2 — per-channel correlations ──────────────────────────────

def channel_corr_table(rows: list[dict], *, normalize: bool) -> list[dict]:
    """Spearman ρ per channel against signed and |dEval_mover|."""
    with_eval = [r for r in rows if r['dEval_mover'] is not None]
    if len(with_eval) < 4:
        return []

    def scale(r: dict, c: str) -> float:
        v = r[f'dE_{c}']
        if not normalize:
            return v
        pm = r.get('piece_moved') or 'P'
        w  = abs(SPECTRAL_VALS.get(pm.upper(), SPECTRAL_VALS['P']))
        return v / w if w else v

    dEval = np.array([r['dEval_mover'] for r in with_eval])

    out = []
    for c in ALL_CHANNELS:
        dE = np.array([scale(r, c) for r in with_eval])
        rho_s, p_s = _spearmanr(dE, dEval)
        rho_a, p_a = _spearmanr(np.abs(dE), np.abs(dEval))
        out.append({
            'channel':  c,
            'rho_s':    rho_s,   'p_s':    p_s,
            'rho_abs':  rho_a,   'p_abs':  p_a,
        })
    return out


def print_corr_table(title: str, rows: list[dict]) -> None:
    print(title)
    hdr = f"  {'ch':<4} {'rho_signed':>11} {'p_signed':>10}   {'rho_abs':>8} {'p_abs':>10}"
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    for r in rows:
        print(f"  {r['channel']:<4} "
              f"{r['rho_s']:>+9.3f}{_sig_mark(r['p_s'])} "
              f"{r['p_s']:>10.3g}   "
              f"{r['rho_abs']:>+6.3f}{_sig_mark(r['p_abs'])} "
              f"{r['p_abs']:>10.3g}")
    sig = [r['channel'] for r in rows
           if r['p_s'] < P_SIG or r['p_abs'] < P_SIG]
    print(f"  significant (p<{P_SIG}): {sig if sig else '(none)'}")
    print()


# ─── Z-scoring ───────────────────────────────────────────────────────────

def compute_zscores(rows: list[dict]) -> None:
    """Populate r['z_<c>'] = (dE_c / |val(piece_moved)| − μ) / σ in place.
    Guards σ<1e-9 by setting z to 0. Uses all plies (including ply 1)."""
    for c in ALL_CHANNELS:
        vals = []
        for r in rows:
            pm = r.get('piece_moved') or 'P'
            w  = abs(SPECTRAL_VALS.get(pm.upper(), SPECTRAL_VALS['P']))
            vals.append(r[f'dE_{c}'] / w if w else r[f'dE_{c}'])
        arr = np.array(vals)
        mu  = float(arr.mean())
        sd  = float(arr.std(ddof=0))
        for r, v in zip(rows, vals):
            r[f'z_{c}'] = (v - mu) / sd if sd > 1e-9 else 0.0


# ─── Step 3 — anomaly scores ────────────────────────────────────────────

def compute_anomaly(rows: list[dict]) -> None:
    """Add r['L2_all'], r['L2_irrep'], r['L2_fiber'] — L2 of z-scores."""
    for r in rows:
        z_all   = np.array([r[f'z_{c}'] for c in ALL_CHANNELS])
        z_irrep = np.array([r[f'z_{c}'] for c in IRREP_CHANNELS])
        z_fiber = np.array([r[f'z_{c}'] for c in FIBER_CHANNELS])
        r['L2_all']   = float(np.linalg.norm(z_all))
        r['L2_irrep'] = float(np.linalg.norm(z_irrep))
        r['L2_fiber'] = float(np.linalg.norm(z_fiber))


def anomaly_correlations(rows: list[dict]) -> dict:
    with_eval = [r for r in rows if r['dEval_mover'] is not None]
    ae = np.array([abs(r['dEval_mover']) for r in with_eval])
    out = {}
    for key in ('L2_all', 'L2_irrep', 'L2_fiber'):
        vals = np.array([r[key] for r in with_eval])
        rho, p = _spearmanr(vals, ae)
        out[key] = (rho, p, len(with_eval))
    return out


def blunder_pr(rows: list[dict], score_key: str,
               *, tail_frac: float = 0.10) -> dict:
    """Precision/recall at the top-tail-per-side for a given score vs
    truth set (NAG ∈ {??, ?} ∪ {dEval_mover < −1.0})."""
    alerts = set()
    for side in ('w', 'b'):
        sub = [r for r in rows if r['side'] == side]
        if not sub:
            continue
        sub_sorted = sorted(sub, key=lambda r: -r[score_key])
        k = max(1, int(round(tail_frac * len(sub_sorted))))
        alerts.update(id(r) for r in sub_sorted[:k])

    truth = {id(r) for r in rows
             if r['nag'] in BLUNDER_NAGS
             or (r['dEval_mover'] is not None
                 and r['dEval_mover'] < -1.0)}

    tp = len(alerts & truth)
    fp = len(alerts - truth)
    fn = len(truth - alerts)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    return {'tp': tp, 'fp': fp, 'fn': fn,
            'precision': prec, 'recall': rec}


def print_anomaly_report(game_tag: str, rows: list[dict]) -> None:
    print(f"[{game_tag}] Step 3 — multi-channel anomaly scores")
    corrs = anomaly_correlations(rows)
    print(f"  Spearman(score, |dEval_mover|)  n={corrs['L2_all'][2]}")
    for key, (rho, p, _) in corrs.items():
        print(f"    {key:<9} rho={rho:+.3f}{_sig_mark(p)} p={p:.3g}")

    print("\n  Blunder precision/recall at top-10% tail per side "
          "(truth = NAG in {??,?} or dEval<-1.0):")
    for key in ('L2_all', 'L2_irrep', 'L2_fiber'):
        pr = blunder_pr(rows, key)
        print(f"    {key:<9} precision={pr['precision']:.2f} "
              f"recall={pr['recall']:.2f}  "
              f"(tp={pr['tp']}, fp={pr['fp']}, fn={pr['fn']})")

    print("\n  Top-10 plies by L2_all (descending):")
    top = sorted(rows, key=lambda r: -r['L2_all'])[:10]
    print(f"    {'ply':>3} {'side':>4} {'san':<8} {'nag':<3} "
          f"{'dEval':>7} {'L2_all':>7} {'L2_irr':>7} {'L2_fib':>7}")
    for r in top:
        de = (f"{r['dEval_mover']:+.2f}"
              if r['dEval_mover'] is not None else '  ---')
        print(f"    {r['ply']:>3} {r['side']:>4} {r['san']:<8} "
              f"{r['nag']:<3} {de:>7} "
              f"{r['L2_all']:>7.2f} {r['L2_irrep']:>7.2f} "
              f"{r['L2_fiber']:>7.2f}")
    print()


# ─── Step 4 — blunder fingerprints ───────────────────────────────────────

def print_fingerprints(game_tag: str, rows: list[dict]) -> None:
    flagged = [r for r in rows if r['nag'] in NAG_ALL]
    if not flagged:
        print(f"[{game_tag}] Step 4 — no NAG-annotated plies.\n")
        return
    print(f"[{game_tag}] Step 4 — blunder fingerprint (z-scores)")
    chans = '  '.join(f"{c:>5}" for c in ALL_CHANNELS)
    print(f"  {'ply':>3} {'side':>4} {'san':<8} {'nag':<3} {'dEval':>7} | {chans}")
    for r in flagged:
        de = (f"{r['dEval_mover']:+.2f}"
              if r['dEval_mover'] is not None else '  ---')
        zs = '  '.join(f"{r[f'z_{c}']:>+5.2f}" for c in ALL_CHANNELS)
        print(f"  {r['ply']:>3} {r['side']:>4} {r['san']:<8} "
              f"{r['nag']:<3} {de:>7} | {zs}")
    print()


# ─── Step 5 — chaos ratio ────────────────────────────────────────────────

def chaos_ratio(rows: list[dict]) -> float:
    fiber = np.array([r['L2_fiber'] for r in rows])
    irrep = np.array([r['L2_irrep'] for r in rows])
    mi = float(irrep.mean())
    return float(fiber.mean() / mi) if mi > 1e-9 else float('nan')


def nag_count(rows: list[dict]) -> dict:
    c = {'??': 0, '?': 0, '?!': 0}
    for r in rows:
        if r['nag'] in c:
            c[r['nag']] += 1
    return c


# ─── Driver ──────────────────────────────────────────────────────────────

def analyze_one(path: str) -> dict:
    tag = Path(path).stem.replace('safety_field_', '')
    rows = load_game(path)
    print(f"=== {tag}  ({len(rows)} plies from {path}) ===\n")

    # Step 1: raw ΔE correlations
    print_corr_table(f"[{tag}] Step 1 — raw dE_c vs dEval_mover",
                     channel_corr_table(rows, normalize=False))

    # Step 2: value-normalized ΔE correlations
    print_corr_table(f"[{tag}] Step 2 — dE_c / |val(piece_moved)| vs dEval_mover",
                     channel_corr_table(rows, normalize=True))

    # Steps 3 & 4 run off z-scored, value-normalized ΔE.
    compute_zscores(rows)
    compute_anomaly(rows)
    print_anomaly_report(tag, rows)
    print_fingerprints(tag, rows)

    # Step 5 inputs.
    return {
        'tag':       tag,
        'rows':      rows,
        'chaos':     chaos_ratio(rows),
        'nags':      nag_count(rows),
        'scalar_S_corr': _spearmanr(
            np.array([r['dS_mover'] for r in rows if r['dEval_mover'] is not None]),
            np.array([r['dEval_mover'] for r in rows if r['dEval_mover'] is not None]),
        ),
        'anomaly_corr':  anomaly_correlations(rows),
    }


def cross_game_report(games: list[dict]) -> None:
    print("=== Cross-game summary ===\n")
    print(f"  {'game':<10} {'plies':>5} {'??':>3} {'?':>3} {'?!':>3} "
          f"{'chaos':>7} {'rho_S':>7} {'rho_L2_all':>10}")
    for g in games:
        n    = len(g['rows'])
        nags = g['nags']
        rhoS = g['scalar_S_corr'][0]
        rhoL = g['anomaly_corr']['L2_all'][0]
        print(f"  {g['tag']:<10} {n:>5} "
              f"{nags['??']:>3} {nags['?']:>3} {nags['?!']:>3} "
              f"{g['chaos']:>7.3f} {rhoS:>+7.3f} {rhoL:>+10.3f}")
    print()

    # Pooled precision/recall for L2_all across all games.
    pooled = [r for g in games for r in g['rows']]
    pr = blunder_pr(pooled, 'L2_all')
    print(f"  Pooled L2_all blunder precision/recall (top-10% per side "
          f"within each game's distribution is not the same as pooled; "
          f"this pool ranks globally across games):")
    print(f"    precision={pr['precision']:.2f} recall={pr['recall']:.2f} "
          f"(tp={pr['tp']}, fp={pr['fp']}, fn={pr['fn']})")
    print()

    # Findings line — honest verdict.
    print("=== Findings ===\n")
    for g in games:
        rhoS = g['scalar_S_corr'][0]
        rhoL = g['anomaly_corr']['L2_all'][0]
        verdict = ("beats" if abs(rhoL) > abs(rhoS) + 0.05
                   else "ties" if abs(rhoL) > abs(rhoS) - 0.05
                   else "loses to")
        print(f"  [{g['tag']}] L2_all (ρ={rhoL:+.3f}) {verdict} "
              f"scalar ΔS (ρ={rhoS:+.3f}) against |dEval|.")
    print()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    ap.add_argument('csvs', nargs='+', help='safety_field_*.csv inputs')
    args = ap.parse_args(argv)

    games = [analyze_one(p) for p in args.csvs]
    if len(games) > 1:
        cross_game_report(games)
    return 0


if __name__ == '__main__':
    sys.exit(main())
