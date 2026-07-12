cmake_minimum_required(VERSION 3.20)
project(srmech C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Mirrors docs/antikythera-maths/ephemerides-spectral/CMakeLists.txt.
# Same flags, same scikit-build-core install pattern, same JPL Rule 10
# pedantic-build option. The two C trees in this monorepo share one
# build mental model.
#
# srmech is C11-clean; -std=c17 works under gcc ≥ 8 / clang ≥ 7, but
# we pin C11 here for the broadest cross-compiler support. See
# c/README.md for the local Makefile flow.

if(MSVC OR (CMAKE_C_COMPILER_ID STREQUAL "Clang" AND CMAKE_C_SIMULATE_ID STREQUAL "MSVC"))
    add_compile_options(/W4 /O2)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -O2)
endif()

# ─────────────────────────────────────────────────────────────────
# JPL Power-of-Ten Rule 10 — pedantic-build option (planned: B6).
#
# When SRMECH_PEDANTIC=ON, elevate Wall/Wextra/Wpedantic (gcc/clang)
# or /W4 (MSVC) to ERRORS so any new warning fails the build. Off by
# default so casual local builds stay friendly; the CI matrix at
# .github/workflows/srmech-ci.yml turns it on once Phase B6 is live.
# ─────────────────────────────────────────────────────────────────
option(SRMECH_PEDANTIC "Treat compiler warnings as errors (JPL Rule 10)" OFF)
if(SRMECH_PEDANTIC)
    if(MSVC OR (CMAKE_C_COMPILER_ID STREQUAL "Clang" AND CMAKE_C_SIMULATE_ID STREQUAL "MSVC"))
        add_compile_options(/WX)
    else()
        add_compile_options(-Werror)
    endif()
    message(STATUS "SRMECH_PEDANTIC=ON — compiler warnings will fail the build")
endif()

# libm: GNU/Linux requires explicit -lm to link math runtime symbols.
# MSVC links it implicitly; macOS Clang resolves it via libSystem
# (linking -lm there is a harmless no-op).
if(UNIX)
    set(SRMECH_MATH_LIB m)
else()
    set(SRMECH_MATH_LIB "")
endif()

# ─────────────────────────────────────────────────────────────────
# Shared library
#
# What gets shipped in the Python wheel under srmech/_native/ and
# called via ctypes from srmech.amsc._native (planned, Phase B3+).
#
# Phase B1: file(GLOB ... c/src/*.c) returns the empty list because
# src/ contains only .gitkeep. CMake refuses to add a library with
# zero sources, so we add a placeholder TU (c/include/srmech.h
# compiled as C via a trivial wrapper) only when SRCS is empty.
# Phase B3 onward populates src/ and the placeholder branch is no
# longer taken.
# ─────────────────────────────────────────────────────────────────

file(GLOB SRMECH_SRCS CONFIGURE_DEPENDS c/src/*.c)

if(SRMECH_SRCS)
    add_library(srmech SHARED ${SRMECH_SRCS})
    target_include_directories(srmech PUBLIC c/include)
    target_link_libraries(srmech PRIVATE ${SRMECH_MATH_LIB})

    if(WIN32)
        # Drop the "lib" prefix so the file is `srmech.dll`,
        # matching what the ctypes wrapper looks for. POSIX gets
        # `libsrmech.{so,dylib}` from CMake defaults.
        set_target_properties(srmech PROPERTIES PREFIX "")
    endif()

    # POSIX: PIC so ctypes can load the .so from any process.
    # Windows: WINDOWS_EXPORT_ALL_SYMBOLS so the export list is
    # generated automatically (no __declspec(dllexport) needed in
    # the header). Default symbol visibility — see the visibility
    # note in ephemerides-spectral's CMakeLists.txt for the chess-
    # spectral 1.7.0 M2.1 trap (hidden visibility broke ctypes
    # dlsym, silently flipped HAS_NATIVE to False).
    set_target_properties(srmech PROPERTIES
        POSITION_INDEPENDENT_CODE ON
        WINDOWS_EXPORT_ALL_SYMBOLS ON
    )

    # scikit-build-core wheel install. SKBUILD is defined when
    # building under `pip install .` / `python -m build`; the
    # shared library goes into srmech/_native/.
    if(DEFINED SKBUILD)
        install(TARGETS srmech
                RUNTIME DESTINATION srmech/_native
                LIBRARY DESTINATION srmech/_native
                ARCHIVE DESTINATION srmech/_native)
    endif()

    # ─────────────────────────────────────────────────────────────────
    # Standalone C-HOST smoke (0.9.0rc8, F868) — compiled in the pedantic
    # CI matrix so the Q61 stay-rational transcendental surface is proven
    # to BUILD for a C-ONLY host (no Python) on Linux gcc / macOS clang /
    # Windows MSVC under -Werror / /WX. It reassembles all 9 transcendentals
    # from the six srmech_*_q61 peers + the SRMECH_Q61_* constants and checks
    # them against libm. Run it for the value check (62 asserts):
    #   ./build/test_srmech_trans_q61          (exit 0 = all pass)
    # Guarded by SRMECH_PEDANTIC so it joins the warnings-as-errors gate but
    # is never built into the shipped wheel. (The other c/test/*.c smokes
    # keep their dev-time/WSL2 run convention.)
    # ─────────────────────────────────────────────────────────────────
    if(SRMECH_PEDANTIC)
        add_executable(test_srmech_trans_q61 c/test/test_srmech_trans_q61.c)
        target_link_libraries(test_srmech_trans_q61 PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc44 CRT-GF-RREF rung 1: the swell-free GF(p) RREF + prime-successor
        # smoke. Joins the warnings-as-errors gate (Release/NDEBUG strips assert,
        # so an assert-only param would warn -Werror=unused-parameter). Run it:
        #   ./build/test_srmech_modular_linalg     (exit 0 = all pass)
        add_executable(test_srmech_modular_linalg c/test/test_srmech_modular_linalg.c)
        target_link_libraries(test_srmech_modular_linalg PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc45 CRT closers rung 2: crt_combine + rational_reconstruct over
        # srmech_bigint. Cross-checked against an independent CRT oracle + a
        # reconstruction round-trip (incl. >2**64 moduli). Run it:
        #   ./build/test_srmech_crt_reconstruct    (exit 0 = all pass)
        add_executable(test_srmech_crt_reconstruct c/test/test_srmech_crt_reconstruct.c)
        target_link_libraries(test_srmech_crt_reconstruct PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc48 CRT-QMat CLOSER: srmech_qmat_rref_crt -- the single-symbol C
        # orchestration of the whole bounded-memory exact-Q CRT solve (gf_rref +
        # crt_combine + rational_reconstruct + the descending prime walk). Proves a
        # C-only host gets the exact-Q RREF (incl. a >2**64 bigint answer, the
        # fractional floor-residue path, and the first-prime-unlucky restart). Run:
        #   ./build/test_srmech_qmat_crt           (exit 0 = all pass)
        add_executable(test_srmech_qmat_crt c/test/test_srmech_qmat_crt.c)
        target_link_libraries(test_srmech_qmat_crt PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc141 Foundation F0 (carriers-C): the bare-C-HOST carrier smoke.
        # Proves a C host with no Python builds + holds + manipulates a
        # srmech_mat_t/srmech_vec_t (ctor/get-set/row-col/elementwise/scalar/
        # conj/transpose) + feeds the buffer to srmech_dense_matmul_complex
        # ZERO-COPY. Joins the warnings-as-errors gate (Release/NDEBUG strips
        # assert). Run it:
        #   ./build/test_srmech_carrier            (exit 0 = all pass)
        add_executable(test_srmech_carrier c/test/test_srmech_carrier.c)
        target_link_libraries(test_srmech_carrier PRIVATE srmech ${SRMECH_MATH_LIB})
    endif()
else()
    # Phase B1 only: no .c files yet. Emit a status line so the
    # build log makes the scaffold state obvious.
    message(STATUS "srmech: no C sources in c/src/ yet (Phase B1 scaffolding); skipping library target")
endif()
