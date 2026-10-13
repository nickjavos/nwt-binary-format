#!/usr/bin/env python3
"""nwt: inspect, check, filter, repack and query NWT containers.

    python3 tools/nwt.py COMMAND ...

    inspect FILE                      header, manifest, frame table, record counts by type
    validate FILE                     structure, semantic rules, summaries and the ordering claim
    cat FILE [--pretty]               every record as one JSON object per line
    extract FILE OUT [filters]        a new container holding the records that match the filters
    merge OUT FILE... --order POLICY  combine containers under an explicit ordering policy
    split FILE DIR --by KEY           one container per type, instrument or day
    repack FILE OUT                   re-frame and recompress as a store file (same records, same order)
    query FILE [filters]              read only the frames that can match, using END, INDEX and FRAME_SUMMARY
    resolve FILE SYMBOL               look up a symbol, ISIN, CUSIP or FIGI from SYMBOL_MAP and SECURITY_DEF
    stats FILE                        sizes, bytes per type, compression ratio
    convert KIND SRC OUT              source file to container (present when tools/nwt_convert.py is)

Filters: --type 2,TRADE   --instrument 2001,3000-3999   --from TIME   --to TIME (half open: from <= ts_event < to).
TIME is nanoseconds since 1970, a date (2025-09-16) or a UTC timestamp (2025-09-16T11:05:00Z).

No command reorders records. extract, merge and split write new containers: new stream ID, sequences renumbered
per (publisher, channel) from 1. Every failure prints "NWT error: ..." on stderr and exits with status 1.
"""

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
import market_state  # noqa: E402
import nwt_example as nwt  # noqa: E402
from nwt_parse import parse_date_ns, parse_timestamp_ns  # noqa: E402

try:
    import nwt_convert
except ModuleNotFoundError as error:
    if error.name != "nwt_convert":
        raise
    nwt_convert = None

ERRORS = (ValueError, KeyError, OverflowError, UnicodeError, OSError)
SUMMARY = 20  # FRAME_SUMMARY
SYMBOLOGY = {"native": 1, "osi": 2, "isin": 3, "figi": 4, "root": 5, "continuous": 6}
IDENTIFIERS = {"isin": ("isin",), "cusip": ("cusip",), "figi": ("composite_figi", "figi")}  # SECURITY_DEF texts
SUMMARY_FRAME = {"type_mask": 1 << SUMMARY, "min_instrument_id": 0, "max_instrument_id": 0}
KINDS = {1: "DATA", 2: "INDEX", 3: "END"}


# ----------------------------------------------------------- record header fields


def rtype(raw):
    return nwt.get(raw, 4, 2)


def rinst(raw):
    return nwt.get(raw, 16, 8)


def rtime(raw):
    return nwt.get(raw, 24, 8)


def type_bit(t):
    """FRAME_SUMMARY type_mask bit for a record type: bit n for types 1-63, bit 0 for any other."""
    return 1 << (t if 1 <= t <= 63 else 0)


# --------------------------------------------------------------- command arguments


def parse_types(text):
    names = {s["name"]: t for t, s in nwt.S.items()}
    out = []
    for part in text.split(","):
        part = part.strip()
        nwt.need(part.upper() in names or part.isdigit(), f"unknown record type {part!r}")
        out.append(names.get(part.upper()) or int(part))
    return out


def parse_instruments(text):
    """'2001,3000-3999' -> [2001, (3000, 3999)]"""
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
    """The select() keyword arguments given on the command line."""
    given = lambda value, parse: None if value is None else parse(value)  # noqa: E731
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


# ------------------------------------------------------------------ reading files


@contextmanager
def opened(path):
    with open(path, "rb") as f:
        yield nwt.open_reader(f)


def head(path):
    """A Reader with header and metadata checked; its file is already closed, so only the metadata is usable."""
    with opened(path) as reader:
        return reader


def scan_complete(reader, decode=False):
    """reader.scan() plus the check of nwt.complete_records: an aborted END is an error after the last frame."""
    yield from reader.scan(decode=decode)
    nwt.need(reader.end["status"] == 0, "aborted container")


def raw_records(path):
    """Every record of a complete container, in order, except FRAME_SUMMARY records: they describe the old framing."""
    with opened(path) as reader:
        summaries_seen = False
        for _, raws, _ in scan_complete(reader):
            for raw in raws:
                if rtype(raw) == SUMMARY:
                    summaries_seen = True
                else:
                    nwt.need(not summaries_seen, "FRAME_SUMMARY records are not at the end of the container")
                    yield raw


# ----------------------------------------------- what a FRAME_SUMMARY says, and the seek path


def frame_facts(raws):
    """What a FRAME_SUMMARY states about one DATA frame, computed from the frame's records."""
    kinds = {rtype(r) for r in raws}
    ids = [i for i in map(rinst, raws) if i]
    times = [t for t in map(rtime, raws) if t != nwt.NULL]
    return dict(
        kinds=kinds,
        type_mask=sum({type_bit(t) for t in kinds}),
        min_instrument_id=min(ids, default=0),
        max_instrument_id=max(ids, default=0),
        # bit 0: some ts_event is null; bit 1: the non-null ones are non-decreasing (true for none or one)
        summary_flags=int(len(times) < len(raws)) | int(all(a <= b for a, b in zip(times, times[1:]))) << 1,
    )


def summary_values(record):
    """{field name: int} of a decoded FRAME_SUMMARY, reserved fields left out."""
    return {f["name"]: int(record["fields"][f["name"]]) for f in nwt.S[SUMMARY]["fields"] if f["name"] != "reserved"}


def summary_frames(reader, index):
    """Raw records of each trailing DATA frame that holds FRAME_SUMMARY records only, in file order.

    Walks back from the last frame. A summary record is 104 bytes with a null ts_event, so an INDEX entry
    that does not look like that is never read."""
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
    """The FRAME_SUMMARY records of a store file, found through END, INDEX and the last frames only.

    One dict per described DATA frame, in frame order, with the record's fields as ints: data_frame_seq,
    data_frame_offset, stored_bytes, codec, summary_flags, type_mask, min_instrument_id, max_instrument_id.
    [] when the file has none."""
    tail = summary_frames(reader, reader.index())
    return [summary_values(nwt.decode_record(raw)) for raws in tail for raw in raws]


def plan(reader):
    """(INDEX entry, summary dict or None) for every DATA frame, summary frames included."""
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
    """[7, (100, 199)] -> [(7, 7), (100, 199)]"""
    return [(i, i) if isinstance(i, int) else tuple(i) for i in instruments]


def matcher(types=None, ranges=None, t0=None, t1=None):
    """Record predicate shared by select() and extract. ranges come from spans(). With a time bound,
    a record whose ts_event is null never matches."""
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
    """False only when the summary proves that no record of the frame is in the ranges.
    The summary ignores instrument 0, so a range that includes 0 can never be ruled out."""
    lo, hi = s["min_instrument_id"], s["max_instrument_id"]
    return any(a == 0 or (hi != 0 and a <= hi and lo <= b) for a, b in ranges)


def select(reader, types=None, instruments=None, t0=None, t1=None):
    """Raw records that match, in file order, reading only the frames that can contain a match.

    types: iterable of record types. instruments: iterable of IDs or (low, high) pairs, both ends included.
    t0 <= ts_event < t1, either bound optional; a null ts_event never matches a time bound.
    Uses END, INDEX and, when the file has them, FRAME_SUMMARY records. The result equals filtering a full scan."""
    ranges = None if instruments is None else spans(instruments)
    match = matcher(types, ranges, t0, t1)
    want = None if types is None else sum({type_bit(t) for t in types})
    for entry, s in plan(reader):
        if t0 is not None or t1 is not None:
            if entry.min_event_ns == nwt.NULL:  # only null event times in the frame
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


# ------------------------------------------------------------ what a record stream is


class Facts:
    """What one pass over a record stream learns: types, counts and which ordering claims are true."""

    def __init__(self):
        self.count, self.types = 0, set()
        self.by_ts = self.by_instrument = True
        self.last_ts, self.last_key = 0, (0, 0)

    def add(self, raw):
        self.count += 1
        self.types.add(rtype(raw))
        t = rtime(raw)
        if t != nwt.NULL:  # records without an event time are exempt
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


# ---------------------------------------------------------------- writing files


@contextmanager
def atomic(path):
    """Write to PATH.tmp and rename when done, so a failed command never leaves a half-written file."""
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
    """A new stream ID (random unless --stream-id) and creation time (now unless --created-ns)."""
    stream_id = bytes.fromhex(getattr(args, "stream_id", None) or "") or os.urandom(16)
    return dict(stream_id=stream_id, created_ns=getattr(args, "created_ns", None) or time.time_ns())


def derive_manifest(manifests, facts, summaries_on=False, whole=False):
    """MANIFEST text for a container made from the given source manifests.

    whole=False declares only the types actually written (all publishers are kept: BEST_QUOTE may name any of
    them as a venue). whole=True keeps the source's schemas, for repack. summaries_on declares type 20, not required."""
    m = dict(manifests[0])
    if len(manifests) > 1:
        for key in ("dataset", "producer"):
            m[key] = "+".join(dict.fromkeys(x[key] for x in manifests))
    pool = {}
    for x in manifests:
        for s in x["schemas"]:
            pool.setdefault((s["type"], s["version"]), s)
    schemas = [s for s in manifests[0]["schemas"] if s["type"] != SUMMARY] if whole else [pool[(t, 1)] for t in sorted(facts.types)]
    schemas = [dict(s, required=True) if s["type"] == 15 else s for s in schemas]  # BOOK_DELTA must be required
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
    """PROVENANCE text for extract, merge and split: the source's own (when there is one source) plus what was done."""
    prov = dict(sources[0].provenance or {}) if len(sources) == 1 else {}
    prov.update(
        derived_by="tools/nwt.py " + tool,
        derived_note=note,
        source_stream_ids=",".join(s.header["stream_id"].hex() for s in sources),
    )
    return json.dumps(prov, separators=(",", ":"), ensure_ascii=False)


class Sink:
    """One container being written. add() takes raw records in order; finish() closes it.

    renumber=True gives sequences 1, 2, ... per (publisher, channel); False keeps the records' own, which must be
    contiguous. summaries=True ends the file with FRAME_SUMMARY frames that describe every other DATA frame."""

    def __init__(self, out, manifest, provenance, who, renumber, frame_bytes=1 << 20, level=None, summaries=False):
        self.writer = nwt.Writer(out, manifest, who["stream_id"], who["created_ns"], provenance=provenance,
                                 frame_bytes=frame_bytes, zstd_level=level)  # fmt: skip
        self.renumber, self.summaries = renumber, summaries
        self.sequencer = nwt.Sequencer()
        self.facts, self.pending = [], []  # facts of each closed frame; raw records of the open frame

    def add(self, raw):
        b = bytearray(raw)
        scope = (nwt.get(b, 8, 4), nwt.get(b, 12, 4))
        if self.renumber:
            nwt.put(b, 40, 8, self.sequencer.next(*scope))
        else:
            self.sequencer.last[scope] = nwt.get(b, 40, 8)
        closed = len(self.writer.frames)
        self.writer.write_raw(b)
        if len(self.writer.frames) > closed:  # the writer closed the earlier records' frame before taking this one
            self.facts.append(frame_facts(self.pending))
            self.pending = []
        self.pending.append(bytes(b))

    def finish(self):
        w = self.writer
        w.flush()
        if self.pending:
            self.facts.append(frame_facts(self.pending))
        if self.summaries:
            for info, f in zip(list(w.frames), self.facts):  # summary frames are not described by themselves
                w.write(nwt.make_record(
                    SUMMARY, publisher_id=0, channel_id=0, instrument_id=0, sequence=self.sequencer.next(0, 0),
                    data_frame_seq=info.seq, data_frame_offset=info.offset, stored_bytes=info.stored_bytes,
                    codec=info.codec, summary_flags=f["summary_flags"], type_mask=f["type_mask"],
                    min_instrument_id=f["min_instrument_id"], max_instrument_id=f["max_instrument_id"],
                ))  # fmt: skip
        w.close()


def write_derived(out, paths, stream, tool, note, args):
    """extract and merge: two passes over stream() (the first finds the types, so the manifest is exact)."""
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


# --------------------------------------------------------------------- commands


def cmd_inspect(args):
    with opened(args.file) as reader:
        frames, counts = [], {}
        for info, raws, _ in reader.scan(decode=False):
            frames.append(info)
            for raw in raws:
                counts[rtype(raw)] = counts.get(rtype(raw), 0) + 1
        h, m, end = reader.header, reader.manifest, reader.end
        null = lambda v: "-" if v == nwt.NULL else str(v)  # noqa: E731
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
    """Registry rules that depend on the manifest alone."""
    for s in manifest["schemas"]:
        t = s["type"]
        nwt.need(t != 15 or s["required"], "BOOK_DELTA must be declared required")
        nwt.need(t != SUMMARY or not s["required"], "FRAME_SUMMARY must be declared not required")
        nwt.need(manifest["profile"] != "generic-events" or not 10 <= t <= 19, "types 10-19 need the market-data profile")


def check_summaries(frames, found):
    """frames: (FrameInfo, frame_facts) per DATA frame; found: the FRAME_SUMMARY records' values in file order."""
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
                      codec=info.codec, **{k: f[k] for k in ("type_mask", "min_instrument_id", "max_instrument_id", "summary_flags")})  # fmt: skip
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
    stream = lambda: (raw for raw in raw_records(args.file) if match(raw))  # noqa: E731
    note = "records filtered; sequences renumbered per (publisher, channel); FRAME_SUMMARY records dropped"
    write_derived(args.out, [args.file], stream, "extract", note, args)


def keyed(i, stream):
    """(ts_event, input number, position, record) with a null ts_event inheriting the one before it in its input."""
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
        stream = lambda: itertools.chain.from_iterable(raw_records(p) for p in args.files)  # noqa: E731
    else:
        stream = lambda: (item[3] for item in heapq.merge(*(keyed(i, raw_records(p)) for i, p in enumerate(args.files))))  # noqa: E731
    note = f"{len(args.files)} inputs merged, policy {args.order}; sequences renumbered per (publisher, channel)"
    write_derived(args.out, args.files, stream, "merge", note, args)


def cmd_split(args):
    day = lambda raw: "no-time" if rtime(raw) == nwt.NULL else nwt.pretty_time(rtime(raw))[:10]  # noqa: E731
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
    for start in range(0, len(keys), 64):  # at most 64 output files open at a time
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
    print("# partial: earlier definitions and book state are not included", file=sys.stderr)
    with opened(args.file) as reader:
        batch = []
        for raw in select(reader, **filters(args)):
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
            else:  # the latest SECURITY_DEF of a listing, as of --at, states its current identifiers
                if at is None or f["ts_event"] == str(nwt.NULL) or int(f["ts_event"]) <= at:
                    latest[(f["publisher_id"], f["instrument_id"])] = r
    lines = [
        nwt.json_object([("source", "SYMBOL_MAP")] + [(k, r["fields"][k]) for k in ("publisher_id", "instrument_id")]
                        + [(k, r["fields"][k]) for k in ("symbology", "valid_from_ns", "valid_to_ns")]
                        + [("symbol", r["texts"]["symbol"])])
        for r in maps
    ]  # fmt: skip
    for r in latest.values():
        for kind, names in IDENTIFIERS.items():
            if args.symbology in (None, kind) and any(r["texts"][n] == args.symbol for n in names):
                lines.append(nwt.json_object(
                    [("source", "SECURITY_DEF")] + [(k, r["fields"][k]) for k in ("publisher_id", "instrument_id")]
                    + [("identifier", kind), ("symbol", r["texts"]["symbol"])]
                    + [(n, r["texts"][n]) for n in ("isin", "cusip", "composite_figi", "figi")]
                ))  # fmt: skip
    nwt.need(lines, f"no mapping found for {args.symbol}" + (f" at {args.at}" if args.at else ""))
    nwt.emit("".join(line + "\n" for line in lines))


def cmd_stats(args):
    with opened(args.file) as reader:
        per_type, data = {}, [0, 0, 0, 0]  # DATA frames: count, Zstd frames, stored bytes, raw bytes
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


# ------------------------------------------------------------------ command line


def build_parser():
    parser = argparse.ArgumentParser(prog="nwt", description=__doc__.split("\n\n")[0])
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
                   "ts_event: interleave by event time (every input must already be in ts_event order)")  # fmt: skip
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
    except BrokenPipeError:  # for example `cat | head`
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0
    except ERRORS as error:
        print("NWT error: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
