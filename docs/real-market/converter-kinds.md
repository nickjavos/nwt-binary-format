# Converter kinds

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
