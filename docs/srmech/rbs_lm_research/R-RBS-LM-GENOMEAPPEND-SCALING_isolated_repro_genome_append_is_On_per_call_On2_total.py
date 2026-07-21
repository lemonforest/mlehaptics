r"""R-RBS-LM-GENOMEAPPEND-SCALING — isolated, reproducible measurement showing `srmech.amsc.genome.genome_append`
is O(n) PER CALL (O(n^2) total) in chromosome count, NOT the "O(1) amortised" its docstring claims. This is the
attested repro for the UPSTREAM_NOTES §55 ask (b) re-open (append half): §55 ask (b) — "a non-quadratic high-
chromosome-count pack/append" — was RESOLVED at rc241 for `genome_pack` (flat ~0.47 ms/chromosome) but the SAME
fix did NOT reach `genome_append`.

Method (isolates the append cost from payload/tokenisation): append N chromosomes of a FIXED 50-leaf Klein-4
payload to one genome, timing each `genome_append` call, and report the mean ms/call in 10 equal buckets. Constant
payload => a truly O(1)-amortised append is FLAT across buckets; any upward slope is per-call work that grows with
the existing chromosome count. We also print `manifest.json` size vs chromosome count — the suspected cause is that
each append REWRITES the whole manifest (the derived catalog grows with n), so the "append one entry" is actually
"rewrite n entries".

Run:  /tmp/srmech_v/venv/bin/python3 R-RBS-LM-GENOMEAPPEND-SCALING_*.py [N]
srmech 0.9.0rc253. No ALU magnitude-builtin; sha256 via sha256_raw. Composes UPSTREAM_NOTES §55 / F833 / PKG-3.
"""
import os
import shutil
import statistics
import sys
import tempfile
import time

import srmech
from srmech.amsc import genome as g, hdc
from srmech.amsc.format import sha256_raw

DIM = 64


def leaves(n_leaf):
    """A fixed-size payload: n_leaf constant Klein-4 leaves (each DIM lanes in {0,1,2,3})."""
    return [[(i * 7 + j) % 4 for j in range(DIM)] for i in range(n_leaf)]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    n_leaf = 50
    one = hdc.klein4_expand(DIM, 0)
    d = tempfile.mkdtemp()
    print(f"=== genome_append scaling repro (srmech {srmech.__version__}) — {n} appends of a fixed {n_leaf}-leaf payload ===")
    g.genome_save(g.genome(kernels=[("seed", leaves(n_leaf))], the_one=one), d, one, labels=["seed"])

    times, man = [], os.path.join(d, "manifest.json")
    man_sizes = {}
    for i in range(n):
        lab = sha256_raw(f"c{i}".encode())[:16].hex()
        t = time.perf_counter()
        g.genome_append(d, lab, leaves(n_leaf), one)
        times.append(time.perf_counter() - t)
        if (i + 1) % max(1, n // 10) == 0:
            man_sizes[i + 1] = os.path.getsize(man)

    buckets = 10
    step = max(1, n // buckets)
    print(f"\n{'append #':>14} {'ms/call':>9}  (FLAT = O(1); rising = O(n)/call)")
    first_mean = statistics.mean(times[:step])
    for b in range(buckets):
        seg = times[b * step:(b + 1) * step]
        if not seg:
            continue
        m = statistics.mean(seg)
        print(f"{b * step:>6}-{(b + 1) * step:<7} {1000 * m:>9.2f}  {'x%.1f' % (m / first_mean):>6} vs first bucket")

    total = sum(times)
    print(f"\ntotal genome_append wall: {total:.1f}s for {n} calls; last-bucket/first-bucket ratio = "
          f"{statistics.mean(times[-step:]) / first_mean:.1f}x (O(1) would be ~1.0x)")
    print("manifest.json size vs chromosome count:", {k: f"{v / 1024:.0f}KB" for k, v in man_sizes.items()})
    verdict = statistics.mean(times[-step:]) / first_mean
    print(f"VERDICT: per-call time is {'RISING (O(n)/call, O(n^2) total)' if verdict > 2 else 'flat'} — "
          f"the append rewrites the growing manifest each call. Contrast: genome_pack is ~0.47 ms/chromosome (flat) at rc241.")
    shutil.rmtree(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
