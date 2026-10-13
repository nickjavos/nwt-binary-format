# How a reader seeks by time and instrument

A reader needs one operation: read n bytes at an offset. With it, the reader answers a query in five steps.

![In a store file a reader goes from the END frame to the INDEX frames, then to the summary frames, and reads only the DATA frames that can hold a match](../diagrams/selective-read.svg "From END to INDEX to the summaries, then to the chosen frames")

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

A file without `FRAME_SUMMARY` records is read the same way with the time test alone. A container with `DATA` frames and no `INDEX` is read from the first byte with [cat](../tools/cat.md) or [extract](../tools/extract.md).

## Time order and binary search

The time ranges of frames can overlap and go backward, so a reader looks at every `INDEX` entry. A manifest that declares `"ordering": "ts_event"` states that the non-null `ts_event` values do not decrease in byte order across the whole container. The ranges of the entries are then monotonic, and a binary search by time is valid. `"ordering": "instrument,ts_event"` states that the records are ordered by instrument ID and then by `ts_event`. Records with a null `ts_event` are exempt from both.

`repack` declares an `ordering` only when the records have it, and [validate](../tools/validate.md) checks every declaration it finds. The `nwt` command reads all entries in order: after step 2 they are in memory.

## Over any byte source

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
