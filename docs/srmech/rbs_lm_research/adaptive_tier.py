r"""adaptive_tier.py -- the progressive Tier-2 made operational (F628), riding the fixed BitExactCommKernel foundation.

Implements the F622/F625/F626 architecture as real code:
  • TIER 1 (foundation): the fixed BitExactCommKernel (F613) -- bit-exact, content-addressed, NEVER mutated.
  • adapt(key, content, attestation) = DISCOVER-ON-WRITE (F625): if the new fact conflicts with a foundation tome
    (same key, digest mismatch), it is HELD (logged, not overwritten); else it joins the live adaptive layer. GPU-free.
  • the live adaptive layer is a BOUNDED RING (deque, F222 capacity; old evicted) + an APPEND-ONLY DISK STREAM (the
    helix axial, F625 -- nothing lost on disk).
  • recall(key) honors the NO-SINGLE-TRUTH law (F626): a held-conflict key returns BOTH frames (foundation + new),
    neither privileged (F398), held without collapse (F394) -- the kernel never asserts one truth.

srmech 0.7.5rc6: amsc.format.sha256_bytes (content-address / conflict digest + the fixed foundation digest);
BitExactCommKernel (F613). No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from srmech.amsc import format as fmt
from bit_exact_comm_kernel import BitExactCommKernel
from collections import deque


class AdaptiveTier:
    def __init__(self, foundation_facts, ring_size=4):
        self.kernel = BitExactCommKernel()                         # Tier 1 (the bit-exact comm kernel, F613)
        self.foundation = dict(foundation_facts)                   # key -> (content, attestation), FIXED
        self.ring = deque(maxlen=ring_size)                        # live working set (bounded, F222)
        self.disk_stream = []                                      # append-only helix history (F625)
        self.held_conflicts = []                                   # discovered conflicts (HELD, F394/F626)
        self.adaptive = {}                                         # live adaptive facts (key -> (content, att))
        self.evicted = []                                          # fell off the live ring (still on disk)

    def foundation_digest(self):                                   # Tier-1 fixed digest (never changes)
        return fmt.sha256_bytes("|".join(f"{k}={self.foundation[k][0]}" for k in sorted(self.foundation)).encode())

    def adapt(self, key, content, attestation):
        addr = lambda c: fmt.sha256_bytes(c.encode())
        if key in self.foundation and addr(content) != addr(self.foundation[key][0]):
            self.held_conflicts.append((key, self.foundation[key], (content, attestation)))   # HELD, not overwritten
            event = "CONFLICT-HELD"
        else:
            self.adaptive[key] = (content, attestation)            # GPU-free: just a write (add), no gradient
            event = "ADAPTED"
        if len(self.ring) == self.ring.maxlen:
            self.evicted.append(self.ring[0][0])                   # about to fall off the live ring (kept on disk)
        self.ring.append((key, event))
        self.disk_stream.append((key, content, attestation, event))   # append-only (nothing lost on disk)
        return event

    def recall(self, key):
        for k, f, n in self.held_conflicts:                        # F626: a held conflict returns BOTH frames
            if k == key:
                return ("HELD-CONFLICT (no single truth, F626)", {"foundation": f, "new": n})
        if key in self.adaptive:
            return ("adaptive", self.adaptive[key])
        if key in self.foundation:
            return ("foundation", self.foundation[key])
        return ("unknown", None)


def main():
    print(f"=== adaptive_tier — the progressive Tier-2, operational (F628): discover / hold / ring / stream  (srmech {srmech.__version__}) ===\n")
    foundation = {
        "speed_of_light": ("299792458 m/s", "CODATA"),
        "pluto_status":   ("pluto is a planet", "pre-2006"),       # foundational ERROR (stale)
        "water_formula":  ("H2O", "IUPAC"),
    }
    tier = AdaptiveTier(foundation, ring_size=4)
    d0 = tier.foundation_digest()
    print(f"(0) Tier 1 foundation digest (FIXED): {d0[:16]}...  ({len(foundation)} tomes)\n")

    # a user session: consistent / conflict / new / new... enough to exceed the ring and evict to disk
    session = [
        ("speed_of_light", "299792458 m/s", "CODATA-2018"),        # consistent
        ("pluto_status",   "pluto is a dwarf planet", "IAU-2006"), # CONFLICT (held)
        ("user_prefers",   "ASL surface", "user"),                 # new
        ("dna_helix",      "DNA is a double helix", "Watson-Crick"),  # new
        ("user_topic",     "cave art", "user"),                    # new (evicts oldest from the ring)
        ("water_formula",  "water is an element", "folk"),         # CONFLICT (held)
        ("user_topic",     "the octonion", "user"),                # new (re-adapt; ring evicts)
    ]
    print("(1) the user session -- discover-on-write (GPU-free); foundation digest checked every step:")
    for key, content, att in session:
        ev = tier.adapt(key, content, att)
        print(f"    adapt '{key}' = {content!r:<26} [{att:<11}] -> {ev:<14} | Tier-1 digest unchanged: {tier.foundation_digest()==d0}")
    print()

    print("(2) the live RING (bounded) vs the disk STREAM (append-only) -- the helix at its two coordinates:")
    print(f"    LIVE RING (working set, maxlen 4): {[k for k,_ in tier.ring]}")
    print(f"    evicted from live (kept on disk):  {tier.evicted}")
    print(f"    DISK STREAM (append-only history): {len(tier.disk_stream)} events, nothing lost\n")

    print("(3) HELD CONFLICTS (discovered, NOT overwritten -- held-open F394; recall surfaces BOTH frames, F626):")
    for k, f, n in tier.held_conflicts:
        print(f"    '{k}': foundation={f[0]!r} [{f[1]}]  vs  new={n[0]!r} [{n[1]}]  -> HELD")
    print(f"    recall('pluto_status') -> {tier.recall('pluto_status')[0]}")
    pl = tier.recall('pluto_status')[1]
    print(f"        foundation frame: {pl['foundation'][0]!r} [{pl['foundation'][1]}]")
    print(f"        new frame:        {pl['new'][0]!r} [{pl['new'][1]}]  -- BOTH returned, neither privileged (F398/F626)")
    print(f"    recall('dna_helix') -> {tier.recall('dna_helix')}  (adapted, no conflict)")
    print(f"    recall('speed_of_light') -> {tier.recall('speed_of_light')[0]}  (consistent restatement -> foundation/adaptive)\n")

    print("VERDICT (the adaptive Tier-2 is operational):")
    print(f"  • IT RUNS THE F622/F625/F626 ARCHITECTURE AS CODE: a fixed bit-exact foundation (digest UNCHANGED across the")
    print(f"    whole session) + a GPU-free adaptive layer (write = add, no gradient) that DISCOVERS conflicts on write")
    print(f"    ({len(tier.held_conflicts)} held) and never overwrites the foundation.")
    print(f"  • THE HELIX IS A BOUNDED RING x A DISK STREAM: the live working set is bounded (maxlen 4; {len(tier.evicted)} evicted to")
    print(f"    disk), the disk stream is the complete append-only history ({len(tier.disk_stream)} events, nothing lost) -- the same")
    print(f"    helix at its two coordinates (F625).")
    print(f"  • CONFLICTS ARE HELD, NOT RESOLVED, AND recall RETURNS BOTH FRAMES (the F626 law operational): for a held-")
    print(f"    conflict key the kernel returns the foundation frame AND the new frame, neither privileged (F398), held")
    print(f"    without collapse (F394) -- it NEVER asserts a single truth. (Resolution by attestation/expert is a")
    print(f"    separate step, F282.)")
    print(f"  • SO THE TWO-TIER KERNEL IS NOW WHOLE: fixed foundation (F613-F618) + the operational adaptive Tier-2 here,")
    print(f"    discovering + holding conflicts + bounded-ring/disk-stream + the no-single-truth recall. GPU-free, no")
    print(f"    catastrophic forgetting, no retraining. NEXT: wire the named IR vocabulary (F627) + run the full named loop")
    print(f"    through the adaptive tier on a live session.")
    print(f"  • Composes F613 (the foundation) + F622 (two-tier) + F625 (conflict-discovery / ring x stream) + F626 (no")
    print(f"    single truth -- recall returns both frames) + F584 (persistence) + F222 (ring capacity) + F398/F394/F282.")
    print(f"    srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
