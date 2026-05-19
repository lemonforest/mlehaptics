"""Spike #147 — Holographic-projection hypothesis test.

Hypothesis (user 2026-05-19):
    The SENTENCE is the 3D_s-spatial projection of a higher-resolution
    structural image. Different word-orderings of the same canonical
    content = different projections of the SAME image. Bag (Class M
    bundle without position-bind) isolates the meaning component;
    sequence (with position-bind) encodes the projection-specific order.

Test design
-----------
Construct 5-10 paraphrase-cohorts. Each cohort has 3-5 sentences
expressing the same canonical project content. For each sentence:
  - encode_bag(tokens) → meaning-fingerprint
  - encode_sequence(tokens) → order-fingerprint
Compute pairwise BSC similarity (in [-1, 1]).

Prediction:
  WITHIN-cohort BAG similarity:   HIGH    (>~ 0.5  for same-meaning content)
  BETWEEN-cohort BAG similarity:  LOW     (<~ 0.2)
  WITHIN-cohort SEQ similarity:   MEDIUM  (>~ 0.1; same tokens, varied order)
  BETWEEN-cohort SEQ similarity:  near 0  (orthogonal HDC vectors)

Verdict:
  HOLOGRAPHIC-PROJECTION-VERIFIED if mean(within-bag) >> mean(between-bag)
  AND the within/between gap is robust (>= 2x).
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

from srmech.amsc.hdc import similarity

import spike147_lexicon_encoder as enc


# ----- Paraphrase cohorts (canonical project content) -----------------------
#
# 10 cohorts × 4 paraphrases each. Each cohort expresses one canonical
# project stance; paraphrases differ in word order / synonyms / register.
# Drawn from real project memory / notebook content.

COHORTS: dict[str, list[str]] = {
    "vocab_14_AN_intact": [
        "the primitive class vocabulary stays at 14 classes A through N",
        "fourteen primitive classes A-N remain intact; no promotion of any candidate to a new class",
        "no new class. dissolve before promote. vocabulary at 14 A-N unchanged",
        "the 14 A-N primitive class vocabulary remains complete and untouched",
    ],
    "kepler_shape_universal": [
        "any system showing kepler-shape spectral content instantiates the pin-slot-gear primitive composition",
        "kepler-equation algebra is pin slot gear primitive composition at any substrate",
        "kepler-shape universally implies the primitive class composition mechanism",
        "the kepler shape identifies pin-slot-gear primitives across substrates",
    ],
    "fiber_spatially_absent": [
        "a fiber over a manifold encodes algebraic content that is spatially absent until projected",
        "fiber bundles store spatially absent algebra; projection makes the algebra visible",
        "the algebraic content lives in the fiber and is spatially absent",
        "fiber-stored algebraic content remains hidden in space until external operation projects it",
    ],
    "time_as_shadow": [
        "time is part of the shadow not the projector; bronze is dimensional deficit not animacy",
        "time-as-dimensional-shadow: clock-time is projected from cascade composition",
        "the temporal dimension is shadow content; the projector is the cascade",
        "time is dimensional shadow; bronze antikythera is dimensional deficit not animacy",
    ],
    "cascade_lives_on_circles": [
        "the cascade lives on circles; class C orientation on class I cyclic produces unit-circle eigenvalues",
        "cascade composition preserves circularity; lorentzian dispersion is a further projection shadow",
        "circles are the substrate of the cascade; hyperbolic shapes are wick-rotation shadows",
        "directed cyclic groups under cascade composition stay on the unit circle",
    ],
    "dark_sector_ring_down_age": [
        "the dark sector represents cosmic ring-down accumulation; the universe is 95 percent old",
        "ring-down fraction defines cosmic age; dark sector is the accumulation of ring-down",
        "universe age is the fraction of cosmic ring-down complete; dark matter and dark energy track this",
        "cosmic ring-down accumulation = dark sector content; 95 percent old at present",
    ],
    "math_doesnt_lie": [
        "math does not lie; investigate anomalies do not paper over discrepancies",
        "anomalies are information; the math always tells truth and we investigate when numbers disagree",
        "math-doesnt-lie discipline: discrepancies signal real structure to investigate",
        "when numbers disagree it is signal not noise; never paper over with framing",
    ],
    "mpm_discipline": [
        "the mathematical provenance method requires closed-form deterministic computation no sgd",
        "mpm discipline: ground-proof against published values no per-particle free parameters",
        "mpm = closed-form deterministic computation grounded in published reference values",
        "ground-proof published values; no stochastic gradient descent; mpm reproducibility floor",
    ],
    "identity_not_implementation": [
        "x IS y not x implements y; burden flips from show mechanism to show non-identity",
        "the identity stance is x is y; implementation framing is the wrong abstraction layer",
        "identity-not-implementation: shadow-stances claim x is y not x implements y",
        "claims of identity flip the burden of proof onto the negation",
    ],
    "ndjson_over_json": [
        "ndjson is one record per line; new results should be ndjson not indented json arrays",
        "prefer ndjson for new results output; toml for descriptor shaped data",
        "ndjson over bloated json: every result record on its own line",
        "new results style outputs land as ndjson one line per record",
    ],
}


def encode_for_cohort(sentences: list[str]) -> list[dict]:
    """Encode each sentence into bag + seq fingerprints."""
    out = []
    for s in sentences:
        toks = enc.tokenize(s, drop_stopwords=True)
        bag_fp = enc.encode_bag(toks)
        seq_fp = enc.encode_sequence(toks)
        out.append(
            {
                "sentence": s,
                "tokens": toks,
                "n_tokens": len(toks),
                "bag_fp": bag_fp,
                "seq_fp": seq_fp,
            }
        )
    return out


def pairwise(records: list[dict], key: str) -> list[float]:
    """All unordered pairs' similarity on records[*][key]."""
    sims = []
    n = len(records)
    for i in range(n):
        for j in range(i + 1, n):
            sims.append(similarity(records[i][key], records[j][key]))
    return sims


def cross_cohort_pairwise(
    cohort_a: list[dict], cohort_b: list[dict], key: str
) -> list[float]:
    """All a×b pair similarities."""
    return [similarity(a[key], b[key]) for a in cohort_a for b in cohort_b]


def stats(xs: list[float]) -> dict:
    """Standard descriptive stats."""
    if not xs:
        return {"n": 0}
    return {
        "n": len(xs),
        "min": round(min(xs), 4),
        "max": round(max(xs), 4),
        "mean": round(statistics.fmean(xs), 4),
        "median": round(statistics.median(xs), 4),
        "stdev": round(statistics.pstdev(xs), 4) if len(xs) > 1 else 0.0,
    }


def main() -> int:
    t0 = time.time()
    print("[hp-test] encoding cohorts", file=sys.stderr)
    encoded: dict[str, list[dict]] = {}
    for name, sentences in COHORTS.items():
        encoded[name] = encode_for_cohort(sentences)

    out_path = Path(__file__).parent / "spike147_holographic_projection_results.ndjson"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    within_bag_all: list[float] = []
    within_seq_all: list[float] = []
    between_bag_all: list[float] = []
    between_seq_all: list[float] = []

    records: list[dict] = []

    # Within-cohort
    for name, recs in encoded.items():
        wb = pairwise(recs, "bag_fp")
        ws = pairwise(recs, "seq_fp")
        within_bag_all.extend(wb)
        within_seq_all.extend(ws)
        records.append(
            {
                "kind": "within_cohort",
                "cohort": name,
                "n_sentences": len(recs),
                "n_pairs": len(wb),
                "token_counts": [r["n_tokens"] for r in recs],
                "bag_similarity": stats(wb),
                "seq_similarity": stats(ws),
                "bag_pairs": [round(x, 4) for x in wb],
                "seq_pairs": [round(x, 4) for x in ws],
            }
        )

    # Between-cohort
    names = list(encoded.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a_name, b_name = names[i], names[j]
            cb = cross_cohort_pairwise(encoded[a_name], encoded[b_name], "bag_fp")
            cs = cross_cohort_pairwise(encoded[a_name], encoded[b_name], "seq_fp")
            between_bag_all.extend(cb)
            between_seq_all.extend(cs)
            records.append(
                {
                    "kind": "between_cohort",
                    "cohort_a": a_name,
                    "cohort_b": b_name,
                    "n_pairs": len(cb),
                    "bag_similarity": stats(cb),
                    "seq_similarity": stats(cs),
                }
            )

    # Aggregate verdict record
    within_bag_stats = stats(within_bag_all)
    between_bag_stats = stats(between_bag_all)
    within_seq_stats = stats(within_seq_all)
    between_seq_stats = stats(between_seq_all)

    bag_ratio = (
        round(within_bag_stats["mean"] / between_bag_stats["mean"], 3)
        if between_bag_stats["mean"] not in (0, 0.0)
        else None
    )
    seq_ratio = (
        round(within_seq_stats["mean"] / between_seq_stats["mean"], 3)
        if between_seq_stats["mean"] not in (0, 0.0)
        else None
    )

    verdict_bag = (
        "HOLOGRAPHIC-PROJECTION-VERIFIED (bag)"
        if (
            within_bag_stats["mean"] > 2 * abs(between_bag_stats["mean"])
            and within_bag_stats["mean"] > 0.1
        )
        else "BAG-SEPARATION-WEAK"
    )
    verdict_seq = (
        "HOLOGRAPHIC-PROJECTION-VERIFIED (seq)"
        if (
            within_seq_stats["mean"] > 2 * abs(between_seq_stats["mean"])
            and within_seq_stats["mean"] > 0.05
        )
        else "SEQ-SEPARATION-WEAK"
    )

    summary = {
        "kind": "verdict",
        "spike": "147",
        "test": "holographic_projection",
        "n_cohorts": len(COHORTS),
        "within_bag": within_bag_stats,
        "between_bag": between_bag_stats,
        "within_seq": within_seq_stats,
        "between_seq": between_seq_stats,
        "bag_ratio_within_over_between": bag_ratio,
        "seq_ratio_within_over_between": seq_ratio,
        "verdict_bag": verdict_bag,
        "verdict_seq": verdict_seq,
        "config": {
            "hdc_bytes": enc.HDC_BYTES,
            "drop_stopwords": True,
            "tokenizer": "regex [A-Za-z][A-Za-z0-9_-]+, len>=2, lowercase",
        },
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    records.insert(0, summary)

    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[ok] wrote {out_path}", file=sys.stderr)
    print(f"[verdict-bag] {verdict_bag}", file=sys.stderr)
    print(f"[verdict-seq] {verdict_seq}", file=sys.stderr)
    print(f"[within-bag mean] {within_bag_stats['mean']}", file=sys.stderr)
    print(f"[between-bag mean] {between_bag_stats['mean']}", file=sys.stderr)
    print(f"[bag ratio w/b] {bag_ratio}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
