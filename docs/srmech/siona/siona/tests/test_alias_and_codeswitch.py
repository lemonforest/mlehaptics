"""Alias/morphology (prefix-cover, chosen by pre-measurement: Gram unchanged 0.271, eval 15/18 kept,
alias 3/5 gained; byteglyph vecs REJECTED read-independently at +0.130 cross-talk) + CODE-SWITCHING
(the merged bilingual board; the attested 'save' homograph drops to grounding: operators declared,
when declarations collide operands decide)."""
import os
import siona

DESC = os.path.join(os.path.dirname(siona.__file__), "descriptors", "bislama_udhr.toml")


def test_alias_prefix_cover():
    g = siona.Grounding()
    # morphology: 'cosine' covers the tool named 'cos' (suffixation prefix-cover)
    assert g.ground("compute the cosine of the angle", 1, owner="srmech")[0][1].endswith(".cos")
    assert g.ground("the sine of the angle", 1, owner="srmech")[0][1].endswith(".sin")
    # and the exact-name promotions still hold
    assert g.ground("bundle these klein-4 hypervectors by majority", 1,
                    owner="srmech")[0][1].split(".")[-1] == "klein4_bundle"


def test_codeswitch_merged_board():
    mix, conflicts = siona.merge_boards(siona.ENGLISH, siona.load_board(DESC))
    # the attested homograph: save -> SUPERPOSED senses (F1018 wiring), rung-selected at dispatch
    assert conflicts == {"save": (("english", "siona.memory.remember"),
                                  ("bislama-udhr", "siona.memory.recall"))}
    assert "save" not in mix.verb_tools and "save" in mix.self_verbs
    assert mix.homographs == conflicts and len(mix.parents) == 2
    s = siona.Session(board=mix)
    # mixed routing (bis operators + eng content and vice versa)
    assert s.route("wanem is the fiedler vector") == "define"
    assert s.route("mekem the gcd blong 48 and 36") == "tool-call"
    # mixed dialogue: eng verb + bis content, note stored UNDOCTORED (function words kept, F982)
    _, tag, out = s.turn("siona remember that wota i boela long 100 selsius")
    assert tag == "siona.remember"
    assert "wota i boela long 100 selsius" in s.mem[-1], s.mem[-1]
    _, _, out = s.turn("mekem the gcd blong 48 and 36")
    assert "gcd(48, 36) = 12" in out
    # save-with-content: the LANGUAGE VOTE dispatches the English sense deterministically now
    _, tag, _ = s.turn("siona save the note that chess is a game")
    assert tag == "siona.remember"
