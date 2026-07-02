"""Smoke: the F1012 10-turn session driven through the PACKAGED siona.infer.Session.
Covers: self-surface registration, routing, grounding, drive (real srmech ops), cross-turn
operand resolution, kernel-composed exact-rational answer, continuation, live Class-H help."""
import siona


def test_session_smoke():
    s = siona.Session()
    turns = [
        ("siona remember that water boils at 100 celsius", lambda o: "noted" in o),
        ("siona ingest the kernel fahrenheit is celsius times 9 over 5 plus 32", lambda o: "noted" in o),
        ("compute the gcd of the boiling point of water and 48", lambda o: "gcd(100, 48) = 4" in o),
        ("siona water boils at what fahrenheit", lambda o: "212" in o),
        ("factor 360 into primes", lambda o: "(2, 3), (3, 2), (5, 1)" in o),
        ("water boils at", lambda o: o.strip() == "100"),
        ("siona what can you do", lambda o: "answer" in o),
        ("siona show your working memory", lambda o: "water boils" in o),
    ]
    for u, check in turns:
        _, _, out = s.turn(u)
        assert check(str(out)), "turn failed: %r -> %r" % (u, out)


def test_boards_swap_shape():
    b = siona.ENGLISH
    assert b.name == "english" and b.address == "siona"
    # the board is a profile: frozen, swappable, disjoint operator classes
    assert b.self_verbs.isdisjoint(b.imperatives)
    assert not set(w for f in b.define_frames for w in f) & b.self_verbs
