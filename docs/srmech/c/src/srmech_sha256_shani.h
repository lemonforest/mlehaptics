/*
 * srmech_sha256_shani.h — attested target-specific data for the SHA-NI
 * single-stream kernel (the x86 Intel SHA Extensions optimize path).
 *
 * Holds the ONE piece of magic in srmech_sha256_shani.c that is NOT
 * derivable from srmech's own framework and was historically transcribed
 * by hand: the packed per-group round-constant table KP[16][2]. A single
 * wrong hex digit here is invisible on a host without the SHA feature and
 * silently corrupts every digest on a host with it — this is exactly the
 * rc18 defect (KP[14] read 0x8CC70808 where it must be 0x8CC70208). It now
 * lives behind an attestation block + a derive-and-assert test.
 *
 * ────────────────────────────────────────────────────────────────────
 * ATTESTATION (MPR v1) — TWO things are attested here:
 *
 * (1) The KP[16][2] CONSTANTS — the same 64 FIPS 180-4 §4.2.2 round
 *     constants K[0..63] as srmech_sha256_constants.h, re-expressed in the
 *     Intel SHA-NI packing: each row g = (hi64, lo64) feeds
 *     _mm_set_epi64x(hi64, lo64) so its four 32-bit lanes are
 *     [K[4g], K[4g+1], K[4g+2], K[4g+3]].
 *       source_doi   : 10.6028/NIST.FIPS.180-4   (the constants)
 *       packing_src  : Intel® 64 and IA-32 Architectures Software
 *                      Developer's Manual, Vol 2 — SHA256RNDS2 / SHA256MSG1
 *                      / SHA256MSG2 ; Intel® SHA Extensions whitepaper
 *                      (S. Gulley et al., 2013).
 *       verification : COMPUTATIONAL — tests/test_fips_constants_attested.py
 *                      decodes every KP[g] pair to four uint32 lanes and
 *                      asserts they equal the FIPS K[4g..4g+3] re-derived
 *                      from cube-roots-of-primes. Fails on one wrong digit,
 *                      on ANY host. (This is the test that would have caught
 *                      rc18 at unit-test time rather than on SHA-NI CI.)
 *
 * (2) The INSTRUCTION SEQUENCE in srmech_sha256_shani.c (the order of
 *     _mm_sha256rnds2_epu32 / _mm_sha256msg1_epu32 / _mm_sha256msg2_epu32 /
 *     _mm_alignr_epi8 + the ABEF/CDGH state packing) is NOT a derivable
 *     constant — it is an algorithm. Its provenance:
 *       primary      : Intel® SHA Extensions whitepaper + the Intel
 *                      Intrinsics Guide entries for the four intrinsics
 *                      (operational semantics).
 *       impl_pointer : J. Walton, public-domain sha256-x86.c
 *                      (github.com/noloader/SHA-Intrinsics) — read as a
 *                      working-impl reference, NOT pinned by byte-hash (a
 *                      master-branch file drifts; that would be WEAKER
 *                      provenance than the primary spec + the test).
 *       verification : tests/test_sha256_shani.py exercises the kernel on
 *                      SHA-NI-capable CI and asserts bit-exactness with
 *                      hashlib / the scalar oracle (gold-is-law gate).
 *       retrieved_at : 2026-06-03
 *       cite_as      : "Intel SHA Extensions (SHA256RNDS2/MSG1/MSG2),
 *                      Intel SDM Vol 2 + Intel SHA Extensions whitepaper."
 * ────────────────────────────────────────────────────────────────────
 *
 * License: GPL-3.0-or-later.
 */
#ifndef SRMECH_SHA256_SHANI_H
#define SRMECH_SHA256_SHANI_H

#include "srmech_simd.h"   /* SRMECH_SIMD_X86 / SRMECH_SIMD_SHANI_KERNEL */

#include <stdint.h>

#if SRMECH_SIMD_X86 && SRMECH_SIMD_SHANI_KERNEL

/* Packed per-group round constants (hi64, lo64) for _mm_set_epi64x — the
 * 16 literals of the Intel SHA-NI reference. Guarded so a build that does
 * not compile the kernel never carries an unused table. DO NOT hand-edit:
 * the FIPS derivation in tests/test_fips_constants_attested.py is law. */
static const uint64_t SRMECH_SHA256NI_KP[16][2] = {
    { 0xE9B5DBA5B5C0FBCFULL, 0x71374491428A2F98ULL },
    { 0xAB1C5ED5923F82A4ULL, 0x59F111F13956C25BULL },
    { 0x550C7DC3243185BEULL, 0x12835B01D807AA98ULL },
    { 0xC19BF1749BDC06A7ULL, 0x80DEB1FE72BE5D74ULL },
    { 0x240CA1CC0FC19DC6ULL, 0xEFBE4786E49B69C1ULL },
    { 0x76F988DA5CB0A9DCULL, 0x4A7484AA2DE92C6FULL },
    { 0xBF597FC7B00327C8ULL, 0xA831C66D983E5152ULL },
    { 0x1429296706CA6351ULL, 0xD5A79147C6E00BF3ULL },
    { 0x53380D134D2C6DFCULL, 0x2E1B213827B70A85ULL },
    { 0x92722C8581C2C92EULL, 0x766A0ABB650A7354ULL },
    { 0xC76C51A3C24B8B70ULL, 0xA81A664BA2BFE8A1ULL },
    { 0x106AA070F40E3585ULL, 0xD6990624D192E819ULL },
    { 0x34B0BCB52748774CULL, 0x1E376C0819A4C116ULL },
    { 0x682E6FF35B9CCA4FULL, 0x4ED8AA4A391C0CB3ULL },
    { 0x8CC7020884C87814ULL, 0x78A5636F748F82EEULL },
    { 0xC67178F2BEF9A3F7ULL, 0xA4506CEB90BEFFFAULL }
};

#endif /* SRMECH_SIMD_X86 && SRMECH_SIMD_SHANI_KERNEL */

#endif /* SRMECH_SHA256_SHANI_H */
