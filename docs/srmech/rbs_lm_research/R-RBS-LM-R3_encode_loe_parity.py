"""#855 R3 / UPSTREAM §17.1 — parity check: does the UPSTREAMED text->instrument
encoder (encode_loe_content) reproduce our hand-rolled K1/K3 notebook signal?

If yes -> we can migrate onto the one-call upstreamed surface (retire the hand-roll).
If no  -> our K1 (Class-L co-occurrence Laplacian eigendecomp; already srmech-primitive-
          native) stays; encode_loe_content is a different (content-fingerprint) object.

Baseline of comparison = F339 K1 on the srmech notebook: framework-probe peak z=+2.59,
negative peak z=-0.27 (framework clearly > negatives).

Test: encode the srmech notebook + the same F339 framework/negative probes via
srmech.signal_processing.encode_loe_content; baseline = random paragraph pairs; report
framework-vs-negative z discrimination; compare to K1's pattern.

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R3_encode_loe_parity.py
"""
import json, re, random
from pathlib import Path
import numpy as np
import srmech
from srmech.signal_processing import encode_loe_content
from srmech.amsc.hdc import similarity

HERE = Path(__file__).parent
REPO = HERE.parent.parent.parent
NB = REPO / "docs/srmech/srmech_research_notebook.md"
D = 8192

FRAMEWORK_PROBES = [
    "cascade composition class L laplacian eigenspectrum",
    "primitive class operator vocabulary A N",
    "one three seven three partition hurwitz",
    "stored relationship mechanism cyclic group",
    "hyperdimensional bind bundle permute klein four",
    "AMSC attestation provenance source doi",
]
NEGATIVE_PROBES = [
    "chocolate ice cream flavor",
    "professional soccer match score",
    "kitchen pencil sharpener metal",
    "tropical rainforest humidity bright",
    "vintage automobile manufacturing",
    "ocean coral reef colorful",
]


def main():
    print(f"#855 R3 / §17.1 — encode_loe_content parity vs hand-rolled K1 (srmech {srmech.__version__})")
    text = NB.read_text()
    print(f"  notebook chars: {len(text):,}")

    # encode the notebook as one LoE instrument (the upstreamed text->instrument)
    import time
    t0 = time.time()
    S = encode_loe_content(text, D=D)
    print(f"  encode_loe_content(notebook) -> {len(S)} bytes in {time.time()-t0:.1f}s")

    # baseline: random paragraph pairs
    paras = [p for p in re.split(r"\n\n+", text) if 50 < len(p) < 500]
    rng = random.Random(20260603)
    sims = []
    for _ in range(100):
        a, b = rng.sample(paras, 2)
        sims.append(similarity(encode_loe_content(a, D=D), encode_loe_content(b, D=D)))
    m = float(np.mean(sims)); s = float(np.std(sims)); mx = float(max(sims))
    print(f"  baseline (paragraph pairs): mean={m:+.4f} std={s:.4f} max={mx:+.4f}")

    def probe_z(p):
        sim = similarity(encode_loe_content(p, D=D), S)
        return sim, (sim - m) / max(s, 1e-9)

    print("\n  === framework probes (want z>>0, like K1's +2.59) ===")
    fw = []
    for p in FRAMEWORK_PROBES:
        sim, z = probe_z(p); fw.append(z)
        print(f"    z={z:+.2f}  sim={sim:+.4f}  {p}")
    print("  === negative probes (want z~0) ===")
    neg = []
    for p in NEGATIVE_PROBES:
        sim, z = probe_z(p); neg.append(z)
        print(f"    z={z:+.2f}  sim={sim:+.4f}  {p}")

    fw_peak, fw_mean = max(fw), float(np.mean(fw))
    neg_peak = max(neg)
    print(f"\n  encode_loe_content: framework peak z={fw_peak:+.2f} (mean {fw_mean:+.2f}) | negative peak z={neg_peak:+.2f}")
    print(f"  hand-rolled K1 (F339):       framework peak z=+2.59             | negative peak z=-0.27")
    discriminates = fw_mean > 1.0 and fw_peak > neg_peak + 1.0
    print(f"\n  VERDICT: encode_loe_content {'REPRODUCES' if discriminates else 'does NOT reproduce'} the K1 framework-vs-negative discrimination")
    print(f"           -> {'MIGRATE-able (one-call surface works)' if discriminates else 'KEEP hand-rolled K1 (different object: content-fingerprint vs relationship-kernel)'}")

    out = {"partition": "R-RBS-LM-R3 (#855 R3 / §17.1)", "srmech_version": srmech.__version__,
           "baseline": {"mean": m, "std": s, "max": mx},
           "framework_z": fw, "negative_z": neg, "fw_peak": fw_peak, "fw_mean": fw_mean,
           "neg_peak": neg_peak, "K1_ref": {"fw_peak": 2.59, "neg_peak": -0.27},
           "encode_loe_reproduces_K1": discriminates}
    (HERE / "R-RBS-LM-R3_parity_results.json").write_text(json.dumps(out, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R3_parity_results.json'}")


if __name__ == "__main__":
    main()
