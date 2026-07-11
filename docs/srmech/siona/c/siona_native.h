/* siona_native.h — Siona's OWN native plugin surface (the [profile.native] tier).
 *
 * Siona is a srmech PROFILE. srmech's profile_loader loads THIS library as
 * `srmech.profile("siona").native` (a bound ctypes lib) after an ABI handshake:
 * it calls siona_native_abi_version() and checks it against the profile
 * descriptor's expected_abi_version. Once validated, siona's Python dispatches
 * its validated hot-path ops here (the has_native pattern), falling back to the
 * pure-Python reference when the lib is absent.
 *
 * This is the SCAFFOLD: one real op (FNV-1a-64 content hash — the exact
 * bytes->int shape the tokenize/content-address hot-path needs) proves the whole
 * chain end-to-end (build -> package-data -> loader -> ABI -> symbol -> parity)
 * before the heavy ports (tokenize / cooccurrence accumulator) drop in.
 *
 * JPL Power-of-Ten clean (mirrors srmech's C discipline): no goto, no malloc,
 * <=60-line functions, >=2 asserts per non-exempt function, no multi-line macros,
 * caller-owned memory only.
 */
#ifndef SIONA_NATIVE_H
#define SIONA_NATIVE_H

#include <stddef.h>
#include <stdint.h>

/* Plugin ABI version. Bump in lockstep with expected_abi_version in
 * siona/srmech_profile.toml [profile.native] whenever an EXISTING exported
 * symbol's wire format changes. Adding a new symbol does NOT bump it. */
#define SIONA_NATIVE_ABI_VERSION 1

/* Defensive upper bound on a single hashed buffer (JPL Rule 2: bounded).
 * 2^31 - 1 bytes; any real Siona input is far smaller. */
#define SIONA_NATIVE_MAX_INPUT ((size_t)0x7fffffffUL)

/* The ABI handshake symbol the loader calls (argtypes=[], restype=c_int). */
int siona_native_abi_version(void);

/* FNV-1a 64-bit hash of `len` bytes at `data`. Deterministic, exactly
 * reproducible by the pure-Python reference in siona/_native.py. */
uint64_t siona_native_fnv1a64(const unsigned char *data, size_t len);

#endif /* SIONA_NATIVE_H */
