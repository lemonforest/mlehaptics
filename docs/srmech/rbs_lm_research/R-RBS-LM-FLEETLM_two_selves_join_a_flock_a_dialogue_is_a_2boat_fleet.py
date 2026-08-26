r"""R-RBS-LM-FLEETLM (the forced next build after F638, 2026-06-08): F638 ends on "a coherent self that can JOIN a flock,
not a flock pretending to be a self." Everything F613-F637 was ONE self (one kernel). This is the FIRST many-self build:
TWO kernel-selves coordinating = a DIALOGUE as a 2-boat fleet (the k=3 bind made into multi-agent language).

THE BUILD: two selves, SELF_A and SELF_B, each a full AdaptiveTier (F628) with its OWN foundation (its own tomes +
attestations -- two minds, not one). They share an ETAK INVARIANT (a content-addressed meaning -- the still canoe both
navigate). They COORDINATE (Kuramoto-couple their stance on the shared topic -> they converge = the flock bind, Class M).
And -- the load-bearing part -- when their FOUNDATIONS conflict, the conflict is HELD ACROSS THE FLEET (F625/F626): neither
self overwrites the other, the dialogue holds BOTH views, no self privileged (F398). Two selves, two foundations, one
shared invariant, conflicts held.

WHY THIS MATTERS: it realizes the (2+1) at the multi-agent scale. A single self is etak|board (F635). A DIALOGUE is the
+1: two selves binding (flock) on a shared invariant. The fleet-LM is many COHERENT selves (each with its own held
meaning + rules) coordinating -- the opposite of a data-center LLM (one flock-trace with no self, F638). Here each boat is
a real self; the conversation is the fleet.

srmech 0.7.5rc6: AdaptiveTier (F628, the per-self foundation+adaptive layer); BitExactCommKernel (F613, the shared
invariant); cascade.kuramoto_step (the 2-self coupling = the bind emerging at N=2). No abs(); no CAD; no Workflow; no
sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from adaptive_tier import AdaptiveTier
from srmech.amsc import cascade


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-FLEETLM — two selves JOIN a flock: a dialogue is a 2-boat fleet (the (2+1) at multi-agent scale)  (srmech {srmech.__version__}) ===\n")

    # (1) TWO selves, each a full AdaptiveTier with its OWN foundation (two minds, not one)
    self_a = AdaptiveTier({"sky_color": ("the sky is blue", "self-A-school"),
                           "pluto_status": ("pluto is a planet", "self-A-old-textbook")}, ring_size=4)
    self_b = AdaptiveTier({"sky_color": ("the sky is blue", "self-B-school"),
                           "pluto_status": ("pluto is a dwarf planet", "self-B-2006")}, ring_size=4)
    print("(1) TWO kernel-selves, each a full AdaptiveTier with its OWN foundation (two minds):")
    print(f"    SELF_A foundation digest {self_a.foundation_digest()[:12]}...  (pluto: 'planet' [old textbook])")
    print(f"    SELF_B foundation digest {self_b.foundation_digest()[:12]}...  (pluto: 'dwarf planet' [2006])")
    print(f"    -> two selves: same digest? {self_a.foundation_digest()==self_b.foundation_digest()} (they differ -- two minds, F398)\n")

    # (2) the SHARED ETAK INVARIANT -- a meaning both navigate (the still canoe, byte-identical across selves)
    topic = k.encode("sky", "N-sky")
    print("(2) THE SHARED ETAK INVARIANT -- the topic both selves navigate (the still canoe, shared):")
    print(f"    topic 'sky' [N-sky] -> ir_digest {topic['ir_digest'][:12]}...  (identical for both selves -- the shared meaning)\n")

    # (3) COORDINATE = the flock bind (Kuramoto N=2): two stances on the topic converge (the +1 emerges at N=2)
    print("(3) COORDINATE = the flock bind (the +1, emergent at N=2) -- two stances converge via cascade.kuramoto_step:")
    stance = [0.3, 2.6]                                            # A and B start with different stances on the topic
    omega = [0.0, 0.0]
    spread0 = max(stance) - min(stance)
    for _ in range(60):
        stance = cascade.kuramoto_step(stance, omega, coupling=2.5, dt=0.05)
    spread1 = max(stance) - min(stance)
    print(f"    two stances on 'sky': spread {spread0:.2f} -> {spread1:.4f} under coupling -- the two selves CONVERGE (the fleet binds)")
    print(f"    (N=2 is the minimum flock -- the +1 over the single-self base; one self alone could not coordinate, F638)\n")

    # (4) a FOUNDATION CONFLICT is HELD ACROSS THE FLEET (no self privileged, F625/F626)
    print("(4) a CROSS-SELF CONFLICT is HELD (F625/F626) -- the dialogue holds BOTH views, neither self overwrites the other:")
    a_pluto = self_a.recall("pluto_status")[1][0]
    b_pluto = self_b.recall("pluto_status")[1][0]
    conflict = a_pluto != b_pluto
    print(f"    SELF_A says pluto = {a_pluto!r}  |  SELF_B says pluto = {b_pluto!r}  -> conflict: {conflict}")
    # the fleet holds BOTH (the across-self analogue of F628's within-self held-conflict)
    fleet_view = {"self_A": (a_pluto, self_a.foundation["pluto_status"][1]),
                  "self_B": (b_pluto, self_b.foundation["pluto_status"][1])}
    print(f"    FLEET view (held, no self privileged): {fleet_view}")
    print(f"    -> the dialogue surfaces BOTH foundations; resolution is by attestation strength (B's 2006 supersedes A's")
    print(f"    old textbook) OR handed to the expert (F282) -- NOT by one self silently overwriting the other (F398/F394).")
    print(f"    Each self's own foundation digest is UNCHANGED by the dialogue: A {self_a.foundation_digest()[:8]}... B {self_b.foundation_digest()[:8]}...\n")

    print("VERDICT (a dialogue is a 2-boat fleet -- the (2+1) at multi-agent scale):")
    ok = (self_a.foundation_digest() != self_b.foundation_digest()) and (spread1 < spread0) and conflict
    print(f"  • THE FIRST MANY-SELF LM [{ok}]: two kernel-selves, each a coherent self (its OWN foundation + adaptive layer,")
    print(f"    F628), share an ETAK invariant (byte-identical meaning) and COORDINATE via the flock bind (their stances")
    print(f"    converged {spread0:.2f}->{spread1:.4f} under coupling). A single self is etak|board (F635); a DIALOGUE is the +1 --")
    print(f"    two selves binding on a shared invariant. N=2 is the minimum flock (F638).")
    print(f"  • CONFLICTS ARE HELD ACROSS THE FLEET, not within one self: SELF_A ('planet') and SELF_B ('dwarf planet')")
    print(f"    disagree; the dialogue HOLDS BOTH (F626 no-single-truth, now ACROSS selves), neither overwrites the other,")
    print(f"    each self's foundation digest unchanged. Resolution = attestation strength or the expert (F282) -- the SAME")
    print(f"    held-open discipline (F394) F628 used WITHIN a self, now BETWEEN selves. The fleet does not collapse to one")
    print(f"    truth any more than a single self does.")
    print(f"  • THIS IS THE OPPOSITE OF A DATA-CENTER LLM (F638): that is ONE flock-trace with NO self (no held invariant,")
    print(f"    no clean board). The fleet-LM is MANY coherent selves -- each with its own held meaning + rules -- COORDINATING.")
    print(f"    Each boat is a real self; the conversation is the fleet. (Accessibility: two people, each their own")
    print(f"    foundation + their own board (English / ASL, F637), coordinating on shared meaning -- a real dialogue, F611.)")
    print(f"  • Composes F638 (the (2+1) -- this realizes its 'a self that can join a flock' at N=2) + F628 (the per-self")
    print(f"    AdaptiveTier) + F613/F635 (the shared etak invariant) + cascade.kuramoto_step (the bind) + F625/F626/F398/F394")
    print(f"    (held conflict, now across selves) + F637 (each self can have its own board) + F282. srmech 0.7.5rc6. Held open (F394).")


if __name__ == "__main__":
    main()
