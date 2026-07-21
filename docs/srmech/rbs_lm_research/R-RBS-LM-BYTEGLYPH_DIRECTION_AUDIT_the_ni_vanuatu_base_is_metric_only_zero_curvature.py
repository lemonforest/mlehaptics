r"""R-RBS-LM-BYTEGLYPH_DIRECTION_AUDIT (F1211, root-first audit per user "audit the ni-Vanuatu / sandroing core") —
does the ni-Vanuatu byte-glyph BASE (the abstract translation layer every language kernel builds FROM, F761) carry
DIRECTION, or only undirected adjacency?

The current `_word_hv` (R-RBS-LM-SIONAGENEPOOL) = klein4_bundle of adjacent-glyph BIGRAM binds. This audit measures the
two channels separately (the F1209/F1210 metric-vs-curvature split, at the glyph level):
  • METRIC (undirected adjacency) = ANAGRAM distinguishability (F1013's test; changes which glyphs neighbor which).
  • CURVATURE (direction/order)    = WORD vs its REVERSE (same adjacency multiset, opposite direction).

Result (the root finding): klein4_bind is ABELIAN (commutative), so word == reverse EXACTLY (sim 1.000) — the base has
the SAME bag-at-the-curvature-channel as the wiki kernel. F1013 certified "order-carrying" because it only tested the
METRIC channel (anagrams). The naive position-role fix ALSO collapses under the (order-blind) klein4 similarity, and
there is no klein4-native order primitive (`permute` is a raw bit-rotation on bytes, not a sector permute) — so DIRECTION
needs the NON-ABELIAN channel (the_one winding / cd_mult; the sandroing directed walk), not the abelian Klein-4 bind.

srmech 0.9.0rc238; klein4 HDC. Run: /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-BYTEGLYPH_DIRECTION_AUDIT_...py
"""
from srmech.amsc import hdc

DIM = 8192
GLYPHS = "abcdefghijklmnopqrstuvwxyz'- "


def _seed(t):
    return int.from_bytes(t.encode()[:8].ljust(8, b"\x00"), "big") % (2 ** 31)


def _glyph(ch):
    return hdc.klein4_expand(DIM, _seed("niv/" + ch))


def _pos(i):
    return hdc.klein4_expand(DIM, _seed("niv/pos/%d" % i))


def _word(w, mode="bigram"):
    """mode='bigram' = the CURRENT _word_hv (adjacent-glyph bind bundle). mode='pos' = the UNUSED order-preserving
    position-role variant (`_posrole`, line 78 of the genepool — defined but never called by _word_hv)."""
    ch = [c for c in w.lower() if c in GLYPHS]
    if len(ch) < 2:
        return _glyph(ch[0])
    if mode == "bigram":
        parts = [hdc.klein4_bind(_glyph(ch[i]), _glyph(ch[i + 1])) for i in range(len(ch) - 1)][:32]
    else:
        parts = [hdc.klein4_bind(_pos(i), _glyph(ch[i])) for i in range(len(ch))][:32]
    return hdc.klein4_bundle(*parts)


def main():
    sim = hdc.klein4_similarity
    print("=== ni-Vanuatu byte-glyph BASE — direction (curvature) audit ===\n")
    a, b = _glyph("a"), _glyph("b")
    comm = sim(hdc.klein4_bind(a, b), hdc.klein4_bind(b, a))
    print("(1) klein4_bind ABELIAN? sim(bind(a,b), bind(b,a)) = %.3f  -> %s"
          % (comm, "COMMUTATIVE (abelian; direction within a bind is LOST)" if comm > 0.99 else "non-commutative"))

    print("\n(2) CURVATURE channel — WORD vs REVERSE (same adjacency, opposite direction):")
    print("    %-16s %-18s %-18s" % ("word/reverse", "bigram (current)", "posrole (unused)"))
    for w in ("abc", "cat", "listen", "stressed", "draw"):
        r = w[::-1]
        print("    %-16s %-18.3f %-18.3f" % (w + "/" + r, sim(_word(w), _word(r)), sim(_word(w, "pos"), _word(r, "pos"))))
    print("    -> sim 1.000 == BAG at the direction channel: the base cannot tell a word from its reverse.")

    print("\n(3) METRIC channel — ANAGRAMS (what F1013 tested; changes adjacency):")
    for x, y in (("cat", "act"), ("listen", "silent"), ("stop", "pots")):
        print("    sim(%s, %s) = %.3f" % (x, y, sim(_word(x), _word(y))))
    print("    -> < 1.0 == the metric (undirected adjacency) IS carried; anagrams are distinguishable.")

    print("\nVERDICT: the ni-Vanuatu base carries the METRIC (adjacency) but has ZERO CURVATURE (direction) — the same\n"
          "metric-vs-curvature split as the wiki kernel (F1210), at the ROOT. Cause: klein4_bind is ABELIAN. F1013\n"
          "certified 'order-carrying' from the METRIC channel only. Direction needs the NON-ABELIAN channel\n"
          "(the_one winding / cd_mult / the sandroing directed glyph-walk), not the Klein-4 bind.")


if __name__ == "__main__":
    main()
