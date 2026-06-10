"""Path A baseline — closed-form signal-processing operations.

Phase 2 of the RBS-HDC-LoE dual-path architecture per the implementation plan
``docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md``.

Each module in this package re-surfaces an existing closed-form algebra
operation as a Path A baseline. The operations are identity-not-implementation
re-surfaces of compositions over the 14-class A-N vocabulary; no new primitive
class is introduced (per ``[[feedback_no_privileged_primitive_classes]]``).

Each module exports:

- Module-level constants: ``OPERATION_NAME``, ``CLASS_COMPOSITION``,
  ``PERFORMANCE_HINT``, ``SSOT_CITATION``.
- A single callable ``op(*args, **kwargs) -> result`` wrapping the existing
  ``srmech.amsc.*`` primitive (or, for ops whose primitive is not yet in
  srmech.amsc, the closed-form reference implementation via numpy/scipy).

The 38 ops cover the eight categories surveyed in Spike #178 §1:

- Spectral analysis: ``fft``, ``stft``, ``dct``, ``wavelet``, ``spectrogram``,
  ``cross_spectral``, ``multitaper``.
- Filtering: ``matched_filter``, ``wiener``, ``fir``, ``iir``, ``allpass``.
- Denoising: ``sign_quantise``, ``heat_kernel``, ``spectral_subtraction``.
- Compression: ``huffman``, ``arithmetic_coding``, ``lz77``, ``rle``,
  ``jpeg``, ``hdc_truncation``, ``vector_quantisation``.
- Modulation (civilian-comms framing per
  ``[[feedback_trauma_informed_defensive_scope]]``): ``psk_qam``, ``fsk``,
  ``ofdm``, ``mimo_svd``, ``viterbi``, ``mlse``.
- Multi-rate: ``multirate``, ``polyphase``, ``farrow``, ``sinc_interp``.
- Adaptive / multi-signal: ``beamforming_fixed``, ``ica_jade``, ``music``,
  ``esprit``, ``lmmse``, ``map_ml``.

Post-merge integration (Phase 1 work): a registration script iterates the 38
modules and registers each in ``srmech.signal_processing.path_registry`` using
the module-level constants.
"""

from __future__ import annotations

from srmech._scientific import make_lazy_op_getattr as _make_lazy_op_getattr

#: Every op submodule, imported LAZILY (rc71): the numpy-free ops (the FFT
#: family) import + run with no numpy; the numpy ops import numpy only when
#: accessed. Eager ``from . import (…all 41…)`` previously forced numpy onto
#: ``import srmech.signal_processing`` even for the numpy-free ops.
_OP_MODULES = (
    "allpass", "arithmetic_coding", "beamforming_fixed", "cross_spectral",
    "dct", "esprit", "farrow", "fft", "fir", "fsk", "hdc_truncation",
    "heat_kernel", "huffman", "ica_jade", "ifft", "iir", "jpeg", "lmmse",
    "lz77", "map_ml", "matched_filter", "mimo_svd", "mlse", "multirate",
    "multitaper", "music", "ofdm", "pi_cascade", "polyphase", "psk_qam",
    "rfft", "rle", "sign_quantise", "sinc_interp", "spectral_subtraction",
    "spectrogram", "stft", "vector_quantisation", "viterbi", "wavelet",
    "wiener",
)

__getattr__ = _make_lazy_op_getattr(__name__, _OP_MODULES)


def __dir__():
    return sorted(set(globals()) | set(_OP_MODULES))

#: Canonical list of all 38 Path A op module names. Used by tests and the
#: post-merge registration script (Phase 1 integration).
PATH_A_OP_MODULES = (
    "fft",
    "stft",
    "dct",
    "wavelet",
    "spectrogram",
    "cross_spectral",
    "multitaper",
    "matched_filter",
    "wiener",
    "fir",
    "iir",
    "allpass",
    "sign_quantise",
    "heat_kernel",
    "spectral_subtraction",
    "huffman",
    "arithmetic_coding",
    "lz77",
    "rle",
    "jpeg",
    "hdc_truncation",
    "vector_quantisation",
    "psk_qam",
    "fsk",
    "ofdm",
    "mimo_svd",
    "viterbi",
    "mlse",
    "multirate",
    "polyphase",
    "farrow",
    "sinc_interp",
    "beamforming_fixed",
    "ica_jade",
    "music",
    "esprit",
    "lmmse",
    "map_ml",
)

__all__ = [
    "PATH_A_OP_MODULES",
    "allpass",
    "arithmetic_coding",
    "beamforming_fixed",
    "cross_spectral",
    "dct",
    "esprit",
    "farrow",
    "fft",
    "fir",
    "fsk",
    "hdc_truncation",
    "heat_kernel",
    "huffman",
    "ica_jade",
    "ifft",
    "iir",
    "jpeg",
    "lmmse",
    "lz77",
    "map_ml",
    "matched_filter",
    "mimo_svd",
    "mlse",
    "multirate",
    "multitaper",
    "music",
    "ofdm",
    "pi_cascade",
    "polyphase",
    "psk_qam",
    "rfft",
    "rle",
    "sign_quantise",
    "sinc_interp",
    "spectral_subtraction",
    "spectrogram",
    "stft",
    "vector_quantisation",
    "viterbi",
    "wavelet",
    "wiener",
]
