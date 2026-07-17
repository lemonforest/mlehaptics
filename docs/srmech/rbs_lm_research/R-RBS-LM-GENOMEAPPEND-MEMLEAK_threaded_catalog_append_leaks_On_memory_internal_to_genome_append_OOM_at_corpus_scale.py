r"""R-RBS-LM-GENOMEAPPEND-MEMLEAK — regression guard for the §97 append-RAM leak, NOW FIXED at rc266.

HISTORY (§97, rc257→rc265): the O(1)-TIME threaded-catalog `genome_append` had an O(n)-MEMORY growth — peak RSS climbed
~8 MB/append even though the returned catalog dict stayed < 1 MB, so the retained memory was INTERNAL to the append
(the appended body's staged turns), not the caller's threaded `cat`. At corpus scale it OOMed: the PKG-3 simplewiki
encode (240k bodies, ~413 leaves/body) was OOM-killed at anon-rss 95 GB after only 3361 bodies.

    Measured then (rc265, fixed 413-leaf bodies):  400→1.64 GB · 800→5.88 GB · 2000→16.80 GB  (~8 MB/append)

RESOLVED at rc266 (§97.1): the leak was in the PYTHON WRAPPER ONLY — it sized its append-arena by mis-detecting the
v12 head-only manifest (read whole-body length instead of the head), ballooning the arena on every call. The C-native
`srmech_genome_append` was ALREADY O(1); rc266 moved the sizing to one shared C source of truth
(`srmech_genome_append_arena_bytes`) so the wrapper can't mis-size it. So a C-only / microcontroller host was never
affected. Re-measured at rc266: FLAT (~0.0 MB/append). This script is now a REGRESSION GUARD — it PASSES iff the
per-append RAM stays flat (O(1)); it FAILS if the O(n) leak ever returns.

srmech 0.9.0rc267. No ALU magnitude-builtin. Composes §95.3/§95.5/§97/§97.1, #1407, PKG-3.
Run:  /tmp/srmech_latest/venv/bin/python3 R-RBS-LM-GENOMEAPPEND-MEMLEAK_*.py [N]
"""
import resource
import sys
import tempfile

from srmech.amsc import genome as G, hdc


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    body = 413                                          # ~ a full-corpus body in leaves
    one = hdc.klein4_random(64, seed=0)
    leaves = [[(i * 7 + j) % 4 for j in range(64)] for i in range(body)]   # one reused fixed payload
    d = tempfile.mkdtemp()
    cat = G.genome_save(G.genome([("seed", leaves[:3])], one), d, one, labels=["seed"])
    print(f"=== genome_append threaded-catalog MEMORY (srmech {__import__('srmech').__version__}); {body}-leaf bodies ===")
    print(f"{'appends':>8} {'peak_RSS_GB':>12} {'cat_chrom':>10} {'MB/append':>10}")
    base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
    for i in range(1, n + 1):
        cat = G.genome_append(d, "b%d" % i, leaves, one, catalog=cat)
        if i % max(1, n // 5) == 0:
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
            print(f"{i:>8} {rss:>12.2f} {len(cat.get('chromosomes', [])):>10} {1000 * (rss - base) / i:>10.2f}")
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
    import sys as _s
    cat_bytes = sum(_s.getsizeof(v) for v in cat.values())
    mb_per = 1000 * (rss - base) / n
    flat = mb_per < 1.0                                 # O(1) RAM: < 1 MB/append (rc266 measures ~0.0; the leak was ~8)
    print(f"\nVERDICT: {'PASS (O(1) RAM — §97 leak stays fixed)' if flat else 'FAIL (O(n) RAM leak RETURNED — §97 regressed)'} — "
          f"peak RSS {rss:.2f} GB over {n} appends = {mb_per:.2f} MB/append (catalog dict ~{cat_bytes/1e3:.0f} KB). "
          f"rc266 fixed the python-wrapper arena mis-size (C native was already O(1), §97.1); "
          f"flat here confirms the streaming corpus encode is RAM-bounded.")
    return 0 if flat else 1


if __name__ == "__main__":
    sys.exit(main())
