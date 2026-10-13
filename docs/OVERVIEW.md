# NWT Binary Format

NWT Binary Format is a binary file and stream format for market data and reference data. It stores trades, quotes, order books, bars, instrument definitions and corporate actions as fixed-layout records inside checksummed frames. The kit contains what you need to build a reader, a writer or a data pipeline: the specification, a field reference, reference codecs in Python, Rust, C# and C++, the `nwt` command, conformance files and samples.

## What NWT is for

Every source of market data has its own message types, units, time formats and ways to mark a missing value. A system that stores this data or passes it on needs one representation that every producer writes the same way and every consumer can verify. NWT is that representation: one file or stream holds records of different types in delivery order, with exact decimal values, nanosecond timestamps and a checksum on every frame.

With the kit you can read and write NWT files in Python, Rust, C# and C++, convert source files to NWT, and inspect, validate and query a file with the `nwt` command. A query by time, record type or instrument reads only the frames that can hold a match. The conformance files let you check your own implementation byte for byte.

## How it works

A converter or a writer turns source data into an NWT container. The container starts with a header and a manifest, which declares the publishers and the record types in use. Frames follow. Each frame holds whole records, carries its own checksum and can be compressed on its own. A reader checks a frame, decodes its records, and uses the index to read only the frames it needs.

![Sources feed a converter and a writer, which produce one NWT container; the nwt command, the four reference codecs and selective readers read it](diagrams/overview.svg "From source data to an NWT file and its readers")

[How it works](HOW-IT-WORKS.md) · [Specification](SPECIFICATION.md) · [Use NWT in practice](USE-CASES.md)

## What the format provides

- **22 record types.** Trades, quotes, bars, order books, statistics, option analytics and reference data share one container.
- **Fixed layouts.** Every record starts with the same 48-byte header, and its size is fixed or computed from length fields.
- **Exact numbers.** Prices and quantities are 64-bit integers scaled by 10⁹, and no floating-point value is stored.
- **Nanosecond timestamps.** Every record carries its event time and its receive time in nanoseconds since the Unix epoch, UTC.
- **Integrity checks.** A CRC-32C protects the container header, the metadata, every frame header and every frame payload.
- **Optional compression.** Each frame is stored raw or as one Zstandard frame, and both kinds can appear in one file.
- **Selective reads.** An optional `INDEX` frame and `FRAME_SUMMARY` records let a reader choose frames by time range, record type and instrument.
- **Reference codecs.** The Python, Rust, C# and C++ codecs read and write every record type and produce byte-identical output for the conformance files.

## Documentation

<!-- nwt-doc-cards -->

<!-- nwt-doc-list -->
- [How it works](HOW-IT-WORKS.md): the container, the frames and the records explained with diagrams.
- [Use NWT in practice](USE-CASES.md): common tasks done with the format and the kit.
- [Specification](SPECIFICATION.md): the byte layouts and rules of the container, the metadata and the frames, and the table of the 22 record types.
- [Record types](records/INDEX.md): one page for each of the 22 types, with its fields, rules, example, commands and conformance vectors.
- [Field reference](FIELD-REFERENCE.md): how values are encoded, and the fields of the record header, the container, the metadata, the frames and the index, with offset, type, width, unit and null value.
- [Working with the examples](FEED-COOKBOOK.md): building the reference codecs once, the sample and conformance files the examples use, and how the record types group by role.
- [Implementation guide](IMPLEMENTATION-GUIDE.md): how to build and run the four reference codecs and how their code is organized.
- [State and recovery](STATE-AND-RECOVERY.md): record order, snapshots, the trade lifecycle and recovery after a gap.
- [Store profile](STORE.md): how to write a file that answers queries by time, record type and instrument.
- [Size and speed](PERFORMANCE.md): measurements of file size and of read and write speed.
- [The nwt command](TOOLS.md): inspect, check, convert, repack and query files from the command line.
- [Reference data samples](REAL-DATA.md): venues, listings, options, securities and corporate actions converted from source files.
- [Market data samples](REAL-DATA-MARKET.md): trades, quotes, order books, bars and statistics converted from exchange exports.
- [Downloads](DOWNLOADS.md): the kit archive, the schema, the conformance files and every sample, with checksums.
- [Glossary](GLOSSARY.md): the terms used in the documentation.
- [Licenses](../THIRD-PARTY-NOTICES.md): third-party software and the notices of the sample data.
<!-- /nwt-doc-list -->

## Record types

Each name links to the page of that record type, with its fields, rules, example and conformance vectors.

| Type | Name | Purpose |
|---:|---|---|
| 1 | [`TRADE`](records/TRADE.md) | Trade, with its correction and cancellation |
| 2 | [`QUOTE`](records/QUOTE.md) | Best bid and ask |
| 3 | [`BAR`](records/BAR.md) | Completed OHLCV bar |
| 4 | [`MBO`](records/MBO.md) | Change to the order book, one order at a time |
| 5 | [`BOOK_SNAPSHOT`](records/BOOK_SNAPSHOT.md) | Aggregate order book, ranked by price |
| 6 | [`INSTRUMENT_DEF`](records/INSTRUMENT_DEF.md) | Instrument definition |
| 7 | [`STATUS`](records/STATUS.md) | Trading status |
| 8 | [`GAP`](records/GAP.md) | Discontinuity in the source |
| 9 | [`SYSTEM`](records/SYSTEM.md) | Heartbeat and diagnostics |
| 10 | [`VENUE_DEF`](records/VENUE_DEF.md) | Trading venue or segment, by market identifier code |
| 11 | [`OPTION_DEF`](records/OPTION_DEF.md) | Option contract terms |
| 12 | [`LISTING`](records/LISTING.md) | Symbol directory entry |
| 13 | [`STATISTICS`](records/STATISTICS.md) | Open, high, low, close, settlement, VWAP, volume, open interest |
| 14 | [`OPTION_ANALYTICS`](records/OPTION_ANALYTICS.md) | Implied volatility and Greeks |
| 15 | [`BOOK_DELTA`](records/BOOK_DELTA.md) | Change to one price level of the aggregate order book |
| 16 | [`IMBALANCE`](records/IMBALANCE.md) | Auction imbalance |
| 17 | [`SYMBOL_MAP`](records/SYMBOL_MAP.md) | Symbol of an instrument over a time interval |
| 18 | [`TRADE_QUOTE`](records/TRADE_QUOTE.md) | Trade with the top of book immediately before it |
| 19 | [`BEST_QUOTE`](records/BEST_QUOTE.md) | Best bid and ask with the venue of each side |
| 20 | [`FRAME_SUMMARY`](records/FRAME_SUMMARY.md) | Summary of one frame, for selective reads |
| 21 | [`SECURITY_DEF`](records/SECURITY_DEF.md) | Security master entry with identifiers and key dates |
| 22 | [`CORPORATE_ACTION`](records/CORPORATE_ACTION.md) | Corporate action event |

## Files

- [nwt-binary-format-kit.zip](files/nwt-binary-format-kit.zip): the whole kit, with the documents, the schema, the reference codecs, the tools and the fixtures.
- [records.json](files/records.json): the machine-readable schema of all 22 record types.
- [all-records.nwt](files/samples/all-records.nwt) and [all-records.zst.nwt](files/samples/all-records.zst.nwt): the conformance files. Each holds 47 records of 21 record types (every type except `FRAME_SUMMARY`), the first in raw frames and the second in Zstandard frames.
- [equity-quotes.nwt](files/samples/equity-quotes.nwt): a sample of equity quotes, with `QUOTE` and `TRADE_QUOTE` records.
- [equity-orders.nwt](files/samples/equity-orders.nwt): a sample of an equity order book, with `MBO` and `TRADE` records.
- [venues.nwt](files/samples/venues.nwt): a sample of trading venues, with `VENUE_DEF` records.
- [SHA256SUMS.txt](files/SHA256SUMS.txt): the checksums of every hosted file.

[Downloads](DOWNLOADS.md) lists every file with its size, record types and checksum. The source of the kit is on [GitHub](https://github.com/nickjavos/nwt-binary-format).

<!-- nwt-repo-card -->

## Requirements

- **Python 3.10 or later** runs the `nwt` command, the converters, the store profile writer, the state rules and the Python reference codec. They use the standard library only.
- **Rust and Cargo** build the Rust reference codec.
- **The .NET 10 SDK** builds the C# reference codec.
- **A C++20 compiler** builds the C++ reference codec.
- **Zstandard frames** need the system library [libzstd](https://github.com/facebook/zstd) in Python, C# and C++, or the [zstd](https://github.com/gyscos/zstd-rs) crate in Rust. Raw frames need no library.
