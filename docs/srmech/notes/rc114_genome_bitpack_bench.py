"""rc114 (issue #1245 / UPSTREAM §55) — genome bit-packing DoD measurement.

Generates the issue's reference workload and reports:
  (a) the on-disk size of the 1,024-leaf x 256-symbol chromosome (the rc107
      baseline wrote 264,230 bytes — turns.bin 262,400 + manifest ~1,830);
  (b) the per-append wall time for 10 / 20 / 40 appends of 64 KB(-payload)
      chromosomes — the rc107 baseline measured 0.22 -> 0.34 s/append and
      climbing (the F833 super-linear wall). NOTE: rc114 ships (a) complete;
      the O(1)-amortized append + non-quadratic pack ((b) of the issue) is the
      DIRECT FOLLOW-UP rc, so the append numbers here are the honest rc114
      baseline for that work, measured over the ~3.9x smaller packed bodies.

Computational-provenance discipline: this is the committed generating code for
the numbers lodged in the rc114 CHANGELOG entry / issue #1245 thread.

Run:  python notes/rc114_genome_bitpack_bench.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from srmech.amsc import _native                                  # noqa: E402
from srmech.amsc import genome as G                              # noqa: E402
from srmech.amsc.hdc import klein4_random                        # noqa: E402

DIM = 256          # one full tome (LEAF_CAP) — the issue's leaf width
N_LEAVES = 1024    # the issue's chromosome: 1,024 leaves x 256 symbols


def _leaves(n, pool_seeds=range(8)):
    pool = [klein4_random(DIM, seed=s) for s in pool_seeds]
    return [pool[i % len(pool)] for i in range(n)]


def measure_write_size():
    one = klein4_random(DIM, seed=7)
    d = Path(tempfile.mkdtemp())
    try:
        G.genome_save(G.chromosome(_leaves(N_LEAVES), one, label="kernel"),
                      d, the_one=one)
        body = (d / "turns.bin").stat().st_size
        man = (d / "manifest.json").stat().st_size
        total = body + man
        print(f"[write-size DoD] 1,024 x 256 chromosome:")
        print(f"  turns.bin      = {body:,} B")
        print(f"  manifest.json  = {man:,} B")
        print(f"  total          = {total:,} B  (rc107 baseline: 264,230 B; "
              f"reduction {264_230 / total:.2f}x; payload 65,536 B -> "
              f"overhead {total - 65_536:,} B)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def measure_appends(counts=(10, 20, 40)):
    one = klein4_random(DIM, seed=7)
    for n in counts:
        d = Path(tempfile.mkdtemp())
        try:
            G.genome_save(G.chromosome(_leaves(4), one, label="seed"),
                          d, the_one=one)
            t0 = time.perf_counter()
            for k in range(n):
                G.genome_append(d, f"chr{k:04d}", _leaves(N_LEAVES), one)
            dt = time.perf_counter() - t0
            print(f"[append] {n:3d} appends of the 1,024-leaf chromosome: "
                  f"{dt:7.2f} s total, {dt / n:6.3f} s/append")
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    print(f"srmech genome bench (rc114) — native={_native.has_native_genome()}")
    measure_write_size()
    measure_appends()
