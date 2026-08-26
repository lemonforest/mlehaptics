#!/usr/bin/env python3
"""R-RBS-LM-250 — BEGIN the extended-research arc: spectrally test the MFO finding
'true vs false statements are structurally different' on OUR OWN worker-subagent data.

The twin-research workflow (F248; research-twin) produces, as a byproduct of its adversarial
compare step, MATCHED true/false statement pairs — a FALSE statement the workers emitted
(hallucinated attribution / over-claim / factual error) and its TRUE correction. This script
treats those as a labeled corpus and computes each statement's srmech-native Class-L spectral
signature (F172: the co-occurrence Laplacian eigenspectrum), then asks WITHIN each matched pair
whether the false version's spectral shape differs from the true version's — the MFO claim, now
testable at scale on data we generate ourselves.

DISCIPLINE: srmech-native (dense_laplacian 2-tuples+weights; jacobi_eigvals; sha256_bytes; NO
hashlib/Counter/np.linalg.eig/abs). Pre-STATED NULL (reachable, EXPECTED at this N): 'true and
false statements do NOT differ spectrally — the per-pair feature deltas have no consistent sign.'
HONEST N: this seed corpus is SMALL (the session's caught pairs); the instrument + the
accumulation (every twin run appends its caught pairs) is the deliverable — the powered test
awaits corpus growth. Tier: DEMONSTRATED for the measured spectra; the MFO structural-difference
claim is the prior finding under FALSIFICATION (no leaning). Anchor: user_stance_true_vs_false_
statements_structurally_different. Defensive scope; CAD-ban.
"""
import json, re
import numpy as np
from srmech.amsc import laplacian
from srmech.amsc.format import sha256_bytes

# --- matched (false, true) pairs CAUGHT by this session's workers/verification ------------------
# each: the FALSE statement a worker emitted + its TRUE correction + which finding caught it.
PAIRS = [
 {"caught_by": "F248 sonnet false-attribution #1",
  "false": "The Cassiopea sleep paper is by Nath Bedbrook Abrams Basinger Bhatt Bhattacharyya and Bhaskaran 2017 Current Biology",
  "true":  "The Cassiopea sleep paper is by Nath Bedbrook Abrams Basinger Bois Prober Sternberg Gradinaru and Goentoro 2017 Current Biology"},
 {"caught_by": "F248 sonnet false-attribution #2",
  "false": "The DYSCALCULIA Venus flytrap mutant paper is by Suda Mano Toyota 2023 Current Biology pages 502 to 512",
  "true":  "The DYSCALCULIA Venus flytrap mutant paper is by Iosip and colleagues 2023 Current Biology pages 589 to 596"},
 {"caught_by": "F240b citation cross",
  "false": "The Micrixalus saxicola foot-flagging playback quote comes from the Current Science paper indexed at JSTOR 24099756",
  "true":  "The Micrixalus saxicola foot-flagging playback quote comes from the Behavioral Ecology and Sociobiology paper doi 10.1007 s00265 013 1489 6"},
 {"caught_by": "F121b cnidarian over-claim",
  "false": "The box jellyfish swims using four functional central pattern generator pacemakers",
  "true":  "The box jellyfish has four rhopalia anatomically but its swim dynamics fit two functional pacemakers"},
 {"caught_by": "F248 sonnet unification over-claim",
  "false": "Storage equals sculpt the attractor recurs across every substrate regardless of molecular implementation",
  "true":  "The sculpt the attractor description reads across the media only as a lens not a demonstrated common physical mechanism"},
 {"caught_by": "F242c notation confound (corrected)",
  "false": "The prose renders carry higher round trip structural loss than the structured renders",
  "true":  "After notation normalization the structured renders carry higher loss than the prose renders as creation exceeds echo"},
 # --- batch grow +8: caught (false, true) pairs from the F251/F252/F240c twin runs (all citation/attribution-stratum) ---
 {"caught_by": "F251 opus Aplysia companion mis-attribution",
  "false": "The commentary An Emerging Role for RNA in a Memory Like Behavioral Effect in Aplysia is a companion authored by the Glanzman lab team Bedecarrats Chen Pearce Cai Glanzman",
  "true":  "The commentary An Emerging Role for RNA in a Memory Like Behavioral Effect in Aplysia is a single author piece by Rosalind Carney distinct from the Bedecarrats Glanzman transfer paper"},
 {"caught_by": "F251 sonnet Beisson PMID slip",
  "false": "The Beisson and Sonneborn 1965 cortical inheritance paper has PubMed identifier 14324527",
  "true":  "The Beisson and Sonneborn 1965 cortical inheritance paper has PubMed identifier 14294056 because 14324527 indexes a different chlorophyll optical rotatory dispersion paper"},
 {"caught_by": "F251 sonnet Biomolecules year slip",
  "false": "The Retention and Distribution of Dopamine Dependent Reward Memory in Regenerating Planaria article was published in year 2025",
  "true":  "The Retention and Distribution of Dopamine Dependent Reward Memory in Regenerating Planaria article is volume 16 published in year 2026"},
 {"caught_by": "F252 opus Bielecki DOI slip",
  "false": "The primary Bielecki 2023 box jellyfish associative learning paper has digital object identifier 10.1016 cub 2023 08 020",
  "true":  "The primary Bielecki 2023 box jellyfish associative learning paper has digital object identifier 10.1016 cub 2023 08 056 while 08 025 indexes the commentary"},
 {"caught_by": "F252 sonnet PMC malformed identifier",
  "false": "The Pascual Torner 2022 immortal jellyfish genome paper has PubMed Central identifier PMC 36037356",
  "true":  "The Pascual Torner 2022 immortal jellyfish genome paper has PubMed Central identifier PMC 9459311 because 36037356 is the PubMed identifier not a PubMed Central identifier"},
 {"caught_by": "F240c sonnet Camponotus mus author slip",
  "false": "The Camponotus mus antennation encodes colony needs paper is by Josens and Roces published in year 2000",
  "true":  "The Camponotus mus antennation encodes colony needs paper is by McCabe Farina and Josens published in Insectes Sociaux in year 2006"},
 {"caught_by": "F240c opus Camponotus mus lineage slip",
  "false": "The Camponotus mus antennation encodes colony needs paper is from the De Marco and Farina lineage",
  "true":  "The Camponotus mus antennation encodes colony needs paper is by McCabe Farina and Josens 2006 and De Marco is not an author of it"},
 {"caught_by": "F240c sonnet Schultheiss species slip",
  "false": "The Follower ants in a tandem pair are not always naive paper studies the species Temnothorax",
  "true":  "The Follower ants in a tandem pair are not always naive paper by Schultheiss Raderschall and Narendra 2015 studies the species Camponotus consobrinus"},
]

STOP = {"the","a","an","of","is","by","and","at","to","its","than","as","not","comes","from","using","carry","equals"}

def signature(text):
    """srmech-native Class-L spectral signature of a statement (F172): token co-occurrence
    Laplacian (adjacent + window-2) -> jacobi_eigvals -> shape features."""
    toks = [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]
    vocab = sorted(set(toks)); idx = {t: i for i, t in enumerate(vocab)}; n = len(vocab)
    if n < 3:
        return None
    w = {}
    seq = [idx[t] for t in toks]
    for d in (1, 2):                                   # adjacency + window-2 co-occurrence
        for a, b in zip(seq, seq[d:]):
            if a != b:
                k = (min(a, b), max(a, b)); w[k] = w.get(k, 0.0) + 1.0
    edges = list(w.keys()); weights = [w[e] for e in edges]
    L = laplacian.dense_laplacian(n, edges, weights)
    spec = sorted(float(x) for x in laplacian.jacobi_eigvals(L))
    nz = [x for x in spec if x > 1e-9]
    fiedler = nz[0] if nz else 0.0                     # algebraic connectivity
    lam_max = spec[-1]
    mean_nz = sum(nz) / len(nz) if nz else 0.0
    return {"n_nodes": n, "n_edges": len(edges), "fiedler": fiedler,
            "lambda_max": lam_max, "mean_nonzero": mean_nz,
            "spread_ratio": (lam_max / fiedler) if fiedler > 1e-9 else 0.0,
            "spectrum": [round(x, 4) for x in spec]}

def main():
    rows, deltas = [], {"fiedler": [], "spread_ratio": [], "mean_nonzero": []}
    for p in PAIRS:
        sf, st = signature(p["false"]), signature(p["true"])
        if not sf or not st:
            continue
        d = {k: round(sf[k] - st[k], 4) for k in deltas}
        for k in deltas:
            deltas[k].append(sf[k] - st[k])
        rows.append({"caught_by": p["caught_by"], "false_sig": sf, "true_sig": st, "false_minus_true": d})
    # exploratory sign-consistency per feature (is there a CONSISTENT direction false-vs-true?)
    def sign_consistency(xs):
        pos = sum(1 for x in xs if x > 1e-9); neg = sum(1 for x in xs if x < -1e-9)
        return {"n": len(xs), "pos": pos, "neg": neg,
                "consistent": (pos == len(xs) or neg == len(xs)) and len(xs) >= 5,
                "mean_delta": round(sum(xs) / len(xs), 4) if xs else 0.0}
    # length/elaboration CONFOUND diagnostic (F242c-style artifact guard): if the LONGER statement
    # systematically has the lower Fiedler, an observed false-vs-true Fiedler lean may be a LENGTH
    # artifact (true corrections tend to be longer/more-elaborated), NOT a truth-value signal. The
    # product (n_false - n_true) * (fiedler_false - fiedler_true) < 0 means longer<->lower-Fiedler.
    inv = sum(1 for r in rows
              if (r["false_sig"]["n_nodes"] - r["true_sig"]["n_nodes"]) * r["false_minus_true"]["fiedler"] < 0)
    true_longer = sum(1 for r in rows if r["true_sig"]["n_nodes"] > r["false_sig"]["n_nodes"])
    n = len(rows)
    lc = {"true_longer_than_false": "%d/%d" % (true_longer, n),
          "longer_stmt_has_lower_fiedler": "%d/%d" % (inv, n),
          "interpretation": ("LENGTH-CONFOUNDED: the false-vs-true Fiedler/spread lean tracks statement "
                             "LENGTH, not truth-value (true corrections are systematically longer/more-"
                             "elaborated); the corpus MUST be length/elaboration-matched before the MFO "
                             "claim can be tested." if (n and inv >= n - 1 and true_longer >= n - 1)
                             else "no dominant length confound detected at this N")}
    summary = {
        "n_pairs": len(rows),
        "length_confound": lc,
        "feature_sign_consistency": {k: sign_consistency(v) for k, v in deltas.items()},
        "PRE_STATED_NULL": "true and false statements do NOT differ spectrally (no consistent-sign per-pair feature delta)",
        "VERDICT": None,  # filled below
        "honest_N": ("SEED corpus N=%d matched pairs — UNDER-POWERED; this is the instrument + the "
                     "accumulation start, NOT a powered test. Every research-twin run appends its "
                     "caught false/true pairs; re-run as N grows." % len(rows)),
        "rows": rows,
    }
    any_consistent = any(summary["feature_sign_consistency"][k]["consistent"] for k in deltas)
    summary["VERDICT"] = (
        "EXPLORATORY SIGNAL: at least one spectral feature has a consistent sign across all %d pairs "
        "(suggestive of the MFO true-vs-false structural difference; needs N growth to power)." % len(rows)
        if any_consistent else
        "NULL (pre-stated, EXPECTED at this N): no spectral feature separates true from false with a "
        "consistent sign across the seed pairs. The MFO claim is NEITHER supported NOR refuted here — "
        "N=%d is too small; the instrument + accumulation is the deliverable, the powered falsification "
        "awaits corpus growth across twin runs." % len(rows))
    if lc["interpretation"].startswith("LENGTH-CONFOUNDED"):
        summary["VERDICT"] += ("  ** CONFOUND OVERRIDES THE 'small-N' READING: " + lc["interpretation"] +
            " The N=%d 13/14-style Fiedler/spread lean IS this length artifact, NOT a truth-value signal; "
            "growing N will NOT help until the corpus is length/elaboration-matched (and de-stratified "
            "from the current attribution-correction heavy mix). **" % len(rows))
    summary["response_sha256"] = sha256_bytes(
        json.dumps({k: v for k, v in summary.items() if k != "VERDICT"}, sort_keys=True, default=str).encode())
    return summary

if __name__ == "__main__":
    print(json.dumps(main(), indent=2, default=str))
