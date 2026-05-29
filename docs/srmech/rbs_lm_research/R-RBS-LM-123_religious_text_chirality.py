"""R-RBS-LM-123 — Religious-text 28D chirality revisit (Phase 1: signatures).

Loads descriptor_religious_texts.toml via srmech.amsc.load_descriptor and tests
whether the 28D bi-axial chirality decomposition LIFTS the flat-spectral
structural degeneracy R-RBS-LM-53 measured (the big-3 Abrahamic texts at
diagonal/off-diagonal similarity ratio 0.99 — MFO §VII.6.20 ceiling).

Two per-text signatures + a discrimination contrast:

  FLAT baseline (reproduces R-RBS-LM-53):
    bundle each text's bigram vectors (all sector 0) → one aggregate vector;
    pairwise klein4_similarity → expect ~uniform high (the 0.99 degeneracy).

  CHIRALITY signature (the 28D revisit):
    route each bigram to a sector by WORD-ORDER PARITY (catalog
    sector_routing=bigram_parity):
        p1 = reverse-bigram-present?  (word-order symmetry; γ₅-like)
        p2 = position-index % 2       (positional rhythm; iω₇-like)
        sector = 2*p1 + p2  ∈ {0,1,2,3}
    → per-text parity-occupancy [f0,f1,f2,f3] is a STRUCTURAL fingerprint
      (word-order rigidity differs by text); plus chirality-op self-similarity
      (γ₅ flip / iω₇ flip / CPT mirror) of the parity-tagged bundle.

  DISCRIMINATION TEST:
    does the parity-occupancy distance matrix SEPARATE texts that flat
    similarity merged? If yes → chirality lifts the degeneracy (refines
    §VII.6.20). If occupancy is also ~uniform → null (ceiling holds at
    chirality depth; F142: chirality discriminates only where it is the
    load-bearing distinction).

SCOPE: structural/spectral ONLY. Texts are structural test-objects. No
doctrinal/truth/origin/ranking claims. §VII.6.20 honored — form only.
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

from srmech.amsc import load_descriptor, descriptor_hash, hdc, format as amsc_format
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CANONICAL_VARIANT = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"

_GUT_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG", re.I)
_GUT_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG", re.I)
_WORD = re.compile(r"[a-z]+")


def strip_gutenberg(text: str) -> str:
    """Strip PG header/footer boilerplate (ports R-RBS-LM-53 strip_gutenberg)."""
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


def load_text_units(path: Path, n_units: int, rng) -> list[list[str]]:
    """Load a text, strip PG, split to verse-line units, tokenize, sample n."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    body = strip_gutenberg(raw)
    units = []
    for line in body.splitlines():
        toks = _WORD.findall(line.lower())
        if len(toks) >= 2:        # need ≥1 bigram
            units.append(toks)
    if len(units) > n_units:
        idx = rng.choice(len(units), size=n_units, replace=False)
        units = [units[i] for i in sorted(idx)]
    return units


def encode_word(word: str, D: int, hex_chars: int) -> np.ndarray:
    seed = int(amsc_format.sha256_bytes(word.encode("utf-8"))[:hex_chars], 16)
    return hdc.klein4_random(D, np.random.default_rng(seed))


def encode_bigram(a: str, b: str, D: int, hex_chars: int, sector: int) -> np.ndarray:
    bound = hdc.klein4_bind(encode_word(a, D, hex_chars), encode_word(b, D, hex_chars))
    return hdc.klein4_bind(bound, np.full(D, sector, dtype=np.uint8))


def text_bigrams(units: list[list[str]]):
    """Yield (a, b, position_index) for every consecutive bigram across units."""
    pos = 0
    for toks in units:
        for i in range(len(toks) - 1):
            yield toks[i], toks[i + 1], pos
            pos += 1


def parity_sector(a: str, b: str, pos: int, reverse_present: set) -> int:
    """bigram_parity routing: 2*(reverse present?) + (position parity)."""
    p1 = 1 if (b, a) in reverse_present else 0
    p2 = pos & 1
    return 2 * p1 + p2


def analyze_text(units, params, routing: str):
    """Return flat-bundle vector + parity-occupancy + chirality-op responses."""
    D = int(params["substrate"]["D"])
    hex_chars = int(params["substrate"]["token_seed_hex_chars"])

    bigram_set = set()
    bigrams = list(text_bigrams(units))
    for a, b, _ in bigrams:
        bigram_set.add((a, b))

    # FLAT bundle (all sector 0)
    flat_vecs = [encode_bigram(a, b, D, hex_chars, 0) for a, b, _ in bigrams]
    flat_bundle = hdc.klein4_bundle(*flat_vecs)

    # CHIRALITY: route by parity, count occupancy, bundle parity-tagged vectors
    occ = Counter()
    parity_vecs = []
    for a, b, pos in bigrams:
        if routing == "bigram_parity":
            s = parity_sector(a, b, pos, bigram_set)
        else:  # hash null-control
            s = int(amsc_format.sha256_bytes(f"{a}_{b}".encode())[:8], 16) % 4
        occ[s] += 1
        parity_vecs.append(encode_bigram(a, b, D, hex_chars, s))
    parity_bundle = hdc.klein4_bundle(*parity_vecs)
    total = sum(occ.values())
    occupancy = [occ.get(s, 0) / total for s in range(4)]

    # Chirality-op self-similarity of the parity-tagged bundle
    g5 = hdc.klein4_similarity(parity_bundle, hdc.klein4_chirality_flip_gamma5(parity_bundle))
    o7 = hdc.klein4_similarity(parity_bundle, hdc.klein4_chirality_flip_omega7(parity_bundle))
    cpt = hdc.klein4_similarity(parity_bundle, hdc.klein4_cpt_mirror(parity_bundle))

    return {
        "n_bigrams": len(bigrams),
        "n_unique_bigrams": len(bigram_set),
        "flat_bundle": flat_bundle,
        "parity_occupancy": occupancy,
        "chirality_self_sim": {"gamma5": g5, "omega7": o7, "cpt": cpt},
    }


def l1(a, b):
    return float(sum(abs(x - y) for x, y in zip(a, b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CANONICAL_VARIANT)
    ap.add_argument("--routing", default=None, help="override sector_routing (bigram_parity|hash)")
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    cs_cfg = lc["chirality_signature"]
    routing = args.routing or cs_cfg["sector_routing"]
    n_units = int(cs_cfg["n_units_per_text"])
    seed = int(cs_cfg["seed"])
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    texts = lc["corpus"]["texts"]

    attestation = {
        "descriptor_path": str(desc.path),
        "descriptor_hash": dh,
        "source_key": desc.source["key"],
        "srmech_version": SRMECH_VERSION,
        "abi_version": NATIVE_ABI_VERSION,
        "has_native": HAS_NATIVE,
        "routing": routing,
        "scope": "STRUCTURAL-ONLY per MFO VII.6.20; no doctrinal/ranking claims",
    }

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {desc.path.name}  hash={dh[:16]}...  routing={routing}  n_units={n_units}\n")

    # Verify corpus hashes (attestation) + load
    rng = np.random.default_rng(seed)
    keys, labels, analyses = [], {}, {}
    for key, meta in texts.items():
        path = cache_dir / meta["filename"]
        actual = amsc_format.sha256_bytes(path.read_bytes())
        ok = actual == meta["sha256"]
        units = load_text_units(path, n_units, np.random.default_rng(seed))
        print(f"  {meta['label']:34s} sha✓={ok}  units={len(units)}")
        keys.append(key)
        labels[key] = meta["label"]
        analyses[key] = analyze_text(units, lc, routing)

    # --- FLAT baseline similarity matrix (reproduce R-RBS-LM-53 0.99) ---
    print("\n" + "=" * 92)
    print("FLAT-spectral bundle similarity (reproduces R-RBS-LM-53 degeneracy)")
    print("=" * 92)
    print("           " + "  ".join(f"{k[:8]:>8}" for k in keys))
    flat_offdiag = []
    for ki in keys:
        row = []
        for kj in keys:
            s = hdc.klein4_similarity(analyses[ki]["flat_bundle"], analyses[kj]["flat_bundle"])
            row.append(s)
            if ki != kj:
                flat_offdiag.append(s)
        print(f"  {ki[:9]:>9} " + "  ".join(f"{s:8.4f}" for s in row))
    flat_off_mean = float(np.mean(flat_offdiag))
    print(f"\n  off-diagonal mean similarity = {flat_off_mean:.4f}  (diagonal = 1.0; ratio {flat_off_mean:.3f})")

    # --- CHIRALITY parity-occupancy signatures ---
    print("\n" + "=" * 92)
    print(f"CHIRALITY parity-occupancy [s0=asym/even, s1=asym/odd, s2=sym/even, s3=sym/odd]")
    print("=" * 92)
    print(f"  {'text':>20} | {'s0':>6} {'s1':>6} {'s2':>6} {'s3':>6} | {'γ5':>6} {'ω7':>6} {'cpt':>6}")
    print("  " + "-" * 78)
    for k in keys:
        occ = analyses[k]["parity_occupancy"]
        cs = analyses[k]["chirality_self_sim"]
        print(f"  {labels[k][:20]:>20} | {occ[0]:6.3f} {occ[1]:6.3f} {occ[2]:6.3f} {occ[3]:6.3f} | "
              f"{cs['gamma5']:6.3f} {cs['omega7']:6.3f} {cs['cpt']:6.3f}")

    # --- DISCRIMINATION: occupancy L1 distance matrix ---
    print("\n" + "=" * 92)
    print("CHIRALITY occupancy L1-distance (does it SEPARATE what flat merged?)")
    print("=" * 92)
    print("           " + "  ".join(f"{k[:8]:>8}" for k in keys))
    occ_dists = []
    for ki in keys:
        row = []
        for kj in keys:
            d = l1(analyses[ki]["parity_occupancy"], analyses[kj]["parity_occupancy"])
            row.append(d)
            if ki != kj:
                occ_dists.append(d)
        print(f"  {ki[:9]:>9} " + "  ".join(f"{d:8.4f}" for d in row))
    occ_off_mean = float(np.mean(occ_dists))
    occ_off_max = float(np.max(occ_dists))
    print(f"\n  off-diagonal L1 distance: mean={occ_off_mean:.4f}  max={occ_off_max:.4f}")

    # --- Verdict ---
    print("\n" + "=" * 92)
    flat_degenerate = flat_off_mean > 0.90
    chirality_discriminates = occ_off_mean > 0.05   # L1 occupancy separation threshold
    print(f"VERDICT (routing={routing}):")
    print(f"  flat-spectral degenerate?  {flat_degenerate} (off-diag sim {flat_off_mean:.3f})")
    print(f"  chirality discriminates?   {chirality_discriminates} (occupancy L1 mean {occ_off_mean:.3f})")
    if flat_degenerate and chirality_discriminates:
        print("  → 28D chirality LIFTS the flat-spectral degeneracy (refines §VII.6.20)")
    elif flat_degenerate and not chirality_discriminates:
        print("  → ceiling HOLDS at chirality depth (DOMAIN anchor still required; F142 null)")
    else:
        print("  → flat baseline not degenerate at this sample; inspect before concluding")

    # --- MPR-attested NDJSON output ---
    out_records = [{**attestation, "phase": "P0_attestation_header",
                    "flat_offdiag_mean": flat_off_mean,
                    "occupancy_l1_mean": occ_off_mean, "occupancy_l1_max": occ_off_max}]
    for k in keys:
        a = analyses[k]
        out_records.append({
            **attestation, "phase": "P1_chirality_signature", "text_key": k,
            "text_label": labels[k], "n_bigrams": a["n_bigrams"],
            "n_unique_bigrams": a["n_unique_bigrams"],
            "parity_occupancy": a["parity_occupancy"],
            "chirality_self_sim": a["chirality_self_sim"],
        })
    out_path = args.catalog.parent / lc["fetch"]["ndjson_path"] if "fetch" in lc else \
        args.catalog.parent / "substrate_measurements" / "religious_texts.ndjson"
    out_path = args.catalog.parent / desc.schema["ndjson_file"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for rec in out_records:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\nResults: {out_path}  ({len(out_records)} records)")


if __name__ == "__main__":
    main()
