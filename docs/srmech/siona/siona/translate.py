"""siona.translate — translation as ``b = B(A⁻¹(A(a)))`` (F1118), runnable on attested parallel text.

The F1118 formalism made executable: a knowledge ``a`` is the OPERAND (invariant); languages ``A``/``B`` are
OPERATORS (renderings). Given a source unit in language ``A``, translation is two ops in order:

    (1) COMPREHEND  A⁻¹ : source unit  → the knowledge invariant ``a``   (an order-carrying Klein-4 shape —
                                          the "sounds and looks like" structural signature, F1100)
    (2) RENDER      B   : ``a``         → the nearest unit in language ``B``'s corpus → the surface ``b``

``render`` here is RETRIEVAL from a parallel corpus — honest for a fixed bitext (the target rendering already
exists; we find it). Render-as-GENERATION (emit novel target text) is the #246 Gilgamesh next step.

HONEST on the bridge: for a COGNATE pair (a shared-lexifier language like Bislama↔English) the invariant ``a``
is carried largely by byte/glyph SPELLING overlap (``edukesen``~``education``), so alignment succeeds with ZERO
dictionary (F1015). For a NON-COGNATE pair (Egyptian / Sumerian ↔ English) spelling does not bridge — the
invariant ``a`` must carry KNOWLEDGE, which needs a shared concept-anchor. That gap IS the #246 challenge.

numpy-free; order-carrying Klein-4 (NEVER a bag — order is content, per discipline); no abs; no Counter.
"""
import re

from srmech.amsc import hdc
from srmech.rbs_lm import substrate as _S

__all__ = ["comprehend", "render", "translate", "docf_gate", "mnn_invariant", "D"]

D = 8192
_cs = _S.ContextSubstrate(D=D, hex_chars=16)


def _toks(s):
    # keep Latin + Greek/Coptic + CJK ranges so non-Latin lineages tokenise too (F1015 charset)
    return [w for w in re.split(r"[^0-9a-zÀ-˿Ͱ-῿Ⲁ-⳿一-鿿]+", (s or "").lower()) if len(w) > 1]


def _sim(a, b):
    q = hdc.klein4_similarity(a, b)
    return q.as_float() if hasattr(q, "as_float") else float(q)


def docf_gate(units, frac=0.6):
    """The MEASURED function-word gate (F768, language-agnostic): a token that appears in ≥ ``frac`` of the
    corpus units is function-like and dropped. Per-corpus, so it needs no per-language stoplist."""
    docf = {}
    for u in units:
        for w in set(_toks(u)):
            docf[w] = docf.get(w, 0) + 1
    cut = int(len(units) * frac)
    return lambda w: docf.get(w, 0) < cut


def comprehend(text, *, gate=None):
    """``A⁻¹``: read a source unit DOWN to the knowledge invariant ``a`` — an ORDER-CARRYING Klein-4 encoding
    (unigrams + adjacent-bigram binds), optionally function-word-gated. This is the "sounds and looks like"
    structural shape (F1100), the tower's invariant."""
    ws = [w for w in _toks(text) if (gate is None or gate(w))]
    parts = [_cs.enc(w) for w in ws]
    parts += [hdc.klein4_bind(_cs.enc(x), _cs.enc(y)) for x, y in zip(ws, ws[1:])]   # order = content
    return _cs.bundle_odd(parts or [_cs.enc("_")])


def render(a, target_units, *, gate=None, target_vecs=None):
    """``B``: RENDER the knowledge ``a`` by finding the nearest unit in the target corpus →
    ``(surface_b, index, confidence)``. ``target_vecs`` may be precomputed (comprehend of each target unit)."""
    if target_vecs is None:
        g = gate if gate is not None else docf_gate(target_units)
        target_vecs = [comprehend(u, gate=g) for u in target_units]
    ranked = sorted(((_sim(a, tv), i) for i, tv in enumerate(target_vecs)), reverse=True)
    conf, i = ranked[0]
    return target_units[i], i, conf


def translate(source_text, target_units, *, gate=None, src_gate=None):
    """``b = B(A⁻¹(A(a)))`` (F1118): COMPREHEND the source to the invariant ``a``, then RENDER by the nearest
    target unit. Returns ``(translation_b, index, confidence)``. Render = retrieval from the parallel corpus.

    ``gate`` gates the TARGET side; ``src_gate`` gates the SOURCE. Pass a PER-LANGUAGE ``src_gate`` for a
    cross-language pair (F1120): function-word-ness is per-language, so gating the source with the target's docf
    leaves the source's own function-words in and drops the signal to chance (measured: shared-English gate 3%
    top-1 vs per-side gate 10%). If ``src_gate`` is omitted it falls back to the target ``gate`` (correct only
    for a same-language / monolingual retrieval).

    CAVEAT (F1120): with the byte-glyph ``comprehend``, ``A⁻¹`` reaches only the BYTE substrate, so this
    transcode conserves byte-shared genes (cognates/loanwords) and CHANGES meaning-shared-but-spelling-divergent
    genes. For a NON-cognate pair (Gilgamesh, #246) byte-invariance is ~0 — a DEEPER knowledge ``A⁻¹`` is
    required. The GENOME-transcode direction (pack each side as per-gene genes, translate gene-by-gene, read via
    ``gene_express``) sidesteps the F871 bundle-saturation the article-level bundle hits."""
    g = gate if gate is not None else docf_gate(target_units)
    sg = src_gate if src_gate is not None else g         # PER-LANGUAGE source gate for a cross-language pair
    tvecs = [comprehend(u, gate=g) for u in target_units]
    a = comprehend(source_text, gate=sg)             # A⁻¹ : source → knowledge a (source-language gated)
    return render(a, target_units, target_vecs=tvecs)    # B  : a → nearest target surface b


def mnn_invariant(src, tgt, *, sim=None):
    """DETECT transcode-coherency-loss MUTATIONS via mutual-nearest-neighbour round-trip (F1121): a source item
    is INVARIANT iff it round-trips — its best target is the target whose best source is it (A→B→A returns) —
    else it is a MUTATION (coherency-loss at this ``A⁻¹`` depth). Returns a bool list over ``src`` (``True`` =
    invariant / round-trips).

    ``sim(a, b)`` is the similarity between items; default is the byte-glyph Klein-4 vector sim (``src``/``tgt``
    are vectors). Pass a WORD-based ``sim`` — e.g. ``siona.relate.related`` (the sparse CO-OCCURRENCE deeper-`A⁻¹`,
    F1126) — with ``src``/``tgt`` as WORDS to run the detector over the RELATIONSHIP layer instead of bytes; this
    LOWERS the mutation rate (synonyms round-trip via relatedness, F1129) — the deeper `A⁻¹` recovering the
    coherency the shallow byte read lost.

    This is a GENUINE detector, not a hand-list: the round-trip is biology's proofreading move (check the
    complement) — the triality 2-of-3 EC (F826) lifted from the substrate to the COHERENCY. The MUTATION-RATE
    (fraction ``False``) measures transcode fidelity at this comprehend depth. The flagged mutation is UNREAD at
    this coherency (chirality-locked), not lost — read all the chiral coordinates (no information without value)."""
    s = sim if sim is not None else _sim
    if not src or not tgt:
        return [False] * len(src)
    ab = [max(range(len(tgt)), key=lambda j: s(src[i], tgt[j])) for i in range(len(src))]   # A → B
    ba = [max(range(len(src)), key=lambda i: s(tgt[j], src[i])) for j in range(len(tgt))]   # B → A
    return [ba[ab[i]] == i for i in range(len(src))]                                        # mutual? (round-trip)
