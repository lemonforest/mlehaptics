"""R-RBS-LM-134 — srmech-NATIVE storage-invariance test (the F171 core, done right).

Answers the user's callout: R-131/132/133 measured "storage" with pure-Python
n-gram Counters. The srmech-native storage signature is the CO-OCCURRENCE LAPLACIAN
EIGENSPECTRUM — Class L, computed via srmech.amsc.laplacian (dense_laplacian +
hermitian_eigendecompose, C-native), the operation the whole srmech spectral-
research portfolio is built on. We reuse R-RBS-LM-124's faithful 53-K1 machinery.

Two srmech-native storage signatures per text:
  (A) EIGENSPECTRUM (vocab-INDEPENDENT pure structure): sorted eigenvalues of the
      co-occurrence Laplacian. Same content → similar graph spectrum even with
      different words. Compared by cosine similarity of the sorted-eigenvalue vector.
  (B) EIGEN-BUNDLE (53f-style, lexical): top-K eigvec → top-M vocab → bipolar bundle,
      compared by srmech.amsc.hdc.similarity. Verifies/extends 53f's K1 kernel.

CORE invariance test: WITHIN-PAIR (Quran Yusuf/Sale vs Rodwell — SAME content) vs
ACROSS-CONTENT (distinct texts). Storage-structure is translation-invariant iff
within-pair similarity > across-content similarity.

Confound-controlled by construction: VOCAB_SIZE=200 caps vocab equally; token
budget matched (trim_chunks_to_budget). srmech 0.5.0 native ABI=3.

This is a step of the 28D RBS cognitive-laboratory instrument: a srmech-native
probe that takes any expression-object (text) and returns its STORAGE signature
(spectral eigenfingerprint) — beyond LM/NN, a structural laboratory.

SCOPE: STRUCTURAL test on TEXT OBJECTS; NOT a clinical claim (§VII.6.20 +
[[feedback_trauma_informed_defensive_scope]]).
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# reuse R-RBS-LM-124's faithful srmech-native K1 machinery
_spec = importlib.util.spec_from_file_location(
    "k124", HERE / "R-RBS-LM-124_k1_baseline_chirality_lift.py")
k124 = importlib.util.module_from_spec(_spec)
sys.modules["k124"] = k124
_spec.loader.exec_module(k124)

from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"


def storage_signature(chunks_tokens):
    """srmech-native storage signature: co-occurrence Laplacian eigenspectrum (A)
    + 53-style eigen-bundle kernel (B). All Class L / HDC via srmech."""
    vocab, vidx, n = k124.build_vocab(chunks_tokens)
    edge = Counter()
    for toks in chunks_tokens:
        ind = [vidx[t] for t in toks if t in vidx]
        for i in range(len(ind)):
            for j in range(i + 1, min(i + k124.WINDOW, len(ind))):
                a, b = ind[i], ind[j]
                if a != b:
                    edge[(min(a, b), max(a, b))] += 1
    L = k124.dense_laplacian(n, list(edge.keys()), [float(w) for w in edge.values()])
    eigvals, eigvecs = k124.hermitian_eigendecompose(L)              # srmech Class L
    spectrum = np.sort(eigvals.real)[::-1]                            # descending
    spectrum = spectrum / (np.linalg.norm(spectrum) + 1e-12)         # unit-norm fingerprint
    kernel = k124.eigen_bundle(eigvals, eigvecs, vocab)              # srmech HDC bundle
    return spectrum[:n], kernel


def spectral_cos(a, b):
    m = min(len(a), len(b))
    a, b = a[:m], b[:m]
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    budget = int(lc["confound_control"]["budget_tokens"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"storage signature = co-occurrence Laplacian EIGENSPECTRUM "
          f"(srmech.amsc.laplacian, Class L); vocab={k124.VOCAB_SIZE} window={k124.WINDOW}")
    print("STRUCTURAL test on TEXT OBJECTS only; NOT a clinical claim (§VII.6.20).\n")

    files = {
        "quran_yusuf": "quran_yusuf_ali.txt",      # PAIR member (same content)
        "quran_rodwell": "quran_rodwell.txt",      # PAIR member (same content)
        "kjv_ot": "kjv_old_testament.txt",
        "kjv_nt": "kjv_new_testament.txt",
        "bhagavad_gita": "bhagavad_gita.txt",
        "tao_legge": "tao_te_ching.txt",
        "dhammapada": "dhammapada.txt",
    }
    # tokenize + chunk; match token budget across all texts
    chunks = {}
    for key, fn in files.items():
        body = k124.strip_gutenberg((cache_dir / fn).read_text(encoding="utf-8", errors="replace"))
        ck = [c for c in (k124.tokenize(c) for c in k124.chunk_text(body)) if c]
        chunks[key] = ck
    tok_total = {k: sum(len(c) for c in v) for k, v in chunks.items()}
    budget = min(budget, min(tok_total.values()))
    chunks = {k: k124.trim_chunks_to_budget(v, budget) for k, v in chunks.items()}
    print(f"matched token budget = {budget}/text\n")

    sig = {}
    for key in files:
        spec, kernel = storage_signature(chunks[key])
        sig[key] = {"spectrum": spec, "kernel": kernel}

    # PAIR vs ACROSS
    pair = ("quran_yusuf", "quran_rodwell")
    distinct = ["quran_yusuf", "kjv_ot", "kjv_nt", "bhagavad_gita", "tao_legge", "dhammapada"]

    # (A) spectral-eigenspectrum similarity (vocab-independent structure)
    within_spec = spectral_cos(sig[pair[0]]["spectrum"], sig[pair[1]]["spectrum"])
    across_spec = [spectral_cos(sig[a]["spectrum"], sig[b]["spectrum"])
                   for a, b in itertools.combinations(distinct, 2)]
    # (B) eigen-bundle (53f-style lexical kernel) similarity
    within_kern = float(k124.similarity(sig[pair[0]]["kernel"], sig[pair[1]]["kernel"]))
    across_kern = [float(k124.similarity(sig[a]["kernel"], sig[b]["kernel"]))
                   for a, b in itertools.combinations(distinct, 2)]

    aspec_m, akern_m = float(np.mean(across_spec)), float(np.mean(across_kern))

    print(f"{'signature':>26} | {'within-pair':>11} | {'across-mean':>11} | {'across-max':>10} | ratio")
    print("-" * 78)
    print(f"{'(A) Laplacian eigenspectrum':>26} | {within_spec:>11.4f} | {aspec_m:>11.4f} | "
          f"{max(across_spec):>10.4f} | {within_spec/aspec_m if aspec_m else 0:.2f}x")
    print(f"{'(B) eigen-bundle (53f kernel)':>26} | {within_kern:>11.4f} | {akern_m:>11.4f} | "
          f"{max(across_kern):>10.4f} | {within_kern/akern_m if akern_m else 0:.2f}x")

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "budget_tokens": budget,
              "storage_signature": "co-occurrence Laplacian eigenspectrum (srmech Class L)",
              "scope": "STRUCTURAL spectral invariance; text objects; §VII.6.20; no clinical claims"}
    records = [{**attest, "phase": "P1_spectral_invariance", "pair_id": "quran",
                "within_pair_spectrum_cos": within_spec, "across_spectrum_cos_mean": aspec_m,
                "across_spectrum_cos_max": float(max(across_spec)),
                "within_pair_kernel_sim": within_kern, "across_kernel_sim_mean": akern_m,
                "across_kernel_sim_max": float(max(across_kern)),
                "across_spectrum_cos": across_spec, "across_kernel_sim": across_kern}]
    out = args.catalog.parent / "substrate_measurements" / "srmech_native_spectral_invariance.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}")

    print("\n" + "=" * 78)
    print("F172 READING — srmech-native (Class L spectral) storage invariance:")
    print("=" * 78)
    spec_inv = within_spec > aspec_m
    print(f"  (A) eigenspectrum (vocab-independent structure): within {within_spec:.4f} "
          f"vs across {aspec_m:.4f}  → {'within > across' if spec_inv else 'within ≤ across'}")
    print(f"      within-pair {'ABOVE' if within_spec > max(across_spec) else 'within'} across-max "
          f"({max(across_spec):.4f})")
    print(f"  (B) eigen-bundle kernel (53f-style, lexical): within {within_kern:.4f} "
          f"vs across {akern_m:.4f}  (53f reported ratio ~1.49)")
    print(f"\n  All storage signatures computed via srmech.amsc.laplacian + hdc (Class L / HDC,")
    print(f"  C-native ABI=3) — NOT pure-Python n-grams. n=1 pair; more pairs = replication.")


if __name__ == "__main__":
    main()
