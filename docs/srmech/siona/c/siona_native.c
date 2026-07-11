/* siona_native.c — Siona's native plugin (the [profile.native] tier). See
 * siona_native.h. JPL Power-of-Ten clean; caller-owned memory only. */
#include "siona_native.h"

#include <assert.h>

/* FNV-1a 64-bit constants (Fowler-Noll-Vo; public-domain algorithm). */
#define SIONA_FNV64_OFFSET_BASIS 14695981039346656037ULL
#define SIONA_FNV64_PRIME        1099511628211ULL

/* Trivial accessor (JPL Rule 5 exempt class: no branches, no memory). */
int siona_native_abi_version(void)
{
    return SIONA_NATIVE_ABI_VERSION;
}

uint64_t siona_native_fnv1a64(const unsigned char *data, size_t len)
{
    assert(data != NULL);              /* contract: non-null buffer */
    assert(len <= SIONA_NATIVE_MAX_INPUT);  /* JPL Rule 2: bounded input */

    uint64_t hash = SIONA_FNV64_OFFSET_BASIS;
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint64_t)data[i];
        hash *= SIONA_FNV64_PRIME;     /* wraps mod 2^64 by C unsigned rules */
    }
    return hash;
}
