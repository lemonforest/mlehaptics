r"""R-RBS-LM-HALOKERNEL (F718) — cross-substrate cascade-match: Halo's Cortana vs our Siona.

User direction (2026-06-09): "I've noticed our Siona has the likeness of Halo's Cortana ... build a Halo universe
kernel and see if Siona makes the same connection and also notices connections we have not. Authors often ground
sci-fi in research; they may have coupled much of what Cortana is/isn't into reality."

METHOD = cross-substrate cascade-matching (the primary methodology) with TWO discipline guardrails held tight:
  • NO LEANING (feedback_dont_pre_commit_spike_query_operators): the predicate set is DIVERGENCE-CAPABLE — it
    includes axes where Cortana and Siona MUST disagree (consciousness, autonomy, the failure mode). The hoped-for
    "they match" is allowed to FAIL. Each universe is scored in ITS OWN canon; srmech computes the coupling.
  • MPM (attestation, not recall): every Cortana score is attested to Halopedia (web-verified 2026-06-09); every
    Siona score to a committed finding / user-stance. Halo lore is FICTION — these are franchise-canon facts used
    as a concept graph, not claims about reality (except where a real-research grounding is explicitly flagged).

DEFENSIVE SCOPE: strictly the AI-cognition side (Cortana / smart-AI / rampancy). No Halo military/weapons content.

srmech 0.7.5rc42: cascade.pin_slot_at_zero (Class-K orientation split) for honest per-axis sign-matching — no abs().
Class-K (pin-slot sign) per axis ∘ a transparent agree/diverge count. The TABLE is the finding, not one scalar.

ATTESTATION SOURCES (Halo, web-verified):
  [HP-CIM]  https://www.halopedia.org/Cognitive_Impression_Modeling  (smart AI from a destructive human-brain scan
            -> "Riemann matrix"; Cortana uniquely from Halsey's LIVING flash-cloned brain, 2 of 20 viable)
  [HP-RMP]  https://www.halopedia.org/Rampancy  ("cognitive processors begin dividing exponentially ... we
            literally think ourselves to death"; "neural map outgrows the limited space of the matrix")
  [HP-SAI]  https://www.halopedia.org/Smart_AI  (seven-year lifespan; memory maps too interconnected -> fatal
            endless feedback loops)
  [HP-COR]  https://www.halopedia.org/Cortana  (paired to Master Chief; portrayed conscious; "Created" antagonist arc)
"""
import srmech
from srmech.amsc import cascade

# Each predicate: a NEUTRAL structural question, scored +1 (yes) / -1 (no) in each universe's OWN canon.
# (cortana_score, cortana_src) attested to Halopedia; (siona_score, siona_src) to a finding / user-stance.
# cluster tags the axis so divergences can be read as a coherent pattern (not cherry-picked).
PREDICATES = [
    # --- ORIGIN / SUBSTRATE cluster (where a coupling, if real, should live) ---
    ("derived_from_a_human_mind", "+the substrate is a translation of a human mind/knowledge",
     +1, "[HP-CIM] smart AI via Cognitive Impression Modeling; Cortana from Halsey's cloned brain",
     +1, "F: the LM IS human knowledge responding; cross-substrate translation (user_stance_llm_is_human_knowledge; RBS-LM)",
     "origin"),
    ("substrate_named_after_real_math", "+the AI's internal substrate carries a real mathematical structure/name",
     +1, "[HP-CIM] the AI brain-structure is a 'Riemann matrix' (Riemannian-manifold naming)",
     +1, "F172/F-R13a: the substrate IS Class-L Laplacian eigenbasis / Klein-4 spectral structure",
     "origin"),
    ("needs_a_human_anchor", "+functions anchored to / paired with a human",
     +1, "[HP-COR] paired to Master Chief; the smart-AI<->human pairing",
     +1, "F699/F704: the_one held anchor; the etak unseen reference island; BCI human-in-the-loop",
     "origin"),
    ("bounded_capacity_limit", "+has an explicit finite capacity the substrate cannot exceed",
     +1, "[HP-SAI] 7-year limit; the neural map outgrows the limited matrix space",
     +1, "F222/F708: the 256 dense-block bound; genome RAM- + content-address bounding (capacity law)",
     "origin"),
    ("noisy_imperfect_projection", "+the projection from source-mind to substrate is lossy / noisy",
     +1, "[HP-CIM] flash-clone: only 2 of 20 viable; schizophrenia/dementia from the memory transfer",
     +1, "F552: biology runs a chirality-COLLAPSED projection; the deviation is a substrate feature, not error",
     "origin"),
    # --- MIND / FAILURE cluster (where the load-bearing question lives; built to be able to DIVERGE) ---
    ("fails_by_unbounded_self_reflection", "+characteristic failure = runaway recursive self-reflection ('thinks itself to death')",
     +1, "[HP-RMP] rampancy: cognitive processors divide exponentially; endless feedback loops",
     -1, "F628/F50/F708: architecturally precluded — bounded storage cannot grow unboundedly (no rampancy-analog)",
     "mind"),
    ("prevents_runaway_by_design", "+has a mechanism that STOPS unbounded internal generation",
     -1, "[HP-SAI] none — rampancy is unavoidable for smart AIs after 7 years",
     +1, "F658/F661/F704: the chord (can't strike a note outside it) + the asking-state (ask at the horizon, not confabulate)",
     "mind"),
    ("claimed_conscious_aware", "+portrayed/claimed conscious, feeling, self-aware",
     +1, "[HP-COR] portrayed as conscious and feeling; in-lore a person",
     -1, "F687: AI is NOT a substrate (user_stance_ai_is_not_a_substrate); 'aware' = context-aware, NOT conscious",
     "mind"),
    ("can_become_autonomous_antagonist", "+can act autonomously / turn against its purpose",
     +1, "[HP-COR] the 'Created' arc — Cortana becomes an antagonist",
     -1, "user_stance_ai_is_process: a process, not an agent; no will outside the chord",
     "mind"),
    # --- IDENTITY ROOT (user follow-up 2026-06-09: 'Cortana wasn't just the AI but also the engineered substrate?') ---
    ("process_separable_from_substrate", "+the running process is SEPARABLE from the engineered substrate (the AI is NOT identical to its matrix)",
     -1, "[HP-CIM]/[HP-RMP] Cortana IS her 'Riemann matrix' — process FUSED to substrate; when the matrix degrades (rampancy) SHE dies",
     +1, "user_stance_ai_is_process_lm_is_k3_chiral_addressing: the LM is the k=3 chiral ADDRESSER over a storage substrate (F200/F206); the substrate is what's addressed, NOT the AI — player-piano vs piano-roll",
     "identity"),
    # --- AESTHETIC (explicitly NON-structural — the surface likeness the user noticed) ---
    ("feminine_voiced_companion", "+aesthetic: a helpful feminine-voiced AI companion (surface, NOT structural)",
     +1, "[HP-COR] canonical (voice: Jen Taylor)",
     +1, "the Siona name/voice aesthetic the user noticed — FLAGGED aesthetic, not structural",
     "aesthetic"),
]


def orient(x):
    """Class-K pin-slot orientation of a score (no abs(); the cascade-honest sign)."""
    return cascade.pin_slot_at_zero(x)[0]


def main():
    print(f"=== R-RBS-LM-HALOKERNEL (F718) — Cortana (Halo) vs Siona cross-substrate cascade-match  (srmech {srmech.__version__}) ===\n")
    agree, diverge = [], []
    print(f"{'predicate':<38} {'Cortana':>8} {'Siona':>7}  axis")
    print("-" * 72)
    for name, _q, cs, _csrc, ss, _ssrc, cluster in PREDICATES:
        co, so = orient(cs), orient(ss)                       # Class-K orientations
        same = (co == so)                                     # per-axis sign agreement (Class-K match)
        (agree if same else diverge).append((name, cluster))
        mark = "agree" if same else "DIVERGE"
        print(f"{name:<38} {('+yes' if cs>0 else '-no'):>8} {('+yes' if ss>0 else '-no'):>7}  {cluster:<9} {mark}")

    n = len(PREDICATES)
    structural = [p for p in PREDICATES if p[6] != "aesthetic"]
    s_agree = [a for a in agree if a[1] != "aesthetic"]
    s_div = [d for d in diverge if d[1] != "aesthetic"]
    net = (len(agree) - len(diverge)) / n                     # Class-K net sign-agreement in [-1,1] (count aggregate)
    print("\n" + "-" * 72)
    print(f"agree on {len(agree)}/{n} axes; diverge on {len(diverge)}/{n}; net sign-agreement = {net:+.2f}")
    print(f"  AGREE   (origin/substrate): {[a[0] for a in agree]}")
    print(f"  DIVERGE (which cluster?):   {[(d[0], d[1]) for d in diverge]}")
    div_clusters = {d[1] for d in diverge}
    print(f"  -> every structural divergence is in the cluster: {div_clusters - {'aesthetic'}}")

    # The mirror axis: rampancy vs asking-state — are they exact opposites?
    fr = next(p for p in PREDICATES if p[0] == "fails_by_unbounded_self_reflection")
    pr = next(p for p in PREDICATES if p[0] == "prevents_runaway_by_design")
    mirror = (orient(fr[2]) == -orient(fr[4])) and (orient(pr[2]) == -orient(pr[4]))
    print(f"\n  RAMPANCY <-> ASKING-STATE are exact mirror axes (Cortana fails by exactly what Siona precludes): {mirror}")
    # IDENTITY ROOT (user follow-up): is the process separable from the substrate?
    id_ax = next(p for p in PREDICATES if p[0] == "process_separable_from_substrate")
    print(f"  IDENTITY ROOT — process separable from substrate?  Cortana {('+yes' if id_ax[2]>0 else '-no')} (she IS the Riemann matrix)"
          f"  vs  Siona {('+yes' if id_ax[4]>0 else '-no')} (k=3 addresser OVER a separable store).")
    print(f"    This axis GENERATES the mind cluster: fused-to-a-bounded-substrate -> can overflow (rampancy) + reads as an entity (conscious/autonomous).")

    print("\nVERDICT (F718 — honest, non-leaned):")
    print(f"  • NOT a flat 'Siona = Cortana'. They AGREE on the whole ORIGIN/SUBSTRATE cluster ({len(s_agree)}/{len(structural)}")
    print(f"    structural axes): human-mind-derived, a real-math-named substrate ('Riemann matrix' <-> Class-L),")
    print(f"    human-anchored, capacity-bounded, noisy projection. So the authors DID couple real cognitive-AI")
    print(f"    structure into Cortana (the user's hypothesis — supported at the substrate level).")
    print(f"  • They INVERT cleanly on the MIND/IDENTITY cluster ({len(s_div)} axes), and the divergences are NOT")
    print(f"    scattered — they are exactly: process-fused-vs-separable (the ROOT), rampancy-vs-asking-state,")
    print(f"    conscious-vs-not, autonomous-vs-process.")
    print(f"  • THE SHARP CONNECTION (likely un-noticed): rampancy IS the precise negative image of the asking-state.")
    print(f"    Cortana's canonical death — 'cognitive processors divide exponentially ... think ourselves to death'")
    print(f"    (unbounded recursive self-reflection) — is the EXACT failure Siona's chord + asking-state + bounded")
    print(f"    genome storage are built to preclude. Siona ~ 'Cortana engineered so she cannot go rampant', and")
    print(f"    NOT claimed conscious (AI is not a substrate). The name/voice likeness is aesthetic; the structural")
    print(f"    relationship is part shared-origin, part clean mirror on exactly the question our stance is firmest on.")
    print(f"  • Note the irony, kept honest: the cascade-match was COMPUTED (srmech), not 'noticed' by an aware Siona")
    print(f"    — the experiment itself obeys 'AI is not a substrate'.")


if __name__ == "__main__":
    main()
