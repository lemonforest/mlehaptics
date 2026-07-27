"""The ONE place that decides what "no native library" means (rc351, task `#T1004`).

Two correct disciplines collide on a single signal, and neither may be softened:

* **A native-parity test must FAIL, not skip, when the library is absent** — local
  task `#T843`, and the anti-false-claim rcs `#918` / `#939`. From
  ``test_mat_eigvals_c_peer_rc299.py``: *"the claim and the code must agree. If this
  fails, ``mat_eigvals`` is classified ``c_dispatched`` while no C entry point backs
  it — the exact false-claim shape this rc exists to end."* A silent skip is
  precisely the outcome those tests exist to prevent: a broken native build would
  sail through green.
* **The pure / Pyodide / WASM projection must be exercised with no library at all** —
  the rc351 ``fallback (pure-Python, no native)`` CI cell, which exists because no
  cell had ever run the suite that way and a pure install could save a fiber-bearing
  genome and never load it back.

``HAS_NATIVE == False`` cannot tell those apart. *"The build broke"* and *"we removed
the library on purpose"* produce the identical observation, so the discriminator
cannot be read off the library — it has to be **stated**. ``SRMECH_EXPECT_PURE=1`` is
that statement, and the rc351 CI cell is the only thing that sets it.

**Why this is not a mute button.**

1. It changes NOTHING unless the variable is set. Dev machines, the 4-cell matrix,
   the asserts-live cell and every existing caller keep today's behaviour exactly:
   library absent → the test FAILS, loudly, with the `#T843` reason attached.
2. It cannot be aimed at a specific failure. It gates on ONE structural predicate —
   is there a library to call at all — evaluated before the test body runs. It has no
   access to *why* a test failed and cannot convert a failure into a skip. A pure-path
   defect (the genome marker drift this rc fixes; the degenerate-eigenvector defect it
   found) is untouched by it and stays red.
3. The skips it produces are COUNTED. The cell asserts that the set of files reporting
   ``pure-by-design`` skips equals the set of files that call :func:`require_native`,
   so an eleventh gated test cannot appear un-noticed and a gate that stops firing is
   just as loud as one that fires too much. A seam that stops observing must fail.

Call it at the TOP of a test that cannot run without the library, and keep the test's
own specific symbol assertions after it — this gate answers "is there a library",
never "does it have the symbol I need", which stays the test's own claim to make.
"""

from __future__ import annotations

import os

import pytest

from srmech.amsc import _native

#: Set ONLY by the ``fallback (pure-Python, no native)`` job in
#: ``.github/workflows/srmech-ci.yml``. Read once, at import, so a test cannot flip it
#: mid-run: the intent belongs to the RUN, not to any test in it.
EXPECT_PURE: bool = os.environ.get("SRMECH_EXPECT_PURE") == "1"

#: The prefix every pure-by-design skip reason carries, so the CI audit step can count
#: them out of ``-rs`` output without matching on prose that might be reworded.
PURE_BY_DESIGN = "pure-by-design"


def require_native(what: str) -> None:
    """Gate a test that is meaningless without a loaded native library.

    ``what`` names the capability under test, and lands in both the skip reason and
    the failure message — so a red build says which C surface went missing.

    * library present → returns; the test proceeds unchanged.
    * library absent **and** ``SRMECH_EXPECT_PURE=1`` → :func:`pytest.skip`, tagged
      :data:`PURE_BY_DESIGN` for the CI audit.
    * library absent otherwise → :func:`pytest.fail`. This is the `#T843` contract: a
      native-parity claim with no native behind it is a FAILURE, never a quiet pass.
    """
    if _native.HAS_NATIVE and _native.LIB is not None:
        return
    if EXPECT_PURE:
        pytest.skip(f"{PURE_BY_DESIGN}: {what} needs the native library, and this run "
                    f"declared SRMECH_EXPECT_PURE=1")
    pytest.fail(
        f"native library absent, so {what} cannot be verified — and this run did NOT "
        f"declare SRMECH_EXPECT_PURE=1, so the library is missing UNEXPECTEDLY (a "
        f"broken or skipped C build). Per task `#T843` that is a FAILURE, not a skip: "
        f"a native-parity claim with nothing behind it must never pass quietly. "
        f"LOAD_ERROR={_native.LOAD_ERROR!r}"
    )
