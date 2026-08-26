"""R-RBS-LM recursive-compose arc (F963, opened from F962) — the SCALE-INVARIANT n-gram recall.

ONE operation, `compose`, is the n-gram at every scale (F962): the position-keyed role-filler bind+bundle.
Applied recursively it lifts glyph -> word -> phrase -> sentence; and ONE `recall_level` reads the next
unit at ANY scale. The byte->word leaf is srmech's own `encode_word_byteglyph` (`ContextSubstrate.enc`),
itself "the scale-invariant role-filler bundle over the word's UTF-8 bytes" (its docstring).

DISCIPLINE: sparse Klein-4 HDC only (klein4_bind / bundle_odd / klein4_similarity, integer match-counts,
the role-filler bundle); NO dense matrix, NO numpy, NO abs/Counter. The dynamic n-gram WIDTH (F961) is the
`k` knob; the UNIT STREAM (words / phrases / ASL-gloss, F958/F959) is what you feed it; the SCALE is the
recursion depth. The "three items" (F959) are knob settings on this one op, not separate machinery.
"""
from srmech.rbs_lm import substrate as S
from srmech.amsc import hdc

def fl(q):
    return q.as_float() if hasattr(q, "as_float") else float(q)


def compose(cs, unit_hvs):
    """THE scale-invariant n-gram: position-keyed role-filler bind + bundle of a unit sequence.

    `cs` = a ContextSubstrate (for `pos_key` + `bundle_odd`). A 1-unit group is the unit itself
    (the identity of the n-gram). Same op for bytes->word, words->phrase, phrases->sentence."""
    if len(unit_hvs) == 1:
        return unit_hvs[0]
    return cs.bundle_odd([hdc.klein4_bind(cs.pos_key(p), u) for p, u in enumerate(unit_hvs)])


def lift(cs, units, k):
    """Chunk a `(hv, label)` unit stream into non-overlapping k-groups; compose each -> next-level units.

    The dynamic width `k` (F961) is the only parameter that changes between scales. Returns `(hv, label)`
    so every level stays a labelled unit stream (recursable)."""
    out = []
    for i in range(0, len(units) - k + 1, k):
        grp = units[i:i + k]
        hv = compose(cs, [h for h, _ in grp])
        lab = " ".join(l for _, l in grp)
        out.append((hv, lab))
    return out


def words_of(cs, text):
    """Leaf level: text -> labelled WORD units via srmech's byte/glyph word encoder (byte->word n-gram)."""
    return [(cs.enc(w), w) for w in text.split()]


def recall_level(cs, units, k_ctx=2):
    """Scale-invariant recall: learn a sparse (k_ctx-context -> next) memory over a unit stream, return a
    `recall(context_units)` that cleans up to the next unit's label. SAME code at word/phrase/sentence scale.

    Sparse: M is a single Klein-4 bundle (the role-filler memory); cleanup is integer match-count similarity
    over the DISTINCT units only (no dense matrix). Returns (recall_fn, n_distinct)."""
    hvs = [h for h, _ in units]
    seen = {}
    for h, l in units:
        seen.setdefault(l, h)
    dlabs = list(seen.keys())
    dhvs = [seen[l] for l in dlabs]
    pairs = [hdc.klein4_bind(compose(cs, hvs[i:i + k_ctx]), hvs[i + k_ctx])
             for i in range(len(hvs) - k_ctx)]
    M = cs.bundle_odd(pairs) if pairs else None

    def recall(ctx_units):
        if M is None:
            return None
        probe = hdc.klein4_bind(M, compose(cs, [h for h, _ in ctx_units]))
        j = max(range(len(dhvs)), key=lambda j: fl(hdc.klein4_similarity(probe, dhvs[j])))
        return dlabs[j]

    return recall, len(dlabs)


def _demo():
    cs = S.ContextSubstrate(D=8192, hex_chars=16)
    text = ("april is the fourth month of the year april has thirty days "
            "april comes after march april comes before may")
    words = words_of(cs, text)
    print("recursive-compose arc demo (sparse Klein-4; one compose, every scale)")
    print("  text words:", len(words), "| distinct:", len(set(w for _, w in words)))

    # WORD scale: same recall_level, k_ctx=2 (F961 wider = sharper)
    rec_w, nw = recall_level(cs, words, k_ctx=2)
    ctx = [words[0], words[1]]                       # ['april','is']
    print("  WORD  scale (k_ctx=2): ctx ['april','is'] -> next =", rec_w(ctx), "(%d distinct word-units)" % nw)

    # PHRASE scale: lift words -> 3-word phrases, SAME recall_level
    phrases = lift(cs, words, k=3)
    rec_p, npg = recall_level(cs, phrases, k_ctx=1)
    print("  phrases:", [l for _, l in phrases][:4], "...")
    pctx = [phrases[0]]                              # ['april is the']
    print("  PHRASE scale (k_ctx=1): ctx [%r] -> next phrase = %r (%d distinct phrase-units)"
          % (phrases[0][1], rec_p(pctx), npg))
    print("  => one compose() + one recall_level() at two scales (scale-invariant); phrase units are content-dense")


if __name__ == "__main__":
    _demo()
