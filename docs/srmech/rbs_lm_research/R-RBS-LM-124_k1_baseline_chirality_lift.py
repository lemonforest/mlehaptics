"""R-RBS-LM-124 — True R-RBS-LM-53 K1 baseline + 28D directed-chirality lift test.

Answers the headline question cleanly: does the 28D bi-axial chirality
decomposition LIFT the flat-spectral degeneracy R-RBS-LM-53 measured?

THE 53 K1 BASELINE (reproduced faithfully):
  build_K1 = Class L (Laplacian) spectral kernel over an UNDIRECTED
  co-occurrence graph. Critically, 53 symmetrized every edge:
      edge_count[(min(a,b), max(a,b))] += 1
  → the co-occurrence Laplacian is γ₅-EVEN (direction discarded). Top-K=33
  eigenvectors → top-M=21 vocab each → bipolar-mint bundle. This is the kernel
  that gave the Abrahamic texts near-identical signatures (the "0.99 ceiling").

THE 28D CHIRALITY LIFT (the new test):
  The information 53 threw away by symmetrizing IS the chirality (γ₅-odd) axis.
  Build the DIRECTED co-occurrence A (a precedes b within window). Its
  antisymmetric part  A_anti = A − Aᵀ  is the word-order chirality. Form the
  Hermitian  H_chiral = i·A_anti  (skew-real → Hermitian; real eigenvalues),
  eigendecompose (srmech Class L hermitian_eigendecompose), bundle the top
  eigenvector vocab the same way → K1-chiral.

  TEST: does K1-chiral SEPARATE texts that K1-flat merged? Focus on the
  within-Abrahamic triangle (Quran / KJV-OT / KJV-NT) where 53 found the
  degeneracy. If chiral within-Abrahamic similarity drops well below flat →
  28D chirality lifts the ceiling. If it stays high → ceiling holds at
  chirality depth (F142 null; DOMAIN anchor still required).

SCOPE: structural/spectral ONLY. Texts are structural test-objects. No
doctrinal/truth/origin/ranking claims. §VII.6.20 honored.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.amsc import format as amsc_format
from srmech.signal_processing import mint_vector
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

VARIANT = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"

_GUT_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG", re.I)
_GUT_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG", re.I)
_WORD = re.compile(r"[a-z]+")

# K1 params — faithful to R-RBS-LM-53 build_K1
K_EIG = 33
M_VOCAB = 21
VOCAB_SIZE = 200
WINDOW = 5
N_CHUNKS = 64
_MINT_CACHE: dict[str, np.ndarray] = {}


def strip_gutenberg(text: str) -> str:
    lines = text.splitlines()
    start, end = 0, len(lines)
    for i, ln in enumerate(lines):
        if _GUT_START.search(ln):
            start = i + 1
            break
    for i in range(len(lines) - 1, -1, -1):
        if _GUT_END.search(lines[i]):
            end = i
            break
    return "\n".join(lines[start:end])


def mint(token: str) -> np.ndarray:
    if token not in _MINT_CACHE:
        _MINT_CACHE[token] = np.frombuffer(mint_vector(token, D=8192), dtype=np.uint8)
    return _MINT_CACHE[token]


def chunk_text(text: str, n_chunks: int = N_CHUNKS):
    raw_chunks = re.split(r"\n\s*\n+", text)
    target = max(len(text) // n_chunks, 1000)
    out, buf = [], ""
    for c in raw_chunks:
        buf += "\n" + c
        if len(buf) >= target:
            out.append(buf); buf = ""
    if buf.strip():
        out.append(buf)
    return out


def tokenize(text: str):
    return _WORD.findall(text.lower())


def build_vocab(chunks_tokens):
    freq = Counter(t for toks in chunks_tokens for t in toks)
    n = min(VOCAB_SIZE, len(freq))
    vocab = [t for t, _ in freq.most_common(n)]
    return vocab, {t: i for i, t in enumerate(vocab)}, n


def eigen_bundle(eigvals, eigvecs, vocab):
    """Top-K eigvecs → top-M vocab by |component|² each → bipolar-mint bundle."""
    order = np.argsort(eigvals.real)            # ascending
    top = order[-K_EIG:][::-1]                  # largest K
    hvs = []
    for k in top:
        ev = np.abs(eigvecs[:, k]) ** 2
        idx = np.argsort(-ev)[:M_VOCAB]
        hvs.append(bundle([mint(vocab[i]) for i in idx]))
    return bundle(hvs)


def build_K1_flat(chunks_tokens):
    """53 K1: UNDIRECTED co-occurrence Laplacian spectral kernel (γ₅-even)."""
    vocab, vidx, n = build_vocab(chunks_tokens)
    edge = Counter()
    for toks in chunks_tokens:
        ind = [vidx[t] for t in toks if t in vidx]
        for i in range(len(ind)):
            for j in range(i + 1, min(i + WINDOW, len(ind))):
                a, b = ind[i], ind[j]
                if a != b:
                    edge[(min(a, b), max(a, b))] += 1   # symmetrized — direction discarded
    L = dense_laplacian(n, list(edge.keys()), [float(w) for w in edge.values()])
    eigvals, eigvecs = hermitian_eigendecompose(L)
    return eigen_bundle(eigvals, eigvecs, vocab), vocab


def build_K1_chiral(chunks_tokens, vocab):
    """28D lift: DIRECTED co-occurrence antisymmetric part as Hermitian i·(A−Aᵀ)."""
    vidx = {t: i for i, t in enumerate(vocab)}
    n = len(vocab)
    A = np.zeros((n, n), dtype=np.float64)
    for toks in chunks_tokens:
        ind = [vidx[t] for t in toks if t in vidx]
        for i in range(len(ind)):
            for j in range(i + 1, min(i + WINDOW, len(ind))):
                a, b = ind[i], ind[j]
                if a != b:
                    A[a, b] += 1.0                       # DIRECTED: a precedes b
    A_anti = A - A.T                                      # γ₅-odd word-order chirality
    H = 1j * A_anti                                       # skew-real → Hermitian
    eigvals, eigvecs = hermitian_eigendecompose(H)
    chiral_energy = float(np.sum(np.abs(A_anti))) / (float(np.sum(A)) + 1e-9)
    return eigen_bundle(eigvals, eigvecs, vocab), chiral_energy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=VARIANT)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    texts = lc["corpus"]["texts"]

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"K1 params: K={K_EIG} M={M_VOCAB} vocab={VOCAB_SIZE} window={WINDOW} chunks={N_CHUNKS}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...\n")

    keys, labels, fams = [], {}, {}
    flat_kernels, chiral_kernels, chiral_energy = {}, {}, {}
    for key, meta in texts.items():
        path = cache_dir / meta["filename"]
        body = strip_gutenberg(path.read_text(encoding="utf-8", errors="replace"))
        chunks = [tokenize(c) for c in chunk_text(body)]
        chunks = [c for c in chunks if c]
        kf, vocab = build_K1_flat(chunks)
        kc, ce = build_K1_chiral(chunks, vocab)
        flat_kernels[key] = kf
        chiral_kernels[key] = kc
        chiral_energy[key] = ce
        keys.append(key); labels[key] = meta["label"]; fams[key] = meta["family"]
        print(f"  {meta['label']:34s} fam={meta['family']:9s} chunks={len(chunks):4d} chiral_energy={ce:.4f}")

    def matrix(kernels, title):
        print("\n" + "=" * 92)
        print(title)
        print("=" * 92)
        print("           " + "  ".join(f"{k[:8]:>8}" for k in keys))
        m = {}
        for ki in keys:
            row = []
            for kj in keys:
                s = float(similarity(kernels[ki], kernels[kj]))
                m[(ki, kj)] = s
                row.append(s)
            print(f"  {ki[:9]:>9} " + "  ".join(f"{s:8.4f}" for s in row))
        return m

    flat_m = matrix(flat_kernels, "K1-FLAT (53 reproduction: undirected co-occurrence Laplacian — γ₅-even)")
    chiral_m = matrix(chiral_kernels, "K1-CHIRAL (directed antisymmetric Hermitian i·(A−Aᵀ) — γ₅-odd)")

    # Within-Abrahamic triangle — where 53 found the degeneracy
    abr = [k for k in keys if fams[k] == "abrahamic"]
    def within(m, group):
        vals = [m[(a, b)] for a in group for b in group if a != b]
        return float(np.mean(vals)) if vals else float("nan")
    def across(m):
        vals = [m[(a, b)] for a in keys for b in keys
                if a != b and fams[a] != fams[b]]
        return float(np.mean(vals))

    print("\n" + "=" * 92)
    print("LIFT TEST — within-Abrahamic similarity (the 53 degeneracy triangle)")
    print("=" * 92)
    fw, cw = within(flat_m, abr), within(chiral_m, abr)
    fa, ca = across(flat_m), across(chiral_m)
    print(f"  within-Abrahamic   FLAT={fw:.4f}   CHIRAL={cw:.4f}   (drop {fw - cw:+.4f})")
    print(f"  across-family      FLAT={fa:.4f}   CHIRAL={ca:.4f}")
    print(f"  flat  contrast (within/across)   = {fw / fa:.3f}")
    print(f"  chiral contrast (within/across)  = {cw / ca:.3f}" if ca > 1e-6 else "  chiral across ~0")

    print("\n" + "=" * 92)
    # Lift = chirality makes within-Abrahamic LESS similar (separates) relative to flat
    lifts = (fw > 0.5) and (cw < fw - 0.10)
    print("VERDICT:")
    print(f"  flat degenerate within-Abrahamic?  {fw > 0.5} (sim {fw:.3f})")
    print(f"  chirality separates them?          {cw < fw - 0.10} (chiral sim {cw:.3f}, drop {fw-cw:+.3f})")
    if lifts:
        print("  → 28D directed-chirality LIFTS the 53 flat-spectral degeneracy")
    else:
        print("  → ceiling HOLDS at chirality depth (F142 null; DOMAIN anchor still required)")

    # MPR-attested NDJSON
    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE,
              "scope": "STRUCTURAL-ONLY per MFO VII.6.20; no doctrinal/ranking claims"}
    recs = [{**attest, "phase": "P0_header", "k1_params": {"K": K_EIG, "M": M_VOCAB,
             "vocab": VOCAB_SIZE, "window": WINDOW},
             "within_abrahamic_flat": fw, "within_abrahamic_chiral": cw,
             "across_family_flat": fa, "across_family_chiral": ca,
             "chirality_lifts": bool(lifts)}]
    for k in keys:
        recs.append({**attest, "phase": "P1_kernel", "text_key": k, "text_label": labels[k],
                     "family": fams[k], "chiral_energy": chiral_energy[k],
                     "flat_self": flat_m[(k, k)]})
    out = args.catalog.parent / "substrate_measurements" / "religious_texts_k1_chirality.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in recs:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(recs)} records)")


if __name__ == "__main__":
    main()
