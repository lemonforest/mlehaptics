# ⚠️ CRITICAL: ESP-IDF Build System Constraint

## TL;DR

**PlatformIO's `build_src_filter` DOES NOT WORK with ESP-IDF!**

ESP-IDF uses CMake - it ignores PlatformIO's build filters.

## Correct Approach

✅ **Use Python pre-build script**: `scripts/select_source.py`
✅ **Script modifies**: `src/CMakeLists.txt` before each build
✅ **Already configured**: Just add new tests to source_map

❌ **NEVER use**: `build_src_filter` in platformio.ini with ESP-IDF
❌ **Will silently fail**: No error, but doesn't work

## Adding New Tests

1. Create test file: `test/my_test.c`
2. Edit `scripts/select_source.py`:
   ```python
   source_map = {
       ...
       "my_test": "../test/my_test.c",
   }
   ```
3. Edit `platformio.ini`:
   ```ini
   [env:my_test]
   extends = env:xiao_esp32c6
   build_flags = ${env:xiao_esp32c6.build_flags} -DHARDWARE_TEST=1
   # NO build_src_filter!
   ```
4. Build: `pio run -e my_test`

## Full Documentation

See: **`docs/ESP_IDF_BUILD_CONSTRAINTS.md`**

---

**Remember**: `framework = espidf` means CMake is in control, not PlatformIO!
