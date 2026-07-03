"""F1027: multi-note synthesis (compare) + the wiki-attested conversion kernel (self-verified,
inverted exact-rationally, anchor-confirmed) + the srmech calculus/rational catalog reach
(sin/hypot exact). Memory-seeded with synthetic attestations -- mechanism, not knowledge."""
import siona


def _attest(s, topic, sha="0" * 64):
    s.attestations.append({
        "data": {"topic": topic}, "note_index": len(s.mem) - 1,
        "rendering": {"cite_as": "test source, %r" % topic},
        "attestation": {"response_sha256": sha}})


def test_synthesis_wiki_kernel_and_trig():
    s = siona.Session()

    # --- multi-note synthesis (the F774 compare op) ---
    s.mem.append("february is the second month it has 28 days in a common year")
    _attest(s, "february")
    s.mem.append("march is the third month between february and april it has 31 days")
    _attest(s, "march")
    _, tag, out = s.turn("which has more days february or march")
    assert "march" in out.split("--")[0] and "31 days" in out and "28 days" in out, out
    assert out.count("attested") == 2, out                    # BOTH sides cited

    # --- the wiki-attested conversion kernel (parse -> K self-verify -> invert -> confirm) ---
    s.mem.append("fahrenheit is a temperature unit the conversion rate to degrees celsius "
                 "is c 5 9 x f 32 water freezes at 32 f and boils at 212 f")
    _attest(s, "fahrenheit")
    s.turn("siona remember that water boils at 100 celsius")
    _, tag, out = s.turn("water boils at what fahrenheit")
    assert "212" in out and "acquired from the attested note" in out, out
    assert "CONFIRMED" in out, out                            # the article's own 212 anchor

    # --- the srmech continuous-math catalog reach (exact rational returns) ---
    _, tag, out = s.turn("compute the hypotenuse of legs 3 and 4")
    assert "hypot" in out and "= 5" in out, out               # Class-N sqrt cascade, exact
    _, tag, out = s.turn("compute the sine of 1 with 10 terms")
    assert "sin(1.0, terms=10)" in out and "/" in out, out    # exact rational Q
