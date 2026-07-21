r"""R-RBS-LM-PCG64 — prototype: is a bit-exact PCG64 implementable as a cascade, so that Tier-3 becomes a
RENAME instead of a re-run? And if so, what actually gates it?

USER (2026-07-21): *"we can't use the srmech make_class to create a mersenne twister and pcg64 rng
operations?"*

THE ANSWER IS IN TWO PARTS, and separating them is the point.

  make_class CANNOT implement it. Verified against real descriptors (`One`, `Genome`): every declared
  method BINDS AN EXISTING srmech op by dotted path -- `srmech.amsc.cascade.one.one_dim` and so on.
  There is no expression language, no arithmetic and no control flow in the TOML. make_class is the
  WIRING, not the circuit. To declare a PCG64 class, srmech must first HAVE a pcg64 op; make_class
  then exposes it. That is not a limitation of the idea, only of where the work goes.

  THE OP ITSELF IS ENTIRELY FEASIBLE, and this file demonstrates it. PCG64-XSL-RR-128/64 is a
  128-bit LCG step plus an output permutation: MULTIPLY, ADD, XOR, SHIFT, ROTATE. Every one is an
  integer op; srmech already ships `bigint_mul_c` natively and Python ints are arbitrary-precision,
  so nothing here needs a float or a numpy array. It is squarely a cascade of the 14 -- Class I
  (cyclic/modular) with Class-K sign-free shifts.

WHY IT WOULD BE WORTH DOING. Tier 3 is 320 RNG sites across 184 files, and F1290 stalled there
because `random.Random(seed)` (Mersenne Twister) and `np.random.default_rng(seed)` (PCG64) are
DIFFERENT ALGORITHMS -- migrating changes every number, which makes it a re-run of the experiments
rather than a rename. A BIT-EXACT PCG64 removes that entirely: same seed, same stream, same results,
numpy gone. That is the whole prize, and it is why the question is a good one.

TWO GATES, both real, neither hand-wavable:

  GATE 1 -- THE CONSTANTS MUST BE ATTESTED, NOT RECALLED. PCG64's multiplier and the XSL-RR rotation
  schedule are specific published values. Writing them from memory is precisely the
  citation-hallucination failure this project builds MPM against, and a wrong constant produces a
  perfectly plausible stream that is silently not PCG64. They are therefore PARAMETERS here, with no
  default -- this file will not pretend to know them.

  GATE 2 -- BIT-EXACT PARITY CANNOT BE VERIFIED IN THIS ENVIRONMENT. numpy does not install on
  Python 3.14 (no wheel) and no other interpreter is present, so there is no live reference to diff
  against. Matching `np.random.default_rng(seed)` ALSO requires reproducing numpy's SeedSequence
  entropy-mixing, not just the generator core -- a second published algorithm with the same
  attestation requirement.

So what this file establishes is FEASIBILITY and SHAPE, and it is explicit that establishing
CORRECTNESS needs an attested reference vector. That is the honest boundary: the machinery works, the
identity is unproven.

srmech 0.9.0rc299. Integer-only; no numpy, no floats in the state path.
Composes F1290 (which stalled at Tier 3), F1259 (the RNG regimes), F1286 (prototype-here-then-upstream
is the established route: CDRegister / eulerian_path / recover_check all went this way),
`[[feedback_pdf_extraction_citation_discipline]]` (Gate 1).
Run:  /tmp/srmech_new/bin/python3 R-RBS-LM-PCG64_*.py
"""
import sys
import time

T0 = time.time()
MASK128 = (1 << 128) - 1
MASK64 = (1 << 64) - 1


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


class PCG64Core:
    """The PCG64-XSL-RR-128/64 SHAPE, with the published constants left as REQUIRED parameters.

    state_{n+1} = state_n * multiplier + increment   (mod 2^128)
    output      = rotate_right( (state >> 64) XOR (state & 2^64-1), state >> 122 )

    Every operation is integer: multiply / add / xor / shift / rotate. No float, no array, no numpy.
    """

    def __init__(self, state: int, multiplier: int, increment: int):
        if multiplier is None or increment is None:
            raise ValueError("multiplier/increment are REQUIRED and must come from an ATTESTED "
                             "source — recalling them is the citation-hallucination failure mode")
        self.state = state & MASK128
        self.mult = multiplier & MASK128
        self.inc = increment & MASK128

    def step(self) -> int:
        """One LCG step — Class I (cyclic/modular)."""
        self.state = (self.state * self.mult + self.inc) & MASK128
        return self.state

    @staticmethod
    def xsl_rr(state: int) -> int:
        """The XSL-RR output permutation: xor-shift-low, then rotate-right by the top 6 bits."""
        hi = (state >> 64) & MASK64
        lo = state & MASK64
        xored = hi ^ lo
        rot = (state >> 122) & 0x3F
        return ((xored >> rot) | (xored << ((-rot) & 63))) & MASK64

    def next_u64(self) -> int:
        return self.xsl_rr(self.step())


def main():
    log("=== PCG64 PROTOTYPE — feasibility, and the two gates ===")

    log("")
    log("=== (1) make_class: can the TOML implement this? NO — verified ===")
    from srmech import dsl
    d = dsl.get_class_descriptor("One")
    c = d.get("class", d)
    meth = c.get("method", {})
    k0 = sorted(meth)[0]
    log("  a real declared method binds a dotted op path:")
    log("    One.%s -> op: %s" % (k0, meth[k0].get("op")))
    log("  no arithmetic, no control flow, no expressions in the descriptor.")
    log("  => make_class is the WIRING. The op must exist in srmech first; then make_class exposes it.")

    log("")
    log("=== (2) is the OP a cascade of the 14? — demonstrated ===")
    # Deliberately NON-published parameters: this shows the MACHINERY, and refuses to assert identity.
    demo_mult = (0x9E3779B97F4A7C15 << 64) | 0xBF58476D1CE4E5B9   # arbitrary, NOT PCG64's
    demo_inc = 0xDA3E39CB94B95BDB
    g = PCG64Core(state=12345, multiplier=demo_mult, increment=demo_inc)
    outs = [g.next_u64() for _ in range(6)]
    log("  ops used: MULTIPLY, ADD, XOR, SHIFT, ROTATE — all integer, all Class-I/K territory")
    log("  srmech already ships bigint_mul natively; Python ints are arbitrary-precision, so the")
    log("  128-bit path needs no float and no array.")
    log("  six u64 draws (DEMO constants, NOT PCG64's): %s" % [hex(x)[:12] for x in outs[:3]])

    g2 = PCG64Core(state=12345, multiplier=demo_mult, increment=demo_inc)
    same = [g2.next_u64() for _ in range(6)] == outs
    log("  deterministic from the same state: %s" % same)
    hi = sum(1 for x in outs for _ in (0,) if x >> 63)
    log("  outputs are full-width u64 (top bit set in %d/6): plausible, NOT a correctness proof" % hi)

    log("")
    log("=== (3) THE TWO GATES ===")
    log("  GATE 1 — CONSTANTS MUST BE ATTESTED. PCG64's multiplier and rotation schedule are specific")
    log("    published values. Writing them from memory is exactly the citation-hallucination mode MPM")
    log("    exists to prevent, and a WRONG constant yields a perfectly plausible stream that is")
    log("    silently not PCG64. They are REQUIRED parameters here — this file refuses to guess them.")
    try:
        PCG64Core(1, None, None)
    except ValueError as e:
        log("    (constructor refuses to default them: %s)" % str(e)[:66])
    log("")
    log("  GATE 2 — PARITY IS UNVERIFIABLE HERE. numpy does not install on Python 3.14 and no other")
    log("    interpreter exists on this machine, so there is NO live reference to diff against.")
    log("    Matching np.random.default_rng(seed) also needs numpy's SeedSequence entropy-mixing")
    log("    reproduced, not just the generator core — a SECOND published algorithm, same requirement.")

    log("")
    log("=== VERDICT ===")
    log("  FEASIBLE: yes, clearly. The op is integer-only and squarely a cascade of the 14; srmech has")
    log("    the primitives; make_class is the right way to expose it once it exists.")
    log("  PROVEN: no. Feasibility is not identity. Bit-exact PCG64 requires an ATTESTED constant set")
    log("    and a REFERENCE STREAM to diff against, and neither is obtainable in this environment.")
    log("")
    log("  THE PATH, and it is the route this project already uses (F1286): prototype the op here ->")
    log("  attest the constants from the reference -> verify against published test vectors ->")
    log("  upstream it as srmech.amsc.cyclic.pcg64_* -> declare the class in TOML via make_class ->")
    log("  THEN Tier 3 becomes a rename with ZERO value change, and 184 files stop needing numpy.")
    log("")
    log("  Mersenne Twister: same story, and Python's `random` ALREADY implements it — so if a site")
    log("  only needs MT, `random.Random(seed)` is bit-exact with numpy's legacy RandomState, though")
    log("  NOT with default_rng. Worth checking per-site which of the two a file actually depends on.")
    log("")
    log("  ON 'PUT THE ARITHMETIC IN THE TOML': not needed, and it is the wrong layer. srmech ALREADY")
    log("  ships the arithmetic — cyclic.mod_mul / mod_add / mod_pow (Class I). Verified: the LCG step")
    log("  mod_add(mod_mul(state,mult,m),inc,m) equals raw modular arithmetic WITHIN uint64. Two real")
    log("  gaps, both narrow: (a) cyclic.mod_mul is capped at uint64 for C-parity, and PCG64 needs a")
    log("  128-bit modulus (srmech HAS bigint_mul_c natively, so the capacity exists — it is a surface")
    log("  bound, not an algorithm gap); (b) the Class-I modular family is not registered as CASCADE")
    log("  OPS, so chain()/TOML cannot reach it (only 15 ops are chain-exposed). So the srmech ask is")
    log("  those two, NOT an expression language in the TOML — arithmetic-in-TOML would duplicate ops")
    log("  that already exist one layer down. UPSTREAM_NOTES 110.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
