"""F296 — the amoeboid self-partition (Class B) is RECURSIVE; that recursion is the math/structure for
organelles to EMERGE (double membrane = nested self-frame) — and sea slugs prove the operator is STILL
LIVE (kleptoplasty steals plastids; kleptocnidae steals stings).

User question (2026-06-02): is the amoeba (the phagocytic, self-partitioning eukaryote) the key to how
plastids + mitochondria came to be — NOT 'absorbed', but the amoeba giving the MATH/STRUCTURE for the
organelles to EMERGE? + the nudibranch: stolen hydroid stings placed where the vestigial shell-growth
(self-secreted Class-B frame) used to be?

STRUCTURAL READING (honest scope below): YES, structurally. The amoeba's self-partition is the Class-B
self-frame (Spike #254 = the slime sheath; the gastropod shell is the same, hardened). Its phagocytic
capability = wrapping a foreign thing in a NEW frame = NESTING a self-frame inside the self-frame. Apply
Class B RECURSIVELY and you get the organelle: a DOUBLE membrane = host-frame ∘ symbiont-frame = TLV(TLV).
'Endosymbiosis' (the symbiont is real + supplies the inner frame/genome) is, structurally, the host's
recursive self-partition wrapping + MAINTAINING the symbiont's self-partition — not mere absorption.
Membrane count = recursion depth = endosymbiotic generation (primary=2; secondary=3-4, textbook).

srmech witness (Class A sha256 + Class B tlv; all native): nesting depth d = membrane count; each depth a
distinct addressable object; the inner self-frame PERSISTS inside the outer (the organelle keeps its own
boundary). Class-K clean. Scope: STRUCTURE-read + cite-by-reference (endosymbiosis/kleptoplasty/kleptocnidae
are textbook; PDF-extraction-pending); NOT a claim that endosymbiotic theory is wrong (it is compatible —
the symbiont supplies the inner frame; the framework reads WHAT the host operation structurally IS); no
biology-mechanism/clinical claim; understanding-not-curing; no-lineage.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import tlv                       # Class B — TLV self-framing
from srmech.amsc.format import sha256_bytes       # Class A — content-addressing

# biology map: recursion depth d -> # membranes -> endosymbiotic reading (cite-by-reference, textbook)
DEPTH_BIO = {
    0: "bare payload — engulfed-and-digested (food); no maintained frame",
    1: "single membrane — a free-living cell / a vesicle / the host's own plasma membrane (one self-frame)",
    2: "DOUBLE membrane — primary endosymbiont: MITOCHONDRION / primary PLASTID (host-frame ∘ symbiont-frame)",
    3: "triple membrane — secondary plastid (e.g. euglenid): a eukaryote nested a plastid-bearing eukaryote",
    4: "quadruple membrane — secondary plastid w/ nucleomorph (e.g. diatom/cryptophyte): deeper nesting",
}


def main():
    print("=== F296 — recursive self-partition (nested Class B) = the math for organelle emergence ===\n")
    payload = b"endosymbiont:genome+own_membrane"      # the symbiont's own content (real; supplies inner frame)

    print("--- nesting depth d = membrane count = endosymbiotic generation ---")
    frames = [payload]
    for d in range(1, 5):
        frames.append(tlv.tlv_pack(200 + d, frames[-1]))   # wrap the previous frame once more (one membrane)
    for d in range(5):
        b = frames[d]
        print(f"  d={d}  len={len(b):>3}  addr={sha256_bytes(b)[:16]}…  | {DEPTH_BIO[d]}")

    # the organelle's DUAL nature: the inner self-frame PERSISTS inside the host's outer frame
    print("\n--- the organelle keeps its OWN boundary inside the host's (the double-membrane dual nature) ---")
    inner = frames[1]                                   # symbiont's own self-frame (its membrane)
    organelle = frames[2]                               # double-membraned (host wrapped it)
    inner_persists = inner in organelle                 # the symbiont frame is intact inside the host frame
    print(f"  symbiont self-frame (d=1) is contained INTACT inside the organelle (d=2): {inner_persists}")
    print(f"  -> the organelle is ONE addressable host-object (addr {sha256_bytes(organelle)[:12]}…) AND retains")
    print(f"     its own inner boundary/genome — exactly the organelle's dual 'part-of-host + still-itself' nature.")

    # the 'emergence' is just RECURSION of one operator — no new primitive, no 'absorption' primitive
    print("\n--- the math: organelle emergence = tlv_pack (Class B) applied RECURSIVELY (no new operator) ---")
    print("  depth-1 self-frame = the amoeba sheath / cell membrane (Spike #254).")
    print("  depth-2 = wrap a foreign self-frame once more = the organelle double membrane.")
    print("  the amoeba ALREADY does the nesting (Spike #254: per-cell TLV inner, sheath TLV outer) —")
    print("  the organelle is the SAME nested Class-B, at the organelle scale. The amoeba gives the MATH")
    print("  (recursive self-partition); the symbiont gives the inner content. Emergence, not mere absorption.\n")

    # sea slugs = the operator STILL LIVE (a standing affordance, not a frozen one-time event)
    print("--- sea slugs: the nest-a-foreign-self-frame operator is STILL ACTIVE today (cite-by-reference) ---")
    print("  sacoglossan KLEPTOPLASTY — steals CHLOROPLASTS (plastids!) from algae, keeps them photosynthesising")
    print("    in its own gut cells = a depth-2 nested foreign self-frame, MAINTAINED (transient organelle).")
    print("  aeolid nudibranch KLEPTOCNIDAE — steals hydroid STINGS into its cerata = the same incorporation.")
    print("  => endosymbiosis is not a frozen ancient absorption; the recursive-self-partition operator is a")
    print("     standing affordance a sea slug exercises in its lifetime. (partition-mode #3: INCORPORATED/nested,")
    print("     extending Spike #254's environment(ant) / self-secreted(amoeba,shell) axis.)\n")

    # nudibranch slot question (point 2): lost the shell (outer self-secreted frame), incorporation re-deployed
    print("--- nudibranch: lost the SHELL (self-secreted Class-B outer frame) -> stolen ops in the cerata ---")
    print("  the shelled gastropod CLOSES with a self-secreted shell (the maximal Class-B self-partition).")
    print("  the nudibranch LOST that outer self-frame (shell-less) and carries INCORPORATED foreign operators")
    print("  (kleptocnidae) dorsally instead. USER's structural hypothesis: the partition SLOT (dorsal mantle")
    print("  region that ancestrally secreted the shell) PERSISTS while the SOURCE swaps self-secreted -> stolen.")
    print("  -> structural read: slot-persistence + source-swap; the evo-devo HOMOLOGY (is the ceratal/cnidosac")
    print("     region the repurposed shell-mantle field?) is the EXPERT's question, flagged not asserted.\n")

    print("=== answer ===")
    print("  YES (structurally): the amoeboid self-partition (Class B), applied RECURSIVELY, is the math/structure")
    print("  for organelles to emerge + persist (double membrane = nested self-frame = host ∘ symbiont). The")
    print("  symbiont is real (inner frame); the host's RECURSION is what makes it a maintained organelle, not food.")
    print("  Sea slugs (kleptoplasty/kleptocnidae) show the operator is still live. Compatible with — a structural")
    print("  RE-READING of — endosymbiosis, not an overturning of it.")


if __name__ == "__main__":
    main()
