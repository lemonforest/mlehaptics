r"""R-RBS-LM-SIONAGENEPOOL (F739-followon) — wire the storyteller + etak-walk into the genome, and put the
FOUNDATIONAL MFO + srmech research notebooks into Siona's genepool. srmech 0.7.5rc149.

WHAT THIS DOES:
  1. Builds the full Siona GENEPOOL genome on disk: siona_identity · signwriting (F735) · dict-en-1600 +
     dict-en-2026 (F739 era-dictionaries) · **mfo_notebook** + **srmech_notebook** (each section = a GENE).
  2. A genome-BACKED storyteller World whose knowledge IS the genepool — it INTROSPECTS (genome_catalog), routes a
     prompt to a chromosome, and ETAK-WALKS it (page the chromosome's genes, navigate to the section that matches),
     then RENDERS, or ASKS on a gap (F661 carries). This is STORYMODULE's World, genome-backed (the SIONASERVER /v1
     would import THIS instead of its hardcoded demo shelf).

ETAK-WALK (F704 "thinking is a grounded walk, not a trace"): the walk = introspect -> page the chromosome
(genome_genes) -> navigate to the nearest landmark (here: the section whose heading/summary best matches the query
terms — a legible placeholder for the spectral etak-head F510; the SEMANTIC nearest-section is the WIKIKERNEL
co-occurrence-Laplacian follow-on). The genome supplies the *navigable structure*; etak supplies the *walk*.

NOTEBOOKS-AS-KERNELS (honest scope): each notebook's `## ` sections become GENES (content-addressed leaves); the
renderable text (heading + first content line) is MPR-attested payload (NDJSON, the AMSC content layer). So the
genome holds the notebook's introspectable SECTIONAL STRUCTURE; full per-paragraph deep-encoding is the WIKIKERNEL
follow-on. The MFO (ontology) + srmech (mechanism) notebooks are now in Siona's foundational genepool.

Run (rc149 venv, numpy-free), from the worktree root:
  /tmp/srmech_rc149/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONAGENEPOOL_...py
No abs(); no CAD; research-subtree scaffold (NOT a package edit).
"""
import re
import tempfile
import os
from pathlib import Path
import srmech
from srmech.amsc import genome as g, hdc
from srmech.amsc.format import sha256_raw, write_ndjson, read_ndjson, MPRRecord

DIM = 64
ONE = hdc.klein4_random(DIM, seed=0)
def _seed(t): return int.from_bytes(sha256_raw(t.encode())[:4], "big")
def _leaf(t): return hdc.klein4_random(DIM, seed=_seed(t))
def _slug(s): return (re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "sec")[:36]

ERA_DEFS = {
    "dict-en-1600": {"nice": "foolish or ignorant", "awful": "awe-inspiring, worthy of awe",
                     "computer": "a person who computes", "meat": "food in general", "silly": "blessed, innocent"},
    "dict-en-2026": {"nice": "pleasant, agreeable", "awful": "very bad",
                     "computer": "an electronic machine", "meat": "animal flesh", "silly": "foolish"},
}
NOTEBOOKS = {"mfo_notebook": "docs/antikythera-maths/mfo_spectral_research_notebook.md",
             "srmech_notebook": "docs/srmech/srmech_research_notebook.md"}


def parse_sections(path, cap=48):
    """## headings -> [(section_label, heading_text, summary_line)]; the notebook's sectional structure."""
    lines = Path(path).read_text(errors="replace").splitlines()
    secs = []
    for idx, ln in enumerate(lines):
        if ln.startswith("## "):
            heading = ln[3:].strip()
            summ = ""
            for j in range(idx + 1, min(idx + 10, len(lines))):
                t = lines[j].strip()
                if t and not t.startswith("#"):
                    summ = t[:160]; break
            secs.append((f"{len(secs):02d}_{_slug(heading)}", heading, summ))
    return secs[:cap]


def build_genepool(path):
    payload = []                                              # MPR rows: the renderable text (AMSC content layer)
    chromosomes = [("siona_identity", [("self", [_leaf("siona/self")])]),
                   ("signwriting", [(c, [_leaf(f"sw/{c}")]) for c in
                                    ("hands", "movement", "dynamics", "head_faces", "body", "punctuation", "location")])]
    for era, defs in ERA_DEFS.items():
        chromosomes.append((era, [(w, [_leaf(f"{era}/{w}")]) for w in defs]))
        payload += [(era, w, d) for w, d in defs.items()]
    for kernel, nbpath in NOTEBOOKS.items():
        secs = parse_sections(nbpath)
        chromosomes.append((kernel, [(lab, [_leaf(f"{kernel}/{lab}")]) for lab, _, _ in secs]))
        payload += [(kernel, lab, f"{head} — {summ}".strip(" —")) for lab, head, summ in secs]
    strand = g.genome(chromosomes=[(lab, genes) for lab, genes in chromosomes], the_one=ONE)
    g.genome_save(strand, path, ONE, [lab for lab, _ in chromosomes])
    rows = [MPRRecord(mpr_version="1.0",
                      data={"kernel": k, "key": key, "text": txt},
                      data_schema_id="rbslm://schema/siona_genepool/v1",
                      attestation={"retrieved_at": "2026-06-14T00:00:00Z",
                                   "response_sha256": sha256_raw(f"{k}/{key}/{txt}".encode()).hex(),
                                   "license": "CC0", "parser_version": f"srmech {srmech.__version__}"},
                      rendering={"name": f"{k}:{key}", "purpose": "genepool kernel content", "cite_as": k})
            for k, key, txt in payload]
    write_ndjson(Path(path) / "genepool.ndjson", rows)


class SionaGenepool:
    """STORYMODULE's World, genome-backed: introspect / route / etak-walk / render / ask."""
    def __init__(self, path):
        self.path = path
        self._text = {(r.data["kernel"], r.data["key"]): r.data["text"]
                      for r in read_ndjson(Path(path) / "genepool.ndjson")}

    def introspect(self):
        return [(c["label"], c["leaf_count"]) for c in g.genome_catalog(self.path, the_one=ONE)["chromosomes"]]

    def _route(self, prompt):                                # which chromosome does this prompt land in?
        p = prompt.lower()
        if "mfo" in p or "ontolog" in p or "chirality" in p: return "mfo_notebook"
        if "srmech" in p or "cascade" in p or "a-n" in p or "class" in p: return "srmech_notebook"
        yrs = [int(y) for y in re.findall(r"\b(1[0-9]{3}|20[0-2][0-9])s?\b", p)]
        if re.search(r"\b(archaic|olde?|old|historical|centur)\b", p) or any(y < 1900 for y in yrs): return "dict-en-1600"
        return "dict-en-2026"

    def etak_walk(self, kernel, prompt):                     # page the chromosome, navigate to the nearest section
        genes = [lab for lab, _ in g.genome_genes(self.path, kernel, the_one=ONE)]   # page IN (the genome supplies structure)
        q = set(re.findall(r"[a-z0-9]+", prompt.lower()))
        def score(lab):                                       # proximity gate: term-overlap with the section text (etak landmark)
            txt = self._text.get((kernel, lab), lab).lower()
            return len(q & set(re.findall(r"[a-z0-9]+", txt)))
        best = max(genes, key=score) if genes else None
        return best, (score(best) if best else 0)

    def infer(self, prompt):
        kernel = self._route(prompt)
        if kernel.startswith("dict-en-"):                    # a definition lookup (era-correct)
            words = [w for w, _ in g.genome_genes(self.path, kernel, the_one=ONE)]
            hit = next((w for w in words if re.search(rf"\b{re.escape(w)}\b", prompt.lower())), None)
            if hit: return f"[{kernel}] {hit}: {self._text[(kernel, hit)]}"
            return f"[{kernel}] no matching word loaded. What is it?"                 # asking-state
        lab, sc = self.etak_walk(kernel, prompt)             # a notebook walk
        if lab and sc > 0:
            return f"[{kernel} -> §{lab}] {self._text.get((kernel, lab), lab)}"
        return f"[{kernel}] I walked the genome but found no matching section. What is it?"   # asking-state


def main():
    print(f"=== R-RBS-LM-SIONAGENEPOOL — storyteller+etak over the genome, notebooks in the genepool (srmech {srmech.__version__}) ===\n")
    d = tempfile.mkdtemp(prefix="siona_genepool_")
    build_genepool(d)
    s = SionaGenepool(d)

    print("Siona INTROSPECTS her genepool (genome_catalog):")
    for lab, n in s.introspect():
        print(f"    {lab:16} ({n} genes)")
    print("\n--- the storyteller etak-walks the genome to answer ---")
    for q in ["what is MFO about chirality?",
              "explain the srmech A-N classes",
              "translate this 1600s line: a nice and awful sight  (define awful)",
              "in modern english, define awful",
              "what is qwérty?"]:
        print(f"  Q: {q}\n   A: {s.infer(q)}")
    print("\nVERDICT: storyteller World is GENOME-BACKED (introspect genome_catalog -> route -> etak-walk genome_genes")
    print("  -> render MPR payload / ask). MFO + srmech notebooks are in the genepool as section-gene chromosomes.")
    print("  etak-walk = page the chromosome + navigate to the matching section (legible placeholder; semantic")
    print("  nearest-section = the WIKIKERNEL spectral follow-on). The SIONASERVER /v1 imports THIS as its World.")


if __name__ == "__main__":
    main()
