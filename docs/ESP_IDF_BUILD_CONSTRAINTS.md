# ESP-IDF Build System - Critical Constraints

## ⚠️ NEVER USE `build_src_filter` WITH ESP-IDF ⚠️

**PlatformIO's `build_src_filter` DOES NOT WORK with ESP-IDF framework!**

### Why It Doesn't Work

```
PlatformIO Build Flow with ESP-IDF:
1. PlatformIO reads platformio.ini
2. PlatformIO calls ESP-IDF's CMake system
3. CMake reads src/CMakeLists.txt directly
4. CMake compiles the files listed in CMakeLists.txt
5. build_src_filter is COMPLETELY IGNORED (CMake doesn't see it)
```

**Key Facts:**
- ESP-IDF framework uses CMake for all compilation
- `framework = espidf` in platformio.ini means CMake is in control
- CMake reads `src/CMakeLists.txt` for source file list
- PlatformIO's `build_src_filter` only works with PlatformIO's native build system
- When CMake is active, PlatformIO build filters have **NO EFFECT**

### Correct Approach: Python Pre-Build Script

**File: `scripts/select_source.py`**

```python
# This script runs BEFORE CMake configuration
# It modifies src/CMakeLists.txt to select the correct source file

Import("env")
import os

# Map environment name to source file
source_map = {
    "xiao_esp32c6": "main.c",
    "hbridge_test": "../test/hbridge_test.c",
    "ulp_hbridge_test": "../test/ulp_hbridge_test.c",
}

# Get current build environment
build_env = env["PIOENV"]
source_file = source_map.get(build_env, "main.c")

# Modify src/CMakeLists.txt
cmake_path = os.path.join(env["PROJECT_DIR"], "src", "CMakeLists.txt")
# ... modify SRCS line in CMakeLists.txt ...
```

**File: `platformio.ini`**

```ini
[env:xiao_esp32c6]
framework = espidf
extra_scripts = pre:scripts/select_source.py  # Runs BEFORE CMake

; ❌ WRONG - This does nothing with ESP-IDF:
; build_src_filter = +<*> -<test/>

; ✅ CORRECT - Python script handles source selection
```

**File: `src/CMakeLists.txt`**

```cmake
# This file is MODIFIED by select_source.py before each build
idf_component_register(
    SRCS "main.c"  # or "../test/hbridge_test.c" etc.
    INCLUDE_DIRS "."
    REQUIRES freertos esp_system driver nvs_flash bt
)
```

## Adding New Test Environments

**Step-by-step checklist:**

1. ✅ Create test file: `test/my_new_test.c`

2. ✅ Add to Python script: `scripts/select_source.py`
   ```python
   source_map = {
       ...
       "my_new_test": "../test/my_new_test.c",
   }
   ```

3. ✅ Add environment: `platformio.ini`
   ```ini
   [env:my_new_test]
   extends = env:xiao_esp32c6
   build_flags = 
       ${env:xiao_esp32c6.build_flags}
       -DHARDWARE_TEST=1
   ```

4. ❌ DO NOT add `build_src_filter` - it doesn't work with ESP-IDF!

5. ✅ Test build: `pio run -e my_new_test`
   - Python script runs first
   - Modifies src/CMakeLists.txt
   - CMake reads modified file
   - Correct source file is compiled

## Common Mistakes

### ❌ Mistake #1: Using build_src_filter
```ini
[env:my_test]
framework = espidf
build_src_filter = +<test/> -<main.c>  # SILENTLY IGNORED!
```

**Why it fails:** CMake doesn't read build_src_filter

### ❌ Mistake #2: Manual CMakeLists.txt Editing
```cmake
# Manually editing this before each build
idf_component_register(
    SRCS "main.c"  # Change to test file manually
```

**Why it fails:** Breaks automation, error-prone, not scalable

### ❌ Mistake #3: Conditional Compilation in main.c
```c
#ifdef HARDWARE_TEST
    #include "../test/hbridge_test.c"
#endif
```

**Why it fails:** Clutters main.c, hard to maintain, violates separation

### ✅ Correct: Python Pre-Build Script
```python
# Automated, reliable, scalable
source_file = source_map.get(build_env, "main.c")
# Modify CMakeLists.txt automatically
```

## ULP-Specific Considerations

**ULP source files are handled differently:**

**File: `ulp/CMakeLists.txt`**
```cmake
# ULP has its own CMakeLists.txt
set(ulp_sources "ulp_motor_control.c")
ulp_embed_binary(ulp_motor_control ${ulp_sources} "ulp_riscv")
```

**How it works:**
1. Main source file selected by `scripts/select_source.py`
2. ULP source compiled by `ulp/CMakeLists.txt`
3. ULP binary embedded in main firmware automatically
4. **NO build_src_filter needed or used**

## Verification

**Check that source selection worked:**

```bash
# Build the project
pio run -e hbridge_test

# Check console output for:
# [BUILD] Configured CMakeLists.txt for hbridge_test: ../test/hbridge_test.c

# Verify CMakeLists.txt was modified:
cat src/CMakeLists.txt
# Should show: SRCS "../test/hbridge_test.c"
```

## References

- **Architecture Decision**: `docs/architecture_decisions.md` → AD022
- **Build Commands**: `BUILD_COMMANDS.md` → "Adding New Test Environments"
- **Implementation**: `scripts/select_source.py`
- **ESP-IDF CMake Docs**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-guides/build-system.html

## Quick Reference Table

| Feature | Arduino Framework | ESP-IDF Framework |
|---------|------------------|-------------------|
| Build System | PlatformIO native | **CMake** |
| Source Selection | `build_src_filter` ✅ | `build_src_filter` ❌ |
| Correct Method | `build_src_filter` | **Python script** |
| Config File | platformio.ini | **CMakeLists.txt** |

---

**Remember:** When `framework = espidf`, CMake is in control!

**Always use:** Python pre-build scripts to modify CMakeLists.txt

**Never use:** build_src_filter with ESP-IDF (it's silently ignored)
