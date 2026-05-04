"""bit_alu vs complex128 reference encoder — performance + memory benchmark.

Compares the four core HDC operations (bind / bundle / permute /
similarity) and the full encoder round-trip between:

    - the existing complex128 reference (``encode_ant.py`` /
      ``np.complex128`` arrays of dimension D), and
    - the bit-packed binary ALU (``bit_alu.py`` / ``np.uint64`` arrays
      of length ``n_words(D) = ceil(D/64)``).

Run::

    python -m research.bit_alu_benchmark           # default: D=940 + D=13440
    python -m research.bit_alu_benchmark --D 940
    python -m research.bit_alu_benchmark --reps 100000

Reports per-op throughput (ops/sec), wall time per op, and per-HV
memory footprint.

Methodology
-----------

Each operation is timed in a tight loop over ``--reps`` iterations
(default 10_000).  The reference operations use numpy broadcast
where natural; the bit ALU operations use the routines in
``bit_alu``.  Setup cost (basis vector creation, cache warming) is
excluded from the timed region — the loop body runs the operation
on pre-allocated inputs.

The benchmark is intentionally simple: a single-thread, in-process
microbenchmark.  It does NOT speak to inter-process / GPU /
SIMD-accelerated implementations of either backend.

Findings (typical, on contemporary x86-64)
------------------------------------------

See ``figures/bit_alu_findings.md`` for the formatted results table
and discussion.  Headline numbers (D=940):

    bind:        ~10-50× faster on bit ALU (XOR vs complex multiply)
    permute:     ~2-5×  faster on bit ALU (big-int shift+mask vs np.roll)
    similarity:  ~5-20× faster on bit ALU (popcount vs complex inner)
    memory:      125×   smaller         (120 B vs 15 KB at D=940)
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import numpy as np

from . import bit_alu


# ---------------------------------------------------------------------------
# Reference operations on complex128 hypervectors (matches encode_ant.py)
# ---------------------------------------------------------------------------

def _ref_random_hv(D: int, rng: np.random.Generator) -> np.ndarray:
    real = rng.standard_normal(D)
    imag = rng.standard_normal(D)
    v = (real + 1j * imag).astype(np.complex128)
    return v / np.linalg.norm(v)


def _ref_bind(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Element-wise complex multiply.  This is the FHRR-style bind;
    the numpy native operation closest to the bit-ALU's XOR."""
    return a * b


def _ref_bundle(stack: List[np.ndarray]) -> np.ndarray:
    """Sum + L2-normalise — what ``encode_ant._encode_dense`` does."""
    out = np.zeros_like(stack[0])
    for v in stack:
        out = out + v
    n = np.linalg.norm(out)
    if n > 0:
        out = out / n
    return out


def _ref_permute(v: np.ndarray, n: int) -> np.ndarray:
    """Cyclic shift via ``np.roll`` (the existing encoder's permute)."""
    return np.roll(v, n)


def _ref_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Bipolar inner product analogue: |⟨a, b⟩|, real-valued."""
    return float(abs(np.vdot(a, b)))


# ---------------------------------------------------------------------------
# Microbenchmark harness
# ---------------------------------------------------------------------------

@dataclass
class BenchResult:
    op: str
    backend: str
    D: int
    reps: int
    total_seconds: float

    @property
    def per_op_seconds(self) -> float:
        return self.total_seconds / max(self.reps, 1)

    @property
    def ops_per_second(self) -> float:
        return self.reps / max(self.total_seconds, 1e-12)


def _time_op(reps: int, op: Callable[[], None]) -> float:
    """Time ``reps`` invocations of ``op``.  Warms once before the
    timed region.  Returns total wall seconds."""
    op()  # warm
    t0 = time.perf_counter()
    for _ in range(reps):
        op()
    return time.perf_counter() - t0


def benchmark_bind(
    D: int, reps: int, rng: np.random.Generator,
) -> Tuple[BenchResult, BenchResult]:
    a_ref = _ref_random_hv(D, rng)
    b_ref = _ref_random_hv(D, rng)
    a_bit = bit_alu.random_hv(D, rng)
    b_bit = bit_alu.random_hv(D, rng)

    t_ref = _time_op(reps, lambda: _ref_bind(a_ref, b_ref))
    t_bit = _time_op(reps, lambda: bit_alu.bind(a_bit, b_bit))
    return (
        BenchResult("bind", "complex128", D, reps, t_ref),
        BenchResult("bind", "bit_alu", D, reps, t_bit),
    )


def benchmark_bundle(
    D: int, reps: int, rng: np.random.Generator, M: int = 8,
) -> Tuple[BenchResult, BenchResult]:
    refs = [_ref_random_hv(D, rng) for _ in range(M)]
    bits = [bit_alu.random_hv(D, rng) for _ in range(M)]
    bits_stack = np.stack(bits)  # (M, n_words)

    t_ref = _time_op(reps, lambda: _ref_bundle(refs))
    t_bit = _time_op(reps, lambda: bit_alu.bundle_majority(bits_stack, D))
    return (
        BenchResult(f"bundle (M={M})", "complex128", D, reps, t_ref),
        BenchResult(f"bundle (M={M})", "bit_alu", D, reps, t_bit),
    )


def benchmark_permute(
    D: int, reps: int, rng: np.random.Generator, n: int = 1,
) -> Tuple[BenchResult, BenchResult]:
    v_ref = _ref_random_hv(D, rng)
    v_bit = bit_alu.random_hv(D, rng)

    t_ref = _time_op(reps, lambda: _ref_permute(v_ref, n))
    t_bit = _time_op(reps, lambda: bit_alu.permute(v_bit, n, D))
    return (
        BenchResult(f"permute (n={n})", "complex128", D, reps, t_ref),
        BenchResult(f"permute (n={n})", "bit_alu", D, reps, t_bit),
    )


def benchmark_similarity(
    D: int, reps: int, rng: np.random.Generator,
) -> Tuple[BenchResult, BenchResult]:
    a_ref = _ref_random_hv(D, rng)
    b_ref = _ref_random_hv(D, rng)
    a_bit = bit_alu.random_hv(D, rng)
    b_bit = bit_alu.random_hv(D, rng)

    t_ref = _time_op(reps, lambda: _ref_similarity(a_ref, b_ref))
    t_bit = _time_op(reps, lambda: bit_alu.similarity(a_bit, b_bit, D))
    return (
        BenchResult("similarity", "complex128", D, reps, t_ref),
        BenchResult("similarity", "bit_alu", D, reps, t_bit),
    )


def benchmark_full_encode(
    D: int, reps: int,
) -> Tuple[BenchResult, BenchResult]:
    """Time a complete date-to-state round-trip for both backends."""
    from .encode_ant import REFERENCE_JD, _encode_dense
    jd = REFERENCE_JD + 100.0  # arbitrary mid-cycle date

    t_ref = _time_op(reps, lambda: _encode_dense(jd, D))
    t_bit = _time_op(reps, lambda: bit_alu.encode_ant_bit(jd, D))
    return (
        BenchResult("encode_full", "complex128", D, reps, t_ref),
        BenchResult("encode_full", "bit_alu", D, reps, t_bit),
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _memory_footprint_bytes(D: int) -> Tuple[int, int]:
    """Returns (complex128_bytes, bit_alu_bytes) for a single
    hypervector at dimension D."""
    return (D * 16, bit_alu.n_words(D) * 8)


def _format_results(
    results: List[Tuple[BenchResult, BenchResult]],
) -> str:
    lines: List[str] = []
    lines.append(
        f"  {'op':<20}  {'D':>5}  {'reps':>7}  {'cx128 µs/op':>11}  "
        f"{'bit  µs/op':>11}  {'speedup':>8}"
    )
    lines.append("  " + "-" * 75)
    for ref, bit in results:
        cx_us = ref.per_op_seconds * 1e6
        bit_us = bit.per_op_seconds * 1e6
        speedup = (ref.per_op_seconds / max(bit.per_op_seconds, 1e-12))
        lines.append(
            f"  {ref.op:<20}  {ref.D:>5}  {ref.reps:>7}  "
            f"{cx_us:>11.3f}  {bit_us:>11.3f}  {speedup:>7.2f}×"
        )
    return "\n".join(lines)


def _format_memory(D: int) -> str:
    cx, bit = _memory_footprint_bytes(D)
    return (
        f"  D = {D}: complex128 HV = {cx:>6} B; "
        f"bit_alu HV = {bit:>5} B; ratio = {cx/bit:.1f}×"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m research.bit_alu_benchmark",
        description=(
            "Microbenchmark bit_alu vs complex128 reference for the "
            "four HDC primitives + full encoder round-trip."
        ),
    )
    p.add_argument(
        "--D", type=int, action="append", default=None,
        help="Hypervector dimension(s) to test (default: 940 then 13440)."
             " Repeat the flag for multiple D values.",
    )
    p.add_argument(
        "--reps", type=int, default=10_000,
        help="Iteration count per op (default: 10000).",
    )
    p.add_argument(
        "--encode-reps", type=int, default=200,
        help="Iteration count for the full-encode round-trip "
             "(default: 200; encode is ~100× slower than primitives).",
    )
    p.add_argument(
        "--seed", type=int, default=42,
        help="RNG seed for input vectors (default: 42).",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    Ds = args.D if args.D else [940, 13440]
    rng = np.random.default_rng(args.seed)

    print(f"bit_alu benchmark — reps={args.reps}, encode_reps={args.encode_reps}")
    print(f"  numpy: {np.__version__}")
    print()

    print("Memory footprint per hypervector:")
    for D in Ds:
        print(_format_memory(D))
    print()

    for D in Ds:
        print(f"D = {D}:")
        results: List[Tuple[BenchResult, BenchResult]] = []
        results.append(benchmark_bind(D, args.reps, rng))
        results.append(benchmark_bundle(D, args.reps // 5, rng, M=8))
        results.append(benchmark_permute(D, args.reps // 5, rng, n=1))
        results.append(benchmark_similarity(D, args.reps, rng))
        # Full encode is heavier; reduce reps further.
        results.append(benchmark_full_encode(D, args.encode_reps))
        print(_format_results(results))
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
