r"""R-RBS-LM-GENOMEAPPEND-MEMLEAK — the O(1)-TIME threaded-catalog `genome_append` (§95.3/§95.5, rc257→rc265) has an
O(n)-MEMORY leak: peak RSS climbs ~linearly with the number of appends even though the returned catalog dict stays
tiny — so the retained memory is INTERNAL to `genome_append` (the coupled leaves / turns of every appended body), not
the caller's threaded `cat`. At corpus scale this OOMs: the PKG-3 simplewiki encode (240k bodies, ~413 leaves/body)
was OOM-killed at anon-rss 95 GB after only 3361 bodies.

Measured (rc265, fixed 413-leaf bodies = a full-corpus body):
    appends   peak_RSS_GB   cat.chromosomes   cat.regions
        400      1.64            401              401
        800      5.88            801              801
       2000     16.80           2001             2001
  -> ~8 MB retained PER APPEND, but `cat` is < 1 MB (chromosomes/regions are pointer lists) — the leak is in
     genome_append, not in cat.

Ask (srmech): free the per-append working set (the coupled leaf HVs / staged turns) after the O(1) tail-extend + head
write, so `genome_append` is O(1) in RAM as well as in TIME. Until then, a large corpus must use the memory-bounded
batch/explode/pack path (build each batch in-RAM, explode, one final linear `genome_pack`).

srmech 0.9.0rc265. No ALU magnitude-builtin. Composes §95.3/§95.5/§97, #1407, PKG-3.
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
    print(f"\nVERDICT: peak RSS grew to {rss:.1f} GB over {n} appends (~{1000*(rss-base)/n:.1f} MB/append), but the "
          f"catalog dict is only ~{cat_bytes/1e3:.0f} KB — the leak is INTERNAL to genome_append (retains the "
          f"appended turns), not in the caller's cat. O(1) in time, O(n) in RAM -> OOM at corpus scale (§97).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
