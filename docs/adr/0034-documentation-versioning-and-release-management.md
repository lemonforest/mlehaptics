# 0034: Documentation Versioning and Release Management

**Date:** 2025-11-13
**Phase:** Phase 1b
**Status:** Approved
**Type:** Documentation

---

## Summary (Y-Statement)

In the context of maintaining multiple core project documents across evolving phases,
facing difficulty tracking when documentation is out of sync or outdated,
we decided to implement unified semantic versioning (v0.MAJOR.MINOR pre-release format) across all Tier 1 core documents,
and neglected per-document versioning or date-only tracking,
to achieve immediate visibility of out-of-sync documents and clear project milestone references,
accepting the overhead of updating version numbers across all docs for any change.

---

## Problem Statement

Project documentation spans multiple core files (CLAUDE.md, README.md, requirements_spec.md, etc.) that evolve during development. Without unified versioning, it's difficult to:
- Detect when documents are out of sync with each other
- Track which documentation version corresponds to which code state
- Provide clear reference points for discussions and rollback
- Signal project maturity (pre-release vs production)

---

## Context

**Background:**
- Multiple core documentation files evolve together
- Phase-based development (Phase 1b, 1c, 2, 3, etc.)
- Need to track project milestones (BLE integration, dual-device support)
- Git provides commit-level tracking but lacks semantic meaning
- Date-only tracking doesn't communicate "what changed"

**Requirements:**
- Easy detection of out-of-sync documents
- Clear project milestone tracking
- Git tag integration for version checkout
- Pre-release format signaling active development
- Low maintenance overhead

---

## Decision

Implement unified semantic versioning for project documentation using v0.MAJOR.MINOR pre-release format.

### Versioned Documents (Tier 1 - Core Project Docs)

1. CLAUDE.md - AI reference guide
2. README.md - Main project documentation
3. QUICK_START.md - Consolidated quick start guide
4. BUILD_COMMANDS.md - Essential build commands reference
5. docs/architecture_decisions.md - Design decision record (this document)
6. docs/requirements_spec.md - Full project specification
7. docs/ai_context.md - API contracts and rebuild instructions

### Excluded from Versioning

- test/ directory documents (test-specific, evolve independently)
- Session summaries (already date-tracked)
- Archived documentation (frozen by nature)

### Standard Header Format

```markdown
# Document Title

**Version:** v0.1.0
**Last Updated:** 2025-11-13
**Status:** Production-Ready | In Development | Archived
**Project Phase:** Phase 4 Complete (JPL-Compliant)
```

### Version Bump Guidelines

**v0.x.Y (Minor):** Documentation updates, clarifications, typo fixes, content additions
**v0.X.0 (Major):** New features (BLE, dual-device), architecture changes, requirement updates
**v1.0.0:** Production release (feature-complete, tested, documented)

### Git Tag Policy

- Create git tags for all minor and major version bumps
- Tag format: `v0.1.0`, `v0.2.0`, etc.
- Tag message includes brief description of changes

### CHANGELOG.md Tracking

- Track major project milestones only (not individual doc edits)
- Examples: BLE integration, Phase 4 completion, dual-device support
- Link to relevant session summaries and ADs

### Implementation Timeline

**Implementation Date:** 2025-11-13
**Initial Version:** v0.1.0 (Phase 4 Complete with BLE GATT production-ready)

---

## Consequences

### Benefits

- ✅ **Synchronization Detection:** Out-of-date docs immediately visible (mismatched version numbers)
- ✅ **Release Management:** Git tags enable rollback to specific documentation versions
- ✅ **Change Tracking:** CHANGELOG.md provides high-level project milestone history
- ✅ **Collaboration:** Version numbers provide clear reference points for discussions
- ✅ **Maintenance:** Unified versioning reduces overhead compared to per-doc versioning
- ✅ **Maturity Signal:** v0.x.x clearly indicates pre-release development status

### Drawbacks

- All core docs must be updated together (even for single-file changes)
- Version number updates add commit overhead
- CHANGELOG.md requires manual curation
- Risk of version number getting out of sync if forgotten

---

## Options Considered

### Option A: Per-Document Versioning

**Pros:**
- Each document evolves independently
- Only update version for changed document

**Cons:**
- Complex synchronization tracking
- Difficult to know which documents match
- No project-level milestone tracking

**Selected:** NO
**Rationale:** Synchronization complexity outweighs independence benefits

### Option B: Date-Only Tracking

**Pros:**
- Simple to implement
- No version number maintenance

**Cons:**
- No semantic meaning (what changed?)
- Difficult to track milestones
- No rollback reference points

**Selected:** NO
**Rationale:** Lacks semantic versioning benefits

### Option C: No Versioning

**Pros:**
- Minimal overhead
- Git commits provide tracking

**Cons:**
- Difficult to detect out-of-sync docs
- No clear milestone references
- Poor collaboration experience

**Selected:** NO
**Rationale:** Insufficient for multi-document project

### Option D: Unified Semantic Versioning (Selected)

**Pros:**
- Single version number for entire project
- Out-of-sync docs immediately visible
- Clear milestone tracking
- Git tag integration
- Pre-release format signaling

**Cons:**
- All docs updated together
- Version bump overhead

**Selected:** YES
**Rationale:** Best balance of visibility and maintainability

---

## Related Decisions

### Related
- Session summaries remain date-tracked (not versioned) - they're historical records
- Archived documentation (docs/archive/) frozen at their final version

---

## Implementation Notes

### Update Workflow

When ANY core document is updated:
1. Make content changes
2. Bump version number across ALL Tier 1 core docs
3. Update "Last Updated" date across all docs
4. Update CHANGELOG.md (for major milestones only)
5. Commit changes with descriptive message
6. Create git tag (for major/minor bumps)

Example commit message:
```
[Docs] v0.2.0 - Phase 1b Complete (Dual-Device Support)

- Added dual-device peer discovery documentation
- Updated BLE service architecture
- Documented battery-based role assignment
- Added session summaries for Phase 1b milestones

Bumped version: v0.1.0 → v0.2.0
```

### Git Tag Creation

```bash
git tag -a v0.2.0 -m "v0.2.0 - Phase 1b Complete (Dual-Device Support)"
git push origin v0.2.0
```

### CHANGELOG.md Format

```markdown
## [v0.2.0] - 2025-11-19

### Added
- Dual-device peer discovery (Phase 1b)
- Battery-based role assignment (Phase 1c)
- Time synchronization protocol (Phase 2)

### Changed
- BLE service architecture (Configuration + Bilateral services)

### Session Summaries
- SESSION_SUMMARY_PHASE_1B.md
- SESSION_SUMMARY_PHASE_1C.md
```

### Build Environment

- **Version Control:** Git
- **Tag Format:** `vMAJOR.MINOR.PATCH` (e.g., `v0.1.0`, `v0.2.0`, `v1.0.0`)
- **CHANGELOG Location:** `CHANGELOG.md` (project root)

### Testing & Verification

**Verification Steps:**
1. All Tier 1 docs have matching version numbers
2. Git tag exists for current version
3. CHANGELOG.md entry exists for major versions
4. "Last Updated" dates are recent

**Known Limitations:**
- Relies on manual version number updates (no automation)
- CHANGELOG.md curation is manual process
- Version mismatches possible if updates forgotten

---

## Integration Notes

### When to Bump Version

**Minor (v0.x.Y):**
- Documentation clarifications
- Typo fixes
- Content additions without feature changes
- Test-specific guide updates

**Major (v0.X.0):**
- New features (BLE, dual-device)
- Architecture changes (modular refactoring)
- Requirement updates (new therapeutic modes)
- Phase completions (1b, 1c, 2, etc.)

**Production (v1.0.0):**
- Feature-complete device
- Hardware testing complete
- Regulatory documentation complete
- Production-ready firmware

### Migration from Pre-Versioning Docs

Existing documents updated to v0.1.0 baseline:
- Reflects Phase 4 completion (JPL-compliant single-device)
- BLE GATT production-ready
- Modular architecture foundation

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD034 (lines 3352-3426)
Git commit: TBD (migration commit)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
