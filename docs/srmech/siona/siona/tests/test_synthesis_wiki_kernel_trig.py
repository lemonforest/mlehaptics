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


def test_register_conversion_ladder_rc117():
    """F1039: the register becomes a CONVERSION LADDER -- when a tool needs a higher-rung carrier
    and the register holds a lower one on the same ladder, siona auto-PROMOTES via the srmech
    carrier_ladder_descriptor (#1248). A Poly in hand reaches a BiPoly|TriPoly consumer."""
    import importlib.util
    if importlib.util.find_spec("srmech.amsc.carrier_ladder") is None:
        import pytest
        pytest.skip("carrier_ladder (srmech rc117+) not on this floor")
    s = siona.Session()
    s.turn("compute the poly from coeffs 1 2 3")                         # -> Poly in register (rung 1)
    _, tag, out = s.turn("compute the poly promote of it")
    assert "poly_promote(Poly" in out and "BiPoly" in out, out          # Poly -> BiPoly
    s.turn("compute the poly from coeffs 1 2 3")
    _, tag, out = s.turn("compute the poly project of it")              # projector wants BiPoly|TriPoly
    assert "poly_project(BiPoly" in out, out                            # the Poly was auto-promoted UP


def test_cd_ladder_auto_promote_rc117():
    """F1040: the register auto-promotes on the CAYLEY-DICKSON ladder too -- a cd element
    (rung = its length) is lifted UP to a Hurwitz consumer's rung (the algebra NAME is the rung:
    octonion == dim 8). quaternion_exp -> a rung-4 quaternion -> octonion op promotes 4->8."""
    import importlib.util
    if importlib.util.find_spec("srmech.amsc.carrier_ladder") is None:
        import pytest
        pytest.skip("carrier_ladder (srmech rc117+) not on this floor")
    s = siona.Session()
    s.turn("compute the quaternion exp of 0.5")                          # -> rung-4 quaternion
    _, tag, out = s.turn("compute the quaternion conjugate of it")
    assert "quaternion_conjugate([" in out, out                         # same rung, direct bind
    _, tag, out = s.turn("compute the quaternion exp of 0.5")
    _, tag, out = s.turn("compute the octonion conjugate of it")
    assert "octonion_conjugate([" in out, out                           # rung 4 AUTO-PROMOTED to 8
    # a length-8 result proves the promotion (a bare quaternion would have errored or stayed len-4)
    assert out.count("Fraction") >= 8 or out.count(",") >= 7, out


def test_cd_explicit_dim_promotion_rc117():
    """F1041: explicit-dim cd promotion -- 'promote it to a sedenion' / 'to N'. The register (a cd
    element) binds to cd_promote's x AS-IS and the target dim rides the utterance (algebra word or
    'to N'), not the op name. The _fit refactor: a ref-fit param is excluded from operand accounting."""
    import importlib.util
    if importlib.util.find_spec("srmech.amsc.carrier_ladder") is None:
        import pytest
        pytest.skip("carrier_ladder (srmech rc117+) not on this floor")
    s = siona.Session()
    s.turn("compute the quaternion exp of 0.5")                          # rung-4 quaternion in register
    _, tag, out = s.turn("compute the cd promote of it to a sedenion")
    assert "cd_promote([0.877" in out and ", 16)" in out, out            # register->x AS-IS, dim=16 from word
    s.turn("compute the quaternion exp of 0.5")
    _, tag, out = s.turn("compute the cd promote of it to 8")
    assert "cd_promote([0.877" in out and ", 8)" in out, out             # dim=8 from 'to N'


def test_cd_rung_read_from_declared_contract_rc120():
    """F1043: #1254 delivered (rc120) -- the per-op carrier contract ships as
    carrier_ladder_descriptor()['ops']. Siona READS the consumer's rung from it (octonion_conjugate
    -> 8) instead of name-mapping 'octonion'->8. The name-map survives only as the pre-rc120 fallback."""
    import importlib.util
    if importlib.util.find_spec("srmech.amsc.carrier_ladder") is None:
        import pytest
        pytest.skip("carrier_ladder not on this floor")
    from srmech.amsc.carrier_ladder import carrier_ladder_descriptor
    if "ops" not in carrier_ladder_descriptor():
        import pytest
        pytest.skip("per-op contract (ops map, #1254/rc120) not on this floor")
    s = siona.Session()
    assert s._op_consume_rung("srmech.qm.octonion.octonion_conjugate") == 8   # READ, not name-mapped
    assert s._op_consume_rung("srmech.qm.quaternion.quaternion_norm") == 4
    assert s._op_consume_rung("srmech.amsc.cascade.cd_promote") is None       # 'any' -> not a fixed rung
    # and the auto-promote still lands (4->8) driven by the contract-read rung
    s.turn("compute the quaternion exp of 0.5")
    _, tag, out = s.turn("compute the octonion conjugate of it")
    assert "octonion_conjugate([" in out, out
