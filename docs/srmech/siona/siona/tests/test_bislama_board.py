"""The REAL Bislama board (UDHR-attested vocabulary; siona/descriptors/bislama_udhr.toml).
Every operator token is attested in the local UDHR-bis text with the parallel English article as
gloss (the Rosetta method attesting its own board). Routing + self-dispatch run UNCHANGED under it.
The remember slot is honestly UNATTESTED (no tingbaot in the UDHR) -> memory is seeded directly."""
import os
import siona

DESC = os.path.join(os.path.dirname(siona.__file__), "descriptors", "bislama_udhr.toml")


def test_bislama_board_loads_attested():
    b = siona.load_board(DESC)
    assert b.name == "bislama-udhr"
    # attested operator classes, pairwise disjoint
    assert b.self_verbs == frozenset({"soem", "luksave", "talem", "save"})
    assert b.self_verbs.isdisjoint(b.imperatives)
    assert "wanem" in b.interrogatives
    # the honest gap: NO remember mapping (unattested)
    assert "siona.memory.remember" not in set(b.verb_tools.values())


def test_bislama_routing_and_dispatch():
    s = siona.Session(board=siona.load_board(DESC))
    # define frame: 'wanem X' = 'what X' (attested arts 16/23)
    assert s.route("wanem raet blong evriwan") == "define"
    # continue = the default (a dangling content prefix; function words measured, not invented)
    assert s.route("ol man mo woman i gat") == "continue"
    # operands still route tool-call (language-independent evidence)
    assert s.route("mekem gcd blong 48 mo 36") == "tool-call"
    # seed memory directly (the remember verb is unattested -- documented gap)
    s.mem.append("wota i boela long 100 selsius")
    # luksave (recognize -> recall, art 6) retrieves the note
    _, tag, out = s.turn("siona luksave wota")
    assert tag == "siona.recall" and "wota" in out, (tag, out)
    # soem (show/manifest, art 18) lists the memory
    _, tag, out = s.turn("siona soem")
    assert tag == "siona.show" and "wota" in out, (tag, out)
    # a real srmech drive under the Bislama utterance (ints + name token carry it)
    _, tag, out = s.turn("mekem gcd blong 48 mo 36")
    assert "gcd(48, 36) = 12" in out or "gcd(36, 48)" in out, out
