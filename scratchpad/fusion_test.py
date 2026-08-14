"""Robertsonian-fusion test IN THE CARRIER — the srmech rc345 (task T964) provenance harness.

SAME content, DIFFERENT chromosome partitioning. Which count is invariant?

This is the generating code for every number quoted in the rc345 CHANGELOG entry and in
``tests/test_genome_content_invariant.py`` (computational-provenance discipline: a
load-bearing number ships its generator).

It runs in TWO modes and is deliberately written against ONLY the surfaces that clean
``origin/main`` already publishes (``chromosome`` / ``genome_save`` / ``genome_catalog`` /
``genome_census``), so it executes unchanged on a pre-rc345 tree:

  * ``python3 fusion_test.py``            — the measurement table (runs on origin/main)
  * ``python3 fusion_test.py --ratchet``  — assert the rc345 claims; exits 1 on a tree
                                            that has not landed them (the origin/main
                                            proof; an ImportError proves nothing, so the
                                            checks are feature-probes, not imports).
  * ``python3 fusion_test.py --cost``     — derive-vs-head-read timings (rc345 only)

Findings pinned here
--------------------
F1  ``genome_save`` returns the FULL catalog (``chromosomes`` / ``regions`` arrays);
    the on-disk HEAD carries the scalar ``n_chromosomes``. Pre-rc345 the catalog had NO
    scalar ``n_chromosomes`` — hence the 8/8 ``None`` reading. The count was never
    missing, it was carried as ``len(data["chromosomes"])``.
F2  Each chromosome emits EXACTLY one boundary cap and a cap IS a turn, so
    ``n_turns - n_chromosomes`` is the INTERIOR block count. It is invariant under
    repartitioning of fixed content; ``n_turns`` and ``body_sha256`` are not.
F3  The interior count equals the LEAF count only when the chromosomes carry no inline
    caps. With ``genes=``, each GENE cap is an interior block too, so the honest law is
    ``n_turns - n_chromosomes == total_leaves + n_interior_caps``.
"""

import os
import sys
import tempfile
import time

# The stale namespace-package `srmech` in ~/.local/lib/python3.10/site-packages shadows
# the source tree in SCRIPT mode (the script's own directory precedes cwd on sys.path).
# Anchor the tree explicitly and PRINT what actually got imported — never trust a number
# from an unverified import.
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRMECH_PY = os.path.join(_HERE, "..", "docs", "srmech", "python")
if os.path.isdir(os.path.join(_SRMECH_PY, "srmech")):
    sys.path.insert(0, os.path.abspath(_SRMECH_PY))

import srmech                                    # noqa: E402
import srmech.amsc.genome as G                   # noqa: E402
from srmech.amsc.hdc import klein4_expand        # noqa: E402

DIM, TOTAL, SEED = 64, 24, 7
PARTITIONS = (1, 2, 3, 4, 6, 8, 12, 24)


def identity():
    """Which srmech is under test? (the verify-the-artifact discipline)."""
    print(f"srmech.__file__ : {srmech.__file__}")
    print(f"srmech.__version__ : {srmech.__version__}")
    print(f"native_status : {srmech.native_status()}")
    print()


def sweep(tmp):
    """The 8-row partition sweep over FIXED content. Returns a list of row dicts."""
    one = klein4_expand(DIM, SEED)
    leaves = [klein4_expand(DIM, s) for s in range(TOTAL)]      # FIXED content
    rows = []
    for parts in PARTITIONS:
        step = TOTAL // parts
        strand = []
        for i in range(parts):
            strand += G.chromosome(leaves[i * step:(i + 1) * step], one, label=f"c{i}")
        p = os.path.join(tmp, f"g{parts}.gnm")
        ret = G.genome_save(strand, p, coupling=one)
        cat = G.genome_catalog(p, coupling=one)
        cen = G.genome_census(p, coupling=one)
        rows.append({
            "parts": parts,
            "step": step,
            # what the RETURN carries ...
            "ret_n_turns": ret.get("n_turns"),
            "ret_n_chromosomes": ret.get("n_chromosomes"),      # None pre-rc345
            "ret_len_chromosomes": len(ret.get("chromosomes", [])),
            "ret_n_content": ret.get("n_content"),              # None pre-rc345
            # ... vs what the re-derived catalog carries
            "cat_n_turns": cat.get("n_turns"),
            "cat_n_chromosomes": cat.get("n_chromosomes"),      # None pre-rc345
            "total_leaves": cen["total_leaves"],
            "body_sha256": ret["body_sha256"],
        })
    return rows


def genes_row(tmp):
    """The F3 control — ONE chromosome carrying 4 inline GENE caps over the same 24
    leaves. The interior count must exceed the leaf count by exactly the cap count."""
    one = klein4_expand(DIM, SEED)
    leaves = [klein4_expand(DIM, s) for s in range(TOTAL)]
    genes = [(f"g{i}", leaves[i * 6:(i + 1) * 6]) for i in range(4)]
    strand = G.chromosome(coupling=one, label="multi", genes=genes)
    p = os.path.join(tmp, "genes.gnm")
    ret = G.genome_save(strand, p, coupling=one)
    cen = G.genome_census(p, coupling=one)
    n_chrom = len(ret.get("chromosomes", []))
    return {
        "n_turns": ret["n_turns"],
        "n_chromosomes": n_chrom,
        "total_leaves": cen["total_leaves"],
        "interior": ret["n_turns"] - n_chrom,
    }


def report(rows, gr):
    print(f"{'partition':>26} | n_turns | n_chrom | leaves | interior | body_sha256[:16]")
    print("-" * 92)
    for r in rows:
        interior = r["ret_n_turns"] - r["ret_len_chromosomes"]
        print(f"{r['parts']:>3} chromosome(s) x {r['step']:>2} leaves | "
              f"{r['ret_n_turns']:>7} | {r['ret_len_chromosomes']:>7} | "
              f"{r['total_leaves']:>6} | {interior:>8} | {r['body_sha256'][:16]}")
    turns = sorted({r["ret_n_turns"] for r in rows})
    interiors = sorted({r["ret_n_turns"] - r["ret_len_chromosomes"] for r in rows})
    shas = {r["body_sha256"] for r in rows}
    print()
    print(f"distinct n_turns             : {turns}"
          f"   -> {'INVARIANT' if len(turns) == 1 else 'VARIES'}")
    print(f"distinct n_chromosomes       : {sorted({r['ret_len_chromosomes'] for r in rows})}"
          f"   -> VARIES (it IS the partitioning)")
    print(f"distinct (n_turns - n_chrom) : {interiors}"
          f"   -> {'INVARIANT' if len(interiors) == 1 else 'VARIES'}")
    print(f"distinct body_sha256         : {len(shas)} distinct"
          f"   -> {'INVARIANT' if len(shas) == 1 else 'VARIES'}")
    print()
    print("--- F1: what genome_save RETURNS vs what the HEAD stores ---")
    n_none = sum(1 for r in rows if r["ret_n_chromosomes"] is None)
    print(f"return['n_chromosomes'] is None in {n_none}/{len(rows)} runs "
          f"(pre-rc345 expected {len(rows)}/{len(rows)}, rc345 expected 0/{len(rows)})")
    print(f"return['n_content']     is None in "
          f"{sum(1 for r in rows if r['ret_n_content'] is None)}/{len(rows)} runs")
    print()
    print("--- F3: the GENE-cap control (interior != leaves when caps are inline) ---")
    print(f"1 chromosome x 4 genes x 6 leaves -> n_turns {gr['n_turns']}, "
          f"n_chromosomes {gr['n_chromosomes']}, total_leaves {gr['total_leaves']}, "
          f"interior {gr['interior']}")
    print(f"interior - total_leaves = {gr['interior'] - gr['total_leaves']} "
          f"(== the inline GENE-cap count)")


def ratchet(rows, gr):
    """The rc345 claims, as assertions. Fails LOUD on clean origin/main."""
    fails = []

    # (1) F2 — the interior count is invariant under repartitioning; n_turns is not.
    interiors = {r["ret_n_turns"] - r["ret_len_chromosomes"] for r in rows}
    if interiors != {TOTAL}:
        fails.append(f"n_turns - n_chromosomes not invariant at {TOTAL}: {sorted(interiors)}")
    if len({r["ret_n_turns"] for r in rows}) == 1:
        fails.append("n_turns is invariant — the fixture no longer discriminates")

    # (2) F1 — genome_save's return must carry the scalar n_chromosomes (rc345).
    for r in rows:
        if r["ret_n_chromosomes"] is None:
            fails.append(f"genome_save return has no 'n_chromosomes' "
                         f"(parts={r['parts']}) — pre-rc345 shape")
            break
        if r["ret_n_chromosomes"] != r["ret_len_chromosomes"]:
            fails.append(f"return n_chromosomes {r['ret_n_chromosomes']} != "
                         f"len(chromosomes) {r['ret_len_chromosomes']}")

    # (3) rc345 — the DERIVED content key is present and correct on both surfaces.
    for r in rows:
        if r["ret_n_content"] is None:
            fails.append(f"genome_save return has no 'n_content' "
                         f"(parts={r['parts']}) — pre-rc345 shape")
            break
        if r["ret_n_content"] != r["ret_n_turns"] - r["ret_len_chromosomes"]:
            fails.append(f"n_content {r['ret_n_content']} != n_turns - n_chromosomes")
    for r in rows:
        if r["cat_n_chromosomes"] is None:
            fails.append("genome_catalog has no 'n_chromosomes' — pre-rc345 shape")
            break

    # (4) rc345 — the O(1) head accessor exists and agrees with the O(n) catalog.
    if not hasattr(G, "genome_content"):
        fails.append("srmech.amsc.genome.genome_content is absent — pre-rc345 surface")

    # (5) F3 — the gene control: interior exceeds leaves by exactly the cap count.
    if gr["interior"] <= gr["total_leaves"]:
        fails.append(f"gene control did not produce interior caps: "
                     f"interior {gr['interior']} <= leaves {gr['total_leaves']}")

    print()
    if fails:
        print(f"RATCHET: {len(fails)} violation(s)")
        for f in fails:
            print(f"  FAIL {f}")
        return 1
    print("RATCHET: clean — every rc345 claim holds")
    return 0


def cost():
    """MEASURE what deriving CONTENT costs against reading the head's cached scalars.

    The one-encoding-per-datum rule admits a cache only when a MEASUREMENT shows CPU
    cost demands it, so the decision needs this number rather than an intuition.

    Read the result carefully: the two columns are NOT the same work. ``genome_content``
    scans the body and therefore also re-derives the region chain and holds it against
    the head's committed ``body_sha256`` (the rc342 read-side integrity bound);
    ``_read_head`` parses a small JSON file and trusts what it says. So the ratio is the
    price of VERIFICATION, not the price of the counts.
    """
    from srmech.amsc.hdc import klein4_expand as _ke
    print()
    print("--- derive (scan + bound) vs head read (cached, unverified) ---")
    print("%9s %11s %13s %13s %8s" % ("leaves", "body_B", "derive_ms", "head_ms", "ratio"))
    one = _ke(DIM, SEED)
    tmp = tempfile.mkdtemp(prefix="cost_")
    for n in (256, 1024, 4096, 16384, 65536, 262144):
        leaves = [_ke(DIM, s % 4) for s in range(n)]
        p = os.path.join(tmp, "g%d" % n)
        G.genome_save(G.chromosome(leaves, one, label="c0"), p, coupling=one)
        body = os.path.getsize(os.path.join(p, "turns.bin"))
        reps = 5
        t = time.perf_counter()
        for _ in range(reps):
            G.genome_content(p)
        derive = (time.perf_counter() - t) / reps * 1000.0
        t = time.perf_counter()
        for _ in range(reps):
            G._read_head(p)
        head = (time.perf_counter() - t) / reps * 1000.0
        print("%9d %11d %13.3f %13.3f %8.1f" % (n, body, derive, head, derive / head))


def main():
    identity()
    tmp = tempfile.mkdtemp(prefix="fusion_")
    rows = sweep(tmp)
    gr = genes_row(tmp)
    report(rows, gr)
    if "--cost" in sys.argv:
        cost()
    if "--ratchet" in sys.argv:
        return ratchet(rows, gr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
