"""Spike #147 — Local lexicon-encoding pipeline.

Goal
----
Build a LOCAL pipeline that ingests user-prompt corpora (Claude Code JSONL
transcripts) and produces an inspectable HDC structural-image fingerprint
via Class A (hashing) + Class M (HDC bind/bundle) + Class L (Laplacian
eigvals) + Class K (sparse-truncate). No external API calls.

Per spike spec:
  D = 8192 bits = 1024 bytes (matches Spike #142 standard).
  Top-N = 64 eigencomponents (project sparse-truncate standard).
  Window = 5 for co-occurrence graph.
  Cap n_tokens at 1000 by frequency (Laplacian tractable; numpy fallback).
  Bundle MAX_BUNDLE_N = 257 → chunked bundling.

Outputs NDJSON (one record per line) per `[[feedback_ndjson_over_bloated_json]]`.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np

from srmech.amsc.hdc import bind, bundle, similarity
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals

# ----- Constants (no magic numbers) -----------------------------------------

HDC_BYTES = 1024  # = 8192 bits (Spike #142 standard)
HDC_BITS = 8 * HDC_BYTES
COOCCURRENCE_WINDOW = 5
TOP_N_TOKENS = 1000  # Laplacian dimension cap
TOP_N_EIGENCOMPONENTS = 64  # Class K sparse-truncate
MIN_TOKEN_LEN = 2
BUNDLE_CHUNK = 257  # MAX_BUNDLE_N from srmech.amsc.hdc
TIE_BREAKER_NAMESPACE = b"spike147:tie-breaker"

# Reasonable English stop-word set — kept SHORT so user-lexicon outliers
# remain visible. Long stop-lists kill structural signal.
STOP_WORDS = frozenset(
    "the of and to a in is it that this for as on with be by are was an "
    "or at from but not have has had can will would should which who whom "
    "do does did so if then than there here their them they we us our you "
    "your i me my mine he she his her its".split()
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]+")


# ----- Class A: SHA-256 deterministic vector mint ---------------------------


def vec_for_token(token: str, namespace: bytes = b"spike147:token") -> bytes:
    """Deterministic D-bit vector for a token via SHA-256 expansion.

    Class A primitive. Uses XOF-style block expansion: repeated SHA-256 of
    (namespace || token || counter) until HDC_BYTES bytes are accumulated.
    """
    out = bytearray()
    counter = 0
    seed = namespace + b"|" + token.encode("utf-8") + b"|"
    while len(out) < HDC_BYTES:
        h = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:HDC_BYTES])


def vec_for_position(idx: int) -> bytes:
    """Deterministic D-bit vector for a position index."""
    return vec_for_token(f"pos:{idx}", namespace=b"spike147:position")


# ----- Class M: HDC bind/bundle with chunked bundling -----------------------


def chunked_bundle(vectors: list[bytes]) -> bytes:
    """Bundle arbitrary count of vectors via hierarchical chunked majority.

    BSC bundle requires odd count and ≤ MAX_BUNDLE_N. We split into
    odd-sized chunks ≤ BUNDLE_CHUNK, bundle each, then recurse on the
    partial-bundles. Adds a deterministic tie-breaker vector when the
    count is even.
    """
    if not vectors:
        raise ValueError("chunked_bundle: empty input")
    tie = vec_for_token("tie-breaker", namespace=TIE_BREAKER_NAMESPACE)
    while len(vectors) > 1:
        if len(vectors) <= BUNDLE_CHUNK:
            vs = vectors if len(vectors) % 2 == 1 else vectors + [tie]
            return bundle(vs)
        next_layer: list[bytes] = []
        i = 0
        while i < len(vectors):
            chunk = vectors[i : i + BUNDLE_CHUNK]
            if len(chunk) == 1:
                next_layer.append(chunk[0])
            else:
                if len(chunk) % 2 == 0:
                    chunk = chunk + [tie]
                next_layer.append(bundle(chunk))
            i += BUNDLE_CHUNK
        vectors = next_layer
    return vectors[0]


def encode_sequence(tokens: list[str]) -> bytes:
    """Encode a token sequence as a single HDC fingerprint.

    For each position i with token t:
        v_i = bind(vec_for_position(i), vec_for_token(t))
    Then bundle all v_i.
    """
    bound = [bind(vec_for_position(i), vec_for_token(t)) for i, t in enumerate(tokens)]
    return chunked_bundle(bound)


def encode_bag(tokens: list[str]) -> bytes:
    """Encode a token bag (position-free) as a single HDC fingerprint.

    Position-free encoding is the holographic-projection-test natural form:
    paraphrases of same meaning share token bag (~) but differ in order.
    Class M bundle without position-bind isolates the meaning component.
    """
    return chunked_bundle([vec_for_token(t) for t in tokens])


# ----- Tokenization ---------------------------------------------------------


def tokenize(text: str, drop_stopwords: bool = True) -> list[str]:
    """Lowercase + regex split; drop short tokens and (optionally) stopwords."""
    tokens = [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]
    tokens = [t for t in tokens if len(t) >= MIN_TOKEN_LEN]
    if drop_stopwords:
        tokens = [t for t in tokens if t not in STOP_WORDS]
    return tokens


# ----- Transcript extraction (Claude Code JSONL) ----------------------------


# System-injected pseudo-user records that should NOT count as
# user-authored prose. These are tool / harness output that Claude Code
# wraps as role="user" for the assistant's next turn.
_SYSTEM_TAGS = (
    "<task-notification>",
    "<system-reminder>",
    "<bash-input>",
    "<bash-stdout>",
    "<bash-stderr>",
    "<command-message>",
    "<command-args>",
    "<command-name>",
    "<local-command-stdout>",
    "<user-memory-input>",
)


def _looks_like_system_injection(text: str) -> bool:
    """Heuristic: text starts with a known system-injected XML tag."""
    if not text:
        return False
    stripped = text.lstrip()
    return any(stripped.startswith(tag) for tag in _SYSTEM_TAGS)


def iter_user_messages_from_jsonl(path: Path) -> Iterator[str]:
    """Stream user-message text content from one Claude Code JSONL.

    Each JSONL line is a record. We accept records where
        record["type"] == "user"  OR  record["role"] == "user"
    and extract any string content (drops tool-result records — those have
    structured content and are not user-authored prose). Also drops
    system-injected pseudo-user records (task-notification, system-reminder,
    bash-input/stdout/stderr, command-message, etc.) — those are tool /
    harness wrappers that Claude Code feeds back as role="user".
    """
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Claude Code schema: rec["type"] == "user" wraps rec["message"]
            msg = rec.get("message") or rec
            if not isinstance(msg, dict):
                continue
            role = msg.get("role") or rec.get("type")
            if role != "user":
                continue
            content = msg.get("content")
            if isinstance(content, str):
                # Skip tool-result strings (those start with structured markers)
                if content.startswith("[{") or content.startswith("{"):
                    continue
                if _looks_like_system_injection(content):
                    continue
                yield content
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text = part.get("text") or ""
                        if text and not _looks_like_system_injection(text):
                            yield text


def collect_user_corpus(jsonl_paths: list[Path], drop_stopwords: bool = True) -> list[str]:
    """Read all user prompts from all JSONLs; return token stream."""
    tokens: list[str] = []
    n_msgs = 0
    n_chars = 0
    for p in jsonl_paths:
        for text in iter_user_messages_from_jsonl(p):
            n_msgs += 1
            n_chars += len(text)
            tokens.extend(tokenize(text, drop_stopwords=drop_stopwords))
    print(
        f"[corpus] {len(jsonl_paths)} files | {n_msgs} user msgs | "
        f"{n_chars} chars | {len(tokens)} tokens",
        file=sys.stderr,
    )
    return tokens


# ----- Class L: co-occurrence Laplacian + Class K sparse-truncate -----------


def cooccurrence_edges(
    tokens: list[str], vocab: dict[str, int], window: int
) -> tuple[list[tuple[int, int]], list[float]]:
    """Build co-occurrence edge list weighted by co-occurrence count."""
    counts: dict[tuple[int, int], int] = collections.Counter()
    indices = [vocab.get(t, -1) for t in tokens]
    n = len(indices)
    for i in range(n):
        ai = indices[i]
        if ai < 0:
            continue
        jmax = min(n, i + window + 1)
        for j in range(i + 1, jmax):
            bj = indices[j]
            if bj < 0 or bj == ai:
                continue
            u, v = (ai, bj) if ai < bj else (bj, ai)
            counts[(u, v)] += 1
    edges = list(counts.keys())
    weights = [float(c) for c in counts.values()]
    return edges, weights


def laplacian_top_k(
    n: int, edges: list[tuple[int, int]], weights: list[float], k: int
) -> np.ndarray:
    """Compute Laplacian, eigvalues; return top-k by magnitude.

    Top by MAGNITUDE = largest eigenvalues (Class K sparse-truncate per
    standard project convention; smallest are dominated by the zero-mode).
    """
    L = dense_laplacian(n, edges, weights)
    eigs = jacobi_eigvals(L)  # ascending
    # Top-k by magnitude:
    k = min(k, len(eigs))
    return np.sort(eigs)[::-1][:k]


# ----- Main encoder pipeline ------------------------------------------------


def build_fingerprint(
    tokens: list[str],
    *,
    top_vocab: int = TOP_N_TOKENS,
    window: int = COOCCURRENCE_WINDOW,
    top_eigs: int = TOP_N_EIGENCOMPONENTS,
) -> dict:
    """Run the full pipeline; return summary dict (NDJSON-ready)."""
    if not tokens:
        return {
            "ok": False,
            "reason": "empty-token-stream",
        }
    counter = collections.Counter(tokens)
    top_tokens = [t for t, _ in counter.most_common(top_vocab)]
    vocab = {t: i for i, t in enumerate(top_tokens)}

    edges, weights = cooccurrence_edges(tokens, vocab, window)
    n_nodes = len(top_tokens)
    if n_nodes == 0 or not edges:
        return {"ok": False, "reason": "no-edges", "n_tokens_raw": len(tokens)}

    t0 = time.time()
    top_k_eigs = laplacian_top_k(n_nodes, edges, weights, top_eigs)
    t_lap = time.time() - t0

    # HDC fingerprints
    t1 = time.time()
    # Bag fingerprint over top vocab (deterministic; ignores corpus order
    # within top-1000 vocab; suitable for similarity comparison).
    bag_fp = encode_bag(top_tokens)
    t_bag = time.time() - t1

    # Sequence fingerprint over the FIRST top_vocab-worth of token positions.
    # Keeps the pipeline ~ linear in vocab size and not corpus size.
    t2 = time.time()
    seq_tokens = tokens[: top_vocab * 5]
    seq_fp = encode_sequence(seq_tokens)
    t_seq = time.time() - t2

    return {
        "ok": True,
        "n_tokens_raw": len(tokens),
        "n_unique_tokens": len(counter),
        "n_vocab_kept": n_nodes,
        "n_edges": len(edges),
        "top_20_tokens": [
            {"token": t, "count": int(counter[t])} for t in top_tokens[:20]
        ],
        "top_k_eigvalues": [float(x) for x in top_k_eigs],
        "n_eigs_kept": int(len(top_k_eigs)),
        "bag_fingerprint_sha256": hashlib.sha256(bag_fp).hexdigest(),
        "seq_fingerprint_sha256": hashlib.sha256(seq_fp).hexdigest(),
        "seq_tokens_count": len(seq_tokens),
        "timing_seconds": {
            "laplacian_and_eigs": round(t_lap, 3),
            "bag_fingerprint": round(t_bag, 3),
            "seq_fingerprint": round(t_seq, 3),
        },
        "config": {
            "hdc_bytes": HDC_BYTES,
            "hdc_bits": HDC_BITS,
            "cooccurrence_window": window,
            "top_n_tokens": top_vocab,
            "top_n_eigencomponents": top_eigs,
            "min_token_len": MIN_TOKEN_LEN,
            "n_stopwords": len(STOP_WORDS),
        },
    }


def fingerprint_bytes(tokens: list[str], top_vocab: int = TOP_N_TOKENS) -> tuple[bytes, bytes]:
    """Return (bag_fp, seq_fp) bytes — usable for similarity comparisons."""
    counter = collections.Counter(tokens)
    top_tokens = [t for t, _ in counter.most_common(top_vocab)]
    if not top_tokens:
        empty = bytes(HDC_BYTES)
        return empty, empty
    bag_fp = encode_bag(top_tokens)
    seq_tokens = tokens[: top_vocab * 5]
    if not seq_tokens:
        seq_fp = bag_fp
    else:
        seq_fp = encode_sequence(seq_tokens)
    return bag_fp, seq_fp


# ----- CLI ------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Spike #147 local lexicon encoder")
    parser.add_argument(
        "--transcripts",
        nargs="+",
        required=True,
        help="Paths to Claude Code JSONL transcript files OR directories",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="NDJSON output path",
    )
    parser.add_argument("--top-vocab", type=int, default=TOP_N_TOKENS)
    parser.add_argument("--top-eigs", type=int, default=TOP_N_EIGENCOMPONENTS)
    parser.add_argument("--window", type=int, default=COOCCURRENCE_WINDOW)
    parser.add_argument(
        "--no-stopword-drop", action="store_true", help="Keep stopwords"
    )
    args = parser.parse_args()

    jsonl_paths: list[Path] = []
    for t in args.transcripts:
        p = Path(t)
        if p.is_dir():
            jsonl_paths.extend(sorted(p.glob("*.jsonl")))
        elif p.suffix == ".jsonl":
            jsonl_paths.append(p)
    if not jsonl_paths:
        print("no JSONL transcripts found", file=sys.stderr)
        return 2

    tokens = collect_user_corpus(jsonl_paths, drop_stopwords=not args.no_stopword_drop)
    summary = build_fingerprint(
        tokens,
        top_vocab=args.top_vocab,
        window=args.window,
        top_eigs=args.top_eigs,
    )
    summary["spike"] = "147"
    summary["transcript_paths"] = [str(p) for p in jsonl_paths]
    summary["transcript_count"] = len(jsonl_paths)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(f"[ok] wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
