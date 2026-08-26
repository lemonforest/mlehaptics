"""Bag-of-words regression fixtures (PKG-1 audit standard) + the operator-board swap test.

The three caught bag incidents are pinned here so they can never silently return:
  F1004 — byte/glyph must be ORDER-aware (anagrams distinct, never bag-equal);
  F1008 — bag-of-tokens grounding crossed domains ('klein-4' retrieved klein_gordon);
  F1010 — commutative pair-binding aliased (lives,in)->the into (in,the)->lives.
Plus the swap test: the router + FULL session (incl. the exact-rational kernel answer) run
unchanged under a synthetic-language board — English is a profile, not core.
"""
import os
import siona


def _sim(g, a, b):
    return g.sim(a, b)


def test_f1004_byteglyph_order_aware():
    g = siona.Grounding()
    for a, b in (("cat", "act"), ("no", "on"), ("dog", "god"), ("was", "saw")):
        s = _sim(g, g.cs.enc(a), g.cs.enc(b))
        assert s < 0.95, "anagrams bag-equal: %s/%s sim=%.3f" % (a, b, s)


def test_f1008_no_cross_domain_bag_collision():
    g = siona.Grounding()
    for q, family in (("similarity between two klein-4 vectors", "klein4"),
                      ("bundle these klein-4 hypervectors by majority", "klein4"),
                      ("generate a random klein-4 hypervector", "klein4")):
        top = g.ground(q, 3, owner="srmech")
        names = [n.split(".")[-1] for _, n in top]
        assert names[0].startswith(family), "%r -> %s (crossed out of %s)" % (q, names, family)
        assert not names[0].startswith("klein_gordon"), "the F1008 physics collision returned"


def test_f1008_within_family_rerank():
    g = siona.Grounding()
    # exact name-token coverage promotes the right family member (the F1008 open lever, closed)
    assert g.ground("bundle these klein-4 hypervectors by majority", 1,
                    owner="srmech")[0][1].split(".")[-1] == "klein4_bundle"
    assert g.ground("similarity between two klein-4 vectors", 1,
                    owner="srmech")[0][1].split(".")[-1] == "klein4_similarity"


def test_f1010_no_context_aliasing():
    s = siona.Session()
    s.turn("siona remember that the pope lives in the vatican")
    _, _, out = s.turn("the pope lives in the")
    assert out.strip() == "vatican", "F1010 aliasing returned: got %r" % out


def test_board_swap_full_session():
    fix = os.path.join(os.path.dirname(__file__), "fixtures", "testlang_board.toml")
    b = siona.load_board(fix)
    s = siona.Session(board=b)
    # routing parity under the swapped profile
    assert s.route("ada memoru da wota boila long 100 selsius") == "self-command"
    assert s.route("komputa da gcd blong 48 mo 36") == "tool-call"
    assert s.route("kesa lo laplasian") == "define"
    assert s.route("wota boila long") == "continue"
    # the FULL kernel composition, zero English operators:
    _, _, o1 = s.turn("ada memoru da wota boila long 100 selsius")
    assert "noted" in o1
    _, _, o2 = s.turn("ada injesu da kernelu farenhait esa selsius taimsa 9 ova 5 plusa 32")
    assert "noted" in o2
    _, _, o3 = s.turn("ada wota boila long kesa farenhait")
    assert "212" in str(o3), "kernel answer under swapped board failed: %r" % o3
    # and a real srmech drive routed by the swapped imperative
    _, _, o4 = s.turn("komputa da gcd blong 48 mo 36")
    assert "gcd(48, 36) = 12" in o4 or "gcd(36, 48)" in o4
