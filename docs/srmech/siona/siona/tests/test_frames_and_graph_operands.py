"""Gate items: PARAPHRASE frames (politeness prefixes = declared operators, consumed before routing)
+ GRAPH operands (edge-pairs 'a-b' -> Iterable[Tuple[int,int]] params; n derives from the edges)."""
import re
import siona


def test_politeness_paraphrase_frames():
    s = siona.Session()
    assert s.route("please compute the gcd of 48 and 36") == "tool-call"
    assert s.route("could you describe the fiedler vector") == "define"
    assert s.route("can you tell me about prime factorization") == "define"
    _, tag, out = s.turn("please compute the gcd of 48 and 36")
    assert "gcd(48, 36) = 12" in out
    # politeness words in content position are NOT eaten (only the prefix is operator)
    assert s.route("water can flow down the") == "continue"


def test_graph_edge_operands():
    s = siona.Session()
    _, tag, out = s.turn("compute the magnetic laplacian of the edges 0-1 1-2 2-0")
    assert tag == "srmech"
    assert "magnetic_laplacian(3, [(0, 1), (1, 2), (2, 0)]" in out, out
