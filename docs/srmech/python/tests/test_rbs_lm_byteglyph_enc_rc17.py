"""rc17 — the C1-enc graduation (F916/F917 Part A): the byte/glyph LM substrate.

Covers the three shipped pieces + the behaviour-pin guarantee:
  1. ``hdc.klein4_compose`` — the scale-invariant role-filler compositor; it is
     similarity-PRESERVING where a chained ``klein4_bind`` fold collapses to chance.
  2. ``ContextSubstrate`` ``enc_mode`` — byte/glyph default restores MORPHOLOGY;
     ``wordhash`` reproduces the prior bytes EXACTLY (the pin).
  3. ``scale_signature`` — coherence == scale-invariance, made introspectable, and
     stable across the byte and word scales (F900).
  4. ``RBSLMInferenceSubstrate`` runs on the byte/glyph object natively.

numpy-free (the no-numpy-test discipline); deterministic (seeded ``klein4_random``).
"""

from srmech.amsc import hdc
from srmech.rbs_lm import substrate as cs

D = 96
_PERTURB = hdc.klein4_random(D, seed=999)  # a fixed off-manifold atom


def _retained_sim(parts, i):
    """sim(compose(parts), compose(parts with parts[i] swapped for _PERTURB))."""
    swapped = list(parts)
    swapped[i] = _PERTURB
    return float(hdc.klein4_similarity(
        hdc.klein4_compose(parts), hdc.klein4_compose(swapped)))


def _chained_retained_sim(parts, i):
    """Same one-part perturbation, but through a chained ``klein4_bind`` fold."""
    def fold(vs):
        acc = vs[0]
        for v in vs[1:]:
            acc = hdc.klein4_bind(acc, v)
        return acc
    swapped = list(parts)
    swapped[i] = _PERTURB
    return float(hdc.klein4_similarity(fold(parts), fold(swapped)))


# ---------------------------------------------------------------- klein4_compose

def test_klein4_compose_is_similarity_preserving_vs_chained_fold():
    """A one-part change degrades the compositor GRACEFULLY; the chained-bind fold
    collapses to ~chance — the F900 core claim, the reason C1 is the LM substrate."""
    parts = [hdc.klein4_random(D, seed=s) for s in (1, 2, 3, 4, 5)]
    comp = [_retained_sim(parts, i) for i in range(len(parts))]
    chain = [_chained_retained_sim(parts, i) for i in range(len(parts))]
    # compose retains structure; chained fold falls toward the ~0.25 chance level.
    assert min(comp) > 0.40, comp
    assert max(chain) < 0.35, chain
    assert min(comp) > max(chain) + 0.10


def test_klein4_compose_single_and_empty():
    one = hdc.klein4_random(D, seed=7)
    out = hdc.klein4_compose([one])
    assert len(out) == D  # single part → position-bound (the identity rung)
    try:
        hdc.klein4_compose([])
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("empty parts must raise ValueError")


def test_klein4_compose_order_sensitive():
    """Position-binding makes the compositor order-sensitive (a sequence model)."""
    a = hdc.klein4_random(D, seed=11)
    b = hdc.klein4_random(D, seed=12)
    c = hdc.klein4_random(D, seed=13)
    s_ab = float(hdc.klein4_similarity(
        hdc.klein4_compose([a, b, c]), hdc.klein4_compose([c, b, a])))
    assert s_ab < 0.6  # reordering moves the composite well off identity


# ---------------------------------------------------------------- byte/glyph enc

def test_byteglyph_restores_morphology_wordhash_does_not():
    ec = lambda s: hdc.klein4_encode_bytes(s.encode("utf-8"), D)
    cat_cats = float(hdc.klein4_similarity(ec("cat"), ec("cats")))
    cat_dog = float(hdc.klein4_similarity(ec("cat"), ec("dog")))
    assert cat_cats > 0.5 > cat_dog          # shared prefix bytes ≫ disjoint
    # the word-hash dual is morphology-BLIND: cat/cats ≈ cat/dog ≈ chance
    wh = lambda s: cs.encode_word_k4(s, D=D, sector=0, hex_chars=8)
    wh_cats = float(hdc.klein4_similarity(wh("cat"), wh("cats")))
    assert wh_cats < 0.4                       # ~chance — no morphology


def test_enc_mode_default_is_byteglyph_and_wordhash_pins_prior_bytes():
    ctx = cs.ContextSubstrate(D=D, hex_chars=8)
    assert ctx.enc_mode == "byteglyph"
    # wordhash mode reproduces encode_word_k4 EXACTLY (the behaviour pin)
    ctx_w = cs.ContextSubstrate(D=D, hex_chars=8, enc_mode="wordhash")
    direct = cs.encode_word_k4("hello", D=D, sector=0, hex_chars=8)
    assert list(ctx_w.enc("hello")) == list(direct)
    # byteglyph differs from wordhash (the deliverable is a real numerics change)
    assert list(ctx.enc("hello")) != list(ctx_w.enc("hello"))
    # encode_context numerics: wordhash reproduces, byteglyph is the new object
    win = ["the", "cat", "sat"]
    assert list(ctx.encode_context(win)) != list(ctx_w.encode_context(win))


def test_enc_mode_invalid_raises():
    try:
        cs.ContextSubstrate(D=D, hex_chars=8, enc_mode="bogus")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("invalid enc_mode must raise ValueError")


def test_pos_key_is_enc_mode_independent():
    """Position role vectors must NOT change with enc_mode (orthogonal atoms)."""
    cb = cs.ContextSubstrate(D=D, hex_chars=8)               # byteglyph
    cw = cs.ContextSubstrate(D=D, hex_chars=8, enc_mode="wordhash")
    assert list(cb.pos_key(2)) == list(cw.pos_key(2))
    # adjacent position keys stay near-orthogonal (no byte-correlation leak)
    pk_adj = float(hdc.klein4_similarity(cb.pos_key(3), cb.pos_key(4)))
    assert pk_adj < 0.45


# ---------------------------------------------------------------- scale_signature

def test_scale_signature_is_scale_invariant_and_above_chance():
    """The fractal coherence signature is stable across the byte and word scales
    (the same operator at every rung) and well above the ~0.25 chance floor."""
    byte_atoms = [hdc.klein4_random(D, seed=b) for b in b"abcde"]   # byte rung
    word_vecs = [hdc.klein4_encode_bytes(w, D)                      # word rung
                 for w in (b"alpha", b"bravo", b"charlie", b"delta", b"echo")]
    sig_byte = float(cs.scale_signature(byte_atoms))
    sig_word = float(cs.scale_signature(word_vecs))
    assert sig_byte > 0.35 and sig_word > 0.35           # coherent, above chance
    assert abs(sig_byte - sig_word) < 0.25               # SAME band → scale-invariant


def test_scale_signature_needs_two_parts():
    try:
        cs.scale_signature([hdc.klein4_random(D, seed=1)])
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("scale_signature needs >= 2 parts")


# ------------------------------------------------- inference runs on byte/glyph

def _params(enc_mode):
    return {
        "substrate": {"D": D, "token_seed_hex_chars": 8, "enc_mode": enc_mode},
        "inference": {"instrument": {
            "operating_k": 2, "operating_temperature": 1.0,
            "memory_capacity": 64, "default_max_tokens": 8, "learn_seed": 3}},
    }


def test_inference_substrate_runs_on_byteglyph_object():
    from srmech.rbs_lm.inference import RBSLMInferenceSubstrate
    sub = RBSLMInferenceSubstrate.from_params(_params("byteglyph"))
    assert sub.ctx.enc_mode == "byteglyph"
    sub.learn(["the", "cat", "sat", "on", "the", "mat"])
    out = sub.infer(["the", "cat"], max_tokens=3)
    assert isinstance(out, (list, tuple)) and len(out) >= 1
    # default (no enc_mode in params) also resolves to byteglyph
    p = _params("byteglyph"); del p["substrate"]["enc_mode"]
    assert RBSLMInferenceSubstrate.from_params(p).ctx.enc_mode == "byteglyph"
