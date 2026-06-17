/*
 * srmech_meta.c — version + ABI accessors for the runtime ctypes shim.
 *
 * The Python `srmech.amsc._native` loader calls `srmech_abi_version()`
 * at load time and compares against EXPECTED_ABI_VERSION. A mismatch
 * causes HAS_NATIVE to stay False; the Python fallback path runs
 * unchanged.
 *
 * License: MIT.
 */

#include "srmech.h"

const char *srmech_version(void)
{
    return SRMECH_VERSION;
}

int srmech_abi_version(void)
{
    /* Returns SRMECH_ABI_VERSION (declared in srmech.h). Indirected
     * through this function so the Python ctypes shim can verify
     * ABI agreement at runtime without compile-time symbol-binding
     * to the macro value.
     */
    return SRMECH_ABI_VERSION;
}
