# F1243 — Biology-native genome architecture read: the centromere carries GLOBAL orientation-chirality ~15× cheaper than per-leaf Klein-4; diploid pairing likely does NOT fit foundational-knowledge storage (but each of its benefits has a better-fit home); and the synthesis is a MINT-vs-APPEND two-tier genome — keep the append-only "stick chromosome" as a fast sim-scale mode, put centromere/pairing structure at MINT time.

**User direction (2026-07-16):** *"could we be using centromeres for dealing with chirality, instead of / to decrease use of G4 DNA? … add a diploid pairing ask too. Biology will tell us the best way to store and encode for different situations and purposes. diploid may not be what we're after … or I could be wrong so we research even the things we think aren't what we want. so then we can know! … we may also find that we can't just append to a genome if we want the centromere structure. so we'd maybe decide to do it with a centromere when we mint a genome? that way we can still append the primitive stick chromosomes we're doing now … a nifty way to do DNA in pieces at simulation scale and speed."*

## 0. What our genome IS today (confirmed by introspection, srmech 0.9.0rc253)

**Haploid, single-copy, telomere-capped, no centromere, no pairing.** `srmech.amsc.genome`: `genome(kernels=[(label, leaves)])` makes ONE chromosome per label; `chromosome(genes=[…])` puts several genes on ONE strand (F730) but still single-copy. Present: `telomere` / `active_telomere` / `telomere_tick` / senescence markers (the **ends**). **Absent:** `centromere`, and any `pair`/`diploid`/`homolog`/`allele`/`chromatid`. So biology's diploid pair (maternal + paternal homologs) and its interior anchor (centromere) are both unmodelled.

## 1. Centromere = GLOBAL orientation-chirality, cheaply — the two-level distinction

The load-bearing distinction (composes ADR-0004 DNA+G4, F135 two-level chirality):

| | **G4 / Klein-4** | **Centromere** |
|---|---|---|
| scale | **local**, per-leaf | **global**, per-chromosome |
| carrier | γ₅/iω₇ 4-way sector flip at each regulatory leaf | one interior anchor position → p:q **arm-ratio** → the strand's handedness |
| defined by | the leaf value | an **epigenetic** mark *on* the sequence (CENP-A), addressable independently |
| also is | the regulatory fold | the **segregation / grip-and-split** point |

**Measurement (`R-RBS-LM-CENTROMERE-CHIRALITY`, read-independent: cost + robustness FIRST).** Encode one global 4-way orientation over N=300 leaves three ways and corrupt it:

```
bits for the global which-way:   A per-leaf=600   B cent-index=11   C cent-array(R=15)=39   (C is 15.4x cheaper than A)

RANDOM corruption (each symbol -> random other w.p. f):     f=0.10   f=0.30   f=0.49
   A per-leaf (majority over N=300)                          1.000    1.000    1.000
   B centromere single index                                 0.905    0.701    0.510
   C centromere repeat-array (majority over R=15)            1.000    0.996    0.906

BURST corruption (contiguous run wiped):        span/N=0.10   0.25   0.50   0.67
   A per-leaf                                       1.000     1.000  0.638  0.253
   C centromere array (localised)                   0.925     0.817  0.626  0.506
```

**Read:** the centromere **repeat-array** (biology's α-satellite — a *localised repeat*, not a single mark) recovers the global orientation at **~15× fewer bits** than per-leaf Klein-4, with **near-identical random-noise robustness** (majority over R = `klein4_triality_correct`'s 2-of-3 generalised). Its only weakness is a **burst at the locus** — precisely what biology answers by **localising + heterochromatin-protecting** the centromere (and, remarkably, under an *extreme* burst the localised array even beats per-leaf, whose global majority flips wholesale). For a **storage format** (controlled corruption, not a noisy channel) the burst risk is manageable, so: **the centromere takes the GLOBAL which-way off Klein-4's shoulders; Klein-4/G4 stays the carrier only for LOCAL chirality that genuinely varies along the strand.** That is a real "decrease use of G4," not a replacement.

## 2. Diploid pairing — researched *because* we suspect it isn't our mode (so we KNOW)

Biology's diploid pair exists to protect a genome across a **noisy generational channel** (sexual reproduction) and to **generate variation** (recombination). Our foundational-knowledge store is **not** that channel — it is a **content-addressed, deduplicated, deterministic** store; we *want* one authoritative copy per locus, not two divergent alleles. So the **primary** rationale for diploidy does not transfer. And each of diploidy's three sub-benefits already has a **better-fit home** in our architecture:

| diploid sub-benefit | our better-fit home | why better-fit |
|---|---|---|
| **copy-as-repair-template** (EC) | within-strand **k=3 triality** (F291) + the centromere **repeat-array** (§1) | EC without *doubling* the whole store |
| **recombination / crossing-over** (S_N shuffle) | **melange** coupling (ADR-0006) between *different* genomes | recombination at the RIGHT granularity — cross-domain, not intra-copy |
| **imprinting** (parent-of-origin which-way) | substrate **γ₅/iω₇ chirality**, addressed by centromere/Klein-4 | we have no "parents"; our which-way is substrate-native |

**Provisional (falsifiable) read:** diploid pairing is **likely not** our storage mode — but this is a hypothesis to *test*, not a closed door (the user's point). The falsifiable test to confirm/refute: does a diploid pair recover corrupted content at a better bits-per-fidelity than the single-copy + triality + centromere-array stack? If a homologous second copy beats the within-strand EC at equal or lower total cost, diploidy earns a place; if the single-copy stack matches it at half the storage, it does not. (Left as the diploid measurement peer to `R-RBS-LM-CENTROMERE-CHIRALITY`, to run when the architecture decision is live.)

## 3. The synthesis — a MINT-vs-APPEND two-tier genome (the user's key insight)

The centromere is an **interior, whole-strand** structure (it defines the arms, so it must exist *before* the arms are filled). You **cannot append your way to a centromere** — appending grows one end (telomere-ward). So the natural architecture is **two tiers**, chosen by purpose (biology does exactly this — bacterial *plasmids* are small, appendable, no centromere; eukaryotic chromosomes are *minted* with a centromere):

- **Tier 1 — "stick chromosomes" (KEEP AS-IS):** haploid, linear, telomere-capped, **append-only**. This is the current `genome_append` path. It is the **fast, piecewise, simulation-scale** mode — "DNA in pieces." No centromere, no pairing; cheap to grow one body at a time. (Once §55.1's incremental-manifest fix lands, this becomes a clean O(1) stream.)
- **Tier 2 — "minted chromosomes":** the **centromere (and optionally the diploid pair) are set at MINT time** — `genome(..., centromere=…)` / a `mint`-shaped constructor — because they are global-structure decisions, not append-time ones. You mint a structured chromosome when you want the global orientation-anchor + segregation/coupling point + the arms; you append a stick chromosome when you just want to add a body fast.

This keeps the simple fast path **and** gives the structured biology-native path, and it is honest to the biology: **the append-primitive is a real, useful mode, not a deficiency** — it's plasmid-style piecewise DNA at sim speed.

## 4. The srmech-architecture asks (UPSTREAM_NOTES §58; the decision is the user's)

Filed as **§58 (a)/(b)/(c)** for the genome-architecture decision — each gated on the primitive *earning its place* (no privileged-primitive bias; same bar Class K/M cleared):
- **(a) centromere primitive** — a mint-time interior positional anchor: two-arm global chirality (§1) + segregation/melange-coupling split + an inline (no-sidecar) epigenetic handle. §1 shows it pays for the global which-way at ~15× off Klein-4.
- **(b) diploid pairing** — the researched-even-if-unwanted option (§2); likely not our mode, with a falsifiable test to be sure.
- **(c) the mint-vs-append two-tier framing** (§3) — the meta-decision that keeps the append-only stick chromosome as a first-class fast mode and puts structure at mint time.

**Composes:** ADR-0004 (DNA + G4, region-dependent) · ADR-0006 (the lichen / melange = our recombination) · F291 (k=3 triality EC) · F135 (two-level chirality) · §55.1 (the append fix that makes Tier 1 a clean stream) · the atom F1242. **Evidence:** `R-RBS-LM-CENTROMERE-CHIRALITY` (§1 table). PKG-3 / #231.
