r"""R-RBS-LM-GENOMECRUD (F738) — re-runnable check of the FULL genome CRUD + .chr bundle surface (rc149 delivered
GENOMEPLAN Stage 1 §45 in-place edit + Stage 2 §43 export/import). The substrate-readiness gate for the Siona LM.

Verifies, on the installed srmech: create (genome/genome_save) · read (genome_load/window/genes) · UPDATE in place
(genome_replace) · DELETE in place (genome_remove) · BUNDLE out (genome_export -> .chr) · BUNDLE in (genome_import).
rc149 RESULT: all green (remove leaves survivors intact; replace sets new content; export writes a self-contained
.chr; import re-adds byte-intact). KNOWN-OPEN (GENOMEPLAN Stage 0b / §44 last mile): genome_load still requires
manifest.json (delete it -> GenomeBoundingError) — biology-faithful polish, NOT a CRUD/LM blocker.

Run (numpy-free venv): <venv>/python R-RBS-LM-GENOMECRUD_full_crud_plus_chr_bundle.py
No abs(); no CAD; research-subtree provenance.
"""
import os
import tempfile
import srmech
from srmech.amsc import genome as g, hdc

DIM = 64
ONE = hdc.klein4_random(DIM, seed=0)
def Lv(s, n): return [hdc.klein4_random(DIM, seed=s * 100 + i) for i in range(n)]


def main():
    print(f"=== R-RBS-LM-GENOMECRUD — full genome CRUD + .chr bundle (srmech {srmech.__version__}) ===\n")
    ok = {}
    d = tempfile.mkdtemp()
    g.genome_save(g.genome([("alpha", Lv(1, 3)), ("beta", Lv(2, 2)), ("gamma", Lv(3, 4))], ONE), d, ONE)
    ok["CREATE/READ (save+load, 3 kernels)"] = g.genome_load(d)[2] == ["alpha", "beta", "gamma"]

    g.genome_remove(d, "beta", the_one=ONE)                            # DELETE in place
    ok["DELETE in place (genome_remove 'beta')"] = g.genome_load(d)[2] == ["alpha", "gamma"]

    g.genome_replace(d, "alpha", Lv(7, 5), ONE)                        # UPDATE in place
    cat = g.genome_catalog(d, the_one=ONE)
    ok["UPDATE in place (genome_replace 'alpha' 3->5)"] = next(c["leaf_count"] for c in cat["chromosomes"] if c["label"] == "alpha") == 5

    out = os.path.join(tempfile.mkdtemp(), "gamma.chr")               # BUNDLE out
    g.genome_export(d, "gamma", out, the_one=ONE)
    ok["BUNDLE out (genome_export -> .chr file)"] = os.path.exists(out) and os.path.getsize(out) > 0

    d2 = tempfile.mkdtemp(); g.genome_save(g.genome([("seed", Lv(9, 1))], ONE), d2, ONE)   # BUNDLE in
    g.genome_import(out, d2, the_one=ONE)
    imported = g.partition(g.genome_load(d2)[0], ONE).get("gamma")
    ok["BUNDLE in (genome_import .chr, byte-intact)"] = imported == g.partition(g.genome([("gamma", Lv(3, 4))], ONE), ONE)["gamma"]

    for k, v in ok.items():
        print(f"  [{'OK ' if v else 'FAIL'}] {k}")
    allok = all(ok.values())
    print(f"\n  {sum(ok.values())}/{len(ok)} CRUD+bundle ops OK")

    # the one known-open item (Stage 0b keystone) — load without manifest
    d3 = tempfile.mkdtemp(); g.genome_save(g.genome([("x", Lv(5, 2))], ONE), d3, ONE)
    os.remove(os.path.join(d3, "manifest.json"))
    try:
        g.genome_load(d3); stage0b = True
    except Exception:
        stage0b = False
    print(f"  Stage 0b (§44 last mile: load WITHOUT manifest): {'DONE' if stage0b else 'OPEN (manifest still required — biology-faithful polish, not an LM blocker)'}")
    print(f"\nVERDICT: genome CRUD + .chr bundling {'COMPLETE' if allok else 'INCOMPLETE'} on {srmech.__version__}."
          f" Substrate {'READY' if allok else 'NOT ready'} to back the Siona LM (create/read/update/delete/bundle on")
    print("  genome-stored kernels). Remaining for LM progress = research-subtree wiring (storyteller World <- genome),")
    print("  NOT srmech. Only open srmech item: Stage 0b (manifest-optional load). (F738)")


if __name__ == "__main__":
    main()
