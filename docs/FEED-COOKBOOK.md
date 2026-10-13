# Working with the examples

This page prepares you to work with the examples. It shows how to build and run the four reference codecs once, which sample and conformance files the examples use, how to read a decoded example, and how the 22 record types group by role. The example, the commands and the conformance vectors of each record type are on its own page; start from [Record types](records/INDEX.md).

## Before you start

### Build a reference codec

Download [nwt-binary-format-kit.zip](files/nwt-binary-format-kit.zip), unpack it, and run every command on this page from the kit root. Build the reference codec of your language once. Each one needs only its own toolchain: Python 3.10 or newer, Rust with Cargo, the .NET 10 SDK, or a C++20 compiler.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
mkdir -p work
python3 examples/python/nwt_example.py write-golden work/python.nwt
cmp work/python.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: Rust -->
```bash
mkdir -p work
cargo build --locked --manifest-path examples/rust/Cargo.toml
examples/rust/target/debug/nwt-example write-golden work/rust.nwt
cmp work/rust.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: C# -->
```bash
mkdir -p work
dotnet build examples/csharp/NwtExample.csproj -o work/csharp
dotnet work/csharp/NwtExample.dll write-golden work/csharp.nwt
cmp work/csharp.nwt fixtures/golden/all-records.nwt
```
<!-- nwt-title: C++ -->
```bash
mkdir -p work
c++ -std=c++20 -O2 examples/cpp/main.cpp -o work/nwt-cpp
work/nwt-cpp write-golden work/cpp.nwt
cmp work/cpp.nwt fixtures/golden/all-records.nwt
```
<!-- /nwt-tabs -->

`write-golden` writes the conformance file, a container of 47 records of 21 record types. `cmp` prints nothing, because every reference codec writes the same bytes as `fixtures/golden/all-records.nwt`.

The C++ command builds the codec without [Zstandard](https://github.com/facebook/zstd). On this page only `all-records.zst.nwt` needs Zstandard; the [Implementation guide](IMPLEMENTATION-GUIDE.md) shows the build with `libzstd`.

### Files the examples use

| File | Contents |
|---|---|
| [all-records.nwt](files/samples/all-records.nwt) | The conformance file: 47 records of 21 record types, every type except FRAME_SUMMARY. In the kit it is `fixtures/golden/all-records.nwt`. |
| [all-records.zst.nwt](files/samples/all-records.zst.nwt) | The same records in Zstandard frames. |
| [records.json](files/records.json) | The schema of all 22 record types. The reference codecs take every layout from it. In the kit it is `schemas/records.json`. |
| `fixtures/catalog.json` | 49 scenarios for types 1–9. The `write` command writes them as one container. |
| `fixtures/catalog-golden.json` | 48 scenarios: every scenario of types 10–22, and the 11 records of types 1–9 that complete the conformance file. |

A scenario is one record written as JSON: a name, the record type, every field as a decimal string, the texts and the levels.

<!-- nwt-file: fixtures/records/002-trade-new.json -->

Each scenario is also stored encoded, as one raw record. `fixtures/records/` holds the scenarios of `fixtures/catalog.json`, and `fixtures/golden/records/` holds those of `fixtures/catalog-golden.json`. A file name is the position of the scenario in its catalog followed by its name, for example `002-trade-new.bin`.

These files are the conformance vectors that the record pages list. `record N` writes the first vector in the table on the page of type N, and `decode-record` accepts any of them:

```bash
python3 examples/python/nwt_example.py decode-record fixtures/records/003-trade-correct.bin
```

The samples are containers converted from exchange and registry data. Open the one that holds the record type you work on:

| Sample | Record types |
|---|---|
| [equity-orders.nwt](files/samples/equity-orders.nwt) | INSTRUMENT_DEF, MBO, TRADE |
| [futures-orders.nwt](files/samples/futures-orders.nwt) | INSTRUMENT_DEF, MBO |
| [equity-quotes.nwt](files/samples/equity-quotes.nwt) | INSTRUMENT_DEF, QUOTE, TRADE_QUOTE |
| [equity-bars.nwt](files/samples/equity-bars.nwt) | INSTRUMENT_DEF, BAR |
| [depth-10.nwt](files/samples/depth-10.nwt) | INSTRUMENT_DEF, OPTION_DEF, BOOK_SNAPSHOT |
| [equity-deltas.nwt](files/samples/equity-deltas.nwt) | INSTRUMENT_DEF, BOOK_DELTA |
| [statistics.nwt](files/samples/statistics.nwt) | INSTRUMENT_DEF, OPTION_DEF, STATISTICS |
| [option-definitions.nwt](files/samples/option-definitions.nwt) | INSTRUMENT_DEF, OPTION_DEF |
| [option-best-quotes.nwt](files/samples/option-best-quotes.nwt) | INSTRUMENT_DEF, OPTION_DEF, BEST_QUOTE |
| [venues.nwt](files/samples/venues.nwt) | VENUE_DEF |
| [listings-nasdaq.nwt](files/samples/listings-nasdaq.nwt), [listings-other.nwt](files/samples/listings-other.nwt) | LISTING, SYMBOL_MAP |
| [secmaster-us.nwt](files/samples/secmaster-us.nwt), [secmaster-global.nwt](files/samples/secmaster-global.nwt) | SECURITY_DEF |
| [corporate-actions-us.nwt](files/samples/corporate-actions-us.nwt), [corporate-actions-global.nwt](files/samples/corporate-actions-global.nwt) | SECURITY_DEF, CORPORATE_ACTION |

[Market data samples](REAL-DATA-MARKET.md) and [Reference data samples](REAL-DATA.md) describe every sample. No sample contains STATUS, GAP, SYSTEM, OPTION_ANALYTICS, IMBALANCE or FRAME_SUMMARY records, so the examples on the pages of those types come from conformance vectors.

### How to read an example

Each example shows one decoded record, and its caption names the file the record comes from.

- Every number is a decimal string, so no 64-bit value is rounded.
- Prices and quantities are the raw integers, scaled by 10⁹: `123450000000` is 123.45.
- Timestamps are nanoseconds since the Unix epoch, in UTC.
- The null sentinel is `-9223372036854775808` (`INT64_MIN`) in a signed field, `18446744073709551615` (`UINT64_MAX`) in an unsigned 64-bit field and `4294967295` (`UINT32_MAX`) in a 32-bit count.

`decode-record` prints the same values as one `name=value` line per field, with the reserved and length fields included and the record number in front. For the `trade-new` vector the report is:

```text
1.record_bytes=88
1.record_type=1
1.schema_version=1
1.flags=0
1.publisher_id=1
1.channel_id=0
1.instrument_id=1001
1.ts_event=1700000000000001000
1.ts_recv=1700000000000001100
1.sequence=2
1.price=123450000000
1.quantity=10000000000
1.trade_id=42
1.original_sequence=0
1.action=1
1.aggressor=1
1.conditions=0
1.reserved=0
```

The four reference codecs print the same report and write the same bytes.

A raw record file holds one record and nothing else. To interpret it, a reader also needs the definitions and the state that precede it in a stream; a complete container supplies them in order. `to-json` prints every record of a container as JSON Lines:

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py to-json fixtures/golden/all-records.nwt --pretty
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example to-json fixtures/golden/all-records.nwt --pretty
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll to-json fixtures/golden/all-records.nwt --pretty
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp to-json fixtures/golden/all-records.nwt --pretty
```
<!-- /nwt-tabs -->

With `--pretty`, prices and quantities are decimals with nine fractional digits, timestamps are ISO 8601 with nanoseconds, and a null value is the JSON value `null`. Without it, every value is the raw integer string. `to-csv FILE TYPE` writes the records of one type as CSV. Both commands read any container, for example `fixtures/real-market/equity-quotes.nwt`.

## How the record types fit together

| Type | Number | Group | Carries |
|---|---:|---|---|
| [`TRADE`](records/TRADE.md) | 1 | Trades and quotes | A trade print with its corrections and cancellation |
| [`QUOTE`](records/QUOTE.md) | 2 | Trades and quotes | The best bid and the best ask of one instrument |
| [`TRADE_QUOTE`](records/TRADE_QUOTE.md) | 18 | Trades and quotes | A trade with the top of book immediately before it |
| [`BEST_QUOTE`](records/BEST_QUOTE.md) | 19 | Trades and quotes | The best bid and offer across venues, with the venue of each side |
| [`MBO`](records/MBO.md) | 4 | Order book | One change to an order-level book, or a snapshot marker |
| [`BOOK_SNAPSHOT`](records/BOOK_SNAPSHOT.md) | 5 | Order book | The whole aggregate book, up to 1,024 levels per side |
| [`BOOK_DELTA`](records/BOOK_DELTA.md) | 15 | Order book | A change to one price level of the aggregate book |
| [`BAR`](records/BAR.md) | 3 | Bars and statistics | A completed bar: open, high, low, close, volume and trade count |
| [`STATISTICS`](records/STATISTICS.md) | 13 | Bars and statistics | An official value: open, high, low, close, settlement, VWAP, volume or open interest |
| [`OPTION_ANALYTICS`](records/OPTION_ANALYTICS.md) | 14 | Bars and statistics | Implied volatility and Greeks of an option |
| [`IMBALANCE`](records/IMBALANCE.md) | 16 | Bars and statistics | The imbalance of an auction |
| [`INSTRUMENT_DEF`](records/INSTRUMENT_DEF.md) | 6 | Reference data | The definition that every market record depends on |
| [`VENUE_DEF`](records/VENUE_DEF.md) | 10 | Reference data | A trading venue or segment, identified by its MIC |
| [`OPTION_DEF`](records/OPTION_DEF.md) | 11 | Reference data | The terms of an option contract |
| [`LISTING`](records/LISTING.md) | 12 | Reference data | One row of a symbol directory |
| [`SYMBOL_MAP`](records/SYMBOL_MAP.md) | 17 | Reference data | A symbol that names an instrument over a time interval |
| [`SECURITY_DEF`](records/SECURITY_DEF.md) | 21 | Reference data | The security-master record of one listing |
| [`CORPORATE_ACTION`](records/CORPORATE_ACTION.md) | 22 | Reference data | One corporate-action event |
| [`STATUS`](records/STATUS.md) | 7 | Status and control | The trading status of an instrument |
| [`GAP`](records/GAP.md) | 8 | Status and control | A discontinuity in the source feed |
| [`SYSTEM`](records/SYSTEM.md) | 9 | Status and control | A heartbeat or a diagnostic message |
| [`FRAME_SUMMARY`](records/FRAME_SUMMARY.md) | 20 | Status and control | A per-frame summary for selective reads |

- **Market records** are [TRADE](records/TRADE.md), [QUOTE](records/QUOTE.md), [BAR](records/BAR.md), [MBO](records/MBO.md), [BOOK_SNAPSHOT](records/BOOK_SNAPSHOT.md), [STATUS](records/STATUS.md), [STATISTICS](records/STATISTICS.md), [OPTION_ANALYTICS](records/OPTION_ANALYTICS.md), [BOOK_DELTA](records/BOOK_DELTA.md), [IMBALANCE](records/IMBALANCE.md), [TRADE_QUOTE](records/TRADE_QUOTE.md) and [BEST_QUOTE](records/BEST_QUOTE.md). Each needs an [INSTRUMENT_DEF](records/INSTRUMENT_DEF.md) for its instrument earlier in the file.
- **Reference records** are [VENUE_DEF](records/VENUE_DEF.md), [OPTION_DEF](records/OPTION_DEF.md), [LISTING](records/LISTING.md), [SYMBOL_MAP](records/SYMBOL_MAP.md), [SECURITY_DEF](records/SECURITY_DEF.md) and [CORPORATE_ACTION](records/CORPORATE_ACTION.md). They need no [INSTRUMENT_DEF](records/INSTRUMENT_DEF.md) and do not replace one.
- [GAP](records/GAP.md) invalidates the book and status state of its publisher and channel. [FRAME_SUMMARY](records/FRAME_SUMMARY.md) supports selective reads and carries no state.
- In a variable-size type, the size given on its record page is the fixed part. The texts follow it, and the record is padded with zero bytes to a multiple of 8.

A typical file for one equity venue has a [VENUE_DEF](records/VENUE_DEF.md), one [INSTRUMENT_DEF](records/INSTRUMENT_DEF.md) per symbol, and then trades, quotes and bars. A reference-data file has [LISTING](records/LISTING.md), [SYMBOL_MAP](records/SYMBOL_MAP.md), [SECURITY_DEF](records/SECURITY_DEF.md) and [CORPORATE_ACTION](records/CORPORATE_ACTION.md) records and no market data.
