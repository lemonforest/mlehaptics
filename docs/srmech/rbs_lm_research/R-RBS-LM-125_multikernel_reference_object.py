"""R-RBS-LM-125 — Multi-kernel RBS-NN reference object: 6 text kernels in ONE
queryable RBSHDCInstrument; decode_fingerprint retrieval.

The operational closure of the DOMAIN-anchor thread (R-RBS-LM-53 F44–F50 +
R-RBS-LM-54 Rosetta Stone Layer), instantiated on srmech's real object path:

  - One RBSHDCInstrument holds all N text kernels as a LABELED catalog
    {text_label: kernel_bytes}.
  - decode_fingerprint(probe, catalog) does Class M similarity-argmax → returns
    the best-match LABEL. The labeled binding IS the external DOMAIN anchor that
    pairwise form-similarity (53/124) structurally lacks (§VII.6.20).

Held-out self-retrieval design (avoids trivial identity):
  Split each text into KERNEL-half + PROBE-half (disjoint verse-lines). Build
  the K1 kernel from the kernel-half; build the probe from the probe-half.
  decode_fingerprint(probe) → which text's kernel does the held-out probe
  retrieve? Measure exact-text accuracy AND family accuracy + the ranked
  multi-fire pattern (lexical inheritance, F45).

Length-controlled per F163 §7 (equal token budget) — the standing rule after the
F163 size-artifact null. Expected per §VII.6.20 / F163: across-family routing
clean; within-family disambiguation at/near the degeneracy.

SCOPE: structural/spectral ONLY. The object is a content-addressable
FORM-CATEGORY ROUTER over text test-objects — NOT a meaning oracle, NOT a
doctrine-mixer. Returns labels by form-match, ceiling-bounded.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# reuse the faithful K1 machinery from R-RBS-LM-124
_spec = importlib.util.spec_from_file_location(
    "k1mod", HERE / "R-RBS-LM-124_k1_baseline_chirality_lift.py")
k1mod = importlib.util.module_from_spec(_spec)
sys.modules["k1mod"] = k1mod
_spec.loader.exec_module(k1mod)

from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector
from srmech.signal_processing.rbs_hdc_instrument import RBSHDCInstrument
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

VARIANT = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"


def mint(t):
    return np.frombuffer(mint_vector(t, D=8192), dtype=np.uint8)


def probe_from_chunks(chunks):
    """Build a probe = bundle of the probe-half's top-frequency vocab mints."""
    from collections import Counter
    freq = Counter(t for toks in chunks for t in toks)
    top = [t for t, _ in freq.most_common(k1mod.M_VOCAB * 2 + 1)]   # odd target
    if not top:
        return None
    if len(top) % 2 == 0:          # hdc.bundle requires an ODD vector count
        top = top[:-1]
    return bundle([mint(t) for t in top])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=VARIANT)
    ap.add_argument("--equal-tokens", action="store_true", default=True,
                    help="length-control per F163 §7 (on by default)")
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    texts = lc["corpus"]["texts"]

    inst = RBSHDCInstrument.build(D=8192)
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"RBSHDCInstrument: {inst.describe()}")
    print(f"memory pathways: {list(inst.memory.keys())}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...  equal_tokens={args.equal_tokens}\n")

    # Pass 1: load + tokenize + split kernel-half / probe-half
    fams, labels = {}, {}
    kchunks, pchunks = {}, {}
    keys = []
    for key, meta in texts.items():
        path = cache_dir / meta["filename"]
        body = k1mod.strip_gutenberg(path.read_text(encoding="utf-8", errors="replace"))
        chunks = [c for c in (k1mod.tokenize(c) for c in k1mod.chunk_text(body)) if c]
        # split chunks alternately → disjoint kernel-half / probe-half
        kchunks[key] = chunks[0::2]
        pchunks[key] = chunks[1::2]
        keys.append(key); labels[key] = meta["label"]; fams[key] = meta["family"]

    if args.equal_tokens:
        budget = min(sum(len(c) for c in kchunks[k]) for k in keys)
        print(f"  [equal-tokens] kernel-half capped to {budget} tokens/text\n")
        kchunks = {k: k1mod.trim_chunks_to_budget(v, budget) for k, v in kchunks.items()}

    # Build kernels → labeled catalog (the multi-kernel reference object)
    catalog = {}
    for key in keys:
        kf, _vocab = k1mod.build_K1_flat(kchunks[key])
        catalog[key] = kf
        # also store into a family-partitioned memory pathway (demo)
        pathway = "semantic" if fams[key] == "abrahamic" else "episodic_LTM"
        inst.bind_and_remember(kf, pathway)
        print(f"  loaded kernel: {labels[key]:34s} fam={fams[key]:9s} → catalog + pathway[{pathway}]")

    # Held-out probe retrieval via decode_fingerprint
    print("\n" + "=" * 96)
    print("HELD-OUT PROBE RETRIEVAL — decode_fingerprint(probe_half) over the 6-kernel catalog")
    print("=" * 96)
    print(f"  {'probe text':>22} | {'→ decoded label':>22} | exact? | family? | top-2 ranked sims")
    print("  " + "-" * 92)
    exact_hits = fam_hits = 0
    records = []
    for key in keys:
        probe = probe_from_chunks(pchunks[key])
        decoded = inst.decode_fingerprint(probe, catalog)
        sims = sorted(((similarity(probe, catalog[k]), k) for k in keys), reverse=True)
        exact = decoded == key
        fam_ok = fams[decoded] == fams[key]
        exact_hits += exact
        fam_hits += fam_ok
        top2 = ", ".join(f"{labels[k][:14]}={s:.3f}" for s, k in sims[:2])
        print(f"  {labels[key][:22]:>22} | {labels[decoded][:22]:>22} | "
              f"{'✓' if exact else '✗':^6} | {'✓' if fam_ok else '✗':^7} | {top2}")
        records.append({"phase": "P1_decode", "probe_text": labels[key],
                        "probe_family": fams[key], "decoded_label": labels[decoded],
                        "decoded_family": fams[decoded], "exact": bool(exact),
                        "family_match": bool(fam_ok),
                        "ranked": [{"text": labels[k], "sim": float(s)} for s, k in sims]})

    n = len(keys)
    print("\n" + "=" * 96)
    print("RETRIEVAL ACCURACY (operationalized DOMAIN anchor; §VII.6.20-bounded)")
    print("=" * 96)
    print(f"  exact-text retrieval : {exact_hits}/{n} = {exact_hits/n:.3f}")
    print(f"  family   retrieval   : {fam_hits}/{n} = {fam_hits/n:.3f}")

    # Within- vs across-family mean sim (probe × kernel, excluding self)
    within, across = [], []
    for ki in keys:
        probe = probe_from_chunks(pchunks[ki])
        for kj in keys:
            if ki == kj:
                continue
            s = float(similarity(probe, catalog[kj]))
            (within if fams[ki] == fams[kj] else across).append(s)
    wm, am = float(np.mean(within)), float(np.mean(across))
    print(f"  probe→other-kernel sim: within-family={wm:.4f}  across-family={am:.4f}  contrast={wm/am if am>1e-6 else float('inf'):.3f}")

    print("\n" + "=" * 96)
    print("VERDICT (form-category router, ceiling-bounded):")
    print(f"  across-family routing works?   {fam_hits >= n - 1} (family acc {fam_hits/n:.2f})")
    print(f"  within-family disambiguation?  {exact_hits == n} (exact acc {exact_hits/n:.2f})")
    if fam_hits >= n - 1 and exact_hits < n:
        print("  → object routes by FORM-CATEGORY (family) but not substrate-identity")
        print("    (within-family) — operational §VII.6.20: labeled binding IS the")
        print("    DOMAIN anchor at the resolution form supports.")
    elif exact_hits == n:
        print("  → object disambiguates EXACT text (form carries per-text signal at this scale)")
    else:
        print("  → routing weak; inspect (length-control / probe construction)")

    # MPR-attested NDJSON
    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "equal_tokens": args.equal_tokens,
              "scope": "STRUCTURAL form-category router; no doctrinal claims; §VII.6.20"}
    out_records = [{**attest, "phase": "P0_header", "n_kernels": n,
                    "exact_acc": exact_hits / n, "family_acc": fam_hits / n,
                    "within_family_sim": wm, "across_family_sim": am}]
    out_records += [{**attest, **r} for r in records]
    out = args.catalog.parent / "substrate_measurements" / "religious_texts_multikernel.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in out_records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(out_records)} records)")


if __name__ == "__main__":
    main()
