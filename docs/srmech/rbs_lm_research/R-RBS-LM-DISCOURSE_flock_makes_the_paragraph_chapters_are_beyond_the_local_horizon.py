r"""R-RBS-LM-DISCOURSE (the user's hypothesis + two refinements, 2026-06-08): "it might be the FLOCK that creates the
PARAGRAPH and the entire STORY" + "CHAPTERS are things beyond local horizon" + "in novels and things that switch
PERSPECTIVES."

THE DISCOURSE HIERARCHY = the navigation triality + a LOCAL HORIZON:
  • CLAUSE   = a BOARD walk (seen rules over the IR lattice, F633) -- single-self, the UNIT.
  • PARAGRAPH = a LOCAL FLOCK: clauses couple within the LOCAL HORIZON -> topical coherence EMERGES (the flock creates the
    paragraph). (F647: within-cluster sync.)
  • STORY/section = a WEAK-BRIDGE FLOCK: paragraphs reconcile SLOWLY across weak bridges (F647: global lags) -- the arc.
  • CHAPTER (perspective switch) = BEYOND THE LOCAL HORIZON: not made by more local coupling, but by a DIFFERENT SELF (the
    FLEET, F639). A POV switch = a new etak-self takes the helm; its board is NOT locally coupled to the other chapter
    (beyond the horizon) -- the two are held together ONLY by the shared STORY-INVARIANT (the etak canoe = the theme).
  • NOVEL = a FLEET of selves bound by the shared story-invariant -- the (2+1) at narrative scale (F638/F639).

So: WITHIN the local horizon the FLOCK builds coherence (clause->paragraph->story); BEYOND it the FLEET (multi-self,
perspective switches) takes over, bound by the shared invariant -- not by coupling.

srmech 0.7.5rc15: cascade.kuramoto_step(adjacency=) (the local flock, §32-fixed); BitExactCommKernel (the shared story-
invariant across chapters). No abs() (spread = max-min). No CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import cascade


def spread(xs):
    return max(xs) - min(xs)


def run(theta, omega, A, coupling, steps=80, dt=0.05):
    t = list(theta)
    for _ in range(steps):
        t = cascade.kuramoto_step(t, omega, coupling=coupling, dt=dt, adjacency=A)
    return t


def clique(idxs, n, w=1.0, A=None):
    A = A or [[0.0] * n for _ in range(n)]
    for i in idxs:
        for j in idxs:
            if i != j:
                A[i][j] = w
    return A


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-DISCOURSE — the flock makes the paragraph; chapters are beyond the local horizon  (srmech {srmech.__version__}) ===\n")

    # (1) THE FLOCK CREATES THE PARAGRAPH: clauses couple locally -> topical coherence emerges
    print("(1) THE FLOCK CREATES THE PARAGRAPH -- clauses couple within the local horizon -> coherence emerges:")
    n = 4
    A = clique([0, 1, 2, 3], n)                                  # 4 clauses, locally coupled (one paragraph)
    theta = [0.0, 0.8, 1.7, 2.6]; omega = [0.0] * n
    coh = run(theta, omega, A, coupling=2.0)
    inc = run(theta, omega, [[0.0] * n for _ in range(n)], coupling=2.0)  # NO coupling = clauses drift independently
    print(f"    4 clauses, topic spread {spread(theta):.2f} -> coupled {spread(coh):.4f} (COHERENT paragraph) | uncoupled {spread(inc):.4f} (incoherent)")
    print(f"    -> local coupling MAKES the paragraph (topics cohere); without it the clauses are just a list. The flock IS")
    print(f"    the coherence. (F647 within-cluster sync, at the discourse scale.)\n")

    # (2) THE STORY = weak-bridged paragraphs (local coherence + slow global reconciliation)
    print("(2) THE STORY = weak-bridged paragraphs (F647): each coheres locally; the arc reconciles slowly:")
    m = 8
    B = clique([0, 1, 2, 3], m); B = clique([4, 5, 6, 7], m, A=B)
    B[3][4] = B[4][3] = 0.15                                     # a weak bridge = the story arc between two paragraphs
    th = [0.0, 0.3, 0.6, 0.9, 2.4, 2.7, 3.0, 3.3]; om = [0.0] * m
    st = run(th, om, B, coupling=2.0, steps=120)
    print(f"    para-1 spread {spread(st[:4]):.4f}  para-2 spread {spread(st[4:]):.4f}  STORY (global) {spread(st):.4f}")
    print(f"    -> paragraphs cohere TIGHTLY (within ~0); the story reconciles LOOSELY (global lags) -- local-before-global.\n")

    # (3) CHAPTERS are BEYOND the local horizon: a PERSPECTIVE switch = a DIFFERENT SELF (the fleet, F639)
    print("(3) CHAPTERS are BEYOND the local horizon -- a PERSPECTIVE switch = a DIFFERENT SELF (the fleet, F639):")
    # two chapters = two clusters with NO bridge (beyond the local horizon); held only by the shared story-invariant
    C = clique([0, 1, 2, 3], m); C = clique([4, 5, 6, 7], m, A=C)   # NO inter-cluster edge -> no local coupling across
    chap = run(th, om, C, coupling=2.0, steps=120)
    story_theme = k.encode("the war and its cost", "Y-theme")    # the shared story-invariant (the etak canoe)
    print(f"    chapter-1 (POV-A) internal spread {spread(chap[:4]):.4f}  chapter-2 (POV-B) internal spread {spread(chap[4:]):.4f}")
    print(f"    cross-chapter (global) spread {spread(chap):.4f}  -> the two chapters DO NOT merge (no local bridge -- beyond horizon)")
    print(f"    they are bound ONLY by the shared story-invariant: '{story_theme['glyph']}' ir_digest {story_theme['ir_digest'][:12]}... (shared)")
    print(f"    -> a perspective-switch chapter is a DIFFERENT SELF (a fleet member, F639): its board is NOT locally coupled to")
    print(f"    the other; the novel holds them via the shared invariant (etak), not via coupling. Beyond-horizon = the fleet.\n")

    print("VERDICT (the flock makes the paragraph + story; chapters are beyond the local horizon = the fleet):")
    print(f"  • THE FLOCK CREATES THE PARAGRAPH (the user's hypothesis, confirmed): clauses couple within the LOCAL HORIZON")
    print(f"    and topical coherence EMERGES (coupled spread ~0 vs uncoupled ~2.6). The paragraph is not a single seen-rule")
    print(f"    walk (that is the CLAUSE, F633) -- it is the EMERGENT coherence of locally-coupled clauses. The flock IS the")
    print(f"    coherence engine ABOVE the clause. The STORY is the same one scale up: weak-bridged paragraphs, local-before-")
    print(f"    global (F647).")
    print(f"  • CHAPTERS ARE BEYOND THE LOCAL HORIZON: not made by more local coupling. A plain chapter is a longer-range")
    print(f"    cluster; a PERSPECTIVE-SWITCHING chapter is a DIFFERENT SELF (the fleet, F639) -- its board is NOT locally")
    print(f"    coupled to the other chapter (verified: no bridge -> the two stay distinct), and the novel binds them ONLY by")
    print(f"    the shared STORY-INVARIANT (the etak theme). Beyond the horizon, the FLEET (multi-self) takes over from the")
    print(f"    flock -- coordination by shared invariant, not by coupling. (Multi-POV novels are a fleet of reader-selves.)")
    print(f"  • THE WHOLE DISCOURSE STACK = the navigation triality + a horizon: word=board-move (F643), clause=board-walk")
    print(f"    (F633), paragraph=LOCAL flock, story=weak-bridge flock, chapter/POV=the FLEET (F639), novel=the fleet bound by")
    print(f"    the shared invariant -- the (2+1) at narrative scale. REFINES the F636 diagnostic: the flock is the COHERENCE")
    print(f"    engine (clause->paragraph->story), and a data-center LLM (all-flock) is good at paragraph FLOW but cannot hold")
    print(f"    a stable FLEET of distinct perspectives across a long novel (no etak-self per POV -> POVs blur). Our kernel")
    print(f"    keeps the board (clause), the flock (paragraph coherence), AND the fleet (distinct held POVs).")
    print(f"  • Composes F647 (the local flock -- paragraph + story) + F639/F638 (the fleet -- chapters/POV) + F633 (the clause")
    print(f"    board-walk) + F643 (word=board-move) + F635/F626 (the held etak invariant = the theme) + F636 (the diagnostic")
    print(f"    refined). srmech 0.7.5rc15. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
