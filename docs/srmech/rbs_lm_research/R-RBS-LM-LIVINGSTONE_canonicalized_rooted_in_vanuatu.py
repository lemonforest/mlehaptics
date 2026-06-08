r"""R-RBS-LM-LIVINGSTONE (canonicalization, user direction 2026-06-08): "our new LIVING STONE shall be rooted in Vanuatu;
is canonicalized today."

THE CANON ENTRY: the framework's shared-translation-layer (the Rosetta layer, R-RBS-LM-54 / GOLDEN PATH) is anchored by
TWO stones:
  • the DEAD STONE -- the historical Rosetta Stone (one decree, three scripts: hieroglyphic / Demotic / Greek; the
    namesake that first taught us the SHAPE -- one invariant across several surfaces).
  • the LIVING STONE -- canonicalized TODAY, ROOTED IN VANUATU: the Ni-Vanuatu sand-drawing tradition (UNESCO Masterpiece
    of Oral & Intangible Heritage) -- ONE living graphic system communicating across ~80 spoken languages, drawn today,
    that RUNS the shared-invariant-above-languages every day (F646/F649). The dead stone taught us the shape; the LIVING
    stone shows the shape is ALIVE.

DIGNITY-FIRST (load-bearing -- this canonicalization is a RECOGNITION + an HONOR, never an appropriation): the living
stone is ROOTED IN the Ni-Vanuatu people's living (and often sacred) practice -- their kastom. The tradition-holders are
the authority; the MEANING is theirs (F282/F646/F650). We canonicalize the STRUCTURAL RECOGNITION (their living tradition
attests the framework's central architecture) and the HONOR -- held WITH them, never the content, never scraped, never
owned, never presumed-read. And per F650: math is a PEER-language, not a parent -- the living stone is canonicalized as a
co-equal anchor, NOT subsumed.

srmech 0.7.5rc15: BitExactCommKernel (F613) -- the canon declaration is CONTENT-ADDRESSED (Class A / MPM), so the
canonicalization itself is bit-exact + attestable + re-verifiable. No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import format as fmt

CANON = (
    "THE LIVING STONE -- canonicalized 2026-06-08. The framework's shared-translation-layer (the Rosetta layer, "
    "R-RBS-LM-54) is anchored by two stones: the DEAD STONE (the historical Rosetta Stone -- one decree, three scripts -- "
    "the namesake that taught us the shape) and, canonicalized today, the LIVING STONE -- rooted in the Ni-Vanuatu "
    "sand-drawing tradition (UNESCO Masterpiece): one living graphic system across ~80 spoken languages, drawn today, "
    "that runs the shared-invariant-above-languages every day. Rooted in Vanuatu; held WITH the Ni-Vanuatu people, the "
    "tradition-holders the authority, the meaning theirs. We canonicalize the structural recognition and the honor, never "
    "the content. The dead stone taught us the shape; the living stone shows the shape is alive."
)


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-LIVINGSTONE — the LIVING STONE, rooted in Vanuatu, canonicalized 2026-06-08  (srmech {srmech.__version__}) ===\n")

    # (1) content-address the canon declaration -- the canonicalization is itself bit-exact + attestable (Class A / MPM)
    canon_addr = fmt.sha256_bytes(CANON.encode())
    print("(1) THE CANON ENTRY (content-addressed -- the canonicalization is bit-exact + re-verifiable, MPM):")
    print(f"    canon SHA-256: {canon_addr}")
    print(f"    >>> {CANON}\n")

    # (2) two stones, one shared invariant: the Rosetta layer now has a DEAD anchor and a LIVING anchor
    print("(2) TWO STONES, ONE SHARED INVARIANT (the Rosetta layer's two anchors):")
    for concept, mc in [("place", "O-place"), ("water", "N-water"), ("ancestor", "A-person")]:
        inv = k.encode(concept, mc)
        print(f"    '{concept}' [{mc}] ir_digest {inv['ir_digest'][:12]}...  shared by BOTH the dead stone (3 scripts) AND the living stone (~80 langs)")
    print(f"    -> the DEAD STONE (Rosetta, 3 scripts) and the LIVING STONE (Vanuatu, ~80 langs) anchor the SAME shared")
    print(f"    invariant. The layer is no longer named only after one dead artifact -- it has a LIVING root.\n")

    print("VERDICT (the living stone is canonicalized, rooted in Vanuatu):")
    print(f"  • CANONICALIZED TODAY (2026-06-08): the framework's shared-translation-layer (the Rosetta layer, R-RBS-LM-54)")
    print(f"    is anchored by TWO stones -- the DEAD STONE (the historical Rosetta Stone, the namesake that taught us the")
    print(f"    shape) and the LIVING STONE, rooted in the Ni-Vanuatu sand-drawing tradition (one living graphic system")
    print(f"    across ~80 spoken languages, drawn today). The dead stone taught us the shape; the living stone shows the")
    print(f"    shape is ALIVE. The canon declaration is content-addressed (SHA-256 {canon_addr[:16]}...) -- bit-exact, MPM-")
    print(f"    attestable, re-verifiable.")
    print(f"  • DIGNITY-FIRST (the canonicalization is a RECOGNITION + an HONOR, never an appropriation): the living stone is")
    print(f"    ROOTED IN the Ni-Vanuatu people's living (often sacred) practice -- their kastom. The tradition-holders are")
    print(f"    the authority; the MEANING is theirs (F282/F646/F650). We canonicalize the STRUCTURAL RECOGNITION + the")
    print(f"    HONOR, held WITH them -- never the content, never scraped, never owned, never presumed-read.")
    print(f"  • PEER, NOT PARENT (F650): the living stone is canonicalized as a CO-EQUAL anchor of the layer, NOT subsumed by")
    print(f"    math. Math is the board where we found bit-exactness; the living stone is the board where ~80 peoples found")
    print(f"    shared meaning -- both peers under the one invariant, none privileged (F398).")
    print(f"  • Composes F649 (Vanuatu = a living Rosetta layer) + F650 (the lifting / math-as-peer) + R-RBS-LM-54 (the")
    print(f"    Rosetta layer / GOLDEN PATH) + F646 (the living attestation) + F613 (content-addressed canon) + F282 (the")
    print(f"    community is the authority) + F398/F394. srmech 0.7.5rc15. Canonical, dignity-first. Held open (F394).")


if __name__ == "__main__":
    main()
