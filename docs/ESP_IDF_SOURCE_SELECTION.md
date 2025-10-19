# ESP-IDF Source Selection for Hardware Tests

## The Problem

ESP-IDF uses CMake as its build system, which requires source files to be specified in `src/CMakeLists.txt`. PlatformIO's `build_src_filter` option doesn't work with ESP-IDF framework.

## The Solution

We use a PlatformIO `extra_scripts` feature to automatically modify `src/CMakeLists.txt` before each build, selecting the correct source file based on the build environment.

## How It Works

### 1. Python Script (`scripts/select_source.py`)

Before each build, PlatformIO runs this Python script which:
- Detects which environment is being built (e.g., `hbridge_test`)
- Looks up the correct source file for that environment
- Modifies `src/CMakeLists.txt` to use that source file

### 2. Source File Mapping

The script maintains a mapping of environments to source files:

```python
source_map = {
    "xiao_esp32c6": "main.c",                    # Main application
    "xiao_esp32c6_production": "main.c",         # Production build
    "xiao_esp32c6_testing": "main.c",            # Unit testing
    "hbridge_test": "../test/hbridge_test.c",    # H-bridge test
    # Add future tests here
}
```

### 3. CMakeLists.txt Modification

The script modifies this line in `src/CMakeLists.txt`:

**Before build:**
```cmake
SRCS "main.c"
```

**After running script (for hbridge_test):**
```cmake
SRCS "../test/hbridge_test.c"
```

## Adding New Hardware Tests

To add a new hardware test:

### 1. Create Test File
```bash
# Create your test in test/ directory
test/my_new_test.c
```

### 2. Update Python Script
Edit `scripts/select_source.py` and add your test to the `source_map`:

```python
source_map = {
    "xiao_esp32c6": "main.c",
    "xiao_esp32c6_production": "main.c",
    "xiao_esp32c6_testing": "main.c",
    "hbridge_test": "../test/hbridge_test.c",
    "my_new_test": "../test/my_new_test.c",  # <-- Add this line
}
```

### 3. Add Environment to platformio.ini
```ini
[env:my_new_test]
extends = env:xiao_esp32c6

build_flags = 
    ${env:xiao_esp32c6.build_flags}
    -DHARDWARE_TEST=1
    -DDEBUG_LEVEL=3

; Note: Source file selection handled by extra_scripts in base environment
```

### 4. Build Your Test
```bash
pio run -e my_new_test -t upload && pio device monitor
```

## Build Process Flow

```
1. User runs: pio run -e hbridge_test -t upload
2. PlatformIO reads platformio.ini
3. Sees extra_scripts = pre:scripts/select_source.py
4. Runs select_source.py BEFORE building
5. Script modifies src/CMakeLists.txt
6. ESP-IDF CMake reads modified CMakeLists.txt
7. Compiles correct source file
8. Upload to board
```

## Advantages

✅ **ESP-IDF native** - Works with CMake build system  
✅ **Automatic** - No manual file editing needed  
✅ **Clean** - Source files stay separate  
✅ **Scalable** - Easy to add new tests  
✅ **Safe** - Each build uses correct source file  

## Troubleshooting

### Script doesn't run
- Check that `scripts/select_source.py` exists and is executable
- Verify `extra_scripts = pre:scripts/select_source.py` is in platformio.ini

### Wrong source file compiled
- Check console output for `[BUILD] Configured CMakeLists.txt for...`
- Verify your environment name is in the `source_map` dictionary
- Look at `src/CMakeLists.txt` to see which SRCS line is present

### Python errors
- Ensure Python is installed and in PATH
- Check that the script has correct syntax
- Look for detailed error in PlatformIO build output

## Notes

- The script runs on every build (very fast, <100ms)
- `src/CMakeLists.txt` is modified in-place (but not committed to git)
- Each environment gets the correct source file automatically
- No need to manually edit CMakeLists.txt ever again!
