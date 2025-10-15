# EMDR Bilateral Stimulation Device
# CMakeLists.txt for ESP-IDF v5.x with PlatformIO structure
#
# This file is required by ESP-IDF build system
# Configured for PlatformIO's src/ directory instead of ESP-IDF's main/
#
# Generated with assistance from Claude Sonnet 4 (Anthropic)

cmake_minimum_required(VERSION 3.16)

# Tell ESP-IDF where to find components (PlatformIO uses 'src' not 'main')
set(EXTRA_COMPONENT_DIRS src)

# Include ESP-IDF CMake build system
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# Define the project
project(emdr_bilateral_device)
