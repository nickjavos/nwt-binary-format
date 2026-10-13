#!/usr/bin/env python3
"""Compare one reference codec with the conformance files.

Usage: golden_check.py NAME CMD [ARG...]

NAME labels the output. CMD [ARG...] is the command that starts the codec, for example
`python3 examples/python/nwt_example.py` or `dotnet build/NwtExample.dll`.
The script runs 16 checks and exits with status 1 when any of them fails.
"""
import json, pathlib, subprocess, sys, tempfile

KIT = pathlib.Path(__file__).resolve().parents[1]
F = KIT / "fixtures"
G = F / "golden"
PY = [sys.executable, str(KIT / "examples/python/nwt_example.py")]
res = []


def run(args, c=None):
    try:
        return subprocess.run((c or cmd) + [str(a) for a in args], capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, b"", b"timeout")


def check(label, ok, detail=""):
    res.append(ok)
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else "  <- " + detail[:260].replace("\n", " | ")))


def same_file(label, r, path, golden):
    ok = r.returncode == 0 and path.exists() and path.read_bytes() == golden.read_bytes()
    check(label, ok, f"rc={r.returncode} {r.stderr.decode(errors='replace')}" if r.returncode else "bytes differ")


def same_out(label, r, golden):
    g = golden.read_bytes()
    ok = r.returncode == 0 and r.stdout == g
    d = ""
    if not ok:
        if r.returncode:
            d = f"rc={r.returncode} {r.stderr.decode(errors='replace')}"
        else:
            a, b = r.stdout.split(b"\n"), g.split(b"\n")
            i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            d = f"line {i+1}: got {a[i][:110] if i < len(a) else b'<eof>'!r} want {b[i][:110] if i < len(b) else b'<eof>'!r}"
    check(label, ok, d)


def main(out):
    same_file("write", run(["write", out / "basic.nwt"]), out / "basic.nwt", F / "all-records.nwt")
    same_file("write-golden raw", run(["write-golden", out / "golden.nwt"]), out / "golden.nwt", G / "all-records.nwt")
    same_out("read types 1-9", run(["read", F / "all-records.nwt"]), F / "all-fields.txt")
    same_out("read raw", run(["read", G / "all-records.nwt"]), G / "all-fields.txt")
    same_out("read zstd", run(["read", G / "all-records.zst.nwt"]), G / "all-fields.txt")
    same_out("read zstd+checksum", run(["read", G / "all-records.zst-checksum.nwt"]), G / "all-fields.txt")
    r = run(["read", G / "all-records.zst.nwt", out / "again.nwt"])
    same_file("re-encode zstd -> raw", r, out / "again.nwt", G / "all-records.nwt")
    same_out("to-json", run(["to-json", G / "all-records.nwt"]), G / "all-records.jsonl")
    same_out("to-json --pretty", run(["to-json", G / "all-records.nwt", "--pretty"]), G / "all-records.pretty.jsonl")
    bad = []
    for t in [1, 2, 3, 4] + list(range(6, 23)):
        for suffix, extra in (("", []), (".pretty", ["--pretty"])):
            r = run(["to-csv", G / "all-records.nwt", t] + extra)
            if r.returncode or r.stdout != (G / f"type-{t:02d}{suffix}.csv").read_bytes():
                bad.append(f"{t}{suffix}")
    check("to-csv all types (42 files)", not bad, "differs: " + " ".join(bad))
    check("to-csv 5 refused", run(["to-csv", G / "all-records.nwt", 5]).returncode != 0, "accepted")
    bad, seen = [], set()
    for f in sorted((G / "records").glob("*.bin")):
        t = json.loads(f.with_suffix(".json").read_text())["type"]
        r = run(["decode-record", f])
        want = subprocess.run(PY + ["decode-record", str(f)], capture_output=True).stdout
        if r.returncode or r.stdout != want:
            bad.append("decode " + f.name)
        if t >= 10 and t not in seen:
            seen.add(t)
            o = out / f"rec-{t}.bin"
            r = run(["record", t, o])
            if r.returncode or not o.exists() or o.read_bytes() != f.read_bytes():
                bad.append(f"record {t}")
    check("record 10-22 and decode-record (48 files)", not bad, " ; ".join(bad))
    bad = [f.name for f in sorted((G / "malformed").glob("*.nwt")) if run(["read", f]).returncode == 0]
    check("malformed all rejected (15 files)", not bad, "accepted: " + " ".join(bad))
    r = run(["write-golden", out / "golden-zstd.nwt", "--zstd"])
    if r.returncode:
        check("write-golden --zstd", False, r.stderr.decode(errors="replace"))
    else:
        same_out("write-golden --zstd read by itself", run(["read", out / "golden-zstd.nwt"]), G / "all-fields.txt")
        same_out("write-golden --zstd read by Python", run(["read", out / "golden-zstd.nwt"], c=PY), G / "all-fields.txt")
    r = run(["bench", G / "all-records.nwt"])
    ok = r.returncode == 0 and b"records_per_second" in r.stdout
    check("bench runs", ok, r.stderr.decode(errors="replace") or r.stdout.decode(errors="replace"))
    print(f"{name}: {sum(res)}/{len(res)} checks pass")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    name, cmd = sys.argv[1], sys.argv[2:]
    with tempfile.TemporaryDirectory() as folder:
        main(pathlib.Path(folder))
    sys.exit(0 if all(res) else 1)
