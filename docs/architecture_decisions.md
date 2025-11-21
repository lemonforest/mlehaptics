# Architecture Decisions - MIGRATED

⚠️ **This document has been restructured for better AI workflow compatibility.**

**Migration Date:** November 21, 2025
**Reason:** The monolithic 4,354-line document exceeded Claude Code's read tool token limit (25,000 tokens), making it inaccessible to AI agents.

---

## 📂 New Location

**All 40 Architecture Decision Records are now in:** `docs/adr/`

**Access Methods:**

1. **Browse Complete Index:**
   - See [docs/adr/README.md](adr/README.md) for comprehensive table with filters

2. **Individual ADR Files:**
   - Format: `docs/adr/NNNN-kebab-case-title.md`
   - Example: [AD035: Battery-Based Role Assignment](adr/0035-battery-based-initial-role-assignment.md)

3. **Quick Links to Key Decisions:**
   - [AD001: ESP-IDF v5.5.0 Framework](adr/0001-esp-idf-v5-5-0-framework-selection.md)
   - [AD010: Race Condition Prevention](adr/0010-race-condition-prevention-strategy.md)
   - [AD028: Command-and-Control Architecture](adr/0028-command-control-synchronized-fallback.md)
   - [AD030: BLE Bilateral Control Service](adr/0030-ble-bilateral-control-service.md)
   - [AD032: BLE Service UUID Namespace](adr/0032-ble-configuration-service-architecture.md)
   - [AD035: Battery-Based Role Assignment](adr/0035-battery-based-initial-role-assignment.md)
   - [AD038: UUID-Switching Strategy](adr/0038-uuid-switching-strategy.md)
   - [AD039: Time Synchronization Protocol](adr/0039-time-synchronization-protocol.md)
   - [AD040: Firmware Version Checking](adr/0040-firmware-version-checking.md)

---

## 📋 What Changed

### Old Structure (Deprecated)
- **Single file:** 4,354 lines, 186 KB
- **Problem:** Exceeded AI token limits, difficult to navigate
- **Archived:** `docs/archive/architecture_decisions.md`

### New Structure (Current)
- **Individual files:** 40 ADR files in `docs/adr/` directory
- **Format:** MADR 4.0.0 (Markdown Any Decision Records)
- **Index:** `docs/adr/README.md` with filtering by phase, status, type
- **Benefits:**
  - ✅ AI agents can read complete decisions (500-1000 tokens each)
  - ✅ Fast grep/search for specific decisions
  - ✅ Clear template for future decisions
  - ✅ Parallel development (no merge conflicts)
  - ✅ Granular git history per decision

---

## 🔍 Reference Format (Unchanged)

**The "AD0XX" reference format still works:**

```markdown
# In documentation:
See AD030 for details  → Works with both old and new structure

# In code comments:
// Per AD035, battery-based role assignment
// See docs/adr/0035-battery-based-initial-role-assignment.md
```

---

## 📊 Quick Stats

- **Total Decisions:** 40 (AD001-AD040)
- **Accepted:** 30 decisions
- **Implemented:** 3 decisions (AD035, AD038, AD039)
- **Approved:** 4 decisions (awaiting implementation)
- **Superseded:** 3 decisions (AD008, AD026, AD037)

**Supersession Chain:**
- AD008 (BLE Protocol) → Superseded by AD030 + AD032
- AD026 (Automatic Role Recovery) → Superseded by AD028
- AD037 (State-Based Connection ID) → Superseded by AD038

---

## 🔗 Navigation by Phase

- **Phase 0.1 - Foundation:** [AD001-AD009, AD011-AD013, AD015-AD017, AD022]
- **Phase 1b - BLE Infrastructure:** [AD008, AD010, AD026-AD028, AD030, AD032-AD034]
- **Phase 1b.3 - Pairing & Security:** [AD036-AD038]
- **Phase 1c - Role Assignment:** [AD035]
- **Phase 2 - Time Sync & Commands:** [AD028-AD029, AD039-AD040]
- **Phase 3 - Power & Sleep:** [AD014, AD020-AD021, AD023, AD025]
- **Phase 4 - Production:** [AD018-AD019, AD024]

[See complete phase-based navigation in index](adr/README.md#navigation-by-phase)

---

## 📝 Creating New ADRs

**Template:** `docs/adr/_template.md` (MADR 4.0.0 format)

**Process:**
1. Copy template: `cp docs/adr/_template.md docs/adr/NNNN-title.md`
2. Fill in all sections (see template for structure)
3. Update `docs/adr/README.md` index
4. Reference in code: `// See ADNNN: Title`

**MADR 4.0.0 Structure:**
- Summary (Y-Statement)
- Problem Statement, Context, Decision
- Consequences (Benefits & Drawbacks)
- Options Considered (with pros/cons)
- Related Decisions
- Implementation Notes
- JPL Coding Standards Compliance

---

## 🗂️ Original Document

The complete original document is archived at:
- **Location:** `docs/archive/architecture_decisions.md`
- **Purpose:** Historical reference, emergency backup
- **Status:** Frozen (no updates)

---

## ❓ Questions?

- **Template:** See `docs/adr/_template.md`
- **Examples:** Browse any file in `docs/adr/`
- **Index:** See `docs/adr/README.md`
- **MADR Standard:** https://adr.github.io/madr/

---

**Migration completed:** November 21, 2025
**Git Commit:** [to be added]
**Maintained by:** Project team + Claude Code AI
