/*
 * srmech_progress_internal.h — INTERNAL declaration of the progress-emit hook
 * (0.9.0rc242, #840). NOT part of the public ABI: srmech.h exposes only the
 * srmech_progress_cb_t typedef + the srmech_set_progress_cb registration. The
 * central invoke spine (srmech_invoke.c's iv_dispatch) calls
 * srmech_progress_emit_dispatch to fire the registered callback for one
 * dispatched tool. Split out so the emit builder + the process-global callback
 * slot live in srmech_progress.c, not in the hot dispatch translation unit.
 */
#ifndef SRMECH_PROGRESS_INTERNAL_H
#define SRMECH_PROGRESS_INTERNAL_H

#include "srmech.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Fire the registered progress callback (if any) for one dispatched tool.
 * Builds a compact canonical-JSON event
 *   {"category": <category>, "mpr_version": "1.0", "op_name": <op_name>}
 * (sorted keys, ensure_ascii=False — byte-identical to the Python
 * srmech.introspect._event.serialize shape) and hands it to the callback with
 * its registered user_data. A no-op when no callback is registered (the hot
 * path pays only a single NULL-pointer test). op_name / category are
 * NUL-terminated; NULL is tolerated and emitted as "". */
void srmech_progress_emit_dispatch(const char *op_name, const char *category);

#ifdef __cplusplus
}
#endif

#endif /* SRMECH_PROGRESS_INTERNAL_H */
