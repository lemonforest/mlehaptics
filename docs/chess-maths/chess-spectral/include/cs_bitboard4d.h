/* cs_bitboard4d.h — native fast-path for spatial_4d.Bitboard4D primitives.
 *
 * 4096-bit bitset over the Z_8^4 lattice (4D chess). Mirrors the
 * pure-Python ``chess_spectral.spatial_4d.Bitboard4D`` API for the
 * subset of operations that benefit most from native code:
 *
 *   - popcount (sum of set bits)
 *   - bitwise AND / OR / XOR / NOT / set-difference (vectorized)
 *   - per-square set / clear / toggle / test
 *   - empty / full predicate, equality
 *
 * Storage: ``uint64_t[CS_BB4_N_WORDS]`` (CS_BB4_N_WORDS = 64; 64*64=4096
 * bits). Same layout as ``Bitboard4D.to_numpy_uint64()`` so Python
 * callers can pass a ``np.uint64[64]`` array directly.
 *
 * Bit ordering: square index ``s`` lives at ``bits[s / 64] >> (s % 64)``.
 * Squares 0..63 in word 0, 64..127 in word 1, etc. Matches the
 * existing ``int.to_bytes`` / numpy projection convention in
 * ``Bitboard4D.to_numpy_uint64``.
 *
 * Fallback discipline (chess-spectral 1.7.0 D2 spec):
 *   The Python wrapper checks ``_HAS_NATIVE_BITBOARD`` at import; if
 *   the .so/.dll isn't shipped (sdist-only install, Pyodide without
 *   WASM compile, etc.), the pure-Python ``Bitboard4D`` continues to
 *   work unchanged. This header + cs_bitboard4d.c provide the fast
 *   path WHEN AVAILABLE — they don't replace the Python primitive.
 */

#ifndef CS_BITBOARD4D_H
#define CS_BITBOARD4D_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Number of uint64 words per Bitboard4D. 64 * 64 = 4096 bits. */
#define CS_BB4_N_WORDS 64
#define CS_BB4_N_SQUARES 4096

/* Population count: total set bits across all 64 words. */
int cs_bb4_popcount(const uint64_t *bits);

/* Bitwise ops: out = a OP b (or out = OP a for unary).
 * Caller owns ``out``; aliasing with ``a`` or ``b`` is safe. */
void cs_bb4_and(uint64_t *out, const uint64_t *a, const uint64_t *b);
void cs_bb4_or(uint64_t *out, const uint64_t *a, const uint64_t *b);
void cs_bb4_xor(uint64_t *out, const uint64_t *a, const uint64_t *b);
void cs_bb4_not(uint64_t *out, const uint64_t *a);
void cs_bb4_sub(uint64_t *out, const uint64_t *a, const uint64_t *b);

/* Per-square ops. ``sq`` must be in [0, 4096). Returns nonzero on
 * out-of-range; caller validates upstream. */
void cs_bb4_set_square(uint64_t *bits, int sq);
void cs_bb4_clear_square(uint64_t *bits, int sq);
void cs_bb4_toggle_square(uint64_t *bits, int sq);
int cs_bb4_test_square(const uint64_t *bits, int sq);

/* Predicates: 1 if true, 0 if false. */
int cs_bb4_is_empty(const uint64_t *bits);
int cs_bb4_is_full(const uint64_t *bits);
int cs_bb4_equals(const uint64_t *a, const uint64_t *b);
int cs_bb4_intersects(const uint64_t *a, const uint64_t *b);

/* Iteration: fill ``out_squares[]`` with the indices of set bits, in
 * ascending order. Returns the number of indices written (==
 * cs_bb4_popcount(bits)).
 *
 * The caller MUST ensure ``out_squares`` has room for at least
 * CS_BB4_N_SQUARES (=4096) ints — the worst case is a fully-set
 * bitboard. Practical bitboards are usually sparse (popcount under
 * a few dozen), but the safe-allocation discipline matches numpy's
 * convention for output buffers.
 *
 * This is the load-bearing speedup over pure Python's
 * ``Bitboard4D.squares()`` generator: per-bit LSB extraction in C
 * (``__builtin_ctzll`` / ``_BitScanForward64`` / SWAR fallback)
 * + ``b &= b - 1`` clear, all without crossing the ctypes boundary
 * per square. One ctypes call per bitboard amortizes the marshaling
 * overhead. */
int cs_bb4_to_squares(int *out_squares, const uint64_t *bits);

/* Version stamp for the native ABI. The Python wrapper checks this
 * matches its expected version before dispatching ops; on mismatch
 * the fallback path is used. Bump on incompatible changes.
 *
 * Version history:
 *   1: initial primitives (popcount, bitwise, predicates).
 *   2: added cs_bb4_to_squares for native iteration (1.7.0 M2.2). */
int cs_bb4_abi_version(void);
#define CS_BB4_ABI_VERSION 2

#ifdef __cplusplus
}  /* extern "C" */
#endif

#endif  /* CS_BITBOARD4D_H */
