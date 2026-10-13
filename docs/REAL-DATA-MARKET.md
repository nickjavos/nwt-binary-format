# Real market data

This page covers the real examples of the market-data record types and the converters that made them.
Reference data (venues, listings, security master, corporate actions) is in [REAL-DATA.md](REAL-DATA.md).

| Record type | Example | Source shape |
|---|---|---|
| INSTRUMENT_DEF (6) | `fixtures/real-market/equity-definitions.nwt` | Definitions |
| INSTRUMENT_DEF (6), OPTION_DEF (11) | `fixtures/real-market/option-definitions.nwt` | Definitions |
| MBO (4), TRADE (1) | `fixtures/real-market/equity-orders.nwt`, `futures-orders.nwt` | Order-level book |
| BOOK_DELTA (15) | `fixtures/real-market/equity-deltas.nwt` | Derived from the order-level book |
| QUOTE (2), TRADE_QUOTE (18) | `fixtures/real-market/equity-quotes.nwt` | Top of book |
| BAR (3) | `fixtures/real-market/equity-bars.nwt` | One-minute bars |
| BEST_QUOTE (19) | `fixtures/real-market/option-best-quotes.nwt` | Consolidated top of book |
| BOOK_SNAPSHOT (5) | `fixtures/real-market/depth-10.nwt` | Ten-level depth |
| STATISTICS (13) | `fixtures/real-market/statistics.nwt` | Venue statistics |

The data is a licensed vendor CSV export. Read `fixtures/real-market/NOTICE.md` before passing any of it on.

## Running a conversion

```sh
python3 tools/nwt_convert_market.py KIND SRC OUT --dataset NAME [--option value | --flag] ...
python3 tools/nwt_convert.py        KIND SRC OUT --dataset NAME [--option value | --flag] ...
```

The converter prints the provenance it wrote, as JSON. On any failure it prints
`NWT error: <file> line N: ...`, exits with status 1 and writes no output file.

| Kind | Source shape | Writes |
|---|---|---|
| `csv-definition` | Definitions | INSTRUMENT_DEF; OPTION_DEF for calls and puts |
| `csv-mbo` | Order-level book | MBO and TRADE; with `--emit-deltas`, a second file of BOOK_DELTA |
| `csv-mbp1` | Top of book | QUOTE for every row; TRADE_QUOTE for trade rows |
| `csv-mbp10` | Ten-level depth | BOOK_SNAPSHOT, depth-limited |
| `csv-cmbp1` | Consolidated top of book | BEST_QUOTE |
| `csv-ohlcv` | One-minute bars | BAR |
| `csv-statistics` | Venue statistics | STATISTICS |

| Option | Meaning |
|---|---|
| `--dataset NAME` | Required. The manifest dataset, for example `REAL.XNAS.ITCH`. |
| `--quantity-unit TEXT` | The unit of order sizes, for example `share` or `contract`. The source has no such column, so this is always a stated policy. |
| `--currency TEXT` | The currency for instruments whose definition has none. Used only where the source is empty. |
| `--venue TEXT` | The venue text for INSTRUMENT_DEF where the definition has none. Optional. |
| `--definitions FILE` | The venue's definition file. Each instrument's INSTRUMENT_DEF (and OPTION_DEF) is written immediately before its first record. |
| `--skip-undefined` | Leave out, and count, the instruments whose definition has no currency, instead of stopping. |
| `--trades FILE` | `csv-ohlcv` only, required: the venue's top-of-book, order-level or consolidated file, for the trade counts. |
| `--emit-deltas [FILE]` | `csv-mbo` only: also write the derived BOOK_DELTA container (default `OUT` with `.deltas.nwt`). |
| `--fill-rule NAME` | `csv-mbo` only: `cancel-carries-fill` (default) or `fill-reduces`. See [Fill and cancel rule](#fill-and-cancel-rule). |
| `--max-rows N` | Convert only the first N data rows. |

## Rules that hold for every kind

- No value passes through floating point. Prices and sizes are parsed as exact decimals and timestamps as
  integer nanoseconds (`tools/nwt_parse.py`). A price with more than nine decimals stops the conversion, so
  nothing is ever rounded; the provenance states `values_rounded: 0`.
- Source `publisher_id` and `instrument_id` are kept. The channel is the source `channel_id` where the file
  has that column, otherwise 0.
- NWT sequences restart at 1 for each (publisher, channel). The source sequence number is not carried.
- `ts_event` and `ts_recv` are the source columns of the same names. A file without `ts_recv` gives null.
- Records keep the order of the source rows. Nothing is reordered.
- A definition always precedes the first record of its instrument. Without `--definitions` the converter
  writes a minimal INSTRUMENT_DEF: the row's symbol, asset class 0, null increments, and the currency,
  quantity unit and venue from the options (`--currency` is then required).
- An unknown code, a missing column, a row with the wrong number of columns or a text over its byte limit
  stops the conversion with the file name and line number. Nothing is truncated or guessed.
- Source flags are not carried. Rows that have no NWT form are skipped and counted.
- Output is deterministic. `created_ns` is fixed at 2026-10-13T00:00:00Z. The stream ID is the first 16 bytes
  of the SHA-256 of the kind, the output role and the SHA-256 of the source rows read. The same rows and
  options give the same bytes.
- Every publisher ID that appears is declared in the manifest as `publisher-<id>` with an empty venue: the
  source gives numbers only.

The PROVENANCE element of every container holds: `source_format` (`vendor CSV export`), `source_schema`,
`source_sha256` and `source_rows` (of the rows read), `conversion_policy` (the rules applied, as text),
`policy_options` (the options given), `records_written` by type, `rows_skipped` by reason, `values_rounded`,
`notes` (counts of rows handled by a stated policy), and where they apply `definitions_sha256`,
`trades_sha256` and `output` (`main` or `deltas`).

## Column mapping

### Definitions → INSTRUMENT_DEF and OPTION_DEF

| Source column | NWT field |
|---|---|
| `raw_symbol` | INSTRUMENT_DEF `symbol` |
| `instrument_class` | `asset_class`: `K` → 1 equity, `F` → 2 future, `C` and `P` → 3 option; `B`, `I`, `M`, `S`, `T`, `X`, `Y` → 0 unspecified. Any other letter stops the conversion. |
| `min_price_increment` | `price_increment`; empty → null |
| `expiration` | `expiration_ns`; empty → null |
| `underlying_id` | `underlying_instrument_id` (0 = none) |
| `strike_price` | `strike`; empty → null |
| `exchange` | `venue`; empty → `--venue`, else empty |
| `currency` | `currency`; empty → `--currency` |
| — | `quantity_unit` = `--quantity-unit` |
| — | `quantity_increment` and `contract_multiplier` are null |
| `security_update_action` | `A` and `M` write a definition (a later one replaces an earlier one). `D` rows are skipped and counted. |

`quantity_increment` is null because the source has lot sizes, not a size increment. `contract_multiplier`
is null because the source has a contract size in a unit of measure (pounds, tonnes, index points), which is
not in general a price multiplier.

A call or a put also gets an OPTION_DEF, directly after its INSTRUMENT_DEF:

| Source column | OPTION_DEF field |
|---|---|
| `instrument_class` | `right`: `C` → 1 call, `P` → 2 put |
| `underlying_id`, `expiration`, `strike_price` | The same values as in the INSTRUMENT_DEF |
| `asset` | `root` |
| `underlying` | `underlying_symbol` |
| `raw_symbol` | `osi_symbol`, only when the symbol has the 21-character OSI layout; otherwise empty |
| `cfi` | `exercise_style`: for a six-letter code starting with `O`, third letter `A` → 1 American, `E` → 2 European; anything else → 0 unknown |
| — | `settlement`, `closing_type` and `option_flags` are 0; `contract_multiplier` is null |

Exercise style is never inferred from a symbol. An option row with neither an underlying ID nor an
underlying symbol cannot form a valid OPTION_DEF: it gets its INSTRUMENT_DEF only, and the provenance counts it.

### Order-level book → MBO and TRADE

NWT MBO carries the remaining size of an order; the source carries size changes. The converter therefore
keeps every live order of every book.

| Source `action` | Written |
|---|---|
| `R` clear | MBO CLEAR |
| `A` add | MBO ADD with the row's price and size |
| `C` cancel | MBO MODIFY with the remaining size, or MBO DELETE when nothing remains |
| `M` modify | MBO MODIFY with the row's price and size. A side change is DELETE then ADD. A modify for an order that is not in the book is written as ADD and counted. |
| `T` trade | TRADE NEW: the row's price and size, `trade_id` 1, 2, 3, … per instrument in file order, aggressor from `side` (`B` buyer, `A` seller, `N` unknown) |
| `F` fill | Nothing; counted. See the next section. |
| `N` | Nothing; counted as a row with no book effect |

- `side` `B` → 1 bid, `A` → 2 ask. `priority` is null: the source gives no queue rank. `mbo_flags` is 0.
- A trade row without a price or with size 0 is skipped and counted.
- A book must begin with a clear row. An add, cancel or modify before the instrument's first `R` row stops
  the conversion, as do a cancel for an unknown order, a cancel larger than the remaining size, and an add
  for an order already in the book.
- The `flags` values seen in the corpus are 0, 2, 8, 40, 128, 130 and 168. None of their bits changes how a
  row is applied. A value with any other bit stops the conversion.

`--emit-deltas` writes a second container of BOOK_DELTA records. They are **derived**: they are not in the
source, and the provenance says so. After each order-level row is applied, the aggregate size and order
count at each changed price becomes a SET, or a DELETE when the level is empty; a clear row becomes CLEAR
with side 0. `LAST_IN_EVENT` marks the last delta derived from each source row. A book with more than 1,024
price levels on one side stops the conversion, as the BOOK_DELTA limit requires.

### Fill and cancel rule

The source reports an execution against a resting order as up to three rows: a trade (`T`), a fill (`F`)
naming the resting order, and a cancel (`C`) for the same order and size. Two readings are possible:

- `cancel-carries-fill`: the fill row does not change the book; the cancel row that follows removes the size.
- `fill-reduces`: the fill row removes the size, and the cancel row removes more.

The data settles it. For each venue below, the book was rebuilt from the converter's MBO records for the
first 20,000 order-level rows and compared with the venue's top-of-book file (first 20,000 rows) at every
source sequence number present in both. Best bid and best ask were compared on price, size and order count.
A top-of-book trade row shows the book at the trade, before it takes effect, so it is compared with the
rebuilt book at that trade row; every other row is compared with the book after the last row of its sequence.

| Venue | Rule | Shared sequences | Mismatches |
|---|---|---:|---:|
| `REAL.XNAS.ITCH` (equities, one symbol) | `cancel-carries-fill` | 8,835 | 0 |
| `REAL.GLBX.MDP3` (futures, one contract) | `cancel-carries-fill` | 5,578 | 0 |

`fill-reduces` is wrong on both. On the equities venue it stops at source line 20: a 200-share order is
filled for 180, and the cancel that follows is also for 180, which is more than the 20 that would remain.
On the futures venue it stops at line 8,848, where the cancel names an order the fill would already have removed.

The first execution of the equities fixture shows the rule. Source lines 18 to 20 are a sell of 180 at 177.03
against order 18315, which rested with 200:

```
T  side A  177.030000000  size 180
F  side B  177.030000000  size 180  order 18315
C  side B  177.030000000  size 180  order 18315
```

They become one TRADE (aggressor seller, quantity 180) and one MBO MODIFY that leaves order 18315 with 20.

`cancel-carries-fill` is the default for every venue. Only the two venues in the table were compared when
this page was written; the corpus check compares every venue that has both files.

### Top of book → QUOTE and TRADE_QUOTE

| Source column | NWT field |
|---|---|
| `bid_px_00`, `ask_px_00` | `bid_price`, `ask_price`; empty → the side is absent (null price, quantity 0, count 0) |
| `bid_sz_00`, `ask_sz_00` | `bid_quantity`, `ask_quantity` |
| `bid_ct_00`, `ask_ct_00` | `bid_order_count`, `ask_order_count`; a 0 on a present side is written as a null count and counted |
| `price`, `size`, `side` on a `T` row | TRADE_QUOTE `price`, `quantity`, `aggressor` |

- Every row becomes a QUOTE with the row's book columns. `quote_flags` is 0.
- A trade row also becomes a TRADE_QUOTE, written after its QUOTE. On a trade row the book columns are the
  top of book at the trade. `trade_id` is 0, because the source has none, and `conditions` is 0.
- A present side with size 0, or a size without a price, stops the conversion.
- TRADE (from the order-level file) and TRADE_QUOTE (from this file) describe the same prints, so they are
  never written to the same container.

### Ten-level depth → BOOK_SNAPSHOT

Every row becomes one BOOK_SNAPSHOT with `book_flags` 1 (depth-limited). The ten `bid_*_NN` and `ask_*_NN`
column groups become paired levels under the same presence rules as QUOTE. Trailing levels that are empty on
both sides are dropped, so a book with three bid and five ask levels gives five levels with the bids absent
in the last two. A row with an empty level above a filled one, or with bid prices not strictly falling or
ask prices not strictly rising, stops the conversion with its line number. Trade rows restate the book; the
print itself is not carried by this kind, and the provenance counts those rows.

### Consolidated top of book → BEST_QUOTE

| Source column | NWT field |
|---|---|
| `bid_px_00`, `ask_px_00`, `bid_sz_00`, `ask_sz_00` | Prices and quantities, as for QUOTE |
| `bid_pb_00`, `ask_pb_00` | `bid_publisher_id`, `ask_publisher_id`; 0 on an absent side |
| — | Order counts are null on a present side: the source has none. `interval_ns` is 0 (event-driven). |

Every venue ID that appears is declared in the manifest. A trade row carries the publisher of the venue
where the trade happened; it restates the best quote under that publisher, and its print is not carried by
this kind (counted in the provenance).

### One-minute bars → BAR

| Source column | NWT field |
|---|---|
| `ts_event` | `interval_start_ns`. `interval_end_ns` is 60 seconds later, and the record's `ts_event` is the interval end. |
| `open`, `high`, `low`, `close`, `volume` | The same fields |
| — | `trade_count`, from the `--trades` file |

The source bars have no trade count, and a BAR is never written with an invented one. The converter counts
the trade rows of the `--trades` file whose capture time (`ts_recv`) falls in the bar's minute, for the same
publisher and instrument; the source builds its bars on that timestamp. The summed size of those rows must
equal the bar's volume. Without `--trades`, or on any mismatch, the conversion fails and names the bar.
Only rows with `rtype` 33 (one minute) are accepted.

For the equities fixture all 921 bars of the day agree with the trade rows of the venue's top-of-book file.

### Venue statistics → STATISTICS

| Source `stat_type` | Source meaning | NWT `stat_type` |
|---:|---|---|
| 1 | Opening price | 1 open |
| 5 | Trading session high price | 2 high |
| 4 | Trading session low price | 3 low |
| 11 | Close price | 4 close |
| 3 | Settlement price | 5 settlement |
| 6 | Cleared volume | 7 volume |
| 9 | Open interest | 8 open interest |

How the map was confirmed:

- **Codes.** The export format's public reference page for this schema lists the types by number with the
  meanings above (read 13 October 2026).
- **High against low, from the data.** Over all 4,151,957 rows of the statistics file, the latest type 5
  value was never below the latest type 4 value of the same instrument (7,917 comparisons, 0 violations).
- **`stat_flags`.** In the file the flag is 1 only on settlement prices (584,812 rows; 2,580 settlement
  rows have 0). The format's page for this venue states that bit 0 means a final settlement. NWT has the
  opposite bit, "preliminary", so a settlement with source flag 1 is written with `stat_flags` 0 and a
  settlement with source flag 0 is written with `stat_flags` 1. The same page defines bit 1 as a theoretical
  settlement; NWT has no field for it and it does not occur in the file, so that value stops the conversion,
  as does any flag on another type.

Other rules: `update_action` 1 → SET, 2 → DELETE (both values null). An empty `ts_ref` is null; it is empty
on every row of the file. A price type takes its value from `price` and has a null quantity; a quantity type
takes it from `quantity` and has a null price. The source writes "no quantity" as 9223372036854775807, which
becomes the NWT null. A row with no value is skipped and counted. Any `stat_type` outside the table stops
the conversion.

Two things to know when reading the result. Source type 6 is the cleared volume of the previous trading
date, and the source gives no reference date, so NWT `volume` records from this source have a null `ts_ref`.
"Preliminary" for a settlement with flag 0 follows the reference's statement that the flag tells final from
preliminary; the venue page itself names only the final bit.

## Fixtures

All in `fixtures/real-market/`. Each `NAME.nwt` comes with `NAME.jsonl` (`to-json`), `NAME.fields.txt`
(`read`) and `NAME.provenance.json` (the converter's summary; for `equity-orders` it also holds the
provenance of `equity-deltas`). The source slices are in `source/` under neutral names, cut from the start
of each file without changing a byte. `SHA256SUMS` covers the slices and the generated files.

| Fixture | Source slice | Records |
|---|---|---|
| `equity-definitions` | First 200 definition rows of one equities venue | 200 INSTRUMENT_DEF |
| `equity-orders` | First 2,000 order-level rows, one symbol, 16 September 2025 | 1 INSTRUMENT_DEF, 1,818 MBO (1 CLEAR, 1,420 ADD, 39 MODIFY, 358 DELETE), 123 TRADE; 59 fill rows counted |
| `equity-deltas` | The same 2,000 rows | 1 INSTRUMENT_DEF, 1,818 BOOK_DELTA (1 CLEAR, 1,599 SET, 218 DELETE); derived |
| `equity-quotes` | First 2,000 top-of-book rows, same symbol and day | 1 INSTRUMENT_DEF, 2,000 QUOTE, 476 TRADE_QUOTE |
| `equity-bars` | All 921 one-minute bars of the same symbol and day | 1 INSTRUMENT_DEF, 921 BAR |
| `futures-orders` | First 2,000 order-level rows of one futures contract | 1 INSTRUMENT_DEF, 2,000 MBO (1 CLEAR, 1,999 ADD) |
| `option-definitions` | First 500 definition rows of a consolidated options feed | 500 INSTRUMENT_DEF, 370 OPTION_DEF |
| `option-best-quotes` | First 2,000 consolidated top-of-book rows | 641 INSTRUMENT_DEF, 641 OPTION_DEF, 2,000 BEST_QUOTE |
| `depth-10` | First 500 ten-level depth rows of one futures-options venue | 199 INSTRUMENT_DEF, 187 OPTION_DEF, 500 BOOK_SNAPSHOT (1 to 10 levels) |
| `statistics` | First 2,000 rows with a value from one derivatives venue | 1,831 INSTRUMENT_DEF, 36 OPTION_DEF, 1,831 STATISTICS (1,809 open, 22 preliminary settlement) |

Notes on single fixtures:

- **Definitions for the data fixtures.** Each data fixture has a second slice holding the definition rows
  of the instruments that appear in it (for example `source/xnas-itch_definition_equities.csv`, one row).
  These are the only slices that are not "first rows": they are the matching rows of the venue's definition
  file, unchanged.
- **`equity-*`.** The equities definitions have no currency, so `--currency USD --quantity-unit share` is the
  stated policy.
- **`futures-orders`.** The first 2,000 rows of this file are the book at the start of the session: one clear
  and 1,999 adds. The slice contains no trade, cancel or modify.
- **`option-best-quotes`.** Four of the 2,000 rows are trade rows under the publisher of the executing
  venue, which is why three instruments are defined a second time under another publisher.
- **`depth-10`.** The 12 option strategies in the slice have no currency in their definition rows. Every
  outright option in the slice is the same product, priced in `USX`, so `--currency USX` is the stated
  fallback. The strategies get an INSTRUMENT_DEF with asset class 0 and no OPTION_DEF.
- **`statistics`.** 169 of the 2,000 instruments are spreads and strategies without a currency. The venue
  trades in several currencies, so no fallback is given: `--skip-undefined` leaves those instruments out and
  the provenance counts them. 1,689 option rows have no underlying ID or symbol in the definitions and get
  an INSTRUMENT_DEF only.

### Rebuild

```sh
sh fixtures/real-market/rebuild.sh
```

The script runs from any directory and rebuilds everything from `source/`. Running it twice gives identical
files. It works offline with one exception: the trade counts of `equity-bars` need the venue's full
top-of-book file, which is too large to keep in the kit. That fixture is rebuilt only when `NWT_SAMPLES_DIR`
points at the sample corpus; otherwise the script prints a notice and leaves it as it is.

The commands it runs, from the kit root (`S` is `fixtures/real-market/source`, `F` is `fixtures/real-market`):

```sh
python3 tools/nwt_convert_market.py csv-definition $S/xnas-itch_definition_all.csv $F/equity-definitions.nwt \
    --dataset REAL.XNAS.ITCH --currency USD --quantity-unit share
python3 tools/nwt_convert_market.py csv-mbo $S/xnas-itch_mbo_equities.csv $F/equity-orders.nwt \
    --dataset REAL.XNAS.ITCH --definitions $S/xnas-itch_definition_equities.csv \
    --currency USD --quantity-unit share --emit-deltas $F/equity-deltas.nwt
python3 tools/nwt_convert_market.py csv-mbp1 $S/xnas-itch_mbp-1_equities.csv $F/equity-quotes.nwt \
    --dataset REAL.XNAS.ITCH --definitions $S/xnas-itch_definition_equities.csv --currency USD --quantity-unit share
python3 tools/nwt_convert_market.py csv-ohlcv $S/xnas-itch_ohlcv-1m_equities.csv $F/equity-bars.nwt \
    --dataset REAL.XNAS.ITCH --definitions $S/xnas-itch_definition_equities.csv --currency USD --quantity-unit share \
    --trades TOP-OF-BOOK-FILE-OF-THE-SAME-VENUE-AND-DAY
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

python3 examples/python/nwt_example.py to-json $F/NAME.nwt > $F/NAME.jsonl
python3 examples/python/nwt_example.py read    $F/NAME.nwt > $F/NAME.fields.txt
```

## Corpus check

```sh
NWT_SAMPLES_DIR=/path/to/samples python3 tools/corpus_check.py [--rows 20000]
```

The sample corpus is 121 CSV files from 26 venues, about 20 GB; it is not part of the kit. The check converts
the first 20,000 rows of every file into a temporary container, reads it back, runs the semantic checker
(`examples/python/market_state.py`) and runs the cross-checks that apply:

- order-level book: the rebuilt best bid and ask against the venue's top-of-book file, as described under
  [Fill and cancel rule](#fill-and-cancel-rule);
- bars: every bar's volume against the summed trade sizes of its minute (the conversion fails otherwise).

It prints one row per file (venue, schema, class, rows in, records out, skipped, result) and writes the
table to `fixtures/real-market/CORPUS-CHECK.md`. A file that cannot be converted is a table row with its
cause, not a crash. The check uses the venue's definition file for every data file, `--skip-undefined`, and a
`USD` currency fallback for the equities venues and for the one futures venue whose definitions have no currency.

**Status when this page was written: the corpus check had not been run.** Only the conversions that produce
the fixtures above, and the two comparisons in the fill-rule table, were run. `CORPUS-CHECK.md` appears when
the check is run; until then, treat every file outside the fixtures as unverified.

## What is not carried

- The source sequence number, the source flags, and the source's capture-delay column.
- Queue priority (the source has none), trade IDs (the source has none; TRADE gets 1, 2, 3, …).
- The trade prints inside ten-level and consolidated files (use the order-level or top-of-book file).
- Definition columns with no NWT field: lot sizes, price limits, contract size and unit of measure, strategy
  legs, settlement currency, matching algorithm and the rest. Settlement method is left unknown even where
  the CFI code states it.
- Statistics types other than the seven in the table, and the theoretical-settlement flag.
