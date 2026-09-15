"""rc473 instrument repair 1 (`#T1188`): two read-only probes behind the repair's CHANGELOG figures.

Usage:  python3 notes/_rc473_instr_r1_probe.py spellings <docs/srmech/python root>
        python3 notes/_rc473_instr_r1_probe.py named <ledger .ndjson> <name|op> <hook stderr file>

``spellings`` imports the root's ``tools/ripple_check.py`` and prints, for every forwarded spelling
gate round i1 named, what that runner's refusal returns — ``refused_forwarded_args`` where the
runner has it (the repair), ``narrowing_args`` where it does not (the instrument round's deny-list).

``named`` reads a Stop-hook block message and prints how many rows the hook claimed for that
ledger ("N of M ... ledger rows") and how many of the ledger's row names the message names
OUTSIDE its abbreviated one-line summary. Asserts nothing. numpy-free; no hashlib; no abs().
"""
import json
import re
import sys
from pathlib import Path

SPELLINGS = [
    ["-k", "pin"], ["-kpin"], ["-m", "slow"], ["--co"], ["-qk", "pin"], ["-xk", "pin"], ["-vk", "pin"],
    ["-xkpin"], ["-vkpin"], ["-qm", "slow"], ["-xm", "slow"], ["-o", "addopts=-k pin"],
    ["-oaddopts=-kscrub"], ["--override-ini=addopts=-kpin"], ["-c", "/tmp/other.ini"], ["--setup-plan"],
    ["--setup-only"], ["--fixtures"], ["--markers"], ["--version"], ["-h"], ["-p", "no:python"],
    ["tests/test_jpl_audit.py"], ["-x"], ["-xq"], ["-rfEs"], ["--tb=short"], ["--maxfail", "2"],
]


def spellings(root: Path) -> None:
    sys.path.insert(0, str(root / "tools"))
    import ripple_check as rc
    fn = getattr(rc, "refused_forwarded_args", None) or rc.narrowing_args
    print(f"runner {root / 'tools' / 'ripple_check.py'} judges with {fn.__name__}")
    let_through = 0
    for s in SPELLINGS:
        got = fn(s)
        let_through += not got
        print(f"  {' '.join(s):32s} -> {'REFUSED ' + repr(got) if got else 'let through'}")
    print(f"  let through: {let_through} of {len(SPELLINGS)} (the last 5 are the allowed report/stop options)")


def named(ledger: Path, key: str, err: Path) -> None:
    names = set()
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.strip():
            obj = json.loads(line)
            if obj.get("record") != "meta" and isinstance(obj.get(key), str):
                names.add(obj[key])
    text = err.read_text(encoding="utf-8", errors="replace")
    label = "worked-example" if key == "name" else "example-args"
    claim = re.search(r"(\d+) of (\d+) " + label + r" ledger rows", text)
    body = "\n".join(l for l in text.splitlines() if "unverified rows:" not in l)
    found = sorted(n for n in names if re.search(r"(?<![\w.])" + re.escape(n) + r"(?![\w.])", body))
    print(f"  {label}: hook claimed {claim.group(1) + ' of ' + claim.group(2) if claim else 'no block'}; "
          f"row names in the message outside its summary line: {len(found)}")


if __name__ == "__main__":
    if sys.argv[1] == "spellings":
        spellings(Path(sys.argv[2]))
    elif sys.argv[1] == "named":
        named(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    else:
        raise SystemExit("spellings | named")
