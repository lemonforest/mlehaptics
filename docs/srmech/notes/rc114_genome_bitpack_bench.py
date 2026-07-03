"""rc114/rc115 (issue #1245) — genome bit-packing + O(1)-append DoD measurement.

Generates the issue's reference workload and reports:
  (a) [rc114, #1245 ask (a)] the on-disk size of the 1,024-leaf x 256-symbol
      chromosome (the rc107 baseline wrote 264,230 bytes — turns.bin 262,400 +
      manifest ~1,830; rc114 bit-packing removes the 4.03x byte-per-symbol bloat);
  (b) [rc115, #1245 ask (b)] the per-append wall time for 10 / 20 / 40 appends of
      the 1,024-leaf chromosome. The rc107 baseline measured 0.22 -> 0.34 s/append
      and CLIMBING (the F833 super-linear wall); the rc114 packed body measured
      0.213 / 0.203 / 0.243 s/append (still whole-body-rewrite bound). rc115 makes
      append O(1)-amortised (tail-extend turns.bin + a manifest region-entry +
      an O(1) body_sha256 chain extension — NO whole-body rewrite / re-hash), so
      the per-append time goes FLAT and DROPS to near-constant ms; AND
  (c) [rc115, #1245 ask (b)] genome_pack SCALING at 2-3 body sizes — the single-
      pass compaction is LINEAR in body size (the old import-per-bundle loop was
      quadratic), plus an EXACT leaf-for-leaf round-trip across append+pack.

Computational-provenance discipline: this is the committed generating code for
the numbers lodged in the rc114/rc115 CHANGELOG entries / issue #1245 thread.

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
    """(b) DoD — per-append wall time. rc115 makes this FLAT + near-constant ms
    (tail-extend, no whole-body rewrite): a per-append time that does NOT grow with
    the genome's total size, far below the 0.213-0.243 s/append rc114 baseline."""
    one = klein4_random(DIM, seed=7)
    per = []
    for n in counts:
        d = Path(tempfile.mkdtemp())
        try:
            G.genome_save(G.chromosome(_leaves(4), one, label="seed"),
                          d, the_one=one)
            t0 = time.perf_counter()
            for k in range(n):
                G.genome_append(d, f"chr{k:04d}", _leaves(N_LEAVES), one)
            dt = time.perf_counter() - t0
            per.append(dt / n)
            print(f"[append] {n:3d} appends of the 1,024-leaf chromosome: "
                  f"{dt:7.2f} s total, {dt / n:6.3f} s/append")
        finally:
            shutil.rmtree(d, ignore_errors=True)
    # FLATNESS: the per-append time must NOT grow super-linearly with the genome
    # size (the F833 wall closed). 40-append per-append <= 1.5x the 10-append one.
    if len(per) >= 2:
        ratio = per[-1] / per[0]
        print(f"[append] flatness: 40-vs-10 per-append ratio = {ratio:.2f} "
              f"({'FLAT — O(1) amortised' if ratio < 1.5 else 'STILL CLIMBING'})")


def _pack_roundtrip_exact(one, n_chroms):
    """Build an n_chroms genome by append, explode + pack it, and prove the packed
    genome round-trips EXACT leaf-for-leaf (per chromosome). Returns the pack
    wall-time + the packed body size."""
    d = Path(tempfile.mkdtemp())
    try:
        want = {}
        lv0 = _leaves(N_LEAVES)
        G.genome_save(G.chromosome(lv0, one, label="c000"), d / "g", the_one=one)
        want["c000"] = [list(x) for x in lv0]
        for k in range(1, n_chroms):
            # full 1,024-leaf chromosomes so the packed body scales ~n x (66 KB
            # each) — a clean linear-scaling probe across the size sweep.
            lv = _leaves(N_LEAVES)
            G.genome_append(d / "g", f"c{k:03d}", lv, one)
            want[f"c{k:03d}"] = [list(x) for x in lv]
        G.genome_explode(d / "g", d / "loose", the_one=one)
        body = (d / "g" / "turns.bin").stat().st_size
        t0 = time.perf_counter()
        G.genome_pack(d / "loose", d / "packed", the_one=one)
        dt = time.perf_counter() - t0
        # EXACT round-trip: every chromosome's leaves survive pack, leaf-for-leaf.
        for lbl, leaves in want.items():
            win = G.genome_window(d / "packed", lbl, the_one=one)
            got = [list(G.quad_turn(t, one)) for t in win]
            assert got == leaves, f"pack round-trip MISMATCH for {lbl}"
        return dt, body
    finally:
        shutil.rmtree(d, ignore_errors=True)


def measure_pack(sizes=(10, 20, 40)):
    """(c) DoD — genome_pack single-pass compaction is LINEAR in body size (the old
    import-per-bundle loop was quadratic). Also asserts an EXACT append+pack
    round-trip. Reports pack s / body-MB to expose the scaling."""
    one = klein4_random(DIM, seed=7)
    rates = []
    for n in sizes:
        dt, body = _pack_roundtrip_exact(one, n)
        mb = body / 1e6
        rate = dt / mb if mb else 0.0
        rates.append(rate)
        print(f"[pack] {n:3d} chromosomes ({body:,} B body): {dt:6.3f} s pack, "
              f"{rate:6.3f} s/MB  (round-trip EXACT)")
    if len(rates) >= 2:
        spread = max(rates) / min(rates) if min(rates) else 0.0
        print(f"[pack] scaling: s/MB spread across sizes = {spread:.2f}x "
              f"({'LINEAR — const s/MB' if spread < 2.0 else 'SUPER-LINEAR'})")


if __name__ == "__main__":
    print(f"srmech genome bench (rc115) — native={_native.has_native_genome()}")
    measure_write_size()
    measure_appends()
    measure_pack()
