# Store profile

A store file is an NWT container written for fast selective reads: large frames, [Zstandard](https://github.com/facebook/zstd) compression, an `INDEX` and `FRAME_SUMMARY` records. This page shows how to write one, how a reader finds records in it by time, record type and instrument, and how to check it. It is for engineers who keep NWT files in an archive or in object storage and query them.

## What the store profile is

The store profile is a set of choices a writer makes. It is not a second format: a store file has the same container header, the same frames and the same records as any other NWT file, and every NWT reader reads it from the first byte to `END`. A reader that knows the profile answers a query by reading only the frames that can hold a match.

| Setting | Value in a store file | Purpose |
|---|---|---|
| Frame size | 1,048,576 bytes of raw payload by default; at most 16,777,216 | Fewer frame headers, better compression, fewer reads |
| Compression | Zstandard, level 3 by default. A frame that does not shrink is stored raw. | Smaller files |
| `INDEX` | Always written | One entry per `DATA` frame: offset, lowest and highest `ts_event`, raw size and record count |
| `FRAME_SUMMARY` | Always written | Per frame: the record types it holds, the lowest and the highest instrument ID, the stored size and the codec |
| `ordering` | Declared in the manifest when it holds | States that the records are in `ts_event` order, or in instrument and then `ts_event` order |

Records are never reordered. Byte order is the delivery order, and definitions, snapshots and trade corrections depend on it. Writing a store file changes the framing and the compression, and nothing else about the records.

Zstandard frames need the system [libzstd](https://github.com/facebook/zstd) (Python, C#, C++) or the [zstd](https://github.com/gyscos/zstd-rs) crate (Rust). Raw frames need no library. The Specification defines the profile in [Store profile](SPECIFICATION.md#store-profile).

## When to use it

Use the store profile for a complete file that is read many times and queried by time, by record type or by instrument: a daily archive, an object in a bucket that is read with range requests, a research file on disk.

Write an ordinary container while a feed is live, and repack it as a store file when it is closed. The `INDEX`, the summaries and the `ordering` declaration describe the whole file, so a writer produces them when the last record is known.

A consumer that replays a whole file reads a store file like any other container.

## Write a store file

### With the nwt command

[repack](TOOLS.md#repack) rewrites any container as a store file.

```bash
mkdir -p work
python3 tools/nwt.py repack fixtures/real-market/equity-quotes.nwt work/equity-quotes.store.nwt --frame-bytes 65536
python3 tools/nwt.py validate work/equity-quotes.store.nwt
```

```text
valid records=2481 data_frames=5 summaries=4 ordering=ts_event
```

The input is the sample [equity-quotes.nwt](files/samples/equity-quotes.nwt), 251,520 bytes with 2,477 records. With the default frame size it fits in one `DATA` frame. `--frame-bytes 65536` gives four frames of records, so the examples on this page have frames to skip.

`repack` works in two passes:

1. It reads the whole input, checks its structure and finds out which `ordering` holds. The manifest carries the declaration, and the manifest is written before the first frame.
2. It writes the header, the metadata, the `DATA` frames, one `FRAME_SUMMARY` record for each of them, the `INDEX` and `END`.

The output has the same records in the same order with the same sequences, and a new stream ID. Its `minor` is 1, because the manifest declares `FRAME_SUMMARY`, type 20, with `required` false. `repack` writes to `OUT.tmp` and renames the file when it is complete.

When `libzstd` is not available, `repack` prints `NWT notice: Zstd library not available; writing raw frames` on standard error and writes raw frames. The rest of the profile stays in place.

### From Python

`tools/nwt.py` is importable. `main` runs any command of the tool and returns its exit status:

```python
import sys
sys.path[:0] = ["tools", "examples/python"]
import nwt as tool

status = tool.main(["repack", "fixtures/real-market/equity-quotes.nwt",
                    "work/equity-quotes.store.nwt", "--frame-bytes", "65536"])
```

To write a store file from records you produce yourself, use the classes behind `repack`. `Facts` tracks the record types and the orderings that hold, and `Sink` writes the frames, the summaries, the `INDEX` and `END`. This program writes one instrument definition and 5,000 trades:

```python
import os, sys, time
sys.path[:0] = ["tools", "examples/python"]
import nwt_example as codec
import nwt as tool

start = 1_758_000_000_000_000_000                 # 2025-09-16T05:20:00Z
records = [codec.make_record(
    6, instrument_id=1001, ts_event=start, sequence=1,
    price_increment=10_000_000, quantity_increment=1_000_000_000, contract_multiplier=codec.NULL_I64,
    expiration_ns=codec.NULL, underlying_instrument_id=0, strike=codec.NULL_I64, asset_class=1,
    texts={"symbol": "NWTX", "venue": "XNAS", "currency": "USD", "quantity_unit": "share"},
)]
for i in range(1, 5001):                          # one trade per millisecond
    records.append(codec.make_record(
        1, instrument_id=1001, ts_event=start + i * 1_000_000, sequence=1,
        price=124_250_000_000 + i * 10_000_000, quantity=100_000_000_000, trade_id=i,
        original_sequence=0, action=1, aggressor=0, conditions=0,
    ))
raws = [codec.encode_record(r) for r in records]

facts = tool.Facts()                              # record types present and the orderings that hold
for raw in raws:
    facts.add(raw)
ordering = facts.ordering()
manifest = codec.build_manifest(
    "EXAMPLE.STORE", "my-writer/1", [{"id": 1, "name": "Example Feed", "venue": "XNAS"}],
    types=facts.types | {20}, ordering=None if ordering == "none" else ordering,
)
identity = dict(stream_id=os.urandom(16), created_ns=time.time_ns())
level = 3 if codec.zstd_available() else None     # None writes raw frames

with tool.atomic("work/trades.store.nwt") as out:
    sink = tool.Sink(out, manifest, None, identity, renumber=True,
                     frame_bytes=65536, level=level, summaries=True)
    for raw in raws:
        sink.add(raw)
    sink.finish()
```

`renumber=True` makes the sink assign the sequences, so the value passed to `make_record` is a placeholder. Type 20 in `types` declares `FRAME_SUMMARY` in the manifest. Check the result:

```bash
python3 tools/nwt.py validate work/trades.store.nwt
```

```text
valid records=5008 data_frames=8 summaries=7 ordering=ts_event
```

## File layout

| Part | Content |
|---|---|
| Container header and metadata | The 64-byte header, the `MANIFEST` and, when the source had one, the `PROVENANCE` |
| `DATA` frames with records | The records, in their original order |
| Summary frames | `DATA` frames that hold `FRAME_SUMMARY` records and nothing else: one record for each frame above, in ascending frame order |
| `INDEX` frames | One 40-byte entry per `DATA` frame, summary frames included |
| `END` frame | 96 bytes at the end of the file: the offset of the first `INDEX` frame and the totals |

The frame table of [inspect](TOOLS.md#inspect) shows the layout of the file written above:

```bash
python3 tools/nwt.py inspect work/equity-quotes.store.nwt | tail -n 13
```

```text
frame seq kind codec offset stored_bytes raw_bytes records min_event_ns max_event_ns
0 DATA 1 2120 9605 65480 652 1758006306677514564 1758009758289670910
1 DATA 1 11792 9221 65520 652 1758009758289672303 1758009809048757997
2 DATA 1 21080 8735 65496 647 1758009809049258043 1758009844980010260
3 DATA 1 29880 7493 52752 526 1758009844980046859 1758009883915993953
4 DATA 1 37440 102 416 4 - -
5 INDEX 0 37608 200 200 0 - -
6 END 0 37872 32 32 0 - -
end data_frames=5 records=2481 status=normal
records QUOTE 2000
records INSTRUMENT_DEF 1
records TRADE_QUOTE 476
records FRAME_SUMMARY 4
```

Frames 0–3 hold the records. Frame 4 is the summary frame: 4 records of 104 bytes, with `-` for both time bounds because a `FRAME_SUMMARY` has no event time. Codec 1 is Zstandard. The stored sizes and the offsets after frame 0 depend on the version of the Zstandard library.

A `FRAME_SUMMARY` record is 104 bytes. Its publisher, channel and instrument are 0, and both timestamps are null.

| Field | Meaning |
|---|---|
| `data_frame_seq` | `frame_seq` of the frame it describes |
| `data_frame_offset` | Offset of that frame from byte 0 of the container |
| `stored_bytes` | Payload size of that frame as stored, after compression |
| `codec` | 0 raw, 1 Zstandard |
| `type_mask` | Bit n, for n from 1 to 63, is set when record type n occurs in the frame. Bit 0 is set when any other type occurs. |
| `min_instrument_id`, `max_instrument_id` | Lowest and highest non-zero instrument ID in the frame. Both are 0 when the frame has none. |
| `summary_flags` | Bit 0: some `ts_event` in the frame is null. Bit 1: the non-null `ts_event` values do not decrease within the frame. |

The first summary of the file describes frame 0:

```bash
python3 tools/nwt.py query work/equity-quotes.store.nwt --type FRAME_SUMMARY 2> /dev/null | head -n 1
```

```text
{"type_name":"FRAME_SUMMARY","record_bytes":"104","record_type":"20","schema_version":"1","flags":"0","publisher_id":"0","channel_id":"0","instrument_id":"0","ts_event":"18446744073709551615","ts_recv":"18446744073709551615","sequence":"1","data_frame_seq":"0","data_frame_offset":"2120","stored_bytes":"9605","codec":"1","summary_flags":"2","type_mask":"262212","min_instrument_id":"11667","max_instrument_id":"11667"}
```

`type_mask` 262212 is 2¹⁸ + 2⁶ + 2²: the frame holds `TRADE_QUOTE`, `INSTRUMENT_DEF` and `QUOTE` records. The masks of frames 1–3 are 262148, without the bit of `INSTRUMENT_DEF`. The Specification defines the record in [FRAME_SUMMARY](SPECIFICATION.md#frame_summary).

## How a reader seeks by time and instrument

A reader needs one operation: read n bytes at an offset. With it, the reader answers a query in five steps.

![In a store file a reader goes from the END frame to the INDEX frames, then to the summary frames, and reads only the DATA frames that can hold a match](diagrams/selective-read.svg "From END to INDEX to the summaries, then to the chosen frames")

1. Read the last 96 bytes of the file, the `END` frame, and validate it. It gives the offset of the first `INDEX` frame and the number of `DATA` frames.
2. Read the `INDEX` frames, which lie between that offset and `END`. Each 40-byte entry gives the offset of a `DATA` frame, its lowest and highest `ts_event`, its raw size and its record count.
3. Walk back from the last `DATA` frame while the entry looks like a summary frame: null time bounds and a raw size of 104 bytes per record. Read those frames and check that they hold `FRAME_SUMMARY` records only.
4. Keep a frame when it can hold a match:
   - **Time.** With a time bound, a frame is kept when its range from lowest to highest `ts_event` can overlap the requested range. A frame with null bounds holds only records without an event time; a null time never matches a time bound, so the frame is skipped.
   - **Record type.** The `type_mask` of the frame shares a bit with the requested types.
   - **Instrument.** A requested ID or range overlaps the range from `min_instrument_id` to `max_instrument_id`. The summary does not cover instrument 0, so a request that includes 0 never skips a frame on this test.
5. Read each kept frame in file order, check its header, its payload and its CRC-32C, split it into records and apply the filter to every record.

The result equals a full scan with the same filter: the same records in the same order. `select` in `tools/nwt.py` is the implementation:

<!-- nwt-file: tools/nwt.py lines=204-220 -->

A file without `FRAME_SUMMARY` records is read the same way with the time test alone. A container with `DATA` frames and no `INDEX` is read from the first byte with [cat](TOOLS.md#cat) or [extract](TOOLS.md#extract).

### Time order and binary search

The time ranges of frames can overlap and go backward, so a reader looks at every `INDEX` entry. A manifest that declares `"ordering": "ts_event"` states that the non-null `ts_event` values do not decrease in byte order across the whole container. The ranges of the entries are then monotonic, and a binary search by time is valid. `"ordering": "instrument,ts_event"` states that the records are ordered by instrument ID and then by `ts_event`. Records with a null `ts_event` are exempt from both.

`repack` declares an `ordering` only when the records have it, and [validate](TOOLS.md#validate) checks every declaration it finds. The `nwt` command reads all entries in order: after step 2 they are in memory.

### Over any byte source

`nwt_example.Reader` takes a function `read_at(offset, n)` and the size of the object, so the same code runs on a local file, on a memory-mapped file and on HTTP range requests. This program uses a byte string in place of a remote object and counts what the reader asks for:

```python
import sys
sys.path[:0] = ["tools", "examples/python"]
import nwt_example
import nwt as tool

def measure(path, **query):
    data = open(path, "rb").read()          # stands in for a remote object
    fetched = []

    def read_at(offset, n):                 # replace with an HTTP Range request
        fetched.append(n)
        return data[offset : offset + n]

    reader = nwt_example.Reader(read_at, len(data))
    found = list(tool.select(reader, **query))
    print(f"{len(found)} records; {sum(fetched)} of {len(data)} bytes in {len(fetched)} reads")

measure("work/equity-quotes.store.nwt", types=[18],
        t0=tool.parse_time("2025-09-16T08:03:00Z"), t1=tool.parse_time("2025-09-16T08:04:00Z"))
measure("work/equity-quotes.store.nwt", types=[6])
```

```text
228 records; 20736 of 37968 bytes in 12 reads
1 records; 12320 of 37968 bytes in 10 reads
```

The first query is for `TRADE_QUOTE` records of one minute. The minute lies in frames 1 and 2, so the reader fetches `END`, the `INDEX`, the summary frame and those two frames. The second query is for `INSTRUMENT_DEF` records: only the mask of frame 0 has that bit. The byte counts follow the stored sizes, which depend on the version of the Zstandard library.

## What a partial read returns

A selective read returns the matching records of the frames it read, and nothing of the frames it skipped. The instrument definitions, the snapshots and the trade history before the first frame it read are not part of the result. Such a result is raw and partial: it is not a reconstructed book, and a reader labels it so.

[query](TOOLS.md#query) writes this label on standard error before the first record:

```bash
python3 tools/nwt.py query work/equity-quotes.store.nwt --type TRADE_QUOTE --from 2025-09-16T08:03:04.5303Z --to 2025-09-16T08:03:04.5304Z --pretty
```

```text
# partial: earlier definitions and book state are not included
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530356100Z","ts_recv":"2025-09-16T08:03:04.530521940Z","sequence":"734","price":"177.290000000","quantity":"78.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530358866Z","ts_recv":"2025-09-16T08:03:04.530522753Z","sequence":"736","price":"177.290000000","quantity":"250.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
```

The sequences 734 and 736 are those of the file. The record with sequence 735 is a `QUOTE`, so it is not part of this selection.

To turn a selection into data you can interpret:

1. Read the definitions too. `--type INSTRUMENT_DEF` returns them, and their frames are found through the type mask.
2. For a book, read every frame from the last snapshot of that book, in file order, and replay the records. [State and recovery](STATE-AND-RECOVERY.md#selective-reads-summaries-and-state) lists the frames each question needs.
3. For a file you hand to someone else, use [extract](TOOLS.md#extract). It reads the whole input and writes a new container with its own stream ID and sequences.

## Choose settings

| Setting | Option of `repack` | Guidance |
|---|---|---|
| Frame size | `--frame-bytes N`, from 48 to 16777216 | A larger frame compresses better and needs fewer reads for a long range. A query reads a whole frame even when one record matches, so a smaller frame serves narrow queries with fewer bytes. A record larger than the frame size gets a frame of its own. |
| Zstandard level | `--level N`, from 1 to 22 | A higher level gives a smaller file and a slower write. The level does not change how the file is read. |
| Raw frames | `--raw` | Writes every frame raw. Use it when readers run without a Zstandard library. |
| Summaries | `--no-summary` | Leaves out the `FRAME_SUMMARY` frames. Readers then skip frames by time only. |

Only `DATA` frames are compressed, and only when the compressed form is smaller. `INDEX` and `END` are always raw, so a reader finds them without a codec. Two writers with different versions of the Zstandard library produce different compressed bytes for the same records, so compare decoded records, not compressed files.

## Check a store file

[validate](TOOLS.md#validate) reads the whole file and checks the structure, the state rules, the `ordering` declaration and every value of every `FRAME_SUMMARY` record against the frame it describes.

```bash
python3 tools/nwt.py validate work/equity-quotes.store.nwt
```

```text
valid records=2481 data_frames=5 summaries=4 ordering=ts_event
```

[stats](TOOLS.md#stats) shows how many frames are compressed and what the compression saved:

```bash
python3 tools/nwt.py stats work/equity-quotes.store.nwt
```

```text
file_bytes 37968
header_and_metadata_bytes 2120
data_frames 5 zstd_frames=5 stored_bytes=35156 raw_bytes=249664
compression_ratio 7.101  (raw payload bytes / stored payload bytes, DATA frames)
index_bytes 264
end_bytes 96
records 2481
type 2 QUOTE records=2000 record_bytes=192000
type 6 INSTRUMENT_DEF records=1 record_bytes=128
type 18 TRADE_QUOTE records=476 record_bytes=57120
type 20 FRAME_SUMMARY records=4 record_bytes=416
```

A file that was cut off fails every command with a reason that starts with `incomplete`. A seek needs the `END` frame at the end of the file:

```bash
head -c 30000 work/equity-quotes.store.nwt > work/cut.nwt
python3 tools/nwt.py query work/cut.nwt --type QUOTE
```

```text
NWT error: incomplete: no END frame at the end of the file
```

The command exits with status 1 and prints no record.
