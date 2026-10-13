# NWT feed cookbook — all 22 types, all four languages

Use the [quick start](IMPLEMENTATION-GUIDE.md) to build the programs once. Each section below covers one record type: what it is for, the rules to remember, a worked example, and the commands that write and decode it in all four languages. The layouts, offsets and limits are in the [field reference](FIELD-REFERENCE.md); the normative rules are in the [specification](SPECIFICATION.md).

## About the examples

- **Real example.** Where a real source exists, the worked example is the first record of that type read from a real fixture under `fixtures/real/`, `fixtures/real-market/` or `fixtures/real-reference/`. These fixtures are converted from public symbol-directory and market-identifier files and from licensed data exports; see [REAL-DATA.md](REAL-DATA.md) and [REAL-DATA-MARKET.md](REAL-DATA-MARKET.md) for their sources and terms before you redistribute them.
- **Synthetic example.** Six types never have a real source: STATUS, GAP, SYSTEM, OPTION_ANALYTICS, IMBALANCE and FRAME_SUMMARY. Any other type also gets a synthetic example when its real fixture file is not present in the kit. For them the example is a catalog scenario, made up for testing and labelled as synthetic. The synthetic catalogs (`fixtures/catalog.json`, `fixtures/catalog-v1.1.json`) and the files in `fixtures/v1.1/` exist so that the four codecs can be compared byte for byte. They are conformance vectors, not market data.
- The examples are produced by the build script from the fixtures at the time the documentation is built, so they always match the files in the kit.
- Every number in a JSON example is a decimal string, so no 64-bit value is rounded. Prices and quantities are the raw integers (× 10⁹). A null is `-9223372036854775808` for a signed field and `18446744073709551615` for an unsigned one.
- Each generated `.bin` file from the `record` command is one raw record. It needs the preceding definitions and state when it is interpreted semantically. The complete containers supply those prerequisites in order.

## How the types fit together

| Group | Types | Notes |
|---|---|---|
| Market data | 1 TRADE, 2 QUOTE, 3 BAR, 4 MBO, 5 BOOK_SNAPSHOT, 13 STATISTICS, 14 OPTION_ANALYTICS, 15 BOOK_DELTA, 16 IMBALANCE, 18 TRADE_QUOTE, 19 BEST_QUOTE | Market records. Each needs an INSTRUMENT_DEF for its instrument earlier in the file. |
| Instrument and reference data | 6 INSTRUMENT_DEF, 10 VENUE_DEF, 11 OPTION_DEF, 12 LISTING, 17 SYMBOL_MAP, 21 SECURITY_DEF, 22 CORPORATE_ACTION | Types 10–12, 17, 21 and 22 are reference records. They need no INSTRUMENT_DEF and do not replace one. |
| State and control | 7 STATUS, 8 GAP, 9 SYSTEM, 20 FRAME_SUMMARY | GAP invalidates book and status state. FRAME_SUMMARY is the index for selective reads. |

A typical file for one equity venue has a VENUE_DEF, an INSTRUMENT_DEF per symbol, then trades, quotes and bars. A reference-data file has LISTING, SYMBOL_MAP, SECURITY_DEF and CORPORATE_ACTION records, and no market data.

## 1. TRADE — Trades

A trade print with a lifecycle. NEW introduces a trade, CORRECT replaces its price, size, aggressor and conditions, and CANCEL ends it. CORRECT and CANCEL name the trade by `trade_id` and point `original_sequence` at the NEW record, never at an earlier correction.

Rules to remember:

- NEW needs a non-null price, a positive quantity, a nonzero `trade_id` and `original_sequence` 0.
- CANCEL carries a null price, a null quantity, aggressor 0 and conditions 0.
- A canceled trade cannot be corrected again.
- A trade does not change an order-level book. The venue must send the matching MODIFY or DELETE.

### Worked example

<!-- nwt-example: 1 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 1` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 1 work/type-1-python.bin
python3 examples/python/nwt_example.py decode-record work/type-1-python.bin

examples/rust/target/debug/nwt-example record 1 work/type-1-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-1-rust.bin

dotnet work/csharp/NwtExample.dll record 1 work/type-1-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-1-csharp.bin

work/nwt-cpp record 1 work/type-1-cpp.bin
work/nwt-cpp decode-record work/type-1-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 2 | trade-new | [`fixtures/records/002-trade-new.bin`](../fixtures/records/002-trade-new.bin) |
| 3 | trade-correct | [`fixtures/records/003-trade-correct.bin`](../fixtures/records/003-trade-correct.bin) |
| 4 | trade-cancel | [`fixtures/records/004-trade-cancel.bin`](../fixtures/records/004-trade-cancel.bin) |
| 5 | trade-negative-price | [`fixtures/records/005-trade-negative-price.bin`](../fixtures/records/005-trade-negative-price.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 2. QUOTE — Best bid and ask

The best bid and best ask, replaced as a whole. An empty quote is valid and clears both sides.

Rules to remember:

- An absent side has a null price, quantity 0 and count 0. A present side has a non-null price and a positive quantity; its count is positive or `UINT32_MAX` (unknown).
- Crossed and locked quotes are valid. Do not reject them because bid ≥ ask.
- A quote does not clear MBO or aggregate-depth state.

### Worked example

<!-- nwt-example: 2 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 2` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 2 work/type-2-python.bin
python3 examples/python/nwt_example.py decode-record work/type-2-python.bin

examples/rust/target/debug/nwt-example record 2 work/type-2-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-2-rust.bin

dotnet work/csharp/NwtExample.dll record 2 work/type-2-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-2-csharp.bin

work/nwt-cpp record 2 work/type-2-cpp.bin
work/nwt-cpp decode-record work/type-2-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 6 | quote-two-sided | [`fixtures/records/006-quote-two-sided.bin`](../fixtures/records/006-quote-two-sided.bin) |
| 7 | quote-one-sided | [`fixtures/records/007-quote-one-sided.bin`](../fixtures/records/007-quote-one-sided.bin) |
| 8 | quote-empty | [`fixtures/records/008-quote-empty.bin`](../fixtures/records/008-quote-empty.bin) |
| 9 | quote-crossed | [`fixtures/records/009-quote-crossed.bin`](../fixtures/records/009-quote-crossed.bin) |
| 33 | quote-recovery | [`fixtures/records/033-quote-recovery.bin`](../fixtures/records/033-quote-recovery.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 3. BAR — Completed OHLCV bars

One completed time bucket built from trades, over a half-open interval `[start, end)`. `ts_event` equals the interval end, so timestamp order can differ from arrival order.

Rules to remember:

- A nonempty bar has non-null open, high, low and close with `low ≤ open, close ≤ high`, a positive volume and a positive trade count.
- An empty bar has the empty flag, four null prices, volume 0 and count 0. Empty bars are never forward-filled.
- Each `(publisher, channel, instrument, start, end)` appears at most once in a container.

### Worked example

<!-- nwt-example: 3 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 3` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 3 work/type-3-python.bin
python3 examples/python/nwt_example.py decode-record work/type-3-python.bin

examples/rust/target/debug/nwt-example record 3 work/type-3-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-3-rust.bin

dotnet work/csharp/NwtExample.dll record 3 work/type-3-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-3-csharp.bin

work/nwt-cpp record 3 work/type-3-cpp.bin
work/nwt-cpp decode-record work/type-3-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 10 | bar-complete | [`fixtures/records/010-bar-complete.bin`](../fixtures/records/010-bar-complete.bin) |
| 11 | bar-empty | [`fixtures/records/011-bar-empty.bin`](../fixtures/records/011-bar-empty.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 4. MBO — Market by order

Order-level book changes. Quantity is the absolute remaining size, never a delta. The six actions are ADD, MODIFY, DELETE, CLEAR, SNAPSHOT_BEGIN and SNAPSHOT_END.

Rules to remember:

- A book is valid only after CLEAR or a completed snapshot. ADD alone does not prove a complete book.
- A snapshot is built privately between SNAPSHOT_BEGIN and SNAPSHOT_END and may cross DATA frames.
- MODIFY replaces price, size and priority and must keep the side. Changing side is DELETE then ADD.
- DELETE, CLEAR and the snapshot markers carry a null price, quantity 0 and a null priority.

### Worked example

<!-- nwt-example: 4 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 4` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 4 work/type-4-python.bin
python3 examples/python/nwt_example.py decode-record work/type-4-python.bin

examples/rust/target/debug/nwt-example record 4 work/type-4-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-4-rust.bin

dotnet work/csharp/NwtExample.dll record 4 work/type-4-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-4-csharp.bin

work/nwt-cpp record 4 work/type-4-cpp.bin
work/nwt-cpp decode-record work/type-4-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 12 | mbo-clear | [`fixtures/records/012-mbo-clear.bin`](../fixtures/records/012-mbo-clear.bin) |
| 13 | mbo-add | [`fixtures/records/013-mbo-add.bin`](../fixtures/records/013-mbo-add.bin) |
| 14 | mbo-modify | [`fixtures/records/014-mbo-modify.bin`](../fixtures/records/014-mbo-modify.bin) |
| 15 | mbo-delete | [`fixtures/records/015-mbo-delete.bin`](../fixtures/records/015-mbo-delete.bin) |
| 16 | mbo-snapshot-begin | [`fixtures/records/016-mbo-snapshot-begin.bin`](../fixtures/records/016-mbo-snapshot-begin.bin) |
| 17 | mbo-snapshot-bid | [`fixtures/records/017-mbo-snapshot-bid.bin`](../fixtures/records/017-mbo-snapshot-bid.bin) |
| 18 | mbo-snapshot-ask | [`fixtures/records/018-mbo-snapshot-ask.bin`](../fixtures/records/018-mbo-snapshot-ask.bin) |
| 19 | mbo-snapshot-end | [`fixtures/records/019-mbo-snapshot-end.bin`](../fixtures/records/019-mbo-snapshot-end.bin) |
| 35 | mbo-recovery-begin | [`fixtures/records/035-mbo-recovery-begin.bin`](../fixtures/records/035-mbo-recovery-begin.bin) |
| 36 | mbo-recovery-add | [`fixtures/records/036-mbo-recovery-add.bin`](../fixtures/records/036-mbo-recovery-add.bin) |
| 37 | mbo-recovery-end | [`fixtures/records/037-mbo-recovery-end.bin`](../fixtures/records/037-mbo-recovery-end.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 5. BOOK_SNAPSHOT — Aggregate depth snapshots

An atomic replacement of a ranked aggregate book with up to 1024 levels per side. Level `i` pairs the bid at rank `i` with the ask at rank `i`.

Rules to remember:

- Bids strictly decrease in price and asks strictly increase. An absent element must form a suffix of its side.
- The depth-limited flag means deeper prices may exist. Do not treat the book as the full exchange book.
- Zero levels is a valid empty book.
- A snapshot cannot rebuild individual orders or repair MBO state.

### Worked example

<!-- nwt-example: 5 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 5` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 5 work/type-5-python.bin
python3 examples/python/nwt_example.py decode-record work/type-5-python.bin

examples/rust/target/debug/nwt-example record 5 work/type-5-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-5-rust.bin

dotnet work/csharp/NwtExample.dll record 5 work/type-5-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-5-csharp.bin

work/nwt-cpp record 5 work/type-5-cpp.bin
work/nwt-cpp decode-record work/type-5-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 20 | book-two-levels | [`fixtures/records/020-book-two-levels.bin`](../fixtures/records/020-book-two-levels.bin) |
| 21 | book-empty | [`fixtures/records/021-book-empty.bin`](../fixtures/records/021-book-empty.bin) |
| 22 | book-depth-limited | [`fixtures/records/022-book-depth-limited.bin`](../fixtures/records/022-book-depth-limited.bin) |
| 34 | book-recovery | [`fixtures/records/034-book-recovery.bin`](../fixtures/records/034-book-recovery.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 6. INSTRUMENT_DEF — Instrument definitions

Reference data that every market record needs first. It gives the symbol, venue, currency, quantity unit, increments, multiplier, expiration, strike, underlying and one of eight asset classes.

Rules to remember:

- A definition precedes every market record for its instrument in byte order. A later definition replaces the earlier one for later records.
- Currency and quantity unit never change for an existing instrument ID.
- A fact the producer does not know is null or “unspecified”. Do not infer option rights from the symbol; use OPTION_DEF (type 11).

### Worked example

<!-- nwt-example: 6 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 6` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 6 work/type-6-python.bin
python3 examples/python/nwt_example.py decode-record work/type-6-python.bin

examples/rust/target/debug/nwt-example record 6 work/type-6-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-6-rust.bin

dotnet work/csharp/NwtExample.dll record 6 work/type-6-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-6-csharp.bin

work/nwt-cpp record 6 work/type-6-cpp.bin
work/nwt-cpp decode-record work/type-6-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 1 | definition-1 | [`fixtures/records/001-definition-1.bin`](../fixtures/records/001-definition-1.bin) |
| 43 | definition-0 | [`fixtures/records/043-definition-0.bin`](../fixtures/records/043-definition-0.bin) |
| 44 | definition-2 | [`fixtures/records/044-definition-2.bin`](../fixtures/records/044-definition-2.bin) |
| 45 | definition-3 | [`fixtures/records/045-definition-3.bin`](../fixtures/records/045-definition-3.bin) |
| 46 | definition-4 | [`fixtures/records/046-definition-4.bin`](../fixtures/records/046-definition-4.bin) |
| 47 | definition-5 | [`fixtures/records/047-definition-5.bin`](../fixtures/records/047-definition-5.bin) |
| 48 | definition-6 | [`fixtures/records/048-definition-6.bin`](../fixtures/records/048-definition-6.bin) |
| 49 | definition-7 | [`fixtures/records/049-definition-7.bin`](../fixtures/records/049-definition-7.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 7. STATUS — Trading status

Replacement trading status for one instrument and channel, with a reason. It does not clear books and does not forbid trades during a halt or auction.

Rules to remember:

- Six status values and five reasons are defined; any other value is invalid.
- A GAP invalidates status. A new STATUS record restores it.

### Worked example

<!-- nwt-example: 7 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 7` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 7 work/type-7-python.bin
python3 examples/python/nwt_example.py decode-record work/type-7-python.bin

examples/rust/target/debug/nwt-example record 7 work/type-7-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-7-rust.bin

dotnet work/csharp/NwtExample.dll record 7 work/type-7-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-7-csharp.bin

work/nwt-cpp record 7 work/type-7-cpp.bin
work/nwt-cpp decode-record work/type-7-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 23 | status-0 | [`fixtures/records/023-status-0.bin`](../fixtures/records/023-status-0.bin) |
| 24 | status-1 | [`fixtures/records/024-status-1.bin`](../fixtures/records/024-status-1.bin) |
| 25 | status-2 | [`fixtures/records/025-status-2.bin`](../fixtures/records/025-status-2.bin) |
| 26 | status-3 | [`fixtures/records/026-status-3.bin`](../fixtures/records/026-status-3.bin) |
| 27 | status-4 | [`fixtures/records/027-status-4.bin`](../fixtures/records/027-status-4.bin) |
| 28 | status-5 | [`fixtures/records/028-status-5.bin`](../fixtures/records/028-status-5.bin) |
| 38 | status-recovery | [`fixtures/records/038-status-recovery.bin`](../fixtures/records/038-status-recovery.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 8. GAP — Source gaps

A discontinuity in the upstream feed, not a missing NWT frame. It invalidates all book and status state for its publisher and channel.

Rules to remember:

- The source sequence bounds are inclusive. Both are null when unknown.
- `recovery_id` is nonzero and unique among GAP records in the container.
- Quote, depth, MBO and status each recover on their own record. Trade and bar completeness stays uncertain for the gap interval.

### Worked example

<!-- nwt-example: 8 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 8` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 8 work/type-8-python.bin
python3 examples/python/nwt_example.py decode-record work/type-8-python.bin

examples/rust/target/debug/nwt-example record 8 work/type-8-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-8-rust.bin

dotnet work/csharp/NwtExample.dll record 8 work/type-8-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-8-csharp.bin

work/nwt-cpp record 8 work/type-8-cpp.bin
work/nwt-cpp decode-record work/type-8-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 29 | gap-1 | [`fixtures/records/029-gap-1.bin`](../fixtures/records/029-gap-1.bin) |
| 30 | gap-2 | [`fixtures/records/030-gap-2.bin`](../fixtures/records/030-gap-2.bin) |
| 31 | gap-3 | [`fixtures/records/031-gap-3.bin`](../fixtures/records/031-gap-3.bin) |
| 32 | gap-4 | [`fixtures/records/032-gap-4.bin`](../fixtures/records/032-gap-4.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 9. SYSTEM — System and heartbeat

A heartbeat or a diagnostic message, with UTF-8 text of up to 4096 bytes. Diagnostics never trigger commands or state repair.

Rules to remember:

- Severity follows the code: heartbeat and info 0, warning 1, error 2.
- A heartbeat has no text and no related recovery ID.
- Text lengths count bytes, not characters.

### Worked example

<!-- nwt-example: 9 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 9` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 9 work/type-9-python.bin
python3 examples/python/nwt_example.py decode-record work/type-9-python.bin

examples/rust/target/debug/nwt-example record 9 work/type-9-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-9-rust.bin

dotnet work/csharp/NwtExample.dll record 9 work/type-9-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-9-csharp.bin

work/nwt-cpp record 9 work/type-9-cpp.bin
work/nwt-cpp decode-record work/type-9-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the draft.2 catalog, kept unchanged. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 39 | system-1 | [`fixtures/records/039-system-1.bin`](../fixtures/records/039-system-1.bin) |
| 40 | system-2 | [`fixtures/records/040-system-2.bin`](../fixtures/records/040-system-2.bin) |
| 41 | system-3 | [`fixtures/records/041-system-3.bin`](../fixtures/records/041-system-3.bin) |
| 42 | system-4 | [`fixtures/records/042-system-4.bin`](../fixtures/records/042-system-4.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 10. VENUE_DEF — Venue definitions

A trading venue or one of its segments, identified by a market identifier code (MIC). It is a reference record: it has publisher ≠ 0 and instrument 0, and needs no INSTRUMENT_DEF.

Rules to remember:

- Identity is `(publisher, mic)`. A later record replaces the earlier one.
- `kind` 1 (operating) requires `mic` to equal `operating_mic`.
- MIC and country are uppercase ASCII letters or digits. Dates are midnight UTC of the source date.
- Nine texts, all counted in bytes; `name` is 1–255 bytes, `lei` is 0 or 20.

### Worked example

<!-- nwt-example: 10 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 10` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 10 work/type-10-python.bin
python3 examples/python/nwt_example.py decode-record work/type-10-python.bin

examples/rust/target/debug/nwt-example record 10 work/type-10-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-10-rust.bin

dotnet work/csharp/NwtExample.dll record 10 work/type-10-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-10-csharp.bin

work/nwt-cpp record 10 work/type-10-cpp.bin
work/nwt-cpp decode-record work/type-10-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 3 | venue-operating | [`fixtures/v1.1/records/003-venue-operating.bin`](../fixtures/v1.1/records/003-venue-operating.bin) |
| 4 | venue-segment-unicode | [`fixtures/v1.1/records/004-venue-segment-unicode.bin`](../fixtures/v1.1/records/004-venue-segment-unicode.bin) |
| 5 | venue-expired | [`fixtures/v1.1/records/005-venue-expired.bin`](../fixtures/v1.1/records/005-venue-expired.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 11. OPTION_DEF — Option contract terms

The terms of one option contract: underlying, expiration, strike, multiplier, right, exercise style, settlement and the root, underlying and OSI symbols. A producer that does not know a fact says “unknown”.

Rules to remember:

- Identity is `(publisher, instrument)`. A later record replaces the earlier one.
- `underlying_instrument_id` 0 requires a non-empty `underlying_symbol`.
- If an INSTRUMENT_DEF exists for the instrument, its asset class must be option and its expiration, strike and underlying must equal this record's.
- Never infer exercise style or settlement from the symbol.

### Worked example

<!-- nwt-example: 11 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 11` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 11 work/type-11-python.bin
python3 examples/python/nwt_example.py decode-record work/type-11-python.bin

examples/rust/target/debug/nwt-example record 11 work/type-11-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-11-rust.bin

dotnet work/csharp/NwtExample.dll record 11 work/type-11-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-11-csharp.bin

work/nwt-cpp record 11 work/type-11-cpp.bin
work/nwt-cpp decode-record work/type-11-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 10 | option-def-call | [`fixtures/v1.1/records/010-option-def-call.bin`](../fixtures/v1.1/records/010-option-def-call.bin) |
| 11 | option-def-unknowns | [`fixtures/v1.1/records/011-option-def-unknowns.bin`](../fixtures/v1.1/records/011-option-def-unknowns.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 12. LISTING — Listings

One row of a symbol directory: symbol, name, listing venue, round lot, ETF and test-issue flags, market tier and financial status. It is a reference record.

Rules to remember:

- Identity is `(publisher, instrument)`.
- `financial_flags` bits 1–3 (deficient, delinquent, bankrupt) require bit 0 (reported). Value 1 means normal; 0 means the source reports no financial status.
- The `ts_event` of a directory row is often null.

### Worked example

<!-- nwt-example: 12 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 12` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 12 work/type-12-python.bin
python3 examples/python/nwt_example.py decode-record work/type-12-python.bin

examples/rust/target/debug/nwt-example record 12 work/type-12-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-12-rust.bin

dotnet work/csharp/NwtExample.dll record 12 work/type-12-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-12-csharp.bin

work/nwt-cpp record 12 work/type-12-cpp.bin
work/nwt-cpp decode-record work/type-12-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 6 | listing-normal | [`fixtures/v1.1/records/006-listing-normal.bin`](../fixtures/v1.1/records/006-listing-normal.bin) |
| 7 | listing-etf-deficient | [`fixtures/v1.1/records/007-listing-etf-deficient.bin`](../fixtures/v1.1/records/007-listing-etf-deficient.bin) |
| 8 | listing-minimal | [`fixtures/v1.1/records/008-listing-minimal.bin`](../fixtures/v1.1/records/008-listing-minimal.bin) |
| 9 | listing-awkward-text | [`fixtures/v1.1/records/009-listing-awkward-text.bin`](../fixtures/v1.1/records/009-listing-awkward-text.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 13. STATISTICS — Statistics

One reference statistic for an instrument: open, high, low, close, settlement, VWAP, volume or open interest, with the session or date it refers to in `ts_ref`.

Rules to remember:

- `stat_type` 1–6 are price types and 7–8 are quantity types.
- SET of a price type needs a non-null price and a null quantity; SET of a quantity type needs the reverse.
- DELETE needs both null and flags 0.
- The latest SET per `(instrument, stat_type, ts_ref)` wins; DELETE withdraws it.

### Worked example

<!-- nwt-example: 13 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 13` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 13 work/type-13-python.bin
python3 examples/python/nwt_example.py decode-record work/type-13-python.bin

examples/rust/target/debug/nwt-example record 13 work/type-13-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-13-rust.bin

dotnet work/csharp/NwtExample.dll record 13 work/type-13-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-13-csharp.bin

work/nwt-cpp record 13 work/type-13-cpp.bin
work/nwt-cpp decode-record work/type-13-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 27 | stat-open | [`fixtures/v1.1/records/027-stat-open.bin`](../fixtures/v1.1/records/027-stat-open.bin) |
| 28 | stat-settlement-preliminary | [`fixtures/v1.1/records/028-stat-settlement-preliminary.bin`](../fixtures/v1.1/records/028-stat-settlement-preliminary.bin) |
| 29 | stat-volume | [`fixtures/v1.1/records/029-stat-volume.bin`](../fixtures/v1.1/records/029-stat-volume.bin) |
| 30 | stat-open-interest | [`fixtures/v1.1/records/030-stat-open-interest.bin`](../fixtures/v1.1/records/030-stat-open-interest.bin) |
| 31 | stat-delete | [`fixtures/v1.1/records/031-stat-delete.bin`](../fixtures/v1.1/records/031-stat-delete.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 14. OPTION_ANALYTICS — Option analytics

Implied volatility, delta, gamma, theta, vega, rho, the underlying price and a theoretical price for an option. Each value is a fixed-point integer, independently nullable.

Rules to remember:

- At least one of the six analytics is non-null.
- Non-null implied volatility and gamma are ≥ 0. Non-null delta lies in −1 … +1.
- No floating point on the wire. A producer rounds to nine decimals and the wire value is authoritative.
- Each record replaces the previous analytics of the instrument.

### Worked example

<!-- nwt-example: 14 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 14` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 14 work/type-14-python.bin
python3 examples/python/nwt_example.py decode-record work/type-14-python.bin

examples/rust/target/debug/nwt-example record 14 work/type-14-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-14-rust.bin

dotnet work/csharp/NwtExample.dll record 14 work/type-14-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-14-csharp.bin

work/nwt-cpp record 14 work/type-14-cpp.bin
work/nwt-cpp decode-record work/type-14-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 32 | analytics-full | [`fixtures/v1.1/records/032-analytics-full.bin`](../fixtures/v1.1/records/032-analytics-full.bin) |
| 33 | analytics-iv-only | [`fixtures/v1.1/records/033-analytics-iv-only.bin`](../fixtures/v1.1/records/033-analytics-iv-only.bin) |
| 34 | analytics-put-negative | [`fixtures/v1.1/records/034-analytics-put-negative.bin`](../fixtures/v1.1/records/034-analytics-put-negative.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 15. BOOK_DELTA — Book deltas

A change to the aggregate book that BOOK_SNAPSHOT replaces, one price level at a time. Levels are keyed by price, not by rank. `required` must be true.

Rules to remember:

- SET adds a level or replaces its size and count. DELETE removes a level. CLEAR empties one side, or the whole book when `side` is 0.
- The book is valid after a BOOK_SNAPSHOT or a CLEAR with side 0. A delta against an invalid book is an error. GAP invalidates the book.
- `LAST_IN_EVENT` marks the last delta of one source event.
- A side never grows beyond 1024 levels, so the state can always be sent again as one BOOK_SNAPSHOT.

### Worked example

<!-- nwt-example: 15 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 15` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 15 work/type-15-python.bin
python3 examples/python/nwt_example.py decode-record work/type-15-python.bin

examples/rust/target/debug/nwt-example record 15 work/type-15-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-15-rust.bin

dotnet work/csharp/NwtExample.dll record 15 work/type-15-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-15-csharp.bin

work/nwt-cpp record 15 work/type-15-cpp.bin
work/nwt-cpp decode-record work/type-15-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 20 | delta-set-bid | [`fixtures/v1.1/records/020-delta-set-bid.bin`](../fixtures/v1.1/records/020-delta-set-bid.bin) |
| 21 | delta-set-ask-last | [`fixtures/v1.1/records/021-delta-set-ask-last.bin`](../fixtures/v1.1/records/021-delta-set-ask-last.bin) |
| 22 | delta-delete | [`fixtures/v1.1/records/022-delta-delete.bin`](../fixtures/v1.1/records/022-delta-delete.bin) |
| 23 | delta-clear-side | [`fixtures/v1.1/records/023-delta-clear-side.bin`](../fixtures/v1.1/records/023-delta-clear-side.bin) |
| 24 | delta-clear-all | [`fixtures/v1.1/records/024-delta-clear-all.bin`](../fixtures/v1.1/records/024-delta-clear-all.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 16. IMBALANCE — Auction imbalance

An opening, closing or intraday auction imbalance with the reference, near and far prices. It is informational: it changes no book or status state.

Rules to remember:

- `imbalance_side` 0 requires `imbalance_quantity` 0, and the reverse.
- Each record replaces the previous imbalance of the instrument.

### Worked example

<!-- nwt-example: 16 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 16` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 16 work/type-16-python.bin
python3 examples/python/nwt_example.py decode-record work/type-16-python.bin

examples/rust/target/debug/nwt-example record 16 work/type-16-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-16-rust.bin

dotnet work/csharp/NwtExample.dll record 16 work/type-16-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-16-csharp.bin

work/nwt-cpp record 16 work/type-16-cpp.bin
work/nwt-cpp decode-record work/type-16-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 35 | imbalance-buy | [`fixtures/v1.1/records/035-imbalance-buy.bin`](../fixtures/v1.1/records/035-imbalance-buy.bin) |
| 36 | imbalance-none | [`fixtures/v1.1/records/036-imbalance-none.bin`](../fixtures/v1.1/records/036-imbalance-none.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 17. SYMBOL_MAP — Symbol maps

A symbol that names an instrument over a half-open time interval, in one of six symbologies: native, OSI, ISIN, FIGI, root, continuous.

Rules to remember:

- The header instrument is the mapped instrument.
- For symbologies 1–4 and 6, intervals for one `(publisher, symbology, symbol)` must not overlap: a symbol names one instrument at any time.
- Symbology 5 (root) is one-to-many. One instrument may have many symbols.
- `valid_to_ns` null means open-ended.

### Worked example

<!-- nwt-example: 17 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 17` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 17 work/type-17-python.bin
python3 examples/python/nwt_example.py decode-record work/type-17-python.bin

examples/rust/target/debug/nwt-example record 17 work/type-17-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-17-rust.bin

dotnet work/csharp/NwtExample.dll record 17 work/type-17-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-17-csharp.bin

work/nwt-cpp record 17 work/type-17-cpp.bin
work/nwt-cpp decode-record work/type-17-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 12 | symbol-map-native | [`fixtures/v1.1/records/012-symbol-map-native.bin`](../fixtures/v1.1/records/012-symbol-map-native.bin) |
| 13 | symbol-map-closed-isin | [`fixtures/v1.1/records/013-symbol-map-closed-isin.bin`](../fixtures/v1.1/records/013-symbol-map-closed-isin.bin) |
| 14 | symbol-map-root | [`fixtures/v1.1/records/014-symbol-map-root.bin`](../fixtures/v1.1/records/014-symbol-map-root.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 18. TRADE_QUOTE — Trade with top of book

One trade print together with the top of book immediately before it. It is a derived sampling record with no correction or cancel lifecycle.

Rules to remember:

- Quote-side presence rules match QUOTE.
- It does not initialise or replace QUOTE state.
- A producer must not emit TRADE and TRADE_QUOTE for the same prints on one channel.

### Worked example

<!-- nwt-example: 18 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 18` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 18 work/type-18-python.bin
python3 examples/python/nwt_example.py decode-record work/type-18-python.bin

examples/rust/target/debug/nwt-example record 18 work/type-18-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-18-rust.bin

dotnet work/csharp/NwtExample.dll record 18 work/type-18-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-18-csharp.bin

work/nwt-cpp record 18 work/type-18-cpp.bin
work/nwt-cpp decode-record work/type-18-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 37 | trade-quote | [`fixtures/v1.1/records/037-trade-quote.bin`](../fixtures/v1.1/records/037-trade-quote.bin) |
| 38 | trade-quote-one-sided | [`fixtures/v1.1/records/038-trade-quote-one-sided.bin`](../fixtures/v1.1/records/038-trade-quote-one-sided.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 19. BEST_QUOTE — Best quote with venues

The best bid and offer with the venue that set each side, optionally sampled at an interval. It keeps its own state and does not replace QUOTE state.

Rules to remember:

- Presence rules match QUOTE. A non-zero venue ID must be a declared publisher; 0 means the side is absent or the venue is unknown.
- With `interval_ns` > 0, `ts_event` equals the interval end.

### Worked example

<!-- nwt-example: 19 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 19` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 19 work/type-19-python.bin
python3 examples/python/nwt_example.py decode-record work/type-19-python.bin

examples/rust/target/debug/nwt-example record 19 work/type-19-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-19-rust.bin

dotnet work/csharp/NwtExample.dll record 19 work/type-19-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-19-csharp.bin

work/nwt-cpp record 19 work/type-19-cpp.bin
work/nwt-cpp decode-record work/type-19-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 39 | best-quote-event | [`fixtures/v1.1/records/039-best-quote-event.bin`](../fixtures/v1.1/records/039-best-quote-event.bin) |
| 40 | best-quote-sampled | [`fixtures/v1.1/records/040-best-quote-sampled.bin`](../fixtures/v1.1/records/040-best-quote-sampled.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 20. FRAME_SUMMARY — Frame summaries

A per-frame summary that lets a reader skip frames by type and instrument without reading them. It is an ordinary optional record, so a 1.0 reader skips it. `required` must be false.

Rules to remember:

- Publisher 0, channel 0, instrument 0, both timestamps null.
- The records fill trailing DATA frames that contain nothing else, and describe every other DATA frame exactly once.
- A validator checks every value against a full scan; a disagreeing summary is an error.
- `type_mask` bit n (1–63) is set when standard type n is present; bit 0 when any other type is present.

### Worked example

<!-- nwt-example: 20 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 20` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 20 work/type-20-python.bin
python3 examples/python/nwt_example.py decode-record work/type-20-python.bin

examples/rust/target/debug/nwt-example record 20 work/type-20-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-20-rust.bin

dotnet work/csharp/NwtExample.dll record 20 work/type-20-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-20-csharp.bin

work/nwt-cpp record 20 work/type-20-cpp.bin
work/nwt-cpp decode-record work/type-20-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 48 | frame-summary | [`fixtures/v1.1/records/048-frame-summary.bin`](../fixtures/v1.1/records/048-frame-summary.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 21. SECURITY_DEF — Security master

The security-master record of one listing of one security, with its identifiers (ISIN, CUSIP, FIGI, LEI, CFI and others), codes, countries, currencies, shares outstanding and key dates. 30 texts. It is a reference record.

Rules to remember:

- Identity is `(publisher, instrument)`, the listing. A later record replaces the earlier one.
- `shares_outstanding` is a whole share count, not scaled by 10⁹.
- `security_type`, `structure`, `listing_status` and `voting` are short producer-defined codes; systems that exchange them must agree on the code set.
- `ts_event` is when the facts became effective.

### Worked example

<!-- nwt-example: 21 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 21` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 21 work/type-21-python.bin
python3 examples/python/nwt_example.py decode-record work/type-21-python.bin

examples/rust/target/debug/nwt-example record 21 work/type-21-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-21-rust.bin

dotnet work/csharp/NwtExample.dll record 21 work/type-21-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-21-csharp.bin

work/nwt-cpp record 21 work/type-21-cpp.bin
work/nwt-cpp decode-record work/type-21-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 43 | security-def-full | [`fixtures/v1.1/records/043-security-def-full.bin`](../fixtures/v1.1/records/043-security-def-full.bin) |
| 44 | security-def-minimal | [`fixtures/v1.1/records/044-security-def-minimal.bin`](../fixtures/v1.1/records/044-security-def-minimal.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## 22. CORPORATE_ACTION — Corporate actions

One corporate-action event for one listing: dates, ratios, identifiers, short codes, and a `details` text that holds event-specific terms as one JSON object with sorted keys. It is a reference record.

Rules to remember:

- Identity is `(publisher, unique_id)`. A later record with the same `unique_id` replaces the earlier one.
- `event`, `subtype`, `action`, `status`, `participation`, `payment_type` and `fraction` are short producer-defined codes.
- A reader must not need `details` to interpret the fixed fields.
- Listing facts such as the issuer name and symbols are not repeated here; a SECURITY_DEF for the same instrument carries them.

### Worked example

<!-- nwt-example: 22 -->

### Write and decode this type in each language

Run from the developer-kit root, after the builds in the implementation guide. `record 22` writes the first catalog example of this type as one raw record; `decode-record` prints every field. Rust is written to the same contract but was not compiled or run in this release.

```sh
python3 examples/python/nwt_example.py record 22 work/type-22-python.bin
python3 examples/python/nwt_example.py decode-record work/type-22-python.bin

examples/rust/target/debug/nwt-example record 22 work/type-22-rust.bin
examples/rust/target/debug/nwt-example decode-record work/type-22-rust.bin

dotnet work/csharp/NwtExample.dll record 22 work/type-22-csharp.bin
dotnet work/csharp/NwtExample.dll decode-record work/type-22-csharp.bin

work/nwt-cpp record 22 work/type-22-cpp.bin
work/nwt-cpp decode-record work/type-22-cpp.bin
```

### Conformance vectors (synthetic)

These are scenarios of the 1.1 catalog. They test edge cases; they are not market data.

| No. | Scenario | Binary fixture |
|---:|---|---|
| 45 | corporate-action-dividend | [`fixtures/v1.1/records/045-corporate-action-dividend.bin`](../fixtures/v1.1/records/045-corporate-action-dividend.bin) |
| 46 | corporate-action-split | [`fixtures/v1.1/records/046-corporate-action-split.bin`](../fixtures/v1.1/records/046-corporate-action-split.bin) |
| 47 | corporate-action-minimal | [`fixtures/v1.1/records/047-corporate-action-minimal.bin`](../fixtures/v1.1/records/047-corporate-action-minimal.bin) |

To inspect any variant with any language, give its path to `decode-record`. The four decoders produce matching field reports, including all reserved and length fields.

## Export and benchmark commands

These commands work on any valid container, including the real fixtures. The examples use the 22-type conformance container because it is always present. `--pretty` writes decimal prices and quantities with nine fractional digits and ISO-8601 nanosecond timestamps; without it every value is the raw integer string. The exact text formats are in `fixtures/v1.1/FORMAT-NOTES.md`.

```sh
# Python
python3 examples/python/nwt_example.py to-json fixtures/v1.1/all-records.nwt --pretty
python3 examples/python/nwt_example.py to-csv fixtures/v1.1/all-records.nwt 12
python3 examples/python/nwt_example.py write-v11 work/python-v11.zst.nwt --zstd
python3 examples/python/nwt_example.py bench work/python-v11.zst.nwt

# Rust (not compiled or run in this release)
examples/rust/target/debug/nwt-example to-json fixtures/v1.1/all-records.nwt --pretty
examples/rust/target/debug/nwt-example to-csv fixtures/v1.1/all-records.nwt 12

# C#
dotnet work/csharp/NwtExample.dll to-json fixtures/v1.1/all-records.nwt --pretty
dotnet work/csharp/NwtExample.dll to-csv fixtures/v1.1/all-records.nwt 12

# C++
work/nwt-cpp to-json fixtures/v1.1/all-records.nwt --pretty
work/nwt-cpp to-csv fixtures/v1.1/all-records.nwt 12
```

`to-csv` writes one record type per output and refuses type 5, which has levels; use `to-json` for it. Zstd output is not byte-identical across library versions, so compare decoded reports, not compressed bytes.

## Store, query and convert

The `nwt` Python tool converts source files, repacks a file as a store file (large frames, Zstd, an INDEX and FRAME_SUMMARY records), and answers time, type and instrument queries by reading only the frames it needs. See [TOOLS.md](TOOLS.md) and [STORE.md](STORE.md).
