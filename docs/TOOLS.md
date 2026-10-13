# The nwt command

`nwt` is the command-line tool of the kit: it inspects, validates, prints, filters, merges, splits, repacks, queries and converts NWT containers. This page is its reference, one section per subcommand, for engineers who work with NWT files in a shell or call the tool from Python. The tool is the file `tools/nwt.py`, written in Python on top of the Python reference codec and the state rules.

## Run it

Run the tool from the kit root with Python 3.10 or later. It uses the standard library only. Zstandard frames need the system [libzstd](https://github.com/facebook/zstd); raw frames need no library.

```bash
python3 tools/nwt.py COMMAND [ARGUMENTS]
```

`python3 tools/nwt.py --help` lists the subcommands, and `python3 tools/nwt.py COMMAND --help` lists the arguments of one.

| Command | What it does |
|---|---|
| [inspect](#inspect) | Prints the header, the manifest, the frame table and the record counts |
| [validate](#validate) | Checks the structure, the state rules, the summaries and the `ordering` declaration |
| [cat](#cat) | Prints every record as one JSON object per line |
| [extract](#extract) | Writes the records that match a filter to a new container |
| [merge](#merge) | Combines containers under a stated ordering policy |
| [split](#split) | Writes one container per record type, instrument or day |
| [repack](#repack) | Rewrites a container as a store file |
| [query](#query) | Prints matching records, reading only the frames that can hold a match |
| [resolve](#resolve) | Looks up a symbol, ISIN, CUSIP or FIGI |
| [stats](#stats) | Prints sizes, bytes per record type and the compression ratio |
| [convert](#convert) | Converts a source file to a container |

The examples read the samples in `fixtures/real/`, `fixtures/real-reference/` and `fixtures/real-market/`, which are also on the [Downloads](DOWNLOADS.md) page. They write to the folder `work/`:

```bash
mkdir -p work
```

### Rules for every command

- **Records keep their order.** No command reorders records. `repack` changes framing and compression; `extract`, `merge` and `split` keep the order of the records they keep.
- **A derived container has its own identity.** `extract`, `merge` and `split` write a container with a new random stream ID and with sequences that start at 1 for each publisher and channel. `repack` writes a new stream ID and keeps every sequence.
- **Manifests are exact.** The output of `extract`, `merge` and `split` declares only the record types it holds, and it declares an `ordering` only when its records have it.
- **Output is complete or absent.** A writing command writes to `OUT.tmp` and renames the file when it is finished. `OUT` cannot be one of the inputs.
- **A whole-file command validates what it reads.** `inspect`, `validate`, `cat`, `stats` and the writing commands read every frame and check every CRC-32C, length and sequence. `query` and `resolve` check the frames they read.

### Exit status

| Status | Meaning |
|---|---|
| 0 | The command succeeded. |
| 1 | The command failed. One line `NWT error: <reason>` is on standard error. |
| 2 | The arguments are wrong. The usage text is on standard error. |

A file that ends early fails with a reason that starts with `incomplete`. A Zstandard frame on a system without `libzstd` fails with `Zstd library not available`.

### Filters

`extract` and `query` take the same filters. Every filter is optional, and a record matches when it passes all the filters that are given.

| Option | Meaning |
|---|---|
| `--type TYPES` | Record types, by number or by name, separated by commas: `2,TRADE` |
| `--instrument IDS` | Instrument IDs and inclusive ranges, separated by commas: `2001,3000-3999` |
| `--from TIME` | Start of the `ts_event` range, inclusive: a record matches when its `ts_event` is at or after `TIME` |
| `--to TIME` | End of the `ts_event` range, exclusive: a record matches when its `ts_event` is before `TIME` |

`TIME` has one of three forms:

| Form | Example |
|---|---|
| Nanoseconds since 1970-01-01 UTC | `1758009784530300000` |
| Date, read as midnight UTC | `2025-09-16` |
| Timestamp with a zone and up to nine fractional digits | `2025-09-16T08:03:04.5303Z` |

A record whose `ts_event` is null never matches `--from` or `--to`. Reference records such as `LISTING` often have a null `ts_event`, so select them by record type or by instrument.

## inspect

Prints what a container holds: its header, its manifest, every frame and the number of records of each type.

```bash
python3 tools/nwt.py inspect FILE
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |

The output is plain text, one item per line:

| Line starts with | Content |
|---|---|
| `file`, `size` | Path and size in bytes |
| `container` | `major`, `minor`, the stream ID as 32 hexadecimal digits, and the creation time in nanoseconds |
| `dataset`, `producer`, `profile` | Manifest: dataset, producer, profile, clock and `ordering` |
| `publisher` | One line per declared publisher: ID, name and venue |
| `schema` | One line per declared record type: number, schema version, name and `required` |
| `provenance` | `PROVENANCE` object as JSON, when the container has one |
| `frame` | Heading of the frame table. One row per frame follows: `frame_seq`, kind, codec, offset, stored bytes, raw bytes, record count, lowest and highest `ts_event`. A null time prints as `-`. |
| `end` | Totals of `END` and its status, `normal` or `aborted` |
| `records` | One line per record type that occurs: name and count |

The frame table and the lines after it, for the sample [equity-bars.nwt](files/samples/equity-bars.nwt):

```bash
python3 tools/nwt.py inspect fixtures/real-market/equity-bars.nwt | tail -n 7
```

```text
frame seq kind codec offset stored_bytes raw_bytes records min_event_ns max_event_ns
0 DATA 0 1856 103280 103280 922 1758006306677514564 1758067200000000000
1 INDEX 0 105200 40 40 0 - -
2 END 0 105304 32 32 0 - -
end data_frames=1 records=922 status=normal
records BAR 921
records INSTRUMENT_DEF 1
```

## validate

Checks a container completely and reports the first rule it breaks.

```bash
python3 tools/nwt.py validate FILE
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to check |

`validate` runs these checks and stops at the first one that fails:

1. The structure: header, metadata and every frame, with all CRC-32C values, lengths, sequences, declared record types and publishers, frame time bounds, the `INDEX` entries and the totals of `END`.
2. The manifest: `BOOK_DELTA` is declared with `required` true, `FRAME_SUMMARY` with `required` false, and record types 10–19 appear only under the profile `market-data`.
3. Every record against the state rules of `examples/python/market_state.py`: definitions before market data, trade lifecycles, order-level and aggregate books, statistics, symbol intervals and the other rules of [State and recovery](STATE-AND-RECOVERY.md).
4. The end of the container: the status of `END` is normal, and no snapshot is open.
5. The `ordering` declaration of the manifest against the records.
6. When the container has `FRAME_SUMMARY` records: they fill the last `DATA` frames, there is one for every other `DATA` frame, and every value equals the value computed from the frame.

On success it prints one line and exits with status 0:

```bash
python3 tools/nwt.py validate fixtures/real-reference/corporate-actions-us.nwt
```

```text
valid records=1641 data_frames=1 summaries=0 ordering=none
```

On the first broken rule it prints the reason and exits with status 1. A reason from the state rules names the record. The file in this example holds order records without the definition of their instrument:

```bash
python3 tools/nwt.py extract fixtures/real-market/equity-orders.nwt work/orders-only.nwt --type MBO
python3 tools/nwt.py validate work/orders-only.nwt
```

```text
NWT error: record 1 (MBO, sequence 1): definition must precede data
```

## cat

Prints every record of a container as one JSON object per line.

```bash
python3 tools/nwt.py cat FILE [--pretty]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |
| `--pretty` | Prints prices and quantities as decimals with nine fractional digits, times as `YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ`, and null values as JSON `null` |

An object starts with `type_name`, then the header fields, the body fields and the texts, in schema order. Without `--pretty`, every value is the stored integer as a decimal string. A `BOOK_SNAPSHOT` has a `levels` array. Reserved fields are left out.

`cat` prints the records of a frame after that frame has passed its checks. When a later frame is damaged, the records before it are already printed and the command exits with status 1, so rely on the exit status, not on the amount of output. When the program at the other end of a pipe closes it early, as `head` does, `cat` stops with status 0.

```bash
python3 tools/nwt.py cat fixtures/real-market/equity-quotes.nwt --pretty | head -n 2
```

```text
{"type_name":"INSTRUMENT_DEF","record_bytes":"128","record_type":"6","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T07:05:06.677514564Z","ts_recv":"2025-09-16T07:05:06.677677658Z","sequence":"1","price_increment":null,"quantity_increment":null,"contract_multiplier":null,"expiration_ns":null,"underlying_instrument_id":"0","strike":null,"asset_class":"1","symbol_bytes":"4","venue_bytes":"4","currency_bytes":"3","quantity_unit_bytes":"5","symbol":"NVDA","venue":"XNAS","currency":"USD","quantity_unit":"share"}
{"type_name":"QUOTE","record_bytes":"96","record_type":"2","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:00:00.015298471Z","ts_recv":"2025-09-16T08:00:00.015462508Z","sequence":"2","bid_price":null,"ask_price":"186.000000000","bid_quantity":"0.000000000","ask_quantity":"100.000000000","bid_order_count":"0","ask_order_count":"1","quote_flags":"0"}
```

## extract

Writes the records that match a filter to a new container.

```bash
python3 tools/nwt.py extract FILE OUT [--type TYPES] [--instrument IDS] [--from TIME] [--to TIME] [--stream-id HEX] [--created-ns NS]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |
| `OUT` | Container to write |
| `--type`, `--instrument`, `--from`, `--to` | [Filters](#filters) |
| `--stream-id HEX` | Stream ID of the output as 32 hexadecimal digits. The default is random. |
| `--created-ns NS` | Creation time of the output in nanoseconds. The default is the current time. |

- The output has a new stream ID, sequences renumbered from 1, and a manifest that declares only the record types kept.
- The `PROVENANCE` of the input is carried over with three added strings: `derived_by`, `derived_note` and `source_stream_ids`.
- `FRAME_SUMMARY` records are left out: they describe the framing of the input. `repack` writes them for the output.
- When no record matches, the command fails with `no record to write`.

`--stream-id` and `--created-ns` make the output reproducible byte for byte.

```bash
python3 tools/nwt.py extract fixtures/real-market/equity-quotes.nwt work/trade-quotes.nwt --type INSTRUMENT_DEF,TRADE_QUOTE --stream-id 00112233445566778899aabbccddeeff --created-ns 1758020700000000000
python3 tools/nwt.py validate work/trade-quotes.nwt
```

```text
valid records=477 data_frames=1 summaries=0 ordering=ts_event
```

The filter of this example keeps the `INSTRUMENT_DEF` record, so the output passes the state rules. `extract` copies the records that match and no others, so add the definitions to the filter when the output has to stand on its own.

## merge

Combines two or more containers into one, in an order you state.

```bash
python3 tools/nwt.py merge OUT FILE FILE... --order POLICY [--stream-id HEX] [--created-ns NS]
```

| Argument | Meaning |
|---|---|
| `OUT` | Container to write |
| `FILE` | Two or more input containers |
| `--order concat` | Writes the inputs one after another, in the order given. Each input keeps its record order. |
| `--order ts_event` | Interleaves the inputs by `ts_event`. The command accepts only inputs that are in `ts_event` order. Records with equal times come in input order. A record with a null `ts_event` stays directly behind the record before it in its input. |
| `--stream-id HEX`, `--created-ns NS` | Same as for [extract](#extract) |

`--order` is required: the tool does not choose an order for you.

- The output has a new stream ID and renumbered sequences. The dataset names and the producers of the inputs are joined with `+`.
- Inputs that share a publisher ID give it the same name and venue. Otherwise the command fails with `publisher N differs between the inputs`.
- With `--order ts_event`, an input that is out of order makes the command fail with `input N is not in ts_event order; use --order concat`.
- `merge` checks the framing and the manifests. Run `validate` on the result to check the state rules of the combined stream.

```bash
python3 tools/nwt.py merge work/quotes-and-orders.nwt fixtures/real-market/equity-quotes.nwt fixtures/real-market/equity-orders.nwt --order ts_event
python3 tools/nwt.py validate work/quotes-and-orders.nwt
```

```text
valid records=4419 data_frames=1 summaries=0 ordering=ts_event
```

## split

Writes one container for each record type, instrument or day of the input.

```bash
python3 tools/nwt.py split FILE DIR --by KEY
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |
| `DIR` | Folder for the output files. It is created when it does not exist. |
| `--by type` | One file per record type, named `NN-name.nwt`, for example `22-corporate_action.nwt` |
| `--by instrument` | One file per instrument ID, named `instrument-ID.nwt` |
| `--by day` | One file per UTC date of `ts_event`, named `YYYY-MM-DD.nwt`. Records with a null `ts_event` go to `no-time.nwt`. |

Each output file has its own stream ID, renumbered sequences and an exact manifest. A record goes to exactly one file, and definitions are not repeated: the file of one day can use an instrument that is defined in the file of an earlier day. On success the command prints the number of files on standard error.

```bash
python3 tools/nwt.py split fixtures/real-market/equity-bars.nwt work/by-day --by day
ls work/by-day
```

```text
wrote 2 files to work/by-day
2025-09-16.nwt
2025-09-17.nwt
```

## repack

Rewrites a container as a store file: the same records in the same order, in new frames, with Zstandard compression, an `INDEX` and `FRAME_SUMMARY` records.

```bash
python3 tools/nwt.py repack FILE OUT [--frame-bytes N] [--level N] [--raw] [--no-summary] [--stream-id HEX] [--created-ns NS]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |
| `OUT` | Store file to write |
| `--frame-bytes N` | Raw bytes per `DATA` frame, from 48 to 16777216. The default is 1048576. |
| `--level N` | Zstandard level, from 1 to 22. The default is 3. |
| `--raw` | Writes every frame raw |
| `--no-summary` | Leaves out the `FRAME_SUMMARY` frames |
| `--stream-id HEX`, `--created-ns NS` | Same as for [extract](#extract) |

- The output keeps every record and every sequence, and has a new stream ID.
- A frame is stored with Zstandard only when the compressed form is smaller.
- The manifest declares `FRAME_SUMMARY`, so `minor` of the output is 1. It declares an `ordering` when the records have one. The command rejects an input that declares an `ordering` its records do not have.
- `FRAME_SUMMARY` records of the input are replaced by new ones for the new frames.
- Without `libzstd`, the command prints `NWT notice: Zstd library not available; writing raw frames` on standard error and writes raw frames.

```bash
python3 tools/nwt.py repack fixtures/real-market/equity-quotes.nwt work/equity-quotes.store.nwt --frame-bytes 65536
python3 tools/nwt.py validate work/equity-quotes.store.nwt
```

```text
valid records=2481 data_frames=5 summaries=4 ordering=ts_event
```

The input has 2,477 records. The output has four more: one `FRAME_SUMMARY` for each of the four frames that hold the records. [Store profile](STORE.md) describes the layout and how to choose the settings.

## query

Prints the records that match a filter and reads only the frames that can hold a match.

```bash
python3 tools/nwt.py query FILE [--type TYPES] [--instrument IDS] [--from TIME] [--to TIME] [--pretty]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read, with an `INDEX` |
| `--type`, `--instrument`, `--from`, `--to` | [Filters](#filters) |
| `--pretty` | Same as for [cat](#cat) |

`query` reads the `END` frame, then the `INDEX`, then the `FRAME_SUMMARY` frames at the end of the file. It keeps the `DATA` frames whose time range, type mask and instrument range can hold a match, reads those, and prints the matching records as JSON Lines in file order. The result equals `cat` with the same filter applied. On a file without `FRAME_SUMMARY` records it skips frames by time only.

`query` checks the frames it reads: the frame header, the payload CRC-32C and every record it prints. Run `validate` to check the whole file.

The first line of output goes to standard error. It labels the result as partial: the definitions and the book state before the frames that were read are not part of it.

```bash
python3 tools/nwt.py query work/equity-quotes.store.nwt --type TRADE_QUOTE --from 2025-09-16T08:03:04.5303Z --to 2025-09-16T08:03:04.5304Z --pretty
```

```text
# partial: earlier definitions and book state are not included
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530356100Z","ts_recv":"2025-09-16T08:03:04.530521940Z","sequence":"734","price":"177.290000000","quantity":"78.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
{"type_name":"TRADE_QUOTE","record_bytes":"120","record_type":"18","schema_version":"1","flags":"0","publisher_id":"2","channel_id":"0","instrument_id":"11667","ts_event":"2025-09-16T08:03:04.530358866Z","ts_recv":"2025-09-16T08:03:04.530522753Z","sequence":"736","price":"177.290000000","quantity":"250.000000000","trade_id":"0","bid_price":"177.260000000","ask_price":"177.300000000","bid_quantity":"20.000000000","ask_quantity":"1100.000000000","bid_order_count":"1","ask_order_count":"2","aggressor":"0","conditions":"0"}
```

[Store profile](STORE.md#how-a-reader-seeks-by-time-and-instrument) describes the read path step by step.

## resolve

Looks up the instrument that a symbol or an identifier names.

```bash
python3 tools/nwt.py resolve FILE SYMBOL [--at TIME] [--symbology KIND] [--publisher ID]
```

| Argument | Meaning |
|---|---|
| `FILE` | Container with `SYMBOL_MAP` or `SECURITY_DEF` records and an `INDEX` |
| `SYMBOL` | Text to look up: a symbol, an ISIN, a CUSIP or a FIGI |
| `--at TIME` | Moment to look up, in one of the forms of [Filters](#filters). The default is any time. |
| `--symbology KIND` | Kind of symbol to match: `native`, `osi`, `isin`, `figi`, `root`, `continuous` or `cusip`. The default is every kind. |
| `--publisher ID` | Publisher to search. The default is every publisher. |

The command prints one JSON line per match and exits with status 1 and `no mapping found for SYMBOL` when there is none.

- **`SYMBOL_MAP`.** A record matches when its symbol text equals `SYMBOL`. The line holds `source`, `publisher_id`, `instrument_id`, `symbology` (1 native, 2 OSI, 3 ISIN, 4 FIGI, 5 root, 6 continuous), `valid_from_ns`, `valid_to_ns` and `symbol`. The interval is half-open: with `--at T`, a record matches when `valid_from_ns` is at or before T and T is before `valid_to_ns`. An open end prints as `18446744073709551615`. Without `--at`, every interval of the symbol is printed.
- **`SECURITY_DEF`.** A record matches when `SYMBOL` equals its ISIN, its CUSIP, its composite FIGI or its FIGI. The line holds `source`, `publisher_id`, `instrument_id`, the kind of identifier that matched, and the symbol and identifiers of the listing. The latest record of each publisher and instrument counts; with `--at T`, records with a `ts_event` after T are ignored.
- `--symbology cusip` searches `SECURITY_DEF` records only.

A symbol from the sample [listings-nasdaq.nwt](files/samples/listings-nasdaq.nwt):

```bash
python3 tools/nwt.py resolve fixtures/real/listings-nasdaq.nwt AAPL
```

```text
{"source":"SYMBOL_MAP","publisher_id":"1","instrument_id":"4519135547670130507","symbology":"1","valid_from_ns":"1791907860000000000","valid_to_ns":"18446744073709551615","symbol":"AAPL"}
```

An ISIN from the sample [secmaster-us.nwt](files/samples/secmaster-us.nwt). Two listings carry it:

```bash
python3 tools/nwt.py resolve fixtures/real-reference/secmaster-us.nwt US78462F1030
```

```text
{"source":"SECURITY_DEF","publisher_id":"1","instrument_id":"1688030","identifier":"isin","symbol":"SPY","isin":"US78462F1030","cusip":"78462F103","composite_figi":"BBG000BDTBL9","figi":""}
{"source":"SECURITY_DEF","publisher_id":"1","instrument_id":"11756875","identifier":"isin","symbol":"SPY","isin":"US78462F1030","cusip":"78462F103","composite_figi":"BBG000BDTBL9","figi":"BBG000BDTF76"}
```

## stats

Prints the size of every part of a container and the bytes of each record type.

```bash
python3 tools/nwt.py stats FILE
```

| Argument | Meaning |
|---|---|
| `FILE` | Container to read |

The output is plain text, one item per line:

| Line | Content |
|---|---|
| `file_bytes` | Size of the file |
| `header_and_metadata_bytes` | 64-byte header plus the metadata |
| `data_frames` | Number of `DATA` frames, how many of them are Zstandard, and their stored and raw payload bytes |
| `compression_ratio` | Raw payload bytes divided by stored payload bytes of the `DATA` frames, with three decimals; `-` when the file has no data |
| `index_bytes`, `end_bytes` | Size of the `INDEX` frames and of the `END` frame, headers included |
| `records` | Number of records |
| `type` | One line per record type: number, name, record count and record bytes |

The store file written in [repack](#repack):

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

The stored bytes depend on the version of the Zstandard library.

## convert

Converts a source file, such as a CSV export or a public symbol directory, to a container.

```bash
python3 tools/nwt.py convert KIND SRC OUT [--name value]... [--flag]...
```

| Argument | Meaning |
|---|---|
| `KIND` | Format of the source. An unknown kind fails with the list of the known kinds. |
| `SRC` | Source file |
| `OUT` | Container to write |
| `--name value` | Option of the converter, passed through as text. `--name=value` is equivalent. |
| `--flag` | Option of the converter without a value |

The converters are Python modules beside the tool. The kinds for reference data are `mic`, `nasdaqlisted`, `otherlisted`, `options`, `csv-secmaster` and `csv-corporate-actions`; their options are in [Reference data samples](REAL-DATA.md). The kinds for market data are `csv-definition`, `csv-mbo`, `csv-mbp1`, `csv-mbp10`, `csv-cmbp1`, `csv-ohlcv` and `csv-statistics`; their options are in [Market data samples](REAL-DATA-MARKET.md).

On success the command prints a summary of the conversion as JSON on standard output: the policy it applied, the checksum of the source and the number of records of each type. The output carries the same facts in its `PROVENANCE`.

This example converts the ISO 10383 list of market identifier codes and reproduces the sample [venues.nwt](files/samples/venues.nwt) byte for byte:

```bash
python3 tools/nwt.py convert mic fixtures/real/source/ISO10383_MIC.csv work/venues.nwt --retrieved 2026-10-13 > work/venues.provenance.json
cmp work/venues.nwt fixtures/real/venues.nwt
python3 tools/nwt.py validate work/venues.nwt
```

```text
valid records=100 data_frames=1 summaries=0 ordering=none
```

## Use from Python

`tools/nwt.py` is importable. Put `tools` and `examples/python` on `sys.path`, then import `nwt` for the tool and `nwt_example` for the codec.

| Function | What it does |
|---|---|
| `main(argv)` | Runs a command line, for example `main(["validate", path])`, and returns the exit status |
| `select(reader, types=None, instruments=None, t0=None, t1=None)` | Yields the raw bytes of the matching records in file order, reading only the frames that can hold a match. `instruments` holds IDs or `(low, high)` pairs with both ends included. A record matches when `t0 <= ts_event < t1`. |
| `summaries(reader)` | Returns the `FRAME_SUMMARY` records of a store file as a list of dictionaries of integers, found through `END` and `INDEX`. The list is empty for a file without summaries. |
| `parse_time(text)` | Converts a `TIME` of [Filters](#filters) to nanoseconds |

`reader` is an `nwt_example.Reader`. `nwt_example.open_reader(file)` makes one for an open binary file, and `nwt_example.Reader(read_at, size)` makes one for any source that can read n bytes at an offset.

```python
import sys
sys.path[:0] = ["tools", "examples/python"]
import nwt_example
import nwt as tool

with open("work/equity-quotes.store.nwt", "rb") as f:
    reader = nwt_example.open_reader(f)
    for summary in tool.summaries(reader):
        print(summary["data_frame_seq"], summary["stored_bytes"], bin(summary["type_mask"]))
    t0 = tool.parse_time("2025-09-16T08:03:00Z")
    t1 = tool.parse_time("2025-09-16T08:04:00Z")
    for raw in tool.select(reader, types=[18], t0=t0, t1=t1):
        record = nwt_example.decode_record(raw)
        print(record["fields"]["sequence"], record["fields"]["price"])
        break
```

```text
0 9605 0b1000000000001000100
1 9221 0b1000000000000000100
2 8735 0b1000000000000000100
3 7493 0b1000000000000000100
734 177290000000
```

[Store profile](STORE.md#over-any-byte-source) has a program that reads a store file through a `read_at` function and counts the bytes it fetches.
