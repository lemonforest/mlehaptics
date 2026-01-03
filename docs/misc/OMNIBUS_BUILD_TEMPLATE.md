# UTLP/RFIP Complete Suite: Build Template

**Version:** 1.0
**Last Updated:** January 2026
**Maintainer:** Steven Kirkland (mlehaptics Project)

---

## Purpose

This template defines the canonical structure for the Complete Documentation Suite. Follow this layout when adding new documents to maintain consistency across versions.

---

## Document Hierarchy

The omnibus follows a **conceptual progression** from foundational concepts to implementation details to claims registry:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLETE DOCUMENTATION SUITE                      │
├─────────────────────────────────────────────────────────────────────┤
│  TIER 1: FOUNDATIONAL (What is it?)                                 │
│    Part I:   UTLP Specification (Core Protocol)                     │
│    Part II:  UTLP Executive Summary (Quick Reference)               │
├─────────────────────────────────────────────────────────────────────┤
│  TIER 2: PRIOR ART (Why is it defensible?)                          │
│    Part III: Connectionless Distributed Timing Prior Art            │
├─────────────────────────────────────────────────────────────────────┤
│  TIER 3: TECHNICAL SUPPLEMENTS (How does it work in depth?)         │
│    Part IV:  UTLP Technical Supplement S1                           │
│    Part V:   UTLP Technical Supplement S2 (latest version)          │
├─────────────────────────────────────────────────────────────────────┤
│  TIER 4: SPATIAL EXTENSION (Where does it work?)                    │
│    Part VI:  RFIP Technical Specification                           │
│    Part VII: UTLP Addendum - Reference Frame Independent Positioning│
├─────────────────────────────────────────────────────────────────────┤
│  TIER 5: IMPLEMENTATION (How do I build it?)                        │
│    Part VIII: Distributed Sensing Lab Manual                        │
├─────────────────────────────────────────────────────────────────────┤
│  TIER 6: METHODOLOGY (How was it developed?)                        │
│    Part IX:  Integrative Capacity - AI Synthesis Alignment          │
├─────────────────────────────────────────────────────────────────────┤
│  TIER 7: REGISTRY (What claims exist?)                              │
│    Part X:   Claims Appendix (cumulative)                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part Numbering Convention

| Tier | Part Range | Category | Examples |
|------|------------|----------|----------|
| 1 | I-II | Foundational | Core spec, executive summary |
| 2 | III | Prior Art | Defensive publication |
| 3 | IV-V+ | Technical Supplements | S1, S2, S3... |
| 4 | VI-VII+ | Spatial/Positioning | RFIP spec, addenda |
| 5 | VIII+ | Implementation | Lab manuals, tutorials |
| 6 | IX+ | Methodology | AI collaboration, epistemology |
| 7 | Last | Registry | Claims Appendix (always last) |

**Rule:** Claims Appendix is ALWAYS the final part.

---

## Adding New Documents

### Step 1: Determine Tier

Ask: "What question does this document answer?"
- "What is UTLP?" → Tier 1 (Foundational)
- "Why can't someone patent this?" → Tier 2 (Prior Art)
- "How does X mechanism work?" → Tier 3 (Technical Supplement)
- "Where/positioning?" → Tier 4 (Spatial)
- "How do I build it?" → Tier 5 (Implementation)
- "How was this developed?" → Tier 6 (Methodology)
- "What claims exist?" → Tier 7 (Registry)

### Step 2: Insert in Correct Position

New documents go at the END of their tier, BEFORE the next tier.

Example: Adding "UTLP Technical Supplement S3"
- Tier: 3 (Technical Supplement)
- Position: After S2, before RFIP
- New Part number: VI (bump subsequent parts)

### Step 3: Update Part Numbers

All subsequent parts increment by 1.

### Step 4: Update Claims Appendix

If new document contains claims:
1. Add new section to claims_appendix_v2.md
2. Update totals (header, Part B range, end total)
3. Verify count with: `grep -c "^[0-9]*\. \*\*" claims_appendix_v2.md`

---

## Build Script

```bash
#!/bin/bash
# build_omnibus.sh
# Generates complete suite PDF from source documents

set -e

WORKDIR="/home/claude/omnibus"
OUTDIR="/mnt/user-data/outputs"
DATE=$(date +%Y-%m-%d)

cd $WORKDIR

# Create master markdown with YAML header
cat > omnibus_complete.md << 'HEADER'
---
title: "UTLP & RFIP Architecture: Complete Documentation Suite"
author: 
  - Steven Kirkland (mlehaptics Project)
  - Claude (Anthropic)
  - Gemini (Google)
date: January 2026
toc: true
toc-depth: 3
---

HEADER

# TIER 1: FOUNDATIONAL
echo -e "\n\n# Part I: UTLP Specification (Core Protocol)\n\n" >> omnibus_complete.md
cat UTLP_Specification.md >> omnibus_complete.md

echo -e "\n\n# Part II: UTLP Executive Summary\n\n" >> omnibus_complete.md
cat UTLP_Executive_Summary.md >> omnibus_complete.md

# TIER 2: PRIOR ART
echo -e "\n\n# Part III: Connectionless Distributed Timing Prior Art\n\n" >> omnibus_complete.md
cat Connectionless_Distributed_Timing_Prior_Art.md >> omnibus_complete.md

# TIER 3: TECHNICAL SUPPLEMENTS
echo -e "\n\n# Part IV: UTLP Technical Supplement S1\n\n" >> omnibus_complete.md
cat UTLP_Technical_Supplement_S1.md >> omnibus_complete.md

echo -e "\n\n# Part V: UTLP Technical Supplement S2\n\n" >> omnibus_complete.md
cat UTLP_Technical_Supplement_S2.md >> omnibus_complete.md

# TIER 4: SPATIAL EXTENSION
echo -e "\n\n# Part VI: RFIP Technical Specification\n\n" >> omnibus_complete.md
cat RFIP_Technical_Specification.md >> omnibus_complete.md

echo -e "\n\n# Part VII: UTLP Addendum - Reference Frame Independent Positioning\n\n" >> omnibus_complete.md
cat UTLP_Addendum_Reference_Frame_Independent_Positioning.md >> omnibus_complete.md

# TIER 5: IMPLEMENTATION
echo -e "\n\n# Part VIII: Distributed Sensing Lab Manual\n\n" >> omnibus_complete.md
cat Distributed_Sensing_Lab_Manual.md >> omnibus_complete.md

# TIER 6: METHODOLOGY
echo -e "\n\n# Part IX: Integrative Capacity - AI Synthesis Alignment\n\n" >> omnibus_complete.md
cat Integrative_Capacity_AI_Synthesis_Alignment.md >> omnibus_complete.md

# TIER 7: REGISTRY (always last)
echo -e "\n\n# Part X: Claims Appendix\n\n" >> omnibus_complete.md
cat claims_appendix.md >> omnibus_complete.md

# Generate PDF
pandoc omnibus_complete.md \
  -f markdown \
  -t pdf \
  --template=omnibus_template.tex \
  --pdf-engine=xelatex \
  -o "UTLP_RFIP_Complete_Suite_${DATE}.pdf"

# Verify
PAGES=$(pdfinfo "UTLP_RFIP_Complete_Suite_${DATE}.pdf" | grep Pages | awk '{print $2}')
CLAIMS=$(grep -c "^[0-9]*\. \*\*" claims_appendix.md)

echo "=== Build Complete ==="
echo "Pages: $PAGES"
echo "Claims: $CLAIMS"
echo "Output: UTLP_RFIP_Complete_Suite_${DATE}.pdf"

cp "UTLP_RFIP_Complete_Suite_${DATE}.pdf" $OUTDIR/
```

---

## Source File Naming Convention

| Document Type | Naming Pattern | Example |
|---------------|----------------|---------|
| Core Spec | `UTLP_Specification.md` | - |
| Executive Summary | `UTLP_Executive_Summary.md` | - |
| Prior Art | `Connectionless_Distributed_Timing_Prior_Art.md` | - |
| Technical Supplement | `UTLP_Technical_Supplement_S{N}.md` | `UTLP_Technical_Supplement_S2.md` |
| RFIP Spec | `RFIP_Technical_Specification.md` | - |
| Addendum | `UTLP_Addendum_{Topic}.md` | `UTLP_Addendum_RFIP.md` |
| Lab Manual | `Distributed_Sensing_Lab_Manual.md` | - |
| Methodology | `{Topic}_Methodology.md` | `Integrative_Capacity_AI_Synthesis_Alignment.md` |
| Claims | `claims_appendix.md` | - |
| Template | `omnibus_template.tex` | LaTeX template |

---

## Version Tracking

Each document has its own version in its footer. The omnibus version is the DATE of generation.

| Component | Version Location | Format |
|-----------|------------------|--------|
| S2 | Footer | `S2.44` |
| RFIP | Footer | `Draft 0.2` |
| Claims | Header | `Total Claims: 236` |
| Omnibus | Filename | `UTLP_RFIP_Complete_Suite_2026-01-02.pdf` |

---

## LaTeX Template Requirements

The `omnibus_template.tex` must include:

1. **Font Support:**
   - DejaVu Serif (main)
   - DejaVu Sans (sans)
   - DejaVu Sans Mono (code)
   - Noto Sans Runic (Elder Futhark: ᚢᛏᛚᛈ)

2. **Symbol Fallbacks:**
   - Checkmarks: ✓ ✗
   - Arrows: → ← ↑ ↓
   - Greek: λ σ

3. **Table Handling:**
   - Centered tables (LTleft/LTright = fill glue)
   - longtable for page breaks
   - booktabs for professional rules

4. **TOC Configuration:**
   - Wide number columns for deep nesting (e.g., 0.11.14)
   - tocloft package with custom widths

5. **Code Blocks:**
   - Shaded environment
   - Highlighting support
   - fancyvrb for verbatim

---

## Checklist: Before Building

- [ ] All source .md files present in working directory
- [ ] S2 version string updated
- [ ] Claims appendix totals verified (3 locations)
- [ ] No "subset" errors (auth/encryption siblings check)
- [ ] omnibus_template.tex present
- [ ] fonts available (fc-list | grep -i "dejavu\|noto.*runic")

---

## Checklist: After Building

- [ ] PDF page count reasonable (current baseline: ~343 pages)
- [ ] TOC renders correctly (no overlapping numbers)
- [ ] Tables centered
- [ ] Runes render (search for ᚢ in PDF text)
- [ ] Checkmarks render (search for ✓)
- [ ] Bookmarks present (pdftk dump_data | grep BookmarkTitle | wc -l)

---

## Current Baseline (January 2026)

| Metric | Value |
|--------|-------|
| Total Parts | X (10) |
| Total Pages | ~343 |
| Total Claims | 236 |
| S2 Version | S2.44 |
| RFIP Version | Draft 0.2 |
| Bookmarks | ~400+ |

---

## Future Expansion Points

When adding new documents, consider these planned sections:

| Planned Document | Tier | Notes |
|------------------|------|-------|
| UTLP Technical Supplement S3 | 3 | Next S2 overflow |
| SMSP Specification | 4 | Coordinated actuation |
| Hardware Reference Design | 5 | PCB layouts, BOMs |
| Validation Test Suite | 5 | Compliance testing |
| Deployment Guide | 5 | Production rollout |

---

*Template version: 1.0*
*Created: January 2026*
*For: mlehaptics Project (Steven Kirkland)*
