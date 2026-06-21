"""rc18 — F917 Part B: the L1/L2/L3 ladder rebuilt on klein4_compose, + the
klein4_compose native C peer (srmech_klein4_compose).

  1. The ladder is now ONE scale-invariant compositor end to end — a one-word
     change degrades GRACEFULLY (similarity-preserving), where the old chained
     ``klein4_bind`` fold collapsed to ~chance.
  2. ``hdc.klein4_compose`` matches the explicit role-filler composition byte-
     for-byte for every n (native single-call == the multi-call composition, and
     the pure path when no native).

numpy-free; deterministic (seeded ``klein4_random``).
"""

from srmech.amsc import hdc
from srmech.rbs_lm import substrate as cs

D = 96
HEX = 8


def _sim(a, b):
    return float(hdc.klein4_similarity(a, b))


# ----------------------------------------------- klein4_compose native parity

def _manual_compose(parts):
    """The explicit role-filler composition the op is the native peer of."""
    n = len(parts)
    Dn = len(parts[0])
    bound = [hdc.klein4_bind(p, hdc._klein4_pos_key(Dn, i))
             for i, p in enumerate(parts)]
    if n == 1:
        return bound[0]
    return hdc.klein4_bundle(*bound)


def test_klein4_compose_matches_manual_role_filler():
    """klein4_compose (native single-call when present, else pure) == the
    explicit klein4_bind/klein4_bundle composition, for every n incl. 1
    (identity rung) + even (ties→0) + odd."""
    for n in (1, 2, 3, 5, 8):
        parts = [hdc.klein4_random(80, seed=100 + i) for i in range(n)]
        got = list(hdc.klein4_compose(parts))
        exp = list(_manual_compose(parts))
        assert got == exp, (n, got[:6], exp[:6])


def test_klein4_compose_single_is_position_bound():
    one = hdc.klein4_random(D, seed=42)
    out = hdc.klein4_compose([one])
    assert list(out) == list(hdc.klein4_bind(one, hdc._klein4_pos_key(D, 0)))


# ----------------------------------------------- ladder is scale-invariant now

def test_sentence_ladder_is_similarity_preserving_vs_chained_fold():
    """L3 sentence (now klein4_compose) keeps a one-word change GRACEFULLY —
    the F917 Part B fix. The old chained ``klein4_bind`` fold of the same words
    collapses a one-word change toward chance; the compose does not, and the
    change stays closer than a disjoint sentence."""
    base = ["the", "cat", "sat", "on", "mat"]
    one_changed = ["the", "cat", "ran", "on", "mat"]
    disjoint = ["dog", "fox", "owl", "elk", "ant"]

    def chained(tokens, enc_mode):
        enc = ((lambda t: cs.encode_word_byteglyph(t, D=D, sector=0))
               if enc_mode == "byteglyph"
               else (lambda t: cs.encode_word_k4(t, D=D, sector=0, hex_chars=HEX)))
        acc = enc(tokens[0])
        for t in tokens[1:]:
            acc = hdc.klein4_bind(acc, enc(t))
        return acc

    # compose: a one-word change degrades gracefully + stays closer than disjoint
    s0 = cs.encode_sentence_l3(base, D=D, hex_chars=HEX)
    s1 = cs.encode_sentence_l3(one_changed, D=D, hex_chars=HEX)
    sx = cs.encode_sentence_l3(disjoint, D=D, hex_chars=HEX)
    sim_change = _sim(s0, s1)
    assert sim_change > 0.6, sim_change                       # graceful
    assert sim_change > _sim(s0, sx) + 0.10                   # closer than disjoint
    # ... and retains far MORE than the chained fold over the same words
    assert sim_change > _sim(chained(base, "byteglyph"),
                             chained(one_changed, "byteglyph")) + 0.20

    # the cleanest contrast — with ORTHOGONAL (word-hash) atoms the chained fold
    # collapses a one-word change to ~chance (0.25) while the compose stays high.
    c0 = cs.encode_sentence_l3(base, D=D, hex_chars=HEX, enc_mode="wordhash")
    c1 = cs.encode_sentence_l3(one_changed, D=D, hex_chars=HEX, enc_mode="wordhash")
    assert _sim(c0, c1) > 0.5                                 # compose: graceful
    assert _sim(chained(base, "wordhash"),
               chained(one_changed, "wordhash")) < 0.32       # chained: ~chance


def test_bigram_and_skeleton_share_structure():
    """L1/L2 are the same compositor; bigrams sharing a word stay closer than
    disjoint bigrams."""
    b_tc = cs.encode_bigram_l1("the", "cat", D=D, hex_chars=HEX)
    b_tr = cs.encode_bigram_l1("the", "rat", D=D, hex_chars=HEX)   # shares "the"
    b_xy = cs.encode_bigram_l1("dog", "owl", D=D, hex_chars=HEX)   # disjoint
    assert _sim(b_tc, b_tr) > _sim(b_tc, b_xy)
    sk = cs.encode_skeleton_l2(("the", "cat"), ("on", "mat"), D=D, hex_chars=HEX)
    assert len(sk) == D and sk.sectors == 4


# ----------------------------------------------- enc_mode flag on the ladder

def test_ladder_enc_mode_default_byteglyph_and_wordhash_pins():
    bg = cs.encode_bigram_l1("cat", "sat", D=D, hex_chars=HEX)            # default
    wh = cs.encode_bigram_l1("cat", "sat", D=D, hex_chars=HEX, enc_mode="wordhash")
    assert list(bg) != list(wh)                          # real numerics change
    # determinism in both modes
    assert list(bg) == list(cs.encode_bigram_l1("cat", "sat", D=D, hex_chars=HEX))
    assert list(wh) == list(
        cs.encode_bigram_l1("cat", "sat", D=D, hex_chars=HEX, enc_mode="wordhash"))
    # byteglyph atoms carry morphology into the bigram; wordhash does not
    bg_cot = cs.encode_bigram_l1("cot", "sat", D=D, hex_chars=HEX)
    wh_cot = cs.encode_bigram_l1("cot", "sat", D=D, hex_chars=HEX, enc_mode="wordhash")
    assert _sim(bg, bg_cot) > _sim(wh, wh_cot)
