# Market data samples

The market data samples are ten NWT files built from exchange market-data exports in CSV: an order-level book, top of book, ten-level depth, one-minute bars, instrument definitions and statistics. They hold eleven record types: `TRADE`, `QUOTE`, `BAR`, `MBO`, `BOOK_SNAPSHOT`, `INSTRUMENT_DEF`, `OPTION_DEF`, `STATISTICS`, `BOOK_DELTA`, `TRADE_QUOTE` and `BEST_QUOTE`. Use them to test a reader against real values, to see how each source column becomes an NWT field, and as a model for converting your own exports with `tools/nwt_convert_market.py`. Venues, listings, the security master and corporate actions are covered in [Reference data samples](REAL-DATA.md).

## Samples

Each sample is an `.nwt` file. Where a `.jsonl` file is listed, it is the JSON Lines view of the same sample: one JSON object per record, in file order. In every sample, the definition of an instrument precedes its first record.

| File | Record types | Contents |
|---|---|---|
| [equity-definitions.nwt](files/samples/equity-definitions.nwt)<br>[equity-definitions.jsonl](files/samples/equity-definitions.jsonl) | `INSTRUMENT_DEF` | 200 instrument definitions of one equities venue |
| [equity-orders.nwt](files/samples/equity-orders.nwt)<br>[equity-orders.jsonl](files/samples/equity-orders.jsonl) | `INSTRUMENT_DEF`, `MBO`, `TRADE` | The first 2,000 order-level rows of one equity on 16 September 2025: 1,818 `MBO` records (1 CLEAR, 1,420 ADD, 39 MODIFY, 358 DELETE) and 123 `TRADE` records |
| [equity-deltas.nwt](files/samples/equity-deltas.nwt)<br>[equity-deltas.jsonl](files/samples/equity-deltas.jsonl) | `INSTRUMENT_DEF`, `BOOK_DELTA` | Price-level changes derived from the same 2,000 rows: 1,818 `BOOK_DELTA` records (1 CLEAR, 1,599 SET, 218 DELETE) |
| [equity-quotes.nwt](files/samples/equity-quotes.nwt)<br>[equity-quotes.jsonl](files/samples/equity-quotes.jsonl) | `INSTRUMENT_DEF`, `QUOTE`, `TRADE_QUOTE` | The first 2,000 top-of-book rows of the same equity and day: 2,000 `QUOTE` and 476 `TRADE_QUOTE` records |
| [equity-bars.nwt](files/samples/equity-bars.nwt)<br>[equity-bars.jsonl](files/samples/equity-bars.jsonl) | `INSTRUMENT_DEF`, `BAR` | The 921 one-minute bars of the same equity and day |
| [futures-orders.nwt](files/samples/futures-orders.nwt)<br>[futures-orders.jsonl](files/samples/futures-orders.jsonl) | `INSTRUMENT_DEF`, `MBO` | The order book of one futures contract at the start of a session: 2,000 `MBO` records (1 CLEAR, 1,999 ADD) |
| [option-definitions.nwt](files/samples/option-definitions.nwt)<br>[option-definitions.jsonl](files/samples/option-definitions.jsonl) | `INSTRUMENT_DEF`, `OPTION_DEF` | 500 definitions from a consolidated options feed: 130 underlying equities and 370 options, each option with an `OPTION_DEF` |
| [option-best-quotes.nwt](files/samples/option-best-quotes.nwt)<br>[option-best-quotes.jsonl](files/samples/option-best-quotes.jsonl) | `INSTRUMENT_DEF`, `OPTION_DEF`, `BEST_QUOTE` | 2,000 consolidated best quotes of options, with the venue of each side, and 641 `INSTRUMENT_DEF` and 641 `OPTION_DEF` records |
| [depth-10.nwt](files/samples/depth-10.nwt)<br>[depth-10.jsonl](files/samples/depth-10.jsonl) | `INSTRUMENT_DEF`, `OPTION_DEF`, `BOOK_SNAPSHOT` | 500 book snapshots of 1 to 10 levels for options on futures, with 199 `INSTRUMENT_DEF` and 187 `OPTION_DEF` records |
| [statistics.nwt](files/samples/statistics.nwt)<br>[statistics.jsonl](files/samples/statistics.jsonl) | `INSTRUMENT_DEF`, `OPTION_DEF`, `STATISTICS` | 1,831 statistics of one derivatives venue: 1,809 opening prices and 22 preliminary settlement prices |

The first three records of `equity-quotes.jsonl` are the `INSTRUMENT_DEF`, a `QUOTE` with an absent bid side, and a `QUOTE` with both sides. Every integer is written as a decimal string. Prices and quantities are scaled by 10⁹, `-9223372036854775808` is the null price, and `18446744073709551615` is the null timestamp or quantity.

<!-- nwt-file: fixtures/real-market/equity-quotes.jsonl lines=1-3 -->

## Convert a file

The converter, `tools/nwt_convert_market.py`, is a Python script that uses only the standard library. This procedure builds the `equity-orders.nwt` and `equity-deltas.nwt` samples from the saved rows of an order-level export.

1. Open a terminal in the kit root.
2. Run the converter with a kind, a source file, an output file and the options:

   ```bash
   python3 tools/nwt_convert_market.py csv-mbo fixtures/real-market/source/xnas-itch_mbo_equities.csv equity-orders.nwt \
       --dataset REAL.XNAS.ITCH --definitions fixtures/real-market/source/xnas-itch_definition_equities.csv \
       --currency USD --quantity-unit share --emit-deltas equity-deltas.nwt
   ```

   The converter writes both files and prints the provenance it stored in `equity-orders.nwt`, as JSON. The record counts are under `records_written`, and the provenance of `equity-deltas.nwt` is under `deltas`:

   ```text
     "records_written": {
       "INSTRUMENT_DEF": 1,
       "MBO": 1818,
       "TRADE": 123
     },
   ```
3. Check the file with the `nwt` command:

   ```bash
   python3 tools/nwt.py inspect equity-orders.nwt
   ```

   The last lines of the output confirm a complete file with 1,942 records:

   ```text
   end data_frames=1 records=1942 status=normal
   records TRADE 123
   records MBO 1818
   records INSTRUMENT_DEF 1
   ```
4. Print the records as JSON Lines. Add `--pretty` for decimal prices and ISO 8601 timestamps.

   ```bash
   python3 examples/python/nwt_example.py to-json equity-orders.nwt
   ```

The same converter runs through two other entry points, which take the same arguments:

```bash
python3 tools/nwt_convert.py KIND SRC OUT --dataset NAME [--option value | --flag] ...
```

```bash
python3 tools/nwt.py convert KIND SRC OUT --dataset NAME [--option value | --flag] ...
```

The other commands of `tools/nwt.py` are described in [The nwt command](TOOLS.md).

## Converter kinds

The first argument selects the kind of export.

| Kind | Input | Records written |
|---|---|---|
| `csv-definition` | Instrument definitions | `INSTRUMENT_DEF` for every row; `OPTION_DEF` after it for a call or a put |
| `csv-mbo` | Order-level book: one row per order event | `MBO` and `TRADE`; with `--emit-deltas`, a second file of `BOOK_DELTA` |
| `csv-mbp1` | Top of book: best bid and ask after every event | `QUOTE` for every row; `TRADE_QUOTE` for every trade row |
| `csv-mbp10` | Ten-level depth | `BOOK_SNAPSHOT` for every row |
| `csv-cmbp1` | Consolidated top of book across venues | `BEST_QUOTE` for every row |
| `csv-ohlcv` | One-minute bars | `BAR` for every row |
| `csv-statistics` | Statistics published by the venue | `STATISTICS` for every row that has a value |

Every kind except `csv-definition` also writes the `INSTRUMENT_DEF` of each instrument, and its `OPTION_DEF` where it has one, immediately before the first record of that instrument.

## Options

Options follow the output file, as `--name value`, `--name=value` or a bare `--flag`.

| Option | Applies to | Meaning |
|---|---|---|
| `--dataset NAME` | Every kind | Required. The dataset name in the manifest, for example `REAL.XNAS.ITCH`. |
| `--quantity-unit TEXT` | Every kind | Required. The unit of order sizes, for example `share` or `contract`. It becomes the `quantity_unit` of every `INSTRUMENT_DEF`; the exports have no such column. |
| `--definitions FILE` | Every kind except `csv-definition` | The definitions export of the same venue. The converter takes each instrument's definition from it. An instrument that is missing from the file stops the conversion. |
| `--currency TEXT` | Every kind | The currency of an instrument whose definition row has none. Required when `--definitions` is not given. |
| `--venue TEXT` | Every kind | The `venue` text of an `INSTRUMENT_DEF` whose definition row has none. |
| `--skip-undefined` | Every kind | Skips an instrument whose definition row has no currency and counts its rows in the provenance. Without the option, such an instrument stops the conversion. |
| `--trades FILE` | `csv-ohlcv` | Required. The top-of-book, order-level or consolidated export of the same venue and day, from which the converter counts the trades of each bar. |
| `--emit-deltas [FILE]` | `csv-mbo` | Also writes the derived `BOOK_DELTA` file. Without a file name, the name is the output name with `.nwt` replaced by `.deltas.nwt`. |
| `--fill-rule NAME` | `csv-mbo` | The rule for fill rows: `cancel-carries-fill` (the default) or `fill-reduces`. See [Fills and cancels](#fills-and-cancels). |
| `--max-rows N` | Every kind | Converts only the first N data rows. |

## Rules for every conversion

**Record header**

Every record takes its header fields from the source row.

| Source column | NWT field | Rule |
|---|---|---|
| `publisher_id` | `publisher_id` | Kept. 0 stops the conversion. |
| `instrument_id` | `instrument_id` | Kept. 0 stops the conversion. |
| `channel_id` | `channel_id` | Kept. 0 when the file has no such column. |
| `ts_event` | `ts_event` | UTC timestamp with up to nine fractional digits, stored as POSIX nanoseconds. |
| `ts_recv` | `ts_recv` | As `ts_event`. Null when the file has no such column. |

- `sequence` restarts at 1 for each pair of publisher and channel in each output file. The source sequence number is not carried.
- Every publisher ID that appears is declared in the manifest under the name `publisher-<id>` with an empty venue.

**Exact values**

- Prices, sizes and timestamps are parsed with integer arithmetic (`tools/nwt_parse.py`). No value passes through floating point.
- Nothing is rounded. A price or a size with more than nine decimal places stops the conversion, and the provenance states `values_rounded` as 0.
- The converter accepts a timestamp only in UTC, written with `Z` or `+00:00`. Any other offset stops the conversion.
- Text is copied exactly. A text longer or shorter than its field allows stops the conversion.
- An unknown code, a missing column, a repeated column name or a row with the wrong number of columns stops the conversion.

**Nulls**

- An empty price becomes the null price.
- An empty timestamp becomes the null timestamp.
- A book side with no price is an absent side: null price, quantity 0 and order count 0.

**Instrument definitions**

- A definition always precedes the first record of its instrument. It is written once for each pair of publisher and instrument, on the publisher and channel of that first record.
- With `--definitions`, the definition comes from the definitions export, by the mapping in [Instrument definitions](#instrument-definitions-instrument_def-and-option_def). When the export has several rows for one instrument, the last row is used.
- Without `--definitions`, the converter writes a minimal `INSTRUMENT_DEF`: the `symbol` of the row, `asset_class` 0, null increments, expiration and strike, null `ts_event` and `ts_recv`, and the currency, quantity unit and venue given as options.

**Rows and columns**

- Records keep the order of the source rows.
- A source column that is not in a mapping table of this page is not carried. This includes the source `flags`, the source sequence number and the capture-delay column `ts_in_delta`.
- A row that has no NWT form is skipped and counted in the provenance under `rows_skipped`, by reason. A row that is converted by a stated rule, such as a fill row, is counted under `notes`.

**Output**

- On any failure the converter prints a message that starts with `NWT error:`, exits with status 1 and writes no output file. A failure in a row names the source file and line: `NWT error: <file> line N: …`.
- The output is deterministic. The container `created_ns` is the constant 2026-10-13T00:00:00Z. The stream ID is the first 16 bytes of the SHA-256 of the kind, the output role (`main` or `deltas`) and the SHA-256 of the source rows read. The same rows and the same options give the same container bytes.
- Every container has a `PROVENANCE` element, described under [Provenance](#provenance).

## Instrument definitions: INSTRUMENT_DEF and OPTION_DEF

The kind `csv-definition` converts a definitions export on its own. The other kinds apply the same mapping to the rows of the `--definitions` file.

| Source column | NWT field | Rule |
|---|---|---|
| `raw_symbol` | `symbol` | Copied exactly. An empty symbol stops the conversion. |
| `instrument_class` | `asset_class` | `K` is 1 (equity), `F` is 2 (future), `C` and `P` are 3 (option). `B`, `I`, `M`, `S`, `T`, `X` and `Y` are 0 (unspecified). Any other letter stops the conversion. |
| `min_price_increment` | `price_increment` | Exact decimal. Empty becomes null. Zero or a negative value stops the conversion. |
| `expiration` | `expiration_ns` | UTC timestamp. Empty becomes null. |
| `underlying_id` | `underlying_instrument_id` | Kept. 0 means that the instrument has no underlying. |
| `strike_price` | `strike` | Exact decimal. Empty becomes null. |
| `exchange` | `venue` | Copied exactly. When empty, the value of `--venue`, or an empty text. |
| `currency` | `currency` | Copied exactly. When empty, the value of `--currency`. |
| `security_update_action` | None | `A` and `M` write a definition. A `D` row is skipped and counted. Any other letter stops the conversion. |

The converter sets the remaining fields:

- `quantity_unit` is the value of `--quantity-unit`.
- `quantity_increment` is null. The export has lot sizes, not a size increment.
- `contract_multiplier` is null. The export has a contract size in a unit of measure, which is not a price multiplier.

A call or a put also gets an `OPTION_DEF`, directly after its `INSTRUMENT_DEF`:

| Source column | NWT field | Rule |
|---|---|---|
| `instrument_class` | `right` | `C` is 1 (call), `P` is 2 (put). |
| `underlying_id` | `underlying_instrument_id` | The same value as in the `INSTRUMENT_DEF`. |
| `expiration` | `expiration_ns` | The same value as in the `INSTRUMENT_DEF`. An option row with no expiration stops the conversion. |
| `strike_price` | `strike` | The same value as in the `INSTRUMENT_DEF`. An option row with no strike stops the conversion. |
| `asset` | `root` | Copied exactly. When empty, the root of the OSI symbol. A row with neither stops the conversion. |
| `underlying` | `underlying_symbol` | Copied exactly. |
| `raw_symbol` | `osi_symbol` | Only when the symbol has the 21-character OSI layout. Otherwise empty. |
| `cfi` | `exercise_style` | For a six-letter code that starts with `O`: third letter `A` is 1 (American), `E` is 2 (European). Anything else is 0 (unknown). |
| `currency` | `currency` | The same value as in the `INSTRUMENT_DEF`. |

- `settlement`, `closing_type` and `option_flags` are 0, and `contract_multiplier` is null.
- Exercise style is never inferred from a symbol.
- An option row with neither an underlying ID nor an underlying symbol cannot form an `OPTION_DEF`. It gets its `INSTRUMENT_DEF` only, and the provenance counts it under `notes`.

An option from the `option-definitions.nwt` sample, as its `INSTRUMENT_DEF` and its `OPTION_DEF`:

<!-- nwt-file: fixtures/real-market/option-definitions.jsonl lines=2-3 -->

## Order-level book: MBO and TRADE

The kind `csv-mbo` reads an order-level export, in which every row is one event of one order. An `MBO` record carries the remaining size of an order, and the export carries size changes, so the converter tracks every live order of every book. A book is the set of orders of one publisher, channel and instrument.

| Source `action` | Records written | Rule |
|---|---|---|
| `R` | `MBO` CLEAR | Empties the book. |
| `A` | `MBO` ADD | The price and size of the row. An add for an order that is already in the book stops the conversion. |
| `C` | `MBO` MODIFY or DELETE | MODIFY with the remaining size, or DELETE when nothing remains. A cancel for an unknown order, or for more than the remaining size, stops the conversion. |
| `M` | `MBO` MODIFY | The price and size of the row. A change of side is written as DELETE and then ADD. A modify for an order that is not in the book is written as ADD and counted. |
| `T` | `TRADE` NEW | The price and size of the row. A trade row with no price or with size 0 is skipped and counted. |
| `F` | None, or `MBO` MODIFY or DELETE | Decided by the fill rule. See [Fills and cancels](#fills-and-cancels). |
| `N` | None | Skipped and counted as a row with no book effect. |

The other columns map as follows:

| Source column | NWT field | Rule |
|---|---|---|
| `order_id` | `order_id` | Kept. 0 on an order event stops the conversion. |
| `price` | `price` | Exact decimal. Null in a DELETE and a CLEAR. |
| `size` | `quantity` | In an `MBO`, the remaining size of the order after the event. In a `TRADE`, the traded size. |
| `side` | `side`, `aggressor` | In an `MBO`: `B` is 1 (bid), `A` is 2 (ask). In a `TRADE`, the aggressor: `B` is 1 (buyer), `A` is 2 (seller), `N` is 0 (unknown). |
| `flags` | None | Checked and not carried. The bit values 2, 8, 32 and 128 are allowed. Any other bit stops the conversion. |

- `priority` is null: the export gives no queue rank. `mbo_flags` is 0.
- `trade_id` counts 1, 2, 3 and so on for each book, in file order: the export has no trade identifier. `conditions` is 0.
- A book begins with a clear row. An add, a cancel or a modify before the first `R` row of its book stops the conversion.

### Derived price levels: BOOK_DELTA

`--emit-deltas` writes a second file of `BOOK_DELTA` records. They are derived: the export has no price-level rows, and the provenance of the file says so.

- After each order-level row is applied, every price whose aggregate changed gets one `BOOK_DELTA`: SET with the new aggregate size and order count, or DELETE when the level is empty.
- A clear row becomes CLEAR with `side` 0 and a null price.
- An order that moves to another price gives a delta for the old price and a delta for the new one.
- `LAST_IN_EVENT` (`delta_flags` bit 0) marks the last delta derived from each source row.
- A book with more than 1,024 price levels on one side stops the conversion: a `BOOK_DELTA` book holds at most 1,024 price levels on a side.
- The file has its own `INSTRUMENT_DEF` records and its own sequence numbers.

### Fills and cancels

An order-level export reports an execution against a resting order as up to three rows: a trade (`T`), a fill (`F`) that names the resting order, and a cancel (`C`) for the same order and size. `--fill-rule` states which row removes the size from the book.

| Fill rule | Fill row | Cancel row |
|---|---|---|
| `cancel-carries-fill` | Does not change the book. It is counted in the provenance. | Removes the filled size. |
| `fill-reduces` | Removes its size from the order, like a cancel. | Removes its own size as well. |

`cancel-carries-fill` is the default, and the samples are built with it. Choose `fill-reduces` for an export in which the cancel row does not repeat the size of the fill.

The first execution of the `equity-orders.nwt` sample shows the default rule. Source lines 18–20 are a sell of 180 at 177.03 against order 18315, which rested with 200:

| `action` | `side` | `price` | `size` | `order_id` |
|---|---|---:|---:|---:|
| `T` | `A` | 177.030000000 | 180 | 0 |
| `F` | `B` | 177.030000000 | 180 | 18315 |
| `C` | `B` | 177.030000000 | 180 | 18315 |

They become one `TRADE` (aggressor seller, quantity 180) and one `MBO` MODIFY that leaves order 18315 with 20:

<!-- nwt-file: fixtures/real-market/equity-orders.jsonl lines=18-19 -->

## Top of book: QUOTE and TRADE_QUOTE

The kind `csv-mbp1` reads a top-of-book export. Every row becomes a `QUOTE` with the book columns of the row. A trade row (`action` `T`) also becomes a `TRADE_QUOTE`, written after its `QUOTE`. On a trade row the book columns are the top of book at the trade.

| Source column | NWT field | Rule |
|---|---|---|
| `bid_px_00`, `ask_px_00` | `bid_price`, `ask_price` | Exact decimal. Empty means that the side is absent. |
| `bid_sz_00`, `ask_sz_00` | `bid_quantity`, `ask_quantity` | A present side with size 0, or a size on a side with no price, stops the conversion. |
| `bid_ct_00`, `ask_ct_00` | `bid_order_count`, `ask_order_count` | A count of 0 on a present side is written as a null count and counted in the provenance. |
| `price` | `price` | `TRADE_QUOTE` only. The trade price. |
| `size` | `quantity` | `TRADE_QUOTE` only. The traded size. |
| `side` | `aggressor` | `TRADE_QUOTE` only. `B` is 1 (buyer), `A` is 2 (seller), `N` is 0 (unknown). |

- `quote_flags` is 0. In a `TRADE_QUOTE`, `trade_id` is 0, because the export has no trade identifier, and `conditions` is 0.
- A trade row with no price or with size 0 gives its `QUOTE` and no `TRADE_QUOTE`. The provenance counts it.
- `TRADE` records from an order-level export and `TRADE_QUOTE` records from a top-of-book export describe the same trades. The converter writes them to different files.

The first `TRADE_QUOTE` of the `equity-quotes.nwt` sample is the same trade as in [Fills and cancels](#fills-and-cancels):

<!-- nwt-file: fixtures/real-market/equity-quotes.jsonl lines=10-10 -->

## Ten-level depth: BOOK_SNAPSHOT

The kind `csv-mbp10` reads a depth export. Every row becomes one `BOOK_SNAPSHOT` with `book_flags` 1 (depth-limited).

| Source column | NWT field | Rule |
|---|---|---|
| `bid_px_NN`, `ask_px_NN` | `bid_price`, `ask_price` of level NN | Exact decimal. Empty means that the side is absent at this level. |
| `bid_sz_NN`, `ask_sz_NN` | `bid_quantity`, `ask_quantity` | As for `QUOTE`. |
| `bid_ct_NN`, `ask_ct_NN` | `bid_count`, `ask_count` | As for `QUOTE`. |

- `NN` runs from `00`, the best level, to `09`. Each level pairs one bid and one ask.
- Trailing levels that are empty on both sides are dropped. A book with three bid levels and five ask levels gives five levels, with the bid absent in the last two.
- An empty level above a filled one stops the conversion. So do bid prices that do not strictly fall and ask prices that do not strictly rise.
- A trade row restates the book. The converter writes its snapshot and counts the row in the provenance. The trade itself is carried by `csv-mbo` and `csv-mbp1`.

A snapshot from the `depth-10.nwt` sample:

<!-- nwt-file: fixtures/real-market/depth-10.jsonl lines=3-3 -->

## Consolidated top of book: BEST_QUOTE

The kind `csv-cmbp1` reads a consolidated top-of-book export, in which each side of the best quote names the venue that set it. Every row becomes one `BEST_QUOTE`.

| Source column | NWT field | Rule |
|---|---|---|
| `bid_px_00`, `ask_px_00` | `bid_price`, `ask_price` | As for `QUOTE`. |
| `bid_sz_00`, `ask_sz_00` | `bid_quantity`, `ask_quantity` | As for `QUOTE`. |
| `bid_pb_00`, `ask_pb_00` | `bid_publisher_id`, `ask_publisher_id` | The venue ID of each side. 0 on an absent side. |

- Every venue ID that appears is declared in the manifest as a publisher.
- The export has no order counts: a present side has a null order count.
- `interval_ns` is 0, which marks an event-driven quote. `quote_flags` is 0.
- A trade row carries the publisher of the venue where the trade happened and restates the best quote under that publisher. The converter writes its `BEST_QUOTE` and counts the row in the provenance. The trade itself is not carried by this kind.

A `BEST_QUOTE` from the `option-best-quotes.nwt` sample:

<!-- nwt-file: fixtures/real-market/option-best-quotes.jsonl lines=3-3 -->

## One-minute bars: BAR

The kind `csv-ohlcv` reads a bars export. Every row becomes one `BAR`.

| Source column | NWT field | Rule |
|---|---|---|
| `ts_event` | `interval_start_ns` | The start of the minute. `interval_end_ns` is 60 seconds later, and the `ts_event` of the record is the end of the interval. A time that is not the start of a minute stops the conversion. |
| `open`, `high`, `low`, `close` | `open`, `high`, `low`, `close` | Exact decimals. |
| `volume` | `volume` | Exact decimal, above 0. |
| `rtype` | None | 33, which marks a one-minute bar. Any other value stops the conversion. |

The export has no trade count, and the converter never writes an invented one. It takes `trade_count` from the `--trades` file:

1. It counts the trade rows of the `--trades` file whose `ts_recv` falls in the minute of the bar, for the same publisher and instrument.
2. It sums the sizes of those rows and compares the sum with the `volume` of the bar.
3. When a bar has no matching trade rows, or the sum differs, the conversion stops and reports the source line of the bar.

`ts_recv` is null, because the export has no such column, and `bar_flags` is 0. A bar whose `low` is above its open or close, or whose `high` is below them, stops the conversion.

The first bars of the `equity-bars.nwt` sample:

<!-- nwt-file: fixtures/real-market/equity-bars.jsonl lines=2-3 -->

## Venue statistics: STATISTICS

The kind `csv-statistics` reads a statistics export. Every row that has a value becomes one `STATISTICS` record.

| Source `stat_type` | Source meaning | NWT `stat_type` |
|---:|---|---|
| 1 | Opening price | 1 (open) |
| 5 | Trading session high price | 2 (high) |
| 4 | Trading session low price | 3 (low) |
| 11 | Close price | 4 (close) |
| 3 | Settlement price | 5 (settlement) |
| 6 | Cleared volume | 7 (volume) |
| 9 | Open interest | 8 (open interest) |

Any other `stat_type` stops the conversion. The other columns map as follows:

| Source column | NWT field | Rule |
|---|---|---|
| `price` | `price` | The value of a price type (NWT types 1–5). The quantity is null. |
| `quantity` | `quantity` | The value of a quantity type (NWT types 7 and 8). The price is null. The export writes "no quantity" as 9223372036854775807, which becomes null. |
| `update_action` | `action` | 1 is SET, 2 is DELETE. A DELETE has a null price and a null quantity. |
| `ts_ref` | `ts_ref` | UTC timestamp. Empty becomes null. |
| `stat_flags` | `stat_flags` | See the rules below. |

- A row with `update_action` 1 and no value is skipped and counted.
- A row that carries a value in the column of the other kind stops the conversion.
- On a settlement price, source `stat_flags` 1 marks a final settlement. NWT marks the opposite case: bit 0 of `stat_flags` means preliminary. A settlement price with source flag 1 is written with `stat_flags` 0, and a settlement price with source flag 0 is written with `stat_flags` 1.
- Any other source flag value, or a flag on another type, stops the conversion.

A statistic from the `statistics.nwt` sample:

<!-- nwt-file: fixtures/real-market/statistics.jsonl lines=2-2 -->

## Provenance

Every container has a `PROVENANCE` element: a JSON object that records what was converted and by which rules. The converter prints the same object when it finishes. With `--emit-deltas`, the printed object also holds the provenance of the second file under `deltas`.

| Key | Content |
|---|---|
| `source_schema` | The kind of export: `definition`, `mbo`, `mbp-1`, `mbp-10`, `cmbp-1`, `ohlcv-1m` or `statistics` |
| `source_sha256`, `source_rows` | The SHA-256 and the number of the source rows read |
| `definitions_sha256` | The SHA-256 of the `--definitions` file, when one is given |
| `trades_sha256` | The SHA-256 of the `--trades` file, for `csv-ohlcv` |
| `output` | `main`, or `deltas` for the file written by `--emit-deltas` |
| `policy_options` | The options that decide what is written, as given on the command line |
| `conversion_policy` | The rules applied, as text |
| `records_written` | The number of records, by record type |
| `rows_skipped` | The number of rows left out, by reason |
| `notes` | The number of rows converted by a stated rule, by rule |
| `values_rounded` | Always 0 |

The object also holds `source_format`, `converter` and `license_reference`.

## Rebuild the samples

The kit keeps the source rows of the samples in `fixtures/real-market/source/`, cut from the start of each export without changing a byte. A sample that needs definitions has a second file with the definition rows of its instruments.

1. Run the rebuild script. It runs from any directory.

   ```bash
   sh fixtures/real-market/rebuild.sh
   ```

   For every sample the script writes `NAME.nwt`, the provenance printed by the converter as `NAME.provenance.json`, the JSON Lines view `NAME.jsonl` and the field-by-field view `NAME.fields.txt`. It ends by writing `SHA256SUMS` for the folder. The rebuilt `.nwt` files are byte-identical to the samples.
2. To rebuild `equity-bars.nwt` as well, set `NWT_SAMPLES_DIR` to the folder that holds the full exports and run the script again. The trade counts of the bars come from the full top-of-book export of the same venue and day, which is not part of the kit. Without the variable, the script prints a notice and leaves `equity-bars.nwt` as it is.

The script runs these conversions from the kit root:

<!-- nwt-title: Equities -->
```bash
S=fixtures/real-market/source
F=fixtures/real-market
python3 tools/nwt_convert_market.py csv-definition $S/xnas-itch_definition_all.csv $F/equity-definitions.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share
python3 tools/nwt_convert_market.py csv-mbo $S/xnas-itch_mbo_equities.csv $F/equity-orders.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share \
    --definitions $S/xnas-itch_definition_equities.csv --emit-deltas $F/equity-deltas.nwt
python3 tools/nwt_convert_market.py csv-mbp1 $S/xnas-itch_mbp-1_equities.csv $F/equity-quotes.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share \
    --definitions $S/xnas-itch_definition_equities.csv
python3 tools/nwt_convert_market.py csv-ohlcv $S/xnas-itch_ohlcv-1m_equities.csv $F/equity-bars.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share \
    --definitions $S/xnas-itch_definition_equities.csv \
    --trades $NWT_SAMPLES_DIR/xnas.itch/xnas.itch_mbp-1_equities.csv
```

<!-- nwt-title: Futures and options -->
```bash
S=fixtures/real-market/source
F=fixtures/real-market
python3 tools/nwt_convert_market.py csv-mbo $S/glbx-mdp3_mbo_futures.csv $F/futures-orders.nwt \
    --dataset REAL.GLBX.MDP3 --definitions $S/glbx-mdp3_definition_futures.csv --quantity-unit contract
python3 tools/nwt_convert_market.py csv-definition $S/opra-pillar_definition_all.csv $F/option-definitions.nwt \
    --dataset REAL.OPRA.PILLAR --quantity-unit contract
python3 tools/nwt_convert_market.py csv-cmbp1 $S/opra-pillar_cmbp-1_options.csv $F/option-best-quotes.nwt \
    --dataset REAL.OPRA.PILLAR --definitions $S/opra-pillar_definition_options.csv --quantity-unit contract
python3 tools/nwt_convert_market.py csv-mbp10 $S/ifus-impact_mbp-10_options.csv $F/depth-10.nwt \
    --dataset REAL.IFUS.IMPACT --definitions $S/ifus-impact_definition_options.csv --currency USX --quantity-unit contract
python3 tools/nwt_convert_market.py csv-statistics $S/xeur-eobi_statistics_all.csv $F/statistics.nwt \
    --dataset REAL.XEUR.EOBI --definitions $S/xeur-eobi_definition_statistics.csv --quantity-unit contract --skip-undefined
```

The options follow from the content of each export:

- The equities definitions have no currency, so the commands pass `--currency USD`.
- In the depth export, 12 instruments are not outright options and have no currency in their definition rows. Every outright option in the sample is priced in `USX`, so the command passes `--currency USX`. These 12 instruments get an `INSTRUMENT_DEF` with `asset_class` 0 and no `OPTION_DEF`.
- In the statistics export, 169 instruments have no currency in their definition rows. The venue trades in several currencies, so the command gives no fallback: `--skip-undefined` leaves these instruments out, and the provenance counts them.
- In the same export, 1,689 options have neither an underlying ID nor an underlying symbol in their definition rows, so they have an `INSTRUMENT_DEF` and no `OPTION_DEF`.
