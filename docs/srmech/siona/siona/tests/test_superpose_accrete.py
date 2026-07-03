"""Gate items (F1018 wiring): SUPERPOSED homograph dispatch on the merged board (rung-select by the
language vote; low margin -> ASK, the conflict-fallback) + operator ACCRETION with guards."""
import os
import siona

DESC = os.path.join(os.path.dirname(siona.__file__), "descriptors", "bislama_udhr.toml")


def test_homograph_superposed_dispatch_and_fallback():
    mix, _ = siona.merge_boards(siona.ENGLISH, siona.load_board(DESC))
    s = siona.Session(board=mix)
    # ENGLISH-context vote -> the English sense (remember); deterministic now, not grounding-luck
    _, tag, out = s.turn("siona save the note that chess is a game")
    assert tag == "siona.save" or tag == "siona.remember", (tag, out)
    if tag == "siona.save":  # ask-fallback did NOT fire; vote dispatched
        raise AssertionError(out)
    assert "noted" in out
    # BISLAMA-context vote ('blong' is bis operator vocab) -> the Bislama sense (recall)
    _, tag, out = s.turn("siona save blong wota")
    assert tag == "siona.recall", (tag, out)
    # sparse context -> the ASK fallback (never guess)
    _, tag, out = s.turn("siona save wota")
    assert "ambiguous" in str(out) and "remember" in str(out) and "recall" in str(out), (tag, out)


def test_accretion_with_guards():
    s = siona.Session()
    for _ in range(3):  # three consistent meaning-resolutions ('note' content grounds to remember)
        s.turn("siona stash the note that water boils")
    assert s.learned_verbs.get("stash") == "siona.memory.remember", s.learned_verbs
    _, tag, _ = s.turn("siona stash the note that chess is fun")  # now deterministic
    assert tag == "siona.remember"
    s.unlearn("stash")
    assert "stash" not in s.learned_verbs


def test_cross_language_content_recall():
    """The F1017 measured boundary, closed by the F1021 hybrid note encoding: an ENGLISH query
    retrieves a BISLAMA note via the byteglyph spelling bridge (water~wota)."""
    import pytest
    s = siona.Session()
    if getattr(s.g.cs, "enc_mode", None) != "byteglyph":
        pytest.skip("srmech byteglyph encoder (0.9.0rc28+) not on this floor -- "
                    "hybrid degrades to token-only (documented in PUBLISH_GATE)")
    s.mem.extend(["wota i boela long 100 selsius",
                  "chess is a game of 64 squares",
                  "the fiedler vector splits a graph"])
    _, tag, out = s.turn("siona recall water boiling")
    assert tag == "siona.recall" and "wota" in out, (tag, out)
