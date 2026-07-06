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

__all__ = ["comprehend", "render", "translate", "docf_gate", "D"]

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


def translate(source_text, target_units, *, gate=None):
    """``b = B(A⁻¹(A(a)))`` (F1118): COMPREHEND the source to the invariant ``a``, then RENDER by the nearest
    target unit. Returns ``(translation_b, index, confidence)``. Render = retrieval from the parallel corpus
    (honest for a fixed bitext); the gate is shared across both sides so the same function-words drop."""
    g = gate if gate is not None else docf_gate(target_units)
    tvecs = [comprehend(u, gate=g) for u in target_units]
    a = comprehend(source_text, gate=g)              # A⁻¹ : source → knowledge a
    return render(a, target_units, target_vecs=tvecs)    # B  : a → nearest target surface b
