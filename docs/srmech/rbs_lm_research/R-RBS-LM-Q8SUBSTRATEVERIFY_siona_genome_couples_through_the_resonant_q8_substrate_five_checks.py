r"""R-RBS-LM-Q8SUBSTRATEVERIFY — the committed generating code for the siona Q₈ substrate move (N3 + F1307).

siona's genome can now couple through the NON-ABELIAN Q₈ quaternion substrate (`element_type=Q8`), not only
the abelian klein4 (V4) shadow. The Q₈ coupling `one` is RESONANT — a declared function of `the_one`, NEVER a
seed (the rc311 srmech TEST mints its Q₈ one from an RNG, which is exactly the F1304/F1259 defect for siona;
this rejects that and constructs a resonant one instead). klein4 stays the default and is BYTE-UNTOUCHED.

The five checks below are re-run in the MAIN LOOP against the edited `genome_store.py` (independent of the
implementing agent's report). Per `[[feedback_computational_provenance_discipline]]` this is the generating code.
Exit non-zero if any check regresses.

  [4] coupler_q8 RESONANT — deterministic (no seed), π-faithful (`q8_project_v4(_coupler_q8) == _coupler`),
      sign channel non-trivial (exercises the non-abelian structure, not klein4-in-disguise).
  [1] Q₈ round-trip EXACT — genuine sectors=8 content (with winding sign bits ≥4) survives pack→load bit-exact;
      manifest carrier == "q8" (the v16 3-bit on-disk packer).
  [2] BACKWARD-FAITHFUL — `q8_project_v4(Q8 recall) == klein4 recall == original` (the rc311-P2 π-homomorphism
      at the genome level: the Q₈ genome IS a klein4 genome plus the sign bit V4 discards).
  [3] klein4 default BYTE-UNTOUCHED — `turns.bin` byte-identical to the raw srmech `genome()`/`genome_save`
      path; default round-trip exact.
  [5] FAIL-LOUD — `express`/`add_kernel` raise `NotImplementedError` on Q₈ (their srmech primitives
      `gene_express`/`genome_append` have no `element_type` yet — UPSTREAM §Q8-siona; never silently corrupt).

srmech 0.9.0rc313. siona path-imported. No numpy/fractions; no abs() (sign is Class-K). Composes F1307/F1304/
F1259/F1306 + the Q₈ arc (rc308-313).
Run:  PYTHONPATH=<repo>/docs/srmech/siona /tmp/srmech_313/bin/python3 R-RBS-LM-Q8SUBSTRATEVERIFY_*.py
"""
import os
import sys
import tempfile

import srmech
from srmech.amsc import hdc as H, genome as G, q8 as Q8

from siona import genome_store as GS

D = 512


def main():
    print("=== siona Q₈ substrate verification (srmech %s) ===" % srmech.__version__)
    ok = True

    # [4] resonant coupler
    c1 = GS._coupler_q8(256)
    c2 = GS._coupler_q8(256)
    det = list(c1) == list(c2)
    pif = list(Q8.q8_project_v4(bytes(int(x) for x in c1))) == [int(x) for x in GS._coupler(256)]
    signs = sum(int(x) >> 2 for x in c1)
    nontrivial = 0 < signs < 256
    ok &= det and pif and nontrivial
    print("  [4] coupler_q8: deterministic=%s pi-faithful=%s sign-nontrivial=%s (%d/256)"
          % (det, pif, nontrivial, signs))

    # [1] genuine winding round-trip
    oct_content = H.HV.from_sequence(bytes((i % 8) for i in range(D)), sectors=G.OCT)
    oc = [int(x) for x in oct_content]
    p = os.path.join(tempfile.mkdtemp(), "q8gp")
    mani = GS.pack_instrument([("w", oct_content)], p, element_type=GS.ELEMENT_TYPE_Q8)
    rt = GS.load_instrument(p, element_type=GS.ELEMENT_TYPE_Q8)["w"] == oc
    has_wind = any(v >= 4 for v in oc)
    ok &= rt and has_wind and mani.get("carrier") == "q8"
    print("  [1] Q8 round-trip: carrier=%s bit-exact=%s content-has-winding=%s"
          % (mani.get("carrier"), rt, has_wind))

    # [2] backward-faithful
    kv = H.klein4_encode_bytes(b"beat", D)
    kl = [int(x) for x in kv]
    dq = tempfile.mkdtemp()
    pq, pk = os.path.join(dq, "q8"), os.path.join(dq, "k4")
    GS.pack_instrument([("k", kv)], pq, element_type=GS.ELEMENT_TYPE_Q8)
    GS.pack_instrument([("k", kv)], pk)
    q8r = GS.load_instrument(pq, element_type=GS.ELEMENT_TYPE_Q8)["k"]
    k4r = GS.load_instrument(pk)["k"]
    bf = list(Q8.q8_project_v4(bytes(q8r))) == k4r == kl
    ok &= bf
    print("  [2] backward-faithful (q8_project_v4(Q8 recall)==klein4 recall==orig): %s" % bf)

    # [3] klein4 default byte-untouched
    dk = tempfile.mkdtemp()
    pk1, pk2 = os.path.join(dk, "a"), os.path.join(dk, "b")
    GS.pack_instrument([("k", kv)], pk1)
    one = GS._coupler(256)
    G.genome_save(G.genome({"k": GS._leaves(kv, 256)}, one), pk2, one, ["k"])
    b1 = open(os.path.join(pk1, "turns.bin"), "rb").read()
    b2 = open(os.path.join(pk2, "turns.bin"), "rb").read()
    untouched = b1 == b2 and GS.load_instrument(pk1)["k"] == kl
    ok &= untouched
    print("  [3] klein4 default turns.bin == raw srmech genome() path + round-trip exact: %s" % untouched)

    # [5] fail-loud guards
    guards = True
    for fn in ("express", "add_kernel"):
        try:
            if fn == "express":
                GS.express(None, 0, the_one=None, element_type=GS.ELEMENT_TYPE_Q8)
            else:
                GS.add_kernel("x", "l", kv, element_type=GS.ELEMENT_TYPE_Q8)
            guards = False
        except NotImplementedError:
            pass
    ok &= guards
    print("  [5] express/add_kernel Q8 fail-loud (NotImplementedError): %s" % guards)

    print("\n=== %s ===" % ("ALL FIVE PASS — Q₈ substrate live, klein4 byte-untouched, coupler resonant."
                            if ok else "REGRESSION — do not trust the substrate move until reconciled."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
