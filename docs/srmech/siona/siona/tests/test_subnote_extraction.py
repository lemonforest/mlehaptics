"""F1026: the F774 closed-op SUB-NOTE EXTRACTION rung -- the wh-frame declares the answer's
shape (number/ordinal + unit); extraction is an adjacency read over the best note, never
generation; misses fall to the cited whole-note recall. Memory-seeded (no corpus dependency
in the wheel -- mechanism, not knowledge)."""
import siona


def test_subnote_extraction():
    s = siona.Session()
    s.turn("siona remember april is the fourth month of the year and one of four months to have 30 days")

    intent, tag, out = s.turn("april has how many days")
    assert "30 days" in out and "extracted from" in out, out   # count: NUMBER + unit

    intent, tag, out = s.turn("april is what month of the year")
    assert "fourth month" in out, out                          # ordinal via the board numwords

    s.turn("siona remember chess is a strategy game on a board")
    intent, tag, out = s.turn("chess is played by how many players")
    assert out.startswith("recall:"), out                      # no answering span -> honest floor
