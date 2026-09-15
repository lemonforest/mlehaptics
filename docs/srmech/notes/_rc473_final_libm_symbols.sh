#!/bin/bash
# rc473 final round (`#T1188`): the undefined symbols of the two Class-K / Kuramoto
# objects and of the shared library, from a committed command. Truth repair 1's
# CHANGELOG grounded "no libm in srmech_kepler.c / srmech_kuramoto.c" on a scratch
# script (w_sym.sh) that was never committed; this is its committed replacement.
#
# Usage: notes/_rc473_final_libm_symbols.sh <cmake build dir>   (a gcc/clang build)
set -u
B=${1:?usage: $0 <cmake build dir>}
OBJ_KEPLER=$(find "$B" -name 'srmech_kepler.c.o' | head -1)
OBJ_KURAMOTO=$(find "$B" -name 'srmech_kuramoto.c.o' | head -1)
LIB=$(find "$B" -maxdepth 1 -name 'libsrmech.so' | head -1)
echo "srmech_kepler.c.o undefined: $(nm -u "$OBJ_KEPLER" | awk '{print $NF}' | sort | tr '\n' ' ')"
echo "srmech_kuramoto.c.o undefined: $(nm -u "$OBJ_KURAMOTO" | awk '{print $NF}' | sort | tr '\n' ' ')"
LIBM='^(sin|cos|tan|atan|atan2|exp|log|log1p|sqrt|pow|fabs|floor|ceil|fmod|hypot|sinh|cosh|tanh)(@.*)?$'
echo "libm-named undefined symbols: kepler $(nm -u "$OBJ_KEPLER" | awk '{print $NF}' | grep -cE "$LIBM")" \
     "kuramoto $(nm -u "$OBJ_KURAMOTO" | awk '{print $NF}' | grep -cE "$LIBM")" \
     "libsrmech.so $(nm -D --undefined-only "$LIB" | awk '{print $NF}' | grep -cE "$LIBM")"
echo "libsrmech.so NEEDED: $(readelf -d "$LIB" | awk '/NEEDED/ {print $NF}' | tr -d '[]' | tr '\n' ' ')"
