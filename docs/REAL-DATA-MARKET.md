# Market data samples

The market data samples are ten NWT files built from exchange market-data exports in CSV: an order-level book, top of book, ten-level depth, one-minute bars, instrument definitions and statistics. They hold eleven record types: `TRADE`, `QUOTE`, `BAR`, `MBO`, `BOOK_SNAPSHOT`, `INSTRUMENT_DEF`, `OPTION_DEF`, `STATISTICS`, `BOOK_DELTA`, `TRADE_QUOTE` and `BEST_QUOTE`. Use them to test a reader against real values, to see how each source column becomes an NWT field, and as a model for converting your own exports with `tools/nwt_convert_market.py`. Venues, listings, the security master and corporate actions are covered in [Reference data samples](REAL-DATA.md).

## Sections

- [Samples](real-market/samples.md): The sample files made from real market exports, with the record types and contents of each.
- [Convert a file](real-market/convert-a-file.md): The converter, `tools/nwt_convert_market.py`, is a Python script that uses only the standard library.
- [Converter kinds](real-market/converter-kinds.md): The first argument selects the kind of export.
- [Options](real-market/options.md): Options follow the output file, as `--name value`, `--name=value` or a bare `--flag`.
- [Rules for every conversion](real-market/rules-for-every-conversion.md): The rules that hold for every kind: record header, exact values, nulls, instrument definitions, rows and columns, and output.
- [Instrument definitions: INSTRUMENT_DEF and OPTION_DEF](real-market/instrument-definitions-instrument_def-and-option_def.md): The kind `csv-definition` converts a definitions export on its own.
- [Order-level book: MBO and TRADE](real-market/order-level-book-mbo-and-trade.md): The kind `csv-mbo` reads an order-level export, in which every row is one event of one order.
- [Top of book: QUOTE and TRADE_QUOTE](real-market/top-of-book-quote-and-trade_quote.md): The kind `csv-mbp1` reads a top-of-book export.
- [Ten-level depth: BOOK_SNAPSHOT](real-market/ten-level-depth-book_snapshot.md): The kind `csv-mbp10` reads a depth export.
- [Consolidated top of book: BEST_QUOTE](real-market/consolidated-top-of-book-best_quote.md): The kind `csv-cmbp1` reads a consolidated top-of-book export, in which each side of the best quote names the venue that set it.
- [One-minute bars: BAR](real-market/one-minute-bars-bar.md): The kind `csv-ohlcv` reads a bars export.
- [Venue statistics: STATISTICS](real-market/venue-statistics-statistics.md): The kind `csv-statistics` reads a statistics export.
- [Provenance](real-market/provenance.md): Every container has a `PROVENANCE` element: a JSON object that records what was converted and by which rules.
- [Rebuild the samples](real-market/rebuild-the-samples.md): The kit keeps the source rows of the samples in `fixtures/real-market/source/`, cut from the start of each export without changing a byte.
