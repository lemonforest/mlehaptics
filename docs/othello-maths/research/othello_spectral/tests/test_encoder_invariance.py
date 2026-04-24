"""D4xZ2 equivariance + frame round-trip tests for the Othello encoder.

The irrep decomposition means that the encoder output must transform
predictably under spatial rotations/reflections and under Z2 colour
flip.  Specifically:

  - Z2-odd ('-') irrep blocks sign-flip under colour inversion s -> -s.
  - Z2-even ('+') irrep blocks are invariant under colour inversion.
  - Under a D4 element g, the block for a 1-dim irrep is invariant
    up to the irrep's character chi_mu(g) in {-1, +1}.  For the E
    irrep (2-dim), the block rotates within its own subspace and
    the squared norm is invariant.

For fiber channels built from L_ortho @ s and L_diag @ s, the Z2
colour flip inverts them (linear in s) and D4 rotations permute cells
within each channel (L_ortho and L_diag are D4-invariant operators).

Run:
    cd docs/othello-maths/research
    python -m othello_spectral.tests.test_encoder_invariance
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np


_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from d4_z2 import apply_element  # noqa: E402
from othello_spectral import encode_768  # noqa: E402
from othello_spectral.encoder import channel_energies  # noqa: E402
from othello_spectral.frame import Frame, read_file, write_file  # noqa: E402
from othello_spectral.tables import (  # noqa: E402
    CHANNEL_NAMES, N_CHANNELS, channel_slice,
)


def _random_state(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Sample Blume-Capel values uniformly; enforce a couple of
    # empties so the configuration is non-trivial but generic.
    s = rng.choice([-1, 0, 1], size=64, p=[0.4, 0.2, 0.4]).astype(int)
    return s


def test_z2_flip_signs_minus_blocks() -> None:
    s = _random_state(seed=11)
    enc_s = encode_768(s)
    enc_neg = encode_768(-s)
    # Z2-odd channels are indices 0..4 (magn_*minus); Z2-even 5..9
    # and fiber 10..11 require separate handling:
    #   occ channels depend on s^2 which is invariant under s -> -s.
    #   fiber channels are linear in s so they sign-flip.
    for i in range(5):  # magnetisation '-' irreps
        a = enc_s[channel_slice(i)]
        b = enc_neg[channel_slice(i)]
        assert np.allclose(b, -a, atol=1e-12), (
            f"channel {CHANNEL_NAMES[i]} should sign-flip under Z2"
        )
    for i in range(5, 10):  # occupation '+' irreps
        a = enc_s[channel_slice(i)]
        b = enc_neg[channel_slice(i)]
        assert np.allclose(b, a, atol=1e-12), (
            f"channel {CHANNEL_NAMES[i]} should be invariant under Z2"
        )
    for i in (10, 11):  # fiber on s
        a = enc_s[channel_slice(i)]
        b = enc_neg[channel_slice(i)]
        assert np.allclose(b, -a, atol=1e-12), (
            f"fiber channel {CHANNEL_NAMES[i]} should sign-flip under Z2"
        )


def test_d4_channel_energy_invariance() -> None:
    # Under any D4 element g, each channel block permutes within
    # itself (for 1-dim irreps, up to a sign; for the E irrep, as a
    # 2-dim rotation within its 2*64-dim isotypic component).  Hence
    # the squared norm of each channel block must be D4-invariant.
    s = _random_state(seed=17)
    base_energies = channel_energies(encode_768(s))
    for g in range(8):
        s_g = apply_element(s, g, 0)
        energies_g = channel_energies(encode_768(s_g))
        for name, e in base_energies.items():
            eg = energies_g[name]
            # For 1-dim irreps the block itself is D4-equivariant up
            # to chi_mu(g) sign; ||block||^2 invariant.  For E (2-dim)
            # the block rotates within its own subspace; ||block||^2
            # invariant.  Fiber channels are D4-invariant by
            # construction (L_ortho, L_diag commute with D4).
            assert abs(e - eg) < 1e-10, (
                f"channel {name} energy not D4-invariant under g={g}: "
                f"{e:.6g} vs {eg:.6g}"
            )


def test_encoder_sum_of_energies_equals_norm() -> None:
    s = _random_state(seed=22)
    enc = encode_768(s)
    en = channel_energies(enc)
    total_en = sum(en.values())
    sq = float(np.dot(enc, enc))
    assert abs(total_en - sq) < 1e-10, (total_en, sq)


def test_frame_roundtrip_bit_identical() -> None:
    # Random corpus of 5 positions, write + re-read, verify arrays
    # agree at float32 precision and metadata is preserved.
    states = [_random_state(seed=s) for s in (1, 2, 3, 4, 5)]
    frames_out = [
        Frame(data=encode_768(s), ply=i) for i, s in enumerate(states)
    ]
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "smoke.spectralz"
        write_file(
            p, frames_out, metadata="smoke_test run=sanity",
        )
        hdr, frames_in = read_file(p)
        assert hdr.n_frames == 5
        assert hdr.metadata.startswith("smoke_test"), hdr.metadata
        for fout, fin in zip(frames_out, frames_in):
            # Writer casts to float32; compare at float32 precision.
            out32 = np.asarray(fout.data, dtype=np.float32)
            assert np.array_equal(out32, fin.data), (
                "frame data changed across write+read"
            )
            assert fout.ply == fin.ply


ALL_TESTS = [
    test_z2_flip_signs_minus_blocks,
    test_d4_channel_energy_invariance,
    test_encoder_sum_of_energies_equals_norm,
    test_frame_roundtrip_bit_identical,
]


if __name__ == "__main__":
    failures = 0
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as exc:
            print(f"FAIL  {fn.__name__}: {exc}")
            failures += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
            failures += 1
    if failures:
        print(f"\n{failures} failures")
        sys.exit(1)
    print("\nall invariance tests passed")
