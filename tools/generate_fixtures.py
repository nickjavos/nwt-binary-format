#!/usr/bin/env python3
"""Regenerate deterministic teaching fixtures after syncing embedded data.

The fixed ID is reserved for reproducible test output, not production use.
"""

import ctypes
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples/python"))
import nwt_example as nwt
from market_state import validate


def dump(data):
    return (
        "\n".join(f"{i:08x}  {data[i:i+16].hex(' ')}" for i in range(0, len(data), 16))
        + "\n"
    )


def fields(data, definitions):
    return {
        name: str(nwt.get(data, offset, width)) for name, offset, width in definitions
    }


def main():
    fixtures = ROOT / "fixtures"
    data = nwt.write_container(nwt.CATALOG)
    records = nwt.read_container(data)
    final_state = validate(records)
    (fixtures / "all-records.nwt").write_bytes(data)
    (fixtures / "all-records.hex.txt").write_text(dump(data))
    (fixtures / "all-fields.txt").write_text(nwt.report(records))
    for i, (sample, record) in enumerate(zip(nwt.CATALOG, records, strict=True), 1):
        name = f"{i:03}-{sample['label']}"
        (fixtures / "records" / f"{name}.bin").write_bytes(nwt.encode_record(record))
        (fixtures / "records" / f"{name}.json").write_text(
            json.dumps(sample, indent=2, ensure_ascii=False) + "\n"
        )

    container = fields(
        data,
        [
            ("major", 8, 2),
            ("minor", 10, 2),
            ("header_bytes", 12, 2),
            ("flags", 14, 2),
            ("metadata_bytes", 16, 4),
            ("metadata_crc32c", 20, 4),
            ("created_ns", 40, 8),
            ("reserved_48", 48, 8),
            ("header_crc32c", 56, 4),
            ("reserved_60", 60, 4),
        ],
    )
    container.update(magic_hex=data[:8].hex(), stream_id_hex=data[24:40].hex())
    frame_fields = [
        ("envelope_version", 4, 1),
        ("kind", 5, 1),
        ("codec", 6, 1),
        ("flags", 7, 1),
        ("header_bytes", 8, 2),
        ("reserved_10", 10, 2),
        ("stored_bytes", 12, 4),
        ("raw_bytes", 16, 4),
        ("record_count", 20, 4),
        ("frame_seq", 24, 8),
        ("min_event_ns", 32, 8),
        ("max_event_ns", 40, 8),
        ("payload_crc32c", 48, 4),
        ("header_crc32c", 52, 4),
        ("reserved_56", 56, 8),
    ]
    result = {
        "container_header": container,
        "manifest_tlv": fields(
            data[64:], [("type", 0, 2), ("flags", 2, 2), ("value_bytes", 4, 4)]
        ),
        "frames": [],
    }
    p = 64 + nwt.get(data, 16, 4)
    while p < len(data):
        header = data[p : p + 64]
        entry = fields(header, frame_fields)
        entry.update(offset=str(p), magic_hex=header[:4].hex())
        size = nwt.get(header, 12, 4)
        payload = data[p + 64 : p + 64 + size]
        if header[5] == 2:
            entry["index_entries"] = [
                fields(
                    payload[q : q + 40],
                    [
                        ("data_frame_seq", 0, 8),
                        ("data_frame_offset", 8, 8),
                        ("min_event_ns", 16, 8),
                        ("max_event_ns", 24, 8),
                        ("raw_bytes", 32, 4),
                        ("record_count", 36, 4),
                    ],
                )
                for q in range(0, size, 40)
            ]
        if header[5] == 3:
            entry["end_payload"] = fields(
                payload,
                [
                    ("first_index_offset", 0, 8),
                    ("total_data_frames", 8, 8),
                    ("total_records", 16, 8),
                    ("completion_status", 24, 4),
                    ("reserved", 28, 4),
                ],
            )
        result["frames"].append(entry)
        p += 64 + ((size + 7) & ~7)
    (fixtures / "container-fields.json").write_text(json.dumps(result, indent=2) + "\n")
    provenance = {
        "source_format": "synthetic",
        "source_version": "1.0-draft.2",
        "converter": "nwt-example",
        "conversion_policy": "All values are exact synthetic examples; no rounding.",
        "clock_policy": "POSIX nanoseconds; no source leap-smear applied.",
        "license_reference": "Example data generated for this documentation.",
    }
    (fixtures / "provenance-example.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
    value = json.dumps(provenance, separators=(",", ":")).encode()
    header = bytearray(8)
    nwt.put(header, 0, 2, 2)
    nwt.put(header, 4, 4, len(value))
    tlv = nwt.pad(bytes(header) + value)
    (fixtures / "provenance-example.tlv.bin").write_bytes(tlv)
    (fixtures / "provenance-example.tlv.hex.txt").write_text(dump(tlv))
    coverage = {}
    for schema in nwt.SCHEMA["schemas"][:9]:  # the draft.2 catalog covers types 1-9 only
        group = [r for r in records if r["type"] == schema["type"]]
        coverage[schema["name"]] = {
            "record_count": len(group),
            "all_fixed_fields_present": all(
                set(f["name"] for f in nwt.SCHEMA["header"] + schema["fields"])
                == set(r["fields"])
                for r in group
            ),
            "text_fields": schema["texts"],
            "payload_fields": [f["name"] for f in schema["fields"]],
        }
    summary = {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "records": len(records),
        "frames": len(result["frames"]),
        "coverage": coverage,
        "semantic_final_state": final_state,
    }
    (fixtures / "expected.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "bytes": len(data),
                "records": len(records),
                "frames": len(result["frames"]),
                "sha256": summary["sha256"],
            }
        )
    )


V11 = ROOT / "fixtures/v1.1"
V11_CREATED = 1760000000000000000


def v11_records():
    return [r for r in nwt.CATALOG_V11 if not r.get("standalone")]


def v11_container(patches=None, store=None, zstd_level=None, every=False):
    """The v1.1 container. `patches` maps a label to a function over that record's bytes;
    `store` rewrites the stored bytes of the first frame that compresses, or of every such frame."""
    out = io.BytesIO()
    writer = nwt.Writer(out, nwt.MANIFEST_V11, nwt.V11_ID, V11_CREATED, frame_records=3, zstd_level=zstd_level)
    if store:
        normal, used = writer.store, []

        def custom(payload):
            codec, stored = normal(payload)
            if codec == 0 or (used and not every):
                return codec, stored
            used.append(1)
            return 1, store(stored, payload)

        writer.store = custom
    for record in v11_records():
        raw = nwt.encode_record(record)
        if patches and record["label"] in patches:
            raw = patches[record["label"]](bytearray(raw))
        writer.write_raw(raw)
    writer.close()
    return out.getvalue()


def offset(typ, name, nth=0):
    """Absolute record offset of the nth body field called `name`."""
    at = 48
    for f in nwt.S[typ]["fields"]:
        if f["name"] == name:
            if nth == 0:
                return at
            nth -= 1
        at += f["bytes"]
    raise KeyError(name)


def patch(typ, *edits):
    """A record patch: (field name, nth, value) edits, then the bytes are returned unchanged otherwise."""

    def apply(raw):
        for name, nth, value in edits:
            width = next(f["bytes"] for f in nwt.S[typ]["fields"] if f["name"] == name)
            nwt.put(raw, offset(typ, name, nth), width, value)
        return bytes(raw)

    return apply


def longer_statistics(raw):
    """A STATISTICS record with eight extra zero bytes and a matching record_bytes: valid framing, wrong fixed size."""
    raw += bytes(8)
    nwt.put(raw, 0, 4, len(raw))
    return bytes(raw)


def zstd_reheader(descriptor, size_delta=0):
    """Replace the header of a single-segment Zstd frame and keep its blocks.

    The new header is the `descriptor` bytes followed by a 4-byte content size."""

    def apply(stored, payload):
        d = stored[4]
        assert d & 0x20 and not d & 0x0F, "expected a plain single-segment frame"
        n = (1, 2, 4, 8)[d >> 6]
        return stored[:4] + bytes(descriptor) + (len(payload) + size_delta).to_bytes(4, "little") + stored[5 + n :]

    return apply


def library_decompress(stored, size):
    """ZSTD_decompress with no NWT checks, to show a rejected frame is otherwise decodable."""
    out = ctypes.create_string_buffer(size)
    n = nwt.zstd_load().ZSTD_decompress(out, size, stored, len(stored))
    return out.raw[:n] if n == size else None


def zstd_with_checksum(_, payload):
    """Level 3 with Zstd's own content checksum, which the spec allows (the plain ZSTD_compress call omits it)."""
    lib = nwt.zstd_load()
    lib.ZSTD_createCCtx.restype = ctypes.c_void_p
    lib.ZSTD_freeCCtx.argtypes = [ctypes.c_void_p]
    lib.ZSTD_CCtx_setParameter.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    lib.ZSTD_CCtx_setParameter.restype = ctypes.c_size_t
    lib.ZSTD_compress2.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t]
    lib.ZSTD_compress2.restype = ctypes.c_size_t
    context = lib.ZSTD_createCCtx()
    try:
        for parameter, value in ((100, 3), (201, 1)):  # ZSTD_c_compressionLevel, ZSTD_c_checksumFlag
            assert not lib.ZSTD_isError(lib.ZSTD_CCtx_setParameter(context, parameter, value))
        room = lib.ZSTD_compressBound(len(payload))
        out = ctypes.create_string_buffer(room)
        n = lib.ZSTD_compress2(context, out, room, payload, len(payload))
        assert not lib.ZSTD_isError(n)
        return out.raw[:n]
    finally:
        lib.ZSTD_freeCCtx(context)


def swap_manifest_text(data, old, new):
    """Swap equal-length manifest text, so no offset moves, and repair the metadata and header CRCs."""
    size = nwt.get(data, 16, 4)
    meta = data[64 : 64 + size]
    assert len(old) == len(new) and meta.count(old) == 1
    head = bytearray(data[:64])
    nwt.put(head, 20, 4, nwt.crc(meta.replace(old, new)))
    return nwt.hcrc(head, 56) + meta.replace(old, new) + data[64 + size :]


def with_minor(data, minor):
    head = bytearray(data[:64])
    nwt.put(head, 10, 2, minor)
    return nwt.hcrc(head, 56) + data[64:]


def minor_zero_new_types_only():
    """A valid file whose only 1.1 types are 21 and 22, with the header minor set to 0."""
    publishers = json.loads(nwt.MANIFEST_V11)["publishers"]
    manifest = nwt.build_manifest("EXAMPLE.V11", "nwt-developer-kit/1.1-draft.1", publishers, [*range(1, 10), 21, 22])
    sequencer = nwt.Sequencer()
    records = []
    for record in v11_records():
        if record["type"] in (21, 22):
            f = record["fields"]
            sequence = sequencer.next(int(f["publisher_id"]), int(f["channel_id"]))
            records.append({**record, "fields": {**f, "sequence": str(sequence)}})
    return with_minor(nwt.write_container(records, manifest, nwt.V11_ID, V11_CREATED), 0)


def malformed(raw):
    """name -> (bytes, the reference reader's error). Each file has exactly one defect; all CRCs are valid."""
    skippable = b"\x50\x2a\x4d\x18" + (4).to_bytes(4, "little") + b"skip"
    wide = v11_container(store=zstd_reheader([0x80, 0x78]), zstd_level=3)  # window descriptor 0x78 = 32 MiB
    at = next(p for p in frame_offsets(wide) if wide[p + 6] == 1)
    stored, size = wide[at + 64 : at + 64 + nwt.get(wide, at + 12, 4)], nwt.get(wide, at + 16, 4)
    assert library_decompress(stored, size) is not None, "the wide-window frame must still be valid Zstd"
    return {
        "bad-enum": (v11_container({"stat-open": patch(13, ("stat_type", 0, 9))}), "invalid stat_type"),
        "bad-mask": (v11_container({"delta-set-bid": patch(15, ("delta_flags", 0, 2))}), "invalid delta_flags bits"),
        "nonzero-reserved": (v11_container({"listing-normal": patch(12, ("reserved", 1, 1))}), "nonzero reserved"),
        # One byte moves from legal_entity to name: 256 bytes in a 255-byte text, same record size.
        "text-over-limit": (
            v11_container(
                {"venue-segment-unicode": patch(10, ("name_bytes", 0, 256), ("legal_entity_bytes", 0, 23))}
            ),
            "name text limit",
        ),
        # One byte moves from osi_symbol to underlying_symbol: 20 bytes where only 0 or 21 are allowed.
        "wrong-text-exact": (
            v11_container(
                {"option-def-call": patch(11, ("underlying_symbol_bytes", 0, 5), ("osi_symbol_bytes", 0, 20))}
            ),
            "osi_symbol text length",
        ),
        "wrong-fixed-size": (v11_container({"stat-volume": longer_statistics}), "padding/record length"),
        "wrong-minor": (with_minor(raw, 0), "container minor"),
        "wrong-minor-new-types": (minor_zero_new_types_only(), "container minor"),
        "undeclared-type": (swap_manifest_text(raw, b'"type":13,', b'"type":99,'), "undeclared record type"),
        "undeclared-publisher": (swap_manifest_text(raw, b'{"id":1,', b'{"id":3,'), "undeclared publisher"),
        "zstd-content-size": (v11_container(store=zstd_reheader([0xA0], 1), zstd_level=3), "Zstd content size"),
        "zstd-window": (wide, "Zstd window"),
        "zstd-dictionary": (v11_container(store=zstd_reheader([0xA1, 0x01]), zstd_level=3), "Zstd dictionary"),
        "zstd-skippable": (v11_container(store=lambda stored, _: skippable + stored, zstd_level=3), "Zstd magic"),
        "zstd-trailing-bytes": (
            v11_container(store=lambda stored, _: stored + skippable, zstd_level=3),
            "Zstd frame must fill",
        ),
    }


def frame_offsets(data):
    at = 64 + nwt.get(data, 16, 4)
    while at < len(data):
        yield at
        at += 64 + ((nwt.get(data, at + 12, 4) + 7) & ~7)


def v11():
    nwt.zstd_load()  # the Zstd goldens cannot be written without the library
    for folder, patterns in (("records", ("*.bin", "*.json")), ("malformed", ("*.nwt", "*.json"))):
        (V11 / folder).mkdir(parents=True, exist_ok=True)
        for pattern in patterns:  # drop outputs of scenarios that no longer exist
            for stale in (V11 / folder).glob(pattern):
                stale.unlink()
    raw = v11_container()
    records = nwt.read_container(raw)
    fields = nwt.report(records)
    (V11 / "all-records.nwt").write_bytes(raw)
    (V11 / "all-fields.txt").write_bytes(fields.encode())
    for name, data in (
        ("all-records.zst.nwt", v11_container(zstd_level=3)),
        ("all-records.zst-checksum.nwt", v11_container(store=zstd_with_checksum, zstd_level=3, every=True)),
    ):
        assert nwt.report(nwt.read_container(data)) == fields and any(data[p + 6] == 1 for p in frame_offsets(data))
        (V11 / name).write_bytes(data)
    for pretty, suffix in ((False, ""), (True, ".pretty")):
        lines = "".join(nwt.to_json_line(r, pretty) + "\n" for r in records)
        (V11 / f"all-records{suffix}.jsonl").write_bytes(lines.encode())
        for typ, schema in sorted(nwt.S.items()):
            if schema["has_levels"]:
                continue  # to-csv refuses types with levels
            rows = [nwt.csv_header(typ)] + [nwt.to_csv_line(r, pretty) for r in records if r["type"] == typ]
            (V11 / f"type-{typ:02}{suffix}.csv").write_bytes("".join(row + "\n" for row in rows).encode())
    for i, sample in enumerate(nwt.CATALOG_V11, 1):
        name = f"{i:03}-{sample['label']}"
        (V11 / "records" / f"{name}.bin").write_bytes(nwt.encode_record(sample))
        (V11 / "records" / f"{name}.json").write_text(json.dumps(sample, indent=2, ensure_ascii=False) + "\n")
    cases = malformed(raw)
    for name, (data, reason) in cases.items():
        try:
            nwt.read_container(data)
        except ValueError as error:
            assert reason in str(error), f"{name}: rejected for the wrong reason: {error}"
        else:
            raise AssertionError(f"{name}: accepted")
        (V11 / "malformed" / f"{name}.nwt").write_bytes(data)
    expected = {f"{name}.nwt": "reject" for name in sorted(cases)}
    (V11 / "malformed" / "expected.json").write_text(json.dumps(expected, indent=2) + "\n")
    print(
        json.dumps(
            {
                "v1.1 bytes": len(raw),
                "records": len(records),
                "frames": len(list(frame_offsets(raw))),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "malformed": len(cases),
            }
        )
    )


if __name__ == "__main__":
    main()
    v11()
