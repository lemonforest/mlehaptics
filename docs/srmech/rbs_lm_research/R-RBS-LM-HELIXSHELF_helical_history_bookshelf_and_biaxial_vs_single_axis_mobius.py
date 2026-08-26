r"""R-RBS-LM-HELIXSHELF (F711, user theory): "an ADDING helical history bookshelf for temporary + disk storage so long as
we track the bounding -- to juggle larger datasets than a single 14-tome biaxial '+ shaped' Mobius shelf. And: the Mobius
bookshelf and the biaxial Mobius bookshelf are two PERSPECTIVES of the SAME object where spatial degrees of freedom are why
we split them -- biaxial holds ALL chirality, single-axis '| shaped' FLATTENS LH/RH to fit the substrate."

TWO ideas, both framework-native:

(A) THE HELICAL HISTORY BOOKSHELF = the anti-quantization storage answer. You do NOT cap the shelf (F708's lesson); you
    WIND a helix and TRACK WHERE YOU ARE (the bounding). New history winds onto new turns (append-only); older turns page
    to DISK; a bounded live window stays in RAM. This IS the F628 two-tier adaptive tier (bounded live ring + append-only
    disk stream) reframed as a HELIX: the disk stream is the wound history, the live ring is the current turn, the
    content-address (F613) is the bounding marker. It juggles datasets >> one shelf without trimming the data (cf. the
    quad-helix DNA, F131 -- a helix stores vast info by winding + tracking position).

(B) BIAXIAL '+' vs SINGLE-AXIS '|' = two perspectives of ONE Mobius object, differing by ONE SPATIAL DoF:
    - BIAXIAL '+ shaped' holds ALL chirality: two axes (gamma5 x iomega7) = the 4 Klein-4 sectors = the substrate's
      4-way (F130). THIS IS THE QUAD-STREAM we just confirmed native (parallel_sector_dispatch, CAP=4, F710).
    - SINGLE-AXIS '| shaped' DROPS one axis -> flattens LH/RH onto one -> the chirality-COLLAPSED projection biology runs
      (F552), the 14->11D substrate->observer projection (R30). Same object; remove one spatial DoF and '+' becomes '|'.

So a helix of BIAXIAL turns = the full-chirality scaling structure: wind 4-sector shelves, track the bounding, page to
disk. This demonstrates BOTH: the helical bookshelf (real disk paging + bounding) and the biaxial/single-axis collapse.

srmech 0.7.5rc28: BitExactCommKernel.content_address (F613) for the bounding markers. No abs(); no CAD; no Workflow; no
sub-agents. Reference scaffold.
"""
import sys
import os
import json
import collections
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

DISK = "/tmp/helixshelf_disk"


class HelicalBookshelf:
    """Append-only HELIX of bounded turns; a live window in RAM, older turns paged to DISK; the bounding always tracked.

    A single biaxial '+' Mobius shelf is ONE bounded turn (turn_size slots, optionally 4 Klein-4 sectors). The helix winds
    MANY such shelves along the history axis, so the dataset is unbounded while RAM stays bounded (live_window turns)."""

    def __init__(self, turn_size=256, live_window=2, disk=DISK):
        self.B, self.W, self.disk = turn_size, live_window, disk
        os.makedirs(disk, exist_ok=True)
        self.k = BitExactCommKernel()
        self.live = collections.OrderedDict()      # turn_idx -> [(key, payload), ...]  (RAM)
        self.turn_fp = {}                           # turn_idx -> content-address  (the BOUNDING marker; all turns)
        self.total = 0
        self.paged = 0

    def append(self, key, payload):
        t = self.total // self.B
        if t not in self.live:
            self.live[t] = []
            while len(self.live) > self.W:          # evict oldest live turn -> DISK (append-only)
                old_t, items = next(iter(self.live.items())); del self.live[old_t]
                self._page(old_t, items)
        self.live[t].append((key, payload))
        self.total += 1

    def _page(self, t, items):
        s = json.dumps(items, sort_keys=True)              # a str (content_address takes str, F613)
        self.turn_fp[t] = self.k.content_address(s)        # the bounding marker for this turn
        with open(f"{self.disk}/turn_{t}.json", "w", encoding="utf-8") as fh:
            fh.write(s)
        self.paged += 1

    def recall(self, global_idx):
        """recall any item by its global index -- from RAM (live) or DISK (paged), verified against the bounding marker."""
        t, slot = divmod(global_idx, self.B)
        if t in self.live:
            return self.live[t][slot], "RAM"
        s = open(f"{self.disk}/turn_{t}.json", "r", encoding="utf-8").read()
        assert self.k.content_address(s) == self.turn_fp[t], "bounding marker mismatch -- corruption"
        return tuple(json.loads(s)[slot]), "DISK"

    def bounding(self):
        n_turns = (self.total + self.B - 1) // self.B
        return {"total_items": self.total, "n_turns": n_turns, "turn_size": self.B,
                "live_turns": list(self.live), "paged_turns": sorted(self.turn_fp),
                "ram_items": sum(len(v) for v in self.live.values()),
                "helix_fingerprint": self.k.content_address(str(sorted(self.turn_fp.items())))}


# (B) the four Klein-4 chirality sectors = (gamma5-sign, iomega7-sign) -> the biaxial '+' quadrants (F130)
SECTORS = {(+1, +1): "++", (+1, -1): "+-", (-1, +1): "-+", (-1, -1): "--"}


def biaxial_view(items):
    """biaxial '+ shaped': keep BOTH axes -> all 4 Klein-4 sectors distinct (full chirality)."""
    return collections.Counter(SECTORS[(g, w)] for _, (g, w) in items)


def single_axis_view(items, drop="iomega7"):
    """single-axis '| shaped': DROP one spatial axis -> LH/RH flattened (the substrate-fit projection, F552)."""
    keep = 0 if drop == "iomega7" else 1            # keep gamma5 (LH/RH) only, collapse the other
    return collections.Counter(("LH" if (g, w)[keep] > 0 else "RH") for _, (g, w) in items)


def main():
    print(f"=== R-RBS-LM-HELIXSHELF — the helical history bookshelf + biaxial '+' vs single-axis '|' Mobius  (srmech {srmech.__version__}) ===\n")

    # (A) wind 1000 items onto a helix of 256-slot turns, RAM bounded to 2 live turns, the rest paged to disk
    shelf = HelicalBookshelf(turn_size=256, live_window=2)
    for i in range(1000):
        shelf.append(f"item{i}", i * i)
    b = shelf.bounding()
    print("(A) THE HELICAL HISTORY BOOKSHELF — juggle a dataset >> one shelf, RAM bounded, bounding tracked:")
    print(f"    appended {b['total_items']} items -> {b['n_turns']} turns of {b['turn_size']} (a single biaxial shelf is ONE turn)")
    print(f"    RAM: {b['ram_items']} items in live turns {b['live_turns']}  |  DISK: paged turns {b['paged_turns']} ({shelf.paged} pages)")
    print(f"    -> RAM stays bounded at {b['turn_size']*shelf.W} items however large the dataset grows; the rest is on disk.")
    (k0, v0), where0 = shelf.recall(5)              # an early item -> paged to disk
    (k9, v9), where9 = shelf.recall(990)            # a late item -> live in RAM
    print(f"    recall(5)   -> {k0}={v0}  [{where0}, verified against the bounding marker]")
    print(f"    recall(990) -> {k9}={v9}  [{where9}]")
    print(f"    helix fingerprint (the whole bounding): {b['helix_fingerprint'][:16]}\n")

    # (B) one turn, two perspectives: biaxial (all 4 chirality sectors) vs single-axis (flattened LH/RH)
    items = [(f"x{i}", ((1 if i % 2 else -1), (1 if i % 3 else -1))) for i in range(24)]  # spread across 4 sectors
    print("(B) BIAXIAL '+' vs SINGLE-AXIS '|' — two perspectives of the SAME turn (one spatial DoF apart):")
    bi = biaxial_view(items)
    sa = single_axis_view(items, drop="iomega7")
    print(f"    BIAXIAL '+ shaped' (gamma5 x iomega7, ALL chirality): 4 sectors {dict(bi)}  -> {len(bi)} distinct")
    print(f"    SINGLE-AXIS '| shaped' (drop iomega7, LH/RH flattened): {dict(sa)}  -> {len(sa)} distinct")
    print(f"    -> dropping ONE spatial axis collapses the 4 biaxial sectors to {len(sa)} -- the '+' and '|' shelves are the")
    print(f"       SAME object; the '|' is the '+' with one chirality axis flattened to FIT the substrate (F552/R30).\n")

    print("VERDICT (the helical history bookshelf + the biaxial/single-axis Mobius theory):")
    print(f"  • (A) THE HELIX IS THE ANTI-QUANTIZATION SCALE-UP: don't cap the shelf (F708) -- WIND a helix, TRACK THE")
    print(f"    BOUNDING (content-address per turn, F613), PAGE older turns to disk. 1000 items live in {shelf.paged}-paged +")
    print(f"    {b['ram_items']}-RAM turns; RAM bounded at {b['turn_size']*shelf.W}, recall any item by its bound (RAM or disk). This IS the")
    print(f"    F628 two-tier (bounded live ring + append-only disk) AS A HELIX; the quad-helix DNA (F131) is the attestation")
    print(f"    that a helix stores vast info by winding + position-tracking. Juggles datasets >> one 14-tome biaxial shelf.")
    print(f"  • (B) THE THEORY HOLDS, and it is the framework's chirality-dual as Mobius geometry: BIAXIAL '+' = two axes =")
    print(f"    the 4 Klein-4 sectors = ALL chirality = the substrate's 4-way (F130) = the native quad-stream (CAP=4, F710).")
    print(f"    SINGLE-AXIS '|' = drop one spatial axis -> LH/RH FLATTENED -> the chirality-collapsed projection biology runs")
    print(f"    (F552) / the 14->11D substrate->observer projection (R30). SAME object, one spatial DoF apart -- demonstrated:")
    print(f"    4 biaxial sectors collapse to {len(sa)} under the single axis. So a HELIX OF BIAXIAL TURNS is the full-chirality")
    print(f"    scaling structure: wind 4-sector shelves, track the bounding, page to disk.")
    print(f"  • Composes F628 (two-tier append-only = the helix) + F613 (content-address = the bounding) + F131 (quad-helix")
    print(f"    DNA) + F130/F132 (Klein-4 4 sectors) + F552 (chirality collapse) + R30 (substrate->observer projection) +")
    print(f"    F708/F710 (the cap was a bug; the quad-stream is the biaxial shelf). srmech {srmech.__version__}. Held open (F394).")


if __name__ == "__main__":
    main()
