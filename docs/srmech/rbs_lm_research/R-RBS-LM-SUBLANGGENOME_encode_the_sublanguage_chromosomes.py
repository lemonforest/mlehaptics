r"""R-RBS-LM-SUBLANGGENOME (F1204/#231) — GENOME-ENCODE the sub-language FORM-CLASS vocabularies as CHROMOSOMES in one
language-layer genome, sibling to the `markup` chromosome (F764). Each sublanguage's form-classes are Klein-4 byte-glyph
encoded and bundled into ONE chromosome HV; the 7 chromosomes (markup + latex + convert + chem + ipa + score + cite) pack
into a native srmech genome() strand via siona.genome_store.pack_instrument (#249), byte-exact recallable.

This makes the sublanguages first-class GENOME objects (recall / gene_express / compose) instead of loose research
scripts — the depth of "the LaTeX etc. aren't genome-encoded yet" closed. The chromosome discriminates its own
vocabulary (a form-class of a sublanguage is nearer ITS chromosome than another's), so the genome IS the language-layer
determinative Siona reads to know which sublanguage a construct belongs to.

srmech 0.9.0rc209. Klein-4 HDC (Class-M) + native genome (Class-A/B). numpy-free; no Python abs builtin; no Counter; no
CAD. Persisted OUTSIDE the repo. Run (siona on the path):
  PYTHONPATH=docs/srmech/siona /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SUBLANGGENOME_...py
"""
import importlib.util
import sys
from pathlib import Path

from srmech.amsc import hdc
from siona import genome_store as GS

_D = "docs/srmech/rbs_lm_research/"
OUT = str(Path.home() / "corpora" / "wikipedia" / "sublanguage_genome")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


MK = _load("mk", _D + "R-RBS-LM-MARKUPGRAMMAR_class_bf_form_layer_understand_not_strip.py")
LX = _load("lx", _D + "R-RBS-LM-LATEXKERNEL_math_notation_sublanguage_comprehend_not_strip.py")
CH = _load("ch", _D + "R-RBS-LM-CHEMKERNEL_ce_reaction_notation_sublanguage_reaction_graph.py")
CV = _load("cv", _D + "R-RBS-LM-CONVERTKERNEL_quantity_unit_sublanguage_the_mass_count_determinative.py")
CI = _load("ci", _D + "R-RBS-LM-CITEKERNEL_citation_sublanguage_attestable_source_graph.py")

# IPA + score form-classes (the kernels use them implicitly; named here as the chromosome's gene labels).
IPA_FORM_CLASSES = ("ipa_vowel", "ipa_consonant", "ipa_primary_stress", "ipa_secondary_stress", "ipa_length",
                    "ipa_syllable_break", "ipa_diacritic", "ipa_tone")
SCORE_FORM_CLASSES = ("score_note", "score_pitch_class", "score_duration", "score_rest", "score_clef",
                      "score_key_signature", "score_time_signature", "score_melodic_interval", "score_chord", "score_bar")

# the 7 language-layer chromosomes: (name, form-class vocabulary).
CHROMOSOMES = [
    ("markup", MK.MARKUP_FORM_CLASSES),
    ("latex", LX.MATH_FORM_CLASSES),
    ("convert", CV.DIMENSIONS),
    ("chem", CH.CHEM_FORM_CLASSES),
    ("ipa", IPA_FORM_CLASSES),
    ("score", SCORE_FORM_CLASSES),
    ("cite", CI.CITE_FORM_CLASSES),
]


def _chromosome_hv(form_classes, dim=8192):
    """One sublanguage chromosome = the Klein-4 bundle of its form-class byte-glyph encodings (Class-M)."""
    return hdc.klein4_bundle(*[hdc.klein4_encode_bytes(fc.encode("utf-8"), dim) for fc in form_classes])


def main():
    print("=== SUBLANGGENOME — genome-encode the 7 sub-language chromosomes (srmech %s) ===\n" % __import__("srmech").__version__)
    named = [(name, _chromosome_hv(fcs)) for name, fcs in CHROMOSOMES]
    for (name, fcs), (_n, hv) in zip(CHROMOSOMES, named):
        print("  chromosome %-8s : %2d form-classes -> HV[%d]" % (name, len(fcs), len(hv)))
    manifest = GS.pack_instrument(named, OUT)
    print("\n  packed -> %s  (%d chromosomes, native genome strand)" % (OUT, len(named)))

    # VERIFY 1 — byte-exact recall of every chromosome
    recalled = GS.load_instrument(OUT)
    ok = all(list(recalled[name]) == [int(x) for x in hv] for name, hv in named)
    print("  byte-exact recall of all chromosomes:", ok)

    # VERIFY 2 — the chromosome DISCRIMINATES its own vocabulary (a form-class is nearer ITS chromosome than another's)
    print("\n  discrimination (own form-class vs own chromosome > vs a foreign chromosome):")
    chrom_hv = dict(named)
    probes = [("latex", "math_variable"), ("chem", "reaction_arrow"), ("cite", "journal"),
              ("convert", "temperature"), ("ipa", "ipa_vowel"), ("markup", "wiki_link")]
    hits = 0
    for owner, fc in probes:
        p = hdc.klein4_encode_bytes(fc.encode(), 8192)
        own = float(hdc.klein4_similarity(chrom_hv[owner], p))
        foreign = max(float(hdc.klein4_similarity(chrom_hv[o], p)) for o in chrom_hv if o != owner)
        good = own > foreign
        hits += good
        print("     %-8s '%s': own %.3f vs best-foreign %.3f  %s" % (owner, fc, own, foreign, "OK" if good else "x"))
    print("\n  DISCRIMINATION: %d/%d form-classes route to their own chromosome (the language-layer determinative)" % (hits, len(probes)))


if __name__ == "__main__":
    main()
