"""siona_debruijn_plugin (F824) — a C-native de Bruijn walk as a 3rd-party srmech profile plugin.

This package ships its own libsiona_debruijn.so and declares a ``srmech.profiles`` entry-point so srmech's
profile_loader discovers it (ABI-checked, smoke-tested) WITHOUT any edit to srmech core — the "lean srmech +
Siona owns the inference layer" architecture probe.
"""
