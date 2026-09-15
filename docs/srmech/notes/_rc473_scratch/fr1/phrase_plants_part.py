"""rc473 final repair 1: the gate_f1 can-fail lens's own phrase-plant driver
(gate_f1_canfail/phrase_plants.py), run UNCHANGED, over a slice of its plan list so that
each part fits one foreground call. Usage: python phrase_plants_part.py <repo_root> <out.ndjson> <start> <end>
The driver is loaded as source with its module-level plan loop replaced by the slice;
nothing else in it changes (printed: the sha256 of the driver file)."""
import hashlib
import sys

DRIVER = "/mnt/c/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/rc473h/gate_f1_canfail/phrase_plants.py"
root, out, start, end = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
src = open(DRIVER, "rb").read()
print("driver sha256", hashlib.sha256(src).hexdigest()[:16], flush=True)
text = src.decode("utf-8")
anchor = 'print("plans", len(plans), flush=True)'
assert text.count(anchor) == 1
text = text.replace(anchor, "plans = plans[%d:%d]\n" % (start, end) + anchor)
text = text.replace('with OUT.open("w") as fh:', 'with OUT.open("a") as fh:')
assert text.count('with OUT.open("a") as fh:') == 1
sys.argv = [DRIVER, root, out]
exec(compile(text, DRIVER, "exec"), {"__name__": "__main__", "__file__": DRIVER})
