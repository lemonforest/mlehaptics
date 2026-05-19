"""Spike #125.1 — Python reference numerical check (Julia parity).

Mirrors `spike125_1_bigram_cascade_detector.jl` algorithmically so we can verify
the logic numerically when Julia is unavailable. Per spike brief: if Julia
isn't installed in WSL2, write the script and document install requirement;
use a Python reference check to validate the algorithm logic (not bit-exact in
Julia, but bit-exact in Python across runs).

Differences from parent Spike #125 (`spike125_empirical_haiku_validation.py`):
1. State vector is BIGRAM-frequency over top-N bigrams (not unigram-frequency).
2. Co-occurrence Laplacian is built over bigram-tokens (nodes = top-N bigrams).
3. State vectors L¹-normalised over the bigram alphabet.
4. Decompose via NumPy eigendecomposition (no srmech.spectral, since we're
   testing the bigram refinement, not the spectral surface API).
5. Adversarial classes are IDENTICAL to parent (citation/value/vocab/shuffle).
6. Cohen's d metric is identical.

Run with:
    cd D:/GitHub/mlehaptics/.claude/worktrees/agent-.../docs/srmech/notes
    python spike125_1_bigram_cascade_detector_pyref.py

Bit-exact reproducibility (Python-side): np.random.default_rng(42) +
sorted dict iteration + deterministic NumPy FP ops.

Anchors:
  - parent Spike #125 (spike125_*)
  - [[feedback_every_doc_edit_faces_falsification]]
  - [[feedback_autonomous_research_followup_authorization]]
"""

from __future__ import annotations

import re
import time
from collections import Counter
from pathlib import Path

import numpy as np


# =====================================================================
# 1. Configuration constants (mirrors Julia driver)
# =====================================================================

ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789 .,()[]+-=*/_<>:; \n\t" + "\"'"
ALPHA64 = ALPHABET[:64]
ALPHA_INDEX = {c: i for i, c in enumerate(ALPHA64)}

N_ALPHA = 64
TOP_N_BIGRAMS = 1000
CHUNK_SIZE = 2000
COOC_WINDOW = 1
HELD_OUT_FRAC = 0.30
RNG_SEED = 42


# =====================================================================
# 2. Corpus load
# =====================================================================

REPO_ROOT = Path(__file__).resolve().parents[3]
MFO_PATH = REPO_ROOT / "docs/antikythera-maths/mfo_spectral_research_notebook.md"
SRMECH_PATH = REPO_ROOT / "docs/srmech/srmech_research_notebook.md"


def load_attested_corpus() -> str:
    parts = []
    for path in (MFO_PATH, SRMECH_PATH):
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def text_to_indices(text: str) -> list[int]:
    return [ALPHA_INDEX[c] for c in text.lower() if c in ALPHA_INDEX]


def indices_to_bigrams(idxs: list[int]) -> list[int]:
    return [idxs[i] * N_ALPHA + idxs[i + 1] for i in range(len(idxs) - 1)]


# =====================================================================
# 3. Top-N bigram alphabet selection
# =====================================================================


def topn_bigrams(corpus: str, topn: int) -> tuple[list[int], dict[int, int]]:
    idxs = text_to_indices(corpus)
    bigrams = indices_to_bigrams(idxs)
    counts = Counter(bigrams)
    # Sort by (-count, token-id) for deterministic ordering.
    pairs = sorted(counts.items(), key=lambda p: (-p[1], p[0]))
    selected = [p[0] for p in pairs[:topn]]
    token_to_slot = {t: i for i, t in enumerate(selected)}
    return selected, token_to_slot


# =====================================================================
# 4. Bigram co-occurrence Laplacian (Hermitian PSD)
# =====================================================================


def bigram_cooc_laplacian(corpus: str,
                          token_to_slot: dict[int, int],
                          n_nodes: int,
                          window: int = COOC_WINDOW) -> np.ndarray:
    idxs = text_to_indices(corpus)
    bigrams = indices_to_bigrams(idxs)
    A = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    nb = len(bigrams)
    for i in range(nb):
        a = bigrams[i]
        sa = token_to_slot.get(a, -1)
        if sa < 0:
            continue
        upper = min(i + window + 1, nb)
        for j in range(i + 1, upper):
            b = bigrams[j]
            sb = token_to_slot.get(b, -1)
            if sb < 0 or sa == sb:
                continue
            A[sa, sb] += 1.0
            A[sb, sa] += 1.0
    deg = A.sum(axis=1)
    L = -A
    np.fill_diagonal(L, deg)
    # Symmetrise against FP drift.
    L = (L + L.T) / 2.0
    return L


# =====================================================================
# 5. Bigram state vectors + spectral projection
# =====================================================================


def chunk_bigram_state(chunk: str,
                       token_to_slot: dict[int, int],
                       n_nodes: int) -> np.ndarray:
    state = np.zeros(n_nodes, dtype=np.float64)
    idxs = text_to_indices(chunk)
    bigrams = indices_to_bigrams(idxs)
    for b in bigrams:
        s = token_to_slot.get(b, -1)
        if s >= 0:
            state[s] += 1.0
    total = state.sum()
    if total > 0:
        state /= total
    return state


def spectral_project(state: np.ndarray, eigvecs: np.ndarray) -> np.ndarray:
    return eigvecs.T @ state


def cosine_real(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# =====================================================================
# 6. Adversarial contrast generators (4 classes + held-out)
# =====================================================================

ARXIV_RE = re.compile(r"arXiv:\s*(?:\d{4}\.\d{4,5}|[a-z\-]+/\d{7})")

VALUE_PATTERNS = [
    (re.compile(r"1/4"), "7/3"),
    (re.compile(r"0\.34439"), "0.91234"),
    (re.compile(r"0\.0104109"), "0.7654321"),
    (re.compile(r"d_geom"), "q_phug"),
    (re.compile(r"A/4"), "B/9"),
    (re.compile(r"7\.69%?"), "31.42%"),
    (re.compile(r"1\.78"), "9.99"),
]

VOCAB_PATTERNS = [
    (re.compile(r"\bClass L\b"), "Class Z"),
    (re.compile(r"\bClass M\b"), "Class Q"),
    (re.compile(r"\bClass K\b"), "Class W"),
    (re.compile(r"\bClass C\b"), "Class Y"),
    (re.compile(r"\bClass I\b"), "Class X"),
    (re.compile(r"\bsrmech\b"), "frobnication"),
    (re.compile(r"\bspectral\b"), "telegnostic"),
    (re.compile(r"\bcascade\b"), "phrenology"),
    (re.compile(r"\bsubstrate\b"), "ectoplasm"),
]


def adv_citation_swap(text: str, rng: np.random.Generator) -> str:
    def _swap(_m):
        yr = int(rng.integers(1990, 2099))
        nm = int(rng.integers(0, 100000))
        return f"arXiv:{yr}.{nm:05d}"
    return ARXIV_RE.sub(_swap, text)


def adv_value_mutation(text: str) -> str:
    for pat, repl in VALUE_PATTERNS:
        text = pat.sub(repl, text)
    return text


def adv_vocab_swap(text: str) -> str:
    for pat, repl in VOCAB_PATTERNS:
        text = pat.sub(repl, text)
    return text


def adv_random_baseline(text: str, rng: np.random.Generator) -> str:
    chars = list(text)
    rng.shuffle(chars)
    return "".join(chars)


# =====================================================================
# 7. Chunking + Cohen's d
# =====================================================================


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    out = []
    half = chunk_size // 2
    for i in range(0, len(text), chunk_size):
        c = text[i:i + chunk_size]
        if len(c) >= half:
            out.append(c)
    return out


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    pooled = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2.0)
    if pooled == 0:
        return float("inf")
    return float((np.mean(a) - np.mean(b)) / pooled)


# =====================================================================
# 8. Main experiment
# =====================================================================


def run_once() -> dict:
    rng = np.random.default_rng(RNG_SEED)
    np.random.seed(RNG_SEED)

    print("=" * 72)
    print("Spike #125.1 — Python reference (bigram-cascade)")
    print("=" * 72)

    corpus = load_attested_corpus()
    print(f"\nAttested corpus: {len(corpus):,} chars from MFO + srmech notebooks")

    selected, token_to_slot = topn_bigrams(corpus, TOP_N_BIGRAMS)
    n_nodes = len(selected)
    print(f"Top-N bigrams: {n_nodes} (cap {TOP_N_BIGRAMS})")

    L = bigram_cooc_laplacian(corpus, token_to_slot, n_nodes, window=COOC_WINDOW)
    sym = np.allclose(L, L.T, atol=1e-10)
    print(f"Bigram Laplacian: {L.shape}; symmetric: {sym}")

    print("Eigendecomposing Laplacian (this is the slow step) ...")
    t0 = time.perf_counter()
    eigvals, eigvecs = np.linalg.eigh(L)
    t_eig = time.perf_counter() - t0
    print(f"  eigendecomposition time: {t_eig:.2f}s")

    truth_chunks = chunk_text(corpus, CHUNK_SIZE)
    print(f"\nAttested chunks: {len(truth_chunks)} of {CHUNK_SIZE}-char")

    t0 = time.perf_counter()
    truth_coeffs = []
    for c in truth_chunks:
        state = chunk_bigram_state(c, token_to_slot, n_nodes)
        truth_coeffs.append(spectral_project(state, eigvecs))
    t_dec = time.perf_counter() - t0
    n_chars = sum(len(c) for c in truth_chunks)
    print(f"Truth-fingerprint: {len(truth_coeffs)} chunks; {t_dec:.3f}s; "
          f"{t_dec / n_chars * 1e6:.2f} us/char")

    ref = np.mean(np.stack(truth_coeffs, axis=0), axis=0)

    seed_start = int(0.7 * len(corpus))
    seed_text = corpus[seed_start:]
    seed_chunks = chunk_text(seed_text, CHUNK_SIZE)
    print(f"\nAdversarial seed: {len(seed_chunks)} chunks from held-out 30%")

    adv_classes = [
        ("attested_held_out", seed_chunks),
        ("citation_swap",     [adv_citation_swap(c, rng) for c in seed_chunks]),
        ("value_mutation",    [adv_value_mutation(c) for c in seed_chunks]),
        ("vocab_swap",        [adv_vocab_swap(c) for c in seed_chunks]),
        ("random_baseline",   [adv_random_baseline(c, rng) for c in seed_chunks]),
    ]

    print("\n--- Per-class spectral fingerprint similarity ---")
    print(f"{'Class':<22} {'real_sim_mean':>14} {'real_sim_std':>14} {'n_chunks':>10}")
    class_sims = {}
    for cname, chunks in adv_classes:
        sims = []
        for c in chunks:
            state = chunk_bigram_state(c, token_to_slot, n_nodes)
            coeffs = spectral_project(state, eigvecs)
            sims.append(cosine_real(ref, coeffs))
        sims = np.array(sims)
        class_sims[cname] = sims
        print(f"{cname:<22} {sims.mean():>14.6f} {sims.std(ddof=1):>14.6f} {len(sims):>10d}")

    print("\n--- Cohen's d (attested_held_out vs adversarial) ---")
    attested = class_sims["attested_held_out"]
    d_results = {}
    for cname in ("citation_swap", "value_mutation", "vocab_swap", "random_baseline"):
        d = cohens_d(attested, class_sims[cname])
        d_results[cname] = d
        verdict = "DISCRIMINATES" if abs(d) >= 2.0 else ("WEAK" if abs(d) >= 0.5 else "NULL")
        print(f"  attested vs {cname:<22} d = {d:+.4f}   [{verdict}]")

    abs_ds = {k: abs(v) for k, v in d_results.items()}
    all_null = all(v < 0.5 for v in abs_ds.values())
    any_disc = any(v >= 0.5 for v in abs_ds.values())
    any_null = any(v < 0.5 for v in abs_ds.values())

    if all_null:
        composite = "BIGRAM-NULLS-TOO"
    elif any_disc and any_null:
        composite = "BIGRAM-PARTIAL"
    elif any_disc and not any_null:
        composite = "BIGRAM-DISCRIMINATES"
    else:
        composite = "BIGRAM-UNKNOWN"

    print(f"\n>>> Composite verdict: {composite}")

    return {
        "verdict": composite,
        "cohens_d": d_results,
        "class_sim_means": {k: float(np.mean(v)) for k, v in class_sims.items()},
        "class_sim_stds":  {k: float(np.std(v, ddof=1)) for k, v in class_sims.items()},
        "n_nodes": n_nodes,
        "n_truth_chunks": len(truth_chunks),
        "n_seed_chunks": len(seed_chunks),
        "eigendecompose_s": t_eig,
    }


def reproducibility_check():
    print("\n=== Run 1 ===")
    r1 = run_once()
    print("\n=== Run 2 ===")
    r2 = run_once()
    same_d = all(r1["cohens_d"][k] == r2["cohens_d"][k] for k in r1["cohens_d"])
    same_means = all(r1["class_sim_means"][k] == r2["class_sim_means"][k]
                     for k in r1["class_sim_means"])
    print("\n--- Bit-exact reproducibility (Python-side) ---")
    print(f"  Cohen's d identical:   {same_d}")
    print(f"  class_sim_means equal: {same_means}")
    print(f"  Overall bit-exact:     {same_d and same_means}")
    return r1, r2, (same_d and same_means)


if __name__ == "__main__":
    r1, r2, bitexact = reproducibility_check()
    print("\nVerdict:", r1["verdict"])
    print("Bit-exact:", bitexact)
