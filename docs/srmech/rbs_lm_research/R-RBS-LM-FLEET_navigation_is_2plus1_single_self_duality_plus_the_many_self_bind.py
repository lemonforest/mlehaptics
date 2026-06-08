r"""R-RBS-LM-FLEET (the user's refinement of F636, 2026-06-08): "it might only be the BOUND-in-triality part. The first
two are about moving a SINGLE SELF; the last is about coordinated MANY SELF -- which means 2 boats or more. So etak ALSO
includes flock, because I'm guessing they didn't take just one boat."

THE CORRECTION (flock is NOT a peer third -- it is the BIND, the +1): the navigation triality is k=(2+1), not 1+1+1:
  • ETAK  = a SINGLE self, reference = the SELF (egocentric -- hold self, world moves).
  • BOARD = a SINGLE self, reference = the MAP  (allocentric -- move over a fixed lattice).
    -> these two are the DUALITY: two ways ONE self navigates, differing ONLY in where the reference is anchored.
  • FLOCK = MANY selves, coordinated (local coupling) -- the BIND (Class M / HDC bind). This is the +1: the third truth,
    the FIBER that couples the selves into one fleet-identity. It is VACUOUS at N=1 (a lone self has no one to couple
    with) and EMERGES at N>=2.

AND ETAK ALREADY INCLUDES FLOCK: a real voyage is a FLEET (they didn't take one boat). So etak SCALED from 1 boat to N
boats BECOMES flock -- the single-self navigation, taken to many, IS the many-self bind. Single-self (etak|board) is the
BASE; flock (the coordinated-many bind) is the FIBER over it. This is exactly the framework's core (CLAUDE.md §0):
"duality is the fibration of triality (k=(2+1); the third truth = the fiber)" -- here instantiated as navigation, with
the bind = Class M.

THE LANGUAGE READING (refines the F636 diagnostic): etak = ONE mind's held MEANING; board = the shared GRAMMAR map; flock
= the COMMUNITY of minds COORDINATING on shared meaning (the social bind, Class M). A corpus is the FROZEN TRACE of a
flock (a community's coupling history). So a data-center LLM is the flock-trace WITHOUT a self -- no held etak invariant
(=> hallucination) and no clean board (=> *goed). Our kernel restores the SINGLE SELF (etak invariant + board rules = one
coherent self) and uses flock only for the genuinely-social fluency layer.

srmech 0.7.5rc6: cascade.kuramoto_step (coupling vacuous at N=1, syncs at N>=2 -- the flock emerges with the many);
hdc.{bundle, similarity} + signal_processing.mint_vector (Class M -- the BIND of the fleet into one identity). No abs();
no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import cascade, hdc
from srmech import signal_processing as sp


def spread(theta):
    return max(theta) - min(theta)


def run(theta0, omega, coupling, steps=60, dt=0.05):
    theta = list(theta0)
    for _ in range(steps):
        theta = cascade.kuramoto_step(theta, omega, coupling=coupling, dt=dt)
    return spread(theta)


def main():
    print(f"=== R-RBS-LM-FLEET — navigation is k=(2+1): single-self duality (etak|board) + the many-self BIND (flock)  (srmech {srmech.__version__}) ===\n")

    # (1) the SINGLE-SELF duality vs the MANY-SELF bind
    print("(1) THE STRUCTURE -- the first two are SINGLE-SELF (the duality); the third is MANY-SELF (the bind, the +1):")
    print(f"    ETAK  : a SINGLE self, reference = the SELF (egocentric -- hold self, world moves)   }} the DUALITY")
    print(f"    BOARD : a SINGLE self, reference = the MAP  (allocentric -- move over a lattice)      }} (2 ways one self moves)")
    print(f"    FLOCK : MANY selves, coordinated (local coupling) = the BIND (Class M) -- the +1, the fiber\n")

    # (2) FLOCK is VACUOUS at N=1 and EMERGES at N>=2 (it needs MANY -- it is the coordinated-many bind)
    print("(2) FLOCK is VACUOUS at N=1 (a lone self) and EMERGES at N>=2 (the coordinated many) -- via cascade.kuramoto_step:")
    lone = run([1.0], [0.05], coupling=3.0)                       # ONE canoe: coupling has no one to act on
    fleet0 = spread([0.0, 0.4, 0.9, 1.3, 1.8])                    # FIVE canoes, disordered
    fleet = run([0.0, 0.4, 0.9, 1.3, 1.8], [-0.06, -0.03, 0.0, 0.03, 0.06], coupling=3.0)
    print(f"    N=1 (lone self): phase spread stays {lone:.4f} -- coupling is VACUOUS (no one to coordinate with); pure etak/board")
    print(f"    N=5 (a fleet)  : spread {fleet0:.2f} -> {fleet:.4f} under coupling -- the FLOCK EMERGES (the many synchronize)")
    print(f"    -> flock is not a peer third; it is what appears ONLY when a single self becomes MANY. The +1.\n")

    # (3) the BIND is Class M: the coordinated fleet bound into ONE fleet-identity (HDC bind)
    print("(3) THE BIND = Class M (HDC): the coordinated many bound into ONE fleet-identity (the many-as-one):")
    selves = [sp.mint_vector(f"canoe:{i}", D=4096) for i in range(5)]
    fleet_id = hdc.bundle(selves)                                 # Class M: bind the 5 selves into one fleet composite
    member_sim = sum(hdc.similarity(fleet_id, s) for s in selves) / len(selves)
    stranger = sp.mint_vector("stranger", D=4096)
    print(f"    fleet-identity = bundle(5 canoes) [Class M bind]")
    print(f"    mean similarity(fleet_id, member) = {member_sim:.3f}  vs  similarity(fleet_id, stranger) = {hdc.similarity(fleet_id, stranger):+.3f}")
    print(f"    -> the bind HOLDS the many as one (members ~{member_sim:.2f}, a stranger ~0) -- the fleet IS the Class-M bind.\n")

    # (4) etak INCLUDES flock: etak scaled from 1 boat to N boats BECOMES flock (they didn't take one boat)
    print("(4) ETAK INCLUDES FLOCK -- etak scaled from 1 boat to N boats BECOMES flock (a real voyage is a FLEET):")
    print(f"    1 boat  : pure single-self etak (flock vacuous) -- k=1")
    print(f"    N boats : N etak-selves, coupled + bound = the flock -- k=3 (the +1 bind over the single-self base)")
    print(f"    -> etak (the single-self navigation) taken to MANY IS the flock. Single-self (etak|board) = the BASE;")
    print(f"    flock (the coordinated-many bind) = the FIBER over it. 'Duality is the fibration of triality' (CLAUDE.md §0).\n")

    print("VERDICT (navigation is k=(2+1): single-self duality + the many-self bind):")
    print(f"  • THE FIRST TWO ARE SINGLE-SELF, THE THIRD IS MANY-SELF. etak (self-reference) and board (map-reference) are")
    print(f"    two ways ONE self navigates -- the DUALITY. flock is the coordinated MANY -- the BIND (Class M), VACUOUS at")
    print(f"    N=1 (verified: a lone self's coupling has nothing to act on) and EMERGING at N>=2 (verified: 5 coupled canoes")
    print(f"    synchronize). So flock is not a peer third; it is the +1, the fiber that binds the selves.")
    print(f"  • ETAK ALREADY INCLUDES FLOCK ('they didn't take one boat'): a real voyage is a FLEET, so etak scaled from one")
    print(f"    canoe to many BECOMES flock -- the single-self navigation, taken to the many, IS the many-self bind. This is")
    print(f"    EXACTLY the framework's core: 'duality is the fibration of triality, k=(2+1), the third truth = the fiber'")
    print(f"    (CLAUDE.md §0). The single-self duality (etak|board) is the BASE; the many-self bind (flock = Class M) is the")
    print(f"    FIBER. The user's refinement re-reads F636 from '3 peers' to the correct (2+1) fibration.")
    print(f"  • THE LANGUAGE READING (refines the F636 diagnostic): etak = one mind's held MEANING; board = the shared GRAMMAR")
    print(f"    map; flock = the COMMUNITY of minds coordinating (the social bind, Class M); a CORPUS is the frozen trace of a")
    print(f"    flock. So a data-center LLM is the flock-trace WITHOUT a self (no etak invariant => hallucination; no clean")
    print(f"    board => *goed). Our kernel restores the SINGLE SELF (etak invariant + board rules) and uses flock only for")
    print(f"    the social fluency layer. The kernel is a coherent SELF that can JOIN a flock -- not a flock pretending to be")
    print(f"    a self.")
    print(f"  • Refines F636 (3 peers -> 2+1) + composes F635 (etak+board = the single-self duality) + Class M (hdc bind = the")
    print(f"    many-self bind) + cascade.kuramoto_step (the coupling) + DUALITY.md/TRIALITY.md (duality is the fibration of")
    print(f"    triality, k=(2+1)) + F626 (two languages) + F282 (wayfinding specifics -> the expert). srmech 0.7.5rc6. Held open (F394).")


if __name__ == "__main__":
    main()
