r"""R-RBS-LM-U1ACCEPTANCE (F722) — srmech 0.7.5rc49 ships R3 U1 (tokenize + cooccurrence_edges), but it FAILS the
§40 acceptance bar on all three points; R3 U1 is NOT closeable yet.

User direction (2026-06-09): "srmech 0.7.5rc49 is ready on test.pypi.org" — run the §40 acceptance bar (the spec
we wrote when the dropped commit's signatures looked off).

CONTEXT. UPSTREAM_NOTES §40 specced tokenize/cooccurrence_edges from the wiki kernel's real requirements. rc49
shipped both in srmech.amsc.laplacian. This is the MPM verification: do the SHIPPED ops meet the bar? (Run with
the rc49 venv: /tmp/srmech_rc49/venv/bin/python3.)

RESULT — three acceptance failures (each disqualifying for a different real use):
  BAR 1 (Unicode, F698): tokenize is ASCII-only — it strips accents and DROPS non-Latin scripts entirely
    (café->caf, naïve->na+ve, Москва/日本語 -> gone). Disqualifies the R6 multilingual corpus (#846/#847): it
    cannot tokenize non-English at all.
  BAR 2 (no silent vocab cap, F708): cooccurrence_edges DEFAULTS to vocab_size=1000 -> a 1500-word stream is
    SILENTLY capped to 1000. This is the EXACT pre-encode quantization F708 removed, now baked in as the default.
    Overridable (vocab_size=1500 works) but there is NO 'all' sentinel (vocab_size=None raises).
  BAR 3 (document-boundary window-reset): the arg is a FLAT token stream with no boundary/docs param, so
    co-occurrence BLEEDS across article boundaries (the wiki kernel needs one-article-one-window-reset).

CORRECT FORMAT (the parts that ARE right): edges are 2-tuples + a parallel weights list, returned as
(n, edges, weights) straight into dense_laplacian; a `stopwords=` param exists. So for English / single-document /
small-vocab it works and retires Counter() — but it does not meet the bar for our full-vocab multilingual
multi-article kernel.

GENOME REGRESSION: confirm rc49 did not break the F716-F721 storage surface.
No abs(); srmech-first (these ARE the srmech ops under test). Acceptance-bar harness; R3 U1 stays OPEN.
"""
import inspect
import srmech
from srmech.amsc import laplacian as L
from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_random


def bar1_unicode():
    toks = L.tokenize("café Москва naïve 日本語 hello world")
    keeps = ("café" in toks) and ("naïve" in toks) and any("москва" in t for t in toks) and ("日本語" in toks)
    return keeps, toks


def bar2_vocab_cap():
    big = [f"w{i}" for i in range(1500)] * 2
    n_default = L.cooccurrence_edges(big, window=2)[0]
    no_cap_default = (n_default >= 1500)                       # PASS only if the default does NOT cap
    try:
        L.cooccurrence_edges(big, window=2, vocab_size=None)
        has_all_sentinel = True
    except Exception:
        has_all_sentinel = False
    return no_cap_default, n_default, has_all_sentinel


def bar3_boundary():
    sig = str(inspect.signature(L.cooccurrence_edges))
    has_boundary = ("boundaries" in sig) or ("docs" in sig) or ("reset" in sig)
    return has_boundary, sig


def genome_regression():
    one = klein4_random(64, seed=1)
    kernels = {"a": [klein4_random(64, seed=s) for s in (10, 11)], "b": [klein4_random(64, seed=20)]}
    strand = G.genome(kernels, one)
    back = G.partition(strand, one, list(kernels))
    return all([list(map(list, back[k])) == list(map(list, kernels[k])) for k in kernels])


def main():
    print(f"=== R-RBS-LM-U1ACCEPTANCE (F722) — rc49 tokenize/cooccurrence_edges vs the §40 bar  (srmech {srmech.__version__}) ===\n")
    assert srmech.__version__ == "0.7.5rc49"

    print("WHERE: tokenize + cooccurrence_edges shipped in srmech.amsc.laplacian (Option 3; §40 recommended amsc.text).\n")

    b1, toks = bar1_unicode()
    print(f"BAR 1 — Unicode-aware tokenize (F698):           {'PASS' if b1 else 'FAIL'}")
    print(f"   tokenize('café Москва naïve 日本語 hello world') -> {toks}")
    print(f"   (FAIL: accents stripped, Cyrillic + CJK dropped -> ASCII-only; cannot tokenize non-English)\n")

    b2, n_default, sentinel = bar2_vocab_cap()
    print(f"BAR 2 — no silent vocab cap (F708):              {'PASS' if b2 else 'FAIL'}")
    print(f"   1500 distinct words, DEFAULT call -> n={n_default}  (default vocab_size=1000 SILENTLY caps)")
    print(f"   'all' sentinel (vocab_size=None) available? {sentinel}  (FAIL: must pass an explicit size to avoid the cap)\n")

    b3, sig = bar3_boundary()
    print(f"BAR 3 — document-boundary window-reset:          {'PASS' if b3 else 'FAIL'}")
    print(f"   signature: cooccurrence_edges{sig}")
    print(f"   (FAIL: flat token stream, no boundary/docs param -> co-occurrence bleeds across article boundaries)\n")

    reg = genome_regression()
    print(f"GENOME REGRESSION (F716-F721 storage surface still works): {'PASS' if reg else 'FAIL'}\n")

    passed = sum([b1, b2, b3])
    print("VERDICT (F722):")
    print(f"  • R3 U1 SHIPPED in rc49 (srmech.amsc.laplacian) — format is correct (2-tuples + weights ->")
    print(f"    dense_laplacian; stopwords= exists) and it retires Counter() for English/single-doc/small-vocab.")
    print(f"  • But it FAILS the §40 acceptance bar {3-passed}/3: (1) ASCII-only tokenize (kills R6 multilingual),")
    print(f"    (2) default vocab_size=1000 silent cap (the F708 bug, re-introduced as a default), (3) no")
    print(f"    document-boundary window-reset (cross-article bleed). So R3 U1 is NOT closeable; the wiki kernel")
    print(f"    cannot adopt it unquantized/multilingual/per-article without the three fixes.")
    print(f"  • The required fixes (for UPSTREAM §40): (1) Unicode tokenize (unicodedata L/M categories, not \\w+);")
    print(f"    (2) default = no cap (vocab_size=None/0 -> all; a cap is an explicit, logged opt-in); (3) a")
    print(f"    boundaries=/docs= param so the window resets per document. GENOME surface unaffected (regression {reg}).")


if __name__ == "__main__":
    main()
