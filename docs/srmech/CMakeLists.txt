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
        # /w44062 enables C4062 (enumerator not handled in a switch with no
        # `default:`) at level 4 — it is OFF BY DEFAULT even at /W4, so without
        # this the Windows leg would not enforce the A1 dispatch's
        # switch-exhaustiveness drift gate that gcc/clang get from -Wswitch
        # (inside -Wall). MEASURED 2026-08-23 (MSVC 2022, /std:c11): a deleted
        # `case` in cr_exec_cyc compiled SILENTLY CLEAN under /W4 alone, warned
        # C4062 under /W4 /w44062, and failed under /W4 /w44062 /WX; the full
        # 138-TU src sweep is clean under the new flags (zero C4062).
        add_compile_options(/WX /w44062)
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
        # ─────────────────────────────────────────────────────────────
        # rc356 (`#T953`) — the C tests are now RUN, not just compiled.
        #
        # Before this line existed there was no enable_testing(), no
        # add_test() and no ctest step in any workflow, so **0 of the 30
        # c/test/*.c binaries were executed by any automation, local or
        # CI.** The nine below were built by the pedantic matrix and the
        # binaries thrown away. That is the guard-that-never-fires shape,
        # and it did what that shape always does: rc307 reinterpreted the
        # fiedler `ws_len` unit (DOUBLES -> BYTES, ABI 9 -> 10) and left
        # test_srmech_progress_tick.c behind on the old convention. It
        # returned SRMECH_ERR_BAD_INPUT instead of SRMECH_CANCELLED for
        # ~48 rcs, and nothing noticed, because compiling a test proves
        # only that it compiles. ADR-0003 says the C host stands alone;
        # that claim was not verifiable by automation in its entirety.
        #
        # The `make test` target (c/Makefile) is the OTHER half of this
        # fix and covers all 30 on POSIX. This block deliberately carries
        # only the tests already proven to build on the 3-OS matrix (plus
        # genome, see below) — see tests/test_c_test_wiring_rc356.py, the
        # down-only ratchet that drains the remainder.
        # ─────────────────────────────────────────────────────────────
        enable_testing()

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

        # rc242 progress / introspection callback (#840): the bare-C-HOST smoke.
        # Proves a C host with no Python registers a srmech_progress_cb_t and
        # OBSERVES which op the invoke spine dispatched (Class-H), asserting the
        # exact canonical-JSON event. Runtime if-guards (not assert), so it is a
        # real value check even under Release/NDEBUG, and joins the -Werror/-WX
        # gate. Run it:
        #   ./build/test_srmech_progress           (exit 0 = all pass)
        add_executable(test_srmech_progress c/test/test_srmech_progress.c)
        target_link_libraries(test_srmech_progress PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc256 bignum carrier smoke: set_i64/from_dec/to_dec round-trips,
        # add/sub/mul/divmod (Python FLOOR), divmod_small (the rc256 single-limb
        # divisor peer), shl/shr, isqrt, gcd (Lehmer + lean-Euclid byte-identity),
        # pow. Joins the -Werror/-WX gate (was previously an un-wired dev smoke).
        # Run it for the value check: ./build/test_srmech_bigint (exit 0 = all pass)
        add_executable(test_srmech_bigint c/test/test_srmech_bigint.c)
        target_link_libraries(test_srmech_bigint PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc275 §101 ENCODE-PROGRESS + graceful-abort: the bare-C-HOST smoke for the
        # srmech_progress_tick_cb_t per-iteration heartbeat + nonzero-return-to-CANCEL.
        # Cancels fiedler_file_iterate at iter 3 (asserts SRMECH_CANCELLED + zeroed
        # out_vec) and srmech_genome_mint at kernel 1 (asserts the valid byte-prefix
        # partial), + a NULL-tick == plain-symbol check. Runtime if-guards (not
        # assert), so it is a real value check under Release/NDEBUG and joins the
        # -Werror/-WX gate. Run it:
        #   ./build/test_srmech_progress_tick      (exit 0 = all pass)
        add_executable(test_srmech_progress_tick c/test/test_srmech_progress_tick.c)
        target_link_libraries(test_srmech_progress_tick PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc293 (#928) fold_marks: the bare-C-HOST smoke for combining-mark
        # folding. This op is the first text op whose table a host COULD have
        # derived from Python (unicodedata exposes category + decomposition,
        # unlike the UAX #29 properties rc287 needed), so the reason it is
        # vendored rests entirely on the bare-C host being real — which this
        # links and exercises: default table -> fold, across Latin
        # precomposed/decomposed, the Devanagari virama, Hangul, CJK, emoji,
        # plus OVERFLOW + malformed-UTF-8 rejection. Runtime if-guards (not
        # assert), so it is a real value check under Release/NDEBUG and joins
        # the -Werror/-WX gate. Run it:
        #   ./build/test_srmech_text_fold        (exit 0 = all pass)
        add_executable(test_srmech_text_fold c/test/test_srmech_text_fold.c)
        target_include_directories(test_srmech_text_fold PRIVATE c/src)
        target_link_libraries(test_srmech_text_fold PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc356 (`#T953`): §41 genome persistence — the test the finding was
        # filed against. It was buildable all along (0 warnings, 231 assertions
        # green), but could not join this matrix because its ensure_dir() was a
        # NO-OP under _WIN32 ("the parity harness runs on Linux"), so every save
        # would have failed on windows-latest. rc356 gives it a real _mkdir and
        # drops the shell-out entirely, which is what makes this line safe.
        add_executable(test_srmech_genome c/test/test_srmech_genome.c)
        target_link_libraries(test_srmech_genome PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc391 (`#T907` slice 1): the srmech_toml_parse_arena_bytes sizer +
        # a parse round-trip smoke. Public-API only (srmech.h), so it links the
        # shipped lib like the others and needs no c/src include. Joins the
        # -Werror/-WX gate AND the ctest run so the new C symbol is exercised on
        # all three OSes. Run it: ./build/test_srmech_toml_arena (exit 0 = pass)
        add_executable(test_srmech_toml_arena c/test/test_srmech_toml_arena.c)
        target_link_libraries(test_srmech_toml_arena PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc397 (`#T1066`): the correctly-rounded, libm-free srmech_toml
        # decimal->double parse (Clinger fast path + srmech_bigint exact tail).
        # Compares the parser's SRMECH_TOML_FLOAT value BIT-FOR-BIT against the
        # host compiler's own double literals (correctly rounded), plus the
        # denormal / overflow->inf / underflow->0 boundaries built from bit
        # patterns. Public-API only (srmech.h), joins the -Werror/-WX gate AND
        # the ctest run so the fix is proven on all three OSes. Run it:
        #   ./build/test_srmech_toml_float        (exit 0 = all pass)
        add_executable(test_srmech_toml_float c/test/test_srmech_toml_float.c)
        target_link_libraries(test_srmech_toml_float PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc441 (`#T1148`): Class B's READER half. Through rc440 srmech_tlv_pack
        # shipped with NO reader anywhere in C — a round-trip wire format with
        # one of its two halves projected — while the compiled tool registry told
        # users tlv_unpack was "the ONLY correct way to read these frames back".
        # This gate is the bare-C proof that a host can now walk back a frame it
        # wrote: round trip, the next_offset walk over a 3-frame concatenation,
        # big-endian length recovery, every truncation, and the UINT32_MAX
        # length that WRAPS a 32-bit end bound into an out-of-bounds span.
        # Public-API only (srmech.h), so it joins the -Werror//WX gate AND the
        # ctest run and the wrap row is proven on all three OSes — MSVC included,
        # which is where a 32-bit bound bug would be most tempting to write.
        # Wired on arrival rather than added to the rc356 unwired residual: that
        # ratchet is DOWN-ONLY and a new test must not raise it. Run it:
        #   ./build/test_srmech_tlv_unpack_rc441   (exit 0 = all pass)
        add_executable(test_srmech_tlv_unpack_rc441 c/test/test_srmech_tlv_unpack_rc441.c)
        target_link_libraries(test_srmech_tlv_unpack_rc441 PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc442 (`#T1150`): the §GROUP/v20 nesting grammar, from BARE C. ADR-0003
        # says the C host stands alone, and a nesting grammar is exactly the kind
        # of surface where that claim is easy to assert and easy to leave untested
        # — the Python differential proves the two projections AGREE, which is a
        # different statement from "the C surface is usable with no oracle to
        # compare against". This exercises wrap-then-walk, the validate-only
        # (out == NULL) shape, arity 1 legal / arity 0 refused, all four malformed
        # classes including R4's unrepresentable crossing, the depth cap returning
        # SRMECH_ERR_LIMIT rather than SRMECH_ERR_OVERFLOW, an ungrouped strand
        # reporting zero groups, and emit-on-POP ordering under nesting.
        # Public-API only (srmech.h), so it joins the -Werror//WX gate AND the
        # ctest run on all three OSes. Wired on arrival: the rc356 unwired
        # residual is DOWN-ONLY and a new test must not raise it. Run it:
        #   ./build/test_srmech_genome_group_rc442   (exit 0 = all pass)
        add_executable(test_srmech_genome_group_rc442 c/test/test_srmech_genome_group_rc442.c)
        target_link_libraries(test_srmech_genome_group_rc442 PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc402 (`#T1068`): the srmech_json number-scanner + integer-range
        # correctness gate. Before rc402 an out-of-int64 integer returned
        # SRMECH_OK with the value CLAMPED to INT64_MAX (strtoll's ERANGE was
        # never read), a malformed literal like `--1` or `1e` returned
        # SRMECH_OK with an invented value, and a NUL-bearing object key came
        # back silently TRUNCATED. All three now DECLINE with a status the
        # caller can see. This test fails 20 of its 45 assertions against the
        # pre-rc402 parser, so it is a real instrument rather than a
        # rubber-stamp. Public-API only (srmech.h), joins the -Werror/-WX gate
        # AND the ctest run so the fix is proven on all three OSes. Run it:
        #   ./build/test_srmech_json_number_rc402   (exit 0 = all pass)
        add_executable(test_srmech_json_number_rc402
                       c/test/test_srmech_json_number_rc402.c)
        target_link_libraries(test_srmech_json_number_rc402
                              PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc403 (`#T1071`): the Ryu-class shortest-round-trip double->decimal
        # writer. TWO halves, because a bare-C host has no CPython to ask.
        # Half (A) PROVES shortest-round-trip: emit the decimal, parse it back
        # with srmech's own libm-free correctly-rounded decimal->double (rc397,
        # via srmech_toml_parse), require bit-identity, then require that
        # NEITHER one-digit-shorter neighbour round-trips. Half (B) pins the
        # SPELLING against CPython repr(float) literals — which is also the
        # platform-independence gate, since %.17g of 1e17 is "1e+017" on Windows
        # and "1e+17" on Linux, and this runs on all three OSes.
        #
        # It is a real instrument, not a rubber stamp: run against the
        # PRE-rc403 library it exits 1 with 109 failures (87042 values checked),
        # while 3,000,000 uniformly random bit patterns found ZERO — the defect
        # lived in the zero-mantissa class, which random sampling never hits.
        # Public-API only (srmech.h). ~0.95 s. Run it:
        #   ./build/test_srmech_ryu_repr_rc403     (exit 0 = all pass)
        add_executable(test_srmech_ryu_repr_rc403
                       c/test/test_srmech_ryu_repr_rc403.c)
        target_link_libraries(test_srmech_ryu_repr_rc403
                              PRIVATE srmech ${SRMECH_MATH_LIB})

        # rc404 (`#T1069`): the SRMECH_ERR_OVERFLOW / SRMECH_ERR_LIMIT
        # discriminator. Asserts that a caller can tell "grow your arena and
        # retry" from "this bound is structural, retrying is futile" — which
        # through rc403 it could not, because both returned status 4.
        #
        # A real instrument, measured against both libraries: rc403 exits 1
        # with 5 of 12 rows failing (the five NOT_RETRYABLE rows whose sites
        # rc404 moves); rc404 exits 0. The negative-control rows return
        # BAD_INPUT in BOTH builds, so the gate is not "everything returns
        # OVERFLOW", and the valid-document rows pass in both, so it is not
        # "everything is broken". Adding the enum constant alone does NOT
        # satisfy it — only re-statusing the sites does.
        # Public-API only (srmech.h). ~0 s. Run it:
        #   ./build/test_srmech_status_discrimination_rc404   (exit 0 = pass)
        add_executable(test_srmech_status_discrimination_rc404
                       c/test/test_srmech_status_discrimination_rc404.c)
        target_link_libraries(test_srmech_status_discrimination_rc404
                              PRIVATE srmech ${SRMECH_MATH_LIB})

        # gh #1653 rc447 — the ADR-0003 BARE-C HOST PROOF for config-driven
        # cascade execution. Every OTHER gate for that reaches the library
        # through ctypes, which proves the library computes but NOT that a host
        # without Python can drive a cascade from a descriptor. It found two
        # things ctypes could not: an out-of-int64 literal declines at the
        # parser (so the bigint carrier needs the decimal-STRING transport), and
        # the arena is dominated by 4096 * chain_len (a 3-step chain wants
        # ~2.6 MiB). Wired here rather than raising CEIL_UNWIRED_C_TESTS,
        # because an unwired C test is one nobody runs.
        # Public-API only (srmech.h). ~0 s. Run it:
        #   ./build/test_srmech_chain_run   (exit 0 = pass, 17 checks)
        add_executable(test_srmech_chain_run
                       c/test/test_srmech_chain_run.c)
        target_link_libraries(test_srmech_chain_run
                              PRIVATE srmech ${SRMECH_MATH_LIB})

        # THE RUN STEP. Every executable above is registered with ctest, so
        # `ctest --output-on-failure` in .github/workflows/srmech-ci.yml
        # actually executes them on all three OSes. Whole set = 551 ms wall on
        # WSL2, so there is no runtime argument against running them.
        foreach(t
            test_srmech_trans_q61 test_srmech_modular_linalg
            test_srmech_crt_reconstruct test_srmech_qmat_crt test_srmech_carrier
            test_srmech_progress test_srmech_bigint test_srmech_progress_tick
            test_srmech_text_fold test_srmech_genome test_srmech_toml_arena
            test_srmech_toml_float test_srmech_json_number_rc402
            test_srmech_ryu_repr_rc403
            test_srmech_status_discrimination_rc404
            test_srmech_tlv_unpack_rc441
            test_srmech_genome_group_rc442
            test_srmech_chain_run)
            add_test(NAME ${t} COMMAND ${t})
        endforeach()

        # ─────────────────────────────────────────────────────────────
        # rc452 (`#T1166`) — THE REMAINING 20. The block above carried
        # only the tests "already proven to build on the 3-OS matrix",
        # and the down-only CEIL_UNWIRED_C_TESTS ratchet was supposed to
        # drain the rest. Measured at the rc452 branch point: 38 test
        # files exist, 18 were registered, and the other 20 ran in NO
        # automation at all. `c/Makefile`'s `make test` runs all 38 on
        # POSIX (38/38 pass on WSL2, measured this session) but NO
        # WORKFLOW INVOKES make — so "covered by the Makefile" was
        # coverage nobody executed, which is the rc356 shape one level up:
        # rc356 fixed "compiled but not run", and this fixes "runnable but
        # not reached".
        #
        # These are registered as a LIST rather than 20 hand-written
        # stanzas so that adding a test file is a one-line change, and
        # tests/test_ctest_collection_parity_rc452.py asserts STRICT
        # two-way equality between the registered set and the
        # c/test/test_srmech_*.c census — so a future file cannot land
        # unregistered and a registration cannot outlive its file. That
        # closes the rc356 shape STRUCTURALLY instead of once.
        #
        # ⚠️ These 20 have only ever been executed on WSL2. The macOS
        # clang and Windows MSVC cells are UNMEASURED for them as of this
        # commit. A cell that reds is a finding to FIX, not to
        # deregister — deregistering would restore exactly the state this
        # block removes.
        # ─────────────────────────────────────────────────────────────
        set(SRMECH_C_TESTS_RC452
            test_srmech_bigexp test_srmech_config test_srmech_coupling
            test_srmech_factor_poly test_srmech_fiedler
            test_srmech_fiedler_file test_srmech_gosper test_srmech_hdc
            test_srmech_json test_srmech_ndjson test_srmech_parallel
            test_srmech_poly test_srmech_q_wz_verify test_srmech_qi
            test_srmech_qmat test_srmech_recursive_cut test_srmech_sha256
            test_srmech_toml test_srmech_wz test_srmech_zeilberger)
        foreach(t ${SRMECH_C_TESTS_RC452})
            add_executable(${t} c/test/${t}.c)
            target_link_libraries(${t} PRIVATE srmech ${SRMECH_MATH_LIB})
            add_test(NAME ${t} COMMAND ${t})
        endforeach()

        # test_srmech_config.c includes the INTERNAL header srmech_platform.h,
        # which lives in c/src rather than the public c/include. Same treatment
        # as test_srmech_text_fold above (line ~214), and the same rationale
        # c/Makefile:81 already records for its own `-I$(SRCDIR)`. Found by
        # registering it: the file had never been compiled by CMake, so the
        # missing include path had nowhere to surface. Exactly the class the
        # 3-OS matrix is being pointed at these 20 to find.
        target_include_directories(test_srmech_config PRIVATE c/src)
    endif()
else()
    # Phase B1 only: no .c files yet. Emit a status line so the
    # build log makes the scaffold state obvious.
    message(STATUS "srmech: no C sources in c/src/ yet (Phase B1 scaffolding); skipping library target")
endif()
