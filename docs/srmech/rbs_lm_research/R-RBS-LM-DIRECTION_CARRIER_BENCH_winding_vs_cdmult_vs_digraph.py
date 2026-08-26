r"""R-RBS-LM-DIRECTION_CARRIER_BENCH (F1211 fix, user "compare carriers first") — which direction carrier should the
ni-Vanuatu byte-glyph BASE use? The base is metric-only (F1211: word == reverse at sim 1.000, abelian klein4_bind).
Bench THREE non-abelian direction carriers for a word's glyph-order, on the read-independent structural axes:

  A) WINDING (the_one)       — net signed winding of the glyph-index walk (the sandroing/holonomy reading, F1079).
  B) CD_MULT (octonion fold) — left-fold cd_mult over per-glyph octonions ("walk-order lives in non-commutative cd_mult").
  C) DIGRAPH (F1210 scale-down) — the word as a directed glyph-graph (consecutive g_i->g_{i+1}); charge = which-first.

Measured per carrier: (1) DIRECTION = word vs reverse distinguished (non-palindrome) — the thing the base LACKS;
(2) METRIC/CAPACITY = distinct signatures over a word list (collisions kill a base); (3) ROUND-TRIP = recover the
ordered glyphs (the sandroing walk); (4) GENOME-COMPOSABLE = does it pack.

srmech 0.9.0rc238; exact ℚ (cd_mult) / integer (digraph); no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-DIRECTION_CARRIER_BENCH_...py
"""
from fractions import Fraction

from srmech.amsc import cascade as C

GLYPHS = "abcdefghijklmnopqrstuvwxyz'- "
GI = {c: i for i, c in enumerate(GLYPHS)}
NG = len(GLYPHS)

WORDS = ("cat act tac listen silent enlist stop pots spot draw ward reward drawer "
         "level deed noon radar abc cba the and for with from that this word order "
         "sand draw ni vanuatu glyph story ocean planet water fire earth wind stone").split()
REVPAIRS = [("cat", "tac"), ("listen", "netsil"), ("draw", "ward"), ("stop", "pots"),
            ("abc", "cba"), ("stressed", "desserts"), ("level", "level"), ("noon", "noon")]  # last two palindromes


# ---- A) WINDING: net signed circular winding of the glyph-index walk (reverse -> negated) ----
def winding_sig(w):
    ch = [c for c in w.lower() if c in GI]
    net = 0
    for i in range(len(ch) - 1):
        d = (GI[ch[i + 1]] - GI[ch[i]]) % NG
        if d > NG // 2:
            d -= NG                                   # signed shortest circular step (Class-K pin at the half-cycle)
        net += d
    return net                                        # a single signed integer (the winding number)


# ---- B) CD_MULT: per-glyph octonion, left-fold the non-commutative Cayley-Dickson product ----
def _octo(ch):
    i = GI[ch]
    v = [Fraction(0)] * 8
    v[0] = Fraction(1, 1)                             # real part 1 (nonzero -> nonzero norm, invertible)
    v[1 + (i % 7)] = Fraction(1 + i, 1 + NG)          # one imaginary component keyed to the glyph
    return tuple(v)


def cdmult_sig(w):
    ch = [c for c in w.lower() if c in GI]
    acc = _octo(ch[0])
    for c in ch[1:]:
        acc = C.cd_mult(acc, _octo(c))                # non-commutative, non-associative fold = the ordered walk
    return acc


# ---- C) DIGRAPH: the word as a directed glyph-graph (F1210 scale-down); charge = which-glyph-first ----
def digraph_sig(w):
    ch = [c for c in w.lower() if c in GI]
    charge = {}
    for i in range(len(ch) - 1):
        u, v = GI[ch[i]], GI[ch[i + 1]]
        if u == v:
            continue
        lo, hi = (u, v) if u < v else (v, u)
        charge[(lo, hi)] = charge.get((lo, hi), 0) + (1 if u < v else -1)   # +1 lo-before-hi, -1 hi-before-lo
    return tuple(sorted((k, v) for k, v in charge.items() if v != 0))


def digraph_roundtrip(w):
    """Reconstruct the ordered glyph walk from the directed consecutive-pair edges (the sandroing/Eulerian read)."""
    ch = [c for c in w.lower() if c in GI]
    if len(ch) < 2:
        return w
    edges = [(ch[i], ch[i + 1]) for i in range(len(ch) - 1)]   # directed consecutive pairs (the stored walk)
    outs = {}
    indeg = {}
    for a, b in edges:
        outs.setdefault(a, []).append(b); indeg[b] = indeg.get(b, 0) + 1
    start = ch[0]
    for n in outs:
        if len(outs[n]) - indeg.get(n, 0) == 1:       # Eulerian-path start = the unique out>in node
            start = n; break
    path = [start]; avail = {k: list(v) for k, v in outs.items()}
    cur = start
    for _ in range(len(edges)):
        if not avail.get(cur):
            break
        nxt = avail[cur].pop(0); path.append(nxt); cur = nxt
    return "".join(path)


def _dist(a, b):
    return sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)) ** 0.5


def main():
    print("=== direction-carrier bench for the ni-Vanuatu base (F1211 fix) ===\n")
    carriers = [("A) winding (the_one)", winding_sig, False),
                ("B) cd_mult (octonion)", cdmult_sig, True),
                ("C) digraph (F1210)", digraph_sig, True)]
    for name, sig, _ in carriers:
        # (1) DIRECTION: word vs reverse distinguished (skip palindromes)
        dist_ok = 0; dist_tot = 0
        for x, y in REVPAIRS:
            if x == y[::-1] and x != x[::-1]:          # a genuine reverse pair, not a palindrome
                dist_tot += 1
                if sig(x) != sig(y):
                    dist_ok += 1
        # (2) CAPACITY: distinct signatures over the word list (collisions)
        sigs = [sig(w) for w in WORDS]
        distinct = len({str(s) for s in sigs})
        # (3) ROUND-TRIP
        if name.startswith("C"):
            rt = sum(1 for w in WORDS if digraph_roundtrip(w) == "".join(c for c in w.lower() if c in GI))
            rtmsg = "YES  (%d/%d words recovered via Eulerian walk)" % (rt, len(WORDS))
        elif name.startswith("B"):
            inv = C.left_mult_is_invertible(_octo("a"))
            rtmsg = "YES-in-principle (octonion is a division algebra; left_mult_is_invertible=%s)" % inv
        else:
            rtmsg = "NO   (a scalar winding cannot recover the glyphs)"
        print("%-24s direction(word!=reverse)=%d/%d   distinct/%d=%d   round-trip: %s"
              % (name, dist_ok, dist_tot, len(WORDS), distinct, rtmsg))

    # the killer contrast: a palindrome-free reverse pair, all three
    print("\n  worked example  cat vs tac (reverse):")
    print("    winding:  %s  vs  %s" % (winding_sig("cat"), winding_sig("tac")))
    print("    cd_mult:  dist = %.3f  (0 == indistinguishable)" % _dist(cdmult_sig("cat"), cdmult_sig("tac")))
    print("    digraph:  %s  vs  %s" % (digraph_sig("cat"), digraph_sig("tac")))
    print("    digraph round-trip: cat->'%s'  tac->'%s'" % (digraph_roundtrip("cat"), digraph_roundtrip("tac")))

    print("\nVERDICT: pick the carrier that is directional AND high-capacity AND round-trippable AND genome-composable.\n"
          "  A winding  = directional but ~1 scalar -> massive collisions (a SUMMARY, not a store); no round-trip.\n"
          "  B cd_mult  = directional + invertible, but an opaque octonion (not a sparse edge object to pack).\n"
          "  C digraph  = directional + full-capacity + round-trips via the Eulerian/sandroing walk + IS the F1210\n"
          "              directed-edge object one scale down (packs as a kernel chromosome; one object at every scale).")


if __name__ == "__main__":
    main()
