"""#855 R5 — byte-level + Class-C glyph-chirality robustness to typos/dyslexia.

Tests the claims from the dyslexia exchange (depends on R1's gamma5 axis):
  (1) byte BAG (permutation-invariant) catches TRANSPOSITIONS ~perfectly (same byte multiset);
  (2) byte SEQUENCE (position-bound) degrades GRACEFULLY on transpositions (no BPE cliff);
  (3) byte-identity MISSES b/d, p/q MIRROR confusions (distinct bytes, ~orthogonal);
  (4) a Class-C GLYPH-CHIRALITY (shape-class) encoding CATCHES the mirror (b,d share a shape-class);
  (5) PHONETIC errors (enuff/enough) are OUT OF SCOPE for byte-level (honest negative).

srmech-native: mint_vector (Class A byte/glyph atoms) / bundle (bag) / bind+permute (sequence)
/ similarity (Class M). The glyph-chirality map folds horizontal-mirror pairs (b<->d, p<->q)
to a shared shape-class atom -- the Class-C gamma5 relation made explicit at the glyph level.

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R5_byte_glyph_chirality_dyslexia.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc.hdc import bundle, bind, permute, similarity
from srmech.signal_processing import mint_vector

HERE = Path(__file__).parent
D = 8192
STRIDE = D // 3

# horizontal-mirror (glyph-chirality / gamma5) pairs — the canonical dyslexia confusions
MIRROR = {"b": "v_bd", "d": "v_bd", "p": "v_pq", "q": "v_pq"}

_C = {}
def atom(tok):
    if tok not in _C:
        _C[tok] = mint_vector(tok, D=D)
    return _C[tok]

def _odd(vecs):
    return vecs if len(vecs) % 2 == 1 else vecs + [vecs[0]]

def byte_bag(word):
    return bundle(_odd([atom(f"byte:{ord(c)}") for c in word]))

def byte_seq(word):
    hv = atom(f"byte:{ord(word[0])}")
    for i, c in enumerate(word[1:], 1):
        hv = bind(hv, permute(atom(f"byte:{ord(c)}"), i * STRIDE))
    return hv

def glyph_bag(word):
    # Class-C glyph-chirality: fold mirror pairs to a shared shape-class atom
    return bundle(_odd([atom(f"glyph:{MIRROR.get(c, c)}") for c in word]))

PROBES = {
    "transposition": [("the", "teh"), ("form", "from"), ("trial", "trail"), ("angel", "angle")],
    "omit_insert":   [("hello", "helo"), ("really", "realy"), ("necessary", "necesary")],
    "mirror_bd_pq":  [("bad", "dad"), ("bog", "dog"), ("bpdq", "dqbp"), ("dip", "diq")],
    "phonetic":      [("enough", "enuff"), ("phone", "fone"), ("night", "nite")],
}


def main():
    print(f"#855 R5 — byte + glyph-chirality typo/dyslexia robustness (srmech {srmech.__version__}, D={D})")
    print(f"  {'error type':>14} | {'pair':>18} | {'byte_bag':>8} | {'byte_seq':>8} | {'glyph_bag':>9}")
    rows = []
    for etype, pairs in PROBES.items():
        for correct, typo in pairs:
            bb = similarity(byte_bag(correct), byte_bag(typo))
            bs = similarity(byte_seq(correct), byte_seq(typo))
            gb = similarity(glyph_bag(correct), glyph_bag(typo))
            rows.append({"type": etype, "correct": correct, "typo": typo,
                         "byte_bag": bb, "byte_seq": bs, "glyph_bag": gb})
            print(f"  {etype:>14} | {correct+'/'+typo:>18} | {bb:>8.3f} | {bs:>8.3f} | {gb:>9.3f}")

    def avg(etype, key):
        v = [r[key] for r in rows if r["type"] == etype]
        return float(np.mean(v))

    print("\n=== per-error-type means ===")
    print(f"  {'type':>14} | {'byte_bag':>8} | {'byte_seq':>8} | {'glyph_bag':>9}")
    summary = {}
    for etype in PROBES:
        summary[etype] = {k: avg(etype, k) for k in ("byte_bag", "byte_seq", "glyph_bag")}
        s = summary[etype]
        print(f"  {etype:>14} | {s['byte_bag']:>8.3f} | {s['byte_seq']:>8.3f} | {s['glyph_bag']:>9.3f}")

    print("\n=== verdict ===")
    t = summary["transposition"]; m = summary["mirror_bd_pq"]; ph = summary["phonetic"]
    print(f"  (1) transposition: byte_bag {t['byte_bag']:.3f} (~1 = caught), byte_seq {t['byte_seq']:.3f} (graceful, no cliff)")
    print(f"  (3) mirror b/d,p/q: byte_bag {m['byte_bag']:.3f} (misses) -> glyph_bag {m['glyph_bag']:.3f} (CAUGHT by Class-C shape-class)")
    print(f"  (5) phonetic: byte_bag {ph['byte_bag']:.3f}, glyph_bag {ph['glyph_bag']:.3f} (OUT OF SCOPE -- both low, honest negative)")
    bag_catches_transp = t["byte_bag"] > 0.9
    seq_graceful = 0.1 < t["byte_seq"] < t["byte_bag"]
    glyph_beats_byte_on_mirror = m["glyph_bag"] > m["byte_bag"] + 0.2
    phonetic_oos = ph["glyph_bag"] < 0.7
    print(f"\n  bag catches transposition (>0.9): {bag_catches_transp}")
    print(f"  sequence degrades gracefully (between 0.1 and bag): {seq_graceful}")
    print(f"  glyph-chirality beats byte-identity on mirror (+0.2): {glyph_beats_byte_on_mirror}")
    print(f"  phonetic out-of-scope (glyph<0.7): {phonetic_oos}")

    out = {"partition": "R-RBS-LM-R5 (#855 R5)", "srmech_version": srmech.__version__, "D": D,
           "rows": rows, "summary": summary,
           "bag_catches_transposition": bag_catches_transp, "sequence_graceful": seq_graceful,
           "glyph_beats_byte_on_mirror": glyph_beats_byte_on_mirror, "phonetic_out_of_scope": phonetic_oos}
    (HERE / "R-RBS-LM-R5_results.json").write_text(json.dumps(out, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R5_results.json'}")


if __name__ == "__main__":
    main()
