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


def test_source_qualified_selection():
    """F1033: 'per <src>' selects the sense from that attested source; the unqualified ask
    surfaces the PARALLEL SOURCE (conflicting senses superpose, neither deleted)."""
    s = siona.Session()
    s.mem.append("a widget is a small mechanical device with 3 parts")
    s.attestations.append({"data": {"topic": "widget"}, "note_index": 0,
                           "rendering": {"cite_as": "encyclopedia alpha, 'widget'"},
                           "attestation": {"response_sha256": "a" * 64, "source_url": "file://alpha"}})
    s.mem.append("a widget is not a device it is a 2 sided abstraction with 3 views")
    s.attestations.append({"data": {"topic": "widget"}, "note_index": 1,
                           "rendering": {"cite_as": "framework notes beta, 'widget'"},
                           "attestation": {"response_sha256": "b" * 64, "source_url": "file://beta"}})
    _, _, out = s.turn("per beta a widget is what")
    assert "abstraction" in out and "beta" in out, out         # the qualified source wins
    _, _, out = s.turn("per alpha a widget is what")
    assert "mechanical" in out and "alpha" in out, out
    _, _, out = s.turn("a widget is what")
    assert "PARALLEL SOURCE" in out, out                       # unqualified -> both surfaced


def test_carrier_register_chain_rc113():
    """F1038: the F1024 result-register generalizes from Mat to EVERY carrier -- rc113's new
    carrier-consuming tools (heat_trace: Mat+scalar-union t; theta_coefficients: UnaryTheta+n)
    chain from a prior build turn. The scalar-union 'float | Sequence[float]' binds SCALAR."""
    s = siona.Session()
    s.turn("compute the magnetic laplacian of the edges 0-1 1-2 2-0")   # -> Mat in register
    _, tag, out = s.turn("compute the heat trace of it at 1")
    assert "heat_trace(Mat" in out and ", 1.0)" in out, out              # scalar t, not [1]
    s.turn("compute the unary theta with char minus12 j 0 a 1 b 0 d 24") # -> UnaryTheta in register
    _, tag, out = s.turn("compute the theta coefficients of it with n max 12")
    assert "theta_coefficients(UnaryTheta" in out and "[1, -1, -1" in out, out   # eta/Euler head
