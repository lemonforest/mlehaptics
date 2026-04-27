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
target_link_libraries(spectral PRIVATE cs_core miniz)

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
    src/cs_temporal.c
    src/cs_frame.c
    src/cs_gzip.c
)
target_link_libraries(cs_test PRIVATE cs_core miniz)
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
target_link_libraries(spectral_4d PRIVATE cs_core_4d miniz)

add_custom_target(codegen_4d
    COMMAND ${CMAKE_COMMAND} -E echo "Running 4D codegen scripts..."
    COMMAND python ${CMAKE_SOURCE_DIR}/codegen/emit_tables_4d.py
    COMMAND python ${CMAKE_SOURCE_DIR}/codegen/emit_test_vectors_4d.py
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Regenerate 4D C tables and reference test vectors from Python"
)

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
endif()
