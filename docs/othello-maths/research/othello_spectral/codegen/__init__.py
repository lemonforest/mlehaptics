"""Codegen — Python -> C bit-identical table emission.

Uses the Python runtime's ``tables`` module as the single source of
truth and emits C17 const arrays carrying the same float64 entries
in little-endian memory layout.  The generated header is consumed
by c_encoder/src/othello_spectral.c to build the bit-identical
reference encoder.
"""
