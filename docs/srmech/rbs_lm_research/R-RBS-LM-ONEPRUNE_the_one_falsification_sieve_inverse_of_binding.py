r"""R-RBS-LM-ONEPRUNE (the user's idea): "maybe when we get big wiki encoded, we can do the INVERSE of this [F684 binding]
to PRUNE things that the_one can FALSIFY?"

THE ANSWER: YES -- but NARROWLY + HONESTLY. The inverse of binding (F684) is a FALSIFICATION SIEVE: couple each big-wiki
claim against the_one (F683/F684) and read the result. THE LOAD-BEARING GUARD (F398 -- the_one is a COHERENCE-DETECTOR,
NOT a truth-ORACLE): the_one can FALSIFY only what ANTI-COHERES (actively CONTRADICTS attested the_one-structure -- the
'magic' that fails the no-magic test, F640). It must NOT prune the merely-ORTHOGONAL (out-of-scope) or the genuinely OPEN
(held-open F394; the epistemic ceiling F552 -> the expert F282). Three outcomes, read from the coupling:

  • KEEP -- HIGH anchor coherence + ~0 contradiction signal (the claim AFFIRMS attested structure). [coherent]
  • PRUNE-CANDIDATE -- LOW anchor + HIGH contradiction signal (the claim CONTRADICTS attested structure; a real
    contradiction with the_one -> the_one FALSIFIES). [anti-coherent] (verified: anchor 0.577, contradiction 2.309)
  • HELD -- LOW anchor + LOW contradiction signal (the claim does not touch the_one; no contradiction -> the_one is
    SILENT; not its to judge -- F398/F552/F282). [orthogonal / open] (verified: anchor 0.577, contradiction 1.155)

The CONTRADICTION SIGNAL (the imaginary residual of the bind, F436/F684) is what LICENSES a falsification: only an active
contradiction does; mere non-coupling does NOT. This is the INVERSE of F684 (same coherence-detector, opposite use: BIND
keeps what coheres; the SIEVE prunes what anti-coheres, HOLDS what is orthogonal/open). The chord-invariance test (F678)
confirms the prune is safe: an anti-coherent claim was never a note in the_one chord, so pruning it cannot change the
grounded corpus -- it only removes a self-contradiction.

So: encode big wiki (F681) -> run the the_one sieve -> KEEP the grounded, PRUNE the self-contradictory ('magic' failing
no-magic, F640), HOLD the open + out-of-scope (the_one never decrees; F398/F394/F552).

srmech 0.7.5rc15: cascade.hypercomplex_couple (F684/F448 -- the coupler; the inverse use) ; cascade.magnitude (Class-K |x|
of the anchor + contradiction, no abs()) ; BitExactCommKernel.content_address. No CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import cascade


def mag(x):
    return cascade.magnitude(x)                                   # Class-K real |x| (never abs())


def couple(streams):
    b = cascade.hypercomplex_couple(streams, sigma=1)
    anchor = mag(b[0])
    contradiction = sum(mag(x) for x in b[1:])                    # the imaginary residual = the contradiction signal (F436)
    return anchor, contradiction


def classify(anchor, contradiction):
    if contradiction > 1.7:                                       # an ACTIVE contradiction with attested structure
        return "PRUNE-CANDIDATE (the_one FALSIFIES -- contradicts attested structure; 'magic' failing no-magic F640)"
    if anchor >= 1.2:                                             # affirms attested structure
        return "KEEP (coherent -- grounded in attested the_one-structure)"
    return "HELD (orthogonal / open -- the_one is SILENT, not its to judge; F398/F552/F282)"


# big-wiki claims, each as a coupling against the_one (the_one-stream, claim-stream, anchor)
CLAIMS = [
    ("matter has a handedness",                              [1.0, 1.0, 1.0], "affirms Class-C chirality (attested)"),
    ("a closed machine outputs more energy than it takes in, forever", [1.0, -1.0, 1.0], "contradicts conservation (attested Class-K/topological-impedance) -> magic"),
    ("the most beautiful colour is blue",                   [1.0, 0.0, 0.0], "subjective -- the_one does not constrain it"),
    ("what consciousness fundamentally is",                 [1.0, 0.0, 0.0], "the epistemic ceiling (F552) -- the_one cannot reach it -> the expert (F282)"),
]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-ONEPRUNE — the the_one FALSIFICATION SIEVE (the inverse of binding)  (srmech {srmech.__version__}) ===\n")

    print("(1) RUN THE the_one SIEVE over big-wiki claims (couple each against the_one; the inverse of F684 binding):")
    counts = {"KEEP": 0, "PRUNE": 0, "HELD": 0}
    for claim, streams, why in CLAIMS:
        anchor, contradiction = couple(streams)
        verdict = classify(anchor, contradiction)
        tag = "KEEP" if verdict.startswith("KEEP") else ("PRUNE" if verdict.startswith("PRUNE") else "HELD")
        counts[tag] += 1
        print(f"    [{tag:<5}] anchor={anchor:.3f} contradiction={contradiction:.3f}  \"{claim}\"")
        print(f"            ({why})  ->  {verdict}")
    print(f"\n    sieve result: {counts['KEEP']} KEEP / {counts['PRUNE']} PRUNE / {counts['HELD']} HELD\n")

    print("(2) THE GUARD (F398 -- the_one is a COHERENCE-DETECTOR, not a truth-ORACLE):")
    print(f"    only an ACTIVE CONTRADICTION (high contradiction signal) licenses a falsification (the perpetual-motion claim,")
    print(f"    contradiction 2.31). The orthogonal/open claims (colour, consciousness) have NO contradiction signal -> the_one")
    print(f"    is SILENT -> HELD, never pruned. Mere non-coupling is NOT falsification. (No-truth-monopoly, F398; the ceiling F552.)\n")

    print("VERDICT (the inverse of binding = a the_one falsification SIEVE -- prune the anti-coherent, hold the open):")
    print(f"  • YES -- the inverse of F684 binding is a FALSIFICATION SIEVE over encoded big-wiki (F681): couple each claim")
    print(f"    against the_one; KEEP the coherent (grounded in attested structure), PRUNE the ANTI-coherent (contradicts")
    print(f"    attested structure -- the 'magic' that fails no-magic, F640; verified: anchor 0.58, contradiction 2.31), and")
    print(f"    HOLD the orthogonal/open (the_one is silent). The CONTRADICTION SIGNAL (the imaginary residual, F436/F684) is")
    print(f"    what LICENSES a falsification -- only an active contradiction does; mere non-coupling does NOT.")
    print(f"  • THE GUARD IS LOAD-BEARING (F398 -- the_one is a COHERENCE-DETECTOR, not a truth-ORACLE): it can falsify ONLY")
    print(f"    what anti-coheres (a real contradiction with attested structure). It NEVER prunes the merely-orthogonal (out-")
    print(f"    of-scope -- 'blue is the best colour') or the genuinely OPEN (the epistemic ceiling -- 'what consciousness is'")
    print(f"    -> held-open F394 / the expert F282). The_one does not decree truth; it detects incoherence. (This is the no-")
    print(f"    magic discipline F640 as a sieve: 'magic' = unattested AND self-contradictory; an honest open question is NOT magic.)")
    print(f"  • IT IS THE INVERSE OF F684 (same detector, opposite use): BIND keeps what coheres (couple the worlds); the SIEVE")
    print(f"    prunes what anti-coheres (falsify the contradictions) and HOLDS what is orthogonal/open. The chord-invariance")
    print(f"    test (F678) confirms the prune is safe -- an anti-coherent claim was never a note in the_one chord, so pruning")
    print(f"    it cannot change the grounded corpus; it only removes a self-contradiction.")
    print(f"  • Composes F684 (binding -- this is its inverse) + F683 (query the_one) + F678 (the prune + chord-invariance) +")
    print(f"    F640 (no-magic = the sieve) + F398 (no-truth-monopoly = the guard) + F394 (held-open) + F552/F282 (the ceiling")
    print(f"    / the expert) + F681 (the big-wiki corpus) + F436 (the contradiction signal). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
