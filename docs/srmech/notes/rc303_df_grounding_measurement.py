"""rc303 (§112 / task #941) — computational-provenance generator for the
df-gated aboutness grounding encoder.

Runs the utterance->tool retrieval over the LIVE srmech tool_schema and reports
top-1/top-3 for:

  baseline_encode_sentence_l3_byteglyph : the SHIPPED encoder (default byteglyph)
  baseline_encode_sentence_l3_wordhash  : the SHIPPED encoder (seed wordhash dual)
  encode_aboutness_byteglyph            : the NEW rc303 op (default; STRUCTURE-BEARING)
  encode_aboutness_address              : the NEW rc303 op (F1008 orthogonal dual)

Plus the F1260 discriminant (cat/cats near-pair vs cat/dog control) per token
backend of the new op. The eval is an 18-utterance HAND-AUTHORED input harness
(test INPUTS, not stored content — the stored content is the real tool_schema),
identical to the F1008 (SIONA-INFER-2, research/rbs-lm-rolling-2 PR #687) set so
the numbers are directly comparable to the F1008 78%/83% baseline (measured over
347 tools then; the schema is 477 tools now and one former target, klein4_random,
is no longer in the schema = an automatic miss for every encoder).

Writes NDJSON to rc303_df_grounding_measurement.ndjson beside this file.
Run (numpy-absent WSL): PYTHONPATH=python python3 docs/srmech/notes/rc303_df_grounding_measurement.py
numpy-free; no abs()/Counter/bag.

Provenance note: the COMMITTED reference NDJSON was generated over the rc302
BASELINE schema (n_tools=477 — before this rc registered its own
encode_aboutness ToolEntry), so the 18 utterances ground against the
pre-existing catalog and the op-under-test is not in its own retrieval index.
Re-running this script post-merge grounds against the live schema (478, the new
op included); the grounding top-1 for the 18 pre-existing targets is unaffected
(the new op is not one of them), so the 72.2% reproduces.

"""
import json
import os
import sys

from srmech.amsc import tool_schema as ts, hdc
from srmech.rbs_lm import encode_aboutness, encode_sentence_l3
# tokenizer + doc-frequency gate are PRIVATE glue (kept off the classified public
# surface — see grounding.py); a provenance script may reach them directly.
from srmech.rbs_lm.grounding import (
    _aboutness_tokens as aboutness_tokens,
    _doc_frequencies as doc_frequencies,
)

D = 8192
HEX = 16

# 18 hand-authored (utterance -> intended tool leaf) paraphrases; the F1008 set.
EVAL = [
    ("hash these bytes with sha256", "sha256_bytes"),
    ("hash many messages at once with simd", "sha256_batch"),
    ("compute the greatest common divisor of two integers", "gcd"),
    ("best rational approximation with a bounded denominator", "best_rational"),
    ("factor this number into primes", "factor"),
    ("the magnetic laplacian of a directed graph", "magnetic_laplacian"),
    ("signed laplacian with positive and negative edges", "signed_laplacian"),
    ("symmetric jacobi eigenvalues of a matrix", "jacobi_eigvals"),
    ("hermitian eigendecomposition of a complex matrix", "hermitian_eigendecompose"),
    ("the fiedler vector for graph bisection", "fiedler_vector"),
    ("bundle these klein-4 hypervectors by majority", "klein4_bundle"),
    ("recover a bound value from a klein-4 bundle", "klein4_unbundle"),
    ("similarity between two klein-4 vectors", "klein4_similarity"),
    ("generate a random klein-4 hypervector", "klein4_random"),
    ("cyclic bit rotation of a hypervector", "permute"),
    ("weighted co-occurrence graph from documents", "cooccurrence_edges"),
    ("three-fold spectral eigenvector grouping", "three_fold_eigvec_groups"),
    ("polar hypervector with minus one zero and plus one", "polar_random"),
]


def _fl(x):
    return x.as_float() if hasattr(x, "as_float") else float(x)


def _sim(a, b):
    return _fl(hdc.klein4_similarity(a, b))


def _retrieve_factory(index):
    def retrieve(qvec, k=3):
        return [n for _, n in sorted(((_sim(qvec, v), n) for n, v in index),
                                     reverse=True)[:k]]
    return retrieve


def measure(label, encode_tool, encode_query, tools):
    index = [(t.name, encode_tool(t)) for t in tools]
    retrieve = _retrieve_factory(index)
    top1 = top3 = 0
    rows = []
    for utt, want in EVAL:
        got = [g.split(".")[-1] for g in retrieve(encode_query(utt), 3)]
        h1 = got[0] == want
        h3 = want in got
        top1 += h1
        top3 += h3
        rows.append({"utterance": utt, "want": want, "got": got,
                     "top1": bool(h1), "top3": bool(h3)})
    return {"encoder": label, "n": len(EVAL), "top1": top1, "top3": top3,
            "top1_pct": round(100 * top1 / len(EVAL), 1),
            "top3_pct": round(100 * top3 / len(EVAL), 1), "rows": rows}


def main():
    tools = ts.get_tool_schema().tools
    NT = len(tools)
    short = {t.name.split(".")[-1] for t in tools}
    missing = sorted({w for _, w in EVAL if w not in short})

    # doc-frequency gate over the live catalog (name-leaf + summary per tool)
    docs = [aboutness_tokens(t.name.split(".")[-1]) + aboutness_tokens(t.summary)
            for t in tools]
    df, n_docs = doc_frequencies(docs)

    def leaf(t):
        return t.name.split(".")[-1]

    encoders = {
        "baseline_encode_sentence_l3_byteglyph": (
            lambda t: encode_sentence_l3(aboutness_tokens(leaf(t)) + aboutness_tokens(t.summary) or ["_"],
                                         D=D, hex_chars=HEX, enc_mode="byteglyph"),
            lambda u: encode_sentence_l3(aboutness_tokens(u) or ["_"],
                                         D=D, hex_chars=HEX, enc_mode="byteglyph"),
        ),
        "baseline_encode_sentence_l3_wordhash": (
            lambda t: encode_sentence_l3(aboutness_tokens(leaf(t)) + aboutness_tokens(t.summary) or ["_"],
                                         D=D, hex_chars=HEX, enc_mode="wordhash"),
            lambda u: encode_sentence_l3(aboutness_tokens(u) or ["_"],
                                         D=D, hex_chars=HEX, enc_mode="wordhash"),
        ),
        "encode_aboutness_byteglyph": (
            lambda t: encode_aboutness(t.summary, D=D, df=df, n_docs=n_docs,
                                       name=leaf(t), token_mode="byteglyph"),
            lambda u: encode_aboutness(u, D=D, df=df, n_docs=n_docs,
                                       token_mode="byteglyph"),
        ),
        "encode_aboutness_address": (
            lambda t: encode_aboutness(t.summary, D=D, df=df, n_docs=n_docs,
                                       name=leaf(t), token_mode="address"),
            lambda u: encode_aboutness(u, D=D, df=df, n_docs=n_docs,
                                       token_mode="address"),
        ),
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "rc303_df_grounding_measurement.ndjson")
    records = []
    header = {"record": "meta", "srmech_version": ts.get_tool_schema().srmech_version,
              "n_tools": NT, "D": D, "eval_n": len(EVAL),
              "eval_targets_missing_from_schema": missing,
              "note": "F1008 eval set; klein4_random target absent from schema = auto-miss for all."}
    records.append(header)
    print("META", json.dumps(header))

    for label, (et, eq) in encoders.items():
        res = measure(label, et, eq, tools)
        rec = {"record": "grounding", **{k: res[k] for k in
               ("encoder", "n", "top1", "top3", "top1_pct", "top3_pct")}}
        records.append({"record": "grounding_detail", "encoder": label, "rows": res["rows"]})
        records.append(rec)
        print("GROUND %-40s top-1 %2d/%d = %4.1f%%   top-3 %2d/%d = %4.1f%%"
              % (label, res["top1"], res["n"], res["top1_pct"],
                 res["top3"], res["n"], res["top3_pct"]))

    # F1260 discriminant on the NEW op, per token backend.
    pairs = [("cat", "cats"), ("walk", "walked"), ("nation", "national"), ("cat", "dog")]
    for mode in ("byteglyph", "address"):
        disc = {}
        for a, b in pairs:
            va = encode_aboutness(a, D=D, token_mode=mode)
            vb = encode_aboutness(b, D=D, token_mode=mode)
            disc["%s/%s" % (a, b)] = round(_sim(va, vb), 4)
        near = disc["cat/cats"]
        ctrl = disc["cat/dog"]
        rec = {"record": "f1260_discriminant", "token_mode": mode, "sims": disc,
               "near_gt_control": bool(near > ctrl + 0.1)}
        records.append(rec)
        print("F1260 %-10s %s   near>control=%s"
              % (mode, disc, rec["near_gt_control"]))

    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    print("WROTE", out_path)


if __name__ == "__main__":
    sys.exit(main())
