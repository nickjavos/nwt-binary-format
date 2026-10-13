#!/usr/bin/env python3

import argparse
import heapq
import itertools
import json
import os
import sys
import time
from contextlib import ExitStack, contextmanager

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(TOOLS), "examples", "python"))
sys.path.insert(0, TOOLS)
import market_state
import nwt_example as nwt
from nwt_parse import parse_date_ns, parse_timestamp_ns

try:
    import nwt_convert
except ModuleNotFoundError as error:
    if error.name != "nwt_convert":
        raise
    nwt_convert = None

ERRORS = (ValueError, KeyError, OverflowError, UnicodeError, OSError)
SUMMARY = 20
SYMBOLOGY = {"native": 1, "osi": 2, "isin": 3, "figi": 4, "root": 5, "continuous": 6}
IDENTIFIERS = {"isin": ("isin",), "cusip": ("cusip",), "figi": ("composite_figi", "figi")}
SUMMARY_FRAME = {"type_mask": 1 << SUMMARY, "min_instrument_id": 0, "max_instrument_id": 0}
KINDS = {1: "DATA", 2: "INDEX", 3: "END"}




def rtype(raw):
    return nwt.get(raw, 4, 2)


def rinst(raw):
    return nwt.get(raw, 16, 8)


def rtime(raw):
    return nwt.get(raw, 24, 8)


def type_bit(t):
    return 1 << (t if 1 <= t <= 63 else 0)




def parse_types(text):
    names = {s["name"]: t for t, s in nwt.S.items()}
    out = []
    for part in text.split(","):
        part = part.strip()
        nwt.need(part.upper() in names or part.isdigit(), f"unknown record type {part!r}")
        out.append(names.get(part.upper()) or int(part))
    return out


def parse_instruments(text):
    out = []
    for part in text.split(","):
        lo, dash, hi = part.strip().partition("-")
        nwt.need(lo.isdigit() and (not dash or hi.isdigit()), f"bad instrument {part!r}")
        nwt.need(not dash or int(lo) <= int(hi), f"empty instrument range {part!r}")
        out.append((int(lo), int(hi)) if dash else int(lo))
    return out


def parse_time(text):
    if text.isdigit():
        return int(text)
    return parse_date_ns(text) if len(text) == 10 else parse_timestamp_ns(text)


def filters(args):
    given = lambda value, parse: None if value is None else parse(value)
    return dict(
        types=given(args.types, parse_types),
        instruments=given(args.instruments, parse_instruments),
        t0=given(args.t0, parse_time),
        t1=given(args.t1, parse_time),
    )


def add_filters(parser):
    parser.add_argument("--type", dest="types", metavar="TYPES", help="record types, numbers or names: 2,TRADE")
    parser.add_argument("--instrument", dest="instruments", metavar="IDS", help="instrument IDs and ranges: 7,100-199")
    parser.add_argument("--from", dest="t0", metavar="TIME", help="ts_event >= TIME")
    parser.add_argument("--to", dest="t1", metavar="TIME", help="ts_event < TIME")




@contextmanager
def opened(path):
    with open(path, "rb") as f:
        yield nwt.open_reader(f)


def head(path):
    with opened(path) as reader:
        return reader


def scan_complete(reader, decode=False):
    yield from reader.scan(decode=decode)
    nwt.need(reader.end["status"] == 0, "aborted container")


def raw_records(path):
    with opened(path) as reader:
        summaries_seen = False
        for _, raws, _ in scan_complete(reader):
            for raw in raws:
                if rtype(raw) == SUMMARY:
                    summaries_seen = True
                else:
                    nwt.need(not summaries_seen, "FRAME_SUMMARY records are not at the end of the container")
                    yield raw




def frame_facts(raws):
    kinds = {rtype(r) for r in raws}
    ids = [i for i in map(rinst, raws) if i]
    times = [t for t in map(rtime, raws) if t != nwt.NULL]
    return dict(
        kinds=kinds,
        type_mask=sum({type_bit(t) for t in kinds}),
        min_instrument_id=min(ids, default=0),
        max_instrument_id=max(ids, default=0),
        summary_flags=int(len(times) < len(raws)) | int(all(a <= b for a, b in zip(times, times[1:]))) << 1,
    )


def summary_values(record):
    return {f["name"]: int(record["fields"][f["name"]]) for f in nwt.S[SUMMARY]["fields"] if f["name"] != "reserved"}


def summary_frames(reader, index):
    found = []
    for entry in reversed(index):
        if entry.min_event_ns != nwt.NULL or entry.raw_bytes != 104 * entry.record_count:
            break
        raws = reader.read_frame(entry)
        if {rtype(r) for r in raws} != {SUMMARY}:
            break
        found.append(raws)
    return found[::-1]


def summaries(reader):
    tail = summary_frames(reader, reader.index())
    return [summary_values(nwt.decode_record(raw)) for raws in tail for raw in raws]


def plan(reader):
    index = reader.index()
    tail = summary_frames(reader, index)
    found = [summary_values(nwt.decode_record(raw)) for raws in tail for raw in raws]
    body = len(index) - len(tail)
    if found:
        nwt.need(len(found) == body, "FRAME_SUMMARY records do not match the INDEX")
        for entry, s in zip(index, found):
            same = (s["data_frame_seq"], s["data_frame_offset"]) == (entry.seq, entry.offset)
            nwt.need(same, "FRAME_SUMMARY records do not match the INDEX")
    return [(e, found[i] if found else None) for i, e in enumerate(index[:body])] + [
        (e, SUMMARY_FRAME) for e in index[body:]
    ]


def spans(instruments):
    return [(i, i) if isinstance(i, int) else tuple(i) for i in instruments]


def matcher(types=None, ranges=None, t0=None, t1=None):
    wanted = None if types is None else set(types)

    def match(raw):
        if wanted is not None and rtype(raw) not in wanted:
            return False
        if ranges is not None and not any(a <= rinst(raw) <= b for a, b in ranges):
            return False
        if t0 is not None or t1 is not None:
            t = rtime(raw)
            if t == nwt.NULL or (t0 is not None and t < t0) or (t1 is not None and t >= t1):
                return False
        return True

    return match


def wants_instrument(ranges, s):
    lo, hi = s["min_instrument_id"], s["max_instrument_id"]
    return any(a == 0 or (hi != 0 and a <= hi and lo <= b) for a, b in ranges)


def select(reader, types=None, instruments=None, t0=None, t1=None):
    ranges = None if instruments is None else spans(instruments)
    match = matcher(types, ranges, t0, t1)
    want = None if types is None else sum({type_bit(t) for t in types})
    for entry, s in plan(reader):
        if t0 is not None or t1 is not None:
            if entry.min_event_ns == nwt.NULL:
                continue
            if (t0 is not None and entry.max_event_ns < t0) or (t1 is not None and entry.min_event_ns >= t1):
                continue
        if s and want is not None and not s["type_mask"] & want:
            continue
        if s and ranges is not None and not wants_instrument(ranges, s):
            continue
        for raw in reader.read_frame(entry):
            if match(raw):
                yield raw




class Facts:

    def __init__(self):
        self.count, self.types = 0, set()
        self.by_ts = self.by_instrument = True
        self.last_ts, self.last_key = 0, (0, 0)

    def add(self, raw):
        self.count += 1
        self.types.add(rtype(raw))
        t = rtime(raw)
        if t != nwt.NULL:
            key = (rinst(raw), t)
            self.by_ts = self.by_ts and t >= self.last_ts
            self.by_instrument = self.by_instrument and key >= self.last_key
            self.last_ts, self.last_key = t, key

    def holds(self, claim):
        return {"none": True, "ts_event": self.by_ts, "instrument,ts_event": self.by_instrument}[claim]

    def ordering(self, prefer="none"):
        if prefer != "none" and self.holds(prefer):
            return prefer
        return "ts_event" if self.by_ts else "instrument,ts_event" if self.by_instrument else "none"




@contextmanager
def atomic(path):
    tmp = str(path) + ".tmp"
    try:
        with open(tmp, "wb") as f:
            yield f
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def refuse_same(out, *paths):
    for path in paths:
        nwt.need(not (os.path.exists(out) and os.path.samefile(out, path)), "OUT must differ from its input")


def identity(args):
    stream_id = bytes.fromhex(getattr(args, "stream_id", None) or "") or os.urandom(16)
    return dict(stream_id=stream_id, created_ns=getattr(args, "created_ns", None) or time.time_ns())


def derive_manifest(manifests, facts, summaries_on=False, whole=False):
    m = dict(manifests[0])
    if len(manifests) > 1:
        for key in ("dataset", "producer"):
            m[key] = "+".join(dict.fromkeys(x[key] for x in manifests))
    pool = {}
    for x in manifests:
        for s in x["schemas"]:
            pool.setdefault((s["type"], s["version"]), s)
    schemas = [s for s in manifests[0]["schemas"] if s["type"] != SUMMARY] if whole else [pool[(t, 1)] for t in sorted(facts.types)]
    schemas = [dict(s, required=True) if s["type"] == 15 else s for s in schemas]
    if summaries_on:
        schemas.append(dict(type=SUMMARY, version=1, required=False, name="FRAME_SUMMARY", spec_uri="urn:nwt:spec:1.1"))
    m["schemas"] = sorted(schemas, key=lambda s: (s["type"], s["version"]))
    publishers = {}
    for x in manifests:
        for p in x["publishers"]:
            nwt.need(publishers.setdefault(p["id"], p) == p, f"publisher {p['id']} differs between the inputs")
    m["publishers"] = [publishers[i] for i in sorted(publishers)]
    ordering = facts.ordering(manifests[0].get("ordering", "none") if whole else "none")
    m.pop("ordering", None)
    if ordering != "none":
        m["ordering"] = ordering
    text = json.dumps(m, separators=(",", ":"), ensure_ascii=False)
    nwt.parse_manifest(text)
    return text


def derived_provenance(sources, tool, note):
    prov = dict(sources[0].provenance or {}) if len(sources) == 1 else {}
    prov.update(
        derived_by="tools/nwt.py " + tool,
        derived_note=note,
        source_stream_ids=",".join(s.header["stream_id"].hex() for s in sources),
    )
    return json.dumps(prov, separators=(",", ":"), ensure_ascii=False)


class Sink:

    def __init__(self, out, manifest, provenance, who, renumber, frame_bytes=1 << 20, level=None, summaries=False):
        self.writer = nwt.Writer(out, manifest, who["stream_id"], who["created_ns"], provenance=provenance,
                                 frame_bytes=frame_bytes, zstd_level=level)
        self.renumber, self.summaries = renumber, summaries
        self.sequencer = nwt.Sequencer()
        self.facts, self.pending = [], []

    def add(self, raw):
        b = bytearray(raw)
        scope = (nwt.get(b, 8, 4), nwt.get(b, 12, 4))
        if self.renumber:
            nwt.put(b, 40, 8, self.sequencer.next(*scope))
        else:
            self.sequencer.last[scope] = nwt.get(b, 40, 8)
        closed = len(self.writer.frames)
        self.writer.write_raw(b)
        if len(self.writer.frames) > closed:
            self.facts.append(frame_facts(self.pending))
            self.pending = []
        self.pending.append(bytes(b))

    def finish(self):
        w = self.writer
        w.flush()
        if self.pending:
            self.facts.append(frame_facts(self.pending))
        if self.summaries:
            for info, f in zip(list(w.frames), self.facts):
                w.write(nwt.make_record(
                    SUMMARY, publisher_id=0, channel_id=0, instrument_id=0, sequence=self.sequencer.next(0, 0),
                    data_frame_seq=info.seq, data_frame_offset=info.offset, stored_bytes=info.stored_bytes,
                    codec=info.codec, summary_flags=f["summary_flags"], type_mask=f["type_mask"],
                    min_instrument_id=f["min_instrument_id"], max_instrument_id=f["max_instrument_id"],
                ))
        w.close()


def write_derived(out, paths, stream, tool, note, args):
    refuse_same(out, *paths)
    sources = [head(p) for p in paths]
    facts = Facts()
    for raw in stream():
        facts.add(raw)
    nwt.need(facts.count, "no record to write")
    manifest = derive_manifest([s.manifest for s in sources], facts)
    with atomic(out) as f:
        sink = Sink(f, manifest, derived_provenance(sources, tool, note), identity(args), renumber=True)
        for raw in stream():
            sink.add(raw)
        sink.finish()




def cmd_inspect(args):
    with opened(args.file) as reader:
        frames, counts = [], {}
        for info, raws, _ in reader.scan(decode=False):
            frames.append(info)
            for raw in raws:
                counts[rtype(raw)] = counts.get(rtype(raw), 0) + 1
        h, m, end = reader.header, reader.manifest, reader.end
        null = lambda v: "-" if v == nwt.NULL else str(v)
        lines = [
            f"file {args.file}",
            f"size {reader.size}",
            f"container major={h['major']} minor={h['minor']} stream_id={h['stream_id'].hex()} created_ns={null(h['created_ns'])}",
            f"dataset {m['dataset']}",
            f"producer {m['producer']}",
            f"profile {m['profile']} clock={m['clock']} ordering={m.get('ordering', 'none')}",
        ]
        lines += [f"publisher {p['id']} {p['name']} venue={p['venue']}" for p in m["publishers"]]
        lines += [
            f"schema {s['type']} v{s['version']} {s['name']} required={str(s['required']).lower()}"
            for s in m["schemas"]
        ]
        if reader.provenance is not None:
            lines.append("provenance " + json.dumps(reader.provenance, separators=(",", ":"), ensure_ascii=False))
        lines.append("frame seq kind codec offset stored_bytes raw_bytes records min_event_ns max_event_ns")
        lines += [
            f"{i.seq} {KINDS[i.kind]} {i.codec} {i.offset} {i.stored_bytes} {i.raw_bytes} {i.record_count} "
            f"{null(i.min_event_ns)} {null(i.max_event_ns)}"
            for i in frames
        ]
        lines.append(
            f"end data_frames={end['total_data_frames']} records={end['total_records']} "
            f"status={'normal' if end['status'] == 0 else 'aborted'}"
        )
        lines += [f"records {nwt.S[t]['name']} {n}" for t, n in sorted(counts.items())]
    nwt.emit("".join(line + "\n" for line in lines))


def check_manifest(manifest):
    for s in manifest["schemas"]:
        t = s["type"]
        nwt.need(t != 15 or s["required"], "BOOK_DELTA must be declared required")
        nwt.need(t != SUMMARY or not s["required"], "FRAME_SUMMARY must be declared not required")
        nwt.need(manifest["profile"] != "generic-events" or not 10 <= t <= 19, "types 10-19 need the market-data profile")


def check_summaries(frames, found):
    tail = 0
    while tail < len(frames) and frames[-1 - tail][1]["kinds"] == {SUMMARY}:
        tail += 1
    body = frames[: len(frames) - tail]
    nwt.need(not any(SUMMARY in f["kinds"] for _, f in body), "FRAME_SUMMARY records are not in trailing summary frames")
    if not tail:
        return
    nwt.need(len(found) == len(body), "FRAME_SUMMARY count differs from the number of other DATA frames")
    for (info, f), s in zip(body, found):
        actual = dict(data_frame_seq=info.seq, data_frame_offset=info.offset, stored_bytes=info.stored_bytes,
                      codec=info.codec, **{k: f[k] for k in ("type_mask", "min_instrument_id", "max_instrument_id", "summary_flags")})
        for name, value in actual.items():
            nwt.need(s[name] == value, f"FRAME_SUMMARY for frame {info.seq} disagrees with the file: {name}")


def cmd_validate(args):
    with opened(args.file) as reader:
        check_manifest(reader.manifest)
        state = market_state.MarketState({p["id"] for p in reader.manifest["publishers"]})
        facts, frames, found, records = Facts(), [], [], 0
        for info, raws, decoded in reader.scan():
            if info.kind != 1:
                continue
            for number, (raw, record) in enumerate(zip(raws, decoded), records + 1):
                try:
                    state.apply(record)
                except ValueError as error:
                    name, seq = nwt.S[record["type"]]["name"], record["fields"]["sequence"]
                    raise ValueError(f"record {number} ({name}, sequence {seq}): {error}") from None
                facts.add(raw)
                if record["type"] == SUMMARY:
                    found.append(summary_values(record))
            frames.append((info, frame_facts(raws)))
            records += len(raws)
        nwt.need(reader.end["status"] == 0, "aborted container")
        state.finish()
        claim = reader.manifest.get("ordering", "none")
        nwt.need(facts.holds(claim), f"the manifest declares ordering {claim} but the records are not in that order")
        check_summaries(frames, found)
        print(f"valid records={records} data_frames={len(frames)} summaries={len(found)} ordering={claim}")


def cmd_cat(args):
    with opened(args.file) as reader:
        for _, _, decoded in scan_complete(reader, decode=True):
            nwt.emit("".join(nwt.to_json_line(r, args.pretty) + "\n" for r in decoded))


def cmd_extract(args):
    flt = filters(args)
    match = matcher(flt["types"], None if flt["instruments"] is None else spans(flt["instruments"]), flt["t0"], flt["t1"])
    stream = lambda: (raw for raw in raw_records(args.file) if match(raw))
    note = "records filtered; sequences renumbered per (publisher, channel); FRAME_SUMMARY records dropped"
    write_derived(args.out, [args.file], stream, "extract", note, args)


def keyed(i, stream):
    last = 0
    for n, raw in enumerate(stream):
        t = rtime(raw)
        if t != nwt.NULL:
            nwt.need(t >= last, f"input {i + 1} is not in ts_event order; use --order concat")
            last = t
        yield last, i, n, raw


def cmd_merge(args):
    nwt.need(len(args.files) >= 2, "merge needs at least two input files")
    if args.order == "concat":
        stream = lambda: itertools.chain.from_iterable(raw_records(p) for p in args.files)
    else:
        stream = lambda: (item[3] for item in heapq.merge(*(keyed(i, raw_records(p)) for i, p in enumerate(args.files))))
    note = f"{len(args.files)} inputs merged, policy {args.order}; sequences renumbered per (publisher, channel)"
    write_derived(args.out, args.files, stream, "merge", note, args)


def cmd_split(args):
    day = lambda raw: "no-time" if rtime(raw) == nwt.NULL else nwt.pretty_time(rtime(raw))[:10]
    key_of = {"type": rtype, "instrument": rinst, "day": day}[args.by]
    name_of = {
        "type": lambda k: f"{k:02}-{nwt.S[k]['name'].lower()}.nwt" if k in nwt.S else f"{k}.nwt",
        "instrument": lambda k: f"instrument-{k}.nwt",
        "day": lambda k: f"{k}.nwt",
    }[args.by]
    source = head(args.file)
    groups = {}
    for raw in raw_records(args.file):
        groups.setdefault(key_of(raw), Facts()).add(raw)
    nwt.need(groups, "no record to write")
    os.makedirs(args.dir, exist_ok=True)
    note = f"split by {args.by}; sequences renumbered per (publisher, channel); earlier definitions are not copied"
    keys = sorted(groups)
    for start in range(0, len(keys), 64):
        batch = keys[start : start + 64]
        with ExitStack() as stack:
            sinks = {}
            for k in batch:
                out = stack.enter_context(atomic(os.path.join(args.dir, name_of(k))))
                manifest = derive_manifest([source.manifest], groups[k])
                sinks[k] = Sink(out, manifest, derived_provenance([source], "split", note), identity(args), True)
            for raw in raw_records(args.file):
                if key_of(raw) in sinks:
                    sinks[key_of(raw)].add(raw)
            for sink in sinks.values():
                sink.finish()
    print(f"wrote {len(keys)} files to {args.dir}", file=sys.stderr)


def cmd_repack(args):
    refuse_same(args.out, args.file)
    source = head(args.file)
    facts = Facts()
    for raw in raw_records(args.file):
        facts.add(raw)
    claim = source.manifest.get("ordering", "none")
    nwt.need(facts.holds(claim), f"the input declares ordering {claim} but its records are not in that order")
    summaries_on = not args.no_summary
    manifest = derive_manifest([source.manifest], facts, summaries_on, whole=True)
    provenance = None if source.provenance is None else json.dumps(source.provenance, separators=(",", ":"), ensure_ascii=False)
    level = None if args.raw else args.level
    nwt.need(level is None or 1 <= level <= 22, "--level must be 1 to 22")
    if level is not None and not nwt.zstd_available():
        print("NWT notice: Zstd library not available; writing raw frames", file=sys.stderr)
        level = None
    with atomic(args.out) as f:
        sink = Sink(f, manifest, provenance, identity(args), False, args.frame_bytes, level, summaries_on)
        for raw in raw_records(args.file):
            sink.add(raw)
        sink.finish()


def cmd_query(args):
    with opened(args.file) as reader:
        found = select(reader, **filters(args))
        first = list(itertools.islice(found, 1))
        print("# partial: earlier definitions and book state are not included", file=sys.stderr)
        batch = []
        for raw in itertools.chain(first, found):
            batch.append(nwt.to_json_line(nwt.decode_record(raw), args.pretty) + "\n")
            if len(batch) >= 1000:
                nwt.emit("".join(batch))
                batch = []
        nwt.emit("".join(batch))


def cmd_resolve(args):
    at = None if args.at is None else parse_time(args.at)
    code = SYMBOLOGY.get(args.symbology)
    maps, latest = [], {}
    with opened(args.file) as reader:
        for raw in select(reader, types=[17, 21]):
            r = nwt.decode_record(raw)
            f = r["fields"]
            if args.publisher is not None and int(f["publisher_id"]) != args.publisher:
                continue
            if r["type"] == 17:
                start, end = int(f["valid_from_ns"]), int(f["valid_to_ns"])
                inside = at is None or (start <= at and (end == nwt.NULL or at < end))
                wrong_kind = args.symbology == "cusip" or code not in (None, int(f["symbology"]))
                if r["texts"]["symbol"] == args.symbol and inside and not wrong_kind:
                    maps.append(r)
            else:
                if at is None or f["ts_event"] == str(nwt.NULL) or int(f["ts_event"]) <= at:
                    latest[(f["publisher_id"], f["instrument_id"])] = r
    lines = [
        nwt.json_object([("source", "SYMBOL_MAP")] + [(k, r["fields"][k]) for k in ("publisher_id", "instrument_id")]
                        + [(k, r["fields"][k]) for k in ("symbology", "valid_from_ns", "valid_to_ns")]
                        + [("symbol", r["texts"]["symbol"])])
        for r in maps
    ]
    for r in latest.values():
        for kind, names in IDENTIFIERS.items():
            if args.symbology in (None, kind) and any(r["texts"][n] == args.symbol for n in names):
                lines.append(nwt.json_object(
                    [("source", "SECURITY_DEF")] + [(k, r["fields"][k]) for k in ("publisher_id", "instrument_id")]
                    + [("identifier", kind), ("symbol", r["texts"]["symbol"])]
                    + [(n, r["texts"][n]) for n in ("isin", "cusip", "composite_figi", "figi")]
                ))
    nwt.need(lines, f"no mapping found for {args.symbol}" + (f" at {args.at}" if args.at else ""))
    nwt.emit("".join(line + "\n" for line in lines))


def cmd_stats(args):
    with opened(args.file) as reader:
        per_type, data = {}, [0, 0, 0, 0]
        other = {2: 0, 3: 0}
        for info, raws, _ in reader.scan(decode=False):
            size = 64 + ((info.stored_bytes + 7) & ~7)
            if info.kind == 1:
                data = [data[0] + 1, data[1] + info.codec, data[2] + info.stored_bytes, data[3] + info.raw_bytes]
            else:
                other[info.kind] += size
            for raw in raws:
                row = per_type.setdefault(rtype(raw), [0, 0])
                row[0] += 1
                row[1] += len(raw)
        ratio = "-" if not data[2] else f"{data[3] * 1000 // data[2] // 1000}.{data[3] * 1000 // data[2] % 1000:03}"
        lines = [
            f"file_bytes {reader.size}",
            f"header_and_metadata_bytes {64 + len(reader.metadata)}",
            f"data_frames {data[0]} zstd_frames={data[1]} stored_bytes={data[2]} raw_bytes={data[3]}",
            f"compression_ratio {ratio}  (raw payload bytes / stored payload bytes, DATA frames)",
            f"index_bytes {other[2]}",
            f"end_bytes {other[3]}",
            f"records {sum(n for n, _ in per_type.values())}",
        ]
        lines += [f"type {t} {nwt.S[t]['name']} records={n} record_bytes={b}" for t, (n, b) in sorted(per_type.items())]
    nwt.emit("".join(line + "\n" for line in lines))




def build_parser():
    parser = argparse.ArgumentParser(prog="nwt", description="nwt: inspect, check, filter, repack and query NWT containers.")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def command(name, func, help_, *positional):
        p = sub.add_parser(name, help=help_)
        for arg in positional:
            p.add_argument(arg[0], **(arg[1] if len(arg) > 1 else {}))
        p.set_defaults(func=func)
        return p

    def identity_options(p):
        p.add_argument("--stream-id", metavar="HEX", help="16-byte stream ID as 32 hex digits (default: random)")
        p.add_argument("--created-ns", type=int, metavar="NS", help="creation time (default: now)")

    command("inspect", cmd_inspect, "header, manifest, frame table, record counts", ("file",))
    command("validate", cmd_validate, "structure, semantic rules, summaries, ordering claim", ("file",))
    command("cat", cmd_cat, "records as JSON Lines", ("file",)).add_argument("--pretty", action="store_true")
    p = command("extract", cmd_extract, "filter into a new container", ("file",), ("out",))
    add_filters(p)
    identity_options(p)
    p = command("merge", cmd_merge, "combine containers", ("out",), ("files", dict(nargs="+")))
    p.add_argument("--order", required=True, choices=["concat", "ts_event"], help="concat: inputs one after another; "
                   "ts_event: interleave by event time (every input must already be in ts_event order)")
    identity_options(p)
    p = command("split", cmd_split, "one container per type, instrument or day", ("file",), ("dir",))
    p.add_argument("--by", required=True, choices=["type", "instrument", "day"])
    p = command("repack", cmd_repack, "rewrite as a store file", ("file",), ("out",))
    p.add_argument("--frame-bytes", type=int, default=1 << 20, help="raw bytes per DATA frame (default 1 MiB)")
    p.add_argument("--level", type=int, default=3, help="Zstd level 1-22 (default 3)")
    p.add_argument("--raw", action="store_true", help="no compression")
    p.add_argument("--no-summary", action="store_true", help="do not write FRAME_SUMMARY frames")
    identity_options(p)
    p = command("query", cmd_query, "read only the frames that can match", ("file",))
    add_filters(p)
    p.add_argument("--pretty", action="store_true")
    p = command("resolve", cmd_resolve, "look up a symbol or identifier", ("file",), ("symbol",))
    p.add_argument("--at", metavar="TIME", help="the moment to look up (default: any time)")
    p.add_argument("--symbology", choices=sorted(SYMBOLOGY) + ["cusip"], help="only this kind of symbol")
    p.add_argument("--publisher", type=int, metavar="ID")
    command("stats", cmd_stats, "sizes, bytes per type, compression ratio", ("file",))
    if nwt_convert:
        nwt_convert.register(sub)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args) or 0
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0
    except ERRORS as error:
        print("NWT error: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
