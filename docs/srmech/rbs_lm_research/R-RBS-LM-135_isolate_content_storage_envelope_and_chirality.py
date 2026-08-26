"""R-RBS-LM-135 — 28D instrument: isolate content-specific storage by (C) subtracting
the universal spectral envelope and (D) using the 28D chirality (γ₅-odd) coordinate.

F172 left the frontier: the pure co-occurrence-Laplacian eigenspectrum is at the
universal flat-spectral ceiling (can't discriminate), and the lexical kernel that
DOES discriminate is expression-laden. The hypothesis needs a signature that is
content-specific BUT expression-independent. Two srmech-native candidates:

  (C) ENVELOPE-SUBTRACTED spectrum: residual = text_spectrum − mean_spectrum(all).
      Removes the universal language-graph envelope; the residual is the
      content-specific deviation. Test: is the residual translation-INVARIANT
      (within-pair > across-content)?
  (D) 28D CHIRALITY signature: the K1-chiral bundle (R-124) — eigen-bundle of the
      DIRECTED γ₅-odd antisymmetric co-occurrence H = i·(A−Aᵀ), the word-ORDER
      structure the symmetric spectrum discards. Test: is chirality
      translation-invariant (within-pair > across-content)? (F163 found chirality
      did not lift DISCRIMINATION across different texts; INVARIANCE across
      same-content translations is a distinct question.)

All via srmech Class L (dense_laplacian / hermitian_eigendecompose) + HDC. Reuses
R-124/R-134. Quran Yusuf/Sale vs Rodwell (attested) + distinct-content reference.

This is the next component of the 28D RBS cognitive-laboratory instrument: a
storage probe that factors the universal envelope off and reads the 28D chirality
coordinate. STRUCTURAL test on text objects; §VII.6.20; no clinical claims.
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

_spec = importlib.util.spec_from_file_location(
    "k124", HERE / "R-RBS-LM-124_k1_baseline_chirality_lift.py")
k124 = importlib.util.module_from_spec(_spec)
sys.modules["k124"] = k124
_spec.loader.exec_module(k124)

from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"


def flat_spectrum(chunks_tokens):
    """Co-occurrence Laplacian eigenspectrum (Class L, srmech), sorted desc, unit-norm."""
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
    eigvals, _ = k124.hermitian_eigendecompose(L)
    s = np.sort(eigvals.real)[::-1]
    return s / (np.linalg.norm(s) + 1e-12), vocab


def cos(a, b):
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
    print("28D instrument: (C) envelope-subtracted spectrum + (D) chirality coordinate")
    print("STRUCTURAL test on text objects; §VII.6.20; no clinical claims.\n")

    files = {
        "quran_yusuf": "quran_yusuf_ali.txt", "quran_rodwell": "quran_rodwell.txt",
        "kjv_ot": "kjv_old_testament.txt", "kjv_nt": "kjv_new_testament.txt",
        "bhagavad_gita": "bhagavad_gita.txt", "tao_legge": "tao_te_ching.txt",
        "dhammapada": "dhammapada.txt",
    }
    chunks = {}
    for key, fn in files.items():
        body = k124.strip_gutenberg((cache_dir / fn).read_text(encoding="utf-8", errors="replace"))
        chunks[key] = [c for c in (k124.tokenize(c) for c in k124.chunk_text(body)) if c]
    budget = min(budget, min(sum(len(c) for c in v) for v in chunks.values()))
    chunks = {k: k124.trim_chunks_to_budget(v, budget) for k, v in chunks.items()}
    print(f"matched token budget = {budget}/text\n")

    spec, chiral, chiral_e = {}, {}, {}
    for key in files:
        s, vocab = flat_spectrum(chunks[key])
        spec[key] = s
        cb, ce = k124.build_K1_chiral(chunks[key], vocab)   # 28D γ₅-odd directed part
        chiral[key] = cb
        chiral_e[key] = ce

    # (C) envelope subtraction: residual content-specific spectrum
    L = min(len(s) for s in spec.values())
    M = np.stack([spec[k][:L] for k in files])
    envelope = M.mean(axis=0)
    resid = {k: spec[k][:L] - envelope for k in files}

    pair = ("quran_yusuf", "quran_rodwell")
    distinct = ["quran_yusuf", "kjv_ot", "kjv_nt", "bhagavad_gita", "tao_legge", "dhammapada"]

    def within_across(simfn):
        w = simfn(pair[0], pair[1])
        prs = list(itertools.combinations(distinct, 2))
        a = [simfn(x, y) for x, y in prs]
        amax_i = int(np.argmax(a))
        return w, float(np.mean(a)), float(max(a)), a, prs[amax_i]

    cw, cam, cax, cacross, cmaxpair = within_across(lambda x, y: cos(resid[x], resid[y]))
    dw, dam, dax, dacross, dmaxpair = within_across(lambda x, y: float(k124.similarity(chiral[x], chiral[y])))
    print(f"  across-MAX driven by: (C) {cmaxpair}   (D) {dmaxpair}\n")

    print(f"{'signature':>34} | {'within':>7} | {'across-mean':>11} | {'across-max':>10} | ratio | beats-max?")
    print("-" * 92)
    print(f"{'(C) envelope-subtracted spectrum':>34} | {cw:>7.4f} | {cam:>11.4f} | {cax:>10.4f} | "
          f"{cw/cam if cam else 0:>4.2f}x | {cw > cax}")
    print(f"{'(D) 28D chirality (K1-chiral)':>34} | {dw:>7.4f} | {dam:>11.4f} | {dax:>10.4f} | "
          f"{dw/dam if dam else 0:>4.2f}x | {dw > dax}")
    print(f"\n  chiral energy (γ₅-odd / total) per text: "
          + ", ".join(f"{k.split('_')[0]}={chiral_e[k]:.3f}" for k in files))

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "budget_tokens": budget,
              "scope": "STRUCTURAL 28D storage isolation; text objects; §VII.6.20; no clinical claims"}
    rec = [{**attest, "phase": "P1_isolate", "pair_id": "quran",
            "envelope_resid_within": cw, "envelope_resid_across_mean": cam,
            "envelope_resid_across_max": cax, "envelope_beats_max": bool(cw > cax),
            "chirality_within": dw, "chirality_across_mean": dam,
            "chirality_across_max": dax, "chirality_beats_max": bool(dw > dax),
            "chiral_energy": chiral_e}]
    out = args.catalog.parent / "substrate_measurements" / "isolate_content_storage.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in rec:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}")

    print("\n" + "=" * 92)
    print("R-135 READING — does either signature ISOLATE content-specific, translation-invariant storage?")
    print("=" * 92)
    for name, w, am, ax in (("(C) envelope-subtracted spectrum", cw, cam, cax),
                            ("(D) 28D chirality coordinate", dw, dam, dax)):
        verdict = ("ISOLATES invariance (within ABOVE across-max)" if w > ax
                   else "within > mean but not max — partial" if w > am
                   else "no isolation (within ≤ mean)")
        print(f"  {name:>34}: within {w:.4f} vs across-max {ax:.4f} → {verdict}")
    print("\n  n=1 pair; the metric is fixed forward. If a signature beats across-MAX, it")
    print("  isolates content-specific storage independent of the universal envelope.")


if __name__ == "__main__":
    main()
