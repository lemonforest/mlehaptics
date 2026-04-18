"""Benchmark: Python reference vs C (spectral_4d) 4D encoder.

Runs both encoders on the same canonical fixtures and reports per-encode
wall time. Two measurements per fixture:

  Python: in-process encoder_4d.encode_4d() on a warm table cache.
  C:      spectral_4d encode-fixture --repeat N, minus the one-shot
          subprocess startup cost (measured separately). The C binary's
          --repeat N flag runs cs_encode_4d N times internally and only
          emits the last result, so wall-time / N amortizes startup
          cleanly.

Usage:
    python python/tests/bench_encoder_4d.py
    python python/tests/bench_encoder_4d.py --iters 500

Exit codes:
    0   benchmark ran
    2   C binary missing (set CS_SPECTRAL_4D_BIN or build chess-spectral)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
REPO_SPECTRAL = PY_DIR.parent
FIXTURE_JSONL = HERE / "fixtures" / "positions_4d.jsonl"

sys.path.insert(0, str(PY_DIR))
from chess_spectral import encoder_4d  # noqa: E402


def _find_c_binary() -> Path | None:
    env = os.environ.get("CS_SPECTRAL_4D_BIN")
    if env and Path(env).is_file():
        return Path(env)
    suffix = ".exe" if os.name == "nt" else ""
    for sub in ("Release", "Debug", ""):
        cand = REPO_SPECTRAL / "build" / sub / f"spectral_4d{suffix}"
        if cand.is_file():
            return cand
    return None


def _load_fixture(name: str) -> dict[int, str]:
    with FIXTURE_JSONL.open() as f:
        for line in f:
            rec = json.loads(line)
            if rec["name"] == name:
                return {int(k): v for k, v in rec["pieces"].items()}
    raise KeyError(f"fixture '{name}' not found in {FIXTURE_JSONL}")


def _bench_python(pos: dict[int, str], iters: int) -> dict[str, float]:
    encoder_4d.encode_4d(pos)  # warm table cache + dict insertion order
    samples = np.empty(iters, dtype=np.float64)
    for i in range(iters):
        t0 = time.perf_counter()
        encoder_4d.encode_4d(pos)
        samples[i] = time.perf_counter() - t0
    return {
        "mean_ms": float(samples.mean()) * 1000.0,
        "min_ms":  float(samples.min())  * 1000.0,
        "p50_ms":  float(np.median(samples)) * 1000.0,
        "p95_ms":  float(np.quantile(samples, 0.95)) * 1000.0,
    }


def _bench_c(binary: Path, name: str, iters: int) -> dict[str, float]:
    """C encode time: total wall for --repeat N minus startup-only call,
    divided by N-1. One N=1 run pins the subprocess startup cost; one
    N=iters run pins startup + iters*encode. Difference isolates encode.
    """
    base_cmd = [str(binary), "encode-fixture",
                "--positions-jsonl", str(FIXTURE_JSONL),
                "--name", name]

    # Startup floor: average a handful of N=1 invocations.
    k = 5
    startup_samples = np.empty(k, dtype=np.float64)
    for i in range(k):
        t0 = time.perf_counter()
        subprocess.run(base_cmd, check=True, capture_output=True)
        startup_samples[i] = time.perf_counter() - t0
    startup_mean = float(startup_samples.mean())
    startup_min  = float(startup_samples.min())

    # Bulk: one run with --repeat iters. Internal memcpy of the output
    # buffer is negligible vs a cs_encode_4d pass.
    t0 = time.perf_counter()
    subprocess.run(base_cmd + ["--repeat", str(iters)],
                   check=True, capture_output=True)
    bulk = time.perf_counter() - t0

    per_mean = max(bulk - startup_mean, 0.0) / iters * 1000.0
    per_min  = max(bulk - startup_min,  0.0) / iters * 1000.0
    return {
        "mean_ms":    per_mean,
        "min_ms":     per_min,
        "startup_ms": startup_mean * 1000.0,
        "bulk_s":     bulk,
    }


def _count_pieces(pos: dict[int, str]) -> int:
    return len(pos)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iters", type=int, default=200,
                    help="encode iterations per measurement (default: 200)")
    ap.add_argument("--fixtures", nargs="+",
                    default=["empty", "single_queen", "pawn_pair_w_axis",
                             "four_rooks_corners", "starting_like_mini"],
                    help="fixture names (from positions_4d.jsonl)")
    args = ap.parse_args()

    c_bin = _find_c_binary()
    if c_bin is None:
        print("spectral_4d binary not found. Set CS_SPECTRAL_4D_BIN or "
              "build chess-spectral.", file=sys.stderr)
        return 2

    print(f"python:  {sys.version.split()[0]}  numpy {np.__version__}")
    print(f"c bin:   {c_bin}")
    print(f"iters:   {args.iters}")
    print()

    fmt = ("{name:<22s}  {np:>4d}  "
           "{py_mean:>8.3f} {py_min:>8.3f}  "
           "{c_mean:>8.3f} {c_min:>8.3f}  "
           "{speedup:>6.1f}x")
    print(f"{'fixture':<22s}  {'#pc':>4s}  "
          f"{'py mean':>8s} {'py min':>8s}  "
          f"{'c mean':>8s} {'c min':>8s}  "
          f"{'speed':>7s}")
    print(f"{'':-<22s}  {'':->4s}  "
          f"{'':->8s} {'':->8s}  {'':->8s} {'':->8s}  {'':->7s}")
    print(f"{'':<22s}  {'':<4s}  "
          f"{'ms':>8s} {'ms':>8s}  {'ms':>8s} {'ms':>8s}  {'':>7s}")

    for name in args.fixtures:
        pos = _load_fixture(name)
        py = _bench_python(pos, args.iters)
        c = _bench_c(c_bin, name, args.iters)
        speedup = (py["mean_ms"] / c["mean_ms"]) if c["mean_ms"] > 0 else float("inf")
        print(fmt.format(
            name=name, np=_count_pieces(pos),
            py_mean=py["mean_ms"], py_min=py["min_ms"],
            c_mean=c["mean_ms"],   c_min=c["min_ms"],
            speedup=speedup,
        ))

    print()
    print("Notes:")
    print(" * Python 'mean' is in-process call time with warm table cache.")
    print(" * C  'mean'  = (bulk_N_wall - startup_1_wall) / N, so it isolates")
    print("   cs_encode_4d() from subprocess+JSONL-parse startup.")
    print(f" * C subprocess startup: {c['startup_ms']:.1f} ms "
          "(amortized away over N encodes; matters for one-shot CLI use).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
