"""
PlatformIO Pre-Build Script
Modifies src/CMakeLists.txt to select correct source file based on build environment

This script runs before each build and updates the SRCS line in src/CMakeLists.txt
to compile either the main application or a hardware test.
"""

Import("env")
import os

# Get the current build environment name
build_env = env["PIOENV"]

# Define source file mapping
source_map = {
    "xiao_esp32c6": "main.c",
    "xiao_esp32c6_production": "main.c",
    "xiao_esp32c6_testing": "main.c",
    "hbridge_test": "../test/hbridge_test.c",
    "hbridge_pwm_test": "../test/hbridge_pwm_test.c",
    "ulp_hbridge_test": "../test/ulp_hbridge_test.c",
    "ledc_blink_test": "../test/ledc_blink_test.c",
    # Add future test environments here
}

# Get the source file for this environment
source_file = source_map.get(build_env, "main.c")

# Path to src/CMakeLists.txt
cmake_path = os.path.join(env["PROJECT_DIR"], "src", "CMakeLists.txt")

# Read the current CMakeLists.txt
with open(cmake_path, 'r') as f:
    lines = f.readlines()

# Find and replace the SRCS line
new_lines = []
for line in lines:
    if line.strip().startswith('SRCS'):
        # Replace with the correct source file
        new_lines.append(f'    SRCS "{source_file}"\n')
        print(f"[BUILD] Configured CMakeLists.txt for {build_env}: {source_file}")
    else:
        new_lines.append(line)

# Write back the modified CMakeLists.txt
with open(cmake_path, 'w') as f:
    f.writelines(new_lines)

print(f"[BUILD] Source selection complete")
