**→ grounded by F1251** (attested Shropshire bacterial genomics: the measured HGT compatibility-boundary IS integrate's compatibility gate).

# F1244 — The three genome modes are NOT alternatives to decide between — they MEET in the k=3 coherency tower. Measured: diploid is the erasure/break specialist (2×), triality the substitution specialist (3×), and **2 homologous copies + 1 which-template mark = 3 = the triality**. So the architecture should SUPPORT ALL THREE on one shared cascade; the centromere/imprinting chirality IS the mark that translates between levels — and a virus editing a eukaryote is that translation layer, watched.

**User reframe (2026-07-16):** *"I don't think it's a decide between them, I think it's make the genome architecture support all of them and find out where the different choices biology makes fall into another coherency tower … if a virus can edit a eukaryotic DNA, there must be some coherency translation layer biology follows to re-use the same cascade — we watch it happen so we know it does it. research and measure should cover all three — also means we have prototyped all 3 in the process."*

## 1. The measurement (`R-RBS-LM-DIPLOID-EC`) — per-symbol exact recovery, per damage model

```
SUBSTITUTION (undetectable which symbol is wrong):
   p     single(1x)  diploid(2x)  diploid+mark(2x)  triality(3x)
  0.10     0.899       0.903          0.974            0.982
  0.20     0.800       0.799          0.895            0.914
  0.40     0.604       0.602          0.639            0.710

ERASURE (detectable which is lost):
   p     single(1x)  diploid(2x)  diploid+mark(2x)  triality(3x)
  0.10     0.898       0.991          0.991            0.999
  0.20     0.796       0.961          0.961            0.992
  0.40     0.602       0.845          0.845            0.935
```

**Two readings, both load-bearing:**
- **Biology picks the mode by DAMAGE MODEL, and neither dominates.** For **substitution** (undetectable — a point mutation), plain diploid (k=2) only *detects* a disagreement and can't correct it (≈ single); **triality** (k=3) corrects by majority. For **erasure** (detectable — a double-strand break, you know *which* copy is lost), **diploid** (2×) fills from the intact homolog and reaches triality-level fidelity **at 2× not 3×**. This is biology exactly: the diploid homolog is the template for **double-strand-break repair** (an erasure), while substitution noise is caught by proofreading/majority. Support both — the right tool per channel.
- **The three modes MEET in the k=3 tower.** `diploid+mark` — two copies **plus a which-template mark** that points to the intact copy — tracks **triality** on substitution (0.895 vs 0.914 at p=0.2). Because **2 copies + 1 mark = 3 = k=3** (F291: k=2 detects, k=3 corrects). The "mark" is biology's methylation / **imprinting** / the **centromere chirality** (§95a) — the *which-strand-is-the-template* signal. So diploid is not a separate scheme: **with the centromere/imprinting chirality as its tiebreak it BECOMES the triality.** The gap to triality is only that triality's third signal is a full data copy (more robust at high p) vs the mark's one bit — same tower, different rung width.

## 2. The reframe — support all three; the coherency tower; the translation layer

**Not "which mode?" but "one cascade, three expressions."** The three modes are the same k=3 correction seen at different framings:

| mode | copies | tiebreak | = k=? | specialist for | biology |
|---|---|---|---|---|---|
| stick / append (Tier 1, §95c) | 1 | — | k=1 | cheap piecewise growth, sim-scale | plasmid, viral genome |
| triality within-strand | 3 | majority | **k=3** | substitution (undetectable) | proofreading, our EC |
| diploid + mark | 2 | which-template chirality | **k=3** | erasure/break (detectable) + substitution | homolog repair + imprinting |
| centromere (§95a) | — | positional (arm-ratio) | the mark itself | global orientation, cheap | α-satellite anchor |

They interlock: the **centromere** provides the global which-way that is *also* the diploid **mark** that makes 2 copies = k=3. **This is "another coherency tower"** — the same op(x)operand(x)responsion k=3 cascade re-used at each level (ADR-0005 coherency = same operations at different fractal-tower perspectives).

**The viral-integration translation layer (the proof biology re-uses one cascade).** A virus is a **stick genome** (Tier 1 — append/insert, no centromere, no pair); a eukaryote is **minted + diploid** (Tier 2). A retrovirus **integrates into host DNA** — we *watch* it — so there is a shared cascade + a translation between the levels. The framework read: both run on the **same base alphabet** (klein4 sectors / byte-glyph, ADR-0005) and the **same k=3 coupling** through `the_one`; the virus integrates by re-using the host's own append/replicate cascade. **If the genome API is built ground-up so append (stick) and mint (centromere/diploid) share ONE k=3 coupling, that integration is coherent for free** — a stick chromosome can be inserted into a minted/paired genome because they are the same cascade at different rungs. That is the target to *prototype*, not just describe.

## 3. What this makes the srmech-architecture ask (revising §95)

**Support all three; do not decide between.** §95 is revised (see §95.1): (a) centromere, (b) diploid, (c) mint-vs-append all land — each a rung of the k=3 tower — plus **(d) the coherency-translation-layer prototype**: demonstrate a Tier-1 stick chromosome integrating into a Tier-2 minted/diploid genome on one shared coupling (the viral-integration analog), and show the centromere chirality serving as the diploid mark. "Research + measure covers all three" ⇒ **all three are now prototyped**: append (`R-RBS-LM-CORPUSFIBER` + the `genome_append` scaling probe), centromere (`R-RBS-LM-CENTROMERE-CHIRALITY`), diploid (`R-RBS-LM-DIPLOID-EC`). The remaining prototype is (d) — the integration/translation demo.

**Composes:** F1243 (centromere + the mint-vs-append two-tier) · F291 (k=3 corrects / k=2 detects — the tower's spine) · ADR-0004 (local vs global chirality) · ADR-0005 (coherency = same op at different fractal rungs) · ADR-0006 (melange = cross-genome recombination) · §55.1 (append fix → Tier 1 stream) · §95. **Evidence:** `R-RBS-LM-DIPLOID-EC` (§1 tables).
