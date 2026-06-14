r"""R-RBS-LM-SIONAGENOME (F737-build) — the next two steps for Siona LM progress, on srmech 0.7.5rc149:
  STEP 1: build the FOUNDATIONAL language kernel into a genome on disk (SignWriting F735 + identity + an ERA-aware
          dictionary), each a chromosome.
  STEP 2: wire a genome-BACKED Siona World — its inventory comes from genome introspection (genome_catalog), it
          LOADS/UNLOADS dictionary chromosomes by context, renders era-correct definitions, and ASKS on a gap.

THE ERA-DICTIONARY IDEA (user direction 2026-06-14): definitions drift, so a dictionary kernel is bound to a NOW.
We ship TWO era-dictionaries of the SAME words to PROVE the drift (real, well-known semantic shifts — illustrative,
not from a cited period dictionary; a production era-dictionary is built from real period sources, "anyone can"):
  word       dict-en-1600 (era)                         dict-en-2026 (now)
  nice       foolish / ignorant (L. nescius)            pleasant, agreeable
  awful      awe-inspiring, worthy of awe               very bad
  computer   a person who computes                      an electronic machine
  meat       food in general                            animal flesh
  silly      blessed, innocent, happy (OE sælig)        foolish
The ERA BINDING = the chromosome LABEL (`dict-en-1600` / `dict-en-2026`) + the genome's MPR `retrieved_at` timestamp.
The genome holds the era-stamped, introspectable STRUCTURE (words = genes); the renderable definition TEXT is the
MPR-attested payload (NDJSON) — the AMSC content layer (this is payload, not the structural sidecar §44 rejects).

SELF-REALISATION (the mechanism, honestly scoped): Siona introspects `genome_catalog` to KNOW which eras it holds,
and a context cue (a pre-1900 year, or 'archaic/old') self-selects the era-dictionary to load. Full autonomous
era-detection from arbitrary text is the inference capability that GENERALISES with enough reference material — we
build the ABILITY (introspect + load/unload + render-by-era + ask), others bring the corpora.

Run (rc149 venv, numpy-free): <venv>/python R-RBS-LM-SIONAGENOME_genome_backed_world_era_dictionary.py
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

def _seed(text):                                  # Class-A content-address -> deterministic leaf seed
    return int.from_bytes(sha256_raw(text.encode())[:4], "big")
def _leaf(text):
    return hdc.klein4_random(DIM, seed=_seed(text))

# the era-stamped definition payload (the renderable text; the genome holds the structure)
ERA_DEFS = {
    "dict-en-1600": {"nice": "foolish or ignorant", "awful": "awe-inspiring, worthy of awe",
                     "computer": "a person who computes", "meat": "food in general",
                     "silly": "blessed, innocent, happy"},
    "dict-en-2026": {"nice": "pleasant, agreeable", "awful": "very bad",
                     "computer": "an electronic machine", "meat": "animal flesh",
                     "silly": "foolish"},
}


def build_foundation(path):
    """STEP 1 — pack the foundational language kernels into one genome on disk."""
    chromosomes = [
        ("siona_identity", [("self", [_leaf("siona is the grounded interface")])]),
        ("signwriting",    [(c, [_leaf(f"signwriting/{c}")]) for c in
                            ("hands", "movement", "dynamics", "head_faces", "body", "punctuation", "location")]),
        # each era-dictionary = a chromosome; each WORD = a gene (content-addressed); era lives in the LABEL
        ("dict-en-1600",   [(w, [_leaf(f"1600/{w}")]) for w in ERA_DEFS["dict-en-1600"]]),
        ("dict-en-2026",   [(w, [_leaf(f"2026/{w}")]) for w in ERA_DEFS["dict-en-2026"]]),
    ]
    strand = g.genome(chromosomes=[(lab, genes) for lab, genes in chromosomes], the_one=ONE)
    g.genome_save(strand, path, ONE, [lab for lab, _ in chromosomes])
    # the renderable definitions = MPR-attested payload alongside the genome (AMSC content layer)
    rows = [MPRRecord(mpr_version="1.0",
                      data={"era": era, "word": w, "definition": d},
                      data_schema_id="rbslm://schema/era_dictionary/v1",
                      attestation={"retrieved_at": f"{era.split('-')[-1]}-01-01T00:00:00Z",
                                   "response_sha256": sha256_raw(f"{era}/{w}/{d}".encode()).hex(),
                                   "license": "CC0", "parser_version": f"srmech {srmech.__version__}"},
                      rendering={"name": f"{era}:{w}", "purpose": "era-correct definition", "cite_as": era})
            for era, defs in ERA_DEFS.items() for w, d in defs.items()]
    write_ndjson(Path(path) / "definitions.ndjson", rows)


class GenomeWorld:
    """STEP 2 — a Siona World whose knowledge is the genome on disk (introspect / load / unload / render / ask)."""
    def __init__(self, path):
        self.path = path
        self.active_era = None
        self.shelf = {}                                            # word -> definition (the LOADED era)
        self._defs = {(r.data["era"], r.data["word"]): r.data["definition"]
                      for r in read_ndjson(Path(path) / "definitions.ndjson")}

    def introspect(self):                                          # what do I hold? (genome_catalog = self-knowledge)
        cat = g.genome_catalog(self.path, the_one=ONE)
        return [(c["label"], c["leaf_count"]) for c in cat["chromosomes"]]

    def eras_available(self):
        return sorted(lab for lab, _ in self.introspect() if lab.startswith("dict-en-"))

    def load_era(self, era):                                       # page that dictionary chromosome IN
        words = [w for (w, _) in g.genome_genes(self.path, era, the_one=ONE)]
        self.shelf = {w: self._defs[(era, w)] for w in words if (era, w) in self._defs}
        self.active_era = era
        return len(self.shelf)

    def unload(self):
        self.shelf = {}; self.active_era = None

    def self_select_era(self, prompt):                            # the self-realisation cue (mechanism)
        yrs = [int(y) for y in re.findall(r"\b(1[0-9]{3}|20[0-2][0-9])s?\b", prompt)]   # 's?' catches "1600s"
        archaic = bool(re.search(r"\b(archaic|olde?|old|historical|ye|centur)\b", prompt, re.I)) or any(y < 1900 for y in yrs)
        return "dict-en-1600" if archaic else "dict-en-2026"

    def define(self, word):                                        # render from the LOADED era, or ASK (F661)
        if word in self.shelf:
            return f"({self.active_era}) {word}: {self.shelf[word]}"
        return f"I have no '{word}' loaded for {self.active_era or 'any era'}. What is it?"   # asking-state


def main():
    print(f"=== R-RBS-LM-SIONAGENOME — genome-backed Siona + era dictionary (srmech {srmech.__version__}) ===\n")
    d = tempfile.mkdtemp(prefix="siona_foundation_")
    build_foundation(d)
    w = GenomeWorld(d)

    print("STEP 1 — foundational language genome on disk:", sorted(os.listdir(d)))
    print("\nSTEP 2 — Siona INTROSPECTS the genome (self-knowledge, no hardcoded shelf):")
    for lab, n in w.introspect():
        print(f"    chromosome {lab:16} ({n} genes)")
    print(f"    eras Siona holds: {w.eras_available()}")

    print("\n(a) ERA-CORRECT definitions — same word, bound to its NOW:")
    for era in ("dict-en-2026", "dict-en-1600"):
        w.load_era(era)
        print(f"    [{era}] " + " | ".join(w.define(x) for x in ("nice", "awful", "computer")))

    print("\n(b) SELF-REALISATION by context cue (load/unload the right era):")
    for passage in ["translate this 1600s text: 'a nice and awful sight'",
                    "modern usage: that was a nice, awful movie"]:
        era = w.self_select_era(passage); w.load_era(era)
        print(f"    prompt={passage!r}\n      -> self-selected {era}; 'awful' = {w.define('awful')}")
        w.unload()

    print("\n(c) ASKING-STATE on a gap (load an era, ask for a word not in it):")
    w.load_era("dict-en-2026")
    print("    ", w.define("blockchain"))

    print("\nVERDICT: STEP 1+2 DONE on rc149 — Siona's knowledge is now GENOME-BACKED (introspect via genome_catalog,")
    print("  load/unload era-dictionary chromosomes by context, render era-correct, ask on a gap). The dictionary")
    print("  kernel is bound to a NOW via the chromosome label + MPR retrieved_at. Honest scope: definition TEXT is")
    print("  MPR-attested payload (NDJSON, the AMSC content layer); full autonomous era-detection generalises with")
    print("  more reference material — we built the ABILITY, anyone can bring real period dictionaries. (F737-build)")


if __name__ == "__main__":
    main()
