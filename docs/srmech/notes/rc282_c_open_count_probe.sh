#!/usr/bin/env bash
# rc282 - GENERATING CODE for the COMPILED-projection open count
# (computational-provenance discipline; ADR-0009 parity evidence).
#
# rc296 REPAIR: this probe did not run as committed. The rc290 `the_one` ->
# `coupling` rename left the section_counts call raising TypeError, so from rc290
# onward the generating code for rc282's "4 / 4 / 4 / 4" claim was dead. Provenance
# that does not execute is not provenance - a committed harness needs the same
# rename discipline as shipped code. Re-run at rc296 after the fix: the claim
# REPRODUCES exactly (4 opens of turns.bin per scan, flat across the sweep).
#
# rc296 also makes this measurable WITHOUT strace, from inside the test suite:
# the PAL read-path open counter (srmech_plat_file_opens / _reset) is asserted by
# tests/test_genome_read_io_ratchet_rc282.py. This script stays as the independent
# syscall-level oracle - the counter says what the library thinks it did, strace
# says what the kernel was actually asked for, and agreement between two
# instruments is the point.
#
# Counts openat("</path/to>/turns.bin") syscalls performed by the NATIVE
# srmech_genome_section_counts during one scan, over a sweep of section counts.
#
# Before rc282 the C refilled its 64 KiB sliding window through
# srmech_plat_file_read_region, which fopen/fcloses on every call -> at least one
# open per SECTION (more for a region wider than the window). rc282 holds ONE
# handle for the whole scan, so the count is constant in P.
#
# The markers are SYSCALLS (opening a uniquely-named file), not stderr writes,
# because "strace -o" records syscalls only - a stderr marker never lands in the
# trace and the scan window cannot be isolated from the store BUILD that precedes
# it (which legitimately opens turns.bin many times).
#
# Usage:  cd docs/srmech/python && bash ../notes/rc282_c_open_count_probe.sh
#         (requires strace and a built srmech/_native/libsrmech.so)
set -u

PY=/tmp/rc282_csc.py
cat > "$PY" <<'PYEOF'
import sys, tempfile
from srmech.amsc import _native, plasmid as P
from srmech.amsc.hdc import klein4_expand
n = int(sys.argv[1])
one = klein4_expand(64, 1282)
docs = [[f"w{(d * 17 + i * 5) % 400}" for i in range(40)] for d in range(n)]
d = tempfile.mkdtemp(prefix="rc282_csc_")
P.plasmid_extract(docs, d, one, window=2, k=8)
assert _native.has_native_genome_section_counts(), "native section_counts absent"
open("/tmp/RC282_MARK_START", "w").close()
_native.file_opens_reset_c()                     # rc296 in-library counter
P.section_counts(d, coupling=one)   # rc296: was `the_one=` (renamed at rc290)
c_opens = _native.file_opens_c()
open("/tmp/RC282_MARK_END", "w").close()
# rc296 cross-instrument line: what the LIBRARY counted for itself. strace (below)
# counts what the kernel was asked for, including the Python-side opens that happen
# before dispatch; this counts only the C library's own read-path opens. The two are
# different quantities on purpose - they must agree on the C-side subtotal.
with open("/tmp/RC296_C_OPENS", "w") as fh:
    fh.write(str(c_opens))
PYEOF

for n in 25 50 100 200; do
    tr=/tmp/rc282_tr_$n.txt
    PYTHONPATH=. strace -f -e trace=openat -o "$tr" python3 "$PY" "$n" 2>/dev/null
    start=$(grep -n 'RC282_MARK_START' "$tr" | head -1 | cut -d: -f1)
    end=$(grep -n 'RC282_MARK_END' "$tr" | head -1 | cut -d: -f1)
    if [ -z "$start" ] || [ -z "$end" ]; then
        echo "n_sections=$n  ERROR: markers not found in trace"
        continue
    fi
    span=$((end - start))
    opens=$(tail -n +"$start" "$tr" | head -n "$span" | grep -c 'turns\.bin')
    c_opens=$(cat /tmp/RC296_C_OPENS 2>/dev/null || echo '?')
    echo "n_sections=$n  turns_bin_opens_during_native_scan=$opens" \
         " c_library_read_path_opens=$c_opens"
done
