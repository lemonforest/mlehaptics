"""ephemerides_spectral srmech-profile smoke test.

ADR-0001 §5.5 — every srmech profile declares a single ``smoke_test``
callable that srmech invokes at first activation per profile-version.
A passing result is cached at
``~/.cache/srmech/profile_smoke_tests/ephemerides-<version>.toml``.

The contract: return ``None`` on success; raise on failure. The
exception message is what surfaces to the user as
``SmokeTestFailedError``.

The ephemerides-profile smoke test exercises load-bearing surfaces
across the declared bridge spectrum:

  1. ``get_version`` — version introspection.
  2. ``list_bodies`` — body catalog.
  3. ``list_attested_sources`` — AMSC catalog enumeration (the
     post-Task-#197 srmech-powered surface).
  4. ``_native_bip.HAS_NATIVE`` — confirms the plugin-tier native
     library (declared via ``[profile.native]`` since v0.28.0rc2)
     loaded cleanly with a matching ABI handshake. Skipped on the
     pure-Python wheel (Pyodide / WASM) where ``_native_bip`` reports
     no native library was found.

We deliberately AVOID the heavy dynamics surfaces (``find_syzygies``,
``find_itn_chains``, ``get_em_state``) in the smoke test — those have
load-bearing skyfield kernel dependencies that may not be present
in every deployment context (Pyodide, minimal install). The bridge
surfaces are still bound + callable; the smoke test just doesn't
invoke them.
"""

from __future__ import annotations


def smoke_test() -> None:
    """Verify the ephemerides-profile bridge surfaces work end-to-end.

    Raises:
        Any exception from the underlying call sites propagates. The
        srmech profile loader catches it and re-raises as
        ``srmech.SmokeTestFailedError`` with the original exception
        chained.
    """
    # Import inside the function so that import-time failures become
    # smoke-test failures rather than module-load failures.
    from ephemerides_spectral.bridge import (
        get_version,
        list_bodies,
        list_attested_sources,
    )

    v = get_version()
    if not isinstance(v, dict) or "version" not in v:
        raise RuntimeError(
            f"get_version returned {type(v).__name__}; "
            f"expected dict with 'version' key"
        )

    bodies = list_bodies()
    if not isinstance(bodies, dict) or "bodies" not in bodies:
        raise RuntimeError(
            f"list_bodies returned {type(bodies).__name__}; "
            f"expected dict with 'bodies' key"
        )
    # The Sol roster has 52 body slots as of v0.16.0; assert a sane
    # lower bound rather than the exact count (the roster grows in
    # minor versions; locking the count here would break the smoke
    # test on every new-body ship).
    if len(bodies["bodies"]) < 9:
        raise RuntimeError(
            f"list_bodies returned only {len(bodies['bodies'])} bodies; "
            "Sol Star System catalog should have at least the 9 major "
            "planets"
        )

    sources = list_attested_sources()
    if not isinstance(sources, dict):
        raise RuntimeError(
            f"list_attested_sources returned {type(sources).__name__}; "
            "expected dict"
        )
    # The "ok" status is what srmech.amsc.catalog returns for a healthy
    # enumeration; if attestation infra is wired correctly we'll get a
    # truthy result.
    if not sources.get("ok", False):
        raise RuntimeError(
            "list_attested_sources reported ok=False; AMSC catalog "
            f"infrastructure may be misconfigured. Full response: {sources!r}"
        )

    # ── Plugin-tier check (v0.28.0rc2+) ────────────────────────────────
    # The [profile.native] block in srmech_profile.toml declares
    # ephemerides_spectral as a plugin-tier profile; srmech's loader
    # has already verified the ABI handshake at Profile() construction
    # before this smoke test runs. The check here is the *paired*
    # confirmation: ephemerides-spectral's own ctypes shim
    # (_native_bip) must also load the same library cleanly.
    #
    # Pure-Python wheel (Pyodide / WASM / no-C build): _native_bip
    # reports HAS_NATIVE = False with LOAD_ERROR populated to "no
    # native library available". This is the expected pure-Python
    # path — we skip the assertion. Distinguishable from the v0.27.0-
    # era silent-rejection bug (ABI mismatch) which reported a
    # different LOAD_ERROR string.
    from ephemerides_spectral import _native_bip

    if not _native_bip.HAS_NATIVE:
        err = _native_bip.LOAD_ERROR or ""
        # Pyodide / pure-py wheel — expected, not an error.
        is_pure_python_install = (
            "no native library" in err.lower()
            or "could not locate" in err.lower()
            or err == ""
        )
        if not is_pure_python_install:
            raise RuntimeError(
                f"_native_bip.HAS_NATIVE is False with LOAD_ERROR "
                f"{err!r}. The plugin-tier profile is declared but the "
                f"paired ephemerides-spectral ctypes shim cannot load "
                f"the library. Check ABI version alignment between "
                f"_native_bip.EXPECTED_ABI_VERSION and the wheel's "
                f"bundled native library."
            )
