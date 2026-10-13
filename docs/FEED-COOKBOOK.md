# Examples by record type

This page shows each of the 22 NWT record types on a concrete record: what it carries, the rules that decide whether it is valid, a decoded example, the commands that write and decode it with each reference codec, and the conformance vectors that cover its edge cases. Use it when you implement a reader or a writer and need a known record to compare your output with.

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

These files are the conformance vectors that each section below lists. `record N` writes the first vector in the table of type N, and `decode-record` accepts any of them:

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

[Market data samples](REAL-DATA-MARKET.md) and [Reference data samples](REAL-DATA.md) describe every sample. No sample contains STATUS, GAP, SYSTEM, OPTION_ANALYTICS, IMBALANCE or FRAME_SUMMARY records, so the examples of those types are conformance vectors.

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
| `TRADE` | 1 | Trades and quotes | A trade print with its corrections and cancellation |
| `QUOTE` | 2 | Trades and quotes | The best bid and the best ask of one instrument |
| `TRADE_QUOTE` | 18 | Trades and quotes | A trade with the top of book immediately before it |
| `BEST_QUOTE` | 19 | Trades and quotes | The best bid and offer across venues, with the venue of each side |
| `MBO` | 4 | Order book | One change to an order-level book, or a snapshot marker |
| `BOOK_SNAPSHOT` | 5 | Order book | The whole aggregate book, up to 1,024 levels per side |
| `BOOK_DELTA` | 15 | Order book | A change to one price level of the aggregate book |
| `BAR` | 3 | Bars and statistics | A completed bar: open, high, low, close, volume and trade count |
| `STATISTICS` | 13 | Bars and statistics | An official value: open, high, low, close, settlement, VWAP, volume or open interest |
| `OPTION_ANALYTICS` | 14 | Bars and statistics | Implied volatility and Greeks of an option |
| `IMBALANCE` | 16 | Bars and statistics | The imbalance of an auction |
| `INSTRUMENT_DEF` | 6 | Reference data | The definition that every market record depends on |
| `VENUE_DEF` | 10 | Reference data | A trading venue or segment, identified by its MIC |
| `OPTION_DEF` | 11 | Reference data | The terms of an option contract |
| `LISTING` | 12 | Reference data | One row of a symbol directory |
| `SYMBOL_MAP` | 17 | Reference data | A symbol that names an instrument over a time interval |
| `SECURITY_DEF` | 21 | Reference data | The security-master record of one listing |
| `CORPORATE_ACTION` | 22 | Reference data | One corporate-action event |
| `STATUS` | 7 | Status and control | The trading status of an instrument |
| `GAP` | 8 | Status and control | A discontinuity in the source feed |
| `SYSTEM` | 9 | Status and control | A heartbeat or a diagnostic message |
| `FRAME_SUMMARY` | 20 | Status and control | A per-frame summary for selective reads |

- **Market records** are TRADE, QUOTE, BAR, MBO, BOOK_SNAPSHOT, STATUS, STATISTICS, OPTION_ANALYTICS, BOOK_DELTA, IMBALANCE, TRADE_QUOTE and BEST_QUOTE. Each needs an INSTRUMENT_DEF for its instrument earlier in the file.
- **Reference records** are VENUE_DEF, OPTION_DEF, LISTING, SYMBOL_MAP, SECURITY_DEF and CORPORATE_ACTION. They need no INSTRUMENT_DEF and do not replace one.
- GAP invalidates the book and status state of its publisher and channel. FRAME_SUMMARY supports selective reads and carries no state.
- In a variable-size type, the size given in its section is the fixed part. The texts follow it, and the record is padded with zero bytes to a multiple of 8.

A typical file for one equity venue has a VENUE_DEF, one INSTRUMENT_DEF per symbol, and then trades, quotes and bars. A reference-data file has LISTING, SYMBOL_MAP, SECURITY_DEF and CORPORATE_ACTION records and no market data.

## TRADE

A TRADE record (type 1, 88 bytes) is one trade print: price, quantity, trade identifier, aggressor and conditions. A producer emits it for every execution, and again when the venue corrects or cancels the trade. NEW starts a trade, CORRECT replaces its price, quantity, aggressor and conditions, and CANCEL ends it.

[Field reference](FIELD-REFERENCE.md#trade) · [Specification](SPECIFICATION.md#trade)

- NEW has a non-null price, a positive quantity, a nonzero `trade_id` and `original_sequence` 0.
- CORRECT and CANCEL carry the same `trade_id` and set `original_sequence` to the sequence of the NEW record, never to an earlier correction.
- CANCEL carries a null price, a null quantity, aggressor 0 and conditions 0. A canceled trade cannot be corrected again.
- A price can be negative or zero.
- A trade does not change an order-level book. The matching MBO MODIFY or DELETE from the venue does.

**Example.**

<!-- nwt-example: 1 -->

**Write and decode.** `record 1` writes the `trade-new` vector (88 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 1 work/type-1-python.bin
python3 examples/python/nwt_example.py decode-record work/type-1-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 1 work/type-1-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-1-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 1 work/type-1-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-1-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 1 work/type-1-cpp.bin
work/nwt-cpp decode-record work/type-1-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `trade-new` | `fixtures/records/002-trade-new.bin` | NEW: price 123.45, quantity 10, `trade_id` 42, buyer aggressor. |
| `trade-correct` | `fixtures/records/003-trade-correct.bin` | CORRECT of trade 42: new price and quantity, seller aggressor, off-book condition. `original_sequence` names the NEW record. |
| `trade-cancel` | `fixtures/records/004-trade-cancel.bin` | CANCEL of trade 42 after the correction: null price and quantity, aggressor 0, conditions 0. `original_sequence` still names the NEW record. |
| `trade-negative-price` | `fixtures/records/005-trade-negative-price.bin` | NEW with a negative price (−1.25) and a fractional quantity (0.5), unknown aggressor, and the header flags REPLAY and SUSPECT set. |
| `trade-new` | `fixtures/golden/records/015-trade-new.bin` | The trade of the conformance file: NEW, buyer aggressor. |

## QUOTE

A QUOTE record (type 2, 96 bytes) is the best bid and the best ask of one instrument, each with its quantity and order count. A producer emits it whenever the top of book changes. Every record replaces both sides, and an empty quote is valid and clears both.

[Field reference](FIELD-REFERENCE.md#quote) · [Specification](SPECIFICATION.md#quote)

- An absent side has a null price, quantity 0 and count 0. A present side has a non-null price and a positive quantity; its count is positive or `UINT32_MAX` (unknown).
- Crossed and locked quotes are valid: a reader does not reject a quote because bid ≥ ask.
- Bit 0 of `quote_flags` marks an indicative quote.
- A quote does not clear MBO or aggregate-depth state.

**Example.**

<!-- nwt-example: 2 -->

**Write and decode.** `record 2` writes the `quote-two-sided` vector (96 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 2 work/type-2-python.bin
python3 examples/python/nwt_example.py decode-record work/type-2-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 2 work/type-2-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-2-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 2 work/type-2-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-2-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 2 work/type-2-cpp.bin
work/nwt-cpp decode-record work/type-2-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `quote-two-sided` | `fixtures/records/006-quote-two-sided.bin` | Both sides present, with order counts. |
| `quote-one-sided` | `fixtures/records/007-quote-one-sided.bin` | Bid only. The ask has a null price, quantity 0 and count 0; the bid order count is unknown (`UINT32_MAX`). |
| `quote-empty` | `fixtures/records/008-quote-empty.bin` | Both sides absent. Clears the quote. |
| `quote-crossed` | `fixtures/records/009-quote-crossed.bin` | Bid above ask, with the indicative flag set. Valid. |
| `quote-recovery` | `fixtures/records/033-quote-recovery.bin` | The first quote after the GAP vectors. Restores the quote state. |
| `quote-two-sided` | `fixtures/golden/records/016-quote-two-sided.bin` | The quote of the conformance file: both sides present. |

## BAR

A BAR record (type 3, 112 bytes) is one completed time bucket built from trades: open, high, low, close, volume and trade count over the half-open interval `[interval_start_ns, interval_end_ns)`. A producer emits it when the interval closes. `ts_event` equals the interval end, so timestamp order can differ from arrival order.

[Field reference](FIELD-REFERENCE.md#bar) · [Specification](SPECIFICATION.md#bar)

- A nonempty bar has non-null open, high, low and close with `low ≤ open, close ≤ high`, a positive volume and a positive trade count.
- An empty bar sets bit 0 of `bar_flags` and has four null prices, volume 0 and count 0. Empty bars are never forward-filled.
- Each `(publisher, channel, instrument, start, end)` appears at most once in a container.
- `volume` is traded quantity, not currency turnover.

**Example.**

<!-- nwt-example: 3 -->

**Write and decode.** `record 3` writes the `bar-complete` vector (112 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 3 work/type-3-python.bin
python3 examples/python/nwt_example.py decode-record work/type-3-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 3 work/type-3-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-3-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 3 work/type-3-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-3-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 3 work/type-3-cpp.bin
work/nwt-cpp decode-record work/type-3-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `bar-complete` | `fixtures/records/010-bar-complete.bin` | A 60-second bar built from four trades. `ts_event` is the interval end, which is earlier than the `ts_event` of the records before it in the catalog. |
| `bar-empty` | `fixtures/records/011-bar-empty.bin` | Empty flag, four null prices, volume 0 and trade count 0. |
| `bar-complete` | `fixtures/golden/records/017-bar-complete.bin` | The bar of the conformance file: one trade, so open, high, low and close are equal. |

## MBO

An MBO record (type 4, 88 bytes) is one change to an order-level book: an order added, modified or deleted, the book cleared, or a snapshot marker. A producer emits it for every order event of a market-by-order source. The six actions are ADD, MODIFY, DELETE, CLEAR, SNAPSHOT_BEGIN and SNAPSHOT_END. `quantity` is the quantity that remains in the order, never a delta.

[Field reference](FIELD-REFERENCE.md#mbo) · [Specification](SPECIFICATION.md#mbo)

- A book is valid only after CLEAR or a completed snapshot. ADD alone does not prove a complete book.
- A snapshot is built privately between SNAPSHOT_BEGIN and SNAPSHOT_END and can cross DATA frames. Only SNAPSHOT_END commits it.
- MODIFY replaces price, quantity and priority and keeps the side. A change of side is a DELETE followed by an ADD.
- DELETE, CLEAR and the snapshot markers carry a null price, quantity 0, a null priority and side 0. `order_id` is 0 only for CLEAR and the snapshot markers.
- A lower known `priority` is earlier in the queue at one side and price; `UINT64_MAX` means unknown.

[State and recovery](STATE-AND-RECOVERY.md) shows the book states and what a GAP does to them.

**Example.**

<!-- nwt-example: 4 -->

**Write and decode.** `record 4` writes the `mbo-clear` vector (88 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 4 work/type-4-python.bin
python3 examples/python/nwt_example.py decode-record work/type-4-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 4 work/type-4-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-4-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 4 work/type-4-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-4-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 4 work/type-4-cpp.bin
work/nwt-cpp decode-record work/type-4-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `mbo-clear` | `fixtures/records/012-mbo-clear.bin` | CLEAR: declares a valid empty book. |
| `mbo-add` | `fixtures/records/013-mbo-add.bin` | ADD of bid order 101 with a known priority. |
| `mbo-modify` | `fixtures/records/014-mbo-modify.bin` | MODIFY of order 101: new price, remaining quantity and priority, same side. |
| `mbo-delete` | `fixtures/records/015-mbo-delete.bin` | DELETE of order 101: null price, quantity 0, null priority, side 0. |
| `mbo-snapshot-begin` | `fixtures/records/016-mbo-snapshot-begin.bin` | SNAPSHOT_BEGIN: opens a snapshot that replaces the book. |
| `mbo-snapshot-bid` | `fixtures/records/017-mbo-snapshot-bid.bin` | ADD of a bid order inside the snapshot. |
| `mbo-snapshot-ask` | `fixtures/records/018-mbo-snapshot-ask.bin` | ADD of an ask order inside the snapshot, with an unknown priority (`UINT64_MAX`). |
| `mbo-snapshot-end` | `fixtures/records/019-mbo-snapshot-end.bin` | SNAPSHOT_END: commits the snapshot. In the container that `write` produces, this snapshot crosses a DATA frame boundary. |
| `mbo-recovery-begin` | `fixtures/records/035-mbo-recovery-begin.bin` | SNAPSHOT_BEGIN of the snapshot sent after the GAP vectors. |
| `mbo-recovery-add` | `fixtures/records/036-mbo-recovery-add.bin` | The single order of the recovery snapshot. |
| `mbo-recovery-end` | `fixtures/records/037-mbo-recovery-end.bin` | SNAPSHOT_END of the recovery snapshot. The book is valid again. |
| `mbo-clear` | `fixtures/golden/records/025-mbo-clear.bin` | The MBO CLEAR of the conformance file. |
| `mbo-add` | `fixtures/golden/records/026-mbo-add.bin` | The MBO ADD of the conformance file: one bid order. |

## BOOK_SNAPSHOT

A BOOK_SNAPSHOT record (type 5, 56 bytes plus 48 bytes per level) replaces a ranked aggregate book atomically, with up to 1,024 levels per side. A producer emits it to publish the whole depth: on every update of a depth-snapshot source, at the start of a stream, and to restore the book after a GAP. Level `i` pairs the bid at rank `i` with the ask at rank `i`.

[Field reference](FIELD-REFERENCE.md#book_snapshot) · [Specification](SPECIFICATION.md#book_snapshot)

- Bids strictly decrease in price and asks strictly increase. Absent elements of a side form its suffix.
- Bit 0 of `book_flags`, depth-limited, means that deeper prices may exist. Such a record is not the full exchange book.
- Zero levels is a valid empty book.
- A snapshot cannot rebuild individual orders or repair MBO state.
- `to-csv` rejects this type, because the number of levels varies from record to record. Use `to-json`.

**Example.**

<!-- nwt-example: 5 -->

**Write and decode.** `record 5` writes the `book-two-levels` vector (152 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 5 work/type-5-python.bin
python3 examples/python/nwt_example.py decode-record work/type-5-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 5 work/type-5-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-5-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 5 work/type-5-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-5-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 5 work/type-5-cpp.bin
work/nwt-cpp decode-record work/type-5-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `book-two-levels` | `fixtures/records/020-book-two-levels.bin` | Two levels. The second has a bid only, so the absent ask forms the suffix of its side. |
| `book-empty` | `fixtures/records/021-book-empty.bin` | Zero levels: a valid empty book. |
| `book-depth-limited` | `fixtures/records/022-book-depth-limited.bin` | One level with the depth-limited flag. |
| `book-recovery` | `fixtures/records/034-book-recovery.bin` | The snapshot sent after the GAP vectors. Restores the aggregate book. |
| `book-snapshot` | `fixtures/golden/records/019-book-snapshot.bin` | The snapshot of the conformance file: two full levels. The BOOK_DELTA vectors change this book. |

## INSTRUMENT_DEF

An INSTRUMENT_DEF record (type 6, 112 bytes plus text) is the definition that every market record depends on: symbol, venue, currency, quantity unit, price and quantity increments, contract multiplier, expiration, strike, underlying and one of eight asset classes. A producer emits it before the first market record of an instrument, and again when the definition changes.

[Field reference](FIELD-REFERENCE.md#instrument_def) · [Specification](SPECIFICATION.md#instrument_def)

- A definition precedes every market record for its instrument in byte order. A later definition replaces the earlier one for the records that follow it.
- Currency and quantity unit never change for an existing instrument ID.
- A fact the producer does not know is null or “unspecified”. Option rights are not inferred from the symbol; OPTION_DEF carries them.

**Example.**

<!-- nwt-example: 6 -->

**Write and decode.** `record 6` writes the `definition-1` vector (136 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 6 work/type-6-python.bin
python3 examples/python/nwt_example.py decode-record work/type-6-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 6 work/type-6-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-6-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 6 work/type-6-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-6-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 6 work/type-6-cpp.bin
work/nwt-cpp decode-record work/type-6-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `definition-1` | `fixtures/records/001-definition-1.bin` | Equity (`asset_class` 1): null expiration and strike, no underlying. The other vectors of types 1–7 in this catalog refer to this instrument. |
| `definition-0` | `fixtures/records/043-definition-0.bin` | `asset_class` 0, unspecified. |
| `definition-2` | `fixtures/records/044-definition-2.bin` | Future (`asset_class` 2) with an expiration. |
| `definition-3` | `fixtures/records/045-definition-3.bin` | Option (`asset_class` 3) with an expiration, a strike and an underlying instrument. |
| `definition-4` | `fixtures/records/046-definition-4.bin` | FX (`asset_class` 4). |
| `definition-5` | `fixtures/records/047-definition-5.bin` | Crypto (`asset_class` 5). |
| `definition-6` | `fixtures/records/048-definition-6.bin` | Index (`asset_class` 6). |
| `definition-7` | `fixtures/records/049-definition-7.bin` | Fixed income (`asset_class` 7). |
| `def-equity` | `fixtures/golden/records/001-def-equity.bin` | The equity that the market vectors of the conformance file refer to. |
| `def-option` | `fixtures/golden/records/002-def-option.bin` | The option on that equity: expiration, strike, underlying, multiplier 100 and a 21-byte OSI symbol. |

## STATUS

A STATUS record (type 7, 64 bytes) is the trading status of one instrument on one channel, with a reason. A producer emits it when the venue changes the trading state, and each record replaces the previous status. It does not clear books and does not forbid trades during a halt or an auction.

[Field reference](FIELD-REFERENCE.md#status) · [Specification](SPECIFICATION.md#status)

- `status` is 0 unknown, 1 pre-open, 2 open, 3 halted, 4 closed or 5 auction. `reason` is 0 unspecified, 1 scheduled, 2 volatility, 3 regulatory or 4 technical. Any other value is invalid.
- A GAP invalidates status. A new STATUS record restores it.

**Example.**

<!-- nwt-example: 7 -->

**Write and decode.** `record 7` writes the `status-0` vector (64 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 7 work/type-7-python.bin
python3 examples/python/nwt_example.py decode-record work/type-7-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 7 work/type-7-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-7-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 7 work/type-7-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-7-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 7 work/type-7-cpp.bin
work/nwt-cpp decode-record work/type-7-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `status-0` | `fixtures/records/023-status-0.bin` | `status` 0 (unknown), `reason` 0 (unspecified). |
| `status-1` | `fixtures/records/024-status-1.bin` | `status` 1 (pre-open), `reason` 1 (scheduled). |
| `status-2` | `fixtures/records/025-status-2.bin` | `status` 2 (open), `reason` 2 (volatility). |
| `status-3` | `fixtures/records/026-status-3.bin` | `status` 3 (halted), `reason` 3 (regulatory). |
| `status-4` | `fixtures/records/027-status-4.bin` | `status` 4 (closed), `reason` 4 (technical). |
| `status-5` | `fixtures/records/028-status-5.bin` | `status` 5 (auction), `reason` 0 (unspecified). |
| `status-recovery` | `fixtures/records/038-status-recovery.bin` | The status sent after the GAP vectors: open, reason technical. Restores the status state. |
| `status-open` | `fixtures/golden/records/018-status-open.bin` | The status of the conformance file: open, reason scheduled. |

## GAP

A GAP record (type 8, 80 bytes) reports a discontinuity in the source feed, not a missing NWT frame. A producer emits it when source messages were lost or may have been lost. It invalidates all book and status state of its publisher and channel.

[Field reference](FIELD-REFERENCE.md#gap) · [Specification](SPECIFICATION.md#gap)

- The source sequence bounds are inclusive. Both are null when unknown.
- `reason` is 1 source packet loss, 2 source reset, 3 producer overflow or 4 unknown discontinuity.
- `recovery_id` is nonzero and unique among the GAP records of the container.
- Quote, depth, MBO and status each recover on their own record. Trade and bar completeness stays uncertain for the gap interval.

[State and recovery](STATE-AND-RECOVERY.md) describes recovery after a GAP.

**Example.**

<!-- nwt-example: 8 -->

**Write and decode.** `record 8` writes the `gap-1` vector (80 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 8 work/type-8-python.bin
python3 examples/python/nwt_example.py decode-record work/type-8-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 8 work/type-8-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-8-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 8 work/type-8-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-8-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 8 work/type-8-cpp.bin
work/nwt-cpp decode-record work/type-8-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `gap-1` | `fixtures/records/029-gap-1.bin` | `reason` 1, source packet loss, with the known bounds 100–105. |
| `gap-2` | `fixtures/records/030-gap-2.bin` | `reason` 2, source reset. Both bounds are null. |
| `gap-3` | `fixtures/records/031-gap-3.bin` | `reason` 3, producer overflow. Both bounds are null. |
| `gap-4` | `fixtures/records/032-gap-4.bin` | `reason` 4, unknown discontinuity. Both bounds are null. |
| `gap` | `fixtures/golden/records/041-gap.bin` | The GAP of the conformance file: source packet loss, bounds 500–509. |

## SYSTEM

A SYSTEM record (type 9, 64 bytes plus text) is a heartbeat or a diagnostic message with UTF-8 text of up to 4,096 bytes. A producer emits heartbeats on a quiet stream and info, warning and error messages for operators. Diagnostics never trigger commands or state repair.

[Field reference](FIELD-REFERENCE.md#system) · [Specification](SPECIFICATION.md#system)

- `code` is 1 heartbeat, 2 info, 3 warning or 4 error. `severity` follows the code: 0 for heartbeat and info, 1 for warning, 2 for error.
- A heartbeat has no text and no related recovery ID.
- `related_recovery_id` is 0 or the `recovery_id` of an earlier GAP.
- Text lengths count bytes, not characters.

**Example.**

<!-- nwt-example: 9 -->

**Write and decode.** `record 9` writes the `system-1` vector (64 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 9 work/type-9-python.bin
python3 examples/python/nwt_example.py decode-record work/type-9-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 9 work/type-9-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-9-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 9 work/type-9-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-9-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 9 work/type-9-cpp.bin
work/nwt-cpp decode-record work/type-9-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `system-1` | `fixtures/records/039-system-1.bin` | Heartbeat: no text, `related_recovery_id` 0. |
| `system-2` | `fixtures/records/040-system-2.bin` | Info message that refers to the GAP with `recovery_id` 4. Its text mixes ASCII, accented Latin and CJK characters, so its byte length differs from its character count. |
| `system-3` | `fixtures/records/041-system-3.bin` | Warning, `severity` 1, with the same text. |
| `system-4` | `fixtures/records/042-system-4.bin` | Error, `severity` 2, with the same text. |
| `system-heartbeat` | `fixtures/golden/records/042-system-heartbeat.bin` | The heartbeat of the conformance file, sent with publisher 0. |

## VENUE_DEF

A VENUE_DEF record (type 10, 96 bytes plus text) describes a trading venue or one of its segments, identified by a market identifier code (MIC). A producer emits it once per venue, and again when the venue record changes. It is a reference record: publisher is nonzero, instrument is 0, and it needs no INSTRUMENT_DEF.

[Field reference](FIELD-REFERENCE.md#venue_def) · [Specification](SPECIFICATION.md#venue_def)

- Identity is `(publisher, mic)`. A later record replaces the earlier one.
- `kind` 1 is an operating venue, whose `mic` equals `operating_mic`. `kind` 2 is a market segment.
- MIC and country are uppercase ASCII letters or digits. Dates are midnight UTC of the source date.
- The record has nine texts, all counted in bytes. `name` is 1–255 bytes; `lei` is 0 or 20 bytes.

**Example.**

<!-- nwt-example: 10 -->

**Write and decode.** `record 10` writes the `venue-operating` vector (192 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 10 work/type-10-python.bin
python3 examples/python/nwt_example.py decode-record work/type-10-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 10 work/type-10-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-10-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 10 work/type-10-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-10-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 10 work/type-10-cpp.bin
work/nwt-cpp decode-record work/type-10-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `venue-operating` | `fixtures/golden/records/003-venue-operating.bin` | Operating venue (`kind` 1, `mic` equal to `operating_mic`), active, with all nine texts filled. |
| `venue-segment-unicode` | `fixtures/golden/records/004-venue-segment-unicode.bin` | Market segment (`kind` 2) of that venue, status updated. `name` is 128 characters and exactly 255 bytes of UTF-8, the maximum; the optional texts are empty. |
| `venue-expired` | `fixtures/golden/records/005-venue-expired.bin` | Expired venue (`status` 3) with an expiry date, a null `created_ns`, and empty `legal_entity` and `lei`. |

## OPTION_DEF

An OPTION_DEF record (type 11, 96 bytes plus text) carries the terms of one option contract: underlying, expiration, strike, multiplier, right, exercise style, settlement, and the root, underlying and OSI symbols. A producer emits it for each option contract, and again when the terms change. A fact the producer does not know is written as “unknown”.

[Field reference](FIELD-REFERENCE.md#option_def) · [Specification](SPECIFICATION.md#option_def)

- Identity is `(publisher, instrument)`. A later record replaces the earlier one.
- With `underlying_instrument_id` 0, `underlying_symbol` is nonempty.
- If an INSTRUMENT_DEF exists for the instrument, its asset class is option, and its expiration, strike and underlying equal those of this record.
- Exercise style and settlement are never inferred from the symbol.

**Example.**

<!-- nwt-example: 11 -->

**Write and decode.** `record 11` writes the `option-def-call` vector (128 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 11 work/type-11-python.bin
python3 examples/python/nwt_example.py decode-record work/type-11-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 11 work/type-11-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-11-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 11 work/type-11-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-11-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 11 work/type-11-cpp.bin
work/nwt-cpp decode-record work/type-11-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `option-def-call` | `fixtures/golden/records/010-option-def-call.bin` | Call with American exercise, physical settlement, a normal-hours close, multiplier 100 and a 21-byte OSI symbol. The underlying is given by instrument ID. |
| `option-def-unknowns` | `fixtures/golden/records/011-option-def-unknowns.bin` | Put with `underlying_instrument_id` 0 and the underlying named by symbol. Multiplier, exercise style, settlement and closing type are unknown; the pending and adjusted flags are set; the OSI symbol and the currency are empty. |

## LISTING

A LISTING record (type 12, 72 bytes plus text) is one row of a symbol directory: symbol, name, listing venue, round lot, ETF and test-issue flags, market tier and financial status. A producer emits one record per listed instrument when it publishes or refreshes the directory. It is a reference record.

[Field reference](FIELD-REFERENCE.md#listing) · [Specification](SPECIFICATION.md#listing)

- Identity is `(publisher, instrument)`. A later record replaces the earlier one.
- Bits 1–3 of `financial_flags` (deficient, delinquent, bankrupt) require bit 0 (reported). The value 1 means normal; 0 means the source reports no financial status.
- `round_lot` is a whole count, not scaled by 10⁹; `UINT32_MAX` means unknown.
- The `ts_event` of a directory row is often null.

**Example.**

<!-- nwt-example: 12 -->

**Write and decode.** `record 12` writes the `listing-normal` vector (120 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 12 work/type-12-python.bin
python3 examples/python/nwt_example.py decode-record work/type-12-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 12 work/type-12-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-12-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 12 work/type-12-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-12-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 12 work/type-12-cpp.bin
work/nwt-cpp decode-record work/type-12-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `listing-normal` | `fixtures/golden/records/006-listing-normal.bin` | Common stock: round lot 100, `market_tier` 1, `financial_flags` 1 (reported, normal), null `ts_event`. |
| `listing-etf-deficient` | `fixtures/golden/records/007-listing-etf-deficient.bin` | ETF flag, `market_tier` 2, `financial_flags` 3 (reported and deficient), empty `cqs_symbol`. |
| `listing-minimal` | `fixtures/golden/records/008-listing-minimal.bin` | Only `symbol` is filled: both timestamps are null, `round_lot` is unknown (`UINT32_MAX`) and every optional text is empty. |
| `listing-awkward-text` | `fixtures/golden/records/009-listing-awkward-text.bin` | Test-issue flag and a `name` that contains a comma, double quotes, a backslash, a line break, a control character and a non-ASCII letter. Exercises escaping in JSON and CSV output. |

## STATISTICS

A STATISTICS record (type 13, 80 bytes) is one official statistic of an instrument: open, high, low, close, settlement, VWAP, volume or open interest, with the session or date it refers to in `ts_ref`. A producer emits it when the venue publishes, revises or withdraws an official value.

[Field reference](FIELD-REFERENCE.md#statistics) · [Specification](SPECIFICATION.md#statistics)

- `stat_type` 1–6 are price types (open, high, low, close, settlement, VWAP); 7 and 8 are quantity types (volume, open interest).
- SET of a price type has a non-null price and a null quantity. SET of a quantity type has the reverse.
- DELETE has both values null and flags 0.
- The latest SET per `(instrument, stat_type, ts_ref)` wins; DELETE withdraws it.
- Bit 0 of `stat_flags` marks a preliminary value.

**Example.**

<!-- nwt-example: 13 -->

**Write and decode.** `record 13` writes the `stat-open` vector (80 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 13 work/type-13-python.bin
python3 examples/python/nwt_example.py decode-record work/type-13-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 13 work/type-13-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-13-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 13 work/type-13-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-13-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 13 work/type-13-cpp.bin
work/nwt-cpp decode-record work/type-13-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `stat-open` | `fixtures/golden/records/027-stat-open.bin` | SET of the open price: non-null price, null quantity. |
| `stat-settlement-preliminary` | `fixtures/golden/records/028-stat-settlement-preliminary.bin` | SET of the settlement price with the preliminary flag. |
| `stat-volume` | `fixtures/golden/records/029-stat-volume.bin` | SET of the volume, a quantity type: null price, non-null quantity. |
| `stat-open-interest` | `fixtures/golden/records/030-stat-open-interest.bin` | SET of the open interest of the option. |
| `stat-delete` | `fixtures/golden/records/031-stat-delete.bin` | DELETE of the settlement price: both values null, flags 0. |

## OPTION_ANALYTICS

An OPTION_ANALYTICS record (type 14, 120 bytes) carries implied volatility, delta, gamma, theta, vega and rho of an option, with the underlying price and a theoretical price. A producer emits it when it recalculates the analytics. Every value is a fixed-point integer scaled by 10⁹ and independently nullable.

[Field reference](FIELD-REFERENCE.md#option_analytics) · [Specification](SPECIFICATION.md#option_analytics)

- The definition of the instrument has the asset class option.
- At least one of the six analytics is non-null.
- Non-null implied volatility and gamma are not negative. Non-null delta lies between −1 and +1.
- An implied volatility of 1 means 100%. Theta is per calendar day; vega and rho are per 0.01 change in volatility and in rate.
- No floating point is used on the wire. A producer rounds to nine decimals, and the wire value is authoritative.
- Each record replaces the previous analytics of the instrument.

**Example.**

<!-- nwt-example: 14 -->

**Write and decode.** `record 14` writes the `analytics-full` vector (120 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 14 work/type-14-python.bin
python3 examples/python/nwt_example.py decode-record work/type-14-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 14 work/type-14-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-14-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 14 work/type-14-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-14-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 14 work/type-14-cpp.bin
work/nwt-cpp decode-record work/type-14-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `analytics-full` | `fixtures/golden/records/032-analytics-full.bin` | All eight values present; price basis mid, model Black-Scholes-Merton. |
| `analytics-iv-only` | `fixtures/golden/records/033-analytics-iv-only.bin` | Only the implied volatility is non-null; price basis and model are unspecified. |
| `analytics-put-negative` | `fixtures/golden/records/034-analytics-put-negative.bin` | Negative delta and rho, as for a put; price basis settlement, binomial model. |

## BOOK_DELTA

A BOOK_DELTA record (type 15, 72 bytes) changes one price level of the aggregate book that BOOK_SNAPSHOT replaces. A producer emits it for incremental depth updates between snapshots. Levels are keyed by price, not by rank. The manifest declares this type with `required` true.

[Field reference](FIELD-REFERENCE.md#book_delta) · [Specification](SPECIFICATION.md#book_delta)

- SET adds a level or replaces its quantity and order count. DELETE removes a level. CLEAR empties one side, or the whole book when `side` is 0.
- The book is valid after a BOOK_SNAPSHOT or a CLEAR with `side` 0. A delta against an invalid book is an error. A GAP invalidates the book.
- Bit 0 of `delta_flags`, LAST_IN_EVENT, marks the last delta of one source event.
- A side never grows beyond 1,024 levels, so the state can always be sent again as one BOOK_SNAPSHOT.

[State and recovery](STATE-AND-RECOVERY.md) describes the aggregate book with deltas.

**Example.**

<!-- nwt-example: 15 -->

**Write and decode.** `record 15` writes the `delta-set-bid` vector (72 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 15 work/type-15-python.bin
python3 examples/python/nwt_example.py decode-record work/type-15-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 15 work/type-15-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-15-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 15 work/type-15-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-15-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 15 work/type-15-cpp.bin
work/nwt-cpp decode-record work/type-15-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `delta-set-bid` | `fixtures/golden/records/020-delta-set-bid.bin` | SET of a new bid level with order count 1. The first of two deltas of one source event. |
| `delta-set-ask-last` | `fixtures/golden/records/021-delta-set-ask-last.bin` | SET that replaces an ask level, with an unknown order count and LAST_IN_EVENT set. It has the same `ts_event` as `delta-set-bid`. |
| `delta-delete` | `fixtures/golden/records/022-delta-delete.bin` | DELETE of the bid level at 149.23: quantity 0, order count `UINT32_MAX`. |
| `delta-clear-side` | `fixtures/golden/records/023-delta-clear-side.bin` | CLEAR of the ask side, with a null price. |
| `delta-clear-all` | `fixtures/golden/records/024-delta-clear-all.bin` | CLEAR with `side` 0: empties the whole book and leaves it valid. |

## IMBALANCE

An IMBALANCE record (type 16, 104 bytes) is the imbalance of an opening, closing or intraday auction: the reference, near and far prices, the paired quantity, and the unmatched quantity with its side. A producer emits it while the venue publishes imbalance information ahead of an auction. It is informational and changes no book or status state.

[Field reference](FIELD-REFERENCE.md#imbalance) · [Specification](SPECIFICATION.md#imbalance)

- `imbalance_side` is 0 exactly when `imbalance_quantity` is 0.
- `reference_price` and `imbalance_quantity` are never null. The auction time, the near and far prices and the paired quantity can be null.
- Each record replaces the previous imbalance of the instrument.

**Example.**

<!-- nwt-example: 16 -->

**Write and decode.** `record 16` writes the `imbalance-buy` vector (104 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 16 work/type-16-python.bin
python3 examples/python/nwt_example.py decode-record work/type-16-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 16 work/type-16-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-16-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 16 work/type-16-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-16-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 16 work/type-16-cpp.bin
work/nwt-cpp decode-record work/type-16-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `imbalance-buy` | `fixtures/golden/records/035-imbalance-buy.bin` | Closing auction with a buy imbalance; every price and quantity is present. |
| `imbalance-none` | `fixtures/golden/records/036-imbalance-none.bin` | No imbalance: `imbalance_side` 0 and `imbalance_quantity` 0. The auction time, the near and far prices and the paired quantity are null; the auction type is unspecified. |

## SYMBOL_MAP

A SYMBOL_MAP record (type 17, 72 bytes plus text) states that a symbol names an instrument over a half-open time interval, in one of six symbologies: native, OSI, ISIN, FIGI, root or continuous. A producer emits it to tie external identifiers to instrument IDs, and again when a symbol starts to name another instrument. It is a reference record.

[Field reference](FIELD-REFERENCE.md#symbol_map) · [Specification](SPECIFICATION.md#symbol_map)

- The header instrument is the mapped instrument.
- For symbologies 1–4 and 6, the intervals of one `(publisher, symbology, symbol)` do not overlap: a symbol names one instrument at any time.
- Symbology 5, root, is one-to-many. One instrument can have many symbols.
- A null `valid_to_ns` means an open-ended interval.

**Example.**

<!-- nwt-example: 17 -->

**Write and decode.** `record 17` writes the `symbol-map-native` vector (80 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 17 work/type-17-python.bin
python3 examples/python/nwt_example.py decode-record work/type-17-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 17 work/type-17-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-17-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 17 work/type-17-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-17-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 17 work/type-17-cpp.bin
work/nwt-cpp decode-record work/type-17-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `symbol-map-native` | `fixtures/golden/records/012-symbol-map-native.bin` | Native symbol with an open-ended interval (`valid_to_ns` null). |
| `symbol-map-closed-isin` | `fixtures/golden/records/013-symbol-map-closed-isin.bin` | ISIN with a closed interval. |
| `symbol-map-root` | `fixtures/golden/records/014-symbol-map-root.bin` | Root symbol (symbology 5) mapped to the option. The interval ends at the expiration. |

## TRADE_QUOTE

A TRADE_QUOTE record (type 18, 120 bytes) is one trade print together with the top of book immediately before it. A producer emits it when the source publishes trades with the prevailing quote. It is a derived sampling record with no correction or cancellation lifecycle.

[Field reference](FIELD-REFERENCE.md#trade_quote) · [Specification](SPECIFICATION.md#trade_quote)

- The presence rules of the quote sides match QUOTE.
- It does not initialize or replace QUOTE state.
- TRADE and TRADE_QUOTE are never emitted for the same prints on one channel.
- `trade_id` is 0 when the source gives no trade identifier.

**Example.**

<!-- nwt-example: 18 -->

**Write and decode.** `record 18` writes the `trade-quote` vector (120 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 18 work/type-18-python.bin
python3 examples/python/nwt_example.py decode-record work/type-18-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 18 work/type-18-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-18-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 18 work/type-18-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-18-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 18 work/type-18-cpp.bin
work/nwt-cpp decode-record work/type-18-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `trade-quote` | `fixtures/golden/records/037-trade-quote.bin` | Buyer-aggressor trade at the ask, with a two-sided top of book. |
| `trade-quote-one-sided` | `fixtures/golden/records/038-trade-quote-one-sided.bin` | Absent bid side, unknown ask order count, `trade_id` 0, seller aggressor and the off-book condition. |

## BEST_QUOTE

A BEST_QUOTE record (type 19, 112 bytes) is the best bid and offer across venues, with the venue that set each side. The producer of a consolidated feed emits it on every change, or once per sampling interval. It keeps its own state and does not replace QUOTE state.

[Field reference](FIELD-REFERENCE.md#best_quote) · [Specification](SPECIFICATION.md#best_quote)

- The presence rules match QUOTE.
- A nonzero `bid_publisher_id` or `ask_publisher_id` is a declared publisher; 0 means the side is absent or the venue is unknown.
- `interval_ns` 0 marks an event-driven quote. With `interval_ns` greater than 0, `ts_event` equals the interval end.
- A GAP invalidates this state; the next BEST_QUOTE restores it.

**Example.**

<!-- nwt-example: 19 -->

**Write and decode.** `record 19` writes the `best-quote-event` vector (112 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 19 work/type-19-python.bin
python3 examples/python/nwt_example.py decode-record work/type-19-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 19 work/type-19-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-19-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 19 work/type-19-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-19-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 19 work/type-19-cpp.bin
work/nwt-cpp decode-record work/type-19-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `best-quote-event` | `fixtures/golden/records/039-best-quote-event.bin` | Event-driven quote (`interval_ns` 0) with a different venue on each side. |
| `best-quote-sampled` | `fixtures/golden/records/040-best-quote-sampled.bin` | Quote sampled once per second: `ts_event` at the interval end, an absent ask with `ask_publisher_id` 0, and the indicative flag. |

## FRAME_SUMMARY

A FRAME_SUMMARY record (type 20, 104 bytes) summarizes one DATA frame: its offset, stored size, codec, the record types it contains and its range of instrument IDs. A writer that follows the store profile emits one record per DATA frame, so a reader can skip frames by type and instrument without reading them. The manifest declares this type with `required` false, so a reader that does not use summaries skips the records.

[Field reference](FIELD-REFERENCE.md#frame_summary) · [Specification](SPECIFICATION.md#frame_summary)

- Publisher, channel and instrument are 0, and both timestamps are null.
- The records fill trailing DATA frames that contain nothing else, and describe every other DATA frame exactly once.
- Bit n (1–63) of `type_mask` is set when standard type n is present in the frame; bit 0 is set when any other type is present.
- A validator checks every value against a full scan. A summary that disagrees with its frame is an error.

[Store profile](STORE.md) describes files that carry these records, and [State and recovery](STATE-AND-RECOVERY.md) explains what a selective read can and cannot conclude.

**Example.**

<!-- nwt-example: 20 -->

**Write and decode.** `record 20` writes the `frame-summary` vector (104 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 20 work/type-20-python.bin
python3 examples/python/nwt_example.py decode-record work/type-20-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 20 work/type-20-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-20-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 20 work/type-20-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-20-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 20 work/type-20-cpp.bin
work/nwt-cpp decode-record work/type-20-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `frame-summary` | `fixtures/golden/records/048-frame-summary.bin` | Summary of DATA frame 0 of the conformance file: offset 2,272, 480 stored bytes, raw codec, `type_mask` bits 6 and 10 (INSTRUMENT_DEF and VENUE_DEF), instrument IDs 2001–2002. A standalone vector: `write-golden` does not put it into the conformance file. |

## SECURITY_DEF

A SECURITY_DEF record (type 21, 216 bytes plus text) is the security-master record of one listing of one security: identifiers such as ISIN, CUSIP, FIGI, LEI and CFI, classification codes, countries, currencies, shares outstanding and key dates, in 30 texts and a block of numeric fields. A producer of reference data emits it when the facts of a listing are published or change. It is a reference record.

[Field reference](FIELD-REFERENCE.md#security_def) · [Specification](SPECIFICATION.md#security_def)

- Identity is `(publisher, instrument)`, the listing. A later record replaces the earlier one.
- `shares_outstanding` is a whole share count, not scaled by 10⁹.
- `security_type`, `structure`, `listing_status` and `voting` are short producer-defined codes. Their meaning is an agreement between the producer and its consumers.
- `ts_event` is the time the facts became effective.

**Example.**

<!-- nwt-example: 21 -->

**Write and decode.** `record 21` writes the `security-def-full` vector (440 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 21 work/type-21-python.bin
python3 examples/python/nwt_example.py decode-record work/type-21-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 21 work/type-21-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-21-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 21 work/type-21-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-21-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 21 work/type-21-cpp.bin
work/nwt-cpp decode-record work/type-21-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `security-def-full` | `fixtures/golden/records/043-security-def-full.bin` | All 30 texts filled, with identifiers, dates, share count, lot size and par value; main listing, multi-currency flag, null `delisting_ns`. |
| `security-def-minimal` | `fixtures/golden/records/044-security-def-minimal.bin` | The smallest valid record: every text empty, every nullable field null, every producer identifier 0. |

## CORPORATE_ACTION

A CORPORATE_ACTION record (type 22, 184 bytes plus text) is one corporate-action event for one listing: dates, ratios, identifiers, short codes, and a `details` text that holds the event-specific terms as one JSON object with sorted keys. A producer of reference data emits it when an event is announced or its record changes. It is a reference record.

[Field reference](FIELD-REFERENCE.md#corporate_action) · [Specification](SPECIFICATION.md#corporate_action)

- Identity is `(publisher, unique_id)`. A later record with the same `unique_id` replaces the earlier one.
- `event`, `subtype`, `action`, `status`, `participation`, `payment_type` and `fraction` are short producer-defined codes.
- A ratio is two fields: for a 4-for-1 split, `ratio_old` is 1 and `ratio_new` is 4.
- The fixed fields can be interpreted without `details`.
- Listing facts such as the issuer name and the symbols are not repeated here. A SECURITY_DEF for the same instrument carries them.

**Example.**

<!-- nwt-example: 22 -->

**Write and decode.** `record 22` writes the `corporate-action-dividend` vector (288 bytes), and `decode-record` prints its fields.

<!-- nwt-tabs -->
<!-- nwt-title: Python -->
```bash
python3 examples/python/nwt_example.py record 22 work/type-22-python.bin
python3 examples/python/nwt_example.py decode-record work/type-22-python.bin
```
<!-- nwt-title: Rust -->
```bash
examples/rust/target/debug/nwt-example record 22 work/type-22-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-22-rust.bin
```
<!-- nwt-title: C# -->
```bash
dotnet work/csharp/NwtExample.dll record 22 work/type-22-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-22-csharp.bin
```
<!-- nwt-title: C++ -->
```bash
work/nwt-cpp record 22 work/type-22-cpp.bin
work/nwt-cpp decode-record work/type-22-cpp.bin
```
<!-- /nwt-tabs -->

**Conformance vectors.**

| Scenario | File | Exercises |
|---|---|---|
| `corporate-action-dividend` | `fixtures/golden/records/045-corporate-action-dividend.bin` | Cash dividend with ex, record and payment dates, null ratios, the default-option flag and a `details` JSON object with sorted keys. |
| `corporate-action-split` | `fixtures/golden/records/046-corporate-action-split.bin` | 4-for-1 split: `ratio_old` 1, `ratio_new` 4, an outturn security with its ISIN, a related event and an empty `details`. |
| `corporate-action-minimal` | `fixtures/golden/records/047-corporate-action-minimal.bin` | Only the required texts `event`, `event_id` and `unique_id`. Every date and ratio is null; `option_id` and `serial_id` are unknown (`UINT32_MAX`). |
