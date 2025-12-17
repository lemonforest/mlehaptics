# AI Orchestration Prompt Template
## For Creating Hardware Test Documentation and Build Guide Entries

Use this prompt template when starting a new chat to create documentation for hardware tests, build guides, or project planning documents.

---

## 📋 Standard Prompt Template

```
I need help documenting a new hardware test for my EMDR Pulser project. Please review the project structure and create consistent documentation following our established patterns.

**Project Context:**
- Location: MCP local drive access at \AI_PROJECTS\EMDR_PULSER_SONNET4
- Framework: ESP-IDF v5.5.0 with PlatformIO
- Board: Seeed Xiao ESP32C6
- Build System: ESP-IDF CMake with Python source selection (see AD022 in docs/architecture_decisions.md)

**Key Documentation Files to Review:**
1. docs/ai_context.md - Complete project DNA and API contracts
2. docs/architecture_decisions.md - Technical architecture (especially AD022 for build system)
3. test/README.md - Hardware test documentation patterns
4. BUILD_COMMANDS.md - Build command quick reference
5. platformio.ini - Build environment configurations
6. scripts/select_source.py - Source file selection script

**What I Need:**
[Describe your specific need here, for example:]
- Create a new hardware test for [feature]
- Document an existing test that was manually created
- Add a new build environment
- Update planning documents for [feature]

**Expected Deliverables:**
1. Test source code (if creating new test): test/[test_name].c
2. Updated scripts/select_source.py (add source mapping)
3. Updated platformio.ini (add environment section)
4. Updated test/README.md (comprehensive test documentation)
5. Updated BUILD_COMMANDS.md (quick reference entry)
6. Quick reference guide: test/[TEST_NAME]_GUIDE.md
7. If planning: Updated docs/ai_context.md or architecture_decisions.md

**Documentation Standards to Follow:**
- ✅ JPL Coding Standard compliance (no busy-wait loops, use vTaskDelay())
- ✅ Comprehensive Doxygen documentation for all functions
- ✅ Clear GPIO pin definitions and behavior
- ✅ Expected behavior with checkboxes
- ✅ Troubleshooting section with common issues
- ✅ Console output examples
- ✅ Integration notes for main program
- ✅ Build commands for all platforms (Linux/Mac/Windows)

**Build System Requirements (AD022):**
- ESP-IDF uses CMake (not PlatformIO's build_src_filter)
- Source files must be added to scripts/select_source.py
- Each test environment extends env:xiao_esp32c6
- All tests set -DHARDWARE_TEST=1 flag
- Follow existing patterns in platformio.ini

Please review the existing documentation patterns and create consistent entries for all required files.
```

---

## 🎯 Specific Use Case Prompts

### For New Hardware Test Creation

```
I need to create a hardware test for [FEATURE_NAME] on the Seeed Xiao ESP32C6 for my EMDR Pulser project.

**Project Location:** \AI_PROJECTS\EMDR_PULSER_SONNET4

**Test Requirements:**
- GPIO pins: [list pins and functions]
- Test behavior: [describe expected behavior]
- Hardware needed: [list components]
- Success criteria: [list checkboxes]

**Review These Files First:**
- docs/ai_context.md (project DNA and GPIO assignments)
- docs/architecture_decisions.md (especially AD022 build system)
- test/README.md (existing test patterns)
- test/button_deepsleep_test.c (reference implementation)

**Create:**
1. test/[test_name].c with comprehensive documentation
2. Update scripts/select_source.py
3. Update platformio.ini environment
4. Update test/README.md with full section
5. Update BUILD_COMMANDS.md with commands
6. Create test/[TEST_NAME]_GUIDE.md quick reference

**Follow Patterns From:**
- test/button_deepsleep_test.c (comprehensive example)
- test/hbridge_pwm_test.c (PWM implementation)
- test/ledc_blink_test.c (minimal test example)

All code must be JPL compliant with vTaskDelay() for timing (no busy-wait loops).
```

### For Updating Architecture Decisions

```
I need to document a new architecture decision for my EMDR Pulser project.

**Project Location:** \AI_PROJECTS\EMDR_PULSER_SONNET4

**Review First:**
- docs/architecture_decisions.md (see existing AD format)
- docs/ai_context.md (project context)

**New Decision:**
- **Title:** [Decision name]
- **Problem:** [What problem are we solving?]
- **Solution:** [Chosen approach]
- **Alternatives Considered:** [What else was evaluated?]
- **Rationale:** [Why this solution?]
- **Technical Details:** [Implementation specifics]

**Format to Follow:**
### AD0XX: [Decision Title]

**Decision**: [One-line summary]

**Problem Statement:** [Detailed problem description]

**Solution Strategy:** [Chosen approach with subsections]

**Alternatives Considered:**
1. **Option 1**: ❌ Rejected because...
2. **Option 2**: ❌ Rejected because...

**Rationale:**
- Technical reason 1
- Technical reason 2

**Implementation Requirements:**
- Requirement 1
- Requirement 2

**Benefits:**
✅ Benefit 1
✅ Benefit 2

**Verification:**
- How to verify this decision works

Create the new AD entry in docs/architecture_decisions.md following this format.
```

### For Build System Updates

```
I need to add/update a build environment for my EMDR Pulser project.

**Project Location:** \AI_PROJECTS\EMDR_PULSER_SONNET4

**Critical:** Read AD022 in docs/architecture_decisions.md first!
ESP-IDF uses CMake - PlatformIO's build_src_filter DOES NOT WORK.

**Environment Details:**
- Environment name: [name]
- Source file: [path]
- Purpose: [description]
- Special flags: [any custom flags]

**Update Required Files:**
1. scripts/select_source.py (add source mapping)
2. platformio.ini (add environment section)
3. BUILD_COMMANDS.md (add to Hardware Test Environments table)
4. test/README.md (if hardware test)

**Follow Pattern From:**
- [env:button_deepsleep_test] in platformio.ini
- Existing entries in scripts/select_source.py
- Existing sections in BUILD_COMMANDS.md

Ensure all documentation is updated consistently.
```

---

## 📚 Documentation Checklist

When documenting any new feature or test, ensure all these files are updated:

### Core Documentation
- [ ] test/[test_name].c - Source code with Doxygen comments
- [ ] test/README.md - Comprehensive test documentation section
- [ ] test/[TEST_NAME]_GUIDE.md - Quick reference guide
- [ ] BUILD_COMMANDS.md - Quick command reference

### Build System (AD022)
- [ ] scripts/select_source.py - Source file mapping
- [ ] platformio.ini - Build environment configuration

### Optional (as needed)
- [ ] docs/ai_context.md - Update API contracts if new APIs added
- [ ] docs/architecture_decisions.md - New AD if architectural change
- [ ] docs/ESP_IDF_SOURCE_SELECTION.md - Build system changes

### Cross-Platform Commands
- [ ] Linux/Mac bash/zsh aliases
- [ ] Windows PowerShell functions  
- [ ] Windows Command Prompt batch files

---

## 🎨 Documentation Style Guide

### File Headers
```c
/**
 * @file [filename].c
 * @brief [One-line description]
 * 
 * Purpose: [Detailed purpose explanation]
 * 
 * Test behavior:
 *   - [Behavior point 1]
 *   - [Behavior point 2]
 * 
 * GPIO Configuration:
 *   - GPIO[X]: [Function] ([details])
 *   - GPIO[Y]: [Function] ([details])
 * 
 * Build: pio run -e [env_name] -t upload && pio device monitor
 * 
 * Seeed Xiao ESP32C6: ESP-IDF v5.5.0
 * Generated with assistance from Claude Sonnet 4 (Anthropic)
 */
```

### Function Documentation
```c
/**
 * @brief [Brief description]
 * @param [param_name] [Parameter description]
 * @return [Return value description]
 * 
 * [Detailed explanation of function behavior]
 * 
 * [Implementation notes if needed]
 * 
 * [JPL compliance notes if relevant]
 */
```

### README Sections
```markdown
### N. Test Name (`test_file.c`)

**Purpose:** [One-line purpose]

**Test Sequence:**
- Step 1 → Expected result
- Step 2 → Expected result

**GPIO Configuration:**
- GPIO[X]: [Function] - [Details]

**Hardware Requirements:**
- [Required components]

**Build & Run:**
```bash
[Build command]
```

**Expected Behavior:**
- ✅ [Success criterion 1]
- ✅ [Success criterion 2]

**What to Check:**
- [ ] [Checklist item 1]
- [ ] [Checklist item 2]

**Troubleshooting:**
- **[Issue]:** [Solution]

**Why This Test?**
[Explanation of what this test validates]
```

### BUILD_COMMANDS.md Entries
```markdown
| `environment_name` | Brief description | `pio run -e environment_name -t upload && pio device monitor` |
```

---

## 🔧 Technical Requirements

### JPL Coding Standard Compliance
- ✅ No dynamic memory allocation (malloc/free)
- ✅ No recursion
- ✅ All timing uses vTaskDelay() (no busy-wait loops)
- ✅ Comprehensive error checking (esp_err_t return values)
- ✅ Cyclomatic complexity ≤ 10
- ✅ All variables explicitly initialized
- ✅ Single entry/exit points

### ESP-IDF v5.5.0 APIs
- Use `gpio_config()` for GPIO initialization
- Use `vTaskDelay()` for all timing (never esp_rom_delay_us())
- Use `ESP_LOGI/LOGD/LOGE` for logging
- Use `esp_timer_get_time()` for high-resolution timing
- Return `esp_err_t` from all functions

### Build System (AD022)
- ESP-IDF uses CMake (not PlatformIO build filters)
- Source files selected via Python script
- All tests extend `env:xiao_esp32c6`
- Hardware tests set `-DHARDWARE_TEST=1`

---

## 📦 Example: Complete Documentation Set

For reference, see the button_deepsleep_test documentation:
- Source: `test/button_deepsleep_test.c`
- README: `test/README.md` (section 4)
- Guide: `test/BUTTON_DEEPSLEEP_TEST_GUIDE.md`
- Build: `BUILD_COMMANDS.md` (Hardware Test Environments table)
- Config: `platformio.ini` ([env:button_deepsleep_test])
- Script: `scripts/select_source.py` (source mapping entry)

This provides a complete pattern to follow for future tests.

---

## 🚀 Quick Start for AI Assistants

When starting a new chat with this prompt:

1. **Read project context** from `docs/ai_context.md`
2. **Review build system** from `docs/architecture_decisions.md` (AD022)
3. **Check existing patterns** from `test/README.md`
4. **Follow format** from reference test (e.g., button_deepsleep_test)
5. **Update all files** in the documentation checklist
6. **Maintain consistency** with existing style and structure
7. **Test commands** work on all platforms (Linux/Mac/Windows)

---

**Last Updated:** 2025-10-20
**Template Version:** 1.0
**Project:** EMDR Bilateral Stimulation Device (ESP32-C6)
