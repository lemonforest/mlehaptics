"""
Spike #43c — Multi-modal signature analysis.

Apply Spike #43's R1-R5 + S1-S8 signatures to each substrate across modalities,
PLUS new modality-adaptive signatures:

  C1-C5 (CODE modality): cross-function calls, unique-symbol propagation,
                          function-length Pareto, module-overlap, comment-density
  O1-O5 (ORAL modality): repetition-pattern density (intentional in oral),
                          rhyme-scheme regularity (approximate end-rhyme),
                          mnemonic-hook density, narrative-arc cascade

Discipline:
- Closed-form deterministic computation
- NDJSON output
- 14-class A-N vocabulary; no new classes
- Math doesn't lie; iterate the test, not the verdict
"""

from __future__ import annotations

import collections
import json
import math
import re
from pathlib import Path
from typing import Optional


OUT_DIR = Path(r"D:\temp\spike_43c")
CORPUS_DIR = OUT_DIR / "corpus"


# ---------------------------------------------------------------------------
# Tokenisation (text)
# ---------------------------------------------------------------------------

STOPWORDS = set(
    """
the and that this with from for not but are was were has have had been being
your this these those they them their there here what which when where how
about between under above before after during through across over also more
most some such only than then them was were when which while with would your
a an as at be by do does did dont in is it its of on or so to up us we i you
""".split()
)


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z']+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def tokenize_words(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def tokenize_paragraphs_simple(text: str) -> list[str]:
    paras = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paras if len(p.strip()) >= 30]


def tokenize_sentences(para: str) -> list[str]:
    cleaned = re.sub(r"```.*?```", " ", para, flags=re.DOTALL)
    cleaned = re.sub(r"`[^`]*`", " ", cleaned)
    parts = _SENTENCE_RE.split(cleaned.strip())
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Text-substrate signatures (carried over from Spike #43)
# ---------------------------------------------------------------------------


def r1_word_freq_kladder(text: str, k_max: int = 6) -> dict:
    """K-ladder fit on top-(k_max+1) content-word frequencies.

    Returns eps_unbiased, K_k(text) substrate-binding, r2.
    """
    words = [w for w in tokenize_words(text) if w not in STOPWORDS and len(w) >= 4]
    counter = collections.Counter(words)
    most_common = counter.most_common(k_max + 1)
    if len(most_common) < k_max + 1:
        return {"valid": False, "reason": "not enough types"}
    c0 = most_common[0][1]
    if c0 == 0:
        return {"valid": False, "reason": "c0=0"}
    c = [most_common[i][1] / c0 for i in range(1, k_max + 1)]
    log_ck = [math.log(max(abs(c[i]), 1e-12)) for i in range(k_max)]
    log_ck_times_k = [log_ck[i] + math.log(i + 1) for i in range(k_max)]
    ks = list(range(1, k_max + 1))
    sum_k = sum(ks)
    sum_kk = sum(k * k for k in ks)
    sum_y = sum(log_ck_times_k)
    sum_ky = sum(ks[i] * log_ck_times_k[i] for i in range(k_max))
    log_eps = (k_max * sum_ky - sum_k * sum_y) / (k_max * sum_kk - sum_k * sum_k)
    eps_unbiased = math.exp(log_eps)
    K_k_substrate = [c[i] / (eps_unbiased ** (i + 1)) for i in range(k_max)]
    pred = [k * log_eps for k in ks]
    mean_y = sum(log_ck_times_k) / k_max
    ss_res = sum((log_ck_times_k[i] - pred[i]) ** 2 for i in range(k_max))
    ss_tot = sum((log_ck_times_k[i] - mean_y) ** 2 for i in range(k_max))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "top_words": [w for w, _ in most_common],
        "freqs": [n for _, n in most_common],
        "c_k": c,
        "eps_unbiased_fit": eps_unbiased,
        "K_k_substrate": K_k_substrate,
        "r2": r2,
    }


def r2_paragraph_length_pareto(text: str) -> dict:
    paras = tokenize_paragraphs_simple(text)
    lengths = []
    for p in paras:
        wl = len(tokenize_words(p))
        if wl >= 5:
            lengths.append(wl)
    if len(lengths) < 20:
        return {"valid": False, "n": len(lengths)}
    lengths.sort(reverse=True)
    n = len(lengths)
    ranks = list(range(1, n + 1))
    log_r = [math.log(r) for r in ranks]
    log_l = [math.log(l) for l in lengths]
    mean_r = sum(log_r) / n
    mean_l = sum(log_l) / n
    cov = sum((log_r[i] - mean_r) * (log_l[i] - mean_l) for i in range(n))
    var = sum((log_r[i] - mean_r) ** 2 for i in range(n))
    slope = cov / var if var else 0.0
    pred = [mean_l + slope * (log_r[i] - mean_r) for i in range(n)]
    ss_res = sum((log_l[i] - pred[i]) ** 2 for i in range(n))
    ss_tot = sum((log_l[i] - mean_l) ** 2 for i in range(n))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    mean_l_raw = sum(lengths) / n
    return {
        "valid": True,
        "n_paragraphs": n,
        "max_length": lengths[0],
        "median_length": lengths[n // 2],
        "min_length": lengths[-1],
        "power_law_slope": slope,
        "power_law_r2": r2,
        "max_over_median_ratio": lengths[0] / max(1, lengths[n // 2]),
    }


def r3_rare_word_cascade(text: str) -> dict:
    paras = tokenize_paragraphs_simple(text)
    all_words = [w for w in tokenize_words(text) if w not in STOPWORDS and len(w) >= 5]
    counter = collections.Counter(all_words)
    rare = {w for w, c in counter.items() if 2 <= c <= 5}
    if not rare:
        return {"valid": False, "reason": "no rare words"}
    intro_counts = 0
    propagated_counts = 0
    intro_seen: set[str] = set()
    for i, p in enumerate(paras):
        words = set(tokenize_words(p)) & rare
        new_in_p = words - intro_seen
        for w in new_in_p:
            intro_counts += 1
            if i + 1 < len(paras):
                w_next1 = set(tokenize_words(paras[i + 1]))
                if w in w_next1:
                    propagated_counts += 1
                    continue
            if i + 2 < len(paras):
                w_next2 = set(tokenize_words(paras[i + 2]))
                if w in w_next2:
                    propagated_counts += 1
        intro_seen |= new_in_p
    return {
        "valid": True,
        "rare_word_count": len(rare),
        "intro_count": intro_counts,
        "propagated_count": propagated_counts,
        "propagation_rate": propagated_counts / max(1, intro_counts),
    }


_CALLBACK_PATTERNS = [
    r"as (?:we |I )?(?:showed|saw|noted|established|argued|stated|defined|introduced)",
    r"recall (?:from|that)",
    r"per (?:Spike|Section|Part|Chapter|§)",
    r"see (?:also |above |below |Spike|Section|Part|Chapter|§)",
    r"\[\[[^\]]+\]\]",
    r"in Chapter \d+",
    r"\(§[\d.]+",
    r"§\s*[\d.]+",
    r"in (?:section|chapter|book|part) [IVX\d]+",
    r"as (?:described|discussed|mentioned|explained|shown) (?:above|earlier|previously|before)",
    r"the (?:above|previous|preceding|former|latter)",
    r"this (?:section|chapter|theorem|definition|argument)",
    r"\bcf\.\s*\w+",
    r"\bvide\b",
    r"\bibid\.?\b",
    r"\bsupra\b",
    r"\binfra\b",
    r"Figure \d+|Table \d+|Eq\. \(?\d+|Equation \(?\d+",
    r"page\s+\d+",
]


def r4_callback_density(text: str) -> dict:
    n_words = len(tokenize_words(text))
    if n_words < 200:
        return {"valid": False}
    total = 0
    counts = {}
    for pat in _CALLBACK_PATTERNS:
        m = re.findall(pat, text, re.IGNORECASE)
        if m:
            counts[pat[:30]] = len(m)
            total += len(m)
    return {
        "valid": True,
        "n_words": n_words,
        "callback_count_total": total,
        "callbacks_per_1000_words": (total / n_words) * 1000,
    }


def s3_zipf(text: str) -> dict:
    words = tokenize_words(text)
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
    pred = [mean_f + slope * (log_r[i] - mean_r) for i in range(n)]
    ss_res = sum((log_f[i] - pred[i]) ** 2 for i in range(n))
    ss_tot = sum((log_f[i] - mean_f) ** 2 for i in range(n))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "n_words": len(words),
        "n_unique": len(counter),
        "zipf_slope": slope,
        "r2": r2,
    }


def s7_vocab_richness(text: str) -> dict:
    words = tokenize_words(text)
    counter = collections.Counter(words)
    if not counter:
        return {"valid": False}
    n = len(words)
    v = len(counter)
    hapax = sum(1 for w, c in counter.items() if c == 1)
    dis = sum(1 for w, c in counter.items() if c == 2)
    pervasive = sum(1 for w, c in counter.items() if c >= 20)
    samples = []
    for k in range(1, 11):
        cutoff = (n * k) // 10
        if cutoff < 10:
            continue
        seen = set()
        for w in words[:cutoff]:
            seen.add(w)
        samples.append((cutoff, len(seen)))
    if len(samples) < 5:
        return {"valid": False}
    log_n = [math.log(s[0]) for s in samples]
    log_v = [math.log(s[1]) for s in samples]
    nn = len(samples)
    mean_n = sum(log_n) / nn
    mean_v = sum(log_v) / nn
    cov = sum((log_n[i] - mean_n) * (log_v[i] - mean_v) for i in range(nn))
    var = sum((log_n[i] - mean_n) ** 2 for i in range(nn))
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


def s6_concept_intro_rate(text: str, n_buckets: int = 20) -> dict:
    words = [w for w in tokenize_words(text) if w not in STOPWORDS and len(w) >= 4]
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
    A = max(new_counts)
    if A <= 0:
        return {"valid": False, "reason": "A=0"}
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
    den = n_pts * sxx - sx * sx
    beta = (n_pts * sxy - sx * sy) / den if den else 0.0
    log_tau_neg = (sy - beta * sx) / n_pts
    tau = math.exp(-log_tau_neg / beta) if beta else float("inf")
    pred = [log_tau_neg + beta * p[0] for p in pts]
    mean_y = sy / n_pts
    ss_res = sum((pts[i][1] - pred[i]) ** 2 for i in range(n_pts))
    ss_tot = sum((p[1] - mean_y) ** 2 for p in pts)
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "n_words": n,
        "n_buckets": n_buckets,
        "beta_fit": beta,
        "tau_fit": tau,
        "r2": r2,
    }


# ---------------------------------------------------------------------------
# Modality-specific signatures
# ---------------------------------------------------------------------------


_C_FUNCTION_RE = re.compile(
    r"^(?:static\s+|inline\s+|extern\s+)*(?:[A-Za-z_][\w\s\*]+?)\s+([A-Za-z_]\w*)\s*\(",
    re.MULTILINE,
)
_PY_FUNCTION_RE = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
_PY_CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_]\w*)\s*[:\(]", re.MULTILINE)
_IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")


def c1_code_function_size_pareto(text: str, lang: str) -> dict:
    """CODE-modality variant of R2 paragraph-Pareto: function-length distribution."""
    # detect function bodies by heuristic indentation/brace tracking
    if lang == "C":
        # crude: count lines between matching braces of a function-like signature
        sigs = list(_C_FUNCTION_RE.finditer(text))
        lengths = []
        for m in sigs:
            start = m.end()
            depth = 0
            # find opening brace
            brace_start = text.find("{", start)
            if brace_start == -1 or brace_start - start > 200:
                continue
            i = brace_start
            depth = 1
            i += 1
            while i < len(text) and depth > 0:
                ch = text[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                i += 1
            body = text[brace_start + 1 : i - 1]
            n_lines = body.count("\n") + 1
            if 2 <= n_lines <= 5000:
                lengths.append(n_lines)
    elif lang == "PY":
        # crude: find def, count following indented lines
        lines = text.split("\n")
        lengths = []
        i = 0
        while i < len(lines):
            line = lines[i]
            m = re.match(r"^(\s*)(?:async\s+)?def\s+", line)
            if m:
                base_indent = len(m.group(1))
                j = i + 1
                while j < len(lines):
                    ln = lines[j]
                    if ln.strip() == "":
                        j += 1
                        continue
                    cur_indent = len(ln) - len(ln.lstrip())
                    if cur_indent <= base_indent and ln.strip():
                        break
                    j += 1
                if j - i - 1 >= 2:
                    lengths.append(j - i - 1)
                i = j
            else:
                i += 1
    else:
        return {"valid": False}

    if len(lengths) < 10:
        return {"valid": False, "n": len(lengths)}
    lengths.sort(reverse=True)
    n = len(lengths)
    ranks = list(range(1, n + 1))
    log_r = [math.log(r) for r in ranks]
    log_l = [math.log(l) for l in lengths]
    mean_r = sum(log_r) / n
    mean_l = sum(log_l) / n
    cov = sum((log_r[i] - mean_r) * (log_l[i] - mean_l) for i in range(n))
    var = sum((log_r[i] - mean_r) ** 2 for i in range(n))
    slope = cov / var if var else 0.0
    pred = [mean_l + slope * (log_r[i] - mean_r) for i in range(n)]
    ss_res = sum((log_l[i] - pred[i]) ** 2 for i in range(n))
    ss_tot = sum((log_l[i] - mean_l) ** 2 for i in range(n))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "lang": lang,
        "n_functions": n,
        "max_length": lengths[0],
        "median_length": lengths[n // 2],
        "min_length": lengths[-1],
        "power_law_slope": slope,
        "power_law_r2": r2,
        "max_over_median_ratio": lengths[0] / max(1, lengths[n // 2]),
    }


def c2_cross_function_call_density(text: str, lang: str) -> dict:
    """CODE-modality variant of R4 callback density: cross-function call count."""
    # find function names defined in the file
    if lang == "C":
        funcs = set(m.group(1) for m in _C_FUNCTION_RE.finditer(text))
    elif lang == "PY":
        funcs = set(m.group(1) for m in _PY_FUNCTION_RE.finditer(text))
    else:
        return {"valid": False}
    if len(funcs) < 5:
        return {"valid": False, "n_funcs": len(funcs)}
    # count uses of those names elsewhere in the file (calls + references)
    all_idents = re.findall(_IDENT_RE, text)
    counts = collections.Counter(all_idents)
    # subtract one definition per function
    total_uses = sum(counts.get(f, 1) - 1 for f in funcs)
    n_lines = text.count("\n") + 1
    return {
        "valid": True,
        "lang": lang,
        "n_functions": len(funcs),
        "total_cross_uses": total_uses,
        "uses_per_function": total_uses / len(funcs),
        "n_lines": n_lines,
        "callbacks_per_1000_lines": (total_uses / n_lines) * 1000 if n_lines else 0,
    }


def c3_comment_density(text: str, lang: str) -> dict:
    if lang == "C":
        single_line_re = re.compile(r"//[^\n]*")
        block_re = re.compile(r"/\*.*?\*/", re.DOTALL)
    elif lang == "PY":
        single_line_re = re.compile(r"#[^\n]*")
        block_re = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', re.DOTALL)
    else:
        return {"valid": False}
    sls = single_line_re.findall(text)
    blocks = block_re.findall(text)
    comment_chars = sum(len(s) for s in sls) + sum(len(b) for b in blocks)
    total_chars = len(text)
    n_lines = text.count("\n") + 1
    return {
        "valid": True,
        "lang": lang,
        "n_single_line": len(sls),
        "n_block": len(blocks),
        "comment_char_fraction": comment_chars / max(1, total_chars),
        "comments_per_100_lines": (len(sls) + len(blocks)) / n_lines * 100 if n_lines else 0,
    }


def o1_repetition_density(text: str, window: int = 50) -> dict:
    """ORAL-modality variant: intentional repetition density.

    Oral traditions use repetition for mnemonic transmission. Sliding 50-word
    windows; count windows where N-gram (n=3) repeats from previous window.
    """
    words = [w for w in tokenize_words(text) if w not in STOPWORDS]
    if len(words) < 200:
        return {"valid": False}
    n = len(words)
    # rolling 3-gram counts
    threegrams = []
    for i in range(n - 2):
        threegrams.append((words[i], words[i + 1], words[i + 2]))
    counter = collections.Counter(threegrams)
    repeated_3grams = sum(1 for tg, c in counter.items() if c >= 2)
    repeated_3gram_total_occurrences = sum(c for tg, c in counter.items() if c >= 2)
    return {
        "valid": True,
        "n_words": n,
        "n_distinct_3grams": len(counter),
        "n_repeated_3grams": repeated_3grams,
        "repeated_3gram_fraction": repeated_3grams / max(1, len(counter)),
        "repeated_3gram_density_per_1k": (repeated_3gram_total_occurrences / n) * 1000,
    }


def o2_rhyme_regularity(text: str) -> dict:
    """ORAL-modality variant: end-rhyme regularity at line/sentence ends.

    Crude proxy for verse/song: tail-bigram coincidence in adjacent lines.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 5]
    if len(lines) < 20:
        return {"valid": False, "n_lines": len(lines)}

    def last_phon(line: str) -> str:
        # last "word" stripped of punctuation
        m = re.findall(r"[A-Za-z']+", line)
        if not m:
            return ""
        return m[-1][-3:].lower() if len(m[-1]) >= 3 else m[-1].lower()

    last_phons = [last_phon(l) for l in lines if last_phon(l)]
    if len(last_phons) < 10:
        return {"valid": False}
    # adjacent and ABAB rhyme counts
    adj_match = sum(1 for i in range(len(last_phons) - 1) if last_phons[i] == last_phons[i + 1] and last_phons[i])
    abab_match = sum(1 for i in range(len(last_phons) - 2) if last_phons[i] == last_phons[i + 2] and last_phons[i])
    return {
        "valid": True,
        "n_lines_with_phons": len(last_phons),
        "adjacent_rhyme_count": adj_match,
        "alternating_rhyme_count": abab_match,
        "adj_rhyme_rate": adj_match / max(1, len(last_phons) - 1),
        "alt_rhyme_rate": abab_match / max(1, len(last_phons) - 2),
    }


# ---------------------------------------------------------------------------
# Substrate-level dispatch
# ---------------------------------------------------------------------------


def detect_code_lang(path: str) -> Optional[str]:
    if path.endswith(".c") or path.endswith(".h"):
        return "C"
    if path.endswith(".py"):
        return "PY"
    return None


def signature_run(name: str, modality: str, text: str, source_url: Optional[str]) -> dict:
    """Run all signatures applicable to this substrate / modality."""
    out = {"substrate": name, "modality": modality}

    # text signatures (apply to all text-based modalities)
    out["R1_kladder"] = r1_word_freq_kladder(text)
    out["R2_para_pareto"] = r2_paragraph_length_pareto(text)
    out["R3_rare_cascade"] = r3_rare_word_cascade(text)
    out["R4_callbacks"] = r4_callback_density(text)
    out["S3_zipf"] = s3_zipf(text)
    out["S7_vocab"] = s7_vocab_richness(text)
    out["S6_cascade_beta"] = s6_concept_intro_rate(text)

    # modality-specific signatures
    if modality == "M5_CODE":
        # detect language from source url
        lang = None
        if source_url:
            if source_url.endswith(".c") or source_url.endswith(".h"):
                lang = "C"
            elif source_url.endswith(".py"):
                lang = "PY"
        if lang:
            out["C1_func_size_pareto"] = c1_code_function_size_pareto(text, lang)
            out["C2_cross_func_calls"] = c2_cross_function_call_density(text, lang)
            out["C3_comment_density"] = c3_comment_density(text, lang)

    if modality == "M6_ORAL":
        out["O1_repetition"] = o1_repetition_density(text)
        out["O2_rhyme"] = o2_rhyme_regularity(text)

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # Load corpus records to know what's available
    corpus_records_path = OUT_DIR / "spike_43c_corpus_records_2026-05-17.ndjson"
    if not corpus_records_path.exists():
        print(f"ERROR: corpus records not found at {corpus_records_path}")
        return

    substrates = []
    with corpus_records_path.open("r", encoding="utf-8") as f:
        for line in f:
            substrates.append(json.loads(line))

    # only process those with text
    fingerprint_records = []
    summary_lines = []
    for s in substrates:
        if s["status"] not in ("OK", "CACHED"):
            continue
        if s["n_chars"] < 5000:
            print(f"  [skip-thin]  {s['substrate_name']:<55} ({s['n_chars']} chars)")
            continue
        text_path = CORPUS_DIR / f"{s['substrate_name']}.txt"
        if not text_path.exists():
            print(f"  [skip-nofile] {s['substrate_name']}")
            continue
        text = text_path.read_text(encoding="utf-8", errors="replace")
        fp = signature_run(s["substrate_name"], s["modality"], text, s.get("url"))
        fp["date"] = "2026-05-17"
        fp["spike"] = "43c"
        fp["author"] = s.get("author")
        fp["title"] = s.get("title")
        fp["year"] = s.get("year")
        fp["n_chars"] = s["n_chars"]
        fingerprint_records.append(fp)
        # short summary line
        r1 = fp["R1_kladder"]
        r4 = fp["R4_callbacks"]
        r3 = fp["R3_rare_cascade"]
        s7 = fp["S7_vocab"]
        r2 = fp["R2_para_pareto"]
        print(
            f"  {s['substrate_name']:<55} {s['modality']:<14} "
            f"eps={r1.get('eps_unbiased_fit', float('nan')):.4f} "
            f"r4/1k={r4.get('callbacks_per_1000_words', float('nan')):>6.2f} "
            f"r3rate={r3.get('propagation_rate', float('nan')):.3f} "
            f"hapax={s7.get('hapax_fraction', float('nan')):.3f} "
            f"r2slope={r2.get('power_law_slope', float('nan')):.3f}"
        )

    out_path = OUT_DIR / "spike_43c_signature_records_2026-05-17.ndjson"
    with out_path.open("w", encoding="utf-8") as f:
        for rec in fingerprint_records:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\n  [write] {out_path}  ({len(fingerprint_records)} records)")


if __name__ == "__main__":
    main()
