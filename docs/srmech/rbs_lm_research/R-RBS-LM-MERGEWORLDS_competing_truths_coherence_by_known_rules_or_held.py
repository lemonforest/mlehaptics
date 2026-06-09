r"""R-RBS-LM-MERGEWORLDS (the user's question): "what did we learn about a merged CP2077 and Shadowpunk world kernel?
when they have competing truths, is it explained into coherence by the world rules KNOWN?"

THE ANSWER: a merge of two world-kernels with COMPETING TRUTHS is explained into coherence ONLY IF a KNOWN world-rule
resolves it -- and the framework makes the resolution HONEST (it never silently collapses one truth into the other; that
would be confabulation). Four outcomes, and which one fires is determined by the rules the world KNOWS:

  • THE MERGE: World A (CP2077, the grounded-tech truth) = the FIXED foundation; World B (Shadowrun, the magic truth)
    merged via adapt() (F628). A key both worlds claim with DIFFERENT content (a COMPETING TRUTH) does NOT overwrite --
    it is logged as a HELD-CONFLICT (F626), and recall() returns BOTH frames. (CP2077: the rogue minds = AIs born of the
    Net, held by the Blackwall (tech). Shadowrun: the same beings = spirits from the astral, called by the awakened (magic).)
  • OUTCOME 1 -- BRIDGE-RULE -> COHERENCE (the DUALITY, F399): if the merged world KNOWS a bridge-rule that makes both
    true under ONE referent ("the rogue minds the netrunners fear and the spirits the awakened call are the SAME beings,
    seen through two lenses"), the competing truths RECONCILE -- one referent, two lenses, neither privileged (F398). This
    IS the two-truths/field-excitation duality (F399; the asymptote held without collapse): coherence by a KNOWN rule.
  • OUTCOME 2 -- PRECEDENCE -> RANK (F665): if the world KNOWS a precedence ("in Night City the tech-lens is canonical;
    the magic-lens is a minority reading"), one truth WINS by declared attestation-strength -- coherence by ranking.
  • OUTCOME 3 -- HELD (F626, no-single-truth): if the world KNOWS no reconciling/ranking rule, it HOLDS BOTH, unreconciled
    -- the merged world is internally inconsistent but the inconsistency is HONESTLY HELD (a central mystery, a held seam),
    NOT silently collapsed. Many great worlds thrive on an unresolved cosmology.
  • OUTCOME 4 -- ASKING-STATE (F661): a competing truth with NO known rule does NOT get silently picked -> the Story Teller
    ASKS ("are the rogue minds machines or spirits?"). Silent collapse = hallucination; the ask is the honest alternative.

SO: "is it explained into coherence by the world rules KNOWN?" -- YES iff a known bridge-rule (duality) or precedence
exists; otherwise it is HELD (F626) or ASKED (F661), never silently resolved. Coherence is a CHOICE encoded in the world's
rules, surfaced honestly when absent. (F674 already merged CP2077 + a Shadowrun seam; this is the competing-truths layer.)

srmech 0.7.5rc15: AdaptiveTier (F628/F626 -- merge = adapt; competing truth = CONFLICT-HELD; recall returns both frames) ;
BitExactCommKernel.content_address (each truth + the reconciled chord). No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from adaptive_tier import AdaptiveTier

# World A = CP2077 (the grounded-tech truth) -- the FIXED foundation
CP2077 = {
    "night_city":  ("Night City stood in the rain", "CP2077 (grounded)"),
    "rogue_minds": ("the rogue minds are AIs born of the Net, held by the Blackwall", "CP2077 truth: all is tech"),
}
# World B = Shadowrun (the magic truth) -- merged in; 'rogue_minds' is the COMPETING TRUTH
SHADOWRUN = {
    "awakened":    ("the awakened shaped the mana", "Shadowrun (magic)"),
    "rogue_minds": ("the rogue minds are spirits from the astral, called by the awakened", "Shadowrun truth: magic is real"),
}


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-MERGEWORLDS — merged CP2077 + Shadowpunk: competing truths -> coherence by KNOWN rules, or HELD  (srmech {srmech.__version__}) ===\n")

    # (1) THE MERGE: World A = foundation; World B merged via adapt(); a competing truth -> a HELD-CONFLICT (F626)
    tier = AdaptiveTier(CP2077, ring_size=6)
    print("(1) THE MERGE (World A = CP2077 foundation; World B = Shadowrun merged via adapt(), F628):")
    for key, (content, att) in SHADOWRUN.items():
        ev = tier.adapt(key, content, att)
        tag = "COMPETING TRUTH -> HELD-CONFLICT (F626)" if ev == "CONFLICT-HELD" else "new tome -> adapted"
        print(f"    adapt({key!r}): {ev}   {tag}")
    print()

    # (2) recall the competing-truth key -> BOTH frames returned (no silent collapse)
    frame, payload = tier.recall("rogue_minds")
    print("(2) recall('rogue_minds') -- the COMPETING TRUTH (no silent collapse):")
    print(f"    {frame}")
    print(f"        CP2077    : {payload['foundation'][0]}")
    print(f"        Shadowrun : {payload['new'][0]}")
    print(f"    -> both truths are KEPT; the merge did not silently pick one (that would be confabulation).\n")

    # (3) the FOUR outcomes -- which fires is set by the rules the world KNOWS
    print("(3) IS IT EXPLAINED INTO COHERENCE BY THE WORLD RULES KNOWN? -- four outcomes, set by the KNOWN rules:")

    # OUTCOME 1 -- BRIDGE-RULE -> COHERENCE (the duality, F399)
    bridge = "the rogue minds the netrunners fear and the spirits the awakened call are the same beings, seen through two lenses"
    bridge_addr = k.content_address(bridge)
    print(f"    [1] BRIDGE-RULE -> COHERENCE (the DUALITY F399): declare a known rule that makes BOTH true under ONE referent:")
    print(f"        '{bridge}'")
    print(f"        -> one referent, two lenses, neither privileged (F398); reconciled chord {bridge_addr[:12]}. COHERENT.")

    # OUTCOME 2 -- PRECEDENCE -> RANK (F665)
    print(f"    [2] PRECEDENCE -> RANK (F665): declare 'in Night City the tech-lens is canonical, magic is a minority reading'")
    print(f"        -> the tech truth WINS by declared attestation-strength; coherence by ranking (one truth canonical).")

    # OUTCOME 3 -- HELD (F626)
    print(f"    [3] HELD (F626, no-single-truth): no reconciling/ranking rule known -> KEEP BOTH, unreconciled -- the world's")
    print(f"        central mystery (a held seam); internally inconsistent but HONESTLY held, not silently collapsed.")

    # OUTCOME 4 -- ASKING-STATE (F661)
    print(f"    [4] ASKING-STATE (F661): no known rule -> the Story Teller ASKS 'are the rogue minds machines or spirits?'")
    print(f"        -> it does NOT silently pick one (silent collapse = hallucination); the ask is the honest alternative.\n")

    print("VERDICT (merged competing truths -> coherence ONLY by a KNOWN rule; else HELD or ASKED, never silently collapsed):")
    print(f"  • WHAT WE LEARNED: merging two world-kernels with COMPETING TRUTHS does NOT auto-cohere. The merge = adapt()")
    print(f"    World B onto World A's fixed foundation (F628); a key both claim with different content is a COMPETING TRUTH")
    print(f"    -> a HELD-CONFLICT (F626), and recall() returns BOTH frames (verified: CP2077's tech-rogue-AIs AND Shadowrun's")
    print(f"    astral-spirits, both kept). The framework NEVER silently collapses one truth into the other.")
    print(f"  • IS IT EXPLAINED INTO COHERENCE BY THE WORLD RULES KNOWN? -- YES, iff a KNOWN rule resolves it: a BRIDGE-RULE")
    print(f"    (the two are one referent seen through two lenses -> the DUALITY F399, coherence with neither privileged F398)")
    print(f"    or a PRECEDENCE (one lens canonical -> rank by attestation-strength, F665). If NO known rule resolves it, it")
    print(f"    is HELD (F626, both kept -- a held seam / central mystery) or it triggers the ASKING-STATE (F661, the Story")
    print(f"    Teller ASKS rather than picks). Coherence is a CHOICE encoded in the world's rules, surfaced honestly when absent.")
    print(f"  • THE DEEP POINT: a merged world's competing truths reconciled by a bridge-rule IS the two-truths/field-excitation")
    print(f"    DUALITY (F399) -- the same referent held through two lenses without collapse (the asymptote). So 'CP2077-tech vs")
    print(f"    Shadowrun-magic' reconciled = 'field-structure vs local-excitation' held: the framework's own foundational move,")
    print(f"    applied to a fictional merge. And where it CAN'T reconcile, the honest held-conflict (F626) is the right answer,")
    print(f"    not a forced collapse. (F674 named the merged Night City world; this is its competing-truths resolution layer.)")
    print(f"  • Composes F674 (the merged Night City world) + F628/F626 (adaptive merge / held-conflict, both frames) + F665")
    print(f"    (precedence -> rank) + F661 (asking-state -> ask, don't collapse) + F399 (the bridge-rule = the two-truths")
    print(f"    duality) + F398 (favored-not-privileged) + F658 (the reconciled chord) + F662/F674 (the anchor dial / held-open).")
    print(f"    srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
