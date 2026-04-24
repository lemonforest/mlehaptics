"""Sheaf-spectrum-coupled phase operator — v0.3.1 scaffold.

The encoder maps each board state to a 768-dim vector.  The phase
operator is a state-dependent transformation of that vector,
parameterised by features of the faithful sheaf's Laplacian
spectrum.  This module implements a minimal viable framework:

  Phi(state)  :  R^768  ->  R^768

  Phi(state) = D(f(state)) · enc(state)

where D is a channel-wise diagonal scaling matrix and f maps the
8-dim sheaf spectrum feature vector to a 12-dim channel-weight
vector.  Different choices of f correspond to different physical
interpretations of the "phase".

Modes (v0.3.1)
--------------

  "identity"
      D = I; passes through.  Baseline for the benchmark.

  "scale_fiber_by_owner_lambda2"
      Channel 10 (sheaf_pending_black) scaled by 1 / (1 + lambda_2^B);
      channel 11 (sheaf_pending_white) by 1 / (1 + lambda_2^W).
      Intuition: when the bracket graph is well-connected (high
      lambda_2) the fiber is "diffused" so its contribution shrinks;
      when bracket structure is sparse the fiber dominates.

  "scale_all_by_kernel_dim"
      All 12 channels multiplied by kernel_dim / N_stalks where
      N_stalks = 192 = 64*3.  A Z2-symmetric averaged kernel:
      weight = 0.5 * (kerdim_B / 192 + kerdim_W / 192).  This
      dampens all channels uniformly in proportion to how
      disconnected the bracket graph is.

  "rotate_E_by_entropy"
      The D4 E irrep channel (indices 4 on magn and 9 on occ,
      2-dim per site) is the only D4-equivariant subspace admitting
      a non-trivial SO(2) rotation.  We apply an SO(2) rotation
      with angle theta = spectral_entropy(state_B).  The 1-dim
      irrep channels are left unchanged (Schur's lemma: D4-
      equivariant linear maps on 1-dim irreps are scalars, and we
      want unitary phases, so we'd need complex encoders to do a
      proper phase — deferred).

  "scale_by_feature_coupling"
      General-purpose mode.  Accepts a user-supplied 8-to-12
      linear coupling matrix M (loaded from a .npy) so
      weights = M @ sheaf_features.  Useful for experiments that
      learn or hand-tune the coupling.

Parity note
-----------
This operator is Python-only at v0.3.1.  The sheaf spectrum
computation uses scipy.linalg.eigh, which is not bit-identical
across machines (LAPACK implementations differ).  A future v0.4
could cache the eigenspectrum from the C encoder's bracket-count
output to get deterministic coupling; for now, reproducibility
is platform-dependent at float64 round-off scale.
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from .encoder import encode_768
from .tables import CHANNEL_NAMES, channel_slice


# Mode whitelist kept in sync with this module's apply()
VALID_MODES = (
    "identity",
    "scale_fiber_by_owner_lambda2",
    "scale_all_by_kernel_dim",
    "rotate_E_by_entropy",
    "scale_by_feature_coupling",
)


def _sheaf_spectrum_features(state: np.ndarray) -> dict:
    """Eight-dim sheaf spectrum features: (lambda_2, lambda_max,
    entropy, kernel_dim) x (black owner, white owner)."""
    import sys
    from pathlib import Path as _Path
    _research_dir = _Path(__file__).resolve().parent.parent
    if str(_research_dir) not in sys.path:
        sys.path.insert(0, str(_research_dir))
    from faithful_sheaf import faithful_sheaf_laplacian, spectrum_summary
    from othello_utils import BLACK

    state_int = np.asarray(state, dtype=int)
    L_b = faithful_sheaf_laplacian(state_int, owner=BLACK)
    spec_b = spectrum_summary(L_b)
    L_w = faithful_sheaf_laplacian(state_int, owner=-BLACK)
    spec_w = spectrum_summary(L_w)
    return {
        "lambda2_B":   spec_b["lambda_2"],
        "lambda2_W":   spec_w["lambda_2"],
        "lambdamax_B": spec_b["lambda_max"],
        "lambdamax_W": spec_w["lambda_max"],
        "entropy_B":   spec_b["entropy"],
        "entropy_W":   spec_w["entropy"],
        "kerdim_B":    float(spec_b["kernel_dim"]),
        "kerdim_W":    float(spec_w["kernel_dim"]),
    }


def _features_array(feats: dict) -> np.ndarray:
    """Canonical ordering used by scale_by_feature_coupling."""
    return np.array([
        feats["lambda2_B"], feats["lambda2_W"],
        feats["lambdamax_B"], feats["lambdamax_W"],
        feats["entropy_B"], feats["entropy_W"],
        feats["kerdim_B"], feats["kerdim_W"],
    ], dtype=np.float64)


class SheafPhaseOperator:
    """Apply a sheaf-spectrum-derived transformation to the 768-dim
    encoding of a state.

    Parameters
    ----------
    mode : str, one of VALID_MODES
        Which coupling to use.  See module docstring for mode-by-
        mode semantics.

    coupling_matrix : np.ndarray shape (12, 8), optional
        Only used when mode == 'scale_by_feature_coupling'.  Row i
        gives the 8-dim projection that produces channel i's weight.

    strength : float, default 1.0
        Interpolation factor between identity and the mode's full
        transformation.  strength=0 => identity; strength=1 =>
        the mode's native weights.  Smaller values yield smaller
        perturbations of the encoder output (useful for sweeping).
    """

    def __init__(
        self,
        mode: str = "identity",
        coupling_matrix: np.ndarray | None = None,
        strength: float = 1.0,
    ):
        if mode not in VALID_MODES:
            raise ValueError(
                f"unknown mode {mode!r}; expected one of {VALID_MODES}"
            )
        if mode == "scale_by_feature_coupling":
            if coupling_matrix is None:
                raise ValueError(
                    "mode='scale_by_feature_coupling' requires "
                    "coupling_matrix"
                )
            if coupling_matrix.shape != (12, 8):
                raise ValueError(
                    f"coupling_matrix must be (12, 8); got "
                    f"{coupling_matrix.shape}"
                )
        self.mode = mode
        self.coupling_matrix = coupling_matrix
        self.strength = float(strength)

    def _channel_weights(self, feats: dict) -> np.ndarray:
        """Return the 12-channel scaling vector for `feats`."""
        weights = np.ones(12, dtype=np.float64)
        if self.mode == "identity":
            return weights
        if self.mode == "scale_fiber_by_owner_lambda2":
            weights[10] = 1.0 / (1.0 + feats["lambda2_B"])
            weights[11] = 1.0 / (1.0 + feats["lambda2_W"])
            return weights
        if self.mode == "scale_all_by_kernel_dim":
            avg = 0.5 * (feats["kerdim_B"] + feats["kerdim_W"])
            weights[:] = avg / 192.0
            return weights
        if self.mode == "rotate_E_by_entropy":
            # For the scaling-only API we just damp E channels by
            # cos(theta); a true SO(2) rotation requires mixing
            # x/y sub-blocks which aren't exposed as a canonical
            # basis yet.  Return the scale approximation.
            theta = feats["entropy_B"]
            scale = float(np.cos(theta))
            # magn E- channel index 4, occ E+ channel index 9
            weights[4] = scale
            weights[9] = scale
            return weights
        if self.mode == "scale_by_feature_coupling":
            x = _features_array(feats)
            return (self.coupling_matrix @ x).astype(np.float64)
        raise AssertionError("unreachable")

    def apply(
        self, enc: np.ndarray, state: np.ndarray | None = None,
    ) -> np.ndarray:
        """Apply the operator to an existing 768-dim encoding.

        If ``state`` is omitted, identity is applied (no sheaf
        features available).  Otherwise the sheaf spectrum is
        computed and the mode's coupling is applied."""
        if enc.shape != (12 * 64,):
            raise ValueError(
                f"encoding must have shape (768,); got {enc.shape}"
            )
        if self.mode == "identity" or state is None:
            return np.asarray(enc, dtype=np.float64)
        feats = _sheaf_spectrum_features(state)
        weights = self._channel_weights(feats)
        # strength-interpolate with identity
        a = self.strength
        final_weights = a * weights + (1.0 - a) * np.ones_like(weights)
        out = np.asarray(enc, dtype=np.float64).copy()
        for k in range(12):
            out[channel_slice(k)] *= final_weights[k]
        return out

    def encode_phased(self, state: np.ndarray) -> np.ndarray:
        """Shorthand: encode the state and apply the operator in
        one call.  Uses v0.3.0 sheaf-fiber encoder by default."""
        enc = encode_768(state)
        return self.apply(enc, state)

    def channel_energies(self, enc: np.ndarray) -> dict:
        """Per-channel squared-norm of a phased encoding."""
        out = {}
        for i, name in enumerate(CHANNEL_NAMES):
            block = enc[channel_slice(i)]
            out[name] = float(np.dot(block, block))
        return out


__all__ = [
    "VALID_MODES",
    "SheafPhaseOperator",
]
