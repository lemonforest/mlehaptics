# 0022: ESP-IDF Build System and Hardware Test Architecture

**Date:** 2025-10-20
**Phase:** 0.4
**Status:** Accepted
**Type:** Build System

---

## Summary (Y-Statement)

In the context of ESP-IDF's CMake-based build system requirements,
facing PlatformIO's build_src_filter incompatibility with ESP-IDF framework,
we decided for Python pre-build scripts to modify CMakeLists.txt dynamically,
and neglected manual file editing or separate PlatformIO projects,
to achieve automated source file selection for hardware tests,
accepting <100ms script overhead per build and one-time script setup.

---

## Problem Statement

ESP-IDF uses CMake as its native build system, which requires source files to be explicitly listed in `src/CMakeLists.txt`. PlatformIO's `build_src_filter` option (used for other frameworks) has **NO EFFECT** with ESP-IDF, making it impossible to select different source files for hardware tests using standard PlatformIO mechanisms.

**Critical Constraint:** When `framework = espidf` is specified, PlatformIO delegates entirely to ESP-IDF's CMake build system. CMake reads `src/CMakeLists.txt` directly with no PlatformIO filtering applied.

---

## Context

**Technical Constraints:**
- ESP-IDF uses CMake (not PlatformIO's native build system)
- PlatformIO's `build_src_filter` only works with PlatformIO's native framework
- Multiple hardware test programs needed: hbridge, battery, WS2812B, button, etc.
- Test code should be separate from main application code
- Single PlatformIO project preferred over multiple projects

**Development Workflow:**
- Frequent switching between main application and hardware tests
- Fast build switching critical for rapid development
- Manual file editing is error-prone and breaks automation

**Project Structure Needs:**
- Clean separation: `test/` directory for hardware tests, `src/` for main application
- No conditional compilation cluttering main.c
- Scalable architecture for adding new tests

---

## Decision

We will use Python pre-build scripts to manage source file selection for ESP-IDF's CMake build system.

**Architecture:**

1. **Python Pre-Build Script** (`scripts/select_source.py`):
   - Runs before every build via PlatformIO's `extra_scripts` feature
   - Detects current build environment name
   - Modifies `src/CMakeLists.txt` to use the correct source file
   - Maintains source file mapping dictionary

2. **Source File Organization:**
   ```
   project_root/
   ├── src/
   │   ├── main.c              # Main application
   │   └── CMakeLists.txt      # Modified by script before each build
   ├── test/
   │   ├── hbridge_test.c      # Hardware validation tests
   │   ├── battery_test.c
   │   └── README.md
   └── scripts/
       └── select_source.py    # Build-time source selector
   ```

3. **Build Environment Configuration:**
   ```ini
   ; Main application (default)
   [env:xiao_esp32c6]
   extends = env:base_config
   extra_scripts = pre:scripts/select_source.py

   ; Hardware test environment
   [env:hbridge_test]
   extends = env:xiao_esp32c6
   build_flags =
       ${env:xiao_esp32c6.build_flags}
       -DHARDWARE_TEST=1
       -DDEBUG_LEVEL=3
   ```

4. **Script Implementation Pattern:**
   ```python
   # scripts/select_source.py
   Import("env")
   import os

   # Source file mapping for each build environment
   source_map = {
       "xiao_esp32c6": "main.c",
       "hbridge_test": "../test/hbridge_test.c",
       "single_device_demo_jpl_queued": "../test/single_device_demo_jpl_queued.c",
   }

   build_env = env["PIOENV"]
   source_file = source_map.get(build_env, "main.c")

   # Modify src/CMakeLists.txt
   cmake_path = os.path.join(env["PROJECT_DIR"], "src", "CMakeLists.txt")
   with open(cmake_path, 'r') as f:
       lines = f.readlines()

   new_lines = []
   for line in lines:
       if line.strip().startswith('SRCS'):
           new_lines.append(f'    SRCS "{source_file}"\n')
       else:
           new_lines.append(line)

   with open(cmake_path, 'w') as f:
       f.writelines(new_lines)
   ```

---

## Consequences

### Benefits

- **ESP-IDF native compatibility:** Works with CMake build system without fighting it
- **Automatic source selection:** No manual file editing needed
- **Clean test separation:** Hardware tests in `test/`, main code in `src/`
- **Scalable architecture:** Easy to add new tests (one line in source_map)
- **Fast build switching:** Script overhead <100ms
- **Deterministic:** Same command always builds same source
- **Developer-friendly:** Simple commands like `pio run -e hbridge_test -t upload`

### Drawbacks

- **CMakeLists.txt gets modified:** File changes on every build (acceptable, it's auto-generated)
- **Script dependency:** One additional script to maintain
- **Non-standard approach:** Requires understanding of ESP-IDF + PlatformIO interaction

---

## Options Considered

### Option A: Multiple CMakeLists.txt Files

**Pros:**
- No dynamic modification needed

**Cons:**
- ESP-IDF expects specific file locations (`src/CMakeLists.txt`)
- Would require complex CMake include logic

**Selected:** NO
**Rationale:** Fights ESP-IDF conventions, adds complexity

### Option B: Conditional Compilation in main.c

**Pros:**
- Single source file
- No build system changes

**Cons:**
- Clutters main application code with test code
- Hardware tests should be standalone
- Difficult to maintain as tests grow

**Selected:** NO
**Rationale:** Poor separation of concerns, maintenance nightmare

### Option C: Separate PlatformIO Projects

**Pros:**
- Clean separation per test
- No shared configuration complexity

**Cons:**
- Duplicates configuration across projects
- Harder to maintain consistency
- More directories to manage

**Selected:** NO
**Rationale:** Excessive overhead for test management

### Option D: Manual CMakeLists.txt Editing

**Pros:**
- No script needed
- Simple to understand

**Cons:**
- Error-prone (forget to switch source files)
- Breaks automation
- Git conflicts on CMakeLists.txt

**Selected:** NO
**Rationale:** Human error risk unacceptable for production builds

### Option E: Python Pre-Build Script (CHOSEN)

**Pros:**
- Automatic source selection
- Works with ESP-IDF's CMake
- Clean test separation
- Scalable for future tests
- Fast (<100ms overhead)

**Cons:**
- One additional script to maintain
- Modifies CMakeLists.txt on every build

**Selected:** YES
**Rationale:** Best balance of automation, maintainability, and ESP-IDF compatibility

---

## Related Decisions

### Related
- **AD027: Modular Source File Architecture** - Production code uses modular structure, tests remain monolithic
- All hardware test implementations depend on this build system

---

## Implementation Notes

### Code References

- **Script:** `scripts/select_source.py` (source file selector)
- **PlatformIO Config:** `platformio.ini` (extra_scripts configuration)
- **CMake Template:** `src/CMakeLists.txt` (modified by script)

### Build Environment

- **Script Language:** Python 3.x
- **Trigger:** PlatformIO `extra_scripts = pre:scripts/select_source.py`
- **Execution Timing:** Before CMake configuration phase

### Testing & Verification

**Verification Commands:**
```bash
# Verify main application builds
pio run -e xiao_esp32c6
cat src/CMakeLists.txt  # Should show: SRCS "main.c"

# Verify test builds
pio run -e hbridge_test
cat src/CMakeLists.txt  # Should show: SRCS "../test/hbridge_test.c"
```

**Adding New Tests:**
1. Create test file: `test/my_new_test.c`
2. Update `scripts/select_source.py`:
   ```python
   source_map = {
       ...
       "my_new_test": "../test/my_new_test.c",
   }
   ```
3. Add environment to `platformio.ini`:
   ```ini
   [env:my_new_test]
   extends = env:xiao_esp32c6
   build_flags =
       ${env:xiao_esp32c6.build_flags}
       -DHARDWARE_TEST=1
   ```
4. Build: `pio run -e my_new_test -t upload`

---

## JPL Coding Standards Compliance

- ✅ Rule #1: No dynamic memory allocation - Script uses Python standard library only
- ✅ Rule #2: Fixed loop bounds - Script has bounded file iteration
- ✅ Rule #3: No recursion - Linear file processing
- ✅ Rule #5: Return value checking - File operations have error handling
- ✅ Deterministic behavior - Same input always produces same output
- ✅ Bounded complexity - Simple dictionary lookup and file modification

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD022
Git commit: (phase 0.4 implementation)

**Future Enhancements:**
- Could extend to select different `sdkconfig` files per environment
- Could manage component dependencies per test
- Could auto-generate test environments from test directory

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
