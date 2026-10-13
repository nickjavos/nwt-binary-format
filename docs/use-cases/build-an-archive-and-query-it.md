# Build an archive and query it

**Goal.** Combine several files into one compressed archive and read one time range or one instrument from it without reading the whole file.

**Input.** [equity-quotes.nwt](files/samples/equity-quotes.nwt), [equity-orders.nwt](files/samples/equity-orders.nwt) and [futures-orders.nwt](files/samples/futures-orders.nwt): quotes and order events of one equity, and order events of one futures contract on a later day.

**Steps.**

1. Merge the three files by event time. [merge](../tools/merge.md) interleaves the inputs by `ts_event`, keeps the record order of each input and gives the output its own sequences:

   ```bash
   python3 tools/nwt.py merge work/archive.nwt fixtures/real-market/equity-quotes.nwt fixtures/real-market/equity-orders.nwt fixtures/real-market/futures-orders.nwt --order ts_event
   ```
2. Rewrite the result as a store file. [repack](../tools/repack.md) keeps the records and their order, and writes Zstandard frames, an `INDEX` and `FRAME_SUMMARY` records. `--frame-bytes 65536` makes small frames, so this small archive has frames to skip:

   ```bash
   python3 tools/nwt.py repack work/archive.nwt work/archive.store.nwt --frame-bytes 65536
   python3 tools/nwt.py validate work/archive.store.nwt
   ```

   ```text
   valid records=6430 data_frames=11 summaries=10 ordering=ts_event
   ```

   The archive has 6,420 records in 10 frames and one more frame with the 10 `FRAME_SUMMARY` records. `repack` found the records in `ts_event` order and declared it in the manifest.
3. Ask for the trades of 200 milliseconds. [query](../tools/query.md) reads the `INDEX` and the summaries, then only the frames whose time range and record types can match:

   ```bash
   python3 tools/nwt.py query work/archive.store.nwt --type TRADE --from 2025-09-16T08:02:08.9Z --to 2025-09-16T08:02:09.1Z --pretty
   ```

   ```text
   # partial: earlier definitions and book state are not included
   {"type_name":"TRADE","record_bytes":"88","record_type":"1","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:02:08.964996591Z","ts_recv":"2025-09-16T08:02:08.965160363Z","sequence":"2238","price":"177.240000000","quantity":"10.000000000","trade_id":"86","original_sequence":"0","action":"1","aggressor":"1","conditions":"0"}
   {"type_name":"TRADE","record_bytes":"88","record_type":"1","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:02:08.964997926Z","ts_recv":"2025-09-16T08:02:08.965164816Z","sequence":"2243","price":"177.240000000","quantity":"2.000000000","trade_id":"87","original_sequence":"0","action":"1","aggressor":"1","conditions":"0"}
   {"type_name":"TRADE","record_bytes":"88","record_type":"1","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:02:09.000021485Z","ts_recv":"2025-09-16T08:02:09.000184864Z","sequence":"2248","price":"177.240000000","quantity":"3.000000000","trade_id":"88","original_sequence":"0","action":"1","aggressor":"1","conditions":"0"}
   ```

   The first line goes to standard error. It labels the result as partial: the instrument definition lies in an earlier frame and is not part of the answer. Add `INSTRUMENT_DEF` to `--type` and drop the time bounds to read the definitions.
4. Ask for one instrument. The futures contract has instrument ID 294973, and the command counts its order records:

   ```bash
   python3 tools/nwt.py query work/archive.store.nwt --type MBO --instrument 294973 2> /dev/null | wc -l
   ```

   ```text
   2000
   ```
5. Measure how much of the file each query reads. Save this program as `work/measure.py`. It gives the reader a function that returns `n` bytes at an offset, as a ranged read of a remote object does, and counts the bytes the reader asks for:

   ```python
   import sys
   sys.path[:0] = ["tools", "examples/python"]
   import nwt_example
   import nwt as tool

   data = open("work/archive.store.nwt", "rb").read()
   fetched = []

   def read_at(offset, n):                     # replace with a ranged read of a remote object
       fetched.append(n)
       return data[offset : offset + n]

   def measure(label, **query):
       fetched.clear()
       reader = nwt_example.Reader(read_at, len(data))
       found = sum(1 for _ in tool.select(reader, **query))
       print(f"{label}: {found} records, {sum(fetched)} of {len(data)} bytes read")

   measure("trades in 200 ms", types=[1],
           t0=tool.parse_time("2025-09-16T08:02:08.9Z"), t1=tool.parse_time("2025-09-16T08:02:09.1Z"))
   measure("one instrument", types=[4], instruments=[294973])
   ```

   ```bash
   python3 work/measure.py
   ```

   ```text
   trades in 200 ms: 3 records, 11664 of 86992 bytes read
   one instrument: 2000 records, 20136 of 86992 bytes read
   ```

   The first query reads the container header, the metadata, the `END` frame, the `INDEX`, the summary frame and one of the ten `DATA` frames that hold the records. The second query reads four of the ten. The byte counts follow the stored sizes of the frames, which depend on the version of the Zstandard library.

**Result.** You have one validated archive of three sources and two queries that return the same records as a full scan while they read a fraction of the file. [Store profile](../STORE.md) describes the layout, the read path and the choice of frame size, and [What a partial read returns](../store/what-a-partial-read-returns.md) explains the label.
