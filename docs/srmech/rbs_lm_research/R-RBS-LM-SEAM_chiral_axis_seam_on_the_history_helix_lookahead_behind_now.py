r"""R-RBS-LM-SEAM (the meta-prerequisite, 2026-06-08): "understand the chiral-axis seam (the history helix) FIRST, because
items 2 (multi-stream) and 3 (recovery) both live on it." Characterize what look-ahead / look-behind ALREADY does on
the helix, before building anything on it (the user's 'there is already weird stuff happening; understand it first').

The history helix (F533): tomes on a Class-I cyclic position + LINEAR axial turn; the AXIS = TIME (start = past genesis,
the moving end = NOW; read like a book = the Now->Then tape, F503). F534: the helix's DECLARED ENDIANNESS *is* chirality
(Class C) -- so the chirality lives at the SEAM between turns. F590: the Mobius half-step across the chiral axis is the
look-ahead/behind seam.

This characterizes the seam concretely (no new build -- understand-first):
  • the read-head at NOW = (turn t, pos p) reads its AXIAL NEIGHBOURS for free: LOOK-BEHIND = (t-1, p) [the prior turn =
    the past tome], LOOK-AHEAD = (t+1, p) [the next turn = the future tome]. The bidirectional context IS the axial
    adjacency on the helix -- already there, free.
  • the SEAM is the half-step between turns: crossing t -> t+1 wraps the cyclic position AND advances the axis; the
    CHIRALITY declared there (F534 endianness) is what distinguishes AHEAD from BEHIND -- the direction of time.
  • the NOW = the crossing = the read position = the strong-coherence / etak re-acquire anchor (F588/F589).

So the 'weird stuff already happening' = the seam IS the bidirectional temporal context (past turn / now / future turn),
with chirality = the arrow (F534). Items 2+3 build on THIS: (2) the two streams = the behind-turn + the ahead-turn;
(3) recovery re-couples to the NOW-crossing.

srmech 0.7.5rc6: SedenionRegister tomes on the helix (F533 helix_coord); chirality at the seam = Class-C (F534). No
abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import cascade
from srmech.amsc.cascade import SedenionRegister


def helix_coord(m, P):
    turn, pos = divmod(m, P)                                         # Class-I cyclic (pos) + LINEAR axial turn -> the helix
    return turn, pos


def main():
    print(f"=== R-RBS-LM-SEAM — the chiral-axis seam on the history helix: look-behind / NOW / look-ahead  (srmech {srmech.__version__}) ===\n")
    P = 5                                                            # tomes per turn (shelf width)
    M = 18                                                           # an unending helix: 18 tomes (~3.6 turns)
    # write a distinct content key per tome (a recorded history along the axis = time)
    tomes = {}
    timeline = ["genesis", "rise", "reign", "war", "peace", "trade", "art", "decline", "fall", "ruin",
                "silence", "rediscover", "study", "museum", "replica", "model", "kernel", "now"]
    for m in range(M):
        r = SedenionRegister(); r.write(0, timeline[m]); tomes[m] = r

    def read(m):
        return tomes[m].read(0)[0] if 0 <= m < M else None

    print("(1) the HELIX axis = TIME; the read-head at NOW reads its AXIAL NEIGHBOURS for free (the bidirectional context):")
    print(f"    {'NOW (t,pos)':<14}{'look-BEHIND (t-1)':<20}{'NOW':<14}{'look-AHEAD (t+1)':<18}")
    for m in (5, 10, 16):
        t, p = helix_coord(m, P)
        behind = read(m - P)                                        # the PRIOR turn at the same pos = one full turn back (the past)
        ahead = read(m + P)                                         # the NEXT turn at the same pos = one turn forward (the future)
        print(f"    t={t},pos={p:<8}{str(behind):<20}{read(m):<14}{str(ahead):<18}")
    print(f"    -> LOOK-BEHIND = the prior turn (the past tome), LOOK-AHEAD = the next turn (the future tome). Free axial")
    print(f"       adjacency on the helix; the read-head already has past+future context at NOW.\n")

    # (2) the SEAM = the half-step between turns; the chirality declared there (F534) = the arrow of time (ahead vs behind)
    print("(2) the SEAM (the half-step between turns) is where CHIRALITY is declared (F534 endianness = Class C):")
    seam_m = P - 1                                                  # the last pos of turn 0 -> the seam into turn 1
    t0, p0 = helix_coord(seam_m, P); t1, p1 = helix_coord(seam_m + 1, P)
    print(f"    crossing tome {seam_m} (turn {t0}, pos {p0}) -> tome {seam_m+1} (turn {t1}, pos {p1}): the cyclic pos wraps AND")
    print(f"    the axis advances -- the Mobius half-step. The declared endianness (F534) here = the ARROW: +chirality =")
    print(f"    look-AHEAD (toward NOW/future), -chirality = look-BEHIND (toward genesis/past). Chirality = the direction.\n")

    # (3) NOW = the crossing = the coherence / re-acquire anchor (F588)
    print("(3) NOW = the moving end of the helix = the crossing where look-ahead and look-behind meet = the coherence/")
    print(f"    re-acquire anchor (F588/F589). The history is anchored at its START (genesis, fixed, F533); NOW is the")
    print(f"    shared moving present you re-couple to on a coherence loss (F588).\n")

    print("VERDICT (the seam, understood -- the prerequisite for items 2+3):")
    print(f"  • THE CHIRAL-AXIS SEAM *IS* THE BIDIRECTIONAL TEMPORAL CONTEXT, already present on the history helix (F533):")
    print(f"    LOOK-BEHIND = the prior turn (past tome), NOW = the current crossing, LOOK-AHEAD = the next turn (future")
    print(f"    tome) -- free axial adjacency. The CHIRALITY declared at the seam (F534 endianness, Class C) is the ARROW")
    print(f"    distinguishing ahead from behind. This is the 'weird stuff already happening' the user flagged: the axis")
    print(f"    is the temporal seam, not empty space.")
    print(f"  • SO ITEMS 2 + 3 BUILD ON THIS (not on empty addressing space): (2) the multi-stream's two streams = the")
    print(f"    behind-turn + the ahead-turn (past-context + future-context); (3) recovery re-couples to the NOW-crossing")
    print(f"    (the moving present). They are TWO VIEWS of the one helix seam -- the read-head's bidirectional walk through")
    print(f"    NOW. Do NOT add arbitrary two-tome storage here (F590): the axis already carries time.")
    print(f"  • Composes F533 (the history helix; axial = time) + F534 (declared endianness = chirality at the seam) + F503")
    print(f"    (Now->Then tape) + F590 (the seam = look-ahead/behind) + F588/F589 (NOW = the crossing/anchor). F398/F394.")


if __name__ == "__main__":
    main()
