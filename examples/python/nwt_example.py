#!/usr/bin/env python3

import copy, ctypes, ctypes.util, io, json, os, struct, sys, time
from collections import namedtuple
from contextlib import nullcontext
from pathlib import Path
from example_data import SCHEMA, CATALOG, MANIFEST, CATALOG_GOLDEN, MANIFEST_GOLDEN

NULL = (1 << 64) - 1
NULL_I64 = -(1 << 63)
NULL_U32 = (1 << 32) - 1
LIMIT = 16777216
S = {s["type"]: s for s in SCHEMA["schemas"]}
LEVEL_BYTES = sum(f["bytes"] for f in SCHEMA["level"])
LEVEL_NAMES = [f["name"] for f in SCHEMA["level"]]
CATALOG_ID = bytes.fromhex("102132435465768798a9bacbdcedfe0f")
GOLDEN_ID = bytes.fromhex("a1b2c3d4e5f60718293a4b5c6d7e8f90")
ORDERINGS = ("none", "ts_event", "instrument,ts_event")
USAGE = (
    "usage: nwt_example.py write FILE | write-golden FILE [--zstd] | read FILE [REENCODED_FILE] | "
    "record TYPE FILE | decode-record FILE | to-json FILE [--pretty] | to-csv FILE TYPE [--pretty] | bench FILE"
)


def need(ok, why):
    if not ok:
        raise ValueError(why)




def crc_table():
    table = []
    for c in range(256):
        for _ in range(8):
            c = (c >> 1) ^ (0x82F63B78 if c & 1 else 0)
        table.append(c)
    return table


CRC_TABLE = crc_table()


def crc(data):
    c = 0xFFFFFFFF
    for x in data:
        c = CRC_TABLE[(c ^ x) & 255] ^ (c >> 8)
    return c ^ 0xFFFFFFFF


def pad(b):
    return b + bytes((-len(b)) % 8)


def get(b, o, n):
    need(0 <= o <= len(b) and n <= len(b) - o, "truncated integer")
    return int.from_bytes(b[o : o + n], "little")


def put(b, o, n, v):
    b[o : o + n] = int(v).to_bytes(n, "little")


def hcrc(b, o):
    b = bytearray(b)
    put(b, o, 4, 0)
    put(b, o, 4, crc(b))
    return bytes(b)


def vh(b, o):
    need(len(b) == 64, "header size")
    tmp = bytearray(b)
    c = get(tmp, o, 4)
    put(tmp, o, 4, 0)
    need(crc(tmp) == c, "header CRC")




def encode_fields(values, fields):
    out = bytearray()
    for f in fields:
        value = int(values[f["name"]])
        width = f["bytes"]
        if f["name"] == "reserved":
            need(value == 0, "reserved must be zero")
        out += value.to_bytes(width, "little", signed=f["signed"])
    return bytes(out)


def decode_fields(b, pos, fields):
    result = {}
    for f in fields:
        width = f["bytes"]
        need(pos + width <= len(b), "field bounds")
        value = int.from_bytes(b[pos : pos + width], "little", signed=f["signed"])
        if f["name"] == "reserved":
            need(value == 0, "nonzero reserved")
        result[f["name"]] = str(value)
        pos += width
    return result, pos


def utf8(text):
    need("\0" not in text, "NUL text")
    return text.encode("utf-8", errors="strict")


def check_schema(s, f):
    for name, allowed in s.get("enums", {}).items():
        need(int(f[name]) in allowed, "invalid " + name)
    for name, mask in s.get("masks", {}).items():
        need(int(f[name]) & ~mask == 0, "invalid " + name + " bits")
    for name, (lo, hi) in s.get("text_limits", {}).items():
        need(lo <= int(f[name + "_bytes"]) <= hi, name + " text limit")
    for name, sizes in s.get("text_exact", {}).items():
        need(int(f[name + "_bytes"]) in sizes, name + " text length")


def encode_record(record):
    r = copy.deepcopy(record)
    f = r["fields"]
    typ = int(f["record_type"])
    need(r["type"] == typ, "record type mismatch")
    s = S[typ]
    need(int(f["schema_version"]) == 1 and int(f["flags"]) & ~3 == 0, "version/flags")
    if s["has_levels"]:
        need(len(r["levels"]) <= 1024, "levels limit")
        f["levels"] = str(len(r["levels"]))
    for name in s["texts"]:
        f[name + "_bytes"] = str(len(utf8(r["texts"][name])))
    check_schema(s, f)
    body = encode_fields(f, s["fields"])
    for level in r["levels"] if s["has_levels"] else []:
        body += encode_fields(level, SCHEMA["level"])
    for name in s["texts"]:
        body += utf8(r["texts"][name])
    body = pad(body)
    f["record_bytes"] = str(48 + len(body))
    need(48 + len(body) <= 1048576, "record limit")
    return encode_fields(f, SCHEMA["header"]) + body


def decode_record(b):
    need(48 <= len(b) <= 1048576 and len(b) % 8 == 0, "record size")
    f, p = decode_fields(b, 0, SCHEMA["header"])
    typ = int(f["record_type"])
    need(int(f["record_bytes"]) == len(b) and typ in S, "length/type")
    need(f["schema_version"] == "1" and int(f["flags"]) & ~3 == 0, "version/flags")
    s = S[typ]
    body, p = decode_fields(b, p, s["fields"])
    f.update(body)
    levels = []
    texts = {}
    if s["has_levels"]:
        n = int(f["levels"])
        need(n <= 1024, "levels limit")
        for _ in range(n):
            level, p = decode_fields(b, p, SCHEMA["level"])
            levels.append(level)
    for name in s["texts"]:
        n = int(f[name + "_bytes"])
        need(n <= len(b) - p, "text bounds")
        texts[name] = b[p : p + n].decode("utf-8", errors="strict")
        utf8(texts[name])
        p += n
    need((p + 7) & ~7 == len(b) and not any(b[p:]), "padding/record length")
    check_schema(s, f)
    return {"type": typ, "fields": f, "texts": texts, "levels": levels}


def make_record(typ, *, publisher_id=1, channel_id=0, instrument_id=0, ts_event=NULL, ts_recv=NULL,
                sequence, flags=0, texts=None, levels=None, **body):
    s = S[typ]
    texts = dict(texts or {})
    need(s["has_levels"] or not levels, "this record type has no levels")
    levels = [
        {name: str(int(level.get(name, 0) if name == "reserved" else level[name])) for name in LEVEL_NAMES}
        for level in levels or []
    ]
    for name in s["texts"]:
        need(name in texts, "missing text " + name)
    need(len(texts) == len(s["texts"]), "unknown text")
    fields = dict(
        record_bytes=0, record_type=typ, schema_version=1, flags=flags, publisher_id=publisher_id,
        channel_id=channel_id, instrument_id=instrument_id, ts_event=ts_event, ts_recv=ts_recv, sequence=sequence,
    )
    for f in s["fields"]:
        name = f["name"]
        if name == "reserved":
            fields[name] = 0
        elif name.endswith("_bytes") and name[:-6] in texts:
            fields[name] = len(utf8(texts[name[:-6]]))
        elif s["has_levels"] and name == "levels":
            fields[name] = len(levels)
        else:
            need(name in body, "missing field " + name)
            fields[name] = body.pop(name)
    need(not body, "unknown field " + ", ".join(body))
    size = s["fixed_bytes"] + LEVEL_BYTES * len(levels) + sum(len(utf8(t)) for t in texts.values())
    fields["record_bytes"] = (size + 7) & ~7
    return {"type": typ, "fields": {k: str(int(v)) for k, v in fields.items()}, "texts": texts, "levels": levels}


class Sequencer:

    def __init__(self):
        self.last = {}

    def next(self, publisher_id, channel_id):
        key = (publisher_id, channel_id)
        self.last[key] = self.last.get(key, 0) + 1
        return self.last[key]




def report_lines(i, r):
    lines = []
    for f in SCHEMA["header"] + S[r["type"]]["fields"]:
        lines.append(f"{i}.{f['name']}={r['fields'][f['name']]}")
    for j, level in enumerate(r["levels"]):
        for f in SCHEMA["level"]:
            lines.append(f"{i}.levels.{j}.{f['name']}={level[f['name']]}")
    for name in S[r["type"]]["texts"]:
        lines.append(f"{i}.{name}={r['texts'][name]}")
    return lines


def report(records):
    return "".join(line + "\n" for i, r in enumerate(records, 1) for line in report_lines(i, r))


def pretty_decimal(v):
    return ("-" if v < 0 else "") + f"{abs(v) // 10**9}.{abs(v) % 10**9:09}"


def pretty_time(ns):
    seconds, fraction = divmod(ns, 10**9)
    days, rest = divmod(seconds, 86400)
    era, doe = divmod(days + 719468, 146097)
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    day = doy - (153 * mp + 2) // 5 + 1
    month = mp + 3 if mp < 10 else mp - 9
    year = yoe + era * 400 + (month <= 2)
    return f"{year:04}-{month:02}-{day:02}T{rest // 3600:02}:{rest % 3600 // 60:02}:{rest % 60:02}.{fraction:09}Z"


def pretty_value(f, text):
    kind = f.get("kind")
    if not kind:
        return text
    v = int(text)
    if v == (NULL_I64 if f["signed"] else NULL):
        return None
    return pretty_time(v) if kind == "time" else pretty_decimal(v)


def output_items(fields, values, pretty):
    for f in fields:
        if f["name"] != "reserved":
            yield f["name"], pretty_value(f, values[f["name"]]) if pretty else values[f["name"]]


def record_items(r, pretty):
    s = S[r["type"]]
    fields = [f for f in SCHEMA["header"] + s["fields"] if not (s["has_levels"] and f["name"] == "levels")]
    return list(output_items(fields, r["fields"], pretty)) + [(name, r["texts"][name]) for name in s["texts"]]


def json_string(text):
    out = ['"']
    for ch in text:
        if ch in '"\\':
            out.append("\\" + ch)
        elif ch < " ":
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return "".join(out) + '"'


def json_object(items):
    return "{" + ",".join(json_string(k) + ":" + ("null" if v is None else json_string(v)) for k, v in items) + "}"


def to_json_line(record, pretty=False):
    s = S[record["type"]]
    text = json_object([("type_name", s["name"])] + record_items(record, pretty))
    if s["has_levels"]:
        levels = ",".join(json_object(output_items(SCHEMA["level"], level, pretty)) for level in record["levels"])
        text = text[:-1] + ',"levels":[' + levels + "]}"
    return text


def csv_value(v):
    if v is None:
        return ""
    return '"' + v.replace('"', '""') + '"' if any(c in v for c in ',"\r\n') else v


def csv_header(typ):
    s = S[typ]
    need(not s["has_levels"], f"type {typ} has levels; use to-json")
    return ",".join([f["name"] for f in SCHEMA["header"] + s["fields"] if f["name"] != "reserved"] + s["texts"])


def to_csv_line(record, pretty=False):
    need(not S[record["type"]]["has_levels"], f"type {record['type']} has levels; use to-json")
    return ",".join(csv_value(v) for _, v in record_items(record, pretty))




def strict_json(text):
    def pairs(items):
        need(len({k for k, _ in items}) == len(items), "duplicate JSON key")
        return dict(items)

    def refuse(_):
        raise ValueError("JSON numbers must be integers")

    return json.loads(text, object_pairs_hook=pairs, parse_float=refuse, parse_constant=refuse)


def is_text(v, lo, hi):
    return isinstance(v, str) and lo <= len(v.encode("utf-8")) <= hi


def is_int(v, lo, hi):
    return type(v) is int and lo <= v <= hi


def parse_manifest(text):
    m = strict_json(text)
    need(isinstance(m, dict), "manifest must be a JSON object")
    for key in ("dataset", "producer", "profile", "publishers", "schemas", "clock"):
        need(key in m, "manifest missing " + key)
    need(is_text(m["dataset"], 1, 255) and is_text(m["producer"], 1, 255), "manifest dataset/producer")
    need(m["profile"] in ("market-data", "generic-events"), "manifest profile")
    need(m["clock"] == "posix-ns", "manifest clock")
    need(m.get("ordering", "none") in ORDERINGS, "manifest ordering")
    publishers, schemas = m["publishers"], m["schemas"]
    need(isinstance(publishers, list) and len(publishers) <= 4096, "manifest publishers")
    for p in publishers:
        need(isinstance(p, dict), "manifest publisher")
        need(is_int(p.get("id"), 1, NULL_U32), "manifest publisher id")
        need(is_text(p.get("name"), 1, 255) and is_text(p.get("venue"), 0, 255), "manifest publisher name/venue")
    need(len({p["id"] for p in publishers}) == len(publishers), "manifest duplicate publisher")
    need(isinstance(schemas, list) and 1 <= len(schemas) <= 4096, "manifest schemas")
    for s in schemas:
        need(isinstance(s, dict), "manifest schema")
        need(is_int(s.get("type"), 1, 65534) and is_int(s.get("version"), 1, 255), "manifest schema type/version")
        need(isinstance(s.get("required"), bool), "manifest schema required")
        need(is_text(s.get("name"), 1, 255) and is_text(s.get("spec_uri"), 1, 2048), "manifest schema name/spec_uri")
    need(len({(s["type"], s["version"]) for s in schemas}) == len(schemas), "manifest duplicate schema")
    return m


def build_manifest(dataset, producer, publishers, types, ordering=None, profile="market-data"):
    m = {"dataset": dataset, "producer": producer, "profile": profile, "clock": "posix-ns"}
    if ordering is not None:
        m["ordering"] = ordering
    m["publishers"] = [{"id": p["id"], "name": p["name"], "venue": p["venue"]} for p in publishers]
    m["schemas"] = [
        {"type": t, "version": 1, "required": t <= 9 or t == 15, "name": S[t]["name"],
         "spec_uri": "urn:nwt:spec:1.0" if t <= 9 else "urn:nwt:spec:1.1"}
        for t in sorted(set(types))
    ]
    text = json.dumps(m, separators=(",", ":"), ensure_ascii=False)
    parse_manifest(text)
    return text


def manifest_minor(manifest):
    return 1 if any(10 <= s["type"] <= 22 for s in manifest["schemas"]) else 0


def tlv(typ, flags, value):
    return pad(struct.pack("<HHI", typ, flags, len(value)) + value)


def parse_metadata(meta):
    out = {}
    p = 0
    while p < len(meta):
        need(len(meta) - p >= 8, "TLV header")
        typ, flags, n = struct.unpack_from("<HHI", meta, p)
        need(0 < typ < 65535 and flags & ~1 == 0, "TLV type/flags")
        need(typ not in out, "duplicate TLV")
        need(n <= len(meta) - p - 8, "TLV length")
        end = p + 8 + n
        out[typ] = (flags, meta[p + 8 : end])
        p = (end + 7) & ~7
        need(not any(meta[end:p]), "TLV padding")
        need(typ in (1, 2) or flags == 0, "unknown required TLV")
    need(1 in out and out[1][0] == 1, "MANIFEST TLV must be present with its required flag")
    need(2 not in out or out[2][0] == 0, "PROVENANCE TLV must not be marked required")
    return out


def parse_provenance(tlvs):
    if 2 not in tlvs:
        return None
    value = strict_json(tlvs[2][1].decode("utf-8"))
    need(isinstance(value, dict), "PROVENANCE must be a JSON object")
    return value



zstd_library = None


def zstd_load():
    global zstd_library
    if zstd_library is None:
        zstd_library = False
        chosen = os.environ.get("NWT_ZSTD_LIB")
        found = ctypes.util.find_library("zstd")
        fallbacks = [found, "/opt/homebrew/lib/libzstd.dylib", "/usr/local/lib/libzstd.dylib", "libzstd.so.1"]
        names = [chosen] if chosen else fallbacks
        for name in filter(None, names):
            try:
                lib = ctypes.CDLL(name)
            except OSError:
                continue
            size, buffer = ctypes.c_size_t, ctypes.c_void_p
            for function, result, arguments in [
                ("ZSTD_compressBound", size, [size]),
                ("ZSTD_compress", size, [buffer, size, ctypes.c_char_p, size, ctypes.c_int]),
                ("ZSTD_decompress", size, [buffer, size, ctypes.c_char_p, size]),
                ("ZSTD_findFrameCompressedSize", size, [ctypes.c_char_p, size]),
                ("ZSTD_isError", ctypes.c_uint, [size]),
            ]:
                getattr(lib, function).restype = result
                getattr(lib, function).argtypes = arguments
            zstd_library = lib
            break
    need(zstd_library, "Zstd library not available")
    return zstd_library


def zstd_available():
    try:
        zstd_load()
    except ValueError:
        return False
    return True


def zstd_check(stored, raw_bytes):
    need(len(stored) >= 6 and stored[:4] == b"\x28\xb5\x2f\xfd", "Zstd magic")
    d = stored[4]
    fcs = d >> 6
    single = d >> 5 & 1
    need(d & 0x08 == 0, "Zstd reserved bit")
    need(d & 0x03 == 0, "Zstd dictionary")
    p = 5
    window = None
    if not single:
        w = stored[p]
        p += 1
        base = 1 << (10 + (w >> 3))
        window = base + (base >> 3) * (w & 7)
    n = (1 if single else 0, 2, 4, 8)[fcs]
    need(n > 0, "Zstd content size missing")
    need(len(stored) >= p + n, "Zstd header")
    size = int.from_bytes(stored[p : p + n], "little") + (256 if fcs == 1 else 0)
    need(size == raw_bytes, "Zstd content size")
    need((size if single else window) <= LIMIT, "Zstd window")


def zstd_compress(b, level=3):
    lib = zstd_load()
    room = lib.ZSTD_compressBound(len(b))
    out = ctypes.create_string_buffer(room)
    n = lib.ZSTD_compress(out, room, b, len(b), level)
    need(not lib.ZSTD_isError(n), "Zstd compression failed")
    return out.raw[:n]


def zstd_decompress(b, raw_bytes):
    zstd_check(b, raw_bytes)
    lib = zstd_load()
    need(lib.ZSTD_findFrameCompressedSize(b, len(b)) == len(b), "Zstd frame must fill stored_bytes exactly")
    out = ctypes.create_string_buffer(max(raw_bytes, 1))
    n = lib.ZSTD_decompress(out, raw_bytes, b, len(b))
    need(not lib.ZSTD_isError(n) and n == raw_bytes, "Zstd decompression failed")
    return out.raw[:raw_bytes]




def frame(kind, seq, payload, count=0, lo=NULL, hi=NULL, codec=0, stored=None):
    stored = payload if stored is None else stored
    h = bytearray(64)
    h[:4] = b"NWF1"
    h[4] = 1
    h[5] = kind
    h[6] = codec
    for o, n, v in [
        (8, 2, 64),
        (12, 4, len(stored)),
        (16, 4, len(payload)),
        (20, 4, count),
        (24, 8, seq),
        (32, 8, lo),
        (40, 8, hi),
        (48, 4, crc(payload)),
    ]:
        put(h, o, n, v)
    return hcrc(h, 52) + pad(stored)


def time_bounds(raws):
    times = [t for t in (get(raw, 24, 8) for raw in raws) if t != NULL]
    return (min(times), max(times)) if times else (NULL, NULL)


def split_records(payload, count):
    need(count > 0 and len(payload) % 8 == 0, "DATA order/count")
    raws = []
    p = 0
    while p < len(payload):
        n = get(payload, p, 4)
        need(48 <= n <= 1048576 and n % 8 == 0 and n <= len(payload) - p, "record bounds")
        raws.append(payload[p : p + n])
        p += n
    need(len(raws) == count, "record count")
    return raws


def index_entry(i):
    return struct.pack("<QQQQII", i.seq, i.offset, i.min_event_ns, i.max_event_ns, i.raw_bytes, i.record_count)


class Scope:

    def __init__(self, manifest):
        self.types = {(s["type"], s["version"]) for s in manifest["schemas"]}
        self.publishers = {p["id"] for p in manifest["publishers"]}
        self.sequences = {}

    def check(self, raw):
        need((get(raw, 4, 2), get(raw, 6, 1)) in self.types, "undeclared record type")
        key = (get(raw, 8, 4), get(raw, 12, 4))
        need(key[0] == 0 or key[0] in self.publishers, "undeclared publisher")
        need(get(raw, 40, 8) == self.sequences.get(key, 0) + 1, "record sequence")
        self.sequences[key] = self.sequences.get(key, 0) + 1


FrameInfo = namedtuple(
    "FrameInfo", "seq offset kind codec stored_bytes raw_bytes record_count min_event_ns max_event_ns"
)


class Writer:

    def __init__(self, fileobj, manifest, stream_id, created_ns=NULL, provenance=None,
                 frame_bytes=1 << 20, frame_records=None, zstd_level=None, metadata=None):
        if metadata is None:
            metadata = tlv(1, 1, manifest.encode("utf-8"))
            if provenance is not None:
                metadata += tlv(2, 0, provenance.encode("utf-8"))
        tlvs = parse_metadata(metadata)
        parse_provenance(tlvs)
        parsed = parse_manifest(tlvs[1][1].decode("utf-8"))
        need(len(metadata) <= 1048576 and len(metadata) % 8 == 0, "metadata length")
        need(len(stream_id) == 16 and any(stream_id), "stream ID must be 16 bytes and not all zero")
        need(48 <= frame_bytes <= LIMIT and (frame_records is None or frame_records > 0), "frame size")
        self.out, self.position = fileobj, 0
        self.frame_bytes, self.frame_records, self.zstd_level = frame_bytes, frame_records, zstd_level
        self.scope = Scope(parsed)
        self.pending, self.pending_bytes = [], 0
        self.frames, self.seq, self.records = [], 0, 0
        h = bytearray(64)
        h[:8] = b"NWTBIN\r\n"
        put(h, 8, 2, 1)
        put(h, 10, 2, manifest_minor(parsed))
        put(h, 12, 2, 64)
        put(h, 16, 4, len(metadata))
        put(h, 20, 4, crc(metadata))
        h[24:40] = stream_id
        put(h, 40, 8, created_ns)
        self.emit(hcrc(h, 56) + metadata)

    def emit(self, data):
        self.out.write(data)
        self.position += len(data)

    def write(self, record):
        self.write_raw(encode_record(record))

    def write_raw(self, record_bytes):
        b = bytes(record_bytes)
        need(48 <= len(b) <= 1048576 and len(b) % 8 == 0 and get(b, 0, 4) == len(b), "record size")
        self.scope.check(b)
        room = self.frame_bytes if self.frame_records is None else LIMIT
        if self.pending and (len(self.pending) == self.frame_records or self.pending_bytes + len(b) > room):
            self.flush()
        self.pending.append(b)
        self.pending_bytes += len(b)

    def store(self, payload):
        if self.zstd_level is None:
            return 0, payload
        packed = zstd_compress(payload, self.zstd_level)
        if len(packed) >= len(payload):
            return 0, payload
        zstd_check(packed, len(payload))
        return 1, packed

    def flush(self):
        if not self.pending:
            return
        payload = b"".join(self.pending)
        lo, hi = time_bounds(self.pending)
        codec, stored = self.store(payload)
        count = len(self.pending)
        self.frames.append(FrameInfo(self.seq, self.position, 1, codec, len(stored), len(payload), count, lo, hi))
        self.emit(frame(1, self.seq, payload, count, lo, hi, codec, stored))
        self.seq += 1
        self.records += count
        self.pending, self.pending_bytes = [], 0

    def close(self, status=0):
        self.flush()
        first_index = self.position if self.frames else 0
        entries = [index_entry(info) for info in self.frames]
        per_frame = LIMIT // 40
        for start in range(0, len(entries), per_frame):
            self.emit(frame(2, self.seq, b"".join(entries[start : start + per_frame])))
            self.seq += 1
        self.emit(frame(3, self.seq, struct.pack("<QQQII", first_index, len(entries), self.records, status, 0)))


class Reader:

    def __init__(self, read_at, size):
        self.read_at, self.size, self.end = read_at, size, None
        h = self.read(0, 64, "container header")
        vh(h, 56)
        need(h[:8] == b"NWTBIN\r\n" and get(h, 8, 2) == 1 and get(h, 12, 2) == 64, "container fields")
        need(get(h, 10, 2) in (0, 1), "unsupported container minor")
        need(get(h, 14, 2) == 0 and not any(h[48:56]) and not any(h[60:64]) and any(h[24:40]), "container reserved/ID")
        ml = get(h, 16, 4)
        need(8 <= ml <= 1048576 and ml % 8 == 0, "metadata length")
        self.metadata = self.read(64, ml, "metadata")
        need(crc(self.metadata) == get(h, 20, 4), "metadata CRC")
        tlvs = parse_metadata(self.metadata)
        self.manifest = parse_manifest(tlvs[1][1].decode("utf-8"))
        self.provenance = parse_provenance(tlvs)
        minor, stream_id = get(h, 10, 2), bytes(h[24:40])
        self.header = dict(major=1, minor=minor, metadata_bytes=ml, stream_id=stream_id, created_ns=get(h, 40, 8))
        need(minor == manifest_minor(self.manifest), "container minor does not match the declared types")

    def read(self, offset, n, what):
        need(offset + n <= self.size, "incomplete: file ends inside " + what)
        data = self.read_at(offset, n)
        need(len(data) == n, "incomplete: file ends inside " + what)
        return data

    def frame_info(self, offset):
        h = self.read(offset, 64, "frame header")
        vh(h, 52)
        need(
            h[:4] == b"NWF1" and h[4] == 1 and h[6] in (0, 1) and h[7] == 0
            and get(h, 8, 2) == 64 and get(h, 10, 2) == 0 and get(h, 56, 8) == 0,
            "frame fields/codec",
        )
        stored, raw, count, lo, hi = get(h, 12, 4), get(h, 16, 4), get(h, 20, 4), get(h, 32, 8), get(h, 40, 8)
        info = FrameInfo(get(h, 24, 8), offset, h[5], h[6], stored, raw, count, lo, hi)
        need(info.kind in (1, 2, 3), "frame sequence/kind")
        need(info.stored_bytes <= LIMIT and info.raw_bytes <= LIMIT, "frame size")
        need(info.stored_bytes == info.raw_bytes if info.codec == 0 else info.kind == 1, "frame size/codec")
        return info, get(h, 48, 4)

    def payload(self, info, payload_crc):
        padded = self.read(info.offset + 64, (info.stored_bytes + 7) & ~7, "frame payload")
        need(not any(padded[info.stored_bytes :]), "frame padding")
        stored = padded[: info.stored_bytes]
        raw = stored if info.codec == 0 else zstd_decompress(stored, info.raw_bytes)
        need(crc(raw) == payload_crc, "payload CRC")
        return raw

    def scan(self, decode=True):
        self.end = None
        scope = Scope(self.manifest)
        pos = 64 + len(self.metadata)
        seq = records = first_index = 0
        entries, index = [], []
        while self.end is None or pos < self.size:
            need(self.end is None, "trailing bytes")
            need(pos < self.size, "incomplete: missing END")
            info, payload_crc = self.frame_info(pos)
            need(info.seq == seq, "frame sequence/kind")
            payload = self.payload(info, payload_crc)
            raws, decoded = [], []
            if info.kind == 1:
                need(first_index == 0, "DATA order/count")
                raws = split_records(payload, info.record_count)
                for raw in raws:
                    scope.check(raw)
                    if decode:
                        decoded.append(decode_record(raw))
                need((info.min_event_ns, info.max_event_ns) == time_bounds(raws), "time bounds")
                entries.append(index_entry(info))
                records += len(raws)
            else:
                need(info.record_count == 0 and info.min_event_ns == info.max_event_ns == NULL, "non-DATA fields")
                if info.kind == 2:
                    need(info.raw_bytes > 0 and info.raw_bytes % 40 == 0, "index size")
                    first_index = first_index or pos
                    index.append(payload)
                else:
                    need(info.raw_bytes == 32, "END size")
                    at, frames, total, status, reserved = struct.unpack("<QQQII", payload)
                    need((at, frames, total, reserved) == (first_index, len(entries), records, 0), "END totals/status")
                    need(status in (0, 1), "END totals/status")
                    need(not first_index or b"".join(index) == b"".join(entries), "index mismatch")
                    self.end = dict(first_index_offset=at, total_data_frames=frames, total_records=total, status=status)
            yield info, raws, decoded
            pos += 64 + ((info.stored_bytes + 7) & ~7)
            seq += 1

    def frames(self):
        for info, raws, _ in self.scan():
            yield info, raws

    def records(self):
        for _, _, decoded in self.scan():
            yield from decoded

    def index(self):
        at = self.size - 96
        need(at >= 64 + len(self.metadata), "incomplete: no END frame at the end of the file")
        try:
            end, payload_crc = self.frame_info(at)
            need(end.kind == 3 and end.raw_bytes == 32, "not END")
            first_index, frames, _, status, reserved = struct.unpack("<QQQII", self.payload(end, payload_crc))
        except ValueError:
            raise ValueError("incomplete: no END frame at the end of the file") from None
        need(reserved == 0 and status in (0, 1), "END totals/status")
        if first_index == 0:
            need(frames == 0, "container has DATA frames but no INDEX")
            return []
        need(64 + len(self.metadata) < first_index < at, "END index offset")
        out = []
        pos, seq = first_index, frames
        while pos < at:
            info, payload_crc = self.frame_info(pos)
            need(info.kind == 2 and info.seq == seq and info.raw_bytes > 0 and info.raw_bytes % 40 == 0, "index size")
            payload = self.payload(info, payload_crc)
            for p in range(0, len(payload), 40):
                n, offset, lo, hi, raw_bytes, count = struct.unpack_from("<QQQQII", payload, p)
                out.append(FrameInfo(n, offset, 1, None, None, raw_bytes, count, lo, hi))
            pos += 64 + ((info.stored_bytes + 7) & ~7)
            seq += 1
        need(pos == at and seq == end.seq, "index mismatch")
        need(len(out) == frames and [e.seq for e in out] == list(range(frames)), "index mismatch")
        offsets = [e.offset for e in out] + [first_index]
        need(offsets[0] == 64 + len(self.metadata), "index offsets")
        need(all(a < b for a, b in zip(offsets, offsets[1:])), "index offsets")
        return out

    def read_frame(self, info):
        got, payload_crc = self.frame_info(info.offset)
        need(
            got.kind == 1
            and (got.seq, got.raw_bytes, got.record_count, got.min_event_ns, got.max_event_ns)
            == (info.seq, info.raw_bytes, info.record_count, info.min_event_ns, info.max_event_ns),
            "index entry does not match its frame",
        )
        return split_records(self.payload(got, payload_crc), got.record_count)


def complete_records(reader):
    yield from reader.records()
    need(reader.end["status"] == 0, "aborted container")


def read_container(data):
    return list(complete_records(Reader(lambda offset, n: data[offset : offset + n], len(data))))


def write_container(records, manifest=MANIFEST, stream_id=CATALOG_ID, created_ns=1700000000000000000,
                    frame_records=3, zstd_level=None):
    out = io.BytesIO()
    writer = Writer(out, manifest, stream_id, created_ns, frame_records=frame_records, zstd_level=zstd_level)
    for r in records:
        writer.write(r)
    writer.close()
    return out.getvalue()




def typed_tables():
    codes = {(1, False): "B", (2, False): "H", (4, False): "I", (8, False): "Q", (8, True): "q"}
    structs, names = {}, {}
    for s in SCHEMA["schemas"]:
        if s["texts"] or s["has_levels"]:
            continue
        fields = SCHEMA["header"] + s["fields"]
        layout = [f"{f['bytes']}x" if f["name"] == "reserved" else codes[f["bytes"], f["signed"]] for f in fields]
        structs[s["type"]] = struct.Struct("<" + "".join(layout))
        names[s["type"]] = tuple(f["name"] for f in fields if f["name"] != "reserved")
        need(structs[s["type"]].size == s["fixed_bytes"], "schema fixed_bytes")
    return structs, names


STRUCTS, TYPED_NAMES = typed_tables()


def dtype(typ):
    import numpy

    fields = SCHEMA["header"] + S[typ]["fields"]
    offsets = [sum(f["bytes"] for f in fields[:i]) for i in range(len(fields))]
    keep = [i for i, f in enumerate(fields) if f["name"] != "reserved"]
    return numpy.dtype(
        {
            "names": [fields[i]["name"] for i in keep],
            "formats": ["<" + ("i" if fields[i]["signed"] else "u") + str(fields[i]["bytes"]) for i in keep],
            "offsets": [offsets[i] for i in keep],
            "itemsize": STRUCTS[typ].size,
        }
    )


def rate_line(label, records, size, ns):
    ns = max(ns, 1)
    mb = size * 10**12 // (ns * 1048576)
    return (
        f"{label} records={records} seconds={ns // 10**9}.{ns % 10**9 // 1000:06} "
        f"records_per_second={records * 10**9 // ns} mb_per_second={mb // 1000}.{mb % 1000:03}\n"
    )


def bench(path):
    data = Path(path).read_bytes()
    start = time.perf_counter_ns()
    values = []
    size = 0
    for _, raws, _ in Reader(lambda offset, n: data[offset : offset + n], len(data)).scan(decode=False):
        for raw in raws:
            typed = STRUCTS.get(raw[4] | raw[5] << 8)
            values.append(typed.unpack(raw) if typed and typed.size == len(raw) else decode_record(raw))
            size += len(raw)
    decoded = time.perf_counter_ns()
    for value in values:
        if type(value) is tuple:
            STRUCTS[value[1]].pack(*value)
        else:
            encode_record(value)
    encoded = time.perf_counter_ns()
    count = len(values)
    return rate_line("decode", count, size, decoded - start) + rate_line("encode", count, size, encoded - decoded)




def open_reader(f):
    def read_at(offset, n):
        f.seek(offset)
        return f.read(n)

    return Reader(read_at, f.seek(0, 2))


def emit(text):
    sys.stdout.buffer.write(text.encode("utf-8"))


def main():
    need(crc(b"123456789") == 0xE3069283, "CRC check")
    options = [a for a in sys.argv[1:] if a in ("--pretty", "--zstd")]
    args = [a for a in sys.argv[1:] if a not in options]
    need(len(args) >= 2, USAGE)
    command, pretty = args[0], "--pretty" in options
    if command == "write":
        Path(args[1]).write_bytes(write_container(CATALOG))
    elif command == "write-golden":
        records = [r for r in CATALOG_GOLDEN if not r.get("standalone")]
        level = 3 if "--zstd" in options else None
        Path(args[1]).write_bytes(write_container(records, MANIFEST_GOLDEN, GOLDEN_ID, 1760000000000000000, 3, level))
    elif command == "record":
        need(len(args) == 3, USAGE)
        typ = int(args[1])
        r = next((r for r in (CATALOG if typ <= 9 else CATALOG_GOLDEN) if r["type"] == typ), None)
        need(r, "no example for this record type")
        Path(args[2]).write_bytes(encode_record(r))
    elif command == "decode-record":
        path = Path(args[1])
        need(path.stat().st_size <= 1048576, "record limit")
        emit(report([decode_record(path.read_bytes())]))
    elif command == "read":
        again = args[2] if len(args) > 2 else None
        same = again and os.path.exists(again) and os.path.samefile(args[1], again)
        need(not same, "REENCODED_FILE must differ from FILE")
        with open(args[1], "rb") as f, (open(again, "wb") if again else nullcontext()) as out:
            reader = open_reader(f)
            identity = (reader.header["stream_id"], reader.header["created_ns"])
            writer = out and Writer(out, None, *identity, frame_records=3, metadata=reader.metadata)
            for i, r in enumerate(complete_records(reader), 1):
                emit("".join(line + "\n" for line in report_lines(i, r)))
                if writer:
                    writer.write(r)
            if writer:
                writer.close()
    elif command == "to-json":
        with open(args[1], "rb") as f:
            for r in complete_records(open_reader(f)):
                emit(to_json_line(r, pretty) + "\n")
    elif command == "to-csv":
        need(len(args) == 3, USAGE)
        typ = int(args[2])
        need(typ in S, "unknown record type")
        header = csv_header(typ)
        with open(args[1], "rb") as f:
            reader = open_reader(f)
            emit(header + "\n")
            for r in complete_records(reader):
                if r["type"] == typ:
                    emit(to_csv_line(r, pretty) + "\n")
    elif command == "bench":
        emit(bench(args[1]))
    else:
        raise ValueError("unknown command")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:  # the reader of a pipe closed it, as `head` does: a normal end
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    except (ValueError, KeyError, OverflowError, UnicodeError, OSError) as e:
        print("NWT error: " + str(e), file=sys.stderr)
        sys.exit(1)
