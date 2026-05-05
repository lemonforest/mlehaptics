cmake_minimum_required(VERSION 3.20)
project(ephemerides_spectral C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# The C source itself is C11-clean; -std=c17 works under gcc ≥ 8 and
# clang ≥ 7, but we pin C11 here for the broadest cross-compiler
# support (older mingw, embedded toolchains, etc.). Same source, same
# Q-format conversions, same byte-exact parity with the Python BIP
# encoder. See c/README.md for the local Makefile flow.

if(MSVC OR (CMAKE_C_COMPILER_ID STREQUAL "Clang" AND CMAKE_C_SIMULATE_ID STREQUAL "MSVC"))
    add_compile_options(/W4 /O2)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -O2)
endif()

# libm: GNU/Linux requires explicit -lm to link round/fabs/isfinite.
# MSVC links the math runtime implicitly; macOS Clang resolves libm
# via libSystem (linking -lm there is a harmless no-op).
if(UNIX)
    set(ES_MATH_LIB m)
else()
    set(ES_MATH_LIB "")
endif()

# ──────────────────────────────────────────────────────────────────────
# Shared library — what gets shipped in the Python wheel under
# ephemerides_spectral/_native/ and called via ctypes from
# python/ephemerides_spectral/_native_bip.py.
# ──────────────────────────────────────────────────────────────────────

add_library(ephemerides_spectral SHARED
    c/src/es_encode.c
    c/src/es_bodies.c
    c/src/es_laplacian.c
    c/src/es_cosine_lut.c
    c/src/es_patches.c
    c/src/es_parity.c
    c/src/es_prng.c
    c/src/es_channel_bases.c
    c/src/es_hd_state.c
)
target_include_directories(ephemerides_spectral PUBLIC c/include)
target_link_libraries(ephemerides_spectral PRIVATE ${ES_MATH_LIB})

# Windows-specific: drop the "lib" prefix so the file is
# `ephemerides_spectral.dll`, matching what the ctypes wrapper
# looks for. POSIX gets the conventional
# `libephemerides_spectral.{so,dylib}` from CMake defaults.
if(WIN32)
    set_target_properties(ephemerides_spectral PROPERTIES PREFIX "")
endif()

# Position-independent code on POSIX so the shared library can be
# loaded by ctypes from any process. Windows: WINDOWS_EXPORT_ALL_SYMBOLS
# instructs CMake to generate the export list automatically (no
# __declspec(dllexport) decorations needed in the header).
#
# Visibility note: we deliberately do NOT set C_VISIBILITY_PRESET=hidden
# here. With hidden visibility, the entire es_* API would be hidden
# from the linker; ctypes.dlsym() would return NULL at load time
# and HAS_NATIVE would silently stay False (chess-spectral hit this
# exact trap in 1.7.0 M2.1). The only "internal" symbols in our TUs
# are `static inline` helpers (es_floor_div in es_encode.c), which
# are never linker-visible regardless. Default visibility exports
# the es_* API; static-inline helpers stay private without any
# extra annotation.
set_target_properties(ephemerides_spectral PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)

# ──────────────────────────────────────────────────────────────────────
# scikit-build-core wheel install
# ──────────────────────────────────────────────────────────────────────
#
# When building under scikit-build-core (i.e. `pip install .` or
# `python -m build`), SKBUILD is defined and we install the shared
# library into ephemerides_spectral/_native/.

if(DEFINED SKBUILD)
    # RUNTIME for Windows DLLs, LIBRARY for POSIX .so/.dylib.
    install(TARGETS ephemerides_spectral
            RUNTIME DESTINATION ephemerides_spectral/_native
            LIBRARY DESTINATION ephemerides_spectral/_native
            ARCHIVE DESTINATION ephemerides_spectral/_native)
endif()
