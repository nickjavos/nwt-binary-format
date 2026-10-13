#!/usr/bin/env python3
"""Contract tests for the NWT 1.1 Python reference codec.

Run: python3 tests/test_contract.py
Plain functions and asserts; every test_* function is called and one summary
line is printed. Exit status is non-zero when any test fails.
"""

import copy
import hashlib
import io
import json
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "examples/python"))
import nwt_example as nwt

EXAMPLE = [sys.executable, str(KIT / "examples/python/nwt_example.py")]
GOLDEN = KIT / "fixtures/v1.1"
LEGACY_SHA = "5b15390e0afd23ee0f8ab4490fd0980a61a0ede8c05d963f29b51fbb3ecf9b59"
V11_ID = bytes.fromhex("a1b2c3d4e5f60718293a4b5c6d7e8f90")
V11_CREATED = 1760000000000000000

# Spec section 3, transcribed independently of schemas/records.json: name:offset:bytes.
LAYOUT = {
    10: "created_ns:48:8 updated_ns:56:8 expiry_ns:64:8 kind:72:1 status:73:1 mic_bytes:74:2 "
    "operating_mic_bytes:76:2 country_bytes:78:2 category_bytes:80:2 acronym_bytes:82:2 "
    "city_bytes:84:2 name_bytes:86:2 legal_entity_bytes:88:2 lei_bytes:90:2 reserved:92:4",
    11: "underlying_instrument_id:48:8 expiration_ns:56:8 strike:64:8 contract_multiplier:72:8 "
    "right:80:1 exercise_style:81:1 settlement:82:1 closing_type:83:1 option_flags:84:1 "
    "reserved:85:3 root_bytes:88:2 underlying_symbol_bytes:90:2 osi_symbol_bytes:92:2 currency_bytes:94:2",
    12: "round_lot:48:4 listing_flags:52:1 market_tier:53:1 financial_flags:54:1 reserved:55:1 "
    "symbol_bytes:56:2 name_bytes:58:2 listing_mic_bytes:60:2 cqs_symbol_bytes:62:2 "
    "alt_symbol_bytes:64:2 reserved:66:6",
    13: "ts_ref:48:8 price:56:8 quantity:64:8 stat_type:72:2 action:74:1 stat_flags:75:1 reserved:76:4",
    14: "implied_volatility:48:8 delta:56:8 gamma:64:8 theta:72:8 vega:80:8 rho:88:8 "
    "underlying_price:96:8 theoretical_price:104:8 price_basis:112:1 model:113:1 reserved:114:6",
    15: "price:48:8 quantity:56:8 order_count:64:4 action:68:1 side:69:1 delta_flags:70:1 reserved:71:1",
    16: "auction_ns:48:8 reference_price:56:8 near_price:64:8 far_price:72:8 paired_quantity:80:8 "
    "imbalance_quantity:88:8 imbalance_side:96:1 auction_type:97:1 reserved:98:6",
    17: "valid_from_ns:48:8 valid_to_ns:56:8 symbology:64:1 reserved:65:1 symbol_bytes:66:2 reserved:68:4",
    18: "price:48:8 quantity:56:8 trade_id:64:8 bid_price:72:8 ask_price:80:8 bid_quantity:88:8 "
    "ask_quantity:96:8 bid_order_count:104:4 ask_order_count:108:4 aggressor:112:1 reserved:113:1 "
    "conditions:114:2 reserved:116:4",
    19: "bid_price:48:8 ask_price:56:8 bid_quantity:64:8 ask_quantity:72:8 bid_order_count:80:4 "
    "ask_order_count:84:4 quote_flags:88:4 bid_publisher_id:92:4 ask_publisher_id:96:4 "
    "reserved:100:4 interval_ns:104:8",
    20: "data_frame_seq:48:8 data_frame_offset:56:8 stored_bytes:64:4 codec:68:1 summary_flags:69:1 "
    "reserved:70:2 type_mask:72:8 min_instrument_id:80:8 max_instrument_id:88:8 reserved:96:8",
}
FIXED = {10: 96, 11: 96, 12: 72, 13: 80, 14: 120, 15: 72, 16: 104, 17: 72, 18: 120, 19: 112, 20: 104}
NAMES = {
    10: "VENUE_DEF", 11: "OPTION_DEF", 12: "LISTING", 13: "STATISTICS", 14: "OPTION_ANALYTICS",
    15: "BOOK_DELTA", 16: "IMBALANCE", 17: "SYMBOL_MAP", 18: "TRADE_QUOTE", 19: "BEST_QUOTE",
    20: "FRAME_SUMMARY",
}  # fmt: skip
TEXTS = {
    10: "mic operating_mic country category acronym city name legal_entity lei",
    11: "root underlying_symbol osi_symbol currency",
    12: "symbol name listing_mic cqs_symbol alt_symbol",
    17: "symbol",
}
SIGNED = {
    11: "strike contract_multiplier",
    13: "price",
    14: "implied_volatility delta gamma theta vega rho underlying_price theoretical_price",
    15: "price",
    16: "reference_price near_price far_price",
    18: "price bid_price ask_price",
    19: "bid_price ask_price",
}
# Brief step 4, verbatim.
RULES = {
    10: {"enums": {"kind": [1, 2], "status": [1, 2, 3]},
         "text_limits": {"mic": [4, 4], "operating_mic": [4, 4], "country": [2, 2], "acronym": [0, 64],
                         "city": [0, 128], "name": [1, 255], "legal_entity": [0, 255]},
         "text_exact": {"category": [0, 4], "lei": [0, 20]}},
    11: {"enums": {"right": [1, 2], "exercise_style": [0, 1, 2], "settlement": [0, 1, 2], "closing_type": [0, 1, 2]},
         "masks": {"option_flags": 3},
         "text_limits": {"root": [1, 16], "underlying_symbol": [0, 255], "currency": [0, 16]},
         "text_exact": {"osi_symbol": [0, 21]}},
    12: {"enums": {"market_tier": [0, 1, 2, 3]}, "masks": {"listing_flags": 7, "financial_flags": 15},
         "text_limits": {"symbol": [1, 255], "name": [0, 512], "cqs_symbol": [0, 255], "alt_symbol": [0, 255]},
         "text_exact": {"listing_mic": [0, 4]}},
    13: {"enums": {"stat_type": [1, 2, 3, 4, 5, 6, 7, 8], "action": [1, 2]}, "masks": {"stat_flags": 1}},
    14: {"enums": {"price_basis": [0, 1, 2, 3, 4, 5], "model": [0, 1, 2, 3, 4]}},
    15: {"enums": {"action": [1, 2, 3], "side": [0, 1, 2]}, "masks": {"delta_flags": 1}},
    16: {"enums": {"imbalance_side": [0, 1, 2], "auction_type": [0, 1, 2, 3, 4, 5]}},
    17: {"enums": {"symbology": [1, 2, 3, 4, 5, 6]}, "text_limits": {"symbol": [1, 255]}},
    18: {"enums": {"aggressor": [0, 1, 2]}, "masks": {"conditions": 1}},
    19: {"masks": {"quote_flags": 1}},
    20: {"enums": {"codec": [0, 1]}, "masks": {"summary_flags": 3}},
    21: {"enums": {"listing_source": [0, 1, 2]}, "masks": {"security_flags": 1},
         "text_limits": {"issuer_name": [0, 255], "description": [0, 255], "security_type": [0, 8], "structure": [0, 8],
                         "listing_status": [0, 8], "voting": [0, 8], "primary_exchange": [0, 16], "exchange": [0, 16],
                         "segment_name": [0, 128], "symbol": [0, 255], "alt_symbol": [0, 255], "local_code": [0, 255],
                         "composite_ticker": [0, 32], "figi_ticker": [0, 32], "fisn": [0, 35], "cic": [0, 8],
                         "gics": [0, 8], "trading_currency": [0, 16], "par_value_currency": [0, 16]},
         "text_exact": {"operating_mic": [0, 4], "segment_mic": [0, 4], "isin": [0, 12], "cusip": [0, 9],
                        "composite_figi": [0, 12], "figi": [0, 12], "lei": [0, 20], "cfi": [0, 6],
                        "incorporation_country": [0, 2], "listing_country": [0, 2], "register_country": [0, 2]}},
    22: {"masks": {"action_flags": 1},
         "text_limits": {"event": [1, 8], "subtype": [0, 16], "action": [0, 8], "status": [0, 8], "participation": [0, 8],
                         "payment_type": [0, 8], "fraction": [0, 8], "date_label": [0, 32], "related_event": [0, 8],
                         "related_event_id": [0, 32], "event_id": [1, 32], "unique_id": [1, 48],
                         "rate_currency": [0, 16], "details": [0, 65535]},
         "text_exact": {"outturn_isin": [0, 12]}},
    6: {"text_limits": {"symbol": [1, 255], "venue": [0, 255], "currency": [1, 16], "quantity_unit": [1, 32]}},
    9: {"text_limits": {"text": [0, 4096]}},
}  # fmt: skip
RULE_KEYS = ("enums", "masks", "text_limits", "text_exact")
# Brief step 5: label, type, instrument.
SCENARIOS = [
    ("def-equity", 6, 2001), ("def-option", 6, 2002), ("venue-operating", 10, 0),
    ("venue-segment-unicode", 10, 0), ("venue-expired", 10, 0), ("listing-normal", 12, 2001),
    ("listing-etf-deficient", 12, 2003), ("listing-minimal", 12, 2005), ("listing-awkward-text", 12, 2006),
    ("option-def-call", 11, 2002), ("option-def-unknowns", 11, 2004), ("symbol-map-native", 17, 2001),
    ("symbol-map-closed-isin", 17, 2001), ("symbol-map-root", 17, 2002), ("trade-new", 1, 2001),
    ("quote-two-sided", 2, 2001), ("bar-complete", 3, 2001), ("status-open", 7, 2001),
    ("book-snapshot", 5, 2001), ("delta-set-bid", 15, 2001), ("delta-set-ask-last", 15, 2001),
    ("delta-delete", 15, 2001), ("delta-clear-side", 15, 2001), ("delta-clear-all", 15, 2001),
    ("mbo-clear", 4, 2001), ("mbo-add", 4, 2001), ("stat-open", 13, 2001),
    ("stat-settlement-preliminary", 13, 2001), ("stat-volume", 13, 2001), ("stat-open-interest", 13, 2002),
    ("stat-delete", 13, 2001), ("analytics-full", 14, 2002), ("analytics-iv-only", 14, 2002),
    ("analytics-put-negative", 14, 2002), ("imbalance-buy", 16, 2001), ("imbalance-none", 16, 2001),
    ("trade-quote", 18, 2001), ("trade-quote-one-sided", 18, 2001), ("best-quote-event", 19, 2001),
    ("best-quote-sampled", 19, 2001), ("gap", 8, 0), ("system-heartbeat", 9, 0),
    ("security-def-full", 21, 3001), ("security-def-minimal", 21, 3002), ("corporate-action-dividend", 22, 3001),
    ("corporate-action-split", 22, 3001), ("corporate-action-minimal", 22, 3002), ("frame-summary", 20, 0),
]  # fmt: skip
AWKWARD = 'Awkward, "Quoted" \\ Name\nLine two\x01 café'


# ---------------------------------------------------------------- helpers


def raises(fn, *args, contains="", **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError as error:
        assert contains in str(error), f"expected {contains!r} in {str(error)!r}"
        return
    raise AssertionError(f"expected ValueError({contains!r})")


def plain(record):
    return {key: record[key] for key in ("type", "fields", "texts", "levels")}


def file_records():
    return [r for r in nwt.CATALOG_V11 if not r.get("standalone")]


def scenario(label):
    return copy.deepcopy(next(r for r in nwt.CATALOG_V11 if r["label"] == label))


def example(typ):
    catalog = nwt.CATALOG if typ <= 9 else nwt.CATALOG_V11
    return copy.deepcopy(next(r for r in catalog if r["type"] == typ))


def offsets(fields, start):
    out = []
    for f in fields:
        out.append((f["name"], start, f["bytes"]))
        start += f["bytes"]
    return out


def body_offsets(typ):
    return offsets(nwt.S[typ]["fields"], 48)


def raw_encode(record):
    """Unchecked encoder, written separately from nwt.encode_record, for building invalid records."""
    schema = nwt.S[record["type"]]
    values = dict(record["fields"])
    for name in schema["texts"]:
        values.setdefault(name + "_bytes", str(len(record["texts"][name].encode())))
    body = b""
    for f in schema["fields"]:
        body += int(values[f["name"]]).to_bytes(f["bytes"], "little", signed=f["signed"])
    for level in record["levels"]:
        for f in nwt.SCHEMA["level"]:
            body += int(level[f["name"]]).to_bytes(f["bytes"], "little", signed=f["signed"])
    for name in schema["texts"]:
        body += record["texts"][name].encode()
    body += bytes(-len(body) % 8)
    values["record_bytes"] = str(48 + len(body))
    head = b""
    for f in nwt.SCHEMA["header"]:
        head += int(values[f["name"]]).to_bytes(f["bytes"], "little", signed=f["signed"])
    return head + body


def set_text(record, name, text):
    record["texts"][name] = text
    record["fields"][name + "_bytes"] = str(len(text.encode()))
    return record


def renumber(records):
    """Copies with fresh consecutive sequences per (publisher, channel)."""
    sequencer = nwt.Sequencer()
    out = []
    for record in records:
        record = copy.deepcopy(record)
        f = record["fields"]
        f["sequence"] = str(sequencer.next(int(f["publisher_id"]), int(f["channel_id"])))
        out.append(record)
    return out


def reader_for(data):
    return nwt.Reader(lambda offset, n: data[offset : offset + n], len(data))


def v11_bytes(**options):
    return nwt.write_container(file_records(), nwt.MANIFEST_V11, V11_ID, V11_CREATED, **options)


def frame_table(data):
    """(offset, kind, codec, stored, raw) for every frame, read without the codec under test."""
    out = []
    at = 64 + int.from_bytes(data[16:20], "little")
    while at < len(data):
        stored = int.from_bytes(data[at + 12 : at + 16], "little")
        raw = int.from_bytes(data[at + 16 : at + 20], "little")
        out.append((at, data[at + 5], data[at + 6], stored, raw))
        at += 64 + ((stored + 7) & ~7)
    return out


def replace_metadata_text(data, old, new):
    """Swap equal-length manifest text and repair the metadata and header CRCs."""
    assert len(old) == len(new)
    size = int.from_bytes(data[16:20], "little")
    meta = data[64 : 64 + size]
    assert meta.count(old) == 1, old
    meta = meta.replace(old, new)
    head = bytearray(data[:64])
    nwt.put(head, 20, 4, nwt.crc(meta))
    return nwt.hcrc(head, 56) + meta + data[64 + size :]


def with_metadata(metadata):
    """An empty legacy-version container (metadata then END) around arbitrary metadata bytes."""
    head = bytearray(nwt.write_container([])[:64])
    nwt.put(head, 16, 4, len(metadata))
    nwt.put(head, 20, 4, nwt.crc(metadata))
    return nwt.hcrc(head, 56) + metadata + nwt.frame(3, 0, struct.pack("<QQQII", 0, 0, 0, 0, 0))


def tlv(typ, flags, value):
    return nwt.pad(struct.pack("<HHI", typ, flags, len(value)) + value)


def run(*arguments, env=None):
    return subprocess.run(EXAMPLE + [str(a) for a in arguments], capture_output=True, timeout=120, env=env)


# ------------------------------------------------------------------ tests


def test_legacy_sha():
    data = nwt.write_container(nwt.CATALOG)
    assert hashlib.sha256(data).hexdigest() == LEGACY_SHA
    assert data == (KIT / "fixtures/all-records.nwt").read_bytes()
    assert data[10:12] == b"\0\0"
    decoded = nwt.read_container(data)
    assert [plain(r) for r in decoded] == [plain(r) for r in nwt.CATALOG]
    assert nwt.report(decoded) == (KIT / "fixtures/all-fields.txt").read_text()
    publishers = [{"id": 1, "name": "Example Feed", "venue": "EXAMPLE"}]
    assert nwt.build_manifest("EXAMPLE.ALL", "nwt-developer-kit/1.0-draft.2", publishers, range(1, 10)) == nwt.MANIFEST


def test_crc_vectors():
    assert nwt.crc(b"123456789") == 0xE3069283
    assert nwt.crc(b"") == 0
    assert nwt.crc(bytes(32)) == 0x8A9136AA  # RFC 3720 B.4
    assert nwt.crc(bytes([255] * 32)) == 0x62A8AB43
    assert nwt.crc(bytes(range(32))) == 0x46DD794E


def test_sizes():
    assert nwt.SCHEMA["revision"] == "1.1-draft.1"
    assert sorted(nwt.S) == list(range(1, 23))
    for typ, text in LAYOUT.items():
        schema = nwt.S[typ]
        want = [(n, int(o), int(b)) for n, o, b in (x.split(":") for x in text.split())]
        assert body_offsets(typ) == want, typ
        assert schema["name"] == NAMES[typ] and schema["version"] == 1
        assert schema["fixed_bytes"] == FIXED[typ] == want[-1][1] + want[-1][2]
        assert schema["texts"] == TEXTS.get(typ, "").split() and schema["has_levels"] is False
        signed = {f["name"] for f in schema["fields"] if f["signed"]}
        assert signed == set(SIGNED.get(typ, "").split()), typ
        length_fields = [f["name"] for f in schema["fields"] if f["name"].endswith("_bytes") and typ != 20]
        assert length_fields == [name + "_bytes" for name in schema["texts"]], typ
    for typ, schema in nwt.S.items():
        for key in RULE_KEYS:
            assert schema.get(key, {}) == RULES.get(typ, {}).get(key, {}), (typ, key)
        for f in schema["fields"] + nwt.SCHEMA["header"] + nwt.SCHEMA["level"]:
            kind = f.get("kind")
            assert kind in (None, "price", "quantity", "time"), f
            if kind:
                assert f["bytes"] == 8 and f["signed"] == (kind == "price"), f
            name = f["name"]
            if name in ("ts_event", "ts_recv") or (name.endswith("_ns") and name != "interval_ns"):
                assert kind == "time", (typ, name)
            if name.endswith("price") or name in ("strike", "contract_multiplier", "open", "high", "low", "close"):
                assert kind == "price", (typ, name)
            if name.endswith("quantity") or name in ("volume", "quantity_increment"):
                assert kind == "quantity", (typ, name)
    assert all(f.get("kind") == "price" for f in nwt.S[14]["fields"][:8])

    assert [(r["label"], r["type"], int(r["fields"]["instrument_id"])) for r in nwt.CATALOG_V11] == SCENARIOS
    assert [r["label"] for r in nwt.CATALOG_V11 if r.get("standalone")] == ["frame-summary"]
    scopes = {}
    for record in nwt.CATALOG_V11:
        f = record["fields"]
        typ = record["type"]
        encoded = nwt.encode_record(record)
        text_bytes = sum(len(t.encode()) for t in record["texts"].values())
        if typ in FIXED:
            want = (FIXED[typ] + text_bytes + 7) & ~7
            assert len(encoded) == want == int(f["record_bytes"]), record["label"]
            if not nwt.S[typ]["texts"]:
                assert len(encoded) == FIXED[typ]
        scope = (f["publisher_id"], f["channel_id"])
        assert int(f["sequence"]) == scopes.get(scope, 0) + 1, record["label"]
        scopes[scope] = int(f["sequence"])
        assert scope == (("0", "0") if record["label"] in ("system-heartbeat", "frame-summary") else ("1", "0"))
    assert set(r["type"] for r in nwt.CATALOG_V11) == set(range(1, 23))
    # Decision recorded in fixtures/v1.1/FORMAT-NOTES.md: STATISTICS ts_ref is a timestamp.
    assert nwt.S[13]["fields"][0]["name"] == "ts_ref" and nwt.S[13]["fields"][0]["kind"] == "time"
    assert "kind" not in nwt.S[19]["fields"][-1] and "kind" not in nwt.S[12]["fields"][0]  # interval_ns, round_lot


def test_round_trip_v11():
    for record in nwt.CATALOG_V11:
        encoded = nwt.encode_record(record)
        assert encoded == raw_encode(record), record["label"]
        decoded = nwt.decode_record(encoded)
        assert decoded == plain(record), record["label"]
        assert nwt.encode_record(decoded) == encoded
    data = v11_bytes()
    assert [plain(r) for r in nwt.read_container(data)] == [plain(r) for r in file_records()]


def test_enum_mask_rejects():
    checked = 0
    for typ, schema in nwt.S.items():
        good = example(typ)
        positions = {name: (offset, width) for name, offset, width in body_offsets(typ)}
        encoded = nwt.encode_record(good)
        for name, allowed in schema.get("enums", {}).items():
            offset, width = positions[name]
            for value in allowed:
                patched = bytearray(encoded)
                nwt.put(patched, offset, width, value)
                assert nwt.decode_record(bytes(patched))["fields"][name] == str(value)
            for value in (max(allowed) + 1, (1 << 8 * width) - 1, *([0] if 0 not in allowed else [])):
                bad = copy.deepcopy(good)
                bad["fields"][name] = str(value)
                raises(nwt.encode_record, bad, contains=name)
                patched = bytearray(encoded)
                nwt.put(patched, offset, width, value)
                raises(nwt.decode_record, bytes(patched), contains=name)
                checked += 1
        for name, mask in schema.get("masks", {}).items():
            offset, width = positions[name]
            patched = bytearray(encoded)
            nwt.put(patched, offset, width, mask)
            assert nwt.decode_record(bytes(patched))["fields"][name] == str(mask)
            for bit in range(8 * width):
                if mask >> bit & 1:
                    continue
                bad = copy.deepcopy(good)
                bad["fields"][name] = str(1 << bit)
                raises(nwt.encode_record, bad, contains=name)
                patched = bytearray(encoded)
                nwt.put(patched, offset, width, mask | 1 << bit)
                raises(nwt.decode_record, bytes(patched), contains=name)
                checked += 1
    assert checked > 100
    for typ in range(1, 10):  # legacy types gained no enum or mask checks
        assert "enums" not in nwt.S[typ] and "masks" not in nwt.S[typ]


def test_text_limits_bytes():
    venue = scenario("venue-segment-unicode")
    name = "é" * 127 + "X"
    assert venue["texts"]["name"] == name and len(name) == 128 and len(name.encode()) == 255
    assert nwt.decode_record(nwt.encode_record(venue))["texts"]["name"] == name
    too_long = set_text(copy.deepcopy(venue), "name", name + "Y")
    raises(nwt.encode_record, too_long, contains="name")
    raises(nwt.decode_record, raw_encode(too_long), contains="name")
    # 128 two-byte characters are 256 bytes: over the limit although under 255 characters.
    raises(nwt.encode_record, set_text(copy.deepcopy(venue), "name", "é" * 128), contains="name")

    for typ, schema in nwt.S.items():
        cases = [(n, lo, hi, [lo, hi], [lo - 1, hi + 1]) for n, (lo, hi) in schema.get("text_limits", {}).items()]
        for n, allowed in schema.get("text_exact", {}).items():
            bad = [x for x in range(max(allowed) + 2) if x not in allowed]
            cases.append((n, min(allowed), max(allowed), allowed, [bad[0], bad[-2], bad[-1]]))
        for name, _, _, good_sizes, bad_sizes in cases:
            for size in good_sizes:
                record = set_text(example(typ), name, "A" * size)
                assert nwt.decode_record(nwt.encode_record(record))["texts"][name] == "A" * size
            for size in bad_sizes:
                if size < 0:
                    continue
                record = set_text(example(typ), name, "A" * size)
                raises(nwt.encode_record, record, contains=name)
                if size <= 65535:  # a longer text has no wire form: its u16 length field cannot hold it
                    raises(nwt.decode_record, raw_encode(record), contains=name)
    # NUL and malformed UTF-8 stay rejected.
    raises(nwt.encode_record, set_text(example(17), "symbol", "A\0B"))
    encoded = bytearray(nwt.encode_record(example(17)))
    encoded[72] = 0xFF
    try:
        nwt.decode_record(bytes(encoded))
    except ValueError:  # UnicodeDecodeError is a ValueError
        pass
    else:
        raise AssertionError("invalid UTF-8 accepted")


def test_reserved_rejects():
    checked = 0
    for typ in nwt.S:
        good = example(typ)
        encoded = nwt.encode_record(good)
        reserved = [(o, w) for name, o, w in body_offsets(typ) if name == "reserved"]
        for offset, width in reserved:
            for byte in range(width):  # every byte of every reserved field
                patched = bytearray(encoded)
                patched[offset + byte] = 1
                raises(nwt.decode_record, bytes(patched), contains="reserved")
                checked += 1
        if reserved:
            bad = copy.deepcopy(good)
            bad["fields"]["reserved"] = "1"
            raises(nwt.encode_record, bad, contains="reserved")
    assert len([1 for n, _, _ in body_offsets(12) if n == "reserved"]) == 2
    book = example(5)
    assert book["levels"]
    encoded = bytearray(nwt.encode_record(book))
    encoded[56 + 40] = 1  # first level's reserved
    raises(nwt.decode_record, bytes(encoded), contains="reserved")
    book["levels"][0]["reserved"] = "1"
    raises(nwt.encode_record, book, contains="reserved")
    assert checked >= 60


def test_minor_rule():
    legacy = nwt.write_container(nwt.CATALOG)
    current = v11_bytes()
    assert legacy[10:12] == b"\0\0" and current[10:12] == b"\1\0"
    assert reader_for(legacy).header["minor"] == 0 and reader_for(current).header["minor"] == 1
    for data, minor in ((legacy, 1), (current, 0), (current, 2)):
        head = bytearray(data[:64])
        nwt.put(head, 10, 2, minor)
        raises(nwt.read_container, nwt.hcrc(head, 56) + data[64:], contains="minor")
    # A manifest that declares type 10 or above makes minor 1 even when no such record is written.
    only_legacy = nwt.write_container(nwt.CATALOG, nwt.MANIFEST_V11)
    assert only_legacy[10:12] == b"\1\0"
    assert len(nwt.read_container(only_legacy)) == len(nwt.CATALOG)


def test_manifest_checks():
    manifest = nwt.parse_manifest(nwt.MANIFEST_V11)
    assert manifest["dataset"] == "EXAMPLE.V11" and manifest["producer"] == "nwt-developer-kit/1.1-draft.1"
    assert manifest["publishers"] == [
        {"id": 1, "name": "Example Feed", "venue": "EXAMPLE"},
        {"id": 2, "name": "Second Venue", "venue": "EXAMPLE2"},
    ]
    assert [s["type"] for s in manifest["schemas"]] == list(range(1, 23))
    for s in manifest["schemas"]:
        typ = s["type"]
        assert s["required"] is (typ <= 9 or typ == 15) and s["version"] == 1
        assert s["name"] == nwt.S[typ]["name"]
        assert s["spec_uri"] == ("urn:nwt:spec:1.0" if typ <= 9 else "urn:nwt:spec:1.1")
    assert nwt.build_manifest(manifest["dataset"], manifest["producer"], manifest["publishers"], range(1, 23)) == nwt.MANIFEST_V11
    assert nwt.MANIFEST_V11 == (KIT / "fixtures/manifest-v1.1.json").read_text().strip()

    base = json.loads(nwt.MANIFEST_V11)

    def text(change):
        m = copy.deepcopy(base)
        change(m)
        return json.dumps(m, separators=(",", ":"))

    for key in ("dataset", "producer", "profile", "publishers", "schemas", "clock"):
        raises(nwt.parse_manifest, text(lambda m: m.pop(key)), contains=key)
    raises(nwt.parse_manifest, text(lambda m: m.update(profile="other")), contains="profile")
    raises(nwt.parse_manifest, text(lambda m: m.update(clock="utc")), contains="clock")
    raises(nwt.parse_manifest, text(lambda m: m.update(ordering="price")), contains="ordering")
    raises(nwt.parse_manifest, text(lambda m: m["schemas"].append(dict(m["schemas"][0]))), contains="duplicate")
    raises(nwt.parse_manifest, text(lambda m: m["publishers"].append(dict(m["publishers"][0]))), contains="publisher")
    raises(nwt.parse_manifest, text(lambda m: m.update(schemas=[])), contains="schemas")
    raises(nwt.parse_manifest, nwt.MANIFEST_V11[:-1] + ',"dataset":"again"}', contains="duplicate")
    raises(nwt.parse_manifest, "[]")
    raises(nwt.parse_manifest, "{")
    for ordering in ("none", "ts_event", "instrument,ts_event"):
        assert nwt.parse_manifest(text(lambda m: m.update(ordering=ordering)))["ordering"] == ordering
        built = nwt.build_manifest("D", "P", base["publishers"], [1, 6], ordering=ordering)
        assert nwt.parse_manifest(built)["ordering"] == ordering
    assert "ordering" not in nwt.parse_manifest(nwt.build_manifest("D", "P", [], [9]))
    assert nwt.parse_manifest(text(lambda m: m.update(future_property={"x": 1})))["dataset"] == "EXAMPLE.V11"
    generic = nwt.parse_manifest(nwt.build_manifest("D", "P", [], [8, 9, 20], profile="generic-events"))
    assert generic["profile"] == "generic-events"

    # Undeclared type and publisher: refused by the writer and by the reader.
    records = file_records()
    without_13 = nwt.build_manifest("D", "P", base["publishers"], [t for t in range(1, 23) if t != 13])
    raises(nwt.write_container, records, without_13, V11_ID, contains="undeclared record type")
    without_pub = nwt.build_manifest("D", "P", base["publishers"][1:], range(1, 23))
    raises(nwt.write_container, records, without_pub, V11_ID, contains="undeclared publisher")
    data = v11_bytes()
    raises(nwt.read_container, replace_metadata_text(data, b'"type":13,', b'"type":99,'), contains="undeclared record type")
    raises(nwt.read_container, replace_metadata_text(data, b'{"id":1,', b'{"id":3,'), contains="undeclared publisher")
    # Publisher 0 (system scope) needs no declaration.
    heartbeat = scenario("system-heartbeat")
    assert len(nwt.read_container(nwt.write_container([heartbeat], nwt.build_manifest("D", "P", [], [9])))) == 1

    # Metadata TLV rules.
    m = nwt.MANIFEST.encode()
    provenance = b'{"source_format":"synthetic"}'
    ok = reader_for(with_metadata(tlv(1, 1, m) + tlv(2, 0, provenance) + tlv(40000, 0, b"private")))
    assert ok.provenance == {"source_format": "synthetic"} and ok.manifest["dataset"] == "EXAMPLE.ALL"
    assert reader_for(with_metadata(tlv(1, 1, m))).provenance is None
    assert list(ok.frames())[-1][0].kind == 3
    for bad, why in [
        (tlv(1, 0, m), "MANIFEST"),  # REQUIRED bit clear
        (tlv(2, 0, provenance), "MANIFEST"),  # no manifest at all
        (tlv(1, 1, m) + tlv(1, 1, m), "duplicate"),
        (tlv(1, 1, m) + tlv(40000, 0, b"a") + tlv(40000, 0, b"b"), "duplicate"),
        (tlv(1, 1, m) + tlv(40000, 1, b"must understand"), "required"),
        (tlv(1, 1, m) + tlv(2, 1, provenance), "PROVENANCE"),
        (tlv(1, 1, m) + tlv(2, 0, b"[]"), "PROVENANCE"),
        (tlv(1, 1, m) + tlv(0, 0, b""), "TLV"),
        (tlv(1, 1, m) + tlv(65535, 0, b""), "TLV"),
        (tlv(1, 1, m) + tlv(40000, 2, b""), "TLV"),
        (tlv(1, 1, m) + struct.pack("<HHI", 40000, 0, 64), "TLV"),  # value runs past the metadata
        (tlv(1, 1, m) + bytes(8), "TLV"),  # padding where an element must start
        (tlv(1, 1, m)[:-1] + b"\1" if len(m) % 8 else tlv(1, 1, m + b" ")[:-1] + b"\1", "TLV"),  # non-zero padding
    ]:
        raises(reader_for, with_metadata(bad), contains=why)


def test_zstd_round_trip():
    if not nwt.zstd_available():
        print("  notice: Zstd library not found; test_zstd_round_trip skipped")
        return "skipped"
    rng = random.Random(7)
    for payload in (b"A", bytes(1000), rng.randbytes(5000), b"NWT " * 50000):
        packed = nwt.zstd_compress(payload)
        assert nwt.zstd_decompress(packed, len(payload)) == payload
    assert len(nwt.zstd_compress(bytes(1 << 20), 19)) < 200

    raw = v11_bytes()
    packed = v11_bytes(zstd_level=3)
    codecs = [codec for _, kind, codec, _, _ in frame_table(packed) if kind == 1]
    assert 1 in codecs and len(codecs) == 16
    assert all(codec == 0 for _, kind, codec, _, _ in frame_table(packed) if kind != 1)
    assert len(packed) < len(raw)
    decoded = nwt.read_container(packed)
    assert nwt.report(decoded) == nwt.report(nwt.read_container(raw))
    assert nwt.write_container(decoded, nwt.MANIFEST_V11, V11_ID, V11_CREATED) == raw

    # A frame that does not shrink is stored raw.
    out = io.BytesIO()
    writer = nwt.Writer(out, nwt.MANIFEST_V11, V11_ID, zstd_level=3)
    noise = rng.randbytes(4096)
    assert writer.store(noise) == (0, noise)
    assert writer.store(bytes(4096))[0] == 1

    # One big frame: the stored payload is one standard Zstd frame that the zstd command also decodes.
    many = renumber(file_records() * 200)
    out = io.BytesIO()
    writer = nwt.Writer(out, nwt.MANIFEST_V11, V11_ID, V11_CREATED, zstd_level=3)
    for record in many:
        writer.write(record)
    writer.close()
    big = out.getvalue()
    offset, kind, codec, stored, raw_size = frame_table(big)[0]
    assert (kind, codec) == (1, 1) and stored < raw_size // 4 and raw_size > 500000
    count = int.from_bytes(big[offset + 20 : offset + 24], "little")
    payload = b"".join(nwt.encode_record(r) for r in many[:count])
    assert raw_size == len(payload)
    assert [plain(r) for r in nwt.read_container(big)] == [plain(r) for r in many]
    if shutil.which("zstd"):
        tool = subprocess.run(["zstd", "-d", "-c"], input=big[offset + 64 : offset + 64 + stored], capture_output=True)
        assert tool.returncode == 0 and tool.stdout == payload
    else:
        print("  notice: zstd command not found; command-line cross-check skipped")


def test_zstd_header_rules():
    def fcs4(packed, window_byte=None, size=None):
        """Rewrite a single-segment frame header with a 4-byte content size and optional window byte."""
        d = packed[4]
        assert d & 0x20 and not d & 0x0F
        n = (1, 2, 4, 8)[d >> 6]
        value = int.from_bytes(packed[5 : 5 + n], "little") + (256 if d >> 6 == 1 else 0)
        size = value if size is None else size
        if window_byte is None:
            return packed[:4] + bytes([0xA0]) + size.to_bytes(4, "little") + packed[5 + n :]
        return packed[:4] + bytes([0x80, window_byte]) + size.to_bytes(4, "little") + packed[5 + n :]

    payload = b"NWT frame payload " * 400
    n = len(payload)
    fake = b"\x28\xb5\x2f\xfd\xa0" + n.to_bytes(4, "little") + bytes(8)  # header only; never decompressed
    # The header rules are checked by hand, so they hold even without the library.
    raises(nwt.zstd_check, fake, n + 1, contains="content size")
    raises(nwt.zstd_check, b"\x50\x2a\x4d\x18" + fake[4:], n, contains="magic")  # skippable frame
    raises(nwt.zstd_check, fake[:4], n, contains="magic")
    raises(nwt.zstd_check, fake[:4] + bytes([0xA1]) + fake[5:], n, contains="dictionary")
    raises(nwt.zstd_check, fake[:4] + bytes([0xA8]) + fake[5:], n, contains="reserved")
    raises(nwt.zstd_check, fake[:4] + bytes([0x00, 0x50]) + fake[5:], n, contains="content size")  # size absent
    raises(nwt.zstd_check, fake[:4] + bytes([0x80, 0x78]) + n.to_bytes(4, "little"), n, contains="window")  # 32 MiB
    raises(nwt.zstd_check, fake[:4] + bytes([0x80, 0x71]) + n.to_bytes(4, "little"), n, contains="window")  # 18 MiB
    raises(nwt.zstd_check, fake[:7], n, contains="header")
    nwt.zstd_check(fake, n)
    nwt.zstd_check(fake[:4] + bytes([0xA4]) + fake[5:], n)  # content checksum flag is allowed
    nwt.zstd_check(fake[:4] + bytes([0x80, 0x70]) + n.to_bytes(4, "little"), n)  # exactly 16 MiB window
    big = 16777216
    nwt.zstd_check(fake[:4] + bytes([0xA0]) + big.to_bytes(4, "little"), big)
    raises(nwt.zstd_check, fake[:4] + bytes([0xA0]) + (big + 1).to_bytes(4, "little"), big + 1, contains="window")

    if not nwt.zstd_available():
        print("  notice: Zstd library not found; decompression half of test_zstd_header_rules skipped")
        return "skipped"
    packed = nwt.zstd_compress(payload)
    assert nwt.zstd_decompress(packed, n) == payload
    assert nwt.zstd_decompress(fcs4(packed), n) == payload  # same blocks, 4-byte size field
    assert nwt.zstd_decompress(fcs4(packed, window_byte=0x70), n) == payload  # 16 MiB window
    raises(nwt.zstd_decompress, packed, n + 1, contains="content size")
    raises(nwt.zstd_decompress, fcs4(packed, size=n + 1), n + 1)  # header lies about the size
    raises(nwt.zstd_decompress, fcs4(packed, window_byte=0x78), n, contains="window")
    raises(nwt.zstd_decompress, packed[:4] + bytes([packed[4] | 1]) + packed[5:], n, contains="dictionary")
    raises(nwt.zstd_decompress, b"\x50\x2a\x4d\x18" + packed[4:], n, contains="magic")
    raises(nwt.zstd_decompress, packed + b"\0", n)  # trailing byte
    raises(nwt.zstd_decompress, packed + packed, n)  # concatenated frames
    raises(nwt.zstd_decompress, packed[:-1], n)  # truncated frame
    skippable = b"\x50\x2a\x4d\x18" + (4).to_bytes(4, "little") + b"skip"
    raises(nwt.zstd_decompress, packed + skippable, n)
    if shutil.which("zstd"):  # a frame with Zstd's own content checksum is valid (spec 10.2)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "payload").write_bytes(payload)
            checked = subprocess.run(["zstd", "-c", "--check", str(Path(tmp) / "payload")], capture_output=True).stdout
        assert checked[4] & 0x04
        assert nwt.zstd_decompress(checked, n) == payload
    # In a container: a frame that says codec 1 but holds raw bytes is rejected.
    data = bytearray(v11_bytes())
    at = frame_table(bytes(data))[0][0]
    data[at + 6] = 1
    data[at : at + 64] = nwt.hcrc(data[at : at + 64], 52)
    raises(nwt.read_container, bytes(data), contains="Zstd")


def test_zstd_missing():
    env = dict(os.environ, NWT_ZSTD_LIB="/nonexistent")
    packed = run("read", GOLDEN / "all-records.zst.nwt", env=env)
    assert packed.returncode != 0 and b"Zstd library not available" in packed.stderr, packed.stderr
    raw = run("read", GOLDEN / "all-records.nwt", env=env)
    assert raw.returncode == 0 and raw.stdout == (GOLDEN / "all-fields.txt").read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        refused = run("write-v11", Path(tmp) / "x.nwt", "--zstd", env=env)
        assert refused.returncode != 0 and b"Zstd library not available" in refused.stderr
    probe = "import nwt_example as n; print(n.zstd_available())"
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, env=env, cwd=KIT / "examples/python")
    assert result.stdout.strip() == b"False", result


def test_writer_reader_stream():
    records = renumber(file_records() * 20)
    provenance = '{"source_format":"synthetic","converter":"test"}'
    out = io.BytesIO()
    writer = nwt.Writer(out, nwt.MANIFEST_V11, V11_ID, V11_CREATED, provenance=provenance, frame_bytes=1024)
    for record in records[:10]:
        writer.write(record)
    for record in records[10:]:
        writer.write_raw(nwt.encode_record(record))
    writer.close()
    data = out.getvalue()

    reads = []

    def read_at(offset, n):
        reads.append((offset, n))
        return data[offset : offset + n]

    reader = nwt.Reader(read_at, len(data))
    assert reader.header["minor"] == 1 and reader.header["stream_id"] == V11_ID
    assert reader.header["created_ns"] == V11_CREATED and reader.header["major"] == 1
    assert reader.manifest == json.loads(nwt.MANIFEST_V11) and reader.provenance == json.loads(provenance)
    assert reader.metadata == data[64 : 64 + len(reader.metadata)] and len(reader.metadata) % 8 == 0
    scanned = list(reader.frames())
    assert [info.seq for info, _ in scanned] == list(range(len(scanned)))
    assert writer.frames == [info for info, _ in scanned if info.kind == 1]  # the writer's own frame table
    assert [info.kind for info, _ in scanned[-2:]] == [2, 3] and not scanned[-1][1]
    data_frames = [(info, raws) for info, raws in scanned if info.kind == 1]
    assert len(data_frames) > 50
    assert b"".join(b"".join(raws) for _, raws in data_frames) == b"".join(nwt.encode_record(r) for r in records)
    assert [plain(r) for r in reader.records()] == [plain(r) for r in records]
    for info, raws in data_frames:
        assert info.raw_bytes == sum(map(len, raws)) and info.record_count == len(raws)
        assert info.raw_bytes <= 1024 or len(raws) == 1
        times = [t for t in (nwt.get(raw, 24, 8) for raw in raws) if t != nwt.NULL]
        assert (info.min_event_ns, info.max_event_ns) == ((min(times), max(times)) if times else (nwt.NULL, nwt.NULL))

    reads.clear()
    index = reader.index()
    assert reads[0] == (len(data) - 96, 64)  # the seek path starts at END
    assert len(index) == len(data_frames)
    for entry, (info, raws) in zip(index, data_frames):
        assert entry.kind == 1
        for key in ("seq", "offset", "raw_bytes", "record_count", "min_event_ns", "max_event_ns"):
            assert getattr(entry, key) == getattr(info, key), key
        assert reader.read_frame(entry) == raws == reader.read_frame(info)
    reads.clear()
    reader.read_frame(index[7])
    assert sum(n for _, n in reads) < 1200  # one frame, not the file

    # frame_records closes a frame by count.
    by_count = nwt.write_container(records, nwt.MANIFEST_V11, V11_ID, V11_CREATED, frame_records=7)
    counts = [info.record_count for info, _ in reader_for(by_count).frames() if info.kind == 1]
    assert counts == [7] * (len(records) // 7) + ([len(records) % 7] if len(records) % 7 else [])

    # An empty container is metadata then END, with no INDEX.
    empty = nwt.write_container([], nwt.MANIFEST_V11, V11_ID, V11_CREATED)
    assert len(empty) == 64 + len(reader_for(empty).metadata) + 96
    assert [info.kind for info, _ in reader_for(empty).frames()] == [3] and reader_for(empty).index() == []

    # Truncation is "incomplete" on both paths, wherever the cut falls.
    first = data_frames[0][0].offset
    for cut in (0, 10, 64, 70, first, first + 10, first + 64, first + 70, scanned[-2][0].offset, len(data) - 96, len(data) - 1):
        short = data[:cut]
        raises(lambda: list(reader_for(short).frames()), contains="incomplete")
        raises(lambda: list(reader_for(short).records()), contains="incomplete")
        raises(lambda: reader_for(short).index(), contains="incomplete")
        raises(nwt.read_container, short, contains="incomplete")
    raises(nwt.read_container, data + b"\0", contains="trailing")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cut file.nwt"
        path.write_bytes(data[: first + 100])
        result = run("read", path)
        assert result.returncode != 0 and b"incomplete" in result.stderr and not result.stdout

    # Writer refuses a sequence gap; an aborted END is readable but not a normal completion.
    out = io.BytesIO()
    writer = nwt.Writer(out, nwt.MANIFEST_V11, V11_ID)
    writer.write(records[0])
    raises(writer.write, records[2], contains="sequence")
    writer.close(status=1)
    aborted = reader_for(out.getvalue())
    assert len(list(aborted.records())) == 1 and aborted.end["status"] == 1
    raises(nwt.read_container, out.getvalue(), contains="aborted")
    raises(nwt.Writer, io.BytesIO(), nwt.MANIFEST_V11, bytes(16), contains="stream ID")

    sequencer = nwt.Sequencer()
    assert [sequencer.next(1, 0), sequencer.next(1, 0), sequencer.next(1, 1), sequencer.next(0, 0), sequencer.next(1, 0)] == [1, 2, 1, 1, 3]


def test_pretty():
    assert nwt.pretty_decimal(-500000000) == "-0.500000000"
    assert nwt.pretty_time(1758020700000000000) == "2025-09-16T11:05:00.000000000Z"
    for value, want in [
        (0, "0.000000000"), (1, "0.000000001"), (-1, "-0.000000001"), (177339000000, "177.339000000"),
        ((1 << 63) - 1, "9223372036.854775807"), (-(1 << 63) + 1, "-9223372036.854775807"),
        ((1 << 64) - 2, "18446744073.709551614"),
    ]:  # fmt: skip
        assert nwt.pretty_decimal(value) == want
    for value, want in [
        (0, "1970-01-01T00:00:00.000000000Z"), (1, "1970-01-01T00:00:00.000000001Z"),
        (951782399999999999, "2000-02-28T23:59:59.999999999Z"), (951782400000000000, "2000-02-29T00:00:00.000000000Z"),
        (4107542400000000000, "2100-03-01T00:00:00.000000000Z"), (1760000000000008100, "2025-10-09T08:53:20.000008100Z"),
        ((1 << 64) - 2, "2554-07-21T23:34:33.709551614Z"),
    ]:  # fmt: skip
        assert nwt.pretty_time(value) == want, value
    rng = random.Random(3)
    for _ in range(2000):
        ns = rng.randrange(1 << 64)
        moment = datetime(1970, 1, 1) + timedelta(seconds=ns // 10**9)
        assert nwt.pretty_time(ns) == moment.strftime("%Y-%m-%dT%H:%M:%S") + f".{ns % 10**9:09}Z"

    minimal = scenario("listing-minimal")
    line = nwt.to_json_line(minimal, pretty=True)
    assert '"ts_event":null,"ts_recv":null,' in line
    assert '"round_lot":"4294967295"' in line  # no kind: left as the stored integer
    assert '"ts_event":"18446744073709551615"' in nwt.to_json_line(minimal)
    assert nwt.to_csv_line(minimal, pretty=True).split(",")[7:9] == ["", ""]
    trade = scenario("trade-new")
    trade["fields"].update(price=str(-500000000), quantity=str((1 << 64) - 1), ts_event="1758020700000000000")
    line = nwt.to_json_line(trade, pretty=True)
    assert '"ts_event":"2025-09-16T11:05:00.000000000Z"' in line
    assert '"price":"-0.500000000","quantity":null,"trade_id":"1"' in line
    trade["fields"]["price"] = str(-(1 << 63))
    assert '"price":null' in nwt.to_json_line(trade, pretty=True)
    assert f'"price":"{-(1 << 63)}"' in nwt.to_json_line(trade)
    book = json.loads(nwt.to_json_line(scenario("book-snapshot"), pretty=True))
    assert book["levels"][0]["bid_price"] == "149.240000000" and book["levels"][0]["bid_count"] == "2"
    unknowns = json.loads(nwt.to_json_line(scenario("option-def-unknowns"), pretty=True))
    assert unknowns["contract_multiplier"] is None and unknowns["strike"] == "12.500000000"
    assert unknowns["expiration_ns"] == "2026-01-16T21:00:00.000000000Z"


def test_json_csv_escaping():
    record = scenario("listing-awkward-text")
    assert record["texts"]["name"] == AWKWARD
    head = (
        '{"type_name":"LISTING","record_bytes":"128","record_type":"12","schema_version":"1","flags":"0",'
        '"publisher_id":"1","channel_id":"0","instrument_id":"2006",'
    )
    tail = (
        '"sequence":"9","round_lot":"10","listing_flags":"2","market_tier":"0","financial_flags":"0",'
        '"symbol_bytes":"4","name_bytes":"40","listing_mic_bytes":"0","cqs_symbol_bytes":"5","alt_symbol_bytes":"0",'
        '"symbol":"AWKW","name":"Awkward, \\"Quoted\\" \\\\ Name\\u000aLine two\\u0001 café",'
        '"listing_mic":"","cqs_symbol":"AWK.W","alt_symbol":""}'
    )
    assert nwt.to_json_line(record) == head + '"ts_event":"18446744073709551615","ts_recv":"1760000000000008100",' + tail
    assert nwt.to_json_line(record, pretty=True) == head + '"ts_event":null,"ts_recv":"2025-10-09T08:53:20.000008100Z",' + tail
    assert json.loads(nwt.to_json_line(record))["name"] == AWKWARD

    assert nwt.csv_header(12) == (
        "record_bytes,record_type,schema_version,flags,publisher_id,channel_id,instrument_id,ts_event,ts_recv,"
        "sequence,round_lot,listing_flags,market_tier,financial_flags,symbol_bytes,name_bytes,listing_mic_bytes,"
        "cqs_symbol_bytes,alt_symbol_bytes,symbol,name,listing_mic,cqs_symbol,alt_symbol"
    )
    quoted = '"Awkward, ""Quoted"" \\ Name\nLine two\x01 café"'
    assert nwt.to_csv_line(record) == (
        "128,12,1,0,1,0,2006,18446744073709551615,1760000000000008100,9,10,2,0,0,4,40,0,5,0,AWKW," + quoted + ",,AWK.W,"
    )
    assert nwt.to_csv_line(record, pretty=True) == (
        "128,12,1,0,1,0,2006,,2025-10-09T08:53:20.000008100Z,9,10,2,0,0,4,40,0,5,0,AWKW," + quoted + ",,AWK.W,"
    )
    assert nwt.csv_value('say "hi"') == '"say ""hi"""' and nwt.csv_value("a\rb") == '"a\rb"'
    assert nwt.csv_value("plain text; no quoting\t") == "plain text; no quoting\t" and nwt.csv_value(None) == ""
    assert nwt.json_string('\x00\x1f\x20\x7f"\\/é\U0001d11e') == '"\\u0000\\u001f \x7f\\"\\\\/é\U0001d11e"'

    # Key order: type_name, header, body, texts, levels; never "reserved"; no spaces.
    for record in list(nwt.CATALOG) + list(nwt.CATALOG_V11):
        schema = nwt.S[record["type"]]
        for pretty in (False, True):
            line = nwt.to_json_line(record, pretty)
            assert "\n" not in line and "\r" not in line
            pairs = json.loads(line, object_pairs_hook=list)
            names = [f["name"] for f in nwt.SCHEMA["header"] + schema["fields"] if f["name"] != "reserved"]
            if schema["has_levels"]:
                names.remove("levels")
            want = ["type_name"] + names + schema["texts"] + (["levels"] if schema["has_levels"] else [])
            assert [key for key, _ in pairs] == want, record["label"]
            values = dict(pairs)
            assert values["type_name"] == schema["name"]
            if not pretty:
                assert all(values[name] == record["fields"][name] for name in names)
                assert all(values[name] == record["texts"][name] for name in schema["texts"])
            if schema["has_levels"]:
                level_names = [f["name"] for f in nwt.SCHEMA["level"] if f["name"] != "reserved"]
                assert all([key for key, _ in level] == level_names for level in values["levels"])
                assert len(values["levels"]) == len(record["levels"])
            else:
                assert nwt.csv_header(record["type"]).split(",") == names + schema["texts"]
                assert nwt.to_csv_line(record, pretty).count(",") >= len(names) + len(schema["texts"]) - 1
    raises(nwt.csv_header, 5, contains="to-json")
    raises(nwt.to_csv_line, scenario("book-snapshot"), contains="to-json")


def random_text(rng, sizes):
    pool = 'ABCxyz019 ,"\\\n\r\x01\x7fé€日\U0001d11e'
    target = rng.choice(sizes)
    out, size = "", 0
    while True:
        ch = rng.choice(pool)
        width = len(ch.encode())
        if size + width > target or len(out) >= 64:  # long texts: 64 mixed characters, then plain filler
            return out + "A" * (target - size)
        out += ch
        size += width


def random_int(rng, f):
    bits = 8 * f["bytes"]
    lo, hi = (-(1 << bits - 1), (1 << bits - 1) - 1) if f["signed"] else (0, (1 << bits) - 1)
    return rng.choice([lo, hi, 0, rng.randint(lo, hi), rng.randint(lo, hi)])


def random_record(rng, typ, sequence):
    schema = nwt.S[typ]
    enums, masks = schema.get("enums", {}), schema.get("masks", {})
    texts = {}
    for name in schema["texts"]:
        if name in schema.get("text_exact", {}):
            sizes = schema["text_exact"][name]
        else:
            lo, hi = schema["text_limits"][name]
            sizes = [lo, hi, rng.randint(lo, hi), rng.randint(lo, min(hi, lo + 12))]
        texts[name] = random_text(rng, sizes)
    body = {}
    for f in schema["fields"]:
        name = f["name"]
        if name == "reserved" or name[:-6] in texts or (schema["has_levels"] and name == "levels"):
            continue
        if name in enums:
            body[name] = rng.choice(enums[name])
        elif name in masks:
            body[name] = rng.getrandbits(8 * f["bytes"]) & masks[name]
        else:
            body[name] = random_int(rng, f)
    levels = None
    if schema["has_levels"]:
        levels = [
            {f["name"]: random_int(rng, f) for f in nwt.SCHEMA["level"] if f["name"] != "reserved"}
            for _ in range(rng.choice([0, 1, 2, 5, rng.randint(0, 40)]))
        ]
    header = {f["name"]: random_int(rng, f) for f in nwt.SCHEMA["header"][4:9]}
    return nwt.make_record(typ, sequence=sequence, flags=rng.randrange(4), texts=texts, levels=levels, **header, **body)


def test_random_round_trip():
    rng = random.Random(20261013)
    total = 0
    for typ in sorted(nwt.S):
        schema = nwt.S[typ]
        for i in range(2000):
            record = random_record(rng, typ, i + 1)
            encoded = nwt.encode_record(record)
            assert len(encoded) % 8 == 0 and len(encoded) == int(record["fields"]["record_bytes"])
            decoded = nwt.decode_record(encoded)
            assert decoded == record, (typ, i)
            if i % 20 == 0:
                assert encoded == raw_encode(record)
                assert json.loads(nwt.to_json_line(record))["sequence"] == str(i + 1)
                json.loads(nwt.to_json_line(record, pretty=True))
                if not schema["has_levels"]:
                    nwt.to_csv_line(record, pretty=True)
            total += 1
    assert total == 44000


def test_make_record():
    made = nwt.make_record(
        15, instrument_id=2001, ts_event=5, sequence=3, price=-1, quantity=2, order_count=nwt.NULL_U32,
        action=1, side=2, delta_flags=1,
    )  # fmt: skip
    assert made["type"] == 15 and made["texts"] == {} and made["levels"] == []
    assert made["fields"] == {
        "record_bytes": "72", "record_type": "15", "schema_version": "1", "flags": "0", "publisher_id": "1",
        "channel_id": "0", "instrument_id": "2001", "ts_event": "5", "ts_recv": str(nwt.NULL), "sequence": "3",
        "price": "-1", "quantity": "2", "order_count": "4294967295", "action": "1", "side": "2", "delta_flags": "1",
        "reserved": "0",
    }  # fmt: skip
    assert (nwt.NULL, nwt.NULL_I64, nwt.NULL_U32) == ((1 << 64) - 1, -(1 << 63), (1 << 32) - 1)
    for item in nwt.CATALOG_V11:
        f, schema = item["fields"], nwt.S[item["type"]]
        derived = {"reserved", "levels"} | {name + "_bytes" for name in schema["texts"]}
        body = {x["name"]: int(f[x["name"]]) for x in schema["fields"] if x["name"] not in derived}
        header = {k: int(f[k]) for k in ("publisher_id", "channel_id", "instrument_id", "ts_event", "ts_recv", "sequence", "flags")}
        assert nwt.make_record(item["type"], texts=item["texts"], levels=item["levels"], **header, **body) == plain(item)
    raises(nwt.make_record, 15, sequence=1, price=1, contains="missing")
    raises(nwt.make_record, 13, sequence=1, ts_ref=0, price=0, quantity=0, stat_type=1, action=1, stat_flags=0, colour=1, contains="unknown")
    raises(nwt.make_record, 17, sequence=1, valid_from_ns=0, valid_to_ns=1, symbology=1, contains="symbol")


def test_typed_path():
    rng = random.Random(11)
    fixed = sorted(t for t, s in nwt.S.items() if not s["texts"] and not s["has_levels"])
    assert fixed == [1, 2, 3, 4, 7, 8, 13, 14, 15, 16, 18, 19, 20] and sorted(nwt.STRUCTS) == fixed
    for typ in fixed:
        assert nwt.STRUCTS[typ].size == nwt.S[typ]["fixed_bytes"]
        names = nwt.TYPED_NAMES[typ]
        assert "reserved" not in names and names[:3] == ("record_bytes", "record_type", "schema_version")
        for i in range(50):
            record = random_record(rng, typ, i + 1)
            encoded = nwt.encode_record(record)
            values = nwt.STRUCTS[typ].unpack(encoded)
            assert dict(zip(names, map(str, values))) == {k: v for k, v in record["fields"].items() if k != "reserved"}
            assert nwt.STRUCTS[typ].pack(*values) == encoded
    try:
        import numpy
    except ImportError:
        print("  notice: NumPy not installed; dtype check skipped")
        return
    for typ in fixed:
        records = [random_record(rng, typ, i + 1) for i in range(8)]
        array = numpy.frombuffer(b"".join(nwt.encode_record(r) for r in records), dtype=nwt.dtype(typ))
        assert array.dtype.itemsize == nwt.S[typ]["fixed_bytes"]
        for name in nwt.TYPED_NAMES[typ]:
            assert [str(int(v)) for v in array[name]] == [r["fields"][name] for r in records], (typ, name)


def test_goldens_current():
    raw = v11_bytes()
    assert (GOLDEN / "all-records.nwt").read_bytes() == raw
    records = nwt.read_container(raw)
    assert (GOLDEN / "all-fields.txt").read_bytes() == nwt.report(records).encode()
    for name in ("all-records.zst.nwt", "all-records.zst-checksum.nwt"):
        packed = (GOLDEN / name).read_bytes()
        assert any(codec == 1 for _, kind, codec, _, _ in frame_table(packed)), name
        if nwt.zstd_available():
            assert nwt.report(nwt.read_container(packed)) == nwt.report(records), name
    # Every DATA frame of the checksum golden carries Zstd's own content checksum (descriptor bit 2).
    checked = (GOLDEN / "all-records.zst-checksum.nwt").read_bytes()
    assert all(checked[at + 64 + 4] & 0x04 for at, kind, codec, _, _ in frame_table(checked) if kind == 1 and codec == 1)
    plain_zstd = (GOLDEN / "all-records.zst.nwt").read_bytes()
    assert not any(plain_zstd[at + 64 + 4] & 0x04 for at, kind, codec, _, _ in frame_table(plain_zstd) if kind == 1 and codec == 1)
    if shutil.which("zstd"):  # the zstd command decodes a stored payload to the raw golden's payload
        for at, (raw_at, _, _, raw_size, _) in zip((f[0] for f in frame_table(checked)), frame_table(raw)[:16]):
            stored = int.from_bytes(checked[at + 12 : at + 16], "little")
            tool = subprocess.run(["zstd", "-d", "-c"], input=checked[at + 64 : at + 64 + stored], capture_output=True)
            assert tool.returncode == 0 and tool.stdout == raw[raw_at + 64 : raw_at + 64 + raw_size]
    for pretty, suffix in ((False, ""), (True, ".pretty")):
        lines = "".join(nwt.to_json_line(r, pretty) + "\n" for r in records)
        assert (GOLDEN / f"all-records{suffix}.jsonl").read_bytes() == lines.encode()
        for typ in sorted(nwt.S):
            path = GOLDEN / f"type-{typ:02}{suffix}.csv"
            if nwt.S[typ]["has_levels"]:
                assert not path.exists()
                continue
            rows = [nwt.to_csv_line(r, pretty) for r in records if r["type"] == typ]
            assert path.read_bytes() == "".join(row + "\n" for row in [nwt.csv_header(typ)] + rows).encode(), path.name
    for i, item in enumerate(nwt.CATALOG_V11, 1):
        stem = GOLDEN / "records" / f"{i:03}-{item['label']}"
        assert stem.with_suffix(".bin").read_bytes() == nwt.encode_record(item)
        assert json.loads(stem.with_suffix(".json").read_text()) == item
    assert len(list((GOLDEN / "records").iterdir())) == 2 * len(nwt.CATALOG_V11)

    # The standalone FRAME_SUMMARY describes DATA frame 0 of the raw golden.
    summary = {k: int(v) for k, v in scenario("frame-summary")["fields"].items()}
    frames = list(reader_for(raw).frames())
    assert [info.kind for info, _ in frames] == [1] * 16 + [2, 3]
    assert (frames[2][0].min_event_ns, frames[2][0].max_event_ns) == (nwt.NULL, nwt.NULL)  # only null timestamps
    assert frames[1][0].min_event_ns != nwt.NULL and any(nwt.get(b, 24, 8) == nwt.NULL for b in frames[1][1])
    info, raws = frames[0]
    heads = [nwt.decode_record(b)["fields"] for b in raws]
    instruments = [int(h["instrument_id"]) for h in heads if h["instrument_id"] != "0"]
    assert (summary["data_frame_seq"], summary["data_frame_offset"], summary["stored_bytes"], summary["codec"]) == (
        info.seq, info.offset, info.stored_bytes, info.codec)  # fmt: skip
    assert summary["type_mask"] == sum({1 << int(h["record_type"]) for h in heads})
    assert (summary["min_instrument_id"], summary["max_instrument_id"]) == (min(instruments), max(instruments))
    times = [int(h["ts_event"]) for h in heads]
    assert summary["summary_flags"] == (nwt.NULL in times) | 2 * (times == sorted(times))

    # The command line reproduces every golden (the commands listed in fixtures/v1.1/README.md).
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp) / "out dir "  # a path with spaces, like the kit's own parent folder
        tmp.mkdir()
        assert run("write", tmp / "legacy.nwt").returncode == 0
        assert hashlib.sha256((tmp / "legacy.nwt").read_bytes()).hexdigest() == LEGACY_SHA
        assert run("write-v11", tmp / "a.nwt").returncode == 0 and (tmp / "a.nwt").read_bytes() == raw
        result = run("read", GOLDEN / "all-records.nwt", tmp / "again.nwt")
        assert result.stdout == (GOLDEN / "all-fields.txt").read_bytes() and (tmp / "again.nwt").read_bytes() == raw
        assert run("to-json", GOLDEN / "all-records.nwt").stdout == (GOLDEN / "all-records.jsonl").read_bytes()
        assert run("to-json", GOLDEN / "all-records.nwt", "--pretty").stdout == (GOLDEN / "all-records.pretty.jsonl").read_bytes()
        for typ in (9, 12, 20):
            assert run("to-csv", GOLDEN / "all-records.nwt", typ).stdout == (GOLDEN / f"type-{typ:02}.csv").read_bytes()
            assert run("to-csv", GOLDEN / "all-records.nwt", typ, "--pretty").stdout == (GOLDEN / f"type-{typ:02}.pretty.csv").read_bytes()
        refused = run("to-csv", GOLDEN / "all-records.nwt", 5)
        assert refused.returncode != 0 and b"to-json" in refused.stderr and not refused.stdout
        for typ in range(1, 23):
            assert run("record", typ, tmp / "r.bin").returncode == 0
            assert (tmp / "r.bin").read_bytes() == nwt.encode_record(example(typ)), typ
            decoded = run("decode-record", tmp / "r.bin")
            assert decoded.stdout == nwt.report([example(typ)]).encode()
        if nwt.zstd_available():
            assert run("write-v11", tmp / "z.nwt", "--zstd").returncode == 0
            result = run("read", tmp / "z.nwt", tmp / "z-raw.nwt")
            assert result.stdout == (GOLDEN / "all-fields.txt").read_bytes() and (tmp / "z-raw.nwt").read_bytes() == raw
            assert run("to-json", GOLDEN / "all-records.zst.nwt").stdout == (GOLDEN / "all-records.jsonl").read_bytes()
        bench = run("bench", GOLDEN / "all-records.nwt")
        lines = bench.stdout.decode().splitlines()
        assert bench.returncode == 0 and [line.split()[0] for line in lines] == ["decode", "encode"]
        for line in lines:
            keys = [part.split("=")[0] for part in line.split()[1:]]
            assert keys == ["records", "seconds", "records_per_second", "mb_per_second"] and "records=47 " in line
        assert run("frobnicate", tmp / "x").returncode != 0 and run().returncode != 0


def test_malformed_goldens():
    expected = json.loads((GOLDEN / "malformed/expected.json").read_text())
    files = sorted(p.name for p in (GOLDEN / "malformed").glob("*.nwt"))
    assert files == sorted(expected) and len(files) >= 11
    assert set(expected.values()) == {"reject"}
    for wanted in ("bad-enum", "bad-mask", "nonzero-reserved", "text-over-limit", "wrong-text-exact", "wrong-fixed-size",
                   "wrong-minor", "undeclared-type", "undeclared-publisher", "zstd-content-size", "zstd-window"):  # fmt: skip
        assert wanted + ".nwt" in expected, wanted
    for name in files:
        data = (GOLDEN / "malformed" / name).read_bytes()
        if nwt.zstd_available() or not name.startswith("zstd-"):
            raises(nwt.read_container, data)
        result = run("read", GOLDEN / "malformed" / name)
        assert result.returncode != 0 and result.stderr.startswith(b"NWT error: "), name


def main():
    tests = [(name, fn) for name, fn in globals().items() if name.startswith("test_") and callable(fn)]
    passed, failed, skipped = 0, [], 0
    for name, fn in tests:
        try:
            outcome = fn()
        except Exception as error:  # report every failing test, then exit non-zero
            failed.append(name)
            tb = error.__traceback__
            while tb.tb_next:
                tb = tb.tb_next
            where = f"{Path(tb.tb_frame.f_code.co_filename).name}:{tb.tb_lineno}"
            print(f"FAIL {name}: {type(error).__name__}: {str(error)[:300]} ({where})")
        else:
            skipped += outcome == "skipped"
            passed += outcome != "skipped"
    print(f"test_contract: {len(tests)} tests, {passed} passed, {len(failed)} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
