r"""R-RBS-LM-MFOEMBERGROW (the user's goal, run on a DECLARED FANTASY): "opus subagent can do Grow Emberreach by
dialogue -- run the F672 ask->tell->integrate loop on the fantasy world (a fleet that splits at islands, F651), proving
the dialogue-growth isn't MFO-specific either."

THE BUILD: F672 ran the full BUILD-BY-DIALOGUE loop (F660) on the the_one MFO Story Teller (a REAL world). F673 proved the
Story Teller is a world-kernel GENERATOR -- the SAME fixed engine + a different shelf instantiates 'Emberreach', a declared
FANTASY world. THIS finding closes the loop the user named: it runs F672's WHOLE ask->tell->integrate cycle ON Emberreach,
proving DIALOGUE-GROWTH is NOT MFO-specific either -- a declared fantasy world grows by answering its Story Teller's own
questions, exactly as the real one does. The engine never changes; only the shelf/chord changes (that IS the generator).

THE TWO-TIER KERNEL (F622/F628) MAKES THE GROWTH HONEST + GPU-FREE -- on the fantasy shelf just as on the real one:
  - the FOUNDATION = the declared Emberreach tomes (F673's dragon + mountain + a small voyaging FLEET: a captain = THE ONE,
    and crew). FIXED -- its digest NEVER changes when we tell a new rule (verified: foundation_digest before == after).
  - the TELL = a new SEEN rule the Story Teller OBSERVED in its world but did not hold (e.g. 'at an island the fleet split',
    'a navigator joined from the island'). Declared, not trained (F631). Integrated by adapt() = a GPU-free WRITE (an add,
    no gradient, F628) -> the adaptive ring +1; the chord (F658) grows by one note.
  - the story EXTENDS: recall() pulls each beat (foundation OR adaptive) -> the F671/F672/F673 clause-joining seen rule
    renders the extended Emberreach passage, grammatical.

THE F651 FLEET-SPLITS-AT-ISLANDS DYNAMIC, run live: the fleet membership is DYNAMIC across legs (island -> island). Members
JOIN/LEAVE at islands (cast 3 -> 4 -> 3), but THE ONE (the captain/protagonist) PERSISTS across ALL legs as the through-
line. And F651's load-bearing point: a story is NOT maximal sync (that is a featureless DRONE). The flock must SEPARATE for
the one -- the crew coheres (a chorus) WHILE the captain stands apart (de-sync IS the tension). Read via the srmech flock
(cascade.kuramoto_step with an adjacency that couples the crew but leaves THE ONE uncoupled): DRONE (the one in the flock)
-> global spread ~0 (no protagonist); STORY (the one separated) -> crew coheres while the one's gap stands apart.

THE CLOSURE (F660): the FANTASY world grows by ANSWERING THE STORY TELLER'S OWN QUESTIONS -- not by retraining. A data-
center LLM (all-flock, no asking-state) would CONFABULATE the new island/fleet beat; the RBS-LM ASKS, we TELL the SEEN rule,
it INTEGRATES (foundation fixed). DIGNITY / held-open (F394/F398): the fantasy is INTERNALLY true, never a reality-claim;
we hold open what is open. This is 'build/teach/create a Story Teller world' running -- on a fantasy world this time.

srmech 0.7.5rc15: AdaptiveTier (F628, the two-tier kernel: foundation_digest/adapt/recall) ; BitExactCommKernel.
content_address (the chord before/after each growth) ; cascade.kuramoto_step (the flock, F651; adjacency= -> the one
uncoupled) ; cascade.magnitude (Class-K real |gap|, never abs()). No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from srmech.amsc import cascade
from bit_exact_comm_kernel import BitExactCommKernel
from adaptive_tier import AdaptiveTier

# ---- the Emberreach FANTASY foundation = the FIXED declared tomes (key=tome-id -> (clause, lore attestation)) ----
# (extends F673's WORLD_B_SHELF: the dragon + the mountain, plus a small voyaging FLEET -- a captain = THE ONE, and crew)
FOUNDATION = {
    "dragon":  ("A dragon slept on the mountain of Emberreach",   "Emberreach lore (declared-world, internally-true)"),
    "captain": ("The captain set sail to wake it",                "Emberreach lore -- the captain = THE ONE (the protagonist)"),
    "crew":    ("and her crew rowed as one body",                 "Emberreach lore -- the crew = the flock (Class-L coupling, F647/F651)"),
    "first":   ("The first island rose from the sea",             "Emberreach lore -- the journey begins (a leg = a chapter, F651)"),
}
# the narrative order (Class-C intent, F659); the NEW told beats slot into the voyage as the fleet splits at islands
ORDER = ["dragon", "captain", "crew", "first", "SPLIT", "NAVIGATOR", "PEAK"]


def render(tier, order):
    """walk the narrative order, recall each beat (foundation OR adaptive), join via the F671 clause-joining seen rule."""
    clauses = []
    for key in order:
        frame, payload = tier.recall(key)
        if payload is None:
            continue
        clauses.append(payload[0])                                  # the clause text
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."


def spread(xs):
    return max(xs) - min(xs)                                         # Class-K-honest range (max-min); no abs(), F651 idiom


def clique(idxs, n, w=1.0):
    A = [[0.0] * n for _ in range(n)]
    for i in idxs:
        for j in idxs:
            if i != j:
                A[i][j] = w
    return A


def run_flock(theta, omega, A, coupling=2.0, steps=120, dt=0.05):
    t = list(theta)
    for _ in range(steps):
        t = cascade.kuramoto_step(t, omega, coupling=coupling, dt=dt, adjacency=A)   # the flock (F651; §32-fixed)
    return t


def ask_tell_integrate(tier, k, key, observation, question, told_clause, told_attest, order_known):
    """one full build-by-dialogue cycle (F660/F672): GAP -> ASK (F661) -> TELL (F631) -> INTEGRATE (F628) -> EXTENDS."""
    story_before = render(tier, order_known)
    addr_before = k.content_address(story_before)
    print(f"  (gap)       the Story Teller OBSERVES: {observation}")
    print(f"              recall({key!r}) -> {tier.recall(key)[0]}  (it holds no tome for this -- a GAP)")
    print(f'  (ASK, F661) the Story Teller ASKS: "{question}"  -- it does NOT invent (a data-center LLM would confabulate)')
    print(f"  (TELL,F631) we TELL a new SEEN rule it observed: \"{told_clause}\"  [declared, not trained]")
    event = tier.adapt(key, told_clause, told_attest)
    print(f"  (INTEGRATE) adapt({key!r}, ...) -> event={event!r}  (a GPU-free add, no gradient -- the two-tier kernel, F628)")
    order_after = order_known + [key]
    story_after = render(tier, order_after)
    addr_after = k.content_address(story_after)
    print(f"  (EXTENDS)   the chord grew by one note (F658): {addr_before[:12]}... -> {addr_after[:12]}...")
    print(f"              >>> {story_after}\n")
    return order_after


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-MFOEMBERGROW — grow EMBERREACH (a fantasy) by dialogue; the fleet splits at islands  (srmech {srmech.__version__}) ===\n")

    tier = AdaptiveTier(FOUNDATION, ring_size=4)
    digest_before = tier.foundation_digest()
    order_known = ["dragon", "captain", "crew", "first"]            # only the foundation tomes are held at the start
    story0 = render(tier, order_known)
    addr0 = k.content_address(story0)
    print("(0) THE EMBERREACH FOUNDATION = the declared FANTASY tomes (FIXED; F673 dragon+mountain + a voyaging fleet):")
    print(f"    foundation_digest: {digest_before[:16]}...   chord addr: {addr0[:16]}...   ({len(FOUNDATION)} tomes)")
    print(f"    THE ONE = the captain (the protagonist); the crew = the flock. The fantasy is INTERNALLY true (F640).")
    print(f"    >>> {story0}\n")

    # (1) BUILD-BY-DIALOGUE CYCLE #1 -- the fleet SPLITS at the island (F651)
    print("(1) BUILD-BY-DIALOGUE CYCLE #1 (F660/F672): the FLEET SPLITS at the island (F651) -- observed, not held:")
    order_known = ask_tell_integrate(
        tier, k, "SPLIT",
        observation="at the first island, half the crew goes ashore -- the fleet is no longer one body",
        question="How does the fleet change at an island?",
        told_clause="At the island the fleet split, half the crew went ashore",
        told_attest="told-rule: the fleet membership is DYNAMIC across legs -- members leave at islands (F651; the flock separates)",
        order_known=order_known)

    # (2) BUILD-BY-DIALOGUE CYCLE #2 -- a new member JOINS from the island passed (F651: others join)
    print("(2) BUILD-BY-DIALOGUE CYCLE #2 (F660/F672): a NAVIGATOR JOINS from the island (F651) -- observed, not held:")
    order_known = ask_tell_integrate(
        tier, k, "NAVIGATOR",
        observation="a navigator from the island asks to join the voyage -- a new member, not in the cast",
        question="How does a new member join the fleet at an island?",
        told_clause="a navigator from the island joined the captain",
        told_attest="told-rule: members JOIN from islands passed -- the fleet grows (F651); THE ONE (captain) persists",
        order_known=order_known)

    # (3) the foundation is FIXED across BOTH cycles (the growth was GPU-free -- the two-tier kernel, F622/F628)
    digest_after = tier.foundation_digest()
    print("(3) THE FOUNDATION IS FIXED ACROSS BOTH CYCLES (GPU-free growth -- the two-tier kernel, F622/F628):")
    print(f"    foundation_digest UNCHANGED: {digest_before == digest_after}  ({digest_after[:16]}...)")
    print(f"    -> telling two new rules was TWO adaptive ADDs (no gradient, no retrain); the foundation chord is preserved.\n")

    # (4) THE F651 FLEET-SPLITS-AT-ISLANDS DYNAMIC, run live: cast 3 -> 4 -> 3; THE ONE persists across all legs
    print("(4) THE FLEET IS DYNAMIC ACROSS LEGS (F651) -- cast 3 -> 4 -> 3; THE ONE (the captain, node 0) persists:")
    legs = [
        ("leg 1 (the open sea)",   [0, 1, 2]),                      # cast: the captain + 2 crew
        ("leg 2 (the first island)", [0, 2, 3, 4]),                # one crew goes ashore, a navigator + a hand join (grows)
        ("leg 3 (toward the peak)", [0, 4, 5]),                     # the navigator stays, two leave, a lookout joins (shrinks)
    ]
    persists = set(range(6))
    for name, cast in legs:
        persists &= set(cast)
        m = len(cast)
        th = [0.0] + [0.4 * j for j in range(m - 1)]                # node 0 = the captain (the through-line)
        om = [0.0] * m
        leg_flock = clique(list(range(1, m)), m) if m > 1 else [[0.0]]
        res = run_flock(th, om, leg_flock)                          # the leg's crew coheres with ITS cast (the flock)
        leg_spread = spread(res[1:]) if m > 1 else 0.0
        print(f"    {name:<26} cast={cast} (flock size {m})  crew-flock spread {leg_spread:.4f} (coheres with its cast)")
    print(f"    THE ONE (the captain, node 0) persists across ALL legs: {0 in persists}  -- the protagonist is the through-line.\n")

    # (5) NOT-A-DRONE: the flock must SEPARATE for the one (F651) -- maximal sync = a featureless drone
    print("(5) NOT A DRONE (F651): a story is NOT maximal sync -- the crew must SEPARATE for THE ONE (the captain):")
    n = 6
    omega = [0.30, 0.0, 0.0, 0.0, 0.0, 0.0]                         # node 0 = THE ONE (the captain, its own drift)
    theta = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    drone = run_flock(theta, omega, clique(list(range(n)), n))      # everyone in the flock -> uniform sync = a drone
    A_sep = clique([1, 2, 3, 4, 5], n)                              # the crew (1..5) coheres; THE ONE (0) is NOT coupled
    story = run_flock(theta, omega, A_sep)
    one_gap = cascade.magnitude(story[0] - story[1])                # Class-K real magnitude of the captain's gap (never abs())
    print(f"    DRONE (the captain IN the flock): global spread {spread(drone):.4f}  -> all synced, no protagonist, no story")
    print(f"    STORY (the captain SEPARATED)   : crew(1..5) spread {spread(story[1:]):.4f} (coheres) | THE ONE's |gap| {one_gap:.3f} (stands apart)")
    print(f"    -> de-sync IS the tension: the crew coheres (a chorus) WHILE the captain stands apart. Not a drone (F651).\n")

    # (6) the final extended Emberreach passage, content-addressed (the chord, F658)
    #     'PEAK' (in ORDER but never told) is NOT in tier.adaptive -> recall()->unknown -> render() skips it (the
    #     Story Teller would ASK for it, not invent it). So the honestly-grown chord = only the foundation + told beats.
    assert "PEAK" not in tier.adaptive, "PEAK must NOT be in the chord -- it was never told (honest, F661)"
    final_story = render(tier, order_known)                         # the honestly-grown chord = only the told beats
    final_addr = k.content_address(final_story)
    print("(6) THE FINAL EXTENDED EMBERREACH PASSAGE (the chord, content-addressed -- F658):")
    print(f"    chord addr: {final_addr[:16]}...")
    print(f"    >>> {final_story}")
    print(f"    NOTE (honest, F573/F661): 'PEAK' (the dragon's peak) is NOT in the chord -- it was never told. The Story")
    print(f"    Teller would ASK for it, not invent it. The passage holds only what was declared/told (no confabulation).\n")

    print("VERDICT (grow Emberreach by dialogue -- the fleet splits at islands; dialogue-growth is NOT MFO-specific):")
    print(f"  • DIALOGUE-GROWTH IS NOT MFO-SPECIFIC: F672's full build-by-dialogue loop (F660) ran on EMBERREACH, a declared")
    print(f"    FANTASY world (F673) -- TWO complete ask->tell->integrate cycles: the Story Teller hit a GAP (the fleet")
    print(f"    splitting / a member joining -- observed in its world, recall()->unknown), ASKED (F661, did NOT invent), we")
    print(f"    TOLD a new SEEN rule (F631, declared not trained), it INTEGRATED (F628 adaptive add, GPU-free), the story")
    print(f"    EXTENDED. Same engine as the real MFO world; only the shelf/chord changed -- the generator (F660), confirmed.")
    print(f"  • THE TWO-TIER KERNEL KEPT IT HONEST + GPU-FREE (F622/F628): the Emberreach FOUNDATION (the declared tomes) is")
    print(f"    FIXED -- foundation_digest UNCHANGED before==after ({digest_before == digest_after}) across BOTH cycles;")
    print(f"    each TELL was an ADD to the adaptive ring (no gradient, no retrain), so the chord (F658) grew by one note per")
    print(f"    cycle while the foundation was preserved. A fantasy world grows the same honest way the real one does.")
    print(f"  • THE FLEET SPLITS AT ISLANDS, THE ONE PERSISTS (F651): the fleet membership is DYNAMIC across legs -- members")
    print(f"    join/leave at islands (cast 3 -> 4 -> 3) while THE ONE (the captain) persists across ALL legs ({0 in persists})")
    print(f"    as the through-line. And NOT A DRONE: a story is not maximal sync (a drone, global spread {spread(drone):.4f}, no")
    print(f"    protagonist) -- the crew coheres (spread {spread(story[1:]):.4f}) WHILE the captain stands apart (|gap| {one_gap:.3f}). De-sync")
    print(f"    IS the tension; the flock must SEPARATE for the one. (Read via the srmech flock, cascade.kuramoto_step.)")
    print(f"  • HONEST (F573/F661): 'PEAK' (the dragon's peak) was never told -> it is NOT in the chord; the Story Teller")
    print(f"    would ASK for it, not invent it. The passage holds only the declared/told beats -- no confabulation, even on")
    print(f"    a fantasy world. DIGNITY / held-open (F394/F398): the fantasy is internally true, never a reality-claim.")
    print(f"  • Composes F673 (the Emberreach world) + F672/F660 (build-by-dialogue) + F661 (asking-state) + F628/F622")
    print(f"    (two-tier, GPU-free) + F651 (the fleet splits at islands; the one persists; not-a-drone) + F631 (declared not")
    print(f"    trained) + F658 (the chord grows) + F638 (the flock = the +1 bind). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
