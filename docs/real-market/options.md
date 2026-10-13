# Options

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
| `--fill-rule NAME` | `csv-mbo` | The rule for fill rows: `cancel-carries-fill` (the default) or `fill-reduces`. See [Fills and cancels](order-level-book-mbo-and-trade.md#fills-and-cancels). |
| `--max-rows N` | Every kind | Converts only the first N data rows. |
