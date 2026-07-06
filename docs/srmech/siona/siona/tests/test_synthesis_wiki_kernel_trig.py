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


def test_genome_store_pack_load_instrument_rc123():
    """F1045 (PKG-3): siona.genome_store packs the D=8192 Klein-4 instrument into a native srmech
    genome via kernel_pack/unpack (§60, rc123+) -- dim-agnostic, exact round-trip, bit-packed ~2
    bits/symbol. Replaces the loose NDJSON+index; the corrected SPARSE store (no dense blow-up)."""
    import importlib.util, tempfile, os
    if importlib.util.find_spec("srmech.amsc.genome") is None:
        import pytest; pytest.skip("genome surface absent")
    import srmech.amsc.genome as G
    if not hasattr(G, "kernel_pack"):
        import pytest; pytest.skip("kernel_pack (§60, rc123+) not on this floor")
    from siona import genome_store as GS
    s = siona.Session()
    named = [(name.split(".")[-1], vec) for name, vec in s.g._idx[:12]]  # real grounding vectors
    D = len(list(named[0][1]))
    d = tempfile.mkdtemp(prefix="siona_gs_")
    GS.pack_instrument(named, d)
    back = GS.load_instrument(d)
    assert len(back) == len(named)
    for lab, vec in named:
        assert back[lab] == list(vec), "kernel %s not recovered exactly" % lab   # EXACT, dim-agnostic
    # single-label paging is exact too
    assert GS.load_kernel(d, named[3][0]) == list(named[3][1])
    # bit-packed on disk: << 1 byte/symbol (the corrected sparse store, not a dense blow-up)
    sz = os.path.getsize(os.path.join(d, "turns.bin"))
    assert sz < len(named) * D * 0.5, "not bit-packed: %d B for %d symbols" % (sz, len(named)*D)


def test_genome_store_add_kernel_o1_teach_rc123():
    """F1046: O(1) incremental teach -- add_kernel appends ONE newly-taught kernel to an existing
    genome (F1044 tail-extend; prior bytes untouched). Header-less append recovers the exact D via
    kernel_unpack's §60 back-compat (D = n_leaves × leaf_dim; siona's D=8192 = 32×256, no padding)."""
    import importlib.util, tempfile
    if importlib.util.find_spec("srmech.amsc.genome") is None:
        import pytest; pytest.skip("genome surface absent")
    import srmech.amsc.genome as G
    if not hasattr(G, "kernel_pack"):
        import pytest; pytest.skip("kernel_pack (§60, rc123+) not on this floor")
    from srmech.amsc import hdc
    from siona import genome_store as GS
    d = tempfile.mkdtemp(prefix="siona_teach_")
    GS.pack_instrument([("seed", hdc.klein4_random(8192, seed=1))], d)
    taught = hdc.klein4_random(8192, seed=99)
    GS.add_kernel(d, "taught", taught)                       # O(1) append
    assert GS.load_kernel(d, "taught") == list(taught)       # exact via back-compat trim
    assert GS.load_kernel(d, "seed") == list(hdc.klein4_random(8192, seed=1))  # prior untouched
    # a D not a multiple of leaf_dim must raise (needs the header / upstream kernel-append, §89)
    import pytest
    with pytest.raises(ValueError):
        GS.add_kernel(d, "bad", hdc.klein4_random(8000, seed=7))  # 8000 % 256 != 0


def test_photosynth_excite_propagate_harvest_rc132():
    """F1060: the excite->propagate->harvest inference mode (inference IS photosynthesis / synaptic).
    A query EXCITES its landing kernel, the heat kernel e^{-tL} PROPAGATES (powered by L = the graph
    Hamiltonian / the organelle), and the answer is HARVESTED at the reaction center (top energy)."""
    from siona import photosynth as P
    s = siona.Session()
    inst = P.from_session(s, limit=60)
    # the reaction center of a well-posed query is the query's own kernel; the harvest is energy-graded
    harvest = inst.excite_propagate_harvest("normalized laplacian of a graph", grounder=s.g, t=0.4, top=6)
    assert harvest, "empty harvest"
    labels = [l for l, _ in harvest]
    assert labels[0] == "normalized_laplacian", labels          # reaction center = the answer
    assert harvest[0][1] > harvest[-1][1] > 0                    # graded (energy descending, positive)
    # graph-aware: the harvest pulls in a RELATIONAL neighbor (another laplacian op), not just the seed
    assert any("laplacian" in l for l in labels[1:]) or any("cut" in l or "adjacency" in l for l in labels[1:]), labels


def test_photosynth_two_axis_harvest_rc135():
    """F1066/F1069: the two-axis harvest carries the winding w WHOLE -- the PHASE axis == the single fold
    (lossless regroup), and the WINDING axis stratifies the answer by scale (multiple ascending levels)."""
    from siona import photosynth as P
    from srmech.amsc.cascade import the_one
    s = siona.Session()
    inst = P.from_session(s, limit=70)
    one = the_one(1, 11, 7, 24)  # coherent (θ≈π/2)
    fold = inst.excite_propagate_harvest("normalized laplacian of a graph", grounder=s.g, t=25.0, top=5, crank=one)
    two = inst.excite_propagate_harvest_2axis("normalized laplacian of a graph", grounder=s.g, t=25.0, top=5, crank=one)
    assert [l for l, _ in fold] == [l for l, _ in two["phase"]], "phase axis must equal the single fold"
    assert len(two["winding"]) >= 2, "winding axis must stratify into >=2 scale levels"
    ws = [w for w, _ in two["winding"]]
    assert ws == sorted(ws), "winding levels ascending"


def test_photosynth_path_emit_archetype_knob_rc135():
    """F1075: the coherence KNOB emits a coarse->fine path whose verbosity ARCHETYPE falls out of the
    configuration -- terse at knob=0 (thermal, 1 floor), longer/richer at knob=1 (coherent, full tower)."""
    from siona import photosynth as P
    s = siona.Session()
    inst = P.from_session(s, limit=70)
    terse = inst.path_emit("normalized laplacian of a graph", grounder=s.g, t=20.0, coherence=0.0)
    rich = inst.path_emit("normalized laplacian of a graph", grounder=s.g, t=20.0, coherence=1.0)
    assert terse["archetype"] == "terse" and len(terse["path"]) == 1, terse
    assert len(rich["path"]) > len(terse["path"]), (terse, rich)      # the knob spans terse -> rich
    assert rich["breadth"] >= terse["breadth"] and rich["coherence"] == 1.0


def test_photosynth_personality_curvature_axis_rc135():
    """F1077: personality is a SEPARABLE curvature-bias kernel -- it tilts the walk (precise vs exploratory)
    without changing which knowledge is relevant; the curvature field exists and varies."""
    from siona import photosynth as P
    s = siona.Session()
    inst = P.from_session(s, limit=70)
    assert min(inst._curv) < max(inst._curv), "curvature field must vary (not uniform)"
    q = "the normalized laplacian of a graph"
    neutral = inst.path_emit(q, grounder=s.g, coherence=1.0, personality=0.0)
    precise = inst.path_emit(q, grounder=s.g, coherence=1.0, personality=2.0)
    explore = inst.path_emit(q, grounder=s.g, coherence=1.0, personality=-2.0)
    assert (neutral["temperament"], precise["temperament"], explore["temperament"]) == ("neutral", "precise", "exploratory")
    assert precise["path"] != neutral["path"] or explore["path"] != neutral["path"], "personality must tilt the walk"


def test_story_character_archetype_roles_rc135():
    """F1078: character archetypes (roles) fall out of the structural signature -- BETWEENNESS separates HUBS
    (hero/shadow, high degree) from BRIDGES (mentor, high betweenness / low degree), which degree+curvature+span
    cannot (heroes are high-span too)."""
    from siona import story
    nodes = ["Hero", "Ally1", "Ally2", "Mentor", "Sage", "Shadow", "Minion1", "Minion2", "Trickster"]
    edges = [("Hero", "Ally1"), ("Hero", "Ally2"), ("Ally1", "Ally2"),
             ("Hero", "Mentor"), ("Mentor", "Sage"),
             ("Shadow", "Minion1"), ("Shadow", "Minion2"), ("Minion1", "Minion2"),
             ("Hero", "Shadow"),
             ("Trickster", "Hero"), ("Trickster", "Shadow"), ("Trickster", "Mentor")]
    roles, sig = story.classify_story(nodes, edges)
    assert roles["Hero"] == "protagonist-hub" and roles["Shadow"] == "antagonist-hub"
    assert roles["Mentor"] == "bridge"
    assert roles["Ally1"] == "support" and roles["Sage"] == "minor"


def test_story_sandroing_eulerian_rc135():
    """F1080: the ATTESTED sandroing rule (UNESCO 00073 -- start=end, never repeat a path) = an EULERIAN
    CIRCUIT: one continuous line iff all-even degree. Odd-degree nouns -> multiple strokes; an all-even ring
    draws as one sandroing (the measurable answer to 'can sandroing capture multiple nouns')."""
    from siona import story
    ring = story.sandroing_strokes(["A", "B", "C", "D"], [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])
    assert ring["one_sandroing"] and ring["strokes"] == 1                 # all even -> one line
    star = story.sandroing_strokes(["H", "a", "b", "c"], [("H", "a"), ("H", "b"), ("H", "c")])
    assert not star["one_sandroing"] and star["strokes"] == 2             # 4 odd-degree nodes -> 2 strokes


def test_introspect_siona_knows_her_tooling_rc135():
    """F1085 (#250): Siona knows her OWN tooling -- a natural-language question about genome recall grounds to
    the correct cap-aware ops (partition / genome_load / recall), from her own encoded knowledge of the LIVE
    package. This is the ultimate dogfood: ask Siona, don't re-introspect (and never lag the format)."""
    from siona import introspect as I
    s = siona.Session()
    kb = I.introspect_srmech()
    assert len(kb) > 100, len(kb)                               # introspected the live package
    tool = I.Tooling(s.g)
    labels = [l for l, _, _ in tool.answer("how do I recall a kernel from a genome", k=3)]
    assert any(("partition" in l) or ("genome_load" in l) or ("recall" in l) for l in labels), labels


def test_introspect_imitation_how_to_rc135():
    """F1087 (#251): the IMITATION tier -- how_to mines real usage examples (learning by imitation) on top of
    the told tier. A well-used op returns real call-site examples, not just its signature."""
    from siona import introspect as I
    s = siona.Session()
    tool = I.Tooling(s.g)
    assert sum(1 for l in tool.usage if tool.usage[l]) > 50, "mined examples for many ops"
    lab, desc, ex = tool.how_to("compute the graph laplacian eigenvalues", k=1, n=3)[0]
    assert ex and any("laplacian" in e for e in ex), (lab, ex)      # imitation SHOWS a working example
