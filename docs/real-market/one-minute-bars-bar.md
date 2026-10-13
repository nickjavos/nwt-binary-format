# One-minute bars: BAR

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
