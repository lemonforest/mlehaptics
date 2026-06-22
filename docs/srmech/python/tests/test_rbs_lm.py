"""Tests for srmech.rbs_lm — the §9 RBS-LM inference substrate (F166 walk).

Covers: encode-helper determinism + sector-respect, ContextSubstrate state
shape + determinism, end-to-end learn → next_token_distribution → infer over a
tiny token stream, attestation block keys, and infer determinism. The substrate
is built via the in-memory ``from_params`` path (no TOML), with one test
exercising ``from_catalog`` through a tmp descriptor.toml.

§57: the candidate set is the full bounded ATOM set (``self.vocab``) scored by
the Class-M resonator over ``M`` — there is NO hand-rolled ``Counter()`` bigram
gate (the STOP-list contaminant). So these tests assert full-vocab candidates +
greedy resonator grounding rather than bigram-legality.

numpy-free (v0.7.5rc113, #564): the encode path returns the framework-native
``srmech.amsc.hv.HV`` carrier and the substrate runs with numpy absent, so these
assertions are HV-native (``len`` / ``.tolist`` / ``==``) rather than ndarray
(``.shape`` / ``np.array_equal``). The structural properties under test
(determinism, the XOR-sector relationship, self-similarity == 1.0, bigram-
legality, same-seed determinism) are RNG-independent, so the rc113 RNG re-base
changes the underlying bytes but pins no test to a specific byte value.
"""
from __future__ import annotations

import pytest

from srmech.rbs_lm import (
    ContextSubstrate,
    RBSLMInferenceSubstrate,
    encode_bigram_l1,
    encode_sentence_l3,
    encode_skeleton_l2,
    encode_word_k4,
    sim_k4_batch,
    token_seed,
)

# A small canonical D / hex_chars + instrument params (the same nested shape the
# descriptor catalog yields under desc.fetch["literature_curated"]).
D = 256
HEX_CHARS = 12

PARAMS = {
    "substrate": {"D": D, "token_seed_hex_chars": HEX_CHARS},
    "inference": {
        "instrument": {
            "operating_k": 2,
            "operating_temperature": 0.1,
            "memory_capacity": 64,
            "default_max_tokens": 8,
            "learn_seed": 1234,
        }
    },
}

TINY_STREAM = ["the", "cat", "sat", "the", "cat", "ran", "the", "dog", "sat"]


# --------------------------------------------------------------- encode helpers

def test_token_seed_deterministic():
    assert token_seed("the", HEX_CHARS) == token_seed("the", HEX_CHARS)
    # Distinct words → (almost surely) distinct seeds.
    assert token_seed("the", HEX_CHARS) != token_seed("cat", HEX_CHARS)


def test_encode_word_k4_deterministic_and_klein4():
    a = encode_word_k4("cat", D=D, sector=0, hex_chars=HEX_CHARS)
    b = encode_word_k4("cat", D=D, sector=0, hex_chars=HEX_CHARS)
    assert a == b
    assert len(a) == D
    assert a.sectors == 4
    # Klein-4 alphabet only.
    assert set(a.tolist()).issubset({0, 1, 2, 3})


def test_encode_word_k4_respects_sector():
    s0 = encode_word_k4("cat", D=D, sector=0, hex_chars=HEX_CHARS)
    s1 = encode_word_k4("cat", D=D, sector=1, hex_chars=HEX_CHARS)
    s2 = encode_word_k4("cat", D=D, sector=2, hex_chars=HEX_CHARS)
    # Sector is a constant XOR-bind, so a different sector → a different vector,
    # and sector-1 is exactly the iω₇ (XOR 1) flip of sector-0 (sector-2 the γ₅
    # XOR 2). Structural — holds independent of the per-token RNG.
    assert s0 != s1
    assert s0 != s2
    base = s0.tolist()
    assert s1 == [x ^ 1 for x in base]
    assert s2 == [x ^ 2 for x in base]


def test_encode_bigram_skeleton_sentence_deterministic():
    b1 = encode_bigram_l1("the", "cat", D=D, hex_chars=HEX_CHARS)
    b2 = encode_bigram_l1("the", "cat", D=D, hex_chars=HEX_CHARS)
    assert b1 == b2
    assert len(b1) == D and b1.sectors == 4

    sk = encode_skeleton_l2(("the", "cat"), ("dog", "sat"), D=D, hex_chars=HEX_CHARS)
    sk2 = encode_skeleton_l2(("the", "cat"), ("dog", "sat"), D=D, hex_chars=HEX_CHARS)
    assert sk == sk2
    assert len(sk) == D

    se = encode_sentence_l3(["the", "cat", "sat"], D=D, hex_chars=HEX_CHARS)
    se2 = encode_sentence_l3(["the", "cat", "sat"], D=D, hex_chars=HEX_CHARS)
    assert se == se2
    assert len(se) == D


def test_sim_k4_batch_self_is_one():
    q = encode_word_k4("cat", D=D, sector=0, hex_chars=HEX_CHARS)
    cands = [
        encode_word_k4("cat", D=D, sector=0, hex_chars=HEX_CHARS),
        encode_word_k4("dog", D=D, sector=0, hex_chars=HEX_CHARS),
    ]
    sims = sim_k4_batch(q, cands)
    assert len(sims) == 2
    assert sims[0] == pytest.approx(1.0)
    assert 0.0 <= sims[1] <= 1.0
    assert sims[1] < sims[0]


# ----------------------------------------------------------- ContextSubstrate

def test_context_substrate_encode_shape_and_determinism():
    ctx = ContextSubstrate(D=D, hex_chars=HEX_CHARS)
    s1 = ctx.encode_context(["the", "cat"])
    s2 = ctx.encode_context(["the", "cat"])
    assert len(s1) == D
    assert s1.sectors == 4
    assert set(s1.tolist()).issubset({0, 1, 2, 3})
    assert s1 == s2
    # Order matters (positional role-filler binding).
    assert ctx.encode_context(["the", "cat"]) != ctx.encode_context(["cat", "the"])


def test_context_substrate_even_window_uses_pad_not_drop():
    ctx = ContextSubstrate(D=D, hex_chars=HEX_CHARS)
    # A single-token window returns the bound vector directly; a 3-token window
    # is an odd bundle. Both produce a valid Klein-4 vector of length D.
    one = ctx.encode_context(["the"])
    three = ctx.encode_context(["the", "cat", "sat"])
    assert len(one) == D and len(three) == D


# ----------------------------------------------------------- build + end-to-end

def test_from_params_constructor():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS)
    assert sub.ctx.D == D
    assert sub.ctx.hex_chars == HEX_CHARS
    assert sub.operating_k == 2
    assert sub.operating_temperature == pytest.approx(0.1)
    assert sub.memory_capacity == 64
    assert sub.default_max_tokens == 8
    assert sub.learn_seed == 1234
    assert isinstance(sub.srmech_version, str) and sub.srmech_version
    assert sub.descriptor_hash == ""
    # has_native is a bool either way; abi_version is an int when native is
    # present, else None (NATIVE_ABI_VERSION). Both are acceptable.
    assert isinstance(sub.has_native, bool)
    assert sub.abi_version is None or isinstance(sub.abi_version, int)


def test_learn_builds_atom_set_and_memory():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS).learn(TINY_STREAM)
    assert sub.M is not None
    assert len(sub.M) == D
    assert sub.n_learned > 0
    assert sub.vocab == sorted(set(TINY_STREAM))
    # §57: the candidate set is the bounded ATOM set (vocab), one HV per atom —
    # NOT a hand-rolled bigram-count table. The Counter()/defaultdict next_after
    # structure the STOP-list forbids is gone.
    assert sub.vocab_vecs is not None
    assert len(sub.vocab_vecs) == len(sub.vocab)
    assert not hasattr(sub, "next_after")
    assert not hasattr(sub, "bigram_counts")


def test_next_token_distribution_full_vocab_candidates():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS).learn(TINY_STREAM)
    cands, probs = sub.next_token_distribution(["the", "cat"])
    # §57: candidates are the FULL bounded atom set (the resonator scores all of
    # vocab), NOT a bigram-legal subset of the last token's successors.
    assert set(cands) == set(sub.vocab)
    assert len(probs) == len(cands)
    assert float(sum(probs)) == pytest.approx(1.0)
    assert all(p >= 0.0 for p in probs)


def test_next_token_distribution_no_dead_end_under_resonator():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS).learn(TINY_STREAM)
    # §57: there is no bigram "dead end" — a context whose last token never
    # appeared as a left-token STILL resonates over the full atom set (grounding
    # comes from M, not a next-token gate), so candidates are never empty here.
    cands, probs = sub.next_token_distribution(["the", "neverseen"])
    assert set(cands) == set(sub.vocab)
    assert float(sum(probs)) == pytest.approx(1.0)


def test_greedy_recovers_grounded_successor():
    # §57 grounding: at inference D the Class-M resonator over M recovers the
    # stored next token. A distinct-token stream makes each k-window unique, so
    # greedy (T<=0, §56 argmax → one-hot) is exact.
    hi = {
        "substrate": {"D": 8192, "token_seed_hex_chars": HEX_CHARS},
        "inference": {"instrument": {
            "operating_k": 2, "operating_temperature": 0.0,
            "memory_capacity": 1000, "default_max_tokens": 8, "learn_seed": 1234}},
    }
    stream = ["a", "b", "c", "d", "e", "f"]
    sub = RBSLMInferenceSubstrate.from_params(hi).learn(stream)
    cands, probs = sub.next_token_distribution(["a", "b"], temperature=0.0)
    # one-hot greedy: the argmax candidate is the grounded successor "c".
    top = cands[max(range(len(probs)), key=lambda i: probs[i])]
    assert top == "c"
    assert float(sum(probs)) == pytest.approx(1.0)


def test_next_token_distribution_before_learn_raises():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS)
    with pytest.raises(RuntimeError):
        sub.next_token_distribution(["the", "cat"])


def test_infer_starts_from_prompt_and_stays_in_vocab():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS).learn(TINY_STREAM)
    out = sub.infer(["the", "cat"], max_tokens=5, seed=7)
    assert isinstance(out, list)
    assert out[:2] == ["the", "cat"]
    # §57: every generated token is drawn from the bounded atom set (the
    # resonator only ever ranks vocab atoms) — no bigram-legality gate.
    assert all(tok in sub.vocab for tok in out)


def test_infer_determinism_same_seed():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS).learn(TINY_STREAM)
    o1 = sub.infer(["the", "cat"], max_tokens=6, seed=42)
    o2 = sub.infer(["the", "cat"], max_tokens=6, seed=42)
    assert o1 == o2


def test_attestation_has_mandatory_keys():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS).learn(TINY_STREAM)
    att = sub.attestation()
    for key in ("method", "descriptor_hash", "srmech_version", "abi_version",
                "has_native", "operating_k", "operating_temperature",
                "memory_capacity", "n_learned", "vocab_size", "substrate",
                "provenance"):
        assert key in att
    assert att["method"] == "config_descriptor"
    assert isinstance(att["srmech_version"], str) and att["srmech_version"]
    assert att["vocab_size"] == len(sub.vocab)
    assert att["n_learned"] == sub.n_learned


def test_describe_smoke():
    sub = RBSLMInferenceSubstrate.from_params(PARAMS).learn(TINY_STREAM)
    text = sub.describe()
    assert "RBSLMInferenceSubstrate" in text
    assert f"D={D}" in text
    assert "k=2" in text


# --------------------------------------------------------------- from_catalog

def _write_descriptor(tmp_path):
    """Write a minimal valid descriptor.toml carrying the inference params under
    [fetch.literature_curated.*] (the structure from_catalog reads)."""
    toml = """\
[source]
key = "rbs_lm_inference_test"
human_readable_name = "RBS-LM Inference Substrate (test)"
purpose = "F166 inference substrate parameterization (test fixture)"
license = "CC0"
homepage = "https://srmech.net"

[fetch]
adapter = "literature_curated"

[fetch.literature_curated.substrate]
D = 256
token_seed_hex_chars = 12

[fetch.literature_curated.inference.instrument]
operating_k = 2
operating_temperature = 0.1
memory_capacity = 64
default_max_tokens = 8
learn_seed = 1234

[parse]
format = "ndjson"

[schema]
schema_id = "test://schema/rbs_lm_inference"

[rendering]
cite_as_template = "RBS-LM inference substrate {source.key}"
purpose_template = "{source.purpose}"

[attestation]
license = "CC0"
"""
    p = tmp_path / "descriptor.toml"
    p.write_text(toml, encoding="utf-8")
    return p


def test_from_catalog_builds_substrate(tmp_path):
    path = _write_descriptor(tmp_path)
    sub = RBSLMInferenceSubstrate.from_catalog(path)
    assert sub.ctx.D == D
    assert sub.operating_k == 2
    assert sub.memory_capacity == 64
    # descriptor_hash is a 64-hex SHA-256 string for the catalog path.
    assert isinstance(sub.descriptor_hash, str)
    assert len(sub.descriptor_hash) == 64
    int(sub.descriptor_hash, 16)  # parses as hex
    # End-to-end works identically to the from_params path (§57: full atom set).
    sub.learn(TINY_STREAM)
    cands, probs = sub.next_token_distribution(["the", "cat"])
    assert set(cands) == set(sub.vocab)
    assert float(sum(probs)) == pytest.approx(1.0)
