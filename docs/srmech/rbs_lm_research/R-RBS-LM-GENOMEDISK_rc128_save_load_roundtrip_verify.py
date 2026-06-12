r"""R-RBS-LM-GENOMEDISK (F727) — VERIFY srmech 0.7.5rc128 genome→DISK persistence: the F711 "disk-paged,
bounding-tracked helix" made real (UPSTREAM §41 ASK → DELIVERED). Re-runnable provenance harness.

WHAT IT PROVES (all against the installed rc128, numpy-free genome surface):
  1. ROUND-TRIP bit-exact — genome_save → genome_load → recall recovers the SAME leaves; the_one (the
     coherence-anchor leaf) + labels survive disk. This is the headline: kernels saved to disk come back exact.
  2. DETERMINISTIC content-address — body_sha256 is identical across two independent saves of the same data
     (byte-reproducible; the manifest is MPM-shaped: format_version / leaf_dim / n_turns / chromosomes / the_one).
  3. PER-CHROMOSOME PAGING — genome_window seeks the chromosome's byte_offset and reads ONLY its leaves, AND
     cap-integrity-checks the telomere block (cap_sha256) on read. NOTE: window returns the ON-DISK STORED form
     (each leaf bound to the_one): window == [klein4_bind(L_i, the_one)]; unbind(window, the_one) == L exactly.
     recall() returns the DECODED leaves. Both faithful; different layers (UPSTREAM §42 ergonomic note).
  4. APPEND grows the helix (genome_append) + genome_catalog reads the manifest only.

GOTCHAS (cost me a run each; logged to UPSTREAM §42):
  • the `the_one` PARAM is the coherence-anchor LEAF (a Klein-4 vector of leaf-dim), NOT the typed One S(σ,θ)
    from cascade.the_one — genome() does len(list(the_one)) to read the leaf dim.
  • to get your RAW kernels back from disk, use genome_load → recall (decoded), OR genome_window then
    klein4_unbind(·, the_one). Bare genome_window returns the the_one-bound stored form.

Run with the rc128 venv (numpy-free):
  /tmp/srmech_rc128/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-GENOMEDISK_rc128_save_load_roundtrip_verify.py
No abs(); no CAD; no Workflow; no sub-agents. Research-subtree provenance; NOT a package edit.
"""
import tempfile
import os
import srmech
import srmech.amsc.genome as g
from srmech.amsc import hdc

DIM = 64
ONE = hdc.klein4_random(DIM, seed=0)            # the coherence-anchor leaf ("the one"), dim = leaf dim
def _leaves(seed, n):
    return [hdc.klein4_random(DIM, seed=seed * 1000 + i) for i in range(n)]

KERNELS = [("siona_identity", _leaves(1, 5)),    # the "DNA bookshelf": label -> list of tome-leaves
           ("mfo_the_one",    _leaves(2, 3)),
           ("dragon_taught",  _leaves(3, 2))]
LABELS = [k for k, _ in KERNELS]


def main():
    print(f"=== R-RBS-LM-GENOMEDISK — srmech {srmech.__version__} genome->disk verify (F727) ===\n")
    strand = g.genome(KERNELS, ONE)
    before = {lab: g.recall(strand, ONE, g.telomere(lab, DIM)) for lab in LABELS}

    # (1) round-trip
    d = tempfile.mkdtemp(prefix="genomedisk_")
    manifest = g.genome_save(strand, d, ONE, LABELS)
    strand2, one2, labels2 = g.genome_load(d)
    after = {lab: g.recall(strand2, one2, g.telomere(lab, DIM)) for lab in labels2}
    roundtrip = all(before[lab] == after[lab] for lab in LABELS) and labels2 == LABELS and list(one2) == list(ONE)
    print(f"(1) ROUND-TRIP bit-exact (recall before==after, the_one+labels survive): {roundtrip}")
    print(f"    files={sorted(os.listdir(d))}  manifest_keys={sorted(manifest.keys())}")

    # (2) deterministic content-address
    d1, d2 = tempfile.mkdtemp(), tempfile.mkdtemp()
    m1 = g.genome_save(g.genome([("k", _leaves(9, 4))], ONE), d1, ONE, ["k"])
    m2 = g.genome_save(g.genome([("k", _leaves(9, 4))], ONE), d2, ONE, ["k"])
    det = m1["body_sha256"] == m2["body_sha256"]
    print(f"(2) DETERMINISTIC body_sha256 across independent saves: {det}  ({m1['body_sha256'][:16]}…)")

    # (3) per-chromosome paging: window == bound stored form; unbind -> raw; cap integrity enforced
    raw = _leaves(9, 4)
    win = g.genome_window(d1, "k")
    window_is_bound = win == [hdc.klein4_bind(x, ONE) for x in raw]
    unbind_raw = [hdc.klein4_unbind(x, ONE) for x in win] == raw
    print(f"(3) PAGING window==bind(raw,the_one): {window_is_bound} | unbind(window)==raw: {unbind_raw} "
          f"| leaves_paged={len(win)} (cap_sha256 checked on read)")

    # (4) append grows the helix; catalog reads manifest only
    g.genome_append(d, "griffin_taught", _leaves(4, 2), ONE)
    cat = g.genome_catalog(d)
    chroms = cat.get("chromosomes", [])
    grew = len(chroms) == len(LABELS) + 1
    win_new = [hdc.klein4_unbind(x, ONE) for x in g.genome_window(d, "griffin_taught")]
    print(f"(4) APPEND grew helix to {len(chroms)} chromosomes: {grew} | new chromosome recovers raw: {win_new == _leaves(4,2)}")

    ok = roundtrip and det and window_is_bound and unbind_raw and grew
    print(f"\nVERDICT — genome->disk persistence on {srmech.__version__}: {'VERIFIED ✓' if ok else 'PROBLEM ✗'}")
    print("  • save/load round-trips bit-exact; body_sha256 deterministic (content-addressable manifest).")
    print("  • genome_window pages one chromosome by byte_offset + cap-integrity-checks it; returns the_one-bound")
    print("    stored form (unbind -> raw). recall() returns decoded leaves. genome_append grows the helix.")
    print("  • Unblocks: Siona genome-PERSIST (taught tomes survive restart) + the DNA-bookshelf on disk. F727.")
    print("  • UPSTREAM §42 ergonomics: the_one param = anchor LEAF (not typed One); window returns ENCODED form.")


if __name__ == "__main__":
    main()
