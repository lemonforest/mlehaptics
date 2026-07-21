#!/usr/bin/env bash
# rc282 - GENERATING CODE for the COMPILED-projection open count
# (computational-provenance discipline; ADR-0009 parity evidence).
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
P.section_counts(d, the_one=one)
open("/tmp/RC282_MARK_END", "w").close()
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
    echo "n_sections=$n  turns_bin_opens_during_native_scan=$opens"
done
