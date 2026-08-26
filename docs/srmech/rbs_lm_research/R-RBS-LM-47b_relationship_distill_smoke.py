"""R-RBS-LM-47b — Cascade-distill from relationship-form vs text-form corpus.

Tests substrate-form hypothesis: does feeding the byte-mode cascade encoder
a relationship-FORM corpus preserve more retrievable structure than feeding
it raw text?

Per R-RBS-LM-43 two-substrate framework: relationships ARE M1-native
(discrete-cyclic-algebra); proper-noun naming layer is M2-instantiation cost.
This experiment strips the M2 cost from the corpus before encoding.

Pipeline:
  source corpus = v29-Chat-fp16 (3596 bytes; from TinyLlama-1.1B-Chat-v1.0)
    -> Pipeline A: raw text → bytes → encoder → instrument_47b_text.bin
                   (this should match existing v29-Chat-fp16 instrument)
    -> Pipeline B: text → extract_relationships → depersonalize → serialize
                   → bytes → encoder → instrument_47b_rel.bin

Then read-mode rank-retrieval smoke on each. SAME probes for both
(formatted to match each instrument's training shape, derived from the
SAME underlying source text).

Per R-RBS-LM-45 protocol: rank-order is load-bearing; absolute sims in-noise.

Falsification:
  - If Pipeline B preserves MORE retrievable signal → substrate-form helps;
    R-RBS-LM-47 (relationships-on-wire) viable for cascade applications.
  - If Pipeline B preserves LESS → cascade is corpus-shape-invariant
    OR relationship-extraction is too lossy for first-pass extractor.
  - If similar → corpus form doesn't matter at this scale; the cascade
    treats both as byte streams without preference.
"""

import json
import re
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import CONTEXT_WINDOW, D, hierarchical_bundle  # noqa: E402
from rbs_lm_bytes import (  # noqa: E402
    BYTE_VOCAB_SIZE,
    compute_byte_vocab_table,
    encode_observation_bytes,
    text_to_bytes,
)
from rbs_lm_read_mode import (  # noqa: E402
    load_instrument_bytes, phrase_match_retrieval, baseline_random_phrase_sim,
)
from rbs_lm_relationships import (  # noqa: E402
    extract_relationships, serialize_triples, pii_audit,
)


SOURCE_CORPUS = (
    "docs/srmech/rbs_lm_research/"
    "rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.corpus.txt"
)


def distill_from_corpus(corpus_text, stride=8):
    """Byte-mode encode + bundle a corpus text → 1024-byte instrument.

    Same pipeline as encode_bytes_variant_b_generic.py steps 3-5, factored
    to operate on already-generated text (no LLM generation step).
    """
    all_bytes = text_to_bytes(corpus_text)
    vocab_table = compute_byte_vocab_table(D)

    observations = []
    for i in range(0, len(all_bytes) - CONTEXT_WINDOW, stride):
        ctx = all_bytes[i:i + CONTEXT_WINDOW]
        nxt = all_bytes[i + CONTEXT_WINDOW]
        observations.append((ctx, nxt))

    t0 = time.time()
    bindings = [
        encode_observation_bytes(ctx, nxt, vocab_table, D)
        for ctx, nxt in observations
    ]
    enc_t = time.time() - t0

    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bnd_t = time.time() - t0

    return {
        "instrument_bytes": instrument,
        "n_observations": len(observations),
        "n_bytes": len(all_bytes),
        "encode_seconds": round(enc_t, 2),
        "bundle_seconds": round(bnd_t, 2),
    }


def make_phrase_corpus(text, max_phrases=60, min_len=15, max_len=180):
    sentences = re.split(r'[.!?\n]\s*', text)
    out, seen = [], set()
    for s in sentences:
        s = s.strip().rstrip(".")
        if min_len <= len(s) <= max_len and s not in seen:
            out.append(s)
            seen.add(s)
            if len(out) >= max_phrases:
                break
    return out


def make_probes_from_corpus(text, n_probes=20, seed=42):
    rng = np.random.default_rng(seed)
    sentences = [s.strip() for s in re.split(r'[.!?\n]\s*', text)
                 if 20 < len(s.strip()) < 200]
    rng.shuffle(sentences)
    probes = []
    for sent in sentences[:n_probes * 3]:
        words = sent.split()
        if len(words) < 5:
            continue
        n_prefix = min(rng.integers(3, 6), len(words) - 1)
        probe = " ".join(words[:n_prefix])
        probes.append((probe, sent))
        if len(probes) >= n_probes:
            break
    return probes


def rank_stats(rank_results, corpus_size):
    n = len(rank_results)
    found = [r for r in rank_results if r >= 0]
    n_found = len(found)
    if not found:
        return {"n_probes": n, "n_found": 0}
    q_t = max(1, corpus_size // 4)
    d_t = max(1, corpus_size // 10)
    rank_1 = sum(1 for r in found if r == 0)
    top_q = sum(1 for r in found if r < q_t)
    top_d = sum(1 for r in found if r < d_t)
    mean_pct = float(np.mean(found)) / max(corpus_size, 1) * 100
    bins = [0] * 5
    bucket = max(corpus_size // 5, 1)
    for r in found:
        bins[min(r // bucket, 4)] += 1
    expected = n_found / 5
    chi2 = sum(((b - expected) ** 2) / expected for b in bins)
    p_est = ("<0.01" if chi2 > 13.28 else "<0.05" if chi2 > 9.49 else
             "<0.10" if chi2 > 7.78 else ">0.10")
    return {
        "n_probes": n, "n_found": n_found,
        "rank_1_count": rank_1, "rank_1_rate": rank_1 / n,
        "top_quartile_count": top_q, "top_quartile_rate": top_q / n,
        "top_decile_count": top_d, "top_decile_rate": top_d / n,
        "mean_rank_percentile": round(mean_pct, 1),
        "chi2_5bins": round(chi2, 2), "p_estimate": p_est,
        "rank_bins": bins, "rank_array": list(rank_results),
    }


def run_read_smoke(label, instrument_bytes, corpus_phrases, probes, vocab_table):
    """Save instrument to temp; load; run read-mode rank smoke; return stats."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(instrument_bytes)
        tmp = f.name
    try:
        instrument = load_instrument_bytes(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)

    baseline = baseline_random_phrase_sim(corpus_phrases, vocab_table, D, n_samples=200)
    rank_results = []
    for query, expected in probes:
        ranked = phrase_match_retrieval(instrument, query, corpus_phrases, vocab_table, D)
        try:
            rank = next(i for i, (phr, _) in enumerate(ranked) if phr == expected)
        except StopIteration:
            try:
                rank = next(i for i, (phr, _) in enumerate(ranked)
                            if expected[:30] in phr or phr in expected)
            except StopIteration:
                rank = -1
        rank_results.append(rank)
    stats = rank_stats(rank_results, len(corpus_phrases))
    print(f"  [{label}] corpus={len(corpus_phrases)}, probes={len(probes)}")
    print(f"    rank-1={stats.get('rank_1_count', 0)}/{stats['n_probes']} "
          f"({100*stats.get('rank_1_rate', 0):.1f}%), "
          f"top-d={100*stats.get('top_decile_rate', 0):.1f}%, "
          f"top-q={100*stats.get('top_quartile_rate', 0):.1f}%, "
          f"mean={stats.get('mean_rank_percentile', 50.0):.1f}%, "
          f"chi²={stats.get('chi2_5bins', 0):.2f} ({stats.get('p_estimate', '?')})")
    return {"corpus_size": len(corpus_phrases), "n_probes": len(probes),
            "baseline": baseline, "stats": stats}


def main():
    print("=== R-RBS-LM-47b — Cascade distill from relationship-form corpus ===\n")

    # ---- 0. Load source text ----
    src_path = Path(SOURCE_CORPUS)
    if not src_path.exists():
        print(f"  FATAL — source corpus not found: {src_path}")
        sys.exit(1)
    raw_text = src_path.read_text()
    print(f"Source corpus: {src_path.name} ({len(raw_text)} chars / "
          f"{len(raw_text.encode('utf-8'))} bytes)")

    # ---- 1. Extract relationships ----
    print(f"\n=== 1. Extract relationships ===")
    t0 = time.time()
    triples, entity_map = extract_relationships(raw_text, depersonalize=True)
    extract_t = time.time() - t0
    rel_corpus = serialize_triples(triples)
    print(f"  triples: {len(triples)}; entities mapped: {len(entity_map)}")
    print(f"  rel-corpus size: {len(rel_corpus.encode('utf-8'))} bytes "
          f"(vs source {len(raw_text.encode('utf-8'))} bytes)")
    print(f"  extract time: {extract_t:.2f}s")

    # Save the relationship corpus
    rel_corpus_path = src_path.with_name("R-RBS-LM-47b_rel.corpus.txt")
    rel_corpus_path.write_text(rel_corpus)
    print(f"  saved: {rel_corpus_path}")

    # Save entity map (NEVER on the wire; lives locally)
    ent_map_path = src_path.with_name("R-RBS-LM-47b_entity_map.json")
    ent_map_path.write_text(json.dumps(dict(entity_map), indent=2, ensure_ascii=False))
    print(f"  entity map (local-only): {ent_map_path}")

    # ---- 2. PII audit on wire form ----
    print(f"\n=== 2. PII audit on wire form (relationship corpus) ===")
    leaks = pii_audit(rel_corpus)
    print(f"  PII suspects in wire form: {len(leaks)}")
    if leaks:
        print(f"  Suspects (first 10):")
        for s in leaks[:10]:
            print(f"    ⚠ {s!r}")

    # ---- 3. Distill cascade instrument from relationship corpus ----
    print(f"\n=== 3. Distill cascade from relationship corpus ===")
    distill_rel = distill_from_corpus(rel_corpus, stride=8)
    rel_instr_path = src_path.with_name(
        "rbs_lm_instrument_v47b_relationship_form.bin")
    rel_instr_path.write_bytes(distill_rel["instrument_bytes"])
    print(f"  observations: {distill_rel['n_observations']}; "
          f"bytes: {distill_rel['n_bytes']}; "
          f"encode: {distill_rel['encode_seconds']}s; "
          f"bundle: {distill_rel['bundle_seconds']}s")
    print(f"  saved: {rel_instr_path}")

    meta = {
        "partition": "R-RBS-LM-47b",
        "variant": "relationship_form_cascade_distill",
        "source_corpus": SOURCE_CORPUS,
        "source_bytes": len(raw_text.encode("utf-8")),
        "rel_corpus_bytes": len(rel_corpus.encode("utf-8")),
        "n_triples": len(triples),
        "n_entities_mapped": len(entity_map),
        "n_observations": distill_rel["n_observations"],
        "stride": 8,
        "instrument_bytes": len(distill_rel["instrument_bytes"]),
        "D": D,
        "context_window_bytes": CONTEXT_WINDOW,
        "vocab_size": BYTE_VOCAB_SIZE,
        "encode_seconds": distill_rel["encode_seconds"],
        "bundle_seconds": distill_rel["bundle_seconds"],
        "extract_seconds": round(extract_t, 2),
        "pii_audit_suspects_in_wire_form": len(leaks),
        "framework_reading": (
            "R-RBS-LM-47b: cascade-distill from relationship-form corpus. "
            "Per R-RBS-LM-43 two-substrate framework, relationships are "
            "M1-native (discrete-cyclic-algebra); the proper-noun naming "
            "layer is M2-instantiation cost. This instrument tests whether "
            "stripping the M2 cost from the input corpus preserves more "
            "retrievable cascade signal."
        ),
    }
    rel_meta_path = src_path.with_name("rbs_lm_instrument_v47b_relationship_form.meta.json")
    rel_meta_path.write_text(json.dumps(meta, indent=2))
    print(f"  meta: {rel_meta_path}")

    # ---- 4. Read-mode rank smoke ----
    print(f"\n=== 4. Read-mode rank smoke ===\n")
    vocab_table = compute_byte_vocab_table(D)

    # Pipeline A — text-form: use the existing v29-Chat-fp16 instrument
    text_instr_path = src_path.with_suffix(".bin")  # the .bin alongside the corpus
    if not text_instr_path.exists():
        # Fall back: re-distill from raw text
        print(f"  (re-distilling text-form instrument from raw text)")
        distill_text = distill_from_corpus(raw_text, stride=8)
        text_instr_bytes = distill_text["instrument_bytes"]
    else:
        text_instr_bytes = text_instr_path.read_bytes()

    # SHARED probes: derived from raw_text so both pipelines see same content
    print(f"  --- Track 1: probes from RAW TEXT corpus (text-shape) ---")
    text_phrase_corpus = make_phrase_corpus(raw_text, max_phrases=60)
    text_probes = make_probes_from_corpus(raw_text, n_probes=20, seed=42)
    result_text_A = run_read_smoke("text-instr × text-probes", text_instr_bytes,
                                   text_phrase_corpus, text_probes, vocab_table)
    result_rel_A = run_read_smoke("rel-instr × text-probes",
                                  distill_rel["instrument_bytes"],
                                  text_phrase_corpus, text_probes, vocab_table)

    print(f"\n  --- Track 2: probes from RELATIONSHIP corpus (rel-shape) ---")
    rel_phrase_corpus = make_phrase_corpus(rel_corpus, max_phrases=60)
    rel_probes = make_probes_from_corpus(rel_corpus, n_probes=20, seed=42)
    result_text_B = run_read_smoke("text-instr × rel-probes", text_instr_bytes,
                                   rel_phrase_corpus, rel_probes, vocab_table)
    result_rel_B = run_read_smoke("rel-instr × rel-probes",
                                  distill_rel["instrument_bytes"],
                                  rel_phrase_corpus, rel_probes, vocab_table)

    # ---- 5. Summary ----
    print(f"\n\n{'='*72}")
    print(f"=== R-RBS-LM-47b — Substrate-form comparison summary")
    print(f"{'='*72}\n")
    print(f"  {'pipeline':<32s} {'rank-1%':>8s} {'top-d%':>7s} {'top-q%':>7s} "
          f"{'mean%':>7s} {'chi²':>7s} {'p-est':>7s}")
    print(f"  {'-'*32} {'-'*8} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    matrix = [
        ("text-instr × text-probes (A)", result_text_A),
        ("rel-instr  × text-probes (A)", result_rel_A),
        ("text-instr × rel-probes  (B)", result_text_B),
        ("rel-instr  × rel-probes  (B)", result_rel_B),
    ]
    for label, r in matrix:
        s = r["stats"]
        print(f"  {label:<32s} {100*s.get('rank_1_rate', 0):>7.1f}% "
              f"{100*s.get('top_decile_rate', 0):>6.1f}% "
              f"{100*s.get('top_quartile_rate', 0):>6.1f}% "
              f"{s.get('mean_rank_percentile', 50.0):>6.1f}% "
              f"{s.get('chi2_5bins', 0):>7.2f} "
              f"{s.get('p_estimate', '?'):>7s}")

    output = {
        "partition": "R-RBS-LM-47b",
        "meta": meta,
        "results": {
            "text_instr_text_probes": result_text_A,
            "rel_instr_text_probes":  result_rel_A,
            "text_instr_rel_probes":  result_text_B,
            "rel_instr_rel_probes":   result_rel_B,
        },
    }
    out_path = Path("docs/srmech/rbs_lm_research/R-RBS-LM-47b_results.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")

    # ---- 6. Reading ----
    print(f"\n=== Reading ===")
    delta_A = (result_text_A["stats"].get("mean_rank_percentile", 50.0)
               - result_rel_A["stats"].get("mean_rank_percentile", 50.0))
    delta_B = (result_text_B["stats"].get("mean_rank_percentile", 50.0)
               - result_rel_B["stats"].get("mean_rank_percentile", 50.0))
    print(f"  Track A (text-probes): text - rel = {delta_A:+.1f}pp mean percentile")
    print(f"    Negative = text-instr wins;  Positive = rel-instr wins")
    print(f"  Track B (rel-probes):  text - rel = {delta_B:+.1f}pp mean percentile")
    if delta_B > 3:
        print(f"  → On rel-probes, rel-instr WINS. Substrate-form matters.")
    elif delta_B < -3:
        print(f"  → On rel-probes, text-instr WINS. Relationship form is lossy/foreign.")
    else:
        print(f"  → On rel-probes, no material difference (<3pp). Probe alignment dominant.")


if __name__ == "__main__":
    main()
