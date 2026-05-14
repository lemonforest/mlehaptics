"""chess_spectral srmech-profile smoke test.

ADR-0001 §5.5 — every srmech profile declares a single ``smoke_test``
callable that srmech invokes at first activation per profile-version.
A passing result is cached at
``~/.cache/srmech/profile_smoke_tests/chess-<version>.toml``; the
test runs again on the next profile-version bump.

The contract: return ``None`` on success; raise on failure. The
exception message is what surfaces to the user as
``SmokeTestFailedError``.

The chess-profile smoke test exercises the four load-bearing
surfaces it declares in ``srmech_profile.toml``'s ``[profile.bridge]``:

  1. FEN parsing (``fen_to_pos``).
  2. Canonical 2D encoder (``encode_2d`` → 640-dim vector).
  3. Channel introspection (``channel_energies`` → 10-channel dict).
  4. Pure-phase integer encoder (``encode_2d_pure_phase``).

If any of these fails at import / call time, the entire profile fails
to activate — surfacing the breakage at boot rather than mid-session.
"""

from __future__ import annotations


def smoke_test() -> None:
    """Verify the chess-profile bridge surfaces work end-to-end.

    Runs the four core surfaces against the standard chess starting
    position. The starting position is the smallest reproducible
    input that exercises every channel + every piece-type encoder
    code path; sub-1-second on any consumer hardware.

    Raises:
        Any exception from the underlying call sites propagates. The
        srmech profile loader catches it and re-raises as
        ``srmech.SmokeTestFailedError`` with the original exception
        chained.
    """
    # Import inside the function so that import-time failures (e.g.,
    # missing numpy in a degraded environment) become smoke-test
    # failures rather than module-load failures of this module itself.
    from chess_spectral.encoder import encode_2d, channel_energies
    from chess_spectral.encoder_pure_phase import encode_2d_pure_phase
    from chess_spectral.fen import fen_to_pos

    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    pos = fen_to_pos(starting_fen)

    enc = encode_2d(pos)
    if enc.shape != (640,):
        raise RuntimeError(
            f"encode_2d returned shape {enc.shape}, expected (640,)"
        )

    energies = channel_energies(enc)
    if not isinstance(energies, dict) or len(energies) == 0:
        raise RuntimeError(
            f"channel_energies returned {type(energies).__name__} "
            f"with {len(energies) if hasattr(energies, '__len__') else '?'} "
            "entries; expected non-empty dict"
        )

    # Pure-phase encoder returns int16 array; same shape as canonical.
    enc_int = encode_2d_pure_phase(pos)
    if enc_int.shape != (640,):
        raise RuntimeError(
            f"encode_2d_pure_phase returned shape {enc_int.shape}, "
            "expected (640,)"
        )
