/* siona_native.h — Siona's OWN native plugin surface (the [profile.native] tier).
 *
 * Siona is a srmech PROFILE. srmech's profile_loader loads THIS library as
 * `srmech.profile("siona").native` (a bound ctypes lib) after an ABI handshake:
 * it calls siona_native_abi_version() and checks it against the profile
 * descriptor's expected_abi_version. Once validated, siona's Python dispatches
 * its validated hot-path ops here (the has_native pattern), falling back to the
 * pure-Python reference when the lib is absent.
 *
 * rc1 native surface:
 *   - siona_native_abi_version   : the ABI handshake symbol.
 *   - siona_native_fnv1a64       : FNV-1a-64 content hash (bytes -> u64).
 *   - siona_native_tokenize      : byte-scan word-boundary finder (the tokenize scan).
 *   - siona_native_cooccurrence_accumulate : windowed token co-occurrence into a
 *                                  caller-arena open-addressing hash (the encode's
 *                                  tokens->edges hot loop — the actual bottleneck).
 *
 * JPL Power-of-Ten clean (mirrors srmech's C discipline): no goto, no malloc,
 * <=60-line functions, >=2 asserts per non-exempt function, no multi-line macros,
 * caller-owned memory only (the co-occurrence arena is caller-allocated).
 */
#ifndef SIONA_NATIVE_H
#define SIONA_NATIVE_H

#include <stddef.h>
#include <stdint.h>

/* Plugin ABI version. Bump in lockstep with expected_abi_version in
 * siona/srmech_profile.toml [profile.native] whenever an EXISTING exported
 * symbol's wire format changes. Adding a new symbol does NOT bump it. */
#define SIONA_NATIVE_ABI_VERSION 1

/* Defensive upper bound on a single input buffer (JPL Rule 2: bounded).
 * 2^31 - 1 bytes; token offsets fit in int32. */
#define SIONA_NATIVE_MAX_INPUT ((size_t)0x7fffffffUL)

/* Empty-slot marker for the co-occurrence arena. A valid packed key is
 * (i<<32)|j with i<j < 2^31, so it is always < this sentinel. */
#define SIONA_NATIVE_ARENA_EMPTY ((uint64_t)0xffffffffffffffffULL)

/* The ABI handshake symbol the loader calls (argtypes=[], restype=c_int). */
int siona_native_abi_version(void);

/* FNV-1a 64-bit hash of `len` bytes at `data`. Deterministic; matches the
 * pure-Python reference in siona/_native.py bit-for-bit. */
uint64_t siona_native_fnv1a64(const unsigned char *data, size_t len);

/* Word-boundary scan. A token = a maximal run of "word bytes": ASCII
 * [A-Za-z0-9] or any byte >= 0x80 (so UTF-8 multibyte chars stay intact).
 * Writes (start, length) int32 pairs into `out` (2 int32 per token). Returns
 * the token count, or -1 if it would exceed `max_tokens`. Casefolding is the
 * caller's job (it slices `data` at these spans). */
long siona_native_tokenize(const unsigned char *data, size_t len,
                           int32_t *out, size_t max_tokens);

/* Windowed co-occurrence accumulator (the encode's tokens->edges hot loop).
 * For each document (doc k spans [prev_end, doc_ends[k])), and each position a,
 * pair token_ids[a] with token_ids[a+1 .. a+window] (window resets per doc),
 * and bump the unordered edge (min,max) — skipping self-pairs. Accumulates into
 * a caller-allocated open-addressing hash arena (keys prefilled to
 * SIONA_NATIVE_ARENA_EMPTY, arena_cap a power of two). Returns the number of
 * DISTINCT edges written (>=0), or -1 if the arena filled (caller grows + retries
 * or falls back to pure-Python). Key packing: (uint64)min << 32 | max. */
long siona_native_cooccurrence_accumulate(const int32_t *token_ids,
                                          size_t n_tokens,
                                          const int32_t *doc_ends, size_t n_docs,
                                          int window, uint64_t *arena_keys,
                                          uint32_t *arena_vals, size_t arena_cap);

/* Compact a filled arena into dense parallel output arrays (the readback done
 * IN C so Python never scans the sparse arena). Walks the arena once, writing
 * each non-empty edge as (out_i[k]=min, out_j[k]=max, out_w[k]=count). Returns
 * the number written (== the accumulate return), or -1 if it exceeds max_out. */
long siona_native_arena_compact(const uint64_t *arena_keys,
                                const uint32_t *arena_vals, size_t arena_cap,
                                int32_t *out_i, int32_t *out_j, uint32_t *out_w,
                                size_t max_out);

#endif /* SIONA_NATIVE_H */
