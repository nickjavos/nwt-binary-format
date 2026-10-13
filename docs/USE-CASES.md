# Use NWT in practice

This page shows what NWT Binary Format is good for and how to do real work with it. It has seven recipes: inspect and validate a file, convert a CSV export, print records, build an archive and query it, rebuild an order book, join market data to reference data, and read and write files from your own code. Each recipe gives the commands to run and the output to expect. The page is for engineers who want to try the format on real files before they read the [Specification](SPECIFICATION.md).

## Why a binary container

- **Prices and quantities are exact.** A price or a quantity is a [64-bit integer scaled by 10⁹](SPECIFICATION.md#decimal-values-and-null-values): 177.03 is stored as `177030000000`. A sum, a comparison or an average gives the same result in every language, with no floating-point rounding.
- **Timestamps have nanosecond resolution.** Every record carries the [event time and the receive time](SPECIFICATION.md#time) as nanoseconds since 1970-01-01 UTC, so two events inside the same microsecond keep distinct times.
- **One file describes itself.** A container holds reference data and market events together, and the definition of an instrument precedes its trades and quotes. The [`MANIFEST`](SPECIFICATION.md#manifest) names the dataset, the publishers and the record types, and the [`PROVENANCE`](SPECIFICATION.md#provenance) records the source of the data and the rules of its conversion.
- **Every frame has a checksum.** A [CRC-32C](SPECIFICATION.md#crc-32c) protects the container header, the metadata, each frame header and each frame payload. A reader checks a frame before it uses any of its records, so damaged or missing bytes are reported and never decoded as data.
- **Compression is optional and per frame.** Each `DATA` frame is stored raw or as one [Zstandard](https://github.com/facebook/zstd) frame, and a reader decodes it without the frames around it. [Compression and integrity](SPECIFICATION.md#compression-and-integrity) gives the rules.
- **A reader opens only the frames it needs.** The [`INDEX`](SPECIFICATION.md#index-frames) gives the time range of every frame, and [`FRAME_SUMMARY`](SPECIFICATION.md#frame_summary) records add its record types and its range of instrument IDs. A query reads the frames that can hold a match and skips the rest.

## Before you start

The recipes use the `nwt` command, `tools/nwt.py`, and the Python reference codec, `examples/python/nwt_example.py`. Both run on Python 3.10 or later with the standard library only.

1. Download [nwt-binary-format-kit.zip](files/nwt-binary-format-kit.zip) and unpack it.
2. Open a terminal in the kit root. Every command on this page runs from there.
3. Create the folder for the output files:

   ```bash
   mkdir -p work
   ```

Each recipe names its input as a download link. In the kit, the same files are in `fixtures/real/`, `fixtures/real-reference/` and `fixtures/real-market/`, and the commands use those paths. A recipe that has a Python program asks you to save it in `work/` and run it from the kit root.

Zstandard frames need the system [libzstd](https://github.com/facebook/zstd) (Python, C#, C++) or the [zstd](https://github.com/gyscos/zstd-rs) crate (Rust). Raw frames need no library. Only [Build an archive and query it](#build-an-archive-and-query-it) writes Zstandard frames.

## Inspect and validate a file

**Goal.** Find out what an NWT file holds and whether it is complete and consistent, without knowing anything about it in advance.

**Input.** [depth-10.nwt](files/samples/depth-10.nwt), a sample of book snapshots for options on futures.

**Steps.**

1. Print what the file declares about itself. [inspect](TOOLS.md#inspect) reads the container header and the `MANIFEST`:

   ```bash
   python3 tools/nwt.py inspect fixtures/real-market/depth-10.nwt | grep -E '^(container|profile|publisher|schema)'
   ```

   ```text
   container major=1 minor=1 stream_id=c62bb6aea2cce2e4bb7ca4d0c7d2e6ad created_ns=1791849600000000000
   profile market-data clock=posix-ns ordering=none
   publisher 97 publisher-97 venue=
   schema 5 v1 BOOK_SNAPSHOT required=true
   schema 6 v1 INSTRUMENT_DEF required=true
   schema 11 v1 OPTION_DEF required=false
   ```

   The file declares one publisher and three record types. `inspect` also prints the dataset, the producer and the `PROVENANCE` object; the filter leaves those lines out.
2. Print the frames and the record counts, which are the last eight lines of the same output:

   ```bash
   python3 tools/nwt.py inspect fixtures/real-market/depth-10.nwt | tail -n 8
   ```

   ```text
   frame seq kind codec offset stored_bytes raw_bytes records min_event_ns max_event_ns
   0 DATA 0 1896 122920 122920 886 1743984000000000000 1744011000192310000
   1 INDEX 0 124880 40 40 0 - -
   2 END 0 124984 32 32 0 - -
   end data_frames=1 records=886 status=normal
   records BOOK_SNAPSHOT 500
   records INSTRUMENT_DEF 199
   records OPTION_DEF 187
   ```

   One raw `DATA` frame holds all 886 records. The `INDEX` and the `END` frame close the file, and `status=normal` says that the producer completed it.
3. Check the whole file. [validate](TOOLS.md#validate) verifies every checksum, length and sequence, and then applies the state rules to every record:

   ```bash
   python3 tools/nwt.py validate fixtures/real-market/depth-10.nwt
   ```

   ```text
   valid records=886 data_frames=1 summaries=0 ordering=none
   ```
4. See how a cut file and a damaged file are reported. The first copy loses its end, and the second has one changed byte in the middle of the payload:

   ```bash
   head -c 100000 fixtures/real-market/depth-10.nwt > work/cut.nwt
   python3 tools/nwt.py validate work/cut.nwt
   ```

   ```text
   NWT error: incomplete: file ends inside frame payload
   ```

   ```bash
   cp fixtures/real-market/depth-10.nwt work/damaged.nwt
   printf '\377' | dd of=work/damaged.nwt bs=1 seek=50000 conv=notrunc 2> /dev/null
   python3 tools/nwt.py validate work/damaged.nwt
   ```

   ```text
   NWT error: payload CRC
   ```

   Both commands exit with status 1.

**Result.** You know the publisher, the record types and the record counts of the file, you know that it is complete and passes the state rules, and you have seen the two messages that a broken copy produces.

## Convert a CSV export

**Goal.** Turn a top-of-book export in CSV into an NWT file and prove that the conversion kept every value.

**Input.** `fixtures/real-market/source/xnas-itch_mbp-1_equities.csv` from the [kit](files/nwt-binary-format-kit.zip): 2,000 top-of-book rows of one equity. The result equals the sample [equity-quotes.nwt](files/samples/equity-quotes.nwt). The first line of the source names the columns, and each further line is one book event with decimal prices and UTC timestamps:

<!-- nwt-file: fixtures/real-market/source/xnas-itch_mbp-1_equities.csv lines=1-3 -->

**Steps.**

1. Convert the file. `csv-mbp1` is the converter kind for a top-of-book export, and `--definitions` names the export that holds the definition of the instrument:

   ```bash
   python3 tools/nwt.py convert csv-mbp1 fixtures/real-market/source/xnas-itch_mbp-1_equities.csv work/equity-quotes.nwt --dataset REAL.XNAS.ITCH --definitions fixtures/real-market/source/xnas-itch_definition_equities.csv --currency USD --quantity-unit share > work/equity-quotes.provenance.json
   ```

   The command writes the container and prints a summary of the conversion as JSON, which the redirection saves. The same summary is stored in the `PROVENANCE` of the container.
2. Read the record counts and the rounding count from the summary:

   ```bash
   grep -A 4 records_written work/equity-quotes.provenance.json
   grep values_rounded work/equity-quotes.provenance.json
   ```

   ```text
     "records_written": {
       "INSTRUMENT_DEF": 1,
       "QUOTE": 2000,
       "TRADE_QUOTE": 476
     },
     "values_rounded": 0
   ```

   Every row became a `QUOTE`, and each of the 476 trade rows also became a `TRADE_QUOTE`. No value was rounded: the converter parses decimals with integer arithmetic and stops at a value it cannot store exactly.
3. Check the result. `cmp` prints nothing when two files are byte-identical, and `validate` confirms the structure and the state rules:

   ```bash
   cmp work/equity-quotes.nwt fixtures/real-market/equity-quotes.nwt
   python3 tools/nwt.py validate work/equity-quotes.nwt
   ```

   ```text
   valid records=2477 data_frames=1 summaries=0 ordering=none
   ```
4. Compare one source row with its record. The second line of the export has an ask of 186 for 100 shares and no bid:

   ```bash
   python3 tools/nwt.py cat work/equity-quotes.nwt --pretty | sed -n 2p
   ```

   ```text
   {"type_name":"QUOTE","record_bytes":"96","record_type":"2","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:00:00.015298471Z","ts_recv":"2025-09-16T08:00:00.015462508Z","sequence":"2","bid_price":null,"ask_price":"186.000000000","bid_quantity":"0.000000000","ask_quantity":"100.000000000","bid_order_count":"0","ask_order_count":"1","quote_flags":"0"}
   ```

**Result.** You have an NWT file that is byte-identical to the published sample, with the instrument definition in front of the quotes and the conversion rules recorded inside the file. [Market data samples](REAL-DATA-MARKET.md#converter-kinds) lists the converter kinds for order-level books, depth, bars, definitions and statistics, and [Reference data samples](REAL-DATA.md#converter-kinds) lists the kinds for venues, listings, securities and corporate actions.

## Print records as JSON Lines or CSV

**Goal.** Read the records of a file as text, with the stored integers for a program or with readable values for a person.

**Input.** [equity-bars.nwt](files/samples/equity-bars.nwt): 921 one-minute bars of one equity.

**Steps.**

1. Print the records as JSON Lines. [cat](TOOLS.md#cat) writes one JSON object per record, and every value is the stored integer as a decimal string. The second record of the file is the first bar:

   ```bash
   python3 tools/nwt.py cat fixtures/real-market/equity-bars.nwt | sed -n 2p
   ```

   ```text
   {"type_name":"BAR","record_bytes":"112","record_type":"3","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"1758009660000000000","ts_recv":"18446744073709551615","sequence":"2","interval_start_ns":"1758009600000000000","interval_end_ns":"1758009660000000000","open":"177030000000","high":"177280000000","low":"177030000000","close":"177280000000","volume":"3300000000000","trade_count":"51","bar_flags":"0"}
   ```

   `open` is 177.03 scaled by 10⁹, and `ts_recv` holds the null sentinel, `18446744073709551615`.
2. Add `--pretty` for readable values: decimals with nine fractional digits, ISO 8601 times in UTC, and JSON `null` for a null value:

   ```bash
   python3 tools/nwt.py cat fixtures/real-market/equity-bars.nwt --pretty | sed -n 2p
   ```

   ```text
   {"type_name":"BAR","record_bytes":"112","record_type":"3","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:01:00.000000000Z","ts_recv":null,"sequence":"2","interval_start_ns":"2025-09-16T08:00:00.000000000Z","interval_end_ns":"2025-09-16T08:01:00.000000000Z","open":"177.030000000","high":"177.280000000","low":"177.030000000","close":"177.280000000","volume":"3300.000000000","trade_count":"51","bar_flags":"0"}
   ```
3. Print one record type as CSV with the Python reference codec. `to-csv` takes the file and the number of the record type; `BAR` is type 3. The command prints a header line and 921 bars; the first three lines are shown, and 919 more follow:

   ```bash
   python3 examples/python/nwt_example.py to-csv fixtures/real-market/equity-bars.nwt 3 --pretty | head -n 3
   ```

   ```text
   record_bytes,record_type,schema_version,flags,publisher_id,channel_id,instrument_id,ts_event,ts_recv,sequence,interval_start_ns,interval_end_ns,open,high,low,close,volume,trade_count,bar_flags
   112,3,1,0,2,0,11667,2025-09-16T08:01:00.000000000Z,,2,2025-09-16T08:00:00.000000000Z,2025-09-16T08:01:00.000000000Z,177.030000000,177.280000000,177.030000000,177.280000000,3300.000000000,51,0
   112,3,1,0,2,0,11667,2025-09-16T08:02:00.000000000Z,,3,2025-09-16T08:01:00.000000000Z,2025-09-16T08:02:00.000000000Z,177.220000000,177.280000000,177.210000000,177.240000000,1694.000000000,24,0
   ```

   A null value is an empty CSV field. Without `--pretty`, `to-csv` prints the stored integers.
4. Pass the text to other tools. This pipeline finds the bar with the highest volume and prints its start time, its four prices, its volume and its trade count:

   ```bash
   python3 examples/python/nwt_example.py to-csv fixtures/real-market/equity-bars.nwt 3 --pretty | tail -n +2 | sort -t, -k17,17 -n -r | head -n 1 | cut -d, -f11,13-18
   ```

   ```text
   2025-09-16T20:00:00.000000000Z,174.870000000,174.990000000,174.850000000,174.900000000,11263305.000000000,164
   ```

**Result.** You can turn any NWT file into JSON Lines, and any record type into CSV, in the raw or the readable form, and feed the text to a shell pipeline, a spreadsheet or a database loader. All four reference codecs have the `to-json` and `to-csv` commands and print the same text.

## Build an archive and query it

**Goal.** Combine several files into one compressed archive and read one time range or one instrument from it without reading the whole file.

**Input.** [equity-quotes.nwt](files/samples/equity-quotes.nwt), [equity-orders.nwt](files/samples/equity-orders.nwt) and [futures-orders.nwt](files/samples/futures-orders.nwt): quotes and order events of one equity, and order events of one futures contract on a later day.

**Steps.**

1. Merge the three files by event time. [merge](TOOLS.md#merge) interleaves the inputs by `ts_event`, keeps the record order of each input and gives the output its own sequences:

   ```bash
   python3 tools/nwt.py merge work/archive.nwt fixtures/real-market/equity-quotes.nwt fixtures/real-market/equity-orders.nwt fixtures/real-market/futures-orders.nwt --order ts_event
   ```
2. Rewrite the result as a store file. [repack](TOOLS.md#repack) keeps the records and their order, and writes Zstandard frames, an `INDEX` and `FRAME_SUMMARY` records. `--frame-bytes 65536` makes small frames, so this small archive has frames to skip:

   ```bash
   python3 tools/nwt.py repack work/archive.nwt work/archive.store.nwt --frame-bytes 65536
   python3 tools/nwt.py validate work/archive.store.nwt
   ```

   ```text
   valid records=6430 data_frames=11 summaries=10 ordering=ts_event
   ```

   The archive has 6,420 records in 10 frames and one more frame with the 10 `FRAME_SUMMARY` records. `repack` found the records in `ts_event` order and declared it in the manifest.
3. Ask for the trades of 200 milliseconds. [query](TOOLS.md#query) reads the `INDEX` and the summaries, then only the frames whose time range and record types can match:

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

**Result.** You have one validated archive of three sources and two queries that return the same records as a full scan while they read a fraction of the file. [Store profile](STORE.md) describes the layout, the read path and the choice of frame size, and [What a partial read returns](STORE.md#what-a-partial-read-returns) explains the label.

## Rebuild an order book

**Goal.** Replay order-level records into an order book and read the best bid and the best ask at a chosen time.

**Input.** [equity-orders.nwt](files/samples/equity-orders.nwt): 1,818 `MBO` records and 123 `TRADE` records of one equity. [equity-quotes.nwt](files/samples/equity-quotes.nwt) holds the top of book of the same equity and day, and serves as the check. After the `INSTRUMENT_DEF`, the order file starts with an `MBO` record with `action` 4, `CLEAR`, which states that the book is empty. Two `ADD` records follow, `action` 1: an ask (`side` 2) at 186 and a bid (`side` 1) at 176.85:

<!-- nwt-file: fixtures/real-market/equity-orders.jsonl lines=2-4 -->

**Steps.**

1. Save this program as `work/top_of_book.py`. It applies every record up to 08:02:00 UTC to a `MarketState`, the implementation of the state rules in `examples/python/market_state.py`, and then reads the live orders of the book:

   ```python
   import sys
   sys.path[:0] = ["tools", "examples/python"]
   import market_state
   import nwt_example as codec
   import nwt as tool

   at = tool.parse_time("2025-09-16T08:02:00Z")
   key = (2, 0, 11667)                              # publisher, channel, instrument
   state = market_state.MarketState()

   with open("fixtures/real-market/equity-orders.nwt", "rb") as f:
       for record in codec.complete_records(codec.open_reader(f)):
           if int(record["fields"]["ts_event"]) > at:
               break                                # the records of this file are in ts_event order
           state.apply(record)                      # checks the record, then changes the book

   orders = state.mbo[key].values()                 # live orders of the book
   for name, side, best in (("bid", 1, max), ("ask", 2, min)):
       price = best(o["price"] for o in orders if o["side"] == side)
       level = [o for o in orders if o["side"] == side and o["price"] == price]
       quantity = sum(o["quantity"] for o in level)
       print(name, codec.pretty_decimal(price), "quantity", codec.pretty_decimal(quantity), "orders", len(level))
   print("live orders", len(orders))
   ```

   ```bash
   python3 work/top_of_book.py
   ```

   ```text
   bid 177.230000000 quantity 300.000000000 orders 3
   ask 177.290000000 quantity 100.000000000 orders 1
   live orders 1052
   ```

   `apply` raises an error when a record breaks a rule, for example an `ADD` for an order that is already live or a change to a book that has no `CLEAR` or snapshot before it.
2. Check the result against the top-of-book sample. The last `QUOTE` before 08:02:00 UTC in `equity-quotes.nwt` carries the same prices, quantities and order counts:

   ```bash
   python3 tools/nwt.py query fixtures/real-market/equity-quotes.nwt --type QUOTE --to 2025-09-16T08:02:00Z --pretty 2> /dev/null | tail -n 1
   ```

   ```text
   {"type_name":"QUOTE","record_bytes":"96","record_type":"2","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:01:59.372520717Z","ts_recv":"2025-09-16T08:01:59.372683640Z","sequence":"427","bid_price":"177.230000000","ask_price":"177.290000000","bid_quantity":"300.000000000","ask_quantity":"100.000000000","bid_order_count":"3","ask_order_count":"1","quote_flags":"0"}
   ```

**Result.** You have the full order book of the instrument at the chosen time, built from 1,052 live orders, and its top agrees with an independent top-of-book file. A book is valid only when the replay starts at a `CLEAR` or a completed snapshot and applies every record after it: [State and recovery](STATE-AND-RECOVERY.md#order-level-book-state) gives the rules, and [Gaps and recovery](STATE-AND-RECOVERY.md#gaps-and-recovery) covers a loss at the source.

## Join market data to reference data

**Goal.** Give a market event its symbol, venue, currency and unit, and give an instrument of a feed its listing name from a symbol directory.

**Input.** [equity-quotes.nwt](files/samples/equity-quotes.nwt), [equity-definitions.nwt](files/samples/equity-definitions.nwt), [listings-nasdaq.nwt](files/samples/listings-nasdaq.nwt), [listings-other.nwt](files/samples/listings-other.nwt) and [secmaster-us.nwt](files/samples/secmaster-us.nwt). A symbol directory keeps two records per symbol, a `LISTING` and a `SYMBOL_MAP`:

<!-- nwt-file: fixtures/real/listings-nasdaq.jsonl lines=45-46 -->

**Steps.**

1. Join an event to its definition inside one file. A market record carries a publisher ID and an instrument ID, and the `INSTRUMENT_DEF` with the same pair comes earlier in the same file. Save this program as `work/label_trades.py`. It prints the first three trades with the texts of their definition:

   ```python
   import sys
   sys.path.insert(0, "examples/python")
   import nwt_example as codec

   definitions = {}                                   # (publisher_id, instrument_id) -> texts of the definition
   shown = 0
   with open("fixtures/real-market/equity-quotes.nwt", "rb") as f:
       for record in codec.complete_records(codec.open_reader(f)):
           fields = record["fields"]
           key = (fields["publisher_id"], fields["instrument_id"])
           if record["type"] == 6:                    # INSTRUMENT_DEF
               definitions[key] = record["texts"]
           elif record["type"] == 18 and shown < 3:   # TRADE_QUOTE
               d = definitions[key]                   # the definition always comes first
               print(codec.pretty_time(int(fields["ts_event"])), d["symbol"], d["venue"],
                     codec.pretty_decimal(int(fields["price"])), d["currency"],
                     codec.pretty_decimal(int(fields["quantity"])), d["quantity_unit"])
               shown += 1
   ```

   ```bash
   python3 work/label_trades.py
   ```

   ```text
   2025-09-16T08:00:00.256830296Z NVDA XNAS 177.030000000 USD 180.000000000 share
   2025-09-16T08:00:00.283911761Z NVDA XNAS 177.180000000 USD 100.000000000 share
   2025-09-16T08:00:00.312811923Z NVDA XNAS 177.100000000 USD 31.000000000 share
   ```
2. Join across files by symbol and market identifier code. Each producer numbers instruments in its own namespace, so an instrument ID of the feed does not appear in the symbol directory. The texts do: the `symbol` and `venue` of an `INSTRUMENT_DEF` equal the `symbol` and `listing_mic` of a `LISTING`. Save this program as `work/join_listings.py`. It indexes the listings of the two directory samples and looks up each of the 200 definitions of the feed:

   ```python
   import sys
   sys.path.insert(0, "examples/python")
   import nwt_example as codec

   def records(path, record_type):
       with open(path, "rb") as f:
           for record in codec.complete_records(codec.open_reader(f)):
               if record["type"] == record_type:
                   yield record

   listings = {}                                      # (symbol, listing MIC) -> LISTING
   for path in ("fixtures/real/listings-nasdaq.nwt", "fixtures/real/listings-other.nwt"):
       for listing in records(path, 12):
           texts = listing["texts"]
           listings[(texts["symbol"], texts["listing_mic"])] = listing

   matched = 0
   for definition in records("fixtures/real-market/equity-definitions.nwt", 6):
       texts = definition["texts"]
       listing = listings.get((texts["symbol"], texts["venue"]))
       if listing is None:
           continue
       matched += 1
       if matched <= 4:
           print(definition["fields"]["instrument_id"], texts["symbol"], texts["venue"],
                 "round lot", listing["fields"]["round_lot"], "|", listing["texts"]["name"].strip())
   print(matched, "of 200 definitions have a listing")
   ```

   ```bash
   python3 work/join_listings.py
   ```

   ```text
   1 A XNYS round lot 100 | Agilent Technologies, Inc. Common Stock
   2 AA XNYS round lot 100 | Alcoa Corporation Common Stock
   3 AAA ARCX round lot 100 | Alternative Access First Priority CLO Bond ETF
   21201 AAAA BATS round lot 100 | Amplius Aggressive Asset Allocation ETF
   126 of 200 definitions have a listing
   ```

   Each directory sample holds the first 100 entries of its source, so 74 definitions find no listing here.
3. Look up a single symbol or identifier with [resolve](TOOLS.md#resolve). `--at` selects the mapping that is valid at a moment, and an ISIN, a CUSIP or a FIGI finds the security master record:

   ```bash
   python3 tools/nwt.py resolve fixtures/real/listings-nasdaq.nwt AAPL --at 2026-11-01
   python3 tools/nwt.py resolve fixtures/real-reference/secmaster-us.nwt US22160K1051
   ```

   ```text
   {"source":"SYMBOL_MAP","publisher_id":"1","instrument_id":"4519135547670130507","symbology":"1","valid_from_ns":"1791907860000000000","valid_to_ns":"18446744073709551615","symbol":"AAPL"}
   {"source":"SECURITY_DEF","publisher_id":"1","instrument_id":"137786","identifier":"isin","symbol":"COST","isin":"US22160K1051","cusip":"22160K105","composite_figi":"BBG000F6H8W8","figi":"BBG000F6HLL1"}
   ```

**Result.** You can label any market record with the texts of its definition, match the instruments of a feed to a symbol directory, and find an instrument by symbol, ISIN, CUSIP or FIGI. [Reference data samples](REAL-DATA.md#instrument-identifiers) explains how the directory samples derive their instrument IDs, and [Reference data and statistics](STATE-AND-RECOVERY.md#reference-data-and-statistics) gives the key of every reference record type.

## Read and write a file from your code

**Goal.** Read an NWT file in a program, compute with its values, and write a new NWT file.

**Input.** [equity-quotes.nwt](files/samples/equity-quotes.nwt): 2,000 `QUOTE` and 476 `TRADE_QUOTE` records of one equity. The codec is `examples/python/nwt_example.py`. Its `Reader` needs one thing from a source, a function that returns `n` bytes at an offset, and `open_reader` builds that function for an open file:

<!-- nwt-file: examples/python/nwt_example.py lines=866-871 -->

**Steps.**

1. Save this program as `work/my_trades.py`. It reads the sample, keeps the definition and the trades, computes the traded volume and the volume-weighted average price with integers, and writes the kept records to a new container:

   ```python
   import os, sys, time
   sys.path.insert(0, "examples/python")
   import nwt_example as codec

   # Read: the container header, the manifest and every frame are checked on the way.
   with open("fixtures/real-market/equity-quotes.nwt", "rb") as f:
       reader = codec.open_reader(f)
       publishers = reader.manifest["publishers"]
       kept = [r for r in codec.complete_records(reader) if r["type"] in (6, 18)]   # INSTRUMENT_DEF, TRADE_QUOTE

   # Compute with the stored integers: prices and quantities are scaled by 10^9.
   trades = [r["fields"] for r in kept if r["type"] == 18]
   volume = sum(int(t["quantity"]) for t in trades)
   turnover = sum(int(t["price"]) * int(t["quantity"]) for t in trades)
   print(len(trades), "trades, volume", codec.pretty_decimal(volume),
         "average price", codec.pretty_decimal(turnover // volume))

   # Write: a new container with its own manifest, stream ID and sequences.
   manifest = codec.build_manifest("EXAMPLE.TRADES", "my-app", publishers, types=[6, 18])
   sequencer = codec.Sequencer()
   with open("work/my-trades.nwt", "wb") as out:
       writer = codec.Writer(out, manifest, os.urandom(16), created_ns=time.time_ns())
       for record in kept:
           fields = record["fields"]
           fields["sequence"] = str(sequencer.next(int(fields["publisher_id"]), int(fields["channel_id"])))
           writer.write(record)
       writer.close()
   ```

   ```bash
   python3 work/my_trades.py
   python3 tools/nwt.py validate work/my-trades.nwt
   ```

   ```text
   476 trades, volume 24421.000000000 average price 177.373739404
   valid records=477 data_frames=1 summaries=0 ordering=none
   ```

   A decoded record is a dictionary with `type`, `fields`, `texts` and `levels`, and every field is the stored integer as a decimal string. The average is the sum of price times quantity divided by the sum of quantity, rounded down to nine decimals. `Writer.close` writes the last `DATA` frame, the `INDEX` and `END`.
2. Read the new file with each reference codec. The four programs have the same commands. Each tab below builds one codec and prints the first trades of the file as CSV.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py to-csv work/my-trades.nwt 18 --pretty | head -n 3
```
<!-- nwt-title: Rust -->
```bash
cargo build --locked --manifest-path examples/rust/Cargo.toml
examples/rust/target/debug/nwt-example to-csv work/my-trades.nwt 18 --pretty | head -n 3
```
<!-- nwt-title: C# -->
```bash
dotnet build examples/csharp/NwtExample.csproj -o work/csharp
dotnet work/csharp/NwtExample.dll to-csv work/my-trades.nwt 18 --pretty | head -n 3
```
<!-- nwt-title: C++ -->
```bash
c++ -std=c++20 -O2 -DNWT_ZSTD examples/cpp/main.cpp -o work/nwt-cpp -lzstd
work/nwt-cpp to-csv work/my-trades.nwt 18 --pretty | head -n 3
```
<!-- /nwt-tabs -->

After the messages of the build, every tab prints the same three lines:

```text
record_bytes,record_type,schema_version,flags,publisher_id,channel_id,instrument_id,ts_event,ts_recv,sequence,price,quantity,trade_id,bid_price,ask_price,bid_quantity,ask_quantity,bid_order_count,ask_order_count,aggressor,conditions
120,18,1,0,2,0,11667,2025-09-16T08:00:00.256830296Z,2025-09-16T08:00:00.256994090Z,2,177.030000000,180.000000000,0,177.030000000,183.000000000,200.000000000,200.000000000,1,1,2,0
120,18,1,0,2,0,11667,2025-09-16T08:00:00.283911761Z,2025-09-16T08:00:00.284075365Z,3,177.180000000,100.000000000,0,177.180000000,183.000000000,100.000000000,200.000000000,1,1,2,0
```

**Result.** You have a program that reads, computes and writes NWT with the Python reference codec, and a file that all four reference codecs read identically. The [Implementation guide](IMPLEMENTATION-GUIDE.md#build-and-run) lists the toolchains and the build options, and shows the same reading and writing in Rust, C# and C++ under [Read a file](IMPLEMENTATION-GUIDE.md#read-a-file) and [Write a file](IMPLEMENTATION-GUIDE.md#write-a-file).

## Where to go next

- [How it works](HOW-IT-WORKS.md) explains the container, the frames and the records with diagrams.
- [Examples by record type](FEED-COOKBOOK.md) shows one worked record for each of the 22 record types.
- [The nwt command](TOOLS.md) is the reference of every subcommand, including `extract`, `split` and `stats`, which this page does not use.
- [Store profile](STORE.md) covers archives and selective reads in depth, and [Size and speed](PERFORMANCE.md) gives the measurements.
- [State and recovery](STATE-AND-RECOVERY.md) defines the state a consumer keeps and how it recovers after a gap.
- [Specification](SPECIFICATION.md) and [Field reference](FIELD-REFERENCE.md) define every byte and every field.
- [Glossary](GLOSSARY.md) defines the terms used on these pages, and [Downloads](DOWNLOADS.md) lists every hosted file with its checksum.

Source code on [GitHub](https://github.com/nickjavos/nwt-binary-format).

<!-- nwt-repo-card -->
