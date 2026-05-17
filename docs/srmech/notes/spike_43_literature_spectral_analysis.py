"""
Spike #43 — Spectral shape of literature / teaching material

Primary analysis: 8 signatures x 6+ substrates.

Discipline:
- Closed-form deterministic computation (no SGD, no per-particle free parameters)
- NDJSON output per [[feedback_ndjson_over_bloated_json]]
- 14-class A-N vocabulary applied; no new classes per [[feedback_no_privileged_primitive_classes]]
- Falsifier discipline: even canonical-good anchors tested rigorously

Signatures applied to TEXT substrate:
  S1 (Class K Kepler-ladder): chapter-length / paragraph-length / sentence-length sequences -> c_k = eps^k * K_k(text)
  S2 (Class L Laplacian): chapter-dependency graph Fiedler partition alignment
  S3 (Class N Zipf rational-approximation): word-frequency distribution
  S4 (Class C streaming coherence): sentence-to-sentence concept-vector overlap
  S5 (Class I cyclic recurrence): theme/motif callbacks across chapters
  S6 (Cascade-beta stretched-exp): concept-introduction-rate exp(-(t/tau)^beta)
  S7 (Class J prime/vocabulary multiset): vocabulary multiset richness + reuse
  S8 (Class M HDC fingerprint): chapter-hypervector binding coherence

Substrate-binding K_k(text) is itself a discovery target.
"""

from __future__ import annotations

import collections
import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence


# ------------------------------------------------------------------------
# Text loading + tokenization
# ------------------------------------------------------------------------


@dataclass
class Substrate:
    name: str
    path: str
    text: str
    is_canonical_good: bool
    notes: str


CANONICAL_PATHS = {
    "mfo_notebook": (
        r"D:\GitHub\mlehaptics\docs\antikythera-maths\mfo_spectral_research_notebook.md",
        True,
        "canonical good — MFO spectral research notebook (foundational ontology)",
    ),
    "srmech_notebook": (
        r"D:\GitHub\mlehaptics\docs\srmech\srmech_research_notebook.md",
        True,
        "canonical good — srmech master architecture notebook",
    ),
    "spike_38b": (
        r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_38b_caffeine_form_function_remnants_2026-05-17.md",
        True,
        "canonical good — Spike #38b template (cascade composition exemplar)",
    ),
    "spike_41": (
        r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_41_fibonacci_unity_2026-05-17.md",
        True,
        "canonical good — Spike #41 (Cauchy-form unbiased fit methodology)",
    ),
    "spike_42": (
        r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_42_imprinting_cascade_entropy_reposture_2026-05-17.md",
        True,
        "canonical good — Spike #42 (K_k(substrate) sharpening; iterative MFO-style)",
    ),
}


def load_substrate(name: str, path: str, is_canonical_good: bool, notes: str) -> Substrate:
    text = Path(path).read_text(encoding="utf-8")
    return Substrate(name=name, path=path, text=text, is_canonical_good=is_canonical_good, notes=notes)


# ---------- chapter / section / paragraph / sentence / word tokenization ----------


def tokenize_chapters(text: str) -> list[tuple[str, str]]:
    """Return list of (heading, body) per top-level chapter or H2."""
    lines = text.split("\n")
    chapters: list[tuple[str, list[str]]] = []
    current_heading = "[front-matter]"
    current_body: list[str] = []
    for line in lines:
        if re.match(r"^## ", line):
            chapters.append((current_heading, current_body))
            current_heading = line[3:].strip()
            current_body = []
        else:
            current_body.append(line)
    chapters.append((current_heading, current_body))
    return [(h, "\n".join(b)) for h, b in chapters if b]


def tokenize_paragraphs(body: str) -> list[str]:
    paras = re.split(r"\n\s*\n", body)
    return [p.strip() for p in paras if p.strip()]


_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def tokenize_sentences(para: str) -> list[str]:
    cleaned = re.sub(r"```.*?```", " ", para, flags=re.DOTALL)
    cleaned = re.sub(r"`[^`]*`", " ", cleaned)
    parts = _SENTENCE_RE.split(cleaned.strip())
    return [p.strip() for p in parts if p.strip()]


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z']+")


def tokenize_words(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


# ------------------------------------------------------------------------
# Signature S3 — Class N Zipf rational-approximation
# ------------------------------------------------------------------------


def zipf_fit(words: list[str]) -> dict:
    """Fit log(freq) vs log(rank) on top-200 words. Ideal Zipf slope is -1.

    Class N rational-approximation lens: how close to s = -1?
    """
    counter = collections.Counter(words)
    most_common = counter.most_common(200)
    if len(most_common) < 20:
        return {"valid": False, "n_words": len(words)}
    ranks = list(range(1, len(most_common) + 1))
    freqs = [c for _, c in most_common]
    log_r = [math.log(r) for r in ranks]
    log_f = [math.log(f) for f in freqs]
    n = len(log_r)
    mean_r = sum(log_r) / n
    mean_f = sum(log_f) / n
    cov = sum((log_r[i] - mean_r) * (log_f[i] - mean_f) for i in range(n))
    var = sum((log_r[i] - mean_r) ** 2 for i in range(n))
    slope = cov / var if var else 0.0
    intercept = mean_f - slope * mean_r
    pred = [intercept + slope * lr for lr in log_r]
    ss_res = sum((log_f[i] - pred[i]) ** 2 for i in range(n))
    ss_tot = sum((log_f[i] - mean_f) ** 2 for i in range(n))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "n_words": len(words),
        "n_unique": len(counter),
        "zipf_slope": slope,
        "zipf_intercept": intercept,
        "r2": r2,
        "abs_deviation_from_neg1": abs(slope - (-1.0)),
    }


# ------------------------------------------------------------------------
# Signature S1 — Class K Kepler-ladder on length sequences
# ------------------------------------------------------------------------


def cauchy_form_fit_lengths(seq: list[int], k_max: int = 6) -> dict:
    """Fit c_k = eps^k * K_k(text) on a sequence of lengths.

    Here we use the DECAY signature: sort sequence descending, divide by max,
    take top-(k_max+1) entries; c_k for k=1..k_max are the normalized lengths
    of the (k+1)th-longest. This probes power-law-vs-stretched-exp tail decay.

    Returns biased eps_fit on log|c_k|, K_k array per Spike #42, and r^2.
    """
    if len(seq) < k_max + 1:
        return {"valid": False, "n": len(seq)}
    sorted_desc = sorted(seq, reverse=True)
    head = sorted_desc[: k_max + 1]
    c0 = head[0]
    if c0 == 0:
        return {"valid": False, "reason": "zero head"}
    c = [head[i] / c0 for i in range(1, k_max + 1)]
    # biased fit: log|c_k| = k log eps + log K_k
    # at first assume K_k = 1/k (Kepler-EOC canonical)
    log_ck = [math.log(max(abs(c[i - 1]), 1e-12)) for i in range(1, k_max + 1)]
    log_ck_times_k = [log_ck[i - 1] + math.log(i) for i in range(1, k_max + 1)]
    # fit log_ck_times_k = k * log(eps) (Spike #41 unbiased)
    ks = list(range(1, k_max + 1))
    sum_k = sum(ks)
    sum_kk = sum(k * k for k in ks)
    sum_y = sum(log_ck_times_k)
    sum_ky = sum(ks[i] * log_ck_times_k[i] for i in range(k_max))
    log_eps = (k_max * sum_ky - sum_k * sum_y) / (k_max * sum_kk - sum_k * sum_k)
    eps_unbiased = math.exp(log_eps)
    # K_k per Spike #42: K_k(substrate) = c_k / eps^k
    K_k_substrate = [c[i - 1] / (eps_unbiased ** i) for i in range(1, k_max + 1)]
    # r^2 on log fit
    pred = [k * log_eps for k in ks]
    mean_y = sum(log_ck_times_k) / k_max
    ss_res = sum((log_ck_times_k[i] - pred[i]) ** 2 for i in range(k_max))
    ss_tot = sum((log_ck_times_k[i] - mean_y) ** 2 for i in range(k_max))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "n": len(seq),
        "c_k": c,
        "eps_unbiased_fit": eps_unbiased,
        "K_k_substrate": K_k_substrate,
        "r2": r2,
        "in_physical_range": 0 < eps_unbiased <= 0.5,
        "head_lengths": head,
    }


# ------------------------------------------------------------------------
# Signature S2 — Class L Laplacian on chapter-dependency graph
# ------------------------------------------------------------------------


def chapter_word_sets(chapters: list[tuple[str, str]], stopwords: set[str]) -> list[set[str]]:
    sets: list[set[str]] = []
    for _, body in chapters:
        words = [w for w in tokenize_words(body) if w not in stopwords and len(w) >= 4]
        counter = collections.Counter(words)
        # Top-100 content words per chapter as the chapter's "concept vector"
        top = {w for w, _ in counter.most_common(100)}
        sets.append(top)
    return sets


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def chapter_dependency_laplacian_stats(chapters: list[tuple[str, str]], stopwords: set[str]) -> dict:
    """Build Jaccard-similarity weighted graph between chapters, compute Laplacian eigenvalues.

    Class L lens. Fiedler value (lambda_2) measures connectivity.
    Algebraic connectivity > 0 implies single connected component.
    Spectral gap (lambda_3 - lambda_2) measures partition quality.
    """
    sets = chapter_word_sets(chapters, stopwords)
    n = len(sets)
    if n < 3:
        return {"valid": False, "n_chapters": n}
    W = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            w = jaccard(sets[i], sets[j])
            W[i][j] = w
            W[j][i] = w
    D = [sum(W[i]) for i in range(n)]
    # L = D - W (combinatorial Laplacian)
    L = [[(D[i] if i == j else 0.0) - W[i][j] for j in range(n)] for i in range(n)]
    # power-iteration for top eigenvalues; for small n use Jacobi-style
    eigvals = jacobi_eigvals_symmetric(L, n)
    eigvals.sort()
    lambda_1 = eigvals[0]
    lambda_2 = eigvals[1]
    lambda_3 = eigvals[2] if n >= 3 else 0.0
    return {
        "valid": True,
        "n_chapters": n,
        "lambda_1": lambda_1,
        "fiedler_lambda_2": lambda_2,
        "lambda_3": lambda_3,
        "spectral_gap": lambda_3 - lambda_2,
        "connected_component_score": lambda_2 > 1e-9,
        "mean_jaccard": sum(W[i][j] for i in range(n) for j in range(i + 1, n))
        / max(1, n * (n - 1) // 2),
    }


def jacobi_eigvals_symmetric(A: list[list[float]], n: int, max_iter: int = 100, tol: float = 1e-10) -> list[float]:
    """Jacobi eigenvalue iteration on symmetric matrix; returns eigenvalues."""
    M = [row[:] for row in A]
    for _ in range(max_iter):
        # find largest off-diagonal
        p, q, max_val = 0, 1, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(M[i][j]) > max_val:
                    max_val = abs(M[i][j])
                    p, q = i, j
        if max_val < tol:
            break
        # rotation
        if abs(M[p][p] - M[q][q]) < tol:
            theta = math.pi / 4
        else:
            theta = 0.5 * math.atan2(2 * M[p][q], M[p][p] - M[q][q])
        c = math.cos(theta)
        s = math.sin(theta)
        Mpp = c * c * M[p][p] + 2 * c * s * M[p][q] + s * s * M[q][q]
        Mqq = s * s * M[p][p] - 2 * c * s * M[p][q] + c * c * M[q][q]
        M[p][p] = Mpp
        M[q][q] = Mqq
        M[p][q] = 0.0
        M[q][p] = 0.0
        for i in range(n):
            if i != p and i != q:
                Mip = c * M[i][p] + s * M[i][q]
                Miq = -s * M[i][p] + c * M[i][q]
                M[i][p] = Mip
                M[p][i] = Mip
                M[i][q] = Miq
                M[q][i] = Miq
    return [M[i][i] for i in range(n)]


# ------------------------------------------------------------------------
# Signature S4 — Class C streaming coherence
# ------------------------------------------------------------------------


def streaming_coherence(sentences: list[str], stopwords: set[str], window: int = 5) -> dict:
    """Sentence-to-sentence concept-vector overlap.

    Class C streaming lens. For each adjacent sentence pair, Jaccard of content-word sets;
    mean + std over the whole document; high mean = coherent.
    """
    sets: list[set[str]] = []
    for s in sentences:
        words = [w for w in tokenize_words(s) if w not in stopwords and len(w) >= 4]
        sets.append(set(words))
    if len(sets) < 2:
        return {"valid": False, "n_sentences": len(sets)}
    overlaps = [jaccard(sets[i], sets[i + 1]) for i in range(len(sets) - 1)]
    window_overlaps = []
    for i in range(len(sets) - window):
        union_window = set()
        for j in range(window):
            union_window.update(sets[i + j])
        window_overlaps.append(jaccard(union_window, sets[i + window]))
    mean_adj = sum(overlaps) / len(overlaps)
    var_adj = sum((o - mean_adj) ** 2 for o in overlaps) / len(overlaps)
    return {
        "valid": True,
        "n_sentences": len(sets),
        "mean_adjacent_jaccard": mean_adj,
        "std_adjacent_jaccard": math.sqrt(var_adj),
        "mean_window_jaccard": (sum(window_overlaps) / len(window_overlaps)) if window_overlaps else 0.0,
        "zero_overlap_fraction": sum(1 for o in overlaps if o == 0.0) / len(overlaps),
    }


# ------------------------------------------------------------------------
# Signature S5 — Class I cyclic recurrence (theme callbacks)
# ------------------------------------------------------------------------


def theme_recurrence(chapters: list[tuple[str, str]], stopwords: set[str]) -> dict:
    """Identify recurring concept-threads across chapters.

    Class I cyclic lens. A "theme" is a content word that appears in >= 50% of chapters.
    Healthy text: a small canonical theme set recurring throughout (cyclic substrate).
    """
    sets = chapter_word_sets(chapters, stopwords)
    n = len(sets)
    if n < 3:
        return {"valid": False, "n_chapters": n}
    counts: collections.Counter = collections.Counter()
    for s in sets:
        for w in s:
            counts[w] += 1
    pervasive = {w: c for w, c in counts.items() if c >= n * 0.5}
    universal = {w: c for w, c in counts.items() if c == n}
    # cyclic-period estimate: gap between appearances for top-10 pervasive themes
    # for each pervasive theme, compute spread variance (low = uniform = canonical recurrence)
    if pervasive:
        theme_uniformity_scores = []
        for w in list(pervasive)[:10]:
            indices = [i for i in range(n) if w in sets[i]]
            if len(indices) > 1:
                gaps = [indices[j + 1] - indices[j] for j in range(len(indices) - 1)]
                mean_gap = sum(gaps) / len(gaps)
                var_gap = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
                cv = math.sqrt(var_gap) / mean_gap if mean_gap > 0 else 0
                theme_uniformity_scores.append(cv)
        mean_uniformity = sum(theme_uniformity_scores) / max(1, len(theme_uniformity_scores))
    else:
        mean_uniformity = 0.0
    return {
        "valid": True,
        "n_chapters": n,
        "pervasive_theme_count": len(pervasive),
        "universal_theme_count": len(universal),
        "pervasive_fraction": len(pervasive) / max(1, sum(len(s) for s in sets) / n),
        "theme_gap_cv_mean": mean_uniformity,  # 0 = perfect uniform spacing; ~1 = Poisson
        "sample_pervasive": list(pervasive)[:10],
    }


# ------------------------------------------------------------------------
# Signature S6 — Cascade-beta stretched-exp on concept-introduction rate
# ------------------------------------------------------------------------


def concept_introduction_rate(text: str, stopwords: set[str], n_buckets: int = 20) -> dict:
    """Track NEW-term density across the document, fit stretched-exp.

    Cascade-beta lens. Per Spike #41/42 cascade structure, well-written text should
    show concept-introduction decay shape exp(-(t/tau)^beta).
    """
    words = [w for w in tokenize_words(text) if w not in stopwords and len(w) >= 4]
    n = len(words)
    if n < 200:
        return {"valid": False, "n_words": n}
    bucket_size = n // n_buckets
    seen: set[str] = set()
    new_counts: list[int] = []
    for b in range(n_buckets):
        new_in_bucket = 0
        for i in range(bucket_size):
            idx = b * bucket_size + i
            if idx >= n:
                break
            w = words[idx]
            if w not in seen:
                new_in_bucket += 1
                seen.add(w)
        new_counts.append(new_in_bucket)
    # fit stretched exp y = A * exp(-(t/tau)^beta) on new_counts; t=1..n_buckets
    # log y = log A - (t/tau)^beta; take log-log of -log(y/A) vs log(t) to extract beta
    A = max(new_counts)
    if A <= 0:
        return {"valid": False, "reason": "A=0"}
    # use ratio y/A; restrict to where y < A (otherwise log0)
    pts = []
    for t, y in enumerate(new_counts, start=1):
        if 0 < y < A:
            arg = -math.log(y / A)
            if arg > 0:
                pts.append((math.log(t), math.log(arg)))
    if len(pts) < 3:
        return {"valid": False, "reason": "not enough decay points"}
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    n_pts = len(pts)
    sxx = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    beta = (n_pts * sxy - sx * sy) / (n_pts * sxx - sx * sx) if (n_pts * sxx - sx * sx) else 0.0
    log_tau_neg = (sy - beta * sx) / n_pts
    tau = math.exp(-log_tau_neg / beta) if beta else float("inf")
    # r^2
    mean_y = sy / n_pts
    pred = [(log_tau_neg + beta * p[0]) for p in pts]
    ss_res = sum((pts[i][1] - pred[i]) ** 2 for i in range(n_pts))
    ss_tot = sum((p[1] - mean_y) ** 2 for p in pts)
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "n_words": n,
        "n_buckets": n_buckets,
        "new_counts": new_counts,
        "beta_fit": beta,
        "tau_fit": tau,
        "r2": r2,
        "total_unique": len(seen),
    }


# ------------------------------------------------------------------------
# Signature S7 — Class J prime/vocabulary multiset
# ------------------------------------------------------------------------


def vocabulary_richness_decomp(words: list[str]) -> dict:
    """Vocabulary multiset decomposition (Class J prime-factorisation analogue).

    Class J lens: how is vocabulary STRUCTURED into recurrence-classes?
    Hapax legomena (freq=1) / dis legomena (freq=2) / pervasive (freq>20) breakdown.
    Heaps' law fit V = K * N^alpha (well-written: alpha typically 0.4-0.6).
    """
    counter = collections.Counter(words)
    if not counter:
        return {"valid": False}
    n = len(words)
    v = len(counter)
    hapax = sum(1 for w, c in counter.items() if c == 1)
    dis = sum(1 for w, c in counter.items() if c == 2)
    pervasive = sum(1 for w, c in counter.items() if c >= 20)
    # Heaps law: vocabulary as function of running word count
    # V(N) sampled at N/10, 2N/10, ..., N
    samples = []
    for k in range(1, 11):
        cutoff = (n * k) // 10
        seen = set()
        for w in words[:cutoff]:
            seen.add(w)
        samples.append((cutoff, len(seen)))
    log_n = [math.log(s[0]) for s in samples]
    log_v = [math.log(s[1]) for s in samples]
    mean_n = sum(log_n) / 10
    mean_v = sum(log_v) / 10
    cov = sum((log_n[i] - mean_n) * (log_v[i] - mean_v) for i in range(10))
    var = sum((log_n[i] - mean_n) ** 2 for i in range(10))
    heaps_alpha = cov / var if var else 0.0
    return {
        "valid": True,
        "n_tokens": n,
        "n_types": v,
        "type_token_ratio": v / n,
        "hapax_count": hapax,
        "hapax_fraction": hapax / v,
        "dis_legomena_count": dis,
        "pervasive_count": pervasive,
        "heaps_alpha": heaps_alpha,
    }


# ------------------------------------------------------------------------
# Signature S8 — Class M HDC fingerprint
# ------------------------------------------------------------------------

HDC_DIM = 1024


def _splitmix64(x: int) -> int:
    """Single SplitMix64 step (constant-time mix, well-distributed)."""
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    x ^= x >> 31
    return x


def _word_code(w: str) -> list[int]:
    """Deterministic +/-1 hypervector for a word via SplitMix64.

    Each word gets a unique 64-bit seed from a string hash, then SplitMix64 produces
    HDC_DIM/64 pseudo-random 64-bit values whose bits are unpacked into +/-1.
    """
    seed = 0xCBF29CE484222325  # FNV offset
    for ch in w:
        seed = ((seed ^ ord(ch)) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    bits: list[int] = []
    state = seed | 1
    words_needed = (HDC_DIM + 63) // 64
    for _ in range(words_needed):
        state = _splitmix64(state)
        v = state
        for b in range(64):
            bits.append(1 if (v >> b) & 1 else -1)
            if len(bits) >= HDC_DIM:
                break
        if len(bits) >= HDC_DIM:
            break
    return bits


def hdc_chapter_vector_bipolar(words: list[str], stopwords: set[str], rng_state: dict) -> list[int]:
    """Build a bipolar HDC vector via SUM (bundle); then threshold-sign for majority."""
    accum = [0] * HDC_DIM
    n_contrib = 0
    for w in words:
        if w in stopwords or len(w) < 4:
            continue
        code = rng_state.get(w)
        if code is None:
            code = _word_code(w)
            rng_state[w] = code
        for i in range(HDC_DIM):
            accum[i] += code[i]
        n_contrib += 1
    if n_contrib == 0:
        return [0] * HDC_DIM
    # threshold to bipolar (majority): >0 -> +1, <0 -> -1, ==0 -> 0
    return [(1 if a > 0 else (-1 if a < 0 else 0)) for a in accum]


def cosine_bipolar(a: list[int], b: list[int]) -> float:
    dot = sum(a[i] * b[i] for i in range(len(a)))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def hdc_chapter_fingerprint(chapters: list[tuple[str, str]], stopwords: set[str]) -> dict:
    """Compute pairwise cosine similarity between chapter bipolar HDC vectors.

    Class M HDC lens. Well-written text: mean intra-doc similarity > random baseline AND
    not too high (chapters do differ); structure visible.

    Random-baseline expectation for independent BIPOLAR HDC vectors: cos sim ~ 0 (variance
    ~ 1/sqrt(HDC_DIM)). Topic-coherent chapters with shared content vocabulary will yield
    POSITIVE mean cosine; randomly-permuted chapters drop toward zero.
    """
    rng_state: dict = {}
    vecs = []
    for _, body in chapters:
        words = tokenize_words(body)
        v = hdc_chapter_vector_bipolar(words, stopwords, rng_state)
        vecs.append(v)
    n = len(vecs)
    if n < 3:
        return {"valid": False, "n_chapters": n}
    sims = []
    for i in range(n):
        for j in range(i + 1, n):
            sims.append(cosine_bipolar(vecs[i], vecs[j]))
    mean_sim = sum(sims) / len(sims)
    var_sim = sum((s - mean_sim) ** 2 for s in sims) / len(sims)
    std_sim = math.sqrt(var_sim)
    return {
        "valid": True,
        "n_chapters": n,
        "mean_pairwise_cosine": mean_sim,
        "std_pairwise_cosine": std_sim,
        "min_pairwise_cosine": min(sims),
        "max_pairwise_cosine": max(sims),
        # well-written sweet spot: chapters cohere (>0.15) but differ (<0.70)
        "in_cohere_but_differ_band": 0.15 <= mean_sim <= 0.70,
    }


# ------------------------------------------------------------------------
# Stopwords (small, hand-curated)
# ------------------------------------------------------------------------


STOPWORDS = set(
    """
the and that this with from for not but are was were has have had been being
your this these those they them their there here what which when where how
about between under above before after during through across over also more
most some such only than then them was were when which while with would your
a an as at be by do does did dont in is it its of on or so to up us we i you
""".split()
)


# ------------------------------------------------------------------------
# Per-substrate run
# ------------------------------------------------------------------------


@dataclass
class SubstrateFingerprint:
    substrate: str
    is_canonical_good: bool
    notes: str
    n_chapters: int
    n_paragraphs: int
    n_sentences: int
    n_words: int
    # signatures
    s1_kepler_chapter_lengths: dict
    s1_kepler_para_lengths: dict
    s2_laplacian: dict
    s3_zipf: dict
    s4_streaming: dict
    s5_cyclic_themes: dict
    s6_cascade_beta: dict
    s7_vocab_richness: dict
    s8_hdc_fingerprint: dict


def fingerprint_substrate(s: Substrate) -> SubstrateFingerprint:
    chapters = tokenize_chapters(s.text)
    paragraphs = []
    sentences = []
    for _, body in chapters:
        paras = tokenize_paragraphs(body)
        paragraphs.extend(paras)
        for p in paras:
            sentences.extend(tokenize_sentences(p))
    words = tokenize_words(s.text)
    chapter_word_counts = [len(tokenize_words(body)) for _, body in chapters if tokenize_words(body)]
    paragraph_word_counts = [len(tokenize_words(p)) for p in paragraphs if tokenize_words(p)]

    return SubstrateFingerprint(
        substrate=s.name,
        is_canonical_good=s.is_canonical_good,
        notes=s.notes,
        n_chapters=len(chapters),
        n_paragraphs=len(paragraphs),
        n_sentences=len(sentences),
        n_words=len(words),
        s1_kepler_chapter_lengths=cauchy_form_fit_lengths(chapter_word_counts, k_max=6),
        s1_kepler_para_lengths=cauchy_form_fit_lengths(paragraph_word_counts, k_max=6),
        s2_laplacian=chapter_dependency_laplacian_stats(chapters, STOPWORDS),
        s3_zipf=zipf_fit(words),
        s4_streaming=streaming_coherence(sentences, STOPWORDS),
        s5_cyclic_themes=theme_recurrence(chapters, STOPWORDS),
        s6_cascade_beta=concept_introduction_rate(s.text, STOPWORDS),
        s7_vocab_richness=vocabulary_richness_decomp([w for w in words if w not in STOPWORDS]),
        s8_hdc_fingerprint=hdc_chapter_fingerprint(chapters, STOPWORDS),
    )


# ------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    substrates: list[Substrate] = []
    for name, (path, canonical, notes) in CANONICAL_PATHS.items():
        if not Path(path).exists():
            print(f"  [skip] {name}: {path} not found")
            continue
        s = load_substrate(name, path, canonical, notes)
        substrates.append(s)
        print(f"  [load] {name}: {len(s.text):,} chars")

    fingerprints = []
    for s in substrates:
        print(f"  [run]  {s.name}")
        fp = fingerprint_substrate(s)
        fingerprints.append(fp)

    # Write NDJSON: one record per (substrate, signature)
    records_path = out / "spike_43_records_2026-05-17.ndjson"
    with records_path.open("w", encoding="utf-8") as f:
        for fp in fingerprints:
            d = asdict(fp)
            base = {
                "date": "2026-05-17",
                "spike": 43,
                "substrate": d["substrate"],
                "is_canonical_good": d["is_canonical_good"],
                "notes": d["notes"],
                "n_chapters": d["n_chapters"],
                "n_paragraphs": d["n_paragraphs"],
                "n_sentences": d["n_sentences"],
                "n_words": d["n_words"],
            }
            for sig_key in [
                "s1_kepler_chapter_lengths",
                "s1_kepler_para_lengths",
                "s2_laplacian",
                "s3_zipf",
                "s4_streaming",
                "s5_cyclic_themes",
                "s6_cascade_beta",
                "s7_vocab_richness",
                "s8_hdc_fingerprint",
            ]:
                rec = dict(base)
                rec["signature"] = sig_key
                rec["fingerprint"] = d[sig_key]
                f.write(json.dumps(rec, default=float) + "\n")
    print(f"  [write] {records_path}")

    # Console summary
    print("\n  --- per-substrate fingerprint summary ---\n")
    for fp in fingerprints:
        print(
            f"  {fp.substrate}  chapters={fp.n_chapters}  paras={fp.n_paragraphs}  "
            f"sent={fp.n_sentences}  words={fp.n_words}"
        )
        if fp.s3_zipf.get("valid"):
            print(
                f"    S3 Zipf slope={fp.s3_zipf['zipf_slope']:.3f} (target -1)  "
                f"r2={fp.s3_zipf['r2']:.4f}"
            )
        if fp.s2_laplacian.get("valid"):
            print(
                f"    S2 Laplacian fiedler={fp.s2_laplacian['fiedler_lambda_2']:.4f}  "
                f"mean_jaccard={fp.s2_laplacian['mean_jaccard']:.4f}"
            )
        if fp.s4_streaming.get("valid"):
            print(
                f"    S4 streaming mean_adj_jac={fp.s4_streaming['mean_adjacent_jaccard']:.4f}  "
                f"zero_frac={fp.s4_streaming['zero_overlap_fraction']:.4f}"
            )
        if fp.s6_cascade_beta.get("valid"):
            print(
                f"    S6 cascade beta={fp.s6_cascade_beta['beta_fit']:.3f}  "
                f"r2={fp.s6_cascade_beta['r2']:.4f}"
            )
        if fp.s7_vocab_richness.get("valid"):
            print(
                f"    S7 heaps alpha={fp.s7_vocab_richness['heaps_alpha']:.3f}  "
                f"hapax_frac={fp.s7_vocab_richness['hapax_fraction']:.3f}"
            )
        if fp.s8_hdc_fingerprint.get("valid"):
            print(
                f"    S8 HDC mean_cos={fp.s8_hdc_fingerprint['mean_pairwise_cosine']:.4f}  "
                f"in_band={fp.s8_hdc_fingerprint['in_cohere_but_differ_band']}"
            )
        if fp.s1_kepler_chapter_lengths.get("valid"):
            print(
                f"    S1 K-ladder (chapter lengths) eps={fp.s1_kepler_chapter_lengths['eps_unbiased_fit']:.4f}  "
                f"r2={fp.s1_kepler_chapter_lengths['r2']:.4f}  "
                f"in_phys={fp.s1_kepler_chapter_lengths['in_physical_range']}"
            )


if __name__ == "__main__":
    main(r"D:\temp\spike_43")
