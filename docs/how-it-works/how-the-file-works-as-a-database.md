# How the file works as a database

A store file answers a query the way a database does: it consults a catalogue first and reads only the blocks the catalogue points to. The blocks are the `DATA` frames. The catalogue is the `FRAME_SUMMARY` records and the `INDEX` frame, which say where every frame starts, which time range it covers, and which record types and instruments it holds. The `END` frame is always the last 96 bytes of the file, and it tells the reader where the `INDEX` begins.

![Records are grouped into DATA frames with a checksum and optional compression; the summary frame and the INDEX frame describe every frame; a query for one minute reads END, INDEX, the summaries and two of four DATA frames](../diagrams/storage.svg "A store file: the frames, the summaries and the index that describe them, and one query")

The diagram shows a real file. The `repack` command writes it from the sample [equity-quotes.nwt](files/samples/equity-quotes.nwt), and `--frame-bytes 65536` makes the frames small enough to get four of them:

```bash
python3 tools/nwt.py repack fixtures/real-market/equity-quotes.nwt work/equity-quotes.store.nwt --frame-bytes 65536
```

The frame table of `inspect` lists the parts of the file with their offsets:

```bash
python3 tools/nwt.py inspect work/equity-quotes.store.nwt | tail -n 13 | head -n 8
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
```

Frames 0 to 3 hold the records, and frame 4 is the summary frame. This query asks for the `TRADE_QUOTE` records of one minute and prints the first of them:

```bash
python3 tools/nwt.py query work/equity-quotes.store.nwt --type TRADE_QUOTE --from 2025-09-16T08:03:00Z --to 2025-09-16T08:04:00Z --pretty | head -n 1
```

```text
# partial: earlier definitions and book state are not included
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530356100Z","ts_recv":"2025-09-16T08:03:04.530521940Z","sequence":"734","price":"177.290000000","quantity":"78.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
```

The next program runs the same query through a function that records every read, so the output shows what the reader fetched:

```python
import sys
sys.path[:0] = ["tools", "examples/python"]
import nwt_example
import nwt as tool

data = open("work/equity-quotes.store.nwt", "rb").read()
reads = []

def read_at(offset, n):                  # the only way the reader touches the file
    reads.append((offset, n))
    return data[offset : offset + n]

reader = nwt_example.Reader(read_at, len(data))
found = list(tool.select(reader, types=[18],     # 18 is TRADE_QUOTE
                         t0=tool.parse_time("2025-09-16T08:03:00Z"),
                         t1=tool.parse_time("2025-09-16T08:04:00Z")))
for offset, n in reads:
    print(f"read {n:5} bytes at offset {offset}")
print(f"{len(found)} records; {sum(n for _, n in reads)} of {len(data)} bytes")
```

```text
read    64 bytes at offset 0
read  2056 bytes at offset 64
read    64 bytes at offset 37872
read    32 bytes at offset 37936
read    64 bytes at offset 37608
read   200 bytes at offset 37672
read    64 bytes at offset 37440
read   104 bytes at offset 37504
read    64 bytes at offset 11792
read  9224 bytes at offset 11856
read    64 bytes at offset 21080
read  8736 bytes at offset 21144
228 records; 20736 of 37968 bytes
```

The reader opens the container header and the metadata, then `END`, the `INDEX` frame and the summary frame, each as a 64-byte frame header followed by its payload. After that it reads frames 1 and 2, whose time ranges overlap the requested minute. Frame 0 ends before 08:03 and frame 3 starts after 08:04, so offsets 2120 and 29880 never appear in the list. The stored sizes and the offsets depend on the version of the Zstandard library.

[Store profile](../STORE.md) · [The nwt command](../TOOLS.md) · [Size and speed](../PERFORMANCE.md)
