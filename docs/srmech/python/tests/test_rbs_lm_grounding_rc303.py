"""rc303 (§112 / #1462, task #941) — the df-gated aboutness grounding encoder.

Covers the F1008 recipe promoted to a first-class rbs_lm op:
  * the F1260 discriminant (byteglyph is structure-bearing; address is not),
  * df-gate + name-weighting + order-aware bigram mechanics,
  * determinism, arg validation,
  * grounding on a controlled synthetic corpus AND the live tool_schema,
  * the tool_schema registration.

numpy-free (the whole rbs_lm encode path is the framework-native HV surface).
"""

import pytest

from srmech.introspect import tool_schema as ts
from srmech.math import hdc
from srmech.rbs_lm import encode_aboutness, ground_tool_schema
from srmech.rbs_lm.grounding import (_aboutness_tokens, _doc_frequencies,
                                     _gate_keep)


def _fl(x):
    return x.as_float() if hasattr(x, "as_float") else float(x)


def _sim(a, b):
    return _fl(hdc.klein4_similarity(a, b))


# ── F1260 discriminant: the encoder must be STRUCTURE-BEARING ────────────────

def test_f1260_byteglyph_is_structure_bearing():
    """The DEFAULT (byteglyph) token backend must keep a morphological near-pair
    (cat/cats) clearly MORE similar than an unrelated control (cat/dog) — the
    F1260 discriminant that a word-hash address FAILS."""
    D = 4096
    cat = encode_aboutness("cat", D=D)
    cats = encode_aboutness("cats", D=D)
    dog = encode_aboutness("dog", D=D)
    near = _sim(cat, cats)
    control = _sim(cat, dog)
    assert near > 0.5, f"cat/cats should carry morphology, got {near}"
    assert control < 0.35, f"cat/dog should be ~floor, got {control}"
    assert near > control + 0.2, (
        f"byteglyph must be structure-bearing: cat/cats {near} must exceed "
        f"cat/dog {control} by a clear margin (F1260)")


def test_f1260_address_dual_is_not_structure_bearing():
    """The token_mode='address' dual is the high-diffusion ADDRESSED regime — it
    is deliberately NOT structure-bearing, so cat/cats collapses onto the
    cat/dog floor. This pins WHY byteglyph is the default."""
    D = 4096
    cat = encode_aboutness("cat", D=D, token_mode="address")
    cats = encode_aboutness("cats", D=D, token_mode="address")
    dog = encode_aboutness("dog", D=D, token_mode="address")
    near = _sim(cat, cats)
    control = _sim(cat, dog)
    assert near < 0.35 and control < 0.35, (
        f"address regime should floor BOTH: cat/cats {near}, cat/dog {control}")
    assert abs(near - control) < 0.12, (
        "address regime must NOT distinguish morphology (no structure)")


# ── mechanics ───────────────────────────────────────────────────────────────

def test_deterministic():
    D = 2048
    a = encode_aboutness("hash bytes with sha256", D=D)
    b = encode_aboutness("hash bytes with sha256", D=D)
    assert a.tobytes() == b.tobytes()


def test_returns_hv_of_dimension_D():
    v = encode_aboutness("the magnetic laplacian", D=1024)
    assert len(v) == 1024


def test_df_gate_drops_catalog_wide_tokens():
    """A token present in EVERY document is a function-word; the gate must drop
    it, so a query made only of such tokens grounds no better than an empty
    query, while a distinctive token still discriminates."""
    D = 2048
    # 'the' in every doc (df = n_docs -> gated out); 'sha256' rare (kept).
    docs = [["the", "sha256", "bytes"], ["the", "gcd"], ["the", "factor"],
            ["the", "laplacian"]]
    df, n = _doc_frequencies(docs)
    assert df["the"] == n              # catalog-wide
    assert df["sha256"] == 1           # distinctive
    # Encoding two DIFFERENT texts that share only the gated 'the' must NOT be
    # forced similar by it: with the gate, 'the sha256' and 'the gcd' keep their
    # distinctive tokens and stay distinguishable.
    a = encode_aboutness("the sha256", D=D, df=df, n_docs=n)
    b = encode_aboutness("the gcd", D=D, df=df, n_docs=n)
    assert _sim(a, b) < 0.6, "the gated function-word must not force similarity"


def test_name_weighting_lifts_the_named_op():
    """Encoding with name=<op leaf> weights the identity tokens; a query that
    NAMES the op should rank the name-carrying doc above a doc that only
    MENTIONS the term in its description."""
    D = 4096
    df, n = _doc_frequencies([
        ["klein4", "similarity"], ["klein4", "bundle"],
        ["compute", "the", "distance"], ["a", "vector", "similarity", "measure"],
    ])
    named = encode_aboutness("majority vote", D=D, df=df, n_docs=n,
                             name="klein4_bundle")
    unnamed = encode_aboutness("majority vote over a klein4 bundle superposition",
                               D=D, df=df, n_docs=n)
    q = encode_aboutness("klein4 bundle", D=D, df=df, n_docs=n)
    assert _sim(q, named) > _sim(q, unnamed), (
        "a query that names the op should prefer the name-weighted encoding")


def test_bigrams_are_order_aware():
    """Order-aware bigrams: 'klein gordon' and 'klein 4' share the unigram
    'klein' but must not collapse together — the adjacency bind distinguishes
    them (the F1008 iter-1 collision class)."""
    D = 4096
    a = encode_aboutness("klein gordon", D=D)
    b = encode_aboutness("klein 4", D=D)
    c = encode_aboutness("klein gordon", D=D)
    assert a.tobytes() == c.tobytes()
    assert _sim(a, b) < 0.9, "shared unigram 'klein' must not collapse the pair"


def test_arg_validation():
    with pytest.raises(ValueError):
        encode_aboutness("x", D=0)
    with pytest.raises(ValueError):
        encode_aboutness("x", D=8, token_mode="bogus")
    with pytest.raises(ValueError):
        encode_aboutness("x", D=8, df={"a": 1})   # df without n_docs


def test_tokenizer_letter_digit_split():
    assert _aboutness_tokens("klein-4 SHA256") == ["klein", "4", "sha", "256"]
    # rc416 (`#T1102`): the letter-digit split is now a LETTER<->NUMBER
    # boundary read from the vendored UCD table, not `[a-z][0-9]`, so it fires
    # outside ASCII too. This is the half of the change that ADDS behaviour.
    assert _aboutness_tokens("κ4") == ["κ", "4"]
    assert _aboutness_tokens("语言4") == ["语言", "4"]


def test_tokenizer_single_glyph_noise_is_gated_not_deleted():
    """rc416 (`#T1102`) — the length floor moved from the TOKENIZER to the GATE.

    This test replaces ``_aboutness_tokens("a of the x") == ["of", "the"]``.
    It is not a relaxation: the property that assertion was protecting is
    *"single-letter noise must not carry aboutness"*, and that property is
    re-asserted below, on the instrument that can actually hold it.

    The old assertion could not. A floor of 2 that drops ``a`` and ``x`` also
    drops ``中``, ``国``, ``κ`` and ``π`` — one-glyph WORDS, not noise — which
    is the rc287 word-tokenizer deletion reproduced one layer down. There is no
    floor value that separates them, because "is this one glyph" is not the
    question. "Is this catalog-wide glue" is, and the F768/F984 doc-frequency
    gate answers it FROM the corpus rather than from a hand-tuned constant.
    """
    # The tokenizer now KEEPS them — deleting content at the front door was
    # the defect, and a one-glyph CJK word survives for the same reason.
    assert _aboutness_tokens("a of the x") == ["a", "of", "the", "x"]
    assert _aboutness_tokens("中 国") == ["中", "国"]

    # ...and the GATE drops them, which is the property under protection.
    docs = [_aboutness_tokens(d) for d in (
        "a matrix of x rows", "a vector of x cells", "a graph of x nodes",
        "a fold of x leaves")]
    df, n_docs = _doc_frequencies(docs)
    func = 0.35 * n_docs
    for glue in ("a", "of", "x"):
        assert not _gate_keep(glue, df, func), (
            f"{glue!r} appears in {df.get(glue)}/{n_docs} docs and must be "
            "gated as catalog-wide glue")
    for content in ("matrix", "vector", "graph", "fold"):
        assert _gate_keep(content, df, func), (
            f"{content!r} is aboutness and must survive the gate")


# ── grounding on a controlled synthetic corpus (fast, deterministic) ─────────

def test_grounding_synthetic_corpus():
    """The end-to-end capability on a controlled 6-op corpus: a natural
    utterance retrieves the intended op by nearest aboutness."""
    D = 4096
    corpus = {
        "sha256_bytes": "hash raw bytes with sha256 returning hex",
        "gcd": "greatest common divisor of two integers",
        "factor": "factor an integer into its prime factors",
        "klein4_bundle": "bundle klein-4 hypervectors by majority vote",
        "jacobi_eigvals": "symmetric jacobi eigenvalues of a matrix",
        "best_rational": "best rational approximation with a bounded denominator",
    }
    docs = [_aboutness_tokens(k) + _aboutness_tokens(v) for k, v in corpus.items()]
    df, n = _doc_frequencies(docs)
    index = [(k, encode_aboutness(v, D=D, df=df, n_docs=n, name=k))
             for k, v in corpus.items()]

    def top1(utt):
        q = encode_aboutness(utt, D=D, df=df, n_docs=n)
        return max(index, key=lambda kv: _sim(q, kv[1]))[0]

    assert top1("hash these bytes with sha256") == "sha256_bytes"
    assert top1("compute the greatest common divisor") == "gcd"
    assert top1("factor this number into primes") == "factor"
    assert top1("bundle klein-4 vectors by majority") == "klein4_bundle"


def test_ground_tool_schema_live_smoke():
    """The one-call surface over the LIVE tool_schema retrieves a clear target
    in the top-3 (D kept modest to bound the test's encode cost)."""
    hits = ground_tool_schema("hash these bytes with sha256", D=2048, k=3)
    leaves = [name.split(".")[-1] for name, _ in hits]
    assert "sha256_bytes" in leaves, f"expected sha256_bytes in top-3, got {leaves}"


# ── registration ────────────────────────────────────────────────────────────

def test_registered_in_tool_schema():
    entry = ts.get_tool_schema().lookup("srmech.rbs_lm.encode_aboutness")
    assert entry is not None
    assert entry.category == "rbs_lm"
    assert entry.owner == "srmech"
    assert entry.mcp_callable is True
    assert "aboutness" in entry.summary.lower()


def test_no_abs_or_numpy_in_source():
    """Cascade-honesty: no ALU abs() call, no Counter, no numpy import in the
    CODE (docstring mentions of the banned names are fine — parse the AST so a
    doc that SAYS 'no abs()' doesn't self-trip)."""
    import ast
    import srmech.rbs_lm.grounding as g
    tree = ast.parse(open(g.__file__, encoding="utf-8").read())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "abs" not in names, "no ALU abs() — sign is Class K"
    assert "Counter" not in names and "Counter" not in attrs
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            imported.add(n.module or "")
    assert not any(m.startswith("numpy") for m in imported), "numpy-free"
