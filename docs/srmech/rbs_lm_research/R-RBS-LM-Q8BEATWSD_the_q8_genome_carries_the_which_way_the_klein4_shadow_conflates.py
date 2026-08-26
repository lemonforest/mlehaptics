r"""R-RBS-LM-Q8BEATWSD — the beat-WSD re-run through the Q₈ substrate (F1309). Committed generating code.

The abelian klein4 (V4) genome is the SHADOW: it holds the word-set (coset) but discards the winding
sign, so it CONFLATES a sense-pair that differs only in DIRECTION. The non-abelian Q₈ substrate
(F1307) carries the winding, so it SEPARATES them. The winding is DERIVED from the directed order
(F1213/F1259), never hand-set.

Two parts, both re-run at rc313:
  PART 1 — the Q₈ GENOME (the storage layer). Minimal WSD pair: "beat the drum" (VERB, beat→drum) vs
    "the drum's beat" (NOUN, drum→beat) — SAME word set {beat,drum}, OPPOSITE direction. Encoded as
    sectors=8 Q₈ HVs (V4 coset = klein4 content of the word SET; sign bit = Class-A address of the
    directed order), packed as a Q₈ genome, recalled. klein4 shadow (q8_project_v4) → sim 1.0 (identical,
    CONFLATED); Q₈ → sim < 1 (SEPARATED). A different-word control separates in BOTH (the shadow loses
    only DIRECTION, not content).
  PART 2 — the SPECTRAL read (F1306), with a corpus-DERIVED charge (Class-C sign × Class-N best_rational
    of directed co-occurrence asymmetry — NOT hand-set cube roots; closes F1306 §5 step 5). Flat
    dense_laplacian → 3-fold {1,2,3,1} (conflation); curved magnetic_laplacian(derived charges) →
    {1,2,1,2,1} + λ₀ lift (separation).

srmech 0.9.0rc313; siona path-imported. No numpy/fractions; NO abs() (sign is Class-C/Class-K).
Composes F1309/F1307/F1306/F1259/F1211/F1255/F1308.
Run:  PYTHONPATH=<repo>/docs/srmech/siona /tmp/srmech_313/bin/python3 R-RBS-LM-Q8BEATWSD_*.py
"""
import os
import sys
import tempfile

import srmech
from srmech.amsc import hdc as H, genome as G, q8 as Q8, laplacian as L, rational as R

from siona import genome_store as GS

D = 512


def q8_sense(word_set, direction):
    """V4 coset = klein4 content of the unordered word SET; winding sign = bit-0 of a Class-A
    klein4_address of the DIRECTED order (DERIVED, never hand-set)."""
    coset = H.klein4_encode_bytes(word_set, D)
    wind = H.klein4_address(D, direction)
    qb = bytes(((int(w) & 1) << 2) | int(c) for c, w in zip(coset, wind))
    return H.HV.from_sequence(qb, sectors=G.OCT)


def match(a, b):
    return round(sum(x == y for x, y in zip(a, b)) / len(a), 4)


def v4(v):
    return list(Q8.q8_project_v4(bytes(v)))


def mult_seq(vals, t=1e-3):
    s, i = [], 0
    while i < len(vals):
        j = i
        while j < len(vals) and (vals[j] - vals[i]) < t:
            j += 1
        s.append(j - i)
        i = j
    return s


def ff(x):
    return float(x.as_float()) if hasattr(x, "as_float") else float(x)


def main():
    print("=== Q8 beat-WSD (srmech %s) ===" % srmech.__version__)
    ok = True

    # PART 1 — the Q8 genome
    senses = {
        "beat_drum_VERB": q8_sense(b"beat|drum", b"dir:beat>drum"),
        "drum_beat_NOUN": q8_sense(b"beat|drum", b"dir:drum>beat"),   # same words, reversed
        "beat_egg_VERB": q8_sense(b"beat|egg", b"dir:beat>egg"),      # control: different words
    }
    path = os.path.join(tempfile.mkdtemp(), "beatwsd_q8")
    mani = GS.pack_instrument(list(senses.items()), path, element_type=GS.ELEMENT_TYPE_Q8)
    rc = GS.load_instrument(path, element_type=GS.ELEMENT_TYPE_Q8)
    rt = all(rc[k] == [int(x) for x in senses[k]] for k in senses)
    r = {k: rc[k] for k in senses}
    q8_pair = match(r["beat_drum_VERB"], r["drum_beat_NOUN"])
    sh_pair = match(v4(r["beat_drum_VERB"]), v4(r["drum_beat_NOUN"]))
    sh_ctrl = match(v4(r["beat_drum_VERB"]), v4(r["beat_egg_VERB"]))
    part1 = rt and mani.get("carrier") == "q8" and q8_pair < 0.99 and sh_pair == 1.0 and sh_ctrl < 0.99
    ok &= part1
    print("  PART 1 — Q8 genome (carrier=%s, round-trip=%s):" % (mani.get("carrier"), rt))
    print("    WSD pair 'beat drum'(verb) vs 'drum beat'(noun):  Q8 sim=%.4f (SEPARATED)  |  klein4 shadow sim=%.4f (%s)"
          % (q8_pair, sh_pair, "CONFLATED" if sh_pair == 1.0 else "?"))
    print("    control (different words):                         klein4 shadow sim=%.4f (still separates by content)" % sh_ctrl)

    # PART 2 — the spectral read, DERIVED charge
    E = [(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0), (0, 5), (5, 6), (6, 0)]
    cooc = {"drum": (5, 1), "tired": (1, 4), "egg": (3, 3)}   # (fwd, bwd) directed co-occurrence

    def charge(fwd, bwd):
        hi, lo = (fwd, bwd) if fwd >= bwd else (bwd, fwd)     # Class-K pin-slot (order), no abs()
        sign = 1 if fwd >= bwd else -1                        # Class-C direction
        p, q = R.best_rational(hi - lo, fwd + bwd, 100)       # Class-N rational anchor
        return sign * (p / q)

    arm = [charge(*cooc[w]) for w in ("drum", "tired", "egg")]
    ch = [0, 0, arm[0], 0, 0, arm[1], 0, 0, arm[2]]
    flat = sorted(round(ff(x), 4) for x in L.symmetric_eigendecompose(L.dense_laplacian(7, E))[0])
    curved = sorted(round(ff(x), 4) for x in L.hermitian_eigendecompose(L.magnetic_laplacian(7, E, charges=ch))[0])
    fseq, cseq = mult_seq(flat), mult_seq(curved)
    part2 = fseq == [1, 2, 3, 1] and cseq != [1, 2, 3, 1] and curved[0] > 0.01
    ok &= part2
    print("  PART 2 — spectral, DERIVED charge %s (Class-C x Class-N, not cube roots):" % [round(a, 3) for a in arm])
    print("    FLAT   mult %s (3-fold = CONFLATION)   CURVED mult %s, λ0 lift %.4f (SEPARATED)" % (fseq, cseq, curved[0]))

    print("\n=== %s ===" % ("BOTH: Q8 substrate carries the which-way the klein4 shadow conflates; derived charge separates."
                            if ok else "REGRESSION — reconcile before trusting F1309."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
