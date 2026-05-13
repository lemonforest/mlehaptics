/*
 * srmech_meta.c — version + ABI accessors for the runtime ctypes shim.
 *
 * The Python `srmech.amsc._native` loader calls `srmech_abi_version()`
 * at load time and compares against EXPECTED_ABI_VERSION. A mismatch
 * causes HAS_NATIVE to stay False; the Python fallback path runs
 * unchanged.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

const char *srmech_version(void)
{
    return SRMECH_VERSION;
}

int srmech_abi_version(void)
{
    /* v1 — Phase B3 baseline: srmech_sha256_hex.
     *
     * Bump in lockstep with the C side whenever the wire format of
     * any exported function changes. Adding a new symbol does NOT
     * bump ABI (the Python shim's _bind() simply doesn't reference
     * symbols it doesn't know about). Changing signatures DOES.
     */
    return 1;
}
