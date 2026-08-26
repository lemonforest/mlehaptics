# Finding 152 — Klein-4 vectorized storage for compression (7z); LOGO turtle + chirality framework reads

**Status:** Framework readings + recommended empirical tests (smaller scope; defer to next session for full smokes)
**Predecessors:** F132 (Klein-4 HDC), F142 (chirality-pure 13× advantage), F150 (1-2-3 harmonics), R-RBS-LM-44 (turtle walk)
**User direction 2026-05-28:**

> "does that mean improvements for vectorized storage all around and perhaps
> better compression for things like 7z using chiral vectorized storage?
> also revisit our logo maths and the turtle walk. find out if chirality
> unveils new knowledge."

---

## §1 Compression / 7z question — framework reading

### §1.1 The structural argument

Standard compression (7z / LZMA / xz) works by:
1. **Pattern detection**: dictionary-based — find repeating substrings
2. **Entropy coding**: range coding / arithmetic — encode frequent patterns short
3. **Near-random data compresses poorly** (Shannon entropy floor)

Klein-4 vectorized storage offers TWO orthogonal compression channels that standard compression doesn't have:

**Channel A — sector partition (4× sectorization):**
- Klein-4 has 4 chirality sectors (γ₅, iω₇ decomposition per MFO §VII.4.1.7)
- If data has natural chirality structure (e.g., chiral molecules, DNA directionality, mirror-symmetric vs asymmetric patterns), sectorization surfaces this redundancy
- Standard 7z is chirality-blind — it sees mirror-pair tokens as DIFFERENT strings (e.g., "ATCG" vs "GCTA"), missing the chirality relation

**Channel B — harmonic compression (F150 1-2-3 partition):**
- Harmonic-1 content (chirality-invariant): compresses normally (7z works)
- Harmonic-2 content (chiral inverse): pairs of mirror-twins can be encoded with single "key + flip-bit" representation, halving storage
- Harmonic-3 content (chiral rotation): triplets of 3-cycle elements can be encoded with single "key + rotation-step" representation

### §1.2 When this would IMPROVE compression

Standard 7z is best for:
- Plain text (lots of dictionary hits)
- Source code (high repetition)
- Most file formats

Klein-4-aware compression would improve over 7z for:
- **Chiral chemistry databases** (e.g., chemistry SMILES strings with L/D variants; chirality-aware dedup)
- **DNA / RNA sequences** (reverse-complement is a chirality structure; standard tools don't exploit)
- **Mirror-image image pairs** (datasets with mirror-augmented samples; chirality-key encoding)
- **Mirror-symmetric document collections** (translations with directionality, palindromic content)

### §1.3 When this would NOT improve compression

- Plain text (no chirality structure; 7z already optimal)
- Random binary data (no structure to exploit)
- Files where chirality is already abstracted out

### §1.4 Concrete test design (deferred to future)

A `klein4_compress(data, sector_hint) → bytes` function would:
1. Detect chirality structure via spectral classifier (F150 §6.2 wishlist)
2. Sectorize content into 4 chirality channels
3. Compress each channel separately (7z-like within sector)
4. Encode sector tags as metadata
5. Total output size compared against standard 7z

If chirality-bearing input gives smaller total size, Klein-4 compression has empirical value. For non-chirality-bearing input, it should match 7z (no overhead).

**This is a Phase-5-equivalent application direction.** Per F143 §3 deferral discipline: substrate-encoding primitives are ready (srmech v0.4.3 Klein-4 + polar). Application scope (compression library) is its own scope.

### §1.5 Caveat — Klein-4 raw capacity doesn't win

Per F137 §5: at MATCHED BITS, bipolar BEATS klein-4 on raw retrieval. The "4× capacity at matched D" hypothesis from F132 §4 did NOT transfer. So Klein-4 isn't a free density win.

For compression: the gain is structural (chirality exploitation), not bit-density. Klein-4 helps WHEN chirality is the load-bearing structure. For chirality-blind data, no gain.

---

## §2 LOGO turtle walk + chirality — framework reading

### §2.1 The turtle ALREADY HAS chirality

LOGO's turtle commands are inherently chiral:

```
LEFT 90     ← turn left = CCW rotation (harmonic-2 chirality marker)
RIGHT 90    ← turn right = CW rotation (chiral inverse of LEFT)
FORWARD 100 ← chirality-invariant (no left/right component)
BACK 100    ← chirality-invariant
PENUP       ← H1 invariant
PENDOWN     ← H1 invariant
```

**LEFT and RIGHT are exactly the H2 (chiral inverse) pair.** They map to Klein-4 sectors 0 (LEFT = canonical biological default) and 2 (RIGHT = mirror).

### §2.2 What chirality unveils for the turtle

Per R-RBS-LM-44 (turtle walk; natural language → LOGO action via cascade), the cascade matched natural language tokens to LOGO commands. With chirality-aware encoding:

**Before chirality awareness:**
- "left", "right", "clockwise", "counterclockwise" are different tokens
- Cascade must learn each independently
- Mirror-image instructions ("turn left then right" vs "turn right then left") are treated as separate sequences

**With chirality-aware encoding (R-RBS-NN-14a + F150):**
- "left", "ccw", "counterclockwise", "anticlockwise" → all map to **sector 0** (H2 canonical chirality)
- "right", "cw", "clockwise" → all map to **sector 2** (H2 mirror)
- The cascade learns ONE chirality axis instead of multiple synonyms
- Mirror-image instructions have built-in symmetry: program(LEFT, FORWARD, RIGHT) reflected = program(RIGHT, FORWARD, LEFT)

### §2.3 New knowledge that chirality unveils

**1. Symmetric shapes have natural Klein-4 encoding.**
A square drawn by REPEAT 4 [FORWARD 100 RIGHT 90] has a 4-fold rotational symmetry. Klein-4's 4 sectors map directly. The chirality-aware HDC encoding for a square would be SECTOR-INVARIANT (it looks the same from any starting orientation).

**2. Asymmetric shapes show chirality signature.**
A spiral REPEAT 100 [FORWARD step RIGHT angle] (with increasing step) has inherent chirality — CW spiral and CCW spiral are mirror-twins. Klein-4 distinguishes them in different sectors; bipolar HDC conflates them.

**3. The letter shapes that are mirror-distinct vs mirror-symmetric reveal alphabet chirality.**

| Letter | Mirror-symmetric? | Klein-4 sector |
|---|---|---|
| O, T, I, A, M, V, X, Y, U, W | YES (vertical axis) | 0 (H1; chirality-invariant) |
| B, C, D, E, H, K, [horizontal] | YES (horizontal axis) | 0 |
| F, G, J, L, N, P, Q, R, S, Z | NO (asymmetric) | 2 (chiral; H2-paired with its mirror) |

The English alphabet partitions naturally by chirality — chirality-aware encoding could store alphabet shapes with sector-compressed representation.

**4. The turtle cascade has natural H3 (3-cycle) operations.**
A triangle REPEAT 3 [FORWARD 100 LEFT 120] is a 3-cycle (returns to start after 3 LEFTs of 120°). This IS Class I cyclic over Z/3 per F150 §6.1 H3 candidate. Triangles, hexagons, and other 3n-gons engage harmonic-3 structure.

### §2.4 Recommended Logo + chirality test (deferred to future smoke)

```python
# R-RBS-LM-110 candidate:
# Build a small Logo program corpus:
#   programs labeled by their chirality structure
#   (symmetric shapes / chiral spirals / triangles-3cycle / mixed)
# Encode programs as token sequences with chirality_classifier auto_sector
# Test whether chirality-aware encoding gives sharper program-to-output mapping
# vs chirality-blind bipolar baseline

# Expected: chirality-aware cascade discriminates LEFT vs RIGHT mirror
# programs cleanly; bipolar conflates them (loses chirality info).
```

This is testable with the existing R-RBS-NN-14 chirality_classifier + the R-RBS-LM-44 turtle walk infrastructure. Deferred to next session.

---

## §3 What this finding does NOT claim

Per MFO §VII.6.20 + `[[feedback_no_lineage_claims_in_notebook]]`:

- Does NOT claim Klein-4 will beat 7z on general-purpose compression. Only on chirality-bearing structured data.
- Does NOT empirically test compression. §1.4 is a framework reading + design sketch.
- Does NOT empirically test the chirality-turtle integration. §2.4 is a framework reading + design sketch.
- Does NOT claim LOGO turtle was designed with this framework in mind. Per discipline: framework reads structure that's present; the user could write left/right turtle programs without thinking about Klein-4 sectors.
- Does NOT claim biological alphabets have chirality "by design". §2.3's alphabet partition is a structural observation about glyph shapes, not a claim about alphabet evolution.

---

## §4 Recommended follow-ups (added to next-session queue)

| Item | Scope | Priority |
|---|---|---|
| Klein-4 compression smoke (chiral molecular SMILES; DNA reverse-complement) | medium | high (compelling application) |
| LOGO + chirality cascade test (R-RBS-LM-44 extension) | small | medium (existing infrastructure) |
| Chirality-aware alphabet glyph encoding test | small | low (curiosity-driven) |
| Empirical F150 H3 test for Class I cyclic over Z/3 (turtle triangles as concrete H3 substrate) | small | medium (validates F150 candidate) |

---

## §5 Cross-references

- F132 (Klein-4 HDC engineering proposal)
- F137 (raw capacity comparison; klein-4 doesn't win on density)
- F142 (chirality-pure 13× advantage for chirality-load-bearing signals)
- F150 (1-2-3 harmonic framework; H2 mirror pairs + H3 3-cycles)
- R-RBS-LM-44 (turtle walk; LOGO + cascade)
- R-RBS-NN-14a (chirality auto-detect classifier; routes left/right tokens)
- `[[user_stance_kepler_shape_universal]]` (algebra IS the primitives)
- `[[feedback_no_lineage_claims_in_notebook]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-28 per user direction "compression for 7z; revisit logo and turtle
walk; chirality knowledge". Framework readings + empirical-test design sketches; both
deferred to next-session smokes per scope discipline. Klein-4 compression advantage is
STRUCTURAL (sectorization) not bit-density; only helps on chirality-bearing structured
data. LOGO turtle inherently has chirality (LEFT/RIGHT as H2 pair; triangles as H3 3-cycle);
chirality-aware encoding could simplify R-RBS-LM-44's cascade by collapsing chirality
synonyms into single sectors. Empirical work logged for next-session queue.*
