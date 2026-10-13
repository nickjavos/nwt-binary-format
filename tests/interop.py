#!/usr/bin/env python3
"""Cross-check the four reference codecs on the container of record types 1-9.

Every codec writes fixtures/all-records.nwt, reads the file written by every other codec and re-encodes it.
The script then checks single records, integer boundaries, 25 malformed containers and the state rules.

Example:
python3 tests/interop.py --rust path/to/nwt-example --cpp path/to/nwt-cpp --csharp dotnet path/to/NwtExample.dll
"""

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "examples/python"))
import nwt_example as py
import market_state


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rust", required=True)
    parser.add_argument("--cpp", required=True)
    parser.add_argument("--csharp", required=True, nargs="+")
    parser.add_argument("--output", type=Path, help="folder for the files written (default: a temporary folder)")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as folder:
        out = (args.output or Path(folder)).resolve()
        out.mkdir(parents=True, exist_ok=True)
        run(args, out)


def run(args, out):
    commands = {
        "python": [sys.executable, str(KIT / "examples/python/nwt_example.py")],
        "rust": [str(Path(args.rust).resolve())],
        "cpp": [str(Path(args.cpp).resolve())],
        "csharp": args.csharp,
    }
    expected_bytes = (KIT / "fixtures/all-records.nwt").read_bytes()
    decoded = py.read_container(expected_bytes)
    expected_report = py.report(decoded).encode()
    catalog = json.loads((KIT / "fixtures/catalog.json").read_text())
    for actual, original in zip(decoded, catalog, strict=True):
        for key in ("type", "fields", "texts", "levels"):
            require(
                actual[key] == original[key],
                f"catalog mismatch: {original['label']} {key}",
            )

    counts = {
        "writer_checks": 0,
        "cross_language_reads": 0,
        "raw_record_reads": 0,
        "single_type_writes": 0,
        "boundary_reads": 0,
        "malformed_rejections": 0,
        "semantic_checks": 0,
    }

    def call(language, *arguments, good=True):
        result = subprocess.run(
            commands[language] + list(map(str, arguments)),
            capture_output=True,
            timeout=30,
        )
        require(
            (result.returncode == 0) == good,
            f"{language}: {arguments}: {result.returncode}\n{result.stderr.decode(errors='replace')}",
        )
        return result.stdout

    for writer in commands:
        path = out / f"{writer}.nwt"
        call(writer, "write", path)
        require(path.read_bytes() == expected_bytes, f"{writer} bytes disagree")
        counts["writer_checks"] += 1
        for reader in commands:
            again = out / f"{writer}-to-{reader}.nwt"
            report = call(reader, "read", path, again)
            require(report == expected_report, f"{writer}->{reader}: field report")
            require(
                again.read_bytes() == expected_bytes, f"{writer}->{reader}: re-encode"
            )
            counts["cross_language_reads"] += 1

    for sample in catalog:
        raw = py.encode_record(sample)
        file = out / "record.bin"
        file.write_bytes(raw)
        wanted = py.report([py.decode_record(raw)]).encode()
        for language in commands:
            require(
                call(language, "decode-record", file) == wanted,
                f"record: {sample['label']} {language}",
            )
            counts["raw_record_reads"] += 1
    for typ in range(1, 10):
        wanted = py.encode_record(next(r for r in catalog if r["type"] == typ))
        for language in commands:
            path = out / f"type-{typ}-{language}.bin"
            call(language, "record", typ, path)
            require(path.read_bytes() == wanted, f"single type writer {typ} {language}")
            counts["single_type_writes"] += 1

    trade = copy.deepcopy(next(r for r in catalog if r["type"] == 1))
    boundaries = []
    for price in (-(1 << 63) + 1, 0, (1 << 63) - 1):
        sample = copy.deepcopy(trade)
        sample["fields"].update(
            price=str(price),
            quantity=str((1 << 64) - 2),
            trade_id=str((1 << 64) - 1),
            ts_event="0",
            ts_recv=str((1 << 64) - 1),
        )
        boundaries.append(sample)
    for sample in boundaries:
        raw = py.encode_record(sample)
        (out / "boundary.bin").write_bytes(raw)
        wanted = py.report([py.decode_record(raw)]).encode()
        for language in commands:
            require(
                call(language, "decode-record", out / "boundary.bin") == wanted,
                "integer boundary",
            )
            counts["boundary_reads"] += 1

    def u(b, p, n):
        return int.from_bytes(b[p : p + n], "little")

    frames = []
    at = 64 + u(expected_bytes, 16, 4)
    record_positions = []
    while at < len(expected_bytes):
        raw = u(expected_bytes, at + 12, 4)
        frames.append((at, raw, expected_bytes[at + 5]))
        if expected_bytes[at + 5] == 1:
            p = at + 64
            while p < at + 64 + raw:
                n = u(expected_bytes, p, 4)
                record_positions.append((at, p, n, u(expected_bytes, p + 4, 2)))
                p += n
        at += 64 + ((raw + 7) & ~7)

    def repair_frame(b, frame):
        raw = u(b, frame + 12, 4)
        py.put(b, frame + 48, 4, py.crc(b[frame + 64 : frame + 64 + raw]))
        b[frame : frame + 64] = py.hcrc(b[frame : frame + 64], 52)

    def edit_record(typ, relative, width, value):
        b = bytearray(expected_bytes)
        f, p, _, _ = next(r for r in record_positions if r[3] == typ)
        py.put(b, p + relative, width, value)
        repair_frame(b, f)
        return bytes(b)

    malformed = {}
    for name, position in [
        ("header-crc", 40),
        ("metadata-crc", 80),
        ("frame-header-crc", frames[0][0] + 32),
        ("payload-crc", record_positions[0][1] + 48),
    ]:
        b = bytearray(expected_bytes)
        b[position] ^= 1
        malformed[name] = bytes(b)
    malformed["missing-end"] = expected_bytes[: frames[-1][0]]
    malformed["truncated-end"] = expected_bytes[:-1]
    malformed["trailing-byte"] = expected_bytes + b"\0"
    for name, offset, width, value in [
        ("wrong-count", 20, 4, 99),
        ("frame-sequence", 24, 8, 7),
        ("oversize-frame", 16, 4, 16777217),
        ("codec-mismatch", 6, 1, 1),
        ("frame-reserved", 56, 8, 1),
    ]:
        b = bytearray(expected_bytes)
        frame = frames[0][0]
        py.put(b, frame + offset, width, value)
        b[frame : frame + 64] = py.hcrc(b[frame : frame + 64], 52)
        malformed[name] = bytes(b)
    malformed.update(
        {
            "record-short": edit_record(1, 0, 4, 40),
            "record-long": edit_record(1, 0, 4, 1048584),
            "record-misaligned": edit_record(1, 0, 4, 87),
            "record-flags": edit_record(1, 7, 1, 128),
            "record-version": edit_record(1, 6, 1, 2),
            "record-reserved": edit_record(1, 84, 4, 1),
            "record-sequence": edit_record(1, 40, 8, 999),
            "levels-limit": edit_record(5, 48, 2, 1025),
            "string-length": edit_record(6, 104, 2, 65535),
            "invalid-utf8": edit_record(6, 112, 1, 255),
            "embedded-nul": edit_record(6, 112, 1, 0),
            "definition-padding": edit_record(6, 135, 1, 1),
        }
    )
    b = bytearray(expected_bytes)
    fi = next(f for f in frames if f[2] == 2)[0]
    py.put(b, fi + 64 + 8, 8, 64)
    repair_frame(b, fi)
    malformed["index-offset"] = bytes(b)
    for name, b in malformed.items():
        file = out / (name + ".nwt")
        file.write_bytes(b)
        for language in commands:
            call(language, "read", file, good=False)
            counts["malformed_rejections"] += 1

    summary = market_state.validate(decoded)
    counts["semantic_checks"] += 1
    semantic_cases = []

    def mutate(label, field, value):
        records = copy.deepcopy(decoded)
        index = next(i for i, r in enumerate(catalog) if r["label"] == label)
        records[index]["fields"][field] = str(value)
        semantic_cases.append((label + ":" + field, records))

    mutate("trade-correct", "original_sequence", 999)
    mutate("trade-new", "quantity", 0)
    mutate("quote-one-sided", "ask_quantity", 1)
    mutate("bar-complete", "high", 1)
    mutate("mbo-modify", "side", 2)
    mutate("mbo-add", "order_id", 0)
    mutate("mbo-snapshot-end", "action", 1)
    mutate("gap-1", "last_missing_source_sequence", 99)
    mutate("gap-2", "recovery_id", 1)
    mutate("status-recovery", "status", 99)
    mutate("system-1", "severity", 1)
    mutate("system-2", "related_recovery_id", 999)
    mutate("definition-1", "quantity_increment", 0)
    for label, records in semantic_cases:
        try:
            market_state.validate(records)
        except ValueError:
            counts["semantic_checks"] += 1
        else:
            raise AssertionError("invalid semantics accepted: " + label)

    state = market_state.MarketState()
    for r in decoded:
        state.apply(r)
        if r["type"] == 4 and r["fields"]["action"] == "5":
            require(state.working, "snapshot should have working state")
        if r["type"] == 8:
            require(not state.mbo and not state.working, "gap must invalidate book")
    result = {
        "status": "PASS",
        "catalog_records": len(catalog),
        "frame_count": len(frames),
        "bytes": len(expected_bytes),
        "sha256": hashlib.sha256(expected_bytes).hexdigest(),
        "checks": counts,
        "malformed_cases": list(malformed),
        "semantic_result": summary,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
