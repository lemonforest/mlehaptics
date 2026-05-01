cmake_minimum_required(VERSION 3.20)
project(chess_spectral C)
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

if(MSVC OR (CMAKE_C_COMPILER_ID STREQUAL "Clang" AND CMAKE_C_SIMULATE_ID STREQUAL "MSVC"))
    add_compile_options(/W4 /O2)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
else()
    add_compile_options(-Wall -Wextra -O2)
endif()

# libm: GNU/Linux requires explicit -lm to link sqrt/fabs/etc. MSVC links
# the math runtime implicitly; macOS Clang resolves libm via libSystem
# (linking -lm there is a harmless no-op). We expose a single
# CS_MATH_LIB variable and link it from each executable that uses
# <math.h>.
if(UNIX)
    set(CS_MATH_LIB m)
else()
    set(CS_MATH_LIB "")
endif()

# Vendored miniz (public domain, RFC 1950/1951). Only the low-level
# deflate/inflate streaming APIs are needed — ZIP archive support
# (miniz_zip.c) is intentionally excluded.
add_library(miniz STATIC
    vendor/miniz/miniz.c
    vendor/miniz/miniz_tdef.c
    vendor/miniz/miniz_tinfl.c
)
target_include_directories(miniz PUBLIC vendor/miniz)
target_compile_definitions(miniz PUBLIC MINIZ_NO_ARCHIVE_APIS)
if(MSVC OR (CMAKE_C_COMPILER_ID STREQUAL "Clang" AND CMAKE_C_SIMULATE_ID STREQUAL "MSVC"))
    # Third-party code: don't fail our /W4 warnings on it.
    target_compile_options(miniz PRIVATE /W0)
endif()

add_library(cs_core STATIC
    src/cs_signal.c
    src/cs_d4.c
    src/cs_fiber.c
    src/cs_encoder.c
    src/cs_tables_data.c
)
target_include_directories(cs_core PUBLIC include)

add_executable(spectral
    src/main.c
    src/cs_fen.c
    src/cs_frame.c
    src/cs_gzip.c
    src/cs_temporal.c
)
target_link_libraries(spectral PRIVATE cs_core miniz ${CS_MATH_LIB})

# Bake the absolute path of the PGN bridge into the binary so `spectral`
# can auto-invoke it without the user wiring up PATH / env vars. Can be
# overridden at runtime with the CS_PGN_BRIDGE environment variable.
target_compile_definitions(spectral PRIVATE
    CS_BRIDGE_SCRIPT_PATH="${CMAKE_SOURCE_DIR}/bridge/pgn_bridge.py"
)

add_executable(cs_test
    test/test_main.c
    test/test_encoder.c
    test/test_channels_extra.c
    test/test_d4.c
    test/test_temporal.c
    test/test_gzip.c
    test/test_frame_v5.c
    src/cs_temporal.c
    src/cs_frame.c
    src/cs_frame_v5.c
    src/cs_gzip.c
)
target_link_libraries(cs_test PRIVATE cs_core miniz ${CS_MATH_LIB})
target_include_directories(cs_test PRIVATE test)

enable_testing()
add_test(NAME spectral_tests COMMAND cs_test)

add_custom_target(codegen
    COMMAND ${CMAKE_COMMAND} -E echo "Running codegen scripts..."
    COMMAND python ${CMAKE_SOURCE_DIR}/codegen/emit_tables.py
    COMMAND python ${CMAKE_SOURCE_DIR}/codegen/emit_test_vectors.py
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Regenerate C tables and reference test vectors from Python"
)

# ─── 4D encoder (v1.1 port) ─────────────────────────────────────────────────
# Separate static lib + binary; zero shared TUs with the 2D paths.
# All 11 channels are real (verified by python/tests/test_c_py_parity_4d.py
# at TOL=1e-10). cs_fen_4d.c (v1.2.4) parses the FEN4 v1 placement literal
# documented in docs/FEN4_FORMAT.md.
add_library(cs_core_4d STATIC
    src/cs_signal_4d.c
    src/cs_a1_4d.c
    src/cs_std4_4d.c
    src/cs_diag_4d.c
    src/cs_pawn_anti_4d.c
    src/cs_fiber_sym_4d.c
    src/cs_encoder_4d.c
    src/cs_fen_4d.c
    src/cs_frame_4d.c
    src/cs_tables_data_4d.c
)
target_include_directories(cs_core_4d PUBLIC include)

add_executable(spectral_4d
    src/main_4d.c
    src/cs_gzip.c
)
target_link_libraries(spectral_4d PRIVATE cs_core_4d miniz ${CS_MATH_LIB})

add_custom_target(codegen_4d
    COMMAND ${CMAKE_COMMAND} -E echo "Running 4D codegen scripts..."
    COMMAND python ${CMAKE_SOURCE_DIR}/codegen/emit_tables_4d.py
    COMMAND python ${CMAKE_SOURCE_DIR}/codegen/emit_test_vectors_4d.py
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Regenerate 4D C tables and reference test vectors from Python"
)

# ─── 1.7.0 D2 M2.1 — native fast-path for spatial_4d.Bitboard4D ────────────
# Shared library (not an executable) compiled from src/cs_bitboard4d.c.
# Loaded at import time by chess_spectral._native_bitboard4d via ctypes.
# Pure-Python Bitboard4D continues to work as fallback when this .so/.dll
# isn't present (sdist install without C toolchain, Pyodide WASM-less
# install, etc.).
add_library(cs_bitboard4d SHARED src/cs_bitboard4d.c)
target_include_directories(cs_bitboard4d PUBLIC include)
# Hide internal symbols on POSIX so only the cs_bb4_* API is exported.
if(NOT MSVC)
    set_target_properties(cs_bitboard4d PROPERTIES
        C_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN ON
    )
endif()
# Force the standard `lib` prefix off on Windows (DLL convention) so
# the file is `cs_bitboard4d.dll`, matching what the ctypes wrapper
# looks for. POSIX gets the conventional `libcs_bitboard4d.so` /
# `libcs_bitboard4d.dylib` from CMake defaults.
if(WIN32)
    set_target_properties(cs_bitboard4d PROPERTIES PREFIX "")
endif()
# MSVC + Windows SDK 10.0.26100 dialect mismatch: every /std:c* mode
# the MSVC C frontend supports (c11, c17, clatest) chokes on
# function-like macro expansion in the SDK's <malloc.h> SAL annotations
# AND the compiler's own <immintrin.h> SIMD intrinsic prototypes —
# both transitively pulled in by <stdint.h> / <intrin.h>. Errors look
# like `'_Ptr': undeclared identifier`, `'_Memory': undeclared
# identifier`, `'__x': undeclared identifier` (the macro parameters
# leak when the strict-C frontend decides the macro body is malformed).
#
# The C++ frontend handles these headers cleanly because it has full
# C++23 conformance and a more capable preprocessor. The cs_bb4_*
# source is plain bit-twiddling — no C99-only syntax, no compound
# literals, no designated initializers — so compiling it as C++ on
# MSVC is a one-line workaround. The header already wraps its API in
# `extern "C"`, so callers don't see any difference.
#
# Linux / macOS / Pyodide still build cs_bitboard4d as C (gcc / clang
# compile the strict-C17 source unchanged).
if(MSVC)
    set_source_files_properties(src/cs_bitboard4d.c PROPERTIES LANGUAGE CXX)
endif()

# ─── scikit-build-core wheel install ────────────────────────────────────────
# When building under scikit-build-core (i.e. `pip install .` or
# `python -m build`), SKBUILD is defined and we install spectral +
# spectral_4d binaries inside the wheel under chess_spectral/_native/.
# The Python `_find_native_binary` helper (cli.py) checks that path
# before falling back to repo-build paths.
if(DEFINED SKBUILD)
    install(TARGETS spectral spectral_4d
            RUNTIME DESTINATION chess_spectral/_native
            COMPONENT chess_spectral_native)
    # 1.7.0 D2 M2.1 — also ship the bitboard shared library.
    # RUNTIME for Windows DLLs, LIBRARY for POSIX .so/.dylib.
    install(TARGETS cs_bitboard4d
            RUNTIME DESTINATION chess_spectral/_native
            LIBRARY DESTINATION chess_spectral/_native
            COMPONENT chess_spectral_native)
endif()
