"""Spike #147 — User-lexicon outlier signature.

Goal
----
Compute the OUTLIER fingerprint of the user's prompt corpus relative to a
baseline English-prose distribution. This is the "structural image" the
user asked about: which tokens / which spectral components / which
co-occurrence structures are *more characteristic of the user's lexicon*
than generic English.

Methodology
-----------
1. User corpus: all transcript .jsonl files across project folders
   (Spike #147 lexicon-encoder pipeline; same as Deliverable A).
2. Baseline corpus: generic English source. Per the spike spec
   "use a small local cache if available; otherwise document as TODO
   with placeholder baseline" — we use the Python standard library's
   docstring corpus (every public stdlib module's __doc__) as a
   purely-local baseline. It's:
     - LOCAL (no network)
     - ENGLISH PROSE (well-written stdlib docstrings)
     - GENERIC w.r.t. the project (Python documentation, not project
       vocabulary)
   This baseline is documented as a methodological choice with known
   limitations; a richer baseline (Wikipedia / Project Gutenberg)
   is follow-up.
3. Delta operations:
     - Token-level: log-odds-ratio = log((p_user + ε) / (p_baseline + ε))
       This is the well-established lexicon-comparison primitive
       (Monroe et al. 2008; see citation appendix). Ranked top-N gives
       the user's distinguishing tokens.
     - HDC-level: Class M XOR delta (bind operation) — `bind(user_fp,
       baseline_fp)` IS the bitwise symmetric-difference operator on
       BSC hypervectors. Bits set in the delta vector are bits where
       user and baseline disagree.
     - Class L spectral delta: top-N eigvalue differences after
       size-normalisation.
4. Project-canon alignment: compute similarity of user fingerprint
   against project-canon sentences (the cohorts from
   spike147_holographic_projection_test). The user's lexicon SHOULD
   align with project canon at higher similarity than baseline.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from srmech.amsc.hdc import bind, similarity

import spike147_lexicon_encoder as enc
import spike147_holographic_projection_test as hpt


# ----- Baseline: Python stdlib docstrings (local English prose) -------------


def collect_baseline_corpus() -> list[str]:
    """Collect docstrings from every public stdlib module reachable.

    Uses pkgutil to walk the stdlib. Filters to modules whose name
    does not start with '_'. Returns the list of tokens.
    """
    import importlib
    import pkgutil
    import sys

    tokens: list[str] = []
    n_modules = 0
    n_chars = 0

    # Walk built-in module list. Skip modules with import side-effects
    # we don't want printed (e.g. `this` prints the Zen of Python).
    SKIP = {"this", "antigravity", "turtle", "turtledemo", "tkinter", "idlelib"}

    for modname in sorted(sys.stdlib_module_names):
        if modname.startswith("_") or modname in SKIP:
            continue
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        n_modules += 1
        # Collect docstrings: module + top-level callables/classes
        sources = [mod.__doc__ or ""]
        for attr_name in dir(mod):
            if attr_name.startswith("_"):
                continue
            try:
                attr = getattr(mod, attr_name)
                doc = getattr(attr, "__doc__", None)
                if isinstance(doc, str):
                    sources.append(doc)
            except Exception:
                continue
        text = "\n".join(s for s in sources if isinstance(s, str))
        n_chars += len(text)
        tokens.extend(enc.tokenize(text, drop_stopwords=True))

    print(
        f"[baseline] {n_modules} stdlib modules | "
        f"{n_chars} chars | {len(tokens)} tokens",
        file=sys.stderr,
    )
    return tokens


# ----- Token-level log-odds delta (Monroe et al. 2008) ----------------------


def log_odds_delta(
    user_tokens: list[str],
    baseline_tokens: list[str],
    top_k: int = 50,
    min_count: int = 5,
) -> list[dict]:
    """Compute log-odds ratio of token frequencies.

    log_odds(t) = log( (n_user(t)+ε) / (N_user+εV) ) -
                  log( (n_base(t)+ε) / (N_base+εV) )

    where ε = 0.5 (additive smoothing) and V is the union vocabulary size.
    Tokens with count < min_count in BOTH corpora are dropped to
    suppress rare-noise inflation.
    """
    c_u = Counter(user_tokens)
    c_b = Counter(baseline_tokens)
    n_u = sum(c_u.values())
    n_b = sum(c_b.values())
    V = len(set(c_u) | set(c_b))
    epsilon = 0.5

    results = []
    for tok in set(c_u) | set(c_b):
        u, b = c_u.get(tok, 0), c_b.get(tok, 0)
        if u < min_count and b < min_count:
            continue
        # Compute log-odds (no normalisation factor; we want raw ranking)
        p_u = (u + epsilon) / (n_u + epsilon * V)
        p_b = (b + epsilon) / (n_b + epsilon * V)
        lo = math.log(p_u / p_b)
        # Variance-based z (Monroe et al. 2008 informative-Dirichlet prior)
        # Simplified pooled variance:
        var = 1.0 / (u + epsilon) + 1.0 / (b + epsilon)
        z = lo / math.sqrt(var)
        results.append(
            {
                "token": tok,
                "user_count": u,
                "baseline_count": b,
                "log_odds": round(lo, 4),
                "z_score": round(z, 3),
            }
        )

    results.sort(key=lambda r: r["log_odds"], reverse=True)
    user_top = results[:top_k]
    baseline_top = list(reversed(results[-top_k:]))
    return user_top, baseline_top


# ----- HDC delta (Class M bind = bitwise XOR / symmetric difference) --------


def hdc_delta(user_fp: bytes, baseline_fp: bytes) -> bytes:
    """Class M bind = bitwise XOR. Bit-1 in delta = bits where corpora disagree."""
    return bind(user_fp, baseline_fp)


def bit_density(fp: bytes) -> float:
    """Fraction of bits set in fp."""
    n_ones = sum(bin(b).count("1") for b in fp)
    return n_ones / (8.0 * len(fp))


# ----- Class L spectral delta ----------------------------------------------


def spectral_delta(user_eigs: list[float], baseline_eigs: list[float]) -> dict:
    """Compare top-N eigvalue spectra after frequency-normalisation.

    Eigenvalues are size-normalised by dividing by the largest eigvalue
    of each spectrum (max-normalisation; preserves shape).
    """
    u = np.array(user_eigs)
    b = np.array(baseline_eigs)
    if u.size == 0 or b.size == 0:
        return {"ok": False, "reason": "empty-spectrum"}
    u_norm = u / u.max() if u.max() > 0 else u
    b_norm = b / b.max() if b.max() > 0 else b
    n = min(len(u_norm), len(b_norm))
    diff = u_norm[:n] - b_norm[:n]
    return {
        "ok": True,
        "n": int(n),
        "delta_mean": float(diff.mean()),
        "delta_max": float(diff.max()),
        "delta_min": float(diff.min()),
        "delta_l2": float(np.linalg.norm(diff)),
        "delta_top_5": [float(x) for x in diff[:5]],
    }


# ----- Project-canon alignment ---------------------------------------------


def alignment_to_project_canon(
    user_fp_bytes: bytes,
    user_tokens_sample: list[str],
    baseline_fp_bytes: bytes,
) -> dict:
    """Measure similarity of user fingerprint to project-canon sentences.

    Pulls the 40 paraphrase sentences from the holographic-projection
    test (10 cohorts × 4 sentences). For each, encode bag and compute
    bag-similarity against the user and baseline fingerprints.
    Predicts: user mean similarity > baseline mean similarity (user
    lexicon aligns with project canon).
    """
    canon_sentences: list[tuple[str, str]] = []
    for cohort, sentences in hpt.COHORTS.items():
        for s in sentences:
            canon_sentences.append((cohort, s))

    user_sims = []
    baseline_sims = []
    per_canon = []
    for cohort, s in canon_sentences:
        toks = enc.tokenize(s, drop_stopwords=True)
        canon_fp = enc.encode_bag(toks)
        u_sim = similarity(user_fp_bytes, canon_fp)
        b_sim = similarity(baseline_fp_bytes, canon_fp)
        user_sims.append(u_sim)
        baseline_sims.append(b_sim)
        per_canon.append(
            {
                "cohort": cohort,
                "sentence": s,
                "user_sim": round(u_sim, 4),
                "baseline_sim": round(b_sim, 4),
                "user_minus_baseline": round(u_sim - b_sim, 4),
            }
        )

    return {
        "n_canon_sentences": len(canon_sentences),
        "user_mean_sim": round(float(np.mean(user_sims)), 4),
        "baseline_mean_sim": round(float(np.mean(baseline_sims)), 4),
        "user_minus_baseline_mean": round(
            float(np.mean(user_sims) - np.mean(baseline_sims)), 4
        ),
        "alignment_verdict": (
            "USER-LEXICON-ALIGNS-WITH-PROJECT-CANON"
            if float(np.mean(user_sims)) > float(np.mean(baseline_sims)) + 0.05
            else "USER-LEXICON-CANON-ALIGNMENT-MARGINAL"
        ),
        "per_canon": per_canon,
    }


# ----- Main -----------------------------------------------------------------


def main() -> int:
    print("[outlier] collecting user corpus", file=sys.stderr)
    transcript_dirs = [
        Path("C:/Users/sckir/.claude/projects/D--GitHub-mlehaptics"),
        Path(
            "C:/Users/sckir/.claude/projects/D--GitHub-mlehaptics-docs-srmech--claude-worktrees-practical-booth-75e9b9"
        ),
        Path(
            "C:/Users/sckir/.claude/projects/D--GitHub-mlehaptics-docs-antikythera-maths--claude-worktrees-funny-wozniak-569530"
        ),
    ]
    jsonl_paths: list[Path] = []
    for d in transcript_dirs:
        if d.exists():
            jsonl_paths.extend(sorted(d.glob("*.jsonl")))
    user_tokens = enc.collect_user_corpus(jsonl_paths, drop_stopwords=True)

    print("[outlier] collecting baseline corpus (stdlib docstrings)", file=sys.stderr)
    baseline_tokens = collect_baseline_corpus()

    # Token-level log-odds delta
    print("[outlier] computing log-odds delta", file=sys.stderr)
    user_top, baseline_top = log_odds_delta(
        user_tokens, baseline_tokens, top_k=50, min_count=5
    )

    # HDC fingerprints
    print("[outlier] computing HDC fingerprints", file=sys.stderr)
    user_bag, _user_seq = enc.fingerprint_bytes(user_tokens, top_vocab=1000)
    baseline_bag, _baseline_seq = enc.fingerprint_bytes(baseline_tokens, top_vocab=1000)
    hdc_xor = hdc_delta(user_bag, baseline_bag)
    direct_sim = similarity(user_bag, baseline_bag)

    # Class L spectral delta — compute both spectra
    print("[outlier] computing Class L spectral delta", file=sys.stderr)
    user_summary = enc.build_fingerprint(user_tokens, top_vocab=1000)
    baseline_summary = enc.build_fingerprint(baseline_tokens, top_vocab=1000)
    sp_delta = spectral_delta(
        user_summary["top_k_eigvalues"], baseline_summary["top_k_eigvalues"]
    )

    # Project-canon alignment
    print("[outlier] computing project-canon alignment", file=sys.stderr)
    alignment = alignment_to_project_canon(user_bag, user_tokens[:1000], baseline_bag)

    # Write NDJSON
    out_path = (
        Path(__file__).parent / "spike147_user_lexicon_outlier_signature.ndjson"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "kind": "summary",
                    "spike": "147",
                    "deliverable": "D-user-lexicon-outlier-signature",
                    "n_user_tokens": len(user_tokens),
                    "n_baseline_tokens": len(baseline_tokens),
                    "user_bag_sha256": hashlib.sha256(user_bag).hexdigest(),
                    "baseline_bag_sha256": hashlib.sha256(baseline_bag).hexdigest(),
                    "hdc_xor_delta_sha256": hashlib.sha256(hdc_xor).hexdigest(),
                    "hdc_xor_bit_density": round(bit_density(hdc_xor), 4),
                    "user_bag_bit_density": round(bit_density(user_bag), 4),
                    "baseline_bag_bit_density": round(bit_density(baseline_bag), 4),
                    "direct_bag_similarity_user_vs_baseline": round(direct_sim, 4),
                    "spectral_delta": sp_delta,
                    "alignment_to_project_canon": {
                        k: v for k, v in alignment.items() if k != "per_canon"
                    },
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "kind": "top_user_tokens",
                    "description": "Tokens characteristic of USER corpus vs baseline (log-odds ranked)",
                    "tokens": user_top,
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "kind": "top_baseline_tokens",
                    "description": "Tokens characteristic of BASELINE corpus (anti-user, ranking floor)",
                    "tokens": baseline_top,
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "kind": "project_canon_alignment_detail",
                    "per_canon": alignment["per_canon"],
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "kind": "summary_stats",
                    "user_summary": {
                        k: v
                        for k, v in user_summary.items()
                        if k
                        in (
                            "n_tokens_raw",
                            "n_unique_tokens",
                            "n_vocab_kept",
                            "n_edges",
                            "top_20_tokens",
                        )
                    },
                    "baseline_summary": {
                        k: v
                        for k, v in baseline_summary.items()
                        if k
                        in (
                            "n_tokens_raw",
                            "n_unique_tokens",
                            "n_vocab_kept",
                            "n_edges",
                            "top_20_tokens",
                        )
                    },
                }
            )
            + "\n"
        )

    print(f"[ok] wrote {out_path}", file=sys.stderr)
    print(
        f"[direct sim user-vs-baseline bag] {round(direct_sim, 4)}", file=sys.stderr
    )
    print(
        f"[canon alignment] {alignment['alignment_verdict']} "
        f"user_sim={alignment['user_mean_sim']} baseline_sim={alignment['baseline_mean_sim']}",
        file=sys.stderr,
    )
    print("[outlier top user tokens]", file=sys.stderr)
    for t in user_top[:15]:
        print(
            f"  {t['log_odds']:>+7.3f}  {t['token']:<25} (user={t['user_count']} base={t['baseline_count']})",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
