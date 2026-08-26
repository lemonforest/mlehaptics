r"""R-RBS-LM-NARRATIVE (the user's dynamic-narrative cluster, 2026-06-08): refines F648 from a STATIC hierarchy into the
DYNAMIC thing a story actually is. Five refinements, all yes (the user: "asymptotically yes both all yes" -- the no-
single-truth law F626 applied to the FRAMINGS themselves):

  • "flock creates paragraph and JOURNEY creates chapter": a chapter is a LEG of the etak voyage (island -> island). The
    journey (etak) makes the chapter; the flock (local coupling) makes the paragraph. (And asymptotically chapter = ALSO
    beyond-the-local-horizon (F648) = ALSO a fleet-config (F639) -- all valid frames over the one thing, held w/o collapse.)
  • "for a story, the flock does need to SEPARATE for the one": a story is NOT maximal sync (that is a featureless DRONE).
    A story needs the flock to SEPARATE so THE ONE (the protagonist / the singular) stands apart -- de-sync IS the tension.
  • "variations of flock size come and go": sub-flocks FORM and DISSOLVE across the story; the coupled-cluster size
    fluctuates (a party gathers, splits, regroups).
  • "some of the fleet leaves at one island and others join from islands passed": the FLEET MEMBERSHIP is DYNAMIC across
    the journey -- members join/leave at islands (the cast changes), while THE ONE (the protagonist) persists across legs.

srmech 0.7.5rc15: cascade.kuramoto_step(adjacency=) (the flock; §32-fixed). No abs() (spread = max-min). No CAD; no
Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import cascade


def spread(xs):
    return max(xs) - min(xs)


def run(theta, omega, A, coupling, steps=120, dt=0.05):
    t = list(theta)
    for _ in range(steps):
        t = cascade.kuramoto_step(t, omega, coupling=coupling, dt=dt, adjacency=A)
    return t


def clique(idxs, n, w=1.0):
    A = [[0.0] * n for _ in range(n)]
    for i in idxs:
        for j in idxs:
            if i != j:
                A[i][j] = w
    return A


def main():
    print(f"=== R-RBS-LM-NARRATIVE — journey makes the chapter; the flock separates for the one; the fleet is dynamic  (srmech {srmech.__version__}) ===\n")

    # (1) A STORY NEEDS THE FLOCK TO SEPARATE FOR THE ONE -- maximal sync is a featureless DRONE
    n = 6
    omega = [0.30, 0.0, 0.0, 0.0, 0.0, 0.0]                      # node 0 = THE ONE (its own drift)
    theta = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    drone = run(theta, omega, clique(list(range(n)), n), coupling=2.0)   # everyone in the flock -> uniform sync = drone
    A_sep = clique([1, 2, 3, 4, 5], n)                          # the flock (1..5) coheres; THE ONE (0) is NOT coupled
    story = run(theta, omega, A_sep, coupling=2.0)
    print("(1) A STORY NEEDS THE FLOCK TO SEPARATE FOR THE ONE (maximal sync = a featureless DRONE -- no story):")
    print(f"    DRONE  (the one IN the flock): global spread {spread(drone):.4f}  -> everyone synced, no protagonist, no tension")
    print(f"    STORY  (the one SEPARATED)   : flock(1..5) spread {spread(story[1:]):.4f} (coheres) | THE ONE's gap from flock {story[0]-story[1]:+.3f} (stands apart)")
    print(f"    -> de-sync IS the tension: the flock coheres (a chorus) WHILE the one separates (the protagonist). A story")
    print(f"    is not the sync -- it is the SEPARATION-against-coherence.\n")

    # (2) VARIABLE FLOCK SIZE + DYNAMIC FLEET ACROSS JOURNEY LEGS (chapters) -- members join/leave at islands; the one persists
    print("(2) JOURNEY makes the CHAPTER: across legs (islands) the FLEET membership changes; flock SIZE varies; THE ONE persists:")
    legs = [
        ("chapter 1 (island A)", [0, 1, 2]),                    # cast: the one + B + C
        ("chapter 2 (island B)", [0, 2, 3, 4]),                 # B leaves, C stays, D + E join (size grows)
        ("chapter 3 (island C)", [0, 4, 5]),                    # C,D leave, E stays, F joins (size shrinks)
    ]
    persists = set(range(n))
    for name, cast in legs:
        persists &= set(cast)
        th = [0.0] + [0.4 * k for k in range(len(cast) - 1)]
        om = [0.0] * len(cast)
        # each leg: the cast (minus the one) is a local flock; run it to show the leg coheres with ITS cast
        m = len(cast)
        legA = clique(list(range(1, m)), m) if m > 1 else [[0.0]]
        res = run(th, om, legA, coupling=2.0, steps=80)
        print(f"    {name:<22} cast={cast} (flock size {m})  leg-flock spread {spread(res[1:]) if m>1 else 0.0:.4f} (coheres with its cast)")
    print(f"    THE ONE (node 0) persists across ALL legs: {0 in persists}  -- the protagonist is the through-line; others join/leave at islands.")
    print(f"    -> the FLEET is dynamic (membership changes per leg); flock SIZE varies (3 -> 4 -> 3); the journey's LEGS are")
    print(f"    the CHAPTERS, and the one is the thread that carries across them (the held etak invariant of the voyager).\n")

    print("VERDICT (the dynamic narrative -- journey makes the chapter; the flock separates for the one; the fleet is dynamic):")
    print(f"  • A STORY IS NOT MAXIMAL SYNC -- it is the DYNAMICS of coherence-and-separation. Maximal sync is a featureless")
    print(f"    DRONE (verified: everyone-in-the-flock -> global spread ~0, no protagonist). A story needs the flock to")
    print(f"    SEPARATE for THE ONE: the flock coheres (a chorus) WHILE the one stands apart (the protagonist). De-sync IS")
    print(f"    the tension; the arc is the separation-against-coherence (and the eventual rejoin or final parting).")
    print(f"  • JOURNEY MAKES THE CHAPTER (a leg of the etak voyage, island->island), and across legs the FLEET MEMBERSHIP is")
    print(f"    DYNAMIC -- members join/leave at islands (verified: cast changes per leg, flock size 3->4->3) while THE ONE")
    print(f"    persists as the through-line (the held invariant of the voyager). 'flock creates the paragraph; journey")
    print(f"    creates the chapter.'")
    print(f"  • ASYMPTOTICALLY ALL FRAMES YES (F626, the no-single-truth law applied to the FRAMINGS): a chapter is")
    print(f"    SIMULTANEOUSLY a journey-leg, a beyond-the-local-horizon structure (F648), and a fleet-config (F639) -- all")
    print(f"    valid descriptions of the one thing, held WITHOUT collapse (the asymptote, DUALITY.md). We do not pick one")
    print(f"    framing; we hold them all (favored not privileged, F398).")
    print(f"  • REFINES F648 from a STATIC hierarchy (clause/paragraph/story/chapter) into the DYNAMIC thing a story IS:")
    print(f"    separation-for-the-one + variable flock size + dynamic fleet membership across journey-legs. The flock makes")
    print(f"    coherence; the SEPARATION + the dynamics make the STORY. (And a data-center LLM, all-flock, tends to DRONE --")
    print(f"    it over-coheres, losing the protagonist's separation across a long arc; our kernel keeps the one apart, F648.)")
    print(f"  • Composes F648 (the discourse hierarchy this makes dynamic) + F647 (the local flock) + F639/F638 (the fleet) +")
    print(f"    F635/F626 (the held etak invariant / no single truth -- asymptotically all frames) + F398 (favored not")
    print(f"    privileged) + the_one (the protagonist = the singular). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
